import pytest
from pathlib import Path
from unittest.mock import MagicMock
from codeannex.core.pdf_builder import _make_bookmark_key

class TestSummaryHierarchy:
    def should_organize_files_into_nested_tree(self):
        """Tests the logic of building a nested tree for the summary."""
        root = Path("/workspaces/codeannex")
        files = [
            (root / "README.md", "text"),
            (root / ".github/workflows/publish.yml", "text"),
            (root / "codeannex/__init__.py", "text")
        ]
        
        nested_tree = {"_files": []}
        for fpath, ftype in files:
            rel = fpath.relative_to(root)
            curr = nested_tree
            for part in rel.parts[:-1]:
                curr = curr.setdefault(part, {"_files": []})
            curr["_files"].append((rel.name, _make_bookmark_key(rel.as_posix())))

        assert len(nested_tree["_files"]) == 1
        assert nested_tree["_files"][0][0] == "README.md"
        assert ".github" in nested_tree
        assert "workflows" in nested_tree[".github"]
        assert len(nested_tree[".github"]["workflows"]["_files"]) == 1
        assert "codeannex" in nested_tree

    def should_ensure_all_parent_folders_are_present(self):
        """Verify that even with deeply nested files, the full path is represented."""
        root = Path("/root")
        files = [(root / "a/b/c/d.py", "text")]
        
        nested_tree = {"_files": []}
        for fpath, ftype in files:
            rel = fpath.relative_to(root)
            curr = nested_tree
            for part in rel.parts[:-1]:
                curr = curr.setdefault(part, {"_files": []})
            curr["_files"].append((rel.name, _make_bookmark_key(rel.as_posix())))
            
        assert "a" in nested_tree
        assert "b" in nested_tree["a"]
        assert "c" in nested_tree["a"]["b"]
        assert nested_tree["a"]["b"]["c"]["_files"][0][0] == "d.py"
