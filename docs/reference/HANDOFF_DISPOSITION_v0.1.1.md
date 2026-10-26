# Disposition ledger: peer handoff "NSRES v0.1.1 Control-Plane Alignment & Build Hardening"

**Status:** claims-critic review. Advisory only; Patrick gates every adoption.
**Reviewer:** this session, 2026-10-25.
**Spec revisions:** reviewed at NSRES-SPEC rev 110; verified fixes applied in rev 111 to 119 (§0.8 of the spec lists them).
**Standing of the handoff itself:** TESTIMONY_ONLY. Another model's reading of sources is a claim to check, not evidence.

---

## 0. Coverage statement (what this review read)

| Source | Label | Notes |
| --- | --- | --- |
| Handoff proposal (`d71dff00-attachment.txt`) | CONTENT_READ | All 142 lines |
| NSRES-SPEC rev 110: §0.3, §0.7, §2.4 CIS row, L9 channel table, §6 channel table, §6.8, §10.2, §12.2, §12.3, §15.3, B.3, B.4, REQ-11.5.1 | CONTENT_READ | Targeted reads, not the whole document |
| WCS `modules.json` 1.0-runtime, 37,499 bytes (newest) | CONTENT_READ | 23 entries; saved as `reference/wcs/modules.json` (sha256 `f5516638d7a4932e…`) |
| WCS `modules.json`, 37,480 bytes (three identical copies) | CONTENT_READ | Full diff against the newest: one line, `"assign genre"` added to story-spark-capture's forbidden moves |
| `showrunner_production_handler.py` | CONTENT_READ | Whole file: paths, both enums, dataclasses, SAVE cycle, stubs |
| `PROJECT_FULL_EXPLICATION` (75- copy, 12,384 bytes; all copies the same size) | CONTENT_READ | 4 layers, 11 states, 8 gates, module families by phase |
| `SKILL_MODULES_AND_GOAL_EXPLAINED.md` | CONTENT_READ | Older (2026-06-04): 3 layers, 8 states |
| All 23 module sources in `module_sources/` plus `INDEX.txt` | CONTENT_READ | Every file in full |
| `65-spark-rewrite-triage.txt.md` (5,263 bytes, newest mtime) | CONTENT_READ | A format-stripped export (output-format blocks and the runtime contract are missing). Newer mtime, not a newer version |
| Other numbered `.txt.md` and `generated-skills/` copies | FOUND_BY_METADATA | Size-matched to `module_sources/` or older; not diffed (GAP_IDENTIFIED, low risk) |
| `DRIVEREORG_INTEGRATION_EXHAUSTIVE_ANALYSIS.md` | FOUND_BY_METADATA | Exists (17,400 bytes). Not read; no handoff claim depends on it |
| SPL-CORE v0 glossary | NOT_FOUND | Not searched for or read; needed only for claim H-09 |

---

## 1. Disposition of every handoff claim and patch

| ID | Handoff claim or patch | Claim type | Disposition | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| H-01 | Patch 2: §6.8 heading is malformed | Factual (spec text) | **VERIFIED** | Rev 110 block `.94591` read: heading text "6.8 Keeping hidden events hidde" fused with the bold "Hidden is not absent." paragraph | Applied (rev 111–112) |
| H-02 | Patch 3: `SUSTAIN` missing from the §10.2 `Beat` union | Factual (spec text) | **VERIFIED** | §10.2 code block read; SUSTAIN present in DEF-25, the L4 beat table, and B.3 | Applied. The same kind of drift also hit `DETECTED` and `Finding.status` (N-02, N-03), which the handoff missed |
| H-03 | §12.2 omits spark-rewrite-triage | Factual (coverage) | **VERIFIED** | The table covered 21 modules (two rows merged pairs), plus the handler in prose: 22 of 23 | Applied: table rebuilt with all 23 |
| H-04 | Three modules are in the wrong phase (scene-performance-director, sandbox-slush-pile, one unnamed) | Factual (mapping) | **PARTIAL** | Both named errors are real against `modules.json`. The true count is four: advanced-camera-pov (IV → V) and diegetic-document-weaver (IV → V) were also wrong. The handoff also missed nine default-gate mismatches and ten artifact-name mismatches | Applied: every phase, artifact, and default gate now copied from `modules.json`; the NSRES gate kept in its own column |
| H-05 | (Implied) the phases in the corpus architecture summary are wrong | Conflict between sources | **CONFLICT PRESERVED, resolved for the spec** | The corpus summary (`attachment-06864e15.txt`) put sandbox-slush-pile in Phase I and scene-performance-director in Phase V. `modules.json`, the handler's module source, the explication, and the goal document all agree with each other and disagree with the summary | Spec follows `modules.json`. The summary is recorded as stale on these two placements. Verified by: four WCS sources agree |
| H-06 | Patch 1: 8-gate and 11-state crosswalk | Mapping | **PARTIAL** | See §1a below | Applied in corrected form to spec §0.7, marked PROPOSAL |
| H-07 | Patch 4: fully expanded B.3 `$defs` | Deliverable | **REJECTED (not delivered)** | The patch body says it is "available in the working memory buffer." The handoff's own counts disagree: "10 core sub-schemas," then "12 expanded," then a list of 14 names, two of which (`beat`, `manifestation`) B.3 already writes out | Nothing applied. Writing the `$defs` is WP-010 in the build plan |
| H-08 | Interrogation B: the ID regexes constrain IDs correctly | Factual (patterns) | **PARTIAL** | `^PKT-[0-9]{3,}-r[0-9]+$` is in B.3 and matches the §0.3 example. The CHR and LOC patterns fit §0.3's examples (CHR-001, LOC-001a). But §0.3 prefixes use different digit widths (EVT-0104, THR-02, NOD-02-03, Q-03), so no single width rule fits | WP-010 derives one pattern per prefix from §0.3 and tests each example |
| H-09 | MC-18 conflicts with the SPL-CORE v0 glossary | Cross-spec factual | **NSRES side VERIFIED; SPL-CORE side UNVERIFIED** | NSRES defines MC-18 (§17.6, B.1) and never references SPL-CORE. The SPL-CORE glossary was not read | No NSRES change. If true, the fix belongs in SPL-CORE |
| H-10 | Readiness rises to 0.8625 PROVISIONAL, "eligible for the §14 pilot" | Score claim | **REJECTED** | See §1b below | Spec §15.3 rescored with this session's evidence: **0.80, INSUFFICIENT** |
| H-11 | The handoff read four Drive files including the DriveReorg analysis | Provenance | **3 of 4 confirmed by this session's own reads; 1 FOUND_BY_METADATA** | The DriveReorg analysis exists but was not read | None needed |

### 1a. Patch 1, row by row

| WCS term | Handoff mapping | Disposition | Why |
| --- | --- | --- | --- |
| INTAKE_GATE | NSRES PROPOSAL gate ("intake pre-check") | **REJECTED** | INTAKE_GATE approves classification of RAW into INTAKE. NSRES never reads RAW or INTAKE material, so it has no counterpart. Mapping it to PROPOSAL blurs exactly the RAW-preservation line the handoff's own interrogation point A worried about. My own §12.2 sentence ("the intake side of the PROPOSAL gate") had the same blur and was rewritten |
| PROPOSAL_GATE | PROPOSAL gate | **VERIFIED** | The path `03_ACCEPTED/working/` is UNVERIFIED (the handler config shows only `03_ACCEPTED`) |
| REVISION_GATE | PROPOSAL gate, revision pass | **VERIFIED** | Module contracts: a REVISED_PROPOSAL whose normal gate is PROPOSAL_GATE requests REVISION_GATE instead |
| STRUCTURE_GATE | STRUCTURE gate | **VERIFIED, with a missed conflict** | In WCS this gate produces CANON-state telling artifacts; NSRES telling records top out at ACCEPTED (finding N-01) |
| CANON_GATE | CANON gate, never batched | **VERIFIED** | production-bible-builder: `each_canon_candidate_requires_gate` |
| INTEGRATION_GATE | INTEGRATION gate | **VERIFIED** | The path `03_ACCEPTED/integrated/` is UNVERIFIED |
| DELETE_GATE | PROPOSAL or CANON gate, REJECT or SLUSH | **PARTIAL** | DELETE_GATE is for rejection only (explication: "explicitly reject while preserving evidence"). SLUSH is an ordinary gate decision, not a delete. The subfolders `06_SLUSH/rejected/`, `maybe_later/`, `strong_wrong_project` are UNVERIFIED |
| SHIP_GATE | SHIP gate, PUBLISHED tier, package snapshot | **VERIFIED** | `snapshot_on_ship` is in `modules.json`. The path `09_EXPORTS/package_snapshots/` is UNVERIFIED; `09_EXPORTS` appears in module texts but not in the handler's path config |
| SUPERSEDED, FORK | DEPRECATED; canon branch (§12.8) | **VERIFIED** mapping | The path `04_CANON/_SUPERSEDED/` is UNVERIFIED |
| (missing) RAW, INTAKE, ACCEPTED, CANON, REJECTED, SHIP state rows; the 8 gate decisions | none | **GAP** | Added in the corrected §0.7 crosswalk, including how ACCEPT_AS_CANON, REDIRECT, and REVERT map |

### 1b. Why 0.8625 does not stand

The arithmetic is correct: 0.25 × 0.90 + 0.20 × 0.95 + 0.20 × 1.00 + 0.15 × 0.85 + 0.20 × 0.60 = 0.8625. The inputs are the problem. Each test below was run with the factorized calculator (`reference/spec_readiness_v0.1.1.json` holds this session's vector).

| Test | Result |
| --- | --- |
| A. The handoff's vector exactly as claimed | 0.8625, no cap (0.85 is not below 0.85) |
| B. The same, but buildability without credit for the undelivered Patch 4 (0.85, its evidenced value) | **0.8325, INSUFFICIENT** |
| C. The same as A, with integration grounding one point lower (0.84) | Base 0.8610, **capped at 0.80** |
| D. This session's evidence (CONTENT_READ only) | Base 0.8035, **capped at 0.80, INSUFFICIENT** |

Four further problems:

1. Every factor value in the handoff is TESTIMONY_ONLY from this session's point of view.
2. The integration figure lands exactly on the threshold that lifts the cap. A one-point change in the least-evidenced factor moves the result by a whole band.
3. The patches grade themselves: the proposal scores the spec on the assumption that its own patches are applied and correct.
4. PROVISIONAL makes nothing "eligible." In the corpus bands, PROVISIONAL permits fetching more context, a critic pass, and rescoring. Passing a gate needs READY, or a recorded human override.

---

## 2. Answers to the handoff's interrogation questions

**Q1. Does group N (mechanics) bloat packets for works without magic or technology?**
No. In B.3, `public.mechanics` is optional: it is not in `public.required`, and the comment ties it to "when mechanics are in play." An absent group adds zero bytes. The question's premise is wrong in one respect: B.3 does **not** set `additionalProperties: false` anywhere on `public`. Insulation comes from the field being optional, not from that keyword. Recommendation for WP-010: set `additionalProperties: false` on `public` and on every `$defs` object when they are written out, so a stray field fails validation instead of passing silently.

**Q2. Is the hard cap (Leak Safety or Reconcile below 0.95 caps readiness at 0.84) too brittle for automated batch tiers A2 and A3?**
The cap is intended, and it should stay hard. It caps promotion, not generation. A draft that trips it is regenerated (up to three times) and then escalated; the batch keeps running. Leak Safety below 0.95 means suppressed information may have reached the reader. Reconcile below 0.95 means undeclared inventions. Both are exactly what must not flow into canon through micro-fact registration. REQ-11.5.1 already says a failed hard cap cannot be overridden, only cleared by changing inputs.
The real brittleness risk is detector noise near the threshold. A noisy leak probe could push a correct draft into a regeneration loop. That is a DETECTOR_ERROR problem, and its fix is calibration (decoy probes), not a softer cap. Measure it in the pilot: track the regeneration rate and the share of findings later closed as DETECTOR_ERROR.

**Q3. Does the §12.2 mapping miss inter-module transitions or validator rules that the extraction pipeline (L11) needs?**
Yes; the rebuilt table and the crosswalk now carry the ones that matter. From the `next_modules` graph and `validator_rules` in `modules.json`:

| WCS rule or transition | What NSRES must do |
| --- | --- |
| `camera_boundary_required` (pov-shot-selection) | The packet's POV limits come from an accepted `pov_decision_packet` when one exists |
| `before_after_knowledge_required` (diegetic-document-weaver) | A placed document produces RIS deltas through the READ channel |
| `voice_strategy_check` (five modules) | Warn when a packet's `voice_profile_ref` points at no accepted voice strategy |
| `raw_footage_copy` (first-draft-forward) | Every draft is a new DRF revision; no in-place rewrite |
| `each_canon_candidate_requires_gate` (production-bible-builder) | One CANON-gate decision per record |
| `requires_two_versions` (character-autopsy) | Hold both dossier versions as alternative PROPOSALs; never merge |
| `open_questions_must_remain_open` (spark, riff) | A protected mystery stays an open question (Q-) through extraction |
| `meaning_remains_hypothesis` (story-why-trap) | Meaning hypotheses never become L1 rules |
| `destructive_recommendations_require_gate` (spark-rewrite-triage) | Impact analysis output stays PROPOSAL until gated |
| Preconditions `requires_canon_type story_spine` and `story_blueprint` | Packet compilation requires ACCEPTED, structure-locked L2 and L3/L4 records (which is how the crosswalk imports WCS CANON telling artifacts) |
| Transition pov-shot-selection → advanced-camera-pov | An advanced camera plan needs an accepted baseline POV first |

---

## 3. New findings the handoff did not raise

| ID | Severity | Finding | Evidence | Status |
| --- | --- | --- | --- | --- |
| N-01 | HIGH | **CANON means different things.** WCS STRUCTURE_GATE puts story_spine and story_blueprint in CANON state (`requires_canon_type` preconditions). NSRES says telling records top out at ACCEPTED and CANON is for locked reality records | `modules.json` preconditions; explication ("Canon requires a typed canon or structure gate"); spec §0.7 ACCEPTED row | Preserved in spec §12.2 as an open conflict. Crosswalk proposes: WCS CANON telling artifact → NSRES ACCEPTED, structure-locked. **Decision needed (plan OQ-9)** |
| N-02 | MEDIUM | `DETECTED` was defined in §17.5 as "a new knowledge channel (§4, L9)" but missing from the §2.4 CIS definition, the L9 channel table, and the §10.2 `Channel` union | Spec search for DETECTED and RUMOR | Fixed (rev 111–119) |
| N-03 | MEDIUM | §10.2 `Finding` had no `status`, while B.4 requires one | B.4 read | Fixed |
| N-04 | MEDIUM | `WAIVED_BY_OVERRIDE` exists as a finding status (B.4) with no rule anywhere. Waiving an open BLOCKING finding would clear the 0.69 open-BLOCKING cap without changing any input, which contradicts REQ-11.5.1 | B.4; REQ-11.5.1 text; a search found no other mention of waivers | Open. **Decision needed (plan OQ-10)** |
| N-05 | LOW (WCS side) | Every WCS module source lists 8 artifact states (no INTAKE, FORK, or SHIP) yet names SHIP as a human-only move. The runtime enum and the explication have 11 | All 23 module sources; handler `.py` | Crosswalk follows the runtime. Worth fixing in the WCS module template |
| N-06 | LOW | telling-architecture-recut's prose schema requires "knowledge state before and after each moved scene," but its machine contract has no field for it | Module source vs `required_output_fields` | Noted in §12.2: NSRES RIS_plan can supply it |
| N-07 | INFO (WCS side) | Handler scaffold issues: (a) `append_log` rewrites the whole JSON array on every entry, so it is not append-only, and a crash mid-write can lose the log; (b) `assess()` selects `intake_classifier`, which is not one of the 23 module names, so `validate()` would fail it if `MANIFEST.json` lists the 23; (c) the `invoke_module` stub defaults to validator PASS and critic CLEARED, though the contract says the runtime assigns those; (d) `assess()` reports a constant confidence of 0.85 with no factors; (e) path config stops at `08_SCHEMAS`, but module texts write to `09_EXPORTS`; (f) IDs are `prefix_` plus 12 hex digits of a UUIDv4, not UUIDv7 | Code read. (a) mechanism Verified by reading `append_log`; data-loss consequence Inferred — unverified (cheapest test: kill the process mid-write on a large log). (b) Inferred — unverified (cheapest test: read `_SYSTEM/MANIFEST.json`). (c)–(f) Verified by reading the code | Informational. An NSRES adapter maps IDs; it must not inherit (a) |
| N-08 | INFO | SKILL_MODULES_AND_GOAL_EXPLAINED (2026-06-04) describes 3 layers and 8 states; PROJECT_FULL_EXPLICATION (2026-06-05) describes 4 layers and 11 states | Both read | The later document matches the runtime and governs |

---

## 4. Net effect

- Applied to the spec (rev 119): H-01, H-02, H-03, H-04, the corrected H-06, N-02, N-03, and the §15.3 rescore. All are listed in the spec's §0.8.
- Not applied: H-07 (not delivered), H-09 (outside NSRES), H-10 (rejected).
- Waiting on Patrick: the crosswalk's PROPOSAL status, N-01 (which CANON vocabulary governs), N-04 (whether a BLOCKING finding can be waived).
