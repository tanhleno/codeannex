import fnmatch
import os
import subprocess
from pathlib import Path


def classify_file(filepath: Path) -> str:
    """
    Detects binaries cross-platform (Windows/Linux/macOS).
    Simple and reliable heuristic: null bytes = binary
    Returns: "text", "binary", or "error"
    """
    try:
        # Empty files are text
        if filepath.stat().st_size == 0:
            return "text"

        # Read first 512 bytes (enough to detect null bytes)
        with open(filepath, "rb") as f:
            chunk = f.read(512)

        # Null bytes is the most reliable indicator of binary
        # (works on Windows, Linux, macOS without dependencies)
        if b"\0" in chunk:
            return "binary"

        return "text"
    except Exception:
        return "error"


def is_text_file(filepath: Path) -> bool:
    # Rejeita extensões binárias conhecidas rapidamente
    binary_extensions = {".pdf", ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                        ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".whl"}
    if filepath.suffix.lower() in binary_extensions:
        return False

    return classify_file(filepath) == "text"


def is_binary_file(filepath: Path) -> bool:
    return classify_file(filepath) == "binary"


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
        except ValueError:
            return False
        rel_str = rel.as_posix()
        parts   = rel.parts
        for rule in self.rules:
            if rule.startswith("/"):
                r = rule[1:]
                if fnmatch.fnmatch(rel_str, r) or fnmatch.fnmatch(rel_str, f"{r}/*"):
                    return True
            else:
                if fnmatch.fnmatch(rel_str, rule) or fnmatch.fnmatch(rel_str, f"{rule}/*"):
                    return True
                if any(fnmatch.fnmatch(p, rule) for p in parts):
                    return True
        return False


def sort_files(files: list[Path], root: Path) -> list[Path]:
    """
    Sorts files respecting the rule:
    - Root files first, in alphabetical order
    - Then each directory (alphabetical), recursively with the same rule
    """
    def sort_key(p: Path):
        parts = p.relative_to(root).parts
        # Intercala cada parte com um flag (1 = está dentro de dir, 0 = é arquivo na raiz do nível)
        # Para cada nível exceto o último (nome do arquivo), coloca (1, nome_dir)
        # Para o arquivo em si, coloca (0, nome) no seu nível
        dirs  = parts[:-1]
        fname = parts[-1]
        return tuple(val for d in dirs for val in (1, d.lower())) + (0, fname.lower())

    return sorted(files, key=sort_key)


def get_project_files(root: Path) -> list[Path]:
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       cwd=root, capture_output=True, check=True)
        tracked   = subprocess.run(["git", "ls-files", "-z"],
                                   cwd=root, capture_output=True, check=True).stdout.split(b"\0")
        untracked = subprocess.run(["git", "ls-files", "-z", "--others", "--exclude-standard"],
                                   cwd=root, capture_output=True, check=True).stdout.split(b"\0")
        files = [root / f.decode() for f in set(tracked + untracked) if f]
        print("✅ Using Git's native engine to perfectly interpret .gitignore.")
        return sorted(files)

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Git not detected in the project. Using manual scan with Fallback.")
        system_ignores = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
        filt  = FallbackGitignoreFilter(root)
        files = []
        for dp, dns, fns in os.walk(root):
            curr   = Path(dp)
            dns[:] = [d for d in dns if d not in system_ignores and not filt.is_ignored(curr / d)]
            files.extend(curr / f for f in fns if not filt.is_ignored(curr / f))
        return sorted(files)
