"""Tests for the projects module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from filter.projects import ProjectManager


class TestProjectManager:
    """Tests for ProjectManager class."""

    def test_init(self) -> None:
        """Test ProjectManager initialization."""
        project_path = Path("/test/project")
        manager = ProjectManager(project_path)

        assert manager.project_path == project_path
        assert manager.filter_dir == project_path / ".filter"
        assert manager.kanban_dir == project_path / ".filter" / "kanban"

    def test_create_project_structure_success(self) -> None:
        """Test successful project structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            is_successful, message = manager.create_project_structure()

            assert is_successful is True
            assert "Filter project created successfully" in message

            # Verify directory structure
            assert manager.filter_dir.exists()
            assert manager.kanban_dir.exists()
            assert (manager.filter_dir / "stories").exists()

            # Verify kanban stages
            expected_stages = ["planning", "in-progress", "testing", "pr", "complete"]
            for stage in expected_stages:
                assert (manager.kanban_dir / stage).exists()

            # Verify README
            readme_path = manager.filter_dir / "README.md"
            assert readme_path.exists()
            readme_content = readme_path.read_text()
            assert "Filter Project" in readme_content

    def test_create_project_structure_already_exists(self) -> None:
        """Test creating project when .filter directory already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create .filter directory first
            manager.filter_dir.mkdir()

            is_successful, message = manager.create_project_structure()

            assert is_successful is False
            assert "Filter project already exists" in message

    @patch("filter.projects.shutil.rmtree")
    def test_create_project_structure_permission_error(self, mock_rmtree) -> None:  # type: ignore[no-untyped-def]
        """Test project creation with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Mock mkdir to raise OSError
            with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
                is_successful, message = manager.create_project_structure()

                assert is_successful is False
                assert "Failed to create project structure" in message

    def test_delete_project_structure_success(self) -> None:
        """Test successful project deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project first
            manager.create_project_structure()
            assert manager.filter_dir.exists()

            # Delete project
            is_successful, message = manager.delete_project_structure(force=True)

            assert is_successful is True
            assert "Filter project deleted successfully" in message
            assert not manager.filter_dir.exists()

    def test_delete_project_structure_not_exists(self) -> None:
        """Test deleting project when .filter directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            is_successful, message = manager.delete_project_structure()

            assert is_successful is False
            assert "No filter project found" in message

    def test_delete_project_structure_with_stories_no_force(self) -> None:
        """Test deleting project with stories without force flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project and add a story file
            manager.create_project_structure()
            stories_dir = manager.filter_dir / "stories"
            (stories_dir / "story1.md").write_text("# Story 1")

            is_successful, message = manager.delete_project_structure(force=False)

            assert is_successful is False
            assert "contains 1 stories" in message
            assert "Use --force" in message
            assert manager.filter_dir.exists()

    def test_delete_project_structure_with_stories_force(self) -> None:
        """Test deleting project with stories using force flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project and add story files
            manager.create_project_structure()
            stories_dir = manager.filter_dir / "stories"
            (stories_dir / "story1.md").write_text("# Story 1")
            (stories_dir / "story2.md").write_text("# Story 2")

            is_successful, message = manager.delete_project_structure(force=True)

            assert is_successful is True
            assert "Filter project deleted successfully" in message
            assert not manager.filter_dir.exists()

    def test_delete_project_structure_permission_error(self) -> None:
        """Test project deletion with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project first
            manager.create_project_structure()

            # Mock rmtree to raise OSError only for our specific call
            with patch("filter.projects.shutil.rmtree", side_effect=OSError("Permission denied")):
                is_successful, message = manager.delete_project_structure(force=True)

                assert is_successful is False
                assert "Failed to delete project structure" in message

    def test_project_exists_true(self) -> None:
        """Test project_exists when project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project
            manager.create_project_structure()

            assert manager.project_exists() is True

    def test_project_exists_false(self) -> None:
        """Test project_exists when project doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            assert manager.project_exists() is False

    def test_get_project_info_success(self) -> None:
        """Test getting project info for existing project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            # Create project and add some test data
            manager.create_project_structure()
            stories_dir = manager.filter_dir / "stories"
            (stories_dir / "story1.md").write_text("# Story 1")
            (stories_dir / "story2.md").write_text("# Story 2")

            # Add story to kanban stage
            planning_dir = manager.kanban_dir / "planning"
            (planning_dir / "story1.md").write_text("# Story 1")

            project_info = manager.get_project_info()

            assert project_info is not None
            assert project_info["project_path"] == str(project_path)
            assert project_info["filter_path"] == str(manager.filter_dir)
            assert project_info["total_stories"] == 2
            assert "planning" in project_info["stage_counts"]
            assert project_info["stage_counts"]["planning"] == 1
            assert "created_at" in project_info

    def test_get_project_info_no_project(self) -> None:
        """Test getting project info when no project exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            project_info = manager.get_project_info()

            assert project_info is None

    def test_generate_readme_content(self) -> None:
        """Test README content generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            manager = ProjectManager(project_path)

            readme_content = manager._generate_readme_content()

            assert "# Filter Project" in readme_content
            assert "stories/" in readme_content
            assert "kanban/" in readme_content
            assert "planning/" in readme_content
            assert "filter" in readme_content.lower()
