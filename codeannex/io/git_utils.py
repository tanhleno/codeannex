import subprocess
from pathlib import Path

def get_git_info(root: Path, use_git: bool = True) -> tuple[str | None, str | None, str | None]:
    """Retrieves origin URL, current branch and commit SHA from Git."""
    if not use_git: return None, None, None
        
    repo_url, branch_name, commit_sha = None, None, None
    try:
        # Check if inside a work tree first
        res_inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True)
        if res_inside.returncode != 0: return None, None, None

        # Check if the current root is the top-level of the repository
        res_toplevel = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
        if res_toplevel.returncode == 0:
            toplevel_path = Path(res_toplevel.stdout.strip()).resolve()
            if toplevel_path != root.resolve():
                return None, None, None

        # 1. Get remote URL
        res_url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True)
        if res_url.returncode == 0: repo_url = res_url.stdout.strip()
            
        # 2. Get current branch
        res_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True)
        branch_name = res_branch.stdout.strip() if res_branch.returncode == 0 else None
        if not branch_name:
            res_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, capture_output=True, text=True)
            if res_branch.returncode == 0:
                branch_name = res_branch.stdout.strip()
                if branch_name == "HEAD": branch_name = None

        # 3. Get commit SHA (short)
        res_sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True)
        if res_sha.returncode == 0: commit_sha = res_sha.stdout.strip()

    except (subprocess.CalledProcessError, FileNotFoundError): pass
    return repo_url, branch_name, commit_sha

def get_git_files(root: Path) -> list[Path]:
    """Returns a list of files tracked or untracked by Git, respecting .gitignore."""
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout.split(b"\0")
    untracked = subprocess.run(["git", "ls-files", "-z", "--others", "--exclude-standard"], cwd=root, capture_output=True, check=True).stdout.split(b"\0")
    return [root / f.decode() for f in set(tracked + untracked) if f]
