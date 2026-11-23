"""Live cards, redrawn by the GitHub Action (.github/workflows/profile.yml).

    python scripts/live.py            # real data: needs PROFILE_TOKEN or GITHUB_TOKEN in the environment
    python scripts/live.py --sample   # made-up numbers, for previewing without a token

Writes generated/{stats,streak,year,ticker}-{light,dark}.svg, generated/repo-<n>-{light,dark}.svg
and generated/building.json (which repo each card shows, for readme.py).
Only needs fontTools (pip install fonttools).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from art import BODY, CAPE_B, HAIR, LEGS
from lib.svgkit import MONO_ADV, PALETTES, ROOT, THEMES, config, doc, dots, panel, text, text_width, write

W = 830
NOW = dt.datetime.now(dt.timezone.utc)


# ---------------------------------------------------------------- data

QUERY = """
query($login: String!) {
  user(login: $login) {
    id
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    recent: repositories(first: 12, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                         orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes { name isArchived }
    }
  }
}
"""

REPO_FIELDS = """
  nameWithOwner name description url isPrivate pushedAt
  owner { login }
  primaryLanguage { name color }
  defaultBranchRef { target { ... on Commit {
    history(first: 15) { nodes { messageHeadline parents { totalCount } } }
    mine: history(first: 8, author: {id: %s}) { nodes { messageHeadline committedDate parents { totalCount } } }
  } } }
"""


def gql(query: str, variables: dict, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "el-profile"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        print("GraphQL said:", json.dumps(out["errors"])[:600], file=sys.stderr)
    return out.get("data") or {}


def fetch(cfg: dict, token: str) -> dict:
    user = cfg["user"]
    d = gql(QUERY, {"login": user}, token)["user"]
    cc = d["contributionsCollection"]
    days = [day for w in cc["contributionCalendar"]["weeks"] for day in w["contributionDays"]]
    langs: dict[str, list] = {}
    stars = 0
    for repo in d["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
    # the repos to look up: your pins, then your public repos by latest push
    b = cfg["building"]
    pins = [f for f in b.get("pin", []) if not f.get("upcoming")]
    skip = {x.lower() for x in b.get("skip", [])} | {user.lower()}
    pinned = {f["repo"].rpartition("/")[2].lower() for f in b.get("pin", [])}
    recent = [r["name"] for r in d["recent"]["nodes"]
              if not r["isArchived"] and r["name"].lower() not in skip | pinned]
    wanted = [f["repo"] for f in pins] + recent[:8]
    parts = []
    for i, full in enumerate(wanted):
        owner, _, name = full.rpartition("/")
        parts.append(f'r{i}: repository(owner: {json.dumps(owner or user)}, name: {json.dumps(name)}) {{{REPO_FIELDS % json.dumps(d["id"])}}}')
    found = gql("query {" + "\n".join(parts) + "}", {}, token) if parts else {}
    looked_up = [found.get(f"r{i}") for i in range(len(wanted))]
    return dict(
        days=[(x["date"], x["contributionCount"]) for x in days],
        total=cc["contributionCalendar"]["totalContributions"],
        commits=cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        prs=d["pullRequests"]["totalCount"], issues=d["issues"]["totalCount"],
        contributed=d["repositoriesContributedTo"]["totalCount"], stars=stars,
        langs=langs, cards=pick_cards(cfg, looked_up[:len(pins)], looked_up[len(pins):]),
        pushes=latest_pushes(looked_up),
    )


def latest_pushes(repos: list, n: int = 6) -> list[tuple[str, str, str]]:
    """Your own latest commits across the looked-up public repos, newest first: (repo, message, date).
    Merge commits are skipped; private repos never get here, so their messages stay private."""
    out = []
    for repo in repos:
        if not repo or repo.get("isPrivate"):
            continue
        tgt = ((repo.get("defaultBranchRef") or {}).get("target") or {})
        for c in (tgt.get("mine") or {}).get("nodes") or []:
            if (c.get("parents") or {}).get("totalCount", 1) <= 1:
                out.append((repo["name"], c["messageHeadline"], c["committedDate"]))
    return sorted(out, key=lambda x: x[2], reverse=True)[:n]


def pick_cards(cfg: dict, pinned: list, recent: list) -> list[tuple[dict | None, dict]]:
    """Cards for "currently building": (repo or None, meta). Pins first, then the latest
    pushes fill the free slots, and "coming soon" pins go last so live work leads."""
    b = cfg["building"]
    notes = {k.lower(): v for k, v in b.get("notes", {}).items()}
    pins = b.get("pin", [])
    live_pins = [f for f in pins if not f.get("upcoming")]
    soon = [f for f in pins if f.get("upcoming")]
    free = max(0, b.get("slots", 4) - len(pins))
    note = lambda f: {**notes.get(f["repo"].rpartition("/")[2].lower(), {}), **f}
    cards = [(r, note(f)) for r, f in zip(pinned, live_pins)]
    for repo in recent:
        if len(cards) >= len(live_pins) + free:
            break
        if not repo:
            continue
        meta = {"repo": repo["nameWithOwner"], **notes.get(repo["name"].lower(), {})}
        cards.append((repo, meta))
    return cards + [(None, note(f)) for f in soon]


def sample(cfg: dict) -> dict:
    rng = random.Random(82)
    start = (NOW - dt.timedelta(days=364)).date()
    days = []
    for i in range(365):
        d = start + dt.timedelta(days=i)
        busy = 0.35 if 140 < i < 210 or i > 300 else 0
        v = rng.random() + busy - (0.25 if d.weekday() >= 5 else 0)
        days.append((d.isoformat(), 0 if v < 0.4 else int((v - 0.4) * 14)))
    for i in range(1, 13):
        days[-i] = (days[-i][0], max(1, days[-i][1]))
    langs = {"Java": [34, "#b07219"], "TypeScript": [22, "#3178c6"], "Python": [18, "#3572A5"],
             "JavaScript": [12, "#f1e05a"], "Elixir": [8, "#6e4a7e"], "CSS": [6, "#663399"]}
    # (repo, language, hours since the push, latest commit)
    fake = [("Merlin", ("TypeScript", "#3178c6"), 2, "fix(fire): steadier flame flicker"),
            ("my-portfolio", ("Astro", "#ff5a03"), 9, "feat(aura): El splits the rock"),
            ("Ka-dugo", ("JavaScript", "#f1e05a"), 30, "docs: README with screenshots"),
            ("ThriftBite", ("Java", "#b07219"), 50, "docs: rewrite the README as a front page"),
            ("webapp-secondserve", ("Python", "#3572A5"), 120, "feat(api): pickup time slots")]
    recent = [dict(name=n, nameWithOwner=f"{cfg['user']}/{n}", description=None, url=f"https://github.com/{cfg['user']}/{n}",
                   isPrivate=False, owner={"login": cfg["user"]}, pushedAt=(NOW - dt.timedelta(hours=h)).isoformat(),
                   primaryLanguage={"name": lang, "color": col},
                   defaultBranchRef={"target": {"history": {"nodes": [{"messageHeadline": msg, "parents": {"totalCount": 1}}]}}})
              for n, (lang, col), h, msg in fake]
    pins = [f for f in cfg["building"].get("pin", []) if not f.get("upcoming")]
    pinned = [next((r for r in recent if r["name"] == f["repo"].rpartition("/")[2]), None) for f in pins]
    rest = [r for r in recent if r not in pinned]
    pushes = [(n, msg, (NOW - dt.timedelta(hours=h)).isoformat()) for n, _, h, msg in fake]
    return dict(pushes=pushes, days=days, total=sum(c for _, c in days), commits=412, prs=37, issues=12, contributed=6, stars=9,
                langs=langs, cards=pick_cards(cfg, pinned, rest))


# ---------------------------------------------------------------- numbers

def streaks(days):
    counts = [c for _, c in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if counts and counts[-1] == 0:
        i -= 1          # today isn't over yet
    while i >= 0 and counts[i]:
        cur, i = cur + 1, i - 1
    return cur, longest


def aura(d) -> str:
    score = d["commits"] + 3 * d["prs"] + d["issues"] + 4 * d["stars"] + 5 * d["contributed"]
    for cut, grade in ((1500, "S"), (700, "A+"), (350, "A"), (180, "B+"), (80, "B")):
        if score >= cut:
            return grade
    return "C"


def ago(iso: str) -> str:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = (NOW - t).total_seconds()
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"pushed {int(s // n)}{unit} ago"
    return "pushed just now"


def fit(s: str, size: float, max_w: float, **kw) -> str:
    if text_width(s, size, **kw) <= max_w:
        return s
    while s and text_width(s + "…", size, **kw) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def wrap(s: str, size: float, max_w: float, lines: int, **kw) -> list[str]:
    out, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if text_width(trial, size, **kw) <= max_w:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = fit(out[-1] + " …", size, max_w, **kw)
    return [x for x in out if x]


def sh(c, x, y, w, h, color):
    """Solid comic offset shadow."""
    return f'<rect x="{x + 6}" y="{y + 6}" width="{w}" height="{h}" fill="{color}"/>'


# ---------------------------------------------------------------- cards

def stats_card(theme, d):
    c = PALETTES[theme]
    pw, ph = 404, 196
    body = sh(c, 0, 0, pw, ph, c["ink"]) + panel_plain(c, 0, 0, pw, ph, "~/el/stats")
    rows = [("Commits (past year)", d["commits"]), ("Pull requests", d["prs"]), ("Issues", d["issues"]),
            ("Stars earned", d["stars"]), ("Contributed to", d["contributed"])]
    for i, (k, v) in enumerate(rows):
        y = 60 + i * 26
        body += text(k, 18, y, 14, c["ink"], wght=600) + text(f"{v:,}", 268, y, 15, c["ink"], wght=700, anchor="end")
    g = aura(d)
    pts = " ".join(f"{338 + (52 if i % 2 == 0 else 28) * math.cos(i * math.pi / 8 - math.pi / 2):.1f},"
                   f"{112 + (52 if i % 2 == 0 else 28) * math.sin(i * math.pi / 8 - math.pi / 2):.1f}" for i in range(16))
    body += (f'<polygon class="burst" points="{pts}" fill="{c["accent"]}" stroke="{c["ink"]}" stroke-width="3" stroke-linejoin="round"/>'
             + text(g, 338, 122, 30, c["white"], wght=700, wdth=70, anchor="middle")
             + text("AURA", 338, 138, 9, c["white"], wght=700, ls=1, anchor="middle"))
    # languages
    x0 = pw + 22
    body += sh(c, x0, 0, pw, ph, c["ink"]) + panel_plain(c, x0, 0, pw, ph, "~/el/languages")
    total = sum(v for v, _ in d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1][0])[:5]
    rest = total - sum(v for _, (v, _) in top)
    items = [(n, v / total, col) for n, (v, col) in top] + ([("Other", rest / total, c["muted"])] if rest > 0 else [])
    bx, by, bw = x0 + 18, 48, pw - 36
    body += f'<rect x="{bx}" y="{by}" width="{bw}" height="14" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
    cx = bx + 1.25
    for n, share, col in items:
        w = (bw - 2.5) * share
        body += f'<rect x="{cx:.1f}" y="{by + 1.25}" width="{max(w, 0):.1f}" height="11.5" fill="{col}"/>'
        cx += w
    for i, (n, share, col) in enumerate(items):
        col_x = bx + (i % 2) * (bw / 2 + 6)
        y = by + 44 + (i // 2) * 28
        body += f'<circle cx="{col_x + 6}" cy="{y - 5}" r="6" fill="{col}" stroke="{c["ink"]}" stroke-width="1.5"/>'
        body += text(n, col_x + 18, y, 14, c["ink"], wght=600)
        body += text(f"{share * 100:.0f}%", col_x + bw / 2 - 14, y, 14, c["ink"], wght=700, anchor="end")
    label = (f"Stats: {d['commits']} commits in the past year, {d['prs']} pull requests, {d['issues']} issues, "
             f"{d['stars']} stars, contributed to {d['contributed']} repos. Top languages: "
             + ", ".join(f"{n} {s * 100:.0f}%" for n, s, _ in items))
    css = ".burst{transform-origin:338px 112px;animation:spin 24s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
    return doc(W, ph + 8, body, label, css)


def panel_plain(c, x, y, w, h, title):
    return (f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{w - 3}" height="{h - 3}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="26" fill="{c["ink"]}"/>'
            + text(title, x + 12, y + 18, 12, c["card"], mono=True, bold=True))


def streak_card(theme, d):
    c = PALETTES[theme]
    cur, longest = streaks(d["days"])
    h = 124
    w3 = (W - 8 - 6) / 3.2
    mid = W - 8 - 6 - 2 * w3
    body = sh(c, 0, 0, W - 8, h, c["accent"]) + f'<rect x="0" y="0" width="{W - 8}" height="{h}" fill="{c["ink"]}"/>'
    cells = [(3, w3 - 3, f"{d['total']:,}", "TOTAL CONTRIBUTIONS", "in the past year", False),
             (3 + w3, mid - 3, str(cur), "CURRENT STREAK", "days · inconsistency, reformed" if cur >= 7 else "days · the comeback starts now", True),
             (3 + w3 + mid, w3 - 3, str(longest), "LONGEST STREAK", "days in a row", False)]
    for x, w, big, lab, sub, hi in cells:
        if not hi:
            body += f'<rect x="{x}" y="3" width="{w}" height="{h - 6}" fill="{c["paper"]}"/>'
        fg = c["card"] if hi else c["ink"]
        cx = x + w / 2
        body += text(big, cx, 62 if not hi else 66, 44 if not hi else 56, c["on_ink_accent"] if hi else c["ink"], wght=700, wdth=70, anchor="middle")
        body += text(lab, cx, 88, 13, fg, wght=700, ls=0.5, anchor="middle")
        body += text(sub, cx, 106, 12, c["muted"] if not hi else fg, wght=400, anchor="middle", extra='' if not hi else ' opacity="0.75"')
    label = f"{d['total']} contributions in the past year. Current streak {cur} days, longest {longest} days."
    return doc(W, h + 8, body, label)


def year_card(theme, d):
    c = PALETTES[theme]
    days = d["days"]
    first = dt.date.fromisoformat(days[0][0])
    pad = (first.weekday() + 1) % 7          # GitHub weeks start on Sunday
    cells = [None] * pad + days
    weeks = math.ceil(len(cells) / 7)
    mx = max((n for _, n in days), default=1) or 1
    cs, gap = 11, 3
    gx, gy = 40, 82
    gw = weeks * (cs + gap) - gap
    h = gy + 7 * (cs + gap) + 40
    body = panel(c, 0, 0, W - 14, h, "~/el/year.svg", f"{d['total']:,} contributions · past year", uid="y")
    for i, cell in enumerate(cells):
        if cell is None:
            continue
        wk, dow = divmod(i, 7)
        n = cell[1]
        lvl = 0 if n == 0 else min(4, 1 + int(3 * n / mx + 0.25))
        body += f'<rect x="{gx + wk * (cs + gap)}" y="{gy + dow * (cs + gap)}" width="{cs}" height="{cs}" rx="2" fill="{c["levels"][lvl]}"/>'
    # month labels
    seen = set()
    for i, cell in enumerate(cells):
        if cell is None:
            continue
        day = dt.date.fromisoformat(cell[0])
        if day.day <= 7 and day.month not in seen and i // 7 < weeks - 2:
            seen.add(day.month)
            body += text(day.strftime("%b"), gx + (i // 7) * (cs + gap), gy + 7 * (cs + gap) + 16, 11, c["muted"], mono=True)
    # the fog El clears as he runs, and El himself
    T = 16
    body += (f'<clipPath id="yc"><rect x="{gx - 22}" y="{gy - 52}" width="{gw + 34}" height="{7 * (cs + gap) + 54}"/></clipPath>'
             f'<g clip-path="url(#yc)"><g class="run"><rect x="{gx - 2}" y="{gy - 2}" width="{gw + 6}" height="{7 * (cs + gap) + 2}" fill="{c["paper"]}" opacity="0.78"/>'
             f'<g transform="translate({gx - 14} {gy - 46})"><g class="hop">'
             f'<g transform="scale(0.13) translate(-110 -30)">'
             f'<path d="{BODY}" fill="{c["ink"]}"/><path d="{LEGS}" fill="{c["ink"]}"/>'
             f'<path d="{CAPE_B}" fill="{c["accent"]}" stroke="{c["ink"]}" stroke-width="8"/>'
             f'<g transform="translate(92 58) scale(0.55)"><path d="{HAIR}" fill="{c["ink"]}"/></g></g></g></g></g></g>')
    css = (f".run{{animation:run {T}s infinite}}"
           f"@keyframes run{{0%{{transform:translateX(0);animation-timing-function:steps({weeks},end)}}"
           f"75%,100%{{transform:translateX({weeks * (cs + gap)}px)}}}}"
           f".hop{{animation:hop {T * 0.75 / weeks * 2:.3f}s steps(2,jump-none) infinite}}"
           f"@keyframes hop{{0%{{transform:translateY(0)}}100%{{transform:translateY(-5px)}}}}"
           f"@media (prefers-reduced-motion:reduce){{.run{{transform:translateX({weeks * (cs + gap)}px)}}}}")
    label = f"Contribution graph for the past year, {d['total']} contributions. El runs across it week by week."
    return doc(W, h + 14, body, label, css)


def repo_card(theme, repo, meta, i, user):
    c = PALETTES[theme]
    w, h = 404, 176
    shadow = c["accent"] if i == 0 else c["ink"]
    body = sh(c, 0, 0, w, h, shadow)
    body += f'<rect x="1.25" y="1.25" width="{w - 2.5}" height="{h - 2.5}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
    if meta.get("upcoming") or not repo:
        name = meta["repo"].rpartition("/")[2]
        desc, lang, color, msg = meta.get("fallback", ""), "", c["muted"], ""
        when, tag = ("repo coming soon", "Soon") if meta.get("upcoming") else ("repo not found", "Repo")
    else:
        name = repo["name"]
        desc = repo.get("description") or meta.get("fallback", "")
        pl = repo.get("primaryLanguage") or {}
        lang, color = pl.get("name", ""), pl.get("color") or c["muted"]
        tgt = ((repo.get("defaultBranchRef") or {}).get("target") or {})
        commits = (tgt.get("history") or {}).get("nodes") or []
        # skip merge commits ("Merge pull request #2 from ..."): show the last real message
        real = [n for n in commits if (n.get("parents") or {}).get("totalCount", 1) <= 1]
        msg = (real or commits or [{}])[0].get("messageHeadline", "") or tgt.get("messageHeadline", "")
        when = ago(repo["pushedAt"]) if repo.get("pushedAt") else ""
        tag = meta.get("tag") or ("Private" if repo.get("isPrivate") else ("Team" if repo["owner"]["login"].lower() != user.lower() else "Public"))
    name_s = fit(name, 16, w - 120, wght=700)
    body += text(name_s, 18, 32, 16, c["accent"], wght=700)
    tx = 18 + text_width(name_s, 16, 700) + 10
    tw = text_width(tag, 11.5, 500) + 16
    body += f'<rect x="{tx:.1f}" y="18" width="{tw:.1f}" height="19" rx="9.5" fill="none" stroke="{c["muted"]}" stroke-width="1"/>'
    body += text(tag, tx + tw / 2, 31.5, 11.5, c["muted"], wght=500, anchor="middle")
    for j, line in enumerate(wrap(desc, 13, w - 36, 2, wght=400)):
        body += text(line, 18, 60 + j * 19, 13, c["ink"], wght=400)
    css = ""
    if not msg and meta.get("upcoming"):
        # fenced off with caution tape, like the banner at the top of the profile
        band, period = 24, 28
        stripes = "".join(
            f'<polygon points="{x},0 {x + period / 2},0 {x + period / 2 - band},{band} {x - band},{band}" fill="{c["accent"]}"/>'
            for x in range(-2 * period, w + 3 * period, period))
        sign = "UNDER CONSTRUCTION"
        sw = text_width(sign, 11.5, mono=True, bold=True) + 24
        body += (f'<clipPath id="soon{theme}"><rect x="2.5" y="2.5" width="{w - 5}" height="{h - 5}"/></clipPath>'
                 f'<g clip-path="url(#soon{theme})"><g transform="rotate(-4 {w / 2} 111)">'
                 f'<rect x="-30" y="99" width="{w + 60}" height="{band}" fill="{c["ink"]}"/>'
                 f'<svg x="-30" y="99" width="{w + 60}" height="{band}" overflow="hidden"><g class="tape">{stripes}</g></svg>'
                 f'<rect x="{(w - sw) / 2:.1f}" y="97" width="{sw:.1f}" height="{band + 4}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
                 + text(sign, w / 2, 115.5, 11.5, c["ink"], mono=True, bold=True, anchor="middle")
                 + "</g></g>")
        css = f".tape{{animation:slide 2.4s linear infinite}}@keyframes slide{{to{{transform:translateX({period}px)}}}}"
    if msg:
        body += f'<rect x="18" y="98" width="{w - 36}" height="26" fill="{c["ink"]}"/>'
        body += text("$", 28, 115.5, 11.5, c["on_ink_accent"], mono=True, bold=True)
        m = fit(f'git commit -m "{msg}"', 11.5, w - 36 - 34, mono=True)
        if not m.endswith('"'):
            m = m.rstrip("…") + '…"'
        body += text(m, 28 + 11.5 * MONO_ADV * 2, 115.5, 11.5, c["card"], mono=True)
    y = 152
    if lang:
        body += f'<circle cx="24" cy="{y - 4}" r="5.5" fill="{color}"/>' + text(lang, 36, y, 12, c["muted"], wght=500)
    rx = 36 + (text_width(lang, 12, 500) + 18 if lang else -18)
    body += text(meta.get("role", ""), rx, y, 12, c["muted"], wght=500)
    body += text(when, w - 18, y, 12, c["muted"], wght=500, anchor="end")
    if repo and repo.get("pushedAt") and NOW - dt.datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00")) < dt.timedelta(hours=24):
        # pushed in the last day: a pulsing LIVE dot before the time
        lx = w - 18 - text_width(when, 12, 500) - 12
        body += (f'<circle class="ping" cx="{lx:.1f}" cy="{y - 4}" r="4.5" fill="none" stroke="{c["accent"]}" stroke-width="2"/>'
                 f'<circle cx="{lx:.1f}" cy="{y - 4}" r="4.5" fill="{c["accent"]}"/>')
        css = (f".ping{{transform-box:fill-box;transform-origin:center;animation:ping 1.6s ease-out infinite}}"
               f"@keyframes ping{{from{{transform:scale(1);opacity:.9}}to{{transform:scale(2.6);opacity:0}}}}")
        when = "live, " + when
    label = f"{name} ({tag}): {desc} {lang}. {meta.get('role', '')}. {when}. Latest commit: {msg}"
    return doc(w + 8, h + 8, body, label, css)


def ticker(theme, d):
    """Caution tape with your latest pushes scrolling across it, like a news ticker."""
    c = PALETTES[theme]
    h, size = 48, 12.5
    period, band = 36, h
    stripes = "".join(
        f'<polygon points="{x},0 {x + period / 2},0 {x + period / 2 - band},{band} {x - band},{band}" fill="{c["accent"]}"/>'
        for x in range(-period, W + 2 * period, period))
    body = (f'<rect width="{W}" height="{h}" fill="{c["ink"]}"/>'
            f'<svg width="{W}" height="{h}" overflow="hidden"><g class="tape">{stripes}</g></svg>')
    # the strip the text runs on
    sx, sy, sh_ = 172, 9, h - 18
    body += f'<rect x="{sx}" y="{sy}" width="{W - sx - 10}" height="{sh_}" fill="{c["ink"]}" stroke="{c["paper"]}" stroke-width="1.5"/>'
    base = sh_ / 2 + size * 0.36  # inside the strip's own <svg>
    items, x = "", 0.0
    pushes = [(repo, clean(msg), when) for repo, msg, when in d.get("pushes", [])]
    if not pushes:
        pushes = [("el", "quiet on main today. probably drawing lore instead", "")]
    for repo, msg, when in pushes:
        for part, color, bold, extra in ((repo, c["on_ink_accent"], True, ""), ("  " + msg, c["card"], False, ""),
                                         (("  " + short_ago(when)) if when else "", c["card"], False, ' opacity="0.6"'),
                                         ("   ■   ", c["accent"], True, "")):
            if part:
                items += text(part, x, base, size, color, mono=True, bold=bold, extra=extra)
                x += text_width(part, size, mono=True, bold=bold)
    loop = x
    speed = 45  # px per second
    body += (f'<svg x="{sx + 1}" y="{sy}" width="{W - sx - 12}" height="{sh_}" overflow="hidden">'
             f'<g class="run"><g transform="translate(10 0)">{items}</g><g transform="translate({loop + 10:.1f} 0)">{items}</g></g></svg>')
    # the label, pinned on the left like a sign on the tape
    body += (f'<rect x="16" y="11" width="146" height="{h - 18}" fill="{c["ink"]}"/>'
             f'<rect x="12" y="7" width="146" height="{h - 18}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
             f'<circle class="blink" cx="28" cy="{7 + (h - 18) / 2}" r="5" fill="{c["accent"]}"/>'
             + text("LATEST PUSHES", 40, 7 + (h - 18) / 2 + 4.5, 12.5, c["ink"], mono=True, bold=True))
    css = (f".tape{{animation:slide 2.4s linear infinite}}@keyframes slide{{to{{transform:translateX({period}px)}}}}"
           f".run{{animation:run {loop / speed:.1f}s linear infinite}}@keyframes run{{to{{transform:translateX(-{loop:.1f}px)}}}}"
           ".blink{animation:blink 1.2s steps(1) infinite}@keyframes blink{50%{opacity:.15}}")
    label = "Latest pushes: " + "; ".join(f"{r}: {m}" + (f" ({short_ago(w)})" if w else "") for r, m, w in pushes)
    return doc(W, h, body, label, css)


def clean(msg: str, limit: int = 64) -> str:
    """Plain ASCII-ish text that the outlined font can draw, cut to a ticker-friendly length."""
    msg = "".join(ch if 32 <= ord(ch) < 127 or ch == "·" else " " for ch in msg)
    msg = " ".join(msg.split())
    return msg if len(msg) <= limit else msg[: limit - 3].rstrip() + "..."


def short_ago(iso: str) -> str:
    return ago(iso).replace("pushed ", "")


if __name__ == "__main__":
    cfg = config()
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if "--sample" in sys.argv or not token:
        if "--sample" not in sys.argv:
            print("No PROFILE_TOKEN / GITHUB_TOKEN found: drawing sample numbers.", file=sys.stderr)
        d = sample(cfg)
    else:
        d = fetch(cfg, token)
    for theme in THEMES:
        write("stats", theme, stats_card(theme, d), "generated")
        write("streak", theme, streak_card(theme, d), "generated")
        write("year", theme, year_card(theme, d), "generated")
        write("ticker", theme, ticker(theme, d), "generated")
        for i, (repo, meta) in enumerate(d["cards"]):
            write(f"repo-{i + 1}", theme, repo_card(theme, repo, meta, i, cfg["user"]), "generated")
    # readme.py links the cards from this list, since the repos change from run to run
    (ROOT / "generated" / "building.json").write_text(json.dumps(
        [{"repo": m["repo"] if "/" in m["repo"] else f"{cfg['user']}/{m['repo']}", "upcoming": bool(m.get("upcoming"))}
         for _, m in d["cards"]], indent=2) + "\n", encoding="utf-8")
    cur, longest = streaks(d["days"])
    print(f"drew cards: {d['total']} contributions, streak {cur} (best {longest}), aura {aura(d)}, {len(d['cards'])} repo cards: " + ", ".join(m["repo"] for _, m in d["cards"]))
