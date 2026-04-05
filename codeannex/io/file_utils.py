import fnmatch
import os
import subprocess
from pathlib import Path


def classify_file(filepath: Path) -> str:
    """Detects binaries cross-platform."""
    try:
        if filepath.stat().st_size == 0: return "text"
        with open(filepath, "rb") as f:
            chunk = f.read(512)
        return "binary" if b"\0" in chunk else "text"
    except Exception: return "error"


def is_text_file(filepath: Path) -> bool:
    binary_extensions = {".pdf", ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                        ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".whl"}
    if filepath.suffix.lower() in binary_extensions: return False
    return classify_file(filepath) == "text"


class FallbackGitignoreFilter:
    def __init__(self, root: Path):
        self.root = root
        gi = root / ".gitignore"
        self.rules = []
        if gi.exists():
            for line in gi.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self.rules.append(line.rstrip("/"))

    def is_ignored(self, path: Path) -> bool:
        try:
            rel = path.relative_to(self.root)
        except ValueError: return False
        rel_str = rel.as_posix()
        parts   = rel.parts
        for rule in self.rules:
            if rule.startswith("/"):
                r = rule[1:]
                if fnmatch.fnmatch(rel_str, r) or fnmatch.fnmatch(rel_str, f"{r}/*"): return True
            else:
                if fnmatch.fnmatch(rel_str, rule) or fnmatch.fnmatch(rel_str, f"{rule}/*"): return True
                if any(fnmatch.fnmatch(p, rule) for p in parts): return True
        return False


def sort_files(files: list[Path], root: Path) -> list[Path]:
    def sort_key(p: Path):
        parts = p.relative_to(root).parts
        dirs, fname = parts[:-1], parts[-1]
        # (0, d) for directories, (1, fname) for files
        # This makes subdirectories appear before files in the same level
        return tuple(val for d in dirs for val in (0, d.lower())) + (1, fname.lower())
    return sorted(files, key=sort_key)


def should_include(path: Path, root: Path, includes: list[str] | None, excludes: list[str] | None) -> bool:
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError: return True
        
    if excludes:
        for pattern in excludes:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, f"{pattern}/*") or any(fnmatch.fnmatch(p, pattern) for p in Path(rel_path).parts):
                return False

    if includes:
        matched = False
        for pattern in includes:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, f"{pattern}/*") or any(fnmatch.fnmatch(p, pattern) for p in Path(rel_path).parts):
                matched = True
                break
        if not matched: return False

    return True


def get_project_files(root: Path, includes: list[str] | None = None, excludes: list[str] | None = None, use_git: bool = True) -> list[Path]:
    files = []
    if use_git:
        try:
            from .git_utils import get_git_files
            all_git_files = get_git_files(root)
            for f in all_git_files:
                if should_include(f, root, includes, excludes): files.append(f)
            print("✅ Using Git (Recommended) to perfectly interpret .gitignore.")
            return sorted(files)
        except (subprocess.CalledProcessError, FileNotFoundError, ImportError):
            print("⚠️ Git not detected. (Recommended: install git for better file detection)")
            print("   - Linux: sudo apt install git (Ubuntu/Debian) or sudo dnf install git (Fedora)")
            print("   - Windows: Install from https://git-scm.com/download/win")

    print("ℹ️ Using manual scan (Fallback).")
    system_ignores = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
    filt  = FallbackGitignoreFilter(root)
    for dp, dns, fns in os.walk(root):
        curr   = Path(dp)
        dns[:] = [d for d in dns if d not in system_ignores and not filt.is_ignored(curr / d) and should_include(curr / d, root, None, excludes)]
        for f in fns:
            fpath = curr / f
            if not filt.is_ignored(fpath) and should_include(fpath, root, includes, excludes):
                files.append(fpath)
                    
    return sorted(files)
