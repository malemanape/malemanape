# How this profile is built

Everything on the profile is an SVG image, because GitHub strips CSS and JavaScript from READMEs.
Animation lives inside the images. Each image has a `-light` and a `-dark` version, picked by your GitHub theme.

| What | Where | Made by | When |
|---|---|---|---|
| Banner, typing line, about tiles, headings, commit joke, dodge.exe, footer | `assets/` | `scripts/art.py` | When you change `profile.config.json` |
| ASCII gallery (knight, koi, El, campfire) | `assets/gallery-*.svg` | `scripts/gallery.py` | When you change the art |
| Stats, streak, contribution year, featured repo cards | `generated/` | `scripts/live.py` | The Action, every hour |
| `README.md` | repo root | `scripts/readme.py` | The Action, every run |

**Edit `profile.config.json`, not `README.md`.** The Action rewrites the README from the config.

## Running it yourself
```bash
pip install fonttools pillow numpy      # pillow + numpy only for gallery.py
python scripts/art.py                   # static art
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
