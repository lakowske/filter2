# Filter Project

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
