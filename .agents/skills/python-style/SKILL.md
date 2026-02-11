# Python Coding Style

Guide for writing Python code in the chem-validator project.

## Type Hints (Required for Public Functions)

Use type hints for all public functions and methods. Private functions should have type hints when complexity warrants it.

### Common Types

```python
from typing import Optional, List, Dict, Any, Callable, Tuple
```

- `Optional[str]` - Can be string or None
- `List[Dict[str, Any]]` - List of dictionaries
- `Dict[str, Any]` - Dictionary with string keys, any values
- `Callable[[str], None]` - Callback function taking string, returning None
- `Tuple[int, str]` - Tuple with int and string

### Examples

```python
def validate_chemical(
    self,
    row_num: int,
    name: Optional[str],
    cas: Optional[str],
    smiles: Optional[str],
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Validate single chemical against PubChem."""
    pass
```

## Docstrings (Google Style - Required for Public Functions)

### Required For
- All public functions and methods
- All classes
- Complex private functions

### Optional For
- Simple getters/setters
- Obvious helper functions (< 3 lines)
- Very clear self-documenting functions

### Format

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short one-line summary.

    Longer description if needed. Explain the purpose, approach,
    and any important context.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
```

### Class Docstrings

```python
class UnifiedChemicalValidator:
    """
    Validates chemical identifiers against PubChem database.

    Supports two modes:
    - SMILES Retrieval: Name + CAS → retrieve SMILES from PubChem
    - Full Validation: Name + CAS + SMILES → validate all three

    Attributes:
        csv_path: Path to input CSV file
        validation_results: List of validation result dictionaries
        smiles_retrieval_mode: Boolean indicating operational mode
    """
```

## Complete Example

### Good Example

```python
from typing import Optional, Dict, Any

def normalize_cas(self, cas: Optional[str]) -> Optional[str]:
    """
    Normalize CAS number to standard format: XXXXX-XX-X.

    Handles various separator characters (unicode dashes, slashes, spaces)
    and converts them to standard hyphen format.

    Args:
        cas: Raw CAS number, may have non-standard separators or None

    Returns:
        Normalized CAS string in format XXXXX-XX-X, or None if invalid
    """
    if pd.isna(cas) or not cas:
        return None

    cas_str = str(cas).strip()
    if not cas_str:
        return None

    # Replace any run of non-digits with single dash
    cas_str = re.sub(r"[^\d]+", "-", cas_str).strip("-")

    digits_only = cas_str.replace("-", "")
    if not digits_only.isdigit() or len(digits_only) < 5:
        return cas_str

    check_digit = digits_only[-1]
    middle = digits_only[-3:-1]
    first = digits_only[:-3]
    return f"{first}-{middle}-{check_digit}"
```

### Bad Example

```python
def normalize_cas(cas):  # ❌ Missing type hints
    # ❌ No docstring
    if pd.isna(cas):
        return None
    # ... rest of code
```

## Import Organization

Organize imports in three groups, separated by blank lines:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable

# Third-party
import pandas as pd
import pubchempy as pcp

# Local
from src.validator import UnifiedChemicalValidator
```

## Naming Conventions

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

```python
# Good
class ChemicalValidator:
    MAX_RETRIES = 3

    def validate_smiles(self, smiles: str) -> bool:
        return self._query_pubchem(smiles)

    def _query_pubchem(self, identifier: str) -> bool:
        pass
```

## When Docstrings Are Optional

Skip docstrings for these cases:

```python
# Simple property
@property
def is_valid(self) -> bool:
    return self._valid

# Obvious getter
def get_results(self) -> List[Dict[str, Any]]:
    return self.validation_results

# Very simple helper (< 3 lines)
def _trim(self, s: Optional[str]) -> Optional[str]:
    return s.strip() if s else None
```

## Error Handling

Use specific exceptions and always log errors:

```python
def query_pubchem(self, identifier: str) -> Optional[int]:
    """Query PubChem for compound ID."""
    try:
        compounds = pcp.get_compounds(identifier, 'name')
        if compounds:
            return compounds[0].cid
    except Exception as e:
        logger.warning(f"PubChem query failed for {identifier}: {e}")

    return None
```

## Summary Checklist

When writing new code:
- [ ] Add type hints to function parameters and return types
- [ ] Write Google-style docstring for public functions
- [ ] Organize imports (stdlib, third-party, local)
- [ ] Use snake_case for functions/variables
- [ ] Use PascalCase for classes
- [ ] Log errors appropriately
- [ ] Keep functions focused and single-purpose
