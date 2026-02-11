"""Integration tests that hit the real PubChem API.

These tests are marked @pytest.mark.slow and are excluded from
pre-commit hooks. Run with: pixi run test-slow
"""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from src.validator import UnifiedChemicalValidator


@pytest.fixture
def validator(tmp_path):
    """Create a validator instance pointing at a dummy file."""
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("Name,CAS\na,b\n")
    return UnifiedChemicalValidator(str(dummy))


# ── PubChem Query Integration ───────────────────────────────────────────

@pytest.mark.slow
def test_query_pubchem_by_name(validator):
    """Query PubChem by chemical name returns valid CID and InChIKey."""
    cid, inchikey = validator.query_pubchem_cid_and_inchikey("Acetone", "name")
    assert cid is not None
    assert str(cid) == "180"  # Acetone CID
    assert inchikey is not None
    assert inchikey.startswith("CSCPPACGZOOCGX")  # Acetone InChIKey prefix


@pytest.mark.slow
def test_query_pubchem_by_cas(validator):
    """Query PubChem by CAS number returns valid CID."""
    cid, inchikey = validator.query_pubchem_cid_and_inchikey("67-64-1", "name")
    assert cid is not None
    assert str(cid) == "180"


@pytest.mark.slow
def test_query_pubchem_by_smiles(validator):
    """Query PubChem by SMILES returns valid CID."""
    cid, inchikey = validator.query_pubchem_cid_and_inchikey("CC(C)=O", "smiles")
    assert cid is not None
    assert str(cid) == "180"


@pytest.mark.slow
def test_query_pubchem_unknown_chemical(validator):
    """Query PubChem with nonsense returns (None, None)."""
    cid, inchikey = validator.query_pubchem_cid_and_inchikey(
        "xyzzy_not_a_chemical_12345", "name"
    )
    assert cid is None
    assert inchikey is None


# ── SMILES Retrieval Integration ────────────────────────────────────────

@pytest.mark.slow
def test_get_smiles_from_pubchem_real(validator):
    """Retrieve SMILES from a known CID."""
    smiles = validator.get_smiles_from_pubchem(180)  # Acetone
    assert smiles is not None
    assert "C" in smiles  # Acetone SMILES contains carbon


@pytest.mark.slow
def test_retrieve_smiles_real(validator):
    """Full SMILES retrieval: name + CAS -> SMILES."""
    smiles, cid_name, cid_cas, reason = validator.retrieve_smiles(
        1, "Ethanol", "64-17-5"
    )
    assert smiles is not None
    assert reason is None
    assert str(cid_name) == str(cid_cas)  # Both should resolve to same CID


# ── Full Validation Integration ─────────────────────────────────────────

@pytest.mark.slow
def test_validate_chemical_acetone(validator):
    """Validate Acetone with all three identifiers against real PubChem."""
    validator.smiles_retrieval_mode = False
    result = validator.validate_chemical(1, "Acetone", "67-64-1", "CC(C)=O")

    assert result["status"] == "validated"
    assert result["validated_cid"] is not None
    assert result["validated_inchikey"] is not None
    assert result["validated_canonical_inchikey_14"] is not None


@pytest.mark.slow
def test_validate_chemical_ethanol(validator):
    """Validate Ethanol with all three identifiers against real PubChem."""
    validator.smiles_retrieval_mode = False
    result = validator.validate_chemical(1, "Ethanol", "64-17-5", "CCO")

    assert result["status"] == "validated"
    assert result["validated_cid"] is not None


# ── End-to-End CSV Validation ───────────────────────────────────────────

@pytest.mark.slow
def test_validate_csv_full_mode_real(tmp_path):
    """End-to-end: validate a CSV with Name+CAS+SMILES against real PubChem."""
    csv_file = tmp_path / "chemicals.csv"
    csv_file.write_text(
        "Name,CAS,SMILES\n"
        "Acetone,67-64-1,CC(C)=O\n"
        "Ethanol,64-17-5,CCO\n"
    )

    v = UnifiedChemicalValidator(str(csv_file), output_folder=str(tmp_path))
    success = v.validate_csv()
    v.save_results()

    assert success is True
    assert len(v.validation_results) == 2
    assert all(r["status"] == "validated" for r in v.validation_results)

    # Verify output file was created
    xlsx_files = list(tmp_path.glob("validation_results_*.xlsx"))
    assert len(xlsx_files) == 1


@pytest.mark.slow
def test_validate_csv_retrieval_mode_real(tmp_path):
    """End-to-end: validate a CSV with Name+CAS only (retrieval mode)."""
    csv_file = tmp_path / "chemicals.csv"
    csv_file.write_text(
        "Name,CAS\n"
        "Acetone,67-64-1\n"
        "Ethanol,64-17-5\n"
    )

    v = UnifiedChemicalValidator(str(csv_file), output_folder=str(tmp_path))
    success = v.validate_csv()
    v.save_results()

    assert v.smiles_retrieval_mode is True
    assert len(v.validation_results) == 2

    # Both should have retrieved SMILES
    for r in v.validation_results:
        if r["status"] == "validated":
            assert r["smiles"] is not None
            assert r["smiles_source"] == "pubchem"

    xlsx_files = list(tmp_path.glob("validation_results_*.xlsx"))
    assert len(xlsx_files) == 1
