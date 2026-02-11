# Pixi Package Management

Complete guide for using pixi in the chem-validator project.

## First Time Setup

Clone the repository and install environment:

```bash
cd chem-validator
pixi install
```

This command:
- Installs Python 3.13
- Installs all dependencies (pandas, pubchempy, pytest, etc.)
- Creates isolated `.pixi/` environment
- Generates `pixi.lock` file for reproducibility

## Running Tasks

All available tasks are defined in `pixi.toml`. Use `pixi run <task-name>`:

### Development Tasks

```bash
# Launch GUI
pixi run gui

# Run CLI validator
pixi run cli input.csv
pixi run cli input.csv --output-folder auto
pixi run cli input.csv --output-folder /custom/path
```

### Testing Tasks

```bash
# Run all tests
pixi run test

# Run only fast tests (marked with @pytest.mark.fast)
pixi run test-fast

# Run only slow tests (integration tests)
pixi run test-slow

# Run tests with coverage report (HTML + terminal)
pixi run test-coverage

# Check if coverage meets 80% threshold (used in pre-commit)
pixi run coverage-check
```

### Build Tasks

```bash
# Build standalone executable
pixi run build

# Clean build artifacts
pixi run clean
```

### Pre-commit Tasks

```bash
# Install pre-commit hooks (first time only)
pixi run install-hooks

# Run all pre-commit hooks manually
pixi run run-hooks
```

## Adding Dependencies

Add a new Python package:

```bash
pixi add <package-name>
```

### Examples

```bash
# Add numpy
pixi add numpy

# Add requests library
pixi add requests

# Add pytest plugin
pixi add pytest-xdist

# Add with specific version
pixi add "numpy>=1.24.0"
```

This automatically:
- Updates `pixi.toml` [dependencies] section
- Updates `pixi.lock` with resolved versions
- Installs the package in the environment

## Creating New Tasks

Edit `pixi.toml` and add to the `[tasks]` section:

### Simple Command

```toml
[tasks]
my-task = "python my_script.py"
```

### Complex Task with Description

```toml
[tasks]
my-complex-task = { cmd = "pytest && python build.py", description = "Run tests and build" }
```

Then run:
```bash
pixi run my-task
```

## Environment Management

### List Installed Packages

```bash
pixi list
```

### Update Dependencies

Update all packages to latest compatible versions:

```bash
pixi update
```

### View Environment Info

```bash
pixi info
```

Shows Python version, platform, channels, and package count.

### Activate Shell (Optional)

Enter the pixi environment in your shell:

```bash
pixi shell
```

Now you're inside the environment:
```bash
python --version  # Shows 3.13.x
which python      # Points to .pixi/envs/.../bin/python
```

Exit with `exit` or `Ctrl+D`.

## Common Workflows

### Daily Development

```bash
# Test changes in GUI
pixi run gui

# Quick test check
pixi run test-fast

# Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat(gui): add new feature"
```

### Before Committing

```bash
# Run all tests
pixi run test

# Verify coverage threshold
pixi run coverage-check

# Test that build works
pixi run build
```

### Release Workflow

```bash
# Ensure all tests pass
pixi run test

# Build executable
pixi run build

# Test the executable manually
./dist/chem-validator.exe  # Windows
./dist/chem-validator.app  # macOS

# Commit and tag
git commit -m "chore: release v0.2.0"
git tag v0.2.0
```

## Understanding pixi.lock

The `pixi.lock` file:
- Locks exact versions of all dependencies
- Ensures reproducible builds across machines
- Should be committed to git
- Auto-generated (don't edit manually)

If dependencies change, pixi automatically updates the lock file.

## Troubleshooting

### Lock File Out of Sync

If you get lock file errors:

```bash
# Force reinstall
pixi install --locked=false
```

### Clean Environment

Remove environment and reinstall:

```bash
# Clean pixi environment
pixi clean

# Reinstall from scratch
pixi install
```

### Remove Everything

Complete reset:

```bash
rm -rf .pixi pixi.lock
pixi install
```

### Dependency Conflicts

If packages conflict:

```bash
# Check what's installed
pixi list

# Remove problematic package
# Edit pixi.toml to remove the package line, then:
pixi install
```

## Platform-Specific Notes

### Windows

```bash
# Use PowerShell or cmd
pixi run gui

# Build executable
pixi run build
# Creates: dist/chem-validator.exe
```

### macOS

```bash
# Terminal
pixi run gui

# Build executable
pixi run build
# Creates: dist/chem-validator.app
```

### Linux

```bash
pixi run gui

# Note: PyInstaller creates binary (not .app bundle)
pixi run build
# Creates: dist/chem-validator
```

## Advanced: Custom Python Version

To use a different Python version, edit `pixi.toml`:

```toml
[dependencies]
python = "3.12.*"  # Changed from 3.13.*
```

Then:
```bash
pixi install
```

## Pixi vs pip/conda

**Why pixi?**
- Single tool for Python version + packages
- Faster than conda
- Better lock files than pip
- Cross-platform consistency
- No separate virtual environment activation needed

**Don't use:**
- `pip install` - Use `pixi add` instead
- `conda install` - Use `pixi add` instead
- `venv` or `virtualenv` - Pixi handles environments

## Quick Reference

```bash
# Setup
pixi install              # First time setup

# Development
pixi run gui              # Launch GUI
pixi run cli input.csv    # Run CLI

# Testing
pixi run test             # All tests
pixi run test-fast        # Fast tests only
pixi run test-coverage    # With coverage report

# Package Management
pixi add <package>        # Add package
pixi list                 # List packages
pixi update               # Update all packages

# Building
pixi run build            # Build executable
pixi run clean            # Clean artifacts

# Environment
pixi shell                # Activate environment
pixi info                 # Show environment info
pixi clean                # Clean environment
```

## Getting Help

```bash
# General help
pixi --help

# Task-specific help
pixi run --help

# List all available tasks
pixi task list
```
