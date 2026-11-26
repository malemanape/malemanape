"""The art that comes from the config and the clock: banner (with its time-of-day sky), typing line,
About tiles, section headings, the commit joke, dodge.exe and the footer. The Action reruns it every hour.
The banner is also drawn once per time of day (assets/banner-<when>-<theme>.svg) for api/banner.js.

    python scripts/art.py                          # everything except the ASCII gallery (that's gallery.py)
    python scripts/art.py banner --period night    # one image, at a chosen time of day

Writes assets/<name>-light.svg and assets/<name>-dark.svg.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import math
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.svgkit import MONO_ADV, PALETTES, ROOT, THEMES, config, doc, dots, text, text_width, write
import pocket_sprites

W = 830

# El, seen from behind (same paths as the portfolio's AuraFarmer)
ROCK = "M24 336 L46 284 L34 260 L74 228 L112 214 L150 208 L204 210 L236 200 L272 222 L304 246 L296 286 L322 314 L330 336 Z"
ROCK_SHADE = "M236 200 L272 222 L304 246 L296 286 L322 314 L330 336 L252 336 L264 300 L242 262 Z"
BODY = "M128 142 C120 190 122 230 132 252 L208 252 C218 230 220 190 212 142 Z"
LEGS = "M140 246 L138 310 L164 310 L166 246 Z M176 246 L178 310 L204 310 L202 246 Z"
BOOTS = "M126 306 H166 V320 H122 Z M176 306 H214 V320 H180 Z"
HAIR = "M92 150 C78 108 84 66 110 44 L104 14 L126 34 L134 0 L150 30 L170 6 L172 38 L196 22 L188 58 C204 84 206 122 188 150 Z"
# headphones and the cape's fold, as on the portfolio (AuraFarmer.astro, Hero's desk scene): the ear cup and
# band sit in HAIR's coordinates, the fold in the cape's
EAR = "M94 104 C86 102 82 114 88 124 C92 130 98 128 98 122"
BAND = "M116 56 C102 76 100 102 104 128"
FOLD_A, FOLD_B = "M168 146 C162 190 164 226 170 256", "M168 146 C160 184 160 214 166 240"


def el_head(ink: str, light: str) -> str:
    """El's head from behind: the spiky hair, then his headphones (band over the top, ear cup at the side)."""
    return (f'<g transform="translate(92 58) scale(0.55)"><path d="{HAIR}" fill="{ink}"/>'
            f'<path d="{EAR}" fill="{light}" stroke="{ink}" stroke-width="5"/>'
            f'<path d="{BAND}" fill="none" stroke="{light}" stroke-width="6" stroke-linecap="round"/></g>')
CAPE_A = "M132 140 C122 180 120 222 124 262 C150 272 172 252 198 258 C224 264 248 236 274 232 C290 229 302 214 314 204 C288 196 264 188 242 172 C228 162 216 150 208 140 Z"
CAPE_B = "M132 140 C120 176 116 214 118 250 C146 256 166 236 194 238 C222 240 246 210 272 204 C290 200 304 182 318 170 C292 168 266 166 244 158 C228 152 216 146 208 140 Z"


def el_on_rock(c: dict, uid: str) -> str:
    return (
        f'<path d="{ROCK}" fill="{c["rock"]}" stroke="{c["ink"]}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="{ROCK_SHADE}" fill="url(#{uid}ink)" opacity="0.5"/>'
        '<g transform="translate(0 -110)">'
        f'<path d="{BODY}" fill="{c["ink"]}"/><path d="{LEGS}" fill="{c["ink"]}"/><path d="{BOOTS}" fill="{c["ink"]}"/>'
        f'<path d="{CAPE_A}" fill="{c["accent"]}" stroke="{c["ink"]}" stroke-width="4.5" stroke-linejoin="round">'
        f'<animate attributeName="d" dur="2.6s" repeatCount="indefinite" values="{CAPE_A};{CAPE_B};{CAPE_A}"/></path>'
        f'<path d="{FOLD_A}" fill="none" stroke="{c["ink"]}" stroke-width="3" stroke-linecap="round" opacity="0.55">'
        f'<animate attributeName="d" dur="2.6s" repeatCount="indefinite" values="{FOLD_A};{FOLD_B};{FOLD_A}"/></path>'
        + el_head(c["ink"], c["card"]) +
        f'<path d="M130 142 C150 134 190 134 210 142" fill="none" stroke="{c["ink"]}" stroke-width="7" stroke-linecap="round"/>'
        "</g>"
    )


# ---------------------------------------------------------------- El running, side-on

def _pommel(ink, paper):
    """The greatsword's octagonal ring pommel on a short cream rod, ending at x = -14 where the grip starts."""
    return (f'<path d="M-14 -2.2 L-26 -2.2 L-26 2.2 L-14 2.2 Z" fill="{paper}" stroke="{ink}" stroke-width="1.6"/>'
            f'<path d="M-30.6 -5.4 L-26.4 -5.4 L-23.4 -2.4 L-23.4 2.4 L-26.4 5.4 L-30.6 5.4 L-33.6 2.4 L-33.6 -2.4 Z" '
            f'fill="{paper}" stroke="{ink}" stroke-width="2"/><circle cx="-28.5" cy="0" r="1.6" fill="{ink}"/>')


def _haft(ink, x0, x1, r=2.6):
    return f'<path d="M{x0} -{r} L{x1} -{r} L{x1} {r} L{x0} {r} Z" fill="{ink}"/>'


def _greatbow(ink, acc, paper):
    """A heavy recurve greatbow drawn upright (grip at the origin, string on the +x side): thick cream limbs
    with a black core and a cyan inlay, a broad riser, hooked recurve tips and a taut string."""
    def centre(t, sign):
        y = sign * (16 + 58 * t)
        x = -18 * math.sin(math.pi * t * 0.85) + 18 * t ** 4      # bends back, then hooks forward at the tip
        return x, y
    out, tips = "", []
    for sign in (-1, 1):
        n = 22
        L, R, C = [], [], []
        for i in range(n + 1):
            t = i / n
            x, y = centre(t, sign)
            half = 9 - 6 * t
            L.append((x - half, y)); R.append((x + half, y)); C.append((x, y))
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in L + R[::-1]) + " Z"
        out += f'<path d="{d}" fill="{paper}" stroke="{ink}" stroke-width="2.6" stroke-linejoin="round"/>'
        Li = [(x + (cx - x) * 0.62, y) for (x, y), (cx, _) in zip(L, C)]
        Ri = [(x + (cx - x) * 0.62, y) for (x, y), (cx, _) in zip(R, C)]
        core = Li[1:-3] + Ri[1:-3][::-1]
        out += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in core) + f' Z" fill="{ink}"/>'
        inlay = C[2:11]
        out += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in inlay) + f'" fill="none" stroke="{acc}" stroke-width="1.8" stroke-linecap="round"/>'
        tx, ty = C[-1]
        out += f'<path d="M{tx - 2:.1f} {ty:.1f} L{tx + 5:.1f} {ty - 3 * sign:.1f} L{tx + 3:.1f} {ty + 2 * sign:.1f} Z" fill="{paper}" stroke="{ink}" stroke-width="1.8" stroke-linejoin="round"/>'
        tips.append((tx + 2, ty))
    (x1, y1), (x2, y2) = tips
    out = f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{ink}" stroke-width="1.6"/>' + out
    # the riser and its wrapped grip
    out += (f'<path d="M-8 -18 L4 -18 L7 -10 L7 10 L4 18 L-8 18 L-10 10 L-10 -10 Z" fill="{paper}" stroke="{ink}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<path d="M-6 -9 L4 -9 L4 9 L-6 9 Z" fill="{ink}"/>'
            f'<path d="M-6 -4.5 L4 -4.5 M-6 0 L4 0 M-6 4.5 L4 4.5" stroke="{paper}" stroke-width="1.3"/>'
            f'<path d="M-3 -16 L1 -16 L1 -12 L-3 -12 Z M-3 12 L1 12 L1 16 L-3 16 Z" fill="{acc}"/>')
    return out


# El's weapons, each drawn along +x from where his hand holds it (x = 0); the year card picks one a day
WEAPONS = {
    # the greatsword from El's avatar: a broad blade that flares toward a faceted point, cream edges around a
    # black core with a cyan fuller, a slim upright guard, and an octagonal ring pommel
    "sword": lambda ink, acc, paper: (
        _pommel(ink, paper) + f'<path d="M-14 -4 L-2 -4 L-2 4 L-14 4 Z" fill="{ink}"/>'
        f'<path d="M-3 -17 L6 -17 L6 17 L-3 17 Z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>'
        f'<path d="M0.4 -13 L2.6 -13 L2.6 13 L0.4 13 Z" fill="{ink}"/>'
        f'<path d="M6 -8 L92 -14.5 L117 -2 L104 14 L6 8 Z" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M12 -4 L90 -9.5 L108 -2 L99 9 L12 4 Z" fill="{ink}"/>'
        f'<path d="M26 -0.4 L88 -5.4 L101 -1.6 L88 2.6 Z" fill="{acc}"/>'),
    # the axe, hammer, halberd and keyboard share the greatsword's look: cream edges with an ink outline,
    # a black core, a cyan accent, and the octagonal ring pommel on the end of the haft
    # the axe and halberd keep the silhouettes El splits the rock with on the portfolio (AuraFarmer.astro),
    # drawn upright there; here they're turned to lie along +x and given the greatsword's finish
    "axe": lambda ink, acc, paper: (
        _pommel(ink, paper)
        + f'<g transform="rotate(90) scale(0.55)">'
        f'<rect x="-6" y="-178" width="12" height="204" rx="3" fill="{ink}"/>'
        f'<path d="M-6 -164 L-18 -162 L-18 -146 L-6 -144 Z" fill="{paper}" stroke="{ink}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M6 -166 L26 -166 L60 -200 L65 -150 L54 -94 L28 -136 L6 -142 Z" fill="{paper}" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M13 -159 L29 -159 L53 -184 L57 -150 L50 -114 L31 -142 L13 -149 Z" fill="{ink}"/>'
        f'<path d="M52 -180 L58.5 -150 L50 -112 L54 -150 Z" fill="{acc}"/>'
        f'<path d="M-7 -132 H7 M-7 -122 H7" stroke="{paper}" stroke-width="3"/>'
        f'</g>'),
    "hammer": lambda ink, acc, paper: (
        # a war hammer after El's reference: a tall block face on one side (up, when he carries it), a
        # banded round back end on the other, an octagonal socket marked E between them, a wrapped
        # haft and a spiked pommel
        f'<path d="M-14 -4.4 L-21 -7 L-27 0 L-21 7 L-14 4.4 Z" fill="{paper}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M-27 -3 L-36 0 L-27 3 Z" fill="{paper}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        + _haft(ink, -14, 56, 3.4)
        + "".join(f'<path d="M{x} -3.4 L{x + 5} 3.4" stroke="{paper}" stroke-width="1.6"/>' for x in range(-10, 40, 8))
        + f'<path d="M42 -3.6 L50 -3.6 L50 3.6 L42 3.6 Z" fill="{acc}" stroke="{ink}" stroke-width="1.4"/>'
        # the neck collar
        f'<path d="M50 -5 L56 -7.5 L60 -5.5 L60 5.5 L56 7.5 L50 5 Z" fill="{paper}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        # the banded round back end
        f'<path d="M64 -11 L80 -11 L80 -27 C80 -32 64 -32 64 -27 Z" fill="{paper}" stroke="{ink}" stroke-width="2.6" stroke-linejoin="round"/>'
        f'<path d="M64 -17 L80 -17 M64 -22.5 L80 -22.5" stroke="{ink}" stroke-width="2.4"/>'
        # the tall striking block
        f'<path d="M52 12 L94 12 L96 44 L50 44 Z" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M56 16 L90 16 L91 39 L55 39 Z" fill="{ink}"/>'
        f'<path d="M57 26 L89 26 L89 29 L57 29 Z" fill="{acc}"/>'
        f'<path d="M58 12.6 L58 43.4 M88 12.6 L88 43.4" stroke="{paper}" stroke-width="1.6"/>'
        # the octagonal socket, marked E
        f'<path d="M65 -13 L79 -13 L85 -7 L85 7 L79 13 L65 13 L59 7 L59 -7 Z" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M65.5 -7.5 L78.5 -7.5 L78.5 7.5 L65.5 7.5 Z" fill="{ink}"/>'
        f'<g transform="translate(72 0) rotate(90)"><path d="M-4 -5 L4 -5 L4 -2.6 L-1.4 -2.6 L-1.4 -1.1 L3 -1.1 L3 1.1 L-1.4 1.1 '
        f'L-1.4 2.6 L4 2.6 L4 5 L-4 5 Z" fill="{acc}"/></g>'),
    "halberd": lambda ink, acc, paper: (
        _pommel(ink, paper)
        + f'<g transform="rotate(90) scale(0.42)">'
        f'<rect x="-5" y="-216" width="10" height="250" rx="2" fill="{ink}"/>'
        # the spear point: a slim greatsword tip, cream edges, black core, cyan fuller
        f'<path d="M0 -296 L9 -240 L4 -214 L-4 -214 L-9 -240 Z" fill="{paper}" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M0 -282 L5 -242 L2 -222 L-2 -222 L-5 -242 Z" fill="{ink}"/>'
        f'<path d="M0 -270 L2 -244 L0 -228 L-2 -244 Z" fill="{acc}"/>'
        # the axe blade, the back hook and the bands
        f'<path d="M5 -208 L22 -210 L54 -230 L58 -186 L50 -148 L22 -170 L5 -170 Z" fill="{paper}" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M11 -203 L24 -204 L49 -220 L52 -187 L46 -159 L25 -175 L11 -176 Z" fill="{ink}"/>'
        f'<path d="M48 -215 L53.5 -187 L46 -158 L50 -187 Z" fill="{acc}"/>'
        f'<path d="M-5 -206 L-46 -184 L-5 -186 Z" fill="{paper}" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M-7 -170 H7 M-7 -160 H7" stroke="{paper}" stroke-width="3"/>'
        f'</g>'),
    # the zweihander: a long two-hander with a blunt ricasso, parrying hooks and wide curled quillons
    "zweihander": lambda ink, acc, paper: (
        _pommel(ink, paper)
        + f'<path d="M-14 -3.6 L-3 -3.6 L-3 3.6 L-14 3.6 Z" fill="{ink}"/>'
        f'<path d="M-11 -3.6 L-11 3.6 M-7 -3.6 L-7 3.6" stroke="{paper}" stroke-width="1.2"/>'
        # the cross-guard: a bar with its arms curling toward the blade
        f'<path d="M-3 -3 L-3 -19 C-3 -25 3 -28 8 -25 L6 -21.5 C3.5 -23 1.5 -22 1.5 -19 L1.5 19 C1.5 22 3.5 23 6 21.5 L8 25 '
        f'C3 28 -3 25 -3 19 L-3 3 Z" fill="{paper}" stroke="{ink}" stroke-width="2.4" stroke-linejoin="round"/>'
        # the ricasso and its parrying hooks
        f'<path d="M1.5 -4.6 L26 -4.6 L26 4.6 L1.5 4.6 Z" fill="{paper}" stroke="{ink}" stroke-width="2.4"/>'
        f'<path d="M4 -1.6 L24 -1.6 L24 1.6 L4 1.6 Z" fill="{ink}"/>'
        f'<path d="M26 -4.6 L21 -13 L30 -8 Z M26 4.6 L21 13 L30 8 Z" fill="{paper}" stroke="{ink}" stroke-width="2.2" stroke-linejoin="round"/>'
        # the long blade, faceted at the point like the greatsword's
        f'<path d="M26 -8.5 L136 -8.5 L156 0 L136 8.5 L26 8.5 Z" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M31 -4.6 L134 -4.6 L147 0 L134 4.6 L31 4.6 Z" fill="{ink}"/>'
        f'<path d="M36 -1.2 L128 -1.6 L138 0 L128 1.6 L36 1.2 Z" fill="{acc}"/>'),
    "keyboard": lambda ink, acc, paper: (
        _pommel(ink, paper) + f'<path d="M-14 -2 L-4 -2 L-4 2 L-14 2 Z" fill="{ink}"/>'
        + f'<path d="M-4 -15 L90 -15 L94 -11 L94 11 L90 15 L-4 15 Z" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M1 -11 L89 -11 L89 11 L1 11 Z" fill="{ink}"/>'
        + "".join(f'<rect x="{4 + k * 8.4:.1f}" y="{-8 + r * 6}" width="6" height="4" rx="0.8" fill="{acc if (r, k) == (1, 9) else paper}"/>'
                  for r in range(3) for k in range(10))),
}
WEAPONS["greatbow"] = lambda ink, acc, paper: f'<g transform="rotate(90)">{_greatbow(ink, acc, paper)}</g>'
# one a day, Monday to Sunday, in this order (the design board's arsenal shows them the same way)
WEAPONS = {k: WEAPONS[k] for k in ("sword", "zweihander", "axe", "hammer", "halberd", "greatbow", "keyboard")}
WEAPON_NAMES = {"sword": "greatsword", "zweihander": "zweihander", "axe": "greataxe", "hammer": "warhammer",
                "halberd": "halberd", "greatbow": "greatbow", "keyboard": "keyboard"}
# how he carries each one: laid back over the right shoulder, except the bow, held at the grip with its
# limbs arching over the shoulder
CARRY = {"greatbow": "translate(4 -80) rotate(-152) scale(0.85)"}


# the running cape, as in the portfolio's grand opening (intro-art.ts): clasped at the collar, wrapped over his
# shoulder and down his back past the torso, then sweeping back into one pointed tail that lifts in the wind.
# Three shapes with the same commands, so it ripples smoothly from one to the next; w nudges the tail.
def _run_cape(w0, w1, w2, w3):
    return (f"M12 -88 C4 -98 -14 -98 -26 -94 "
            f"C-50 {-96 + w0} -80 {-94 + w1} -104 {-88 + w2} "
            f"Q-114 {-86 + w2} -124 {-82 + w3} "
            f"C-104 {-62 + w3} -70 {-38 + w1} -34 -36 "
            f"L-8 -42 C-2 -60 4 -74 12 -82 Z")


RUN_CAPE = [_run_cape(0, 0, 0, 0), _run_cape(-4, -6, -9, -8), _run_cape(3, 4, 6, 7)]
RUN_FOLD = ["M-10 -86 C-30 -76 -54 -64 -80 -56", "M-10 -86 C-32 -80 -58 -72 -84 -66", "M-10 -86 C-28 -74 -50 -60 -76 -50"]


def el_runner(c, uid, weapon="sword"):
    """El in profile, facing right, feet at (0,0), about 104 units tall. Legs swing from the hip,
    the body bobs twice per stride, the cape ripples, and the weapon (see WEAPONS) rides on his right shoulder."""
    ink, acc, paper = c["ink"], c["accent"], c["paper"]
    leg = ('<path d="M-5 0 L6 0 L7 -20 L5 -44 L-6 -44 L-5 -20 Z" fill="{f}"/>'
           '<path d="M-7 -5 L11 -5 L12 0 L-7 0 Z" fill="{f}"/>')
    torso = "M-11 -46 C-14 -62 -12 -80 -2 -90 L10 -90 C16 -82 16 -62 11 -46 Z"
    held = WEAPONS.get(weapon, WEAPONS["sword"])(ink, acc, paper)
    # laid back over the right shoulder, the business end up and behind him
    sword = f'<g transform="{CARRY.get(weapon, "translate(0 -84) rotate(-155)")}">{held}</g>'
    arm = f'<path d="M4 -84 C8 -76 12 -74 17 -76" fill="none" stroke="{ink}" stroke-width="7" stroke-linecap="round"/>'
    hand = f'<circle cx="17" cy="-76" r="4.8" fill="{ink}"/>'
    return (
        f'<g class="{uid}bob">'
        f'<g transform="translate(0 -44)"><g class="{uid}legB"><g transform="translate(0 44)">{leg.format(f=ink)}</g></g></g>'
        f'<path d="{torso}" fill="{ink}"/>'
        f'<g transform="translate(0 -44)"><g class="{uid}legF"><g transform="translate(0 44)">{leg.format(f=ink)}</g></g></g>'
        # the cape over his back (and the top of the torso), then the weapon on top of it, resting on his shoulder
        f'<path d="{RUN_CAPE[0]}" fill="{acc}" stroke="{ink}" stroke-width="3" stroke-linejoin="round">'
        f'<animate attributeName="d" dur="0.9s" repeatCount="indefinite" values="{";".join(RUN_CAPE + RUN_CAPE[:1])}"/></path>'
        f'<path d="{RUN_FOLD[0]}" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" opacity="0.55">'
        f'<animate attributeName="d" dur="0.9s" repeatCount="indefinite" values="{";".join(RUN_FOLD + RUN_FOLD[:1])}"/></path>'
        f'{sword}'
        # the same head as everywhere else (HAIR, headphones and all), sized for the runner
        f'<g transform="translate(-76 -158) scale(0.5)">{el_head(ink, paper)}</g>'
        f'{arm}{hand}'
        f'</g>'
    )


def runner_css(uid, stride=0.6):
    return (f".{uid}legF{{animation:{uid}sw {stride}s ease-in-out infinite}}"
            f".{uid}legB{{animation:{uid}sw {stride}s ease-in-out infinite;animation-delay:-{stride / 2}s}}"
            f"@keyframes {uid}sw{{0%{{transform:rotate(-36deg)}}50%{{transform:rotate(36deg)}}100%{{transform:rotate(-36deg)}}}}"
            f".{uid}bob{{animation:{uid}bob {stride / 2}s ease-in-out infinite alternate}}"
            f"@keyframes {uid}bob{{from{{transform:translateY(0)}}to{{transform:translateY(-5px)}}}}")


# ---------------------------------------------------------------- the time of day, in your time zone

def period(cfg: dict, name: str | None = None) -> tuple[str, str]:
    """(name, visitor line) for a time of day: the one named, or the one it is now where you live.
    The times and lines are the config's "day" list; api/banner.js reads the same list."""
    day = cfg["day"]
    if name is None and "--period" in sys.argv:  # for previews: --period night
        name = sys.argv[sys.argv.index("--period") + 1]
    if name is None:
        hour = dt.datetime.now(ZoneInfo(cfg["timezone"])).hour
        started = [p for p in day if hour >= p["from"]]
        name = (started[-1] if started else day[-1])["name"]  # before the first one it's still the last (night)
    p = next(p for p in day if p["name"] == name)
    return p["name"], p["says"]


def sky(theme: str, name: str) -> str:
    """The sky behind El, right of the black stripe: sunrise, a high sun, sunset, or stars and a moon."""
    dark = theme == "dark"
    area = '<clipPath id="sky"><polygon points="672,3 827,3 827,297 502,297"/></clipPath>'
    if name == "morning":
        fill = (f'<rect x="0" y="0" width="830" height="300" fill="{"#3B2F22" if dark else "#F6DDB6"}" opacity="0.7"/>'
                f'<circle cx="770" cy="236" r="34" fill="#F2B35B"/>')
    elif name == "sunset":
        fill = (f'<rect x="0" y="0" width="830" height="300" fill="{"#4A2A1C" if dark else "#F3B68A"}" opacity="0.75"/>'
                f'<circle cx="700" cy="250" r="52" fill="#E8693A"/>'
                f'<path d="M560 214 H827 M590 196 H827" stroke="#E8693A" stroke-width="3" opacity="0.5"/>')
    elif name == "night":
        stars = ((612, 40), (700, 26), (742, 92), (806, 128), (650, 118), (780, 196), (690, 168), (812, 24), (560, 180))
        fill = (f'<rect x="0" y="0" width="830" height="300" fill="{"#0B1222" if dark else "#2E3F66"}"/>'
                + "".join(f'<circle class="tw{i % 3}" cx="{x}" cy="{y}" r="{1.6 + (i % 3) * 0.6}" fill="#F4EFE4"/>'
                          for i, (x, y) in enumerate(stars))
                + '<path d="M806 40 A22 22 0 1 0 806 84 A17 17 0 1 1 806 40 Z" fill="#F4EFE4"/>')
    else:  # day
        rays = "".join(f'<path d="M{802 + 22 * math.cos(k * math.pi / 4):.1f} {44 + 22 * math.sin(k * math.pi / 4):.1f} '
                       f'L{802 + 30 * math.cos(k * math.pi / 4):.1f} {44 + 30 * math.sin(k * math.pi / 4):.1f}" '
                       f'stroke="#F2B35B" stroke-width="3" stroke-linecap="round"/>' for k in range(8))
        fill = f'<g class="spin">{rays}</g><circle cx="802" cy="44" r="15" fill="#F2B35B"/>'
    return f"<defs>{area}</defs><g clip-path=\"url(#sky)\">{fill}</g>"


# ---------------------------------------------------------------- the shield by the rock

# a heater shield: flat top, straight upper sides, curving into a point. origin = the middle of the top edge
HEATER = "M-36 0 L36 0 L36 30 C36 58 20 78 0 92 C-20 78 -36 58 -36 30 Z"
HEATER_IN = "M-28 7 L28 7 L28 31 C28 54 15 71 0 82 C-15 71 -28 54 -28 31 Z"


def stuck_arrow(c: dict, x: float, y: float, ang: float, ln: float = 44) -> str:
    """An arrow buried in a surface at (x, y), its shaft sticking out at ang degrees, with cracks where it hit."""
    a = math.radians(ang)
    ex, ey = x + ln * math.cos(a), y + ln * math.sin(a)
    ink = c["ink"]
    cracks = "".join(f'<path d="M{x} {y} l{7 * math.cos(math.radians(k)):.1f} {7 * math.sin(math.radians(k)):.1f}" '
                     f'stroke="{ink}" stroke-width="2" stroke-linecap="round"/>' for k in (ang + 150, ang + 210))
    return (cracks
            + f'<line x1="{x}" y1="{y}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{ink}" stroke-width="4" stroke-linecap="round"/>'
            f'<g transform="translate({ex:.1f} {ey:.1f}) rotate({ang})">'
            f'<path d="M2 0 L-18 0 L-4 -9 L2 -9 Z" fill="{c["accent"]}" stroke="{ink}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<path d="M2 0 L-18 0 L-4 9 L2 9 Z" fill="{c["card"]}" stroke="{ink}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<path d="M2 -3 L7 0 L2 3" fill="none" stroke="{ink}" stroke-width="2.5"/></g>')


def shield_by_rock(c: dict) -> str:
    """El's heater shield, split cream and cyan, propped on its point in front of the rock with two arrows in it.
    Drawn in el_on_rock's coordinates."""
    ink = c["ink"]
    return (f'<path d="M58 334 L108 334" stroke="{ink}" stroke-width="4" stroke-linecap="round" opacity="0.4"/>'
            '<g transform="translate(64 243) rotate(-10)">'
            f'<path d="{HEATER}" fill="{c["card"]}"/>'
            f'<path d="M0 0 L36 0 L36 30 C36 58 20 78 0 92 Z" fill="{c["accent"]}"/>'
            f'<path d="{HEATER}" fill="none" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="{HEATER_IN}" fill="none" stroke="{ink}" stroke-width="2.5"/>'
            f'<line x1="0" y1="0" x2="0" y2="92" stroke="{ink}" stroke-width="3"/>'
            + stuck_arrow(c, -12, 26, -150) + stuck_arrow(c, 10, 46, -115) + "</g>")


# ---------------------------------------------------------------- banner

def banner(theme: str, cfg: dict, when: str | None = None) -> str:
    """The banner, with the sky for `when` (a time of day from the config), or for now."""
    c = PALETTES[theme]
    when, says = period(cfg, when)
    first, _, last = cfg["name"].upper().rpartition(" D. ")
    line1, line2 = (first, "D. " + last) if first else (cfg["name"].upper(), "")
    body = (
        f"<defs>{dots('bd', c['accent'], 9, 1.5, 0.35)}{dots('bink', c['ink'])}</defs>"
        f'<rect x="1.5" y="1.5" width="827" height="297" fill="{c["card"]}" stroke="{c["ink"]}" stroke-width="3"/>'
        '<rect x="1.5" y="1.5" width="827" height="297" fill="url(#bd)"/>'
        f'<polygon points="560,3 640,3 470,297 390,297" fill="{c["accent"]}"/>'
        f'<polygon points="655,3 672,3 502,297 485,297" fill="{c["ink"]}"/>'
        + text(cfg["episode"], 40, 64, 15, c["muted"], wght=700, ls=2.5)
        + text(line1, 38, 150, 92, c["ink"], wght=700, wdth=70)
        + text(line2, 38, 232, 92, c["ink"], wght=700, wdth=70)
    )
    tag_w = text_width(cfg["tagline"], 14, 700, 100, 1) + 24
    body += f'<rect x="40" y="252" width="{tag_w:.0f}" height="28" fill="{c["ink"]}"/>' + text(cfg["tagline"], 52, 271, 14, c["card"], ls=1)
    body += sky(theme, when)
    body += f'<g transform="translate(585 50) scale(0.735)">{el_on_rock(c, "b")}{shield_by_rock(c)}</g>'
    # the comment that pops in from nowhere
    body += (
        '<g class="pop">'
        f'<rect x="420" y="40" width="{text_width(says, 12, 600) + 22:.0f}" height="46" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
        + text("@visitor", 430, 57, 10.5, c["accent"], wght=700)
        + text(says, 430, 76, 12, c["ink"], wght=600)
        + "</g>"
    )
    css = (
        ".pop{opacity:0;transform-origin:504px 63px;animation:pop 6s infinite}"
        "@keyframes pop{0%,20%{opacity:0;transform:scale(.6) rotate(-4deg)}27%{opacity:1;transform:scale(1.06) rotate(1deg)}"
        "31%,85%{opacity:1;transform:scale(1) rotate(0)}92%,100%{opacity:0;transform:scale(.9)}}"
        ".spin{transform-origin:802px 44px;animation:spin 30s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
        ".tw0,.tw1,.tw2{animation:tw 3s ease-in-out infinite alternate}.tw1{animation-delay:-1s}.tw2{animation-delay:-2s}"
        "@keyframes tw{from{opacity:1}to{opacity:.25}}"
    )
    return doc(W, 300, body, f"{cfg['name']}: {cfg['tagline'].lower()} El, seen from behind, stands on a rock with his cape in the wind and an arrow-struck shield propped against it, {when} sky behind him.", css)


# ---------------------------------------------------------------- typing line

def typing(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    size, char_ms, hold_ms, gap_ms = 20, 70, 1800, 350
    cw = size * MONO_ADV
    phrases = ["> " + p for p in cfg["typing"]]
    longest = max(len(p) for p in phrases)
    x0 = (W - (longest + 1) * cw) / 2
    spans = []  # (start_ms, end_ms) per phrase: type, hold, delete
    t = 0
    for p in phrases:
        n = len(p) - 2
        dur = n * char_ms + hold_ms + n * (char_ms // 2) + gap_ms
        spans.append((t, t + dur))
        t += dur
    total = t
    body, css = "", ".caret{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    for i, (p, (s, e)) in enumerate(zip(phrases, spans)):
        n = len(p) - 2

        def pct(ms):
            return f"{ms / total * 100:.3f}%"

        def at(ms, chars):
            return f"{pct(ms)}{{transform:translateX({chars * cw:.1f}px)}}"

        kf = [at(0, 2)]
        if s > 0:
            kf.append(at(s - 1, 2))
        kf += [at(s + j * char_ms, 2 + j) for j in range(n + 1)]
        hold_end = s + n * char_ms + hold_ms
        kf += [at(hold_end + j * (char_ms // 2), 2 + n - j) for j in range(n + 1)]
        kf.append(f"100%{{transform:translateX({2 * cw:.1f}px)}}")
        dur = f"{total / 1000:.2f}s"
        css += f".m{i}{{animation:w{i} {dur} steps(1,end) infinite}}@keyframes w{i}{{{''.join(kf)}}}"
        # only the phrase on screen shows its cursor
        vis = f"0%{{opacity:{1 if s == 0 else 0}}}{pct(s)}{{opacity:1}}{pct(e)}{{opacity:0}}100%{{opacity:0}}"
        css += f".v{i}{{animation:v{i} {dur} steps(1,end) infinite}}@keyframes v{i}{{{vis}}}"
        # the clip rect sits just left of the text; sliding it right reveals the phrase
        body += (
            f'<clipPath id="cp{i}"><rect class="m{i}" x="{x0 - 1200:.1f}" y="4" width="1200" height="34"/></clipPath>'
            f'<g clip-path="url(#cp{i})">' + text(p, x0, 28, size, c["accent"], mono=True, bold=True) + "</g>"
            f'<g class="v{i}"><g class="m{i}"><rect class="caret" x="{x0:.1f}" y="10" width="{cw * 0.9:.1f}" height="22" fill="{c["accent"]}"/></g></g>'
        )
    css += f"@media (prefers-reduced-motion:reduce){{.m0{{transform:translateX({len(phrases[0]) * cw:.1f}px)}}.v0{{opacity:1}}}}"
    return doc(W, 40, body, "Typing: " + "; ".join(cfg["typing"]), css)


# ---------------------------------------------------------------- about tiles

LIVE_FALLBACK = {"latest_repo": {"value": "Something new", "note": "Shows up after the next refresh"},
                 "this_week": {"value": "Counting...", "note": "Shows up after the next refresh"}}


def about_tiles(cfg: dict) -> list[dict]:
    """The config's About tiles, with the "live" ones filled from what live.py found."""
    made = ROOT / "generated" / "live.json"
    found = json.loads(made.read_text(encoding="utf-8")) if made.exists() else {}
    return [{**a, **found.get(a["live"], LIVE_FALLBACK.get(a["live"], {}))} if a.get("live") else a for a in cfg["about"]]


def fit(s: str, size: float, max_w: float, **kw) -> str:
    """s, cut with an ellipsis if it is wider than max_w."""
    if text_width(s, size, **kw) <= max_w:
        return s
    while s and text_width(s + "…", size, **kw) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def about(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    cols, tile_h, gap = 3, 92, 3
    x0, y0, w = 0, 0, W - 12
    tw = (w - 6 - gap * (cols - 1)) / cols
    rows = (len(cfg["about"]) + cols - 1) // cols
    h = 6 + rows * tile_h + (rows - 1) * gap
    body = f"<defs>{dots('ad', c['ink'])}</defs>"
    body += f'<rect x="12" y="12" width="{w}" height="{h}" fill="url(#ad)"/>'
    body += f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{c["ink"]}"/>'
    tiles = about_tiles(cfg)
    for i, a in enumerate(tiles):
        r, col = divmod(i, cols)
        x = x0 + 3 + col * (tw + gap)
        y = y0 + 3 + r * (tile_h + gap)
        hi = a.get("highlight")
        bg, fg, tag = (c["ink"], c["card"], c["on_ink_accent"]) if hi else (c["card"], c["ink"], c["accent"])
        body += f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{tile_h}" fill="{bg}"/>'
        body += text("// " + a["key"], x + 18, y + 26, 11.5, tag, mono=True, bold=True)
        body += text(fit(a["value"], 27, tw - 36, wght=700, wdth=70), x + 18, y + 56, 27, fg, wght=700, wdth=70)
        body += text(fit(a["note"], 11.5, tw - 36, wght=400), x + 18, y + 77, 11.5, fg, wght=400, extra=' opacity="0.8"')
    label = "About El: " + "; ".join(f"{a['key'].replace('_', ' ')}: {a['value']}, {a['note']}" for a in tiles)
    return doc(W, h + 12, body, label)


# ---------------------------------------------------------------- the commit joke

def commit(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    cw = (W - 16 - 12) / 2
    body = (
        f'<g transform="rotate(-1.2 {cw/2+6} 60)">'
        f'<rect x="6" y="14" width="{cw}" height="78" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
        + text("$", 26, 46, 15, c["accent"], mono=True, bold=True)
        + text('git commit -m "fix stuff"', 26 + 15 * MONO_ADV * 2, 46, 15, c["ink"], mono=True, bold=True)
        + text("1 file changed · it works, don't touch it", 26, 72, 14, c["muted"], wght=400)
        + "</g>"
        f'<g transform="rotate(1 {cw*1.5+22} 60)">'
        f'<rect x="{cw+22}" y="14" width="{cw}" height="78" fill="{c["ink"]}" stroke="{c["ink"]}" stroke-width="3"/>'
        + text("Just kidding. These days it's:", cw + 42, 44, 14, c["card"], wght=700)
        + text("$", cw + 42, 70, 11, c["on_ink_accent"], mono=True, bold=True)
        + text('git commit -m "feat(profile): match the portfolio"', cw + 42 + 11 * MONO_ADV * 2, 70, 11, c["card"], mono=True, bold=True)
        + "</g>"
    )
    return doc(W, 108, body, 'git commit -m "fix stuff". Just kidding. These days it\'s: git commit -m "feat(profile): match the portfolio"')


# ---------------------------------------------------------------- dodge.exe

# The portfolio's Pocket runner (src/scripts/dodge.ts) in its demo: a Game Boy style screen in four cyans, El with
# his headphones and cape running by himself, hopping the walking bugs and the low moth, staying under the fly.
# The portfolio plays it live with JavaScript; GitHub can't, so here one loop of the demo is worked out ahead
# of time and played back with CSS. The README links the picture to the portfolio, where it's playable.

# the screen, in the portfolio's pixels, and its physics (dodge.ts: W, H, GROUND, EL_X, SPEED, GRAVITY, JUMP_V)
PK_W, PK_H, PK_GROUND, PK_EL_X = 256, 96, 80, 30
PK_SPEED, PK_GRAVITY, PK_JUMP_V = 92, 620, 222
PK_AIR = 2 * PK_JUMP_V / PK_GRAVITY                 # 0.716 s in the air
PK_PEAK = PK_JUMP_V ** 2 / (2 * PK_GRAVITY)         # 39.7 px up
PK_TRIGGER = 12 + PK_SPEED * 0.05                   # the demo jumps when a bug is this close (dodge.ts step())
# lightest, light, mid, darkest; the dark theme flips the ramp so the screen glows
PK_RAMP = {"light": ["#E2F0EE", "#9CCBD1", "#2F7F92", "#0F2E36"], "dark": ["#0F2328", "#1F4852", "#4FA4B9", "#D6EEF2"]}
# one loop of the demo: (bug, where it starts along the track). Walkers and flyers mixed, never crowding,
# so El always lands before the next jump and no walker needs a jump while the fly is overhead.
PK_SEQ = [("ladybug", 0), ("slime", 150), ("caterpillar", 300), ("moth", 480), ("snail", 640), ("fly", 800),
          ("ladybug", 980), ("slime", 1110), ("moth", 1270), ("caterpillar", 1420), ("snail", 1590), ("fly", 1750)]
PK_LOOP = 1930


def pixels(rows: list[str], pal: dict[str, str], x: int = 0, y: int = 0) -> str:
    """A pixel sprite as one path per colour: each horizontal run of a colour is one small rectangle."""
    runs: dict[str, list[str]] = {}
    for r, row in enumerate(rows):
        q = 0
        while q < len(row):
            col = pal.get(row[q])
            n = 1
            while q + n < len(row) and row[q + n] == row[q]:
                n += 1
            if col:
                runs.setdefault(col, []).append(f"M{x + q} {y + r}h{n}v1h-{n}z")
            q += n
    return "".join(f'<path d="{"".join(d)}" fill="{col}"/>' for col, d in runs.items())


def pixel_text(s: str, col: str, x: float, y: float, k: int = 1) -> str:
    """Words in the 3x5 pixel font, k pixels per font pixel."""
    glyphs = [pocket_sprites.FONT.get(ch, pocket_sprites.FONT[" "]) for ch in s]
    # row r of each glyph is 3 pixels; a blank column between letters
    rows = [".".join(g[r * 3:r * 3 + 3] for g in glyphs).replace("1", "#").replace("0", ".") for r in range(5)]
    return f'<g transform="translate({x} {y}) scale({k})">{pixels(rows, {"#": col})}</g>'


def pk_text_w(s: str, k: int = 1) -> int:
    return len(s) * 4 * k - k


def _frames(cls: str, frames: list[str]) -> str:
    """Frames of a little animation, stacked; CSS (see _frames_css) shows one at a time."""
    return "".join(f'<g class="{cls} f{k}">{f}</g>' for k, f in enumerate(frames))


def _frames_css(anims: dict[str, tuple[int, float]]) -> str:
    """CSS for _frames: {class: (frames, period in s)}. Frame k of n shows during the k-th n-th of each period
    (one keyframe set per n, offset per frame). Every frame but the first starts hidden, so a still shows frame 0."""
    counts = sorted({n for n, _ in anims.values()})
    css = "".join(f"@keyframes fr{n}{{0%{{visibility:visible}}{100 / n:.3f}%,100%{{visibility:hidden}}}}" for n in counts)
    css += ",".join(f".f{k}" for k in range(1, max(counts))) + "{visibility:hidden}"
    for cls, (n, period) in anims.items():
        css += f".{cls}{{animation:fr{n} {period:.3f}s steps(1,end) infinite}}"
        css += "".join(f".{cls}.f{k}{{animation-delay:-{((n - k) % n) * period / n:.3f}s}}" for k in range(n))
    return css


def _pk_bug(kind: str, P: list[str]) -> tuple[str, int]:
    """One bug, drawn with its feet (or its flying height) on the ground line at x = 0. Returns (svg, width)."""
    S = pocket_sprites
    b = S.BUGS[kind]
    pal = {"w": P[0], "l": P[1], "m": P[2], "#": P[3]}
    bottom = PK_GROUND - b["lift"]
    if kind == "caterpillar":
        # the segments ripple, each a pixel out of step with its neighbour (2 frames); 404 on its back
        frames = []
        for f in (0, 1):
            g = ""
            for i in (2, 1, 0):
                sx, up = 8 + i * 8, (f + i) % 2
                g += pixels(S.CATERPILLAR_SEG, pal, sx, bottom - 9 - up)
                g += pixel_text("404"[i], P[3], sx + 3, bottom - 7 - up)
                g += f'<path d="M{sx + 2 + up * 2} {bottom - 1}h1v1h-1z M{sx + 6 - up * 2} {bottom - 1}h1v1h-1z" fill="{P[3]}"/>'
            frames.append(g + pixels(S.CATERPILLAR_HEAD, pal, 0, bottom - 10 - f))
        return _frames("acat", frames), b["w"]
    if kind == "snail":
        # its shell is a loading spinner: a dotted ring with a dark head and a mid tail going round (8 frames)
        sx, sy = 6, bottom - b["h"] - 1
        frames = []
        for head in range(8):
            dots = ""
            for k in range(8):
                back = (head - k + 8) % 8
                if back >= 3 and k % 2:
                    continue
                a = k / 8 * math.tau
                dots += (f'<path d="M{round(sx + 5 + math.cos(a) * 3.2)} {round(sy + 5 + math.sin(a) * 3.2)}h1v1h-1z" '
                         f'fill="{P[3] if back == 0 else P[2]}"/>')
            frames.append(dots)
        body = pixels(S.SNAIL_BODY, pal, 0, bottom - b["h"]) + pixels(S.SNAIL_SHELL, pal, sx, sy)
        return body + _frames("asnail", frames), b["w"]
    frames = [pixels(f, pal, 0, bottom - b["h"]) + (pixel_text(b["label"], P[0], 2, bottom - b["h"] + 5) if b.get("label") else "")
              for f in b["frames"]]
    g = _frames(f"a{kind}", frames)
    return (f'<g class="bob{kind}">{g}</g>' if kind in ("moth", "fly") else g), b["w"]


def _pk_el(P: list[str], frame: int, x: int = PK_EL_X) -> str:
    """Pocket El standing on the ground (dodge.ts drawEl): cape, then him, then his legs. frame 2 is the jump."""
    S = pocket_sprites
    pal = {"#": P[3], "o": P[0], "h": P[2], "b": P[1], "c": P[2]}
    top = PK_GROUND - 18
    return (pixels(S.CAPE[frame], pal, x - 4, top + (8 if frame == 2 else 9))
            + pixels(S.EL_TOP, pal, x, top) + pixels(S.EL_LEGS[frame], pal, x, top + 14))


PK_START = PK_W + 8                                 # bugs come in just past the right edge


def _pk_timeline() -> tuple[float, list[float], list[float]]:
    """One loop of the demo: (its length in s, when El jumps, when each bug is behind him and counts).
    Checks the loop plays like the portfolio's demo: he lands before the next jump, and never needs to
    jump while the fly is overhead. Edit PK_SEQ and this tells you if a gap got too tight."""
    T = PK_LOOP / PK_SPEED
    jumps, passes, flies = [], [], []
    for kind, off in PK_SEQ:
        x0 = PK_START + off
        passes.append(((x0 + pocket_sprites.BUGS[kind]["w"] - (PK_EL_X + 2)) / PK_SPEED) % T)
        if kind == "fly":                                           # he runs under the fly
            flies.append(((x0 - PK_EL_X) / PK_SPEED) % T)
        else:
            jumps.append(((x0 - (PK_EL_X + 10) - PK_TRIGGER) / PK_SPEED) % T)
    jumps.sort()
    for a, b in zip(jumps, jumps[1:] + [jumps[0] + T]):
        if b - a < PK_AIR + 0.1:
            raise ValueError(f"dodge.exe: jumps at {a:.2f}s and {b % T:.2f}s overlap; spread PK_SEQ out")
    for f in flies:
        if any(abs((j - f + T / 2) % T - T / 2) < PK_AIR for j in jumps):
            raise ValueError(f"dodge.exe: El would jump into the fly at {f:.2f}s; spread PK_SEQ out")
    return T, jumps, passes


def _pk_score(T: float, passes: list[float], col: str) -> tuple[str, str]:
    """The title bar's count: one label per number, each shown between two passes. Returns (svg, css)."""
    g, css = "", ""
    bounds = [0.0] + sorted(passes) + [T]
    for n in range(len(passes) + 1):
        a, b = bounds[n], bounds[n + 1]
        if b - a < 0.01:
            continue
        vis = (f"0%{{visibility:{'visible' if a == 0 else 'hidden'}}}"
               + (f"{a / T * 100:.3f}%{{visibility:visible}}" if a > 0 else "")
               + f"{b / T * 100:.3f}%{{visibility:hidden}}100%{{visibility:hidden}}")
        css += f".n{n}{{animation:n{n} {T:.2f}s steps(1,end) infinite}}@keyframes n{n}{{{vis}}}"
        g += f'<g class="n n{n}">' + text(f"{n:03d}", 0, 0, 13, col, mono=True, bold=True) + "</g>"
    return g, ".n{visibility:hidden}" + css


def dodge(theme: str, cfg: dict) -> str:
    c, P = PALETTES[theme], PK_RAMP[theme]
    T, jumps, passes = _pk_timeline()                   # one loop, about 21 s

    def pct(t):
        return f"{(t % T) / T * 100:.3f}%"

    # the track: every bug of the loop, twice, so the screen never empties at the seam
    track = ""
    for kind, off in PK_SEQ:
        g, _ = _pk_bug(kind, P)
        for k in (-1, 0):
            track += f'<g transform="translate({PK_START + off + k * PK_LOOP} 0)">{g}</g>'

    # the jump: a true parabola, up with a quadratic ease-out, down with the matching ease-in
    up, down = "cubic-bezier(.33,.67,.67,1)", "cubic-bezier(.33,0,.67,.33)"
    kf = ["0%{transform:translateY(0)}"]
    air = ["0%{visibility:hidden}"]
    ground = ["0%{visibility:visible}"]
    for j in jumps:
        kf += [f"{pct(j)}{{transform:translateY(0);animation-timing-function:{up}}}",
               f"{pct(j + PK_AIR / 2)}{{transform:translateY(-{PK_PEAK:.1f}px);animation-timing-function:{down}}}",
               f"{pct(j + PK_AIR)}{{transform:translateY(0)}}"]
        air += [f"{pct(j)}{{visibility:visible}}", f"{pct(j + PK_AIR)}{{visibility:hidden}}"]
        ground += [f"{pct(j)}{{visibility:hidden}}", f"{pct(j + PK_AIR)}{{visibility:visible}}"]
    kf.append("100%{transform:translateY(0)}")

    score_g, score_css = _pk_score(T, passes, c["on_panel"])

    # the scenery: far hills and clouds drift slower than the ground (dodge.ts draw())
    hills = "".join(f'<path d="M{x} {PK_GROUND} l22 -22 l8 6 l14 -12 l26 28 Z"/>' for x in range(-64, PK_W + 128, 64))
    clouds = "".join(f'<path d="M{x} 16h18v4h-18z M{x + 4} 12h8v4h-8z M{x + 50} 28h14v3h-14z M{x + 53} 25h6v3h-6z"/>'
                     for x in range(20, PK_W + 320, 160))
    specks = "".join(f'M{x} {PK_GROUND + 5}h4v1h-4z M{x + 13} {PK_GROUND + 9}h2v1h-2z ' for x in range(-24, PK_W + 48, 24))
    el = (f'<g class="elrun">{_frames("aleg", [_pk_el(P, 0), _pk_el(P, 1)])}</g>'
          f'<g class="eljump">{_pk_el(P, 2)}</g>')
    shadow = (f'<path class="elrun" d="M{PK_EL_X + 1} {PK_GROUND + 1}h10v1h-10z" fill="{P[2]}"/>'
              f'<path class="eljump" d="M{PK_EL_X + 3} {PK_GROUND + 1}h6v1h-6z" fill="{P[2]}"/>')
    hud = (f'<g class="blink">{pixel_text("DEMO", P[3], 6, 5)}</g>'
           + pixel_text("CLICK TO PLAY", P[3], (PK_W - pk_text_w("CLICK TO PLAY", 2)) // 2, 30, 2))
    grid_op = "0.18" if theme == "dark" else "0.08"
    lcd = (f'<pattern id="lcd" width="1" height="1" patternUnits="userSpaceOnUse">'
           f'<path d="M0 0.92h1v0.08h-1z M0.92 0h0.08v1h-0.08z" fill="#000" opacity="{grid_op}"/></pattern>')

    # layout: the title bar, the screen under it (the portfolio's shape), the caption
    bar_h, inner_w = 34, W - 20
    screen_h = inner_w * PK_H / PK_W
    h = bar_h + screen_h + 3
    score_x = W - 14 - 14 - 13 * MONO_ADV * 3
    body = (
        f'<rect x="0" y="0" width="{W - 14}" height="{bar_h}" fill="{c["panel_bg"]}"/>'
        + text("dodge.exe", 14, 22, 13, c["on_panel"], wght=700)
        + text("bugs dodged ", score_x - 6, 22, 13, c["on_panel"], wght=500, anchor="end")
        + f'<g transform="translate({score_x:.1f} 22)">{score_g}</g>'
        + f'<rect x="1.5" y="{bar_h}" width="{W - 17}" height="{screen_h + 1.5:.1f}" fill="{P[0]}" stroke="{c["ink"]}" stroke-width="3"/>'
        + f'<rect x="0" y="{bar_h - 1.5}" width="{W - 14}" height="3" fill="{c["panel_bg"]}"/>'
        + f'<svg x="3" y="{bar_h}" width="{inner_w}" height="{screen_h:.1f}" viewBox="0 0 {PK_W} {PK_H}" overflow="hidden" shape-rendering="crispEdges">'
        f'<defs>{lcd}</defs>'
        f'<rect width="{PK_W}" height="{PK_H}" fill="{P[0]}"/>'
        f'<g class="hills" fill="{P[1]}">{hills}</g><g class="clouds" fill="{P[1]}">{clouds}</g>'
        f'<rect x="0" y="{PK_GROUND}" width="{PK_W}" height="2" fill="{P[3]}"/>'
        f'<path class="specks" d="{specks}" fill="{P[2]}"/>'
        f'<g class="track">{track}</g>{shadow}<g class="guy">{el}</g>{hud}'
        f'<rect width="{PK_W}" height="{PK_H}" fill="url(#lcd)"/></svg>'
    )
    cap_y = h + 22
    body += text("Shipping, one bug at a time.", 2, cap_y, 13, c["muted"], wght=500)
    body += text(" Click to play it on the portfolio.", 2 + text_width("Shipping, one bug at a time.", 13, wght=500), cap_y, 13, c["muted"], wght=400)
    # a still for reduced motion: El mid-jump over a slime, as on the portfolio
    slime_off = next(off for kind, off in PK_SEQ if kind == "slime")
    still_x = PK_START + slime_off - (PK_EL_X + 4)
    css = (
        f".track{{animation:track {T:.3f}s linear infinite}}@keyframes track{{to{{transform:translateX(-{PK_LOOP}px)}}}}"
        f".hills{{animation:hills {64 / (PK_SPEED * 0.15):.3f}s linear infinite}}@keyframes hills{{to{{transform:translateX(-64px)}}}}"
        f".clouds{{animation:clouds {160 / (PK_SPEED * 0.08):.3f}s linear infinite}}@keyframes clouds{{to{{transform:translateX(-160px)}}}}"
        f".specks{{animation:specks {24 / PK_SPEED:.4f}s linear infinite}}@keyframes specks{{to{{transform:translateX(-24px)}}}}"
        f".guy{{animation:jump {T:.3f}s linear infinite}}@keyframes jump{{{''.join(kf)}}}"
        f".eljump{{visibility:hidden;animation:air {T:.3f}s steps(1,end) infinite}}@keyframes air{{{''.join(air)}}}"
        f".elrun{{animation:ground {T:.3f}s steps(1,end) infinite}}@keyframes ground{{{''.join(ground)}}}"
        # frame rates as in dodge.ts: legs flip every 0.1 s, the bugs at their own fps
        + _frames_css({"aleg": (2, 0.2), "aladybug": (2, 2 / 8), "aslime": (2, 2 / 3), "amoth": (2, 2 / 7),
                       "afly": (2, 2 / 16), "acat": (2, 2 / 6), "asnail": (8, 8 / 10)})
        # the flyers bob a pixel, at dodge.ts's rates: the moth sin(5t), the fly sin(9t)
        + f".bobmoth{{animation:bobm {math.tau / 5:.3f}s steps(1,end) infinite}}@keyframes bobm{{0%{{transform:translateY(0)}}25%{{transform:translateY(-1px)}}50%{{transform:translateY(0)}}75%{{transform:translateY(1px)}}}}"
        + f".bobfly{{animation:bobf {math.tau / 9:.3f}s steps(1,end) infinite}}@keyframes bobf{{0%{{transform:translateY(0)}}50%{{transform:translateY(-1px)}}}}"
        + ".blink{animation:blink 1s steps(1,end) infinite}@keyframes blink{50%{visibility:hidden}}"
        + score_css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
        f".track{{transform:translateX(-{still_x}px)}}.guy{{transform:translateY(-26px)}}.elrun{{visibility:hidden}}.eljump{{visibility:visible}}.n0{{visibility:visible}}}}"
    )
    label = ("dodge.exe: a Game Boy style screen in four shades of cyan. El, with his headphones and cape, runs by himself and "
             "hops the bugs (a ladybug, a 404 caterpillar, an ERR slime, a loading snail, a low moth) and runs under a fly, "
             "counting the bugs he dodges. Click to play it on the portfolio.")
    return doc(W, cap_y + 8, body, label, css)


# ---------------------------------------------------------------- work-in-progress strip

def wip(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    w = cfg.get("wip", {})
    h, band = 76, 18
    period = 36
    stripes = "".join(
        f'<polygon points="{x},0 {x + period / 2},0 {x + period / 2 - band},{band} {x - band},{band}" fill="{c["accent"]}"/>'
        for x in range(-period, W + 2 * period, period))

    def tape(y, rot, cls):
        return (f'<g transform="rotate({rot} {W / 2} {y + band / 2})"><rect x="-20" y="{y}" width="{W + 40}" height="{band}" fill="{c["ink"]}"/>'
                f'<svg x="-20" y="{y}" width="{W + 40}" height="{band}" overflow="hidden"><g class="{cls}">{stripes}</g></svg></g>')

    title, note = w.get("title", "WORK IN PROGRESS"), w.get("note", "")
    tw = max(text_width(title, 26, 700, 70), text_width(note, 12, mono=True)) + 96
    bx = (W - tw) / 2
    body = (tape(6, -0.8, "s1") + tape(h - band - 6, 0.6, "s2")
            + f'<rect x="{bx + 6}" y="14" width="{tw}" height="{h - 22}" fill="{c["ink"]}"/>'
            + f'<rect x="{bx}" y="8" width="{tw}" height="{h - 22}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
            + f'<circle class="blink" cx="{bx + 22}" cy="{30}" r="6" fill="{c["accent"]}"/>'
            + text(title, bx + 38, 39, 26, c["ink"], wght=700, wdth=70)
            + text(note, bx + 38, 58, 12, c["muted"], mono=True))
    css = (f".s1{{animation:slide 2.4s linear infinite}}.s2{{animation:slide 2.4s linear infinite reverse}}"
           f"@keyframes slide{{to{{transform:translateX({period}px)}}}}"
           ".blink{animation:blink 1.2s steps(1) infinite}@keyframes blink{50%{opacity:.15}}")
    return doc(W, h, body, f"{title}: {note}", css)


# ---------------------------------------------------------------- section headings and footer

HEADINGS = {"stats": "STATS", "activity": "RECENT ACTIVITY", "stack": "STACK", "gallery": "THE GALLERY"}


def heading(theme: str, cfg: dict, title: str) -> str:
    c = PALETTES[theme]
    body = (f'<polygon points="8,6 22,6 16,38 2,38" fill="{c["accent"]}"/>'
            + text(title, 34, 35, 34, c["ink"], wght=700, wdth=70))
    return doc(W, 44, body, title)


def footer(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    body = (f'<rect width="{W}" height="36" fill="{c["ink"]}"/>'
            + text("main · 0 errors · EOF", 14, 23, 12, c["card"], mono=True)
            + text("Thanks for scrolling. The full story is on the portfolio.", W - 14, 23, 12, c["card"], mono=True, anchor="end"))
    return doc(W, 36, body, "End of file. Thanks for scrolling. The full story is on the portfolio.")


BUILDERS = {"wip": wip, "banner": banner, "typing": typing, "about": about, "commit": commit, "dodge": dodge, "footer": footer}
BUILDERS.update({f"h-{key}": functools.partial(heading, title=title) for key, title in HEADINGS.items()})

if __name__ == "__main__":
    cfg = config()
    args = sys.argv[1:]
    if "--period" in args:  # preview a time of day: python scripts/art.py banner --period night
        i = args.index("--period")
        args = args[:i] + args[i + 2:]
    only = args or list(BUILDERS)
    for name in only:
        for theme in THEMES:
            p = write(name, theme, BUILDERS[name](theme, cfg))
            print(f"{p.relative_to(p.parents[1])}  {p.stat().st_size // 1024} KB")
    if "banner" in only:
        # every sky, so api/banner.js can serve the right one the moment someone opens the profile
        for when in (p["name"] for p in cfg["day"]):
            for theme in THEMES:
                p = write(f"banner-{when}", theme, banner(theme, cfg, when))
                print(f"{p.relative_to(p.parents[1])}  {p.stat().st_size // 1024} KB")
