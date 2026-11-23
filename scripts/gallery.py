"""The dense ASCII gallery, one day on the quest: koi -> knight -> desk -> Merlin -> greatsword -> campfire -> El waving goodbye, looping.

Each scene is drawn here as a grayscale vector picture (all original art), rasterised,
and every cell of a 126 x 40 grid becomes a character by how dark it is. Parts marked
"hot" (plume, koi spots, cape, flames) are inked in the accent colour.

    python scripts/gallery.py            # writes assets/gallery-light.svg and -dark.svg
    python scripts/gallery.py --print    # also prints one frame of each scene

Needs rsvg-convert (librsvg) and Pillow. Only run when you change the art.
"""
from __future__ import annotations

import io
import math
import re
import subprocess
import sys
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from art import BAND, BODY, BOOTS, CAPE_A, CAPE_B, EAR, HAIR, LEGS, ROCK, ROCK_SHADE
from lib.svgkit import MONO_ADV, MONO_STACK, PALETTES, THEMES, doc, panel, write

COLS, ROWS = 126, 40
VW, VH = 1896, 1000                     # drawing space; one cell = 15.05 x 25
CX, CY = VW / COLS, VH / ROWS
RAMP = " .:-=+*#%@"
W = 830
FS, LH = 10, 10                         # font size and line height of the grid
GX, GY = 30, 50                         # grid origin inside the panel


# ---------------------------------------------------------------- drawing helpers

class Pen:
    """Builds the same picture twice: in grayscale, and as a white-on-black mask of the hot parts."""

    def __init__(self, mask: bool):
        self.mask, self.parts = mask, []

    def col(self, gray: str, hot: bool = False) -> str:
        return ("#fff" if hot else "#000") if self.mask else gray

    def add(self, s: str):
        self.parts.append(s)

    def svg(self, bg: str = "#ffffff") -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{COLS * 12}" height="{ROWS * 20}">'
                f'<rect width="100%" height="100%" fill="{"#000" if self.mask else bg}"/>{"".join(self.parts)}</svg>')


def raster(svg: str) -> np.ndarray:
    png = subprocess.run(["rsvg-convert"], input=svg.encode(), capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("L").resize((COLS, ROWS), Image.BOX)
    return np.asarray(im, dtype=float) / 255.0


num = re.compile(r"-?\d+\.?\d*")


def lerp_path(a: str, b: str, f: float) -> str:
    na, nb = [float(x) for x in num.findall(a)], [float(x) for x in num.findall(b)]
    vals = iter(x + (y - x) * f for x, y in zip(na, nb))
    return num.sub(lambda m: f"{next(vals):.1f}", a)


def sky(p: Pen, horizon=640, ground="#d4d4d4"):
    p.add('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
          '<stop offset="1" stop-color="#e6e6e6"/></linearGradient></defs>')
    if not p.mask:
        p.add(f'<rect width="{VW}" height="{horizon}" fill="url(#sky)"/>')
    p.add(f'<rect y="{horizon}" width="{VW}" height="{VH - horizon}" fill="{p.col(ground)}"/>')


# ---------------------------------------------------------------- scene 1: the knight

def knight(f: int, p: Pen):
    sky(p, 700)
    sway = math.sin(f * 0.9) * 22
    p.add(f'<path d="M0 700 L220 610 L380 660 L560 590 L760 670 L900 700 Z" fill="{p.col("#b8b8b8")}"/>')
    p.add(f'<path d="M760 200 l16 9 l16 -9 M820 160 l12 7 l12 -7" stroke="{p.col("#333")}" stroke-width="6" fill="none"/>')
    p.add('<g transform="translate(560 1000) scale(1.22) translate(-560 -1000)">')
    # rock
    p.add(f'<path d="M180 1000 L230 820 L330 740 L470 715 L650 712 L800 735 L900 820 L950 1000 Z" fill="{p.col("#8c8c8c")}" stroke="{p.col("#222")}" stroke-width="8"/>')
    p.add(f'<path d="M800 735 L900 820 L950 1000 L780 1000 L820 880 Z" fill="{p.col("#5c5c5c")}"/>')
    p.add(f'<path d="M300 900 L380 860 L420 900 M600 800 L660 780" stroke="{p.col("#444")}" stroke-width="6" fill="none"/>')
    # cape behind him
    p.add(f'<path d="M455 430 L665 430 L760 820 L360 820 Z" fill="{p.col("#4a4a4a")}"/>')
    # legs: knees out, shins down, boots
    for x, k in ((470, -1), (650, 1)):
        p.add(f'<path d="M{x - 45} 640 L{x + 45} 640 L{x + 40 + k * 30} 720 L{x - 40 + k * 30} 720 Z" fill="{p.col("#2c2c2c")}"/>')
        p.add(f'<ellipse cx="{x + k * 30}" cy="705" rx="48" ry="34" fill="{p.col("#555")}" stroke="{p.col("#1a1a1a")}" stroke-width="6"/>')
        p.add(f'<path d="M{x - 30 + k * 30} 730 L{x + 30 + k * 30} 730 L{x + 26 + k * 34} 880 L{x - 34 + k * 34} 880 Z" fill="{p.col("#333")}"/>')
        p.add(f'<path d="M{x - 50 + k * 34} 880 L{x + 40 + k * 40} 880 L{x + 44 + k * 40} 915 L{x - 54 + k * 34} 915 Z" fill="{p.col("#1a1a1a")}"/>')
    # sword planted between the knees
    p.add(f'<path d="M548 560 L572 560 L572 905 L560 935 L548 905 Z" fill="{p.col("#d6d6d6")}" stroke="{p.col("#222")}" stroke-width="5"/>')
    p.add(f'<rect x="480" y="548" width="160" height="20" rx="6" fill="{p.col("#262626")}"/>')
    p.add(f'<rect x="549" y="470" width="22" height="80" fill="{p.col("#333")}"/>')
    p.add(f'<circle cx="560" cy="462" r="17" fill="{p.col("#444")}" stroke="{p.col("#111")}" stroke-width="5"/>')
    # torso and breastplate
    p.add(f'<path d="M470 430 L650 430 L632 650 L488 650 Z" fill="{p.col("#3a3a3a")}"/>')
    p.add(f'<path d="M548 445 L572 445 L566 640 L554 640 Z" fill="{p.col("#7a7a7a")}"/>')
    # arms hugging the grip
    for sx, hx in ((455, 538), (665, 582)):
        p.add(f'<path d="M{sx} 470 Q{sx + (hx - sx) * 0.2} 560 {hx} 515" stroke="{p.col("#262626")}" stroke-width="52" fill="none" stroke-linecap="round"/>')
        p.add(f'<circle cx="{hx}" cy="512" r="24" fill="{p.col("#1c1c1c")}"/>')
    for x in (450, 670):
        p.add(f'<ellipse cx="{x}" cy="452" rx="62" ry="44" fill="{p.col("#2e2e2e")}" stroke="{p.col("#777")}" stroke-width="6"/>')
    # helmet with a visor slit
    p.add(f'<path d="M492 420 L492 330 Q492 262 560 262 Q628 262 628 330 L628 420 Q560 440 492 420 Z" fill="{p.col("#363636")}" stroke="{p.col("#111")}" stroke-width="6"/>')
    p.add(f'<rect x="505" y="335" width="110" height="16" fill="{p.col("#e8e8e8")}"/>')
    p.add(f'<path d="M560 268 L560 420" stroke="{p.col("#666")}" stroke-width="6"/>')
    for i in range(3):
        p.add(f'<circle cx="{528 + i * 32}" cy="385" r="5" fill="{p.col("#bbb")}"/>')
    # plume (cyan), swaying in the wind
    p.add(f'<path d="M560 268 C590 {200 - sway / 2} {660 + sway} {170 + sway / 3} {735 + sway} {205 + sway / 2} '
          f'C{690 + sway} {215 + sway / 3} {640} 240 590 280 Z" fill="{p.col("#7d7d7d", True)}" stroke="{p.col("#222")}" stroke-width="5"/>')
    if f % 11 in (4, 5):
        gx, gy = (520, 340) if f % 11 == 4 else (572, 700)
        p.add(f'<path d="M{gx} {gy - 40} L{gx + 8} {gy - 8} L{gx + 40} {gy} L{gx + 8} {gy + 8} L{gx} {gy + 40} '
              f'L{gx - 8} {gy + 8} L{gx - 40} {gy} L{gx - 8} {gy - 8} Z" fill="{p.col("#ffffff", True)}"/>')
    p.add('</g>')
    # the scroll
    p.add(f'<rect x="1160" y="200" width="560" height="600" fill="{p.col("#fafafa")}" stroke="{p.col("#222")}" stroke-width="8"/>')
    for y in (200, 800):
        p.add(f'<rect x="1130" y="{y - 28}" width="620" height="56" rx="28" fill="{p.col("#9a9a9a")}" stroke="{p.col("#222")}" stroke-width="8"/>')


def knight_text(f: int):
    words = ["rest.", "write.", "train.", "repeat."]
    left = f * 3
    out, quill = [], None
    for i, w in enumerate(words):
        n = max(0, min(len(w), left))
        left -= len(w)
        if n:
            out.append((83, 11 + i * 4, w[:n], False))
        if 0 < n < len(w) or (n == len(w) and left < 0 and quill is None and n):
            quill = (83 + n, 11 + i * 4)
    if f >= 8:
        quill = None
        if f % 2 == 0:
            out.append((86, 29, "~ arete ~", True))
    return out, quill


# ---------------------------------------------------------------- scene 2: the koi pond

def koi_body(p: Pen, cx, cy, rx, ry, a, direction, wiggle, scale=1.0):
    pts = []
    for k in range(9):
        t = a - direction * k * 0.13 * (1.25 if scale > 1.2 else 1.6)
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    widths = [16, 50, 64, 62, 54, 42, 29, 18, 10]
    left, right = [], []
    for k, (x, y) in enumerate(pts):
        x2, y2 = pts[min(k + 1, 8)] if k < 8 else pts[7]
        dx, dy = (x2 - x, y2 - y) if k < 8 else (x - x2, y - y2)
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = widths[k] * scale * (1 + 0.15 * math.sin(wiggle + k))
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    hx, hy = pts[0]
    bx, by = pts[1]
    tip = (hx + (hx - bx) * 0.6, hy + (hy - by) * 0.6)
    tx, ty = pts[8]
    px, py = pts[7]
    ln = math.hypot(tx - px, ty - py) or 1
    ux, uy = (tx - px) / ln, (ty - py) / ln
    nx, ny = -uy, ux
    fl = math.sin(wiggle * 2) * 22
    fin1 = (tx + ux * 70 * scale + nx * (44 * scale + fl), ty + uy * 70 * scale + ny * (44 * scale + fl))
    fin2 = (tx + ux * 70 * scale - nx * (44 * scale - fl), ty + uy * 70 * scale - ny * (44 * scale - fl))
    tail = f'M{tx:.0f} {ty:.0f} L{fin1[0]:.0f} {fin1[1]:.0f} L{tx + ux * 40 * scale:.0f} {ty + uy * 40 * scale:.0f} L{fin2[0]:.0f} {fin2[1]:.0f} Z'
    p.add(f'<path d="{tail}" fill="{p.col("#ffffff")}" stroke="{p.col("#222")}" stroke-width="5"/>')
    # pectoral fins
    for side in (1, -1):
        x, y = pts[2]
        lx, ly = (left if side == 1 else right)[2]
        p.add(f'<ellipse cx="{x + (lx - x) * 1.5:.0f}" cy="{y + (ly - y) * 1.5:.0f}" rx="{22 * scale:.0f}" ry="{12 * scale:.0f}" fill="{p.col("#e8e8e8")}" stroke="{p.col("#222")}" stroke-width="4"/>')
    outline = [tip] + left + right[::-1]
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in outline) + " Z"
    p.add(f'<path d="{d}" fill="{p.col("#ffffff")}" stroke="{p.col("#0a0a0a")}" stroke-width="9" stroke-linejoin="round"/>')
    for k, r in ((2, 20), (4, 16), (6, 9)):
        x, y = pts[k]
        p.add(f'<circle cx="{x + 6:.0f}" cy="{y - 4:.0f}" r="{r * scale:.0f}" fill="{p.col("#3a3a3a", True)}"/>')
    ex, ey = left[1]
    p.add(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{7 * scale:.0f}" fill="{p.col("#111")}"/>')


def koi(f: int, p: Pen):
    n = 12
    p.add(f'<rect width="{VW}" height="{VH}" fill="{p.col("#e9e9e9")}"/>')
    for i in range(12):
        x, y = (i * 397) % VW, (i * 211) % VH
        p.add(f'<path d="M{x} {y} l10 -26 M{x + 14} {y} l6 -18" stroke="{p.col("#9a9a9a")}" stroke-width="5"/>')
    p.add('<defs><radialGradient id="water" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#787878"/>'
          '<stop offset="0.8" stop-color="#626262"/><stop offset="1" stop-color="#4a4a4a"/></radialGradient></defs>')
    p.add(f'<ellipse cx="948" cy="500" rx="800" ry="450" fill="{"#000" if p.mask else "url(#water)"}"/>')
    for k in range(3):
        cx, cy = [(520, 300), (1400, 700), (1250, 260)][k]
        r = ((f / n + k / 3) % 1) * 260
        p.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{r:.0f}" ry="{r * 0.55:.0f}" fill="none" stroke="{p.col("#b4b4b4")}" stroke-width="10" opacity="{1 - r / 260:.2f}"/>')
        p.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 0.6:.0f}" ry="{r * 0.33:.0f}" fill="none" stroke="{p.col("#a0a0a0")}" stroke-width="8" opacity="{1 - r / 260:.2f}"/>')
    for i in range(30):
        a = i * 0.209
        x, y = 948 + 800 * math.cos(a), 500 + 450 * math.sin(a)
        p.add(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{48 + (i * 7) % 20}" ry="{30 + (i * 5) % 12}" fill="{p.col("#c4c4c4")}" stroke="{p.col("#111")}" stroke-width="7"/>')
    for (x, y, r, flower) in ((420, 640, 80, True), (1520, 360, 66, False), (1600, 690, 52, False)):
        p.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p.col("#4c4c4c")}" stroke="{p.col("#222")}" stroke-width="5"/>')
        p.add(f'<path d="M{x} {y} L{x + r + 6} {y - r * 0.35} L{x + r + 6} {y + r * 0.2} Z" fill="{p.col("#a9a9a9")}"/>')
        if flower:
            for j in range(6):
                t = j * math.pi / 3
                p.add(f'<ellipse cx="{x - 16 + 24 * math.cos(t):.0f}" cy="{y - 10 + 24 * math.sin(t):.0f}" rx="18" ry="11" transform="rotate({j * 60} {x - 16 + 24 * math.cos(t):.0f} {y - 10 + 24 * math.sin(t):.0f})" fill="{p.col("#f4f4f4", True)}" stroke="{p.col("#333")}" stroke-width="3"/>')
    a = 2 * math.pi * f / n
    koi_body(p, 948, 500, 470, 270, a, 1, f * 0.8, 1.45)
    koi_body(p, 948, 500, 270, 150, -a + 1.5, -1, f * 0.8 + 1, 1.1)


# ---------------------------------------------------------------- scene 3: El waving

def el(f: int, p: Pen):
    p.add('<defs><radialGradient id="sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#8c8c8c"/>'
          '<stop offset="0.55" stop-color="#b8b8b8"/><stop offset="1" stop-color="#fff"/></radialGradient>'
          '<linearGradient id="far" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b0b0b0"/><stop offset="1" stop-color="#d8d8d8"/></linearGradient>'
          '<linearGradient id="near" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6a6a6a"/><stop offset="1" stop-color="#3a3a3a"/></linearGradient></defs>')
    if not p.mask:
        p.add(f'<circle cx="560" cy="460" r="300" fill="url(#sun)"/><circle cx="560" cy="460" r="120" fill="#fff"/>')
        p.add('<path d="M0 660 L180 500 L300 590 L470 410 L640 590 L760 510 L980 720 L0 720 Z" fill="url(#far)"/>')
        p.add('<path d="M470 410 L520 460 L490 455 L470 475 L445 450 Z" fill="#fff"/>')
        p.add('<path d="M0 840 L140 710 L260 780 L420 660 L600 810 L760 720 L1000 920 L1000 1000 L0 1000 Z" fill="url(#near)"/>')
        for x0, y, h, sp in ((-200, 170, 18, 1.0), (300, 250, 14, 1.4), (-500, 330, 20, 1.2)):
            p.add(f'<path d="M{x0 + f * 26 * sp:.0f} {y} q 90 -{h} 180 0 t 180 0" stroke="#bdbdbd" stroke-width="9" fill="none" stroke-linecap="round"/>')
    else:
        p.add(f'<rect width="{VW}" height="{VH}" fill="#000"/>')
    cape = lerp_path(CAPE_A, CAPE_B, (1 - math.cos(f / 6 * math.pi)) / 2)
    ang = [-38, -14, 12, -14][f % 4]
    ex, ey = 246, 104
    hx, hy = ex + 58 * math.sin(math.radians(ang)), ey - 58 * math.cos(math.radians(ang))
    ink = p.col("#000")
    p.add(f'<g transform="translate(1060 230) scale(2.3)">'
          f'<path d="{ROCK}" fill="{p.col("#9a9a9a")}" stroke="{p.col("#111")}" stroke-width="5"/>'
          f'<path d="{ROCK_SHADE}" fill="{p.col("#5a5a5a")}"/>'
          f'<path d="M60 300 L120 270 L170 290 M150 240 L210 250" stroke="{p.col("#444")}" stroke-width="4" fill="none"/>'
          f'<g transform="translate(0 -110)"><path d="{BODY}" fill="{ink}"/><path d="{LEGS}" fill="{ink}"/><path d="{BOOTS}" fill="{ink}"/>'
          f'<path d="{cape}" fill="{p.col("#6e6e6e", True)}" stroke="{ink}" stroke-width="4"/>'
          f'<path d="M204 150 L{ex} {ey} L{hx:.1f} {hy:.1f}" stroke="{ink}" stroke-width="15" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="11" fill="{ink}"/>'
          f'<g transform="translate(92 58) scale(0.55)"><path d="{HAIR}" fill="{ink}"/>'
          f'<path d="{EAR}" fill="{p.col("#e6e6e6")}" stroke="{ink}" stroke-width="7"/>'
          f'<path d="{BAND}" fill="none" stroke="{p.col("#e6e6e6")}" stroke-width="9" stroke-linecap="round"/></g></g></g>')
    if f >= 2:
        p.add(f'<path d="M300 110 L900 110 L900 330 L760 330 L1120 250 L700 330 L300 330 Z" fill="{p.col("#ffffff")}" stroke="{p.col("#111")}" stroke-width="8" stroke-linejoin="round"/>')


def el_text(f: int):
    if f < 2:
        return []
    out = [(24, 7, "hi, I'm El (^_^)/", True)]
    if f >= 4:
        out.append((24, 10, "thanks for dropping by.", False))
    return out


# ---------------------------------------------------------------- scene 4: the campfire

def campfire(f: int, p: Pen):
    sky(p, 600, "#d9d9d9")
    p.add(f'<path d="M0 600 Q120 520 240 590 Q340 510 470 585 Q600 500 740 590 L740 600 L0 600 Z M1100 600 Q1250 520 1400 585 Q1560 505 1700 580 Q1800 540 1896 590 L1896 600 Z" fill="{p.col("#9c9c9c")}"/>')
    for i in range(18):
        x = (i * 211) % VW
        y = 660 + (i * 97) % 300
        p.add(f'<path d="M{x} {y} l8 -22 M{x + 12} {y} l5 -16" stroke="{p.col("#8a8a8a")}" stroke-width="5"/>')
    fx, fy = 900, 790
    # smoke drifting up and away
    for i in range(4):
        k = (f / 8 + i / 4) % 1
        p.add(f'<circle cx="{fx + 40 + k * 260:.0f}" cy="{fy - 360 - k * 330:.0f}" r="{30 + k * 50:.0f}" fill="none" stroke="{p.col("#cfcfcf")}" stroke-width="{14 - k * 8:.0f}"/>')
    # logs and stones
    for ang in (-18, 18):
        p.add(f'<rect x="{fx - 190}" y="{fy - 22}" width="380" height="44" rx="22" transform="rotate({ang} {fx} {fy})" fill="{p.col("#2e2e2e")}"/>')
    for i in range(11):
        t = math.pi * (i / 10)
        p.add(f'<ellipse cx="{fx - 260 * math.cos(t):.0f}" cy="{fy + 70 - 26 * math.sin(t):.0f}" rx="44" ry="28" fill="{p.col("#5a5a5a")}" stroke="{p.col("#222")}" stroke-width="5"/>')

    def flame(w, h, dx, gray):
        return (f'<path d="M{fx - w} {fy} C{fx - w} {fy - h * 0.5} {fx + dx - w * 0.25} {fy - h * 0.7} {fx + dx} {fy - h} '
                f'C{fx + dx + w * 0.25} {fy - h * 0.7} {fx + w} {fy - h * 0.5} {fx + w} {fy} Z" fill="{p.col(gray, True)}"/>')

    s = math.sin(f * 1.7) * 0.5 + math.sin(f * 0.6) * 0.5
    p.add(flame(160, 440 + s * 50, 50 * s, "#5e5e5e"))
    p.add(flame(108, 330 - s * 36, -36 * s, "#9a9a9a"))
    p.add(flame(56, 196 + s * 24, 20 * s, "#e6e6e6"))
    for i in range(6):
        k = ((f / 8) * 2 + i / 6) % 1
        x = fx + math.sin(i * 2.1 + k * 6) * 120
        p.add(f'<circle cx="{x:.0f}" cy="{fy - 300 - k * 380:.0f}" r="{9 - k * 5:.0f}" fill="{p.col("#333", True)}"/>')
    # the knight's sword, planted for the night, and his helmet on a stone
    p.add(f'<path d="M430 540 L452 540 L452 860 L441 890 L430 860 Z" fill="{p.col("#d6d6d6")}" stroke="{p.col("#222")}" stroke-width="5"/>')
    p.add(f'<rect x="372" y="528" width="138" height="18" rx="6" fill="{p.col("#262626")}"/><rect x="431" y="460" width="20" height="70" fill="{p.col("#333")}"/>')
    p.add(f'<circle cx="441" cy="452" r="15" fill="{p.col("#444")}"/>')
    p.add(f'<ellipse cx="250" cy="900" rx="110" ry="46" fill="{p.col("#6a6a6a")}" stroke="{p.col("#222")}" stroke-width="5"/>')
    p.add(f'<path d="M190 870 L190 800 Q190 740 250 740 Q310 740 310 800 L310 870 Z" fill="{p.col("#363636")}" stroke="{p.col("#111")}" stroke-width="5"/>')
    p.add(f'<rect x="200" y="795" width="100" height="14" fill="{p.col("#e8e8e8")}"/>')
    # the save point sign
    p.add(f'<rect x="1452" y="480" width="22" height="440" fill="{p.col("#444")}"/>')
    p.add(f'<rect x="1260" y="300" width="420" height="230" fill="{p.col("#f6f6f6")}" stroke="{p.col("#222")}" stroke-width="8"/>')
    for x, y in ((1282, 322), (1658, 322), (1282, 508), (1658, 508)):
        p.add(f'<circle cx="{x}" cy="{y}" r="7" fill="{p.col("#555")}"/>')


def campfire_text(f: int):
    out = [(87, 16, "progress saved.", False), (87, 18, "rest: (-_-) zz", False)]
    if f % 4 < 3:
        out.append((87, 14, "SAVE POINT", True))
    return out


# ---------------------------------------------------------------- scene 5: the greatsword, planted

def greatsword(f: int, p: Pen):
    """El's greatsword (the one from the year card) planted deep in his rock, a thin strip of his cape
    knotted on the guard and rippling in the wind while he's away."""
    sky(p, 900, "#d6d6d6")
    if not p.mask:
        p.add('<path d="M0 900 L220 640 L380 760 L560 560 L760 780 L900 700 L1120 900 Z M1180 900 L1380 700 L1560 800 L1700 720 L1896 860 L1896 900 Z" fill="#d0d0d0"/>')
    # wind: streaks and leaves blowing right
    for i in range(7):
        x = (i * 331 + f * 140) % (VW + 400) - 200
        y = 180 + (i * 113) % 420
        p.add(f'<path d="M{x} {y} q 70 -14 140 0 t 140 0" stroke="{p.col("#c4c4c4")}" stroke-width="8" fill="none" stroke-linecap="round"/>')
    for i in range(5):
        x = (i * 397 + f * 190) % (VW + 200) - 100
        y = 260 + (i * 151 + f * 23) % 380
        p.add(f'<ellipse cx="{x}" cy="{y}" rx="16" ry="7" transform="rotate({(f * 40 + i * 70) % 360} {x} {y})" fill="{p.col("#7a7a7a", True)}"/>')
    cx, top, tip = 948, 170, 740          # the blade runs from the guard down into the rock; the tip stays inside it
    # the cape: a thin strip of cloth knotted on the guard, rippling out in the wind
    t = f / 10 * 2 * math.pi
    upper, lower = [], []
    n, length = 28, 760
    for i in range(n + 1):
        u = i / n
        x = cx + 60 + u * length
        y = top + 40 + u * 120 + math.sin(u * 3.2 * math.pi - t) * (14 + 70 * u)
        half = 34 * (1 - u) + 7            # wide at the knot, a thin tail at the end
        upper.append((x, y - half))
        lower.append((x, y + half))
    cape = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in upper + lower[::-1]) + " Z"
    p.add(f'<path d="{cape}" fill="{p.col("#6e6e6e", True)}" stroke="{p.col("#111")}" stroke-width="7" stroke-linejoin="round"/>')
    p.add(f'<path d="M{cx + 40} {top + 4} C{cx + 90} {top - 10} {cx + 100} {top + 60} {cx + 60} {top + 70}" fill="none" '
          f'stroke="{p.col("#555", True)}" stroke-width="22" stroke-linecap="round"/>')
    # blade, fuller, guard, grip, pommel
    p.add(f'<path d="M{cx - 70} {top + 30} L{cx + 70} {top + 30} L{cx + 70} {tip - 70} L{cx} {tip} L{cx - 70} {tip - 70} Z" fill="{p.col("#efefef")}" stroke="{p.col("#111")}" stroke-width="12" stroke-linejoin="round"/>')
    p.add(f'<path d="M{cx} {top + 60} L{cx} {tip - 80}" stroke="{p.col("#555", True)}" stroke-width="16" stroke-linecap="round"/>')
    p.add(f'<rect x="{cx - 150}" y="{top + 2}" width="300" height="40" rx="8" fill="{p.col("#222")}"/>')
    p.add(f'<rect x="{cx - 16}" y="{top - 110}" width="32" height="112" fill="{p.col("#333")}"/>')
    p.add(f'<circle cx="{cx}" cy="{top - 124}" r="26" fill="{p.col("#555", True)}" stroke="{p.col("#111")}" stroke-width="8"/>')
    # the rock goes in front, so the blade sinks into it: a dark gash where it went in, the rock's lip
    # over the front of the gash, then cracks and chips around it
    ry0, k = 270, 1.6
    p.add(f'<g transform="translate({cx - 175 * k:.0f} {ry0}) scale({k})">'
          f'<path d="{ROCK}" fill="{p.col("#8e8e8e")}" stroke="{p.col("#111")}" stroke-width="8"/>'
          f'<path d="{ROCK_SHADE}" fill="{p.col("#6a6a6a")}"/></g>')
    ey = ry0 + 212 * k                      # where the blade meets the rock
    p.add(f'<ellipse cx="{cx}" cy="{ey}" rx="96" ry="26" fill="{p.col("#111")}"/>')
    p.add(f'<path d="M{cx - 118} {ey} Q{cx - 80} {ey + 6} {cx - 50} {ey + 2} Q{cx - 20} {ey + 14} {cx + 10} {ey + 4} '
          f'Q{cx + 50} {ey + 12} {cx + 82} {ey + 2} Q{cx + 104} {ey + 6} {cx + 118} {ey} L{cx + 118} {ey + 60} L{cx - 118} {ey + 60} Z" '
          f'fill="{p.col("#8e8e8e")}"/>')
    p.add(f'<path d="M{cx - 118} {ey} Q{cx - 80} {ey + 6} {cx - 50} {ey + 2} Q{cx - 20} {ey + 14} {cx + 10} {ey + 4} '
          f'Q{cx + 50} {ey + 12} {cx + 82} {ey + 2} Q{cx + 104} {ey + 6} {cx + 118} {ey}" fill="none" stroke="{p.col("#111")}" stroke-width="8"/>')
    for dx, dy, ex, ey2 in ((-96, 4, -190, 70), (-60, 14, -80, 130), (90, 4, 170, 80), (40, 14, 80, 140), (0, 16, -10, 110)):
        p.add(f'<path d="M{cx + dx} {ey + dy} L{cx + ex} {ey + ey2}" stroke="{p.col("#222")}" stroke-width="8" stroke-linecap="round"/>')
    for x, y, r in ((cx - 230, ey + 30, 16), (cx + 210, ey + 36, 13), (cx - 150, ey + 4, 10), (cx + 140, ey + 6, 9)):
        p.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p.col("#4a4a4a")}"/>')


def greatsword_text(f: int):
    out = [(6, 30, "brb, getting coffee.", False), (6, 32, "  - El", False)]
    if f % 4 < 2:
        out.insert(0, (6, 28, "[ do not touch ]", True))
    return out


# ---------------------------------------------------------------- scene 6: Merlin

def _crown(peaks, valleys, base_l, base_r, bend):
    """Merlin's flame layer, ported from his app's fire.ts (via the portfolio's merlinFire.ts)."""
    steps = []
    for i, pt in enumerate(peaks):
        steps.append(("peak", pt))
        if i < len(valleys):
            steps.append(("valley", valleys[i]))
    steps.append(("base", base_r))
    d, prev = f"M{base_l[0]:.1f} {base_l[1]:.1f}", base_l
    for kind, (bx, by) in steps:
        ax, ay = prev
        if kind == "peak":
            dy = ay - by
            c1 = (ax - bend * 0.6 if prev is base_l else ax + 2, ay - dy * 0.55)
            c2 = (bx - bend * 0.4, by + dy * 0.3)
        else:
            dy = by - ay
            c1 = (ax + bend * 0.4, ay + dy * 0.35)
            c2 = (bx - bend * 0.2 if kind == "valley" else bx + bend * 0.8, by - dy * 0.45)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {bx:.1f} {by:.1f}"
        prev = (bx, by)
    return d + " Z"


MERLIN_FIRE = [  # (base left, base right, peaks, valleys, sway, lift, bend, gray), back to front
    ((66, 118), (134, 118), [(34, 40), (62, 6), (100, -18), (138, 0), (168, 36)], [(48, 72), (80, 42), (120, 36), (152, 64)],
     [[-12, -3, -14, -5], [-6, 4, -8, 2], [5, -7, 8, -4], [6, -2, 9, 3], [12, 4, 14, 5]],
     [[0, -8, 4, -4], [-6, 4, -10, 2], [4, -10, 0, -6], [-8, 2, -4, 4], [2, -6, -2, -8]], 16, "#9a9a9a"),
    ((64, 116), (136, 116), [(44, 44), (72, 14), (100, -6), (130, 8), (158, 32)], [(60, 72), (86, 48), (116, 42), (144, 60)],
     [[-10, -2, -12, -4], [-5, 6, -8, 3], [6, -8, 5, -5], [5, -3, 9, 2], [10, 3, 12, 5]],
     [[0, -7, 3, -4], [-5, 3, -9, 2], [3, -8, 0, -5], [-7, 2, -4, 4], [2, -5, -1, -7]], 13, "#5e5e5e"),
    ((72, 104), (128, 104), [(68, 56), (88, 32), (110, 22), (132, 46)], [(78, 72), (98, 54), (122, 60)],
     [[-6, 2, -8, 0], [4, -5, 3, -4], [-5, 6, -4, 5], [6, -2, 8, 1]],
     [[-3, 3, -6, 0], [2, -6, 3, -3], [-4, 0, -6, 3], [0, -4, 2, -5]], 9, "#d8d8d8"),
]


def merlin(f: int, p: Pen):
    """Merlin, the flaming skull mage from merlin-desktop-companion: his fire flickers, he bobs,
    his jaw chatters while he talks, and his rune circle turns under him."""
    sky(p, 880, "#e2e2e2")
    t = f / 12 * 4                       # four flame keyframes, eased through twelve frames
    k0, frac = int(t) % 4, t - int(t)
    k1 = (k0 + 1) % 4
    bob = math.sin(f / 12 * 2 * math.pi) * 6
    s, ox, oy = 4.0, 948 - 100 * 4.0, 120
    # the rune circle on the floor, turning
    rc = f"translate({948} {oy + 200 * s}) scale(1 0.3)"
    rot = f * 15
    p.add(f'<g transform="{rc}"><g transform="rotate({rot})" fill="none" stroke="{p.col("#7a7a7a", True)}">'
          f'<circle r="{62 * s}" stroke-width="16"/><circle r="{50 * s}" stroke-width="8"/>'
          f'<path d="M0 {-50 * s} L{43.3 * s} {25 * s} L{-43.3 * s} {25 * s} Z M0 {50 * s} L{43.3 * s} {-25 * s} L{-43.3 * s} {-25 * s} Z" stroke-width="9"/></g></g>')
    p.add(f'<g transform="translate({ox} {oy + bob * s}) scale({s})">')
    for bl, br, peaks, valleys, sway, lift, bend, gray in MERLIN_FIRE:
        def at(k):
            return [(x + sw[k], y + lf[k]) for (x, y), sw, lf in zip(peaks, sway, lift)]
        pk = [(a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac) for a, b in zip(at(k0), at(k1))]
        p.add(f'<path d="{_crown(pk, valleys, bl, br, bend)}" fill="{p.col(gray, True)}"/>')
    ink, bone = p.col("#111"), p.col("#f2f2f2")
    p.add(f'<path d="M52 106 Q46 54 100 48 Q154 54 148 106 Q148 124 132 130 L128 142 L72 142 L68 130 Q52 124 52 106 Z" fill="{bone}" stroke="{ink}" stroke-width="3.5"/>'
          f'<path d="M120 58 L113 72 L121 78" fill="none" stroke="{ink}" stroke-width="2.5"/>'
          f'<ellipse cx="78" cy="102" rx="16" ry="18" fill="{ink}"/><ellipse cx="122" cy="102" rx="16" ry="18" fill="{ink}"/>'
          f'<circle cx="80" cy="106" r="6.5" fill="{p.col("#bdbdbd", True)}"/><circle cx="120" cy="106" r="6.5" fill="{p.col("#bdbdbd", True)}"/>'
          f'<path d="M95 120 L105 120 L100 128 Z" fill="{ink}"/>')
    jaw = 6 if f % 3 == 1 else 0         # talking
    p.add(f'<g transform="translate(0 {jaw})"><path d="M72 142 L128 142 Q131 162 116 168 L84 168 Q69 162 72 142 Z" fill="{bone}" stroke="{ink}" stroke-width="3.5"/></g>')
    p.add("</g>")


def merlin_text(f: int):
    lines = ["hello, mortal.", "your code compiles?", "...suspicious. (o_o)"]
    shown = min(len(lines), 1 + f // 4)
    return [(6, 12 + 2 * i, s, i == 0) for i, s in enumerate(lines[:shown])]


# ---------------------------------------------------------------- scene: El at his desk

DESK_CODE = ["const el = {", "  focus: 'max',", "  music: 'lofi, loud',", "  status: 'shipping',", "};"]


def desk(f: int, p: Pen):
    """El from behind at his desk, like the portfolio's hero: headphones on, code typing itself on the
    monitor, steam off the mug and a few notes leaking out of the headphones."""
    if not p.mask:
        p.add(f'<rect width="{VW}" height="{VH}" fill="#ececec"/>')
        p.add('<path d="M1500 0 L1896 0 L1896 640 Z" fill="#dcdcdc"/>')
    # the desk
    p.add(f'<rect x="0" y="720" width="{VW}" height="280" fill="{p.col("#c8c8c8")}"/>')
    p.add(f'<rect x="0" y="712" width="{VW}" height="16" fill="{p.col("#222")}"/>')
    # the monitor: dark frame, a blank screen the code types onto, stand
    p.add(f'<rect x="500" y="150" width="720" height="470" rx="18" fill="{p.col("#1a1a1a")}"/>')
    p.add(f'<rect x="530" y="180" width="660" height="400" fill="{p.col("#ffffff")}"/>')
    p.add(f'<path d="M800 620 L920 620 L950 712 L770 712 Z" fill="{p.col("#2a2a2a")}"/>')
    # the keyboard and mouse
    p.add(f'<path d="M560 740 L1080 740 L1120 800 L520 800 Z" fill="{p.col("#333")}"/>')
    for i in range(3):
        p.add(f'<path d="M{580 - i * 12} {752 + i * 16} L{1090 + i * 10} {752 + i * 16}" stroke="{p.col("#777")}" stroke-width="5"/>')
    # the mug, and its steam
    p.add(f'<path d="M300 620 L400 620 L392 712 L308 712 Z" fill="{p.col("#f4f4f4")}" stroke="{p.col("#111")}" stroke-width="8"/>')
    p.add(f'<path d="M400 640 C440 640 440 690 396 690" fill="none" stroke="{p.col("#111")}" stroke-width="8"/>')
    for i, x in enumerate((330, 370)):
        y0 = 600 - ((f * 22 + i * 60) % 140)
        p.add(f'<path d="M{x} {y0 + 60} C{x - 20} {y0 + 40} {x + 20} {y0 + 20} {x} {y0}" fill="none" '
              f'stroke="{p.col("#9a9a9a")}" stroke-width="10" stroke-linecap="round"/>')
    # El, from behind: shoulders, then the same head as everywhere else (hair, headphones)
    ink = p.col("#000")
    p.add(f'<path d="M1240 1000 C1260 840 1360 760 1500 750 C1600 744 1680 770 1720 800 C1780 850 1810 930 1820 1000 Z" fill="{ink}"/>')
    p.add(f'<path d="M1380 1000 C1400 890 1450 830 1520 810" fill="none" stroke="{p.col("#5a5a5a")}" stroke-width="22"/>')
    p.add(f'<g transform="translate(1230 300) scale(3.1)"><path d="{HAIR}" fill="{ink}"/>'
          f'<path d="{EAR}" fill="{p.col("#e6e6e6")}" stroke="{ink}" stroke-width="6"/>'
          f'<path d="{BAND}" fill="none" stroke="{p.col("#e6e6e6")}" stroke-width="7" stroke-linecap="round"/></g>')
    # music leaking out of the headphones
    for i in range(3):
        t = (f + i * 3) % 10
        x, y = 1480 - t * 22 - i * 30, 520 - t * 26
        if t < 8:
            p.add(f'<g fill="{p.col("#555", True)}"><ellipse cx="{x}" cy="{y}" rx="16" ry="12" transform="rotate(-20 {x} {y})"/>'
                  f'<rect x="{x + 12}" y="{y - 60}" width="6" height="60"/><path d="M{x + 12} {y - 60} l30 12 l0 10 l-30 -12 Z"/></g>')


def desk_text(f: int):
    """The code types itself onto the monitor, a line or so a frame; the status line is the hot one."""
    budget = f * 7
    out = []
    for i, line in enumerate(DESK_CODE):
        n = max(0, min(len(line), budget))
        budget -= len(line)
        if n:
            out.append((38, 9 + i * 2, line[:n], i == 3))
    done = sum(len(x) for x in DESK_CODE) <= f * 7
    row = 9 + 2 * min(len(DESK_CODE) - 1, sum(1 for o in out) - 1 if out else 0)
    col = 38 + (len(out[-1][2]) if out else 0)
    if f % 2 == 0 or not done:
        out.append((col, row, "_", True))
    return out


# ---------------------------------------------------------------- frames -> grid -> svg

SCENES = [  # one day on the quest, ending with El waving goodbye to whoever's reading
    # file, caption, draw, text, frames, slots (frame index per step), step seconds
    ("koi.txt", "swim upstream long enough and you become a dragon.", koi, None, 12, list(range(12)) * 2, 0.22),
    ("knight.txt", "rest between quests, then back to building.", knight, knight_text, 14, list(range(14)), 0.3),
    ("desk.txt", "headphones on. the world can wait.", desk, desk_text, 12, list(range(12)) * 2, 0.22),
    ("merlin.txt", "merlin.exe: a desk companion that talks back. mostly sass.", merlin, merlin_text, 12, list(range(12)) * 2, 0.2),
    ("greatsword.txt", "planted for now. the quest picks up tomorrow.", greatsword, greatsword_text, 10, list(range(10)) * 2, 0.2),
    ("campfire.txt", "save point reached. progress saved.", campfire, campfire_text, 8, list(range(8)) * 3, 0.2),
    ("el.txt", "that's the tour. thanks for dropping by, see you next quest.", el, el_text, 12, list(range(12)) + list(range(4, 12)), 0.24),
]


def grid_for(draw, text_fn, f):
    g = raster((lambda p: (draw(f, p), p.svg())[1])(Pen(False)))
    m = raster((lambda p: (draw(f, p), p.svg())[1])(Pen(True))) > 0.45
    chars = [[RAMP[min(len(RAMP) - 1, int((1 - g[y, x]) ** 0.9 * len(RAMP)))] for x in range(COLS)] for y in range(ROWS)]
    hot = [[bool(m[y, x]) for x in range(COLS)] for y in range(ROWS)]
    quill = None
    if text_fn:
        res = text_fn(f)
        items, quill = res if isinstance(res, tuple) else (res, None)
        for col, row, s, h in items:
            for i, ch in enumerate(s):
                chars[row][col + i] = ch
                hot[row][col + i] = h
        if quill:
            qc, qr = quill
            for dr, s in enumerate(["/", "/"]):
                if 0 <= qr - 1 - dr < ROWS and qc + 1 + dr < COLS:
                    chars[qr - 1 - dr][qc + 1 + dr] = s
                    hot[qr - 1 - dr][qc + 1 + dr] = True
            chars[qr][qc] = "_" if f % 2 else "."
            hot[qr][qc] = True
    return chars, hot


def rows_svg(chars, hot) -> str:
    out = []
    for y in range(ROWS):
        spans, cur, h0 = [], "", None
        for x in range(COLS):
            h = hot[y][x]
            if h0 is None or h == h0:
                cur += chars[y][x]
            else:
                spans.append((cur, h0)); cur = chars[y][x]
            h0 = h
        spans.append((cur, h0))
        line = "".join(f'<tspan class="h">{escape(s)}</tspan>' if hh else escape(s) for s, hh in spans)
        if line.strip():
            out.append(f'<text x="{GX}" y="{GY + y * LH}">{line}</text>')
    return "".join(out)


def build(print_frames=False):
    frames = []      # (svg body, scene index)
    timeline = []    # (frame id, seconds)
    for si, (file, caption, draw, text_fn, n, slots, step) in enumerate(SCENES):
        base = len(frames)
        for f in range(n):
            chars, hot = grid_for(draw, text_fn, f)
            if print_frames and f == n // 2:
                print(f"--- {file}")
                print("\n".join("".join(r) for r in chars))
            frames.append((rows_svg(chars, hot), si))
        timeline += [(base + s, step) for s in slots]
    total = sum(s for _, s in timeline)
    # per-frame keyframes: visible during each of its slots
    windows = {i: [] for i in range(len(frames))}
    t = 0.0
    for fid, s in timeline:
        windows[fid].append((t / total * 100, (t + s) / total * 100))
        t += s
    css = f".f{{visibility:hidden;animation-duration:{total:.2f}s;animation-timing-function:steps(1,end);animation-iteration-count:infinite}}"
    for fid, ws in windows.items():
        kf = "0%{visibility:hidden}" if ws[0][0] > 0 else ""
        for a, b in ws:
            kf += f"{a:.3f}%{{visibility:visible}}{b:.3f}%{{visibility:hidden}}"
        kf += "100%{visibility:hidden}"
        css += f".f{fid}{{animation-name:k{fid}}}@keyframes k{fid}{{{kf}}}"
    still = 12  # the knight with his finished scroll, for reduced motion
    css += f"@media (prefers-reduced-motion:reduce){{.f{still}{{visibility:visible}}}}"
    return frames, css


def svg_for(theme: str, frames, css) -> str:
    c = PALETTES[theme]
    h = GY + ROWS * LH + 34
    body = panel(c, 0, 0, W - 14, h, "~/el/gallery/", uid="g")
    names = [s[0] for s in SCENES]
    for i, (rows, si) in enumerate(frames):
        dots = " ".join("■" if j == si else "□" for j in range(len(SCENES)))
        body += (f'<g class="f f{i}">'
                 f'<text class="hd" x="{14 + 13 * MONO_ADV * 13:.1f}" y="19">{names[si]}</text>'
                 f'<text class="hd dots" x="{W - 28}" y="19" text-anchor="end">{dots}</text>'
                 f'{rows}'
                 f'<text class="cap" x="{GX}" y="{GY + ROWS * LH + 14}">&gt; {escape(SCENES[si][1])}</text></g>')
    style = (
        f"text{{font-family:{MONO_STACK};font-size:{FS}px;white-space:pre;fill:{c['ink']}}}"
        f".h{{fill:{c['accent']};font-weight:700}}"
        f".hd{{font-size:13px;font-weight:700;fill:{c['paper']}}}.dots{{fill:{c['on_ink_accent']}}}"
        f".cap{{font-size:13px;font-weight:700}}" + css
    )
    label = ("Looping dense ASCII gallery: a knight sits on a rock hugging his planted sword while a quill writes "
             "two koi circle a pond at dawn; rest, write, train, repeat; El at his desk with his headphones on, code typing "
             "itself; Merlin the flaming skull mage, talking; his greatsword planted in the rock while he gets coffee; "
             "a campfire save point; and El waving goodbye from his rock.")
    return doc(W, h + 14, body, label, style, mono=True)


if __name__ == "__main__":
    frames, css = build("--print" in sys.argv)
    for theme in THEMES:
        p = write("gallery", theme, svg_for(theme, frames, css))
        print(f"{p.name}  {p.stat().st_size // 1024} KB, {len(frames)} frames")
