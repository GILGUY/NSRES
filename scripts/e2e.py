"""Gate stage 9: install the built wheel into a fresh environment and run the CLI flows.

WP-000 checks only that the installed ``nsres --version`` equals the ``pyproject.toml``
version. Later packages add the Appendix A and §17.8 flows against ``fixtures/golden/``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from buildenv import DIST, project_version


def _install(venv: Path, wheel: Path) -> Path:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("e2e: the 'uv' executable is not on PATH")
    subprocess.run(
        [uv, "venv", "--quiet", "--python", sys.executable, str(venv)],
        check=True,
        capture_output=True,
    )
    python = venv / "bin" / "python"
    subprocess.run(
        [uv, "pip", "install", "--quiet", "--python", str(python), str(wheel)],
        check=True,
        capture_output=True,
    )
    return venv / "bin" / "nsres"


def check_version(cli: Path, version: str) -> str | None:
    result = subprocess.run([str(cli), "--version"], capture_output=True, text=True, check=False)
    expected = f"nsres {version}"
    if result.returncode != 0 or result.stdout.strip() != expected:
        return f"--version: expected {expected!r}, got {result.stdout.strip()!r} ({result.stderr})"
    return None


def main() -> int:
    version = project_version()
    wheel = DIST / f"nsres-{version}-py3-none-any.whl"
    if not wheel.exists():
        print(f"missing wheel {wheel}; run the build stage first")
        return 1
    checks: list[Callable[[Path, str], str | None]] = [check_version]
    with tempfile.TemporaryDirectory() as tmp:
        cli = _install(Path(tmp) / "venv", wheel)
        failures = [message for check in checks if (message := check(cli, version)) is not None]
    if failures:
        print("\n".join(failures))
        return 1
    print(f"COUNT: {len(checks)} flows passed against the installed wheel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
