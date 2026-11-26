# How this profile is built

Everything on the profile is an SVG image, because GitHub strips CSS and JavaScript from READMEs.
Animation lives inside the images. Each image has a `-light` and a `-dark` version, picked by your GitHub theme.

| What | Where | Made by | When |
|---|---|---|---|
| Banner (with a sky for the time of day), typing line, about tiles, headings, commit joke, dodge.exe, footer | `assets/` | `scripts/art.py` | The Action, every hour |
| The banner, once per time of day (`banner-<morning/day/sunset/night>-<theme>.svg`) | `assets/` | `scripts/art.py` | The Action, every hour; served live by `api/banner.js` |
| ASCII gallery (seven scenes, one day from koi to El's wave) | `assets/gallery-*.svg` | `scripts/gallery.py` | By hand, when you change the art (commit the result) |
| Stack cards (languages and data, frontend and backend, then tools and design; icons sized so each card is one row) | `generated/stack-*.svg` | `scripts/stack.py`, from the portfolio's `/stack.json` | The Action, every hour |
| Power level, languages, streak, contribution year (El runs it with the weapon of the day), latest-pushes ticker, "recent activity" cards | `generated/` | `scripts/live.py` | The Action, every hour |
| `README.md` | repo root | `scripts/readme.py` | The Action, every run |

**Edit `profile.config.json`, not `README.md`.** The Action rewrites the README from the config.

## The live banner
GitHub runs scheduled Actions only when it has room and skips many, so a banner drawn by the Action can
show the morning sun at night. So the repo is also deployed on Vercel, where `api/banner.js` picks the sky
for the hour it is in `timezone` (from the config's `day` list) the moment someone opens the profile.
It only picks among the skies the Action already drew, so it needs no tokens and no build.
Set `live_banner` in the config to the deployment's address (for example `https://<project>.vercel.app`);
leave it empty and the README uses the banner the Action drew last.

## Running it yourself
```bash
pip install fonttools pillow numpy      # pillow + numpy only for gallery.py
python scripts/art.py                   # config art (add `banner --period night` to preview one sky)
python scripts/gallery.py               # ASCII gallery (also needs rsvg-convert)
python scripts/live.py --sample         # live cards with made-up numbers, for a local look
python scripts/readme.py
```
Don't commit cards made with `--sample`; the Action draws the real ones.

## Tokens
The Action works with the built-in `GITHUB_TOKEN` (public data).
To also count private and organisation work, add a repo secret `PROFILE_TOKEN`:
a fine-grained personal access token with read-only access. Private repo details then show on your public profile, so only feature public ones.

## Fonts
- Archivo (SIL Open Font License, see `fonts/Archivo-OFL.txt`): headings, turned into outlines.
- DejaVu Sans Mono (Bitstream Vera license, see `fonts/DejaVu-LICENSE.txt`): the ASCII, embedded as a small subset.
