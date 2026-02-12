"""Unit tests for the GUI interface (headless-safe, fully mocked Tkinter)."""

# Standard library
import logging
from unittest.mock import MagicMock, patch, PropertyMock

# Third-party
import pytest


def _make_mock_tk():
    """Create a mock Tk root that behaves enough like real Tk."""
    root = MagicMock()
    root.after = MagicMock(side_effect=lambda _, fn: fn())
    return root


def _make_gui():
    """Create a ValidatorGUI with fully mocked Tkinter."""
    with patch("src.gui.tk") as mock_tk, \
         patch("src.gui.ttk"), \
         patch("src.gui.scrolledtext"):
        # Mock StringVar to behave like a simple container
        def make_string_var(**kwargs):
            sv = MagicMock()
            sv._value = kwargs.get("value", "")
            sv.get = MagicMock(side_effect=lambda: sv._value)
            sv.set = MagicMock(side_effect=lambda v: setattr(sv, "_value", v))
            return sv

        mock_tk.StringVar = make_string_var

        def make_bool_var(**kwargs):
            bv = MagicMock()
            bv._value = kwargs.get("value", False)
            bv.get = MagicMock(side_effect=lambda: bv._value)
            bv.set = MagicMock(side_effect=lambda v: setattr(bv, "_value", bool(v)))
            return bv

        mock_tk.BooleanVar = make_bool_var
        mock_tk.Tk.return_value = _make_mock_tk()
        mock_tk.BOTH = "both"
        mock_tk.X = "x"
        mock_tk.W = "w"
        mock_tk.LEFT = "left"
        mock_tk.RIGHT = "right"
        mock_tk.END = "end"
        mock_tk.BOTTOM = "bottom"
        mock_tk.SUNKEN = "sunken"

        from src.gui import ValidatorGUI
        root = mock_tk.Tk.return_value
        app = ValidatorGUI(root)
        return app


@pytest.mark.fast
def test_gui_init():
    """ValidatorGUI initializes with correct defaults."""
    app = _make_gui()
    assert app.file_path.get() == ""
    assert app.output_mode.get() == "current"
    assert app.is_validating is False


@pytest.mark.fast
def test_gui_toggle_output_custom():
    """Custom mode enables custom entry."""
    app = _make_gui()
    app.output_mode.set("custom")
    app.toggle_output_entry()
    app.custom_entry.config.assert_called_with(state="normal")


@pytest.mark.fast
def test_gui_toggle_output_current():
    """Current mode disables custom entry."""
    app = _make_gui()
    app.output_mode.set("current")
    app.toggle_output_entry()
    app.custom_entry.config.assert_called_with(state="disabled")


@pytest.mark.fast
def test_gui_toggle_output_auto():
    """Auto mode disables custom entry."""
    app = _make_gui()
    app.output_mode.set("auto")
    app.toggle_output_entry()
    app.custom_entry.config.assert_called_with(state="disabled")


@pytest.mark.fast
def test_gui_log():
    """log() schedules text insertion via root.after."""
    app = _make_gui()
    app.log("Test message")
    app.root.after.assert_called()


@pytest.mark.fast
def test_gui_update_status():
    """update_status() schedules status update via root.after."""
    app = _make_gui()
    app.update_status("Processing...")
    app.root.after.assert_called()


@pytest.mark.fast
def test_gui_start_validation_no_file():
    """start_validation_thread shows error when no file selected."""
    app = _make_gui()
    app.file_path.set("")

    with patch("src.gui.messagebox") as mock_mb:
        app.start_validation_thread()
        mock_mb.showerror.assert_called_once()
    assert app.is_validating is False


@pytest.mark.fast
def test_gui_start_validation_already_running():
    """start_validation_thread returns early if already validating."""
    app = _make_gui()
    app.is_validating = True
    app.file_path.set("somefile.csv")
    app.start_validation_thread()
    assert app.is_validating is True


@pytest.mark.fast
def test_gui_start_validation_custom_no_path():
    """start_validation_thread errors when custom mode but no path."""
    app = _make_gui()
    app.file_path.set("somefile.csv")
    app.output_mode.set("custom")
    app.custom_output_path.set("")

    with patch("src.gui.messagebox") as mock_mb:
        app.start_validation_thread()
        mock_mb.showerror.assert_called_once()
    assert app.is_validating is False


@pytest.mark.fast
def test_gui_browse_file():
    """browse_file sets file_path from dialog."""
    app = _make_gui()
    with patch("src.gui.filedialog.askopenfilename", return_value="/tmp/test.csv"):
        app.browse_file()
    assert app.file_path.get() == "/tmp/test.csv"


@pytest.mark.fast
def test_gui_browse_file_cancel():
    """browse_file does not change path when dialog cancelled."""
    app = _make_gui()
    app.file_path.set("original.csv")
    with patch("src.gui.filedialog.askopenfilename", return_value=""):
        app.browse_file()
    assert app.file_path.get() == "original.csv"


@pytest.mark.fast
def test_gui_browse_output_folder():
    """browse_output_folder sets custom_output_path."""
    app = _make_gui()
    with patch("src.gui.filedialog.askdirectory", return_value="/tmp/output"):
        app.browse_output_folder()
    assert app.custom_output_path.get() == "/tmp/output"


@pytest.mark.fast
def test_gui_browse_output_folder_cancel():
    """browse_output_folder does not change path when cancelled."""
    app = _make_gui()
    app.custom_output_path.set("original")
    with patch("src.gui.filedialog.askdirectory", return_value=""):
        app.browse_output_folder()
    assert app.custom_output_path.get() == "original"


@pytest.mark.fast
def test_gui_start_validation_auto_mode():
    """start_validation_thread passes 'auto' in auto mode."""
    app = _make_gui()
    app.file_path.set("somefile.csv")
    app.output_mode.set("auto")

    with patch("threading.Thread") as mock_thread:
        app.start_validation_thread()
        mock_thread.assert_called_once()
        args = mock_thread.call_args
        assert args.kwargs["args"] == ("somefile.csv", "auto", False)


@pytest.mark.fast
def test_gui_start_validation_current_mode(tmp_path):
    """start_validation_thread passes input folder in current mode."""
    app = _make_gui()
    app.file_path.set(str(tmp_path / "somefile.csv"))
    app.output_mode.set("current")

    with patch("threading.Thread") as mock_thread:
        app.start_validation_thread()
        mock_thread.assert_called_once()
        args = mock_thread.call_args
        assert args.kwargs["args"] == (str(tmp_path / "somefile.csv"), str(tmp_path), False)


@pytest.mark.fast
def test_gui_run_validation_success():
    """run_validation calls validator and handles success."""
    app = _make_gui()
    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = True

    with patch("src.gui.UnifiedChemicalValidator", return_value=mock_validator), \
         patch("src.gui.messagebox"):
        app.run_validation("input.csv", None, False)

    mock_validator.validate_csv.assert_called_once()
    mock_validator.save_results.assert_called_once()
    assert app.is_validating is False


@pytest.mark.fast
def test_gui_run_validation_failure():
    """run_validation handles validation with rejections."""
    app = _make_gui()
    mock_validator = MagicMock()
    mock_validator.validate_csv.return_value = False

    with patch("src.gui.UnifiedChemicalValidator", return_value=mock_validator), \
         patch("src.gui.messagebox"):
        app.run_validation("input.csv", None, False)

    assert app.is_validating is False


@pytest.mark.fast
def test_gui_run_validation_exception():
    """run_validation handles exceptions gracefully."""
    app = _make_gui()

    with patch("src.gui.UnifiedChemicalValidator", side_effect=Exception("boom")), \
         patch("src.gui.messagebox"):
        app.run_validation("input.csv", None, False)

    assert app.is_validating is False


@pytest.mark.fast
def test_gui_main_function():
    """gui.main() creates root and starts mainloop."""
    with patch("src.gui.tk.Tk") as mock_tk_cls:
        mock_root = MagicMock()
        mock_tk_cls.return_value = mock_root

        with patch("src.gui.ValidatorGUI"):
            from src.gui import main
            main()
            mock_root.mainloop.assert_called_once()


@pytest.mark.fast
def test_gui_start_validation_custom_with_path():
    """start_validation_thread passes custom path in custom mode."""
    app = _make_gui()
    app.file_path.set("somefile.csv")
    app.output_mode.set("custom")
    app.custom_output_path.set("/my/custom/path")

    with patch("threading.Thread") as mock_thread:
        app.start_validation_thread()
        mock_thread.assert_called_once()
        args = mock_thread.call_args
        assert args.kwargs["args"] == ("somefile.csv", "/my/custom/path", False)


@pytest.mark.fast
def test_gui_about_dialog():
    """About dialog shows app metadata."""
    app = _make_gui()
    with patch("src.gui.messagebox.showinfo") as mock_show:
        app.show_about()
        mock_show.assert_called_once()
        _title, msg = mock_show.call_args.args
        assert "License: MIT" in msg
        assert "https://github.com/c1au6i0/chem-validator" in msg
        assert "Copyright" not in msg
