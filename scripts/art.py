"""Static art for the profile README. Run once (and again after editing profile.config.json):

    python scripts/art.py            # everything except the ASCII gallery
    python scripts/gallery.py        # the dense ASCII gallery (needs rsvg-convert + Pillow)

Writes assets/<name>-light.svg and assets/<name>-dark.svg.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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
        f'<g transform="translate(92 58) scale(0.55)"><path d="{HAIR}" fill="{c["ink"]}"/></g>'
        f'<path d="M130 142 C150 134 190 134 210 142" fill="none" stroke="{c["ink"]}" stroke-width="7" stroke-linecap="round"/>'
        "</g>"
    )


# ---------------------------------------------------------------- banner

def banner(theme: str, cfg: dict) -> str:
    c = PALETTES[theme]
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
    body += f'<g transform="translate(585 50) scale(0.735)">{el_on_rock(c, "b")}</g>'
    # the comment that pops in from nowhere
    body += (
        '<g class="pop">'
        f'<rect x="420" y="40" width="168" height="46" fill="{c["paper"]}" stroke="{c["ink"]}" stroke-width="2.5"/>'
        + text("@visitor", 430, 57, 10.5, c["accent"], wght=700)
        + text("yes El, we see the fit (¬_¬)", 430, 76, 12, c["ink"], wght=600)
        + "</g>"
    )
    css = (
        ".pop{opacity:0;transform-origin:504px 63px;animation:pop 6s infinite}"
        "@keyframes pop{0%,20%{opacity:0;transform:scale(.6) rotate(-4deg)}27%{opacity:1;transform:scale(1.06) rotate(1deg)}"
        "31%,85%{opacity:1;transform:scale(1) rotate(0)}92%,100%{opacity:0;transform:scale(.9)}}"
    )
    return doc(W, 300, body, f"{cfg['name']}: {cfg['tagline'].lower()} El, seen from behind, stands on a rock with his cape in the wind.", css)


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
    only = sys.argv[1:] or list(BUILDERS)
    for name in only:
        for theme in THEMES:
            p = write(name, theme, BUILDERS[name](theme, cfg))
            print(f"{p.relative_to(p.parents[1])}  {p.stat().st_size // 1024} KB")
