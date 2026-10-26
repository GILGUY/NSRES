# Harrow House fixtures

## `PKT-007-r3.example.json`

The spec §8.4 example packet, completed so that it validates against the packet schema
(WP-010 exit criterion; DECISIONS D-004).

**Provenance.** Every key and value printed in spec §8.4 (rev 126) is kept unchanged;
`tests/unit/test_schemas.py::test_fixture_keeps_every_value_of_the_spec_example` checks this
against the spec text. The test that follows it checks that nothing else was added. The
completions are:

| Field | Value source | Authority |
| --- | --- | --- |
| `confidence_vector_ref` | §8.2 group A example (`CV-PKT-007-r3`) | Spec example |
| `gate_record` | §8.2 group A example (STRUCTURE, author, 2026-10-25T19:02Z) | Spec example |
| `packet_hash`, `public_hash` | Computed by `nsres.domain.canonical.with_packet_hashes` (D-006) | Computed |
| `public.character_states[CHR-001]` | §8.2 group G examples (Mara: presence, physical, possessions, emotional entry and exit, goals, stance, known secrets) | Spec example |
| `public.character_states[CHR-002]` | §8.2 group G examples (knowledge bounds, speech); cane from §8.4 continuity; goal from BT-007-01 | Spec example, lightly composed |
| `public.character_states[CHR-004]`, `[CHR-006]` | Composed for this fixture: the spec names them as participants (§4, L3 scene record, SCN-007 participants) but gives no state blocks | **Illustrative, not test-authoritative** |
| `public.emotion.scene_tone_target`, `tension_shape`, `narrative_pressure.before` | §8.2 group I examples | Spec example |
| `public.emotion.narrative_pressure.target_after` | Composed from the SCN-007 planned delta (opens Q-03, plants the empty hook): Q +1, S +1 | **Illustrative, not test-authoritative** |
| `public.outcomes.forbidden` | §8.2 group K example | Spec example |

The two illustrative rows are not spec values (plan OQ-5 makes only spec values
test-authoritative). A later package that computes character states or pressure must not
treat them as expected outputs.

**Known spec conflict kept visible.** §8.2 group G gives Mara's entry state as "shaken but
composed"; the L6 contents table (§4, L6 emotional baseline) gives "frightened, controlled". The fixture uses the §8.2 value
because it is the packet field's own example (DECISIONS errata ERR-9).

The spec example as printed fails validation on exactly seven omitted required fields
(`test_spec_example_as_printed_fails_on_exactly_its_omissions`): the four it says it omits
(hashes, character states, emotion) and three it does not mention (`confidence_vector_ref`,
`gate_record`, `outcomes.forbidden`; errata ERR-2).

To regenerate the hashes after an intentional edit, load the file, pass it through
`with_packet_hashes`, and write it back with two-space indentation.

## `canon.json`

The Harrow House canon as authored input: 28 rows of `{"type", "record"}` in the record JSON
form (D-007), every record at PROPOSAL, ready to pass the store's gates. Generated once from
the values below; UUIDs come from a seeded generator.

| Records | Source | Authority |
| --- | --- | --- |
| CHR-001 to CHR-005, OBJ-001 to OBJ-003, GRP-001, and their names and traits | §0.3, §0.5, L1 entity example (Hale: "the Inspector", York City Police, age 52, cane) | Spec |
| CHR-006 Mrs. Dorran (cook) | §4 L3 SCN-007 participants | Spec |
| LOC-001 Harrow House, LOC-001a, LOC-001c, LOC-001d, LOC-001f, LOC-002 The Bell, OBJ-004 key board | §0.3, §8.4, Appendix A.2 | Spec |
| LOC-003 Kellby station, LOC-004 York station | The spec names the places but gives them no handles | **Illustrative handles** |
| CAN-003, CAN-014, CAN-030, CAN-041, CAN-052, CAN-060, CAN-061 statements | Appendix A.1 | Spec (CAN-014's class is PROHIBITION, not A.1's "WORLD RULE": D-017, ERR-14) |
| CAN-062 (45 minutes on foot to The Bell) | L1 metrics example | Spec value, **illustrative handle** |
| CAN-070 daylight rows | First light 06:45 on 15 October is the spec's (§4 L7 example); the other three times are composed to fit "dark from 22:40" | **Illustrative except 06:45** |
| `statement_structured` texts | Written for this fixture in the D-017 forms; the non-metric ones are free text for later engines | Fixture |
