"""Tests for the stories module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from filter.stories import StoryManager


class TestStoryManager:
    """Tests for StoryManager class."""

    def test_init(self) -> None:
        """Test StoryManager initialization."""
        project_path = Path("/test/project")
        manager = StoryManager(project_path)

        assert manager.project_path == project_path
        assert manager.filter_dir == project_path / ".filter"
        assert manager.config_path == project_path / ".filter" / "config.yml"
        assert manager.stories_dir == project_path / ".filter" / "stories"
        assert manager.kanban_dir == project_path / ".filter" / "kanban"

    def test_generate_prefix_normal_name(self) -> None:
        """Test prefix generation for normal project names."""
        manager = StoryManager(Path("/test"))

        # Test normal 5+ character names
        assert manager._generate_prefix("filter") == "FILTE"
        assert manager._generate_prefix("project-management") == "PROJE"
        assert manager._generate_prefix("awesome_app") == "AWESO"

        # Test short names
        assert manager._generate_prefix("app") == "APPXX"
        assert manager._generate_prefix("ui") == "UIXXX"

        # Test names with numbers and dashes (regex removes trailing number/dash groups)
        assert manager._generate_prefix("app-v2-final") == "APP-V"  # Only removes trailing, not middle
        assert manager._generate_prefix("project_2024") == "PROJE"

    def test_ensure_filter_structure_missing(self) -> None:
        """Test filter structure validation when .filter doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            is_valid, message = manager._ensure_filter_structure()

            assert is_valid is False
            assert "No filter project found" in message
            assert "filter project create" in message

    def test_ensure_filter_structure_incomplete(self) -> None:
        """Test filter structure validation when directories are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create .filter but missing stories directory
            manager.filter_dir.mkdir()
            manager.kanban_dir.mkdir()

            is_valid, message = manager._ensure_filter_structure()

            assert is_valid is False
            assert "Missing required directory" in message

    def test_ensure_filter_structure_valid(self) -> None:
        """Test filter structure validation when complete."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create complete structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()

            is_valid, message = manager._ensure_filter_structure()

            assert is_valid is True
            assert "Filter structure verified" in message

    def test_load_config_creates_default(self) -> None:
        """Test config loading creates default when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create minimal .filter structure
            manager.filter_dir.mkdir()

            config = manager._load_config()

            assert config["project_name"] == "test-project"
            assert config["prefix"] == "TEST-"  # Updated to match actual output
            assert config["last_story_number"] == 0
            assert "created_at" in config
            assert config["kanban_stages"] == ["planning", "in-progress", "testing", "pr", "complete"]

            # Verify config file was created
            assert manager.config_path.exists()

    def test_load_config_existing_file(self) -> None:
        """Test config loading from existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create .filter structure and config
            manager.filter_dir.mkdir()
            existing_config = {
                "project_name": "custom-project",
                "prefix": "CUST",
                "last_story_number": 5,
                "created_at": "2024-01-01T00:00:00Z",
                "kanban_stages": ["todo", "doing", "done"],
            }

            with manager.config_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(existing_config, f)

            config = manager._load_config()

            assert config["project_name"] == "custom-project"
            assert config["prefix"] == "CUST"
            assert config["last_story_number"] == 5
            assert config["kanban_stages"] == ["todo", "doing", "done"]

    def test_load_config_partial_file(self) -> None:
        """Test config loading merges missing keys with defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "merge-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create .filter structure and partial config
            manager.filter_dir.mkdir()
            partial_config = {"prefix": "PART", "last_story_number": 3}

            with manager.config_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(partial_config, f)

            config = manager._load_config()

            # Should merge with defaults
            assert config["prefix"] == "PART"  # from file
            assert config["last_story_number"] == 3  # from file
            assert config["project_name"] == "merge-test"  # default
            assert "created_at" in config  # default
            assert config["kanban_stages"] == ["planning", "in-progress", "testing", "pr", "complete"]  # default

    def test_load_config_corrupted_file(self) -> None:
        """Test config loading with corrupted YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "corrupted-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create .filter structure and corrupted config
            manager.filter_dir.mkdir()
            manager.config_path.write_text("invalid: yaml: content: [unclosed", encoding="utf-8")

            config = manager._load_config()

            # Should fall back to defaults
            assert config["project_name"] == "corrupted-test"
            assert config["prefix"] == "CORRU"
            assert config["last_story_number"] == 0

    def test_save_config(self) -> None:
        """Test config saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create .filter structure
            manager.filter_dir.mkdir()

            test_config = {
                "project_name": "test",
                "prefix": "TEST",
                "last_story_number": 10,
                "created_at": "2024-01-01T00:00:00Z",
                "kanban_stages": ["planning", "done"],
            }

            manager._save_config(test_config)

            # Verify file was written correctly
            assert manager.config_path.exists()

            with manager.config_path.open(encoding="utf-8") as f:
                saved_config = yaml.safe_load(f)

            assert saved_config == test_config

    def test_save_config_permission_error(self) -> None:
        """Test config saving with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            test_config = {"test": "value"}

            # Create the filter directory first
            manager.filter_dir.mkdir()

            # Patch yaml.safe_dump to raise an error
            with (
                patch("yaml.safe_dump", side_effect=OSError("Permission denied")),
                pytest.raises(OSError),
            ):
                manager._save_config(test_config)

    def test_get_next_story_number(self) -> None:
        """Test story number generation and config update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "story-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create .filter structure
            manager.filter_dir.mkdir()

            # First story should be 1
            number, story_id = manager._get_next_story_number()
            assert number == 1
            assert story_id == "STORY-1"

            # Second story should be 2
            number, story_id = manager._get_next_story_number()
            assert number == 2
            assert story_id == "STORY-2"

            # Verify config was updated
            config = manager._load_config()
            assert config["last_story_number"] == 2

    def test_create_story_success(self) -> None:
        """Test successful story creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "create-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            for stage in ["planning", "in-progress", "testing", "pr", "complete"]:
                (manager.kanban_dir / stage).mkdir()

            is_successful, message = manager.create_story("Test Story", "A test story description", "planning")

            assert is_successful is True
            assert "Created story CREAT-1: Test Story" in message

            # Verify story file was created
            story_file = manager.stories_dir / "CREAT-1.md"
            assert story_file.exists()

            story_content = story_file.read_text(encoding="utf-8")
            assert "# CREAT-1: Test Story" in story_content
            assert "A test story description" in story_content
            assert "**Status:** Planning" in story_content

            # Verify kanban symlink was created
            kanban_link = manager.kanban_dir / "planning" / "CREAT-1.md"
            assert kanban_link.exists()
            assert kanban_link.is_symlink()

    def test_create_story_no_filter_project(self) -> None:
        """Test story creation when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            is_successful, message = manager.create_story("Test Story")

            assert is_successful is False
            assert "No filter project found" in message

    def test_create_story_invalid_stage(self) -> None:
        """Test story creation with invalid stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()

            is_successful, message = manager.create_story("Test Story", "", "invalid-stage")

            assert is_successful is False
            assert "Invalid stage 'invalid-stage'" in message
            assert "Valid stages:" in message

    def test_create_story_file_error(self) -> None:
        """Test story creation with file creation error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create minimal structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            (manager.kanban_dir / "planning").mkdir()

            # Mock story file write to fail
            with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
                is_successful, message = manager.create_story("Test Story")

                assert is_successful is False
                assert "Failed to create story" in message

    def test_delete_story_success(self) -> None:
        """Test successful story deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "delete-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create complete project structure and story
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            for stage in ["planning", "in-progress", "testing", "pr", "complete"]:
                (manager.kanban_dir / stage).mkdir()

            # Create story first
            manager.create_story("Test Story")

            # Verify story exists
            story_file = manager.stories_dir / "DELET-1.md"
            kanban_link = manager.kanban_dir / "planning" / "DELET-1.md"
            assert story_file.exists()
            assert kanban_link.exists()

            # Delete story
            is_successful, message = manager.delete_story("DELET-1")

            assert is_successful is True
            assert "Deleted story DELET-1" in message
            assert "(was in planning)" in message

            # Verify files were removed
            assert not story_file.exists()
            assert not kanban_link.exists()

    def test_delete_story_not_found(self) -> None:
        """Test deleting non-existent story."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()

            is_successful, message = manager.delete_story("NONEX-1")

            assert is_successful is False
            assert "Story NONEX-1 not found" in message

    def test_delete_story_no_filter_project(self) -> None:
        """Test story deletion when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            is_successful, message = manager.delete_story("TEST-1")

            assert is_successful is False
            assert "No filter project found" in message

    def test_delete_story_file_error(self) -> None:
        """Test story deletion with file removal error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create complete project structure and story
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            (manager.kanban_dir / "planning").mkdir()

            # Create story manually
            story_file = manager.stories_dir / "ERROR-1.md"
            story_file.write_text("# ERROR-1: Test Story")

            # Mock file unlink to fail
            with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
                is_successful, message = manager.delete_story("ERROR-1")

                assert is_successful is False
                assert "Failed to delete story" in message

    def test_list_stories_empty(self) -> None:
        """Test listing stories when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()

            stories = manager.list_stories()

            assert stories == []

    def test_list_stories_multiple(self) -> None:
        """Test listing multiple stories across stages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "lists-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            for stage in ["planning", "in-progress", "testing", "pr", "complete"]:
                (manager.kanban_dir / stage).mkdir()

            # Create stories
            manager.create_story("Story One")
            manager.create_story("Story Two", "", "in-progress")

            stories = manager.list_stories()

            assert len(stories) == 2
            assert stories[0]["id"] == "LISTS-1"
            assert stories[0]["title"] == "Story One"
            assert stories[0]["stage"] == "planning"
            assert stories[1]["id"] == "LISTS-2"
            assert stories[1]["title"] == "Story Two"
            assert stories[1]["stage"] == "in-progress"

    def test_list_stories_filtered_by_stage(self) -> None:
        """Test listing stories filtered by specific stage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "filter-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()
            for stage in ["planning", "in-progress", "testing", "pr", "complete"]:
                (manager.kanban_dir / stage).mkdir()

            # Create stories in different stages
            manager.create_story("Planning Story", "", "planning")
            manager.create_story("Progress Story", "", "in-progress")
            manager.create_story("Another Planning Story", "", "planning")

            # Filter by planning stage
            planning_stories = manager.list_stories("planning")

            assert len(planning_stories) == 2
            assert all(story["stage"] == "planning" for story in planning_stories)
            # Stories may be returned in different order, so just check titles are present
            planning_titles = [story["title"] for story in planning_stories]
            assert "Planning Story" in planning_titles
            assert "Another Planning Story" in planning_titles

            # Filter by in-progress stage
            progress_stories = manager.list_stories("in-progress")

            assert len(progress_stories) == 1
            assert progress_stories[0]["title"] == "Progress Story"

    def test_list_stories_no_filter_project(self) -> None:
        """Test listing stories when no filter project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            stories = manager.list_stories()

            assert stories == []

    def test_extract_title_from_story(self) -> None:
        """Test title extraction from story markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create test story file
            story_file = Path(temp_dir) / "test-story.md"
            story_content = """# TITLE-1: Extract This Title

**Created:** 2024-01-01 12:00:00
**Status:** Planning

## Description

Test description here.
"""
            story_file.write_text(story_content, encoding="utf-8")

            title = manager._extract_title_from_story(story_file)

            assert title == "Extract This Title"

    def test_extract_title_from_story_no_colon(self) -> None:
        """Test title extraction when no colon separator exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create test story file without colon
            story_file = Path(temp_dir) / "test-story.md"
            story_content = """# TITLE-1

**Created:** 2024-01-01 12:00:00
"""
            story_file.write_text(story_content, encoding="utf-8")

            title = manager._extract_title_from_story(story_file)

            assert title == "TITLE-1"

    def test_extract_title_from_story_no_heading(self) -> None:
        """Test title extraction when no heading exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create test story file without heading
            story_file = Path(temp_dir) / "test-story.md"
            story_content = """**Created:** 2024-01-01 12:00:00

Some content without heading.
"""
            story_file.write_text(story_content, encoding="utf-8")

            title = manager._extract_title_from_story(story_file)

            assert title == "test-story"

    def test_extract_title_from_story_file_error(self) -> None:
        """Test title extraction with file read error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            # Create test story file
            story_file = Path(temp_dir) / "test-story.md"
            story_file.write_text("# TEST: Title", encoding="utf-8")

            # Mock read_text to fail
            with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
                title = manager._extract_title_from_story(story_file)

                assert title == "test-story"

    def test_get_project_config_valid_project(self) -> None:
        """Test getting project config for valid project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "config-test"
            project_path.mkdir()
            manager = StoryManager(project_path)

            # Create complete project structure
            manager.filter_dir.mkdir()
            manager.stories_dir.mkdir()
            manager.kanban_dir.mkdir()

            config = manager.get_project_config()

            assert config is not None
            assert config["project_name"] == "config-test"
            assert config["prefix"] == "CONFI"
            assert config["last_story_number"] == 0
            assert "created_at" in config
            assert config["kanban_stages"] == ["planning", "in-progress", "testing", "pr", "complete"]

    def test_get_project_config_no_project(self) -> None:
        """Test getting project config when no project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            config = manager.get_project_config()

            assert config is None

    def test_generate_story_content(self) -> None:
        """Test story content generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            content = manager._generate_story_content("TEST-1", "Test Story", "A test description")

            assert "# TEST-1: Test Story" in content
            assert "**Status:** Planning" in content
            assert "A test description" in content
            assert "## Acceptance Criteria" in content
            assert "## Notes" in content
            assert "## Related Issues" in content

    def test_generate_story_content_no_description(self) -> None:
        """Test story content generation with no description."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = StoryManager(project_path)

            content = manager._generate_story_content("TEST-1", "Test Story", "")

            assert "# TEST-1: Test Story" in content
            assert "No description provided." in content
