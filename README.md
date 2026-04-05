# 📂 codeannex

Generates a professional PDF annex from a project's source code — featuring syntax highlighting, a hierarchical table of contents, image rendering, and version tracking.

## 🚀 Key Features

- **Interactive Wizard 2.0** — Step-by-step configuration with smart sections (Project, Style, Typography, Layout, Filters) and explicit default prompts.
- **Git Version Tracking** — Automatically detects **Repository URL**, **Branch**, and **Commit SHA**. Smart root detection avoids Git metadata on subdirectories.
- **Smart SVG Rendering** — Files are rendered as both a high-quality image and XML code. Entries are intelligently deduplicated in the summary.
- **Improved Document Structure** — Subdirectories and their contents are listed before root files for better organization.
- **High-Contrast Design** — Redesigned cover page, thickened image frames, and optimized line number legibility.
- **Intelligent Font Discovery** — Automatically finds fonts from your system or custom directories via `--font-path`.
- **Flexible File Filtering** — Multi-pattern include and exclude glob filters (e.g., `--include "src/*" --exclude "tests/*"`).
- **Pro-Level UI** — Control paper size (mm), margins (cm), accent colors (HEX), and font sizes.

## 🛠 Installation

The recommended way to install **codeannex** is via [pipx](https://github.com/pypa/pipx):

```bash
pipx install codeannex
```

For full SVG support (required for crisp line numbers and SVG image rendering):

```bash
pipx install "codeannex[svg]"
```

*Alternatively, you can use standard pip:* `pip install codeannex`

## 📖 Usage

### Interactive Mode (Wizard)
Simply run without arguments to start the configuration:
```bash
python3 -m codeannex
```

### Automation / CI
```bash
python3 -m codeannex . \
  --cover-title "Technical Annex" \
  --primary-color "#0f4761" \
  --code-size 9 \
  --include "src/*" \
  --exclude "*.log" \
  --no-input
```

Default output filename is `{project_name}_code_annex.pdf`.

## ⚙️ Configuration Options

### Git & Metadata
- `--repo-url URL` — Manual repository URL.
- `--branch NAME` — Manual branch name.
- `--no-git` — Force disable Git integration.
- `--repo-label LABEL` — Label for repo (default: "Repository: ").

### File Selection
- `--include PATTERN` — Include glob pattern (can be used multiple times).
- `--exclude PATTERN` — Exclude glob pattern (can be used multiple times).

### Design & Layout
- `--page-width MM` / `--page-height MM` — Custom paper size in mm (default: A4).
- `--margin CM` — General margin (top, bottom, left, right).
- `--primary-color HEX` — Accent color for headers, summary icons, and links.
- `--code-size N` — Font size for code and line numbers.

### Fonts
- `--font-path PATH` — Additional directory to search for `.ttf`/`.otf` files.
- `--title-font` / `--normal-font` / `--mono-font` — System font names.

## 🧪 Testing

```bash
PYTHONPATH=. pytest tests --cov=codeannex
```

## 📄 License

MIT
