import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_text_file():
    """Cria um arquivo de texto temporário e retorna o Path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello World")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_binary_file():
    """Cria um arquivo binário temporário e retorna o Path."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        f.write(b'\x00\x01\x02\x03')  # Null bytes
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_empty_file():
    """Cria um arquivo vazio temporário e retorna o Path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        pass  # Empty file
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_text_file_with_binary_extension():
    """Cria um arquivo de texto com extensão binária e retorna o Path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        f.write("This is text but has .pdf extension")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)