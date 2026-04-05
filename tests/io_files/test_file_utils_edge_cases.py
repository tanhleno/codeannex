import pytest
from pathlib import Path
from codeannex.io.file_utils import classify_file, is_text_file, FallbackGitignoreFilter

class TestFileUtilsEdgeCases:
    def should_classify_empty_file(self, tmp_path):
        """Arquivos vazios devem ser classificados como texto."""
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        assert classify_file(empty) == "text"

    def should_classify_binary_with_null_byte(self, tmp_path):
        """Arquivos com byte nulo devem ser binários."""
        binary = tmp_path / "null.bin"
        binary.write_bytes(b"hello\0world")
        assert classify_file(binary) == "binary"

    def should_is_text_file_rejects_common_binaries(self):
        """Extensões conhecidas devem ser rejeitadas rapidamente."""
        assert not is_text_file(Path("test.pdf"))
        assert not is_text_file(Path("test.exe"))
        assert not is_text_file(Path("test.zip"))

    def should_gitignore_filter_logic(self, tmp_path):
        """Testa a lógica manual de parsing do .gitignore."""
        (tmp_path / ".gitignore").write_text("*.log\n/dist\ntemp/")
        filt = FallbackGitignoreFilter(tmp_path)
        assert filt.is_ignored(tmp_path / "error.log")
        assert filt.is_ignored(tmp_path / "dist/bundle.js")
        assert filt.is_ignored(tmp_path / "temp/file.txt")
        assert not filt.is_ignored(tmp_path / "main.py")

    def should_classify_file_permission_error(self, tmp_path):
        """Verifica se classify_file lida com erros de leitura."""
        locked = tmp_path / "locked.txt"
        locked.write_text("secret")
        locked.chmod(0o000)
        res = classify_file(locked)
        assert res in ["text", "error"]
        locked.chmod(0o666)
