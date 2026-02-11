"""Unit tests for the main entry point router."""

# Standard library
import sys
from unittest.mock import patch

# Third-party
import pytest


@pytest.mark.fast
def test_main_routes_to_cli(monkeypatch):
    """With command-line args, main() calls cli.main()."""
    monkeypatch.setattr(sys, "argv", ["main", "input.csv"])

    with patch("src.cli.main") as mock_cli, patch("src.gui.main") as mock_gui:
        from src.main import main
        main()
        mock_cli.assert_called_once()
        mock_gui.assert_not_called()


@pytest.mark.fast
def test_main_routes_to_gui(monkeypatch):
    """With no args, main() calls gui.main()."""
    monkeypatch.setattr(sys, "argv", ["main"])

    with patch("src.cli.main") as mock_cli, patch("src.gui.main") as mock_gui:
        from src.main import main
        main()
        mock_gui.assert_called_once()
        mock_cli.assert_not_called()
