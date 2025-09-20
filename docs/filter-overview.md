## Project Overview

Filter is an **LLM-Powered Kanban Board** system that combines file-system based project management.

## Core Architecture

### 1. **File-System Based Kanban Board**

- **Kanban Columns**: Directories representing workflow stages (`planning/`, `in-progress/`, `testing/`, `pr/`, `complete/`)
- **Story Management**: Markdown files in `stories/` directory linked via symbolic links across workflow stages
- **Multi-Repository Support**: Each story can reference different git repositories with custom branching strategies

### 2. **Project Management System**

- **Project Organization**: Hierarchical structure with auto-generated prefixes for story naming (e.g., `ibstr-1`, `marke-2-refactor`)
- **Configuration Management**: YAML-based project configs with git URLs, maintainers, and metadata
- **Git Integration**: Automatic repository cloning and branch creation per workspace

## CLI Architecture

### **Categorical Design Pattern**

The CLI implements category theory principles with:

- **Functors**: Type-safe transformations for CLI operations
- **Monads**: Composable error handling and result chaining
- **Coproducts**: Command routing with proper universal properties
- **Command Algebra**: Mathematical composition of CLI operations

### **Command Structure**

- **Project Commands**: `create`, `list`, `delete` for project lifecycle management
- **Story Commands**: `create`, `delete`, `workspace` for story-specific operations
- **Utility Commands**: `claude`, `bash` for direct workspace access
- **Template Rendering**: Jinja2 template processing with variable precedence

## Key Features

### **Automated Development Workflow**

- **LLM Integration**: AI agents complete development tasks within workspaces
- **Git Workflow Automation**: Automatic repository cloning, branching, and workspace setup

### **Configuration Management**

- **Hierarchical Configuration**: Global, project, and workspace-level settings
- **Flexible Deployment**: Support for both `.filter` repositories and traditional project structures

## Data Flow Architecture

1. **Story Creation**: Stories defined in markdown with git repository references
1. **Workspace Generation**: Workspace environment directories created from templates
1. **Repository Management**: Git repositories cloned and branched per workspace
1. **Container Execution**: LLMs operate within isolated workspace environments
1. **Workflow Progression**: Stories move through kanban stages via symbolic links
1. **Audit Trail**: All operations logged for compliance and debugging

## Technical Implementation

### **Core Modules**

- **`workspace.py`**: Environment creation and management with Jinja2 templating
- **`projects.py`**: Project lifecycle and story discovery across repositories
- **`command_utils.py`**: Secure command execution with comprehensive logging
- **`cli_categorical.py`**: Mathematical command composition and routing
- **`config.py`**: Hierarchical configuration management

### **Logging & Auditing**

- **Multi-Level Logging**: Console, file, audit, and command-specific logs
- **Structured Logging**: JSON-compatible log entries with contextual metadata
- **Security-Aware**: Sensitive command redaction and user tracking
- **Rotation Management**: Automatic log rotation and size management

This architecture provides a complete solution for AI-assisted development across repositories while maintaining security, auditability, and workflow organization.
