# Implementation status (the cursor)

Authoritative for where work stopped. Read this first, then verify it: re-run the last
verified command and compare with the recorded result before trusting anything below.

```
Current gate:            G1 (records are trustworthy)
Current work package:    WP-020 Record store, statuses, typed gates, audit
Current slice:           not started
Status:                  READY_TO_START
Last verified command:   uv sync --frozen && uv run --frozen python scripts/gate.py
Result:                  exit 0, "GATE PASS: 9/9 stages"; format 48 files, typecheck 47 source
                         files, unit 374 passed, integration 2 passed, wheel 33 files,
                         sdist 33 files, 28 modules 0 network imports, repro identical
                         digests, e2e 2 flows
```

## Handoff note

- Why work stopped: WP-010 closed (TEST_EVIDENCE § WP-010; commit on `main`). Not a budget
  cutoff and not a blocker.
- Done and trustworthy: everything in WP-000, plus `src/nsres/domain/` — 47 closed
  vocabularies tested against the spec text, handle patterns for all 33 prefixes, canonical
  JSON and packet hashes, UUIDv7, every record type with a lossless JSON round trip, and the
  packet and finding JSON Schemas. The completed §8.4 packet is
  `fixtures/harrow-house/PKT-007-r3.example.json`.
- Decisions to know before touching records or schemas: D-004 (schema construction rule),
  D-005 (RSV- for resources), D-006 (hash domain), D-007 (snake_case JSON, integer minutes and
  revisions), D-008 (findings have no record status), D-009 (gate, audit, extraction, and
  validation entries are not gated records), D-010 (REL- for relations), D-011 (artifact and
  mechanics effects).
- Deliberately not done: persistence (WP-020), PK cross-field checks (packet package),
  effect-language parsing (`nsres.effects`).

## Open issues

- Spec errata ERR-1 to ERR-11 (`docs/DECISIONS.md`) await one batch patch proposal at the end
  of G1, for Patrick to gate. Each is resolved in code by a recorded decision, so none blocks
  WP-020. (Verified by: every erratum names its resolving decision, and the WP-010 tests pass
  under those decisions.)
- Two completions in the PKT-007-r3 fixture are illustrative, not spec values
  (`fixtures/harrow-house/README.md`). No later package may use them as expected outputs.
- The spec's own pilot readiness is 0.80, INSUFFICIENT; the build proceeds under D-001. Not a
  build blocker.

## Next exact action

1. `uv sync --frozen && uv run --frozen python scripts/gate.py` (verify this cursor).
2. Start WP-020: read spec §0.7 (statuses, gates, micro-fact codes, WCS crosswalk), §5.4
   (record lifecycle table and REQ-5.4.1 to 5.4.4), §10.4 and §10.5 (storage, bitemporal
   rows), §11.5 (REQ-11.5.1 overrides), REQ-9.1.2, and §12.2 (WCS import rules) in
   `docs/spec/NSRES-SPEC.md`, and plan WP-020 in `docs/IMPLEMENTATION_PLAN.md`. Then build
   `src/nsres/store/` (append-only JSONL log with fsync, revisions, bitemporal queries, the
   §5.4 state machine, the gate API, the hash-chained audit log, the waiver rule) and
   `src/nsres/wcs/` (crosswalk tables as data, import rules), reusing
   `nsres.domain.records` (`GateRecord`, `AuditRecord`, `to_json`, `from_json`).

## Do not do next

- Do not start WP-030 before WP-020's exit criteria are evidenced in `docs/TEST_EVIDENCE.md`.
  (Plan §7 ordering; verified by reading the plan.)
- Do not import `docs/reference/confidence_oracle.py` from `src/` (plan A-12).
- Do not read from or write to WCS folders; the crosswalk is data only (plan WP-020 out of
  scope; OQ-8).
- Do not change a schema or record shape without first amending D-004 or D-007 in
  `docs/DECISIONS.md` (build discipline: contracts change before code).

## Completed

| Package | Closed | Evidence |
| --- | --- | --- |
| WP-000 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-000 and amendment A1 |
| WP-010 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-010 |
