# Decisions

Architecture decisions, gate decisions, deviations, and environment facts. A conflict between
two documents is resolved by recording the resolution here first, never by silently picking one.
Entries are never deleted. A superseded entry stays, with a pointer to the entry that replaced it.

Claim markers: every causal or diagnostic claim carries **Verified by:** (with the command or
observation) or **Inferred — unverified:** (with the cheapest test).

---

## Architecture lock (registered at WP-000)

A-01 to A-17 are registered verbatim in `docs/contracts/ARCHITECTURE.md` (from plan §5). Summary:

| ID | Decision |
| --- | --- |
| A-01 | Python 3.12 or later; one package `nsres`, `src/` layout, PEP 621, hatchling, console script `nsres`, ships `py.typed` |
| A-02 | Runtime dependency `jsonschema` only; `argparse`, `hashlib`, stdlib JSON |
| A-03 | `uv` with committed `uv.lock`; dev tools `pytest`, `ruff`, `mypy` |
| A-04 | Engines are pure functions; clock and seeds injected |
| A-05 | Append-only JSONL record log (append mode, fsync per entry) plus content-addressed artifact store |
| A-06 | Bitemporal rows |
| A-07 | UUIDv7 plus handle; WCS IDs are foreign keys only |
| A-08 | Status and gate vocabulary exactly as spec §0.7; only the gate API changes status |
| A-09 | Story-time in integer minutes from a per-work epoch |
| A-10 | STN with Floyd–Warshall full solve |
| A-11 | Rules are Python predicate modules in a registry with the B.2 shape |
| A-12 | Native confidence engine; golden values from the independent oracle `docs/reference/confidence_oracle.py`, never imported by the package |
| A-13 | AI roles are `typing.Protocol` ports with fixture adapters; no network imports under `src/` |
| A-14 | Canonical serialization and SHA-256 packet hashes |
| A-15 | Engines return findings for domain violations; raise only for programmer errors and schema-invalid input |
| A-16 | Single language: Python |
| A-17 | Closed vocabularies are `Literal`/`StrEnum`, exhaustively checked, and tested equal to the JSON Schema enums |

---

## Gate and override decisions

**D-001 — Build proceeds below spec readiness (human override).** The spec scored 0.78 at v0.1
and 0.80 at v0.1.1 (INSUFFICIENT; spec §15.3). Patrick instructed "execute build pipeline for
software creation" (2026-10-25). Recorded as a human override; it authorizes building the
reference implementation, not promoting the spec. Building is the main lever on the
buildability factor.

**D-002 — Plan gate passed.** Patrick, 2026-10-25: "utilize your recommendations.
https://github.com/GILGUY/NSRES". Plan v0.2.1 is ACCEPTED with every §9 recommendation:

| ID | Decision |
| --- | --- |
| OQ-1 | Code target `GILGUY/NSRES` (GitHub resolves it as `gilguy/nsres`), branch `main`. **Verified by:** `git clone https://github.com/GILGUY/nsres` succeeded; HEAD `ac0bab1 Initial commit` held a 7-byte `README.md` |
| OQ-2 | Python only (A-01 to A-17 as registered) |
| OQ-3 | Scope lock as in `docs/contracts/SCOPE.md` |
| OQ-4 | Spec exported from the controlling doc (rev 126) to `docs/spec/NSRES-SPEC.md`; provenance in `docs/spec/SOURCE.md` |
| OQ-5 | Spec Appendix A and §17.8 example values are test-authoritative fixtures |
| OQ-6 | Story-time in integer minutes from a per-work epoch |
| OQ-7 | Repository private, no license |
| OQ-8 | The spec §0.7 WCS crosswalk is In, as tested data with no I/O (`src/nsres/wcs/`) |
| OQ-9 | The NSRES CANON vocabulary governs: a WCS CANON story_spine, story_blueprint, or recut_proposal imports as ACCEPTED and structure-locked |
| OQ-10 | A BLOCKING finding cannot be WAIVED_BY_OVERRIDE (spec REQ-9.1.2, added at rev 126; B.4 schema clause added) |

**D-003 — Spec version used by the build.** NSRES-SPEC v0.1.1 at Claude Docs rev 126. A later
spec revision is adopted only by a new D-entry naming the revision and what changed.

---

## Deviations

(none yet)

---

## Environment facts

See `docs/ENVIRONMENT.md` for the ledger.
