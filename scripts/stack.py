"""The Stack panel, drawn from the portfolio's /stack.json, so the stack is written once
(in the portfolio's src/data/profile.ts) and the profile follows it.

    python scripts/stack.py                   # fetch <portfolio>/stack.json, then draw
    python scripts/stack.py --from file.json  # draw from a saved copy, for previewing

Writes generated/stack.json (the last good copy, used when the site can't be reached)
and generated/stack-{light,dark}.svg. Runs before live.py, which borrows the logos.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.svgkit import PALETTES, ROOT, THEMES, Glyphs, config, doc, panel, text as outline, text_width, write

W = 830
BOOK: Glyphs | None = None  # set per image: the panel repeats a lot of letters, so each is outlined once
CACHE = ROOT / "generated" / "stack.json"


# ---------------------------------------------------------------- data

def load(cfg: dict) -> dict | None:
    if "--from" in sys.argv:
        return json.loads(Path(sys.argv[sys.argv.index("--from") + 1]).read_text(encoding="utf-8"))
    url = cfg["links"]["portfolio"].rstrip("/") + "/stack.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "el-profile"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return data
    except Exception as e:  # the site is down or moved: keep the last good copy
        print(f"couldn't fetch {url} ({e}); using the saved copy", file=sys.stderr)
        return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else None


def logos() -> dict:
    """Logos by name from the saved stack.json, for other cards (live.py's languages)."""
    return json.loads(CACHE.read_text(encoding="utf-8")).get("logos", {}) if CACHE.exists() else {}


# ---------------------------------------------------------------- parts

def text(*args, **kw) -> str:
    return outline(*args, book=BOOK, **kw)


def logo(c: dict, entry: dict | None, x: float, y: float, size: float, color: str) -> str:
    """A Simple Icons logo (24×24 path) or a lettered tile, with its top-left at x, y."""
    if not entry:
        return ""
    if "path" in entry:
        k = size / 24
        return f'<path transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" d="{entry["path"]}" fill="{color}"/>'
    t = entry["tile"]
    fs = size * (0.42 if len(t) > 2 else 0.5)
    return (f'<rect x="{x + 0.75:.1f}" y="{y + 0.75:.1f}" width="{size - 1.5:.1f}" height="{size - 1.5:.1f}" fill="none" stroke="{color}" stroke-width="1.5"/>'
            + text(t, x + size / 2, y + size / 2 + fs * 0.36, fs, color, mono=True, bold=True, anchor="middle"))


def area_icon(c: dict, markup: str, x: float, y: float, size: float) -> str:
    """The portfolio's hand-drawn area icon, inside an outlined box."""
    k = (size - 12) / 32
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="{c["ink"]}" stroke-width="2"/>'
            f'<g transform="translate({x + 6} {y + 6}) scale({k:.4f})" fill="none" stroke="{c["ink"]}" stroke-width="2.6" '
            f'stroke-linecap="square" stroke-linejoin="miter">{markup}</g>')


def segbar(c: dict, x: float, y: float, level: float, out_of: int = 10, seg: float = 11, gap: float = 3, h: float = 8) -> str:
    """The portfolio's power bar: filled blocks for the level, hollow for the rest."""
    s = ""
    for i in range(out_of):
        on = i < round(level)
        s += (f'<rect x="{x + i * (seg + gap):.1f}" y="{y}" width="{seg}" height="{h}" '
              + (f'fill="{c["ink"]}"/>' if on else f'fill="none" stroke="{c["ink"]}" stroke-width="1" opacity="0.35"/>'))
    return s


def fit(s: str, size: float, max_w: float, **kw) -> str:
    if text_width(s, size, **kw) <= max_w:
        return s
    while s and text_width(s + "…", size, **kw) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


# ---------------------------------------------------------------- the panel

def stack_card(theme: str, data: dict) -> str:
    global BOOK
    BOOK = Glyphs(f"{theme[0]}g")
    c = PALETTES[theme]
    L = data.get("logos", {})
    areas = {a["id"]: a for a in data["areas"]}
    pw = W - 14
    body, y = "", 44
    label = []

    # Languages: power bars, two columns
    langs = areas.get("languages")
    if langs:
        body += area_icon(c, langs.get("icon", ""), 18, y, 34)
        body += text(langs["title"], 64, y + 16, 19, c["ink"], wght=700, wdth=70)
        body += text(langs["line"], 64, y + 31, 11.5, c["muted"], wght=400)
        body += text("Bars: how confident I am, out of 10", pw - 18, y + 31, 11, c["muted"], wght=400, anchor="end")
        y += 52
        cw = (pw - 36 - 24) / 2
        skills = langs.get("skills", [])
        for i, s in enumerate(skills):
            col, row = i % 2, i // 2
            x = 18 + col * (cw + 24)
            ry = y + row * 44
            body += logo(c, L.get(s["name"]), x, ry + 2, 18, c["ink"])
            body += text(s["name"], x + 26, ry + 16, 15, c["ink"], wght=700)
            bx = x + 140
            body += segbar(c, bx, ry + 6, s["level"])
            body += text(f'{s["level"]}/10', x + cw, ry + 14, 12, c["ink"], wght=700, anchor="end")
            body += text(fit(s["note"], 11, cw - 140, wght=400), bx, ry + 30, 11, c["muted"], wght=400)
            label.append(f'{s["name"]} {s["level"]}/10')
        y += ((len(skills) + 1) // 2) * 44
        others = [g for g in langs.get("groups", []) if g.get("iconsOnly")]
        for g in others:
            body += text(g["label"].upper(), 18, y + 19, 10.5, c["muted"], mono=True, bold=True, ls=1)
            x = 92
            for name in g["items"]:
                body += (f'<rect x="{x}" y="{y + 3}" width="26" height="26" fill="none" stroke="{c["ink"]}" stroke-width="1.5" opacity="0.5"/>'
                         + logo(c, L.get(name), x + 5, y + 8, 16, c["ink"]))
                x += 32
            label.append(g["label"] + ": " + ", ".join(g["items"]))
            y += 36
        body += f'<line x1="18" y1="{y + 6}" x2="{pw - 18}" y2="{y + 6}" stroke="{c["ink"]}" stroke-width="1.5" opacity="0.25"/>'
        y += 20

    # The other areas: three to a row, each with its logos
    rest = [a for a in data["areas"] if a["id"] != "languages"]
    cols, gap = 3, 14
    aw = (pw - 36 - gap * (cols - 1)) / cols
    for r in range(0, len(rest), cols):
        row_h = 0
        for j, a in enumerate(rest[r:r + cols]):
            x = 18 + j * (aw + gap)
            part, h = area(c, a, L, x, y, aw)
            body += part
            row_h = max(row_h, h)
            names = [i["text"] for i in a.get("items", [])] + [s["name"] for s in a.get("skills", [])] \
                + [f'{g["label"]}: {", ".join(g["items"])}' for g in a.get("groups", [])]
            label.append(f'{a["title"]}: {", ".join(names)}')
        y += row_h + 18
    h = y + 4
    out = BOOK.defs() + panel(c, 0, 0, pw, h, "~/el/stack.json", f"{len(data['areas'])} areas", uid="st") + body
    return doc(W, h + 14, out, "Stack. " + "; ".join(label))


def area(c: dict, a: dict, L: dict, x: float, y: float, w: float) -> tuple[str, float]:
    """One stack area: icon, title, line, then its logos, skills and labelled groups."""
    s = area_icon(c, a.get("icon", ""), x, y, 30)
    s += text(fit(a["title"], 16, w - 40, wght=700, wdth=70), x + 40, y + 14, 16, c["ink"], wght=700, wdth=70)
    s += text(fit(a["line"], 10.5, w - 40, wght=400), x + 40, y + 28, 10.5, c["muted"], wght=400)
    yy = y + 46
    items = [i["text"] for i in a.get("items", [])]
    half = (w - 8) / 2
    for k, name in enumerate(items):
        col, row = k % 2, k // 2
        ix, iy = x + col * half, yy + row * 22
        s += logo(c, L.get(name), ix, iy, 14, c["ink"])
        s += text(fit(name, 12.5, half - 26, wght=600), ix + 20, iy + 11.5, 12.5, c["ink"], wght=600)
    yy += ((len(items) + 1) // 2) * 22
    for sk in a.get("skills", []):
        s += logo(c, L.get(sk["name"]), x, yy, 14, c["ink"])
        s += text(sk["name"], x + 20, yy + 11.5, 12.5, c["ink"], wght=600)
        s += segbar(c, x + half, yy + 3, sk["level"], seg=7, gap=2.5, h=7)
        s += text(f'{sk["level"]}/10', x + w, yy + 11, 11, c["ink"], wght=700, anchor="end")
        yy += 24
    for g in a.get("groups", []):
        s += text(g["label"].upper(), x, yy + 10, 9.5, c["muted"], mono=True, bold=True, ls=1)
        yy += 16
        has_logos = any(L.get(n) for n in g["items"])
        if has_logos:
            ix = x
            for name in g["items"]:
                iw = 20 + text_width(name, 11.5, 500) + 12
                if ix + iw > x + w and ix > x:
                    ix, yy = x, yy + 20
                pad = 18 if L.get(name) else 0
                s += logo(c, L.get(name), ix, yy, 13, c["ink"]) + text(name, ix + pad, yy + 10.5, 11.5, c["ink"], wght=500)
                ix += iw - (18 - pad)
            yy += 24
        else:
            for name in g["items"]:
                s += text(fit(name, 12, w, wght=600), x, yy + 10, 12, c["ink"], wght=600)
                yy += 18
            yy += 6
    return s, yy - y


if __name__ == "__main__":
    cfg = config()
    data = load(cfg)
    if not data:
        print("no stack.json yet: skipping the Stack panel", file=sys.stderr)
        sys.exit(0)
    for theme in THEMES:
        p = write("stack", theme, stack_card(theme, data), "generated")
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")
