# Implementation status (the cursor)

Authoritative for where work stopped. Read this first, then verify it: re-run the last
verified command and compare with the recorded result before trusting anything below.

```
Current gate:            G1 (records are trustworthy)
Current work package:    WP-040 Confidence engine
Current slice:           not started
Status:                  READY_TO_START
Last verified command:   uv sync --frozen && uv run --frozen python scripts/gate.py
Result:                  exit 0, "GATE PASS: 9/9 stages"; format 67 files, typecheck 66 source
                         files, unit 2125 passed, integration 4 passed, wheel 45 files,
                         sdist 45 files, 40 modules 0 network imports, repro identical
                         digests, e2e 2 flows
```

Environment note: run uv with `UV_SYSTEM_CERTS=1` and `UV_NATIVE_TLS` unset to avoid the
deprecation warning (`docs/ENVIRONMENT.md` E-6). The remote may read `GILGUY/nsres` or
`GILGUY/NSRES`; both push (E-7 and its amendment). Run `git fetch origin main` before pushing
(E-5).

## Handoff note

- Why work stopped: WP-030 closed (TEST_EVIDENCE § WP-030; commit on `main`). Not a budget
  cutoff and not a blocker.
- Done and trustworthy: WP-000 to WP-020, plus `src/nsres/canon/` (structured canon
  statements and the calendar, travel closure, earliest arrival over timetables, speed rules,
  daylight, identity collisions, precedence) and `src/nsres/rules/` (the B.2 rule record and
  registry, runs with UNCHECKABLE and TIGHTEN, the finding factory). The gate console's
  isolation check for canon is `nsres.canon.registry.store_isolation_check`.
- Decisions to know: D-017 (statement forms), D-018 (RC-L1 codes and severities), D-019
  (isolation check), D-020 (precedence tiers), D-021 (registry and factory); and the
  WP-010/WP-020 decisions listed in earlier handoffs (D-004 to D-016).
- Deliberately not done: L1 checks 1 and 4 and RC-08 (G2), evaluation of free-text canon.

## Open issues

- Spec errata ERR-1 to ERR-17 (`docs/DECISIONS.md`) await one batch patch proposal at the
  end of G1 (after WP-040), for Patrick to gate. Each is resolved in code by a recorded
  decision, so none blocks WP-040. (Verified by: every erratum names its resolving decision,
  and the tests pass under those decisions.)
- Fixture completions marked illustrative (`fixtures/harrow-house/README.md`: two in
  PKT-007-r3, LOC-003 and LOC-004 handles, CAN-062 and CAN-070 handles, three daylight times)
  must not be used as expected engine outputs.
- E-2, E-6, and E-7 leave environment claims unverified (uv network use; why the remote URL
  reverts). Not blockers.
- The spec's own pilot readiness is 0.80, INSUFFICIENT; the build proceeds under D-001. Not a
  build blocker.

## Next exact action

1. `uv sync --frozen && uv run --frozen python scripts/gate.py` (verify this cursor).
2. Start WP-040 (plan WP-040 in `docs/IMPLEMENTATION_PLAN.md`): read spec §9.6, §11.5
   (factors, ceilings, the claim ladder REQ-9.6.1, penalties, caps, bands, REQ-11.5.1),
   §15.3 (spec readiness), Appendix A.5 and A.8 (the readiness vectors and scores), and
   `docs/reference/confidence_oracle.py` (read it as the contract, never import it from
   `src/`, plan A-12) with `docs/reference/spec_readiness_v0.1.1.json`. Generate the golden
   fixtures once by running the oracle (`fixtures/golden/`), then build
   `src/nsres/confidence/`. Golden values: 0.9625; 0.8952 base and 0.69 final; 0.9649;
   0.7825; 0.8035 base and 0.80 final.
3. After WP-040 closes, G1 is complete: write the batch spec errata patch proposal (ERR-1 to
   the last) for Patrick to gate, then G2.

## Do not do next

- Do not start a G2 package before WP-040's exit criteria are evidenced in
  `docs/TEST_EVIDENCE.md` and the G1 errata proposal is written. (Plan §7 ordering; the
  errata batch was promised for the end of G1.)
- Do not import `docs/reference/confidence_oracle.py` from `src/` (plan A-12).
- Do not read from or write to WCS folders (plan Out list; D-016).
- Do not change a schema, record shape, lifecycle row, or rule code without first amending
  the matching D-entry in `docs/DECISIONS.md` (build discipline: contracts change before code).
- Do not give `GateConsole` a default isolation check (D-013 item 7).

## Completed

| Package | Closed | Evidence |
| --- | --- | --- |
| WP-000 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-000 and amendment A1 |
| WP-010 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-010 |
| WP-020 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-020 |
| WP-030 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-030 |
