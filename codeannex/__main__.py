import argparse
import io
import os
from pathlib import Path

from .config import IMAGE_EXTENSIONS, BINARY_EXTENSIONS, PDFConfig
from .file_utils import get_project_files, classify_file, sort_files
from .fonts import init_sprites, register_best_font, register_emoji_font, auto_register_font
from .pdf_builder import ModernAnnexPDF
from reportlab.lib.units import cm


def check_emoji_font_style():
    """Utility function to check current emoji font style."""
    from .fonts import register_emoji_font, get_emoji_font_style, is_google_like_emoji_font

    emoji_font = register_emoji_font()
    if emoji_font:
        print(f"✅ Emoji font registered: {emoji_font}")
        print("ℹ️  To check if using Google-like style, look for 'Noto' in the font path above")
        print("💡 Tip: Install Google Noto fonts for authentic Google emoji style")
    else:
        print("⚠️  No emoji font found - emojis may not render correctly")
    return emoji_font


def run_interactive_wizard(args):
    """Interactive wizard to configure the PDF when no arguments are provided."""
    print("\n✨ Welcome to codeannex Interactive Wizard! ✨")
    print("Press Enter to keep the [default] value.\n")
    
    questions = [
        ("name", "Project Name", args.name or "Current Directory"),
        ("cover_title", "Cover Title", args.cover_title),
        ("cover_subtitle", "Cover Subtitle", args.cover_subtitle),
        ("primary_color", "Primary Color (HEX)", args.primary_color),
        ("title_font", "Title Font Name", args.title_font or "Play"),
        ("normal_font", "Normal Text Font Name", args.normal_font or "Tinos"),
        ("mono_font", "Monospace Font Name", args.mono_font or "NotoSansMono"),
        ("margin_top", "Top Margin (cm)", args.margin_top or 2.0),
        ("margin_bottom", "Bottom Margin (cm)", args.margin_bottom or 2.0),
        ("margin_left", "Left Margin (cm)", args.margin_left or 1.5),
        ("margin_right", "Right Margin (cm)", args.margin_right or 1.5),
        ("no_page_numbers", "Disable Page Numbers? (y/n)", "n"),
        ("start_page", "Starting Page Number", args.start_page or 1),
    ]
    
    for i, (attr, label, default) in enumerate(questions, 1):
        # Skip start_page question if page numbers were disabled in previous step
        if attr == "start_page" and args.no_page_numbers:
            continue
            
        choice = input(f"[{i}/{len(questions)}] {label} [{default}]: ").strip()
        if choice:
            if attr == "no_page_numbers":
                args.no_page_numbers = choice.lower() == 'y'
            elif "margin" in attr or attr == "start_page":
                setattr(args, attr, float(choice) if "." in choice else int(choice))
            else:
                setattr(args, attr, choice)
    print("\n🚀 Configuration complete! Generating PDF...\n")


def main():
    parser = argparse.ArgumentParser(description="Generates a PDF code annex with Smart Index and Images.")
    parser.add_argument("dir", nargs="?", default=".", help="Project directory")
    parser.add_argument("-o", "--output", default=None, help="Output PDF filename")
    parser.add_argument("-n", "--name", default=None, help="Project name (default: directory name)")
    parser.add_argument("--no-input", action="store_true", help="Disable interactive mode")
    parser.add_argument("--cover-title", default="TECHNICAL ANNEX", help="Title for the cover page")
    parser.add_argument("--margin", type=float, default=None, help="General margin in cm for all sides")
    parser.add_argument("--margin-left", type=float, default=None, help="Left margin in cm (default: 1.5cm)")
    parser.add_argument("--margin-right", type=float, default=None, help="Right margin in cm (default: 1.5cm)")
    parser.add_argument("--margin-top", type=float, default=None, help="Top margin in cm (default: 2.0cm)")
    parser.add_argument("--margin-bottom", type=float, default=None, help="Bottom margin in cm (default: 2.0cm)")
    parser.add_argument("--start-page", type=int, default=1, help="Starting page number (default: 1)")
    parser.add_argument("--show-project", action="store_true", help="Show project name in footer")
    parser.add_argument("--repo-url", default=None, help="Repository URL to show on cover")
    parser.add_argument("--repo-label", default="Repository: ", help="Label for repo URL (default: 'Repository: ')")
    parser.add_argument("--project-label", default="Project: ", help="Label for project name in footer (default: 'Project: ')")
    parser.add_argument("--file-part-format", default="({current}/{total})", help="Format for file parts continuation (e.g. '({current}/{total})')")
    parser.add_argument("--summary-title", default="Summary / File Index", help="Title for the summary page")
    parser.add_argument("--cover-subtitle", default="Source Code Documentation", help="Subtitle for the cover page")

    parser.add_argument("--page-number-size", type=int, default=8, help="Font size for page numbers (default: 8)")
    parser.add_argument("--page-number-format", default="{n}", help="Format for page numbers (e.g. 'Anexo I - {n}')")
    parser.add_argument("--no-page-numbers", action="store_true", help="Disable page numbers")
    parser.add_argument("--page-bg-color", default="#ffffff", help="Background color for pages (default: #ffffff)")
    parser.add_argument("--normal-font", default=None, help="Normal text font (default: Helvetica)")
    parser.add_argument("--normal-size", type=int, default=10, help="Normal text font size (default: 10)")
    parser.add_argument("--normal-color", default="#4c4f69", help="Normal text color (default: #4c4f69)")
    parser.add_argument("--bold-font", default=None, help="Bold text font (default: Helvetica-Bold)")
    parser.add_argument("--title-font", default=None, help="Title font (default: bold-font)")
    parser.add_argument("--title-size", type=int, default=28, help="Title font size (default: 28)")
    parser.add_argument("--title-color", default="#1e1e2e", help="Title color (default: #1e1e2e)")
    parser.add_argument("--subtitle-font", default=None, help="Subtitle font (default: normal-font)")
    parser.add_argument("--subtitle-size", type=int, default=18, help="Subtitle font size (default: 18)")
    parser.add_argument("--subtitle-color", default=None, help="Subtitle color (default: title-color)")
    parser.add_argument("--primary-color", default="#1e66f5", help="Primary color for accents and headers (default: #1e66f5)")
    parser.add_argument("--code-size", type=int, default=10, help="Font size for code (default: 10)")
    parser.add_argument("--code-bg", default="#1e1e2e", help="Background color for code blocks (default: #1e1e2e)")
    parser.add_argument("--mono-font", default=None, help="Monospace font for code (default: auto-detect)")
    parser.add_argument("--emoji-font", default=None, help="Font for emojis (default: auto-detect)")
    parser.add_argument("--emoji-description", action="store_true", help="Print [description] instead of emoji glyphs")
    parser.add_argument("--check-emoji-font", action="store_true", help="Check current emoji font style and exit")

    args, unknown = parser.parse_known_args()

    # Check if we should run interactive mode: 
    # No optional arguments provided AND --no-input is False
    import sys
    is_interactive = len(sys.argv) <= 2 and not args.no_input
    # If the second arg is actually a directory but no other flags were passed, we can still go interactive
    if is_interactive:
        run_interactive_wizard(args)

    # Pre-register fonts specified in arguments dynamically from system
    if args.normal_font:   args.normal_font   = auto_register_font(args.normal_font, required=True)
    if args.bold_font:     args.bold_font     = auto_register_font(args.bold_font, required=True)
    if args.title_font:    args.title_font    = auto_register_font(args.title_font, required=True)
    if args.subtitle_font: args.subtitle_font = auto_register_font(args.subtitle_font, required=True)
    if args.mono_font:     args.mono_font     = auto_register_font(args.mono_font, required=True)
    if args.emoji_font:    args.emoji_font    = auto_register_font(args.emoji_font, required=True)

    # Handle unknown arguments
    if unknown:
        for u in unknown:
            if u.startswith("-"):
                print(f"⚠️  Warning: Unrecognized argument ignored: {u}")

    # Handle emoji font check
    if args.check_emoji_font:
        check_emoji_font_style()
        return

    root   = Path(args.dir).resolve()
    output = args.output or f"{root.name}_anexo_codigo.pdf"

    script_path = Path(os.path.abspath(__file__))
    output_path = Path(output).resolve()

    mono_font, is_ttf, ttf_path = register_best_font()
    # If --emoji-description is NOT set, we MUST have an emoji font or we exit with error
    emoji_font = register_emoji_font(error_on_missing=not args.emoji_description)
    init_sprites(is_ttf, ttf_path)

    # Determine margin values (specific margins override general --margin)
    def get_margin(spec, general, default):
        if spec is not None:
            return spec * cm
        if general is not None:
            return general * cm
        return default

    # Criar configuração
    config = PDFConfig(
        project_name=args.name or root.name,
        margin_left=get_margin(args.margin_left, args.margin, PDFConfig().margin_left),
        margin_right=get_margin(args.margin_right, args.margin, PDFConfig().margin_right),
        margin_top=get_margin(args.margin_top, args.margin, PDFConfig().margin_top),
        margin_bottom=get_margin(args.margin_bottom, args.margin, PDFConfig().margin_bottom),
        start_page_num=args.start_page,
        show_project_name=args.show_project,
        normal_font=args.normal_font or PDFConfig().normal_font,
        bold_font=args.bold_font or PDFConfig().bold_font,
        mono_font=args.mono_font or mono_font,
        emoji_font=args.emoji_font or emoji_font,
        emoji_description=args.emoji_description,
        repo_url=args.repo_url,
        page_number_size=args.page_number_size,
        title_font=args.title_font,
        title_size=args.title_size,
        title_color=args.title_color,
        subtitle_font=args.subtitle_font,
        subtitle_size=args.subtitle_size,
        subtitle_color=args.subtitle_color,
        normal_text_size=args.normal_size,
        normal_text_color=args.normal_color,
        page_number_format=args.page_number_format,
        show_page_numbers=not args.no_page_numbers,
        cover_title=args.cover_title,
        primary_color=args.primary_color,
        # New dynamic fields
        cover_subtitle=args.cover_subtitle,
        summary_title=args.summary_title,
        repo_label=args.repo_label,
        project_label=args.project_label,
        file_part_format=args.file_part_format,
        code_font_size=args.code_size,
        code_bg_color=args.code_bg,
        page_bg_color=args.page_bg_color,
    )

    print(f"🔍 Analyzing directory: {root}")
    all_files = sort_files(get_project_files(root), root)
    included  = []
    ignored_binaries = []

    for fp in all_files:
        try:
            if fp.resolve() in (script_path, output_path):
                continue
        except Exception:
            pass
        if not fp.is_file():
            continue

        ext = fp.suffix.lower()

        if ext == ".svg":
            included += [(fp, "image"), (fp, "text")]
            continue
        elif ext in IMAGE_EXTENSIONS:
            included.append((fp, "image"))
            continue
        elif ext in BINARY_EXTENSIONS:
            ignored_binaries.append(fp)
            continue

        file_type = classify_file(fp)
        if file_type == "text":
            included.append((fp, "text"))
        elif file_type == "binary":
            ignored_binaries.append(fp)

    if ignored_binaries:
        for bp in ignored_binaries:
            rel_path = bp.relative_to(root)
            print(f"⚠️ Ignoring binary file: {rel_path}")

    if not included:
        print("❌ No compatible files found.")
        return

    print(f"🧮 Step 1/2: Simulating layout of {len(included)} files to generate the Table of Contents...")
    pdf_sim = ModernAnnexPDF(io.BytesIO(), root, mono_font, emoji_font, config)
    pdf_sim.is_simulation = True
    pdf_sim.build(included)

    print("🚀 Step 2/2: Generating the final document with images and code...")
    pdf_final = ModernAnnexPDF(output, root, mono_font, emoji_font, config)
    pdf_final.summary_data = pdf_sim.summary_data
    pdf_final.build(included)

    print(f"✅ Success! The annex was saved to: {output}")


if __name__ == "__main__":
    main()
