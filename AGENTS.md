# Chem Validator - Agent Guide

## Project Overview

Chemical CSV validator with PubChem integration. Validates Name, CAS, and SMILES identifiers against PubChem database. Provides both GUI (Tkinter) and CLI interfaces. Distributed as standalone executables for Windows and macOS.

## Project Structure

```
src/
├── validator.py    # Core validation logic - PubChem integration
├── gui.py          # Tkinter GUI interface
├── cli.py          # Command-line interface
└── main.py         # Entry point (launches GUI by default)

tests/
├── test_validator.py  # Unit tests (use @pytest.mark.fast for quick tests)
├── conftest.py        # Pytest fixtures
└── fixtures/          # Test CSV files

.agents/skills/        # Reusable skills (use /help skills to see available)
├── python-style/      # Type hints, docstrings
├── pixi-usage/        # Pixi commands and workflows
└── commit-conventions/  # Git commit message format
```

## Module Responsibilities

### validator.py (Core Backend - Easy to Update)

**Purpose**: Pure business logic for chemical validation

**Key Functions**:
- **PubChem API interaction**: Query by name, CAS, SMILES
- **Rate limiting**: 0.2s between API calls (see `time.sleep(0.2)` in code)
- **CAS normalization**: Standardize format to XXXXX-XX-X
- **Validation logic**: Check all three identifiers match same CID
- **Duplicate detection**:
  - Exact duplicates (full InChIKey match)
  - Stereoisomer duplicates (14-char canonical InChIKey)
- **Progress callbacks**: Support for GUI live updates

**Design Principle**: Zero GUI/CLI dependencies. Can be updated independently of interfaces.

**Callback Pattern**:
```python
def validate_chemical(
    self,
    row_num: int,
    name: Optional[str],
    cas: Optional[str],
    smiles: Optional[str],
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    if progress_callback:
        progress_callback(f"Processing row {row_num}...")
    # ... validation logic
```

### gui.py (Tkinter GUI)

**Purpose**: User-friendly interface for non-technical users

**Key Features**:
- File picker for CSV input
- Output folder selection (current/auto/custom)
- Live log viewer (scrolling text widget)
- Results summary panel
- Threading for non-blocking validation

**Threading Pattern**: Background thread for validation, UI updates via `.after()` to ensure thread safety.

**Integration**: Calls `validator.validate_csv()` with `progress_callback` parameter.

### cli.py (Command Line)

**Purpose**: Preserve original script behavior for power users and automation

**Features**:
- Argparse interface (same as original script)
- Direct validator.py calls
- Console logging via logging module

**Usage**: `pixi run cli input.csv --output-folder auto`

### main.py (Entry Point)

**Purpose**: Route to appropriate interface based on usage

**Logic**:
- No args → Launch GUI (for users double-clicking .exe)
- With args → Route to CLI (for terminal/automation)

Used by PyInstaller as the executable entry point.

## Key Design Decisions

**Why modular?**
Validator logic (validator.py) can be updated independently of interfaces. Both GUI and CLI share the same validation code. Easier to test, maintain, and extend.

**Why pixi?**
Reproducible environments across platforms. Single tool for Python version + all dependencies. See skill: `/help pixi-usage`

**Why type hints?**
Improve code clarity, catch errors early, enable better IDE support. See skill: `/help python-style`

**Why PyInstaller?**
Creates standalone .exe/.app for end users. No Python installation required. Works offline after download.

**Why pre-commit hooks?**
Catch issues early. Run fast tests before commits to ensure code quality.

## Integration Points

- **GUI → Validator**: Passes `progress_callback` function for live log updates
- **CLI → Validator**: Direct call, logs to console via `logging` module
- **Validator → PubChem**: Rate-limited queries (0.2s sleep between calls)
- **Tests → Validator**: Unit tests mock PubChem responses for speed

## Development Workflow

1. **Setup** (first time only):
   ```bash
   pixi install
   pixi run install-hooks
   ```

2. **Development cycle**:
   ```bash
   # Edit code in src/
   pixi run gui           # Test GUI
   pixi run test-fast     # Quick test check
   ```

3. **Before commit**:
   ```bash
   pixi run test          # All tests
   pixi run coverage-check # Verify 80% coverage
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "feat(validator): add new feature"
   # Pre-commit hooks run automatically
   ```

5. **Build**:
   ```bash
   pixi run build         # Creates executable in dist/
   ```

## Code Style

**Use skills for detailed guidance**:
- **Type hints**: See `/help python-style` - Required for public functions
- **Docstrings**: See `/help python-style` - Google style, required for public functions
- **Pixi commands**: See `/help pixi-usage` - All package management and task running
- **Commit messages**: See `/help commit-conventions` - Conventional Commits format

**Quick conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Imports: stdlib → third-party → local (blank lines between)

## Testing

### Running Tests

```bash
pixi run test          # All tests
pixi run test-fast     # Only @pytest.mark.fast tests
pixi run test-slow     # Only @pytest.mark.slow tests (integration)
pixi run test-coverage # Generate HTML coverage report
```

### Writing Tests

Mark tests appropriately:

```python
@pytest.mark.fast  # Quick unit test (< 0.1s)
def test_cas_normalization():
    validator = UnifiedChemicalValidator("dummy.csv")
    assert validator.normalize_cas("67-64-1") == "67-64-1"

@pytest.mark.slow  # Integration test hitting real PubChem API
def test_pubchem_integration():
    # ... actual API call
```

### Pre-commit

Fast tests and coverage check run automatically before each commit. To skip (not recommended):
```bash
git commit --no-verify
```

## Building Executable

```bash
pixi run build
```

Creates:
- Windows: `dist/chem-validator.exe`
- macOS: `dist/chem-validator.app`

Test the executable manually before distributing. See `docs/BUILD.md` for platform-specific notes.

## Common Tasks

| Task | Command |
|------|---------|
| Add dependency | `pixi add <package>` |
| Run GUI | `pixi run gui` |
| Run CLI | `pixi run cli input.csv` |
| Run tests | `pixi run test` |
| Quick tests | `pixi run test-fast` |
| Coverage report | `pixi run test-coverage` |
| Build exe | `pixi run build` |
| Clean artifacts | `pixi run clean` |
| Install hooks | `pixi run install-hooks` |

## Troubleshooting

- **Import errors**: Run `pixi install` to set up environment
- **Test failures**: Check if you're in pixi environment (`pixi shell`)
- **Build issues**: Clean first (`pixi run clean`) then rebuild
- **Lock file errors**: Try `pixi install --locked=false`

For more detailed help, see the skills in `.agents/skills/` or use `/help <skill-name>`.
