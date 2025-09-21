"""Project CLI commands for filter.

This module contains all CLI commands related to project management.
"""

from pathlib import Path

import click

from .projects import ProjectManager


@click.group()  # type: ignore[misc]
def project() -> None:
    """Manage filter projects with kanban workflow directories."""


@project.command()  # type: ignore[misc]
@click.argument("path", default=".")  # type: ignore[misc]
def create(path: str) -> None:
    """Create a new filter project structure.

    Creates a .filter directory with kanban workflow directories:
    - stories/ for markdown story files
    - kanban/ with planning, in-progress, testing, pr, complete stages
    """
    project_path = Path(path).resolve()
    manager = ProjectManager(project_path)

    is_successful, message = manager.create_project_structure()
    click.echo(message)

    if not is_successful:
        raise click.ClickException(message)


@project.command()  # type: ignore[misc]
@click.argument("path", default=".")  # type: ignore[misc]
@click.option("--force", is_flag=True, help="Delete project even if it contains stories")  # type: ignore[misc]
def delete(path: str, force: bool) -> None:
    """Delete a filter project structure.

    Removes the .filter directory and all its contents.
    Use --force to delete projects that contain stories.
    """
    project_path = Path(path).resolve()
    manager = ProjectManager(project_path)

    if not manager.project_exists():
        click.echo(f"No filter project found at {project_path}")
        return

    # Show project info before deletion
    project_info = manager.get_project_info()
    if project_info and project_info["total_stories"] > 0:
        click.echo(f"Project contains {project_info['total_stories']} stories")
        if not force:
            click.echo("Use --force to delete anyway")
            return

    is_successful, message = manager.delete_project_structure(force=force)
    click.echo(message)

    if not is_successful:
        raise click.ClickException(message)


@project.command()  # type: ignore[misc]
@click.argument("path", default=".")  # type: ignore[misc]
def info(path: str) -> None:
    """Show information about a filter project."""
    project_path = Path(path).resolve()
    manager = ProjectManager(project_path)

    project_info = manager.get_project_info()
    if not project_info:
        click.echo(f"No filter project found at {project_path}")
        return

    click.echo(f"Filter Project: {project_info['project_path']}")
    click.echo(f"Filter Directory: {project_info['filter_path']}")
    click.echo(f"Total Stories: {project_info['total_stories']}")

    if project_info["stage_counts"]:
        click.echo("\nStories by Stage:")
        for stage, count in project_info["stage_counts"].items():
            click.echo(f"  {stage}: {count}")
