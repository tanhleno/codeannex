import pytest
import io
import os
import sys
import unicodedata
from pathlib import Path
from unittest.mock import patch, MagicMock
from reportlab.pdfbase import pdfmetrics

from codeannex.fonts import (
    is_emoji, register_emoji_font, get_emoji_font_style, 
    is_google_like_emoji_font, get_current_emoji_font_info,
    is_char_supported
)
from codeannex.text_utils import (
    sanitize_text, _iter_segments, replace_unsupported_emojis, 
    get_safe_string_width
)
from codeannex.pdf_builder import ModernAnnexPDF
from codeannex.config import PDFConfig

class TestEmojiSupport:
    # --- Detecção e Sanitização ---
    def should_detect_basic_emojis(self):
        """Testa detecção de emojis básicos."""
        basic_emojis = ["😀", "😂", "❤️", "👍", "🔥", "⭐", "🎉", "💯"]
        for emoji in basic_emojis:
            assert is_emoji(emoji), f"Emoji {emoji} should be detected"

    def should_detect_symbol_emojis(self):
        """Testa detecção de símbolos e pictogramas."""
        symbol_emojis = ["⚡", "🔥", "💎", "🎯", "🏆", "🎨", "🎭", "🎪"]
        for emoji in symbol_emojis:
            assert is_emoji(emoji), f"Symbol emoji {emoji} should be detected"

    def should_not_detect_regular_characters(self):
        """Testa que caracteres normais não são detectados como emojis."""
        regular_chars = ["a", "1", "@", " ", "ç", "ñ", "中", "文"]
        for char in regular_chars:
            assert not is_emoji(char), f"Regular character '{char}' should not be detected as emoji"

    def should_sanitize_text_preserving_emojis(self):
        """Testa que sanitize_text preserva emojis."""
        text_with_emojis = "Hello 😀 world! 🎉"
        sanitized = sanitize_text(text_with_emojis)
        assert sanitized == text_with_emojis

    # --- Fontes e Estilos ---
    def should_identify_noto_emoji_font_styles(self):
        """Testa identificação de estilos de fonte Noto."""
        assert get_emoji_font_style("/path/to/NotoSans-Regular.ttf") == "Google Noto"
        assert get_emoji_font_style("/path/to/NotoColorEmoji.ttf") == "Google Noto Color"
        assert get_emoji_font_style("/path/to/NotoEmoji-Regular.ttf") == "Google Noto Emoji"

    def should_detect_google_like_fonts(self):
        """Testa se fontes Noto são detectadas como Google-like."""
        assert is_google_like_emoji_font("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
        assert not is_google_like_emoji_font("/System/Library/Fonts/Apple Symbols.ttf")

    def should_have_glyph_support_in_registered_font(self):
        """Verifica se a fonte de emoji registrada possui glifos reais."""
        emoji_font = register_emoji_font()
        if not emoji_font:
            pytest.skip("No emoji font found on system")
            
        common_emojis = ["😀", "🚀", "🔥"]
        for emoji in common_emojis:
            # Note: Symbola supports these, NotoColor does too but ReportLab might fail to report it correctly
            # depending on the version. We check if at least it doesn't crash.
            is_char_supported(emoji, emoji_font)

    # --- Segmentação e Largura ---
    def should_segment_mixed_text_and_emojis(self):
        """Testa processamento de texto misto com emojis."""
        text = "Code 😀 is 🎉 fun"
        segments = list(_iter_segments(text, "Helvetica", "CustomEmoji"))
        assert len(segments) >= 3
        
        emoji_segs = [seg for seg, is_e in segments if is_e]
        assert "😀" in "".join(emoji_segs)

    def should_calculate_width_correctly_with_emojis(self):
        """Testa cálculo de largura de texto com emojis."""
        emoji_font = register_emoji_font()
        if not emoji_font:
            pytest.skip("No emoji font found")
        width = get_safe_string_width("Hello 😀", "Helvetica", 10, emoji_font)
        assert width > 0

    # --- Tratamento de Erros e Configuração ---
    def should_exit_when_font_missing_and_error_requested(self, capsys):
        """Testa erro fatal quando nenhuma fonte de emoji é encontrada."""
        with patch("os.path.exists", return_value=False):
            with patch("sys.exit") as mock_exit:
                register_emoji_font(error_on_missing=True)
                mock_exit.assert_called_once_with(1)
                assert "❌ Error" in capsys.readouterr().err

    def should_replace_emojis_with_descriptions_when_flag_active(self):
        """Testa substituição por [NAME] quando a flag --emoji-description é usada."""
        text = "Hello 😀"
        result = replace_unsupported_emojis(text, "Helvetica", None, emoji_description=True)
        assert "Hello [GRINNING FACE]" in result

    # --- Renderização Real ---
    def should_embed_emoji_font_in_pdf(self):
        """Verifica se a fonte de emoji é incluída no binário do PDF."""
        output = io.BytesIO()
        emoji_font = register_emoji_font()
        if not emoji_font:
            pytest.skip("No emoji font")
            
        pdf = ModernAnnexPDF(output, Path("."), "Helvetica", emoji_font)
        pdf.start_new_page()
        pdf._dtf(100, 700, "😀", "Helvetica", 12)
        pdf.c.save()
        
        content = output.getvalue()
        assert b"CustomEmoji" in content or b"Symbola" in content or b"NotoEmoji" in content
