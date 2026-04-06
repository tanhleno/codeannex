import io
import os
import sys
from pathlib import Path

from .core.config import PDFConfig
from .core.pdf_builder import ModernAnnexPDF
from .io.file_utils import get_project_files, classify_file, sort_files
from .io.git_utils import get_git_info
from .renderer.fonts import init_sprites, register_best_font, register_emoji_font, auto_register_font, ADDITIONAL_SEARCH_PATHS
from .interface.cli import parse_args, run_interactive_wizard
from reportlab.lib.units import cm


def check_emoji_font_style():
    from .renderer.fonts import get_system_font_paths
    emoji_font, emoji_path = register_emoji_font()
    if emoji_font:
        print(f"✅ Emoji font registered: {emoji_font}")
        if emoji_path:
            p_lower = emoji_path.lower()
            if "noto" in p_lower:
                print("💡 Tip: Google Noto fonts are being used.")
            elif "symbola" in p_lower:
                print("💡 Tip: Symbola font is being used.")
    else:
        print("⚠️  No emoji font found - emojis may not render correctly.")
        print(f"💡 Recommendation: Install 'Symbola' or 'Google Noto Emoji' fonts.")
        
    paths = get_system_font_paths()
    print(f"\n🔍 Font search paths:")
    for p in paths:
        print(f"   - {p}")
    print(f"\n💡 You can add custom search paths using: --font-path /path/to/fonts")
    return emoji_font


def main():
    args, unknown = parse_args()
    is_interactive = len(sys.argv) <= 2 and not args.no_input
    if is_interactive: run_interactive_wizard(args)

    # Register additional search paths first
    if args.font_path:
        ADDITIONAL_SEARCH_PATHS.extend(args.font_path)

    if args.normal_font:   args.normal_font   = auto_register_font(args.normal_font, required=True)
    if args.bold_font:     args.bold_font     = auto_register_font(args.bold_font, required=True)
    if args.title_font:    args.title_font    = auto_register_font(args.title_font, required=True)
    if args.subtitle_font: args.subtitle_font = auto_register_font(args.subtitle_font, required=True)
    if args.mono_font:     args.mono_font     = auto_register_font(args.mono_font, required=True)
    if args.emoji_font:    args.emoji_font    = auto_register_font(args.emoji_font, required=True)

    if unknown:
        for u in unknown:
            if u.startswith("-"): print(f"⚠️  Warning: Unrecognized argument ignored: {u}")

    if args.check_emoji_font:
        check_emoji_font_style()
        return

    root, output = Path(args.dir).resolve(), args.output or f"{Path(args.dir).resolve().name}_code_annex.pdf"
    output_path = Path(output).resolve()
    script_path = Path(__file__).resolve()

    use_git = not args.no_git
    git_url, git_branch, git_sha = get_git_info(root, use_git=use_git)
    repo_url, branch_name = args.repo_url or git_url, args.branch or git_branch

    mono_font, is_ttf, ttf_path = register_best_font()
    emoji_font, _ = register_emoji_font(error_on_missing=not args.emoji_description)
    init_sprites(is_ttf, ttf_path)

    def get_margin(spec, general, default):
        if spec is not None: return spec * cm
        if general is not None: return general * cm
        return default

    from reportlab.lib.units import mm
    config = PDFConfig(
        project_name=args.name or root.name,
        margin_left=get_margin(args.margin_left, args.margin, PDFConfig().margin_left),
        margin_right=get_margin(args.margin_right, args.margin, PDFConfig().margin_right),
        margin_top=get_margin(args.margin_top, args.margin, PDFConfig().margin_top),
        margin_bottom=get_margin(args.margin_bottom, args.margin, PDFConfig().margin_bottom),
        page_width=args.page_width * mm if args.page_width else PDFConfig().page_width,
        page_height=args.page_height * mm if args.page_height else PDFConfig().page_height,
        start_page_num=args.start_page,
        show_project_name=args.show_project,
        normal_font=args.normal_font or PDFConfig().normal_font,
        bold_font=args.bold_font or PDFConfig().bold_font,
        mono_font=args.mono_font or mono_font,
        emoji_font=args.emoji_font or emoji_font,
        emoji_description=args.emoji_description,
        repo_url=repo_url,
        branch_name=branch_name,
        commit_sha=git_sha,
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
        cover_subtitle=args.cover_subtitle,
        summary_title=args.summary_title,
        repo_label=args.repo_label,
        project_label=args.project_label,
        file_part_format=args.file_part_format,
        code_font_size=args.code_size,
        code_bg_color=args.code_bg,
        page_bg_color=args.page_bg_color,
    )

    all_files = sort_files(get_project_files(root, includes=args.include, excludes=args.exclude, use_git=use_git), root)
    included = []
    from .core.config import IMAGE_EXTENSIONS, BINARY_EXTENSIONS

    for fp in all_files:
        # We only silently skip the script itself to avoid infinite recursion if it's in the same folder
        try:
            if fp.resolve() == script_path: continue
        except: pass
        
        if not fp.is_file(): continue
        
        ext = fp.suffix.lower()
        if ext == ".svg":
            included += [(fp, "image"), (fp, "text")]
            continue
        elif ext in IMAGE_EXTENSIONS:
            included.append((fp, "image"))
            continue
        elif ext in BINARY_EXTENSIONS:
            rel_path = fp.relative_to(root).as_posix()
            print(f"⚠️  Skipping binary/unsupported file: {rel_path}")
            continue
        
        file_type = classify_file(fp)
        if file_type == "text":
            included.append((fp, "text"))
        else:
            rel_path = fp.relative_to(root).as_posix()
            print(f"⚠️  Skipping binary file: {rel_path}")

    if not included:
        print("❌ No compatible files found."); return

    print(f"🧮 Step 1/2: Simulating layout of {len(included)} files...")
    pdf_sim = ModernAnnexPDF(io.BytesIO(), root, mono_font, emoji_font, config)
    pdf_sim.is_simulation = True
    pdf_sim.build(included)

    print("🚀 Step 2/2: Generating the final document...")
    pdf_final = ModernAnnexPDF(output, root, mono_font, emoji_font, config)
    pdf_final.summary_data = pdf_sim.summary_data
    pdf_final.build(included)
    print(f"✅ Success! Saved to: {output}")

if __name__ == "__main__":
    main()
