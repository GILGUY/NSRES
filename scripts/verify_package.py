"""Gate stage 7: verify the built wheel and sdist, and that ``src/`` has no network imports.

The wheel and the sdist must contain exactly the expected files, no more and no fewer
(plan §8). No module under ``src/nsres`` may import a network library (plan A-13).
"""

from __future__ import annotations

import ast
import sys
import tarfile
import zipfile
from pathlib import Path

from buildenv import DIST, ROOT, SRC_PACKAGE, project_version, source_files

NETWORK_MODULES = frozenset(
    {
        "aiohttp",
        "asyncio",
        "ftplib",
        "http",
        "httpx",
        "imaplib",
        "nntplib",
        "poplib",
        "requests",
        "smtplib",
        "socket",
        "socketserver",
        "ssl",
        "telnetlib",
        "urllib",
        "urllib3",
        "webbrowser",
        "xmlrpc",
    }
)


def find_network_imports(package_root: Path) -> list[str]:
    """Return ``"path:line: module"`` for every import of a network module under the root."""
    hits: list[str] = []
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [(node.lineno, alias.name) for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imported = [(node.lineno, node.module)]
            else:
                continue
            for lineno, name in imported:
                if name.split(".")[0] in NETWORK_MODULES:
                    hits.append(f"{path}:{lineno}: {name}")
    return hits


def _diff(label: str, actual: set[str], expected: set[str]) -> list[str]:
    problems = [f"{label}: unexpected file {name}" for name in sorted(actual - expected)]
    problems += [f"{label}: missing file {name}" for name in sorted(expected - actual)]
    return problems


def main() -> int:
    version = project_version()
    shipped = [path.as_posix() for path in source_files()]
    wheel = DIST / f"nsres-{version}-py3-none-any.whl"
    sdist = DIST / f"nsres-{version}.tar.gz"
    problems: list[str] = []

    for artifact in (wheel, sdist):
        if not artifact.exists():
            problems.append(f"missing build artifact {artifact.relative_to(ROOT)}")
    if problems:
        print("\n".join(problems))
        return 1

    dist_info = f"nsres-{version}.dist-info"
    expected_wheel = set(shipped) | {
        f"{dist_info}/{name}" for name in ("METADATA", "WHEEL", "RECORD", "entry_points.txt")
    }
    with zipfile.ZipFile(wheel) as archive:
        actual_wheel = set(archive.namelist())
    problems += _diff("wheel", actual_wheel, expected_wheel)

    prefix = f"nsres-{version}"
    expected_sdist = {f"{prefix}/src/{name}" for name in shipped} | {
        f"{prefix}/{name}" for name in ("README.md", "pyproject.toml", "PKG-INFO", ".gitignore")
    }
    with tarfile.open(sdist) as archive:
        actual_sdist = {member.name for member in archive.getmembers() if member.isfile()}
    problems += _diff("sdist", actual_sdist, expected_sdist)

    network = find_network_imports(SRC_PACKAGE)
    problems += [f"network import (plan A-13): {hit}" for hit in network]

    modules = len(list(SRC_PACKAGE.rglob("*.py")))
    if problems:
        print("\n".join(problems))
        return 1
    print(
        f"COUNT: wheel {len(actual_wheel)} files, sdist {len(actual_sdist)} files, "
        f"{modules} modules scanned, 0 network imports"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
