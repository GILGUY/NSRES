"""Gate stage 8: two clean builds must produce byte-identical wheels and sdists."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from buildenv import ROOT, build_environment, project_version


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(out_dir: Path) -> dict[str, str]:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("repro: the 'uv' executable is not on PATH")
    subprocess.run(
        [uv, "build", "--out-dir", str(out_dir)],
        cwd=ROOT,
        env=build_environment(),
        check=True,
        capture_output=True,
    )
    # uv also writes a one-line .gitignore into the output directory; only artifacts count.
    artifacts = [p for p in sorted(out_dir.iterdir()) if p.name.endswith((".whl", ".tar.gz"))]
    return {path.name: _sha256(path) for path in artifacts}


def main() -> int:
    version = project_version()
    expected = {f"nsres-{version}-py3-none-any.whl", f"nsres-{version}.tar.gz"}
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        digests_a = _build(Path(first))
        digests_b = _build(Path(second))
    if set(digests_a) != expected or set(digests_b) != expected:
        print(f"unexpected artifacts: {sorted(digests_a)} / {sorted(digests_b)}")
        return 1
    mismatched = [name for name in sorted(expected) if digests_a[name] != digests_b[name]]
    for name in sorted(expected):
        print(f"{name}  {digests_a[name]}  {digests_b[name]}")
    if mismatched:
        print(f"NOT REPRODUCIBLE: {', '.join(mismatched)}")
        return 1
    print(f"COUNT: 2 builds, {len(expected)} artifacts, identical digests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
