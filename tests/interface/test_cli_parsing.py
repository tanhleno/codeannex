import pytest
from codeannex.interface.cli import parse_args
import sys
from unittest.mock import patch

class TestCliParsing:
    def should_parse_args_defaults(self):
        """Testa se os valores padrão são atribuídos corretamente."""
        with patch.object(sys, 'argv', ['codeannex']):
            args, unknown = parse_args()
            assert args.dir == "."
            assert args.output is None
            assert args.cover_title == "TECHNICAL ANNEX"
            assert args.start_page == 1
            assert not args.no_git

    def should_parse_args_custom_values(self):
        """Testa se valores personalizados via CLI são respeitados."""
        test_args = [
            'codeannex', 'my_project',
            '-o', 'custom.pdf',
            '--cover-title', 'My Manual',
            '--margin-top', '3.5',
            '--page-width', '210',
            '--no-git',
            '--include', 'src/*.py',
            '--include', 'lib/*.py'
        ]
        with patch.object(sys, 'argv', test_args):
            args, unknown = parse_args()
            assert args.dir == "my_project"
            assert args.output == "custom.pdf"
            assert args.cover_title == "My Manual"
            assert args.margin_top == 3.5
            assert args.page_width == 210.0
            assert args.no_git is True
            assert args.include == ['src/*.py', 'lib/*.py']

    def should_parse_args_unknown_arguments(self):
        """Verifica se argumentos desconhecidos são capturados."""
        with patch.object(sys, 'argv', ['codeannex', '--unsupported-flag', 'value']):
            args, unknown = parse_args()
            assert '--unsupported-flag' in unknown
