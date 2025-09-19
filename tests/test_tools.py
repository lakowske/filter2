"""Tests for the tools module."""

import subprocess
from unittest.mock import Mock, patch

from filter.tools import check_github_cli, gh_clone_repo


class TestCheckGithubCli:
    """Tests for check_github_cli function."""

    @patch("filter.tools.subprocess.run")
    def test_github_cli_installed(self, mock_run: Mock) -> None:
        """Test when GitHub CLI is installed and working."""
        mock_run.return_value = Mock(stdout="gh version 2.32.1", returncode=0)

        is_installed, message = check_github_cli()

        assert is_installed is True
        assert message == "GitHub CLI (gh) is installed: gh version 2.32.1"
        mock_run.assert_called_once_with(
            ["gh", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("filter.tools.subprocess.run")
    def test_github_cli_command_error(self, mock_run: Mock) -> None:
        """Test when GitHub CLI command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["gh", "--version"], stderr="Command failed"
        )

        is_installed, message = check_github_cli()

        assert is_installed is False
        assert message == "GitHub CLI command failed: Command failed"

    @patch("filter.tools.subprocess.run")
    def test_github_cli_not_found(self, mock_run: Mock) -> None:
        """Test when GitHub CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()

        is_installed, message = check_github_cli()

        assert is_installed is False
        assert message == "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"


class TestGhCloneRepo:
    """Tests for gh_clone_repo function."""

    @patch("filter.tools.subprocess.run")
    def test_successful_clone(self, mock_run: Mock) -> None:
        """Test successful repository cloning."""
        mock_run.return_value = Mock(stdout="Cloning into 'repo'...", returncode=0)

        is_successful, message = gh_clone_repo("https://github.com/user/repo", "./test_dest")

        assert is_successful is True
        assert message == "Repository cloned successfully to ./test_dest"
        mock_run.assert_called_once_with(
            ["gh", "repo", "clone", "https://github.com/user/repo", "./test_dest"],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("filter.tools.subprocess.run")
    def test_clone_command_error(self, mock_run: Mock) -> None:
        """Test when clone command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["gh", "repo", "clone"], stderr="Repository not found"
        )

        is_successful, message = gh_clone_repo("https://github.com/user/nonexistent", "./test_dest")

        assert is_successful is False
        assert message == "Failed to clone repository: Repository not found"

    @patch("filter.tools.subprocess.run")
    def test_clone_github_cli_not_found(self, mock_run: Mock) -> None:
        """Test when GitHub CLI is not installed during clone."""
        mock_run.side_effect = FileNotFoundError()

        is_successful, message = gh_clone_repo("https://github.com/user/repo", "./test_dest")

        assert is_successful is False
        assert message == "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"
