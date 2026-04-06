import os
import io
import logging
from pathlib import Path
from PIL import Image as PilImage, ImageDraw as PilImageDraw, ImageFont as PilImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Adjusted import for new structure
from ..core.config import CODE_FONT_SIZE, COLOR_GUTTER_FG

logging.getLogger("svglib").setLevel(logging.ERROR)

ADDITIONAL_SEARCH_PATHS: list[str] = []

def get_system_font_paths():
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, ".local/share/fonts"), 
        os.path.join(home, ".fonts"), 
        "/usr/share/fonts", 
        "/usr/local/share/fonts", 
        "/System/Library/Fonts", 
        "/Library/Fonts", 
        "C:\\Windows\\Fonts"
    ]
    # Add user-defined paths
    return [p for p in ADDITIONAL_SEARCH_PATHS + paths if os.path.exists(p)]

def find_font_file(font_name: str) -> str | None:
    search_dirs = get_system_font_paths()
    clean_name = font_name.lower().replace(" ", "").replace("-", "")
    extensions = [".ttf", ".otf", ".ttc"]
    
    candidates = []
    for base_dir in search_dirs:
        for root, _, files in os.walk(base_dir):
            for f in files:
                f_lower = f.lower()
                if any(f_lower.endswith(ext) for ext in extensions):
                    f_clean = f_lower.replace(" ", "").replace("-", "").replace("_", "")
                    if clean_name in f_clean:
                        candidates.append(os.path.join(root, f))
    
    if not candidates: return None
    
    # Priority logic: 
    # 1. Prefer files that DO NOT contain "bold", "italic", "oblique", "light", "thin"
    # 2. Prefer files that contain "regular" or "normal"
    
    def score_font(path: str) -> int:
        p_lower = path.lower()
        score = 0
        if "regular" in p_lower or "normal" in p_lower: score += 10
        if "bold" in p_lower: score -= 20
        if "italic" in p_lower or "oblique" in p_lower: score -= 20
        if "light" in p_lower or "thin" in p_lower: score -= 10
        return score

    candidates.sort(key=score_font, reverse=True)
    return candidates[0]

def auto_register_font(font_name: str, required: bool = False) -> str:
    if not font_name: return font_name
    if font_name in ["Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier"]: return font_name
    try:
        pdfmetrics.getFont(font_name)
        return font_name
    except: pass
    path = find_font_file(font_name)
    if path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, path))
            return font_name
        except: pass
    if required:
        import sys
        print(f"\n🛑 ERROR: Font '{font_name}' not found.\nSearch paths: {', '.join(get_system_font_paths())}\n", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"⚠️ WARNING: Font '{font_name}' not found.")
    return font_name

TTF_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "C:\\Windows\\Fonts\\consola.ttf", "C:\\Windows\\Fonts\\cour.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "C:\\Windows\\Fonts\\arial.ttf"
]
EMOJI_SEARCH_PATHS = [
    "C:\\Windows\\Fonts\\seguiemj.ttf",          # Windows Standard Emoji
    "C:\\Windows\\Fonts\\seguisym.ttf",          # Windows Standard Symbol
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux Standard Fallback
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf", 
    "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf"
]

def _register_font(name: str, paths: list, fallback):
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(name, p))
                return name, p
            except: continue
    return fallback, None

def register_best_font():
    name, path = _register_font("CustomMono", TTF_SEARCH_PATHS, "Courier")
    if name == "Courier": print("ℹ️  Monospace font fallback: Using standard 'Courier'.")
    return name, name != "Courier", path

REGISTERED_EMOJI_FONT_PATH: str | None = None

def register_emoji_font(error_on_missing=False):
    global REGISTERED_EMOJI_FONT_PATH
    name, path = _register_font("CustomEmoji", EMOJI_SEARCH_PATHS, None)
    if name is None:
        dynamic_path = find_font_file("NotoEmoji") or find_font_file("Symbola")
        if dynamic_path: 
            name, path = _register_font("CustomEmoji", [dynamic_path], None)
    
    REGISTERED_EMOJI_FONT_PATH = path
    if name is None:
        if error_on_missing:
            import sys
            print("❌ Error: No emoji font found.", file=sys.stderr)
            sys.exit(1)
        else: print("ℹ️  Emoji fallback: No emoji font found.")
    return name, path

def get_emoji_font_style(font_path: str | None) -> str | None:
    if not font_path: return None
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
    if not font_path: return False
    return "noto" in font_path.lower()

def get_current_emoji_font_info() -> dict:
    if "CustomEmoji" in pdfmetrics._fonts:
        return {
            "name": "CustomEmoji", 
            "is_registered": True, 
            "path": REGISTERED_EMOJI_FONT_PATH,
            "style": get_emoji_font_style(REGISTERED_EMOJI_FONT_PATH)
        }
    return {"name": None, "is_registered": False, "path": None, "style": None}

def is_char_supported(char: str, font_name: str) -> bool:
    try:
        f = pdfmetrics.getFont(font_name)
        if font_name in ["Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier"]: return ord(char) < 256
        if hasattr(f, "face") and hasattr(f.face, "charToGlyph"): return ord(char) in f.face.charToGlyph
        return ord(char) < 256
    except: return False

def is_emoji(char: str) -> bool:
    if not char: return False
    cp = ord(char[0])
    if 0x2500 <= cp <= 0x257F: return False
    import unicodedata
    return unicodedata.category(char[0]) in ['So', 'Sk', 'Cn']

DIGIT_SPRITES: dict | None = None
def get_digit_sprites() -> dict:
    if DIGIT_SPRITES is None: raise RuntimeError("init_sprites() not called.")
    return DIGIT_SPRITES

def init_sprites(is_ttf: bool, ttf_path: str | None):
    global DIGIT_SPRITES
    if DIGIT_SPRITES is not None: return
    DIGIT_SPRITES = {}
    # Increased contrast color (Catppuccin Text instead of Subtext)
    color_hex = "#cdd6f4"
    try:
        import cairosvg
        cairo_available = True
    except ImportError: cairo_available = False

    for d in "0123456789":
        if cairo_available:
            # Scale 5.0 for better crispness
            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><text x="25" y="38" font-family="monospace" font-weight="bold" font-size="42" fill="{color_hex}" text-anchor="middle">{d}</text></svg>'
            png_data = cairosvg.svg2png(bytestring=svg_str.encode(), scale=5.0)
            img = PilImage.open(io.BytesIO(png_data))
        else:
            if d == "0":
                print("ℹ️  Sprite fallback: 'cairosvg' not found. Using PIL.")
            box_size = 250 # Larger base for better downscaling
            font = None
            if is_ttf and ttf_path:
                try: font = PilImageFont.truetype(ttf_path, box_size)
                except: pass
            font = font or PilImageFont.load_default()
            img_large = PilImage.new("RGBA", (box_size, box_size), (0, 0, 0, 0))
            draw = PilImageDraw.Draw(img_large)
            # Brighter color for PIL fallback too
            draw.text((box_size // 2, int(box_size * 0.75)), d, font=font, fill=(205, 214, 244, 255), anchor="ms")
            img = img_large.resize((50, 50), PilImage.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        DIGIT_SPRITES[d] = ImageReader(buf)
