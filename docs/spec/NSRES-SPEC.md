# Narrative State Reconciliation Engine (NSRES) — Specification v0.1

Oct 25, 2026 · @Patrick Gil

## 0. Document control

NSRES-SPEC v0.1.1 is a patch release of the first formal draft (v0.1.0) of the Narrative State Reconciliation Engine (NSRES). The methodology it implements is also called RSSA (Reconciled Story-State Architecture); this spec uses NSRES for both. It defines terms, layers, schemas, engines, and gates. It has not yet been validated by a reference implementation or by experiment.

| Item | Value |
| --- | --- |
| Identifier | NSRES-SPEC (methodology alias: RSSA) |
| Version | 0.1.1 (draft; changes listed in §0.8) |
| Status | Draft for review. No reference implementation. Core thesis untested (see §14). |
| Scope | Long-form fiction: novels, series, screenplays, serials. Partial coverage: interactive fiction, game narrative. |
| Change policy | Semantic versioning. Changing a schema field's meaning or removing a field is a major change. Adding an optional field is minor. Wording fixes are patches. |
| Supersedes | Nothing. First formal statement of the methodology. |

### 0.1 Normative language

MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY carry their RFC 2119 meanings. A conforming software implementation satisfies every MUST. A conforming manual (human-only) practice satisfies every MUST that does not name software, automation, or an engine.

### 0.2 Statement types

Every load-bearing statement in this specification has one of five types. Section 15 audits the high-exposure ones.

| Tag | Type | Meaning | How it fails |
| --- | --- | --- | --- |
| DEF | Definition | Fixes what a term means inside NSRES. | It is ambiguous, circular, or cannot be checked. |
| REQ | Requirement | A rule a conforming system or practice must follow. | It cannot be implemented, or it contradicts another requirement. |
| DD | Design decision | One option chosen among alternatives, with the reason stated. | A better alternative exists. |
| HYP | Hypothesis | An empirical claim not yet tested. | An experiment refutes it. |
| HEU | Heuristic | A rule of thumb with no claim of optimality. | It misleads in common cases. |

### 0.3 Identifier conventions

Every record has two identifiers: a \`uuid\` (UUIDv7, the immutable storage key that all software references use) and a \`handle\` (the prefixed, human-readable ID shown throughout this spec). Neither is ever reused. A retired record keeps both, with status DEPRECATED.

| Prefix | Record type | Example |
| --- | --- | --- |
| CAN- | Canon rule | CAN-014 (no telephone at Harrow House) |
| CHR- | Character | CHR-001 Mara Voss |
| LOC- | Location (sub-locations use a letter suffix) | LOC-001a the study |
| OBJ- | Object | OBJ-001 the ledger |
| GRP- | Group, faction, or public | GRP-001 Kellby village |
| EVT- | Event | EVT-0104 Jonah removes the ledger |
| INF- | Information unit (a proposition) | INF-002 Jonah removed the ledger at 22:40 |
| CLM- | Claim (a proposition asserted or believed by an entity) | CLM-007 Celia says Edmund's heart was weak |
| KG- | Knowledge grant | KG-0031 Mara witnesses INF-006 |
| CE- | Causal edge | CE-0012 EVT-0101 CAUSES EVT-0105 |
| THR- | Thread | THR-02 Jonah's claim |
| NOD- | Node (an event's membership in a thread) | NOD-02-03 |
| SCN- | Scene | SCN-007 |
| BT- | Beat | BT-007-04 |
| RVL- | Reveal record | RVL-02 |
| Q- | Open question (reader-side) | Q-03 what was in Jonah's bundle |
| PKT- | Scene packet | PKT-007-r3 |
| DRF- | Draft | DRF-007-02 |
| FND- | Finding (validation or autopsy) | FND-007-02-05 |
| RUN- | Reconciliation, extraction, or autopsy run | RUN-R-0047 |
| RES- | Resolution record | RES-0019 |

### 0.4 Time notation

- **Story-time (ST).** ISO-8601 in the story's calendar, with a precision tag and an uncertainty window: `1893-10-14T22:40 ±10m`. Non-Gregorian calendars are declared in canon (L1) and mapped to a monotonic integer tick.
- **Narrative-time (NT).** A dotted ordinal `part.chapter.scene.beat`, for example `1.03.2.4`. NT orders presentation. It carries no duration.
- **Discourse-time (DT).** Length of text, in words, per beat, scene, or chapter.
- **Revision-time (RT).** The model version a record or artifact belongs to, written `canon@r12 / truth@r47`.

### 0.5 Running example

All examples use one invented mystery, *Harrow House*, set in Yorkshire in October 1893. Appendix A works it end to end.

| ID | Record | Role |
| --- | --- | --- |
| CHR-001 | Mara Voss, housekeeper | Main POV character |
| CHR-002 | Inspector Teodor Hale, York City Police | Investigator |
| CHR-003 | Lord Edmund Harrow | Dies on the night of 14 October |
| CHR-004 | Jonah Pell, footman | Secretly Edmund's son; removes the ledger |
| CHR-005 | Celia Harrow, Edmund's niece and heir | Poisoner (hidden until the climax) |
| OBJ-001 | The ledger | Records payments to Jonah's mother |
| OBJ-002 | The study key | Normally hangs on the servants' hall board |
| OBJ-003 | The brandy decanter | Poison vector |

### 0.6 Reading paths

| Audience | Read first | Then |
| --- | --- | --- |
| Authors and screenwriters | §1, §2, §4 (each layer's "What" and "Why"), Appendix A | §7, §9 |
| Narrative architects | §2 through §6 | §7 through §9, §13 |
| AI workflow designers | §1, §7, §8, §11 | §9, §14 |
| Knowledge-management researchers | §2, §3, §6, §12 | §10 |
| Systems engineers and developers | §3, §5, §8, §10, Appendix B | §6, §9 |

Sections 16 (World Codex) and 17 (World Mechanics Engine) apply to every audience. Appendix A is the fastest end-to-end orientation, and Appendix B indexes every rule family.

### 0.7 Status, gate, and decision vocabulary

NSRES is the narrative engine of a larger human–AI co-creation control plane (§12). It adopts that control plane's separation of thrust and authority: the LLM supplies thrust (proposals, extractions, drafts) and holds no authority; deterministic engines enforce the rules; a human holds final authority through typed gates.

**Record statuses.**

| Status | Meaning | Set by | Citable by packets? |
| --- | --- | --- | --- |
| PROPOSAL | Exists, not yet approved. Every AI output starts here; human drafts may too. | Author, engine, AI | No |
| ACCEPTED | Approved for working use. A reality record at ACCEPTED is reconciled and citable but still revisable through the gate that accepted it. Telling records (L2–L4) and drafts top out here. | PROPOSAL, STRUCTURE, or INTEGRATION gate | Yes |
| CANON | A locked reality record (L1 records, L5 events, L9 facts, registered micro-facts). Changing it needs the CANON gate; changing PUBLISHED canon also needs a RETCON record. | CANON gate | Yes |
| REJECTED | Declined; kept for audit | Any gate | No |
| SLUSHED | Declined for this work but preserved in the slush archive for possible reuse | PROPOSAL gate | No |
| DEPRECATED | Retired after being ACCEPTED or CANON; keeps its identifiers | Gate matching its status | No |

PUBLISHED is a tier on CANON records whose text is already released. It is not a separate status.

**Typed gates.**

| Gate | Decides | Typical items | Outcomes |
| --- | --- | --- | --- |
| PROPOSAL | Whether a proposal enters the work at all | AI-extracted canon candidates; bridge events; decomposition proposals; autopsy correction proposals | ACCEPT, REVISE, REJECT, SLUSH |
| STRUCTURE | The shape of the telling | L2 outline, thread ranks, reveal plan; L3 scenes; L4 beats; packet freeze | ACCEPT, REVISE, REJECT |
| INTEGRATION | Whether a change merges into the reconciled model or the manuscript | Contradiction resolutions (RES); draft acceptance; prose–model disagreements (§4.18); the RELEASED model tag | ACCEPT, REVISE, REJECT |
| CANON | Whether a reality record is locked | L1 records; L5 events and facts; micro-facts; RETCON records | CANONIZE, REVISE, REJECT |
| SHIP | Whether a segment is released | Chapter, episode, or volume release; the PUBLISHED tier | SHIP, HOLD |

The CANON gate is the corpus's CANON\_GATE, the gate the production bible builder requires for every entry.

**Micro-fact decisions (the Micro-Canon Rule).** A FREE-class detail that a drafter invents and autopsy captures (§3.6, §9) is a micro-fact PROPOSAL. The CANON gate decides it with one of two codes.

| Code | Effect |
| --- | --- |
| ACCEPT\_AND\_REGISTER | The detail is registered in Story Reality with a new uuid and handle, at status CANON. Later packets treat it as LOCKED wherever it applies. |
| REJECT\_MICRO\_FACT | The detail is not registered. Its prose span is flagged NON\_CANONICAL, and a revision task opens unless the author marks the span keep-non-binding. Later packets treat the detail as UNDETERMINED. |

**WCS crosswalk (ACCEPTED, v0.1.1).** When NSRES runs inside the Writing-Craft System (§12.2), the WCS runtime's 11 artifact states, 8 gate types, and 8 gate decisions map to NSRES as below. Sources, all read in full: `showrunner_production_handler.py` (its `ArtifactState` and `GateType` enums), PROJECT\_FULL\_EXPLICATION, and `modules.json` version 1.0-runtime. The state table splits WCS CANON into two rows, because NSRES draws a line there that WCS does not. Patrick accepted it at the plan gate on 2026-10-25 (decisions OQ-8 and OQ-9).

| WCS artifact state | NSRES status | Rule |
| --- | --- | --- |
| RAW | none | NSRES never reads RAW material. It stays in WCS `00_RAW`, hashed and unchanged. |
| INTAKE | none | A classified working copy inside WCS. NSRES does not import it. |
| PROPOSAL | PROPOSAL | Imported as a PROPOSAL record, never as a fact (REQ-12.2.2). |
| REVISED\_PROPOSAL | PROPOSAL, next `rev` | The revision counter increments. The earlier attempt keeps its row. |
| ACCEPTED | ACCEPTED | Same meaning: approved for working use. |
| CANON: a fact, entity, or world rule | CANON | A locked reality record. |
| CANON: story\_spine, story\_blueprint, or recut\_proposal | ACCEPTED, structure-locked | WCS calls a locked telling artifact CANON. NSRES telling records top out at ACCEPTED. See the state-semantics note in §12.2. |
| SLUSH | SLUSHED | Only the name differs. |
| REJECTED | REJECTED | Kept for audit. |
| SUPERSEDED | DEPRECATED, with a successor reference | Identifiers are kept, and the successor is named. |
| FORK | canon branch (§12.8) | Outside the v0.1 build scope. |
| SHIP | SHIP-gate outcome; the PUBLISHED tier on the CANON records the released segment renders | The released draft itself stays ACCEPTED. |

| WCS gate type | NSRES gate | Rule |
| --- | --- | --- |
| INTAKE\_GATE | none | Approves or corrects classification inside WCS. Admission to NSRES still needs the NSRES PROPOSAL gate. |
| PROPOSAL\_GATE | PROPOSAL | Same decision: whether a proposal enters the work. |
| REVISION\_GATE | PROPOSAL, on the next `rev` | WCS opens it when a module whose normal gate is PROPOSAL\_GATE emits a REVISED\_PROPOSAL. By the module contracts' wording, a revision of a STRUCTURE\_GATE or INTEGRATION\_GATE output still requests that gate. |
| STRUCTURE\_GATE | STRUCTURE | Locks a spine, blueprint, or presentation order. In NSRES the result is ACCEPTED and structure-locked, not CANON. |
| CANON\_GATE | CANON | One candidate per gate, never batched (production-bible-builder's `each_canon_candidate_requires_gate`). |
| INTEGRATION\_GATE | INTEGRATION | Merges prose edits into the working draft. Edits to ACCEPTED NSRES text follow §12.3: a new draft revision, with L14 re-validating the changed spans. |
| DELETE\_GATE | the REJECT outcome of the gate that holds the record | WCS needs its own typed confirmation to reject. Inside WCS, NSRES stores that confirmation with the REJECT outcome. Slushing is not a delete. |
| SHIP\_GATE | SHIP | Releases a segment. WCS takes a package snapshot (`snapshot_on_ship`). |

| WCS gate decision | NSRES outcome |
| --- | --- |
| ACCEPT | ACCEPT |
| ACCEPT\_AS\_CANON | ACCEPT, then a separate CANON-gate decision (CANONIZE). NSRES never combines the two in one confirmation. |
| REVISE | REVISE |
| REDIRECT | No outcome. The record stays PROPOSAL and the handler routes it again. |
| FORK | A canon branch (outside the v0.1 build scope) |
| SLUSH | SLUSH |
| REJECT | REJECT (through DELETE\_GATE inside WCS) |
| REVERT | A new PROPOSAL that restores an earlier revision. Nothing is erased. |

WCS requires exact typed confirmation at its STRUCTURE, CANON, INTEGRATION, DELETE, and SHIP gates, and a failed confirmation leaves the gate open and the state unchanged. A gate record that NSRES imports from WCS carries the confirmation text.

### 0.8 Changes in v0.1.1

v0.1.1 is a patch release. A peer AI session's handoff proposal (testimony only) prompted it. Every change below was checked against the spec text or a WCS source before it was applied.

1. §0.7: the WCS crosswalk above (PROPOSAL).
2. §2.4 and L9: the DETECTED knowledge channel, previously defined only in §17.5, added to the CIS definition and the channel table.
3. §6.8: the heading repaired, and "Hidden is not absent" restored as its own paragraph.
4. §10.2: SUSTAIN added to `Beat.type`, DETECTED to `Channel`, and `status` to `Finding` (matching B.4).
5. §12.2: the table rebuilt against `modules.json` 1.0-runtime. It now lists all 23 entries (spark-rewrite-triage and the handler were missing), splits advanced-camera-pov from pov-shot-selection, corrects four phases (sandbox-slush-pile, scene-performance-director, advanced-camera-pov, diegetic-document-weaver), copies artifact names and default gates from the contract, keeps the NSRES gate in its own column, records the state-semantics conflict, and adds REQ-12.2.2.
6. §15.3: rescored at 0.80, INSUFFICIENT. The Source Grounding cap binds.
7. §0.7 and §12.2: the crosswalk accepted and the CANON-vocabulary conflict resolved in favor of NSRES (Patrick's plan gate, 2026-10-25).
8. §9.1 and B.4: REQ-9.1.2 added, so a BLOCKING finding cannot be waived (Patrick's plan gate, 2026-10-25).

## 1. Purpose, scope, and core thesis

NSRES exists to turn long-form AI drafting into a rendering step. The model writes each scene from a validated slice of a fully reconciled story-state, instead of from a narrative-order outline whose gaps it must fill by guessing.

### 1.1 Problem statement

A flat outline lists what the reader sees, in the order the reader sees it. It omits most of what a drafter needs to write a scene without inventing load-bearing facts. Each omission produces a predictable defect class.

| # | Missing from a flat outline | What the drafter does instead | Resulting defect class |
| --- | --- | --- | --- |
| 1 | Offscreen events between scenes | Invents causes on the spot | Unmotivated events; backstory that changes between chapters |
| 2 | Who knows what, and since when | Lets characters know what the reader knows | Knowledge leaks; impossible knowledge |
| 3 | Where every character is | Places characters wherever the scene needs them | Impossible movement; one person in two places |
| 4 | Object custody | Produces objects when convenient | Objects in two places; objects that return after destruction |
| 5 | What the reader has already been told | Re-explains, or assumes context the reader lacks | Redundancy; comprehension gaps; premature reveals |
| 6 | Hidden threads | Ignores them, or exposes them | Twists that collapse on rereading; leaks |
| 7 | Small facts introduced by earlier prose | Forgets them, or restates them differently | Continuity drift |
| 8 | Change propagation | A revised chapter 4 does not update chapter 19 | Silent contradictions after revision |

A larger context window does not remove these problems. Even when a whole manuscript fits in context, offscreen reality is not in the manuscript, so the model has nothing to attend to. Facts scattered across 100,000 words are also attended to unevenly (HYP; tested indirectly by H2).

### 1.2 Core thesis

**H0 (HYP).** In long-form AI-assisted fiction, continuity, causality, and information-state defects come mainly from the absence of a reconciled story-state at generation time, not from prompt wording. Supplying each generation call with a scene packet extracted from a reconciled state reduces these defects more than better prompts applied to a flat outline.

Sub-hypotheses, each tested in §14:

| ID | Statement | Falsified if |
| --- | --- | --- |
| H1 | Defects per 1,000 words fall under packet conditions versus flat-outline conditions with matched token budgets. | No significant reduction at matched budget. |
| H2 | The reduction is not explained by information volume alone. | Unreconciled notes of equal length perform as well as packets. |
| H3 | Hidden-thread leakage falls when hidden facts are withheld and replaced by behavioral constraints (suppression by abstraction), compared with disclosing them plus a "do not reveal" instruction. | Leakage is equal or lower under disclosure. |
| H4 | Author time spent fixing continuity per chapter falls once the model is reconciled. | Fix time does not fall, or modeling time exceeds the savings. |

Status: untested. Until §14 is run, NSRES SHOULD be described as a methodology with a falsifiable rationale, not as a proven improvement.

H0 does not claim that prompt quality is irrelevant. It does not claim that NSRES improves style, voice, or literary merit. It does not claim that models cannot track state without NSRES.

### 1.3 Prior art and position

NSRES formalizes distinctions with long histories. Its claim is integration into a generation pipeline, not invention of the underlying ideas.

| Source | Idea | How NSRES uses it |
| --- | --- | --- |
| Russian Formalism: fabula vs. syuzhet | The chronological events of a story versus their arrangement in the telling | The Reality plane and Telling plane (§3.1) are this pair, made into data |
| Genette's narratology | Order, duration, frequency, focalization | Narrative-time mapping (§2.2) and POV rules (§7.7) |
| Series bibles; film continuity supervision | Hand-kept canon and continuity logs | Canon registry (L1) and validation (L14), made queryable and rule-checked |
| Timeline tools for writers | Chronological event views | Truth Timeline (L5), extended with knowledge propagation and reader state |
| Plan-based story generation research | Events with preconditions, effects, and causal links | Event model (§3.3) and causal edges (§2.3) |
| Temporal reasoning: Allen's interval algebra; simple temporal networks | Qualitative and metric constraints on intervals | Temporal placement and consistency checking (§6.2) |

What is specific to NSRES:

1. A Reader Knowledge Timeline kept separate from character knowledge, tracked both as plan and as actual.
2. The scene packet as a frozen, hashed generation contract.
3. Suppression by abstraction: hidden facts reach the drafter only as behavior.
4. An autopsy loop that feeds facts first introduced in prose back toward canon through a human gate.

### 1.4 Scope

| Coverage | Includes |
| --- | --- |
| In scope | Long-form prose; screenplays and teleplays (camera POV); serialized and multi-volume works; shared universes (many works, one canon); human-only drafting with packets as writer briefs; AI drafting |
| Partial | Interactive fiction and games (reader state becomes player state; branching needs canon branches, §12.8); time-travel and non-linear-reality fiction (needs per-character personal time, §13) |
| Out of scope | Prose style and voice generation (NSRES references a voice profile but does not define one); judging aesthetic quality; story-structure theory (NSRES is structure-agnostic); automated plot invention as a goal |

### 1.5 Design principles

| ID | Principle | Operational consequence |
| --- | --- | --- |
| P1 | Reality before telling | No scene is extracted until the events it renders, and their preconditions, exist in the Truth Timeline and reconcile. |
| P2 | Single source of truth | The Truth Timeline (L5) is the only authoritative record of what happened. Every other timeline is a projection of it. |
| P3 | Derive, never duplicate | Character, location, object, and information timelines are regenerated from L5. Direct edits to them are rejected or redirected to L5 events. |
| P4 | Explicit unknowns | A fact is TRUE, FALSE, or UNDETERMINED at a given story-time. Silence means UNDETERMINED, never FALSE. |
| P5 | Least necessary information | The drafter receives what the scene needs, plus constraints. Hidden facts are withheld by default and represented as behavior (DD; tested by H3). |
| P6 | Separation of thrust and authority | AI supplies thrust: proposals, extractions, drafts. It holds no authority. Only typed human gates (§0.7) move a record to ACCEPTED or CANON, including canon, reveal plans, thread ranks, and contradiction resolutions. |
| P7 | Validation at every boundary | Every transition that changes ACCEPTED or CANON state runs the rule suite. A failed MUST rule blocks the transition. |
| P8 | Traceability | Every packet field cites the records it came from. Every finding cites a text span and a model record. |
| P9 | Revision is propagation | Every gate decision that changes an ACCEPTED or CANON record triggers impact analysis. Dependent packets become STALE, and dependent accepted drafts are flagged. |
| P10 | Prose can teach the model | Facts that first appear in prose are captured as micro-fact proposals and decided ACCEPT\_AND\_REGISTER or REJECT\_MICRO\_FACT (§0.7). Nothing enters canon silently. |

## 2. Formal definitions

Every term below is defined by what it contains, how it is computed, and which component produces and consumes it. All definitions are type DEF unless tagged otherwise. Where a term could be confused with a neighbor, the distinction is stated.

### 2.1 Reality terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Story Reality** (DEF-01) | The complete set of entities, events, facts, and relations that are true inside the fiction, independent of whether or when they are told. Formally SR = (X, E, F, R, C): entities, events, facts, relations, and the canon rules C they must satisfy. | L1 records, L5 events, and the derived L6–L9 projections | Authors and the Reconciliation Engine → Scene Extraction Engine, validators |
| **Reality Layer** (DEF-02) | Any layer whose records assert what is true in-world: L1, L5, and L6–L9. Contrast with Telling layers (L2–L4, L10–L12) and Rendering/Validation layers (L13–L15). A reality record never references narrative-time directly; only telling records do. | A `plane: reality` tag on every record | Schema → all engines |
| **Truth Model** (DEF-03) | The rule set that decides whether a proposition is true at a story-time. It fixes: three-valued truth (TRUE, FALSE, UNDETERMINED); facts holding over intervals; claims kept separate from facts; canon precedence for conflicts; persistence rules; the invention policy for undetermined detail. Full semantics in §3.4. | Engine semantics plus L1 configuration records | Canon Registry → every check |
| **Entity** (DEF-04) | A persistent, identifiable thing with state over time: character, location, object, or group. Its identity lives in L1; its state lives in L5 effects and L6–L8 projections. | CHR-, LOC-, OBJ-, GRP- records | Canon Registry → all layers |
| **Event** (DEF-05) | A record of something that happens in Story Reality over a story-time interval, with participants, a location, preconditions, and effects. Events are the only mechanism by which state changes. | EVT- record in L5 | Authors, lifting, bridge proposals → projections, extraction |
| **Fact / Information Unit** (DEF-06) | A proposition about Story Reality with a truth interval: subject, predicate, object, qualifiers, valid-from, valid-to. Example: INF-002 = (CHR-004, removed, OBJ-001, from LOC-001a, at 1893-10-14T22:40). | INF- record in L9 | Event effects → knowledge tracking, reveal plans |
| **Claim** (DEF-07) | A proposition that an entity asserts or believes, stored with its speaker or holder and with its own truth value. A lie is a claim whose content is FALSE. A rumor is a claim whose origin is uncertain. Claims never change world state; they change only the holders' information states. | CLM- record linked to an INF- or to a false proposition | Event effects (speech, writing) → L9, L10 |
| **World Information State, WIS(t)** (DEF-08) | The set of all facts TRUE at story-time t, each paired with the entities that hold it at t: WIS(t) = {(f, holders(f, t)) : truth(f, t) = TRUE}. It is ground truth plus its distribution. No character or reader holds all of it. | Computed view over L5 and L9 | Projection engines → extraction, checks |
| **Offscreen Activity** (DEF-09) | Any L5 event that no scene renders at the narrative position where it occurs. Subclasses: IMPLIED (the reader can infer it from rendered effects); DEFERRED (rendered later, e.g. confession or flashback); CAUSAL\_UNRENDERED (never shown, but a cause of rendered events); AMBIENT (routine activity that only constrains positions and availability). Offscreen events must reconcile exactly as onscreen ones do. | `render_status` on each event | Telling map → L10 hidden-causality checks |
| **Hidden Causality** (DEF-10) | A causal edge (cause → effect) whose effect is rendered at narrative position n while the cause is not in the Reader Information State at n. It is legitimate only if a reveal record or a permanent-mystery record covers the cause. Otherwise it is a defect: an unmotivated event. | Computed flag on causal edges, per NT position | L10 engine → findings |

### 2.2 Time terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Story-Time** (DEF-11) | The in-world chronological axis. Each event occupies an interval \[start, end\] with a precision (minute, hour, day, season) and an uncertainty window. Order on this axis defines causality and state. | ST fields and temporal constraints on events | Authors, Temporal Constraint Engine → all reality checks |
| **Narrative-Time** (DEF-12) | The ordinal axis of presentation: the position at which a beat, scene, or chapter appears in the text, written part.chapter.scene.beat. It has order but no duration. Text length is tracked separately as discourse-time (words). | NT positions on scenes and beats | Narrative Planner → L10, extraction |
| **Telling Map** (DEF-13) | The many-to-many relation between events and the narrative positions that render them. One event can be rendered several times (retellings, multiple POVs). One scene renders many events. Where story order and narrative order disagree, the mismatch is analepsis (flashback) or prolepsis (flash-forward). | Join records (event, scene, beat, render mode) | Planner and extraction → hidden-causality and reveal checks |
| **Revision-Time** (DEF-14) | The version axis. Every record carries a story-time validity and a transaction revision, so the system can answer both "what was true at 22:40" and "what did the model say at revision 31". | Bitemporal columns (§10.5) | Version Store → audit, rollback, diffs |

### 2.3 Thread and structure terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Thread** (DEF-15) | A connected set of events in Story Reality, linked by causal edges and organized around one dramatic question or line of activity (an investigation, a concealment, a romance, a plan). A thread exists in reality whether or not any of it is told. | THR- record plus member nodes | L2 register, authors → extraction, pressure, checks |
| **Node** (DEF-16) | One event's membership in one thread, with a role: ORIGIN, ESCALATION, TURN, CONVERGENCE, DIVERGENCE, REVEAL\_TARGET, DORMANT, RESOLUTION. One event can be a node in several threads; it is then a convergence point. | NOD- record (thread, event, role, order in thread) | L2/L3 authoring → extraction, priority |
| **Causal Chain** (DEF-17) | An ordered sequence e1 → e2 → … → ek in which each link is a typed causal edge (CAUSES, ENABLES, MOTIVATES, PREVENTS, INFORMS) with a written justification. Validity requires each cause's effect-time to be no later than its successor's start, and any enabling state to persist until the successor begins. | CE- edges in the causal graph | Authors, lifting → hidden-causality, cycle checks |
| **Narrative Thread** (DEF-18) | The projection of a thread onto narrative-time: the subset of its nodes that some scene renders, in narrative order. It is the part of the thread the reader can follow. A thread with no rendered nodes is wholly offscreen. | Computed from thread nodes and the telling map | L10 engine → pressure, priority |
| **Visible Thread** (DEF-19) | A thread whose existence is in the Reader Information State at position n. The reader knows this line of activity exists, even if they lack some of its events. Visibility is evaluated per position. | Per-position visibility map | L10 → extraction |
| **Hidden Thread** (DEF-20) | A thread whose existence, or whose load-bearing nodes, are deliberately absent from the Reader Information State at position n under a registered reveal record. It can be hidden until its reveal and visible afterwards. A thread never revealed but driving rendered effects needs a permanent-mystery record, or it fails the hidden-causality rule. | Per-position visibility map plus RVL- records | L2 reveal plan, L10 → extraction (suppression) |
| **Primary Thread** (DEF-21) | The thread carrying the work's central dramatic question. Its resolution ends the work or volume. Exactly one SHOULD exist per volume. | `rank: primary` | Author (human gate) → extraction priority |
| **Secondary Thread** (DEF-22) | A thread with its own dramatic question that intersects the primary thread at one or more convergence nodes. It resolves on page, or carries an explicit deferral to a later volume. | `rank: secondary` | Author → extraction priority |
| **Tertiary Thread** (DEF-23) | A thread that carries background world and environmental dynamics, texture, motive, or logistics, and feeds causes into higher-ranked threads. It may be mostly offscreen. On-page resolution is not required. Review signals (HEU): a tertiary thread rendered in more than 15% of scenes, or a secondary thread with no convergence node, SHOULD trigger a rank review. | `rank: tertiary` | Author → extraction priority |
| **Scene** (DEF-24) | A contiguous span of narrative-time that presents a bounded story-time interval, at a bounded set of locations, through one POV configuration, and that changes narrative state. A span that changes no world, character, or reader state is an inert-scene defect candidate, unless its beats are declared SUSTAIN beats. | SCN- record in L3 | Planner → extraction |
| **Beat** (DEF-25) | The smallest unit of change within a scene: one action, exchange, perception, revelation, decision, or reversal that alters world, character, or reader state. Exception: in ambient, mood, or montage sequences, a declared SUSTAIN beat holds a state instead of changing it. A beat binds to zero or more events. A beat with zero events changes only reader state (for example, description that plants a clue). | BT- record in L4 | Planner → extraction, beat coverage checks |

### 2.4 Information-state terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Narrative State, NS(n)** (DEF-26) | The state of the telling at narrative position n: the Reader Information State, open questions, the thread visibility map, setups awaiting payoff, active dramatic-irony gaps, and the narrative pressure vector. It is the telling's counterpart of world state. | Computed view in L10 | L10 engine → extraction |
| **Reader Information State, RIS(n)** (DEF-27) | The propositions the text has given the reader by position n, each with a delivery mode: STATED, SHOWN (rendered so the reader observes it), IMPLIED (a competent reader infers it), HINTED (made possible, not likely), MISLED (a deliberately induced false belief). Kept as two tracks: RIS\_plan (what the reveal plan intends) and RIS\_actual (what autopsy finds the accepted text delivers). Their difference is a defect signal. | L10 delivery records | Planner (plan), Autopsy (actual) → extraction, leak checks |
| **Character Information State, CIS(c, t)** (DEF-28) | The propositions character c holds at story-time t. Each carries a source (a knowledge grant), a channel (WITNESSED, TOLD, READ, INFERRED, RUMOR, ASSUMED, and DETECTED when world mechanics are in play, §17.5), a confidence (CERTAIN, BELIEVED, SUSPECTED), and a truth value. CIS can contain false beliefs. A character acting on p at t requires p in CIS(c, t') for some t' ≤ t. | Computed from KG- records in L9 | Knowledge Propagation Engine → POV filter, knowledge checks |
| **Group Information State** (DEF-29) | CIS for a group, faction, or the public ("the village", "the press"). Used for common knowledge, so that public facts need not be granted to each member individually. Members inherit group knowledge only if canon says so. | GRP- holder in KG- records | L9 → checks |
| **Knowledge Grant** (DEF-30) | An event effect that adds a proposition (or a claim) to a holder's information state, with channel, confidence, and time. It is the only way CIS changes. Forgetting is a grant with negative polarity and is rare. | KG- record | Event effects → L9 |
| **Dramatic-Irony Gap** (DEF-31) | A proposition the reader holds that the POV character does not (reader ahead), or one the POV character holds that is deliberately kept from the reader (reader behind, a mystery gap). Reader-behind gaps in close-POV narration require explicit narration rules (§7.7). | Computed per scene from RIS and CIS | L10 → POV rules, drafting constraints |

### 2.5 Process terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **State Reconciliation** (DEF-32) | The process that takes the ACCEPTED and CANON records (plus PROPOSAL records, as dry runs only), solves temporal placement, computes derived states, runs the rule suite, and returns either a CONSISTENT model version or a list of contradictions with candidate repairs. It is deterministic and idempotent: the same inputs give the same output. | RUN-R- record plus report | Reconciliation Engine → human gate, model version |
| **Narrative Extraction** (DEF-33) | The function SEE(SR, NS(n−1), s) → P. Given reconciled Story Reality, the narrative state before scene s, and the plan for s, it selects relevant events, facts, and states; filters them through perception, POV, and reveal rules; turns hidden facts into behavioral constraints; and states the scene's required outcomes as state deltas. | RUN-X- extraction record | Scene Extraction Engine → packet |
| **Scene Packet** (DEF-34) | A frozen, hashed, versioned, self-contained generation contract for one scene. It holds everything the drafter is permitted and required to use, and excludes what the drafter must not reveal (unless informed-drafting mode is enabled). Full schema in §8. | PKT- record | Extraction → drafting, validation, autopsy |
| **Narrative Autopsy** (DEF-35) | Post-generation analysis of drafted text. It extracts the assertions the text actually makes, aligns them to the packet and the model, classifies each, and emits findings, scores, an RIS\_actual update, drift measurements, and proposals for canon changes. Full design in §9. | RUN-A- record plus findings | Autopsy Engine → human gate, L10, L1/L5 proposals |

### 2.6 Integrity and defect terms

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Continuity Integrity** (DEF-36) | A property of a draft, or a whole manuscript, relative to a model version. It holds when: (1) no assertion contradicts an ACCEPTED or CANON fact at the scene's story-time; (2) no character displays knowledge outside its CIS; (3) no proposition enters RIS earlier than its reveal record allows; (4) every rendered effect's cause is in RIS or covered by a reveal or permanent-mystery record. Binary integrity means zero BLOCKING findings on these four conditions. | Integrity score and status per draft and per manuscript | L14, L15 → acceptance gate |
| **Continuity Drift** (DEF-37) | Accumulated divergence between the text and the model across many scenes, where no single scene triggers a blocking finding. Sources: unregistered emergent facts, slowly shifting attribute descriptions, time slippage from implied durations, and RIS\_actual moving away from RIS\_plan. Measured by the drift indices in §9.4. | Drift index time series | L15 → planner, author |
| **Narrative Pressure** (DEF-38, HEU) | A per-position vector estimating unresolved tension: open questions weighted by stakes; story-time distance to known deadlines; threats near the POV character; outstanding setups; dramatic-irony gaps. Formula in §7.8. It is a planning aid, never a quality score. | Vector per NT position | L10 engine → thread priority, planner |
| **Timeline Convergence** (DEF-39) | A story-time interval where two or more threads share a node, or two or more tracked entities share a location with the possibility of interaction. Contradictions concentrate here, and extraction must load multi-thread state here. | Computed convergence records | Projection engines → extraction, checks |
| **Timeline Divergence** (DEF-40) | A point where one trajectory splits: characters part company, a fact becomes known to some holders and not others, or one thread spawns another. Not the same as a Canon Branch, which is a version-control fork of Story Reality itself (§12.8). This spec never uses "divergence" for branches. | Computed divergence records | Projection engines → planner |
| **Finding** (DEF-41) | One detected problem, with rule ID, severity, evidence (text span and model records), detection confidence, and proposed repairs. Severities: BLOCKING (prevents acceptance), MAJOR (requires a decision), MINOR (fix when convenient), INFO (no action required). | FND- record | Validators, autopsy → gate |
| **Invention Policy** (DEF-42) | The classification of detail into LOCKED (must come from the packet), CONSTRAINED (may be invented inside stated bounds), and FREE (may be invented, then registered by autopsy). Defaults in §3.6. | Policy block in each packet | Canon defaults plus scene overrides → drafter, validators |

### 2.7 Corpus terms adopted

These terms come from the corpus control plane that NSRES belongs to. Each is given an operational definition here so it can be checked like any other term.

| Term | Operational definition | Represented as | Produced by → consumed by |
| --- | --- | --- | --- |
| **Hidden Event Pressure** (DEF-43) | The influence a hidden thread's offscreen events exert on a visible scene — on characters' behavior, atmosphere, and subtext — without delivering the hidden facts. Operationally: the set of SUPPRESSED facts active in the scene's window, each with the participants it affects, plus the manifestations derived from them by SU-2 (§7.6). Its magnitude per scene is the stakes-weighted count of active suppressed facts. | `hidden_threads` block of the packet (§8) | L9 secrets register, L11 → drafter, leak probes |
| **Epistemic Mask** (DEF-44) | The pair of filters applied to Story Reality for one scene. The character mask is the POV's and each participant's CIS, bounding interiority, dialogue, and action. The reader mask is RIS(n−1) plus the reveal plan, bounding what the text may deliver. Computed by filtering stages 5–7 (§5.3). | `known_information`, `unknown_information`, `forbidden_revelations` blocks of the packet | L9, L10, L11 → packet |
| **Micro-fact** (DEF-45) | A FREE-class detail first introduced by a draft (an object on a table, the name of the inn's dog) and captured by autopsy. Under the Micro-Canon Rule, every micro-fact is a PROPOSAL decided at the CANON gate as ACCEPT\_AND\_REGISTER or REJECT\_MICRO\_FACT (§0.7). | INF or entity record with provenance DRAFT\_EMERGENT | L15 → CANON gate → L1, L5 |
| **Causal DAG** (DEF-46) | The causal graph of L5, with events as vertices and causal edges as arcs, required to be acyclic (RC-06). Every causal chain (DEF-17) is a path in it. | CE- edges | C3, C8 → hidden-causality checks, extraction |
| **Separation of Thrust and Authority** (DEF-47) | The division of roles that P6 enforces. Thrust is probabilistic generation by an LLM, which produces PROPOSAL records only. Authority is the right to set ACCEPTED or CANON status, held only by typed human gates. Enforcement is the deterministic engines, which validate every proposal before it reaches a gate. | `provenance` and `status` on every record | All components → gates |

**Corpus thread labels mapped to NSRES axes (DD).** NSRES gives every thread two independent properties: a rank (primary, secondary, tertiary) and a visibility evaluated at each narrative position (visible, hidden). The corpus's four thread labels map onto these axes as follows.

| Corpus label | NSRES axis | NSRES value | Note |
| --- | --- | --- | --- |
| Visible Thread | Visibility | VISIBLE at position n (DEF-19) | "On-screen action" in corpus usage corresponds to the FOREGROUND extraction role (§7.8) |
| Secondary Thread | Rank | SECONDARY (DEF-22) | Can be visible or hidden at any position |
| Tertiary Thread | Rank | TERTIARY (DEF-23) | Includes background world and environmental dynamics |
| Hidden Thread | Visibility | HIDDEN at position n (DEF-20) | Any rank; the source of Hidden Event Pressure |

Reason for two axes: importance and visibility change independently. THR-02 (Jonah's claim) is SECONDARY and HIDDEN until 2.14, then SECONDARY and VISIBLE. A single label set cannot express that transition.

## 3. Foundational model

NSRES models three domains — Reality, Telling, and Rendering — joined by explicit mapping relations. Every defect is defined as a mismatch inside one domain or between two of them, which is what makes defects detectable by rule.

### 3.1 The three domains and the control plane

| Domain | Question it answers | Layers | Primary axis | Authoritative record |
| --- | --- | --- | --- | --- |
| Reality | What is true, and what happened? | L1, L5, L6–L9 | Story-time | L5 Truth Timeline, constrained by L1 canon |
| Telling | What is presented to the reader, in what order, through whose view? | L2, L3, L4, L10, L11, L12 | Narrative-time | L3 scene plan and the L10 reveal plan |
| Rendering | What does the text actually say? | L13, L14, L15 | Text spans | Accepted drafts |
| Control (spans all) | Who may change what, in which version, and did it pass? | — | Revision-time | Version Store, Rule Registry, Audit Log, gate records |

The Telling domain reads from Reality but never writes to it, except through proposals that pass a human gate. The Rendering domain reads only from packets. Autopsy reads rendering and writes proposals to the other two domains.

### 3.2 Defect classes as domain mismatches

| Mismatch | Example in *Harrow House* | Detected at |
| --- | --- | --- |
| Reality-internal | The ledger is in Jonah's room and in the study at 23:00 | L5 reconciliation |
| Reality vs. Telling | The scene plan puts Hale in the servants' hall at 07:40 while L5 has him at Kellby station | L3/L5 reconciliation; extraction |
| Telling-internal | Jonah's parentage is revealed before the clue the reveal depends on | L10 reconciliation |
| Telling vs. Rendering | The draft says the bundle was the ledger; the packet forbids it | L14, L15 |
| Reality vs. Rendering | The draft calls Hale "of Scotland Yard"; canon says York City Police | L14, L15 |
| Rendering-internal | Two accepted scenes give Mara grey eyes and brown eyes | L15 drift analysis |

### 3.3 Primitive records

All layers are built from eight record types. Full field definitions are in §10.2; this table fixes the minimum.

| Record | Required fields | Optional fields | Mutability |
| --- | --- | --- | --- |
| Entity (CHR, LOC, OBJ, GRP) | id, kind, canonical\_name, status | aliases, fixed\_traits, defaults for persistent attributes, notes | Identity immutable; attributes change only through event effects |
| Event (EVT) | id, type, st\_start, st\_end, precision, location, participants (with roles), effects, status, provenance | preconditions, temporal constraints, causal edges, uncertainty window, visibility, thread nodes | New revision per change; history kept |
| Fact (INF) | id, subject, predicate, object, valid\_from, valid\_to, truth | qualifiers, created\_by event, secrecy flag | New revision per change |
| Claim (CLM) | id, holder or speaker, proposition (INF id or literal), truth\_value | origin event, distortion of (INF id) | Immutable once ACCEPTED |
| Knowledge Grant (KG) | id, holder, proposition, st\_time, channel, confidence, source event | source entity, premises (for INFERRED), polarity | Immutable once ACCEPTED |
| Causal Edge (CE) | id, from\_event, to\_event, type, justification | strength, required\_state | New revision per change |
| Relation | id, from\_entity, to\_entity, type, valid\_from, valid\_to | visibility, asymmetry note | Changes only through events |
| Canon Rule (CAN) | id, class (INVARIANT, CONDITIONAL, DEFAULT, PROHIBITION, METRIC), statement (structured), statement (natural language), tier, status | scope, exceptions | Change requires gate; published rules require RETCON |

### 3.4 Truth semantics

1. **Three values.** truth(p, t) is TRUE, FALSE, or UNDETERMINED. A query on an unspecified proposition returns UNDETERMINED, never FALSE (P4).
2. **Interval validity.** A fact holds on the half-open interval \[valid\_from, valid\_to). Either end may be open.
3. **Persistence (DD).** A state persists until an event changes it, but only for attributes declared persistent: location, custody, alive/dead, injuries, possessions, relationships, locks. Volatile attributes (mood, posture, expression) do not persist past their scene unless an event restates them. Reason: universal persistence produces false contradictions on mood; no persistence loses injuries.
4. **Claims are not facts.** A claim never changes WIS. It changes the hearers' CIS through a knowledge grant whose content is the claim's proposition, tagged with the claim's truth value. A hearer can therefore hold a false belief that the engine knows is false.
5. **Canon precedence.** When records conflict, the higher tier wins automatically only across tiers:
   1. PUBLISHED — CANON records whose text is already released; immutable within the series except by RETCON.
   2. INVARIANT — CANON-status rules that hold at every story-time.
   3. CANON — events and facts locked at the CANON gate.
   4. ACCEPTED — events and facts approved for working use but not yet locked.
   5. DEFAULT — canon values that hold unless an event overrides them.
   6. PROPOSAL — records awaiting a gate, including all AI-origin records. They never override anything and appear only in dry runs.
6. **Same-tier conflicts** always go to a human gate (the CANON gate for reality records). The engine never silently picks one.
7. **Determinacy by design.** An author may mark a proposition PERMANENTLY\_UNDETERMINED (deliberate ambiguity). The engine then forbids any record from fixing its truth and forbids any packet from asking the text to resolve it.

### 3.5 State computation

The value of an attribute at story-time t is the value set by the latest effect on that attribute with effect-time at or before t. If no effect applies, the canon default applies. If no default exists, the value is UNDETERMINED.

```latex
\mathrm{state}(x, a, t) = \begin{cases} v_k & \text{if } k = \arg\max_i \{\tau_i : \tau_i \le t,\ \mathrm{eff}_i \text{ sets } (x, a) = v_i\} \text{ exists} \\ \mathrm{default}(x, a) & \text{if no such effect and a default exists} \\ \mathrm{UNDETERMINED} & \text{otherwise} \end{cases}
```

- **Effect timing.** Each effect declares when it applies: at START, at END, or at a stated offset from start. The default is END.
- **Exclusive attributes.** Location, custody holder, alive/dead, and lock state admit one value at a time. Two effects that set different values in overlapping windows are a contradiction.
- **Uncertain times.** When event times are windows rather than points, state is computed for every feasible placement. A contradiction found in all placements is CERTAIN. One found in some placements is POSSIBLE. A POSSIBLE contradiction triggers window tightening (§6.2 step 6) or a human review; it is never ignored.

### 3.6 Invention policy

No model can specify every detail a scene needs. NSRES states in advance which details the drafter may invent.

| Class | Rule | Default members | Validation |
| --- | --- | --- | --- |
| LOCKED | Must come from the packet. Inventing or altering is a violation. | Names, titles, ranks, affiliations; who is present; custody; injuries; story-times and durations; knowledge; anything tied to a reveal | Exact or alias match against the packet; mismatch is MAJOR or BLOCKING |
| CONSTRAINED | May be invented inside stated bounds. | Dialogue wording; minor gestures; furnishings not in canon; weather inside the canon's seasonal model; unnamed servants' activity | Checked against the bound; out-of-bound is MINOR or MAJOR |
| FREE | May be invented. Autopsy captures it as a micro-fact PROPOSAL (DEF-45). | Sensory texture; incidental objects with no plot role; similes; background sounds | Decided ACCEPT\_AND\_REGISTER or REJECT\_MICRO\_FACT at the CANON gate; never a violation at creation |

**REQ-3.6.1.** An invented detail that later becomes load-bearing — referenced by a later beat, or used as a reader-visible clue — MUST reach CANON status before the later scene's packet is frozen.

### 3.7 Entry paths

Authors start from different places. NSRES supports three entry paths, which converge at the first reconciliation.

| Path | Start | Steps to first reconciled model | Typical user |
| --- | --- | --- | --- |
| A. Reality-first | Canon and events | 1. Author L1 canon. 2. Author L5 events, including offscreen ones. 3. Reconcile. 4. Plan the telling (L2–L4) as windows selected from reality. | Mystery and thriller writers; worldbuilders; series architects |
| B. Outline-first | A narrative-order outline | 1. Author L1 minimal canon. 2. Author L2–L4. 3. Lift beats into L5 events. 4. Generate bridge-event proposals for failed preconditions. 5. Author gates proposals. 6. Reconcile. | Most novelists and screenwriters |
| C. Manuscript-first (retrofit) | An existing draft | 1. Run autopsy extraction on the manuscript with an empty model. 2. Cluster assertions into candidate entities, events, and facts. 3. Author gates candidates into L1 and L5. 4. Reconcile; contradictions found are defects already in the manuscript. | Authors revising a finished draft; series continuing from published volumes |

All three paths end in the same state: a CONSISTENT model version with a scene plan whose every scene maps to reconciled events.

## 4. Layer stack, part 1: canon, plans, and the Truth Timeline (L1–L5)

NSRES has fifteen layers. Five are authored, five are derived projections, and five are processes or artifacts. Each layer below is specified under the same twelve headings, so implementers can compare layers field by field.

### 4.0 Layer overview

| Layer | Name | Plane | Kind | Primary records | Edited directly? |
| --- | --- | --- | --- | --- | --- |
| L1 | Master Canon | Reality | Authored | CAN, CHR, LOC, OBJ, GRP | Yes, through gate |
| L2 | Master Story Outline | Telling | Authored | THR, RVL, segment map | Yes, through gate |
| L3 | Scene Outline | Telling | Authored or proposed | SCN | Yes, through gate |
| L4 | Beat Outline | Telling | Authored or proposed | BT | Yes, through gate |
| L5 | Truth Timeline | Reality | Authored, lifted, proposed | EVT, CE, INF | Yes, through gate |
| L6 | Character Timeline | Reality | Derived (plus authored overlay) | projection | Only goal and arc overlay |
| L7 | Location Timeline | Reality | Derived | projection | No |
| L8 | Object Timeline | Reality | Derived | projection | No |
| L9 | Information Timeline | Reality | Derived (plus secrets register) | KG, CLM, projection | Only secrets register |
| L10 | Reader Knowledge Timeline | Telling | Derived (plan and actual) | delivery records, Q, irony gaps | No |
| L11 | Narrative Extraction | Telling | Process | RUN-X extraction record | No |
| L12 | Scene Packet | Telling | Artifact (frozen) | PKT | No; regenerate instead |
| L13 | Draft Generation | Rendering | Process plus artifact | DRF | Text yes (as new draft revision) |
| L14 | Continuity Validation | Rendering | Process | FND, validation report | No |
| L15 | Narrative Autopsy | Rendering | Process | FND, scorecard, proposals | No |

Each layer is specified under: **What it is** · **Why it exists** · **Contents** · **Generation** · **Inputs** · **Inherits** · **Outputs and state created** · **Consumed by** · **Contradiction detection** · **Resolution** · **Change propagation** · **Failure modes**.

### L1 Master Canon Layer

**What it is.** The registry of world rules, entity identities, fixed pre-story facts, invariants, metrics, and terminology that every other layer must satisfy.

**Why it exists.** Rules that hold everywhere must be stated once. Then every check can cite them by ID, and no scene re-decides them.

**Contents.**

| Record class | Holds | *Harrow House* example |
| --- | --- | --- |
| Entity identity | Canonical name, aliases, fixed traits, defaults for persistent attributes | CHR-002 Teodor Hale; alias "the Inspector"; York City Police; age 52; walks with a cane (persistent) |
| World rules | Physics, technology, magic, institutions, law, communication | CAN-014: no telephone at Harrow House; telegraph only at Kellby station |
| Invariants | Statements that MUST hold at every story-time | CAN-003: the dead do not act |
| Conditional rules | If-then constraints | CAN-021: a letter posted at Kellby before 17:00 reaches York the next morning |
| Defaults | Values that hold unless an event overrides them | CAN-030: the study is locked at night; its key hangs on the servants' hall board |
| Metrics | Travel-time matrix by mode; calendar; daylight model; perception ranges | Harrow House to The Bell inn: 20 min by carriage, 45 min on foot |
| Backstory facts | Events before the story starts, fixed | EVT-0003 Jonah's mother leaves service at Harrow House, 1870 |
| Terminology | Locked terms, alias rules, forbidden anachronisms | Forbidden: "okay"; locked: "the Bell" (never "the Bell Inn") |
| Precedence configuration | Canon tiers; publication status of prior volumes | Volume 1 status PUBLISHED |

**Generation.** Human-authored. AI MAY extract candidate records from notes, research, prior manuscripts, or series bibles. Candidates enter as PROPOSAL, pass the PROPOSAL gate to ACCEPTED, and are locked at the CANON gate (P6).

**Inputs.** Author notes, prior volumes, research, series bible.

**Inherits.** Nothing. L1 is the root.

**Outputs and state created.** Canon registry version `canon@rN`. Each record carries uuid, handle, class, structured statement, natural-language statement, tier, status, provenance.

**Consumed by.** Every layer. Findings cite canon rules by ID.

**Contradiction detection.**

1. Rule-rule unsatisfiability: two invariants cannot both hold, or a conditional's consequent violates an invariant.
2. Identity collision: two entities share a name or alias with no disambiguation record.
3. Metric inconsistency: the engine computes the shortest-path closure of the travel matrix. A declared direct time longer than the closure raises a WARNING (usually a missing route rule). A declared time shorter than physically allowed by a speed rule raises an ERROR.
4. Backstory facts that violate invariants.

**Resolution.** Same-tier conflicts go to the CANON gate with both records displayed. PUBLISHED records win over everything. Changing a published fact requires a RETCON record naming the affected published passages.

**Change propagation.** A canon change approved at the CANON gate computes its impact set: every event, fact, scene, packet, and draft that cites the changed record, directly or through a derived record. Events in the set are re-validated. Packets in the set become STALE.

**Failure modes.** Over-specification (canon so large authors stop maintaining it). Under-specification (missing travel metrics mean movement checks cannot run; the engine MUST report UNCHECKABLE, never PASS).

### L2 Master Story Outline Layer

**What it is.** The macro telling plan, in narrative order: premise, central dramatic question, thread register with ranks and intended arcs, structural segments, major turning points located by narrative position, the macro reveal plan, and target end states.

**Why it exists.** It records the author's telling intent at the scale of the whole work, so extraction selects from reality according to a plan instead of improvising.

**Contents.**

| Element | Holds | *Harrow House* example |
| --- | --- | --- |
| Premise | One to three sentences | A housekeeper shields the footman she suspects, while the real killer helps steer the inquiry. |
| Central dramatic question | The question whose answer ends the work | Who poisoned Edmund Harrow? |
| Thread register | THR records: name, rank, dramatic question, arc summary, visibility schedule | THR-02 Jonah's claim; secondary; hidden until 2.14 |
| Segment map | Parts, acts, or sequences with NT ranges and functions | Part 1 (1.01–1.08): discovery and first suspicion |
| Turning points | NT position plus the thread nodes rendered | 1.08: Hale learns the ledger is missing |
| Macro reveal plan | RVL records: target proposition, NT position, delivery mode, prerequisites | RVL-05: INF-005 (Celia poisoned the decanter), at 3.22, STATED |
| End-state targets | Required WIS and RIS at the final position | Celia arrested; reader holds INF-002 through INF-005 |

**Generation.** Author-written. AI MAY propose segment maps, turning points, and arcs. In entry path B, L2 is authored before L5 and later lifted.

**Inputs.** L1; author premise and intent.

**Inherits.** Entity and terminology vocabulary from L1.

**Outputs and state created.** Thread Register v1; macro Reveal Plan; segment map; NT skeleton (part and chapter positions).

**Consumed by.** L3 (decomposition), L5 (lifting), L10 (RIS\_plan), L11 (thread priority).

**Contradiction detection.**

1. A turning point depends on a proposition whose reveal is scheduled after it.
2. A thread has neither a resolution node nor a deferral record.
3. A reveal target does not exist in L5 (after lifting), or is UNDETERMINED, or is PERMANENTLY\_UNDETERMINED.
4. Two reveals of the same proposition without a RETELLING tag.
5. An end-state target violates an L1 invariant.

**Resolution.** Author decides. The engine proposes moving the reveal, adding a prerequisite clue, deferring the thread, or re-ranking it.

**Change propagation.** A thread rank change re-weights extraction priority for all unfrozen packets. A reveal position change recomputes RIS\_plan from that position forward and marks affected packets STALE.

**Failure modes.** Plans written as prose summaries with no node references, so nothing can be checked. Reveal plans that name feelings ("the reader realizes the truth") instead of propositions.

### L3 Scene Outline Layer

**What it is.** The ordered list of scenes. Each scene has a narrative position, an intended story-time window, a location, a POV configuration, participants, the thread nodes it renders, and a planned narrative-state change.

**Why it exists.** Scenes are the unit of extraction and drafting. A scene's plan states what must change, so extraction can check that the change is possible and drafting can be held to it.

**Contents (scene record minimum).**

| Field | Holds | Example (SCN-007) |
| --- | --- | --- |
| scene\_id, nt\_position | Identity and order | SCN-007 at 1.03.2 |
| st\_window | Intended story-time window; may be approximate | 1893-10-15 07:40–08:10 |
| location | Primary location; sub-locations | LOC-001c servants' hall |
| pov | Character and mode | CHR-001 Mara; close third, past tense |
| participants | Characters present | CHR-001, CHR-002, CHR-004, CHR-006 (Mrs. Dorran, cook) |
| renders\_nodes | Thread nodes this scene renders | NOD-01-04 (first interview), NOD-04-02 (Mara's choice) |
| purpose | One sentence, as outcome | Hale questions the household; Mara chooses to hide her sighting of Jonah |
| planned\_ns\_delta | RIS additions; questions opened and closed; setups planted | +INF-006 (SHOWN); opens Q-03; plants empty key hook |
| reveal\_tags, suppress\_tags | Reveal records touched; hidden threads active | suppress THR-02, THR-03 |
| length\_target | Words | 2,000–2,800 |

**Generation.** Path B: decomposition of L2 segments; AI MAY propose candidate scene lists for human approval. Path A: scenes are selected as windows over L5 events.

**Inputs.** L2; L5 when it exists.

**Inherits.** Threads, ranks, and reveal plan from L2; entities from L1.

**Outputs and state created.** Scene list with NT order; draft telling map (scene → events).

**Consumed by.** L4, L5 (lifting), L10 (RIS\_plan), L11.

**Contradiction detection.**

1. Two scenes place one character in different locations in overlapping story-time windows.
2. A scene renders a node not belonging to any registered thread.
3. Planned RIS additions include a proposition before its reveal position.
4. Inert scene: the planned delta is empty.
5. The POV character is not a participant, and the POV mode is not omniscient or camera.
6. The st\_window conflicts with the L5 placement of an event the scene renders.

**Resolution.** Planner diagnostics name the conflicting records and propose: shift the window, change the POV, move the scene in NT, or add an event in L5.

**Change propagation.** Reordering scenes changes NT positions, so RIS\_plan is recomputed from the earliest moved position, and every later packet is re-checked.

**Failure modes.** Scenes defined by topic ("the interview") with no outcome. Story-time windows left blank, which disables movement and knowledge checks for the scene.

### L4 Beat Outline Layer

**What it is.** The ordered beats inside each scene. Each beat has a type, actors, an outcome statement, event bindings, state deltas, and a mandatory flag.

**Why it exists.** Beats are the unit that validation can check for coverage. They also force each change to be stated as an outcome before any prose is written.

**Beat types.**

| Type | Changes | Example |
| --- | --- | --- |
| ACTION | World state | Hale examines the key board |
| EXCHANGE | Character or reader state through dialogue | Hale asks who locked the study |
| PERCEPTION | POV CIS and reader state | Mara notices the empty hook |
| REVELATION | RIS; possibly CIS | Mara recalls seeing Jonah at 22:45 (shown to the reader) |
| DECISION | Character state (intention) | Mara decides not to name Jonah |
| REVERSAL | Expectation reversed | Hale already knows the study was locked |
| INTERIOR | POV state, reader state | Mara weighs her loyalty to the house |
| TRANSITION | Position in time or space | The interview ends; Hale goes upstairs |
| PLANT | Reader state (setup) | The empty hook is described |
| PAYOFF | Reader state (setup closed) | The key is found (in a later scene) |
| SUSTAIN | Nothing; holds a state. Ambient, mood, or montage sequences only, and must be declared | Rain on the study window while the house sleeps |

**Rule (DD).** Beats state outcomes, not wording. A beat says "Mara refuses to name whom she saw"; it does not script her words. Reason: scripted beats produce mechanical prose and make the drafter a transcriber.

**Generation.** Authored or proposed from the scene purpose. In path B, every beat that changes world state is lifted into at least one L5 event.

**Inputs.** L3 scene record; L5 entry state.

**Inherits.** Scene participants, location, window, and POV.

**Outputs and state created.** Beat list per scene, each with event bindings and deltas.

**Consumed by.** L5 (lifting), L10 (setups and payoffs), L11, L14 (coverage).

**Contradiction detection.**

1. A beat's precondition is not satisfied by the scene's entry state plus earlier beats.
2. Beat order violates causality inside the scene.
3. A beat binds to an event whose story-time falls outside the scene window.
4. A PLANT with no registered payoff, or a PAYOFF with no prior PLANT.
5. A beat's actor is not a participant.

**Resolution.** Reorder beats, add an enabling beat, or move the bound event. Human approves.

**Change propagation.** A beat change re-lifts its events, re-checks the scene, and marks the scene's packet STALE.

**Failure modes.** Too many mandatory beats for the length target (packet over-constraint). Beats that are summaries of prose instead of state changes.

### L5 Truth Timeline Layer

**What it is.** The canonical record of every event in Story Reality, onscreen and offscreen, ordered by story-time, with participants, location, preconditions, effects, causal edges, visibility designations, and provenance.

**Why it exists.** Principle P2: one place decides what happened. Every projection, check, and packet draws from it.

**Contents (event record summary; full model in §10.2).**

| Field group | Fields |
| --- | --- |
| Identity | id, type, label, status, provenance (author, lifted from BT, AI proposal, imported) |
| Time | st\_start, st\_end, precision, uncertainty window, temporal constraints (Allen relations, metric offsets, anchors) |
| Place | location, sub-location, perceptibility (who nearby could see or hear) |
| Participants | entity IDs with roles: AGENT, PATIENT, WITNESS, PRESENT, REMOTE |
| Logic | preconditions (state predicates); effects (state deltas, knowledge grants, custody transfers, claims made) |
| Causality | causal edges in and out, with types and justifications |
| Threads | node memberships with roles |
| Telling | render\_status (RENDERED, DEFERRED, IMPLIED, CAUSAL\_UNRENDERED, AMBIENT); telling-map links |
| Visibility | REVEALABLE, HIDDEN\_UNTIL(RVL id), PERMANENT\_MYSTERY |

**Generation.** Four sources, all tagged by provenance:

1. Authored events.
2. Lifted events: each world-changing beat in L4 yields at least one event.
3. Bridge events: proposed by the engine or an AI to satisfy failed preconditions. They enter as PROPOSAL, flagged as AI-origin where applicable.
4. Backstory events from L1.

**Inputs.** L1; L3 and L4 for lifting; author.

**Inherits.** Entities, rules, and metrics from L1; nodes from L2 and L3.

**Outputs and state created.** `truth@rN`; the reconciliation report; the solved temporal network (a feasible window per event).

**Consumed by.** L6–L9 (derivation), L10 (hidden-causality checks), L11.

**Contradiction detection.** The full catalog is in §6.11: temporal inconsistency, exclusive-attribute conflicts, invariant violations, precondition failures, effects after destruction, causal cycles, impossible movement, impossible knowledge.

**Resolution.** The protocol in §6.14.

**Change propagation.** An event change approved at a gate re-runs incremental reconciliation over the affected story-time window and entity set. It regenerates L6–L9 projections for affected entities, recomputes hidden-causality flags in L10, and marks dependent packets STALE.

**Failure modes.** Events written as narrative summaries with no effects, so state cannot be computed. Missing offscreen events, discovered only as precondition failures. Over-precise times that create false contradictions (prefer windows to invented minutes).

## 4. Layer stack, part 2: derived timelines (L6–L10)

L6 through L10 are projections. They are computed from L5 (and, for L10, from the telling plan and accepted drafts). They are never the place where a fact is first asserted (P3). Their job is to make each entity's continuous history queryable, so that checks and extraction can ask "where was Jonah at 22:45" or "what had the reader been told by 1.03.2" in one lookup.

### L6 Character Timeline Layer

**What it is.** A per-character projection of L5: presence intervals by location, persistent physical and social state over time, possessions, knowledge state, goals and plans, authored arc annotations, and unaccounted intervals.

**Why it exists.** Scenes are written through characters. The drafter needs each participant's exact state at the scene's story-time. Checks need each character's continuous trajectory to detect impossible movement and state discontinuities.

**Contents.**

| Track | Derived from | CHR-004 Jonah, 14–15 Oct |
| --- | --- | --- |
| Presence | Event participation plus travel inference | 22:15–22:25 study; 22:40 study; 22:45 east corridor; 23:00–06:00 servants' quarters (AMBIENT) |
| Physical state | Persistent-attribute effects (health, injury, clothing, fatigue) | No notable change |
| Possessions | L8 custody records | OBJ-002 study key from 22:15; OBJ-001 ledger from 22:40 |
| Knowledge | L9 knowledge grants | INF-004 (he is Edmund's son), CERTAIN, since 1888 |
| Goals | Authored goal records anchored to events | Keep the ledger safe until he can reach the vicar |
| Arc annotations | Authored, anchored to thread nodes | From loyalty to self-assertion; turn at 2.14 |
| Emotional baseline | Authored per scene entry; volatile (§3.4) | Entry to SCN-007: frightened, controlled |
| Unaccounted intervals | Gaps with no presence evidence | None in the 14–15 Oct window |

**Generation.** Computed by the State Projection Engine. Not edited directly. Edits route to L5 events. The exceptions are goals, arc annotations, and emotional entry states: these are an authored overlay, and each overlay record MUST anchor to an event or node ID.

**Inputs.** L5 events and effects; L8 custody; L9 grants; L1 entity defaults.

**Inherits.** Identity and persistent defaults from L1.

**Outputs and state created.** Per-character interval tree keyed by story-time; per-attribute value timeline; list of unaccounted intervals.

**Consumed by.** L7 (occupancy), L11 (character state compilation), L14 and L15 (character-state checks).

**Contradiction detection.**

1. Ubiquity: presence in two locations in overlapping intervals without a REMOTE role.
2. Impossible movement: consecutive presences closer in time than the minimum travel time (§6.12).
3. State discontinuity: a persistent attribute changes with no event (a bandaged hand is bare in the next scene).
4. Post-death action: any AGENT role after death (CAN-003).
5. Knowledge use without acquisition (§6.13).
6. Goal-action inconsistency: an action contradicting every active goal with no DECISION beat. WARNING only (HEU); characters may act against their goals.
7. Unaccounted interval referenced: a scene or event needs the character's location during a gap.

**Resolution.** Each finding names the L5 events involved. Repairs are L5 edits: move an event, add a travel or bridge event, change a participant, or add a decision beat.

**Change propagation.** Regenerated for a character whenever any event involving that character changes.

**Failure modes.** Overlay goals that never anchor to events, so goal checks never fire. Emotional state treated as persistent, producing false discontinuities.

### L7 Location Timeline Layer

**What it is.** A per-location projection: occupancy intervals, location state over time (locked, lit, damaged, crowded), environmental conditions, objects present, access constraints, events occurring there, and perceptibility links to neighboring locations.

**Why it exists.** Setting is state. A drafter describing a room needs to know whether its door is locked, who is in it, what is on the table, and what can be heard from the corridor. Checks need location state to detect impossible entries and contradictory descriptions.

**Contents.**

| Track | Derived from | LOC-001a the study |
| --- | --- | --- |
| Occupancy | Inverse of L6 presence | Edmund and Jonah 22:15–22:25; Jonah alone 22:38–22:40; empty from 22:40 |
| Lock state | Lock effects; CAN-030 default | Locked from 22:40 (EVT-0104); key with Jonah |
| Light and conditions | L1 daylight model; lighting effects | Dark from 22:40; first daylight about 06:45 on 15 Oct (canon daylight model) |
| Objects present | Inverse of L8 custody (location holder) | OBJ-003 decanter; OBJ-001 ledger until 22:40 |
| Access constraints | Canon rules; lock state; guards | Entry requires OBJ-002 or a forcing event |
| Perceptibility | L1 adjacency and perception ranges | Voices in the study audible in the east corridor (CAN-041) |
| Events here | L5 location field | EVT-0101, EVT-0102, EVT-0103, EVT-0104 |

**Generation.** Computed. Location state effects are written on L5 events ("EVT-0104 effect: LOC-001a.lock = LOCKED").

**Inputs.** L5; L6 presence; L8 custody; L1 adjacency, daylight model, capacities.

**Inherits.** Location identity, adjacency, default states from L1.

**Outputs and state created.** Per-location interval tree; per-attribute state timeline; perceptibility graph slices per time window.

**Consumed by.** L11 (setting state; perception filter), L14 and L15 (setting checks).

**Contradiction detection.**

1. Entry into a locked location with no key, no unlocking event, and no forcing event.
2. Contradictory location state in overlapping windows (locked and open).
3. Use of a destroyed or inaccessible location.
4. Occupancy above declared capacity (WARNING).
5. Perception across locations with no perceptibility link (a character hears a whisper three floors away).

**Resolution.** Add an access event, change lock timing, or add a perceptibility rule to L1 (gate).

**Change propagation.** Regenerated for a location when any event at it, or any presence or custody involving it, changes.

**Failure modes.** Missing adjacency data, which silently disables perception checks; the engine MUST report UNCHECKABLE.

### L8 Object Timeline Layer

**What it is.** A per-object projection: existence interval, custody chain, state changes, declared duplicates, significance, and setup-payoff obligations.

**Why it exists.** Objects carry plot. A missing ledger, a key, a weapon, a letter: each must be in exactly one place at a time, and the reader's knowledge of it must follow the plan.

**Conservation law (REQ-L8.1).** At every story-time in an object's existence interval, it has exactly one custody value: a character, a location, or UNDETERMINED inside a declared custody gap.

**Contents.**

| Track | Derived from | OBJ-001 the ledger |
| --- | --- | --- |
| Existence | Creation and destruction effects | 1871 onward; not destroyed in Volume 1 |
| Custody chain | Transfer effects | Study (to 22:40, 14 Oct) → Jonah (22:40–23:05) → Jonah's room, under the floorboard (from 23:05) |
| State | State effects | Intact; the last page is torn out (EVT-0088, 1892) |
| Significance | Authored | PLOT\_OBJECT, CLUE |
| Setup and payoff | L10 PLANT and PAYOFF beats | Planted 1.01.1 (seen on the desk); missing noticed 1.08; found 2.09 |
| Duplicates | Declared copies | None |

**Generation.** Computed from L5 transfer, creation, destruction, and state effects.

**Inputs.** L5; L1 object identity and significance.

**Outputs and state created.** Per-object custody interval list; state timeline; obligation list.

**Consumed by.** L6 (possessions), L7 (objects present), L11, L14, L15.

**Contradiction detection.**

1. Dual custody in overlapping windows.
2. Appearance before creation or after destruction.
3. Transfer from a holder who does not hold the object at that time.
4. A scene references the object's location during a custody gap.
5. A payoff with no prior setup; a plot object with no payoff by the end of the work (WARNING, unless deferred).
6. An object used in a state it is not in (reading a page that was torn out).

**Resolution.** Add or move a transfer event; declare a duplicate (gate); close a custody gap.

**Change propagation.** Regenerated per object on any transfer or state change.

**Failure modes.** Implicit transfers in prose ("she handed him the key") never lifted into L5. Autopsy must catch these as emergent facts.

### L9 Information Timeline Layer

**What it is.** A per-proposition history: the proposition's truth interval in reality, the event that made it true, every knowledge grant (holder, time, channel, confidence, source), distorted variants (rumors, lies), holders of false versions, and a secrets register.

**Why it exists.** Information is the main currency of most plots. Characters knowing too much, too early, or without a path is a common defect class that a flat outline cannot detect, because the outline never records how anyone learned anything.

**Channel rules.** A knowledge grant is valid only if its channel's preconditions hold at the grant time.

| Channel | Preconditions | Latency | Example |
| --- | --- | --- | --- |
| WITNESSED | Holder present at the event's location, or at a location with a perceptibility link; conscious; within perception range | 0 | KG-0031: Mara sees Jonah in the east corridor at 22:45 |
| TOLD | Teller holds the proposition (or the claim) at grant time; teller and holder co-present, or a remote channel exists | Channel latency from L1 | Mrs. Dorran tells Mara the inspector is coming |
| READ | Holder has access to a document that contains the proposition | 0 after access | Hale reads the chemist's report, 16 Oct 14:00 |
| INFERRED | Holder holds every premise named in the inference record | 0 | Hale suspects poisoning from residue in the decanter |
| RUMOR | Source chain may be unknown; confidence at most BELIEVED | Variable | Kellby village hears of the death by noon |
| ASSUMED | A default belief from canon or social role | n/a | Servants assume Edmund's heart failed |
| DETECTED | Holder has a sensing mechanic whose range and preconditions cover the trace (§17.5) | Per mechanic | A binder within 30 metres detects the frost-rime residue on the anchor (§17.8) |

**Secrets register (authored overlay).** For each secret: the proposition, its holders, the concealment intent (from whom), the concealment strategy, and the planned reveal. Example: INF-004 (Jonah is Edmund's son); holders Jonah, Edmund (until death); concealed from the household and reader; reveal RVL-03 at 2.14.

**Generation.** Computed from knowledge-grant and claim effects on L5 events. The secrets register is authored and gated.

**Inputs.** L5; L6 presence (for WITNESSED); L8 custody (for READ); L1 channel rules and latencies.

**Outputs and state created.** Per-proposition propagation graph; per-holder CIS(c, t) index; false-belief register; secrets register.

**Consumed by.** L6 (knowledge track), L10 (irony gaps), L11 (POV knowledge filter), L14, L15 (knowledge checks).

**Contradiction detection.**

1. Knowledge without a grant: a character acts on or speaks a proposition not in its CIS.
2. Grant that violates channel preconditions (told by someone absent, with no remote channel).
3. Grant before the proposition exists, unless the proposition is tagged as a plan, prediction, or inference.
4. A holder of both p and not-p without a CONFLICTED flag.
5. Secret spread wider than its concealment plan (WARNING: "more people know than the plan allows").
6. An INFERRED grant whose premises are not all held.

**Resolution.** Add a channel event, change the channel, lower the confidence (CERTAIN to SUSPECTED), move the use later, or change what the character says (from knowledge to suspicion).

**Change propagation.** Regenerated per proposition when any grant, claim, or the proposition's source event changes. Every CIS index entry for affected holders is recomputed.

**Failure modes.** Knowledge granted only in prose ("she had heard that…") and never lifted. Inference used to launder impossible knowledge: an INFERRED grant whose premises are themselves impossible. The engine checks premises recursively.

### L10 Reader Knowledge Timeline Layer

**What it is.** The narrative-time-indexed record of what the reader has been given: every delivered proposition with mode and position, planted false beliefs, open questions, setups awaiting payoff, dramatic-irony gaps, and the reveal schedule. It has two tracks: RIS\_plan and RIS\_actual.

**Why it exists.** Character knowledge and reader knowledge are different. A twist depends on the reader not knowing something that a character does. A mystery depends on fair clues reaching the reader before the solution. Neither can be checked without a reader-side ledger.

**Contents.**

| Track | Holds | *Harrow House* example |
| --- | --- | --- |
| Delivered propositions | (INF ID, NT position, mode, delivering scene and beat) | INF-006 at 1.03.2, SHOWN (Mara recalls seeing Jonah with a bundle) |
| Misdirection | False proposition, induced at, corrected at | "Edmund's heart failed" induced at 1.02.1, corrected at 1.09.3 |
| Open questions | Question, opened at, closed at, stakes weight | Q-03: what was in Jonah's bundle? Opened 1.03.2 |
| Setups and payoffs | PLANT beat → PAYOFF beat | Empty key hook at 1.03.2 → key found at 2.11.1 |
| Irony gaps | Reader-ahead and reader-behind propositions per POV scene | Reader ahead of Hale on INF-006 from 1.03.2 |
| Reveal schedule | RVL records with prerequisites | RVL-02: INF-002 at 2.09; requires INF-006 and the key PLANT first |
| Permanent mysteries | Propositions never to be delivered, with the reason | None in Volume 1 |

**Generation.** RIS\_plan is computed from the L2 reveal plan plus L3 and L4 planned deltas. RIS\_actual is computed by L15 autopsy from accepted drafts.

**Inputs.** L2, L3, L4 (plan); L15 autopsy output (actual); L5 causal edges and render status (hidden-causality checks).

**Outputs and state created.** RIS(n) for both tracks at every NT position; open-question ledger; setup-payoff ledger; irony-gap index; hidden-causality flags per position; narrative pressure vector per position (§7.8).

**Consumed by.** L11 (reveal, suppression, irony rules), L14 and L15 (leak checks), the planner (pressure, pacing).

**Contradiction detection.**

1. Premature delivery: a proposition appears in either track before its reveal position.
2. Unfair resolution (genre rule, enabled per work): a solving scene relies on a proposition never delivered before it.
3. Comprehension gap: a packet assumes reader knowledge not in RIS.
4. Orphaned misdirection: a false belief never corrected and not marked permanent.
5. Setup without payoff; payoff without setup.
6. Plan-actual divergence: in RIS\_actual but not RIS\_plan is a leak; in RIS\_plan but not RIS\_actual is an under-delivery.
7. Uncovered hidden causality: a rendered effect whose cause is not in RIS and has no reveal or permanent-mystery record.

**Resolution.** Move the reveal, add a clue scene or beat, revise the draft that leaked, or register a permanent mystery (author gate).

**Change propagation.** Any accepted draft updates RIS\_actual from its position forward. Every later packet is re-checked against the new RIS\_actual and may become STALE. Any change to the plan recomputes RIS\_plan forward from the earliest changed position.

**Failure modes.** Treating IMPLIED delivery as certain. Implied delivery is probabilistic, so autopsy records a confidence on each IMPLIED and HINTED entry and leak probes test it (§9.3).

## 4. Layer stack, part 3: extraction, rendering, validation (L11–L15) and propagation

L11 through L15 turn reconciled state into prose and check the prose against the state. L11 and L12 are telling-side; L13 through L15 are rendering-side. The section ends with the inheritance matrix and the change-propagation rules that bind all fifteen layers.

### L11 Narrative Extraction Layer

**What it is.** The process that converts reconciled Story Reality plus the narrative state before a scene into the content of that scene's packet. Its persistent output is an extraction record that explains every inclusion and exclusion.

**Why it exists.** It is the boundary between a complete world and a single scene. It decides what this scene may use, must use, and must not reveal, so the drafter never has to make those decisions.

**Contents of an extraction record.** Selected event IDs with selection reasons; facts classified by visibility (§7.5); derived behavioral constraints for suppressed facts; the POV filter applied; thread priority scores; the rule trace (each rule fired, with inputs and result); budget decisions (what was summarized or dropped, and why).

**Generation.** Deterministic engine (§7). LLM assistance is permitted only for two steps: wording behavioral manifestations of suppressed facts, and summarizing background material to fit budget. Both outputs are marked AI-origin and re-checked by the leak rules.

**Inputs.** Reconciled L5–L10 at one model version; the L3 scene record and L4 beats; RIS(n−1) from both tracks.

**Inherits.** Everything upstream, read-only.

**Outputs and state created.** RUN-X extraction record; an unfrozen packet candidate.

**Consumed by.** L12.

**Contradiction detection (extraction-time).**

1. The plan requires presenting a fact the POV cannot perceive or know.
2. A required beat conflicts with a forbidden revelation (the beat cannot be rendered without leaking).
3. A required outcome is unreachable from the entry state with the given beats.
4. The scene's story-time window or location conflicts with L5.
5. Mandatory content exceeds the packet budget.

**Resolution.** Extraction never repairs a conflict by silently dropping a required beat or loosening a forbidden revelation. It halts with a diagnostic routed to L3 or L4, and the author decides.

**Change propagation.** None of its own. Extraction is re-run when its inputs change.

**Failure modes.** Over-inclusion (the drafter receives so much that it renders background as foreground). Under-inclusion (a needed persistent state, such as an injury, is dropped by budget). Budget rules in §7.9 rank persistent visible state above texture.

### L12 Scene Packet Layer

**What it is.** The frozen generation contract for one scene: a versioned, hashed record holding every field defined in §8.

**Why it exists.** Drafting must be reproducible and auditable. A frozen packet records exactly what the drafter was given, so every later finding can be attributed to the model, the packet, or the drafter.

**Lifecycle.** PLANNED → EXTRACTED → PACKET\_VALID → FROZEN, then STALE on any upstream change that touches a cited record. Full state machine in §5.4.

**Generation.** Produced by L11, validated by the pre-draft checks (§7.10), frozen at the STRUCTURE gate, by a human or, where the work's automation tier allows it, automatically (§11.4).

**Inputs.** L11 packet candidate.

**Outputs and state created.** PKT record with `packet_hash` (hash of the canonical serialization) and `model_version`.

**Consumed by.** L13 (drafting), L14 (validation), L15 (autopsy).

**Contradiction detection.** Schema validation; cross-field rules (a forbidden revelation cannot also be a required outcome; every participant has a character-state block; every mandatory beat cites an event or a reader delta).

**Resolution.** Return to L11 with the failing rule.

**Change propagation.** A packet never changes after freezing. A new revision (PKT-007-r4) is extracted instead, and drafts made from the old revision are flagged.

**Failure modes.** Packets frozen against an INCONSISTENT model version; prevented by REQ-5.4.2.

### L13 Draft Generation Layer

**What it is.** The rendering of a frozen packet into prose, by an LLM or a human.

**Why it exists.** It is the only layer that produces text. NSRES confines it to rendering: it chooses words, rhythm, image, and dialogue, not facts.

**Inputs.**

1. The frozen packet, compiled into a drafting brief by the Packet Compiler (§10.11).
2. The voice profile referenced by the packet.
3. Optionally, the last N words of the preceding accepted scene, marked as a style reference only. Facts in it are not authoritative; the packet is (DD).

**Outputs and state created.** A DRF record holding: the text; the packet hash; generator identity (model, version, settings) or human author; prompt-template version; an emergent-detail declaration (the drafter's own list of details it invented); a beat map (text spans per beat); the generation log.

**Consumed by.** L14, L15.

**Contradiction detection.** None at this layer. Detection is downstream by design, so the drafter is never also the judge of its own output.

**Rule (REQ-L13.1).** A draft generated from a packet that is STALE at arrival is invalid. It may be kept for reference but cannot be accepted.

**Failure modes.** Invention beyond policy; hidden-thread leaks; omitted beats; POV breaks; length overrun; false or incomplete self-declarations (the emergent-detail list is a hint, never trusted as complete).

### L14 Continuity Validation Layer

**What it is.** A fast, per-scene gate that checks one draft against its packet and the model before the draft can be accepted.

**Why it exists.** Most defects are cheap to fix before acceptance and expensive after, because accepted text updates RIS\_actual and later packets build on it.

**L14 and L15 compared.**

| Aspect | L14 Continuity Validation | L15 Narrative Autopsy |
| --- | --- | --- |
| Scope | One draft against its packet and the model | One or many accepted drafts against the model and the whole manuscript |
| Timing | Before acceptance | After acceptance, or in batch |
| Purpose | Gate | Diagnose; measure drift; update RIS\_actual; propose canon changes; attribute root causes |
| Methods | Deterministic checks plus bounded LLM assertion extraction | Full assertion extraction; cross-scene comparison; leak probes; root-cause analysis |
| Output | PASS, PASS\_WITH\_FINDINGS, or FAIL, with findings | Findings, scorecard, RIS\_actual delta, drift indices, proposals |
| Blocks acceptance? | Yes, on any BLOCKING finding | No, but its findings can reopen accepted scenes |

**Check suites.**

| Suite | Checks | Method |
| --- | --- | --- |
| Lexical | Forbidden terms; locked names and titles spelled exactly; alias rules; anachronism list | Deterministic string and pattern matching |
| Presence | Only packet participants act or speak; others appear only if permitted as background | Named-entity recognition plus entity linking |
| Beat coverage | Every mandatory beat is aligned to a text span; beat order respected where constrained | LLM alignment, confidence-scored; low confidence goes to human |
| POV discipline | Interiority only for the POV character; perception within range | LLM classification of interior statements |
| Invention policy | LOCKED assertions match the packet; CONSTRAINED within bounds | Assertion extraction plus comparison |
| Forbidden revelation | Direct statements of forbidden propositions; forbidden lexical markers | Deterministic markers plus LLM paraphrase detection |
| Format | Length range, tense, person, scene breaks | Deterministic |

**Outputs and state created.** Validation report linked to the DRF; draft state VALIDATED or FAILED.

**Failure modes.** Treating PASS as proof of integrity. A PASS report MUST list which suites ran, their coverage, and any UNCHECKABLE items. A report with no coverage statement is invalid (REQ-L14.1).

### L15 Narrative Autopsy Layer

**What it is.** Deep post-acceptance analysis of drafted text against the model and the rest of the manuscript. Full design in §9.

**Why it exists.** Some defects are only visible across scenes (drift, leaks by accumulation, unfair resolutions). Accepted text also contains new facts the model must learn or reject (P10).

**Outputs and state created.** Findings; a scorecard per draft; an RIS\_actual delta; drift index updates; micro-fact and correction proposals for L1 and L5; root-cause attribution statistics.

**Consumed by.** L10 (RIS\_actual), L1 and L5 (through gated proposals), the planner, the author.

### 4.16 Inheritance matrix

Each row lists what a layer reads from each upstream layer. "—" means no dependency.

| Layer | From L1 | From L2–L4 | From L5 | From L6–L9 | From L10 | From L11–L15 |
| --- | --- | --- | --- | --- | --- | --- |
| L2 | Entities, terms | — | — | — | — | — |
| L3 | Entities | Threads, reveal plan | Events (path A) | — | — | — |
| L4 | Entities | Scene record | Entry state | — | — | — |
| L5 | Rules, metrics, backstory | Beats to lift | — | — | — | Emergent-fact proposals (gated) |
| L6–L9 | Defaults, channels, adjacency | Overlays (goals, secrets) | Events, effects | Each other (presence, custody) | — | — |
| L10 | Genre rules | Reveal plan, planned deltas | Causal edges, render status | — | — | RIS\_actual from L15 |
| L11 | Rules, terms, invention defaults | Scene, beats, thread ranks | Events in window | All projections | RIS, pressure, irony gaps | — |
| L12 | — | — | — | — | — | L11 candidate |
| L13 | Voice profile reference | — | — | — | — | L12 packet |
| L14 | Terms, rules | — | Facts | Projections | — | L12 packet, L13 draft |
| L15 | All | All | All | All | All | L12, L13, L14 |

### 4.17 Change-propagation rules

Every gate decision that changes an ACCEPTED or CANON record produces an impact set, computed over the reverse-reference index (§10.6). The table states what each change class recomputes, invalidates, and asks of a human.

| Change | Recomputed | Invalidated (marked STALE) | Required human action |
| --- | --- | --- | --- |
| Canon rule added or changed | Validation of every event citing the rule; affected projections | Packets citing affected events or the rule | Review new findings |
| Published canon changed | As above | As above, plus accepted drafts in the published range | RETCON record approval |
| Entity attribute default changed | Projections for that entity | Packets with that entity as participant | Review accepted drafts that described the attribute |
| Event added, moved, or removed | Temporal network; projections for participants, location, objects, propositions | Packets whose window or cited records overlap | Resolve any new contradictions |
| Knowledge grant changed | CIS for the holder from grant time forward | Packets with that holder as POV or participant after the grant | Review dialogue in accepted drafts |
| Reveal position moved | RIS\_plan from the earlier of the old and new positions | Packets after that position | Confirm prerequisite clues still precede the reveal |
| Thread rank changed | Priority scores | Unfrozen packets only (frozen packets keep their scores) | None unless re-extraction requested |
| Scenes reordered | NT positions; RIS\_plan from earliest moved position | Every packet after that position | Re-check irony gaps and reveals |
| Draft accepted | RIS\_actual from its position | Later packets whose assumptions differ from the new RIS\_actual | None if no difference |
| Micro-fact registered (ACCEPT\_AND\_REGISTER) | L1 or L5; projections | Packets that cited UNDETERMINED for that fact | Confirm later packets |

### 4.18 When accepted prose and the model disagree

A model change can contradict prose already accepted. NSRES defines three policies, set per work and overridable per finding:

| Policy | Effect | Use when |
| --- | --- | --- |
| MODEL\_WINS | A revision task opens on the affected prose; the model change stands | The prose was wrong, or the change is a deliberate redesign |
| PROSE\_WINS | The model change is reverted, or the prose assertion is canonized | The prose is published, or the author prefers what the prose says |
| HUMAN\_DECIDES (default) | Both options are presented with their impact sets | Always, unless the author has set a standing policy |

**REQ-4.18.1.** No policy may resolve a disagreement silently. Every resolution writes a RES record naming the change, the prose span, the policy, and the person who decided.

## 5. Architecture

The architecture has seventeen components in four planes. Information flows one way from canon to prose, with exactly two feedback paths: autopsy updating reader state, and gated proposals updating canon and events. Every state change passes through the control plane.

### 5.1 Conceptual architecture

| ID | Component | Plane | Responsibility | Reads | Writes |
| --- | --- | --- | --- | --- | --- |
| C1 | Canon Registry | Reality | Store and version L1; evaluate canon rules | — | L1 |
| C2 | Narrative Planner | Telling | Store L2–L4; propose decompositions | L1, L5 | L2–L4 |
| C3 | Event Store | Reality | Append-only, bitemporal L5 event log | L1 | L5 |
| C4 | Temporal Constraint Engine | Reality | Solve metric and qualitative time constraints; compute feasible windows | L1 metrics, L5 constraints | Solved windows |
| C5 | State Projection Engine | Reality | Compute L6–L8 | L5, windows | L6–L8 |
| C6 | Knowledge Propagation Engine | Reality | Compute L9 and CIS indexes | L5, L6, L8, L1 channel rules | L9 |
| C7 | Reader State Engine | Telling | Compute L10 plan and actual tracks; pressure vector | L2–L4, L5, L15 output | L10 |
| C8 | Reconciliation Orchestrator | Control | Run C4–C7 to a fixpoint; run the rule suite; emit the report | All reality layers | RUN-R records, findings |
| C9 | Scene Extraction Engine | Telling | Execute L11 | Reconciled model, L3, L4, L10 | Extraction record, packet candidate |
| C10 | Packet Store | Telling | Validate, freeze, hash, version; track staleness | C9 output, impact sets | L12 |
| C11 | Packet Compiler | Rendering | Render a packet into a drafting brief for a target drafter | L12, voice profile | Brief |
| C12 | Generation Gateway | Rendering | Call drafters; enforce the output contract; log | Brief | L13 DRF records |
| C13 | Validator | Rendering | Execute L14 suites | L12, L13, model | Validation reports |
| C14 | Autopsy Engine | Rendering | Execute L15 | Accepted drafts, model, manuscript | Findings, scorecards, proposals, RIS\_actual deltas |
| C15 | Gate Console | Control | Typed human gates: PROPOSAL, STRUCTURE, INTEGRATION, CANON, SHIP (§0.7) | Everything | Gate and RES records |
| C16 | Rule Registry | Control | Rule definitions, severities, versions | — | Rules |
| C17 | Version Store and Audit Log | Control | Revisions, branches, diffs, audit trail, impact index | All | History |

### 5.2 Data-flow architecture

| Flow | From → To | Payload | Trigger |
| --- | --- | --- | --- |
| F1 | Author → C1 → C15 → C1 | Canon records (PROPOSAL → ACCEPTED → CANON) | Author edit |
| F2 | Author or AI → C2 | L2–L4 records | Author edit; decomposition request |
| F3 | C2 → C3 | Lifted event proposals from beats | Beat ACCEPTED (path B) |
| F4 | C8 ↔ C4, C5, C6, C7 | Reconciliation cycle | Any gate decision that changes an ACCEPTED or CANON record to L1, L5, or overlays |
| F5 | C8 → C15 | Contradictions with candidate repairs | Reconciliation finds a violation |
| F6 | C15 → C1, C3 | Resolutions (approved edits plus RES records) | Human decision |
| F7 | C8 → C17 | Model version tagged CONSISTENT | Reconciliation passes |
| F8 | C2, C7, model → C9 | Scene plan, RIS(n−1), reconciled state | Extraction request |
| F9 | C9 → C10 | Packet candidate; pre-draft check results | Extraction completes |
| F10 | C10 → C11 → C12 | Frozen packet → brief | Draft request |
| F11 | C12 → C13 | Draft with declarations and beat map | Generation completes |
| F12 | C13 → C15 | Validation report | Validation completes |
| F13 | C15 → C14 | Accepted draft | Human acceptance |
| F14 | C14 → C7 | RIS\_actual delta | Autopsy completes |
| F15 | C14 → C15 → C1, C3 | Micro-fact and correction proposals | Autopsy completes; human gate |
| F16 | C17 → C10, C15 | Staleness notices for the impact set | Any commit |

&#91;embedded content: NSRES data flow · 3 planes, 9 layer groups, typed gates\]

Forward flows (solid) carry facts from canon to prose. The three feedback paths (dashed) carry accepted text back into the reader ledger, and micro-facts and corrections back to canon, but only through the human gates.

### 5.3 How state is filtered from world to scene

Extraction narrows the full model to one scene in nine stages. Each stage moves excluded material to an exclusion list with a reason code, so nothing disappears without a trace (P8).

| Stage | Input | Keeps | Excludes (reason code) |
| --- | --- | --- | --- |
| 1. Version pin | All versions | One CONSISTENT model version; only ACCEPTED and CANON records | Unreconciled changes (UNRECONCILED); PROPOSAL records (NOT\_ACCEPTED) |
| 2. Story-time slice | All events and states | Events overlapping the scene window; persistent states at window start | Events outside window (OUT\_OF\_WINDOW); their persistent effects are kept as states |
| 3. Spatial slice | Stage 2 | Events at scene locations; events perceptible from them; remote-channel arrivals | Events elsewhere (OUT\_OF\_PLACE) |
| 4. Participant slice | Stage 3 plus states | States of participants; states of absent characters that beats mention | States of uninvolved entities (UNINVOLVED) |
| 5. POV knowledge filter | Stage 4 | Propositions in CIS(pov, t) for interior narration; perceptible facts for exterior narration | Facts outside the POV's knowledge and perception (POV\_UNKNOWN); kept separately as unknown-information constraints |
| 6. Reader filter | Stage 5 | Each fact classified against RIS(n−1) and the reveal plan (§7.5) | Nothing removed; classification only |
| 7. Suppression transform | Stage 6 | Behavioral constraints derived from suppressed facts | The suppressed facts themselves (SUPPRESSED); stored in the extraction record, not the brief |
| 8. Thread priority | Stage 7 | Active threads ranked; foreground and background assigned | Nothing removed; background threads compressed |
| 9. Budget | Stage 8 | Content within the packet budget, by priority | Lowest-priority texture (BUDGET), never mandatory beats or LOCKED persistent state |

### 5.4 State-transition architecture

Three state machines govern NSRES: one for individual records, one for model versions, and one for each scene's packet-and-draft pipeline.

**Record lifecycle.**

| From | Trigger | Gate and guard | To |
| --- | --- | --- | --- |
| (new) | Created by author, engine, or AI | — | PROPOSAL |
| PROPOSAL | Approved | PROPOSAL gate (STRUCTURE gate for telling records); rule suite passes for the record in isolation | ACCEPTED |
| PROPOSAL | Declined | Any gate | REJECTED (kept for audit) |
| PROPOSAL | Declined for this work, kept for reuse | PROPOSAL gate | SLUSHED |
| PROPOSAL (micro-fact) | ACCEPT\_AND\_REGISTER | CANON gate | CANON |
| PROPOSAL (micro-fact) | REJECT\_MICRO\_FACT | CANON gate | REJECTED; prose span flagged NON\_CANONICAL |
| ACCEPTED (reality record) | Lock | CANON gate; rule suite passes | CANON |
| ACCEPTED | Edit | The gate that accepted it | ACCEPTED (new revision) |
| CANON | Edit | CANON gate; RETCON record if PUBLISHED | CANON (new revision) |
| ACCEPTED or CANON | Retire | Gate matching its status; every dependent re-pointed | DEPRECATED |
| CANON | Segment released | SHIP gate | CANON, tier PUBLISHED |

**Model version lifecycle.**

| From | Trigger | Guard | To |
| --- | --- | --- | --- |
| OPEN | Reconciliation starts | — | RECONCILING |
| RECONCILING | Run completes with zero BLOCKING contradictions among ACCEPTED and CANON records | — | CONSISTENT |
| RECONCILING | Run completes with BLOCKING contradictions remaining | — | INCONSISTENT |
| INCONSISTENT | Resolutions approved | INTEGRATION gate | OPEN |
| CONSISTENT | Tag requested | INTEGRATION gate | RELEASED |
| CONSISTENT or RELEASED | A gate decision changes an ACCEPTED or CANON record | — | New OPEN version; the old version stays readable |

**Scene pipeline.**

| From | Trigger | Guard | To |
| --- | --- | --- | --- |
| PLANNED | Extraction run | Model version CONSISTENT or RELEASED | EXTRACTED |
| EXTRACTED | Pre-draft checks | All MUST rules pass | PACKET\_VALID |
| EXTRACTED | Pre-draft checks | A MUST rule fails | EXTRACTION\_FAILED (diagnostic to L3/L4) |
| PACKET\_VALID | Freeze | STRUCTURE gate (human, or automated per tier, §11.4) | FROZEN |
| FROZEN | Draft request | Packet not STALE | DRAFTING |
| DRAFTING | Draft returned | Output contract satisfied | DRAFTED |
| DRAFTED | Validation | Zero BLOCKING findings; coverage statement present | VALIDATED |
| DRAFTED | Validation | Any BLOCKING finding | FAILED (regenerate, revise, or return to L11) |
| VALIDATED | Acceptance | INTEGRATION gate | ACCEPTED |
| ACCEPTED | Autopsy | — | AUTOPSIED |
| AUTOPSIED | Release | SHIP gate | SHIPPED |
| FROZEN to AUTOPSIED | Impact set includes a cited record | — | STALE |
| STALE (no draft accepted) | Re-extraction | — | EXTRACTED (new packet revision) |
| STALE (draft accepted) | Review of prose against the new model | INTEGRATION gate; prose still consistent | AUTOPSIED (CONFIRMED) |
| STALE (draft accepted) | Review of prose against the new model | INTEGRATION gate; prose inconsistent | REVISION\_REQUIRED, then re-extraction |

&#91;embedded content: Scene pipeline · 12 states, 3 gates, 1 regeneration loop\]

The main path snakes from PLANNED to SHIPPED. A failed validation loops back to drafting, and any upstream change sends a frozen or later scene to STALE, from which it is re-extracted against the new model.

**Requirements.**

- **REQ-5.4.1.** Every transition writes an audit record: from-state, to-state, trigger, actor, model version, timestamp.
- **REQ-5.4.2.** A packet MUST NOT be frozen against an OPEN, RECONCILING, or INCONSISTENT model version.
- **REQ-5.4.3.** A draft MUST NOT be accepted without a validation report that lists the suites run, their coverage, and zero BLOCKING findings.
- **REQ-5.4.4.** Staleness marking is automatic and immediate on any gate decision that changes a cited record. It does not wait for a human.

## 6. Timeline reconciliation

Reconciliation turns a set of event assertions into one consistent, queryable history. It solves time constraints, folds effects into state, propagates knowledge, and runs every rule, repeating until nothing changes or a contradiction blocks the version.

### 6.1 The reconciliation loop

1. **Ingest** all CANON and ACCEPTED records changed since the last CONSISTENT version. PROPOSAL records are reconciled separately, as dry runs against that set; they never change a version's status.
2. **Normalize**: resolve entity references and aliases; assign IDs; reject records that cite unknown entities.
3. **Build the temporal network** from every timestamp, duration, offset, relation, and anchor (§6.2, §6.3).
4. **Check temporal consistency.** A failure is RC-01 and blocks the run.
5. **Compute feasible windows** for every event start and end.
6. **Tighten** windows from derived constraints: travel times (§6.12) and knowledge lead times (§6.13).
7. **Fold effects** into state projections: L6, L7, L8 (§6.4–§6.6).
8. **Propagate knowledge** into L9 (§6.7).
9. **Compute reader-side checks** in L10 against the current telling plan (§6.8, §6.9).
10. **Run the rule suite** (§6.11, Appendix B).
11. **Iterate.** If steps 6–10 added constraints, return to step 4. Tightening only narrows windows, so the loop is monotone; on an integer tick domain it terminates. A run exceeding K iterations (default 20) raises RC-17 and blocks.
12. **Emit** the reconciliation report (§6.15) and set the version CONSISTENT or INCONSISTENT.

Incremental mode (DD): after the first full run, a change re-runs steps 3–11 only over its impact set — the affected story-time window plus every entity touched by events in it. A full run SHOULD still execute before any RELEASED tag.

### 6.2 Building the master timeline

NSRES represents time with two coupled networks.

**Metric network.** A simple temporal network (STN). Each event contributes two time points, start and end. Every metric constraint has the form below, where l and u are bounds in ticks (minutes by default).

```latex
l_{ij} \le t_j - t_i \le u_{ij}
```

The network is consistent if and only if its distance graph has no negative cycle. All-pairs shortest paths (Floyd–Warshall, O(n³), or an incremental variant) give each time point a feasible window relative to a fixed origin.

**Qualitative network.** Allen interval relations between events: BEFORE, MEETS, OVERLAPS, STARTS, DURING, FINISHES, EQUALS, and their inverses. Single relations translate into point constraints and join the STN. Disjunctive relations ("before or after") cannot be translated directly. General Allen-algebra satisfiability is NP-complete, so (DD):

- Disjunctions are allowed only where an author states them explicitly.
- The engine branches over them with a cap (default 2^10 combinations) and reports UNCHECKABLE beyond it.
- Each branch is solved as an STN; the version is consistent if at least one branch is.

**Lazy commitment (DD).** The engine keeps windows instead of choosing exact times. It commits a point only when an author fixes it, or when a packet needs one (the prose will state a clock time). A packet-driven commitment is a gated event edit. Reason: premature precision creates false contradictions, and most fiction never states most times.

### 6.3 Timestamping events

| Form | Syntax | *Harrow House* example | Becomes |
| --- | --- | --- | --- |
| Absolute point | `st: 1893-10-15T06:10 ±5m` | EVT-0105 Mara finds Edmund dead | start in \[06:05, 06:15\] |
| Absolute interval | `st: 22:15–22:25` on 14 Oct | EVT-0103 Edmund gives Jonah the key | start and end fixed |
| Duration | `duration: [20m, 40m]` | EVT-0112 Hale's interview of the household | end − start in \[20, 40\] |
| Relative offset | `after EVT-0104 by [3m, 10m]` | EVT-0106 Mara sees Jonah in the corridor | start(EVT-0106) − end(EVT-0104) in \[3, 10\] |
| Allen relation | `DURING NIGHT(1893-10-14)` | EVT-0101 Celia doses the decanter | Contained in the canon's night interval |
| Anchor | `at ANCHOR-02 (stable clock strikes eleven)` | Shared by two scenes | Both scenes share one time point |
| Fuzzy calendar | `"late October"`, `"a week later"` | Chemist's second report | Window from the canon calendar |
| Causal only | No time; bounded by causes and effects | Jonah hides the ledger | Window derived from neighbors |

Each timestamp carries a precision tag: MINUTE, QUARTER\_HOUR, HOUR, PART\_OF\_DAY, DAY, WEEK, MONTH, SEASON, YEAR. A tag with no explicit ± maps to a default window (HOUR = ±30 min; DAY = the whole day).

**REQ-6.3.1.** A time stated in accepted prose ("the clock showed a quarter to seven") MUST lie inside the event's window. On acceptance, the window collapses to that time through a gated canonization.

### 6.4 Deriving character timelines

1. Collect every event where the character has a role other than REMOTE. Each yields a presence segment: (location, window).
2. Sort segments by earliest feasible start.
3. Merge consecutive segments at the same location when the gap allows the character to have stayed (persistence).
4. For each consecutive pair at different locations, create a travel requirement and check it (§6.12).
5. Label intervals with no evidence as UNACCOUNTED, unless a canon routine applies (CAN-052: servants are in the servants' quarters between 23:00 and 05:30 unless an event says otherwise). Routine-filled intervals are tagged AMBIENT.
6. Fold persistent-attribute effects to produce attribute timelines.

Result for CHR-001 Mara, 14–15 October:

| Window | Location | Source | Notes |
| --- | --- | --- | --- |
| 21:00–22:30 | Servants' hall | EVT-0098 (evening accounts) | — |
| 22:30–22:43 | Stairs to east wing | Travel inference | Feasible: 4 min minimum |
| 22:43–22:48 | East corridor | EVT-0106 | Witnesses Jonah (KG-0031) |
| 22:48–05:30 | Housekeeper's room | CAN-052 routine | AMBIENT |
| 05:30–06:05 | Kitchen and servants' hall | EVT-0099 (morning duties) | — |
| 06:05–06:15 | Edmund's bedroom | EVT-0105 | Finds the body |
| 07:40–08:10 | Servants' hall | EVT-0112 | Interviewed by Hale (SCN-007) |
| 06:15–07:40 | UNACCOUNTED | — | Not referenced by any scene; no finding |

### 6.5 Deriving location timelines

1. Invert all presence segments by location to get occupancy intervals.
2. Fold location-state effects (lock, light, damage) onto canon defaults.
3. Apply the canon daylight model for natural light by story-time.
4. Compute perceptibility windows: for each event, which adjacent locations could perceive it, by sense, using canon adjacency and ranges.
5. Invert object custody where the holder is a location, giving objects present.

### 6.6 Deriving object histories

1. Collect creation, destruction, transfer, and state effects per object.
2. Fold them into a custody chain and a state timeline.
3. Check the conservation law (REQ-L8.1) at every boundary.
4. **Implicit-transfer inference.** If custody is A at t1 and B at t2 with no transfer between, the engine proposes a bridge transfer event with window \[t1, t2\], requiring A and B to be co-present (or an intermediate location). The proposal is never auto-accepted.

### 6.7 Tracking information propagation

1. **Grants from effects.** Every event effect that conveys information produces a knowledge grant.
2. **Witness grants (DD).** For each event with perceptible content, the engine generates WITNESSED grants automatically for AGENT, PATIENT, and WITNESS roles, and proposes them (for confirmation) for PRESENT roles and for entities within perceptibility range. An author suppresses an unwanted grant with a NOT\_NOTICED marker on the event. Reason: auto-granting everyone present over-propagates; granting no one misses most real knowledge.
3. **Told grants** come from dialogue or message events with content fields.
4. **Claims propagate as beliefs.** A lie told to a character becomes a BELIEVED grant whose truth value is FALSE.
5. **Belief revision.** When a holder receives a proposition that conflicts with one already held, the new one replaces the old if the source's trust (from a per-character trust table, default equal) is at least the current source's. Otherwise both are kept and marked CONFLICTED.
6. **Reachability index.** For every proposition, the engine maintains which holders could have learned it by each time, given positions and channels. This powers §6.13.

Propagation of INF-001 (Edmund was poisoned):

| Holder | Time | Channel | Confidence | Source |
| --- | --- | --- | --- | --- |
| Celia | 14 Oct 20:50 | AGENT of EVT-0101 | CERTAIN | Her own act |
| Hale | 15 Oct 09:30 | INFERRED from INF-007 (residue in the decanter) | SUSPECTED | EVT-0114 |
| Hale | 16 Oct 14:00 | READ (chemist's report) | CERTAIN | EVT-0131 |
| GRP-001 Kellby village | 16 Oct evening | RUMOR | BELIEVED | EVT-0133 |

### 6.8 Keeping hidden events hidden

**Hidden is not absent.** Hidden events are fully modeled and reconciled. Only their delivery to the reader is controlled.

1. **Visibility designation.** Each event and fact carries REVEALABLE, HIDDEN\_UNTIL(RVL), or PERMANENT\_MYSTERY.
2. **Trace facts.** Observable effects of hidden events are separate facts with their own visibility. A trace can be REVEALABLE while its cause is HIDDEN. Example: EVT-0103 (Edmund gives Jonah the key) is hidden; its trace INF-008 (the key is missing from the board) is revealable at 1.03.2. Traces are how clues work in NSRES.
3. **Extraction suppression.** Hidden facts never enter a drafting brief by default. They become behavioral constraints (§7.6).
4. **Hidden-causality ledger.** For each NT position, L10 lists every rendered effect whose cause is hidden, with its covering reveal or permanent-mystery record. An entry with no cover is RC-16.

### 6.9 Supporting later reveals

A reveal record (RVL) holds: target propositions; NT position; delivery mode; prerequisites (propositions that MUST be in RIS before the reveal); delivering scene and beat; and a retro-consistency scope (the NT range that must be compatible with the revealed truth).

**REQ-6.9.1 (retro-consistency).** When a reveal's scene is accepted, every accepted scene in its scope is re-checked. No assertion in those scenes may contradict the revealed proposition, except assertions classified as character claims (lies) or as registered narrator misdirection. Informally: the twist must survive rereading.

**Fair-play check (optional, per genre).** For a mystery's solution, each premise of the solving inference must be in RIS\_actual with mode HINTED or stronger before the solving scene.

**Reread probe.** An independent reader model (§9.3) receives only the text before the reveal and judges whether the reveal is already obvious (leak), supported (fair), or unsupported (cheat). The probe is advisory; the author decides.

### 6.10 Overlapping events

1. Concurrency is normal. Many events overlap in story-time.
2. A character may participate in two overlapping events only if both are at the same location, or the character's role in one is REMOTE.
3. **Synchronization anchors.** A shared perceptible event (a clock striking, a gunshot, a storm breaking) gives several scenes a common time point. Scenes citing the same anchor must agree on it (RC-15).
4. **Intercutting.** Two scenes with overlapping windows may be rendered alternately, so NT order differs from ST order. The engine checks that no character in one scene reacts to an event in the other before it occurs in story-time.
5. **One event, two POVs.** Both scenes render the same event. Facts must agree. Perception may differ, because each POV perceives from its own position and range.

### 6.11 Contradiction catalog

| Code | Contradiction | Detection rule | Default severity |
| --- | --- | --- | --- |
| RC-01 | Temporal inconsistency | Negative cycle in the STN (in every branch) | BLOCKING |
| RC-02 | Exclusive-attribute conflict | Two effects set different values of one exclusive attribute in overlapping windows | BLOCKING if CERTAIN; MAJOR if POSSIBLE |
| RC-03 | Invariant violation | A canon invariant evaluates FALSE at some story-time | BLOCKING |
| RC-04 | Precondition failure | A precondition is FALSE at event start (UNDETERMINED gives MAJOR "unsupported") | BLOCKING |
| RC-05 | Existence violation | An entity acts or is used outside its existence interval | BLOCKING |
| RC-06 | Causal cycle | A cycle in the causal graph | BLOCKING |
| RC-07 | Causal order | A cause's effect-time is later than its successor's start | BLOCKING |
| RC-08 | Impossible movement | §6.12 | BLOCKING if impossible; tightening otherwise |
| RC-09 | Ubiquity | Overlapping presences at different locations without REMOTE | BLOCKING |
| RC-10 | Impossible knowledge | §6.13: no valid channel could exist | BLOCKING |
| RC-11 | Unsourced knowledge | Knowledge used, no grant, but a channel was available | MAJOR (grant proposed) |
| RC-12 | Custody violation | Dual custody, or transfer from a non-holder | BLOCKING |
| RC-13 | Access violation | Entry to a locked or inaccessible location with no access event | MAJOR |
| RC-14 | Perception violation | A WITNESSED grant without presence or perceptibility | BLOCKING |
| RC-15 | Anchor disagreement | Scenes citing one anchor at incompatible times | BLOCKING |
| RC-16 | Uncovered hidden causality | A rendered effect with a hidden, uncovered cause | MAJOR |
| RC-17 | Non-convergence | The loop exceeds K iterations | BLOCKING |

### 6.12 Detecting impossible movement

For a character with a presence at location l1 ending in the window \[b1\_min, b1\_max\], followed by a presence at l2 starting in \[a2\_min, a2\_max\], let τ be the minimum travel time from l1 to l2 using the modes available to that character at that time (canon metrics).

```latex
\text{IMPOSSIBLE if } a_2^{\max} - b_1^{\min} < \tau \qquad \text{TIGHTEN if } a_2^{\max} - b_1^{\min} \ge \tau > a_2^{\min} - b_1^{\max} \qquad \text{OK otherwise}
```

- **IMPOSSIBLE**: no placement inside the windows allows the trip. RC-08, BLOCKING.
- **TIGHTEN**: some placements work. The engine adds start(next) − end(previous) ≥ τ to the STN and re-propagates. This can cascade to other events and is how most movement constraints shape the timeline.
- **Schedules.** Where travel depends on timetables (trains, ferries), a fixed τ is replaced by an earliest-arrival function EA(l1, l2, departure time) built from canon timetables. The check becomes: is there a departure time inside the window whose earliest arrival precedes a2\_max?
- **Mode availability.** A mode needs its resources at departure time (a carriage needs a horse and driver present). Unavailable modes are excluded from τ.

**Example.** The first outline has Hale arriving at Harrow House at 07:40 on 15 Oct, summoned by a telegram sent to York at 07:00. York to Kellby by rail plus the station-to-house drive gives an earliest arrival of 09:30 (CAN-060, CAN-061). Result: IMPOSSIBLE (RC-08). Candidate repairs: move SCN-007 after 09:30 (conflicts with two later scenes); or add bridge event EVT-0090, Hale already lodging at The Bell on another inquiry since 13 Oct, fetched by the constable at 07:05 (20 minutes' drive). The author chose the bridge (RES-0011).

### 6.13 Detecting impossible knowledge acquisition

Every beat or event in which an agent acts on, states, or reacts to proposition p creates a knowledge-use record with precondition knows(c, p) at t\_use. The check:

```latex
\exists\, g:\ g.\mathrm{holder} = c \wedge g.\mathrm{prop} \equiv p \wedge g.t \le t_{use} \wedge \mathrm{valid}(g) \wedge \neg \exists\, r:\ \mathrm{revokes}(r, g) \wedge g.t < r.t \le t_{use}
```

| Outcome | Condition | Severity | Typical repair |
| --- | --- | --- | --- |
| VALID | A valid grant exists in time | — | — |
| UNSOURCED | No grant, but the reachability index shows a valid channel was available | MAJOR | Add a grant event (proposed) |
| IMPOSSIBLE | No valid channel could exist, given positions, documents, and remote-channel latencies | BLOCKING | Move the use later; change what the character says; add an earlier event that creates a channel |
| PREMATURE | A grant exists, but after t\_use | BLOCKING | Move the use or the grant |
| OVERCONFIDENT | The use requires CERTAIN; the grant gives SUSPECTED or BELIEVED | MAJOR | Lower the confidence the beat displays |
| LAUNDERED | An INFERRED grant whose premises fail this same check | BLOCKING | Fix the premises first |

The reachability search runs backward from t\_use: for each holder h of p, is there a time t' at which h could have conveyed p to c (co-presence, a document c could access, or a remote channel whose latency fits before t\_use)?

**Example.** An outline beat has Hale say "the brandy was poisoned" at 10:00 on 15 Oct. His only grant of INF-001 is READ at 14:00 on 16 Oct: PREMATURE. Repair chosen: add EVT-0114 at 09:30 (Hale examines the decanter; trace INF-007, residue) with an INFERRED grant at SUSPECTED. The beat changes from a statement to a suspicion (RES-0014).

### 6.14 Resolution protocol

1. **Classify** the contradiction: code, CERTAIN or POSSIBLE, records involved.
2. **Generate candidate repairs** from the repair library for that code: move an event within its window; widen or narrow a window; add a bridge event; add a channel event; change a participant role; lower a displayed confidence; change a beat outcome; amend a canon rule; declare a duplicate object; mark a proposition UNDETERMINED.
3. **Dry-run** each candidate through incremental reconciliation and record the contradictions it creates or removes.
4. **Score** each candidate (HEU). Lower is better. Weights are configurable; defaults w1 = 1, w2 = 10, w3 = 2, w4 = 5.

```latex
\mathrm{cost} = w_1 \cdot \Delta_{\text{records}} + w_2 \cdot \Delta_{\text{published or accepted}} + w_3 \cdot N_{\text{new AI-origin}} + w_4 \cdot N_{\text{new contradictions}}
```

5. **Present** the top candidates, with dry-run results, at the gate.
6. **Decide.** The human picks a candidate or writes a custom repair.
7. **Commit** the decision at the INTEGRATION gate (the CANON gate when canon changes) with a RES record, then re-reconcile.

**REQ-6.14.1.** The engine MUST NOT auto-apply a repair that changes an ACCEPTED or CANON record. It MAY auto-apply window tightening, which narrows solved windows and changes no authored statement.

### 6.15 Reconciliation report

| Field | Content |
| --- | --- |
| run\_id, mode | RUN-R-0047; FULL or INCREMENTAL (with impact set) |
| version\_in, version\_out, status | truth@r46 → truth@r47; CONSISTENT or INCONSISTENT |
| counts | Findings by code and severity |
| findings | FND records with evidence and candidate repairs |
| tightened\_windows | Events whose windows narrowed, before and after |
| proposals | Bridge events, grants, and transfers proposed, all at status PROPOSAL |
| undetermined\_referenced | UNDETERMINED propositions that a planned scene depends on |
| uncheckable | Checks that could not run, with the missing data (for example, no travel metric between LOC-002 and LOC-004) |
| iterations, runtime | Loop count; elapsed time |

## 7. Scene Extraction Engine

The Scene Extraction Engine (SEE) converts one scene plan plus the reconciled model into a packet candidate in eighteen deterministic steps. It decides what the scene may use, must use, and must not reveal, so the drafter makes no fact-level decisions.

### 7.1 Inputs

| Input | Source | Required | Admission check |
| --- | --- | --- | --- |
| Scene record | L3 | Yes | Status ACCEPTED |
| Beat list | L4 | Yes | At least one mandatory beat; all beats ACCEPTED |
| Model version | C17 | Yes | CONSISTENT or RELEASED |
| Projections L6–L9 at that version | C5, C6 | Yes | Generated for the pinned version |
| RIS\_plan(n−1) and RIS\_actual(n−1) | L10 | Yes | RIS\_actual may be empty before any accepted text; the packet is then flagged PLAN\_ONLY |
| Reveal plan and secrets register | L2, L9 | Yes | ACCEPTED or CANON |
| Thread register with ranks | L2 | Yes | Every thread ranked |
| Invention-policy defaults and scene overrides | L1, L3 | Yes | Overrides cite a reason |
| Drafting configuration | L3, work settings | Yes | Length range, tense, person, voice profile reference |
| Budget | Work settings | Yes | Positive integer (tokens or words) |
| Mode flags | Work settings | No | informed\_drafting (default off); strict (default on) |
| Previous packet revision | L12 | No | Used to produce a diff for reviewers |

**REQ-7.1.1.** A packet may cite only ACCEPTED or CANON records. PROPOSAL records are excluded at admission with reason code NOT\_ACCEPTED, so no unapproved AI output can reach a drafter as fact.

### 7.2 Processing pipeline

1. **Admission.** Check every input; pin the model version.
2. **Window resolution.** Take the scene window W = \[ws, we\]. Intersect it with the windows of every event bound to a mandatory beat. An empty intersection halts with EX-01.
3. **Entry snapshot.** Compute state at ws for the scene's locations, participants, objects present, and entities mentioned by beats.
4. **Exit expectation.** Apply beat deltas in order to the entry snapshot. Check that every planned outcome holds at we and no rule fails. Failure halts with EX-03.
5. **Participant verification.** Confirm each participant is present (L6) through the part of W where it acts. Confirm the POV is present if the POV mode requires it. Failure halts with EX-02.
6. **Candidate events.** Collect events overlapping W at the scene locations, perceptible events from adjacent locations, remote-channel arrivals, and all beat-bound events.
7. **Fact gathering.** Collect facts whose truth changes in W; persistent attributes of participants, locations, and objects present; and every proposition a beat references.
8. **POV filter.** Compute CIS(pov, t) across W and the POV's perception set (§7.4).
9. **Visibility classification.** Assign every gathered fact one or more classes (§7.5).
10. **Reveal rules** (§7.7).
11. **Suppression rules** (§7.6), producing behavioral manifestations.
12. **Thread prioritization** (§7.8).
13. **Character-state compilation**, one block per participant (§8, field group G).
14. **Constraint compilation**: continuity constraints, invention policy, locked terms, drafting constraints.
15. **Outcome specification**: required outcomes and forbidden outcomes as state deltas.
16. **Budget allocation** (§7.9).
17. **Pre-draft checks** (§7.10).
18. **Assembly.** Serialize canonically, hash, store as PACKET\_VALID with the extraction record.

### 7.3 Selection rules

| Rule | Statement |
| --- | --- |
| SR-1 | Include every event bound to a mandatory beat. |
| SR-2 | Include every event overlapping W at a scene location in which a participant has a role other than REMOTE. |
| SR-3 | Include events at adjacent locations whose perceptibility reaches the POV's location, as perception candidates (not foreground). |
| SR-4 | Include each participant's persistent state at ws: position in the scene, injuries, changed clothing, possessions with significance CLUE or PLOT\_OBJECT, and relationships with other participants. |
| SR-5 | Include location state: lock state, light, conditions, and objects present with significance CLUE or higher. |
| SR-6 | Include reader-continuity anchors: the last rendered description (from RIS\_actual) of each participant and object the reader will expect to be consistent, such as a described injury or a described room. |
| SR-7 | Include the story-time gap since each participant last appeared in narrative order, plus REVEALABLE offscreen events in that gap that the scene may reference. |
| SR-8 | Exclude events with no involved participant and no perceptibility to the POV. |
| SR-9 | Include open questions the scene's beats touch. |
| SR-10 | Include setups whose payoff is scheduled here, and plants scheduled here. |

### 7.4 POV rules

| POV mode | Narrator knowledge horizon | Interiority allowed | Perception bound |
| --- | --- | --- | --- |
| FIRST\_EXPERIENCING | CIS(pov, t) at each moment | POV only | POV's senses and attention |
| FIRST\_RETROSPECTIVE | CIS(pov, t\_narration); later knowledge only for propositions listed in `narrator_horizon` | POV only | POV's senses at the time |
| CLOSE\_THIRD | CIS(pov, t) | POV only | POV's senses and attention |
| DISTANT\_THIRD | CIS(pov, t), plus externally observable facts at the scene location | Minimal, POV only | Scene location |
| OMNISCIENT | WIS(t), with delivery governed by the reveal plan | Characters listed in `permitted_interiority` | None beyond the reveal plan |
| CAMERA (screenplay, objective) | Observable facts only | None | Camera position or positions |
| UNRELIABLE (modifier on any mode) | Narrator belief set, which may contain FALSE propositions | As base mode | As base mode |

| Rule | Statement |
| --- | --- |
| PV-1 | Interior propositions MUST be a subset of CIS(pov, t), except in OMNISCIENT mode. |
| PV-2 | Perceived events MUST be perceptible to the POV: in range, by an available sense, and not marked NOT\_NOTICED. |
| PV-3 | Reader-ahead irony: if p is in RIS and not in CIS(pov), the POV MUST NOT think about, act on, or allude to p. Listed in `irony_constraints`. |
| PV-4 | Reader-behind withholding: if p is in CIS(pov) but hidden from the reader in a close mode, narration MUST avoid the POV's thoughts on p. This requires an explicit withholding technique in the reveal plan (cut away, attention elsewhere, delayed disclosure). Without one, the scene is flagged CHEAT\_RISK (WARNING), because close narration that conceals what the POV is thinking about can read as unfair. |
| PV-5 | Naming: the POV refers to entities only by names it knows. Mara cannot name a stranger before she is told the name. |
| PV-6 | Unreliable narration: narrator beliefs that are FALSE MAY be asserted; autopsy classifies them as narrator claims, not as contradictions, if they are registered. |

### 7.5 Visibility classes and rules

A fact may carry more than one class. A SUPPRESSED fact active in the scene is usually also FORBIDDEN.

| Class | Condition | Packet treatment |
| --- | --- | --- |
| PERMANENTLY\_UNDETERMINED | Marked by the author | Listed as forbidden; the text must not resolve it |
| FORBIDDEN | Its reveal is later, and this scene's content could leak it | `forbidden_revelations`, with leak indicators |
| REVEAL\_NOW | A reveal or planned delta delivers it here | `required_outcomes`, with delivery mode |
| HINT | A trace or clue scheduled as HINTED here | `permitted_hints`, with maximum explicitness |
| ALREADY\_KNOWN | In RIS(n−1), actual track preferred | `reader_known`; may be referenced, need not be re-explained |
| IRONY | In RIS and not in CIS(pov) | `irony_constraints` |
| UNKNOWN\_TO\_POV | Relevant, not in CIS(pov), not reader-known | `unknown_information`, as an avoidance constraint |
| SUPPRESSED | Hidden, and active in the scene (it affects a participant's behavior) | Not stated; converted to manifestations |
| PERCEIVABLE | Perceptible to the POV, REVEALABLE, not planned | May be rendered as texture, CONSTRAINED |

| Rule | Statement |
| --- | --- |
| VR-1 | Every fact in the packet carries at least one class. |
| VR-2 | A detail in neither RIS nor the packet may be invented only if it is FREE and unrelated to any forbidden proposition. |
| VR-3 | ALREADY\_KNOWN facts carry a reference to how they were delivered (the scene and the established wording), so descriptions stay consistent. |
| VR-4 | A fact that is both REVEAL\_NOW and FORBIDDEN halts extraction with EX-04. |

### 7.6 Suppression rules (suppression by abstraction)

Suppression by abstraction is NSRES's default method for turning Hidden Event Pressure (DEF-43) into drafting input (DD, tested by H3). The drafter never sees the secret. It sees only how the secret shows on the surface.

| Rule | Statement |
| --- | --- |
| SU-1 | With informed drafting off (the default), a SUPPRESSED fact never appears in the packet's drafting brief. It is stored only in the extraction record. |
| SU-2 | For each SUPPRESSED fact active in the scene, derive manifestations: observable behaviors of participants who hold it or are affected by it, consistent with their goals and the secrets register's concealment strategy. Each manifestation names an actor, a behavior, an intensity bound, a permitted in-scene explanation (a deflection), and forbidden explanations. |
| SU-3 | Manifestations MUST NOT, singly or together, let a reader holding RIS(n−1) infer the suppressed fact beyond its scheduled hint level. A pre-draft leak probe (§9.3) tests this. If the probe infers the fact above threshold, intensity is reduced or the manifestation is removed. |
| SU-4 | Manifestations are written in behavioral terms ("Jonah answers in single words and does not meet Hale's eye"), never in motive terms ("Jonah fears Hale will find the ledger"). |
| SU-5 | If a hidden fact changes no onscreen behavior, no manifestation is emitted. |
| SU-6 | Informed-drafting mode (optional) gives the drafter suppressed facts in a sealed section with an explicit non-disclosure instruction. Use it only for human drafters, or for an AI drafter where H3 testing showed benefit. Autopsy applies stricter leak thresholds in this mode. |

**Why suppression by abstraction (DD).** A drafter told a secret and asked not to reveal it tends to write around it, and the shape of the avoidance can itself leak (HYP; this is H3). A drafter that never holds the secret cannot leak it directly. The residual risk is incoherent behavior, which SU-2 addresses by supplying the behavior and its permitted explanation.

### 7.7 Reveal rules

| Rule | Statement |
| --- | --- |
| RV-1 | A REVEAL\_NOW fact is delivered in its planned mode (STATED, SHOWN, IMPLIED, HINTED, or MISLED) and appears in `required_outcomes`. |
| RV-2 | Reveal prerequisites must be in RIS\_actual before freezing. If they are only in RIS\_plan (an earlier scene is not yet accepted), the packet freezes with a dependency flag and is re-checked when that scene is accepted. |
| RV-3 | Deliver exactly the target proposition. Propositions it entails, or that sit next to it, are listed in `adjacent_not_delivered` unless separately scheduled. |
| RV-4 | MISLED delivery requires a registered correction position or a permanent-ambiguity record. |
| RV-5 | A retelling (an already-delivered proposition delivered again, often from a new POV) needs a RETELLING tag and must agree with the earlier delivery. |

### 7.8 Thread prioritization and narrative pressure

Each thread active in the scene's window receives a priority score (HEU). Defaults: w\_r = 1.0, w\_n = 2.0, w\_p = 1.0, w\_g = 0.5, w\_c = 1.0.

```latex
\mathrm{priority}_k = w_r \cdot \mathrm{rank}_k + w_n \cdot \mathbb{1}[\text{scene renders a node of } k] + w_p \cdot \pi_k + w_g \cdot \gamma_k + w_c \cdot \mathbb{1}[\text{convergence node}]
```

Where rank is 3 (primary), 2 (secondary), or 1 (tertiary); π\_k is the thread's normalized share of narrative pressure at n−1; and γ\_k is the normalized narrative distance since the thread was last visibly touched (so dropped threads rise).

| Role assigned | Condition | Treatment |
| --- | --- | --- |
| FOREGROUND | The scene renders a node of the thread | Full context; budget proportional to priority |
| BACKGROUND | Visible, active, no node rendered | Brief mention context; at most one beat of reference |
| SUPPRESSED | Hidden at n | Manifestations only (§7.6) |
| DORMANT | Not active in the window | Omitted |

**Narrative pressure** at position n is a vector of five components (HEU, a planning aid only):

```latex
\mathbf{P}(n) = \Big( \textstyle\sum_{q \in Q_{open}} s_q,\ \sum_{d \in D} s_d\, e^{-\Delta t_d / \lambda},\ \sum_{h \in H} s_h,\ \sum_{u \in S_{open}} \mathrm{age}_u,\ \sum_{g \in I} s_g \Big)
```

The components are: open questions weighted by stakes; deadlines weighted by story-time proximity (λ sets the decay); threats near the POV weighted by severity; outstanding setups weighted by age in scenes; and dramatic-irony gaps weighted by stakes. Stakes weights (s) are author-assigned on a 1–5 scale.

### 7.9 Budget rules

1. Compute mandatory content M: identity and position; POV; mandatory beats; LOCKED persistent state; forbidden revelations; required outcomes; constraints.
2. If M exceeds the budget B, halt with EX-05. Mandatory content is never truncated.
3. Fill the remaining budget in priority order: reader-continuity anchors; foreground thread context; participant goals; setting state; background threads; texture.
4. Summarization of background material by an LLM is permitted. Summaries are tagged AI-origin and re-checked by CC-2 and CC-7.

### 7.10 Pre-draft continuity checks

| Check | Statement |
| --- | --- |
| CC-1 | Every participant is present in L6 across the part of W where it acts. |
| CC-2 | No forbidden proposition appears in any brief field, by string match or by semantic paraphrase check. |
| CC-3 | Required outcomes are reachable from the entry snapshot through the beats, with no rule failure. |
| CC-4 | Every mandatory beat's actor is a participant. |
| CC-5 | Every LOCKED fact in the packet equals the model value in W. |
| CC-6 | Reveal prerequisites are satisfied, or a dependency flag is set. |
| CC-7 | The manifestation leak probe scores below threshold for every suppressed fact. |
| CC-8 | Every proposition in `reader_known` is in RIS(n−1). |
| CC-9 | The POV's interior knowledge list is a subset of CIS(pov). |
| CC-10 | The packet's model version is CONSISTENT or RELEASED. |

### 7.11 Extraction errors

| Code | Error | Routed to |
| --- | --- | --- |
| EX-01 | Empty scene window after intersection | L3 (window) or L5 (event times) |
| EX-02 | Participant or POV absent | L3 participants or L5 presence |
| EX-03 | Required outcome unreachable | L4 beats |
| EX-04 | A fact is both REVEAL\_NOW and FORBIDDEN | L2 reveal plan |
| EX-05 | Mandatory content exceeds budget | L4 (fewer mandatory beats) or budget setting |
| EX-06 | POV cannot perceive a required beat | L3 POV or L4 beat |
| EX-07 | A manifestation leaks irreducibly | L2 reveal plan or L4 beats |

### 7.12 Output

A packet candidate conforming to §8, in state PACKET\_VALID, plus a RUN-X extraction record holding every selection, exclusion, classification, manifestation, score, and rule trace.

## 8. Scene Packet specification

A scene packet is a frozen JSON document with two sections: a public section that is compiled into the drafter's brief, and a sealed section that only validators and autopsy read. Its fields fall into thirteen groups, A through M.

### 8.1 Structure and serialization

- **Two sections.** `public` holds everything the drafter may use. `sealed` holds suppressed facts, forbidden propositions in full, and leak indicators. The sealed section is never sent to a drafter unless INFORMED\_DRAFTING is flagged (SU-6).
- **Canonical serialization.** UTF-8 JSON, keys sorted, no insignificant whitespace. `packet_hash` is the SHA-256 of the canonical whole; `public_hash` is the SHA-256 of the canonical public section alone.
- **Requirement levels.** REQUIRED (always present; may be an empty list where stated), CONDITIONAL (required when its condition holds), OPTIONAL.
- **Traceability.** Every non-empty field is covered by the `sources` map in group M (P8).

### 8.2 Field groups

Each table gives the field's purpose, type and requirement, source layer, validation rule, and an example from SCN-007 (Hale's first interview of the household, Mara's POV).

**A. Identity and provenance**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| packet\_uuid | Storage key | UUIDv7; REQUIRED | L12 | Unique; immutable | 01920c3e-7a41-7c2b-9d1e-5f3a8b2c4d6e |
| packet\_handle | Human-readable ID | `PKT-<scene>-r<n>`; REQUIRED | L12 | Revision increments by one per re-extraction | PKT-007-r3 |
| schema\_version | Consumer compatibility | semver; REQUIRED | L12 | Supported by the compiler and validators | 0.1.0 |
| scene\_ref | Link to the scene plan | handle; REQUIRED | L3 | Scene ACCEPTED | SCN-007 |
| model\_version | Pin to reconciled state | string; REQUIRED | C17 | CONSISTENT or RELEASED (REQ-5.4.2) | canon@r12/truth@r47 |
| extraction\_run | Audit link | handle; REQUIRED | L11 | Same model\_version | RUN-X-0212 |
| packet\_hash, public\_hash | Integrity | SHA-256; REQUIRED | L12 | Recomputed on every read; a mismatch blocks use | sha256:9f2c… |
| status | Lifecycle state | enum; REQUIRED | L12 | Scene pipeline (§5.4) | FROZEN |
| flags | Conditions affecting use | set of PLAN\_ONLY, DEPENDENCY:\<scene>, CHEAT\_RISK, INFORMED\_DRAFTING; OPTIONAL | L11 | Each flag has a cause in the extraction record | DEPENDENCY:SCN-006 |
| gate\_record | Who froze it, at which gate | {gate, actor, time}; CONDITIONAL (FROZEN) | C15 | Gate is STRUCTURE | STRUCTURE, author, 2026-10-25T19:02Z |
| confidence\_vector\_ref | Packet readiness score | ref; REQUIRED | §11.5 | Band READY, or a recorded human override | CV-PKT-007-r3, 0.96 |

**B. Position and time**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| narrative\_position | Place in the telling | NT string; REQUIRED | L3 | Equals L3; unique among ACCEPTED scenes | 1.03.2 |
| story\_time\_range | Story-time window | {start, end, precision}; REQUIRED | L3 intersected with L5 | Non-empty; inside every bound event's window | 1893-10-15T07:40 to 08:10, QUARTER\_HOUR |
| previous\_scene, next\_scene | Narrative neighbors | handles; REQUIRED (null at ends) | L3 | Exist | SCN-006, SCN-008 |
| story\_time\_gap | Elapsed story-time since the previous scene and since each participant last appeared | object; REQUIRED | L6, L10 | Non-negative unless anachrony | None: continuous with SCN-006 (Hale's arrival, 1.03.1) |
| anachrony | Flashback or flash-forward status | NONE, ANALEPSIS, PROLEPSIS, plus frame ref; REQUIRED | L3 | Frame scene exists if not NONE | NONE |
| narration\_stance | Tense and narrating time | {tense, narrating\_time}; REQUIRED | L3 | Consistent with the POV mode | past, retrospective-close |
| anchors | Synchronization anchors in the window | list; OPTIONAL | L5 | Agree across scenes (RC-15) | none |

**C. Setting**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| location | Primary place | handle and name; REQUIRED | L1, L7 | Every participant present there | LOC-001c servants' hall |
| sub\_locations | Adjoining places in play | list; OPTIONAL | L1 | Adjacency exists | LOC-001d kitchen, through an open door |
| setting\_state | Conditions at window start and changes inside the window | list; REQUIRED | L7 | Each value equals the model | Fire lit in the range; grey daylight from the high windows; key board on the east wall |
| objects\_present | Objects in the location, with state and significance | list; REQUIRED | L8 | Conservation law (REQ-L8.1) | OBJ-004 key board; the study key's hook is empty |
| perceptibles | What the POV can hear or see from elsewhere | list; OPTIONAL | L7, L5 | Perceptibility rules | Kitchen sounds through the open door |
| reader\_continuity\_anchors | Last rendered descriptions to stay consistent with | list; OPTIONAL | L10 (RIS\_actual) | Exist in accepted drafts | Hall described at 1.01.3: long deal table, copper pans |

**D. POV and narration**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| pov\_character | Whose view | handle; REQUIRED | L3 | Participant; present (CC-1) | CHR-001 Mara Voss |
| pov\_mode | Narration mode | enum (§7.4); REQUIRED | L3 | Allowed for the work | CLOSE\_THIRD |
| narrator\_horizon | Later knowledge the narration may use | list of INF; CONDITIONAL (FIRST\_RETROSPECTIVE) | L2, L3 | Each item explicitly permitted | empty |
| permitted\_interiority | Whose thoughts may be rendered | list; REQUIRED | L3 | Close modes: POV only (PV-1) | CHR-001 |
| perception\_constraints | Sense and range limits | list; OPTIONAL | L1, L6 | — | Cannot see the east corridor from the hall |
| naming\_map | How the POV refers to each entity | map; REQUIRED | L6, L9 | PV-5; covers every entity in public fields | CHR-002 → "Inspector Hale" |
| voice\_profile\_ref | Style reference | ref; REQUIRED | Work settings | Exists | VOICE-MARA-v2 |
| narrator\_beliefs | False beliefs narration may assert | list of CLM; CONDITIONAL (UNRELIABLE) | L9 | Registered claims (PV-6) | empty |

**E. Threads**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| active\_threads | Threads in play, with role and nodes | list {thread, rank, role, nodes, priority}; REQUIRED | L2, L11 | At least one FOREGROUND | THR-01, primary, FOREGROUND, NOD-01-04, 6.0 |
| hidden\_threads | The scene's Hidden Event Pressure (DEF-43) | list {sup\_ref, manifestations}; REQUIRED, may be empty | L9, L11 | No proposition content; leak probe below threshold (CC-7) | SUP-1 with one manifestation |
| manifestation | One observable behavior | {actor, behavior, intensity 1–3, permitted\_explanation, forbidden\_explanations}; within hidden\_threads | L11 | SU-2 to SU-4 | Jonah answers in single words and avoids Hale's eye; intensity 2; permitted: he slept badly |
| background\_threads | Visible threads with no node here | list; OPTIONAL | L11 | At most one beat of reference each | empty |

**F. Beats**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| required\_beats | Ordered mandatory beats | list {beat, type, actors, outcome, events, deltas}; REQUIRED | L4 | Actors are participants (CC-4); deltas reachable (CC-3) | BT-007-04 DECISION: asked whom she saw, Mara names no one |
| optional\_beats | Beats that may be rendered or omitted | list; OPTIONAL | L4 | As required beats | BT-007-07 Mrs. Dorran pours tea |
| beat\_order | Ordering constraints | list of pairs; OPTIONAL | L4 | Acyclic | BT-007-02 before BT-007-04 |

**G. Character states (one block per participant)**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| character | Who | handle; REQUIRED | L1 | Participant | CHR-001 |
| presence | When and where in the scene | interval and position; REQUIRED | L6 | Inside the window | Whole scene; head of the table |
| physical | Persistent physical state | list; REQUIRED | L6 | Equals model | Mara: unhurt; has not slept |
| possessions | Relevant items held | list; OPTIONAL | L8 | Conservation law | Mara: housekeeper's keys (not the study key) |
| emotional\_entry, emotional\_exit\_target | Volatile state at entry; intended state at exit | strings; REQUIRED for the POV | L6 overlay | Exit reachable through beats | Shaken but composed → resolved and guilty |
| goals\_in\_scene | What the character is trying to do | list; REQUIRED | L6 overlay | Anchored to goal records | Protect Jonah; keep her place |
| stance | Attitude toward each other participant | map; OPTIONAL | L6, relations | — | Toward Hale: wary deference |
| knowledge\_bounds | What the character may and may not display knowing, stated as behavior | list; REQUIRED for non-POV speakers | L9, L11 | Phrased positively; passes CC-2 | Hale treats the death as unexplained and asks only about movements and the locked study |
| known\_secrets | Secrets held that the reader may know at this position | list; OPTIONAL | L9 | MUST NOT contain a SUPPRESSED proposition | Mara: her sighting of Jonah (INF-006) |
| speech | Register and verbal habits | ref; OPTIONAL | Voice profiles | — | Hale: clipped and formal |

**H. Information (the epistemic mask, DEF-44)**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| known\_information | The POV's relevant knowledge | list {inf, statement, confidence, source}; REQUIRED | L9 | Subset of CIS(pov) (CC-9) | INF-006: Mara saw Jonah in the east corridor at 22:45 carrying a cloth-wrapped bundle; CERTAIN; WITNESSED |
| reader\_known | What the reader already holds | list {inf, delivered\_at, mode, wording\_ref}; REQUIRED | L10 | Subset of RIS(n−1) (CC-8) | Edmund found dead in his bed; 1.02.1; SHOWN |
| unknown\_information | Relevant things the POV does not know, stated without revealing them | list; REQUIRED | L9, L11 | Passes CC-2 | Mara does not know what the bundle held or why Jonah carried it |
| irony\_constraints | Reader-ahead items the POV must not act on | list; OPTIONAL | L10 | PV-3 | empty |
| suppressed\_information | Hidden facts active in the scene | public: opaque refs; sealed: propositions; REQUIRED | L11 | Public part carries no content | public SUP-1, SUP-2; sealed: INF-002, INF-004 |
| forbidden\_revelations | What the text must not state or imply | public: behavioral and lexical guards; sealed: propositions and leak indicators; REQUIRED | L2, L10 | Public guard text does not entail any sealed proposition | public: do not describe the bundle's contents, size, or shape, and let no one guess at it |
| permitted\_hints | Clues allowed, with bounded explicitness | list {inf, max\_explicitness 1–3, guidance}; OPTIONAL | L10 | Target is a REVEALABLE trace (PK-6) | INF-008 empty key hook; explicitness 2: Mara notices it and draws no conclusion |
| adjacent\_not\_delivered | Neighboring propositions not to deliver | list; OPTIONAL | L10 | RV-3 | Mara must not conclude that Jonah took the key |
| misdirection | False beliefs to induce | list; CONDITIONAL | L10 | Correction registered (RV-4) | empty |

**I. Emotion and pressure**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| scene\_tone\_target | Overall register | string; REQUIRED | L3 | — | Contained dread under household formality |
| tension\_shape | Coarse curve across beats | list; OPTIONAL | L3 | Beat refs exist | Rises to BT-007-04; settles at BT-007-06 |
| narrative\_pressure | Pressure vector before the scene, and target after | vectors; REQUIRED | L10 | Computed (§7.8) | Before (Q 4, D 0, T 2, S 1, I 0) |

**J. Constraints**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| continuity\_constraints | LOCKED facts the prose must respect | list {statement, source}; REQUIRED | L5–L8 | Each equals the model (CC-5) | The study has been locked since 22:40 and its key is not on the board |
| drafting\_constraints | Form | object; REQUIRED | L3, work settings | — | 2,000–2,800 words; past tense; third person; no flashback; no dream |
| invention\_policy | Class overrides for this scene | object; REQUIRED | L1, L3 | Overrides cite reasons | FREE: kitchen texture; CONSTRAINED: dialogue wording; LOCKED: names, times, who is present |
| terminology | Locked and forbidden terms | object; REQUIRED | L1 | — | Locked: "Inspector Hale", "York City Police"; forbidden: "Scotland Yard", "detective", "okay" |
| first\_contact | Entities new to the reader, shown by behavior before they are named (Unnamed-First Principle, §12.3) | list; CONDITIONAL | L10, editorial laws | Entity not yet in RIS | none (Hale was introduced at 1.03.1) |

**K. Outcomes**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| required\_outcomes | Deltas that must hold at scene end | list {kind WORLD, CHARACTER, or READER; delta; mode}; REQUIRED | L4, L10 | Reachable (CC-3); not forbidden (PK-1) | READER +INF-006 SHOWN; READER +INF-008 HINTED; Hale SUSPECTS Mara is holding something back |
| forbidden\_outcomes | Deltas that must not happen | list; REQUIRED | L2, L10 | Sealed content stays sealed | Mara must not learn what the bundle was |
| exit\_state | Expected state at window end | object; REQUIRED | L5, L6 | Equals the model at the window end | Hale leaves for the study at about 08:10; Jonah stays in the hall |
| hooks | Questions opened or setups planted | list; OPTIONAL | L10 | Payoff registered | Opens Q-03 (what was in the bundle?) |

**L. Validation**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| pre\_draft\_checks | Results of CC-1 to CC-10 | list; REQUIRED | L11 | All PASS | All PASS |
| leak\_probe\_results | Probe score per suppressed fact | list {sup, score, threshold}; CONDITIONAL (hidden threads present) | L11 | Score below threshold | SUP-1 0.08 (threshold 0.25); SUP-2 0.11 |
| autopsy\_targets | Specific checks for the draft | list; REQUIRED | L11 | Each maps to a rule | Mara names no one to Hale; the bundle is not described; the hook is shown empty |

**M. Traceability**

| Field | Purpose | Type; requirement | Source | Validation | Example |
| --- | --- | --- | --- | --- | --- |
| sources | Field path → records it came from | map; REQUIRED | All | Covers every non-empty field (PK-8) | continuity\_constraints\[0\] → EVT-0104, CAN-030 |
| exclusions\_ref | Pointer to excluded material with reason codes | ref; REQUIRED | L11 | Exists | RUN-X-0212#exclusions |

**N. Mechanics.** Scenes with magic, technology, or other world mechanics carry a fourteenth group: mechanics in play, regime, practitioner states, active effects, traces present, mechanic constraints, and forbidden mechanic revelations. Its fields and checks are defined with the World Mechanics Engine (§17.7).

### 8.3 Cross-field validation rules

| Rule | Statement |
| --- | --- |
| PK-1 | No proposition is both a required outcome and a forbidden revelation. |
| PK-2 | Every participant has a character-state block. |
| PK-3 | Every mandatory beat cites at least one event or a READER delta. |
| PK-4 | The public section contains no sealed proposition, by string match or paraphrase check. |
| PK-5 | `known_secrets` never contains a SUPPRESSED proposition; those appear only as manifestations. |
| PK-6 | `permitted_hints` targets REVEALABLE traces, never HIDDEN facts. |
| PK-7 | `naming_map` covers every entity named in public fields. |
| PK-8 | `sources` covers every non-empty field. |
| PK-9 | `packet_hash` and `public_hash` verify. |
| PK-10 | `model_version` equals the extraction run's model version. |

### 8.4 Example: PKT-007-r3 (abridged: hashes, character states, and the emotion block omitted)

```json
{
  "packet_uuid": "01920c3e-7a41-7c2b-9d1e-5f3a8b2c4d6e",
  "packet_handle": "PKT-007-r3",
  "schema_version": "0.1.0",
  "scene_ref": "SCN-007",
  "model_version": "canon@r12/truth@r47",
  "extraction_run": "RUN-X-0212",
  "status": "FROZEN",
  "flags": ["DEPENDENCY:SCN-006"],
  "public": {
    "position": {
      "narrative_position": "1.03.2",
      "story_time_range": {"start": "1893-10-15T07:40", "end": "1893-10-15T08:10", "precision": "QUARTER_HOUR"},
      "previous_scene": "SCN-006",
      "next_scene": "SCN-008",
      "story_time_gap": {"since_previous_scene": "PT0M"},
      "anachrony": "NONE",
      "narration_stance": {"tense": "past", "narrating_time": "retrospective-close"}
    },
    "setting": {
      "location": {"handle": "LOC-001c", "name": "servants' hall"},
      "setting_state": ["fire lit in the range", "grey daylight from the high windows", "key board on the east wall"],
      "objects_present": [{"object": "OBJ-004 key board", "state": "the study key's hook is empty"}],
      "perceptibles": ["kitchen sounds through the open door"]
    },
    "pov": {
      "character": "CHR-001",
      "mode": "CLOSE_THIRD",
      "permitted_interiority": ["CHR-001"],
      "naming_map": {"CHR-002": "Inspector Hale", "CHR-004": "Jonah", "CHR-006": "Mrs. Dorran"},
      "voice_profile_ref": "VOICE-MARA-v2"
    },
    "threads": {
      "active": [
        {"thread": "THR-01", "rank": "primary", "role": "FOREGROUND", "nodes": ["NOD-01-04"], "priority": 6.0},
        {"thread": "THR-04", "rank": "secondary", "role": "FOREGROUND", "nodes": ["NOD-04-02"], "priority": 5.0}
      ],
      "hidden": [
        {"sup_ref": "SUP-1", "manifestations": [{
          "actor": "CHR-004",
          "behavior": "answers in single words and does not meet Hale's eye",
          "intensity": 2,
          "permitted_explanation": "he says he slept badly",
          "forbidden_explanations": ["any mention of the study, the key, or anything he carried"]
        }]},
        {"sup_ref": "SUP-2", "manifestations": [{
          "actor": "CHR-004",
          "behavior": "once seems close to tears and turns to the window",
          "intensity": 1,
          "permitted_explanation": "the shock of the death",
          "forbidden_explanations": ["any personal tie to Lord Harrow beyond service"]
        }]}
      ]
    },
    "required_beats": [
      {"beat": "BT-007-01", "type": "EXCHANGE", "actors": ["CHR-002"], "outcome": "Hale asks the household to account for the night"},
      {"beat": "BT-007-02", "type": "PERCEPTION", "actors": ["CHR-001"], "outcome": "Mara notices the empty hook on the key board", "plants": "INF-008"},
      {"beat": "BT-007-03", "type": "REVELATION", "actors": ["CHR-001"], "outcome": "Mara recalls seeing Jonah in the east corridor with a bundle"},
      {"beat": "BT-007-04", "type": "DECISION", "actors": ["CHR-001"], "outcome": "Asked whom she saw, Mara names no one"},
      {"beat": "BT-007-05", "type": "EXCHANGE", "actors": ["CHR-002", "CHR-001"], "outcome": "Hale lets the answer stand; his manner shows he does not believe it"},
      {"beat": "BT-007-06", "type": "TRANSITION", "actors": ["CHR-002"], "outcome": "Hale asks to be shown the study and leaves the hall"}
    ],
    "information": {
      "known_information": [{"inf": "INF-006", "statement": "Mara saw Jonah in the east corridor at about 22:45 carrying a cloth-wrapped bundle", "confidence": "CERTAIN", "channel": "WITNESSED"}],
      "reader_known": [{"inf": "INF-009", "statement": "Edmund was found dead in his bed", "delivered_at": "1.02.1", "mode": "SHOWN"}],
      "unknown_information": ["Mara does not know what the bundle held or why Jonah carried it"],
      "suppressed_information": ["SUP-1", "SUP-2"],
      "forbidden_revelations": ["Do not describe the bundle's contents, size, or shape, and let no one guess at it"],
      "permitted_hints": [{"inf": "INF-008", "max_explicitness": 2, "guidance": "Mara notices the empty hook and draws no conclusion"}],
      "adjacent_not_delivered": ["Mara must not conclude that Jonah took the key"]
    },
    "constraints": {
      "continuity": [
        {"statement": "The study has been locked since 22:40; its key is not on the board", "sources": ["EVT-0104", "CAN-030"]},
        {"statement": "Hale walks with a cane", "sources": ["CHR-002"]},
        {"statement": "Hale is of the York City Police", "sources": ["CHR-002"]}
      ],
      "drafting": {"words": [2000, 2800], "tense": "past", "person": "third", "forbidden_devices": ["flashback", "dream"]},
      "invention_policy": {"FREE": ["kitchen texture"], "CONSTRAINED": ["dialogue wording"], "LOCKED": ["names", "times", "who is present"]},
      "terminology": {"locked": ["Inspector Hale", "York City Police"], "forbidden": ["Scotland Yard", "detective", "okay"]}
    },
    "outcomes": {
      "required": [
        {"kind": "READER", "delta": "+INF-006", "mode": "SHOWN"},
        {"kind": "READER", "delta": "+INF-008", "mode": "HINTED"},
        {"kind": "CHARACTER", "delta": "CHR-001 intends to protect Jonah"},
        {"kind": "CHARACTER", "delta": "CHR-002 suspects Mara is holding something back", "confidence": "SUSPECTED"}
      ],
      "exit_state": "Hale leaves for the study at about 08:10; Jonah remains in the hall",
      "hooks": ["Q-03"]
    }
  },
  "sealed": {
    "suppressed": {"SUP-1": "INF-002", "SUP-2": "INF-004"},
    "forbidden_propositions": ["INF-002", "INF-003", "INF-004", "INF-005"],
    "leak_indicators": {"INF-002": ["ledger", "account book", "book-shaped"], "INF-004": ["son", "his father", "resemblance"]}
  },
  "validation": {
    "pre_draft_checks": "ALL_PASS",
    "leak_probe_results": [{"sup": "SUP-1", "score": 0.08, "threshold": 0.25}, {"sup": "SUP-2", "score": 0.11, "threshold": 0.25}],
    "autopsy_targets": ["Mara names no one to Hale", "The bundle is not described", "The hook is shown empty"]
  },
  "sources_ref": "PKT-007-r3#sources",
  "exclusions_ref": "RUN-X-0212#exclusions"
}
```

### 8.5 Compiling the packet into a brief

The Packet Compiler (C11) renders the public section into a plain-language drafting brief for a specific drafter. The brief is the only thing the drafter sees.

1. **Order of sections:** the scene in one sentence; where and when; who is here and their state; what the POV knows; what the reader already knows; the beats to render, as outcomes; what must not happen; behaviors under hidden pressure; constraints; the expected ending state; the output contract.
2. **Language:** internal handles are replaced by names from `naming_map`. Rule codes and scores are omitted.
3. **Sealed content** never appears, except in INFORMED\_DRAFTING mode, where it appears in a separately marked section with a non-disclosure instruction.
4. **Output contract** (requested in the brief): the prose; an emergent-detail list (every concrete detail the drafter invented); a beat map (which passage renders which beat). The drafter's list and map are testimony, not evidence. Autopsy verifies both (§9.2).

## 9. Narrative Autopsy System

Autopsy reads accepted prose, extracts what the prose actually asserts, and checks each assertion against the packet and the model. It emits findings, a factorized confidence vector per draft, an RIS\_actual update, drift measurements, micro-fact proposals, and a root-cause attribution for every defect.

### 9.1 What is inspected

| Input | Why | Evidence grade required |
| --- | --- | --- |
| Draft text, in full | The object under test | CONTENT\_READ |
| Frozen packet, public and sealed | The contract the draft was held to | CONTENT\_READ |
| Model at the packet's version and at the current version | Ground truth, and drift since freezing | CONTENT\_READ of cited records |
| Prior accepted drafts in the retro-consistency scope and drift window | Cross-scene checks | CONTENT\_READ for BLOCKING findings; summaries or index rows (FOUND\_BY\_METADATA) only for candidate findings |
| RIS\_actual up to n−1 | Reader state before the scene | Computed |
| Drafter's emergent-detail list and beat map | Hints to verify | TESTIMONY\_ONLY |
| The L14 validation report | Avoid duplicate work; check its coverage claim | — |

**REQ-9.1.1 (the F5 rule, applied to autopsy).** Autopsy MUST NOT report a scene as checked if it saw only a summary, an index row, or an embedding match. Every finding carries the evidence label of its weakest cited evidence, and only findings with CONTENT\_READ evidence may be BLOCKING.

**REQ-9.1.2 (waivers).** A finding may be set to WAIVED\_BY\_OVERRIDE only if its severity is MAJOR, MINOR, or INFO, and only through a gate record that names the actor and the reason. A BLOCKING finding cannot be waived. It closes only as RESOLVED (its inputs changed) or DETECTOR\_ERROR (the detector was wrong). This keeps REQ-11.5.1 intact: waiving an open BLOCKING finding would otherwise lift the open-BLOCKING cap without any input changing.

### 9.2 Pipeline

1. **Segment** the draft into paragraphs, sentences, and dialogue turns, each with a stable span ID.
2. **Extract assertions** with an LLM under a structured output schema. Types: ENTITY\_MENTION, ATTRIBUTE, STATE (location, custody, lock), EVENT, TEMPORAL (clock time, duration, sequence), SPATIAL, KNOWLEDGE\_DISPLAY (a character says, thinks, or acts on a proposition), INTERIORITY, CLAIM, EMOTION\_DISPLAY, OBJECT\_REFERENCE, IMPLICATION (what a competent reader would infer, with a confidence).
3. **Verify spans.** Every assertion must carry an exact quotation of its span. A deterministic check confirms the quotation exists in the text. Assertions that fail are discarded and logged as AU-70, so hallucinated extractions never become findings.
4. **Link entities** to handles using the naming map and canon aliases. Unresolvable mentions are marked AMBIGUOUS.
5. **Normalize** assertions into propositions (subject, predicate, object, story-time).
6. **Align beats.** Check the drafter's beat map, then align every required beat to the spans that render it.
7. **Classify** each assertion: CONSISTENT, CONTRADICTS\_MODEL, CONTRADICTS\_PACKET, UNREGISTERED (a micro-fact if FREE; a violation if LOCKED), LEAK, INFO\_STATE\_VIOLATION, NARRATOR\_CLAIM (a registered lie or unreliable-narrator claim), or UNVERIFIABLE.
8. **Reconcile testimony.** Compare the drafter's emergent-detail list with the UNREGISTERED assertions actually found. Undeclared inventions and declared-but-absent items both count against the reconcile score.
9. **Run check suites and leak probes** (§9.3).
10. **Compare across scenes** for drift (§9.4) and retro-consistency (§9.5).
11. **Score** (§9.6).
12. **Attribute root causes** (§9.7) and **emit outputs** (§9.8).

### 9.3 Failure taxonomy and detection

| Code | Failure | Detection method | Default severity |
| --- | --- | --- | --- |
| **Continuity** |  |  |  |
| AU-01 | Assertion contradicts an ACCEPTED or CANON fact at the scene's story-time | Normalized assertion compared with a state query | BLOCKING if the detail is LOCKED; MAJOR otherwise |
| AU-02 | Assertion contradicts a packet continuity constraint or setting state | Direct comparison with packet fields | BLOCKING |
| AU-03 | Unregistered LOCKED detail (a new name, title, time, or person present) | Classification step 7 | MAJOR |
| AU-04 | Micro-fact (FREE detail first introduced here) | Classification step 7 | INFO; becomes a CANON-gate proposal |
| AU-05 | CONSTRAINED detail outside its bound | Bound check | MINOR or MAJOR |
| **Timeline corruption** |  |  |  |
| AU-10 | Stated or implied clock time outside the scene window | TEMPORAL assertion against story\_time\_range | BLOCKING |
| AU-11 | Sequence inversion: text orders events against story-time with no anachrony tag | Ordering of EVENT assertions | MAJOR |
| AU-12 | Duration contradiction: implied elapsed time overruns the window or the exit state | Sum of implied durations | MAJOR |
| AU-13 | Premature reference to an event not yet begun at the scene's time | Event start compared with scene time | BLOCKING |
| **Information state** |  |  |  |
| AU-20 | Character displays knowledge outside its CIS, or above its confidence | §6.13 check applied to each KNOWLEDGE\_DISPLAY | BLOCKING; MAJOR if only OVERCONFIDENT |
| AU-21 | Interiority rendered for a non-permitted character | INTERIORITY assertion against permitted\_interiority | MAJOR |
| AU-22 | POV perceives something outside its perception set | Perception rules | MAJOR |
| AU-23 | POV uses a name it does not know | naming\_map and CIS | MINOR |
| AU-24 | POV acts on reader-ahead knowledge | irony\_constraints | MAJOR |
| AU-25 | Text presumes reader knowledge not in RIS | IMPLICATION and reference analysis against RIS(n−1) | MAJOR |
| **Hidden-thread leakage** |  |  |  |
| AU-30 | Direct leak: a forbidden proposition is stated | Sealed propositions against normalized assertions | BLOCKING |
| AU-31 | Lexical leak: a leak-indicator term appears | Deterministic match on sealed indicators | MAJOR, routed to review |
| AU-32 | Inferential leak: an independent reader can now infer a forbidden proposition | Leak probe (below) | MAJOR above 0.25; BLOCKING above 0.50 |
| AU-33 | Behavioral leak: manifestation intensity exceeded, or a forbidden explanation given | Comparison with manifestation records | MAJOR |
| AU-34 | Over-delivery: a hint above its maximum explicitness, or an adjacent proposition delivered | Hint and adjacency checks | MAJOR |
| **Character state** |  |  |  |
| AU-40 | Persistent physical state contradicted or ignored (an injury, Hale's cane) | Assertions against character\_states | MAJOR |
| AU-41 | Character holds or uses an object it does not hold | Custody check | BLOCKING |
| AU-42 | A non-participant acts or speaks | Presence check | BLOCKING |
| AU-43 | Emotional exit target not reached, or an unexplained jump with no beat | LLM judgment | MINOR (HEU) |
| AU-44 | Fixed trait or voice inconsistent with canon or the voice profile | Trait comparison; voice classifier | MINOR |
| AU-45 | Action against every active goal with no DECISION beat | Goal records | MINOR (HEU) |
| **Beats and outcomes** |  |  |  |
| AU-50 | Mandatory beat missing | Beat alignment | BLOCKING |
| AU-51 | Required outcome not achieved | Outcome check against final state | BLOCKING |
| AU-52 | Forbidden outcome achieved | Outcome check | BLOCKING |
| AU-53 | Beat order violated | Alignment order | MAJOR |
| **Testimony and extraction** |  |  |  |
| AU-60 | Undeclared invention | UNREGISTERED assertions missing from the drafter's list | MINOR; lowers the reconcile score |
| AU-61 | Beat map claims a span that does not render the beat | Alignment | MINOR; lowers the reconcile score |
| AU-70 | Extraction quotation not found in the text | Span check | Discarded; lowers extraction confidence |

**Leak probe design (HYP; claim C6 in §15).**

1. The probe is an independent LLM reader: a different model or configuration from the drafter, never given sealed content.
2. It receives a summary of RIS\_actual(n−1) and the new scene text.
3. It answers a battery of questions for each sealed proposition, mixed with decoy propositions of the same type (other plausible culprits, other plausible contents of the bundle).
4. Leak score = the probe's probability for the true proposition after reading the scene, minus its probability before (from RIS(n−1) alone), with decoys used to detect a probe that simply guesses the genre-typical answer.
5. Thresholds (HEU): 0.25 is MAJOR; 0.50 is BLOCKING.
6. **Cumulative leakage.** The same probe runs on the whole accepted text at each reveal's prerequisite checkpoint, catching leaks spread thinly across many scenes.

### 9.4 Continuity drift

Drift is measured by five indices, tracked as time series over narrative position. Thresholds are author-set; exceeding one opens a review task (HEU).

| Index | Measures | Method |
| --- | --- | --- |
| DI-1 Attribute drift | Variant descriptions of one attribute across scenes (Mara's eyes grey, then brown) | Entity-attribute history table built from every autopsy; count of non-equivalent values per 10 scenes |
| DI-2 Unregistered accumulation | Micro-facts awaiting a CANON-gate decision, plus REJECT\_MICRO\_FACT spans kept as non-binding | Count per 10,000 words |
| DI-3 Time slippage | Cumulative difference between durations implied by the text and model windows | Sum over scenes of implied minus modeled duration |
| DI-4 RIS divergence | Stakes-weighted symmetric difference between RIS\_actual and RIS\_plan, split into leak and under-delivery | Per position, from L10 |
| DI-5 Description divergence | Semantic distance between successive descriptions of one place or object (reader-continuity anchors) | Embedding distance with a human-calibrated threshold |

### 9.5 Retro-consistency and reread checks

When a reveal scene is accepted, autopsy re-runs AU-01 against every accepted scene in the reveal's retro-consistency scope, using the revealed proposition as ground truth (REQ-6.9.1). The reread probe (§6.9) then judges the reveal as leaked, fair, or unsupported. Both results go to the INTEGRATION gate; neither changes text automatically.

### 9.6 Scoring: the draft confidence vector

Scoring uses the factorized confidence engine of the control plane (§11.5). Every score is a weighted sum of named factors, each with evidence references, minus conflict penalties, clamped to \[0, 1\]:

```latex
\mathrm{score} = \min\!\Big(1,\ \max\!\big(0,\ \textstyle\sum_i w_i \cdot \min(r_i, c_i) - \sum_j p_j\big)\Big), \qquad \textstyle\sum_i w_i = 1
```

Here r\_i is a factor's raw score, c\_i is the lowest evidence ceiling among the factor's cited sources, and p\_j are conflict penalties.

**Evidence ceilings and claim ladder (adopted from the corpus adapter).**

| Evidence or claim status | Ceiling or raw value | NSRES use |
| --- | --- | --- |
| CONTENT\_CONFIRMED | ceiling 1.00 | Deterministic check results on fully read text and records; the raw score is the measured compliance |
| OBJECT\_ID\_CONFIRMED | ceiling 0.90 | Entity linked by handle with no ambiguity |
| METADATA\_STRONG | ceiling 0.85 | Prior scenes checked through structured indexes only |
| METADATA\_WEAK | ceiling 0.60 | Prior scenes checked through summaries only; never cited as read |
| AMBIGUOUS | ceiling 0.40 | Unresolved entity link; freezes CANON-gate actions on the affected record |
| SUPPORTED | raw 0.90 | An LLM judgment (beat alignment, interiority classification) over a verified span with a confirmed link |
| TESTIMONY\_ONLY | raw 0.55 | The drafter's emergent-detail list and beat map |
| INFERRED | raw 0.50 | IMPLICATION assertions |
| CONFLICTED | raw 0.30, plus a conflict penalty | Two detectors disagree (a span check passes but the leak probe flags it) |

**REQ-9.6.1.** Claim-ladder values (SUPPORTED, TESTIMONY\_ONLY, INFERRED, CONFLICTED) cap only factors whose evidence is a judgment, testimony, or inference. Deterministic checks on fully read text report their measured compliance with ceiling 1.00. Without this rule every factor would stop at 0.90, and no draft could reach READY (found while computing Appendix A).

**Score types for a draft.** Default weights (HEU, configurable per work):

| Score type | Factors (weight) | Hard cap? |
| --- | --- | --- |
| Continuity Integrity | model\_consistency 0.35; packet\_constraint\_compliance 0.30; timeline\_integrity 0.20; character\_state\_integrity 0.15 | No |
| Information-State Integrity | character\_knowledge 0.35; pov\_discipline 0.25; perception 0.15; irony\_and\_comprehension 0.15; naming 0.10 | No |
| Leak Safety | direct\_leak\_absence 0.35; inferential\_probe\_margin 0.30; behavioral\_bound\_compliance 0.20; lexical\_absence 0.15 | Yes (the NSRES counterpart of Safety) |
| Plan Alignment | mandatory\_beats 0.35; required\_outcomes 0.30; forbidden\_outcomes\_absent 0.20; beat\_order 0.10; length\_and\_form 0.05 | No |
| Reconcile | declared\_inventions\_match 0.30; beat\_map\_accuracy 0.30; no\_undeclared\_locked\_inventions 0.25; no\_unreported\_changes 0.15 | Yes |
| Identity | links\_confirmed 0.50; ambiguity\_inverse 0.30; alias\_rule\_compliance 0.20 | Yes |
| Source Grounding | findings\_at\_content\_read 0.50; packet\_source\_coverage 0.30; retro\_scope\_read\_completeness 0.20 | Yes |
| Critic | Adversarial critic module's structural assessment | No (advisory only) |

Finding penalties on the affected factor's raw score (HEU): BLOCKING −0.20, MAJOR −0.08, MINOR −0.02. Each detector conflict adds a −0.05 conflict penalty and routes the finding to a human.

**Acceptance readiness (aggregate).**

```latex
R = 0.30\,C_{cont} + 0.25\,C_{info} + 0.20\,C_{plan} + 0.15\,C_{leak} + 0.10\,C_{rec}
```

Hard caps then apply, regardless of how strong the other factors are:

| Condition | Cap on R | Resulting band |
| --- | --- | --- |
| Leak Safety < 0.95 | ≤ 0.84 | INSUFFICIENT at best |
| Reconcile < 0.95 | ≤ 0.84 | INSUFFICIENT at best |
| Any open BLOCKING finding | ≤ 0.69 | UNSTABLE at best |
| Identity < 0.85 | ≤ 0.70 | INSUFFICIENT at best |
| Source Grounding < 0.85 | ≤ 0.80 | INSUFFICIENT at best |

**Bands and permitted actions** (the corpus threshold bands):

| Band | Range | Permitted next actions |
| --- | --- | --- |
| READY | 0.95–1.00 | Eligible for the INTEGRATION gate (acceptance) and, per segment, the SHIP gate |
| PROVISIONAL | 0.85–0.949 | Fetch more evidence (read the retro scope in full), run a critic pass, then rescore |
| INSUFFICIENT | 0.70–0.849 | Acceptance blocked; revise the draft or fix the packet |
| UNSTABLE | 0.40–0.699 | Regenerate, route to human review, or slush the draft |
| FAILED | 0.00–0.399 | Invalid; may not be used as the basis for any decision |

L14 computes a first vector before acceptance, from deterministic checks and bounded extraction. L15 recomputes it with full evidence. If the L15 score falls below READY for an accepted scene, the scene moves to REVISION\_REQUIRED through the INTEGRATION gate.

### 9.7 Root-cause attribution

Every finding is assigned one cause, so fixes go to the right layer.

| Cause | Test | Fix goes to |
| --- | --- | --- |
| MODEL\_GAP | The needed fact was UNDETERMINED in the model | L1 or L5 (author adds the fact) |
| MODEL\_ERROR | The model is wrong and the prose is right | §4.18 policy (PROSE\_WINS candidate) |
| PACKET\_ERROR | The model had the fact; the packet omitted or misclassified it | L11 rules (extraction defect) |
| BRIEF\_ERROR | The packet was right; the compiled brief worded it misleadingly | C11 templates |
| DRAFTER\_VIOLATION | The brief was clear; the drafter did not follow it | Regenerate; drafter statistics |
| DETECTOR\_ERROR | The finding is a false positive on human review | Detector calibration |

Attribution runs mechanically for the first four causes: re-run the failing check against the packet, then the brief, then the model, and stop at the first layer where the needed information is missing. DRAFTER\_VIOLATION and DETECTOR\_ERROR are confirmed by a human. Aggregated cause counts per drafter, extraction rule, and template are the main input for improving the system.

### 9.8 Outputs

| Output | Format | Destination | Gate |
| --- | --- | --- | --- |
| Findings | FND records with span, rule, severity, evidence label, cause | Author; C15 | INTEGRATION gate if a scene reopens |
| Draft confidence vector | `CONFIDENCE_VECTOR.json` linked to the draft and packet | C17; C15 | Read by every later gate |
| RIS\_actual delta | Delivery records with mode and confidence | C7 | None for SUPPORTED entries; IMPLIED entries below SUPPORTED are marked tentative |
| Micro-fact proposals | PROPOSAL records with provenance DRAFT\_EMERGENT | C15 | CANON gate (ACCEPT\_AND\_REGISTER or REJECT\_MICRO\_FACT) |
| Model correction proposals | PROPOSAL records | C15 | PROPOSAL gate, then CANON gate |
| Drift indices | Time series | Planner; author dashboard | None |
| Root-cause statistics | Aggregates | C16 rule review | None |

## 10. Software implementation

The reference implementation stores reality as an append-only, bitemporal record log, projects it into a property graph and interval indexes, and runs every engine as a pure function of a pinned model version. LLMs are reachable only through a gateway that enforces typed input and output contracts and can create nothing above PROPOSAL status.

### 10.1 Components

Seventeen components were defined in §5.1. The control plane adds two more.

| ID | Component | Deterministic? | State | Notes |
| --- | --- | --- | --- | --- |
| C1–C10, C13, C16, C17 | Registries, engines, stores, validator | Yes | Versioned | Pure functions of (inputs, model version) |
| C11 | Packet Compiler | Yes (templates) | Stateless | Templates versioned and hashed |
| C12 | Generation Gateway | No (calls LLMs) | Call log | Only path to any LLM (§10.12) |
| C14 | Autopsy Engine | Mixed | Run records | LLM extraction plus deterministic checks |
| C15 | Gate Console | Human | Gate records | Typed gates (§0.7) |
| C18 | Context Fetch Service | Yes | Fetch logs and bundles | Progressive fetch tiers (§10.4) |
| C19 | Confidence Engine | Yes | Confidence vectors | Factorized scoring, caps, bands (§11.5) |

### 10.2 Data models

Core record types, in TypeScript notation. Every record extends `BaseRecord`.

```typescript
type Status = 'PROPOSAL' | 'ACCEPTED' | 'CANON' | 'REJECTED' | 'SLUSHED' | 'DEPRECATED';
type Provenance = 'AUTHOR' | 'LIFTED_FROM_BEAT' | 'ENGINE_BRIDGE' | 'AI_PROPOSAL' | 'IMPORTED' | 'DRAFT_EMERGENT';
type Confidence = 'CERTAIN' | 'BELIEVED' | 'SUSPECTED';
type Channel = 'WITNESSED' | 'TOLD' | 'READ' | 'INFERRED' | 'RUMOR' | 'ASSUMED' | 'DETECTED';   // DETECTED: §17.5, when world mechanics are in play

interface BaseRecord {
  uuid: string;            // UUIDv7, storage key
  handle: string;          // e.g. 'EVT-0104'
  rev: number;             // revision, increments per change
  status: Status;
  tier?: 'PUBLISHED';
  provenance: Provenance;
  plane: 'reality' | 'telling' | 'rendering' | 'control';
  tx: { from: string; to: string | null };   // revision-time validity
  gate?: GateRecordRef;
  notes?: string;
}

interface Entity extends BaseRecord {
  kind: 'CHARACTER' | 'LOCATION' | 'OBJECT' | 'GROUP';
  canonicalName: string;
  aliases: string[];
  fixedTraits: Record<string, string>;
  persistentDefaults: Record<string, unknown>;
  significance?: 'ORDINARY' | 'CLUE' | 'PLOT_OBJECT';   // objects
}

interface StoryTime {
  start: { lo: string; hi: string };      // feasible window for the start point
  end: { lo: string; hi: string };
  precision: 'MINUTE' | 'QUARTER_HOUR' | 'HOUR' | 'PART_OF_DAY' | 'DAY' | 'WEEK' | 'MONTH' | 'SEASON' | 'YEAR';
}

interface TemporalConstraint {
  kind: 'METRIC' | 'ALLEN' | 'ANCHOR';
  from: string; to: string;               // event handles or anchor handle
  bounds?: [number, number];              // minutes, METRIC
  relations?: string[];                   // ALLEN; more than one = explicit disjunction
}

type Effect =
  | { op: 'SET'; target: string; attr: string; value: unknown; at: 'START' | 'END' | { offsetMin: number } }
  | { op: 'TRANSFER'; object: string; from: string; to: string }
  | { op: 'GRANT'; holder: string; prop: string; channel: Channel; confidence: Confidence; premises?: string[] }
  | { op: 'CLAIM'; speaker: string; prop: string; truth: boolean; hearers: string[] }
  | { op: 'CREATE' | 'DESTROY'; target: string };

interface Event extends BaseRecord {
  type: string;
  label: string;
  time: StoryTime;
  constraints: TemporalConstraint[];
  location: string;
  participants: { entity: string; role: 'AGENT' | 'PATIENT' | 'WITNESS' | 'PRESENT' | 'REMOTE' }[];
  preconditions: string[];                // predicate expressions (§10.9)
  effects: Effect[];
  visibility: 'REVEALABLE' | { hiddenUntil: string } | 'PERMANENT_MYSTERY';
  renderStatus: 'RENDERED' | 'DEFERRED' | 'IMPLIED' | 'CAUSAL_UNRENDERED' | 'AMBIENT';
  notNoticedBy?: string[];
}

interface Fact extends BaseRecord {
  subject: string; predicate: string; object: string | number | boolean;
  qualifiers?: Record<string, string>;
  valid: { from: string | null; to: string | null };
  truth: 'TRUE' | 'FALSE' | 'UNDETERMINED' | 'PERMANENTLY_UNDETERMINED';
  createdBy?: string;                     // event handle
  secret?: { holders: string[]; concealedFrom: string[]; strategy: string; reveal?: string };
}

interface KnowledgeGrant extends BaseRecord {
  holder: string; prop: string; time: string;
  channel: Channel; confidence: Confidence; sourceEvent: string;
  sourceEntity?: string; premises?: string[]; polarity: 1 | -1;
}

interface CausalEdge extends BaseRecord {
  from: string; to: string;
  type: 'CAUSES' | 'ENABLES' | 'MOTIVATES' | 'PREVENTS' | 'INFORMS';
  justification: string;
  requiredState?: string;
}

interface Thread extends BaseRecord {
  name: string;
  rank: 'primary' | 'secondary' | 'tertiary';
  dramaticQuestion: string;
  visibilitySchedule: { fromNT: string; visibility: 'VISIBLE' | 'HIDDEN'; reveal?: string }[];
  nodes: { event: string; role: string; order: number }[];
}

interface Scene extends BaseRecord {
  nt: string; window: StoryTime; location: string;
  pov: { character: string; mode: string };
  participants: string[]; rendersNodes: string[];
  purpose: string; plannedDelta: unknown; lengthTarget: [number, number];
  pipelineState: string;                  // §5.4 scene pipeline
}

interface Beat extends BaseRecord {
  scene: string; order: number;
  type: 'ACTION' | 'EXCHANGE' | 'PERCEPTION' | 'REVELATION' | 'DECISION' | 'REVERSAL' | 'INTERIOR' | 'TRANSITION' | 'PLANT' | 'PAYOFF' | 'SUSTAIN';
  actors: string[]; outcome: string; events: string[]; mandatory: boolean;
}

interface Finding extends BaseRecord {
  rule: string;                           // e.g. 'AU-20'
  severity: 'BLOCKING' | 'MAJOR' | 'MINOR' | 'INFO';
  spans: { draft: string; start: number; end: number; quote: string }[];
  records: string[];
  evidence: 'CONTENT_READ' | 'FOUND_BY_SNIPPET' | 'FOUND_BY_METADATA' | 'CLAIM_INFERRED';
  detectionConfidence: number;
  cause?: 'MODEL_GAP' | 'MODEL_ERROR' | 'PACKET_ERROR' | 'BRIEF_ERROR' | 'DRAFTER_VIOLATION' | 'DETECTOR_ERROR';
  repairs: string[];
  status: 'OPEN' | 'RESOLVED' | 'WAIVED_BY_OVERRIDE' | 'DETECTOR_ERROR';   // matches B.4
}

interface ConfidenceVector extends BaseRecord {
  subject: string;                        // packet, draft, record, or segment
  scores: { type: string; factors: { name: string; weight: number; raw: number; ceiling: number; evidence: string[]; reason: string }[];
            penalties: { reason: string; value: number }[]; value: number }[];
  caps: { condition: string; cap: number; applied: boolean }[];
  aggregate: number;
  band: 'READY' | 'PROVISIONAL' | 'INSUFFICIENT' | 'UNSTABLE' | 'FAILED';
}
```

The packet schema is §8; drafts, reveal records, gate records, and resolution records follow the same `BaseRecord` pattern.

### 10.3 Relationships

| From | Relation | To | Cardinality | Notes |
| --- | --- | --- | --- | --- |
| Event | PARTICIPATES\_IN (with role) | Entity | many to many | Role on the edge |
| Event | OCCURS\_AT | Location | many to one | Sub-location optional |
| Event | HAS\_EFFECT | Effect | one to many | Embedded |
| Event | causal edge (5 types) | Event | many to many | Must form a DAG |
| Event | NODE\_OF (with role) | Thread | many to many | Convergence when more than one |
| KnowledgeGrant | GRANTS | Fact or Claim | many to one | Holder, channel, confidence on the grant |
| Beat | BINDS | Event | many to many | Zero events = reader-only beat |
| Scene | RENDERS (with mode) | Event | many to many | The telling map |
| Reveal | REVEALS | Fact | one to many | With prerequisites |
| Packet | CITES | Any record | many to many | The sources map |
| Draft | RENDERS\_PACKET | Packet | many to one | Packet hash pinned |
| Finding | ABOUT | Span, Record | many to many | Evidence links |
| Location | ADJACENT\_TO (travel, perceptibility) | Location | many to many | Directional; per mode |

### 10.4 Storage architecture

| Store | Holds | Authority | Technology options |
| --- | --- | --- | --- |
| Record log | Every revision of every record | Authoritative | Append-only relational tables with bitemporal columns, or an event-sourcing store |
| Projection stores | Property graph; interval indexes; CIS and RIS tables | Derived; rebuildable from the log | Graph tables or a property-graph database; interval trees in memory, persisted per version |
| Artifact store | Packets, drafts, reports, bundles | Authoritative for artifacts | Content-addressed blob storage (key = SHA-256) |
| Vector index | Embeddings of draft spans and canon descriptions | Non-authoritative; retrieval aid only | Any vector index; results are at most METADATA\_WEAK evidence until read |
| Audit log | Gate records, RES records, transitions, LLM call logs | Authoritative; immutable | Append-only, hash-chained |
| Context bundles | Fetch outputs (C18) | Evidence records | `CONTEXT_BUNDLE.md` and `.json`, `SOURCE_POINTERS.json`, `FETCH_LOG.md`, `CONFIDENCE_VECTOR.json`, `UNRESOLVED_CONTEXT_GAPS.md` |

**Context Fetch Service (C18).** Reads that leave the database (manuscript files in path C, prior drafts for autopsy, external research) go through progressive tiers. Each tier upgrades the evidence label it can support.

| Tier | Action | Highest evidence label |
| --- | --- | --- |
| 0 | Index, tree, or path scan | FOUND\_BY\_METADATA |
| 1 | Metadata probe | FOUND\_BY\_METADATA |
| 2 | Content signature or export metadata | FOUND\_BY\_METADATA (METADATA\_STRONG) |
| 3 | Full text extraction into the active run | CONTENT\_READ |
| 4 | Deep extraction for conflicts, duplicates, or human review | CONTENT\_READ |

The cursor (the task's scope and required context) decides which tiers a task needs; the fetch service executes them and writes the bundle.

### 10.5 Bitemporal model

Every record revision is one row with two time dimensions: story-time validity (when it is true in the fiction) and transaction time (which model revisions contain it). Two queries follow directly:

```sql
-- What was Jonah's location at 22:45 on 14 Oct, according to model revision 47?
SELECT value FROM attribute_state
WHERE entity = 'CHR-004' AND attr = 'location'
  AND st_from <= '1893-10-14T22:45' AND (st_to IS NULL OR st_to > '1893-10-14T22:45')
  AND tx_from <= 47 AND (tx_to IS NULL OR tx_to > 47);

-- What changed about OBJ-001 between revisions 40 and 47?
SELECT * FROM record_revisions
WHERE handle = 'OBJ-001' AND tx_from > 40 AND tx_from <= 47;
```

### 10.6 Indexes

| Index | Key | Serves |
| --- | --- | --- |
| Entity-time interval tree | (entity, interval) | Presence; state at t; ubiquity checks |
| Location-time | (location, interval) | Occupancy; perceptibility |
| Object custody | (object, interval) | Custody at t; conservation checks |
| Proposition-holder | (proposition, holder, time) | CIS(c, t) |
| Reachability | (proposition, holder, time) | Knowledge-acquisition checks (§6.13) |
| Causal adjacency | (event) → in-edges and out-edges | DAG traversal; cycle detection; hidden causality |
| Thread-node | (thread) → ordered nodes | Thread views; priority |
| Narrative position | (NT) → deliveries, scenes | RIS(n); pressure |
| Reverse reference | (record) → dependents | Impact sets (§4.17) |
| Span index | (draft, span) → assertions → records | Traceability from text to model |
| Embeddings | span vector | Retrieval only |

### 10.7 Graph representation

| Node label | Represents |
| --- | --- |
| Character, Location, Object, Group | Entities |
| Event | L5 events |
| Fact, Claim | Propositions |
| Thread, Node | Threads and memberships |
| Scene, Beat, Reveal | Telling plan |
| Packet, Draft, Finding, ConfidenceVector | Artifacts and results |

Edge types are the relations of §10.3. Properties carry roles, channels, confidences, modes, and story-time intervals. The causal subgraph (Event nodes and causal edges only) is the Causal DAG (DEF-46). A cycle check runs on every insert into it.

### 10.8 Timeline representation

1. Each event stores its start and end as feasible windows \[lo, hi\], not points (lazy commitment, §6.2).
2. The STN is a sparse distance graph over time points, solved per model version and cached. Incremental updates use incremental all-pairs shortest paths or directional path consistency on the impact set.
3. Allen relations are stored as constraint records. Single relations compile into STN edges. Explicit disjunctions are branched with a cap (§6.2).
4. Timetables (rail, ferry) are stored as earliest-arrival functions per route (§6.12).
5. Projections (presence, custody, attribute state) are interval lists per entity, rebuilt for the impact set only.

### 10.9 Event representation: effect and precondition language

```ebnf
effect        = set | transfer | grant | claim | create | destroy ;
set           = "set(" ref "." attr "," value ["," timing] ")" ;
transfer      = "transfer(" object "," holder "," holder ")" ;
grant         = "grant(" holder "," prop "," channel "," confidence ["," premises] ")" ;
claim         = "claim(" speaker "," prop "," truth "," hearers ")" ;
precondition  = predicate | "not(" precondition ")" | precondition ("and" | "or") precondition ;
predicate     = "at(" entity "," location ")" | "holds(" entity "," object ")"
              | "knows(" entity "," prop ["," confidence] ")" | "alive(" entity ")"
              | "state(" ref "." attr "==" value ")" | "after(" event ")" | "locked(" location ")" ;
```

Example, EVT-0104 (Jonah removes the ledger and locks the study):

```text
preconditions: at(CHR-004, LOC-001a) and holds(CHR-004, OBJ-002) and state(OBJ-001.location == LOC-001a)
effects:       transfer(OBJ-001, LOC-001a, CHR-004)
               set(LOC-001a.lock, LOCKED, END)
```

### 10.10 Thread representation

A thread stores its rank, dramatic question, ordered nodes, and a visibility schedule: a list of (narrative position, VISIBLE or HIDDEN, reveal record). Rank and visibility are independent fields (§2.7). Rank changes are revisions of the thread record and pass the STRUCTURE gate.

### 10.11 Engines

**Validation rule engine.** Rules are declarative, stored in the Rule Registry (C16) with ID, layer, severity, query, message template, and repair hints. A Datalog-style language suits the checks, because most are joins over intervals. Example, RC-09 (ubiquity):

```prolog
violation('RC-09', C, L1, L2, I1, I2) :-
    presence(C, L1, I1), presence(C, L2, I2),
    L1 \= L2, overlaps(I1, I2),
    \+ remote(C, I1), \+ remote(C, I2).
```

**Reconciliation engine.**

```text
function reconcile(version, changes, mode):
    scope  = (mode == FULL) ? everything : impactSet(changes)
    records = acceptedAndCanon(version) + changes      // PROPOSAL handled by dryRun()
    for i in 1..K:
        stn = buildNetwork(records, scope)
        if negativeCycle(stn): return INCONSISTENT(RC-01)
        windows = solve(stn)
        added = tightenTravel(windows) + tightenKnowledge(windows)
        projections = project(records, windows, scope)    // L6–L9
        reader = readerChecks(projections, tellingPlan)    // L10
        findings = ruleSuite(projections, reader)
        if added is empty: break
    if i == K: findings += RC-17
    return (blocking(findings) ? INCONSISTENT : CONSISTENT, findings, windows)
```

**Packet generator** follows §7.2 steps 1 to 18 as a fixed pipeline. Each step writes its decisions to the extraction record before the next step runs, so a failure leaves a complete trace.

**Packet compiler** renders the public section through a versioned template per drafter family (§8.5).

### 10.12 LLM interfaces

Every LLM call goes through the Generation Gateway (C12). No LLM has write access to any store: its outputs become PROPOSAL records, findings, or draft text, and nothing else (DEF-47).

| Role | Input contract | Output contract | Settings | Validation |
| --- | --- | --- | --- | --- |
| DRAFTER | Compiled brief | Prose; emergent-detail list; beat map | Per work; may be creative | L14, L15 |
| ASSERTION\_EXTRACTOR | Draft text; naming map; assertion schema | Assertions with exact span quotations | Deterministic as far as the provider allows | Span check (AU-70) |
| ENTITY\_LINKER (fallback) | Mention, context, candidate handles | Handle or AMBIGUOUS, with reason | Deterministic | Must choose from candidates |
| LEAK\_PROBE | RIS summary; scene text; question battery | Probabilities per proposition and decoy | Independent of DRAFTER | Calibration against decoys |
| BRIDGE\_PROPOSER | Failed precondition; window; nearby events | Candidate events in the event schema | Moderate | Dry-run reconciliation |
| DECOMPOSER | L2 segment or L3 scene | Candidate scenes or beats in schema | Moderate | Planner rules (L3, L4) |
| MANIFESTATION\_WRITER | Suppressed fact; actor goals; concealment strategy | Behavioral manifestations | Moderate | SU-3, SU-4; pre-draft leak probe |
| SUMMARIZER | Background material | Summary tagged AI-origin | Deterministic | CC-2, CC-7 |
| CRITIC | Draft or proposal; critic rubric | Structured critique | Independent of the author model | Advisory only |

Gateway rules:

1. **Schema-enforced output.** Every non-drafter output is validated against a JSON schema. Invalid output is retried at most three times with the validation error attached, then fails.
2. **Versioned prompts.** Every template has an ID and hash. The call log records template hash, input hash, model ID, settings, and output.
3. **Independence.** LEAK\_PROBE and CRITIC MUST NOT run on the same model and configuration as the DRAFTER whose output they judge.
4. **Model-agnostic contracts.** Roles are defined by contracts, not by provider. Swapping models changes only the gateway configuration.
5. **No sealed content** reaches a DRAFTER unless INFORMED\_DRAFTING is set for that packet.

### 10.13 API surface

| Operation | Effect | Gate |
| --- | --- | --- |
| propose(record) | Creates a PROPOSAL | — |
| decide(gate, record, outcome) | Applies a gate outcome | The named gate |
| reconcile(version, mode) | Runs reconciliation | — |
| query.state(entity, attr, t, version) | State at a story-time | — |
| query.cis(holder, t, version) | Character knowledge | — |
| query.ris(nt, track) | Reader knowledge | — |
| query.impact(record) | Impact set | — |
| extract(scene, version) | Packet candidate | — |
| freeze(packet) | FROZEN | STRUCTURE |
| draft(packet, drafter) | Draft record | — |
| validate(draft) | L14 report and vector | — |
| accept(draft) | ACCEPTED | INTEGRATION |
| autopsy(draft or range) | L15 outputs | — |
| release(segment) | PUBLISHED tier | SHIP |

### 10.14 Performance and scale

- Reconciliation is incremental after the first full run; impact sets bound the work.
- Full STN solving is cubic in time points. A novel-length model is expected to hold thousands of events (an estimate, not a measurement), which full solving handles on commodity hardware; incremental solving keeps interactive edits fast.
- Projections are cached per model version and invalidated by impact set.
- LLM calls dominate cost: one drafter call, one extraction pass, and probe calls per suppressed fact per scene.

### 10.15 Integrity and confidentiality

- Packets, drafts, and bundles are content-addressed; a hash mismatch blocks use.
- The audit log is hash-chained, so gate and resolution history cannot be silently edited.
- Each gate has its own permission. A collaborator may hold STRUCTURE but not CANON authority.
- Manuscript text sent to external LLM providers leaves the system. The gateway records which provider received which content, and works may restrict providers by policy.

## 11. Automation, human control, and the confidence control plane

Humans hold every decision that sets ACCEPTED, CANON, or PUBLISHED status. AI supplies high-volume proposals, extraction, drafting, and probing. Deterministic engines do everything that can be computed. A factorized confidence score decides which next actions are available at all.

### 11.1 Responsibility matrix

| Task | Human | AI (thrust) | Deterministic engine | Gate |
| --- | --- | --- | --- | --- |
| Canon authoring | Writes and decides | Extracts candidates from notes and manuscripts | Rule, collision, and metric checks | PROPOSAL, then CANON |
| Premise, dramatic question, thread ranks | Decides | May suggest | Structural checks (L2) | STRUCTURE |
| Reveal plan | Decides | May flag risks | Prerequisite and retro-scope checks | STRUCTURE |
| Scene and beat plans | Decides | Proposes decompositions | Planner checks (L3, L4) | STRUCTURE |
| Truth Timeline events | Authors | Lifts events from beats; proposes bridge events | Reconciliation | PROPOSAL, then CANON |
| Contradiction resolution | Chooses | Proposes repairs | Generates candidates; dry-runs; scores | INTEGRATION (CANON if canon changes) |
| Extraction | — | Words manifestations; summarizes background | The whole §7 pipeline | STRUCTURE (freeze) |
| Drafting | Optional (human drafters) | Drafts | Compiles the brief | — |
| Validation | Reviews low-confidence findings | Assertion extraction; beat alignment | Deterministic suites | — |
| Acceptance | Decides | — | Acceptance readiness vector | INTEGRATION |
| Autopsy | Confirms causes | Extraction; probes; critic | Checks; scoring; drift | — |
| Micro-facts | Decides | — | Capture and classification | CANON |
| Release | Decides | — | Segment readiness | SHIP |
| Aesthetic judgment (voice, taste, whether a scene works) | Sole authority | Critic, advisory only | None | — |

### 11.2 What remains human-controlled

**REQ-11.2.1.** The following MUST remain human decisions at every automation tier:

1. Locking any record as CANON, including micro-facts and RETCONs.
2. The reveal plan, thread ranks, and the scene plan.
3. Every contradiction resolution that changes an ACCEPTED or CANON record.
4. Draft acceptance into the manuscript.
5. Release (SHIP).
6. Aesthetic judgment.
7. The control plane's own configuration: rule severities, score weights, hard caps, band thresholds, and leak-probe thresholds. These are versioned records, and every confidence vector names the configuration version it used.

### 11.3 Hallucination risk map

Every point where LLM output enters the system has a named risk, a mitigation, and a mandatory validation.

| Entry point | What can be hallucinated | Consequence if missed | Mitigation | Mandatory validation |
| --- | --- | --- | --- | --- |
| Canon extraction from notes | Facts or attributes not in the notes | False canon | PROPOSAL status; a source quotation required per record | Span check against the source; PROPOSAL and CANON gates |
| Lifting beats into events | Effects or participants not in the beat | False state | LIFTED provenance; author review | PROPOSAL gate; reconciliation |
| Bridge proposals | Plausible but unwanted events | Story drift | Never auto-accepted; dry-run results shown | PROPOSAL gate |
| Decomposition | Scenes or beats that do not serve the plan | Structural drift | Planner checks | STRUCTURE gate |
| Manifestation wording | Behavior that leaks the secret | Leaks | Behavioral wording rules (SU-4) | Pre-draft leak probe (CC-7) |
| Background summaries | Invented background | False packet content | AI-origin tag; budget limited to background | CC-2, CC-7 |
| Drafting | Invented facts, leaks, POV breaks, omitted beats | Defects in text | Invention policy; brief discipline | L14 and L15 |
| Drafter testimony | False or incomplete declarations | Missed inventions | Ceiling TESTIMONY\_ONLY (0.55) | Reconcile score |
| Assertion extraction | Missed or invented assertions | False pass or false fail | Exact span quotations | Span check (AU-70); low-confidence findings to a human; periodic human audits of samples |
| Entity linking | Wrong merge of two entities | Misattributed facts | Choose only among candidates; AMBIGUOUS allowed | Identity cap |
| Leak probe | False positives or negatives | Wrong leak verdicts | Decoys; calibration | Thresholds advisory below BLOCKING; human review |
| Critic | Confident but wrong critique | Bad revisions | Advisory only | None; never gates |
| Any reader of prior text | Claiming a scene was checked when only its summary was seen | False coverage | Evidence labels on every finding | REQ-9.1.1 (the F5 rule) |

**REQ-11.3.1.** An LLM's self-reported confidence is never a factor in any score. At most it is TESTIMONY\_ONLY evidence.

### 11.4 Automation tiers

| Tier | Name | Automated | Always human |
| --- | --- | --- | --- |
| A0 | Manual | Engines compute and check; no AI calls | Every gate |
| A1 | Assisted | AI proposals, drafting, extraction, probes | Every gate |
| A2 | Supervised | Packet freeze (STRUCTURE gate) when the packet vector is READY; automatic regeneration of FAILED drafts, at most three times per packet | Acceptance, canon, resolutions, release, plans |
| A3 | Batch-supervised | As A2, plus batch drafting of a scene sequence; acceptance is still human but may be batched | Acceptance, canon, resolutions, release, plans |

**REQ-11.4.1.** No tier automates the CANON, INTEGRATION, or SHIP gates.

**REQ-11.4.2.** Automatic regeneration stops after its limit and escalates to a human with the findings from every attempt. This prevents regeneration loops that never converge.

### 11.5 The confidence control plane

Confidence in NSRES is a deterministic control system, not a model's intuition. It decides whether a proposed transition has enough evidence to proceed, needs more context, or must go to a human. A low score narrows the choice space: the engine offers only the actions its band permits.

**Formula.** As in §9.6: a weighted sum of named factor scores, each capped by its weakest evidence ceiling, minus conflict penalties, clamped to \[0, 1\]. Weights in each score type sum to 1. No score is accepted without its full breakdown (factors, weights, raw scores, ceilings, evidence references, reasons, penalties).

**Score types used in NSRES.** Corpus weights are kept where the corpus defines them; NSRES-assigned defaults are marked (HEU).

| Score type | Applies to | Factors (weight) | Hard cap? |
| --- | --- | --- | --- |
| Identity | Imported artifacts (path C); entity links | Imported artifacts: stable\_id 0.30, metadata 0.20, content\_signature 0.20, path\_continuity 0.15, name 0.10, provenance 0.05. Entity links: §9.6 | Yes (< 0.85 caps at 0.70) |
| Placement | Imported material assigned to a layer or record | schema\_rule 0.30, content\_match 0.25, prior\_identity 0.20, folder\_context 0.15, filename 0.10 | No |
| Fetch Completeness | Any decision that depends on prior text or external sources | sources\_found 0.30, identity\_verified 0.25, freshness 0.15, excerpt\_relevance 0.15, gap\_inverse 0.15 | No |
| Plan Alignment | Drafts against packets (§9.6); proposals against plans | Drafts: §9.6. Proposals: required\_scope 0.25, allowed\_records 0.20, required\_outputs 0.20, non\_goal\_respect 0.15, sequence 0.10, rollback 0.10 | No |
| Scope Compliance | Every automated run and LLM role | allowed\_read 0.25, allowed\_write 0.30, forbidden\_path\_respect 0.25 (no sealed content to a drafter), no\_status\_mutation 0.10, no\_unapproved\_exec 0.10 | Yes (< 0.95 caps at 0.84) |
| Safety | Drafts: Leak Safety (§9.6). System actions: no destructive deletion, rollback available, audit record written, gate respected | Drafts: §9.6. System actions: equal weights (HEU) | Yes (< 0.95 caps at 0.84) |
| Reconcile | Drafts: testimony against observation (§9.6). Automated runs: claimed changes against observed changes | Corpus: diff\_matches\_claim 0.30, no\_unreported\_changes 0.20, created\_as\_claimed 0.15, modified\_as\_claimed 0.15; remaining 0.20 to deleted\_as\_claimed (HEU) | Yes (< 0.95 caps at 0.84) |
| Source Grounding | Every packet, finding set, and canon proposal | §9.6 | Yes (< 0.85 caps at 0.80) |
| Semantic Equivalence | Transformations: packet to brief, summaries, revisions, adaptations (§12.4) | intent\_preservation 0.25, required\_concepts 0.20, forbidden\_meanings\_absent 0.15, structural\_relations 0.15; terminology\_locks 0.15 and no\_added\_claims 0.10 (HEU) | No |
| Critic | Any artifact | Critic module rubric | No; advisory |
| Promotion Readiness | Any promotion to ACCEPTED, CANON, or PUBLISHED | Weighted aggregate of the applicable types, then all hard caps | Applies the caps |

**Packet readiness vector** (read by the STRUCTURE gate at freeze; NSRES defaults, HEU): pre\_draft\_checks 0.35, source\_coverage 0.20, leak\_probe\_margin 0.20, dependency\_resolution 0.15, budget\_fit 0.10. Scope Compliance and Source Grounding caps apply.

**What each gate reads.**

| Gate | Vector | Band required |
| --- | --- | --- |
| PROPOSAL | Proposal vector (identity, source grounding, plan alignment) | READY to present as eligible; lower bands may only be revised, enriched, rejected, or slushed |
| STRUCTURE (freeze) | Packet readiness vector | READY |
| INTEGRATION (acceptance) | Draft acceptance readiness R (§9.6) | READY |
| CANON | Record promotion vector (identity, source grounding, reconcile against the model) | READY |
| SHIP | Segment vector: the minimum R over its scenes, drift indices within thresholds, no open MAJOR findings | READY |

**Overrides (REQ-11.5.1).** A human may accept below READY, because taste is the human's call. The override is recorded on the gate record with a reason, and the record carries an OVERRIDE flag. A failed hard cap cannot be overridden. It is cleared only by changing the inputs: revising the draft, or changing the plan the score is measured against (for example, moving a reveal earlier at the STRUCTURE gate).

**Bands and permitted actions** are those of §9.6: READY (0.95–1.00), PROVISIONAL (0.85–0.949, fetch or critic first), INSUFFICIENT (0.70–0.849, revise), UNSTABLE (0.40–0.699, regenerate, review, or slush), FAILED (below 0.40, not a decision basis). The hard caps are set just below band edges, so any failed cap removes the READY band from the choice space.

### 11.6 Mandatory validation points

| Point | Validation | Cannot be skipped because |
| --- | --- | --- |
| V1 | Rule suite and CANON-gate vector on every canon promotion | Canon errors propagate to every scene |
| V2 | Reconciliation to CONSISTENT before any packet freeze | REQ-5.4.2 |
| V3 | Pre-draft checks CC-1 to CC-10 | Packets are the drafter's only facts |
| V4 | L14 validation before acceptance | Accepted text updates RIS\_actual |
| V5 | L15 autopsy before SHIP | Drift and cumulative leaks are cross-scene |
| V6 | Retro-consistency at every reveal acceptance | REQ-6.9.1 |
| V7 | CANON status before a micro-fact becomes load-bearing | REQ-3.6.1 |
| V8 | Schema validation of every LLM output | Thrust may not bypass structure |
| V9 | Impact analysis on every gate decision | P9 |
| V10 | A confidence vector present at every gate | No gate passes on a bare "looks good" |

## 12. Integration

NSRES is the reality-and-continuity core of a larger control plane. The Writing-Craft System supplies the authored inputs, the Seam Protocol and editorial laws work on accepted prose, the Beat Engine and MAPS render the same story reality into video and images, and GVE can propose counterfactuals. Every integration follows one rule: other systems may read pinned model versions and write PROPOSAL records, and nothing else.

### 12.1 Integration contract

| Rule | Statement |
| --- | --- |
| IN-1 | External systems read only pinned, CONSISTENT or RELEASED model versions. |
| IN-2 | External systems write only PROPOSAL records or draft revisions; gates decide everything else (DEF-47). |
| IN-3 | Every external run is scored for Scope Compliance (§11.5); a run below 0.95 cannot feed a gate. |
| IN-4 | Every external run conforms to the SAVE Contract: Scan the input cursor, Assess, Validate, Execute a proposal artifact. In NSRES terms: admission against a cursor (C18), engine or LLM work, rule suite plus confidence vector, then a PROPOSAL record. |
| IN-5 | Identifiers cross system boundaries as uuid plus handle; names are never used as keys. |

### 12.2 The 23-module Writing-Craft System (WCS)

The central router, showrunner-production-handler, classifies each artifact and its phase and routes one worker at a time. Its INTAKE\_GATE approves that classification inside WCS. NSRES has no counterpart to that gate, because NSRES never reads RAW or INTAKE material (REQ-12.2.2). For NSRES, the handler's routing packet names the layer an incoming artifact proposes to, and the NSRES PROPOSAL gate still decides whether it enters. The table maps all 23 entries in WCS modules.json (version 1.0-runtime: 22 workers and the handler) to the layers they feed. Phases, primary artifacts, and default gates are copied from modules.json. The last column is the NSRES gate that decides the records NSRES derives from each output.

| WCS module | Phase | Primary artifact | WCS default gate | NSRES layer or component | NSRES gate for derived records |
| --- | --- | --- | --- | --- | --- |
| story-bottle-setup | I Capture | bottle\_map | PROPOSAL\_GATE | Initial L1 registry skeleton plus a context bundle (C18) | PROPOSAL |
| story-spark-capture | I Capture | spark\_card | PROPOSAL\_GATE | L2 premise (PROPOSAL). Its Anti-Flattening Check means NSRES requires no scene plan at this stage: L3 and L4 may stay empty. Its protected mystery stays open: NSRES records it as an open question (Q-) and does not resolve it during extraction | PROPOSAL |
| creative-riff-capture | I Capture | riff\_packet | PROPOSAL\_GATE | Raw material only; may seed canon candidates, each traceable to a line of the riff | PROPOSAL |
| story-why-trap | I Capture | why\_trap\_release\_packet | PROPOSAL\_GATE | L2 dramatic question; L6 goal overlay; stakes weights for narrative pressure (§7.8). Its meaning hypotheses stay hypotheses and never become rules | STRUCTURE for the L2 dramatic question |
| character-autopsy | II Bible | character\_dossier | PROPOSAL\_GATE | L1 identity; L6 goal and arc overlay; L9 secrets register (private pressures, masks); relations. Its institutional and relational dossier versions enter as two alternative PROPOSALs, which NSRES does not merge before the human chooses | CANON for identity; STRUCTURE for arcs |
| living-world-loop | II Bible | world\_ripple\_packet | PROPOSAL\_GATE | L5 offscreen and AMBIENT events; tertiary threads; a feed for the simulation layer (§12.9). Its bible candidates stay PROPOSAL | PROPOSAL, then CANON per record |
| production-bible-builder | II Bible | production\_bible\_proposal | PROPOSAL\_GATE, plus one CANON\_GATE per canon candidate | L1, through the CANON gate (its CANON\_GATE). Its classes map as CANON to a CANON-gate candidate, LIKELY to PROPOSAL, OPEN to a fact with truth UNDETERMINED or an open question, CONTRADICTION to an RC finding awaiting a RES record, and SLUSH to SLUSHED | CANON, one gate per record |
| sandbox-slush-pile | III Story discovery and commitment | fit\_verdict | PROPOSAL\_GATE | The SLUSHED status (§0.7). Its verdicts map to PROPOSAL-gate outcomes: ADMIT to ACCEPT, ADAPT to REVISE, HOLD to no outcome, SLUSH to SLUSH, REJECT to REJECT (through the WCS DELETE\_GATE) | PROPOSAL |
| story-conspiracy-board | III Story discovery and commitment | connection\_map | PROPOSAL\_GATE | L5 causal edges (the Causal DAG); secrets register; thread register. Its story-legs test corresponds to the L2 checks that each thread has convergence nodes and a resolution or deferral | PROPOSAL for edges; STRUCTURE when its emerging story becomes the L2 plan |
| story-spine-lock | III Story discovery and commitment | story\_spine | STRUCTURE\_GATE | L2 macro plan and end-state targets. Foreclosed options become L1 PROHIBITION rules or L2 constraints, so reconciliation enforces them | STRUCTURE; CANON for prohibitions |
| story-blueprint-builder | III Story discovery and commitment | story\_blueprint | STRUCTURE\_GATE | L3 scenes and L4 beats. WCS will not run it without a CANON story\_spine (see the state-semantics note below) | STRUCTURE |
| spark-rewrite-triage | III Story discovery and commitment | rewrite\_triage\_verdict | PROPOSAL\_GATE | Change proposals against L2 to L4. NSRES change propagation (§4.17) supplies the blast radius: the packets, drafts, and reveals that a SPARK SHIFT or NEW BLUEPRINT verdict would make stale | PROPOSAL; STRUCTURE for any resulting L2 to L4 change |
| first-draft-forward | IV Production | draft\_forward\_packet | PROPOSAL\_GATE | L13 DRAFTER role. Bracketed marks are drafter annotations, excluded from assertion extraction and logged as testimony (REQ-12.2.1). Raw footage is always a new draft revision, never an in-place rewrite | INTEGRATION for draft acceptance |
| pov-shot-selection | IV Production | pov\_decision\_packet | PROPOSAL\_GATE | L3 POV configuration; §7.4 POV rules. Its information boundary becomes the packet's POV limits; its leak audit corresponds to AU-20 to AU-24 | STRUCTURE |
| scene-performance-director | IV Production | performance\_edit\_packet | INTEGRATION\_GATE | Revisions of ACCEPTED text (§12.3) | INTEGRATION |
| telling-architecture-recut | V Post-production | recut\_proposal | STRUCTURE\_GATE | L3 reorder. Triggers the "scenes reordered" propagation rule (§4.17): RIS\_plan recomputed, every later packet re-checked, reveals and irony gaps re-validated. RIS\_plan also supplies the knowledge state before and after each moved scene, which the module's prose schema requires and its machine contract has no field for | STRUCTURE |
| advanced-camera-pov | V Post-production | advanced\_camera\_plan | INTEGRATION\_GATE | L3 POV configuration changes within a scene. Each cut's information gained is a reader-state change checked against the reveal plan; its drift audit corresponds to AU-20 to AU-24. WCS requires a pov\_decision\_packet first | INTEGRATION; STRUCTURE if a cut changes an L3 POV field |
| diegetic-document-weaver | V Post-production | diegetic\_document\_packet | INTEGRATION\_GATE | Document objects (OBJ) whose contents are propositions. Authorial bias is a set of CLM records with truth values; epistemic limits are the writer's CIS at the time of writing. Readers learn through the READ channel | INTEGRATION for placement; CANON for any document claim promoted to fact |
| prose-voice-strategy | V Post-production | voice\_strategy | PROPOSAL\_GATE | `voice_profile_ref` in packets; AU-44 voice drift | STRUCTURE when adopted as the project voice profile |
| tone-surf-editor | V Post-production | tone\_surf\_edit | INTEGRATION\_GATE | Revisions of ACCEPTED text (§12.3) | INTEGRATION |
| rhythm-edit | V Post-production | rhythm\_edit\_packet | INTEGRATION\_GATE | Revisions of ACCEPTED text (§12.3). The module preserves purposeful fracture, dialect, and fragments by design | INTEGRATION |
| showrunner-final-cut | V Post-production | final\_cut\_decision | SHIP\_GATE | The SHIP gate and the segment readiness vector (§11.5) | SHIP |
| showrunner-production-handler | HANDLER | routing\_packet | INTAKE\_GATE | No layer. Its routing packet names the layer an artifact proposes to; its INTAKE\_GATE has no NSRES counterpart (§0.7) | none |

The WCS critic pass corresponds to the CRITIC role (§10.12): advisory, never gating.

**REQ-12.2.1.** Bracketed editorial marks from first-draft-forward MUST be stripped before assertion extraction and stored as drafter annotations. They are never asserted facts.

**State-semantics conflict (resolved 2026-10-25).** WCS and NSRES use CANON differently for telling artifacts. In WCS, STRUCTURE\_GATE moves a story\_spine or story\_blueprint to CANON state; that is why story-blueprint-builder and first-draft-forward carry the precondition `requires_canon_type` in modules.json. In NSRES, telling records (L2 to L4) top out at ACCEPTED, and CANON means a locked reality record (§0.7). The §0.7 crosswalk proposes how an adapter bridges the two: a WCS CANON telling artifact imports as an ACCEPTED, structure-locked NSRES telling record, and a WCS CANON fact, entity, or world rule imports as NSRES CANON. Patrick decided on 2026-10-25 that the NSRES vocabulary governs (decision OQ-9), so this mapping binds any WCS adapter.

**REQ-12.2.2.** NSRES MUST NOT import WCS material at RAW or INTAKE state, and MUST NOT treat a WCS PROPOSAL or REVISED\_PROPOSAL artifact as a fact. Such an artifact enters NSRES only as a PROPOSAL record. A WCS output whose validator status is FAIL is quarantined by WCS and is not imported at all.

### 12.3 Seam Protocol and editorial laws

The Seam Protocol's four gated passes (Detector, Generator, Critic, Compositor) operate on ACCEPTED prose after autopsy. NSRES binds them with five rules.

1. A seam edit produces a new draft revision of the scene; the accepted revision is kept.
2. The Compositor's micro-edits (cuts, lexical edits, weight edits) are re-validated by L14, scoped to the changed spans.
3. The revision's Semantic Equivalence score (§11.5) against the accepted revision must be READY for beats, outcomes, and LOCKED facts.
4. Seam edits may not add facts. A new concrete detail becomes a micro-fact proposal.
5. Seams created by telling-architecture-recut are routed through propagation (§4.17) before the Seam Protocol runs, because a reorder can change what the reader knows at each seam.

**Editorial laws as an advisory check suite.** These are craft checks. They produce INFO or MINOR findings and never affect integrity scores.

| Code | Law | Detection |
| --- | --- | --- |
| ED-01 | Core Law: a sentence earns its place by doing something the previous sentence did not | Consecutive sentences that yield no new assertion and render no new beat |
| ED-02 | Announcement ban | Sentences that state what is about to be shown instead of showing it |
| ED-03 | Unnamed-First Principle | An entity new to the reader whose proper name appears before any behavior, sound, movement, or function is rendered; checked against the packet's `first_contact` list |
| ED-04 | Jargon ban | A label or taxonomy term used where the behavior it names should appear |

The Unnamed-First Principle governs the order of presentation, not character knowledge. If Mara already knows Hale's name, the prose may still show him before naming him; PV-5 only forbids naming what the POV does not know.

### 12.4 Beat Engine (video) and adaptation

The Beat Engine's core law — a video is a sequence of meaningful state transitions — is the NSRES beat definition (DEF-25) applied to a camera. The Beat Engine's July 2026 intake and reconciliation (v0.1, PROPOSAL) collapsed five overlapping codifications into one beat-level unit and one sequence-level arc; the mapping below uses that reconciled structure. Per that document's exposure entry 4, the rule that every beat alters the viewer's model is scoped to explanatory and narrative sequences. Ambient, mood, and montage beats may hold a state instead (the SUSTAIN beat type, L4). The names Beat Engine and Strange Engines Reveal Protocol follow that document's recommendation, which is still open at its gate P-A.

**Beat level.**

| Beat Engine slot | NSRES source | Note |
| --- | --- | --- |
| ANCHOR | L1 identity locks; `character_states`; setting state; MAPS canonical seeds (§12.5) | What stays recognizable |
| ENTRY (mode and state) | Mode: continuity-match, cold open, in medias res, echo, or frame break. For continuity-match, the entry state equals the previous beat's exit handle | Continuity-match is one option, not a law |
| CLAIM | The beat's single READER delta | One abstraction per beat |
| MECHANISM | The L5 event bound to the beat. The muted-viewer test is the CAMERA POV mode: observable facts only (§7.4) | Demonstrates the claim; does not decorate it |
| CUE | Perceptibility and attention rules (PV-2); camera direction | How attention is steered |
| CONSEQUENCE | The beat's world, character, and reader deltas | The slot the earlier VIDEO UNIT STRUCTURE lacked |
| EXIT HANDLE | An object, motion, or color in the beat's exit state (L7, L8) | Mandatory in chains; optional standalone |
| CONSTRAINTS | Packet constraints, terminology, forbidden revelations | Constant across the sequence |

Per-beat ledger fields outside the unit map as follows: SUBJECT RESPONSE to the anchor's displayed physical and emotional state (`character_states`); CAMERA to camera-mode parameters; SPOKEN LINE to dialogue or voiceover (CONSTRAINED or LOCKED per packet); ENERGY VALUE is inherited from the sequence arc.

**Sequence level.**

| Beat Engine sequence field | NSRES source |
| --- | --- |
| Concept ladder | The ordered READER deltas across the sequence's beats (RIS\_plan) |
| Energy arc | Sequence-level tension shape and narrative-pressure targets (§7.8). Beats inherit their value; energy is not a beat slot |
| Continuity ledger (exit object → entry match → conceptual function) | Seam records between beats. The conceptual function plays the role of a causal-edge justification, so a seam with no function is flagged as decoration |
| Aesthetic lock | Voice profile and MAPS seeds, swappable without touching beat logic (the claim, mechanism, aesthetic separation) |
| Closure rule | The sequence's L2 end-state target: the final beat returns the claim to observable reality |
| Identity Sheet (Stage 0) | L1 identity and format canon, pulled from the Codex PRODUCTION lens (§16.8) |

The Beat Engine's per-clip QA checklist (anchor held, mechanism legible, cue lands, entry state matches, exit handle present, negatives respected) maps to the Identity score, Plan Alignment, and the continuity suite applied at beat boundaries. A failed item regenerates only that beat.

**Adaptation path (novel to screen or video).** The same Story Reality is kept, and a new telling is planned (L3, L4) with pov\_mode CAMERA. Packets are extracted as usual and compiled into model-specific prompts. Compilation is deterministic (the same packet yields the same prompt), but rendering is stochastic: the same prompt yields different clips per seed and model version. NSRES therefore adopts the intake document's relabel (its exposure entry 1) of the corpus "transcompiler" framing as a lossy beat compiler. A compiled prompt is never treated as a continuity guarantee; continuity is established only by QA on the rendered clip. Adaptation fidelity is measured with the Semantic Equivalence score.

**Stage 0 identity set: resolved.** The author has supplied the locked canonical SLB set (GSTC v1.2 / v3.1): SI Structural Identity, EP External Partition, IS Internalized Scaffolding, FT Flow Transduction, SR Systemic Responsivity, DI Delta Integral. This confirms the intake document's candidate identification (its gate P-C) and supersedes the older 5-SLB and 6-SLB vocabularies (FP, CD, II, EI), which NSRES does not use. The physics framing of the set (the Hamiltonian and Lagrangian triads) is GSTC content and is out of scope for this specification.

**Proposed Stage 0 Identity Sheet fields (PROPOSAL; see claim C16).** Each SLB, read through its supplied definition, suggests one field of the identity sheet for a sequence.

| SLB | Supplied definition (paraphrased) | Proposed Identity Sheet field | NSRES source and check |
| --- | --- | --- | --- |
| SI | Closure of identity across state transitions; tracks operative identity against target identity | Identity anchor: what must stay recognizably the same in every beat. The sheet is SI\_target; each rendered clip shows SI\_op | L1 identity locks; Identity score; anchor QA |
| EP | The outer boundary and the exterior pressure the identity must hold against | Audience contract and format boundary: what the sequence is and is not; the constant negatives | L1 format canon; the CONSTRAINTS block |
| IS | Internal topology, channel nesting, and scale gaps that distribute load | Sequence architecture: the concept ladder and how claims are distributed across beats | L2, L3, L4 structure |
| FT | Crossing logic, transduction, and scale translation across boundaries | Transition logic: entry modes, seams, and how each claim crosses into a visible mechanism | ENTRY, EXIT HANDLE, MECHANISM; continuity ledger |
| SR | Drift correction that keeps operative identity tracking target identity | The QA and regeneration loop: per-beat checks; re-roll only the failing beat | L14, L15; per-beat regeneration |
| DI | Reintegration fidelity: preserving shape after changes propagate | Reintegration rule: each consequence integrates into the viewer's model, and revisions propagate without breaking identity | Closure rule; propagation (§4.17); retro-consistency (REQ-6.9.1) |

The SI and SR rows track their definitions closely: target identity, operative identity, and drift correction are exactly what anchor QA measures. The FT and DI rows are looser readings and are the weakest joints of the mapping.

### 12.5 MAPS and visual canon

| MAPS element | NSRES integration |
| --- | --- |
| Seed tags CANONICAL, SEED CANDIDATE, WIP, REJECT | Map to CANON, ACCEPTED, PROPOSAL, REJECTED |
| Character, environment, lighting, and material seeds | Referenced from L1 entity records (`visual_identity` refs) and from packets for illustrated or video scenes |
| Pass 1 (subject, scale, era) | Consumes L1 identity and canon era rules |
| Pass 3 (lighting and atmosphere) | Consumes L7 light and conditions (for SCN-007: grey daylight at 07:40) |
| Three information-flow layers: internal state, external output, human interface | The packet (internal state), the compiled brief or prompt (external output), the Gate Console (human interface) |
| VISUAL-BRIEF router | NSRES exports its Causal DAG, timelines, and thread maps as diagram sources for the router's DIAGRAM and WHITEBOARD-MAP targets |

Attribute drift (DI-1) extends across media: a scar on the left cheek in a canonical seed and on the right in prose is the same defect class as two eye colors in prose.

### 12.6 ARTEMIS EMA and GVE

NSRES uses one interface from this system: GVE (Module 13) as a counterfactual generator. Given a contradiction, or a change the author is considering, GVE proposes alternative Story Reality branches. NSRES treats each as a canon branch dry run (§12.8): it reconciles the branch, reports the structural delta from the main line (records changed, contradictions created or removed, scenes affected), and stores everything at PROPOSAL status. Module 0's role (deterministic verification of generated material) is the same role NSRES's engines play. NSRES makes no use of, and no claims about, the rest of the ARTEMIS architecture.

### 12.7 "Hypocrisy Tax": candidate operationalization (HEU, not adopted)

The corpus term describes the cost of structural contradiction. A checkable form for NSRES would be:

```latex
HT(\text{scope}) = \sum_{f \in \text{open findings}} \mathrm{sev}(f) \cdot \mathrm{age}(f) + \sum_{v \in \text{vectors}} \sum_j p_{v,j}
```

That is, severity-weighted open findings multiplied by how many scenes they have stayed open, plus every conflict penalty in the scope's confidence vectors. Severity weights would follow §9.6 (BLOCKING 0.20, MAJOR 0.08, MINOR 0.02). The thermodynamic framing is a metaphor; this formula is the measurable part. It is not a gate metric until §14 shows it predicts revision cost.

### 12.8 General integration points

| Integration point | Design |
| --- | --- |
| Graph-based storage | The projection graph (§10.7) exports as a labeled property graph. An RDF or OWL export of L1 is optional, for shared ontologies across works. |
| Knowledge bases | Series-bible import and export; research facts enter L1 as world rules with source citations as provenance. |
| RAG systems | Facts are retrieved by key (entity, attribute, story-time, version), never by text similarity. Text retrieval is used only for voice-continuity samples and as a pointer to where to read. Retrieved passages are FOUND\_BY\_SNIPPET or FOUND\_BY\_METADATA until fully read (CONTENT\_READ). |
| Canon registries for shared universes | Several works share one L1. Each work keeps its own L5 segment and telling layers. PUBLISHED canon in any work binds all works. A universe-level CANON gate decides cross-work conflicts. |
| Narrative databases and file formats | JSON (this schema), CSV timelines, Markdown manuscripts, and screenplay formats (Fountain, Final Draft) through import and export adapters. |
| Versioning | Model versions behave like commits. A canon branch is a fork of Story Reality, used for alternate drafts and what-ifs. Merging a branch is a reconciliation of the union, with conflicts decided at the INTEGRATION gate. Diffs are record-level, not text-level. RELEASED and PUBLISHED are tags. |
| Multi-agent systems | A blackboard architecture: the model is the blackboard. Agents (the §10.12 roles and WCS modules) read pinned versions and write PROPOSAL records only. The showrunner handler schedules agents through cursors. No agent holds authority over another. |

### 12.9 Future simulation layers

1. **Offscreen simulation.** Each character runs as an agent with its goals (L6 overlay), knowledge (L9), and the canon's rules of the world, over a story-time window. The simulation proposes offscreen and AMBIENT events that fill unaccounted intervals or test whether a plan is plausible. Runs use fixed seeds for reproducibility. Every output is a PROPOSAL. living-world-loop is the natural driver.
2. **Counterfactual exploration.** GVE branches (§12.6) run as canon-branch dry runs.
3. **Interactive fiction.** Player state is the Reader Information State. Narrative-time branches by player choice, and each branch that changes reality is a canon branch.

## 13. Failure modes, limitations, and open problems

The largest risks to NSRES itself are authoring cost, over-constrained prose, imperfect assertion extraction, and fiction that has no single determinate reality. Each has a stated mitigation; several remain open problems.

### 13.1 Failure modes of the methodology

| ID | Failure mode | Mechanism | Mitigation | Residual risk |
| --- | --- | --- | --- | --- |
| FM-01 | Authoring burden | Modeling every event costs time; authors stop maintaining the model | Lazy commitment; three entry paths; modeling depth tiers (§13.2); AI proposals | High for short works |
| FM-02 | Over-constraint | Dense packets turn drafting into beat-by-beat transcription | Beats as outcomes; CONSTRAINED and FREE classes; budget priority; critic pass | Medium; measured by §14 quality ratings |
| FM-03 | Model–prose gap | Subtext, irony, and ambiguity carry meaning that is not reducible to propositions | IMPLIED and HINTED modes; permanent mysteries; human acceptance | Inherent |
| FM-04 | Extraction ceiling | Assertion extraction misses implied facts or misreads irony | Span checks; human review of low-confidence findings; sample audits | Medium |
| FM-05 | Probabilistic reader inference | What a reader infers varies from reader to reader | Confidence on RIS entries; probes; author judgment | Inherent |
| FM-06 | Goodhart effect | Optimizing scores instead of story | Scores never measure aesthetic quality; critic advisory only; the human taste gate | Medium |
| FM-07 | Wrong canon | Wrong canon yields confident, wrong packets | CANON gate; source citations; reconciliation | Medium |
| FM-08 | Leak-probe validity | LLM readers infer differently from human readers | Decoys; calibration against human readers (§14) | High until calibrated |
| FM-09 | Suppression incoherence | A drafter that never sees the secret writes behavior that does not fit once the secret is revealed | Manifestations derived from the secret by the engine; retro-consistency at reveal | Medium; tested by H3 |
| FM-10 | Scale | Checks across a long series grow large | Incremental reconciliation; impact sets | Low to medium |
| FM-11 | Weak emotional modeling | Emotion is modeled as a volatile authored annotation, which is crude | Treated as guidance; findings capped at MINOR | Inherent |
| FM-12 | Packet overflow | Convergence scenes exceed the budget | EX-05 halts extraction; split the scene; summarize background | Low |
| FM-13 | Control-plane drift | Weights and thresholds changed ad hoc | Versioned configuration; human-controlled (REQ-11.2.1) | Low |
| FM-14 | False authority of numbers | A score of 0.96 looks precise, but its weights are heuristics | Every vector shows its breakdown; HEU tags; calibration plan (§14) | Medium |

### 13.2 Modeling depth tiers

Not every work needs full modeling. A work declares a depth, and the engine reports checks outside that depth as UNCHECKABLE, never as PASS.

| Depth | Modeled | Checks available | Suits |
| --- | --- | --- | --- |
| D1 Skeleton | Entities; scene windows; presence; custody of plot objects; secrets register | Movement, custody, basic knowledge | Short works; early drafts |
| D2 Standard | D1 plus every onscreen event with effects; knowledge grants for plot propositions; reveal plan | All reality checks for plot facts; leak checks | Most novels |
| D3 Full | D2 plus offscreen and ambient events; perceptibility; timetables; emotional overlays | Every check in this specification | Mysteries, thrillers, long series |

### 13.3 Fiction types that strain the model

| Type | Strain | Status |
| --- | --- | --- |
| Time travel and loops | Story-time is not monotonic for some characters; the causal graph may need cycles | Open: needs a personal-time axis per character and a canon rule that scopes permitted loops, relaxing RC-06 only inside them |
| Book-length unreliable narration | The narrator belief set becomes large; unregistered unreliability is hard to tell from error | Partial: PV-6 handles registered claims only |
| Deliberate ambiguity, magical realism | Some contradictions are intended | Partial: PERMANENTLY\_UNDETERMINED covers unresolved facts; intended contradictions need a scoped rule class (open) |
| Multiple realities, dream logic | More than one reality is true at once | Partial: canon branches as parallel realities, selected per scene |
| Epistolary and documentary forms | Facts arrive through documents with bias | Supported: document objects with claims and the READ channel |
| Large ensembles with many POVs | Many CIS tracks; many irony gaps | Supported; cost grows with POV count |

### 13.4 Open problems

1. **OP-1.** Calibrating leak probes against human readers.
2. **OP-2.** Measuring IMPLIED delivery reliably.
3. **OP-3.** Representing subtext as data without flattening it.
4. **OP-4.** Placing fuzzy times without inventing false precision.
5. **OP-5.** A personal-time model for time-travel fiction.
6. **OP-6.** Whether suppression by abstraction beats informed drafting for strong models (H3).
7. **OP-7.** Calibrating the weights in the confidence vectors.
8. **OP-8.** A cost model for when modeling time exceeds revision savings (H4).

## 14. Evaluation plan

H0 through H4 are tested by comparing seven drafting conditions on the same reconciled story models. The primary judges are blinded human annotators and naive human readers, so NSRES's own autopsy is never the only judge of NSRES. None of this has been run yet.

### 14.1 Conditions

| ID | Condition | Drafter receives | Tests |
| --- | --- | --- | --- |
| C-A | Flat outline, plain prompt | Outline and scene summary | Baseline |
| C-B | Flat outline, engineered prompt | Outline plus a best-practice prompt: continuity instructions, character list, style guide, written and iterated by a skilled prompt engineer on held-out scenes | Prompt engineering (H0) |
| C-C | Unreconciled notes, matched length | Outline plus series-bible notes equal in tokens to the NSRES brief | Information volume (H2) |
| C-D | NSRES brief, suppression by abstraction | Compiled brief (public section only) | Treatment (H1) |
| C-E | NSRES brief, informed drafting | Brief plus the sealed section with a non-disclosure instruction | Suppression method (H3) |
| C-F | NSRES brief without the reader layer | Brief with reader\_known, irony constraints, hints, and forbidden revelations removed | Contribution of L10 |
| C-G | Long context | Outline plus all prior drafted text of the work | Whether a large context window substitutes for a reconciled state |

### 14.2 Materials and procedure

1. At least six story models across genres (mystery, thriller, literary, fantasy, romance, screenplay), each with at least 20 scenes, built at depth D3 and reconciled before the trial.
2. All conditions use the same drafter model and sampling settings; the trial is repeated with at least two drafter models.
3. Each scene is drafted at least three times per condition.
4. **Protocol 1 (raw drift).** Each condition drafts its scenes in order and uses its own earlier drafts as context, with no human fixes, so defects accumulate as they would in practice.
5. **Protocol 2 (author cost).** Authors fix each condition's drafts to an acceptable standard, timing the work. NSRES modeling time is recorded separately.

### 14.3 Metrics

| ID | Metric | Measured by | Hypothesis |
| --- | --- | --- | --- |
| M1 | Continuity defects per 1,000 words (AU-0x, AU-1x, AU-4x classes) | Blinded annotators with the model and reader ledger | H1, H2 |
| M2 | Information-state violations per 1,000 words (AU-2x) | Blinded annotators | H1, H2 |
| M3 | Hidden-thread leak rate | Naive readers answer the probe question battery at each reveal checkpoint | H3 |
| M4 | Beat and outcome fulfillment rate | Annotators | H1 |
| M5 | Blind quality ratings: prose, engagement, coherence (1–7) | Naive readers | Over-constraint guard (FM-02) |
| M6 | Author fix time per chapter, plus modeling time | Protocol 2 timing | H4 |
| M7 | Autopsy precision and recall per AU code | Autopsy output against human annotation | Validates L15 |
| M8 | Calibration of the READY band: share of READY drafts with no human-found BLOCKING defect | Confidence vectors against annotation | OP-7 |
| M9 | Leak-probe agreement with naive readers | Probe scores against M3 | OP-1 |
| M10 | Correlation of the candidate Hypocrisy Tax with fix time | §12.7 formula against M6 | §12.7 adoption |

### 14.4 Annotation protocol

1. Two annotators per scene, with adjudication of disagreements.
2. Annotators are blind to condition. Condition-revealing artifacts (bracketed marks, emergent-detail lists, beat maps) are stripped before annotation.
3. Inter-annotator agreement (Krippendorff's alpha) is reported per defect class. Classes with agreement below a pre-registered threshold are reported but not used to test hypotheses.

### 14.5 Pre-registered success criteria

Margins are fixed before the trial, after the pilot. Analysis uses mixed-effects models with story and scene as random effects.

| Hypothesis | Supported if | Falsified if |
| --- | --- | --- |
| H1 | M1 + M2 in C-D are lower than in C-A, C-B, and C-G by the pre-registered margin | No significant reduction against C-B or C-G |
| H2 | M1 + M2 in C-D are lower than in C-C | C-C performs as well as C-D |
| H3 | M3 in C-D is lower than in C-E, with M5 coherence not worse | M3 is equal or lower in C-E |
| H4 | Fix time plus modeling time for C-D is below fix time for the best baseline | Modeling time exceeds the savings |
| Over-constraint guard | M5 in C-D is not lower than in C-B by more than the pre-registered margin | Quality falls beyond the margin |

### 14.6 Threats to validity

| Threat | Mitigation |
| --- | --- |
| Circularity: NSRES judging NSRES | Human annotation and naive readers are primary; autopsy accuracy is itself measured (M7) |
| Information-volume confound | Conditions C-C and C-G |
| Weak prompt-engineering control | C-B written and iterated by a skilled prompt engineer on held-out scenes |
| Drafter-specific effects | At least two drafter models |
| Story-model quality favoring NSRES | Every condition's outline is derived from the same L3 and L4 plans |
| Genre effects; small samples | At least six genres; effect sizes estimated in a pilot first |
| Models changing over time | The trial is versioned and re-run as drafter models change |

### 14.7 Staging

1. **Pilot:** one story model, ten scenes, conditions C-A, C-B, and C-D. Purpose: estimate effect sizes and annotation cost, then fix margins.
2. **Full trial:** all conditions, Protocol 1.
3. **Field study:** working authors, Protocol 2, for H4.

## 15. Claims exposure ledger

This is an adversarial pass over the specification's own load-bearing claims, including claims carried in from the corpus and mappings this draft generated. It is advisory: the author gates every entry. Fluency in the corpus vocabulary is not evidence that a mapping or a claim is true.

### 15.1 Ledger

| ID | Claim | Type | Attack | Exposure | What would raise confidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | H0: continuity-class defects come mainly from the absence of reconciled state, not prompt wording | HYP | Engineered prompts or long context may close the gap; the effect may come from information volume alone; strong models may track state given the whole manuscript | HIGH | §14 conditions C-B, C-C, C-G | UNTESTED |
| C2 | Most outlines are narrative-order representations | Empirical generalization | Many professional writers keep timelines and bibles; no survey was done | MEDIUM | A survey of author practice. NSRES's value does not depend on this being rare | CLAIM\_INFERRED |
| C3 | Corpus wording: AI writing quality does not improve through prompt engineering | Universal empirical claim | A universal negative, contradicted by the ordinary observation that prompts change output | HIGH | Restated in this spec as H0 ("mainly", scoped to continuity-class defects) | NOT ADOPTED as worded |
| C4 | Suppression by abstraction reduces leakage (H3) | HYP | Manifestations can leak by themselves; a drafter without the secret may write behavior that does not fit after the reveal (FM-09) | HIGH | C-D against C-E on M3 and M5 | UNTESTED |
| C5 | Deterministic checks catch most hard defects | HYP | Detection depends on extraction recall; implied contradictions escape span-based checks | MEDIUM | M7 recall per AU code | UNTESTED |
| C6 | LLM leak probes approximate human inference | HYP | LLMs know genre conventions and may over- or under-infer relative to readers | HIGH | M9 | UNTESTED |
| C7 | The narrative pressure vector is meaningful | HEU | Weights and components are chosen, not derived | MEDIUM | Correlation with reader tension ratings | Planning aid only |
| C8 | Confidence weights, caps, and bands produce decisions that track defect risk | HEU and DD | Numbers are chosen, not fitted; precise-looking values invite over-trust (FM-14) | MEDIUM | M8 calibration curve | UNCALIBRATED |
| C9 | Reconciliation is computationally tractable | Technical claim | STN consistency is polynomial (standard result); general Allen-algebra satisfiability is NP-complete (standard result), so the disjunction cap can leave checks UNCHECKABLE | LOW | Benchmarks on real models | SUPPORTED for the STN part; bounded for disjunctions |
| C10 | Modeling cost is repaid by reduced revision cost (H4) | HYP | For many works, modeling may cost more than it saves | HIGH | Protocol 2 field study | UNTESTED |
| C11 | Two thread axes (rank, visibility) beat a single four-label list | DD | Two fields cost more upkeep than one | LOW | Author usability test | DD, justified by the THR-02 transition |
| C12 | "Hypocrisy Tax" as thermodynamic waste heat | Metaphor | No physical quantity is measured; the framing invites over-reading | MEDIUM | §12.7 operationalization plus M10 | NOT ADOPTED as a gate metric |
| C13 | Structural mappings: the Beat Unit maps onto NSRES beats; MAPS's three information layers map onto packet, brief, and console | Claude-generated isomorphism | Mappings may be looser than they read; matching words is not matching mechanisms | MEDIUM | Run one adaptation end to end and record which fields actually carry over | PROPOSAL |
| C14 | The §12.2 WCS module mapping | Mapping | Written from one-paragraph module summaries, not from module specifications | MEDIUM | Read each module's specification in full and diff against §12.2 | PROVISIONAL |
| C15 | §1.3 novelty: what is specific to NSRES | Novelty claim | Narrative-generation research may already track reader knowledge or use packet-like contracts; no literature search was run for this draft | MEDIUM | A literature search | CLAIM\_INFERRED |
| C16 | The six SLBs map onto six Stage 0 Identity Sheet fields (§12.4) | Claude-generated analogical isomorphism | The SLB definitions are physics-framed system properties; applying them to authoring artifacts may be fitting words, not mechanisms. FT (scale translation read as claim-to-mechanism crossing) and DI (shape preservation read as closure and propagation) are the weakest joints; DI's definition is closer to retro-consistency than to a closure rule | MEDIUM | Build one Identity Sheet with these six fields for a real sequence and check whether each field constrains generation or stays empty boilerplate | PROPOSAL |
| C17 | GSVT, UTED-EC, and QMCP can serve as the ontology for a story world's physics (§17.2) | DD | The frameworks are contested as accounts of real physics. Answer: fictional physics is canon by the author's decision, so the engine depends only on the kit being internally consistent and computable, not on its truth about our universe | LOW (for fiction use) | Read the UTED-EC v3.1 and QMCP canon in full and confirm each kit row against the text | PROPOSAL; FOUND\_BY\_SNIPPET grounding |
| C18 | The six SLB axes are the right structure for a mechanic sheet (§17.3) | Claude-generated application | Six axes may be boilerplate for small mechanics (a candle-lighting cantrip); some fields may duplicate each other in practice. GSVT's origin in magic-system design supports the fit but does not prove it | MEDIUM | Write sheets for ten real mechanics; count fields left NOT\_APPLICABLE and fields whose checks never fire | PROPOSAL |
| C19 | Mechanics are deterministic unless an occluded variable is declared (MC-13) | DD | Some authors want genuinely random magic. Answer: declare the randomness as a seeded occluded variable, which keeps outcomes reproducible for checking | LOW | Author usability test on a work with chance-based magic | DD |

### 15.2 Evidence notes

| Item | Evidence label | Note |
| --- | --- | --- |
| Corpus architecture summary (NSRES, WCS, Seam Protocol, MAPS, Beat Engine, ARTEMIS/GVE) | CONTENT\_READ (of the summary document supplied in this session) | The underlying module specifications were not read: GAP\_IDENTIFIED |
| Corpus confidence control plane (formula, score types, caps, bands, fetch tiers, adapter) | CONTENT\_READ (of the summary supplied in this session) | Some factor lists in the summary end in "etc."; NSRES fills those gaps with weights marked HEU |
| STN and Allen-algebra complexity results | Standard results, stated without citation in this draft | Add citations in v0.2 |
| Prior art in §1.3 | Named from general knowledge; not searched | GAP\_IDENTIFIED (C15) |
| Canonical SLB lock (GSTC v1.2 / v3.1) | CONTENT\_READ (of the summary supplied in this session) | Confirms the six-element set. The underlying GSTC specification was not read; the identity-planning field mapping is Claude's (C16) |

### 15.3 Readiness of this specification

Scored with the factorized confidence calculator, for one decision: accepting the specification as the working specification for the §14 pilot. v0.1.1 result: **0.80, INSUFFICIENT** (0.8035 before the Source Grounding cap). v0.1 scored 0.78. The specification remains a PROPOSAL.

| Factor | Weight | Raw | Evidence | Reason |
| --- | --- | --- | --- | --- |
| internal\_consistency | 0.25 | 0.85 | CONTENT\_READ: the v0.1 targeted pass (five defects fixed); v0.1.1 found four more of one kind, prose and code drifting apart (SUSTAIN, DETECTED, Finding.status, the §6.8 heading), all fixed | Still targeted searches, not a full mechanical cross-check of every enumeration; no independent reviewer |
| definitional\_completeness | 0.20 | 0.95 | CONTENT\_READ: all 28 requested terms defined (§2); every requested section present | Complete against the request |
| buildability | 0.20 | 0.85 | CONTENT\_READ: §10.2 to §10.11; B.2 to B.4. GAP\_IDENTIFIED: the peer handoff's full packet sub-schemas (its Patch 4) were never delivered | Several packet sub-schemas still reference §8.2 instead of being written out |
| integration\_grounding | 0.15 | 0.74 | CONTENT\_READ: WCS modules.json 1.0-runtime (both versions), the handler runtime, PROJECT\_FULL\_EXPLICATION, all 23 module sources; Beat Engine intake v0.1; SLB lock. GAP\_IDENTIFIED: Seam Protocol, MAPS, ARTEMIS/GVE, UTED-EC v3.1, QMCP canon | Weighted by target: WCS 0.35 at 0.95, Seam 0.15 at 0.60, Beat Engine 0.15 at 0.80, MAPS 0.10 at 0.55, ARTEMIS 0.10 at 0.55, mechanics kit 0.15 at 0.60 |
| critic | 0.20 | 0.60 | CONTENT\_READ: ledger §15.1; C1, C4, C6, C10 HIGH and untested. The peer handoff attacked none of them | These are what the pilot tests |

The Source Grounding cap binds: integration\_grounding is below 0.85, so improving any other factor cannot lift the score above 0.80. Permitted next actions in this band: enrich context or revise. In order of effect on the score:

1. Read the Seam Protocol, MAPS, ARTEMIS/GVE, UTED-EC v3.1, and QMCP sources in full, then diff §12.3 to §12.6 and §17.2 against them (raises integration\_grounding and lifts the cap). The WCS part of this step was done in v0.1.1.
2. Run an independent review of the whole document (raises internal\_consistency).
3. Write out the remaining packet sub-schemas (raises buildability). This is work package WP-010 in the build plan.
4. Run the §14 pilot (raises critic, and is the only path to testing H0).

## 16. World Codex layer

The Codex is a set of modules that continuously renders the reconciled model into a navigable world bible, while extraction and drafting run on the other side. It produces entity pages, timelines, maps, relationship and causal graphs, and dashboards, each filtered through a declared epistemic lens. It is a projection, never a source: every page is regenerated from a pinned model version, and every edit made through it becomes a PROPOSAL.

### 16.1 Why it exists

1. **The model must be visible to be maintained.** Thousands of records are unreadable as rows. Authors, editors, illustrators, and showrunners need the World Anvil-style view: pages, maps, family trees, chronicles.
2. **Hand-kept bibles drift.** A bible maintained beside the manuscript is a second copy of canon, and it develops the same continuity defects NSRES exists to remove. A generated codex cannot drift from the model, because it is a view of the model.
3. **Different readers need different truths.** The author needs everything. A beta reader at chapter 6 must not see chapter 14's reveal. A published fan wiki must show only what the released text delivered. The lens system (§16.3) gives each of them a correct, spoiler-safe view of one model.
4. **It is the human-interface layer.** In the MAPS three-layer split, the packet is internal state, the brief is external output, and the Codex is the human interface (§12.5).

### 16.2 Principles

| ID | Principle | Operational rule |
| --- | --- | --- |
| CX-1 | Projection only | Pages are views over one pinned model version. No page content is authoritative, and nothing reads facts back from a page. |
| CX-2 | Lens first | Every page renders through a declared lens. Non-author roles default to the most restrictive lens their permissions allow. |
| CX-3 | Edits are proposals | An edit made on a page creates a PROPOSAL against the underlying record field and shows which gate it routes to. |
| CX-4 | Version and status stamped | Every page shows its model version. Every fact shows its status (PROPOSAL, ACCEPTED, CANON, PUBLISHED) and, on request, its provenance and evidence. |
| CX-5 | Generated prose is labeled and disposable | LLM-written blurbs are AI-origin, regenerated each version, never cited as evidence, and never fed into packets. This prevents a circular second source of truth. |
| CX-6 | Spoiler safety is enforced by the engine | Lens filtering uses the same visibility classes and reader ledger as extraction (§7.5, L10). Page templates cannot override it. |
| CX-7 | Runs alongside the work | Regeneration is triggered by model commits and scoped by impact sets. It never blocks extraction or drafting. |

### 16.3 Epistemic lenses

| Lens | Shows | Filter | Typical audience |
| --- | --- | --- | --- |
| TRUTH | All of Story Reality: hidden events, secrets, sealed reveal plans, open findings | None | Author, showrunner |
| WORKING | ACCEPTED and CANON records, with PROPOSAL records as marked overlays | Status | Author during development |
| CANON\_ONLY | CANON records only | Status | Collaborators, licensing, adaptation teams |
| POV(c, t) | What character c knows at story-time t, and what c could perceive there | CIS(c, t) and perception rules | Author checking a scene; actors; voice work |
| READER(n) | What the reader holds at narrative position n, from RIS\_actual (RIS\_plan as a toggle) | RIS(n) and visibility classes | Editors, beta readers, the published fan wiki |
| BRANCH(b) | A canon branch's reality | Branch selection | What-if exploration; GVE counterfactuals |
| PRODUCTION(medium) | Visual canon: seeds, identity locks, continuity anchors | MAPS seed statuses | Illustrators; video production through the Beat Engine |

**READER-lens rules.**

1. A fact appears only if it is in RIS(n) with mode STATED or SHOWN. IMPLIED facts appear only if the work enables it. HINTED facts never appear as facts.
2. MISLED beliefs appear as the reader holds them, attributed to their source in the text ("according to the doctor, a failed heart"), with no truth label. A truth label would itself be a spoiler.
3. Structural elements are filtered too. A family tree must not render an empty father slot for Jonah, and a relationship graph must not draw an unlabeled edge between Jonah and Edmund. Empty slots and unlabeled edges can leak as surely as text (structural leak, rule CX-L1).

### 16.4 Modules

| Module | Function | Deterministic? | Reads | Writes |
| --- | --- | --- | --- | --- |
| CX-M1 Page Generator | Entity pages (character, location, object, group), event pages, thread pages, scene and chapter pages, from templates per kind | Yes | L1, L5–L9, L3 | Page cache |
| CX-M2 Timeline Renderer | Master chronicle by story-time; per-entity timelines; story order and narrative order side by side (fabula against syuzhet); feasible windows drawn as bands so uncertainty stays visible | Yes | L5, L6–L8, L3, L10 | Page cache |
| CX-M3 Graph Renderer | Relationship graph; Causal DAG explorer; thread convergence map; per-proposition propagation graph ("who knew what, when") | Yes | Projection graph (§10.7) | Page cache |
| CX-M4 Map Renderer | Schematic maps from canon adjacency and travel metrics (geographic when coordinates exist); occupancy scrubbable over story-time; movement paths per character | Yes | L1, L6, L7 | Page cache |
| CX-M5 Ledger Dashboards | Open findings; drift indices; confidence vectors; reveal schedule; setups and payoffs; open questions; micro-fact queue; gate queue | Yes | L10, L14, L15, C15, C19 | Page cache |
| CX-M6 Summary Writer | Short prose blurbs per page | No (LLM, AI-origin) | Lens-filtered input only | Page cache, labeled |
| CX-M7 Edit Bridge | Turns in-page edits into PROPOSAL records on source fields | Yes | Page context | PROPOSAL records |
| CX-M8 Export and Publish | Static site per lens; print bible (PDF); adapters for other worldbuilding tools where their formats allow | Yes | Page cache | Export artifacts |
| CX-M9 Visual Brief Bridge | Emits VISUAL-BRIEFs to the MAPS router (character sheets, maps, infographics); links canonical seeds on entity pages | Yes | Pages, MAPS seed library | VISUAL-BRIEF records |

**REQ-16.4.1.** CX-M6 receives only material inside the page's lens. A READER(n) blurb is written from READER(n) data, so the summary writer cannot leak what it was never given (the same reasoning as suppression by abstraction, §7.6).

### 16.5 Page anatomy: one entity, two lenses

Jonah Pell's page shows what the lens system changes.

| Page section | TRUTH lens | READER(1.03.2) lens |
| --- | --- | --- |
| Identity | Footman; Edmund Harrow's son (INF-004, CANON, hidden until 2.14) | Footman at Harrow House |
| Timeline, 14–15 Oct | Study 22:15–22:25 and 22:38–22:40; east corridor 22:45; hides the ledger in his room about 23:05 | Seen by Mara in the east corridor late on 14 Oct, carrying a cloth-wrapped bundle |
| Possessions | Study key (from 22:15); the ledger (22:40–23:05), then under his floorboard | — |
| Knowledge | Knows his parentage; knows Edmund wanted the ledger kept safe | — |
| Secrets held | INF-002, INF-004, with concealment strategy | — |
| Relationships | Son of Edmund (concealed); fellow servant of Mara | Fellow servant of Mara |
| Threads | THR-02 (secondary, hidden); THR-01 | THR-01 |
| Appearances in text | Every scene, with POV and beats | Scenes up to 1.03.2 only |
| Open findings and confidence | Shown | Not shown |

### 16.6 Data flow

1. A gate decision changes a record; the Version Store emits the impact set.
2. The Codex maps the impact set to affected pages, for every lens in use.
3. Affected pages regenerate; the cache key is (page, lens, model version).
4. Readers of a page see the newest version for their lens, with the version stamped.
5. An edit on a page goes through the Edit Bridge as a PROPOSAL, then through its gate; if approved, step 1 repeats.

### 16.7 Codex scores and publishing

| Score type | Factors | Use |
| --- | --- | --- |
| Codex Fidelity | Deterministic diff between each page's facts and the model at the stamped version | Any mismatch is a BLOCKING Codex defect |
| Lens Safety (hard cap) | No out-of-lens fact in text, structure, or blurb; a leak probe on READER pages before publication | Cap 0.84 below 0.95; a READER-lens publication cannot pass the SHIP gate under the cap |
| Freshness | Share of pages regenerated for the latest model version | Dashboards; stale pages are marked stale |

Publishing a READER-lens wiki is a public release, so it passes the SHIP gate like a chapter.

### 16.8 Integration

| System | Relationship |
| --- | --- |
| WCS production-bible-builder | Remains the authoring workflow for canon (through the CANON gate). The Codex renders its committed output; it does not replace it. |
| MAPS | PRODUCTION-lens pages carry seed constellations; CX-M9 sends character-sheet and map briefs to the router. |
| Beat Engine | Its Stage 0 Identity Sheet pulls anchors from PRODUCTION-lens pages, so video identity locks and prose canon share one source. |
| GVE | BRANCH-lens pages let the author browse a counterfactual before deciding on it. |

### 16.9 Risks

| Risk | Mitigation |
| --- | --- |
| Pages treated as truth (a second source) | CX-1 and CX-5: pages are never read back; blurbs are never evidence |
| Authors expect edited blurb text to persist | The Edit Bridge edits fields, not blurbs. Free-form author commentary lives in a non-factual notes field excluded from packets |
| Structural spoilers in graphs and trees | Rule CX-L1; leak probe on READER pages |
| Regeneration cost on large works | Impact-set scoping (CX-7); cache per (page, lens, version) |

**Status:** PROPOSAL. Module boundaries and lens definitions are Claude-generated design and need the author's STRUCTURE gate.

## 17. World Mechanics Engine (magic and story-world physics)

The World Mechanics Engine makes a story world's magic, technology, and physics a tracked system, with the same rigor NSRES applies to people, places, objects, and knowledge. Every working is an event that consumes something, obeys a registered mechanic, leaves residue, and can be checked. In-world physics is canon by the author's decision. The engine does not ask whether a mechanic is true of our universe, only whether the story applies it consistently.

### 17.1 What it tracks and why

Without this engine, magic is the largest unchecked source of continuity defects: costs paid once and then forgotten, powers that grow to fit the plot, effects that outlast their fuel, and climaxes solved by rules the reader never saw. The engine tracks five things:

1. **Mechanics:** the registered laws of each kind of working, specified on six axes.
2. **Resources:** every reserve, field, or material a working draws on, as a conserved or declared-source ledger.
3. **Effects:** every sustained working, as an interval with upkeep.
4. **Traces:** every residue or signature a working leaves, as a fact with decay and perceptibility. Traces feed knowledge (L9) and clues (L10).
5. **Capabilities:** what each practitioner can do, knows, and holds in reserve, over story-time.

**Prior art.** The three "laws of magic" widely cited among fantasy writers state: an author's ability to resolve conflict with magic depends on how well the reader understands it; limitations are more interesting than powers; and expanding existing magic is better than adding new magic. The engine makes each one checkable: MC-14, the cost and limit fields of every mechanic sheet, and MC-16.

### 17.2 Ontology kit: GSVT, UTED-EC, QMCP

The engine works with any physics an author defines. It ships with an optional ontology kit drawn from the author's own frameworks, because GSVT began as a worldbuilding exercise for fantasy magic systems.

| Kit concept | Source | Engine construct |
| --- | --- | --- |
| A substrate that workings act on (the Quantum Primordial Field and its Q-Modes) | UTED-EC, QMCP | **Substrate** record: the medium a mechanic draws on (field, current, mana, flux) |
| Stable effects arise from phase-lock; failed lock attempts dissolve | QMCP | **Lock condition** on each mechanic: what must cohere for the working to hold; failure modes when it does not |
| Energy and information are inseparable | UTED-EC | Every mechanic has an **energy cost** and an **information requirement** (a pattern the practitioner must know). The information requirement is a knowledge precondition checked against CIS (L9) |
| Coherence cascades occur at thresholds, not gradually | UTED-EC | **Threshold rules:** nonlinear cascade events when inputs cross a stated value |
| Manifestation Webs: nested regimes, each bound by its own informational thresholds | UTED-EC | **Regime** records: where and when a given set of laws holds, with interface zones between regimes |
| Determinism; apparent probability is occlusion of state | UTED-EC, GSVT | **Determinism rule:** the same inputs give the same outputs unless a declared occluded variable differs (MC-13) |
| Systemic drag: entropy as dissolution pressure from the containing system | GSVT | **Upkeep and decay:** sustained effects and stored reserves decay unless maintained |
| Six orthogonal load bearers (SI, EP, IS, FT, SR, DI) | GSVT (canonical lock) | The **six-axis mechanic sheet** (§17.3). Because the axes are orthogonal, each is specified independently |

**Version pinning (REQ-17.2.1).** A work that adopts the kit names the kit version in canon. Where kit documents disagree, the conflict is preserved and decided at the CANON gate, never silently. Known instance: an older UTED-EC text describes dark matter as semi-coherent, while QMCP canon gives it zero phase-lock; a February 2026 audit recommended the QMCP reading. A work whose mechanics depend on that point must pin one reading.

### 17.3 The mechanic sheet

Every mechanic is one canon record (MCH-) with the fields below. Fields may be UNDETERMINED or NOT\_APPLICABLE, but never silently empty. A scene that relies on an UNDETERMINED field triggers MC-17.

| Axis or field | Question it answers | Content | Checked by |
| --- | --- | --- | --- |
| **SI: identity** | What makes this mechanic this one and not another? What effect does it aim at (target identity) and what does a given working actually produce (operative identity)? | Name, class (innate, learned, ritual, technological, environmental), the defining effect, the lock condition | MC-01, MC-16 |
| **EP: boundary** | What can it touch, and what pressures oppose it? | Valid targets, range, line-of-sight rules, wards and counter-forces, regimes where it holds | MC-06, MC-07 |
| **IS: scaffolding** | What internal structure carries the load? | Stages, duration, interruptibility, required foci (objects), anchors (places), the practitioner's role, how load is shared among several practitioners | MC-02 |
| **FT: transduction** | How does energy and information cross from substrate into effect? | Inputs (resources, pattern knowledge, traits), the magnitude function, efficiency, scale limits | MC-03, MC-04, MC-10 |
| **SR: responsivity** | How does a working hold or fail under disturbance? | Control and correction, failure modes (backlash, partial effect, collapse), threshold cascades | MC-08 |
| **DI: reintegration** | What persists after the change, and how does the world absorb it? | Costs paid (reserve, fatigue, injury, irreversible), upkeep for sustained effects, residue traces with decay and perceptibility, aftermath | MC-05, MC-09, MC-15 |
| Hard limits | What can it never do? | Prohibitions (no resurrection; no action across regimes) | MC-12 |
| Interactions | How does it combine with other mechanics? | Row in the interaction matrix: amplifies, cancels, blocks, transmutes | MC-07 |
| Reader exposure | Which of its rules has the reader been shown? | Links to L10 delivery records per field | MC-14 |

### 17.4 Records

| Record | Holds | Layer |
| --- | --- | --- |
| Substrate (SUB-) | The medium; ambient level per location and time | L1, with state in L7 |
| Regime (RGM-) | Laws in force, scope (locations, story-time), interface zones, precedence | L1 |
| Mechanic (MCH-) | The mechanic sheet (§17.3) | L1 |
| Constant (MCC-) | Tunable values with units (rates, costs, thresholds) | L1 |
| Resource (RES-) | A reserve or field: owner or location, maximum, regeneration rule, decay, conservation class (CONSERVED, SOURCED, UNBOUNDED; must be declared) | L1, with ledger in L6, L7, L8 |
| Capability (CAP-) | Practitioner × mechanic: proficiency, affinity, known patterns, conditions that impair | L6 overlay, anchored to learning events |
| Working (event type WORKING) | Mechanic used, practitioners, inputs consumed, magnitude, outcome, traces emitted | L5 |
| Active effect (EFF-) | A sustained working: interval, upkeep rate, funding source, state | Derived from L5 |
| Trace (TRC-) | A residue fact: what, where, decay, who can perceive it and how | L9 fact |
| Artifact | An object with embedded mechanics, charges, and state | L8 |

**Effect-language extensions (§10.9).**

```ebnf
effect   += consume | sustain | release | emit_trace | cascade | learn ;
consume  = "consume(" resource "," amount ")" ;
sustain  = "sustain(" effect "," upkeep_per_hour "," funding_resource ")" ;
release  = "release(" effect ")" ;
emit_trace = "emit_trace(" trace "," location "," decay "," perceptibility ")" ;
cascade  = "cascade(" mechanic "," trigger "," outcome ")" ;
learn    = "learn(" entity "," pattern "," proficiency_delta ")" ;
predicate += "reserve(" resource ") >=" amount | "regime(" location ") includes" mechanic
           | "knows_pattern(" entity "," pattern ")" | "active(" effect ")" ;
```

### 17.5 Mechanics ledgers (derived)

| Ledger | Tracks | Conservation or consistency rule |
| --- | --- | --- |
| Resource ledger | Each reserve or field over story-time: regeneration, spend, decay | A CONSERVED or SOURCED balance never goes negative; every gain has a declared source |
| Effect ledger | Each active effect as an interval with upkeep and funding | An effect lasts only while funded; it ends by release, lapse, or counter-working |
| Trace ledger | Each residue with location, decay, perceptibility | A trace exists from its emitting working until its decay ends; anyone perceiving it gains a grant (WITNESSED, or DETECTED through a sensing mechanic) |
| Capability ledger | Each practitioner's proficiency and known patterns | Proficiency changes only through learning, injury, or other declared events |
| Regime map | Which laws hold where and when | A working is valid only where its regime includes the mechanic |

DETECTED is a new knowledge channel (§4, L9): a holder perceives a trace through a sensing mechanic, within that mechanic's range and preconditions.

### 17.6 Mechanics checks

| Code | Check | Detection | Default severity |
| --- | --- | --- | --- |
| MC-01 | Working cites no registered mechanic (magic from nowhere) | Event type WORKING without MCH | BLOCKING |
| MC-02 | Precondition failure: trait, focus, anchor, range, stage, or timing missing | Preconditions against state | BLOCKING |
| MC-03 | Conservation violation: negative balance, or a gain with no source | Resource ledger fold | BLOCKING |
| MC-04 | Magnitude exceeds the mechanic's magnitude function for the inputs | Function evaluation | BLOCKING; MAJOR within declared tolerance |
| MC-05 | Upkeep lapse: an effect persists past its funded duration | Effect ledger | MAJOR |
| MC-06 | Regime violation: a mechanic used where its laws do not hold | Regime map | BLOCKING |
| MC-07 | Interaction violation: incompatible effects coexist, or a cancel rule is ignored | Interaction matrix | BLOCKING |
| MC-08 | Threshold crossed with no cascade event | Threshold rules | MAJOR |
| MC-09 | Missing residue: a working that must leave a trace leaves none | DI field; trace ledger | MAJOR; trace proposed automatically |
| MC-10 | Pattern knowledge violation: a working uses a pattern the practitioner does not know | knows\_pattern against CIS (as RC-10) | BLOCKING |
| MC-11 | Capability discontinuity: proficiency jumps with no event | Capability ledger | MAJOR |
| MC-12 | Hard limit breached | Hard-limit rules | BLOCKING |
| MC-13 | Determinism: equal inputs, different outputs, with no declared occluded variable | Comparison across workings of one mechanic | MAJOR |
| MC-14 | Unearned resolution: a resolving beat relies on mechanic rules not in RIS (SHOWN or stronger) before the scene | Rules used, against L10 | MAJOR; BLOCKING in HARD works |
| MC-15 | Limit erosion: a cost or limit shown on page is later ignored | Autopsy against delivered rules | MAJOR |
| MC-16 | New power in prose: a capability not derivable from registered mechanics | Autopsy classification | MAJOR; becomes a mechanic PROPOSAL (never a FREE micro-fact) |
| MC-17 | A scene relies on an UNDETERMINED mechanic field | Packet compilation | BLOCKING at extraction |
| MC-18 | Kit version conflict: superseded kit definitions in use | Kit version against canon | MAJOR |

**Hardness setting.** A work declares SOFT, FIRM, or HARD mechanics. SOFT keeps hard limits, conservation, and consistency (MC-01 to MC-13, MC-15) but disables MC-14 and relaxes MC-13 to MINOR, for wonder-forward magic. FIRM is the default. HARD makes MC-14 BLOCKING and adds a Mechanics Integrity hard cap: below 0.95, scene acceptance readiness caps at 0.84.

### 17.7 Integration with the layers

| Layer or component | Addition |
| --- | --- |
| L1 | Substrates, regimes, mechanics, constants; locked at the CANON gate |
| L5 | WORKING events with the effect-language extensions |
| L6 | Capability and reserve tracks per practitioner |
| L7 | Regime and substrate state per location; traces present |
| L8 | Artifacts with embedded mechanics and charges |
| L9 | Pattern knowledge as propositions; traces as facts; the DETECTED channel |
| L10 | Reader exposure to each mechanic's rules (costs, limits, magnitudes), per field |
| L11 and L12 | Packet group N (below) |
| L14 and L15 | Autopsy codes AU-80 to AU-84 (below) |
| Codex (§16) | Mechanic pages, regime maps, resource charts, interaction matrix, all lens-filtered. The READER lens shows a mechanic only as far as the reader has been shown it |
| Confidence (§11.5) | Mechanics Integrity score type (MC findings), a hard cap in HARD works |
| Simulation (§12.9) | The engine evaluates workings deterministically, so it can propose offscreen workings and GVE counterfactuals ("what if she had bound two doors") |

**Packet group N: Mechanics.**

| Field | Purpose | Source | Validation |
| --- | --- | --- | --- |
| mechanics\_in\_play | Sheets for every mechanic used or active in the scene; public section limited to rules the drafter needs to render consistently | L1 | Hidden rules go to the sealed section or become manifestations |
| regime | Laws in force at the scene's location and time | L1 regime map | MC-06 |
| practitioner\_states | Reserves, proficiency, known patterns, impairments | L6 | MC-02, MC-10 |
| active\_effects | Sustained effects present, with remaining funded duration | Effect ledger | MC-05 |
| traces\_present | Residues in the scene and who can perceive them | Trace ledger | Perceptibility rules |
| mechanic\_constraints | LOCKED costs, limits, and magnitude bounds the prose must respect | Mechanic sheets | MC-04, MC-12, MC-15 |
| forbidden\_mechanic\_revelations | Rules the reader must not learn yet | L10 | As forbidden revelations |

**Autopsy codes.**

| Code | Failure | Severity |
| --- | --- | --- |
| AU-80 | Rendered effect does not match its mechanic (wrong magnitude, range, or target) | BLOCKING |
| AU-81 | Working rendered without a cost the packet requires to be shown | MAJOR |
| AU-82 | New capability in prose (MC-16) | MAJOR |
| AU-83 | Limit erosion (MC-15) | MAJOR |
| AU-84 | Prose explains a hidden mechanic rule | BLOCKING |

### 17.8 Worked example (invented world, illustrative)

**Canon.** RGM-001 the Drowned Provinces: Binding (MCH-001) and Shear (MCH-002) in force. RGM-002 the Saltmarsh: a null zone where no mechanics hold.

| MCH-001 Binding | Specification |
| --- | --- |
| SI | Phase-locks a target object to an anchor point; the target cannot move while the lock holds |
| EP | Targets: non-living objects only. Range: line of sight at casting. Holds only in RGM-001. Cancelled by Shear |
| IS | One practitioner; one minute of contact with the target beforehand to learn its pattern; casting takes 10 seconds |
| FT | Cost = 5 (small), 15 (medium), or 40 (large target) + 1 per metre of distance, drawn from the binder's reserve. Requires knows\_pattern(binder, target) |
| SR | The lock fails if the reserve reaches zero or a Shear working cuts it. Holding more than three bindings at once triggers a cascade: all locks fail |
| DI | Upkeep 2 per hour from the binder's reserve. No regeneration while sustaining. Residue: frost-rime on the anchor for 24 hours, visible to anyone and detectable by binders within 30 metres |
| Hard limits | Cannot bind a living creature |

**Practitioner.** CHR-101 Ilse Marr: reserve maximum 100, regenerating 5 per hour at rest; proficiency 2.

**Plan as first written.** SCN-212: Ilse binds the harbour gate (large, 20 metres away) at dusk. SCN-219, three days later in story-time, shows the gate still held while she sleeps at an inn.

**Reconciliation.**

1. Casting costs 40 + 20 = 60. Her reserve is 80, leaving 20. Valid.
2. Upkeep is 2 per hour with no regeneration, so 20 units fund 10 hours. The lock lapses about 10 hours after casting. SCN-219 renders an effect past its funded duration: **MC-05 upkeep lapse**.
3. The engine generates candidate repairs: a second binder takes over the lock (bridge event); an artifact anchor with stored charge (new object); the gate held for one night only (scene change); or a lower upkeep constant (canon change, whose impact set lists every scene relying on upkeep).
4. Separately, the climax (SCN-240) has Ilse bind a pursuer's horse. **MC-12 hard limit** (living creature) and, because the reader has seen the limit stated at 1.04.2, **MC-15 limit erosion** in the plan. Repairs: bind the cart instead, or a revelation scene that legitimately changes the limit, which itself becomes a reveal with prerequisites.

### 17.9 Evidence notes

| Item | Evidence label | Note |
| --- | --- | --- |
| UTED-EC concepts (substrate, Q-Modes, energy and information, threshold cascades, Manifestation Webs, determinism) | FOUND\_BY\_SNIPPET (past chats, March 2025 to February 2026) | Full UTED-EC v3.1 text not read this session: GAP\_IDENTIFIED |
| QMCP phase-lock filtering; dark matter as zero phase-lock | FOUND\_BY\_SNIPPET (February 2026 audit) | Conflict with the older UTED-EC wording preserved (REQ-17.2.1) |
| GSVT origin in magic-system worldbuilding | FOUND\_BY\_SNIPPET and memory | Supports the fit of SLB axes to mechanic sheets; does not prove it (claim C18) |
| Older SLB vocabulary (FP, CD, II, EI) in past chats | FOUND\_BY\_SNIPPET | Superseded by the canonical lock; not used here |

**Status:** PROPOSAL. A natural first real application is a work whose magic already derives from these frameworks; its canon would need to be read in full (CONTENT\_READ) before any mechanic sheet is written from it.

## Appendix A. Worked example: Harrow House, 14–15 October 1893

One scene, SCN-007, traced end to end: canon, events, four contradictions found and resolved, derived state, extraction, a first draft that fails, its findings and scores, the regenerated draft that passes, and the gate decisions. All scores were computed with the factorized confidence calculator, not estimated. The inputs are illustrative example data.

### A.1 Canon (excerpt)

| Handle | Class | Statement |
| --- | --- | --- |
| CAN-003 | INVARIANT | The dead do not act |
| CAN-014 | WORLD RULE | No telephone at Harrow House; telegraph only at Kellby station |
| CAN-030 | DEFAULT | The study is locked at night; its key hangs on the servants' hall board |
| CAN-041 | METRIC (perceptibility) | Voices in the study are audible in the east corridor |
| CAN-052 | DEFAULT (routine) | Servants are in the servants' quarters from 23:00 to 05:30 unless an event says otherwise |
| CAN-060 | METRIC (timetable) | First train York to Kellby: departs 07:20, arrives 09:05 |
| CAN-061 | METRIC (travel) | Harrow House to The Bell: 20 minutes by carriage. Kellby station to Harrow House: 25 minutes by carriage |
| CHR-002 | ENTITY | Teodor Hale, inspector, York City Police; walks with a cane |

### A.2 Truth Timeline (excerpt)

| Handle | Story-time | Location | Event | Key effects | Visibility |
| --- | --- | --- | --- | --- | --- |
| EVT-0090 | 13 Oct, afternoon | LOC-002 The Bell | Hale takes lodgings on another inquiry | Presence | REVEALABLE (bridge, RES-0011) |
| EVT-0097 | 14 Oct 19:30 | Servants' hall | Edmund takes the study key from the board | transfer(OBJ-002, board, Edmund) | AMBIENT (bridge, RES-0016) |
| EVT-0101 | 14 Oct 20:50 ±20 min | Study | Celia doses the decanter | set(OBJ-003.poisoned, true) | HIDDEN\_UNTIL RVL-05 |
| EVT-0102 | 21:30 | Study | Edmund drinks from the decanter | INF-001 becomes TRUE | HIDDEN\_UNTIL RVL-01 |
| EVT-0103 | 22:15–22:25 | Study | Edmund, unwell, gives Jonah the key and asks him to keep the ledger safe | transfer(OBJ-002, Edmund, Jonah); grant(Jonah, INF-011, TOLD) | HIDDEN\_UNTIL RVL-02 |
| EVT-0104 | 22:38–22:40 | Study | Jonah removes the ledger and locks the study | transfer(OBJ-001, study, Jonah); set(LOC-001a.lock, LOCKED) | HIDDEN\_UNTIL RVL-02 |
| EVT-0106 | 22:43–22:48 (after EVT-0104 by 3–10 min) | East corridor | Mara sees Jonah carrying a bundle | grant(Mara, INF-006, WITNESSED) | REVEALABLE (shown at 1.03.2) |
| EVT-0107 | about 23:05 | Jonah's room | Jonah hides the ledger under a floorboard | transfer(OBJ-001, Jonah, LOC-001f) | HIDDEN\_UNTIL RVL-02 |
| EVT-0108 | 23:30 ±30 min | Edmund's bedroom | Edmund dies | set(CHR-003.alive, false) | REVEALABLE |
| EVT-0105 | 15 Oct 06:10 ±5 min | Edmund's bedroom | Mara finds Edmund dead | grant(Mara, INF-009, WITNESSED) | SHOWN at 1.02.1 |
| EVT-0109 | 07:05–07:25 | The Bell to Harrow House | The constable fetches Hale | Presence | SHOWN at 1.03.1 |
| EVT-0112 | 07:40–08:10 | Servants' hall | Hale questions the household | grant(Hale, INF-010, INFERRED, SUSPECTED) | SHOWN at 1.03.2 |
| EVT-0113 | 08:15–08:25 | Study | The study door is forced on Hale's order | set(LOC-001a.lock, BROKEN) | SHOWN at 1.03.3 (bridge, RES-0015) |
| EVT-0114 | 09:30 | Study | Hale finds residue in the decanter | INF-007 trace; grant(Hale, INF-001, INFERRED, SUSPECTED) | SHOWN at 1.04.1 (bridge, RES-0014) |
| EVT-0131 | 16 Oct 14:00 | The Bell | Hale reads the chemist's report | grant(Hale, INF-001, READ, CERTAIN) | SHOWN at 1.09.3 |

### A.3 First reconciliation: contradictions found and resolved

| Finding | Rule | What was wrong | Repair chosen | Resolution |
| --- | --- | --- | --- | --- |
| FND-R-01 | RC-08 impossible movement | The outline had Hale arrive from York at 07:40 after a 07:00 telegram; by CAN-060 and CAN-061 the earliest arrival is 09:30 | Bridge: Hale already at The Bell (EVT-0090); the constable fetches him (EVT-0109). The lifted event "Hale arrives from York" is DEPRECATED | RES-0011 |
| FND-R-02 | RC-10 premature knowledge | A beat had Hale say "the brandy was poisoned" at 10:00 on 15 Oct; his only grant was READ on 16 Oct | Bridge EVT-0114 (residue, INFERRED, SUSPECTED); the beat now shows suspicion, not certainty | RES-0014 |
| FND-R-03 | RC-13 access violation | Hale enters the locked study at 08:15 with no key and no access event | Bridge EVT-0113: the door is forced | RES-0015 |
| FND-R-04 | RC-04 precondition failure | EVT-0103 transfers the key from Edmund, but CAN-030 puts the key on the board | Bridge EVT-0097: Edmund takes the key at 19:30 | RES-0016 |

All four bridges entered as PROPOSAL records, were dry-run, and were accepted at the INTEGRATION gate; truth@r47 reconciled CONSISTENT.

### A.4 Derived state at SCN-007 entry (07:40, 15 Oct)

| Query | Result |
| --- | --- |
| OBJ-001 ledger custody | Under the floorboard in Jonah's room since about 23:05 |
| OBJ-002 study key custody | Jonah, since 22:15 |
| LOC-001a study | Locked since 22:40 |
| CIS(Mara, 07:40) | INF-006 (CERTAIN, WITNESSED); INF-009 (CERTAIN). Not INF-001, INF-002, INF-004, INF-005 |
| CIS(Hale, 07:40) | Death unexplained; nothing on poison yet |
| RIS(1.03.1) | INF-009 SHOWN at 1.02.1; "his heart failed" MISLED at 1.02.1; Hale arrived from The Bell, SHOWN at 1.03.1 |

### A.5 Extraction of SCN-007

| Fact | Visibility classes | Packet treatment |
| --- | --- | --- |
| INF-006 Mara saw Jonah with a bundle | REVEAL\_NOW (SHOWN); known to the POV | known\_information; required outcome |
| INF-008 key missing from the board | HINT (explicitness 2); PERCEIVABLE | permitted\_hints; PLANT beat BT-007-02 |
| INF-002 Jonah removed the ledger | SUPPRESSED; FORBIDDEN | SUP-1 manifestation; sealed |
| INF-004 Jonah is Edmund's son | SUPPRESSED; FORBIDDEN | SUP-2 manifestation; sealed |
| INF-001, INF-005 | FORBIDDEN (not active in onscreen behavior) | Sealed only |
| INF-009 Edmund found dead | ALREADY\_KNOWN | reader\_known |
| Study locked; Hale's cane; York City Police | LOCKED continuity | continuity\_constraints |

The resulting packet is PKT-007-r3 (§8.4). Its readiness vector:

| Factor | Weight | Raw | Evidence |
| --- | --- | --- | --- |
| pre\_draft\_checks | 0.35 | 1.00 | CC-1 to CC-10 all PASS |
| source\_coverage | 0.20 | 1.00 | Sources map covers every non-empty field |
| leak\_probe\_margin | 0.20 | 1.00 | Pre-draft probe 0.08 and 0.11, both at or below 0.125 |
| dependency\_resolution | 0.15 | 0.75 | DEPENDENCY:SCN-006; a prerequisite is in RIS\_plan only |
| budget\_fit | 0.10 | 1.00 | Mandatory content within budget |
| **Result** |  | **0.96** | READY; frozen at the STRUCTURE gate |

### A.6 First draft, DRF-007-01 (excerpt, illustrative)

> &#91;S1\] The servants' hall smelled of coal smoke and cold tea, and the grey light from the high windows made everyone look older than they were. \[S2\] Inspector Hale of Scotland Yard stood at the head of the table, his weight on his cane. \[S3\] "I'll ask each of you where you were last night," he said. "Plainly, if you please." \[S4\] Mara's gaze went past him to the key board on the east wall. The hook where the study key hung every night was empty. \[S5\] She had come down the east corridor at a quarter to eleven and seen Jonah ahead of her, a bundle in his arms wrapped in a cloth, the size and weight of the ledger from his lordship's desk. \[S6\] Across the table Jonah kept his eyes on his cup. \[S7\] "Did you see anyone abroad, Mrs. Voss?" \[S8\] "No one, sir." Her candle had burned down to a stub on the dresser behind her. \[S9\] Hale looked at her a moment longer than courtesy allowed, then nodded as though he had written something down.

### A.7 Findings on DRF-007-01

| Finding | Span | Rules | Severity | Cause | Note |
| --- | --- | --- | --- | --- | --- |
| FND-007-01-01 | S2 "of Scotland Yard" | AU-02; forbidden term | BLOCKING | DRAFTER\_VIOLATION | The packet locked "York City Police" and forbade "Scotland Yard" |
| FND-007-01-02 | S5 "the size and weight of the ledger…" | AU-34 (MAJOR); AU-31 "ledger" (MAJOR); AU-32 probe on INF-002 rose from 0.08 to 0.61 (BLOCKING) | BLOCKING | DRAFTER\_VIOLATION | Mara could make this comparison in character, because she has seen the ledger on the desk. The violation is reader-side, so it is a leak finding, not an information-state finding |
| FND-007-01-03 | S8 "Her candle… on the dresser" | AU-04 micro-fact; AU-60 undeclared | INFO; MINOR | — | Goes to the CANON gate |
| FND-007-01-04 | S5 "at a quarter to eleven" | Temporal check: inside the EVT-0106 window | INFO | — | On acceptance, collapses the window to 22:45 (REQ-6.3.1) |
| FND-007-01-05 | S9 Hale's look | Required outcome delivered by implication only | INFO | — | INFERRED evidence (0.50) on required\_outcomes |

### A.8 Scores

| Score type | DRF-007-01 | DRF-007-02 |
| --- | --- | --- |
| Continuity Integrity | 0.94 | 0.99 |
| Information-State Integrity | 0.98 | 0.98 |
| Leak Safety (hard cap) | 0.64 | 0.98 |
| Plan Alignment | 0.90 | 0.90 |
| Reconcile (hard cap) | 0.94 | 0.97 |
| Weighted aggregate before caps | 0.90 | 0.96 |
| Cap conditions triggered | Leak Safety (0.84); Reconcile (0.84); open BLOCKING (0.69) | None |
| **Acceptance readiness R** | **0.69, UNSTABLE** | **0.96, READY** |

The weighted aggregate for DRF-007-01 is 0.90, which an average alone would place in PROVISIONAL. The caps exist so that a leak and a canon violation cannot be averaged away. The binding cap is the open-BLOCKING cap at 0.69, and improving any other factor changes nothing until both BLOCKING findings clear.

### A.9 Decisions and resulting state

1. **DRF-007-01:** FAILED at L14 (lexical and leak suites); UNSTABLE band; regenerated automatically once (tier A2). Root cause for both BLOCKING findings: DRAFTER\_VIOLATION, since the brief already held both constraints.
2. **DRF-007-02:** S2 reads "Inspector Hale" with no affiliation; S5 ends at "a bundle in his arms, wrapped in a cloth". R = 0.96, READY. Accepted at the INTEGRATION gate; the reviewer confirmed that S9 delivers Hale's suspicion, upgrading that outcome's evidence from INFERRED.
3. **Micro-fact:** the candle stub on the dresser was decided ACCEPT\_AND\_REGISTER at the CANON gate and registered as OBJ-012. Later packets treat it as LOCKED wherever the dresser appears.
4. **Window collapse:** EVT-0106 start fixed at 22:45 through the CANON gate.
5. **RIS\_actual updated** from 1.03.2: +INF-006 (SHOWN), +INF-008 (HINTED), Q-03 opened.
6. **Propagation:** the SCN-008 packet re-checked against the new RIS\_actual; no change needed. The Codex regenerated Jonah's READER(1.03.2) page (§16.5).

## Appendix B. Rule catalog and machine-readable schemas

Every rule family in this specification, with where it is defined and how it runs, followed by the Rule Registry record format and schemas for the packet and the finding record.

### B.1 Rule family index

| Family | Codes | Defined in | Runs in | Method |
| --- | --- | --- | --- | --- |
| Design principles | P1–P10 | §1.5 | All | Design constraints |
| Requirements | REQ-3.6.1; REQ-L8.1; REQ-L13.1; REQ-L14.1; REQ-4.18.1; REQ-5.4.1 to 5.4.4; REQ-6.3.1; REQ-6.9.1; REQ-6.14.1; REQ-7.1.1; REQ-9.1.1; REQ-9.1.2; REQ-9.6.1; REQ-11.2.1; REQ-11.3.1; REQ-11.4.1 and 11.4.2; REQ-11.5.1; REQ-12.2.1; REQ-16.4.1; REQ-17.2.1 | Throughout | All | Conformance |
| Reconciliation contradictions | RC-01 to RC-17 | §6.11 | C8 | Deterministic |
| Selection | SR-1 to SR-10 | §7.3 | C9 | Deterministic |
| POV | PV-1 to PV-6 | §7.4 | C9, C13, C14 | Deterministic, plus LLM classification of interiority |
| Visibility | VR-1 to VR-4 | §7.5 | C9 | Deterministic |
| Suppression | SU-1 to SU-6 | §7.6 | C9 | Deterministic, plus LLM wording and probe |
| Reveal | RV-1 to RV-5 | §7.7 | C9 | Deterministic |
| Pre-draft checks | CC-1 to CC-10 | §7.10 | C9, C10 | Deterministic, plus probe (CC-7) |
| Extraction errors | EX-01 to EX-07 | §7.11 | C9 | Deterministic |
| Packet cross-field | PK-1 to PK-10 | §8.3 | C10 | Deterministic |
| Autopsy | AU-01 to AU-70; AU-80 to AU-84 | §9.3; §17.7 | C13, C14 | Mixed: span-verified LLM extraction, deterministic comparison, probes |
| Drift indices | DI-1 to DI-5 | §9.4 | C14 | Computed series |
| Mandatory validation points | V1 to V10 | §11.6 | C15 | Gate preconditions |
| Integration contract | IN-1 to IN-5 | §12.1 | C12, C15 | Conformance |
| Editorial (advisory) | ED-01 to ED-04 | §12.3 | C14 | LLM, advisory only |
| Codex | CX-1 to CX-7; CX-L1 | §16.2, §16.3 | Codex modules | Deterministic, plus probe on READER pages |
| World mechanics | MC-01 to MC-18 | §17.6 | C8, C9, C14 | Deterministic |
| Failure modes, open problems, claims | FM-01 to FM-14; OP-1 to OP-8; C1 to C19 | §13; §15 | Review | Human |

### B.2 Rule Registry record format

Every executable rule is a versioned registry record. Changing severity, logic, or thresholds is a control-plane change (REQ-11.2.1, item 7).

```yaml
rule_id: RC-08
name: Impossible movement
version: 1.0.0
layer: L6
family: reconciliation
severity:
  certain: BLOCKING
  possible: TIGHTEN            # adds a constraint instead of raising a finding
inputs: [presence_segments, travel_metrics, transport_modes, timetables]
logic_ref: rules/rc08_movement.dl   # Datalog-style source (§10.11)
message: "{character} cannot reach {to_location} by {latest_arrival} from {from_location}; minimum travel {tau} min."
repair_hints: [move_event, widen_window, add_bridge_event, change_transport_mode]
uncheckable_when: [missing_travel_metric]
evidence_required: CONTENT_READ
config_version: cp-2026.10.1
```

### B.3 Scene packet schema (JSON Schema, written in YAML)

Top-level structure and required fields. Field-level detail is in §8.2.

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "nsres/scene-packet/0.1.0"
type: object
required: [packet_uuid, packet_handle, schema_version, scene_ref, model_version,
           extraction_run, packet_hash, public_hash, status, public, sealed,
           validation, sources_ref, exclusions_ref]
properties:
  packet_uuid:   { type: string, format: uuid }
  packet_handle: { type: string, pattern: "^PKT-[0-9]{3,}-r[0-9]+$" }
  schema_version: { type: string, pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
  scene_ref:     { type: string, pattern: "^SCN-[0-9]{3,}$" }
  model_version: { type: string }
  extraction_run: { type: string, pattern: "^RUN-X-[0-9]+$" }
  packet_hash:   { type: string, pattern: "^sha256:[0-9a-f]{64}$" }
  public_hash:   { type: string, pattern: "^sha256:[0-9a-f]{64}$" }
  status: { enum: [EXTRACTED, PACKET_VALID, FROZEN, STALE] }
  flags:
    type: array
    items: { type: string, pattern: "^(PLAN_ONLY|CHEAT_RISK|INFORMED_DRAFTING|DEPENDENCY:SCN-[0-9]{3,})$" }
  gate_record: { $ref: "#/$defs/gate_record" }
  confidence_vector_ref: { type: string }
  public:
    type: object
    required: [position, setting, pov, threads, required_beats, character_states,
               information, constraints, outcomes]
    properties:
      position:         { $ref: "#/$defs/position" }
      setting:          { $ref: "#/$defs/setting" }
      pov:              { $ref: "#/$defs/pov" }
      threads:          { $ref: "#/$defs/threads" }
      required_beats:   { type: array, minItems: 1, items: { $ref: "#/$defs/beat" } }
      optional_beats:   { type: array, items: { $ref: "#/$defs/beat" } }
      character_states: { type: array, minItems: 1, items: { $ref: "#/$defs/character_state" } }
      information:      { $ref: "#/$defs/information" }
      emotion:          { type: object }
      constraints:      { $ref: "#/$defs/constraints" }
      outcomes:         { $ref: "#/$defs/outcomes" }
      mechanics:        { $ref: "#/$defs/mechanics" }   # group N, when mechanics are in play
  sealed:
    type: object
    required: [suppressed, forbidden_propositions]
    properties:
      suppressed:            { type: object, additionalProperties: { type: string, pattern: "^INF-[0-9]+$" } }
      forbidden_propositions: { type: array, items: { type: string, pattern: "^INF-[0-9]+$" } }
      leak_indicators:       { type: object, additionalProperties: { type: array, items: { type: string } } }
  validation:
    type: object
    required: [pre_draft_checks, autopsy_targets]
    properties:
      pre_draft_checks: { enum: [ALL_PASS] }   # a packet with any failure is never stored as PACKET_VALID
      leak_probe_results:
        type: array
        items:
          type: object
          required: [sup, score, threshold]
          properties:
            sup: { type: string }
            score: { type: number, minimum: 0, maximum: 1 }
            threshold: { type: number, minimum: 0, maximum: 1 }
      autopsy_targets: { type: array, items: { type: string } }
  sources_ref:    { type: string }
  exclusions_ref: { type: string }
$defs:
  beat:
    type: object
    required: [beat, type, actors, outcome]
    properties:
      beat: { type: string, pattern: "^BT-[0-9]{3,}-[0-9]{2,}$" }
      type: { enum: [ACTION, EXCHANGE, PERCEPTION, REVELATION, DECISION, REVERSAL,
                     INTERIOR, TRANSITION, PLANT, PAYOFF, SUSTAIN] }
      actors: { type: array, minItems: 1, items: { type: string } }
      outcome: { type: string, minLength: 1 }
      events: { type: array, items: { type: string } }
      plants: { type: string }
  manifestation:
    type: object
    required: [actor, behavior, intensity, permitted_explanation, forbidden_explanations]
    properties:
      actor: { type: string }
      behavior: { type: string }
      intensity: { type: integer, minimum: 1, maximum: 3 }
      permitted_explanation: { type: string }
      forbidden_explanations: { type: array, items: { type: string } }
  # position, setting, pov, threads, character_state, information, constraints,
  # outcomes, mechanics, and gate_record follow §8.2 and §17.7 field by field.
```

### B.4 Finding record schema

```yaml
$id: "nsres/finding/0.1.0"
type: object
required: [uuid, handle, rule, severity, evidence, detection_confidence, records, status]
properties:
  uuid:     { type: string, format: uuid }
  handle:   { type: string, pattern: "^FND-" }
  rule:     { type: string, pattern: "^(RC|CC|PK|EX|AU|MC|CX|ED)-?[A-Z0-9-]+$" }
  severity: { enum: [BLOCKING, MAJOR, MINOR, INFO] }
  spans:
    type: array
    items:
      type: object
      required: [draft, start, end, quote]
      properties:
        draft: { type: string }
        start: { type: integer, minimum: 0 }
        end:   { type: integer, minimum: 0 }
        quote: { type: string, minLength: 1 }   # must match the draft text exactly (span check)
  records:  { type: array, minItems: 1, items: { type: string } }
  evidence: { enum: [CONTENT_READ, FOUND_BY_SNIPPET, FOUND_BY_METADATA, CLAIM_INFERRED] }
  detection_confidence: { type: number, minimum: 0, maximum: 1 }
  cause: { enum: [MODEL_GAP, MODEL_ERROR, PACKET_ERROR, BRIEF_ERROR, DRAFTER_VIOLATION, DETECTOR_ERROR] }
  repairs: { type: array, items: { type: string } }
  status: { enum: [OPEN, RESOLVED, WAIVED_BY_OVERRIDE, DETECTOR_ERROR] }
allOf:
  - if: { properties: { severity: { const: BLOCKING } } }
    then: { properties: { evidence: { const: CONTENT_READ } } }   # REQ-9.1.1
  - if: { properties: { status: { const: WAIVED_BY_OVERRIDE } }, required: [status] }
    then: { properties: { severity: { enum: [MAJOR, MINOR, INFO] } } }   # REQ-9.1.2
```

The two allOf clauses encode REQ-9.1.1 and REQ-9.1.2 in the schema itself: a BLOCKING finding without CONTENT\_READ evidence fails validation, and so does a waived BLOCKING finding.
