import pytest
from unittest.mock import patch, MagicMock
from codeannex.interface.cli import run_interactive_wizard

class TestInteractive:
    def should_update_args_from_wizard_input_with_6_sections(self):
        """Tests that the wizard correctly updates args based on user input with 6 sections."""
        class MockArgs:
            def __init__(self):
                self.dir = "."
                self.name = None
                self.branch = None
                self.repo_url = None
                self.cover_title = "DEFAULT"
                self.cover_subtitle = "SUB"
                self.primary_color = "#000"
                self.title_color = "#111"
                self.title_font = None
                self.normal_font = None
                self.mono_font = None
                self.code_size = 10
                self.margin_top = None
                self.margin_bottom = None
                self.page_width = 210.0
                self.page_height = 297.0
                self.no_page_numbers = False
                self.start_page = 1
                self.include = None
                self.exclude = None

        args = MockArgs()
        
        # Inputs para 6 seções:
        # 1. Project Name
        # 2. Use detected Git? (Y/n) -> Digita 'n', depois Branch e URL
        # 3. Customize Style? (y/N) -> 'y', New Cover...
        # 4. Customize Typography? (y/N) -> 'n'
        # 5. Customize Layout? (y/N) -> 'y', Margins...
        # 6. Customize Filters? (y/N) -> 'y', Patterns...
        
        inputs = [
            "New Name",                                   # 1. Identity
            "n", "custom-branch", "https://custom.repo",  # 2. Repo (n -> manual)
            "y", "New Cover", "", "#ffffff", "",          # 3. Style (y)
            "n",                                          # 4. Typography (n)
            "y", "2.5", "2.5", "200", "200", "n", "5",    # 5. Layout (y)
            "y", "src/*", "tests/*"                       # 6. Filters (y)
        ]
        
        # Mockando get_git_info para retornar valores e ativar o fluxo de 'has_git'
        with patch('codeannex.interface.cli.get_git_info', return_value=("detect.url", "main", "abc12345")):
            with patch('codeannex.interface.cli.get_git_remotes', return_value={"origin": "detect.url"}):
                with patch('builtins.input', side_effect=inputs):
                    run_interactive_wizard(args)
        
        assert args.name == "New Name"
        assert args.branch == "custom-branch"
        assert args.repo_url == "https://custom.repo"
        assert args.cover_title == "New Cover"
        assert args.margin_top == 2.5
        assert args.page_width == 200.0
        assert args.start_page == 5
        assert args.include == ["src/*"]
        assert args.exclude == ["tests/*"]

    def should_skip_all_sections_when_answered_no(self):
        """Tests that answering default 'n' skips all optional sections."""
        class MockArgs:
            def __init__(self):
                self.dir = "."
                self.name = "Old"
                self.branch = "old"
                self.repo_url = "old.url"
                self.cover_title = "Old Title"
                self.no_page_numbers = False

        args = MockArgs()
        
        # 1. Name (Enter)
        # 2. Use detected Git? (Enter -> Yes)
        # 3. Style (Enter -> No)
        # 4. Typography (Enter -> No)
        # 5. Layout (Enter -> No)
        # 6. Filters (Enter -> No)
        inputs = ["", "", "", "", "", ""]
        
        with patch('codeannex.interface.cli.get_git_info', return_value=("detect.url", "main", "abc12345")):
            with patch('codeannex.interface.cli.get_git_remotes', return_value={"origin": "detect.url"}):
                with patch('builtins.input', side_effect=inputs):
                    run_interactive_wizard(args)
        
        assert args.name == "Old"
        assert args.branch == "main"
        assert args.repo_url == "detect.url"
        assert args.cover_title == "Old Title"

    def should_select_between_multiple_remotes(self):
        """Testa a seleção entre múltiplos remotos no assistente."""
        class MockArgs:
            def __init__(self):
                self.dir = "."
                self.name = "Test"
                self.branch = None
                self.repo_url = None
                self.no_page_numbers = False

        args = MockArgs()
        
        # 1. Name (Enter)
        # 2. Select remote "2" (upstream), then Use detected Git? (Enter -> Yes)
        # 3-6. Skip other sections (Enter x4)
        inputs = ["", "2", "", "", "", "", ""]
        
        remotes = {
            "origin": "https://github.com/user/origin.git",
            "upstream": "https://github.com/user/upstream.git"
        }
        
        with patch('codeannex.interface.cli.get_git_info', return_value=("detect.url", "main", "abc12345")):
            with patch('codeannex.interface.cli.get_git_remotes', return_value=remotes):
                with patch('builtins.input', side_effect=inputs):
                    run_interactive_wizard(args)
        
        assert args.repo_url == "https://github.com/user/upstream.git"
        assert args.branch == "main"
