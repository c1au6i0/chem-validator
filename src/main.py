"""
Entry point for the NCTP Chemical Validator.

Routes to GUI (no args) or CLI (with args) based on usage.
Used by PyInstaller as the executable entry point.
"""

# Standard library
import sys

# Local
from src import cli, gui


def main():
    """Route to CLI or GUI based on command-line arguments."""
    if len(sys.argv) > 1:
        cli.main()
    else:
        gui.main()


if __name__ == "__main__":
    main()
