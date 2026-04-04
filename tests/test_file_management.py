import pytest
from pathlib import Path
from codeannex.file_utils import get_project_files, classify_file, sort_files
from codeannex.config import BINARY_EXTENSIONS

class TestFileManagement:
    def should_identify_binary_files_by_extension(self):
        """Verifica se extensões binárias conhecidas são identificadas corretamente."""
        binary_samples = [".pdf", ".exe", ".zip", ".pyc"]
        for ext in binary_samples:
            assert ext in BINARY_EXTENSIONS

    def should_classify_file_as_text_or_binary(self, tmp_path):
        """Testa a classificação de arquivos baseada no conteúdo."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello world", encoding="utf-8")
        assert classify_file(text_file) == "text"
        
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(bytes([0x00, 0xFF, 0x00, 0x01]))
        assert classify_file(binary_file) == "binary"

    def should_get_project_files_respecting_git(self, tmp_path):
        """Testa a coleta de arquivos do projeto."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.py").write_text("b")
        (tmp_path / ".git").mkdir()
        
        files = get_project_files(tmp_path)
        assert len(files) >= 2
        assert any(f.name == "a.txt" for f in files)
        assert any(f.name == "b.py" for f in files)

    def should_sort_files_alphabetically_with_root_files_first(self, tmp_path):
        """Testa a ordenação de arquivos: arquivos na raiz primeiro, depois subdiretórios."""
        root = tmp_path
        (root / "z.txt").write_text("z")
        (root / "dir_a").mkdir()
        (root / "dir_a" / "file.txt").write_text("content")
        (root / "a.txt").write_text("a")
        
        files = [root / "z.txt", root / "dir_a" / "file.txt", root / "a.txt"]
        sorted_list = sort_files(files, root)
        
        # a.txt (raiz) -> z.txt (raiz) -> dir_a/file.txt (subdiretório)
        assert sorted_list[0].name == "a.txt"
        assert sorted_list[1].name == "z.txt"
        assert "dir_a" in str(sorted_list[2])
