import click

from src.filter.tools import check_github_cli, gh_clone_repo


@click.group()
def cli():
    """Filter CLI tool."""


@cli.command()
@click.argument("url")
@click.argument("dest", default=".")
def clone(url, dest):
    """Clone a repository."""
    is_successful, message = gh_clone_repo(url, dest)
    if is_successful:
        click.echo(message)
    else:
        click.echo(message)
        return


@cli.command()
def status():
    """Check the status of the tools filter uses."""
    is_installed, message = check_github_cli()
    if is_installed:
        click.echo(message)
    else:
        click.echo(message)
        return


if __name__ == "__main__":
    cli()
