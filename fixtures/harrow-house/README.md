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
