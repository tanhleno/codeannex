import unicodedata
from pathlib import Path
from reportlab.pdfbase import pdfmetrics

from .fonts import is_char_supported, is_emoji


def sanitize_text(text: str) -> str:
    """Remove caracteres de controle invisíveis que quebram o PDF, mantendo emojis intactos."""
    return "".join(
        c if (ord(c) >= 0x20 and ord(c) != 0x7F) or ord(c) in (0x09, 0x0A, 0x0D)
        else " "
        for c in text
    )


def replace_unsupported_emojis(text: str, main_font: str, emoji_font: str | None,
                               emoji_description: bool = False) -> str:
    """Emojis are rendered natively when emoji_font is properly configured.
    If emoji_description is True, emojis are replaced by their [NAME]."""
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
    """Agrupa caracteres consecutivos que usam a mesma fonte, gerando (segmento, usa_emoji)."""
    text = replace_unsupported_emojis(text, main_font, emoji_font, emoji_description)
    segment, using_emoji = "", False
    for c in text:
        # Detecta emojis diretamente pelos ranges Unicode
        needs_emoji = (
            is_emoji(c)
            and emoji_font is not None
            and not emoji_description
        )
        if needs_emoji != using_emoji:
            if segment:
                yield segment, using_emoji
            segment, using_emoji = "", needs_emoji
        segment += c
    if segment:
        yield segment, using_emoji


def _draw_segment(canvas_obj, x: float, y: float, seg: str,
                  font: str, main_font: str, font_size: float) -> float:
    """Draws a segment and returns the new x. Falls back to ASCII in case of error."""
    curr_x = x
    for c in seg:
        if is_emoji(c):
            # Use emoji font with slightly larger size for better appearance
            emoji_size = font_size * 1.1
            canvas_obj.setFont(font, emoji_size)
            try:
                canvas_obj.drawString(curr_x, y, c)
                curr_x += pdfmetrics.stringWidth(c, font, emoji_size)
            except Exception as e:
                canvas_obj.setFont(main_font, font_size)
                canvas_obj.drawString(curr_x, y, "?")
                curr_x += pdfmetrics.stringWidth("?", main_font, font_size)
        else:
            canvas_obj.setFont(font, font_size)
            try:
                canvas_obj.drawString(curr_x, y, c)
                curr_x += pdfmetrics.stringWidth(c, font, font_size)
            except Exception:
                canvas_obj.setFont(main_font, font_size)
                clean = c if ord(c) <= 255 else "?"
                canvas_obj.drawString(curr_x, y, clean)
                curr_x += pdfmetrics.stringWidth(clean, main_font, font_size)
    return curr_x


def get_safe_string_width(text: str, main_font: str, font_size: float,
                          emoji_font: str | None, emoji_description: bool = False) -> float:
    total = 0.0
    for seg, using_emoji in _iter_segments(text, main_font, emoji_font, emoji_description):
        for c in seg:
            if is_emoji(c) and emoji_font and not emoji_description:
                emoji_size = font_size * 1.1
                try:
                    total += pdfmetrics.stringWidth(c, emoji_font, emoji_size)
                except Exception:
                    total += pdfmetrics.stringWidth("?", main_font, font_size)
            else:
                font = emoji_font if (using_emoji and not emoji_description) else main_font
                try:
                    total += pdfmetrics.stringWidth(c, font, font_size)
                except Exception:
                    clean = c if ord(c) <= 255 else "?"
                    total += pdfmetrics.stringWidth(clean, main_font, font_size)
    return total


def draw_text_with_fallback(canvas_obj, x: float, y: float, text: str,
                             main_font: str, font_size: float,
                             emoji_font: str | None, text_color=None,
                             emoji_description: bool = False) -> float:
    if text_color:
        canvas_obj.setFillColor(text_color)
    curr_x = x
    for seg, using_emoji in _iter_segments(text, main_font, emoji_font, emoji_description):
        font = emoji_font if (using_emoji and not emoji_description) else main_font
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
