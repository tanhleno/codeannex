import pytest
from reportlab.lib import colors
from codeannex.renderer.text_utils import get_contrast_color

class TestTextUtils:
    def should_return_white_for_dark_colors(self):
        """Test that dark backgrounds produce white text."""
        assert get_contrast_color("#000000") == colors.white
        assert get_contrast_color("#0f4761") == colors.white
        assert get_contrast_color("#313244") == colors.white

    def should_return_black_for_light_colors(self):
        """Test that light backgrounds produce black text."""
        assert get_contrast_color("#ffffff") == colors.black
        assert get_contrast_color("#ffff00") == colors.black
        assert get_contrast_color("#89b4fa") == colors.black

    def should_handle_short_hex_codes(self):
        """Test that 3-digit hex codes are handled correctly."""
        assert get_contrast_color("#000") == colors.white
        assert get_contrast_color("#fff") == colors.black

    def should_fallback_gracefully_on_invalid_hex(self):
        """Test that invalid input doesn't crash the program."""
        assert get_contrast_color("not-a-color") == colors.white
