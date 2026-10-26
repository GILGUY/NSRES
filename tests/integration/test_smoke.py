"""WP-000 integration smoke test: the module entry point runs in a subprocess."""

import subprocess
import sys

import nsres


def test_module_entry_point_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "nsres", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"nsres {nsres.__version__}"
