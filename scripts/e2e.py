"""Gate stage 9: install the built wheel into a fresh environment and run the CLI flows.

WP-000 checks that the installed ``nsres --version`` equals the ``pyproject.toml`` version.
WP-010 adds that the installed package validates the completed §8.4 packet and verifies its
hashes, run in isolated mode so the checkout's ``src/`` cannot stand in for the wheel. Later
packages add the Appendix A and §17.8 flows against ``fixtures/golden/``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from buildenv import DIST, ROOT, project_version

PACKET_FIXTURE = ROOT / "fixtures" / "harrow-house" / "PKT-007-r3.example.json"

PACKET_PROBE = """
import json, sys
import nsres.domain.schemas as schemas
from nsres.domain.canonical import verify_packet_hashes
packet = json.load(open(sys.argv[1], encoding=\"utf-8\"))
print(schemas.__file__)
print(len(schemas.packet_errors(packet)), len(verify_packet_hashes(packet)))
"""


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


def check_packet_fixture(cli: Path, version: str) -> str | None:
    python = cli.parent / "python"
    result = subprocess.run(
        [str(python), "-I", "-c", PACKET_PROBE, str(PACKET_FIXTURE)],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = result.stdout.strip().splitlines()
    if result.returncode != 0 or len(lines) != 2:
        return f"packet fixture: probe failed ({result.returncode}): {result.stderr.strip()}"
    module, counts = lines
    if not module.startswith(str(cli.parent.parent)):
        return f"packet fixture: imported {module}, not the installed wheel"
    if counts != "0 0":
        return f"packet fixture: expected 0 schema errors and 0 hash problems, got {counts}"
    return None


def main() -> int:
    version = project_version()
    wheel = DIST / f"nsres-{version}-py3-none-any.whl"
    if not wheel.exists():
        print(f"missing wheel {wheel}; run the build stage first")
        return 1
    checks: list[Callable[[Path, str], str | None]] = [check_version, check_packet_fixture]
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
