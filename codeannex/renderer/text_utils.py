import re
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics

def sanitize_text(text: str) -> str:
    """Removes invalid PDF characters."""
    if not text: return ""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

def get_safe_string_width(text, font_name, font_size, emoji_font=None, emoji_description=False):
    from .fonts import is_char_supported
    total_w = 0.0
    for char in text:
        if is_char_supported(char, font_name):
            total_w += pdfmetrics.stringWidth(char, font_name, font_size)
        elif emoji_font:
            if emoji_description: total_w += pdfmetrics.stringWidth(f"[{char}]", font_name, font_size)
            else: total_w += pdfmetrics.stringWidth(char, emoji_font, font_size)
        else: total_w += pdfmetrics.stringWidth("?", font_name, font_size)
    return total_w

def draw_text_with_fallback(canvas, x, y, text, font_name, font_size, emoji_font=None, color=None, emoji_description=False):
    from .fonts import is_char_supported
    if color: canvas.setFillColor(colors.HexColor(color) if isinstance(color, str) else color)
    curr_x = x
    for char in text:
        if is_char_supported(char, font_name):
            canvas.setFont(font_name, font_size)
            canvas.drawString(curr_x, y, char)
            curr_x += pdfmetrics.stringWidth(char, font_name, font_size)
        elif emoji_font:
            if emoji_description:
                canvas.setFont(font_name, font_size)
                label = f"[{char}]"
                canvas.drawString(curr_x, y, label)
                curr_x += pdfmetrics.stringWidth(label, font_name, font_size)
            else:
                canvas.setFont(emoji_font, font_size)
                canvas.drawString(curr_x, y, char)
                curr_x += pdfmetrics.stringWidth(char, emoji_font, font_size)
        else:
            canvas.setFont(font_name, font_size)
            canvas.drawString(curr_x, y, "?")
            curr_x += pdfmetrics.stringWidth("?", font_name, font_size)
    return curr_x

def draw_centred_text_with_fallback(canvas, x, y, text, font_name, font_size, emoji_font=None, color=None, emoji_description=False):
    w = get_safe_string_width(text, font_name, font_size, emoji_font, emoji_description)
    return draw_text_with_fallback(canvas, x - w/2.0, y, text, font_name, font_size, emoji_font, color, emoji_description)

def get_contrast_color(hex_color: str) -> colors.Color:
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3: hex_color = ''.join([c*2 for c in hex_color])
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return colors.white if brightness < 128 else colors.black
    except:
        return colors.white
