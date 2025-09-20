#!/usr/bin/env python3
"""Debug entry point for the filter CLI.

This script imports and runs the filter CLI from the installed package.
Use this for debugging in VS Code or other IDEs.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path for development
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from filter.cli import cli  # noqa: E402

if __name__ == "__main__":
    cli()
