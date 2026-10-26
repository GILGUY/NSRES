# Contract: scope lock

> Registered from `docs/IMPLEMENTATION_PLAN.md` v0.2.1 at WP-000. The plan section is authoritative; this copy exists so a cold session reading only the repository has the contract. Changing it requires the process in the plan's scope-lock note and a `DECISIONS.md` entry first.

## Scope lock (plan §4)

**In (v0.1)**

| Area | Spec reference |
| --- | --- |
| Domain types and JSON Schemas (packet, finding, all sub-objects written out) | §8, §10.2, §17.4, Appendix B.3–B.4 |
| Record store: append-only log, bitemporal revisions, statuses, typed gates, hash-chained audit | §0.7, §5.4, §10.4–10.5 |
| WCS crosswalk as tested data, no I/O (only if OQ-8 is approved) | §0.7 crosswalk, §12.2, REQ-12.2.2 |
| Canon registry: rule classes, travel metric closure, timetables, simple daylight model, precedence | §3.4, L1 |
| Rule registry and findings | Appendix B.2, DEF-41 |
| Confidence engine: factors, ceilings, claim ladder, penalties, caps, bands | §9.6, §11.5, REQ-9.6.1 |
| Temporal engine: STN, windows, metric and single Allen relations, anchors, capped disjunctions | §6.2–6.3 |
| Effect and precondition language; state folding | §3.5, §10.9, §17.4 |
| Projections L6–L8 with RC-02, RC-05, RC-08, RC-09, RC-12, RC-13 | §4 (L6–L8), §6.4–6.6, §6.12 |
| Knowledge L9 with channels (DETECTED included), witness grants, belief revision, reachability, RC-10, RC-11, RC-14 | L9, §6.7, §6.13, §17.5 |
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
| WCS I/O adapter (reading handoff packets and module outputs, writing proposals into WCS folders); MAPS, Beat Engine, Seam Protocol adapters; editorial suite ED-01 to ED-04 | §12.2–12.5 | v0.3 |
| Graph database, vector index, RDF/OWL export | §10.4, §12.8 | v0.3 |
| Import/export adapters (Fountain, Final Draft, Scrivener, series bibles) | §12.8 | v0.3 |
| Datalog rule engine (rules ship as code predicates) | §10.11 | v0.3 |
| Non-Gregorian calendars | §0.4 | v0.3 |
| Ontology kit as executable code (§17.2 is documentation in v0.1) | §17.2 | v0.3 |
| Multi-user permissions per gate | §10.15 | v0.3 |
| Hypocrisy Tax metric | §12.7 | Not adopted |
| The §14 evaluation trial | §14 | Separate study |

Moving anything from Out to In requires a proposal, an impact analysis (permissions, data, tests, distribution), Patrick's approval, and updated contracts before implementation.
