# Implementation status (the cursor)

Authoritative for where work stopped. Read this first, then verify it: re-run the last
verified command and compare with the recorded result before trusting anything below.

```
Current gate:            G1 (records are trustworthy)
Current work package:    WP-010 Domain types, schemas, canonical JSON, identifiers
Current slice:           not started
Status:                  READY_TO_START
Last verified command:   uv sync --frozen && uv run --frozen python scripts/gate.py
Result:                  exit 0, "GATE PASS: 9/9 stages"; unit 5 passed, integration 1 passed,
                         typecheck 33 source files, wheel 27 files, sdist 27 files,
                         repro identical digests, e2e 1 flow
```

## Handoff note

- Why work stopped: WP-000 closed (commit on `main`, see TEST_EVIDENCE WP-000 amendment A1).
  Not a budget cutoff and not a blocker. The first session was interrupted after writing this
  cursor and before committing; the resumed session verified the cursor, ran the cold-resume
  test, and made the closing commit.
- Done and trustworthy: control records, contracts, the spec export (rev 126), the full
  nine-stage gate, reproducible wheel and sdist, and the network-import check (exercised by a
  planted-import test).
- Deliberately not done: any domain logic. Every module under `src/nsres/` is an empty package
  with a docstring naming its spec sections and work package.

## Open issues

- (none blocking)
- The spec's own pilot readiness is 0.80, INSUFFICIENT; the build proceeds under D-001. Not a
  build blocker.

## Next exact action

1. `uv sync --frozen && uv run --frozen python scripts/gate.py` (verify this cursor).
2. Start WP-010: read spec §0.3 (handles), §8.2 (packet fields), §10.2 (types), §17.7
   (packet group N), and Appendix B.3 and B.4 in `docs/spec/NSRES-SPEC.md`; then write
   `src/nsres/domain/` (vocabularies, canonical JSON, UUIDv7, handle patterns) and the packet
   and finding JSON Schemas with every `$defs` written out.

## Do not do next

- Do not start WP-020 before WP-010's exit criteria are evidenced in `docs/TEST_EVIDENCE.md`.
  (Plan §7 ordering; verified by reading the plan.)
- Do not import `docs/reference/confidence_oracle.py` from `src/` (plan A-12).

## Completed

| Package | Closed | Evidence |
| --- | --- | --- |
| WP-000 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-000 and amendment A1 |
