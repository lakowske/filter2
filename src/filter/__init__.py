"""Filter - An LLM-Powered Kanban Board system."""

__version__ = "0.1.0"
__author__ = "Seth Lakowske"
__email__ = "lakowske@gmail.com"

from .actions.build import build
from .core import calculate_sum, greet
from .projects import ProjectManager
from .tools import check_github_cli, gh_clone_repo

__all__ = ["greet", "calculate_sum", "build", "ProjectManager", "check_github_cli", "gh_clone_repo"]
