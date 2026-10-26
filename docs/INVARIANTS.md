# Invariants

Properties that must hold at every commit once the package that enforces them has closed.
Each names its spec source and the package whose exit criteria prove it. Before that package
closes, the invariant is an obligation, not a guarantee.

| ID | Invariant | Spec source | Enforced from |
| --- | --- | --- | --- |
| I-01 | The record log is append-only. No code path rewrites or truncates an existing line | §10.4, plan A-05 | WP-020 |
| I-02 | Only the gate API changes a record's status, and every change writes a gate record and an audit record | §0.7, §5.4 | WP-020 |
| I-03 | No engine function can set ACCEPTED, CANON, or PUBLISHED | §0.7, REQ-5.4.1 to 5.4.4 | WP-020 |
| I-04 | The audit log is hash-chained; altering any line is detected at that line | §10.5 | WP-020 |
| I-05 | Packets never cite PROPOSAL records | §0.7 (citable column), REQ-7.1.1 | WP-120 |
| I-06 | Engines are deterministic: same inputs and configuration, byte-identical outputs | §1.5, plan A-04 | WP-010 onward; e2e at WP-190 |
| I-07 | No module under `src/nsres` imports a network library | plan A-13 | WP-000 (gate stage 7) |
| I-08 | A compiled brief never contains sealed proposition text or a leak indicator | §8, §10.11 | WP-140 |
| I-09 | A BLOCKING finding carries CONTENT_READ evidence | REQ-9.1.1, B.4 | WP-010 (schema), WP-150 |
| I-10 | A BLOCKING finding is never WAIVED_BY_OVERRIDE | REQ-9.1.2, B.4 | WP-010 (schema), WP-020 |
| I-11 | A failed hard cap is never overridden; it clears only when inputs change | REQ-11.5.1 | WP-040 |
| I-12 | WCS material at RAW or INTAKE state is never imported; a WCS PROPOSAL is never a fact | REQ-12.2.2 | WP-020 |
| I-13 | Every closed vocabulary in code equals its JSON Schema enum | plan A-17 | WP-010 |
| I-14 | Wheel and sdist builds are reproducible from a fixed `SOURCE_DATE_EPOCH` | plan §8 | WP-000 (gate stage 8) |
