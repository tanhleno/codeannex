import pytest
from reportlab.lib import colors
from codeannex.text_utils import get_contrast_color

def should_return_white_for_dark_colors():
    """Test that dark backgrounds produce white text."""
    assert get_contrast_color("#000000") == colors.white # Black bg
    assert get_contrast_color("#0f4761") == colors.white # Your dark blue
    assert get_contrast_color("#313244") == colors.white # Catppuccin surface

def should_return_black_for_light_colors():
    """Test that light backgrounds produce black text."""
    assert get_contrast_color("#ffffff") == colors.black # White bg
    assert get_contrast_color("#ffff00") == colors.black # Yellow bg
    assert get_contrast_color("#89b4fa") == colors.black # Original light blue

def should_handle_short_hex_codes():
    """Test that 3-digit hex codes are handled correctly."""
    assert get_contrast_color("#000") == colors.white # Black
    assert get_contrast_color("#fff") == colors.black # White

def should_fallback_gracefully_on_invalid_hex():
    """Test that invalid input doesn't crash the program."""
    # Should default to white on error
    assert get_contrast_color("not-a-color") == colors.white
