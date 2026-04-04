# 📂 codeannex

Generates a professional PDF annex from a project's source code — with syntax highlighting, a clickable table of contents, image rendering, non-selectable line numbers, and configurable fonts.

## Features

- **Syntax highlighting** via Pygments (Catppuccin Mocha theme)
- **Clickable table of contents** with page numbers (two-pass layout)
- **Smart word wrap** — breaks at word boundaries, respects emoji codepoints
- **Non-selectable line numbers** rendered as images
- **Image support** — embeds PNG, JPG, GIF, WebP, BMP, ICO, and SVG files
- **Git-aware** — uses `git ls-files` when available; falls back to manual `.gitignore` parsing
- **Cross-platform font discovery** — finds monospace and emoji fonts on Windows, macOS, and Linux
- **Emoji support** — configurable fonts for emojis, with fallback for better rendering.
  - *Tip for Linux:* Install `fonts-symbola` for high-coverage monochromatic emoji support that works reliably with ReportLab.
- **Emoji descriptions** — option to print `[EMOJI NAME]` instead of glyphs for systems without emoji fonts.
- **Configurable fonts** — customize normal, bold, monospace, and emoji fonts.
- **Page numbering** — customizable font size and position.
- **Repository Link** — show a clickable repository link on the cover page.
- **Fast binary file detection** — quickly ignores common binary extensions.

## Requirements

- Python >= 3.11
- `reportlab`, `Pillow`, `Pygments`

Optional SVG rendering (install at least one):
- `cairosvg` (preferred)
- `svglib`

For development and testing:
- `pytest` (install with `pip install -e ".[dev]"`)

## Installation

```bash
pip install codeannex
```

With SVG support:

```bash
pip install "codeannex[svg]"
```
## Requirements

- Python >= 3.11
- `reportlab`, `Pillow`, `Pygments`, `pdfminer.six`

Optional SVG rendering (install at least one):
...
## Usage

```bash
# Annotate current directory
codeannex

# Annotate a specific project
codeannex /path/to/project

# Custom output filename
codeannex /path/to/project -o my_annex.pdf

# Customized configuration (margins in cm)
codeannex /path/to/project \
  --name "My Project" \
  --repo-url "https://github.com/user/repo" \
  --margin 1.5 \
  --margin-top 2.5 \
  --page-number-size 10 \
  --show-project
```

### Configuration Options

- `--name NAME` — Custom project name (default: directory name).
- `--repo-url URL` — Repository URL to show as a clickable link on the cover.
- `--start-page N` — Starting page number (default: 1).
- `--margin CM` — General margin in cm for all sides.
- `--margin-left CM` — Left margin in cm (default: 1.5).
- `--margin-right CM` — Right margin in cm (default: 1.5).
- `--margin-top CM` — Top margin in cm (default: 2.0).
- `--margin-bottom CM` — Bottom margin in cm (default: 2.0).
- `--show-project` — Show project name in page footer (default: off).
- `--page-number-size N` — Font size for page numbers (default: 8).
- `--normal-font FONT` — Font for normal text (default: Helvetica).
- `--bold-font FONT` — Font for bold text (default: Helvetica-Bold).
- `--mono-font FONT` — Monospace font for code (default: auto-detect).
- `--emoji-font FONT` — Font for emojis (default: auto-detect).
- `--emoji-description` — Print `[DESCRIPTION]` instead of emoji glyphs.
- `--check-emoji-font` — Check current emoji font style and exit.


## Testing

Run the test suite with pytest:

```bash
pytest
```

## Output

The generated PDF contains:

1. **Cover page** — project name with page number
2. **Table of contents** — tree-structured, with clickable links to each file
3. **File pages** — syntax-highlighted source, with file path headers and line numbers

Files are ordered: root files first (alphabetical), then directories recursively (alphabetical).

Binary files (e.g., .pdf, .exe) are automatically ignored with warnings if not in .gitignore.

## License

MIT
