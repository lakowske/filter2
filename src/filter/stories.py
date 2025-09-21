import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class StoryManager:
    """Manages story creation, deletion, and workflow operations."""

    def __init__(self, project_path: Path) -> None:
        """Initialize story manager with the project directory.

        Args:
            project_path: Path to the project directory containing .filter
        """
        self.project_path = Path(project_path)
        self.filter_dir = self.project_path / ".filter"
        self.config_path = self.filter_dir / "config.yml"
        self.stories_dir = self.filter_dir / "stories"
        self.kanban_dir = self.filter_dir / "kanban"

        logger.info(f"Initialized StoryManager - project_path: {self.project_path}")

    def _ensure_filter_structure(self) -> tuple[bool, str]:
        """Ensure the .filter directory structure exists.

        Returns:
            tuple[bool, str]: Success status and message
        """
        if not self.filter_dir.exists():
            return False, f"No filter project found at {self.project_path}. Run 'filter project create' first."

        # Verify essential directories exist
        required_dirs = [self.stories_dir, self.kanban_dir]
        for dir_path in required_dirs:
            if not dir_path.exists():
                return False, f"Missing required directory: {dir_path}. Project structure may be corrupted."

        return True, "Filter structure verified"

    def _load_config(self) -> dict[str, Any]:
        """Load project configuration from config.yml.

        Returns:
            dict: Project configuration
        """
        default_config = {
            "project_name": self.project_path.name,
            "prefix": self._generate_prefix(self.project_path.name),
            "last_story_number": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "kanban_stages": ["planning", "in-progress", "testing", "pr", "complete"],
        }

        if not self.config_path.exists():
            logger.info(f"Creating new config file - path: {self.config_path}")
            self._save_config(default_config)
            return default_config

        try:
            with self.config_path.open(encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config - config: {config}")

                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        logger.debug(f"Added missing config key - key: {key}, value: {value}")

                return config
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Failed to load config, using defaults - error: {e}")
            return default_config

    def _save_config(self, config: dict[str, Any]) -> None:
        """Save project configuration to config.yml.

        Args:
            config: Configuration dictionary to save
        """
        try:
            with self.config_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
                logger.debug(f"Saved config - path: {self.config_path}")
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Failed to save config - error: {e}")
            raise

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

    def _get_next_story_number(self) -> tuple[int, str]:
        """Get the next story number and update configuration.

        Returns:
            tuple[int, str]: Next story number and full story ID
        """
        config = self._load_config()
        next_number = config["last_story_number"] + 1
        story_id = f"{config['prefix']}-{next_number}"

        # Update and save config
        config["last_story_number"] = next_number
        self._save_config(config)

        logger.info(f"Generated next story ID - story_id: {story_id}")
        return next_number, story_id

    def create_story(self, title: str, description: str = "", stage: str = "planning") -> tuple[bool, str]:
        """Create a new story with auto-generated ID.

        Args:
            title: Story title
            description: Optional story description
            stage: Initial kanban stage (default: planning)

        Returns:
            tuple[bool, str]: Success status and message with story ID
        """
        logger.info(f"Creating new story - title: {title}, stage: {stage}")

        # Ensure filter structure exists
        is_valid, message = self._ensure_filter_structure()
        if not is_valid:
            return False, message

        # Validate stage
        config = self._load_config()
        if stage not in config["kanban_stages"]:
            return False, f"Invalid stage '{stage}'. Valid stages: {', '.join(config['kanban_stages'])}"

        try:
            # Generate story ID and create story file
            _, story_id = self._get_next_story_number()
            story_file = self.stories_dir / f"{story_id}.md"

            # Create story content
            story_content = self._generate_story_content(story_id, title, description)
            story_file.write_text(story_content, encoding="utf-8")
            logger.info(f"Created story file - path: {story_file}")

            # Create symlink in kanban stage
            stage_dir = self.kanban_dir / stage
            stage_link = stage_dir / f"{story_id}.md"
            stage_link.symlink_to(f"../../stories/{story_id}.md")
            logger.info(f"Created kanban symlink - stage: {stage}, link: {stage_link}")

            return True, f"Created story {story_id}: {title}"

        except (OSError, FileExistsError) as e:
            logger.error(f"Failed to create story - error: {e}")
            return False, f"Failed to create story: {e}"

    def delete_story(self, story_id: str) -> tuple[bool, str]:
        """Delete a story and its kanban symlinks.

        Args:
            story_id: Story ID to delete (e.g., "FILTE-1")

        Returns:
            tuple[bool, str]: Success status and message
        """
        logger.info(f"Deleting story - story_id: {story_id}")

        # Ensure filter structure exists
        is_valid, message = self._ensure_filter_structure()
        if not is_valid:
            return False, message

        try:
            # Check if story exists
            story_file = self.stories_dir / f"{story_id}.md"
            if not story_file.exists():
                return False, f"Story {story_id} not found"

            # Remove symlinks from all kanban stages
            config = self._load_config()
            removed_stages = []
            for stage in config["kanban_stages"]:
                stage_link = self.kanban_dir / stage / f"{story_id}.md"
                if stage_link.exists():
                    stage_link.unlink()
                    removed_stages.append(stage)
                    logger.debug(f"Removed kanban symlink - stage: {stage}")

            # Remove the story file
            story_file.unlink()
            logger.info(f"Deleted story file - path: {story_file}")

            stage_info = f" (was in {', '.join(removed_stages)})" if removed_stages else ""
            return True, f"Deleted story {story_id}{stage_info}"

        except OSError as e:
            logger.error(f"Failed to delete story - error: {e}")
            return False, f"Failed to delete story: {e}"

    def list_stories(self, stage: Optional[str] = None) -> list[dict[str, str]]:
        """List stories, optionally filtered by stage.

        Args:
            stage: Optional stage to filter by

        Returns:
            list: List of story dictionaries with id, title, and stage
        """
        logger.info(f"Listing stories - stage_filter: {stage}")

        # Ensure filter structure exists
        is_valid, message = self._ensure_filter_structure()
        if not is_valid:
            logger.warning(f"Cannot list stories - {message}")
            return []

        try:
            stories = []
            config = self._load_config()

            # If stage specified, only check that stage
            stages_to_check = [stage] if stage else config["kanban_stages"]

            for check_stage in stages_to_check:
                stage_dir = self.kanban_dir / check_stage
                if not stage_dir.exists():
                    continue

                for link_file in stage_dir.glob("*.md"):
                    if link_file.is_symlink():
                        story_id = link_file.stem
                        story_file = self.stories_dir / f"{story_id}.md"

                        if story_file.exists():
                            title = self._extract_title_from_story(story_file)
                            stories.append({"id": story_id, "title": title, "stage": check_stage})

            logger.debug(f"Found {len(stories)} stories")
            return stories

        except OSError as e:
            logger.error(f"Failed to list stories - error: {e}")
            return []

    def _generate_story_content(self, story_id: str, title: str, description: str) -> str:
        """Generate markdown content for a story.

        Args:
            story_id: Story identifier
            title: Story title
            description: Story description

        Returns:
            str: Formatted markdown content
        """
        return f"""# {story_id}: {title}

**Created:** {datetime.now(timezone.utc).isoformat()}
**Status:** Planning

## Description

{description or 'No description provided.'}

## Acceptance Criteria

- [ ] Define acceptance criteria for this story

## Notes

<!-- Add any additional notes or updates here -->

## Related Issues

<!-- Link to any related issues or stories -->
"""

    def _extract_title_from_story(self, story_file: Path) -> str:
        """Extract title from story markdown file.

        Args:
            story_file: Path to story file

        Returns:
            str: Extracted title or filename if extraction fails
        """
        try:
            content = story_file.read_text(encoding="utf-8")
            # Look for the first heading
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    # Extract title after story ID
                    title_part = line[2:].strip()
                    if ": " in title_part:
                        return title_part.split(": ", 1)[1]
                    return title_part
            return story_file.stem
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to extract title from {story_file} - error: {e}")
            return story_file.stem

    def get_project_config(self) -> Optional[dict[str, Any]]:
        """Get the current project configuration.

        Returns:
            dict: Project configuration or None if no project exists
        """
        is_valid, _ = self._ensure_filter_structure()
        if not is_valid:
            return None

        return self._load_config()
