# Commit Message Conventions

Use Conventional Commits format for all commits in this project.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: Required - Type of change
- **scope**: Optional - What was affected
- **subject**: Required - Brief description (lowercase, no period)
- **body**: Optional - Detailed explanation
- **footer**: Optional - Breaking changes, issue references

## Types

### Primary Types (Use Most Often)

**feat**: New feature for the user

```
feat(gui): add live progress bar to validation
feat(validator): support SMILES retrieval mode
feat: add export to Excel functionality
```

**fix**: Bug fix for the user

```
fix(validator): correct CAS normalization for edge cases
fix(gui): prevent UI freeze during long validations
fix: handle empty CSV files gracefully
```

**docs**: Documentation changes

```
docs: update README with installation instructions
docs(skills): add examples to pixi-usage skill
docs: add troubleshooting guide for macOS
```

### Secondary Types

**style**: Code style changes (formatting, no logic change)

```
style: format code with black
style(validator): fix inconsistent indentation
```

**refactor**: Code restructuring (no functionality change)

```
refactor(validator): extract PubChem query logic
refactor: move constants to separate config file
```

**test**: Adding or updating tests

```
test(validator): add tests for duplicate detection
test: increase coverage to 85%
test: add fixtures for edge cases
```

**chore**: Maintenance tasks (dependencies, configs)

```
chore: update dependencies
chore(pixi): add pytest-mock to dependencies
chore: bump version to 0.2.0
```

**perf**: Performance improvements

```
perf(validator): reduce API calls with caching
perf: optimize duplicate detection algorithm
```

**ci**: CI/CD changes

```
ci: add pre-commit hooks
ci: configure pytest coverage threshold
```

**build**: Build system changes

```
build: configure PyInstaller for smaller executables
build(pixi): update Python to 3.13.5
build: add icon to Windows executable
```

## Scope Examples

Use scope to indicate what part was modified:

- `validator` - Core validation logic (src/validator.py)
- `gui` - Tkinter interface (src/gui.py)
- `cli` - Command-line interface (src/cli.py)
- `tests` - Test suite
- `skills` - OpenCode skills
- `docs` - Documentation files
- `pixi` - Pixi configuration
- `build` - Build/distribution setup

## Subject Guidelines

Follow these rules for the subject line:

1. **Use imperative mood** ("add" not "added" or "adds")
2. **Keep under 50 characters**
3. **Don't capitalize first letter**
4. **No period at the end**
5. **Be specific but concise**

### Good Examples

```
feat(gui): add file picker for CSV input
fix(validator): handle empty CAS fields correctly
docs: add build instructions for macOS
refactor(validator): extract duplicate detection logic
test: add integration tests for PubChem API
```

### Bad Examples

```
Added feature              ❌ Not imperative, not specific
Fix bug.                   ❌ Not specific, has period
GUI changes                ❌ No type prefix
FEAT: BIG UPDATE!!!        ❌ Shouty, not specific
feat(gui): Added the new feature  ❌ Not imperative, capitalized
```

## Body Guidelines (Optional)

Use the body to explain:
- **WHY** the change was made (not what - the diff shows that)
- The approach taken
- Side effects or limitations
- Context for future maintainers

Separate from subject with a blank line:

```
feat(validator): add progress callback mechanism

Allows GUI to receive live updates during validation without
blocking the main thread. Callback is optional and defaults
to None for CLI usage.

The callback receives status strings which are displayed in
the GUI's scrolling log viewer.
```

## Footer Guidelines

### Breaking Changes

Use `BREAKING CHANGE:` in footer or `!` after type:

```
feat(validator)!: change validate_csv signature

BREAKING CHANGE: validate_csv now requires csv_path as first argument
instead of accepting it in constructor. Update all callers.
```

### Issue References

Reference issues in footer:

```
fix(gui): prevent crash on empty CSV

Closes #42
Fixes #38
See also #35
```

## Real Examples from This Project

### New Feature

```
feat(gui): add Tkinter interface with live logging

Implements file picker, output selection, and scrolling log viewer.
Uses threading to prevent UI freeze during PubChem queries.

Features included:
- CSV file browser
- Output location selector (current/auto/custom)
- Live log updates via progress callback
- Results summary panel
```

### Bug Fix

```
fix(validator): normalize CAS with unicode dashes

Some CSV files contain unicode dash characters (–, —) instead of
standard hyphens. Updated regex to handle all non-digit separators.

Fixes #15
```

### Refactoring

```
refactor: extract validation logic into separate module

Moved UnifiedChemicalValidator from 01_validate_csv.py to
src/validator.py. Added type hints and improved docstrings.
No functionality changes.

This enables both GUI and CLI to share the same validation code.
```

### Documentation

```
docs: add commit conventions skill

Provides guidance on Conventional Commits format for consistent
git history across all contributors and AI agents.
```

### Testing

```
test(validator): add comprehensive duplicate detection tests

Added tests for:
- Exact duplicates (full InChIKey match)
- Stereoisomer duplicates (14-char canonical InChIKey)
- Edge cases with missing InChIKeys

Coverage increased from 68% to 82%.
```

### Build/Chore

```
build: configure PyInstaller for GUI mode

Set console=False to hide terminal window on Windows.
Added icon and version info to executable.
Reduced bundle size by excluding dev dependencies.
```

```
chore(pixi): add testing and quality tools

Added dependencies:
- pytest-cov for coverage reports
- pytest-mock for mocking
- pre-commit for git hooks

Updated pixi.lock with resolved versions.
```

## Multi-line Subjects (When Necessary)

If you absolutely need more space, use body instead:

```
feat(gui): add comprehensive validation interface

Created full Tkinter GUI with file selection, output configuration,
live progress logging, and results display. Includes threading to
prevent UI blocking during long PubChem validation operations.
```

Better as:

```
feat(gui): add comprehensive validation interface

Includes:
- File picker and output selector
- Live progress log with threading
- Results summary and table preview
- Non-blocking PubChem validation
```

## Quick Reference

```
feat:      ✨ New feature
fix:       🐛 Bug fix
docs:      📝 Documentation
style:     💄 Code style
refactor:  ♻️  Code restructuring
test:      ✅ Tests
chore:     🔧 Maintenance
perf:      ⚡ Performance
ci:        👷 CI/CD
build:     📦 Build system
```

## Pre-commit Hook Integration

This project can optionally validate commit messages automatically.

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v2.4.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
```

This will **reject commits** that don't follow the convention.

## Examples by Scenario

### Adding a new feature

```
feat(gui): add drag-and-drop CSV support

Users can now drag CSV files directly onto the GUI window
instead of using the file picker dialog.
```

### Fixing a bug

```
fix(validator): handle missing CAS numbers correctly

Previously crashed when CAS field was completely empty.
Now treats empty CAS as None and continues validation.

Fixes #23
```

### Updating documentation

```
docs(build): add macOS code signing instructions

Explains how to sign the .app bundle to avoid Gatekeeper warnings.
Includes both ad-hoc signing and Developer ID signing methods.
```

### Refactoring code

```
refactor(validator): split validation into smaller methods

Extracted _validate_identifiers and _check_pubchem_consistency
from main validate_chemical method. Improves readability and
testability. No behavior changes.
```

### Adding tests

```
test(cli): add tests for command-line argument parsing

Covers all CLI options including --output-folder variants.
Uses pytest fixtures for temporary test files.
```

### Updating dependencies

```
chore(pixi): update pandas to 2.2.0

Includes performance improvements for large CSV files and
bug fixes for CAS number handling.
```

### Performance improvement

```
perf(validator): cache PubChem results

Implements LRU cache for PubChem queries to avoid redundant
API calls for duplicate identifiers. Reduces validation time
by ~30% for typical datasets.
```

## Summary

1. Always use a type prefix (feat, fix, docs, etc.)
2. Optionally add scope in parentheses
3. Write clear, imperative subject (< 50 chars)
4. Add body for context (why, not what)
5. Reference issues in footer
6. Mark breaking changes with `!` or `BREAKING CHANGE:`
