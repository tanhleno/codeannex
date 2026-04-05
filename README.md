# 📂 codeannex

Generates a professional PDF annex from a project's source code — with syntax highlighting, a hierarchical table of contents, image rendering, and intelligent font discovery.

## 🚀 Key Features

- **Interactive Wizard 2.0** — Organized by sections (Project, Style, Typography, Layout, Filters) with smart defaults and explicit (Y/n) prompts.
- **Git Integration & Version Tracking** — Automatically detects Repository URL, Branch, and **Commit SHA**. Supports subdirectories by intelligently ignoring Git metadata if not at the root.
- **Subdirectories First** — Improved document organization by listing subdirectories and their contents before root files.
- **Flexible File Filtering** — Multi-pattern include and exclude glob filters (e.g., `--include "src/*" --exclude "tests/*"`).
- **Intelligent Font Discovery** — Automatically finds fonts from your system (Windows, Linux, macOS) or custom paths via `--font-path`.
- **Fully Customizable UI** — Control everything: paper size (mm), margins (cm), colors (HEX), and font sizes.
- **Hierarchical Summary** — Real tree-structured Table of Contents with increasing page numbers and terminal-like connection lines.
- **Professional Design** — High-contrast line numbers, clean cover page, and smart contrast (auto-switching text between black/white based on accent brightness).

## 🛠 Installation

The recommended way to install **codeannex** is via [pipx](https://github.com/pypa/pipx), which installs the tool in an isolated environment:

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
Simply run without arguments to start the step-by-step configuration:
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

## ⚙️ Configuration Options

### Git & Metadata
- `--repo-url URL` — Manual repository URL.
- `--branch NAME` — Manual branch name.
- `--no-git` — Force disable Git integration.
- `--repo-label LABEL` — Label for repo (default: "Repository Name: ").

### File Selection
- `--include PATTERN` — Include glob pattern (can be used multiple times).
- `--exclude PATTERN` — Exclude glob pattern (can be used multiple times).

### Design & Layout
- `--page-width MM` / `--page-height MM` — Custom paper size in mm (default: A4).
- `--margin CM` — General margin (top, bottom, left, right).
- `--primary-color HEX` — Accent color for headers and summary icons.
- `--code-size N` — Font size for code and line numbers.

### Fonts
- `--font-path PATH` — Additional directory to search for `.ttf`/`.otf` files.
- `--title-font` / `--normal-font` / `--mono-font` — System font names.

## 🧪 Testing

```bash
PYTHONPATH=. pytest
```

## 📄 License

MIT
