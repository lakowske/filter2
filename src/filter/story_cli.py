import logging
from pathlib import Path

import click

from .stories import StoryManager

logger = logging.getLogger(__name__)


@click.group()  # type: ignore[misc]
def story() -> None:
    """Manage stories in the kanban workflow."""


@story.command()  # type: ignore[misc]
@click.argument("title")  # type: ignore[misc]
@click.option("--description", "-d", default="", help="Story description")  # type: ignore[misc]
@click.option("--stage", "-s", default="planning", help="Initial kanban stage")  # type: ignore[misc]
@click.option("--project-path", "-p", default=".", help="Path to the project directory")  # type: ignore[misc]
def create(title: str, description: str, stage: str, project_path: str) -> None:
    """Create a new story with auto-generated ID.

    Creates a story in the project's .filter directory with an auto-generated
    ID based on the project prefix (e.g., FILTE-1, FILTE-2).

    Args:
        title: Story title (required)
        description: Optional story description
        stage: Initial kanban stage (default: planning)
        project_path: Path to the project directory (default: current directory)
    """
    logger.info(f"Creating story - title: {title}, stage: {stage}, project_path: {project_path}")

    try:
        story_manager = StoryManager(Path(project_path))
        is_successful, message = story_manager.create_story(title, description, stage)

        if is_successful:
            click.echo(f"✓ {message}")
            logger.info(f"Story creation successful - message: {message}")
        else:
            click.echo(f"✗ {message}")
            logger.error(f"Story creation failed - message: {message}")
            raise click.ClickException(message)

    except Exception as e:
        logger.error(f"Unexpected error during story creation - error: {e}")
        error_msg = f"Failed to create story: {e}"
        raise click.ClickException(error_msg) from e


@story.command()  # type: ignore[misc]
@click.argument("story_id")  # type: ignore[misc]
@click.option("--project-path", "-p", default=".", help="Path to the project directory")  # type: ignore[misc]
@click.option("--force", "-f", is_flag=True, help="Force deletion without confirmation")  # type: ignore[misc]
def delete(story_id: str, project_path: str, force: bool) -> None:
    """Delete a story and its kanban symlinks.

    Removes the story file and cleans up all kanban stage symlinks.
    Use --force to skip confirmation prompt.

    Args:
        story_id: Story ID to delete (e.g., "FILTE-1")
        project_path: Path to the project directory (default: current directory)
        force: Force deletion without confirmation
    """
    logger.info(f"Deleting story - story_id: {story_id}, project_path: {project_path}, force: {force}")

    try:
        story_manager = StoryManager(Path(project_path))

        # Get confirmation unless force is used
        if not force and not click.confirm(f"Are you sure you want to delete story {story_id}?"):
            click.echo("Deletion cancelled.")
            logger.info(f"Story deletion cancelled by user - story_id: {story_id}")
            return

        is_successful, message = story_manager.delete_story(story_id)

        if is_successful:
            click.echo(f"✓ {message}")
            logger.info(f"Story deletion successful - message: {message}")
        else:
            click.echo(f"✗ {message}")
            logger.error(f"Story deletion failed - message: {message}")
            raise click.ClickException(message)

    except Exception as e:
        logger.error(f"Unexpected error during story deletion - error: {e}")
        error_msg = f"Failed to delete story: {e}"
        raise click.ClickException(error_msg) from e


@story.command()  # type: ignore[misc]
@click.option("--stage", "-s", help="Filter by kanban stage")  # type: ignore[misc]
@click.option("--project-path", "-p", default=".", help="Path to the project directory")  # type: ignore[misc]
def list(stage: str, project_path: str) -> None:  # noqa: A001
    """List stories, optionally filtered by stage.

    Shows all stories in the project or filters by specific kanban stage.

    Args:
        stage: Optional stage to filter by (planning, in-progress, testing, pr, complete)
        project_path: Path to the project directory (default: current directory)
    """
    logger.info(f"Listing stories - stage_filter: {stage}, project_path: {project_path}")

    try:
        story_manager = StoryManager(Path(project_path))
        stories = story_manager.list_stories(stage)

        if not stories:
            stage_msg = f" in stage '{stage}'" if stage else ""
            click.echo(f"No stories found{stage_msg}.")
            logger.info(f"No stories found - stage_filter: {stage}")
            return

        # Display header
        stage_header = f" (stage: {stage})" if stage else ""
        click.echo(f"\nStories{stage_header}:")
        click.echo("─" * 50)

        # Display stories
        for story in stories:
            stage_display = f" [{story['stage']}]" if not stage else ""
            click.echo(f"{story['id']}: {story['title']}{stage_display}")

        click.echo(f"\nTotal: {len(stories)} stories")
        logger.info(f"Listed {len(stories)} stories - stage_filter: {stage}")

    except Exception as e:
        logger.error(f"Unexpected error during story listing - error: {e}")
        error_msg = f"Failed to list stories: {e}"
        raise click.ClickException(error_msg) from e


@story.command()  # type: ignore[misc]
@click.argument("story_id")  # type: ignore[misc]
@click.argument("target_stage")  # type: ignore[misc]
@click.option("--project-path", "-p", default=".", help="Path to the project directory")  # type: ignore[misc]
def move(story_id: str, target_stage: str, project_path: str) -> None:
    """Move a story to a different kanban stage.

    Updates the story's kanban symlink to the target stage.

    Args:
        story_id: Story ID to move (e.g., "FILTE-1")
        target_stage: Target kanban stage (planning, in-progress, testing, pr, complete)
        project_path: Path to the project directory (default: current directory)
    """
    logger.info(f"Moving story - story_id: {story_id}, target_stage: {target_stage}, project_path: {project_path}")

    try:
        story_manager = StoryManager(Path(project_path))

        # Get current config to validate stage
        config = story_manager.get_project_config()
        if not config:
            error_msg = "No filter project found. Run 'filter project create' first."
            raise click.ClickException(error_msg)

        if target_stage not in config["kanban_stages"]:
            valid_stages = ", ".join(config["kanban_stages"])
            error_msg = f"Invalid stage '{target_stage}'. Valid stages: {valid_stages}"
            raise click.ClickException(error_msg)

        # Check if story exists
        story_file = story_manager.stories_dir / f"{story_id}.md"
        if not story_file.exists():
            error_msg = f"Story {story_id} not found"
            raise click.ClickException(error_msg)

        # Remove from current stage(s)
        removed_from = []
        for stage in config["kanban_stages"]:
            stage_link = story_manager.kanban_dir / stage / f"{story_id}.md"
            if stage_link.exists():
                stage_link.unlink()
                removed_from.append(stage)
                logger.debug(f"Removed story from stage - story_id: {story_id}, stage: {stage}")

        # Add to target stage
        target_dir = story_manager.kanban_dir / target_stage
        target_link = target_dir / f"{story_id}.md"
        target_link.symlink_to(f"../../stories/{story_id}.md")

        from_msg = f" from {', '.join(removed_from)}" if removed_from else ""
        click.echo(f"✓ Moved story {story_id}{from_msg} to {target_stage}")
        logger.info(f"Story move successful - story_id: {story_id}, target_stage: {target_stage}")

    except Exception as e:
        logger.error(f"Unexpected error during story move - error: {e}")
        error_msg = f"Failed to move story: {e}"
        raise click.ClickException(error_msg) from e
