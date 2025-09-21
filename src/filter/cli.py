import click

from .project_cli import project
from .story_cli import story
from .tools import check_github_cli, gh_clone_repo


@click.group()  # type: ignore[misc]
def cli() -> None:
    """Filter CLI tool."""


@cli.command()  # type: ignore[misc]
@click.argument("url")  # type: ignore[misc]
@click.argument("dest", default=".")  # type: ignore[misc]
def clone(url: str, dest: str) -> None:
    """Clone a repository."""
    is_successful, message = gh_clone_repo(url, dest)
    if is_successful:
        click.echo(message)
    else:
        click.echo(message)
        return


@cli.command()  # type: ignore[misc]
def status() -> None:
    """Check the status of the tools filter uses."""
    is_installed, message = check_github_cli()
    if is_installed:
        click.echo(message)
    else:
        click.echo(message)
        return


# Register command groups
cli.add_command(project)
cli.add_command(story)


if __name__ == "__main__":
    cli()
