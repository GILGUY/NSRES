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

---

## WP-020 — Record store, statuses, typed gates, audit

**Gate:** G1 (records are trustworthy). **Spec:** NSRES-SPEC rev 126 (D-003). **Decisions
recorded before the code:** D-012 to D-016 and errata ERR-12, ERR-13 in `docs/DECISIONS.md`.

### What was implemented

| File | Contents |
| --- | --- |
| `src/nsres/store/log.py` | The two append-only JSON Lines logs (`log/records.jsonl`, one line per transaction; `log/audit.jsonl`, one hash-chained line per row), fsync per line, and verification: torn or non-JSON lines, consecutive transaction numbers, the chain, and exact row-to-audit coverage by `ref_hash` |
| `src/nsres/store/lifecycle.py` | The 11 rows of the §5.4 record-lifecycle table as data; `plan_decision` (pure); `acceptance_gate`; micro-fact detection; 22 named `Refusal` reasons |
| `src/nsres/store/store.py` | `Store` (create, open with verification, current / history / as-of / changed-between / valid-at reads, dependents, snapshot and digest); `GateConsole` (`decide`, `waive_finding`, `mark_detector_error`, `approve_resolutions`, `tag_release`, author `propose`); `EngineWriter` (`propose` typed `Literal[Status.PROPOSAL]`, `record_finding`, `mark_finding_resolved`, reconciliation version states). One `_apply` path serves writes and replay |
| `src/nsres/store/artifacts.py` | Content-addressed artifact store with hash re-check on read |
| `src/nsres/wcs/crosswalk.py` | The three §0.7 crosswalk tables as data (12 state rows, 8 gate rows, 8 decision rows), the three WCS vocabularies, and the pure `import_decision` |
| `src/nsres/domain/records.py`, `vocab.py` | D-015 extensions: `AuditRecord.tx/ref/ref_hash`, `GateRecord.retcon/successor`, `ModelVersion`, `ModelVersionState` (A-17 test against §5.4) |
| `tests/builders.py` | Record builders, an advancing UTC clock, a seeded UUIDv7 source, a marked isolation check |
| `tests/unit/test_lifecycle.py`, `test_store.py`, `test_wcs_crosswalk.py`; `tests/integration/test_engine_typing.py` | WP-020 tests |
| `docs/ENVIRONMENT.md` | E-6 (`UV_SYSTEM_CERTS`), E-7 (repository moved to `GILGUY/NSRES`) |

### Commands run

| Command | Result |
| --- | --- |
| `uv run --frozen ruff check src` (during the work) | N818 on the two exception names (renamed `StoreCorruptError`, `ArtifactCorruptError`, and the D-012 text with them); three E501 |
| `uv run --frozen mypy src` (during the work) | One error: the runtime guard in `EngineWriter.propose` was unreachable to mypy because the parameter is `Literal[Status.PROPOSAL]`. Kept the guard for untyped callers by comparing through an `object`-typed local |
| `uv run --frozen pytest tests/unit/test_lifecycle.py -x` (first run) | 1 failure: `reality-CANON-None-PROPOSAL-REVISE`. The planner refused (WRONG_GATE); the test oracle allowed it. **Verified by:** D-013 item 6 makes REVISE legal only where the gate could decide the record now, and the PROPOSAL gate cannot decide a CANON record. The oracle was wrong, not the planner; the same reading applied to REJECT on CANON records (only at the CANON gate). Oracle corrected; rerun 1,315 passed |
| `uv run --frozen pytest tests/unit/test_store.py` (first runs) | 3 failures, all test errors: a re-pointed fact still named CHR-004 in its object; SHIP at the SHIP gate on a PROPOSAL is NO_TRANSITION, not OUTCOME_NOT_AT_GATE (both cases now asserted); the busy store writes exactly 20 audit lines (assertion made exact) |
| `uv run --frozen mypy src tests scripts` (before closing) | 3 errors in tests: mypy narrowed `store.model_version.state` across calls (read through a function now); untyped lambdas in a dict (typed); a sample lookup by position broke when ModelVersion was appended (looked up by type) |
| `uv sync --frozen && uv run --frozen python scripts/gate.py` | **Exit 0. GATE PASS: 9/9 stages** (counts below) |

Gate stage counts from the passing run:

| Stage | Result |
| --- | --- |
| 1 format | 58 files already formatted |
| 2 lint | All checks passed |
| 3 typecheck | no issues found in 57 source files |
| 4 unit | 2,065 passed (lifecycle 1,315; WCS crosswalk 332; handles 120; records 77; schemas 70; vocabulary 69; store 41; canonical 29; uuid7 7; smoke 3; verify_package 2) |
| 5 integration | 4 passed (engine typing 2, vocabulary drift 1, smoke 1) |
| 6 build | sdist and wheel built |
| 7 package verify | wheel 38 files, sdist 38 files, 33 modules scanned, 0 network imports |
| 8 reproducibility | 2 builds, 2 artifacts, identical digests |
| 9 end-to-end | 2 flows passed against the installed wheel |

### Exit criteria

| Criterion | How it was met |
| --- | --- |
| Each row of the record-lifecycle table is a passing test, and every transition not in the table is rejected with a named reason | `test_store.py::test_row_01` to `test_row_11` run each §5.4 row end to end through the store (row 2 for all four acceptance gates; row 3 at all four gates with REJECT; row 9 including the PUBLISHED-canon RETCON; row 10 for ACCEPTED and CANON, blocked until dependents are re-pointed). `test_lifecycle.py` checks the 11 rules against the §5.4 table text, then runs `plan_decision` over all 1,305 combinations of 5 record kinds, every reachable status and tier, 5 gates, and 9 outcomes against an oracle written separately in the test; every combination the oracle forbids comes back `Refused` with a `Refusal` reason and a detail. `test_every_refusal_writes_nothing` shows refused requests leave both logs and the projection digest unchanged |
| Altering any one audit line makes chain verification fail at that line | `test_altering_any_audit_line_fails_verification_at_that_line`: for each of the 20 audit lines of a busy store, a copy with that one line edited reports exactly `audit line N: hash does not match its content` and `Store.open` refuses naming line N. A recomputed hash moves the failure to the next link (`prev_hash does not match line N`); an edited record-log row is reported as uncovered |
| Reloading from disk yields state deep-equal and hash-equal to the in-memory state | `test_reloading_yields_a_deep_equal_and_hash_equal_state` (snapshot equality, digest equality, identical audit trail, same model version); `test_a_reloaded_store_keeps_writing_a_valid_chain` writes after reload, verifies, and reloads again |
| An attempt through any engine API to set ACCEPTED or CANON fails the type check (a `mypy` test) and fails at runtime | `tests/integration/test_engine_typing.py` runs `mypy --strict` on a correct snippet (exit 0) and on one that passes `Status.ACCEPTED` and `status=Status.CANON` to `EngineWriter.propose` and calls `decide` and `set_tier` on it (exit 1, exactly those 4 errors). Runtime: `test_engine_writer_refuses_any_status_but_proposal_at_runtime` (NOT_PROPOSAL for an ACCEPTED request, a CANON record, and a PUBLISHED record) |
| Per OQ-10: waiving a BLOCKING finding is refused, never both cleared and uncapped | `test_a_blocking_finding_cannot_be_waived_and_stays_open` (BLOCKING_NOT_WAIVABLE; the finding stays OPEN; logs and digest unchanged). A MAJOR finding is waived only with an actor and reason, through an override gate record. A BLOCKING finding closes as RESOLVED (engine, inputs changed) or DETECTOR_ERROR (human) |
| OQ-8: each of the 11 WCS states, 8 gate types, and 8 decisions maps to exactly one crosswalk row; RAW or INTAKE import is refused; a WCS CANON `story_blueprint` imports per OQ-9 | `test_wcs_crosswalk.py`: vocabularies equal the §0.7 table columns and cover `modules.json`; each table row matches its spec row; every state maps to exactly one row for each of the 23 primary artifact types (CANON splits by type); each gate and decision has exactly one row; RAW and INTAKE refused for all 23 types citing REQ-12.2.2; `story_spine`, `story_blueprint`, `recut_proposal` at CANON import as ACCEPTED and structure-locked |

Also: `test_every_log_line_is_fsynced_before_the_write_returns` counts one `os.fsync` per
appended line (5 lines, 5 calls). Torn final lines and transactions missing their audit
lines are refused on open (D-012 item 4).

### Not done in WP-020 (by plan or by recorded decision)

- Crash repair: v0.1 detects a torn or incomplete transaction and refuses to open; it does
  not repair (D-012 item 4).
- The real isolation check comes from the rule registry (WP-030); the console requires one
  explicitly, with no default (D-013 item 7).
- Engine-proposed changes to ACCEPTED or CANON records (for example the autopsy window
  collapse) will use the gate's `revision=` path; the pending-proposal mechanism arrives with
  the autopsy package.
- Staleness marking (REQ-5.4.4) belongs to the packet pipeline; every `GateResult` returns
  the changed record so that package can react.
- No WCS reads or writes (D-016; plan Out list).

### Open issues carried forward

- Spec errata ERR-1 to ERR-13 await the batch patch proposal at the end of G1.
- E-2 and E-6 leave one environment claim unverified (whether `uv build` reached the
  network); not a blocker.

---

## WP-030 — Canon registry and rule registry

**Gate:** G1 (records are trustworthy). **Spec:** NSRES-SPEC rev 126 (D-003). **Decisions
recorded before the code:** D-017 to D-021 and errata ERR-14 to ERR-17 in `docs/DECISIONS.md`.

### What was implemented

| File | Contents |
| --- | --- |
| `src/nsres/canon/statements.py` | The D-017 structured statement forms (travel, distance, speed, timetable, daylight, disambiguate), `;`-separated statements with quote handling, and the per-work `Calendar` (minutes from epoch, Gregorian display) |
| `src/nsres/canon/metrics.py` | `TravelNetwork`: per-mode Floyd-Warshall closure; time-dependent Dijkstra earliest arrival over travel legs and daily timetable services (FIFO), with the canon sources of the route; closure gaps; speed breaches with UNCHECKABLE for missing distances or speed rules; `DaylightModel` (DAYLIGHT, DARK, or UNCHECKABLE for a date with no row) |
| `src/nsres/canon/identity.py` | Name and alias collisions, case-insensitive with whitespace collapsed, cleared only by a disambiguation covering the pair and the name |
| `src/nsres/canon/precedence.py` | `tier_of` and `resolve` (D-020) |
| `src/nsres/canon/registry.py` | `CanonRegistry`; the five L1 rules RC-L1-0, -2, -3A, -3B, -6 (D-018); `isolation_check` and `store_isolation_check` for the gate console (D-019) |
| `src/nsres/rules/registry.py`, `factory.py` | `RuleRecord` (the B.2 fields), `SeveritySpec` with TIGHTEN, detections, `Uncheckable`, `RuleRegistry` (refuses duplicates and foreign configs; content digest), `RuleRun` (PASS, FAIL, UNCHECKABLE, tightenings); `FindingFactory` (FND-R-nn handles, rendered message in `notes`, repair hints, the REQ-9.1.1 cap) |
| `src/nsres/domain/vocab.py` | `PrecedenceTier` and `precedence_rank` (A-17 test against §3.4 item 5) |
| `fixtures/harrow-house/canon.json`, `README.md` | The Harrow House canon (28 records) with provenance; illustrative handles and values marked |
| `tests/unit/test_canon.py`, `tests/unit/test_rules.py` | WP-030 tests |
| `docs/ENVIRONMENT.md` | E-7 amendment (the remote URL change did not persist) |

### Commands run

| Command | Result |
| --- | --- |
| `uv run --frozen mypy src` (during the work) | 7 errors: one variable name reused across branches of `parse_one` with different types, and one in `speed_breaches`; both renamed. Then the `_record` helper's `**extra` needed three `type: ignore`s; replaced with typed keyword parameters |
| `uv run --frozen ruff check src` (during the work) | RUF002 (an en dash in "Floyd-Warshall"), E501 |
| `uv run --frozen pytest tests/unit/test_canon.py` (first run) | 1 failure, a test-data error: the planted distance (8 km at 15 km/h, minimum 32 min) also made the fixture's own CAN-061 (25 min) a breach. Distance changed to 6 km (minimum 24 min); rerun 43 passed. The extra finding was correct behavior |
| `uv run --frozen mypy src tests scripts` (before closing) | 5 errors: tests reached vocabularies through `nsres.domain.records`, which does not re-export them; imported from `nsres.domain.vocab` |
| `git remote -v` | `https://github.com/GILGUY/nsres`, not the URL E-7 recorded; amendment appended to `docs/ENVIRONMENT.md` |
| `uv sync --frozen && uv run --frozen python scripts/gate.py` | **Exit 0. GATE PASS: 9/9 stages** (counts below) |

Gate stage counts from the passing run:

| Stage | Result |
| --- | --- |
| 1 format | 67 files already formatted |
| 2 lint | All checks passed |
| 3 typecheck | no issues found in 66 source files |
| 4 unit | 2,125 passed (lifecycle 1,315; WCS crosswalk 332; handles 120; records 77; vocabulary 71; schemas 70; canon 43; store 41; canonical 29; rules 15; uuid7 7; smoke 3; verify_package 2) |
| 5 integration | 4 passed |
| 6 build | sdist and wheel built |
| 7 package verify | wheel 45 files, sdist 45 files, 40 modules scanned, 0 network imports |
| 8 reproducibility | 2 builds, 2 artifacts, identical digests |
| 9 end-to-end | 2 flows passed against the installed wheel |

### Exit criteria

| Criterion | How it was met |
| --- | --- |
| A declared direct travel time longer than an indirect route raises the closure WARNING; one faster than the speed rule raises an ERROR | `test_a_direct_time_longer_than_the_closure_raises_the_closure_warning`: The Bell to Kellby station declared at 60 min against the 45 min path through Harrow House gives exactly one RC-L1-3A finding (MINOR, D-018) naming CAN-080, with the 60 and 45 in its message. `test_a_time_faster_than_the_speed_rule_raises_the_speed_error`: 5 min by carriage over 6 km at a 15 km/h speed rule (minimum 24 min) gives exactly one RC-L1-3B finding (BLOCKING) naming the travel, distance, and speed rules. The fixture canon alone produces neither; without distances the speed check reports UNCHECKABLE, not PASS |
| Two entities sharing an alias without a disambiguation record produce an identity-collision finding | `test_two_entities_sharing_an_alias_produce_an_identity_collision` (CHR-002 "the Inspector" and a second entity aliased "The  Inspector": one RC-L1-2 finding, MAJOR, both handles). A disambiguation record clears it, and covers only its own pair and name |
| A cross-tier conflict resolves to the higher tier; a same-tier conflict returns a gate-required finding and picks nothing | `test_a_cross_tier_conflict_resolves_to_the_higher_tier` (an ACCEPTED fact beats a DEFAULT canon rule; no finding). `test_a_same_tier_conflict_returns_a_gate_required_finding_and_picks_nothing` (two CANON facts: no winner, no loser, gate CANON, one RC-L1-6 finding naming both). Telling records go to their acceptance gate (STRUCTURE). All six tiers checked by `test_tiers_follow_section_3_4` |

Spec-anchored values also checked: the earliest arrival from York at 07:00 on 15 October is
09:30 through CAN-060 and CAN-061, as Appendix A.3's FND-R-01 states; the RES-0011 bridge
(fetched from The Bell at 07:05) arrives 07:25; first light 06:45 on 15 October makes 07:40
daylight and 22:40 on the 14th dark. The gate console refuses canon that breaks a speed rule
or is malformed (GUARD_FAILED naming the rule) and accepts canon with only a MINOR closure
finding (D-019).

### Not done in WP-030 (by plan or by recorded decision)

- L1 checks 1 (rule-rule unsatisfiability) and 4 (backstory against invariants): need the
  state engine; G2 reconciliation (D-018).
- Evaluating the free-text canon statements (invariants, prohibitions, defaults): later
  engines read `CanonRegistry.unparsed`.
- Movement checks (RC-08) use `TravelNetwork.earliest_arrival` in G2.

### Open issues carried forward

- Spec errata ERR-1 to ERR-17 await the batch patch proposal at the end of G1 (after WP-040).
- E-7: the remote URL reverts to `GILGUY/nsres` between turns (inferred cause unverified);
  pushes succeed either way.
