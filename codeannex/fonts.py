import io
import logging

from PIL import Image as PilImage, ImageDraw as PilImageDraw, ImageFont as PilImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import CODE_FONT_SIZE, COLOR_GUTTER_FG

logging.getLogger("svglib").setLevel(logging.ERROR)

# ── Caminhos de busca ────────────────────────────
TTF_SEARCH_PATHS = [
    "C:\\Windows\\Fonts\\consola.ttf", "C:\\Windows\\Fonts\\cour.ttf",
    "C:\\Windows\\Fonts\\lucon.ttf",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
]
EMOJI_SEARCH_PATHS = [
    # Monochromatic fonts work best with ReportLab
    "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",  # High coverage, monochromatic
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",         # Standard monochromatic Noto Emoji
    # Cross-platform fonts with reasonable coverage
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",              # Better for general Unicode
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    # Google/Noto color fonts (fallback, may not work in all reportlab versions)
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    # Platform-specific fonts
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Apple Symbols.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "C:\\Windows\\Fonts\\seguisym.ttf", "C:\\Windows\\Fonts\\seguiemj.ttf",
]


def _register_font(name: str, paths: list, fallback):
    import os
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(name, p))
                return name, p
            except Exception:
                continue
    return fallback, None


def register_best_font():
    name, path = _register_font("CustomMono", TTF_SEARCH_PATHS, "Courier")
    return name, name != "Courier", path


def register_emoji_font(error_on_missing=False):
    name, path = _register_font("CustomEmoji", EMOJI_SEARCH_PATHS, None)
    if name is None:
        # Fallback: try to use DejaVu fonts for unicode support
        try:
            dejavu_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            ]
            name, path = _register_font("CustomEmoji", dejavu_paths, None)
        except Exception:
            pass
    
    if name is None:
        msg = (
            "❌ Error: No emoji font found on your system.\n"
            "   Emojis cannot be rendered correctly without a dedicated font.\n\n"
            "   Solutions:\n"
            "   1. Install a font like 'Google Noto Emoji' or 'DejaVu Sans'.\n"
            "      - Ubuntu/Debian: sudo apt install fonts-noto-color-emoji\n"
            "      - Fedora: sudo dnf install google-noto-emoji-color-fonts\n"
            "      - Arch: sudo pacman -S noto-fonts-emoji\n"
            "   2. Use the --emoji-description flag to print [emoji descriptions] instead.\n"
            "   3. Manually specify a font path using --emoji-font \"/path/to/font.ttf\""
        )
        if error_on_missing:
            import sys
            print(msg, file=sys.stderr)
            sys.exit(1)
        else:
            print("⚠️  Warning: Dedicated Emoji font not found. Emojis may not render correctly.")
    else:
        emoji_style = get_emoji_font_style(path)
        if emoji_style:
            print(f"ℹ️  Using {emoji_style} emoji style (font: {path})")
    return name


def get_emoji_font_style(font_path: str | None) -> str | None:
    """Detects the emoji style based on the font path."""
    if not font_path:
        return None

    font_path_lower = font_path.lower()

    # Google/Noto fonts
    if "noto" in font_path_lower:
        if "color" in font_path_lower:
            return "Google Noto Color"
        elif "emoji" in font_path_lower:
            return "Google Noto Emoji"
        else:
            return "Google Noto"

    # Apple fonts
    if "apple" in font_path_lower:
        return "Apple"

    # Microsoft fonts
    if "segui" in font_path_lower or "windows" in font_path_lower:
        return "Microsoft/Windows"

    # Other common fonts
    if "symbola" in font_path_lower:
        return "Symbola (Unicode)"
    if "dejavu" in font_path_lower:
        return "DejaVu"
    if "ubuntu" in font_path_lower:
        return "Ubuntu"

    return "Unknown"


def is_google_like_emoji_font(font_path: str | None) -> bool:
    """Checks if the emoji font is Google-like (Noto-based)."""
    if not font_path:
        return False
    return "noto" in font_path.lower()


def get_current_emoji_font_info() -> dict:
    """Returns information about the currently registered emoji font."""
    from reportlab.pdfbase import pdfmetrics

    if "CustomEmoji" in pdfmetrics._fonts:
        # Tentar obter o caminho da fonte (se disponível)
        font_obj = pdfmetrics._fonts["CustomEmoji"]
        # Esta é uma simplificação - na prática pode ser mais complexo
        # obter o caminho original da fonte registrada
        return {
            "name": "CustomEmoji",
            "is_registered": True,
            "is_google_like": False,  # Não podemos determinar sem o caminho
            "style": "Unknown"
        }

    return {
        "name": None,
        "is_registered": False,
        "is_google_like": False,
        "style": None
    }


# ── Character support cache ───────────────
_FONT_CACHE: dict = {}


_EMOJI_CACHE: dict[str, bool] = {}
_EMOJI_RANGES = [
    (0x1F300, 0x1F9FF),  # Símbolos diversos, pictogramas, emoticons, transporte, etc
    (0x2600, 0x26FF),    # Símbolos diversos
    (0x2700, 0x27BF),    # Dingbats
    (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x2300, 0x23FF),    # Miscellaneous Technical
    (0x2B50, 0x2B55),    # Stars
    (0x1F004, 0x1F0FF),  # Emoticons
]


def is_emoji(char: str) -> bool:
    """Detects if a character is an emoji based on known Unicode ranges (with cache)."""
    if char in _EMOJI_CACHE:
        return _EMOJI_CACHE[char]

    # Check if any code point in the string is in emoji ranges
    result = any(
        any(start <= ord(c) <= end for start, end in _EMOJI_RANGES)
        for c in char
    )
    _EMOJI_CACHE[char] = result
    return result


def is_char_supported(char: str, font_name: str) -> bool:
    """Checks if the font has a glyph for the character. Emojis are always considered supported if emoji_font exists."""
    if font_name not in _FONT_CACHE:
        try:
            _FONT_CACHE[font_name] = pdfmetrics.getFont(font_name)
        except Exception:
            return False

    try:
        f = _FONT_CACHE[font_name]
        char_code = ord(char)

        # Check the font's glyph map
        if hasattr(f, "face") and hasattr(f.face, "charToGlyph"):
            return char_code in f.face.charToGlyph

        # Fallback: supports ASCII
        return char_code <= 255
    except Exception:
        return False


# ── Digit sprites (non-selectable) ─────────
DIGIT_SPRITES: dict | None = None


def get_digit_sprites() -> dict:
    if DIGIT_SPRITES is None:
        raise RuntimeError("init_sprites() was not called before get_digit_sprites().")
    return DIGIT_SPRITES


def init_sprites(is_ttf: bool, ttf_path: str | None):
    global DIGIT_SPRITES
    if DIGIT_SPRITES is not None:
        return
    DIGIT_SPRITES = {}
    color_hex = "#bac2de"

    try:
        import cairosvg
        cairo_available = True
    except ImportError:
        cairo_available = False

    for d in "0123456789":
        if cairo_available:
            svg_str = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
                f'<text x="25" y="40" font-family="monospace" font-size="40" '
                f'fill="{color_hex}" text-anchor="middle">{d}</text></svg>'
            )
            png_data = cairosvg.svg2png(bytestring=svg_str.encode(), scale=4.0)
            img = PilImage.open(io.BytesIO(png_data))
        else:
            box_size = 200
            font = None
            if is_ttf and ttf_path:
                try:
                    font = PilImageFont.truetype(ttf_path, box_size)
                except Exception:
                    pass
            font = font or PilImageFont.load_default()
            r = int(COLOR_GUTTER_FG.red * 255)
            g = int(COLOR_GUTTER_FG.green * 255)
            b = int(COLOR_GUTTER_FG.blue * 255)
            img_large = PilImage.new("RGBA", (box_size, box_size), (0, 0, 0, 0))
            draw = PilImageDraw.Draw(img_large)
            try:
                draw.text((box_size // 2, int(box_size * 0.8)), d, font=font,
                          fill=(r, g, b, 255), anchor="ms")
            except TypeError:
                draw.text((box_size // 4, box_size // 4), d, font=font, fill=(r, g, b, 255))
            img = img_large.resize((50, 50), PilImage.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        DIGIT_SPRITES[d] = ImageReader(buf)
