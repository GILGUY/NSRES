"""WP-020 exit criterion: an engine API cannot request ACCEPTED, CANON, or PUBLISHED.

The type check is exercised by running ``mypy --strict`` on two snippets: one that uses the
engine write path correctly (must pass) and one that asks it for gated statuses or for gate
methods it does not have (must fail with exactly those errors). The runtime refusal is tested
in ``tests/unit/test_store.py``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HEADER = """
from nsres.domain.records import Entity
from nsres.domain.vocab import Status, Tier
from nsres.store import GateResult, Store


def engine(store: Store, record: Entity) -> list[GateResult]:
    writer = store.engine_writer("engine:extract")
"""

ALLOWED = (
    HEADER
    + """
    return [writer.propose(record), writer.propose(record, Status.PROPOSAL)]
"""
)

FORBIDDEN = (
    HEADER
    + """
    results = [
        writer.propose(record, Status.ACCEPTED),
        writer.propose(record, status=Status.CANON),
    ]
    writer.decide()
    writer.set_tier(Tier.PUBLISHED)
    return results
"""
)


def _mypy(tmp_path: Path, name: str, source: str) -> subprocess.CompletedProcess[str]:
    path = tmp_path / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--no-incremental",
            "--cache-dir",
            os.devnull,
            str(path),
        ],
        cwd=tmp_path,
        env={**os.environ, "MYPYPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_engine_path_type_checks_when_used_as_intended(tmp_path: Path) -> None:
    result = _mypy(tmp_path, "allowed", ALLOWED)
    assert result.returncode == 0, result.stdout + result.stderr


def test_asking_the_engine_path_for_gated_statuses_fails_the_type_check(tmp_path: Path) -> None:
    result = _mypy(tmp_path, "forbidden", FORBIDDEN)
    assert result.returncode == 1, result.stdout + result.stderr
    errors = [line for line in result.stdout.splitlines() if ": error:" in line]
    assert len(errors) == 4, result.stdout
    assert (
        sum('"Literal[Status.ACCEPTED]"' in line and "[arg-type]" in line for line in errors) == 1
    )
    assert sum('"Literal[Status.CANON]"' in line and "[arg-type]" in line for line in errors) == 1
    assert sum('has no attribute "decide"' in line for line in errors) == 1
    assert sum('has no attribute "set_tier"' in line for line in errors) == 1
