"""Shared facts for the build-related gate scripts."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SRC_PACKAGE = ROOT / "src" / "nsres"

# Fixed build timestamp so wheel and sdist bytes do not depend on when they were built.
SOURCE_DATE_EPOCH = "1700000000"


def project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = data["project"]["version"]
    if not isinstance(version, str):
        raise TypeError("project.version in pyproject.toml must be a string")
    return version


def build_environment() -> dict[str, str]:
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    return env


def source_files() -> list[Path]:
    """Every file the package ships, relative to ``src/``: Python modules and ``py.typed``."""
    files = [
        path.relative_to(ROOT / "src")
        for path in SRC_PACKAGE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    return sorted(files)
