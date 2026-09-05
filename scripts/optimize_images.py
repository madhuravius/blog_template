#!/usr/bin/env python3
"""Optimize images in public/ using Pillow. Run via: uv run scripts/optimize_images.py"""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

def optimize_logo() -> None:
    src = PUBLIC / "logo.png"
    img = Image.open(src).convert("RGB")

    # Target 200x200 for crisp 2x display at 100px
    target = 200
    img = img.resize((target, target), Image.Resampling.LANCZOS)

    # Optimized PNG fallback (adaptive palette for small size)
    png_out = PUBLIC / "logo.png"
    png_img = img.convert("P", palette=Image.ADAPTIVE, colors=96)
    png_img.save(png_out, "PNG", optimize=True)
    print(f"Optimized PNG: {png_out} ({png_out.stat().st_size} bytes)")

    # WebP for modern browsers (tiny)
    webp_out = PUBLIC / "logo.webp"
    img.save(webp_out, "WEBP", quality=82, method=6)
    print(f"Generated WebP: {webp_out} ({webp_out.stat().st_size} bytes)")

def optimize_favicon() -> None:
    src = PUBLIC / "favicon.png"
    if not src.exists():
        return
    img = Image.open(src).convert("RGBA")

    # 64px PNG favicon, heavily optimized
    favicon_out = PUBLIC / "favicon.png"
    img64 = img.resize((64, 64), Image.Resampling.LANCZOS)
    img64.save(favicon_out, "PNG", optimize=True)
    print(f"Optimized favicon.png: {favicon_out} ({favicon_out.stat().st_size} bytes)")

    # Tiny ICO (32px)
    ico_out = PUBLIC / "favicon.ico"
    ico = img.resize((32, 32), Image.Resampling.LANCZOS)
    ico.save(ico_out, "ICO")
    print(f"Updated favicon.ico: {ico_out} ({ico_out.stat().st_size} bytes)")

def main() -> None:
    optimize_logo()
    optimize_favicon()
    print("Image optimization complete.")

if __name__ == "__main__":
    main()
