"""Writes README.md from profile.config.json and what live.py found, so links never drift.

    python scripts/readme.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.svgkit import ROOT, config


def fresh(file: str) -> str:
    """file plus a fingerprint of its contents, e.g. 'generated/repo-1-dark.svg?v=3fa2c1d0'.
    GitHub caches README images by URL, so a card redrawn under the same name can keep
    showing the old picture. A new fingerprint makes it fetch the new one."""
    f = ROOT / file
    return f"{file}?v={hashlib.sha1(f.read_bytes()).hexdigest()[:8]}" if f.exists() else file


def pic(path: str, alt: str, width: int | str = 830) -> str:
    """Light/dark image pair. path is e.g. 'assets/banner' (without -light.svg)."""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{fresh(path + "-dark.svg")}">'
            f'<img src="{fresh(path + "-light.svg")}" alt="{escape(alt)}" width="{width}"></picture>')


def badge(label: str, message: str, href: str, color: str = "F4EFE4") -> str:
    url = f"https://img.shields.io/badge/{quote(label)}-{quote(message)}-{color}?style=for-the-badge&labelColor=15130F"
    return f'<a href="{escape(href)}"><img src="{url}" alt="{escape(label.title())}: {escape(message.lower())}"></a>'


def real(url: str) -> bool:
    """A link we can actually publish: set, and not a [PLACEHOLDER]."""
    return bool(url) and "[" not in url


def srcset(url: str) -> str:
    # srcset treats commas as separators, so a comma in the URL cuts it short
    return url.replace(",", "%2C")


def activity() -> list[str]:
    """Which repo each "recent activity" card shows, as live.py picked them on its last run."""
    made = ROOT / "generated" / "activity.json"
    return json.loads(made.read_text(encoding="utf-8")) if made.exists() else []


def main():
    cfg = config()
    user, links = cfg["user"], cfg["links"]
    email = links.get("email", "")
    mail = f"mailto:{email}" if "@" in email else ""
    repo_site = f"https://github.com/{user}/my-portfolio"
    site = links["portfolio"] if real(links.get("portfolio", "")) else repo_site
    out = []
    w = cfg.get("wip", {})
    if w.get("on"):
        out.append(f'<p align="center">{pic("assets/wip", w.get("title", "Work in progress") + ": " + w.get("note", ""))}</p>')
    out.append('<p align="center">')
    tag = " ".join(w if w.rstrip(".") == "AI" else w.lower() for w in cfg["tagline"].split())
    out.append(f'  <a href="{escape(site)}">{pic("assets/banner", cfg["name"] + ": " + tag[0].upper() + tag[1:])}</a>')
    out.append("</p>")
    out.append(f'<p align="center">{pic("assets/typing", "> " + " / ".join(cfg["typing"]), 830)}</p>')
    out.append('<p align="center">')
    out.append("  " + badge("portfolio", "visit" if site != repo_site else "in the works", site, "00789A"))
    if real(links.get("linkedin", "")):
        out.append("  " + badge("linkedin", "connect", links["linkedin"]))
    if real(links.get("fiverr", "")):
        out.append("  " + badge("fiverr", "lore for hire", links["fiverr"]))
    if mail:
        out.append("  " + badge("email", "say hi", mail))
    out.append(f'  <img src="https://komarev.com/ghpvc/?username={user}&label=VISITORS&color=00789A&style=for-the-badge" alt="Profile visitors">')
    out.append("</p>")
    out.append("")
    out.append("Hi, I'm **El**. I build web apps front to back, write lore and power systems on the side, "
               "and I'm learning AI engineering properly.")
    out.append("")
    out.append("*ἀρετή (arete): excellence, the full realization of one's potential. The idea I build around.*")
    out.append("")
    out.append(f'<p align="center">{pic("assets/about", "About El")}</p>')
    out.append("")
    out.append(f'<h3>{pic("assets/h-stats", "Stats")}</h3>')
    out.append(f'<p align="center">{pic("generated/stats", "Stats and top languages")}</p>')
    out.append(f'<p align="center">{pic("generated/streak", "Contribution streak")}</p>')
    out.append(f'<p align="center">{pic("generated/year", "Contributions over the past year")}</p>')
    out.append("")
    out.append(f'<h3>{pic("assets/h-gallery", "The gallery")}</h3>')
    out.append(f'<p align="center">{pic("assets/gallery", "ASCII gallery: knight, koi, El waving, campfire")}</p>')
    out.append("")
    out.append(f'<h3>{pic("assets/h-activity", "Recent activity")}</h3>')
    out.append(f'<p align="center">{pic("generated/ticker", "Latest pushes")}</p>')
    cards = [f'<a href="https://github.com/{full}">{pic(f"generated/repo-{i}", full.rpartition("/")[2], 412)}</a>'
             for i, full in enumerate(activity(), 1)]
    for i in range(0, len(cards), 2):
        out.append('<p align="center">')
        out.extend("  " + c for c in cards[i:i + 2])
        out.append("</p>")
    out.append("")
    out.append(f'<h3>{pic("assets/h-stack", "Stack")}</h3>')
    st = cfg["stack"]
    out.append('<p align="center">')
    out.append(f'  <picture><source media="(prefers-color-scheme: dark)" srcset="{srcset("https://skillicons.dev/icons?i=" + st["languages"] + "&theme=dark")}">'
               f'<img src="https://skillicons.dev/icons?i={st["languages"]}&theme=light" alt="Languages: {st["languages"].replace(",", ", ")}"></picture>')
    out.append("  <br>")
    out.append(f'  <picture><source media="(prefers-color-scheme: dark)" srcset="{srcset("https://skillicons.dev/icons?i=" + st["tools"] + "&theme=dark")}">'
               f'<img src="https://skillicons.dev/icons?i={st["tools"]}&theme=light" alt="Tools: {st["tools"].replace(",", ", ")}"></picture>')
    out.append("</p>")
    out.append("")
    out.append(f'<p align="center">{pic("assets/commit", "git commit -m fix stuff. Just kidding.")}</p>')
    out.append(f'<p align="center">{pic("assets/dodge", "dodge.exe")}</p>')
    out.append(f'<p align="center"><a href="{escape(site)}">{pic("assets/footer", "End of file. The full story is on the portfolio.")}</a></p>')
    out.append("")
    out.append("<!-- Generated by scripts/readme.py from profile.config.json. Edit the config, not this file. -->")
    (ROOT / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("README.md written")


if __name__ == "__main__":
    main()
