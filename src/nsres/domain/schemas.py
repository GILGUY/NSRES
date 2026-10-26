"""JSON Schemas for the scene packet (spec §8, B.3) and the finding record (B.4).

The schemas are built here from the closed vocabularies (``nsres.domain.vocab``) and the
handle patterns (``nsres.domain.handles``), so a schema cannot drift from the code. The test
suite checks both against the spec text.

Construction rules (DECISIONS D-004):

1. Nesting and group names follow B.3. Field names inside a group follow the §8.4 example
   where the example shows them, and otherwise the §8.2 name without the group's own prefix
   (``pov_character`` becomes ``pov.character``; ``active_threads`` becomes
   ``threads.active``; ``continuity_constraints`` becomes ``constraints.continuity``).
2. A field is required when either B.3 or §8.2 marks it REQUIRED. CONDITIONAL fields are
   enforced with ``if``/``then`` where the condition is visible inside the packet.
3. Every object sets ``additionalProperties: false``, so an unknown field fails validation.
4. Three places follow B.3 or the §8.4 example over §8.2, because §8.2 conflicts with them:
   ``validation.pre_draft_checks`` is the single value ALL_PASS (§8.2 says a list); the
   §8.2 group M ``sources`` map lives in the extraction record and the packet carries
   ``sources_ref`` (B.3); ``known_information`` items carry ``channel`` (§8.4, §10.2) and may
   also carry ``source`` (§8.2). Spec erratum ERR-3 lists them.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Final

from jsonschema import Draft202012Validator, FormatChecker

from nsres.domain import handles
from nsres.domain.vocab import (
    Anachrony,
    BeatType,
    Channel,
    Confidence,
    DeliveryMode,
    FindingCause,
    FindingEvidence,
    FindingStatus,
    Gate,
    GateOutcome,
    InventionClass,
    OutcomeKind,
    PacketFlag,
    PacketStatus,
    Plane,
    PovMode,
    Precision,
    PressureComponent,
    Provenance,
    Severity,
    ThreadRank,
    ThreadRole,
    values,
)

Schema = dict[str, Any]

PACKET_SCHEMA_ID: Final = "nsres/scene-packet/0.1.0"
FINDING_SCHEMA_ID: Final = "nsres/finding/0.1.0"

NARRATIVE_POSITION: Final = r"^\d+(?:\.\d+){1,3}$"
STORY_TIME: Final = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$"
INSTANT_UTC: Final = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z$"
ISO_DURATION: Final = (
    r"^P(?!$)(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+S)?)?$"
)
SEMVER: Final = r"^[0-9]+\.[0-9]+\.[0-9]+$"
SHA256_REF: Final = r"^sha256:[0-9a-f]{64}$"
RULE_CODE: Final = r"^(RC|CC|PK|EX|AU|MC|CX|ED)-?[A-Z0-9-]+$"


# --- builders --------------------------------------------------------------------------


def _enum(vocabulary: type[StrEnum]) -> Schema:
    return {"enum": values(vocabulary)}


def _handle(prefix: str) -> Schema:
    return {"type": "string", "pattern": handles.pattern(prefix)}


def _handle_of(*prefixes: str) -> Schema:
    return {"type": "string", "pattern": handles.one_of(*prefixes)}


def _text() -> Schema:
    return {"type": "string", "minLength": 1}


def _array(items: Schema, *, min_items: int = 0) -> Schema:
    schema: Schema = {"type": "array", "items": items}
    if min_items:
        schema["minItems"] = min_items
    return schema


def _texts(*, min_items: int = 0) -> Schema:
    return _array(_text(), min_items=min_items)


def _object(
    required: dict[str, Schema],
    optional: dict[str, Schema] | None = None,
    **extra: Any,
) -> Schema:
    properties = {**required, **(optional or {})}
    schema: Schema = {
        "type": "object",
        "required": sorted(required),
        "properties": properties,
        "additionalProperties": False,
    }
    schema.update(extra)
    return schema


def _map(key_pattern: str, value: Schema) -> Schema:
    return {
        "type": "object",
        "propertyNames": {"pattern": key_pattern},
        "additionalProperties": value,
    }


def _ref(name: str) -> Schema:
    return {"$ref": f"#/$defs/{name}"}


def _present(*path: str, schema: Schema) -> Schema:
    """An ``if`` clause that holds only when ``path`` exists and satisfies ``schema``.

    Each level lists its key as required, so an absent branch does not satisfy the clause
    vacuously.
    """
    clause: Schema = schema
    for key in reversed(path):
        clause = {"properties": {key: clause}, "required": [key]}
    return clause


ENTITY_PREFIXES: Final = ("CHR", "LOC", "OBJ", "GRP")
ANY_RECORD_PREFIXES: Final = tuple(handles.ALL_PREFIXES)


# --- packet $defs ------------------------------------------------------------------------


def _packet_defs() -> dict[str, Schema]:
    pressure = _object(
        {component.value: {"type": "number", "minimum": 0} for component in PressureComponent}
    )
    return {
        "gate_record": _object(
            {
                "gate": _enum(Gate),
                "actor": _text(),
                "time": {"type": "string", "pattern": INSTANT_UTC},
            },
            {"outcome": _enum(GateOutcome), "override": {"type": "boolean"}, "reason": _text()},
        ),
        "story_time_range": _object(
            {
                "start": {"type": "string", "pattern": STORY_TIME},
                "end": {"type": "string", "pattern": STORY_TIME},
                "precision": _enum(Precision),
            }
        ),
        "position": _object(
            {
                "narrative_position": {"type": "string", "pattern": NARRATIVE_POSITION},
                "story_time_range": _ref("story_time_range"),
                "previous_scene": {"anyOf": [_handle("SCN"), {"type": "null"}]},
                "next_scene": {"anyOf": [_handle("SCN"), {"type": "null"}]},
                "story_time_gap": _object(
                    {
                        "since_previous_scene": {
                            "anyOf": [{"type": "string", "pattern": ISO_DURATION}, {"type": "null"}]
                        }
                    },
                    {
                        "since_last_appearance": _map(
                            handles.pattern("CHR"), {"type": "string", "pattern": ISO_DURATION}
                        )
                    },
                ),
                "anachrony": _enum(Anachrony),
                "narration_stance": _object({"tense": _text(), "narrating_time": _text()}),
            },
            {"frame_ref": _handle("SCN"), "anchors": _array(_handle("ANCHOR"))},
            allOf=[
                {
                    "if": {
                        "properties": {"anachrony": {"enum": ["ANALEPSIS", "PROLEPSIS"]}},
                        "required": ["anachrony"],
                    },
                    "then": {"required": ["frame_ref"]},
                }
            ],
        ),
        "setting": _object(
            {
                "location": _object({"handle": _handle("LOC"), "name": _text()}),
                "setting_state": _texts(),
                "objects_present": _array(
                    _object({"object": _text(), "state": _text()}, {"significance": _text()})
                ),
            },
            {
                "sub_locations": _texts(),
                "perceptibles": _texts(),
                "reader_continuity_anchors": _texts(),
            },
        ),
        "pov": _object(
            {
                "character": _handle("CHR"),
                "mode": _enum(PovMode),
                "permitted_interiority": _array(_handle("CHR"), min_items=1),
                "naming_map": _map(handles.one_of(*ENTITY_PREFIXES), _text()),
                "voice_profile_ref": _text(),
            },
            {
                "unreliable": {"type": "boolean"},
                "narrator_horizon": _array(_handle("INF")),
                "perception_constraints": _texts(),
                "narrator_beliefs": _array(_handle("CLM")),
            },
            allOf=[
                {
                    "if": {
                        "properties": {"mode": {"const": "FIRST_RETROSPECTIVE"}},
                        "required": ["mode"],
                    },
                    "then": {"required": ["narrator_horizon"]},
                },
                {
                    "if": {
                        "properties": {"unreliable": {"const": True}},
                        "required": ["unreliable"],
                    },
                    "then": {"required": ["narrator_beliefs"]},
                },
            ],
        ),
        "manifestation": _object(
            {
                "actor": _handle_of("CHR", "GRP"),
                "behavior": _text(),
                "intensity": {"type": "integer", "minimum": 1, "maximum": 3},
                "permitted_explanation": _text(),
                "forbidden_explanations": _texts(),
            }
        ),
        "threads": _object(
            {
                "active": {
                    **_array(
                        _object(
                            {
                                "thread": _handle("THR"),
                                "rank": _enum(ThreadRank),
                                "role": _enum(ThreadRole),
                                "nodes": _array(_handle("NOD")),
                                "priority": {"type": "number"},
                            }
                        ),
                        min_items=1,
                    ),
                    "contains": {"properties": {"role": {"const": "FOREGROUND"}}},
                },
                "hidden": _array(
                    _object(
                        {"sup_ref": _handle("SUP"), "manifestations": _array(_ref("manifestation"))}
                    )
                ),
            },
            {"background": _array(_object({"thread": _handle("THR")}, {"reference": _text()}))},
        ),
        "beat": _object(
            {
                "beat": _handle("BT"),
                "type": _enum(BeatType),
                "actors": _array(_handle_of("CHR", "GRP"), min_items=1),
                "outcome": _text(),
            },
            {"events": _array(_handle("EVT")), "plants": _handle("INF"), "deltas": _texts()},
        ),
        "character_state": _object(
            {
                "character": _handle("CHR"),
                "presence": _object({"interval": _text(), "position": _text()}),
                "physical": _texts(),
                "goals_in_scene": _texts(),
            },
            {
                "possessions": _texts(),
                "emotional_entry": _text(),
                "emotional_exit_target": _text(),
                "stance": _map(handles.one_of(*ENTITY_PREFIXES), _text()),
                "knowledge_bounds": _texts(),
                "known_secrets": _array(_object({"inf": _handle("INF"), "statement": _text()})),
                "speech": _text(),
            },
        ),
        "information": _object(
            {
                "known_information": _array(
                    _object(
                        {
                            "inf": _handle("INF"),
                            "statement": _text(),
                            "confidence": _enum(Confidence),
                            "channel": _enum(Channel),
                        },
                        {"source": _text()},
                    )
                ),
                "reader_known": _array(
                    _object(
                        {
                            "inf": _handle("INF"),
                            "delivered_at": {"type": "string", "pattern": NARRATIVE_POSITION},
                            "mode": _enum(DeliveryMode),
                        },
                        {"statement": _text(), "wording_ref": _text()},
                    )
                ),
                "unknown_information": _texts(),
                "suppressed_information": _array(_handle("SUP")),
                "forbidden_revelations": _texts(),
            },
            {
                "permitted_hints": _array(
                    _object(
                        {
                            "inf": _handle("INF"),
                            "max_explicitness": {"type": "integer", "minimum": 1, "maximum": 3},
                            "guidance": _text(),
                        }
                    )
                ),
                "adjacent_not_delivered": _texts(),
                "irony_constraints": _texts(),
                "misdirection": _array(_object({"belief": _text(), "correction_ref": _text()})),
            },
        ),
        "emotion": _object(
            {
                "scene_tone_target": _text(),
                "narrative_pressure": _object({"before": pressure, "target_after": pressure}),
            },
            {"tension_shape": _texts()},
        ),
        "constraints": _object(
            {
                "continuity": _array(
                    _object(
                        {
                            "statement": _text(),
                            "sources": _array(_handle_of(*ANY_RECORD_PREFIXES), min_items=1),
                        }
                    )
                ),
                "drafting": _object(
                    {
                        "words": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "tense": _text(),
                        "person": _text(),
                    },
                    {"forbidden_devices": _texts()},
                ),
                "invention_policy": {
                    "type": "object",
                    "propertyNames": _enum(InventionClass),
                    "additionalProperties": _texts(),
                    "minProperties": 1,
                },
                "terminology": _object({"locked": _texts(), "forbidden": _texts()}),
            },
            {"first_contact": _array(_handle_of(*ENTITY_PREFIXES))},
        ),
        "outcomes": _object(
            {
                "required": _array(
                    _object(
                        {"kind": _enum(OutcomeKind), "delta": _text()},
                        {"mode": _enum(DeliveryMode), "confidence": _enum(Confidence)},
                        allOf=[
                            {
                                "if": {
                                    "properties": {"kind": {"const": "READER"}},
                                    "required": ["kind"],
                                },
                                "then": {"required": ["mode"]},
                            }
                        ],
                    )
                ),
                "forbidden": _texts(),
                "exit_state": _text(),
            },
            {"hooks": _array(_handle("Q"))},
        ),
        "mechanics": _object(
            {
                "mechanics_in_play": _array(
                    _object({"mechanic": _handle("MCH"), "name": _text(), "rules": _texts()}),
                    min_items=1,
                ),
                "regime": _object(
                    {"regime": _handle("RGM"), "mechanics_in_force": _array(_handle("MCH"))}
                ),
                "practitioner_states": _array(
                    _object(
                        {
                            "character": _handle("CHR"),
                            "reserves": _array(
                                _object(
                                    {
                                        "resource": _handle("RSV"),
                                        "value": {"type": "number", "minimum": 0},
                                        "maximum": {"type": "number", "minimum": 0},
                                    }
                                )
                            ),
                            "known_patterns": _texts(),
                            "impairments": _texts(),
                        },
                        {
                            "proficiency": _map(
                                handles.pattern("MCH"), {"type": "integer", "minimum": 0}
                            )
                        },
                    )
                ),
                "active_effects": _array(
                    _object(
                        {
                            "effect": _handle("EFF"),
                            "mechanic": _handle("MCH"),
                            "remaining_funded_minutes": {"type": "integer", "minimum": 0},
                        }
                    )
                ),
                "traces_present": _array(
                    _object({"trace": _handle("TRC"), "what": _text(), "perceptible_by": _texts()})
                ),
                "mechanic_constraints": _array(
                    _object(
                        {
                            "statement": _text(),
                            "sources": _array(_handle_of(*ANY_RECORD_PREFIXES), min_items=1),
                        }
                    )
                ),
                "forbidden_mechanic_revelations": _texts(),
            }
        ),
    }


def build_packet_schema() -> Schema:
    """The scene packet schema (B.3, with every ``$defs`` written out)."""
    dependency = "DEPENDENCY:SCN-" + handles.ALL_PREFIXES["SCN"]
    flag_pattern = "^(?:" + "|".join([*values(PacketFlag), dependency]) + ")$"
    public = _object(
        {
            "position": _ref("position"),
            "setting": _ref("setting"),
            "pov": _ref("pov"),
            "threads": _ref("threads"),
            "required_beats": _array(_ref("beat"), min_items=1),
            "character_states": _array(_ref("character_state"), min_items=1),
            "information": _ref("information"),
            "emotion": _ref("emotion"),
            "constraints": _ref("constraints"),
            "outcomes": _ref("outcomes"),
        },
        {
            "optional_beats": _array(_ref("beat")),
            "beat_order": _array(
                {"type": "array", "items": _handle("BT"), "minItems": 2, "maxItems": 2}
            ),
            "mechanics": _ref("mechanics"),
        },
    )
    sealed = _object(
        {
            "suppressed": _map(handles.pattern("SUP"), _handle("INF")),
            "forbidden_propositions": _array(_handle("INF")),
        },
        {
            "leak_indicators": _map(handles.pattern("INF"), _texts()),
            "hidden_mechanic_rules": _map(handles.pattern("MCH"), _texts()),
        },
    )
    validation = _object(
        {"pre_draft_checks": {"enum": ["ALL_PASS"]}, "autopsy_targets": _texts()},
        {
            "leak_probe_results": _array(
                _object(
                    {
                        "sup": _handle("SUP"),
                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                        "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                    }
                )
            )
        },
    )
    schema = _object(
        {
            "packet_uuid": {"type": "string", "format": "uuid"},
            "packet_handle": _handle("PKT"),
            "schema_version": {"type": "string", "pattern": SEMVER},
            "scene_ref": _handle("SCN"),
            "model_version": _text(),
            "extraction_run": {"type": "string", "pattern": r"^RUN-X-\d{4,}$"},
            "packet_hash": {"type": "string", "pattern": SHA256_REF},
            "public_hash": {"type": "string", "pattern": SHA256_REF},
            "status": _enum(PacketStatus),
            "confidence_vector_ref": _handle("CV"),
            "public": public,
            "sealed": sealed,
            "validation": validation,
            "sources_ref": _text(),
            "exclusions_ref": _text(),
        },
        {
            "flags": _array({"type": "string", "pattern": flag_pattern}),
            "gate_record": _ref("gate_record"),
        },
        allOf=[
            {
                "if": {"properties": {"status": {"const": "FROZEN"}}, "required": ["status"]},
                "then": {"required": ["gate_record"]},
            },
            {
                "if": _present("public", "threads", "hidden", schema={"minItems": 1}),
                "then": {"properties": {"validation": {"required": ["leak_probe_results"]}}},
            },
        ],
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = PACKET_SCHEMA_ID
    schema["$defs"] = _packet_defs()
    return schema


def build_finding_schema() -> Schema:
    """The finding record schema (B.4, completed by D-004 rule 6).

    B.4's fields and its two ``allOf`` clauses (REQ-9.1.1, REQ-9.1.2) are kept as written. The
    record fields §10.2 gives every finding through ``BaseRecord`` (``rev``, ``provenance``,
    ``plane``, ``tx``, and optionally ``gate`` and ``notes``) are added, and ``spans`` and
    ``repairs`` are required because §10.2 does not mark them optional; either may be empty.
    """
    not_blocking = [severity.value for severity in Severity if severity is not Severity.BLOCKING]
    schema = _object(
        {
            "uuid": {"type": "string", "format": "uuid"},
            "handle": _handle("FND"),
            "rev": {"type": "integer", "minimum": 1},
            "provenance": _enum(Provenance),
            "plane": _enum(Plane),
            "tx": _object(
                {
                    "from": {"type": "integer", "minimum": 0},
                    "to": {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]},
                }
            ),
            "rule": {"type": "string", "pattern": RULE_CODE},
            "severity": _enum(Severity),
            "spans": _array(
                _object(
                    {
                        "draft": _handle("DRF"),
                        "start": {"type": "integer", "minimum": 0},
                        "end": {"type": "integer", "minimum": 0},
                        "quote": _text(),
                    }
                )
            ),
            "records": _array(_text(), min_items=1),
            "evidence": _enum(FindingEvidence),
            "detection_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "repairs": _texts(),
            "status": _enum(FindingStatus),
        },
        {
            "cause": _enum(FindingCause),
            "gate": {"type": "string", "format": "uuid"},
            "notes": {"type": "string"},
        },
        allOf=[
            {
                "if": {"properties": {"severity": {"const": Severity.BLOCKING.value}}},
                "then": {"properties": {"evidence": {"const": FindingEvidence.CONTENT_READ.value}}},
            },
            {
                "if": {
                    "properties": {"status": {"const": FindingStatus.WAIVED_BY_OVERRIDE.value}},
                    "required": ["status"],
                },
                "then": {"properties": {"severity": {"enum": not_blocking}}},
            },
        ],
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = FINDING_SCHEMA_ID
    return schema


PACKET_SCHEMA: Final[Schema] = build_packet_schema()
FINDING_SCHEMA: Final[Schema] = build_finding_schema()

Draft202012Validator.check_schema(PACKET_SCHEMA)
Draft202012Validator.check_schema(FINDING_SCHEMA)

_FORMATS: Final = FormatChecker()
_PACKET_VALIDATOR: Final = Draft202012Validator(PACKET_SCHEMA, format_checker=_FORMATS)
_FINDING_VALIDATOR: Final = Draft202012Validator(FINDING_SCHEMA, format_checker=_FORMATS)


def _errors(validator: Draft202012Validator, document: Any) -> list[tuple[str, str]]:
    found = []
    for error in validator.iter_errors(document):
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path
        )
        found.append((path, error.message))
    return sorted(found)


def packet_errors(packet: Any) -> list[tuple[str, str]]:
    """``(json_path, message)`` for every schema violation in a packet; empty when valid."""
    return _errors(_PACKET_VALIDATOR, packet)


def finding_errors(finding: Any) -> list[tuple[str, str]]:
    """``(json_path, message)`` for every schema violation in a finding; empty when valid."""
    return _errors(_FINDING_VALIDATOR, finding)
