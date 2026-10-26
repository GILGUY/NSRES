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

---

## WP-010 — Domain types, schemas, canonical JSON, identifiers

**Gate:** G1 (records are trustworthy). **Spec:** NSRES-SPEC rev 126 (D-003).

### What was implemented

| File | Contents |
| --- | --- |
| `src/nsres/domain/vocab.py` | 47 closed vocabularies as `StrEnum` (A-17), `GATE_OUTCOMES` per gate (§0.7), `severity_rank` with an `assert_never` exhaustiveness check |
| `src/nsres/domain/handles.py` | One anchored pattern per §0.3 prefix (21) and per extended prefix (12: SUP, ANCHOR, CV, the §17.4 mechanics prefixes with RSV for resources, REL) |
| `src/nsres/domain/canonical.py` | Canonical JSON (sorted keys, compact, UTF-8, shortest round-trip numbers, integral floats as integers), `sha256:` content hashes, `packet_hash` and `public_hash` (D-006) |
| `src/nsres/domain/uuid7.py` | UUIDv7 with injected clock and seed; monotonic within a millisecond and across a backwards clock |
| `src/nsres/domain/records.py` | Frozen, keyword-only record types: every §10.2 type, the §3.3 Claim, Canon Rule and Relation, reveal and draft records, resolution records, the §17.4 mechanics records (with the Artifact as `embedded_mechanics` and the six effect-language operations), gate, audit, extraction and validation-report entries; construction-time validation; `to_json` and `from_json` (D-007 to D-011) |
| `src/nsres/domain/schemas.py` | Packet schema (B.3 with all 14 `$defs` written out) and finding schema (B.4 completed), built from the vocabularies and handle patterns (D-004); `packet_errors` and `finding_errors` return `(json_path, message)` |
| `fixtures/harrow-house/PKT-007-r3.example.json`, `README.md` | The §8.4 example completed, with hashes; provenance of every completion |
| `tests/spec_text.py` | Helpers that read the exported spec (TypeScript unions, YAML enums, tables, EBNF) |
| `tests/unit/test_{canonical,uuid7,handles,records,schemas,vocabulary_spec}.py`, `tests/integration/test_vocabulary_drift.py` | WP-010 tests |
| `scripts/e2e.py` | Second flow: the installed wheel validates the fixture packet and verifies its hashes, in isolated mode |
| `docs/DECISIONS.md` | D-004 to D-011, spec errata ERR-1 to ERR-11 |

### Commands run

| Command | Result |
| --- | --- |
| `uv run --frozen pytest tests/unit/test_vocabulary_spec.py` (first run) | 66 passed |
| `uv run --frozen pytest tests/integration/test_vocabulary_drift.py` (first version) | Exit 1: the child pytest ran with `-q -q` (addopts plus the test's own `-q`), so it printed no "2 failed" summary line. The child itself had failed exactly the two BeatType cases. Fixed by dropping the extra `-q`; rerun passed |
| `uv run --frozen ruff check src tests scripts` (during the work) | RUF001, RUF002 (ambiguous characters), UP047, I001, E501, SIM102; each fixed |
| `uv run --frozen mypy src/nsres/domain` (during the work) | One error: `functools.cache` rejected `type[T]` as unhashable; replaced with a dict cache |
| Fixture generation script (scratch, not committed) | Completed example validated with 0 errors on the first run; `packet_hash` `sha256:943e590a…`, `public_hash` `sha256:0187a8c9…` |
| `uv sync --frozen && uv run --frozen python scripts/gate.py` | **Exit 0. GATE PASS: 9/9 stages** (counts below) |
| Installed-wheel probe against a tampered packet copy (`pov.mode` set to UNRELIABLE, `sealed` removed) | Output `2 2` (2 schema errors, 2 hash problems), where the real fixture gives `0 0`. The e2e flow accepts only `0 0`, so it can fail |

Gate stage counts from the passing run:

| Stage | Result |
| --- | --- |
| 1 format | 48 files already formatted |
| 2 lint | All checks passed |
| 3 typecheck | no issues found in 47 source files |
| 4 unit | 374 passed (canonical 29, handles 120, records 75, schemas 70, vocabulary 68, uuid7 7, smoke 3, verify_package 2) |
| 5 integration | 2 passed (smoke 1, vocabulary drift 1) |
| 6 build | sdist and wheel built |
| 7 package verify | wheel 33 files, sdist 33 files, 28 modules scanned, 0 network imports |
| 8 reproducibility | 2 builds, 2 artifacts, identical digests (wheel `36468696…`, sdist `a55e7501…`) |
| 9 end-to-end | 2 flows passed against the installed wheel |

### Exit criteria

| Criterion | How it was met |
| --- | --- |
| Two objects equal up to key order serialize to identical bytes and hashes | `test_canonical.py::test_objects_equal_up_to_key_order_give_identical_bytes_and_hashes` (insertion orders asserted different first); also code-point key order, non-ASCII written raw, control characters escaped, integers and decimals, nested arrays, refusal of NaN, infinities, and non-string keys |
| The §8.4 example packet, completed with its omitted fields, validates | `test_schemas.py::test_completed_example_packet_validates`; `test_fixture_keeps_every_value_of_the_spec_example` reads the example from the spec text and checks every value is kept; `test_fixture_adds_only_the_fields_the_example_omits` |
| Removing `sealed` fails validation with the path named | `test_removing_sealed_fails_with_the_path_named`: exactly `[("$", "'sealed' is a required property")]` |
| An unknown field under `public` fails validation | `test_an_unknown_field_under_public_fails`: exactly one error at `$.public`; also 11 deeper levels and both schemas walked for open objects (none) |
| A BLOCKING finding with FOUND_BY_METADATA evidence is rejected | Schema: `test_a_blocking_finding_with_metadata_evidence_is_rejected` (error at `$.evidence`). Record constructor: `test_records.py::test_blocking_finding_needs_content_read_evidence`. Waived BLOCKING (REQ-9.1.2, OQ-10) rejected by both as well |
| UUIDv7 values sort in injected-time order | `test_uuid7.py::test_values_sort_in_injected_time_order` (200 values, shuffled then sorted, equal to generation order; embedded timestamps equal the injected times); also 5,000 values within one millisecond, and a clock that goes backwards |
| Every §0.3 example handle matches its prefix pattern, and each pattern rejects the other prefixes' examples | `test_handles.py`: the 21 prefixes and examples are parsed from the §0.3 table in the spec text; 53 examples in all (table, other spec examples, extended prefixes); each matches only its own prefix out of 33 |
| A-17 vocabulary test passes, and fails when `SUSTAIN` is removed from the beat-type enum in code only (exercised, then restored) | `test_vocabulary_spec.py`: all 47 vocabularies compared with their spec definitions (54 spec sources: §10.2 TypeScript, B.3, B.4, §10.9 and §17.4 EBNF, prose tables), the per-gate outcome table, and 11 schema enums. `tests/integration/test_vocabulary_drift.py` copies `src/`, confirms the copy is the module imported, runs the A-17 test on the unmodified copy (passes), removes `SUSTAIN` from `BeatType` only, reruns (exit 1, "2 failed": §10.2 Beat.type and B.3 beat.type, "only in spec ['SUSTAIN']"). The repository's own code is never edited, so restoring is automatic |

### Not done in WP-010 (by plan)

- Persistence (plan: out of scope). `from_json` exists because records need a lossless
  round trip, but nothing reads or writes the record log yet (WP-020).
- PK cross-field checks and conditions that need other records (D-004 rule 3): the packet
  package.
- Parsing the textual effect language (§10.9): `nsres.effects`.

### Open issues carried forward

- The spec errata ERR-1 to ERR-11 are recorded in `docs/DECISIONS.md` and proposed for one
  batch patch at the end of G1 (Patrick gates). Not blockers: each is resolved in code by a
  recorded decision.
- Two fixture completions are illustrative, not spec values (character states for CHR-004 and
  CHR-006; `narrative_pressure.target_after`); `fixtures/harrow-house/README.md` says so. No
  test treats them as expected engine output.
