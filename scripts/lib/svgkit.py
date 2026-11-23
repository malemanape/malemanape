"""Shared helpers for every SVG on the profile.

GitHub shows README images through a proxy and never loads web fonts, so:
  - headings and labels are turned into vector outlines (Archivo, from the portfolio)
  - the ASCII uses a small subset of DejaVu Sans Mono, embedded inside the SVG
Every image is written twice: <name>-light.svg and <name>-dark.svg.
"""
from __future__ import annotations

import base64
import functools
import io
import json
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "scripts" / "fonts"

# Same tokens as the portfolio (global.css), plus GitHub's page colours.
PALETTES = {
    "light": dict(
        page="#FFFFFF", card="#F4EFE4", paper="#FBF8F1", ink="#15130F", muted="#5E574D",
        rock="#E6DECF", accent="#00789A", on_ink_accent="#2BA5C6", white="#FFFFFF",
        panel_bg="#15130F", on_panel="#FBF8F1",
        levels=["#E6DECF", "#B9DCE6", "#6FB8CD", "#2C93B0", "#00789A"],
    ),
    "dark": dict(
        page="#0D1117", card="#12110E", paper="#1B1915", ink="#EDE6D8", muted="#A69D8E",
        rock="#2C2821", accent="#2BA5C6", on_ink_accent="#00789A", white="#FFFFFF",
        panel_bg="#211E19", on_panel="#EDE6D8",
        levels=["#2C2821", "#0E3A47", "#13617A", "#1F86A6", "#2BA5C6"],
    ),
}
THEMES = ("light", "dark")

MONO_ADV = 1233 / 2048  # DejaVu Sans Mono advance width, in em


def config() -> dict:
    return json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- outlined text

@functools.cache
def _archivo(wght: int, wdth: int):
    font = TTFont(FONTS / "archivo-var.woff")
    inst = instancer.instantiateVariableFont(font, {"wght": wght, "wdth": wdth})
    return inst, inst.getGlyphSet(), inst.getBestCmap(), inst["hmtx"], inst["head"].unitsPerEm


@functools.cache
def _mono(bold: bool):
    font = TTFont(FONTS / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"))
    return font, font.getGlyphSet(), font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm


def text_width(s: str, size: float, wght=700, wdth=100, ls=0.0, mono=False, bold=False) -> float:
    _, _, cmap, hmtx, upm = _mono(bold) if mono else _archivo(wght, wdth)
    w = 0.0
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        w += hmtx[g][0] * size / upm + ls
    return w - (ls if s else 0)


class Glyphs:
    """Outlines each glyph once, in <defs>, so text-heavy images can <use> it instead of
    repeating the outline every time a letter appears. Pass it to text() as book=, and
    put book.defs() somewhere in the image."""

    def __init__(self, prefix: str = "g"):
        self.prefix, self.paths = prefix, {}

    def ref(self, font_key: str, gs, g: str) -> str:
        key = f"{font_key}/{g}"
        if key not in self.paths:
            pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
            gs[g].draw(pen)
            self.paths[key] = (f"{self.prefix}{len(self.paths)}", pen.getCommands())
        return self.paths[key][0]

    def defs(self) -> str:
        return "<defs>" + "".join(f'<path id="{i}" d="{d}"/>' for i, d in self.paths.values() if d) + "</defs>"


def text(s: str, x: float, y: float, size: float, fill: str, *, wght=700, wdth=100, ls=0.0,
         anchor="start", mono=False, bold=False, extra="", book: Glyphs | None = None) -> str:
    """A <path> with the text outlined (or <use>s of a Glyphs book). y is the baseline."""
    _, gs, cmap, hmtx, upm = _mono(bold) if mono else _archivo(wght, wdth)
    width = text_width(s, size, wght, wdth, ls, mono, bold)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    k = size / upm
    if book is not None:
        font_key = f"m{int(bold)}" if mono else f"a{wght}-{wdth}"
        # one scaled group per string; inside it each letter is a <use> at an x in font units
        uses, ux = "", 0.0
        for ch in s:
            g = cmap.get(ord(ch)) or cmap.get(ord("?"))
            if ch != " ":
                uses += f'<use href="#{book.ref(font_key, gs, g)}" x="{ux:.0f}"/>'
            ux += hmtx[g][0] + ls / k
        return (f'<g fill="{fill}"{extra} transform="translate({x:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})">{uses}</g>'
                if uses else "")
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    cx = x
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
        cx += hmtx[g][0] * k + ls
    d = pen.getCommands()
    return f'<path d="{d}" fill="{fill}"{extra}/>' if d else ""


# ---------------------------------------------------------------- embedded mono font

MONO_CHARS = "".join(chr(c) for c in range(32, 127)) + "¬°·•─│┌┐└┘■□▌▐░▒▓█"


@functools.cache
def mono_css() -> str:
    """@font-face rules with a subset of DejaVu Sans Mono embedded as WOFF."""
    rules = []
    for bold in (False, True):
        font = TTFont(FONTS / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"))
        opts = Options()
        opts.flavor = "woff"
        opts.layout_features = []
        opts.name_IDs = []
        opts.notdef_outline = True
        sub = Subsetter(opts)
        sub.populate(text=MONO_CHARS)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(
            f"@font-face{{font-family:ElMono;font-weight:{700 if bold else 400};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(rules)


MONO_STACK = "ElMono,'DejaVu Sans Mono',Menlo,Consolas,monospace"


# ---------------------------------------------------------------- documents and parts

def doc(w: float, h: float, body: str, label: str, css: str = "", mono: bool = False) -> str:
    style = (mono_css() if mono else "") + css
    style += "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{style}</style>{body}</svg>"
    )


def dots(pid: str, color: str, size=7, r=1.3, opacity=1.0) -> str:
    return (
        f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="{color}" opacity="{opacity}"/></pattern>'
    )


def panel(c: dict, x: float, y: float, w: float, h: float, title: str, right: str = "",
          right_color: str | None = None, uid: str = "p") -> str:
    """Comic panel: halftone drop shadow, 3px ink border, ink header bar with a mono title."""
    return (
        f"<defs>{dots(uid + 'd', c['ink'])}</defs>"
        f'<rect x="{x+12}" y="{y+12}" width="{w}" height="{h}" fill="url(#{uid}d)"/>'
        f'<rect x="{x+1.5}" y="{y+1.5}" width="{w-3}" height="{h-3}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="28" fill="{c["ink"]}"/>'
        + text(title, x + 14, y + 19, 13, c["paper"], mono=True, bold=True)
        + (text(right, x + w - 14, y + 19, 13, right_color or c["on_ink_accent"], mono=True, bold=True, anchor="end") if right else "")
    )


def write(name: str, theme: str, svg: str, folder: str = "assets") -> Path:
    out = ROOT / folder / f"{name}-{theme}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    return out
