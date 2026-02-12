"""Build standalone executables with Nuitka.

Produces consistent output paths for CI artifacts:
- Linux:   dist/chem-validator
- Windows: dist/chem-validator.exe
- macOS:   dist/chem-validator.app
"""

# Standard library
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    # Nuitka runs helper Python processes that can trigger the new Python 3.13
    # REPL (pyrepl) import, which may try to dlopen ncurses. Some environments
    # ship a linker script at libncursesw.so which ctypes cannot load.
    # Force the basic REPL to avoid importing _pyrepl._minimal_curses.
    env.setdefault("PYTHON_BASIC_REPL", "1")

    renamed_ncurses = None
    if sys.platform.startswith("linux"):
        # Work around conda-forge providing libncursesw.so as a linker script
        # (INPUT(...)) which ctypes cannot dlopen. Python 3.13's pyrepl can
        # import _pyrepl._minimal_curses during Nuitka import detection.
        env_lib = Path(sys.prefix) / "lib"
        script_path = env_lib / "libncursesw.so"
        target = None
        for candidate in sorted(env_lib.glob("libncursesw.so.6*")):
            if candidate.is_file() and candidate.stat().st_size > 10_000:
                target = candidate
                break
        if script_path.exists() and target is not None:
            try:
                header = script_path.read_text(errors="ignore").strip()
            except Exception:
                header = ""
            if header.startswith("INPUT("):
                # Prevent ctypes from trying to dlopen the linker script.
                # Rename it out of the way for the duration of the build.
                renamed_ncurses = script_path.with_suffix(".so.linkerscript")
                if renamed_ncurses.exists():
                    renamed_ncurses.unlink()
                script_path.rename(renamed_ncurses)

    try:
        subprocess.check_call(cmd, env=env)
    finally:
        if renamed_ncurses is not None:
            try:
                script_path = Path(sys.prefix) / "lib" / "libncursesw.so"
                if script_path.exists():
                    script_path.unlink()
                renamed_ncurses.rename(script_path)
            except Exception:
                pass


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    dist_dir = root / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    entry = root / "src" / "main.py"
    if not entry.exists():
        raise SystemExit(f"Entry point not found: {entry}")

    base_cmd = [
        sys.executable,
        "-m",
        "nuitka",
        str(entry),
        "--assume-yes-for-downloads",
        "--standalone",
        "--nofollow-import-to=pytest,pytest_cov,pytest_mock",
        "--output-dir=dist",
        "--enable-plugin=tk-inter",
        "--include-data-file=LICENSE=LICENSE",
    ]

    if sys.platform.startswith("win"):
        cmd = base_cmd + [
            "--onefile",
            "--windows-console-mode=disable",
            "--output-filename=chem-validator.exe",
        ]
        _run(cmd)
        return

    if sys.platform == "darwin":
        # Build a GUI .app bundle.
        cmd = base_cmd + [
            "--macos-create-app-bundle",
            "--macos-app-name=chem-validator",
            "--output-filename=chem-validator",
        ]
        _run(cmd)

        # Normalize output path for CI.
        apps = list((root / "dist").glob("*.app"))
        if len(apps) == 1 and apps[0].name != "chem-validator.app":
            apps[0].rename(root / "dist" / "chem-validator.app")
        return

    # Linux
    cmd = base_cmd + [
        "--onefile",
        "--output-filename=chem-validator",
    ]
    _run(cmd)


if __name__ == "__main__":
    main()
