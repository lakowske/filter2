import logging
import subprocess

logger = logging.getLogger(__name__)


def check_github_cli() -> tuple[bool, str]:
    """Check if GitHub CLI (gh) is installed and accessible.

    Returns:
        tuple[bool, str]: A tuple containing (is_installed, message)
            - is_installed: True if gh is available, False otherwise
            - message: Status message describing the result
    """
    logger.info("Checking GitHub CLI installation status")

    try:
        result = subprocess.run(  # noqa: S603
            ["gh", "--version"],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
        )
        version_info = result.stdout.strip()
        logger.info(f"GitHub CLI found - version_info: {version_info}")
        return True, f"GitHub CLI (gh) is installed: {version_info}"
    except subprocess.CalledProcessError as e:
        logger.error(f"GitHub CLI check failed - return_code: {e.returncode}, stderr: {e.stderr}")
        return False, f"GitHub CLI command failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
    except FileNotFoundError:
        logger.warning("GitHub CLI not found in PATH")
        return False, "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"


def gh_clone_repo(repo_url: str, dest_dir: str) -> tuple[bool, str]:
    """Clone a GitHub repository using GitHub CLI.

    Args:
        repo_url (str): The URL of the GitHub repository to clone.
        dest_dir (str): The destination directory where the repository will be cloned.

    Returns:
        tuple[bool, str]: A tuple containing (is_successful, message)
            - is_successful: True if cloning was successful, False otherwise
            - message: Status message describing the result
    """
    logger.info(f"Cloning repository from {repo_url} to {dest_dir}")

    try:
        result = subprocess.run(  # noqa: S603
            ["gh", "repo", "clone", repo_url, dest_dir],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Repository cloned successfully - stdout: {result.stdout}")
        return True, f"Repository cloned successfully to {dest_dir}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository - return_code: {e.returncode}, stderr: {e.stderr}")
        return False, f"Failed to clone repository: {e.stderr.strip() if e.stderr else 'Unknown error'}"
    except FileNotFoundError:
        logger.warning("GitHub CLI not found in PATH")
        return False, "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"
