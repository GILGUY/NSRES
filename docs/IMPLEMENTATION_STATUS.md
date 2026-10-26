# Implementation status (the cursor)

Authoritative for where work stopped. Read this first, then verify it: re-run the last
verified command and compare with the recorded result before trusting anything below.

```
Current gate:            G1 (records are trustworthy)
Current work package:    WP-030 Canon registry and rule registry
Current slice:           not started
Status:                  READY_TO_START
Last verified command:   uv sync --frozen && uv run --frozen python scripts/gate.py
Result:                  exit 0, "GATE PASS: 9/9 stages"; format 58 files, typecheck 57 source
                         files, unit 2065 passed, integration 4 passed, wheel 38 files,
                         sdist 38 files, 33 modules 0 network imports, repro identical
                         digests, e2e 2 flows
```

Environment note: run uv with `UV_SYSTEM_CERTS=1` and `UV_NATIVE_TLS` unset to avoid the
deprecation warning (`docs/ENVIRONMENT.md` E-6). The remote is
`https://github.com/GILGUY/NSRES.git` (E-7).

## Handoff note

- Why work stopped: WP-020 closed (TEST_EVIDENCE § WP-020; commit on `main`). Not a budget
  cutoff and not a blocker.
- Done and trustworthy: WP-000 and WP-010, plus `src/nsres/store/` (append-only record and
  audit logs with fsync per line, hash chain with row coverage, bitemporal reads, the §5.4
  record lifecycle as data with a pure planner, the gate console, the engine writer, model
  versions, the waiver rule, the artifact store) and `src/nsres/wcs/` (the §0.7 crosswalk as
  data and `import_decision`).
- Decisions to know before touching the store: D-012 (layout, transactions, chain), D-013
  (lifecycle mapping, acceptance gates, micro-facts, retire = REJECT, edits run the
  isolation check, REVISE/HOLD), D-014 (engine vs human write paths), D-015 (WP-010 type
  extensions), D-016 (crosswalk).
- How WP-030 plugs in: `Store.gate_console(isolation_check)` requires the rule-suite check as
  an argument with no default (D-013 item 7). WP-030's rule registry should provide a
  function `(record) -> Sequence[str]` of failures, and its finding factory should produce
  `nsres.domain.records.Finding` values for `EngineWriter.record_finding`.
- Deliberately not done: crash repair (detect only), pending engine change proposals
  (autopsy package), staleness marking (packet package), WCS I/O (v0.3).

## Open issues

- Spec errata ERR-1 to ERR-13 (`docs/DECISIONS.md`) await one batch patch proposal at the
  end of G1, for Patrick to gate. Each is resolved in code by a recorded decision, so none
  blocks WP-030. (Verified by: every erratum names its resolving decision, and the tests pass
  under those decisions.)
- Two completions in the PKT-007-r3 fixture are illustrative, not spec values
  (`fixtures/harrow-house/README.md`). No later package may use them as expected outputs.
- E-2 and E-6 leave one environment claim unverified (whether `uv build` reached the
  network). Not a blocker.
- The spec's own pilot readiness is 0.80, INSUFFICIENT; the build proceeds under D-001. Not a
  build blocker.

## Next exact action

1. `uv sync --frozen && uv run --frozen python scripts/gate.py` (verify this cursor).
2. Start WP-030: read spec §3.3 and §3.4 (canon rule classes, truth semantics, precedence
   tiers), the L1 layer section (§4, "L1"), the canon examples in Appendix A.1 (travel,
   timetables CAN-060 and CAN-061, daylight), §6.11 (RC rules that use canon), DEF-41, and
   B.2 (rule registry record), plus plan WP-030 in `docs/IMPLEMENTATION_PLAN.md`. Record any
   spec conflicts as decisions before code. Then build `src/nsres/canon/` (rule classes,
   travel matrix with shortest-path closure, timetables as earliest-arrival functions, a
   table-driven daylight model, precedence) and `src/nsres/rules/` (B.2 registry, finding
   factory, and the isolation check the gate console needs).

## Do not do next

- Do not start WP-040 or any G2 package before WP-030's exit criteria are evidenced in
  `docs/TEST_EVIDENCE.md`. (Plan §7 ordering; WP-040 depends only on WP-010 but G1 closes
  in order here; verified by reading the plan.)
- Do not import `docs/reference/confidence_oracle.py` from `src/` (plan A-12).
- Do not read from or write to WCS folders (plan Out list; D-016).
- Do not change a schema, record shape, or the lifecycle table without first amending the
  matching D-entry in `docs/DECISIONS.md` (build discipline: contracts change before code).
- Do not give `GateConsole` a default isolation check (D-013 item 7).

## Completed

| Package | Closed | Evidence |
| --- | --- | --- |
| WP-000 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-000 and amendment A1 |
| WP-010 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-010 |
| WP-020 | 2026-10-25 | `docs/TEST_EVIDENCE.md` § WP-020 |
