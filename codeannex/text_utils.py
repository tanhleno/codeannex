import unicodedata
from pathlib import Path
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics

from .fonts import is_char_supported, is_emoji


def sanitize_text(text: str) -> str:
    """Remove invisible control characters that break PDF, keeping emojis intact."""
    return "".join(
        c if (ord(c) >= 0x20 and ord(c) != 0x7F) or ord(c) in (0x09, 0x0A, 0x0D)
        else " "
        for c in text
    )


def replace_unsupported_emojis(text: str, main_font: str, emoji_font: str | None,
                               emoji_description: bool = False) -> str:
    """If emoji_description is True, emojis are replaced by their [NAME]."""
    if not emoji_description:
        return text

    result = []
    for c in text:
        if is_emoji(c):
            try:
                name = unicodedata.name(c)
                result.append(f"[{name}]")
            except Exception:
                result.append("[EMOJI]")
        else:
            result.append(c)
    return "".join(result)


def _iter_segments(text: str, main_font: str, emoji_font: str | None,
                   emoji_description: bool = False):
    """
    Core Intelligence: Groups consecutive characters by the font they need.
    It switches to fallback if the main font doesn't support the character.
    """
    text = replace_unsupported_emojis(text, main_font, emoji_font, emoji_description)
    segment, using_fallback = "", False
    
    for c in text:
        # Check if main font can handle it
        supported = is_char_supported(c, main_font)
        # We need fallback if:
        # 1. Main font doesn't support it
        # 2. OR it's an emoji/symbol AND we have a fallback font AND descriptions are OFF
        needs_fallback = (not supported or is_emoji(c)) and emoji_font is not None and not emoji_description
        
        if needs_fallback != using_fallback:
            if segment:
                yield segment, using_fallback
            segment, using_fallback = "", needs_fallback
        segment += c
        
    if segment:
        yield segment, using_fallback


def _draw_segment(canvas_obj, x: float, y: float, seg: str,
                  font: str, main_font: str, font_size: float) -> float:
    """Draws a segment. Uses font as-is, falls back to ASCII '?' on error."""
    curr_x = x
    canvas_obj.setFont(font, font_size)
    for c in seg:
        try:
            canvas_obj.drawString(curr_x, y, c)
            curr_x += pdfmetrics.stringWidth(c, font, font_size)
        except Exception:
            # Last resort fallback
            canvas_obj.setFont(main_font, font_size)
            clean = c if ord(c) <= 255 else "?"
            canvas_obj.drawString(curr_x, y, clean)
            curr_x += pdfmetrics.stringWidth(clean, main_font, font_size)
            canvas_obj.setFont(font, font_size) # Restore font for next chars
    return curr_x


def get_safe_string_width(text: str, main_font: str, font_size: float,
                          emoji_font: str | None, emoji_description: bool = False) -> float:
    total = 0.0
    for seg, using_fallback in _iter_segments(text, main_font, emoji_font, emoji_description):
        font = emoji_font if using_fallback else main_font
        for c in seg:
            try:
                total += pdfmetrics.stringWidth(c, font, font_size)
            except Exception:
                total += pdfmetrics.stringWidth("?", main_font, font_size)
    return total


def draw_text_with_fallback(canvas_obj, x: float, y: float, text: str,
                             main_font: str, font_size: float,
                             emoji_font: str | None, text_color=None,
                             emoji_description: bool = False) -> float:
    if text_color:
        canvas_obj.setFillColor(text_color)
    curr_x = x
    for seg, using_fallback in _iter_segments(text, main_font, emoji_font, emoji_description):
        font = emoji_font if using_fallback else main_font
        curr_x = _draw_segment(canvas_obj, curr_x, y, seg, font, main_font, font_size)
    return curr_x


def draw_centred_text_with_fallback(canvas_obj, x: float, y: float, text: str,
                                     main_font: str, font_size: float,
                                     emoji_font: str | None, text_color=None,
                                     emoji_description: bool = False):
    w = get_safe_string_width(text, main_font, font_size, emoji_font, emoji_description)
    draw_text_with_fallback(canvas_obj, x - w / 2, y, text,
                            main_font, font_size, emoji_font, text_color,
                            emoji_description)

def get_contrast_color(hex_color: str):
    """Returns reportlab white or black depending on the background luminosity."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Perceptive luminance formula
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return colors.white if luminance < 0.5 else colors.black
    except:
        return colors.white
