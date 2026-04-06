import pytest
from unittest.mock import patch, MagicMock
from codeannex.__main__ import main
import sys

def should_exit_gracefully_on_main_keyboard_interrupt():
    """Testa se o programa principal encerra graciosamente com Ctrl+C fora do wizard."""
    # Mock para o _main_impl levantar KeyboardInterrupt
    # Isso simula o usuário apertando Ctrl+C durante qualquer parte do processo
    with patch('codeannex.__main__._main_impl', side_effect=KeyboardInterrupt):
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                main()
                # Verifica se a mensagem de aborto foi impressa
                # Usamos any para checar se alguma das chamadas ao print contém a mensagem
                called_with_abort = any("Operation aborted by user" in str(call) for call in mock_print.call_args_list)
                assert called_with_abort
                # Verifica se saiu com 0
                mock_exit.assert_called_once_with(0)
