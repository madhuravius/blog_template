#!/usr/bin/env python3
"""Render dist/index.html to dist/print.pdf using WeasyPrint."""

from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dist" / "index.html"
OUTPUT = ROOT / "dist" / "print.pdf"


def main() -> None:
    HTML(filename=str(SOURCE)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
