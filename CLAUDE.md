# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**chem-validator** — Chemical CSV validator that validates Name, CAS, and SMILES identifiers against the PubChem database. Detects duplicates and stereoisomers, outputs results to Excel and CSV. Provides both a GUI (Tkinter) and CLI interface, distributed as standalone executables.

## Commands

All tasks run via `pixi run <task>`. Use `pixi install` for first-time setup.

| Task | Command |
|------|---------|
| Launch GUI | `pixi run gui` |
| Run CLI | `pixi run cli input.csv [--output-folder auto\|/path] [--output-format csv\|xlsx\|both]` |
| All tests | `pixi run test` |
| Fast tests only | `pixi run test-fast` |
| Integration tests | `pixi run test-slow` |
| Coverage report | `pixi run test-coverage` |
| Coverage check (80%) | `pixi run coverage-check` |
| Build executable | `pixi run build` |
| Clean artifacts | `pixi run clean` |
| Install git hooks | `pixi run install-hooks` |

Run a single test file: `pixi run test tests/test_validator.py` (append `-k <test_name>` to filter).

Add a dependency: `pixi add <package>` (updates `pixi.toml` and `pixi.lock`).

## Architecture

```
src/
├── main.py        # Entry point: no args → GUI, with args → CLI
├── validator.py   # Core logic: PubChem queries, validation, duplicate detection
├── gui.py         # Tkinter interface with threading for non-blocking validation
└── cli.py         # Argparse CLI; calls validator directly
```

**`validator.py`** is the pure business logic layer with zero GUI/CLI dependencies. Key responsibilities:
- Two validation modes: *Full* (Name + CAS + SMILES) and *Retrieval* (Name + CAS → fetch SMILES from PubChem)
- CAS normalization (standardizes separators to `XXXXX-XX-X`)
- Duplicate detection: exact (full InChIKey) and stereoisomer (first 14 chars of InChIKey)
- Rate limiting: 0.2s sleep between PubChem API calls
- Optional `progress_callback: Callable[[str], None]` parameter used by GUI for live log updates
- TLS trust configured via `CHEM_VALIDATOR_TLS_MODE` env var (`system`/`public`/`custom`)

**`gui.py`** runs validation in a background thread and routes UI updates through `.after()` for thread safety.

**`main.py`** is the Nuitka executable entry point.

## Testing

Tests are marked `@pytest.mark.fast` (unit, mocked PubChem, ~73 tests) or `@pytest.mark.slow` (integration, real PubChem API, ~10 tests). Pre-commit hooks automatically run fast tests and verify 80% coverage on every commit.

## Code Style

- **Type hints** required on all public functions; Google-style docstrings required on all public functions and classes
- **Imports**: stdlib → third-party → local (blank lines between groups)
- **Naming**: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants, `_leading_underscore` private methods
- **Commits**: Conventional Commits format — `type(scope): subject` (imperative, <50 chars). Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`. Scopes: `validator`, `gui`, `cli`, `tests`, `pixi`, `build`

## Skills

Detailed guidance available in `.agents/skills/`:
- `/help python-style` — type hints and docstring conventions
- `/help pixi-usage` — package management and task workflows
- `/help commit-conventions` — commit message format with examples
