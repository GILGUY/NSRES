"""Run the full verification gate (plan §8), in order, stopping at the first failure.

Usage: ``uv run python scripts/gate.py``

Every stage's command, exit code, duration, and count are printed and written to
``.gate/gate-report.json`` so a package's evidence section can quote real numbers.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from buildenv import DIST, ROOT, build_environment

PY = sys.executable


@dataclass
class StageResult:
    number: int
    name: str
    command: list[str]
    exit_code: int
    seconds: float
    count: str
    output_tail: str


def _uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("gate: the 'uv' executable is not on PATH (plan A-03)")
    return uv


def _count(name: str, output: str) -> str:
    patterns = {
        "format": r"(\d+ files? already formatted)",
        "lint": r"(All checks passed!)",
        "typecheck": r"(Success: no issues found in \d+ source files?)",
        "unit": r"(\d+ passed[^\n]*)",
        "integration": r"(\d+ passed[^\n]*)",
        "build": r"(Successfully built [^\n]+(?:\n[^\n]*Successfully built [^\n]+)?)",
        "package verify": r"COUNT: ([^\n]+)",
        "reproducibility": r"COUNT: ([^\n]+)",
        "end-to-end": r"COUNT: ([^\n]+)",
    }
    match = re.search(patterns[name], output)
    return " ".join(match.group(1).split()) if match else "(no count found)"


def _stages() -> list[tuple[str, list[str]]]:
    uv = _uv()
    return [
        ("format", [PY, "-m", "ruff", "format", "--check", "."]),
        ("lint", [PY, "-m", "ruff", "check", "."]),
        ("typecheck", [PY, "-m", "mypy", "--strict", "src", "tests", "scripts"]),
        ("unit", [PY, "-m", "pytest", "tests/unit"]),
        ("integration", [PY, "-m", "pytest", "tests/integration"]),
        ("build", [uv, "build", "--out-dir", str(DIST)]),
        ("package verify", [PY, "scripts/verify_package.py"]),
        ("reproducibility", [PY, "scripts/repro.py"]),
        ("end-to-end", [PY, "scripts/e2e.py"]),
    ]


def main() -> int:
    results: list[StageResult] = []
    for number, (name, command) in enumerate(_stages(), start=1):
        if name == "build" and DIST.exists():
            shutil.rmtree(DIST)
        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=build_environment(),
            capture_output=True,
            text=True,
            check=False,
        )
        seconds = round(time.monotonic() - started, 2)
        output = completed.stdout + completed.stderr
        result = StageResult(
            number=number,
            name=name,
            command=[Path(part).name if part in (PY, _uv()) else part for part in command],
            exit_code=completed.returncode,
            seconds=seconds,
            count=_count(name, output),
            output_tail="\n".join(output.strip().splitlines()[-15:]),
        )
        results.append(result)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"[{number}/9] {name:<16} {status}  {seconds:>6.2f}s  {result.count}")
        if completed.returncode != 0:
            print(output)
            break
    report_dir = ROOT / ".gate"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "gate-report.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8"
    )
    passed = len(results) == 9 and all(r.exit_code == 0 for r in results)
    print("GATE PASS: 9/9 stages" if passed else f"GATE FAIL at stage {len(results)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
