import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from codeannex.fonts import find_font_file, auto_register_font

def should_find_font_file_not_found():
    """Test that find_font_file returns None for a non-existent font."""
    # Searching for a very unlikely font name
    assert find_font_file("NonExistentFont12345") is None

def should_auto_register_standard_fonts():
    """Test that standard ReportLab fonts are returned as-is without searching."""
    assert auto_register_font("Helvetica") == "Helvetica"
    assert auto_register_font("Times-Roman") == "Times-Roman"
    assert auto_register_font("Courier") == "Courier"

def should_auto_register_font_not_found_warning(capsys):
    """Test that auto_register_font prints a warning with ⚠️ but doesn't exit when not required."""
    res = auto_register_font("MissingFontExample", required=False)
    out, err = capsys.readouterr()
    assert res == "MissingFontExample"
    assert "⚠️ WARNING: Font 'MissingFontExample' not found" in out

def should_auto_register_font_not_found_exit(capsys):
    """Test that auto_register_font exits with an error message starting with 🛑 when required=True."""
    with pytest.raises(SystemExit) as excinfo:
        auto_register_font("MissingFontFatal", required=True)
    out, err = capsys.readouterr()
    # Check stderr (since we used file=sys.stderr)
    assert "🛑 ERROR: Font 'MissingFontFatal' not found" in err
    assert excinfo.value.code == 1

@patch("codeannex.fonts.find_font_file")
@patch("codeannex.fonts.TTFont")
@patch("reportlab.pdfbase.pdfmetrics.registerFont")
def should_auto_register_dynamic_success(mock_register, mock_ttfont, mock_find):
    """Test that a font found in the system is correctly registered."""
    mock_find.return_value = "/path/to/FakeFont.ttf"
    mock_ttfont.return_value = MagicMock()
    
    res = auto_register_font("FakeFont")
    
    assert res == "FakeFont"
    mock_register.assert_called_once()
    # Check if we logged success
    # (Since we used print, we could use capsys if needed)
