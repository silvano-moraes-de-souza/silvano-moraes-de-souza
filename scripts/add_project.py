"""Add a project card to the profile README and keep every grid at two columns.

    python scripts/add_project.py --section days --repo sales-analytics-api \
        --title "Day 06 · Sales Analytics API" --text "REST over the gold layer..."

    python scripts/add_project.py --check        # only verify the grids

Sections: ``days`` (30 Days of Data & Software Engineering) and ``projects``.
The card is appended to the section, or replaces the card of the same repo, and
the whole table is rebuilt in rows of two with an empty cell when the count is odd.
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

USER = "silvano-moraes-de-souza"
README = Path(__file__).resolve().parent.parent / "README.md"
HEADINGS = {"days": "## 30 Days of Data & Software Engineering", "projects": "## Projects"}
CELL = re.compile(r'<td width="50%" valign="top">.*?</td>', re.S)
EMPTY = '<td width="50%"></td>'


def card(repo: str, title: str, text: str, image: str) -> str:
    raw = f"https://raw.githubusercontent.com/{USER}/{repo}/main/{image}"
    return (
        f'<td width="50%" valign="top">\n<a href="https://github.com/{USER}/{repo}">'
        f'<img src="{raw}" alt="{title}"></a>\n<br><b>{title}</b>: {text}\n</td>'
    )


def grid(cells: list[str]) -> str:
    rows = []
    for i in range(0, len(cells), 2):
        pair = cells[i : i + 2]
        if len(pair) == 1:
            pair.append(EMPTY)
        rows.append("<tr>\n" + "\n".join(pair) + "\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def check(text: str) -> None:
    for table in re.findall(r"<table>.*?</table>", text, re.S):
        for row in re.findall(r"<tr>.*?</tr>", table, re.S):
            if row.count("<td") > 2:
                raise SystemExit(f"a row has more than two columns:\n{row[:200]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--section", choices=sorted(HEADINGS))
    p.add_argument("--repo")
    p.add_argument("--title")
    p.add_argument("--text")
    p.add_argument("--image", default="docs/assets/banner.svg")
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    text = README.read_text(encoding="utf-8")
    if not a.check:
        if not all([a.section, a.repo, a.title, a.text]):
            p.error("--section, --repo, --title and --text are required")
        url = f"https://raw.githubusercontent.com/{USER}/{a.repo}/main/{a.image}"
        with urllib.request.urlopen(url, timeout=30) as r:  # the banner must exist
            assert r.status == 200
        start = text.index(HEADINGS[a.section])
        t0 = text.index("<table>", start)
        t1 = text.index("</table>", t0) + len("</table>")
        cells = CELL.findall(text[t0:t1])
        new = card(a.repo, a.title, a.text, a.image)
        marker = f"github.com/{USER}/{a.repo}\""
        if any(marker in c for c in cells):
            cells = [new if marker in c else c for c in cells]
        else:
            cells.append(new)
        text = text[:t0] + grid(cells) + text[t1:]
        README.write_text(text, encoding="utf-8", newline="\n")
        print(f"{a.section}: {len(cells)} cards")
    check(text)
    print("every grid has at most two columns")


if __name__ == "__main__":
    main()
