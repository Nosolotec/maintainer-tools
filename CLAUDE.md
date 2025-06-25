# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the OCA (Odoo Community Association) maintainer-tools repository, containing a collection of Python tools for managing Odoo Community projects. The tools are designed for both OCA maintainers and contributors to automate common tasks like repository management, README generation, and addon maintenance.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment and install in development mode
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -e .
```

### Testing
```bash
# Run all tests with tox
tox

# Run tests for specific Python version
tox -e py38

# Run specific tests with pytest directly
pytest --cov=tools --cov-branch --cov-report=html --ignore=tests/test_repo --ignore=template

# Run tests matching a pattern
tox -- -k readme -v
```

### Code Quality
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install

# Format code with black
black .

# Check code style with flake8
flake8
```

## Architecture

### Core Structure
- `tools/` - Main package containing all CLI tools as Python modules
- `template/` - Contains Odoo addon template structure for scaffolding
- `tests/` - Test suite with test data and fixtures
- `setup.py` - Package configuration defining 25+ console entry points

### Key Modules
- `tools/manifest.py` - Core utilities for parsing Odoo manifest files (`__manifest__.py`, `__openerp__.py`)
- `tools/github_login.py` - GitHub authentication and token management
- `tools/gen_addon_readme.py` - Automated README generation from fragments
- `tools/copy_maintainers.py` - Syncs team members from community.odoo.com to GitHub
- `tools/clone_everything.py` - Mass cloning of OCA repositories

### Entry Points
The package provides 25+ CLI commands via setup.py console_scripts, including:
- `oca-gen-addon-readme` - Generate README from fragments
- `oca-gen-addon-icon` - Generate standardized addon icons
- `oca-clone-everything` - Clone all OCA repositories
- `oca-copy-maintainers` - Sync maintainers from Odoo to GitHub
- `oca-towncrier` - Generate changelogs using towncrier

### Configuration
- `oca.cfg` - Stores GitHub tokens and Odoo credentials (contains sensitive data)
- `.pre-commit-config.yaml` - Pre-commit hooks for black and flake8
- `tox.ini` - Test configuration for Python 3.6-3.11

## Key Dependencies
- `github3.py` - GitHub API interactions
- `manifestoo-core` - Odoo manifest parsing
- `towncrier` - Changelog generation
- `jinja2` - Template rendering
- `selenium` - Web automation for certain tools

## Authentication
GitHub authentication is handled via personal access tokens stored in `oca.cfg` or the `GITHUB_TOKEN` environment variable. Use `oca-github-login` to set up authentication.