"""The Stack cards, drawn from the portfolio's /stack.json, so the stack is written once
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.svgkit import PALETTES, ROOT, THEMES, Glyphs, config, doc, text as outline, write

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


def logo(entry: dict | None, x: float, y: float, size: float, color: str) -> str:
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


# ---------------------------------------------------------------- the grid

def names(area: dict) -> list[str]:
    """Everything in one area of the portfolio's stack, in its order."""
    out = [sk["name"] for sk in area.get("skills", [])] + [i["text"] for i in area.get("items", [])]
    for g in area.get("groups", []):
        out += g["items"]
    return out


def groups(data: dict) -> list[tuple[str, str, list[str], bool]]:
    """(title, the portfolio's area icon, logo names, full width?) per card: languages,
    frontend, backend and data as a 2×2 grid, then tools and design across the bottom."""
    areas = {a["id"]: a for a in data["areas"]}
    L = data.get("logos", {})
    cards = []
    for key in ("languages", "web", "backend", "data"):
        a = areas.get(key)
        if a:
            cards.append((a["title"], a.get("icon", ""), [n for n in names(a) if n in L], False))
    bottom = [areas[k] for k in ("tools", "design") if k in areas]
    if bottom:
        cards.append((" & ".join(a["title"].split(" &")[0] for a in bottom), bottom[0].get("icon", ""),
                      [n for a in bottom for n in names(a) if n in L], True))
    # languages: only the ones with a level, the "Others" row would crowd it
    if cards and "languages" in areas:
        lv = [sk["name"] for sk in areas["languages"].get("skills", []) if sk["name"] in L]
        cards[0] = (cards[0][0], cards[0][1], lv, False)
    return cards


def stack_grid(theme: str, data: dict) -> str:
    global BOOK
    BOOK = Glyphs(f"{theme[0]}g")
    c = PALETTES[theme]
    L = data.get("logos", {})
    gap, sh = 18, 6
    half = (W - sh - gap) / 2
    tile, tgap, pad = 38, 8, 16
    body, label = "", []
    x = y = 0.0
    row_h = 0.0
    for title, icon, items, full in groups(data):
        w = W - sh if full else half
        per_row = max(1, int((w - 2 * pad + tgap) // (tile + tgap)))
        rows = (len(items) + per_row - 1) // per_row
        h = 30 + pad + rows * (tile + tgap) - tgap + pad
        if full or x + w > W - sh + 1:
            x, y = 0.0, y + (row_h + gap if row_h else 0)
            row_h = 0.0
        # the card: offset shadow, paper body, ink header with the area's own icon
        body += (f'<rect x="{x + sh}" y="{y + sh}" width="{w}" height="{h}" fill="{c["ink"]}"/>'
                 f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{w - 3}" height="{h - 3}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
                 f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="{c["ink"]}"/>'
                 f'<g transform="translate({x + 12} {y + 6}) scale(0.5625)" fill="none" stroke="{c["paper"]}" stroke-width="3" '
                 f'stroke-linecap="square" stroke-linejoin="miter">{icon}</g>'
                 + text(title.upper(), x + 40, y + 20, 12, c["paper"], mono=True, bold=True, ls=1)
                 + text(str(len(items)), x + w - 14, y + 20, 12, c["on_ink_accent"], mono=True, bold=True, anchor="end"))
        for i, name in enumerate(items):
            r, col = divmod(i, per_row)
            in_row = min(per_row, len(items) - r * per_row)
            left = x + (w - (in_row * (tile + tgap) - tgap)) / 2  # each row centred in its card
            tx = left + col * (tile + tgap)
            ty = y + 30 + pad + r * (tile + tgap)
            body += (f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{tile}" height="{tile}" rx="7" fill="{c["ink"]}"/>'
                     + logo(L.get(name), tx + 9, ty + 9, tile - 18, c["paper"]))
        label.append(f"{title}: {', '.join(items)}")
        row_h = max(row_h, h)
        x = 0.0 if full else x + w + gap
        if full:
            y, row_h = y + h + gap, 0.0
    total = y + row_h if row_h else y - gap
    return doc(W, total + sh, BOOK.defs() + body, "Stack. " + "; ".join(label))


if __name__ == "__main__":
    cfg = config()
    data = load(cfg)
    if not data:
        print("no stack.json yet: skipping the Stack panel", file=sys.stderr)
        sys.exit(0)
    for theme in THEMES:
        p = write("stack", theme, stack_grid(theme, data), "generated")
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")
