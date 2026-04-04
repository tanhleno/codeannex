import argparse
import io
import os
from pathlib import Path

from .config import IMAGE_EXTENSIONS, BINARY_EXTENSIONS, PDFConfig
from .file_utils import get_project_files, classify_file, sort_files
from .fonts import init_sprites, register_best_font, register_emoji_font
from .pdf_builder import ModernAnnexPDF
from reportlab.lib.units import cm


def check_emoji_font_style():
    """Utility function to check current emoji font style."""
    from .fonts import register_emoji_font, get_emoji_font_style, is_google_like_emoji_font

    emoji_font = register_emoji_font()
    if emoji_font:
        # Tentar obter informações sobre a fonte
        # Nota: Esta é uma simplificação - em produção teríamos o caminho armazenado
        print(f"✅ Emoji font registered: {emoji_font}")
        print("ℹ️  To check if using Google-like style, look for 'Noto' in the font path above")
        print("💡 Tip: Install Google Noto fonts for authentic Google emoji style")
    else:
        print("⚠️  No emoji font found - emojis may not render correctly")
    return emoji_font


def main():
    parser = argparse.ArgumentParser(description="Generates a PDF code annex with Smart Index and Images.")
    parser.add_argument("dir", nargs="?", default=".", help="Project directory")
    parser.add_argument("-o", "--output", default=None, help="Output PDF filename")
    parser.add_argument("-n", "--name", default=None, help="Project name (default: directory name)")
    parser.add_argument("--margin", type=float, default=None, help="General margin in cm for all sides")
    parser.add_argument("--margin-left", type=float, default=None, help="Left margin in cm (default: 1.5cm)")
    parser.add_argument("--margin-right", type=float, default=None, help="Right margin in cm (default: 1.5cm)")
    parser.add_argument("--margin-top", type=float, default=None, help="Top margin in cm (default: 2.0cm)")
    parser.add_argument("--margin-bottom", type=float, default=None, help="Bottom margin in cm (default: 2.0cm)")
    parser.add_argument("--start-page", type=int, default=1, help="Starting page number (default: 1)")
    parser.add_argument("--show-project", action="store_true", help="Show project name in footer")
    parser.add_argument("--repo-url", default=None, help="Repository URL to show on cover")
    parser.add_argument("--page-number-size", type=int, default=8, help="Font size for page numbers (default: 8)")
    parser.add_argument("--normal-font", default=None, help="Normal text font (default: Helvetica)")
    parser.add_argument("--bold-font", default=None, help="Bold text font (default: Helvetica-Bold)")
    parser.add_argument("--mono-font", default=None, help="Monospace font for code (default: auto-detect)")
    parser.add_argument("--emoji-font", default=None, help="Font for emojis (default: auto-detect)")
    parser.add_argument("--emoji-description", action="store_true", help="Print [description] instead of emoji glyphs")
    parser.add_argument("--check-emoji-font", action="store_true", help="Check current emoji font style and exit")

    args, unknown = parser.parse_known_args()

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

        # Check known extensions first (without reading file)
        if ext == ".svg":
            included += [(fp, "image"), (fp, "text")]
            continue
        elif ext in IMAGE_EXTENSIONS:
            included.append((fp, "image"))
            continue
        elif ext in BINARY_EXTENSIONS:
            ignored_binaries.append(fp)
            continue

        # Classify file with a single read
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
