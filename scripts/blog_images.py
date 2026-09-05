"""Responsive image handling for blog posts.

Posts reference shared source images in ``posts/images/`` via standard
Markdown syntax ``![alt](photo.jpg)``. At build time this module:

* converts each referenced image to WebP at a fixed set of widths,
* writes the variants to ``dist/blog/images/<stem>-<width>.webp``,
* rewrites the ``<img>`` tag in the rendered HTML to add ``srcset``/``sizes``.

External URLs (http/https), protocol-relative URLs, data URIs, and images that
don't resolve under ``posts/images/`` are left untouched. Uses only the
standard library + Pillow, so no extra dependencies.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

# Target output widths in pixels (aspect ratio preserved).
WIDTHS = [600, 1200]
# The width used as the <img src> fallback for browsers that ignore srcset.
FALLBACK_WIDTH = max(WIDTHS)
# WebP save quality (0-100); 80 is a good quality/size balance.
QUALITY = 80
SIZES = "(max-width: 42rem) 100vw, 42rem"

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC_ATTR = re.compile(r'\bsrc=("[^"]*"|\'[^\']*\')', re.IGNORECASE)
_ALT_ATTR = re.compile(r'\balt="([^"]*)"', re.IGNORECASE)
_TITLE_ATTR = re.compile(r'\btitle="([^"]*)"', re.IGNORECASE)


def _make_variants(src_path: Path, out_dir: Path, stem: str) -> list[tuple[int, Path]]:
    """Convert src_path to WebP width variants under out_dir; return (w, path)."""
    variants = []
    with Image.open(src_path) as img:
        img = img.convert("RGB")
        original_w, original_h = img.size
        for width in WIDTHS:
            height = round(original_h * (width / original_w))
            resized = img.resize((width, height), Image.LANCZOS) if width < original_w else img
            path = out_dir / f"{stem}-{width}.webp"
            resized.save(path, "WEBP", quality=QUALITY, method=4)
            variants.append((width, path))
    return variants


def _resolve(src: str, src_dir: Path) -> Path | None:
    """Resolve a markdown <img> src to a file under src_dir, or None."""
    if not src or src.startswith("data:") or src.startswith("//"):
        return None
    parsed = urlparse(src)
    if parsed.scheme in ("http", "https"):
        return None
    candidate = (src_dir / Path(parsed.path).name).resolve()
    try:
        candidate.relative_to(src_dir.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def process_html_images(html: str, src_dir: Path, out_dir: Path, url_prefix: str = "images/") -> str:
    """Rewrite <img> tags in rendered markdown HTML to responsive WebP variants.

    ``url_prefix`` is the base URL (relative to the post page) the WebP
    variants are served from; variants are written under ``out_dir``.
    """
    src_dir = src_dir.resolve()
    out_dir = out_dir.resolve()

    def _rewrite(match: re.Match) -> str:
        tag = match.group(0)
        src_match = _SRC_ATTR.search(tag)
        if not src_match:
            return tag
        src = src_match.group(1)[1:-1]
        src_path = _resolve(src, src_dir)
        if src_path is None:
            return tag

        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            variants = _make_variants(src_path, out_dir, src_path.stem)
        except Exception:
            return tag

        srcset = ", ".join(f"{url_prefix}{v.name} {w}w" for w, v in variants)
        _, fallback_path = variants[-1]
        fallback = f"{url_prefix}{fallback_path.name}"

        alt = _ALT_ATTR.search(tag)
        title = _TITLE_ATTR.search(tag)
        attrs = []
        if title:
            attrs.append(f'title="{escape(title.group(1), quote=True)}"')
        new_tag = (
            f'<img alt="{escape(alt.group(1), quote=True) if alt else ""}"'
            f'{" " + " ".join(attrs) if attrs else ""}'
            f' src="{fallback}" srcset="{srcset}" sizes="{SIZES}" />'
        )
        return new_tag

    return _IMG_TAG.sub(_rewrite, html)
