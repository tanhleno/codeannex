import pytest
from unittest.mock import patch, MagicMock
from codeannex.__main__ import run_interactive_wizard

def should_update_args_from_wizard_input():
    """Tests that the wizard correctly updates args based on user input."""
    # Mocking argparse Namespace
    class MockArgs:
        def __init__(self):
            self.name = None
            self.cover_title = "DEFAULT"
            self.cover_subtitle = "SUB"
            self.primary_color = "#000"
            self.title_font = None
            self.normal_font = None
            self.mono_font = None
            self.margin_top = None
            self.margin_bottom = None
            self.margin_left = None
            self.margin_right = None
            self.no_page_numbers = False
            self.start_page = None

    args = MockArgs()
    
    # name, cover_title, cover_subtitle, primary_color, title_font, normal_font, mono_font,
    # margin_top, margin_bottom, margin_left, margin_right, no_page_numbers, start_page
    inputs = ["New Name", "", "New Sub", "", "CustomFont", "", "", "2.5", "2.5", "3.0", "3.0", "n", "10"]
    
    with patch('builtins.input', side_effect=inputs):
        run_interactive_wizard(args)
    
    assert args.name == "New Name"
    assert args.cover_title == "DEFAULT"
    assert args.cover_subtitle == "New Sub"
    assert args.title_font == "CustomFont"
    assert args.margin_top == 2.5
    assert args.margin_left == 3.0
    assert args.no_page_numbers is False
    assert args.start_page == 10

def should_skip_start_page_when_no_page_numbers():
    """Tests that the wizard skips start_page question when numbering is disabled."""
    class MockArgs:
        def __init__(self):
            self.no_page_numbers = False
            self.start_page = 1
            # Add other needed attributes
            self.name = self.cover_title = self.cover_subtitle = self.primary_color = None
            self.title_font = self.normal_font = self.mono_font = None
            self.margin_top = self.margin_bottom = self.margin_left = self.margin_right = None

    args = MockArgs()
    
    # Answers up to no_page_numbers = "y". 
    # There should NOT be a request for start_page after this.
    inputs = ["", "", "", "", "", "", "", "", "", "", "", "y"]
    
    with patch('builtins.input', side_effect=inputs) as mock_input:
        run_interactive_wizard(args)
        # Should have called input exactly 12 times (the number of inputs provided)
        assert mock_input.call_count == 12
    
    assert args.no_page_numbers is True
    assert args.start_page == 1 # Remained unchanged
