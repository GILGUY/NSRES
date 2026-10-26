# Test evidence

Append-only. Each package gets one section: what was implemented, every command run with its
actual result, and how each exit criterion was met. Earlier sections are never edited; a
correction is appended as an amendment that names what it corrects.

---

## WP-000 — Control records, contracts, scaffold, full gate

**Date:** 2026-10-25. **Commit:** the WP-000 commit on `main` (this section ships in it).

### Implemented

- Control records: `docs/IMPLEMENTATION_STATUS.md`, `docs/TEST_EVIDENCE.md`,
  `docs/DECISIONS.md` (A-01 to A-17, D-001 to D-003), `docs/INVARIANTS.md` (I-01 to I-14),
  `docs/PROTOCOL.md` (P-1 to P-9), `docs/ENVIRONMENT.md` (E-1 to E-5).
- Contracts registered from plan v0.2.1: `docs/contracts/SCOPE.md`, `ARCHITECTURE.md`,
  `DOMAIN.md`; the plan itself at `docs/IMPLEMENTATION_PLAN.md`.
- Spec exported from the controlling doc at rev 126 to `docs/spec/NSRES-SPEC.md` with
  provenance in `docs/spec/SOURCE.md`. Reference material in `docs/reference/` (plan 0.1.0,
  the handoff disposition ledger, the v0.1.1 readiness vector, the confidence oracle).
- WCS contract fixtures: `fixtures/wcs/modules.json` (sha256 `f5516638…854c`) and
  `module_digest.json`.
- Scaffold: `pyproject.toml` (hatchling 1.32.4 pinned; ruff, mypy, pytest configuration),
  `uv.lock`, `.gitignore`, the `src/nsres/` package with `py.typed`, 18 empty module packages
  matching the domain lock, and a CLI that implements `--version` and help only.
- Gate: `scripts/gate.py` (nine stages), `scripts/verify_package.py`, `scripts/repro.py`,
  `scripts/e2e.py`, with shared facts in `scripts/buildenv.py`.
- Tests: `tests/unit/test_smoke.py` (3), `tests/unit/test_verify_package.py` (2),
  `tests/integration/test_smoke.py` (1).

### Commands and results

| Command | Result |
| --- | --- |
| `git clone --depth 1 https://github.com/GILGUY/nsres /home/claude/nsres` | Exit 0. HEAD `ac0bab1 Initial commit`, one file `README.md` (7 bytes) |
| `uv lock` | Exit 0. Resolved 20 packages |
| `uv sync --frozen` | Exit 0 |
| `uv run --frozen nsres --version` | `nsres 0.1.0.dev0` |
| `uv run --frozen python scripts/gate.py` (first run) | Exit 1. Stage 7 failed: "sdist: unexpected file nsres-0.1.0.dev0/.gitignore" (ENVIRONMENT E-4) |
| same (second run) | Exit 1. Stage 8 failed: uv's output-directory `.gitignore` counted as an artifact (ENVIRONMENT E-3) |
| same (third run, after both fixes) | **Exit 0. GATE PASS: 9/9 stages** (counts below) |
| Two builds with `SOURCE_DATE_EPOCH` 1700000000 and 1800000000 | Wheel digests `29416b12…` and `c8491746…`; sdist digests `9facb991…` and `a0a6d746…`. Different timestamps give different bytes, so the stage-8 digest comparison is able to fail |

Gate stage counts from the passing run:

| Stage | Result |
| --- | --- |
| 1 format | 34 files already formatted |
| 2 lint | All checks passed |
| 3 typecheck | no issues found in 33 source files |
| 4 unit | 5 passed |
| 5 integration | 1 passed |
| 6 build | sdist and wheel built |
| 7 package verify | wheel 27 files, sdist 27 files, 22 modules scanned, 0 network imports |
| 8 reproducibility | 2 builds, 2 artifacts, identical digests |
| 9 end-to-end | 1 flow passed against the installed wheel |

### Exit criteria

| Criterion | How it was met |
| --- | --- |
| `uv run python scripts/gate.py` exits 0 and the log shows all nine stages, each with its own count | Third run above; `.gate/gate-report.json` holds the per-stage record |
| `scripts/repro.py` performs two clean builds with a fixed `SOURCE_DATE_EPOCH` and reports identical wheel digests | Stage 8 PASS; the two-epoch experiment shows the comparison is sensitive |
| `scripts/e2e.py` installs the built wheel into a fresh environment and `nsres --version` equals the `pyproject.toml` version | Stage 9 PASS (fresh `uv venv`, wheel installed with `uv pip install`) |
| `scripts/verify_package.py` fails on a planted `import urllib` under the package root | `tests/unit/test_verify_package.py::test_planted_network_imports_are_found` plants `import urllib.request` and `from http import client` in a temporary package and asserts both are found; the real package scan returns none |
| Cold-resume test: reading only the cursor, its last verified command reproduces its recorded result | Recorded below, after the cursor was written |

### Cold-resume test

See the amendment line appended after the cursor was written.

#### Amendment A1 to WP-000 — cold-resume test, and the closing commit (resumed session, 2026-10-25)

**What this corrects.** The cursor written at 20:31 recorded WP-000 as closed, and the section
above says "the WP-000 commit on `main` (this section ships in it)". At that moment the closing
ritual was incomplete: nothing had been committed or pushed, and the cold-resume line promised
above had not been appended. The session was interrupted after writing the cursor.
**Verified by:** in the resumed session, `git status` showed every WP-000 file untracked and
`git log` showed only `ac0bab1 Initial commit`; `git reflog` showed only the clone. The work
itself was intact (file timestamps 20:23 to 20:31; no other Claude session was running, per the
agent list).

**Cold-resume test.** Read only `docs/IMPLEMENTATION_STATUS.md`, then ran its last verified
command:

| Command | Result |
| --- | --- |
| `uv sync --frozen` | Exit 0 ("Checked 19 packages") |
| `uv run --frozen python scripts/gate.py` | **Exit 0. GATE PASS: 9/9 stages.** format 34 files; lint all checks passed; typecheck 33 source files; unit 5 passed; integration 1 passed; build sdist and wheel; package verify wheel 27 files, sdist 27 files, 22 modules, 0 network imports; repro 2 builds identical digests; e2e 1 flow |

The recorded result was reproduced exactly, so the cursor alone was sufficient to resume.

**Closing ritual completed here.** This amendment, the corrected cursor, and all WP-000 files are
committed together as the WP-000 commit and pushed to `origin/main`. WP-000 counts as closed
from that commit, not from 20:31.
