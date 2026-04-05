import os
import io
import logging
from pathlib import Path
from PIL import Image as PilImage, ImageDraw as PilImageDraw, ImageFont as PilImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import CODE_FONT_SIZE, COLOR_GUTTER_FG

logging.getLogger("svglib").setLevel(logging.ERROR)

# ── Discovery ────────────────────────────────────

def get_system_font_paths():
    """Returns a list of standard system font directories."""
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, ".local/share/fonts"),
        os.path.join(home, ".fonts"),
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        "/System/Library/Fonts",
        "/Library/Fonts",
        "C:\\Windows\\Fonts",
    ]
    return [p for p in paths if os.path.exists(p)]

def find_font_file(font_name: str) -> str | None:
    """Dynamically searches for a font file by name in system directories."""
    search_dirs = get_system_font_paths()
    
    # Normalize name for searching: "NotoEmoji" -> "notoemoji"
    clean_name = font_name.lower().replace(" ", "").replace("-", "")
    
    extensions = [".ttf", ".otf", ".ttc"]

    for base_dir in search_dirs:
        for root, _, files in os.walk(base_dir):
            for f in files:
                f_lower = f.lower()
                # Check if it's a font file
                if any(f_lower.endswith(ext) for ext in extensions):
                    # Check if our clean_name is in the filename
                    # e.g. "notoemoji" in "notocoloremoji.ttf"
                    f_clean = f_lower.replace(" ", "").replace("-", "").replace("_", "")
                    if clean_name in f_clean:
                        return os.path.join(root, f)
    return None

def auto_register_font(font_name: str, required: bool = False) -> str:
    """Attempts to register a font. Errors (🛑) stop execution, Warnings (⚠️) just alert."""
    if not font_name:
        return font_name
        
    # Standard ReportLab fonts
    if font_name in ["Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier"]:
        return font_name

    # Check if already registered
    try:
        pdfmetrics.getFont(font_name)
        return font_name
    except:
        pass

    # Try to find and register
    path = find_font_file(font_name)
    if path:
        try:
            print(f"✅ Found font '{font_name}' at: {path}")
            pdfmetrics.registerFont(TTFont(font_name, path))
            return font_name
        except Exception as e:
            if not required:
                print(f"⚠️ Warning: Could not register font '{font_name}': {e}")
                return font_name
            # If required, it will fall through to the Error block below
    
    # If font is not found or registration failed
    if required:
        msg = (
            f"\n🛑 ERROR: Font '{font_name}' not found or invalid.\n"
            f"   Search paths: {', '.join(get_system_font_paths())}\n\n"
            f"   Fixes:\n"
            f"   - Install the font on your OS (Windows/Linux/macOS).\n"
            f"   - Check for typos in your command.\n"
            f"   - Use a built-in font: Helvetica, Times-Roman, Courier.\n"
        )
        import sys
        print(msg, file=sys.stderr)
        sys.exit(1)
    else:
        print(f"⚠️ WARNING: Font '{font_name}' not found. Emojis or text might not render correctly.")
    
    return font_name

# ── Original Support Functions ───────────────────

TTF_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:\\Windows\\Fonts\\consola.ttf",
]

EMOJI_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
    "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
]

def _register_font(name: str, paths: list, fallback):
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
        # Tenta busca dinâmica como última opção
        dynamic_path = find_font_file("NotoEmoji") or find_font_file("Symbola")
        if dynamic_path:
            name, _ = _register_font("CustomEmoji", [dynamic_path], None)
    
    if name is None and error_on_missing:
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
        import sys
        print(msg, file=sys.stderr)
        sys.exit(1)
    return name

def get_emoji_font_style(font_path: str | None) -> str | None:
    """Detects the emoji style based on the font path."""
    if not font_path:
        return None
    font_path_lower = font_path.lower()
    if "noto" in font_path_lower:
        if "color" in font_path_lower: return "Google Noto Color"
        elif "emoji" in font_path_lower: return "Google Noto Emoji"
        else: return "Google Noto"
    if "apple" in font_path_lower: return "Apple"
    if "segui" in font_path_lower or "windows" in font_path_lower: return "Microsoft/Windows"
    if "symbola" in font_path_lower: return "Symbola (Unicode)"
    if "dejavu" in font_path_lower: return "DejaVu"
    if "ubuntu" in font_path_lower: return "Ubuntu"
    return "Unknown"

def is_google_like_emoji_font(font_path: str | None) -> bool:
    """Checks if the emoji font is Google-like (Noto-based)."""
    if not font_path: return False
    return "noto" in font_path.lower()

def get_current_emoji_font_info() -> dict:
    """Returns information about the currently registered emoji font."""
    if "CustomEmoji" in pdfmetrics._fonts:
        return {
            "name": "CustomEmoji",
            "is_registered": True,
            "is_google_like": False, 
            "style": "Unknown"
        }
    return {
        "name": None,
        "is_registered": False,
        "is_google_like": False,
        "style": None
    }

# ── Character & Sprite Support ───────────────────

_FONT_CACHE: dict = {}

def is_char_supported(char: str, font_name: str) -> bool:
    """Checks if the font has a glyph for the character. True for standard ASCII in built-in fonts."""
    if font_name not in _FONT_CACHE:
        try:
            _FONT_CACHE[font_name] = pdfmetrics.getFont(font_name)
        except:
            return False

    try:
        f = _FONT_CACHE[font_name]
        
        # ReportLab standard fonts (Type1) only support latin-1
        if font_name in ["Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier"]:
            return ord(char) < 256

        # For TTFonts, check the actual glyph map
        if hasattr(f, "face") and hasattr(f.face, "charToGlyph"):
            return ord(char) in f.face.charToGlyph
            
        return ord(char) < 256
    except:
        return False

def is_emoji(char: str) -> bool:
    """
    Returns True if the character is likely an emoji/symbol.
    Excludes box-drawing characters (U+2500 to U+257F).
    """
    if not char: return False
    cp = ord(char[0])
    # Box Drawing range: 2500–257F
    if 0x2500 <= cp <= 0x257F:
        return False
        
    import unicodedata
    category = unicodedata.category(char[0])
    return category in ['So', 'Sk', 'Cn']

DIGIT_SPRITES: dict | None = None

def get_digit_sprites() -> dict:
    if DIGIT_SPRITES is None: raise RuntimeError("init_sprites() not called.")
    return DIGIT_SPRITES

def init_sprites(is_ttf: bool, ttf_path: str | None):
    global DIGIT_SPRITES
    if DIGIT_SPRITES is not None: return
    DIGIT_SPRITES = {}
    color_hex = "#bac2de"
    try:
        import cairosvg
        cairo_available = True
    except ImportError:
        cairo_available = False

    for d in "0123456789":
        if cairo_available:
            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><text x="25" y="40" font-family="monospace" font-size="40" fill="{color_hex}" text-anchor="middle">{d}</text></svg>'
            png_data = cairosvg.svg2png(bytestring=svg_str.encode(), scale=4.0)
            img = PilImage.open(io.BytesIO(png_data))
        else:
            box_size = 200
            font = None
            if is_ttf and ttf_path:
                try: font = PilImageFont.truetype(ttf_path, box_size)
                except: pass
            font = font or PilImageFont.load_default()
            img_large = PilImage.new("RGBA", (box_size, box_size), (0, 0, 0, 0))
            draw = PilImageDraw.Draw(img_large)
            draw.text((box_size // 2, int(box_size * 0.8)), d, font=font, fill=(186, 194, 222, 255), anchor="ms")
            img = img_large.resize((50, 50), PilImage.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        DIGIT_SPRITES[d] = ImageReader(buf)

def register_font_file(name: str, path: str):
    """Fallback for manual registration if needed."""
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            return name
        except: pass
    return None
