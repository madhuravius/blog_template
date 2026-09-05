#!/usr/bin/env python3
"""Render resume.json to dist/index.md and dist/llms.txt.

dist/index.md is a full Markdown rendition of the resume, intended as the
"detailed page" that dist/llms.txt links to, per the llms.txt convention
(https://llmstxt.org). dist/llms.txt is a short, agent-friendly summary with
links to the full Markdown resume and PDF.
"""

import argparse
import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "resume.json"
TEMPLATE_DIR = ROOT / "templates"
DIST = ROOT / "dist"

DEFAULT_SITE_URL = "https://example.com"

TARGETS = [
    ("resume.md.jinja", DIST / "index.md"),
    ("llms.txt.jinja", DIST / "llms.txt"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SITE_URL", DEFAULT_SITE_URL),
        help="Absolute site URL used in llms.txt links (default: %(default)s).",
    )
    args = parser.parse_args()
    site_url = args.base_url.rstrip("/")

    data = json.loads(DATA.read_text())
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    DIST.mkdir(parents=True, exist_ok=True)
    for template_name, output in TARGETS:
        template = env.get_template(template_name)
        output.write_text(template.render(site_url=site_url, **data))
        print(f"Wrote {output.relative_to(ROOT)} from {DATA.name} + templates/{template_name}")


if __name__ == "__main__":
    main()
