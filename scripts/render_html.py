#!/usr/bin/env python3
"""Render resume.json + templates/resume.html.jinja to dist/index.html."""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "resume.json"
TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_NAME = "resume.html.jinja"
OUTPUT = ROOT / "dist" / "index.html"


def main() -> None:
    data = json.loads(DATA.read_text())
    css = (ROOT / "public" / "style.css").read_text()
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(TEMPLATE_NAME)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(template.render(css=css, active="resume", **data))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} from {DATA.name} + templates/{TEMPLATE_NAME}")


if __name__ == "__main__":
    main()
