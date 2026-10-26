"""WP-010 exit criterion: the A-17 check fails when a vocabulary drifts in code only.

A copy of ``src/`` has ``SUSTAIN`` removed from the beat-type enum, and the unit test
``test_vocabulary_spec.py`` is run against the copy in a subprocess. The unmodified copy is
run the same way first, so the failure is shown to come from the edit and nothing else.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUSTAIN_LINE = '    SUSTAIN = "SUSTAIN"\n'


def _run_vocabulary_test(src: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": f"{src}{os.pathsep}{ROOT}"}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "tests/unit/test_vocabulary_spec.py",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_src(destination: Path) -> Path:
    src = destination / "src"
    shutil.copytree(ROOT / "src", src, ignore=shutil.ignore_patterns("__pycache__"))
    return src


def _imported_from(src: Path) -> str:
    probe = subprocess.run(
        [sys.executable, "-c", "import nsres.domain.vocab as v; print(v.__file__)"],
        env={**os.environ, "PYTHONPATH": str(src)},
        capture_output=True,
        text=True,
        check=True,
    )
    return probe.stdout.strip()


def test_removing_sustain_in_code_fails_the_vocabulary_check(tmp_path: Path) -> None:
    src = _copy_src(tmp_path)
    assert _imported_from(src).startswith(str(src)), "the copy is not the module under test"

    control = _run_vocabulary_test(src)
    assert control.returncode == 0, control.stdout + control.stderr

    vocab_file = src / "nsres" / "domain" / "vocab.py"
    original = vocab_file.read_text(encoding="utf-8")
    start = original.index("class BeatType(StrEnum):")
    end = original.index("\nclass ", start + 1)
    beat_type = original[start:end]
    assert beat_type.count(SUSTAIN_LINE) == 1
    edited = original[:start] + beat_type.replace(SUSTAIN_LINE, "") + original[end:]
    vocab_file.write_text(edited, encoding="utf-8")

    drifted = _run_vocabulary_test(src)
    assert drifted.returncode == 1, drifted.stdout + drifted.stderr
    assert "BeatType drifted from §10.2 Beat.type" in drifted.stdout
    assert "BeatType drifted from B.3 beat.type" in drifted.stdout
    assert "only in spec ['SUSTAIN']" in drifted.stdout
    assert "2 failed" in drifted.stdout, drifted.stdout
