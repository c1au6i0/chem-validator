# Chem Validator

[![Build Executables](https://github.com/c1au6i0/chem-validator/actions/workflows/build.yml/badge.svg)](https://github.com/c1au6i0/chem-validator/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/c1au6i0/chem-validator)](https://github.com/c1au6i0/chem-validator/releases)
[![License](https://img.shields.io/github/license/c1au6i0/chem-validator)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)

Chemical CSV validator with PubChem integration. Validates Name, CAS, and SMILES identifiers against the PubChem database, detects duplicates and stereoisomers, and exports results to Excel.

Provides both a GUI (Tkinter) and CLI interface. Distributed as standalone executables for Windows and macOS — no Python installation required.

## Features

- **PubChem validation** — queries Name, CAS, and SMILES against PubChem and verifies all identifiers resolve to the same compound (CID)
- **Two validation modes:**
  - **Full mode** — input has Name + CAS + SMILES columns; validates all three directly
  - **Retrieval mode** — input has only Name + CAS; retrieves SMILES from PubChem, then validates
- **Duplicate detection:**
  - **Exact duplicates** — full InChIKey match
  - **Stereoisomer duplicates** — first 14 characters of InChIKey (canonical layer) match
- **Excel output** — results saved as `.xlsx` with auto-filters and auto-width columns
- **Rate limiting** — 0.2s delay between PubChem API calls to respect usage limits

## Installation

Requires [pixi](https://pixi.sh/) for environment management.

```bash
git clone https://github.com/c1au6i0/chem-validator.git
cd chem-validator
pixi install
pixi run install-hooks
```

## Usage

### GUI

```bash
pixi run gui
```

Or double-click the built executable — launches the GUI by default when no arguments are provided.

#### Startup Time Note

On Windows and Linux, the standalone executable may take a few seconds to start (especially on first launch) because PyInstaller `onefile` builds unpack bundled dependencies to a temp directory. On macOS, the `.app` bundle uses `onedir` mode so startup is faster. The first run on macOS may also include additional OS verification (Gatekeeper).

### CLI

```bash
# Save results to current directory
pixi run cli input.csv

# Save to auto-generated subfolder (output/{input_name}/)
pixi run cli input.csv --output-folder

# Save to a custom folder
pixi run cli input.csv --output-folder /path/to/output
```

### Input Format

CSV or Excel file (`.csv`, `.xlsx`, `.xls`) with columns:

| Mode | Required Columns |
|------|-----------------|
| Full | Name, CAS, SMILES |
| Retrieval | Name, CAS |

Column detection is case-insensitive and uses substring matching (e.g., `Chemical Name`, `CAS Number`, `SMILES` all work).

### Output

Excel file named `validation_results_{input}_{timestamp}.xlsx` containing:

| Column | Description |
|--------|-------------|
| `row_number` | Row number in input file |
| `name` | Chemical name |
| `cas` | Normalized CAS number |
| `smiles` | SMILES string (from input or retrieved) |
| `smiles_source` | `input` or `pubchem` |
| `cid_by_name` | CID resolved from name |
| `cid_by_cas` | CID resolved from CAS |
| `cid_by_smiles` | CID resolved from SMILES |
| `validated_cid` | Confirmed CID (when all match) |
| `validated_inchikey` | Confirmed InChIKey |
| `status` | `validated`, `rejected`, or `stereo_duplicate` |
| `rejection_reason` | Reason for rejection (if applicable) |
| `exact_duplicate_group` | Group number for exact duplicates |
| `stereo_duplicate_group` | Group number for stereoisomer duplicates |

### Status Values

| Status | Meaning |
|--------|---------|
| `validated` | All resolved CIDs match |
| `rejected` | Validation failed |
| `stereo_duplicate` | Validated, but is a stereoisomer of another entry |

### Rejection Reasons

| Reason | Meaning |
|--------|---------|
| `insufficient_identifiers` | Missing required identifiers for the active mode |
| `pubchem_discordance` | CIDs from different identifiers do not match |
| `identifier_not_found` | One or more identifiers not found in PubChem |
| `exact_duplicate` | Full InChIKey matches a previously validated chemical |
| `complex_chemical_no_smiles` | PubChem has the compound but no SMILES available |

## Development

### Project Structure

```
src/
├── main.py         # Entry point (GUI if no args, CLI if args)
├── validator.py    # Core validation logic and PubChem integration
├── gui.py          # Tkinter GUI interface
└── cli.py          # Command-line interface

tests/
├── test_validator.py     # 46 unit tests for core logic
├── test_gui.py           # 20 tests (headless-safe, mocked Tkinter)
├── test_cli.py           # 5 CLI tests
├── test_main.py          # 2 routing tests
├── test_integration.py   # 10 slow tests (real PubChem API)
├── conftest.py           # Pytest markers
└── fixtures/             # Test CSV files
```

### Commands

| Task | Command |
|------|---------|
| Run GUI | `pixi run gui` |
| Run CLI | `pixi run cli input.csv` |
| Run all tests | `pixi run test` |
| Fast tests only | `pixi run test-fast` |
| Integration tests | `pixi run test-slow` |
| Coverage report | `pixi run test-coverage` |
| Coverage check (80%) | `pixi run coverage-check` |
| Build executable | `pixi run build` |
| Clean artifacts | `pixi run clean` |
| Install git hooks | `pixi run install-hooks` |

### Testing

Tests are marked with `@pytest.mark.fast` or `@pytest.mark.slow`:

- **Fast tests** (73) — unit tests with mocked PubChem responses, run in <1s
- **Slow tests** (10) — integration tests hitting the real PubChem API

Pre-commit hooks automatically run fast tests and verify 80% coverage before each commit.

### Building

```bash
pixi run build
```

Packaging is done with PyInstaller via `build.spec`.

Produces a standalone executable in `dist/`:
- **Linux:** `dist/chem-validator`
- **Windows:** `dist/chem-validator.exe`
- **macOS:** `dist/chem-validator.app`

For GitHub Releases on macOS, the app is typically distributed as a zip (e.g. `chem-validator-macos.zip`). Unzip it and then open `chem-validator.app`.

For GitHub Releases on Windows, a `.msi` installer may also be provided (e.g. `chem-validator-windows.msi`).

### Dependencies

| Package | Purpose |
|---------|---------|
| pandas | CSV/Excel reading and data handling |
| pubchempy | PubChem API queries |
| openpyxl | Excel output with formatting |
| pytest | Test framework |
| pytest-cov | Coverage reporting |
| pytest-mock | Test mocking utilities |
| pyinstaller | Standalone executable builds |
| pre-commit | Git hook management |

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
