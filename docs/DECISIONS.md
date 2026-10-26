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

## WP-010 decisions (domain types and schemas)

Drafted while WP-010 was implemented and recorded before the package closed. Nothing outside
WP-010 depends on them yet. Each cites the spec errata entry (below) that it resolves.

**D-004 — Packet and finding schema construction rule.** Spec B.3 writes only the top level,
`beat`, and `manifestation`, and says the other `$defs` "follow §8.2 and §17.7 field by
field". §8.2, §8.4, and B.3 disagree in places (ERR-2, ERR-3, ERR-4, ERR-10, ERR-11). The
schemas in `src/nsres/domain/schemas.py` are built by these rules:

1. **Names.** Nesting and group names follow B.3. Inside a group, field names follow the §8.4
   example where it shows them, and otherwise the §8.2 name without the group's own prefix
   (`pov_character` → `pov.character`; `active_threads` → `threads.active`;
   `continuity_constraints` → `constraints.continuity`; `required_outcomes` →
   `outcomes.required`).
2. **Requiredness.** A field is required when B.3 or §8.2 marks it REQUIRED. Inside list items,
   the fields the §8.4 example shows are required and fields only §8.2 lists are optional.
   Group N (§17.7 gives no levels): when `mechanics` is present, all seven fields are
   required, lists may be empty, and `mechanics_in_play` has at least one item.
3. **Conditional fields** are enforced with `if`/`then` where the condition is visible inside
   the packet: `gate_record` when FROZEN; `validation.leak_probe_results` when
   `public.threads.hidden` is non-empty; `pov.narrator_horizon` for FIRST_RETROSPECTIVE;
   `pov.narrator_beliefs` when `pov.unreliable` is true; `position.frame_ref` for ANALEPSIS
   and PROLEPSIS; `mode` on READER outcomes. Every `if` lists its keys as required, so an
   absent branch does not satisfy it vacuously. Conditions that need other records (emotional
   entry and exit for the POV; knowledge bounds for non-POV speakers; misdirection;
   first contact) are left to the PK checks of the packet package.
4. **Closed objects.** Every object sets `additionalProperties: false`; maps constrain their
   keys with `propertyNames` patterns.
5. **Where §8.2 conflicts with B.3 or §8.4, B.3 or §8.4 wins:** `validation.pre_draft_checks`
   is the single value ALL_PASS; the §8.2 group M `sources` map lives in the extraction record
   and the packet carries `sources_ref`; `known_information` items carry `channel`, with
   §8.2's `source` optional; UNRELIABLE is the boolean modifier `pov.unreliable`, never a
   mode (§7.4 calls it a modifier); the anachrony frame reference is its own field
   `frame_ref`; handle patterns are the §0.3 per-prefix patterns everywhere, stricter than
   B.3's `^INF-[0-9]+$`, `^RUN-X-[0-9]+$`, and `^FND-`. `sealed.hidden_mechanic_rules` is an
   optional addition for §17.7's "hidden rules go to the sealed section".
6. **Finding schema.** B.4's fields, enums, rule pattern, and both `allOf` clauses are kept as
   written. The `BaseRecord` fields §10.2 gives every finding are added (`rev`,
   `provenance`, `plane`, `tx` required; `gate`, `notes` optional), and `spans` and `repairs`
   are required because §10.2 does not mark them optional (either may be empty).

**Verified by:** `tests/unit/test_schemas.py` — the completed example validates and keeps
every value of the §8.4 example; every B.3 `required` list is kept; each conditional fires
and clears; every object in both schemas is closed; the spec example as printed fails on
exactly seven omitted fields. Falsified if any of those fail.

**D-005 — Resource records use `RSV-`.** §17.4 writes the Resource record as `RES-`, which is
already the §0.3 Resolution record (ERR-1). The code gives resources `RSV-`.
**Verified by:** `tests/unit/test_handles.py::test_resolution_and_resource_handles_do_not_collide`
and the cross-rejection test over every example.

**D-006 — Packet hash domain and number form.** §8.1 defines `packet_hash` as the SHA-256 of
"the canonical whole", which cannot include the hash fields themselves. `packet_hash` covers
the canonical packet with `packet_hash` and `public_hash` removed; `public_hash` covers the
canonical `public` section. Both are written `sha256:<hex>` (the B.3 pattern). In canonical
form a float with an integral value is written as an integer (`6.0` → `6`), as in RFC 8785,
so the bytes do not depend on whether a producer computed a whole number as a float.
**Verified by:** `tests/unit/test_canonical.py` (hash fields excluded; public edits break both
hashes, sealed edits only `packet_hash`; `{"priority": 6.0}` and `{"priority": 6}` hash
equal).

**D-007 — JSON and time conventions for records.** §10.2 uses TypeScript camelCase and
string times; §8 uses snake_case; plan A-09 and OQ-6 fix story-time as integer minutes; §10.5
compares transaction revisions as integers (`tx_from <= 47`) while §10.2 types them as
strings (ERR-8). Records therefore:
- serialize to snake_case JSON (`renderStatus` → `render_status`, `hiddenUntil` →
  `hidden_until`, `offsetMin` → `offset_min`, `detectionConfidence` → `detection_confidence`);
  fields whose names are Python keywords keep their spec names in JSON (`from`, `to`,
  `object`, `class`, `is`);
- hold story-time as integer minutes from the work epoch and transaction time as integer
  model revisions;
- omit an optional field that is unset, and write `null` only for a required nullable field
  (`tx.to`);
- type `Scene.pov.mode` as the §7.4 POV mode (§10.2 says `string`).
Packets keep the §8 display strings for story-time (`"1893-10-15T07:40"`), because the brief
and the B.3 example use them; the packet compiler maps minutes to display form.
**Verified by:** `tests/unit/test_records.py` (lossless round trip for every record type
through canonical bytes; snake_case and keyword names asserted).

**D-008 — A finding has no record status.** §10.2 declares `Finding extends BaseRecord` and
then redeclares `status` with the finding lifecycle values, which TypeScript itself would
reject (ERR-5). The code splits `RecordCore` (every `BaseRecord` field except `status`) from
`BaseRecord`; `Finding` extends `RecordCore` and its `status` is the B.4 lifecycle. Findings
never pass a status gate. **Verified by:**
`tests/unit/test_records.py::test_finding_has_no_record_status` and
`test_finding_record_json_satisfies_the_finding_schema`.

**D-009 — Control-plane entries are not gated records.** §10.2 says gate records and
resolution records "follow the same BaseRecord pattern" (ERR-6). Resolution records have a
§0.3 prefix and pass the INTEGRATION gate, so `ResolutionRecord` is a `BaseRecord`. Gate
records, audit records, extraction records, and validation reports are immutable once
written, have no status lifecycle (a gate record cannot itself need a gate; §10.4 makes the
audit log immutable), and so carry a UUIDv7 but no revision or status. Extraction records
keep their `RUN-X-` handle.

**D-010 — Relation records use `REL-`.** The §3.3 catalog defines a Relation record but §0.3
gives it no prefix (ERR-7). The code uses `REL-` followed by at least four digits, as an
extended prefix, until the spec assigns one. **Verified by:** `tests/unit/test_handles.py`
(`REL-0001` matches only `REL`).

**D-011 — Mechanics additions to the record set.** The §17.4 Artifact is an object entity
with `embedded_mechanics` (mechanics, charges as RSV- resources, state) rather than a new
record type, because the spec gives it no prefix and calls it "an object". The §17.4
effect-language operations (`consume`, `sustain`, `release`, `emit_trace`, `cascade`,
`learn`) are record-level effect types in the same `Effect` union as §10.2's, with their own
closed vocabulary `MechanicsEffectOp`; parsing the textual effect language stays with
`nsres.effects`.

---

## WP-020 decisions (record store, gates, audit)

Recorded before the WP-020 code was written.

**D-012 — Store layout, transactions, and the audit chain.**
1. **Files.** A project directory holds `log/records.jsonl` (the record log), `log/audit.jsonl`
   (the audit log), and `artifacts/sha256/<hex>.json` (the content-addressed artifact store;
   spec §10.4, plan A-05). Both logs are opened in append mode; every line is canonical JSON
   followed by a newline and is fsynced before the call returns.
2. **Transactions.** One store operation is one transaction `tx` (1, 2, 3, ...). Its record-log
   line is `{"tx": n, "rows": [{"type": <class name>, "record": <to_json>}, ...]}`, so the
   rows of one transaction land in one fsynced line. Every row is a record revision, a gate
   record, or a model-version state.
3. **Audit chain.** Every row has exactly one audit line, written after the record-log line.
   An audit line is an `AuditRecord` (spec REQ-5.4.1 fields) extended with `tx`, `ref` (the
   uuid of the row it covers), and `ref_hash` (the content hash of that row). `hash` is the
   content hash of the line without its `hash` field, and `prev_hash` is the previous line's
   `hash`, so editing any audit line, or any record-log row, is detected on verification.
   Kinds: TRANSITION for a record revision or model-version change (from-state `(new)` for a
   record's first row, as the §5.4 table writes it), GATE for a gate record.
4. **Recovery.** A torn or unparsable final line, a transaction without its audit lines, or a
   broken chain makes `Store.open` refuse with `StoreCorruptError` naming the file and line. v0.1
   detects; it does not repair. (Crash repair is not in the plan's WP-020 build list.)
5. **Bitemporal rows.** A revision row stores `tx.from` = its transaction and `tx.to` = null.
   Reads fill `tx.to` from the next revision of the same handle, so the log stays append-only.
6. **Model versions.** `ModelVersion` rows (number, state, opened at tx, and the two counters)
   follow the §5.4 version lifecycle. When a version becomes CONSISTENT it fixes its label
   `canon@r<c>/truth@r<t>`: `t` is the transaction number and `c` counts the transactions so
   far that changed a CANON record (the spec's "canon registry version"). Before then the
   label is `open-<number>`. A gate decision that changes an ACCEPTED or CANON record while
   the version is CONSISTENT or RELEASED opens the next version; the old one stays readable
   through `as_of`.

**D-013 — How the §5.4 record-lifecycle table maps to gate outcomes.**
1. Rows are data (`nsres.store.lifecycle.LIFECYCLE`), one per §5.4 row, and the test suite
   checks them against the spec table.
2. The acceptance gate of a PROPOSAL record is STRUCTURE for telling-plane records,
   INTEGRATION for drafts and resolution records (§0.7 typed gates: "draft acceptance",
   "contradiction resolutions"), and PROPOSAL otherwise.
3. A micro-fact is a reality-plane PROPOSAL with provenance DRAFT_EMERGENT. The CANON gate
   decides it with ACCEPT_AND_REGISTER or REJECT_MICRO_FACT only (§0.7: "decides it with one
   of two codes"), so the general PROPOSAL rows do not apply to it.
4. "Retire" (ACCEPTED or CANON → DEPRECATED) is the REJECT outcome at the gate matching the
   record's status: the gate that accepted it, or CANON for CANON records. §0.7 gives
   retirement no outcome code (ERR-12); the WCS crosswalk's DELETE_GATE row maps to the
   same REJECT. The guard "every dependent re-pointed" is computed: no live record (PROPOSAL,
   ACCEPTED, CANON) may still mention the handle. A successor may be named.
5. An edit is ACCEPT (ACCEPTED records, at the gate that accepted them) or CANONIZE (CANON
   records) with a `revision`: same class, uuid, handle, status, and tier, and `rev` one
   higher. Editing PUBLISHED canon needs `retcon` passages. Every transition into ACCEPTED
   or CANON runs the isolation check: rows 2 and 7 state it, rows 5, 8, and 9 do not
   (ERR-13), and skipping it there would let in content that first acceptance refuses.
6. REVISE and HOLD change nothing and are legal where the gate could decide the record now.
   Every other (status, gate, outcome) combination is refused with a named reason
   (`nsres.store.Refusal`), and a refused request writes nothing.
7. The isolation check ("rule suite passes for the record in isolation") is a required
   constructor argument of the gate console, with no default, so no code path passes a guard
   by omission. The rule registry (WP-030) supplies the real check.

**D-014 — Engine and human write paths.** Engines get an `EngineWriter`: propose a record or a
revised proposal, record a finding, mark a finding RESOLVED, and run the reconciliation
states of the model version. Its `propose` takes `status: Literal[Status.PROPOSAL]`, and it
has no method that takes any other record status or a tier, so asking an engine path for
ACCEPTED, CANON, or PUBLISHED is a `mypy` error and is refused at runtime too (plan A-08).
Every other status change goes through the `GateConsole`, which writes a gate record and its
audit lines. Waivers (REQ-9.1.2): only MAJOR, MINOR, or INFO findings, only with an actor and
a reason, recorded as an override gate record; a BLOCKING finding is refused (OQ-10).

**D-015 — Extensions to WP-010 record types.** WP-010 declared the audit chain as WP-020 work.
WP-020 adds optional fields, without changing any existing field: `AuditRecord.tx`, `ref`,
`ref_hash`; `GateRecord.retcon` (affected published passages) and `GateRecord.successor`;
the `ModelVersion` record; and the closed vocabulary `ModelVersionState` (§5.4). This is an
extension, not a reopening of WP-010: WP-010's exit criteria did not claim them.

**D-016 — The WCS crosswalk as data (OQ-8, OQ-9).** `nsres.wcs` holds the three §0.7
crosswalk tables as data rows, the three closed WCS vocabularies they use (11 artifact
states, 8 gate types, 8 decisions; tested against the §0.7 tables and against
`fixtures/wcs/modules.json`), and one pure function, `import_decision`. It reads and writes
nothing (plan Out list: the WCS I/O adapter is v0.3).
- The CANON state is two rows, chosen by artifact type: `story_spine`, `story_blueprint`,
  and `recut_proposal` map to ACCEPTED and structure-locked (OQ-9); any other CANON artifact
  (a fact, entity, or world rule) maps to CANON.
- `import_decision` refuses RAW and INTAKE (REQ-12.2.2), any artifact whose WCS validator
  status is FAIL (quarantined by WCS), and FORK (canon branches are out of v0.1 scope). A
  SUPERSEDED artifact maps to DEPRECATED and needs its successor. SHIP is not a record
  import; it maps to the SHIP-gate outcome.
- The function returns a mapping, not a write. Whatever later imports WCS material must
  still create records through the store's write paths (D-014), so no import can set a
  status outside the gate API.

---

## Spec errata (proposed for the batch patch at the end of G1; Patrick gates)

Found while building WP-010 against NSRES-SPEC rev 126. Each is preserved here rather than
silently resolved; the decision that resolves it in code is named. None changes behavior the
spec states unambiguously.

| ID | Where | Conflict or defect | Resolved in code by | Proposed spec patch |
| --- | --- | --- | --- | --- |
| ERR-1 | §0.3, §17.4 | `RES-` names both the Resolution record and the Resource record | D-005 | §17.4: Resource (RSV-) |
| ERR-2 | §8.4 | The heading lists the omitted parts as hashes, character states, and emotion; the example also omits `confidence_vector_ref`, `gate_record` (required while FROZEN), and `outcomes.forbidden`. **Verified by:** `test_spec_example_as_printed_fails_on_exactly_its_omissions` (7 errors) | D-004 | Add the three fields to the example, or name them in the heading |
| ERR-3 | §8.2, B.3 | (a) `confidence_vector_ref` REQUIRED in §8.2, not in B.3 `required`; (b) §8.2 group I fields REQUIRED, B.3 `emotion: {type: object}` optional; (c) `pre_draft_checks` a list in §8.2, `enum: [ALL_PASS]` in B.3; (d) §8.2 group M `sources` map vs B.3 `sources_ref`; (e) §8.2 flat names vs §8.4 grouped names; (f) B.3 handle patterns looser than §0.3; (g) §17.7 group N gives no requirement levels | D-004 | Align §8.2 with B.3 and §8.4; add a requirement column to §17.7 group N |
| ERR-4 | §8.2 H | `known_information` lists `source`; §8.4 and §10.2 use `channel`, and §8.2's own example value (WITNESSED) is a channel | D-004 rule 5 | `{inf, statement, confidence, channel, source?}` |
| ERR-5 | §10.2 | `Finding extends BaseRecord` redeclares `status` with incompatible values | D-008 | Declare `Finding` over a status-free base, or rename the field `finding_status` |
| ERR-6 | §10.2 | "gate records … follow the same BaseRecord pattern", but gate records have no prefix and no lifecycle | D-009 | State that gate and audit records are immutable control-plane entries |
| ERR-7 | §0.3, §3.3 | The Relation record has no handle prefix | D-010 | Add `REL-` to §0.3 |
| ERR-8 | §10.2, §10.5 | camelCase fields and string times in §10.2; snake_case in §8; integer revisions in §10.5; minutes in plan A-09 | D-007 | Note in §10.2 that the notation is illustrative and give the JSON naming rule |
| ERR-9 | §4 L6, §8.2 G | SCN-007 Mara's entry state is "frightened, controlled" (L6) and "shaken but composed" (§8.2 G) | Fixture uses §8.2 (fixtures/harrow-house/README.md) | Use one wording in both places |
| ERR-10 | B.4, §10.2 | B.4 omits the `BaseRecord` fields and marks `spans` and `repairs` optional where §10.2 requires them | D-004 rule 6 | Add the fields to B.4 |
| ERR-11 | §7.4, §8.2 D | UNRELIABLE appears in the POV-mode table while being a modifier; §8.2 D writes `narrator_beliefs` CONDITIONAL "(UNRELIABLE)" | D-004 rule 5 (`pov.unreliable`) | Add a `pov.unreliable` field to §8.2 D |
| ERR-12 | §5.4, §0.7 | The record-lifecycle "Retire" row has no outcome code in the §0.7 gate table | D-013 item 4 (REJECT at the gate matching the status) | Add RETIRE to the outcome column, or name REJECT in the §5.4 row |
| ERR-13 | §5.4 | The micro-fact registration row and both "Edit" rows state no rule-suite guard, unlike first acceptance and locking | D-013 item 5 (every transition into ACCEPTED or CANON runs the isolation check) | State the guard in those three rows |

---

## Deviations

(none yet; the WP-010 decisions above resolve spec conflicts and do not deviate from the plan)

---

## Environment facts

See `docs/ENVIRONMENT.md` for the ledger.
