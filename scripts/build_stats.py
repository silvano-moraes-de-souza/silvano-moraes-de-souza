"""Generate the animated SVG cards of the profile README from live GitHub data.

    python scripts/build_stats.py            # uses GITHUB_TOKEN if set

- assets/languages.svg  language share across public, non-fork repositories
- assets/progress.svg   30 Days of Data & Software Engineering progress, read
                        from the hub README (rows marked "done")

Runs daily in .github/workflows/stats.yml, so the cards never go stale.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path

USER = "silvano-moraes-de-souza"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
COLORS = {  # GitHub linguist colors
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#663399", "PLpgSQL": "#336790", "SQL": "#e38c00", "Dockerfile": "#384d54",
    "Shell": "#89e051", "PowerShell": "#012456", "TSQL": "#e38c00", "Makefile": "#427819",
}  # fmt: skip
SKIP = {"HTML", "CSS"}  # markup inflates byte counts; show programming languages


def get(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "profile-stats"})  # fmt: skip
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    return json.loads(body) if url.startswith("https://api.") else body


def languages() -> tuple[list[tuple[str, float]], int]:
    repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"] != USER]  # fmt: skip
    total: Counter[str] = Counter()
    for r in repos:
        for lang, size in get(r["languages_url"]).items():
            if lang not in SKIP:
                total[lang] += size
    s = sum(total.values()) or 1
    top = [(lang, 100 * n / s) for lang, n in total.most_common(6) if n / s >= 0.01]
    return top, len(repos)


def progress() -> tuple[int, int]:
    readme = get(f"https://raw.githubusercontent.com/{USER}/30-days-data-eng/main/README.md")
    rows = re.findall(r"^\|\s*(\d{2})\s*\|.*\|\s*(done|next|)\s*\|\s*$", readme, re.M)
    done = sum(1 for _, status in rows if status == "done")
    return done, len(rows) or 31


def languages_svg(top: list[tuple[str, float]], n_repos: int) -> str:
    w, row = 620, 34
    h = 90 + row * len(top)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="Languages across {n_repos} public repositories">',
        "<style>.sans{font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif}"
        ".bar{transform-box:fill-box;transform-origin:left;transform:scaleX(0);"
        "animation:g 1.4s ease-out forwards}@keyframes g{to{transform:scaleX(1)}}</style>",
        f'<rect width="{w}" height="{h}" rx="14" fill="#0d1117" stroke="#30363d"/>',
        '<text x="24" y="40" class="sans" font-size="18" font-weight="700" fill="#e6edf3">'
        "Languages in my repositories</text>",
        f'<text x="24" y="62" class="sans" font-size="12" fill="#8b949e">{n_repos} public '
        "repositories, by bytes of code, updated daily</text>",
    ]
    for i, (lang, pct) in enumerate(top):
        y = 92 + i * row
        color = COLORS.get(lang, "#8b949e")
        bar = max(4, 380 * pct / top[0][1])
        parts += [
            f'<text x="24" y="{y + 12}" class="sans" font-size="14" fill="#e6edf3">{lang}</text>',
            f'<rect x="150" y="{y}" width="380" height="14" rx="7" fill="#21262d"/>',
            f'<rect class="bar" style="animation-delay:{0.15 * i:.2f}s" x="150" y="{y}" '
            f'width="{bar:.1f}" height="14" rx="7" fill="{color}"/>',
            f'<text x="{w - 24}" y="{y + 12}" class="sans" font-size="13" fill="#8b949e" '
            f'text-anchor="end">{pct:.1f}%</text>',
        ]
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def progress_svg(done: int, total: int) -> str:
    w, h, size = 620, 176, 30
    per_row = 16
    step = (w - 48 - size) / (per_row - 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="30 Days of Data and Software Engineering: {done} of {total} done">',
        "<style>.sans{font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif}"
        ".d{opacity:0;animation:in .4s ease-out forwards}@keyframes in{to{opacity:1}}"
        ".now{animation:in .4s ease-out forwards,p 1.6s ease-in-out 1s infinite}"
        "@keyframes p{50%{opacity:.35}}"
        ".fill{transform-box:fill-box;transform-origin:left;transform:scaleX(0);"
        "animation:g 1.8s ease-out .3s forwards}@keyframes g{to{transform:scaleX(1)}}</style>",
        f'<rect width="{w}" height="{h}" rx="14" fill="#0d1117" stroke="#30363d"/>',
        '<text x="24" y="40" class="sans" font-size="18" font-weight="700" fill="#e6edf3">'
        "30 Days of Data &amp; Software Engineering</text>",
        f'<text x="{w - 24}" y="40" class="sans" font-size="18" font-weight="700" fill="#3fb950" '
        f'text-anchor="end">{done} / {total}</text>',
        f'<rect x="24" y="58" width="{w - 48}" height="10" rx="5" fill="#21262d"/>',
        f'<rect class="fill" x="24" y="58" width="{(w - 48) * done / total:.1f}" height="10" '
        'rx="5" fill="#3fb950"/>',
    ]
    for i in range(total):
        x = 24 + (i % per_row) * step
        y = 90 + (i // per_row) * (size + 8)
        is_done = i < done
        cls = "now" if i == done - 1 else "d"
        fill = "#3fb950" if is_done else ("#d29922" if i == done else "#21262d")
        parts.append(f'<rect class="{cls}" style="animation-delay:{0.04 * i:.2f}s" x="{x:.1f}" '
                     f'y="{y}" width="{size}" height="{size}" rx="6" fill="{fill}"/>')  # fmt: skip
        parts.append(f'<text x="{x + size / 2:.1f}" y="{y + size / 2 + 4}" class="sans" font-size="10" '
                     f'text-anchor="middle" fill="{"#0d1117" if i <= done else "#6e7681"}">{i:02d}</text>')  # fmt: skip
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    top, n = languages()
    (ASSETS / "languages.svg").write_text(languages_svg(top, n), encoding="utf-8", newline="\n")
    done, total = progress()
    (ASSETS / "progress.svg").write_text(progress_svg(done, total), encoding="utf-8", newline="\n")
    print(f"languages: {top}\nprogress: {done}/{total}")


if __name__ == "__main__":
    main()
