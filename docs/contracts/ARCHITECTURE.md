# Contract: architecture lock

> Registered from `docs/IMPLEMENTATION_PLAN.md` v0.2.1 at WP-000. The plan section is authoritative; this copy exists so a cold session reading only the repository has the contract. Changing it requires the process in the plan's scope-lock note and a `DECISIONS.md` entry first.

## Architecture lock (plan §5; OQ-2 decided: Python)

If OQ-2 is decided for TypeScript, A-01, A-02, A-03, A-11, A-12, A-13, A-16, and §8 revert to plan 0.1.0 (Appendix B).

| ID | Decision |
| --- | --- |
| A-01 | Python 3.12 or later (developed on 3.13). One package, `nsres`, in a `src/` layout with a PEP 621 `pyproject.toml`, the `hatchling` build backend, a library API, and an `nsres` console script. Ships `py.typed`. |
| A-02 | Runtime dependency: `jsonschema` only (Draft 2020-12). CLI parsing with `argparse`; hashing with `hashlib`; JSON with the standard library. |
| A-03 | Environment and lock: `uv`, with `uv.lock` committed. Dev dependencies: `pytest`, `ruff` (format and lint), `mypy`. Versions pinned. |
| A-04 | Engines are pure functions of (records, model version, configuration). No clock reads and no randomness inside engines: time and seeds are injected. |
| A-05 | Persistence: an append-only JSON Lines record log per project, opened in append mode and fsynced per entry, plus a content-addressed artifact store (`sha256/<hash>.json`). Projections are rebuilt in memory from the log. No database in v0.1. (The WCS handler's read-modify-write log, ledger N-07a, is the pattern to avoid.) |
| A-06 | Bitemporal rows: story-time validity plus transaction revision on every record revision. |
| A-07 | Identity: UUIDv7 (implemented in-house, with injected clock and seed for tests) plus a human handle. Names are never keys. WCS IDs (`prefix_` plus 12 hex digits) are foreign keys only, never NSRES identity. |
| A-08 | Status and gate vocabulary exactly as spec §0.7. Only the gate API changes status, and it always writes a gate record and an audit record. Engine APIs are typed so that they cannot request ACCEPTED, CANON, or PUBLISHED. |
| A-09 | Story-time is integer minutes from a per-work epoch, with a Gregorian display mapping. Precision tags map to default windows (spec §6.3). |
| A-10 | Temporal solving: STN distance graph, Floyd–Warshall full solve per run. Incremental solving is an optimization, permitted only if it produces identical windows (tested). |
| A-11 | Rules are Python predicate modules registered in a Rule Registry with the Appendix B.2 record shape (id, version, layer, severity, message, repair hints, evidence required). |
| A-12 | The confidence engine is a native Python module implementing the factorized calculator's contract. Golden outputs are generated once by running Patrick's `confidence.py` as an independent oracle and committed as fixtures. The package never imports the oracle, so a shared bug cannot hide. |
| A-13 | AI roles are `typing.Protocol` ports. v0.1 ships fixture adapters only, which read pre-recorded outputs from `fixtures/`. No module under `src/` imports `socket`, `http`, `urllib`, or any network library; package verification checks this. |
| A-14 | Canonical serialization: sorted keys, no insignificant whitespace, UTF-8, numbers in shortest round-trip form. Packet hashes are SHA-256 of that form. |
| A-15 | Engines never raise for domain violations; they return findings. They raise only for programmer errors and schema-invalid input. |
| A-16 | Single language: Python for product code, tests, and scripts. |
| A-17 | Every closed vocabulary (statuses, channels, beat types, severities, causes, finding statuses, bands, packet statuses, gate types) is a `Literal` type or `StrEnum` checked for exhaustiveness with `assert_never` under `mypy --strict`. A test asserts each one equals the matching enum in the JSON Schemas. A vocabulary that drifts from its schema fails the gate. |
