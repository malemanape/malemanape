"""Static art for the profile README. Run once (and again after editing profile.config.json):

    python scripts/art.py            # everything except the ASCII gallery
    python scripts/gallery.py        # the dense ASCII gallery (needs rsvg-convert + Pillow)

Writes assets/<name>-light.svg and assets/<name>-dark.svg.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.svgkit import (MONO_ADV, MONO_STACK, PALETTES, ROOT, THEMES, config, doc, dots, frames_css, panel,
                        text, text_width, write)

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
        out += f'<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in core) + f' Z" fill="{ink}"/>'
        inlay = C[2:11]
        out += f'<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in inlay) + f'" fill="none" stroke="{acc}" stroke-width="1.8" stroke-linecap="round"/>'
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
# the lineup, in order (the design board's weapon sheet shows them the same way)
WEAPONS["greatbow"] = lambda ink, acc, paper: f'<g transform="rotate(90)">{_greatbow(ink, acc, paper)}</g>'
# one a day, Monday to Sunday (the design board's arsenal shows them the same way)
WEAPONS = {k: WEAPONS[k] for k in ("sword", "zweihander", "axe", "hammer", "halberd", "greatbow", "keyboard")}
WEAPON_NAMES = {"sword": "greatsword", "zweihander": "zweihander", "axe": "greataxe", "hammer": "warhammer",
                "halberd": "halberd", "greatbow": "greatbow", "keyboard": "keyboard"}
# how he carries each one: laid back over the right shoulder, except the bow, held at the grip with its
# limbs arching over the shoulder
CARRY = {"greatbow": "translate(4 -80) rotate(-152) scale(0.85)"}


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
        # the same cape as everywhere else (CAPE_A/B and its fold, as on the portfolio), mirrored to stream behind him
        f'<g transform="translate(-2 -88) scale(-0.38 0.38) translate(-170 -140)">'
        f'<path d="{CAPE_A}" fill="{acc}" stroke="{ink}" stroke-width="10" stroke-linejoin="round">'
        f'<animate attributeName="d" dur="0.6s" repeatCount="indefinite" values="{CAPE_A};{CAPE_B};{CAPE_A}"/></path>'
        f'<path d="{FOLD_A}" fill="none" stroke="{ink}" stroke-width="7" stroke-linecap="round" opacity="0.55">'
        f'<animate attributeName="d" dur="0.6s" repeatCount="indefinite" values="{FOLD_A};{FOLD_B};{FOLD_A}"/></path></g>'
        f'{sword}'
        f'<path d="{torso}" fill="{ink}"/>'
        f'<g transform="translate(0 -44)"><g class="{uid}legF"><g transform="translate(0 44)">{leg.format(f=ink)}</g></g></g>'
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


# ---------------------------------------------------------------- banner

# ---------------------------------------------------------------- the time of day, in your time zone

PERIODS = (  # (from hour, name, what the visitor says)
    (5, "morning", "morning, El. coffee first (o_o)"),
    (10, "day", "yes El, we see the fit (¬_¬)"),
    (16, "sunset", "the sunset arc hits different (^_^)"),
    (19, "night", "El, go to sleep (-_-) zZ"),
)


def period(cfg: dict) -> tuple[str, str]:
    """(name, visitor line) for the hour right now where you live. The Action redraws every hour."""
    hour = dt.datetime.now(ZoneInfo(cfg.get("timezone", "Asia/Manila"))).hour
    if "--period" in sys.argv:  # for previews: --period night
        name = sys.argv[sys.argv.index("--period") + 1]
        return next((n, line) for _, n, line in PERIODS if n == name)
    started = [p for p in PERIODS if hour >= p[0]]
    _, name, line = started[-1] if started else PERIODS[-1]  # before 5 am it's still night
    return name, line


def sky(c: dict, theme: str, name: str) -> str:
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


def banner(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    when, says = period(cfg)
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
    body += sky(c, theme, when)
    body += f'<g transform="translate(585 50) scale(0.735)">{el_on_rock(c, "b")}</g>'
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
    return doc(W, 300, body, f"{cfg['name']}: {cfg['tagline'].lower()} El, seen from behind, stands on a rock with his cape in the wind, {when} sky behind him.", css)


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
    body, css = "", f".caret{{animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}"
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

# Same scene as the portfolio's Runner.astro (El from the side, spiky hair, hopping over errors).
# The portfolio runs it with JavaScript; here it's one precomputed loop in CSS.
RUN_HEAD = "M13 12 C13 5 18 1 24 1 L23 -7 L28 -1 L31 -9 L33 0 L38 -5 L37 4 C39 7 39 15 36 19 C33 23 27 24 22 23 C16 22 13 18 13 12 Z"
CLOUD = "q8 -10 18 -4 q8 -8 16 2 q8 0 8 8 h-46 q0 -8 4 -6z"


def _bug(label: str, c: dict) -> tuple[str, float]:
    if label == "!":
        return (f'<path d="M13 0 L26 24 L0 24 Z" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5" stroke-linejoin="round"/>'
                f'<path d="M13 8 V15" stroke="{c["ink"]}" stroke-width="2.6" stroke-linecap="round"/>'
                f'<circle cx="13" cy="19.5" r="1.6" fill="{c["ink"]}"/>'), 26
    w = max(26, len(label) * 8 + 14)
    return (f'<rect x="0" y="0" width="{w}" height="24" rx="3" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
            + text(label, w / 2, 16.5, 11, c["ink"], wght=700, anchor="middle")), w


def dodge(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
    VW, VH = 560, 150                      # the scene, in the portfolio's units (its screen is 400 wide)
    GUY_X, GUY_W, GROUND_Y = 52, 42, 128
    SPEED, JUMP_T, PEAK = 170, 0.72, 64.8   # same physics as footer.ts: 360 up, 1000 gravity
    L = 3400                               # one loop of track
    T = L / SPEED                          # 20 s
    seq = [("ERR", 0), ("404", 300), ("!", 640), ("NaN", 900), ("TODO", 1260),
           ("}", 1560), ("null", 1880), ("ERR", 2240), ("!", 2520), ("404", 2860)]
    start = VW + 20
    # track: two copies so the screen is never empty at the seam
    track, passes, jumps = "", [], []
    for label, off in seq:
        g, w = _bug(label, c)
        for k in (-1, 0):
            x = start + off + k * L
            track += f'<g transform="translate({x} {GROUND_Y - 24})">{g}</g>'
        x0 = start + off
        passes.append(((x0 + w - GUY_X) / SPEED) % T)
        jumps.append(((x0 - (GUY_X + GUY_W + 20)) / SPEED) % T)
    pct = lambda t: f"{t / T * 100:.3f}%"
    # El's jump: up with ease-out, down with ease-in, same arc as the portfolio
    kf = ["0%{transform:translateY(0)}"]
    for j in sorted(jumps):
        kf.append(f"{pct(j)}{{transform:translateY(0);animation-timing-function:cubic-bezier(.33,1,.68,1)}}")
        kf.append(f"{pct(j + JUMP_T / 2)}{{transform:translateY(-{PEAK}px);animation-timing-function:cubic-bezier(.32,0,.67,0)}}")
        kf.append(f"{pct(j + JUMP_T)}{{transform:translateY(0)}}")
    kf.append("100%{transform:translateY(0)}")
    # the score: one label per count, each shown between two passes
    order = sorted(passes)
    score_g, score_css = "", ""
    bounds = [0.0] + order + [T]
    for n in range(len(order) + 1):
        a, b = bounds[n], bounds[n + 1]
        if b - a < 0.01:
            continue
        vis = (f"0%{{visibility:{'visible' if a == 0 else 'hidden'}}}"
               + (f"{pct(a)}{{visibility:visible}}" if a > 0 else "")
               + f"{pct(b)}{{visibility:hidden}}100%{{visibility:hidden}}")
        score_css += f".n{n}{{animation:n{n} {T:.2f}s steps(1,end) infinite}}@keyframes n{n}{{{vis}}}"
        score_g += f'<g class="n n{n}">' + text(f"{n:03d}", 0, 0, 13, c["on_panel"], mono=True, bold=True) + "</g>"

    # layout: bar on top, screen below, caption under it
    S = (W - 14 - 6) / VW                  # scale the 800-wide scene into the panel
    bar_h, sx, sy = 34, 3, 34
    screen_h = VH * S
    h = sy + screen_h + 3
    clouds = "".join(f'<path d="M{x} 34 {CLOUD}"/><path d="M{x + 200} 22 {CLOUD}"/>' for x in range(60, 2 * VW + 400, 400))
    dashes = "".join(f"M{x + 10} 138 h8 M{x + 40} 136 h4 M{x + 25} 141 h6 " for x in range(0, VW + 120, 60))
    guy = (f'<g class="guy"><g transform="translate({GUY_X} 74)">'
           f'<path d="{RUN_HEAD}" fill="{c["ink"]}"/><circle cx="31.5" cy="12" r="2.1" fill="{c["paper"]}"/>'
           f'<rect x="17" y="26" width="15" height="17" rx="4" fill="{c["ink"]}"/>'
           f'<path d="M26 30 L37 36" stroke="{c["ink"]}" stroke-width="4.5" stroke-linecap="round"/>'
           f'<g class="la" stroke="{c["ink"]}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M21 43 L14 54"/><path d="M28 43 L36 53"/></g>'
           f'<g class="lb" stroke="{c["ink"]}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M22 43 L21 54"/><path d="M27 43 L30 54"/></g>'
           f"</g></g>")
    score_label = "bugs dodged "
    score_x = W - 14 - 14 - 13 * MONO_ADV * 3
    body = (
        f'<rect x="0" y="0" width="{W - 14}" height="{bar_h}" fill="{c["panel_bg"]}"/>'
        + text("dodge.exe", 14, 22, 13, c["on_panel"], wght=700)
        + text(score_label, score_x - 6, 22, 13, c["on_panel"], wght=500, anchor="end")
        + f'<g transform="translate({score_x:.1f} 22)">{score_g}</g>'
        + f'<rect x="1.5" y="{bar_h}" width="{W - 17}" height="{screen_h + 1.5:.1f}" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="3"/>'
        + f'<rect x="0" y="{bar_h - 1.5}" width="{W - 14}" height="3" fill="{c["panel_bg"]}"/>'
        + f'<svg x="{sx}" y="{sy}" width="{W - 20}" height="{screen_h:.1f}" viewBox="0 0 {VW} {VH}" overflow="hidden">'
        f'<g class="clouds" fill="none" stroke="{c["ink"]}" stroke-width="2" opacity="0.35">{clouds}</g>'
        f'<line x1="0" y1="{GROUND_Y}" x2="{VW}" y2="{GROUND_Y}" stroke="{c["ink"]}" stroke-width="2.5"/>'
        f'<path class="ground" d="{dashes}" stroke="{c["ink"]}" stroke-width="2" stroke-linecap="round" opacity="0.5"/>'
        f'<g class="track">{track}</g>{guy}</svg>'
    )
    cap_y = h + 22
    body += text("Shipping, one bug at a time.", 2, cap_y, 13, c["muted"], wght=500)
    css = (
        f".track{{animation:track {T:.2f}s linear infinite}}@keyframes track{{to{{transform:translateX(-{L}px)}}}}"
        f".ground{{animation:ground {60 / SPEED:.3f}s linear infinite}}@keyframes ground{{to{{transform:translateX(-60px)}}}}"
        f".clouds{{animation:clouds {400 / (SPEED * 0.15):.2f}s linear infinite}}@keyframes clouds{{to{{transform:translateX(-400px)}}}}"
        f".guy{{animation:jump {T:.2f}s linear infinite}}@keyframes jump{{{''.join(kf)}}}"
        ".la{animation:step .22s steps(1,end) infinite}.lb{animation:step .22s steps(1,end) infinite reverse;opacity:0}"
        "@keyframes step{0%{opacity:1}50%{opacity:0}}"
        ".n{visibility:hidden}" + score_css
        + "@media (prefers-reduced-motion:reduce){.guy{transform:translateY(-40px)}.n0{visibility:visible}}"
    )
    label = "dodge.exe: El runs along and hops over errors (ERR, 404, NaN, TODO, null), counting the bugs he dodges."
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


def heading(theme: str, title: str) -> str:
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
for _key, _title in HEADINGS.items():
    BUILDERS[f"h-{_key}"] = (lambda t: (lambda theme, cfg: heading(theme, t)))(_title)

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
