"""Live cards, redrawn by the GitHub Action (.github/workflows/profile.yml).

    python scripts/live.py            # real data: needs PROFILE_TOKEN or GITHUB_TOKEN in the environment
    python scripts/live.py --sample   # made-up numbers, for previewing without a token

Writes generated/{stats,streak,year,ticker}-{light,dark}.svg, generated/repo-<n>-{light,dark}.svg
generated/activity.json (which repo each card shows, for readme.py)
and generated/live.json (the live About tiles, for art.py).
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
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from art import WEAPON_NAMES, WEAPONS, el_runner, runner_css
from lib.svgkit import MONO_ADV, PALETTES, ROOT, THEMES, config, doc, panel, text, text_width, write
from stack import logo, logos

W = 830
NOW = dt.datetime.now(dt.timezone.utc)


# ---------------------------------------------------------------- data

QUERY = """
query($login: String!) {
  user(login: $login) {
    id
    contributionsCollection {
      contributionYears
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
    history(first: 30) { nodes { messageHeadline parents { totalCount } author { user { login } } } }
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


# accounts that commit but aren't people: AI agents and automation (GitHub marks most bots itself)
NOT_PEOPLE = {"claude", "anthropic-claude", "copilot", "copilot-swe-agent", "github-copilot", "devin-ai-integration",
              "codex", "openai-codex", "cursoragent", "cursor-agent", "jules", "google-labs-jules", "sweep-ai",
              "dependabot", "renovate", "github-actions", "actions-user", "web-flow"}


def is_person(login: str, kind: str = "User", extra: set[str] = frozenset()) -> bool:
    """A real teammate: a User account that isn't a bot or an AI agent."""
    login = login.lower()
    return kind == "User" and not login.endswith("[bot]") and login not in NOT_PEOPLE | extra


def contributors(full_name: str, token: str, extra: set[str] = frozenset()) -> set[str] | None:
    """The people who have committed to the repo (GitHub's contributor list), bots and AI agents left out.
    None if GitHub won't say, e.g. a brand-new or empty repo."""
    req = urllib.request.Request(f"https://api.github.com/repos/{full_name}/contributors?per_page=100",
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "el-profile"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {u["login"].lower() for u in json.load(r) if is_person(u["login"], u.get("type", "User"), extra)}
    except Exception as e:  # 204 (empty repo), rate limit, network: fall back to the recent commits
        print(f"couldn't list contributors of {full_name} ({e})", file=sys.stderr)
        return None


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
    # your public repos, by latest push; the cards and the ticker come from these
    act = cfg.get("activity", {})
    skip = {x.lower() for x in act.get("skip", [])} | {user.lower()}
    not_people = {x.lower() for x in act.get("not_people", [])}  # more accounts to never count as teammates
    wanted = [r["name"] for r in d["recent"]["nodes"] if not r["isArchived"] and r["name"].lower() not in skip][:8]
    parts = [f'r{i}: repository(owner: {json.dumps(user)}, name: {json.dumps(name)}) {{{REPO_FIELDS % json.dumps(d["id"])}}}'
             for i, name in enumerate(wanted)]
    found = gql("query {" + "\n".join(parts) + "}", {}, token) if parts else {}
    looked_up = [r for r in (found.get(f"r{i}") for i in range(len(wanted))) if r]
    for repo in looked_up[: act.get("cards", 4)]:
        repo["crew"] = contributors(repo["nameWithOwner"], token, not_people)
    # lifetime commits: GitHub only counts a year at a time, so ask for every year you've been active
    years = cc.get("contributionYears") or []
    per_year = gql("query($login: String!) { user(login: $login) {" + "".join(
        f' y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z")'
        " { totalCommitContributions restrictedContributionsCount }" for y in years) + " } }",
        {"login": user}, token).get("user") or {} if years else {}
    lifetime = sum(v["totalCommitContributions"] + v["restrictedContributionsCount"] for v in per_year.values())
    return dict(
        days=[(x["date"], x["contributionCount"]) for x in days],
        total=cc["contributionCalendar"]["totalContributions"],
        commits=cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        prs=d["pullRequests"]["totalCount"], issues=d["issues"]["totalCount"],
        contributed=d["repositoriesContributedTo"]["totalCount"], stars=stars,
        langs=langs, cards=looked_up[: act.get("cards", 4)], lifetime=lifetime,
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


def people(repo: dict) -> set[str]:
    """Who worked on the repo, bots left out. Tells solo work from team work: everyone GitHub lists
    as a contributor, or, if it couldn't say, whoever committed to the default branch lately."""
    if repo.get("crew") is not None:
        return repo["crew"]
    nodes = ((((repo.get("defaultBranchRef") or {}).get("target") or {}).get("history") or {}).get("nodes")) or []
    logins = {(((n.get("author") or {}).get("user") or {}).get("login") or "").lower() for n in nodes}
    return {x for x in logins if x and is_person(x)}


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
    # (repo, language, hours since the push, latest commit, description, people)
    fake = [("Merlin", ("TypeScript", "#3178c6"), 2, "fix(fire): steadier flame flicker",
             "AI desktop companion: a flaming skull mage who lives on your desktop.", 1),
            ("my-portfolio", ("Astro", "#ff5a03"), 9, "feat(aura): El splits the rock", "My developer portfolio", 1),
            ("Ka-dugo", ("JavaScript", "#f1e05a"), 30, "docs: README with screenshots", None, 4),
            ("ThriftBite", ("Java", "#b07219"), 50, "docs: rewrite the README as a front page",
             "Surplus-food marketplace for Baguio.", 1),
            ("team-capstone", ("Python", "#3572A5"), 120, "feat(api): pickup time slots", "A team project for class", 5)]
    u = cfg["user"]
    recent = [dict(name=n, nameWithOwner=f"{u}/{n}", description=desc, url=f"https://github.com/{u}/{n}",
                   isPrivate=False, owner={"login": u}, pushedAt=(NOW - dt.timedelta(hours=h)).isoformat(),
                   primaryLanguage={"name": lang, "color": col},
                   defaultBranchRef={"target": {"history": {"nodes": [
                       {"messageHeadline": msg if k == 0 else "wip", "parents": {"totalCount": 1},
                        "author": {"user": {"login": u if k == 0 else f"mate{k}"}}} for k in range(ppl)]}}})
              for n, (lang, col), h, msg, desc, ppl in fake]
    pushes = [(n, msg, (NOW - dt.timedelta(hours=h)).isoformat()) for n, _, h, msg, _, _ in fake]
    return dict(lifetime=720, pushes=pushes, days=days, total=sum(c for _, c in days), commits=412, prs=37, issues=12, contributed=6, stars=9,
                langs=langs, cards=recent[: cfg.get("activity", {}).get("cards", 4)])


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


# aura ranks by lifetime commits: (lowest count, grade, title)
RANKS = ((0, "E", "Just spawned"), (50, "D", "Warming up"), (250, "C", "Climbing"), (1_000, "B", "Rising star"),
         (5_000, "A", "Elite"), (10_000, "S", "Legend"), (50_000, "SS", "Mythic"), (100_000, "SSS", "Transcendent"),
         (1_000_000, "EX", "Beyond the scale"))


def rank(d) -> tuple[str, str, float, int, str]:
    """(grade, title, progress through this grade 0..1, commits to the next grade, next grade)."""
    n = d.get("lifetime", 0)
    i = max(k for k, (cut, _, _) in enumerate(RANKS) if n >= cut)
    cut, grade, title = RANKS[i]
    if i == len(RANKS) - 1:
        return grade, title, 1.0, 0, ""
    nxt_cut, nxt, _ = RANKS[i + 1]
    return grade, title, (n - cut) / (nxt_cut - cut), nxt_cut - n, nxt


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


def sh(x, y, w, h, color):
    """Solid comic offset shadow."""
    return f'<rect x="{x + 6}" y="{y + 6}" width="{w}" height="{h}" fill="{color}"/>'


# ---------------------------------------------------------------- cards

def segs(c, x, y, filled, n=10, seg=11.0, gap=3.0, h=8, color=None):
    """The portfolio's power bar: filled blocks, then hollow ones."""
    out = ""
    for i in range(n):
        if i < filled:
            out += f'<rect x="{x + i * (seg + gap):.1f}" y="{y}" width="{seg}" height="{h}" fill="{color or c["ink"]}"/>'
        else:
            out += (f'<rect x="{x + i * (seg + gap) + 0.5:.1f}" y="{y + 0.5}" width="{seg - 1}" height="{h - 1}" fill="none" '
                    f'stroke="{c["ink"]}" stroke-width="1" opacity="0.35"/>')
    return out


def stats_card(theme, d):
    c = PALETTES[theme]
    pw, ph = 400, 232  # two panels + the gap + a 6px shadow must fit inside W
    # left: aura rank, how close the next one is, and the numbers behind it
    body = sh(0, 0, pw, ph, c["accent"]) + panel_plain(c, 0, 0, pw, ph, "~/el/power-level")
    g, title, prog, need, nxt = rank(d)
    bx, by = 70, 92
    pts = " ".join(f"{bx + (48 if i % 2 == 0 else 26) * math.cos(i * math.pi / 8 - math.pi / 2):.1f},"
                   f"{by + (48 if i % 2 == 0 else 26) * math.sin(i * math.pi / 8 - math.pi / 2):.1f}" for i in range(16))
    body += (f'<polygon class="burst" points="{pts}" fill="{c["accent"]}" stroke="{c["ink"]}" stroke-width="3" stroke-linejoin="round"/>'
             + text(g, bx, by + 10, {1: 30, 2: 26, 3: 20}.get(len(g), 20), c["white"], wght=700, wdth=70, anchor="middle")
             + text("AURA", bx, by + 25, 8.5, c["white"], wght=700, ls=1, anchor="middle"))
    body += text(f"AURA RANK · {d.get('lifetime', 0):,} LIFETIME COMMITS", 138, 58, 10.5, c["muted"], mono=True, bold=True, ls=1)
    body += text(title, 138, 88, 28, c["ink"], wght=700, wdth=70)
    body += segs(c, 138, 100, round(prog * 10), seg=13, gap=3.5, h=9, color=c["accent"])
    body += text(f"{need:,} commits to rank {nxt}" if nxt else "Off the scale. Nothing left to rank", 138, 126, 11.5, c["muted"], wght=500)
    # the numbers, in two labelled groups
    groups = [("PAST YEAR", [(d["commits"], "COMMITS"), (d["prs"], "PULL REQS"), (d["issues"], "ISSUES")]),
              ("AROUND GITHUB", [(d["stars"], "STARS"), (d["contributed"], "OTHER REPOS")])]
    n = sum(len(g) for _, g in groups)
    tw = (pw - 6) / n
    top = 146
    body += f'<rect x="3" y="{top}" width="{pw - 6}" height="{ph - top - 3}" fill="{c["ink"]}"/>'
    i = 0
    for gi, (title_g, items) in enumerate(groups):
        gx = 3 + tw * i
        if gi:
            body += f'<line x1="{gx:.1f}" y1="{top + 10}" x2="{gx:.1f}" y2="{ph - 12}" stroke="{c["card"]}" stroke-width="2" opacity="0.5"/>'
        body += text(title_g, gx + 14, top + 20, 9, c["on_ink_accent"], mono=True, bold=True, ls=1)
        for v, k in items:
            cx = 3 + tw * i + tw / 2
            if i and items[0][1] != k:
                body += f'<line x1="{3 + tw * i:.1f}" y1="{top + 34}" x2="{3 + tw * i:.1f}" y2="{ph - 14}" stroke="{c["card"]}" stroke-width="1" opacity="0.2"/>'
            body += text(f"{v:,}", cx, top + 58, 26, c["card"], wght=700, wdth=70, anchor="middle")
            body += text(k, cx, top + 76, 8.5, c["card"], mono=True, bold=True, ls=0.5, anchor="middle", extra=' opacity="0.7"')
            i += 1
    # right: languages as power bars, with their logos
    x0 = pw + 22
    body += sh(x0, 0, pw, ph, c["ink"]) + panel_plain(c, x0, 0, pw, ph, "~/el/languages")
    total = sum(v for v, _ in d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1][0])[:5]
    lead = top[0][1][0] / total if top else 1
    L = logos()
    for i, (n, (v, col)) in enumerate(top):
        y = 58 + i * 34
        share = v / total
        lg = L.get(n)
        if lg:
            body += logo(lg, x0 + 18, y - 13, 16, c["ink"])
        else:
            body += f'<circle cx="{x0 + 26}" cy="{y - 5}" r="6" fill="{col}" stroke="{c["ink"]}" stroke-width="1.5"/>'
        body += text(fit(n, 14, 108, wght=700), x0 + 42, y, 14, c["ink"], wght=700)
        body += segs(c, x0 + 160, y - 10, max(1, round(share / lead * 10)), seg=14, gap=3.5, h=10, color=col)
        body += text(f"{share * 100:.0f}%", x0 + pw - 18, y, 13, c["ink"], wght=700, anchor="end")
    body += text("Share of code across my repos. Top language fills the bar.", x0 + 18, ph - 12, 10, c["muted"], wght=400)
    label = (f"Power level: aura rank {g} ({title}) from {d.get('lifetime', 0)} lifetime commits, {d['commits']} commits in the past year, {d['prs']} pull requests, "
             f"{d['issues']} issues, {d['stars']} stars, contributed to {d['contributed']} repos. Top languages: "
             + ", ".join(f"{n} {v / total * 100:.0f}%" for n, (v, _) in top))
    css = (f".burst{{transform-origin:{bx}px {by}px;animation:spin 24s linear infinite}}"
           "@keyframes spin{to{transform:rotate(360deg)}}")
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
    body = sh(0, 0, W - 8, h, c["accent"]) + f'<rect x="0" y="0" width="{W - 8}" height="{h}" fill="{c["ink"]}"/>'
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


def weapon_of_the_day(cfg: dict) -> str:
    """One weapon per weekday, in your time zone: greatsword on Monday through the keyboard on Sunday."""
    return list(WEAPONS)[dt.datetime.now(ZoneInfo(cfg.get("timezone", "Asia/Manila"))).weekday()]


def year_card(theme, d, weapon="sword", cfg=None):
    c = PALETTES[theme]
    days = d["days"]
    first = dt.date.fromisoformat(days[0][0])
    pad = (first.weekday() + 1) % 7          # GitHub weeks start on Sunday
    cells = [None] * pad + days
    weeks = math.ceil(len(cells) / 7)
    mx = max((n for _, n in days), default=1) or 1
    cs, gap = 11, 3
    gx, gy = 40, 96
    gw = weeks * (cs + gap) - gap
    gh = 7 * (cs + gap)
    h = gy + gh + 40
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
    # El runs side-on along the top into a headwind, greatsword on his shoulder, clearing the fog behind him.
    # A portal opens past the last week; he runs into it and comes out of a second one at the start.
    T, ground = 14, gy - 6
    pin, pout = gx - 18, gx + gw + 16       # the two portals: in at the start, out at the end
    x0, x1 = pin - 30, pout + 75            # he starts hidden behind the start portal and runs until he's fully through
    run = 90                                # % of the loop he spends running; the rest he's between portals
    fx0 = pin + 6                           # the fog's left edge trails just behind his feet
    body += (f'<line x1="{gx - 4}" y1="{ground}" x2="{gx + gw + 4}" y2="{ground}" stroke="{c["ink"]}" stroke-width="2" '
             f'stroke-dasharray="2 6" opacity="0.35"/>')

    def portal(cls, px):
        cy, ry = ground - 30, 34
        swirl = "".join(f'<path d="M0 {-r} A{r} {r} 0 0 1 {r * 0.87:.1f} {r * 0.5:.1f}" fill="none" stroke="{col}" '
                        f'stroke-width="{sw}" stroke-linecap="round"/>'
                        for r, col, sw in ((ry - 8, c["accent"], 4), (ry - 17, c["ink"], 2.5), (ry - 25, c["accent"], 3)))
        return (f'<g transform="translate({px} {cy})"><g class="{cls}">'
                f'<ellipse rx="13" ry="{ry}" fill="{c["accent"]}" opacity="0.22"/>'
                f'<g transform="scale(0.36 1)"><g class="spin">{swirl}'
                f'<g transform="rotate(180)">{swirl}</g></g></g>'
                f'<ellipse rx="13" ry="{ry}" fill="none" stroke="{c["ink"]}" stroke-width="3"/></g></g>')

    # the headwind: streaks blowing in from where he's heading
    winds = ""
    for y, ln, dur, dl, curl in ((ground - 62, 34, 1.7, 0.0, False), (ground - 44, 22, 1.3, 0.5, False),
                                                 (ground - 28, 40, 1.9, 1.1, True), (ground - 12, 18, 1.1, 0.3, False),
                                                 (ground - 52, 26, 1.5, 0.9, True), (ground - 20, 30, 1.6, 1.4, False)):
        tail = " c-9 0 -9 -11 -1 -11" if curl else ""
        winds += (f'<path class="w" style="animation-duration:{dur}s;animation-delay:-{dl}s" '
                  f'd="M{W - 10} {y} h-{ln}{tail}" fill="none" stroke="{c["ink"]}" stroke-width="2" stroke-linecap="round"/>')

    body += (f'<clipPath id="yc"><rect x="3" y="29" width="{W - 20}" height="{h - 32}"/></clipPath>'
             f'<clipPath id="yp"><rect x="{pin}" y="0" width="{pout - pin}" height="{ground + 6}"/></clipPath>'
             f'<g clip-path="url(#yc)">'
             f'<g class="fog"><rect x="{fx0}" y="{gy - 2}" width="{gw + 90}" height="{gh + 2}" fill="{c["paper"]}" opacity="0.8"/></g>'
             f'<g opacity="0.28">{winds}</g>'
             f'<g clip-path="url(#yp)"><g class="elmove"><g transform="translate({x0} {ground})">'
             f'<g transform="scale(0.4)">{el_runner(c, "e", weapon)}</g></g></g></g>'
             + portal("pIn", pin) + portal("pOut", pout) + '</g>')
    dx, fdx = x1 - x0, x1 - x0 - 40
    css = (runner_css("e")
           + f".elmove,.fog{{animation:{T}s linear infinite}}.elmove{{animation-name:move}}.fog{{animation-name:fog}}"
           f"@keyframes move{{0%{{transform:translateX(0)}}{run}%,100%{{transform:translateX({dx}px)}}}}"
           f"@keyframes fog{{0%{{transform:translateX(0);opacity:1}}{run - 4}%{{transform:translateX({fdx}px);opacity:1}}"
           f"{run + 3}%{{transform:translateX({fdx}px);opacity:0}}{run + 3.1}%{{transform:translateX(0);opacity:0}}100%{{transform:translateX(0);opacity:1}}}}"
           # the portals open just before he needs them and close once he's through
           f".pIn,.pOut{{transform-box:fill-box;transform-origin:50% 50%;animation:{T}s ease-in-out infinite}}"
           f".pIn{{animation-name:pIn}}.pOut{{animation-name:pOut}}"
           f"@keyframes pIn{{0%,6%{{transform:scale(1)}}12%,94%{{transform:scale(0,0.6)}}99%,100%{{transform:scale(1)}}}}"
           f"@keyframes pOut{{0%,66%{{transform:scale(0,0.6)}}73%,{run + 1}%{{transform:scale(1)}}{run + 6}%,100%{{transform:scale(0,0.6)}}}}"
           f".spin{{transform-box:fill-box;transform-origin:50% 50%;animation:spin 1.4s linear infinite}}"
           f"@keyframes spin{{to{{transform:rotate(-360deg)}}}}"
           f".w{{animation:wind linear infinite}}"
           f"@keyframes wind{{0%{{transform:translateX(0);opacity:0}}12%{{opacity:1}}85%{{opacity:1}}100%{{transform:translateX(-{W - 40}px);opacity:0}}}}"
           f"@media (prefers-reduced-motion:reduce){{.elmove{{transform:translateX({dx // 2}px)}}.fog,.w{{opacity:0}}}}")
    day = dt.datetime.now(ZoneInfo(cfg.get("timezone", "Asia/Manila"))).strftime("%A").lower() if cfg else "today"
    body += text(f"{day}'s weapon: {WEAPON_NAMES.get(weapon, weapon)}", W - 14 - 18, h - 12, 10.5, c["muted"], mono=True, anchor="end")
    label = (f"Contribution graph for the past year, {d['total']} contributions. "
             f"El runs across it into the wind with his {WEAPON_NAMES.get(weapon, weapon)} on his shoulder, clearing the fog, and loops back through a portal.")
    return doc(W, h + 14, body, label, css)


def repo_card(theme, repo, i, user):
    """One recent repo, drawn only from what GitHub knows: its About text, language,
    latest commit, last push, and whether anyone else commits to it."""
    c = PALETTES[theme]
    w, h = 404, 176
    shadow = c["accent"] if i == 0 else c["ink"]
    body = sh(0, 0, w, h, shadow)
    body += f'<rect x="1.25" y="1.25" width="{w - 2.5}" height="{h - 2.5}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
    name = repo["name"]
    desc = repo.get("description") or ""
    pl = repo.get("primaryLanguage") or {}
    lang, color = pl.get("name", ""), pl.get("color") or c["muted"]
    commits = ((((repo.get("defaultBranchRef") or {}).get("target") or {}).get("history") or {}).get("nodes")) or []
    # skip merge commits ("Merge pull request #2 from ..."): show the last real message
    real = [n for n in commits if (n.get("parents") or {}).get("totalCount", 1) <= 1]
    msg = (real or commits or [{}])[0].get("messageHeadline", "")
    when = ago(repo["pushedAt"]) if repo.get("pushedAt") else ""
    others = len(people(repo) - {user.lower()})
    tag = "Private" if repo.get("isPrivate") else ("Team" if others else "Solo")
    crew = f"you + {others} other{'s' if others > 1 else ''}" if others else ""
    name_s = fit(name, 16, w - 120, wght=700)
    body += text(name_s, 18, 32, 16, c["accent"], wght=700)
    tx = 18 + text_width(name_s, 16, 700) + 10
    tw = text_width(tag, 11.5, 500) + 16
    body += f'<rect x="{tx:.1f}" y="18" width="{tw:.1f}" height="19" rx="9.5" fill="none" stroke="{c["muted"]}" stroke-width="1"/>'
    body += text(tag, tx + tw / 2, 31.5, 11.5, c["muted"], wght=500, anchor="middle")
    if desc:
        for j, line in enumerate(wrap(desc, 13, w - 36, 2, wght=400)):
            body += text(line, 18, 60 + j * 19, 13, c["ink"], wght=400)
    else:
        # the text comes from the repo's About box, so an empty one shows here
        body += text("No description yet.", 18, 60, 13, c["muted"], wght=400)
    if msg:
        body += f'<rect x="18" y="98" width="{w - 36}" height="26" fill="{c["ink"]}"/>'
        body += text("$", 28, 115.5, 11.5, c["on_ink_accent"], mono=True, bold=True)
        m = fit(f'git commit -m "{clean(msg, 200)}"', 11.5, w - 36 - 34, mono=True)
        if not m.endswith('"'):
            m = m.rstrip("…") + '…"'
        body += text(m, 28 + 11.5 * MONO_ADV * 2, 115.5, 11.5, c["card"], mono=True)
    y = 152
    if lang:
        body += f'<circle cx="24" cy="{y - 4}" r="5.5" fill="{color}"/>' + text(lang, 36, y, 12, c["muted"], wght=500)
    rx = 36 + (text_width(lang, 12, 500) + 18 if lang else -18)
    body += text(crew, rx, y, 12, c["muted"], wght=500)
    body += text(when, w - 18, y, 12, c["muted"], wght=500, anchor="end")
    css = ""
    if repo.get("pushedAt") and NOW - dt.datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00")) < dt.timedelta(hours=24):
        # pushed in the last day: a pulsing LIVE dot before the time
        lx = w - 18 - text_width(when, 12, 500) - 12
        body += (f'<circle class="ping" cx="{lx:.1f}" cy="{y - 4}" r="4.5" fill="none" stroke="{c["accent"]}" stroke-width="2"/>'
                 f'<circle cx="{lx:.1f}" cy="{y - 4}" r="4.5" fill="{c["accent"]}"/>')
        css = (".ping{transform-box:fill-box;transform-origin:center;animation:ping 1.6s ease-out infinite}"
               "@keyframes ping{from{transform:scale(1);opacity:.9}to{transform:scale(2.6);opacity:0}}")
        when = "live, " + when
    label = f"{name} ({tag}): {desc or 'no description yet'}. {lang}. {crew}. {when}. Latest commit: {msg}"
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


def live_tiles(d) -> dict:
    """Values for the About tiles that fill themselves: what you pushed last, and your week."""
    tiles = {}
    if d["cards"]:
        r = d["cards"][0]
        tiles["latest_repo"] = {"value": r["name"], "note": r.get("description") or ago(r["pushedAt"]).capitalize()}
    week = d["days"][-7:]
    n, active = sum(c for _, c in week), sum(1 for _, c in week if c)
    tiles["this_week"] = ({"value": f"{n} contribution{'s' if n != 1 else ''}",
                           "note": "Active every day this week" if active == 7 else f"Active {active} of the last 7 days"} if n
                          else {"value": "Recharging", "note": "Nothing pushed in the last 7 days"})
    return tiles


if __name__ == "__main__":
    cfg = config()
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if "--sample" in sys.argv or not token:
        if "--sample" not in sys.argv:
            print("No PROFILE_TOKEN / GITHUB_TOKEN found: drawing sample numbers.", file=sys.stderr)
        d = sample(cfg)
    else:
        d = fetch(cfg, token)
    weapon = weapon_of_the_day(cfg)
    for theme in THEMES:
        write("stats", theme, stats_card(theme, d), "generated")
        write("streak", theme, streak_card(theme, d), "generated")
        write("year", theme, year_card(theme, d, weapon, cfg), "generated")
        write("ticker", theme, ticker(theme, d), "generated")
        for i, repo in enumerate(d["cards"]):
            write(f"repo-{i + 1}", theme, repo_card(theme, repo, i, cfg["user"]), "generated")
    # readme.py links the cards from this list, since the repos change from run to run
    (ROOT / "generated" / "activity.json").write_text(
        json.dumps([r["nameWithOwner"] for r in d["cards"]], indent=2) + "\n", encoding="utf-8")
    # art.py fills the live About tiles from this
    (ROOT / "generated" / "live.json").write_text(json.dumps(live_tiles(d), indent=2) + "\n", encoding="utf-8")
    cur, longest = streaks(d["days"])
    print(f"drew cards: {d['total']} contributions, streak {cur} (best {longest}), rank {rank(d)[0]}, {len(d['cards'])} repo cards: " + ", ".join(r["name"] for r in d["cards"]))
