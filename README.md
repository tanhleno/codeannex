# 📂 codeannex

Generates a professional PDF annex from a project's source code — with syntax highlighting, a hierarchical table of contents, image rendering, and intelligent font discovery.

## 🚀 Key Features

- **Interactive Wizard** — Run without arguments to configure your PDF step-by-step. It intelligently skips irrelevant questions (like starting page if numbering is disabled).
- **Intelligent Font Discovery** — Automatically finds and registers fonts from your system (Windows, Linux, macOS) by name (e.g., `--title-font "Play"`).
- **Fully Customizable UI** — Change every label, color, and size via CLI. Default labels are in English for international consistency.
- **Hierarchical Summary** — Real tree-structured Table of Contents with terminal-like connection lines.
- **Customizable Primary Color** — Set the theme color for headers, folder icons, and accents with `--primary-color`.
- **Smart Contrast** — Automatically switches header text between black and white based on the brightness of your primary color for maximum legibility.
- **Flexible Page Styling** — Support for custom page background and code block colors.
- **Git-Aware** — Perfectly interprets `.gitignore` using Git's native engine.

## 🛠 Installation

```bash
pip install codeannex
```

## 📖 Usage

### Interactive Mode (Wizard)
Simply run without arguments to start the step-by-step configuration:
```bash
codeannex .
```

### Automation / CI
Use the `--no-input` flag to disable the wizard in automated environments:
```bash
codeannex . --no-input
```

### Professional Customization Example
```bash
python3 -m codeannex . \
  --cover-title "Anexo I" \
  --no-page-numbers \
  --primary-color "#0f4761" \
  --title-font "Play" --title-size 20 \
  --normal-font "Times New Roman" --normal-size 12 \
  --margin-top 2.5 --margin-bottom 2.5 --margin-left 3 --margin-right 3 \
  --code-bg "#f5f5f5" --code-size 9
```

## ⚙️ Configuration Options

### Document & Labels
- `--cover-title TITLE` — Title for the cover (default: "ANEXO TÉCNICO").
- `--cover-subtitle SUB` — Subtitle for the cover.
- `--summary-title TITLE` — Title for the summary page.
- `--repo-label LABEL` — Prefix for repository link (default: "Repository: ").
- `--project-label LABEL` — Prefix for project name in footer.
- `--file-part-format FMT` — Format for file parts (default: "({current}/{total})").
- `--no-input` — Disable the interactive wizard.


### Colors & Themes
- `--primary-color HEX` — Main color for headers and accents.
- `--page-bg-color HEX` — Background color for all pages.
- `--code-bg HEX` — Background color for code blocks.
- `--normal-color HEX` / `--title-color HEX` — Text colors.

### Fonts & Sizes
- `--title-font` / `--subtitle-font` / `--normal-font` — System font names.
- `--mono-font` — Font for code (e.g., "Consolas", "Ubuntu Mono").
- `--emoji-font` — Font for emojis (e.g., "Noto Emoji").
- `--code-size N` — Font size for code blocks.

### Layout
- `--margin CM` — General margin for all sides.
- `--margin-top`, `--margin-bottom`, `--margin-left`, `--margin-right` — Specific margins in cm.
- `--no-page-numbers` — Disable page numbering.

## 🧪 Testing

```bash
PYTHONPATH=. pytest
```

## 📄 License

MIT
