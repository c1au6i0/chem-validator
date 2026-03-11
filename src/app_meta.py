"""Application metadata shared by GUI and CLI."""

# Standard library
import tomllib
from pathlib import Path

APP_NAME = "Chem Validator"
LICENSE = "GPL-3.0-or-later"
REPO_URL = "https://github.com/c1au6i0/chem-validator"


def _read_version() -> str:
    """Read version from pixi.toml (single source of truth).

    Checks two locations to support both the dev layout (pixi.toml at project
    root, two levels above this file) and compiled executables where pixi.toml
    is bundled alongside the package directory.
    """
    for candidate in [
        Path(__file__).parent.parent / "pixi.toml",  # dev: project root
        Path(__file__).parent / "pixi.toml",          # compiled: bundled next to src/
    ]:
        try:
            with open(candidate, "rb") as f:
                return tomllib.load(f)["workspace"]["version"]
        except Exception:
            continue
    return "unknown"


__version__ = _read_version()
