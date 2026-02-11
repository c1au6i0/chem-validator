"""Executable entry point.

Routes to GUI (no args) or CLI (with args) based on usage.
Used by PyInstaller as the executable entry point.
"""

# Standard library
import sys

def main():
    """Route to CLI or GUI based on command-line arguments."""
    if len(sys.argv) > 1:
        # Import only when needed to reduce startup time.
        from src import cli

        cli.main()
    else:
        from src import gui

        gui.main()


if __name__ == "__main__":
    main()
