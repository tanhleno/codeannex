import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from codeannex.io.git_utils import get_git_info, get_git_remotes

class TestGitIntegration:
    def should_get_git_remotes_success(self):
        """Testa a obtenção de múltiplos remotos."""
        with patch("subprocess.run") as mock_run:
            stdout = "origin\thttps://github.com/user/repo.git (fetch)\norigin\thttps://github.com/user/repo.git (push)\nupstream\thttps://github.com/other/repo.git (fetch)\n"
            mock_run.return_value = MagicMock(returncode=0, stdout=stdout)
            
            remotes = get_git_remotes(Path("."))
            assert len(remotes) == 2
            assert remotes["origin"] == "https://github.com/user/repo.git"
            assert remotes["upstream"] == "https://github.com/other/repo.git"

    def should_get_git_info_success(self):
        """Simula sucesso na obtenção de URL, Branch e SHA na raiz do repo."""
        with patch("subprocess.run") as mock_run:
            m_inside = MagicMock(returncode=0)
            m_toplevel = MagicMock(returncode=0, stdout=str(Path(".").resolve()))
            m_url = MagicMock(returncode=0, stdout="https://github.com/user/repo.git")
            m_branch = MagicMock(returncode=0, stdout="feature-branch")
            m_sha = MagicMock(returncode=0, stdout="a1b2c3d")
            
            mock_run.side_effect = [m_inside, m_toplevel, m_url, m_branch, m_sha]
            
            url, branch, sha = get_git_info(Path("."))
            assert url == "https://github.com/user/repo.git"
            assert branch == "feature-branch"
            assert sha == "a1b2c3d"

    def should_get_git_info_no_git_directory(self):
        """Simula falha quando não é um repositório git."""
        with patch("subprocess.run") as mock_run:
            # rev-parse --is-inside-work-tree falha
            mock_run.side_effect = [MagicMock(returncode=1)]
            
            url, branch, sha = get_git_info(Path("."))
            assert url is None
            assert branch is None
            assert sha is None

    def should_get_git_info_no_remote(self):
        """Simula caso onde há git na raiz mas não há remote origin."""
        with patch("subprocess.run") as mock_run:
            m_inside = MagicMock(returncode=0)
            m_toplevel = MagicMock(returncode=0, stdout=str(Path(".").resolve()))
            m_url = MagicMock(returncode=1) # remote get-url falha
            m_branch = MagicMock(returncode=0, stdout="main")
            m_sha = MagicMock(returncode=0, stdout="abc1234")
            
            mock_run.side_effect = [m_inside, m_toplevel, m_url, m_branch, m_sha]
            
            url, branch, sha = get_git_info(Path("."))
            assert url is None
            assert branch == "main"
            assert sha == "abc1234"

    def should_return_none_if_target_is_subdirectory_of_repo(self):
        """Verifica que metadados do Git não são retornados se a pasta alvo for uma subpasta."""
        with patch("subprocess.run") as mock_run:
            m_inside = MagicMock(returncode=0)
            # Toplevel é /workspaces/repo, mas o root alvo é /workspaces/repo/tests
            m_toplevel = MagicMock(returncode=0, stdout="/workspaces/repo")
            
            mock_run.side_effect = [m_inside, m_toplevel]
            
            url, branch, sha = get_git_info(Path("/workspaces/repo/tests"))
            assert url is None
            assert branch is None
            assert sha is None
