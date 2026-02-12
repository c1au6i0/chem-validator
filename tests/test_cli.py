"""Unit tests for the CLI interface."""

# Standard library
import sys
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from src import cli


@pytest.mark.fast
def test_cli_main_success(tmp_path, monkeypatch):
    """CLI exits 0 when validation passes."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    monkeypatch.setattr(sys, "argv", ["cli", str(csv_file)])

    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = True
    mock_validator.fatal_error = None

    with patch("src.cli.UnifiedChemicalValidator", return_value=mock_validator):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 0

    mock_validator.validate_csv.assert_called_once()
    mock_validator.save_results.assert_called_once()


@pytest.mark.fast
def test_cli_main_failure(tmp_path, monkeypatch):
    """CLI exits 1 when validation has rejections."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS,SMILES\nAcetone,67-64-1,CC(C)=O\n")

    monkeypatch.setattr(sys, "argv", ["cli", str(csv_file)])

    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = False
    mock_validator.fatal_error = None

    with patch("src.cli.UnifiedChemicalValidator", return_value=mock_validator):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 1


@pytest.mark.fast
def test_cli_main_file_not_found(tmp_path, monkeypatch):
    """CLI exits 1 when input file does not exist."""
    monkeypatch.setattr(sys, "argv", ["cli", str(tmp_path / "nonexistent.csv")])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 1


@pytest.mark.fast
def test_cli_main_output_folder_auto(tmp_path, monkeypatch):
    """CLI passes 'auto' when --output-folder flag used without value."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS\na,b\n")

    monkeypatch.setattr(sys, "argv", ["cli", str(csv_file), "--output-folder"])

    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = True
    mock_validator.fatal_error = None

    with patch("src.cli.UnifiedChemicalValidator", return_value=mock_validator) as mock_cls:
        with pytest.raises(SystemExit):
            cli.main()
        mock_cls.assert_called_once_with(str(csv_file), "auto")


@pytest.mark.fast
def test_cli_main_output_folder_custom(tmp_path, monkeypatch):
    """CLI passes custom path when --output-folder PATH provided."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS\na,b\n")
    custom = str(tmp_path / "my_output")

    monkeypatch.setattr(sys, "argv", ["cli", str(csv_file), "--output-folder", custom])

    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = True
    mock_validator.fatal_error = None

    with patch("src.cli.UnifiedChemicalValidator", return_value=mock_validator) as mock_cls:
        with pytest.raises(SystemExit):
            cli.main()
        mock_cls.assert_called_once_with(str(csv_file), custom)


@pytest.mark.fast
def test_cli_main_fatal_error_exits_2(tmp_path, monkeypatch):
    """CLI exits 2 on fatal input errors and does not save results."""
    csv_file = tmp_path / "input.csv"
    csv_file.write_text("Name,CAS\na,b\n")
    monkeypatch.setattr(sys, "argv", ["cli", str(csv_file)])

    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = False
    mock_validator.fatal_error = "Could not parse file"

    with patch("src.cli.UnifiedChemicalValidator", return_value=mock_validator):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 2

    mock_validator.save_results.assert_not_called()
