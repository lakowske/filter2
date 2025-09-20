"""Tests for the CLI module."""

from click.testing import CliRunner

from filter.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Filter CLI tool" in result.output
        assert "Commands:" in result.output

    def test_status_command(self) -> None:
        """Test status command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        # Command should either succeed or fail gracefully
        assert "GitHub CLI" in result.output

    def test_project_help(self) -> None:
        """Test project subcommand help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["project", "--help"])

        assert result.exit_code == 0
        assert "Manage filter projects" in result.output
        assert "create" in result.output
        assert "delete" in result.output
        assert "info" in result.output

    def test_project_create_help(self) -> None:
        """Test project create command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["project", "create", "--help"])

        assert result.exit_code == 0
        assert "Create a new filter project structure" in result.output

    def test_project_delete_help(self) -> None:
        """Test project delete command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["project", "delete", "--help"])

        assert result.exit_code == 0
        assert "Delete a filter project structure" in result.output
        assert "--force" in result.output

    def test_project_info_help(self) -> None:
        """Test project info command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["project", "info", "--help"])

        assert result.exit_code == 0
        assert "Show information about a filter project" in result.output
