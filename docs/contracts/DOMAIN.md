# Contract: domain lock

> Registered from `docs/IMPLEMENTATION_PLAN.md` v0.2.1 at WP-000. The plan section is authoritative; this copy exists so a cold session reading only the repository has the contract. Changing it requires the process in the plan's scope-lock note and a `DECISIONS.md` entry first.

## Domain lock (plan §6)

**Normative types.** Spec §10.2 (as of v0.1.1) is the normative type set, extended by: mechanics records (§17.4), the packet (§8, with every sub-object written out), validation reports, extraction records, RES records, gate records, and audit records. Deviations from §10.2 must be recorded in `DECISIONS.md` before code.

**Module map**

| Module | Responsibility | Spec |
| --- | --- | --- |
| `src/nsres/domain/` | Types, schemas, canonical JSON, hashing, UUIDv7 | §8, §10.2, B.3–B.4 |
| `src/nsres/store/` | Record log, revisions, bitemporal queries, statuses, gates, audit chain, model versions | §0.7, §5.4, §10.4–10.5 |
| `src/nsres/wcs/` | The §0.7 crosswalk as data, and its import rules (only if OQ-8 is approved) | §0.7, §12.2 |
| `src/nsres/canon/` | Canon rule classes, metrics closure, timetables, daylight, precedence | §3.4, L1 |
| `src/nsres/rules/` | Rule registry, finding factory | B.2 |
| `src/nsres/confidence/` | Factorized scoring, ceilings, ladder, caps, bands | §9.6, §11.5 |
| `src/nsres/time/` | STN, Allen translation, anchors, windows, disjunction branching | §6.2–6.3 |
| `src/nsres/effects/` | Effect and precondition parser; state folding | §3.5, §10.9, §17.4 |
| `src/nsres/project/` | Presence, travel, location state, custody (L6–L8) | §6.4–6.6, §6.12 |
| `src/nsres/knowledge/` | Grants, channels, CIS, belief revision, reachability (L9) | §6.7, §6.13 |
| `src/nsres/reader/` | RIS plan and actual tracks, reveals, questions, irony gaps, hidden causality, pressure (L10) | L10, §6.8–6.9, §7.8 |
| `src/nsres/reconcile/` | Loop, RC rules, report, repairs, dry runs, impact sets, staleness | §6, §4.17 |
| `src/nsres/extract/` | Extraction pipeline and its rule families | §7 |
| `src/nsres/packet/` | Assembly, PK checks, readiness vector, brief compiler, freeze | §8, §10.11 |
| `src/nsres/validate/` | L14 suites, validation report, acceptance readiness | L14, §9.6 |
| `src/nsres/autopsy/` | L15 classification, micro-facts, RIS_actual, root cause, drift, retro-consistency | §9 |
| `src/nsres/mechanics/` | Mechanics records, ledgers, MC rules, packet group N | §17 |
| `src/nsres/ports/` | AI role protocols and fixture adapters | §10.12 |
| `src/nsres/cli/` | `nsres` command | §10.13 |

**Fixtures**

| Directory | Contents |
| --- | --- |
| `fixtures/harrow-house/` | Canon (A.1), events (A.2) in first-outline and repaired forms, L2–L4 plans, reveal plan, drafts DRF-007-01 and DRF-007-02, pre-extracted assertions with exact span quotes, probe scores |
| `fixtures/drowned-provinces/` | Regimes, mechanics, practitioner, scene plans SCN-212, SCN-219, SCN-240 (§17.8) |
| `fixtures/golden/` | Expected reconciliation reports, packet PKT-007-r3, compiled brief, validation reports, confidence vectors, autopsy outputs |
| `fixtures/wcs/` | `modules.json` 1.0-runtime and its sha256 (only if OQ-8 is approved) |

**CLI surface (v0.1)**

`nsres init | propose | decide | reconcile | extract | compile | validate | autopsy | score | mechanics check | report`. Every command reads and writes a project directory; exit codes carry the band where a score is produced.
