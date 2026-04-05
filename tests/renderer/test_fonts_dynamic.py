import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from codeannex.renderer.fonts import find_font_file, auto_register_font

class TestFontsDynamic:
    def should_find_font_file_not_found(self):
        """Test that find_font_file returns None for a non-existent font."""
        assert find_font_file("NonExistentFont12345") is None

    def should_auto_register_standard_fonts(self):
        """Test that standard ReportLab fonts are returned as-is."""
        assert auto_register_font("Helvetica") == "Helvetica"
        assert auto_register_font("Times-Roman") == "Times-Roman"
        assert auto_register_font("Courier") == "Courier"

    def should_auto_register_font_not_found_warning(self, capsys):
        """Test that auto_register_font prints a warning but doesn't exit."""
        res = auto_register_font("MissingFontExample", required=False)
        out, err = capsys.readouterr()
        assert res == "MissingFontExample"
        assert "⚠️ WARNING: Font 'MissingFontExample' not found" in out

    def should_auto_register_font_not_found_exit(self, capsys):
        """Test that auto_register_font exits with error when required=True."""
        with pytest.raises(SystemExit) as excinfo:
            auto_register_font("MissingFontFatal", required=True)
        out, err = capsys.readouterr()
        assert "🛑 ERROR: Font 'MissingFontFatal' not found" in err
        assert excinfo.value.code == 1

    @patch("codeannex.renderer.fonts.find_font_file")
    @patch("codeannex.renderer.fonts.TTFont")
    @patch("reportlab.pdfbase.pdfmetrics.registerFont")
    def should_auto_register_dynamic_success(self, mock_register, mock_ttfont, mock_find):
        """Test that a font found in the system is correctly registered."""
        mock_find.return_value = "/path/to/FakeFont.ttf"
        mock_ttfont.return_value = MagicMock()
        res = auto_register_font("FakeFont")
        assert res == "FakeFont"
        mock_register.assert_called_once()
