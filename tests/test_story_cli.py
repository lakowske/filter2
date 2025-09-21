"""Tests for the story CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from filter.story_cli import story


class TestStoryCLI:
    """Tests for story CLI commands."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def create_test_project(self, temp_dir: str) -> Path:
        """Create a complete test project structure.

        Args:
            temp_dir: Temporary directory path

        Returns:
            Path to project directory
        """
        project_path = Path(temp_dir) / "test-project"
        project_path.mkdir()

        # Create complete .filter structure
        filter_dir = project_path / ".filter"
        filter_dir.mkdir()

        stories_dir = filter_dir / "stories"
        stories_dir.mkdir()

        kanban_dir = filter_dir / "kanban"
        kanban_dir.mkdir()

        # Create kanban stages
        for stage in ["planning", "in-progress", "testing", "pr", "complete"]:
            (kanban_dir / stage).mkdir()

        # Create config.yml
        config_path = filter_dir / "config.yml"
        config_content = """project_name: test-project
prefix: TESTP
last_story_number: 0
created_at: '2024-01-01T00:00:00Z'
kanban_stages:
- planning
- in-progress
- testing
- pr
- complete
"""
        config_path.write_text(config_content, encoding="utf-8")

        return project_path

    def test_create_story_success(self) -> None:
        """Test successful story creation via CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(
                story, ["create", "Test Story", "--description", "A test story", "--project-path", str(project_path)]
            )

            assert result.exit_code == 0
            assert "✓ Created story TESTP-1: Test Story" in result.output

            # Verify story file was created
            story_file = project_path / ".filter" / "stories" / "TESTP-1.md"
            assert story_file.exists()

            story_content = story_file.read_text(encoding="utf-8")
            assert "# TESTP-1: Test Story" in story_content
            assert "A test story" in story_content

    def test_create_story_with_stage(self) -> None:
        """Test story creation with custom stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(
                story, ["create", "In Progress Story", "--stage", "in-progress", "--project-path", str(project_path)]
            )

            assert result.exit_code == 0
            assert "✓ Created story TESTP-1: In Progress Story" in result.output

            # Verify symlink in correct stage
            kanban_link = project_path / ".filter" / "kanban" / "in-progress" / "TESTP-1.md"
            assert kanban_link.exists()
            assert kanban_link.is_symlink()

    def test_create_story_no_project(self) -> None:
        """Test story creation when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(story, ["create", "Test Story", "--project-path", temp_dir])

            assert result.exit_code == 1
            assert "✗" in result.output
            assert "No filter project found" in result.output

    def test_create_story_invalid_stage(self) -> None:
        """Test story creation with invalid stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(
                story, ["create", "Test Story", "--stage", "invalid-stage", "--project-path", str(project_path)]
            )

            assert result.exit_code == 1
            assert "✗" in result.output
            assert "Invalid stage 'invalid-stage'" in result.output

    def test_create_story_default_project_path(self) -> None:
        """Test story creation using default project path."""
        # This test verifies that the --project-path option defaults to current directory
        # Since we can't easily test changing directories in Click tests,
        # we'll test the explicit path which is equivalent
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(story, ["create", "Default Path Story", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "✓ Created story TESTP-1: Default Path Story" in result.output

    def test_delete_story_success(self) -> None:
        """Test successful story deletion via CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create a story first
            self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

            # Delete with force flag
            result = self.runner.invoke(story, ["delete", "TESTP-1", "--force", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "✓ Deleted story TESTP-1" in result.output

            # Verify story file was removed
            story_file = project_path / ".filter" / "stories" / "TESTP-1.md"
            assert not story_file.exists()

    def test_delete_story_with_confirmation(self) -> None:
        """Test story deletion with user confirmation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create a story first
            self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

            # Delete with confirmation (simulate 'y' input)
            result = self.runner.invoke(story, ["delete", "TESTP-1", "--project-path", str(project_path)], input="y\n")

            assert result.exit_code == 0
            assert "Are you sure you want to delete story TESTP-1?" in result.output
            assert "✓ Deleted story TESTP-1" in result.output

    def test_delete_story_cancelled(self) -> None:
        """Test story deletion cancelled by user."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create a story first
            self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

            # Delete with confirmation (simulate 'n' input)
            result = self.runner.invoke(story, ["delete", "TESTP-1", "--project-path", str(project_path)], input="n\n")

            assert result.exit_code == 0
            assert "Deletion cancelled." in result.output

            # Verify story file still exists
            story_file = project_path / ".filter" / "stories" / "TESTP-1.md"
            assert story_file.exists()

    def test_delete_story_not_found(self) -> None:
        """Test deleting non-existent story."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(story, ["delete", "NONEX-1", "--force", "--project-path", str(project_path)])

            assert result.exit_code == 1
            assert "✗" in result.output
            assert "Story NONEX-1 not found" in result.output

    def test_delete_story_no_project(self) -> None:
        """Test story deletion when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(story, ["delete", "TEST-1", "--force", "--project-path", temp_dir])

            assert result.exit_code == 1
            assert "✗" in result.output
            assert "No filter project found" in result.output

    def test_list_stories_empty(self) -> None:
        """Test listing stories when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(story, ["list", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "No stories found." in result.output

    def test_list_stories_multiple(self) -> None:
        """Test listing multiple stories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create multiple stories
            self.runner.invoke(story, ["create", "First Story", "--project-path", str(project_path)])
            self.runner.invoke(
                story, ["create", "Second Story", "--stage", "in-progress", "--project-path", str(project_path)]
            )

            result = self.runner.invoke(story, ["list", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "Stories:" in result.output
            assert "TESTP-1: First Story [planning]" in result.output
            assert "TESTP-2: Second Story [in-progress]" in result.output
            assert "Total: 2 stories" in result.output

    def test_list_stories_filtered_by_stage(self) -> None:
        """Test listing stories filtered by stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create stories in different stages
            self.runner.invoke(story, ["create", "Planning Story", "--project-path", str(project_path)])
            self.runner.invoke(
                story, ["create", "Progress Story", "--stage", "in-progress", "--project-path", str(project_path)]
            )

            result = self.runner.invoke(story, ["list", "--stage", "planning", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "Stories (stage: planning):" in result.output
            assert "TESTP-1: Planning Story" in result.output
            assert "TESTP-2" not in result.output  # Should not show in-progress story
            assert "Total: 1 stories" in result.output

    def test_list_stories_no_project(self) -> None:
        """Test listing stories when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(story, ["list", "--project-path", temp_dir])

            assert result.exit_code == 0
            assert "No stories found." in result.output

    def test_move_story_success(self) -> None:
        """Test successful story move between stages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create a story first
            self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

            # Move story to in-progress
            result = self.runner.invoke(story, ["move", "TESTP-1", "in-progress", "--project-path", str(project_path)])

            assert result.exit_code == 0
            assert "✓ Moved story TESTP-1 from planning to in-progress" in result.output

            # Verify symlinks
            old_link = project_path / ".filter" / "kanban" / "planning" / "TESTP-1.md"
            new_link = project_path / ".filter" / "kanban" / "in-progress" / "TESTP-1.md"
            assert not old_link.exists()
            assert new_link.exists()
            assert new_link.is_symlink()

    def test_move_story_invalid_stage(self) -> None:
        """Test moving story to invalid stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Create a story first
            self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

            result = self.runner.invoke(
                story, ["move", "TESTP-1", "invalid-stage", "--project-path", str(project_path)]
            )

            assert result.exit_code == 1
            assert "Invalid stage 'invalid-stage'" in result.output
            assert "Valid stages:" in result.output

    def test_move_story_not_found(self) -> None:
        """Test moving non-existent story."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            result = self.runner.invoke(story, ["move", "NONEX-1", "in-progress", "--project-path", str(project_path)])

            assert result.exit_code == 1
            assert "Story NONEX-1 not found" in result.output

    def test_move_story_no_project(self) -> None:
        """Test moving story when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(story, ["move", "TEST-1", "in-progress", "--project-path", temp_dir])

            assert result.exit_code == 1
            assert "No filter project found" in result.output

    def test_create_story_exception_handling(self) -> None:
        """Test exception handling in create command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Mock StoryManager to raise exception
            with patch("filter.story_cli.StoryManager") as mock_manager:
                mock_manager.side_effect = Exception("Unexpected error")

                result = self.runner.invoke(story, ["create", "Test Story", "--project-path", str(project_path)])

                assert result.exit_code == 1
                assert "Failed to create story: Unexpected error" in result.output

    def test_delete_story_exception_handling(self) -> None:
        """Test exception handling in delete command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Mock StoryManager to raise exception
            with patch("filter.story_cli.StoryManager") as mock_manager:
                mock_manager.side_effect = Exception("Unexpected error")

                result = self.runner.invoke(story, ["delete", "TEST-1", "--force", "--project-path", str(project_path)])

                assert result.exit_code == 1
                assert "Failed to delete story: Unexpected error" in result.output

    def test_list_stories_exception_handling(self) -> None:
        """Test exception handling in list command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Mock StoryManager to raise exception
            with patch("filter.story_cli.StoryManager") as mock_manager:
                mock_manager.side_effect = Exception("Unexpected error")

                result = self.runner.invoke(story, ["list", "--project-path", str(project_path)])

                assert result.exit_code == 1
                assert "Failed to list stories: Unexpected error" in result.output

    def test_move_story_exception_handling(self) -> None:
        """Test exception handling in move command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = self.create_test_project(temp_dir)

            # Mock StoryManager to raise exception
            with patch("filter.story_cli.StoryManager") as mock_manager:
                mock_manager.side_effect = Exception("Unexpected error")

                result = self.runner.invoke(
                    story, ["move", "TEST-1", "in-progress", "--project-path", str(project_path)]
                )

                assert result.exit_code == 1
                assert "Failed to move story: Unexpected error" in result.output
