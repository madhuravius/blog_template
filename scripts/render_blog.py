#!/usr/bin/env python3
"""Render posts/*.md to dist/blog/ (post list, individual posts, RSS feed).

Each post is a Markdown file with YAML front matter:

    ---
    title: "Hello, World"
    date: 2026-09-03
    summary: "Why I'm starting a blog."
    slug: hello-world      # optional; derived from the filename if omitted
    draft: false           # optional; drafts are skipped
    ---

Post slugs default to the filename with any leading YYYY-MM-DD- prefix and
.md suffix stripped. Out put URLs are /blog/<slug>/ (clean URLs via
index.html, matching the site's root layout).
"""

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown
from pygments.formatters import HtmlFormatter
import frontmatter

from blog_images import process_html_images

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "resume.json"
POSTS_DIR = ROOT / "posts"
TEMPLATE_DIR = ROOT / "templates"
CSS = ROOT / "public" / "style.css"
BLOG_DIR = ROOT / "dist" / "blog"
POST_IMAGES_SRC = ROOT / "posts" / "images"
BLOG_IMAGES_OUT = ROOT / "dist" / "blog" / "images"
# URL prefix (relative to a post page at /blog/<slug>/) of served images.
IMAGE_URL_PREFIX = "../images/"

MD_EXTENSIONS = ["fenced_code", "tables", "codehilite", "pymdownx.tilde"]
MD_EXTENSION_CONFIGS = {"codehilite": {"guess_lang": False, "css_class": "codehilite"}}
# Pygments style used for fenced code blocks (light theme matching the site).
PYGMENTS_STYLE = "default"
DEFAULT_SITE_URL = "https://example.com"


def pygments_css() -> str:
    """Return Pygments highlighting CSS scoped to .codehilite blocks."""
    return HtmlFormatter(style=PYGMENTS_STYLE, cssclass="codehilite").get_style_defs(
        ".codehilite"
    )
DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def date_to_display(value) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value)


def to_rfc822(value) -> str:
    if isinstance(value, dt.datetime):
        return value.strftime("%a, %d %b %Y %H:%M:%S +0000")
    if isinstance(value, dt.date):
        return value.strftime("%a, %d %b %Y") + " 00:00:00 +0000"
    return str(value)


def read_posts() -> list[dict]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        post = frontmatter.load(path)
        if post.get("draft"):
            continue
        raw_date = post.get("date")
        slug = str(post.get("slug") or "").strip() or DATE_PREFIX.sub("", path.stem)
        posts.append(
            {
                "slug": slug,
                "title": str(post.get("title") or path.stem),
                "date": date_to_display(raw_date),
                "rfc822_date": to_rfc822(raw_date),
                "summary": str(post.get("summary") or "").strip(),
                "url": f"blog/{slug}/",
                "body_html": markdown(
                    post.content,
                    extensions=MD_EXTENSIONS,
                    extension_configs=MD_EXTENSION_CONFIGS,
                ),
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SITE_URL", DEFAULT_SITE_URL),
        help="Absolute site URL used for RSS feed links (default: %(default)s).",
    )
    args = parser.parse_args()
    site_url = args.base_url.rstrip("/")

    name = json.loads(DATA.read_text()).get("name", "")
    css = pygments_css() + "\n" + CSS.read_text()
    posts = read_posts()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    BLOG_DIR.mkdir(parents=True, exist_ok=True)

    index_tpl = env.get_template("blog_index.html.jinja")
    index_output = BLOG_DIR / "index.html"
    index_output.write_text(
        index_tpl.render(css=css, name=name, active="blog", posts=posts, site_url=site_url)
    )
    print(f"Wrote {index_output.relative_to(ROOT)} ({len(posts)} posts)")

    feed_tpl = env.get_template("feed.xml.jinja")
    feed_output = BLOG_DIR / "feed.xml"
    feed_output.write_text(feed_tpl.render(name=name, posts=posts, site_url=site_url))
    print(f"Wrote {feed_output.relative_to(ROOT)}")

    post_tpl = env.get_template("post.html.jinja")
    for post in posts:
        output = BLOG_DIR / post["slug"] / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)

        body_html = post["body_html"]
        if POST_IMAGES_SRC.exists():
            body_html = process_html_images(
                html=body_html,
                src_dir=POST_IMAGES_SRC,
                out_dir=BLOG_IMAGES_OUT,
                url_prefix=IMAGE_URL_PREFIX,
            )
        post["body_html"] = body_html

        output.write_text(
            post_tpl.render(
                css=css,
                name=name,
                active="blog",
                site_url=site_url,
                **post,
            )
        )
        print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()