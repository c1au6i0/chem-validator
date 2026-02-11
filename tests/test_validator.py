"""Unit tests for Chem Validator."""

# Standard library
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pandas as pd
import pytest

# Local
from src.validator import UnifiedChemicalValidator

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def validator(tmp_path):
    """Create a validator instance pointing at a dummy file."""
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("Name,CAS\na,b\n")
    return UnifiedChemicalValidator(str(dummy))


# ── CAS Normalization ──────────────────────────────────────────────────

@pytest.mark.fast
def test_cas_normalization_standard(validator):
    assert validator.normalize_cas("67-64-1") == "67-64-1"


@pytest.mark.fast
def test_cas_normalization_no_dashes(validator):
    assert validator.normalize_cas("67641") == "67-64-1"


@pytest.mark.fast
def test_cas_normalization_unicode_dashes(validator):
    # en-dash U+2013
    assert validator.normalize_cas("67\u201364\u20131") == "67-64-1"


@pytest.mark.fast
def test_cas_normalization_underscores(validator):
    assert validator.normalize_cas("67_64_1") == "67-64-1"


@pytest.mark.fast
def test_cas_normalization_whitespace(validator):
    assert validator.normalize_cas("  67-64-1  ") == "67-64-1"


@pytest.mark.fast
def test_cas_normalization_none(validator):
    assert validator.normalize_cas(None) is None


@pytest.mark.fast
def test_cas_normalization_empty(validator):
    assert validator.normalize_cas("") is None


@pytest.mark.fast
def test_cas_normalization_short_digits(validator):
    """CAS with fewer than 5 digits returns as-is after dash normalization."""
    result = validator.normalize_cas("12-3")
    assert result == "12-3"


# ── Column Identification ─────────────────────────────────────────────

@pytest.mark.fast
def test_identify_columns_full_mode(validator):
    df = pd.DataFrame({"Name": [], "CAS": [], "SMILES": []})
    name, cas, smiles = validator.identify_columns(df)
    assert name == "Name"
    assert cas == "CAS"
    assert smiles == "SMILES"
    assert validator.smiles_retrieval_mode is False


@pytest.mark.fast
def test_identify_columns_retrieval_mode(validator):
    df = pd.DataFrame({"chemical_name": [], "cas_number": []})
    name, cas, smiles = validator.identify_columns(df)
    assert name == "chemical_name"
    assert cas == "cas_number"
    assert smiles is None
    assert validator.smiles_retrieval_mode is True


@pytest.mark.fast
def test_identify_columns_smile_singular(validator):
    """Accept 'smile' (singular) as a SMILES column."""
    df = pd.DataFrame({"Name": [], "CAS": [], "smile": []})
    _, _, smiles = validator.identify_columns(df)
    assert smiles == "smile"


@pytest.mark.fast
def test_identify_columns_cassia_excluded(validator):
    """'cassia' should NOT match as CAS column."""
    df = pd.DataFrame({"Name": [], "cassia_oil": [], "CAS_number": []})
    _, cas, _ = validator.identify_columns(df)
    assert cas == "CAS_number"


@pytest.mark.fast
def test_identify_columns_missing_raises(validator):
    df = pd.DataFrame({"Foo": [], "Bar": []})
    with pytest.raises(ValueError, match="Could not find Name or CAS columns"):
        validator.identify_columns(df)


# ── Validation (mocked PubChem) ────────────────────────────────────────

@pytest.mark.fast
def test_validate_chemical_all_match(validator, mocker):
    """All three identifiers resolve to the same CID -> validated."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "INCHIKEY123"),  # by name
        ("123", "INCHIKEY123"),  # by cas
        ("123", "INCHIKEY123"),  # by smiles
    ])

    result = validator.validate_chemical(1, "Test", "67-64-1", "C(=O)C")
    assert result["status"] == "validated"
    assert result["validated_cid"] == "123"
    assert result["validated_inchikey"] == "INCHIKEY123"
    assert result["validated_canonical_inchikey_14"] == "INCHIKEY123"[:14]


@pytest.mark.fast
def test_validate_chemical_discordance(validator, mocker):
    """CIDs mismatch -> pubchem_discordance."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "IK1"),  # by name
        ("456", "IK2"),  # by cas
        ("123", "IK1"),  # by smiles
    ])

    result = validator.validate_chemical(1, "Test", "67-64-1", "C(=O)C")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "pubchem_discordance"


@pytest.mark.fast
def test_validate_chemical_two_found_agree(validator, mocker):
    """Only 2 of 3 found but they agree -> identifier_not_found."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "IK1"),   # by name
        ("123", "IK1"),   # by cas
        (None, None),     # smiles not found
    ])

    result = validator.validate_chemical(1, "Test", "67-64-1", "C(=O)C")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "identifier_not_found"


@pytest.mark.fast
def test_validate_chemical_two_found_disagree(validator, mocker):
    """2 of 3 found but they disagree."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "IK1"),   # by name
        ("456", "IK2"),   # by cas
        (None, None),     # smiles not found
    ])

    result = validator.validate_chemical(1, "Test", "67-64-1", "C(=O)C")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "identifier_not_found_and_pubchem_discordance"


@pytest.mark.fast
def test_validate_chemical_invalid_smiles_rejected(validator, mocker):
    """Invalid SMILES (PubChem 400) is rejected as invalid_smiles."""
    validator.smiles_retrieval_mode = False

    mock_compound = MagicMock()
    mock_compound.cid = "241"
    mock_compound.inchikey = "UHOVQNZJYSORNB"

    mocker.patch(
        "pubchempy.get_compounds",
        side_effect=[
            [mock_compound],
            [mock_compound],
            Exception(
                "PubChem HTTP Error 400 PUGREST.BadRequest: Unable to standardize the given structure"
            ),
        ],
    )
    mocker.patch("src.validator.time.sleep")

    result = validator.validate_chemical(1, "Benzene", "71-43-2", "Cdd")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "invalid_smiles"


@pytest.mark.fast
def test_validate_chemical_invalid_cas_rejected(validator, mocker):
    """Invalid CAS is rejected as invalid_cas before PubChem queries."""
    validator.smiles_retrieval_mode = False

    mock_get = mocker.patch("pubchempy.get_compounds")

    result = validator.validate_chemical(1, "Benzene", "71-43-3", "c1ccccc1")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "invalid_cas"
    mock_get.assert_not_called()


@pytest.mark.fast
def test_validate_chemical_none_found(validator, mocker):
    """None of the identifiers found."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    result = validator.validate_chemical(1, "Test", "67-64-1", "C(=O)C")
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "identifier_not_found"


@pytest.mark.fast
def test_validate_chemical_insufficient_full_mode(validator):
    """Full validation mode: missing SMILES -> rejected."""
    validator.smiles_retrieval_mode = False
    result = validator.validate_chemical(1, "Test", "123-45-6", None)
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "insufficient_identifiers"


@pytest.mark.fast
def test_validate_chemical_insufficient_retrieval_mode(validator):
    """Retrieval mode: missing CAS -> rejected."""
    validator.smiles_retrieval_mode = True
    result = validator.validate_chemical(1, "Test", None, None)
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "insufficient_identifiers"


@pytest.mark.fast
def test_validate_chemical_progress_callback(validator, mocker):
    """Progress callback is called during validation."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", return_value=(None, None))
    messages = []
    result = validator.validate_chemical(1, "Test", "123-45-6", "C(=O)C", progress_callback=messages.append)
    assert len(messages) > 0
    assert "Row 1" in messages[0]


# ── Duplicate Detection ────────────────────────────────────────────────

@pytest.mark.fast
def test_exact_duplicates(validator):
    """Second chemical with same InChIKey gets rejected as exact_duplicate."""
    validator.validation_results = [
        {"status": "validated", "validated_inchikey": "AAAAAAAAA", "validated_canonical_inchikey_14": "AAAAAAAAA12345", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 1, "name": "A"},
        {"status": "validated", "validated_inchikey": "AAAAAAAAA", "validated_canonical_inchikey_14": "AAAAAAAAA12345", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 2, "name": "A dup"},
        {"status": "validated", "validated_inchikey": "BBBBBBBBB", "validated_canonical_inchikey_14": "BBBBBBBBB12345", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 3, "name": "B"},
    ]

    validator.check_exact_duplicates()

    assert validator.validation_results[0]["status"] == "validated"
    assert validator.validation_results[0]["exact_duplicate_group"] == 1
    assert validator.validation_results[1]["status"] == "rejected"
    assert validator.validation_results[1]["rejection_reason"] == "exact_duplicate"
    assert validator.validation_results[2]["status"] == "validated"
    assert validator.validation_results[2]["exact_duplicate_group"] is None


@pytest.mark.fast
def test_stereoisomer_duplicates(validator):
    """Chemicals sharing 14-char canonical InChIKey get marked as stereo_duplicate."""
    validator.validation_results = [
        {"status": "validated", "validated_inchikey": "AAAAAAAAAA-BBB-C", "validated_canonical_inchikey_14": "AAAAAAAAAA-BBB", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 1, "name": "A"},
        {"status": "validated", "validated_inchikey": "AAAAAAAAAA-BBB-D", "validated_canonical_inchikey_14": "AAAAAAAAAA-BBB", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 2, "name": "A-stereo"},
    ]

    validator.check_stereoisomer_duplicates()

    assert validator.validation_results[0]["status"] == "validated"
    assert validator.validation_results[0]["stereo_duplicate_group"] == 1
    assert validator.validation_results[1]["status"] == "stereo_duplicate"
    assert validator.validation_results[1]["stereo_duplicate_group"] == 1


@pytest.mark.fast
def test_no_duplicates(validator):
    """No duplicates when all InChIKeys are unique."""
    validator.validation_results = [
        {"status": "validated", "validated_inchikey": "AAA", "validated_canonical_inchikey_14": "AAA", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 1, "name": "A"},
        {"status": "validated", "validated_inchikey": "BBB", "validated_canonical_inchikey_14": "BBB", "exact_duplicate_group": None, "stereo_duplicate_group": None, "row_number": 2, "name": "B"},
    ]

    validator.check_exact_duplicates()
    validator.check_stereoisomer_duplicates()

    assert all(r["status"] == "validated" for r in validator.validation_results)
    assert all(r["exact_duplicate_group"] is None for r in validator.validation_results)
    assert all(r["stereo_duplicate_group"] is None for r in validator.validation_results)


# ── File I/O ───────────────────────────────────────────────────────────

@pytest.mark.fast
def test_validate_csv_reads_csv(tmp_path, mocker):
    """validate_csv reads a CSV file and processes rows."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    v = UnifiedChemicalValidator(str(csv_file))
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    v.validate_csv()
    assert len(v.validation_results) == 1


@pytest.mark.fast
def test_validate_csv_reads_excel(tmp_path, mocker):
    """validate_csv reads an Excel file."""
    xlsx_file = tmp_path / "input.xlsx"
    df = pd.DataFrame({"Name": ["Acetone"], "CAS": ["67-64-1"], "SMILES": ["CC(C)=O"]})
    df.to_excel(xlsx_file, index=False)

    v = UnifiedChemicalValidator(str(xlsx_file))
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    v.validate_csv()
    assert len(v.validation_results) == 1


@pytest.mark.fast
def test_validate_csv_drops_empty_rows(tmp_path, mocker):
    """Rows with all identifiers empty are dropped."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n,,\n")

    v = UnifiedChemicalValidator(str(csv_file))
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    v.validate_csv()
    assert len(v.validation_results) == 1


@pytest.mark.fast
def test_validate_csv_missing_columns(tmp_path):
    """validate_csv returns False when Name/CAS columns are missing."""
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("Foo,Bar\na,b\n")

    v = UnifiedChemicalValidator(str(csv_file))
    result = v.validate_csv()
    assert result is False


@pytest.mark.fast
def test_save_results_creates_xlsx(tmp_path, mocker):
    """save_results writes an .xlsx file with auto-filter."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    v = UnifiedChemicalValidator(str(csv_file), output_folder=str(tmp_path))
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    v.validate_csv()
    success = v.save_results()

    assert success is True
    xlsx_files = list(tmp_path.glob("validation_results_*.xlsx"))
    assert len(xlsx_files) == 1

    # Verify the file can be read back
    result_df = pd.read_excel(xlsx_files[0])
    assert "status" in result_df.columns
    assert len(result_df) == 1


@pytest.mark.fast
def test_save_results_auto_folder(tmp_path, mocker, monkeypatch):
    """save_results with 'auto' creates output/{stem}/ subfolder."""
    csv_file = tmp_path / "my_chemicals.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    # Run from tmp_path so 'auto' creates output/ there, not in project root
    monkeypatch.chdir(tmp_path)

    v = UnifiedChemicalValidator(str(csv_file), output_folder="auto")
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    v.validate_csv()
    success = v.save_results()

    assert success is True
    auto_dir = tmp_path / "output" / "my_chemicals"
    assert auto_dir.exists()
    xlsx_files = list(auto_dir.glob("*.xlsx"))
    assert len(xlsx_files) == 1


# ── PubChem Query Tests ─────────────────────────────────────────────────

@pytest.mark.fast
def test_query_pubchem_success(validator, mocker):
    """Successful PubChem query returns CID and InChIKey."""
    mock_compound = MagicMock()
    mock_compound.cid = "2244"
    mock_compound.inchikey = "BSYNRYMUTXBXSQ"
    mocker.patch("pubchempy.get_compounds", return_value=[mock_compound])
    mocker.patch("src.validator.time.sleep")

    cid, inchikey = validator.query_pubchem_cid_and_inchikey("aspirin", "name")
    assert cid == "2244"
    assert inchikey == "BSYNRYMUTXBXSQ"


@pytest.mark.fast
def test_query_pubchem_empty_identifier(validator):
    """Empty identifier returns (None, None) without calling PubChem."""
    cid, inchikey = validator.query_pubchem_cid_and_inchikey(None, "name")
    assert cid is None
    assert inchikey is None


@pytest.mark.fast
def test_query_pubchem_exception(validator, mocker):
    """PubChem exception returns (None, None) gracefully."""
    mocker.patch("pubchempy.get_compounds", side_effect=Exception("timeout"))
    mocker.patch("src.validator.time.sleep")

    cid, inchikey = validator.query_pubchem_cid_and_inchikey("badquery", "name")
    assert cid is None
    assert inchikey is None


@pytest.mark.fast
def test_query_pubchem_bad_request_no_retry(validator, mocker):
    """BadRequest (HTTP 400) is treated as non-transient (no retry)."""
    mock_get = mocker.patch(
        "pubchempy.get_compounds",
        side_effect=Exception(
            "PubChem HTTP Error 400 PUGREST.BadRequest: Unable to standardize the given structure"
        ),
    )
    mocker.patch("src.validator.time.sleep")

    cid, inchikey = validator.query_pubchem_cid_and_inchikey("Cdd", "smiles")
    assert cid is None
    assert inchikey is None
    assert mock_get.call_count == 1


@pytest.mark.fast
def test_query_pubchem_no_results(validator, mocker):
    """PubChem returns empty list -> (None, None)."""
    mocker.patch("pubchempy.get_compounds", return_value=[])
    mocker.patch("src.validator.time.sleep")

    cid, inchikey = validator.query_pubchem_cid_and_inchikey("unknown", "name")
    assert cid is None
    assert inchikey is None


# ── get_smiles_from_pubchem ─────────────────────────────────────────────

@pytest.mark.fast
def test_get_smiles_success(validator, mocker):
    """Retrieve SMILES from CID successfully."""
    mock_compound = MagicMock()
    mock_compound.smiles = "CC(=O)O"
    mocker.patch("pubchempy.Compound.from_cid", return_value=mock_compound)
    mocker.patch("src.validator.time.sleep")

    result = validator.get_smiles_from_pubchem("2244")
    assert result == "CC(=O)O"


@pytest.mark.fast
def test_get_smiles_none_cid(validator):
    """None CID returns None without calling PubChem."""
    assert validator.get_smiles_from_pubchem(None) is None


@pytest.mark.fast
def test_get_smiles_exception(validator, mocker):
    """PubChem exception returns None gracefully."""
    mocker.patch("pubchempy.Compound.from_cid", side_effect=Exception("fail"))
    mocker.patch("src.validator.time.sleep")

    assert validator.get_smiles_from_pubchem("9999") is None


# ── retrieve_smiles ─────────────────────────────────────────────────────

@pytest.mark.fast
def test_retrieve_smiles_both_match(validator, mocker):
    """Both name and CAS resolve to same CID, SMILES retrieved."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", return_value=("123", "IK"))
    mocker.patch.object(validator, "get_smiles_from_pubchem", return_value="CC(=O)O")

    smiles, cid_name, cid_cas, reason = validator.retrieve_smiles(1, "Acetic acid", "64-19-7")
    assert smiles == "CC(=O)O"
    assert reason is None


@pytest.mark.fast
def test_retrieve_smiles_discordance(validator, mocker):
    """Name and CAS resolve to different CIDs."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "IK1"),  # by name
        ("456", "IK2"),  # by CAS
    ])

    smiles, cid_name, cid_cas, reason = validator.retrieve_smiles(1, "A", "64-19-7")
    assert smiles is None
    assert reason == "pubchem_discordance"


@pytest.mark.fast
def test_retrieve_smiles_not_found(validator, mocker):
    """Neither identifier found in PubChem."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    smiles, cid_name, cid_cas, reason = validator.retrieve_smiles(1, "Unknown", "00-00-0")
    assert smiles is None
    assert reason == "identifier_not_found"


@pytest.mark.fast
def test_retrieve_smiles_no_smiles_available(validator, mocker):
    """CIDs match but no SMILES available for that compound."""
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", return_value=("123", "IK"))
    mocker.patch.object(validator, "get_smiles_from_pubchem", return_value=None)

    smiles, cid_name, cid_cas, reason = validator.retrieve_smiles(1, "Complex", "12-34-5")
    assert smiles is None
    assert reason == "complex_chemical_no_smiles"


# ── Retrieval Mode in validate_chemical ─────────────────────────────────

@pytest.mark.fast
def test_validate_chemical_retrieval_mode_success(validator, mocker):
    """Retrieval mode: SMILES retrieved, then full validation passes."""
    validator.smiles_retrieval_mode = True

    mocker.patch.object(validator, "retrieve_smiles", return_value=("CC(=O)O", "123", "123", None))
    mocker.patch.object(validator, "query_pubchem_cid_and_inchikey", side_effect=[
        ("123", "INCHIKEY123"),  # by name
        ("123", "INCHIKEY123"),  # by CAS
        ("123", "INCHIKEY123"),  # by SMILES
    ])

    result = validator.validate_chemical(1, "Acetic acid", "64-19-7", None)
    assert result["status"] == "validated"
    assert result["smiles"] == "CC(=O)O"
    assert result["smiles_source"] == "pubchem"


@pytest.mark.fast
def test_validate_chemical_retrieval_mode_rejected(validator, mocker):
    """Retrieval mode: SMILES retrieval fails -> rejected."""
    validator.smiles_retrieval_mode = True

    mocker.patch.object(validator, "retrieve_smiles", return_value=(None, "123", "456", "pubchem_discordance"))

    result = validator.validate_chemical(1, "Test", "12-34-5", None)
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "pubchem_discordance"


# ── save_results with None output_folder ────────────────────────────────

@pytest.mark.fast
def test_save_results_cwd(tmp_path, mocker, monkeypatch):
    """save_results with output_folder=None saves to current working directory."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")
    monkeypatch.chdir(tmp_path)

    v = UnifiedChemicalValidator(str(csv_file), output_folder=None)
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))
    v.validate_csv()
    success = v.save_results()

    assert success is True
    xlsx_files = list(tmp_path.glob("validation_results_*.xlsx"))
    assert len(xlsx_files) == 1


# ── validate_csv with progress_callback ─────────────────────────────────

@pytest.mark.fast
def test_validate_csv_progress_callback(tmp_path, mocker):
    """validate_csv calls progress_callback during processing."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    v = UnifiedChemicalValidator(str(csv_file))
    mocker.patch.object(v, "query_pubchem_cid_and_inchikey", return_value=(None, None))

    messages = []
    v.validate_csv(progress_callback=messages.append)

    assert len(messages) > 0
    assert any("Reading file" in m for m in messages)


# ── validate_csv read error ─────────────────────────────────────────────

@pytest.mark.fast
def test_validate_csv_read_error(tmp_path):
    """validate_csv returns False when file cannot be read."""
    v = UnifiedChemicalValidator(str(tmp_path / "nonexistent.csv"))
    result = v.validate_csv()
    assert result is False
