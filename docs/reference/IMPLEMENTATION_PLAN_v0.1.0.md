# NSRES Engine v0.1 — Implementation Plan

**Status:** PROPOSAL — awaiting Patrick's approval at the plan gate. Nothing is instantiated until approved.
**Plan version:** 0.1.0
**Produced by:** context-to-plan (passes 0–4), 2026-10-25
**Controls:** architecture, scope, and work order for the NSRES reference implementation.

---

## Evidence register

| Source | Label | Note |
| --- | --- | --- |
| NSRES-SPEC v0.1 (Claude Docs, rev 110) | CONTENT_READ | Authored this session. No edits since rev 110. Verified by: a `sinceRev 110` read returned no changed blocks. |
| Corpus architecture summary (`attachment-06864e15.txt`) | CONTENT_READ | Thrust/authority split, NSRES pipeline, WCS, MAPS, Beat Engine, ARTEMIS/GVE |
| Canonical SLB lock (`attachment.txt`) | CONTENT_READ | SI, EP, IS, FT, SR, DI |
| Confidence control plane summary (pasted in chat) | CONTENT_READ | Rules folded into spec §9.6 and §11.5 |
| Beat Engine intake and reconciliation v0.1 (pasted in chat) | CONTENT_READ | Folded into spec §12.4 |
| Confidence calculator (`confidence-calculator` skill script) | CONTENT_READ | Oracle for golden fixtures (A-12) |
| UTED-EC, QMCP concepts | FOUND_BY_SNIPPET | Affects only the optional §17.2 ontology kit, which v0.1 does not implement as code |
| WCS module specifications; full UTED-EC v3.1 and QMCP canon | GAP_IDENTIFIED | Not needed: integrations are on the Out list |

Pass 0 gather (`gather_context.py`, target "nsres narrative engine"): 6 candidates, 6 single-version families, no version families, no empty files. The controlling source (the spec) is a Claude Doc, not a file, so it was not in the gather roots.

---

## 1. Authority and read order

1. `docs/DECISIONS.md` — Patrick's gate decisions and every recorded deviation.
2. **This plan** — controls architecture, scope, and work order.
3. **NSRES-SPEC v0.1** — controls behavior and requirements.
4. `fixtures/` — expected values for tests, derived from spec Appendix A and §17.8 (see OQ-5).
5. Corpus summaries — context only.

**Conflict rule.** Plan against spec on *behavior*: the spec wins, unless `DECISIONS.md` records a deviation. Plan against spec on *architecture or ordering*: the plan wins. A conflict is never resolved silently; the resolution is recorded first.

**Readiness note.** The spec scored **0.78, INSUFFICIENT** for pilot readiness (spec §15.3). The build proceeds on Patrick's explicit instruction ("execute build pipeline for software creation", 2026-10-25). That instruction is recorded as a human override under REQ-11.5.1 (`DECISIONS.md` D-001). Building the reference implementation is also the main lever on the spec's weakest buildability factor.

---

## 2. Code target

- **Repository:** `GILGUY/nsres` on GitHub, private, branch `main`.
- **Session working clone:** `/home/claude/nsres`. It is not durable; every closed package is pushed before the session ends.
- **Precondition:** the repository exists and is attached to the session (OQ-1). Until then this plan cannot be instantiated.

---

## 3. Completion contract (v0.1 is done when all of these hold)

**Function**

1. `nsres reconcile` on the Harrow House first-outline fixture reports exactly the four contradictions of spec Appendix A.3 (RC-08, RC-10, RC-13, RC-04), nothing else, and reports CONSISTENT after the four recorded repairs (RES-0011, RES-0014, RES-0015, RES-0016) are applied.
2. `nsres extract SCN-007` produces a packet that validates against the packet schema, classifies facts exactly as Appendix A.5, keeps INF-002 and INF-004 only in `sealed`, and has the same hash on every run.
3. `nsres validate` marks DRF-007-01 FAILED with BLOCKING findings on S2 and S5 and an acceptance readiness of 0.69 (UNSTABLE). It marks DRF-007-02 VALIDATED at 0.96 (READY). Both match golden values to four decimal places.
4. `nsres autopsy` on accepted DRF-007-02 reproduces Appendix A.9: micro-fact OBJ-012 registered through the CANON gate, RIS_actual gains INF-006 (SHOWN) and INF-008 (HINTED), Q-03 opens, and a window-collapse proposal fixes EVT-0106 at 22:45.
5. `nsres mechanics check` on the Drowned Provinces fixture reports MC-05 for SCN-219, and MC-12 plus MC-15 for SCN-240, as in spec §17.8.

**Integrity**

6. The record log is append-only. Every status change passes through the typed-gate API and writes an audit record. The audit log is hash-chained, and tampering with any line is detected.
7. No engine function can set ACCEPTED, CANON, or PUBLISHED status. Packets never cite PROPOSAL records.
8. Engines are deterministic: the same inputs and configuration produce byte-identical outputs.

**Safety**

9. The engine makes no network calls. AI roles exist only as interfaces with fixture adapters.
10. A compiled brief never contains sealed content: no sealed proposition text and no leak indicator.

**Quality**

11. `npm run gate` passes all nine stages (§8).

**Delivery**

12. Everything is pushed to `GILGUY/nsres`, tagged `v0.1.0`. A fresh clone passes `npm ci && npm run gate`. The cursor and evidence records are current.

---

## 4. Scope lock

**In (v0.1)**

| Area | Spec reference |
| --- | --- |
| Domain types and JSON Schemas (packet, finding, all sub-objects written out) | §8, §10.2, §17.4, Appendix B.3–B.4 |
| Record store: append-only log, bitemporal revisions, statuses, typed gates, hash-chained audit | §0.7, §5.4, §10.4–10.5 |
| Canon registry: rule classes, travel metric closure, timetables, simple daylight model, precedence | §3.4, L1 |
| Rule registry and findings | Appendix B.2, DEF-41 |
| Confidence engine: factors, ceilings, claim ladder, penalties, caps, bands | §9.6, §11.5, REQ-9.6.1 |
| Temporal engine: STN, windows, metric and single Allen relations, anchors, capped disjunctions | §6.2–6.3 |
| Effect and precondition language; state folding | §3.5, §10.9, §17.4 |
| Projections L6–L8 with RC-02, RC-05, RC-08, RC-09, RC-12, RC-13 | §4 (L6–L8), §6.4–6.6, §6.12 |
| Knowledge L9 with channels, witness grants, belief revision, reachability, RC-10, RC-11, RC-14 | L9, §6.7, §6.13 |
| Reader ledger L10 (plan track; actual track from autopsy), reveals, RC-16, pressure vector | L10, §6.8–6.9, §7.8 |
| Reconciliation loop and report, RC-01 to RC-17, version lifecycle | §6.1, §6.11, §6.15 |
| Repairs (subset), dry runs, cost scoring, RES records, impact sets, staleness | §4.17–4.18, §6.14 |
| Extraction engine: all 18 steps, SR, PV, VR, SU, RV, CC, EX rules | §7 |
| Packet assembly, canonical hash, PK rules, packet readiness vector, brief compiler, freeze | §8, §10.11 |
| L14 validator over fixture-supplied assertions | L14, §9.3 |
| L15 autopsy: classification, micro-facts, RIS_actual, window collapse, root cause, DI-1 to DI-4, retro-consistency | §9 |
| World Mechanics Engine: records, ledgers, MC-01 to MC-18, packet group N, AU-80 to AU-84, hardness | §17 |
| CLI over a project directory | §10.13 |
| Fixtures: Harrow House, Drowned Provinces, golden outputs | Appendix A, §17.8 |

**Out (deferred, by name)**

| Deferred item | Spec reference | Target |
| --- | --- | --- |
| World Codex UI and lenses | §16 | v0.2 |
| Live Generation Gateway and real AI roles (drafter, extractor, linker, leak probe, critic, manifestation writer, summarizer) | §10.12 | v0.2 |
| Context Fetch Service | §10.4 (C18) | v0.2 |
| DI-5 description divergence (needs embeddings) | §9.4 | v0.2 |
| Canon branches and merge | §12.8 | v0.3 |
| GVE counterfactuals; simulation layers | §12.6, §12.9 | v0.3 |
| WCS, MAPS, Beat Engine, Seam Protocol adapters; editorial suite ED-01 to ED-04 | §12.2–12.5 | v0.3 |
| Graph database, vector index, RDF/OWL export | §10.4, §12.8 | v0.3 |
| Import/export adapters (Fountain, Final Draft, Scrivener, series bibles) | §12.8 | v0.3 |
| Datalog rule engine (rules ship as TypeScript predicates) | §10.11 | v0.3 |
| Non-Gregorian calendars | §0.4 | v0.3 |
| Ontology kit as executable code (§17.2 is documentation in v0.1) | §17.2 | v0.3 |
| Multi-user permissions per gate | §10.15 | v0.3 |
| Hypocrisy Tax metric | §12.7 | Not adopted |
| The §14 evaluation trial | §14 | Separate study |

Moving anything from Out to In requires a proposal, an impact analysis (permissions, data, tests, distribution), Patrick's approval, and updated contracts before implementation.

---

## 5. Architecture lock

| ID | Decision |
| --- | --- |
| A-01 | TypeScript, `strict` mode, Node 22, ES modules. One package, `nsres`, with a library API and a CLI. |
| A-02 | Runtime dependency: `ajv` (JSON Schema validation) only. CLI argument parsing uses `node:util` `parseArgs`. Hashing uses `node:crypto`. |
| A-03 | Dev dependencies: `typescript`, `vitest`, `eslint` with `typescript-eslint`, `prettier`, `@types/node`. Versions pinned; lockfile committed. |
| A-04 | Engines are pure functions of (records, model version, configuration). No clock reads and no randomness inside engines: time and seeds are injected. |
| A-05 | Persistence: an append-only JSON Lines record log per project, plus a content-addressed artifact store (`sha256/<hash>.json`). Projections are rebuilt in memory from the log. No database in v0.1. |
| A-06 | Bitemporal rows: story-time validity plus transaction revision on every record revision. |
| A-07 | Identity: UUIDv7 (implemented in-house, with injected clock and seed for tests) plus a human handle. Names are never keys. |
| A-08 | Status and gate vocabulary exactly as spec §0.7. Only the gate API changes status, and it always writes a gate record and an audit record. Engine APIs are typed so that they cannot request ACCEPTED, CANON, or PUBLISHED. |
| A-09 | Story-time is integer minutes from a per-work epoch, with a Gregorian display mapping. Precision tags map to default windows (spec §6.3). |
| A-10 | Temporal solving: STN distance graph, Floyd–Warshall full solve per run. Incremental solving is an optimization, permitted only if it produces identical windows (tested). |
| A-11 | Rules are TypeScript predicate modules registered in a Rule Registry with the Appendix B.2 record shape (id, version, layer, severity, message, repair hints, evidence required). |
| A-12 | Confidence engine is a TypeScript port of Patrick's factorized calculator. Golden outputs are generated once with the Python calculator and committed as fixtures; Python is not part of the gate. |
| A-13 | AI roles are TypeScript interfaces (ports). v0.1 ships fixture adapters only, which read pre-recorded outputs from `fixtures/`. No network code exists in `src/`. |
| A-14 | Canonical serialization: sorted keys, no insignificant whitespace, UTF-8, numbers in shortest round-trip form. Packet hashes are SHA-256 of that form. |
| A-15 | Engines never throw for domain violations; they return findings. They throw only for programmer errors and schema-invalid input. |
| A-16 | Single language: TypeScript for product code, tests, and scripts. |

---

## 6. Domain lock

**Normative types.** Spec §10.2 is the normative type set, extended by: mechanics records (§17.4), the packet (§8, with every sub-object written out), validation reports, extraction records, RES records, gate records, and audit records. Deviations from §10.2 must be recorded in `DECISIONS.md` before code.

**Module map**

| Module | Responsibility | Spec |
| --- | --- | --- |
| `src/domain/` | Types, schemas, canonical JSON, hashing, UUIDv7 | §8, §10.2, B.3–B.4 |
| `src/store/` | Record log, revisions, bitemporal queries, statuses, gates, audit chain, model versions | §0.7, §5.4, §10.4–10.5 |
| `src/canon/` | Canon rule classes, metrics closure, timetables, daylight, precedence | §3.4, L1 |
| `src/rules/` | Rule registry, finding factory | B.2 |
| `src/confidence/` | Factorized scoring, ceilings, ladder, caps, bands | §9.6, §11.5 |
| `src/time/` | STN, Allen translation, anchors, windows, disjunction branching | §6.2–6.3 |
| `src/effects/` | Effect and precondition parser; state folding | §3.5, §10.9, §17.4 |
| `src/project/` | Presence, travel, location state, custody (L6–L8) | §6.4–6.6, §6.12 |
| `src/knowledge/` | Grants, channels, CIS, belief revision, reachability (L9) | §6.7, §6.13 |
| `src/reader/` | RIS plan and actual tracks, reveals, questions, irony gaps, hidden causality, pressure (L10) | L10, §6.8–6.9, §7.8 |
| `src/reconcile/` | Loop, RC rules, report, repairs, dry runs, impact sets, staleness | §6, §4.17 |
| `src/extract/` | Extraction pipeline and its rule families | §7 |
| `src/packet/` | Assembly, PK checks, readiness vector, brief compiler, freeze | §8, §10.11 |
| `src/validate/` | L14 suites, validation report, acceptance readiness | L14, §9.6 |
| `src/autopsy/` | L15 classification, micro-facts, RIS_actual, root cause, drift, retro-consistency | §9 |
| `src/mechanics/` | Mechanics records, ledgers, MC rules, packet group N | §17 |
| `src/ports/` | AI role interfaces and fixture adapters | §10.12 |
| `src/cli/` | `nsres` command | §10.13 |

**Fixtures**

| Directory | Contents |
| --- | --- |
| `fixtures/harrow-house/` | Canon (A.1), events (A.2) in first-outline and repaired forms, L2–L4 plans, reveal plan, drafts DRF-007-01 and DRF-007-02, pre-extracted assertions with exact span quotes, probe scores |
| `fixtures/drowned-provinces/` | Regimes, mechanics, practitioner, scene plans SCN-212, SCN-219, SCN-240 (§17.8) |
| `fixtures/golden/` | Expected reconciliation reports, packet PKT-007-r3, compiled brief, validation reports, confidence vectors, autopsy outputs |

**CLI surface (v0.1)**

`nsres init | propose | decide | reconcile | extract | compile | validate | autopsy | score | mechanics check | report`. Every command reads and writes a project directory; exit codes carry the band where a score is produced.

---

## 7. Work packages and gates

Dependency-ordered. One package at a time. No package begins until the previous one's exit criteria are evidenced.

### G0 — Control and gate

**WP-000 Control records, contracts, scaffold, full gate**
- depends on: plan approval; OQ-1 (repository attached)
- gate: G0
- build: `docs/IMPLEMENTATION_STATUS.md`, `docs/TEST_EVIDENCE.md`, `docs/DECISIONS.md` (A-01 to A-16, D-001 override), `docs/contracts/SCOPE.md`, `ARCHITECTURE.md`, `DOMAIN.md`, `docs/INVARIANTS.md`, `docs/PROTOCOL.md`, `docs/ENVIRONMENT.md`; this plan as `docs/IMPLEMENTATION_PLAN.md`; `package.json`, lockfile, `tsconfig.json`, `tsconfig.build.json`, eslint, prettier, and vitest configs; `scripts/verify-package.mjs`, `scripts/repro.mjs`, `scripts/e2e.mjs`; the empty module skeleton; one smoke test per suite.
- required cases: every gate stage runs against the empty project.
- exit criteria:
  - `npm run gate` exits 0, and the log shows all nine stages executed, each with its own count.
  - `scripts/repro.mjs` performs two clean builds and reports identical SHA-256 digests of `dist/`.
  - `scripts/e2e.mjs` runs the built CLI (`nsres --version`) and confirms it equals `package.json` version.
  - Cold-resume test: reading only the cursor, running its last verified command reproduces its recorded result.
- out of scope: any domain logic.

### G1 — Records are trustworthy

**WP-010 Domain types, schemas, canonical JSON, identifiers**
- depends on: WP-000
- build: all types (§6 domain lock); packet and finding JSON Schemas with every `$defs` written out; canonical serializer; hashing helpers; UUIDv7 with injected clock and seed.
- required cases: key order independence; non-ASCII text; integers and decimals; nested arrays; the B.4 rule that a BLOCKING finding needs CONTENT_READ evidence.
- exit criteria:
  - Two objects equal up to key order serialize to identical bytes and hashes.
  - The §8.4 example packet, completed with its omitted fields, validates. Removing `sealed` fails validation with the path named.
  - A BLOCKING finding with FOUND_BY_METADATA evidence is rejected.
  - UUIDv7 values sort in injected-time order.
- out of scope: persistence.

**WP-020 Record store, statuses, typed gates, audit**
- depends on: WP-010
- build: append-only JSONL log; revision rows with transaction revisions; bitemporal queries; record state machine (spec §5.4); gate API `decide(gate, record, outcome, actor, reason)`; model-version lifecycle; hash-chained audit log.
- required cases: every legal transition in the §5.4 record-lifecycle table; illegal transitions; RETCON required to edit PUBLISHED canon; micro-fact ACCEPT_AND_REGISTER and REJECT_MICRO_FACT paths.
- exit criteria:
  - Each row of the record-lifecycle table is a passing test, and every transition not in the table is rejected with a named reason.
  - Altering any one audit line makes chain verification fail at that line.
  - Reloading from disk yields state deep-equal and hash-equal to the in-memory state.
  - An attempt through any engine API to set ACCEPTED or CANON fails to compile (type test) and fails at runtime.
- out of scope: domain validation of record contents.

**WP-030 Canon registry and rule registry**
- depends on: WP-020
- build: canon rule classes; travel matrix with shortest-path closure; timetables as earliest-arrival functions; table-driven daylight model; precedence tiers (§3.4); rule registry (B.2 shape); finding factory.
- required cases: closure warning; speed-rule error; alias collision; cross-tier and same-tier conflicts.
- exit criteria:
  - A declared direct travel time longer than an indirect route raises the closure WARNING; one faster than the speed rule raises an ERROR.
  - Two entities sharing an alias without a disambiguation record produce an identity-collision finding.
  - A cross-tier conflict resolves to the higher tier; a same-tier conflict returns a gate-required finding and picks nothing.
- out of scope: events.

**WP-040 Confidence engine**
- depends on: WP-010
- build: factors, weight normalization, evidence ceilings, claim ladder (REQ-9.6.1), conflict penalties, caps, NSRES bands, contract violations, evidence-label warnings; golden fixtures generated once with the Python calculator.
- required cases: PKT-007-r3; DRF-007-01 sub-scores and aggregate; DRF-007-02; spec readiness; a factor with no evidence; a binding cap.
- exit criteria:
  - TypeScript outputs equal the golden values to four decimals: 0.9625, 0.8952 base and 0.69 final, 0.9649, 0.7825.
  - A factor with no evidence is a contract violation, not a score.
  - When a cap binds, the result names the cap, not the weakest factor, as the thing to fix first.
- out of scope: deciding gate outcomes.

### G2 — Reality is computable

**WP-050 Temporal engine**
- depends on: WP-030
- build: time points; metric, single-Allen, and anchor constraints; distance matrix; Floyd–Warshall; negative-cycle extraction; feasible windows; precision defaults; capped disjunction branching.
- exit criteria:
  - A hand-built five-event network yields windows equal to hand-computed bounds.
  - A contradictory triple yields RC-01 naming exactly its three constraints.
  - A two-disjunction network consistent in exactly one branch reports CONSISTENT with that branch identified.
  - Exceeding the branch cap reports UNCHECKABLE, never PASS.
- out of scope: projections.

**WP-060 Effect language and state folding**
- depends on: WP-050
- build: parser for the §10.9 and §17.4 grammar; `state(x, a, t)` per §3.5; exclusive attributes; persistent versus volatile attributes; CERTAIN versus POSSIBLE under windows; three-valued preconditions.
- exit criteria:
  - EVT-0104's preconditions and effects parse and round-trip to identical text.
  - Conflicting exclusive-attribute effects are reported CERTAIN when they conflict in every placement and POSSIBLE when only in some.
  - A volatile mood does not persist past its scene; an injury does.
  - A precondition that evaluates UNDETERMINED yields a MAJOR "unsupported" finding, not BLOCKING.
- out of scope: reconciliation loop.

**WP-070 Projections L6–L8**
- depends on: WP-060
- build: presence segments; travel requirements; RC-08 IMPOSSIBLE and TIGHTEN (adding an STN constraint and re-solving); RC-09; unaccounted intervals and routine defaults; L7 occupancy, lock state, RC-13, perceptibility; L8 custody with RC-12, existence RC-05, implicit-transfer proposals at PROPOSAL status.
- exit criteria:
  - On the Harrow House first-outline fixture, Hale's arrival from York is RC-08 IMPOSSIBLE with an earliest arrival of 09:30 derived from CAN-060 and CAN-061. With the RES-0011 bridge events applied, no RC-08 remains.
  - Mara's derived timeline equals the spec §6.4 table row for row, including UNACCOUNTED 06:15–07:40 with no finding.
  - Hale entering the locked study before EVT-0113 is RC-13.
  - OBJ-001's custody chain equals the L8 table.
- out of scope: knowledge.

**WP-080 Knowledge L9**
- depends on: WP-070
- build: grants from effects; automatic witness grants for AGENT, PATIENT, WITNESS and proposed grants for PRESENT and perceptibility; NOT_NOTICED; channel preconditions; belief revision with trust; CIS index; reachability; RC-10 outcomes (IMPOSSIBLE, UNSOURCED, PREMATURE, OVERCONFIDENT, LAUNDERED), RC-11, RC-14; the DETECTED channel.
- exit criteria:
  - The §6.7 INF-001 propagation table is reproduced exactly.
  - Hale's 10:00 beat stating the brandy was poisoned is PREMATURE. With EVT-0114 it is VALID at SUSPECTED, and OVERCONFIDENT if the beat displays certainty.
  - An inference whose premise is itself impossible is LAUNDERED.
- out of scope: reader ledger.

### G3 — The model is trustworthy

**WP-090 Reader ledger L10**
- depends on: WP-080
- build: RIS_plan from L2–L4 planned deltas; reveal records and prerequisites; setups and payoffs; open questions; irony gaps; RC-16; pressure vector with configurable weights.
- exit criteria:
  - RIS at 1.03.1 equals spec Appendix A.4.
  - Moving RVL-02 before the key-hook plant produces a prerequisite failure.
  - A rendered effect with a hidden, uncovered cause is RC-16; adding a reveal record covers it.
- out of scope: RIS_actual (WP-160).

**WP-100 Reconciliation loop and report**
- depends on: WP-090
- build: the §6.1 loop with fixpoint and the K cap (RC-17); RC-03, RC-04, RC-06, RC-07, RC-15; the §6.15 report; model-version transitions.
- exit criteria:
  - The first-outline fixture yields exactly FND-R-01 to FND-R-04 (Appendix A.3), with matching codes and records, and nothing else.
  - After the four repairs, the version is CONSISTENT.
  - Re-running on the same inputs yields a byte-identical report.
  - A constructed set of constraints that never stabilizes yields RC-17 at K.
- out of scope: proposing repairs.

**WP-110 Repairs, impact sets, staleness**
- depends on: WP-100
- build: repair library for RC-04, RC-08, RC-10, RC-13 (move within window, add bridge event, add channel event, lower displayed confidence, change beat outcome); dry runs; §6.14 cost score; RES records through gates; reverse-reference index; impact sets; STALE propagation; §4.18 policy (HUMAN_DECIDES default).
- exit criteria:
  - For FND-R-01, the candidate list includes the RES-0011 bridge, whose dry run removes the finding without adding one.
  - Every attempt by the engine to apply a change to an ACCEPTED or CANON record is rejected.
  - Changing CAN-061 marks every scene whose window or cited records overlap the change STALE.
- out of scope: packets.

### G4 — Packets are trustworthy

**WP-120 Extraction pipeline**
- depends on: WP-110
- build: §7.2 steps 1–10 and 12–18 (suppression in WP-130); SR, PV, VR, RV rules; extraction record with exclusions and rule trace; EX-01 to EX-07; REQ-7.1.1.
- exit criteria:
  - SCN-007 facts are classified exactly as Appendix A.5.
  - A fact that is both REVEAL_NOW and FORBIDDEN raises EX-04.
  - PROPOSAL records are excluded with reason NOT_ACCEPTED.
- out of scope: suppression, budget.

**WP-130 Suppression, manifestations, budget**
- depends on: WP-120
- build: SU-1 to SU-6; manifestation-writer and leak-probe ports with fixture adapters; CC-7; §7.9 budget rules; EX-05.
- exit criteria:
  - The SUP-1 and SUP-2 manifestations appear in the public section; `sealed` holds INF-002 and INF-004 and nothing else from the scene.
  - A fixture probe score of 0.30 fails CC-7.
  - Mandatory content over budget raises EX-05 and is never truncated.
- out of scope: hashing and freeze.

**WP-140 Packet assembly, compiler, freeze**
- depends on: WP-130, WP-040
- build: §8 assembly; canonical hash; PK-1 to PK-10; CC-1 to CC-10; packet readiness vector; brief compiler (§8.5); freeze through the STRUCTURE gate.
- exit criteria:
  - PKT-007-r3 equals the golden packet, and its hash is identical across two runs.
  - For every sealed proposition and every leak indicator, the compiled brief does not contain its text.
  - Freezing fails unless the model version is CONSISTENT or RELEASED and the STRUCTURE gate approves.
  - Changing CAN-061 after freezing marks PKT-007-r3 STALE.
  - The packet readiness vector equals the golden 0.9625.
- out of scope: drafts.

### G5 — Rendering is checkable

**WP-150 L14 validator**
- depends on: WP-140
- build: assertion-extractor port with a fixture adapter; span check (AU-70); lexical, presence, beat-coverage, POV, invention-policy, and forbidden-revelation suites; validation report with a mandatory coverage statement; acceptance readiness vector; acceptance through the INTEGRATION gate.
- exit criteria:
  - DRF-007-01 is FAILED with FND-007-01-01 (AU-02) and FND-007-01-02 (AU-34, AU-31, AU-32) BLOCKING, and readiness 0.69 UNSTABLE with all three cap conditions reported.
  - DRF-007-02 is VALIDATED at 0.9649, READY.
  - A report without a coverage statement fails schema validation.
  - A fixture assertion whose quotation does not occur in the draft is discarded as AU-70 and never becomes a finding.
- out of scope: cross-scene checks.

**WP-160 L15 autopsy**
- depends on: WP-150
- build: classification; micro-fact proposals and both CANON-gate decisions; RIS_actual update; window-collapse proposal (REQ-6.3.1); mechanical root-cause attribution; DI-1 to DI-4; retro-consistency at reveal acceptance.
- exit criteria:
  - Appendix A.9 outcomes are reproduced: OBJ-012 registered as CANON; RIS_actual gains INF-006 (SHOWN) and INF-008 (HINTED); Q-03 opens; EVT-0106 is proposed fixed at 22:45.
  - REJECT_MICRO_FACT flags the span NON_CANONICAL and later packets treat the detail as UNDETERMINED.
  - DI-1 detects a grey-eyes and brown-eyes pair across two accepted fixture scenes.
- out of scope: DI-5.

### G6 — World mechanics are checkable

**WP-170 Mechanics records and ledgers**
- depends on: WP-080
- build: SUB, RGM, MCH, MCC, RES, CAP, EFF, TRC records; effect-language extensions; resource, effect, trace, and capability ledgers; regime map; DETECTED grants from traces.
- exit criteria:
  - Ilse's binding in SCN-212 costs 60, her reserve falls from 80 to 20, and the lock lapses ten hours after casting.
  - A trace is perceptible to a binder within 30 metres through DETECTED and to anyone present through WITNESSED, and expires after 24 hours.
- out of scope: MC rules.

**WP-180 Mechanics checks, packet group N, autopsy codes**
- depends on: WP-170, WP-160
- build: MC-01 to MC-18; packet group N; AU-80 to AU-84 (deterministic parts); hardness setting with the Mechanics Integrity cap.
- exit criteria:
  - SCN-219 yields MC-05; SCN-240 yields MC-12, and MC-15 because the limit was shown to the reader at 1.04.2.
  - SOFT hardness disables MC-14 and downgrades MC-13 to MINOR; HARD makes MC-14 BLOCKING and caps acceptance readiness at 0.84 when Mechanics Integrity is below 0.95.
  - A scene relying on an UNDETERMINED mechanic field fails extraction with MC-17.
- out of scope: the ontology kit as code.

### G7 — Delivery

**WP-190 CLI and end-to-end**
- depends on: WP-180
- build: all CLI commands; `scripts/e2e.mjs` running the Appendix A and §17.8 flows from fixtures.
- exit criteria:
  - The e2e script reproduces every golden output byte for byte.
  - Two consecutive e2e runs produce byte-identical outputs.
  - Exit codes reflect bands (0 READY, 1 PROVISIONAL or INSUFFICIENT, 2 UNSTABLE or FAILED, 3 contract violation).
- out of scope: UI.

**WP-200 Release v0.1**
- depends on: WP-190
- build: `README.md` with quickstart; `docs/USAGE.md`; final gate; tag `v0.1.0`; push.
- exit criteria:
  - A fresh clone passes `npm ci && npm run gate`.
  - Tag `v0.1.0` exists on the remote and points at the commit whose gate run is recorded in the evidence file.

---

## 8. Verification gate

`npm run gate` runs, in order, stopping at the first failure:

| Stage | Command | Passes when |
| --- | --- | --- |
| 1 format | `prettier --check .` | No unformatted files |
| 2 lint | `eslint .` | Zero errors, zero warnings |
| 3 typecheck | `tsc --noEmit` | Zero errors |
| 4 unit | `vitest run tests/unit` | All pass; count recorded |
| 5 integration | `vitest run tests/integration` | All pass; count recorded |
| 6 build | `tsc -p tsconfig.build.json` | Exit 0 |
| 7 package verify | `node scripts/verify-package.mjs` | `npm pack --dry-run` lists exactly the expected files |
| 8 reproducibility | `node scripts/repro.mjs` | Two clean builds produce identical `dist/` digests |
| 9 end-to-end | `node scripts/e2e.mjs` | All golden comparisons match |

There is no UI in v0.1, so headed browser verification does not apply. It becomes mandatory with the Codex in v0.2.

---

## 9. Open questions (decisions for Patrick)

| ID | Decision | Recommendation | Blocks |
| --- | --- | --- | --- |
| OQ-1 | Create an empty private repository `GILGUY/nsres` on GitHub (no README, no license), then tell me so I can attach it | Create it | WP-000 |
| OQ-2 | Stack: TypeScript only (A-01, A-16), or Python | TypeScript only | WP-000 |
| OQ-3 | Scope lock as in §4: Core plus Mechanics, AI roles as fixtures | Approve | WP-000 |
| OQ-4 | Spec text inside the repo: (a) you export the doc as Markdown and attach it; (b) I pull it inline (large); (c) the repo links to the doc only | (a) | WP-000 |
| OQ-5 | Treat spec Appendix A and §17.8 example values as test-authoritative fixtures, even though the spec calls them illustrative | Approve | WP-070 onward |
| OQ-6 | Story-time resolution: integer minutes from a per-work epoch (A-09) | Approve | WP-050 |
| OQ-7 | Repository private, no license | Approve | WP-000 |

---

## Appendix — handoff payload for the executing agent

```json
{
  "code_target": "GILGUY/nsres (main); session clone /home/claude/nsres",
  "first_package": "WP-000",
  "files_to_create_in_WP-000": [
    "docs/IMPLEMENTATION_STATUS.md", "docs/TEST_EVIDENCE.md", "docs/DECISIONS.md",
    "docs/IMPLEMENTATION_PLAN.md", "docs/contracts/SCOPE.md", "docs/contracts/ARCHITECTURE.md",
    "docs/contracts/DOMAIN.md", "docs/INVARIANTS.md", "docs/PROTOCOL.md", "docs/ENVIRONMENT.md",
    "package.json", "package-lock.json", "tsconfig.json", "tsconfig.build.json",
    "eslint.config.js", ".prettierrc.json", ".prettierignore", "vitest.config.ts", ".gitignore",
    "scripts/verify-package.mjs", "scripts/repro.mjs", "scripts/e2e.mjs",
    "src/index.ts", "src/cli/main.ts", "tests/unit/smoke.test.ts", "tests/integration/smoke.test.ts"
  ],
  "do_not_touch": ["docs/TEST_EVIDENCE.md existing sections (append only)"],
  "do_not_implement": [
    "network calls of any kind in src/",
    "live LLM adapters", "Codex UI", "DI-5", "canon branches", "Datalog engine",
    "graph or vector databases", "non-Gregorian calendars", "Hypocrisy Tax metric",
    "any engine path that sets ACCEPTED, CANON, or PUBLISHED"
  ],
  "contracts": "docs/contracts/*.md and docs/DECISIONS.md A-01..A-16",
  "acceptance": "section 7 exit criteria per package; section 8 gate"
}
```
