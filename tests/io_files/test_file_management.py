import pytest
from pathlib import Path
from codeannex.io.file_utils import get_project_files, classify_file, sort_files
from codeannex.core.config import BINARY_EXTENSIONS

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

    def should_sort_files_alphabetically_with_subdirs_first(self, tmp_path):
        """Testa a ordenação de arquivos: subdiretórios primeiro, depois arquivos na raiz."""
        root = tmp_path
        (root / "z.txt").write_text("z")
        (root / "dir_a").mkdir()
        (root / "dir_a" / "file.txt").write_text("content")
        (root / "a.txt").write_text("a")
        
        files = [root / "z.txt", root / "dir_a" / "file.txt", root / "a.txt"]
        sorted_list = sort_files(files, root)
        
        # dir_a/file.txt (subdiretório) -> a.txt (raiz) -> z.txt (raiz)
        assert "dir_a" in str(sorted_list[0])
        assert sorted_list[1].name == "a.txt"
        assert sorted_list[2].name == "z.txt"

    def should_filter_files_by_include_and_exclude_patterns(self, tmp_path):
        """Verifica se os padrões de inclusão e exclusão funcionam corretamente."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("main")
        (tmp_path / "src" / "utils.py").write_text("utils")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("test")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "readme.md").write_text("readme")
        (tmp_path / "extra.txt").write_text("extra")

        # 1. Test excludes
        files = get_project_files(tmp_path, excludes=["tests/*", "docs/*"])
        assert not any("tests" in str(f) for f in files)
        assert not any("docs" in str(f) for f in files)
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "extra.txt" for f in files)

        # 2. Test includes
        files = get_project_files(tmp_path, includes=["src/*"])
        assert all("src" in str(f) for f in files)
        assert len(files) == 2

        # 3. Test combined
        files = get_project_files(tmp_path, includes=["src/*", "extra.txt"], excludes=["*utils.py"])
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "extra.txt" for f in files)
        assert not any(f.name == "utils.py" for f in files)
        assert len(files) == 2

    def should_fallback_to_manual_scan_when_git_is_disabled(self, tmp_path):
        """Verifica se o scan manual funciona corretamente quando o Git é desativado via flag."""
        (tmp_path / "manual.txt").write_text("manual content")
        (tmp_path / ".git").mkdir() # Mesmo com pasta .git presente
        
        # Chama explicitamente com use_git=False
        files = get_project_files(tmp_path, use_git=False)
        
        assert len(files) >= 1
        assert any(f.name == "manual.txt" for f in files)
        # O scan manual deve ignorar a pasta .git por padrão
        assert not any(".git" in str(f) for f in files)
