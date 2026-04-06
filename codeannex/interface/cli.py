import argparse
from pathlib import Path
from ..core.config import PDFConfig
from ..io.git_utils import get_git_info, get_git_remotes

# ANSI Colors for a better CLI experience
BOLD = "\033[1m"
BLUE = "\033[34m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def parse_args():
    parser = argparse.ArgumentParser(description="Generates a PDF code annex with Smart Index and Images.")
    parser.add_argument("dir", nargs="?", default=".", help="Project directory")
    parser.add_argument("-o", "--output", default=None, help="Output PDF filename")
    parser.add_argument("-n", "--name", default=None, help="Project name")
    parser.add_argument("--no-input", action="store_true", help="Disable interactive mode")
    parser.add_argument("--cover-title", default="TECHNICAL ANNEX", help="Cover title")
    parser.add_argument("--margin", type=float, default=None, help="General margin (cm)")
    parser.add_argument("--margin-left", type=float, default=None, help="Left margin (cm)")
    parser.add_argument("--margin-right", type=float, default=None, help="Right margin (cm)")
    parser.add_argument("--margin-top", type=float, default=None, help="Top margin (cm)")
    parser.add_argument("--margin-bottom", type=float, default=None, help="Bottom margin (cm)")
    parser.add_argument("--start-page", type=int, default=1, help="Start page")
    parser.add_argument("--show-project", action="store_true", help="Show project in footer")
    parser.add_argument("--repo-url", default=None, help="Repo URL")
    parser.add_argument("--branch", default=None, help="Branch name")
    parser.add_argument("--repo-label", default="Repository Name: ", help="Label for repo")
    parser.add_argument("--project-label", default="Project: ", help="Label for project")
    parser.add_argument("--page-width", type=float, default=None, help="Width (mm)")
    parser.add_argument("--page-height", type=float, default=None, help="Height (mm)")
    parser.add_argument("--include", action="append", default=None, help="Include pattern")
    parser.add_argument("--exclude", action="append", default=None, help="Exclude pattern")
    parser.add_argument("--no-git", action="store_true", help="No Git")
    parser.add_argument("--file-part-format", default="(part {current}/{total})", help="Part format")
    parser.add_argument("--summary-title", default="Summary / File Index", help="Summary title")
    parser.add_argument("--cover-subtitle", default="Source Code Documentation", help="Cover subtitle")
    parser.add_argument("--page-number-size", type=int, default=8, help="Page number size")
    parser.add_argument("--page-number-format", default="{n}", help="Page number format")
    parser.add_argument("--no-page-numbers", action="store_true", help="No page numbers")
    parser.add_argument("--page-bg-color", default="#ffffff", help="Page BG color")
    parser.add_argument("--normal-font", default=None, help="Normal font")
    parser.add_argument("--normal-size", type=int, default=10, help="Normal size")
    parser.add_argument("--normal-color", default="#4c4f69", help="Normal color")
    parser.add_argument("--bold-font", default=None, help="Bold font")
    parser.add_argument("--title-font", default=None, help="Title font")
    parser.add_argument("--title-size", type=int, default=28, help="Title size")
    parser.add_argument("--title-color", default="#1e1e2e", help="Title color")
    parser.add_argument("--subtitle-font", default=None, help="Subtitle font")
    parser.add_argument("--subtitle-size", type=int, default=18, help="Subtitle size")
    parser.add_argument("--subtitle-color", default=None, help="Subtitle color")
    parser.add_argument("--primary-color", default="#1e66f5", help="Primary color")
    parser.add_argument("--code-size", type=int, default=10, help="Code size")
    parser.add_argument("--code-bg", default="#1e1e2e", help="Code background")
    parser.add_argument("--mono-font", default=None, help="Mono font")
    parser.add_argument("--emoji-font", default=None, help="Emoji font")
    parser.add_argument("--font-path", action="append", default=None, help="Additional directory to search for fonts")
    parser.add_argument("--emoji-description", action="store_true", help="Emoji desc")
    parser.add_argument("--check-emoji-font", action="store_true", help="Check emoji")
    return parser.parse_known_args()

def _print_header(step, total, title, details):
    print(f"\n{BLUE}Step {step}/{total}{RESET} {BOLD}--- {title} ---{RESET}")
    if details:
        print(f"   {CYAN}i{RESET} {details}")

def _ask_section(step, total, title, details, default_yes=False):
    _print_header(step, total, title, details)
    prompt = f"{GREEN}Y{RESET}/n" if default_yes else f"y/{GREEN}N{RESET}"
    res = input(f"   Customize this section? ({prompt}): ").strip().lower()
    if not res: return default_yes
    return res == 'y'

def _input_field(label, default):
    prompt = f"   {label} {CYAN}[{default if default is not None else ''}]{RESET}: "
    return input(prompt).strip()

def run_interactive_wizard(args):
    try:
        print(f"\n{BOLD}{BLUE}✨ Welcome to codeannex Interactive Wizard! ✨{RESET}")
        print(f"{YELLOW}Uppercase letters in prompts indicate the [default] action on Enter.{RESET}\n")
        
        root = Path(args.dir).resolve()
        git_url, git_branch, _ = get_git_info(root)
        remotes = get_git_remotes(root)
        total_steps = 6

        # 1. Project Identity
        _print_header(1, total_steps, "Project Identity", "Basic identification of your document")
        args.name = _input_field("Project Name", args.name or root.name) or (args.name or root.name)

        # 2. Repository Info
        has_git = bool(remotes or git_branch)
        if has_git:
            if len(remotes) > 1:
                _print_header(2, total_steps, "Repository Info", "Multiple Git remotes detected")
                print(f"   Available remotes:")
                remote_names = list(remotes.keys())
                for i, name in enumerate(remote_names, 1):
                    print(f"     {i}. {name} ({remotes[name]})")
                
                choice = _input_field("Select remote (number) or press Enter for origin", "1")
                if choice.isdigit() and 1 <= int(choice) <= len(remote_names):
                    selected_remote = remote_names[int(choice)-1]
                    git_url = remotes[selected_remote]
                elif "origin" in remotes:
                    git_url = remotes["origin"]
                else:
                    git_url = remotes[remote_names[0]]
            elif len(remotes) == 1:
                git_url = list(remotes.values())[0]

            _print_header(2, total_steps, "Repository Info", f"Detected: {git_branch or 'N/A'} @ {git_url or 'N/A'}")
            if input(f"   Use detected Git info? ({GREEN}Y{RESET}/n): ").strip().lower() != 'n':
                args.branch = git_branch
                args.repo_url = git_url
            else:
                args.branch = _input_field("Branch Name", git_branch or 'None') or git_branch
                args.repo_url = _input_field("Repository URL", git_url or 'None') or git_url
        else:
            if _ask_section(2, total_steps, "Repository Info", "Branch and Repository URL (No Git detected)"):
                args.branch = _input_field("Branch Name", "None") or None
                args.repo_url = _input_field("Repository URL", "None") or None

        # 3. Visual Style
        if _ask_section(3, total_steps, "Visual Style", "Titles, Subtitles, Accent Colors"):
            args.cover_title = _input_field("Cover Title", args.cover_title) or args.cover_title
            args.cover_subtitle = _input_field("Cover Subtitle", args.cover_subtitle) or args.cover_subtitle
            args.primary_color = _input_field("Primary Accent Color (HEX)", args.primary_color) or args.primary_color
            args.title_color = _input_field("Title Color (HEX)", args.title_color) or args.title_color

        # 4. Typography
        if _ask_section(4, total_steps, "Typography", "Fonts and Text Sizes"):
            args.title_font = _input_field("Title Font", args.title_font or 'Helvetica') or args.title_font
            args.normal_font = _input_field("Normal Font", args.normal_font or 'Helvetica') or args.normal_font
            args.mono_font = _input_field("Monospace Font", args.mono_font or 'Auto') or args.mono_font
            args.code_size = int(_input_field("Code Font Size", args.code_size) or args.code_size)
            
            paths = _input_field("Additional Font Paths (comma-separated)", "None")
            if paths:
                args.font_path = [p.strip() for p in paths.split(",") if p.strip()]

        # 5. Page Layout
        if _ask_section(5, total_steps, "Page Layout & Margins", "Margins, Paper Size, Page Numbering"):
            args.margin_top = float(_input_field("Top Margin (cm)", args.margin_top or 2.0) or (args.margin_top or 2.0))
            args.margin_bottom = float(_input_field("Bottom Margin (cm)", args.margin_bottom or 2.0) or (args.margin_bottom or 2.0))
            args.page_width = float(_input_field("Page Width (mm)", 210.0) or 210.0)
            args.page_height = float(_input_field("Page Height (mm)", 297.0) or 297.0)
            args.no_page_numbers = input(f"   Disable page numbers? (y/{GREEN}N{RESET}): ").strip().lower() == 'y'
            if not args.no_page_numbers:
                args.start_page = int(_input_field("Start Page Number", args.start_page) or args.start_page)

        # 6. Filters
        if _ask_section(6, total_steps, "File Filters", "Include/Exclude patterns (glob)"):
            inc = _input_field("Include Patterns (comma-separated)", "None")
            if inc: args.include = [p.strip() for p in inc.split(",") if p.strip()]
            exc = _input_field("Exclude Patterns (comma-separated)", "None")
            if exc: args.exclude = [p.strip() for p in exc.split(",") if p.strip()]

        print(f"\n{BOLD}{GREEN}🚀 Configuration complete! Generating PDF...{RESET}\n")

    except KeyboardInterrupt:
        import sys
        print(f"\n\n{YELLOW}⚠️  Wizard aborted by user (Ctrl+C).{RESET}")
        sys.exit(0)
