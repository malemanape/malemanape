"""The Stack icon strip, drawn from the portfolio's /stack.json, so the stack is written once
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


# ---------------------------------------------------------------- the strip

def rows(data: dict) -> list[list[str]]:
    """Two rows, like the old icon strip: the languages, then the tools I build with
    (frontend, backend and data, plus Git). All of it comes from the portfolio's stack."""
    areas = {a["id"]: a for a in data["areas"]}
    langs = [sk["name"] for sk in areas.get("languages", {}).get("skills", [])]
    tools = [i["text"] for k in ("web", "backend", "data") for i in areas.get(k, {}).get("items", [])]
    tools += [sk["name"] for sk in areas.get("tools", {}).get("skills", [])]
    return [r for r in (langs, tools) if r]


def stack_strip(theme: str, data: dict) -> str:
    global BOOK
    BOOK = Glyphs(f"{theme[0]}g")
    c = PALETTES[theme]
    L = data.get("logos", {})
    size, gap = 40, 6
    body, y = "", 0
    all_rows = rows(data)
    for row in all_rows:
        x = (W - (len(row) * (size + gap) - gap)) / 2
        for name in row:
            body += (f'<rect x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="8" fill="{c["ink"]}"/>'
                     + logo(c, L.get(name), x + 9, y + 9, size - 18, c["paper"]))
            x += size + gap
        y += size + gap
    label = "Stack. " + " / ".join(", ".join(r) for r in all_rows)
    return doc(W, y - gap, BOOK.defs() + body, label)


if __name__ == "__main__":
    cfg = config()
    data = load(cfg)
    if not data:
        print("no stack.json yet: skipping the Stack panel", file=sys.stderr)
        sys.exit(0)
    for theme in THEMES:
        p = write("stack", theme, stack_strip(theme, data), "generated")
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")
