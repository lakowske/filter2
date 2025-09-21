import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages filter project structure and kanban workflow directories."""

    def __init__(self, project_path: Path) -> None:
        """Initialize project manager with the target project directory.

        Args:
            project_path: Path to the git repository or project directory
        """
        self.project_path = Path(project_path)
        self.filter_dir = self.project_path / ".filter"
        self.config_path = self.filter_dir / "config.yml"
        self.kanban_dir = self.filter_dir / "kanban"

        logger.info(f"Initialized ProjectManager - project_path: {self.project_path}")

    def create_project_structure(self) -> tuple[bool, str]:
        """Create the .filter directory structure with kanban workflow directories.

        Returns:
            tuple[bool, str]: Success status and descriptive message
        """
        logger.info("Creating filter project structure")

        if self.filter_dir.exists():
            logger.warning(f"Filter directory already exists - path: {self.filter_dir}")
            return False, f"Filter project already exists at {self.filter_dir}"

        try:
            # Create main .filter directory
            self.filter_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created filter directory - path: {self.filter_dir}")

            # Create kanban workflow directories
            kanban_stages = ["planning", "in-progress", "testing", "pr", "complete"]

            # Create kanban parent directory
            self.kanban_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created kanban directory - path: {self.kanban_dir}")

            # Create stories directory
            stories_dir = self.filter_dir / "stories"
            stories_dir.mkdir(exist_ok=True)
            logger.info(f"Created stories directory - path: {stories_dir}")

            # Create each kanban stage directory
            for stage in kanban_stages:
                stage_dir = self.kanban_dir / stage
                stage_dir.mkdir(exist_ok=True)
                logger.debug(f"Created kanban stage directory - stage: {stage}, path: {stage_dir}")

            # Create initial config.yml
            config_content = self._generate_config_content()
            self.config_path.write_text(config_content, encoding="utf-8")
            logger.info(f"Created project config - path: {self.config_path}")

            # Create initial README
            readme_content = self._generate_readme_content()
            readme_path = self.filter_dir / "README.md"
            readme_path.write_text(readme_content)
            logger.info(f"Created project README - path: {readme_path}")

            logger.info("Successfully created complete filter project structure")
            return True, f"Filter project created successfully at {self.filter_dir}"

        except OSError as e:
            logger.error(f"Failed to create project structure - error: {e}")
            return False, f"Failed to create project structure: {e}"

    def delete_project_structure(self, force: bool = False) -> tuple[bool, str]:
        """Delete the .filter directory and all its contents.

        Args:
            force: If True, delete without confirmation checks

        Returns:
            tuple[bool, str]: Success status and descriptive message
        """
        logger.info(f"Deleting filter project structure - force: {force}")

        if not self.filter_dir.exists():
            logger.warning(f"Filter directory does not exist - path: {self.filter_dir}")
            return False, f"No filter project found at {self.filter_dir}"

        if not force:
            # Check if there are active stories
            stories_dir = self.filter_dir / "stories"
            if stories_dir.exists() and any(stories_dir.iterdir()):
                story_count = len(list(stories_dir.iterdir()))
                logger.warning(f"Active stories found - count: {story_count}")
                return False, f"Project contains {story_count} stories. Use --force to delete anyway."

        try:
            shutil.rmtree(self.filter_dir)
            logger.info(f"Successfully deleted filter project - path: {self.filter_dir}")
            return True, f"Filter project deleted successfully from {self.project_path}"

        except OSError as e:
            logger.error(f"Failed to delete project structure - error: {e}")
            return False, f"Failed to delete project structure: {e}"

    def project_exists(self) -> bool:
        """Check if a filter project already exists.

        Returns:
            bool: True if .filter directory exists and is valid
        """
        exists = self.filter_dir.exists() and self.filter_dir.is_dir()
        logger.debug(f"Project exists check - path: {self.filter_dir}, exists: {exists}")
        return exists

    def get_project_info(self) -> Optional[dict[str, Any]]:
        """Get information about the current filter project.

        Returns:
            dict with project information or None if no project exists
        """
        if not self.project_exists():
            return None

        try:
            stories_dir = self.filter_dir / "stories"
            story_count = len(list(stories_dir.iterdir())) if stories_dir.exists() else 0

            # Count stories in each kanban stage
            stage_counts = {}
            if self.kanban_dir.exists():
                for stage_dir in self.kanban_dir.iterdir():
                    if stage_dir.is_dir():
                        stage_counts[stage_dir.name] = len(list(stage_dir.iterdir()))

            project_info = {
                "project_path": str(self.project_path),
                "filter_path": str(self.filter_dir),
                "total_stories": story_count,
                "stage_counts": stage_counts,
                "created_at": self.filter_dir.stat().st_ctime,
            }

            logger.debug(f"Retrieved project info - info: {project_info}")
            return project_info

        except OSError as e:
            logger.error(f"Failed to get project info - error: {e}")
            return None

    def _generate_prefix(self, project_name: str) -> str:
        """Generate a story prefix from project name.

        Args:
            project_name: Name of the project

        Returns:
            str: Generated prefix (e.g., "FILTE" for "filter")
        """
        # Remove common suffixes and clean the name
        clean_name = re.sub(r"[-_\d]+$", "", project_name.lower())

        # Take first 5 characters, or pad if shorter
        prefix = clean_name[:5].upper() if len(clean_name) >= 5 else clean_name.upper().ljust(5, "X")

        logger.debug(f"Generated prefix - project_name: {project_name}, prefix: {prefix}")
        return prefix

    def _generate_config_content(self) -> str:
        """Generate initial config.yml content for the filter project.

        Returns:
            str: YAML configuration content
        """
        config = {
            "project_name": self.project_path.name,
            "prefix": self._generate_prefix(self.project_path.name),
            "last_story_number": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "kanban_stages": ["planning", "in-progress", "testing", "pr", "complete"],
        }

        return str(yaml.safe_dump(config, default_flow_style=False, sort_keys=False))

    def _generate_readme_content(self) -> str:
        """Generate README content for the filter project.

        Returns:
            str: README content in markdown format
        """
        return """# Filter Project

This is a Filter-managed project with LLM-powered kanban board functionality.

## Directory Structure

- `stories/` - Contains all story markdown files
- `kanban/` - Kanban workflow directories with symbolic links to stories
  - `planning/` - Stories in planning phase
  - `in-progress/` - Stories currently being worked on
  - `testing/` - Stories in testing phase
  - `pr/` - Stories in pull request review
  - `complete/` - Completed stories

## Usage

Use the `filter` CLI tool to manage stories and workflows:

```bash
# Create a new story
filter story create "Story title"

# Move story to different stage
filter story move <story-id> <stage>

# List stories by stage
filter story list --stage in-progress
```

For more information, see the Filter documentation.
"""
