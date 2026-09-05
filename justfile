# List available recipes.
default:
    @just --list

# Full pipeline: resume.json -> dist/index.html -> dist/print.pdf (+ blog + llms.txt/index.md)
build: assets render blog pdf llms

# Copy static files from public/ into dist/.
assets:
    mkdir -p dist
    cp -R public/. dist/

# Render resume.json + templates/resume.html.jinja -> dist/index.html
render: assets
    uv run scripts/render_html.py

# Render dist/index.html -> dist/print.pdf (uses the current dist/index.html as-is).
# DYLD_FALLBACK_LIBRARY_PATH works around WeasyPrint/Pango dylib lookup on macOS + Homebrew;
# harmless no-op on Linux (e.g. CI).
pdf:
    DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix 2>/dev/null)/lib" uv run scripts/build_pdf.py

# Render posts/*.md + templates to dist/blog/ (list, posts, feed; see scripts/render_blog.py)
blog: assets
    rm -rf dist/blog
    uv run scripts/render_blog.py

# Render resume.json -> dist/index.md + dist/llms.txt (see https://llmstxt.org)
llms: assets
    uv run scripts/render_llms.py

# Render and serve dist/ locally for preview at http://localhost:8000
serve: render blog llms
    cd dist && python3 -m http.server 8000

# Remove generated output.
clean:
    rm -rf dist
