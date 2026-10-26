"""Packet and finding JSON Schemas (spec §8, B.3, B.4; DECISIONS D-004)."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from nsres.domain.schemas import FINDING_SCHEMA, PACKET_SCHEMA, finding_errors, packet_errors
from tests import spec_text as spec

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "fixtures" / "harrow-house" / "PKT-007-r3.example.json"


def _packet() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(PACKET.read_text(encoding="utf-8"))
    return loaded


def _contains(whole: Any, part: Any, path: str = "$") -> list[str]:
    """Paths where ``part`` is not contained in ``whole`` (objects may gain keys; lists and
    scalars must be equal)."""
    if isinstance(part, dict):
        if not isinstance(whole, dict):
            return [path]
        missing = []
        for key, value in part.items():
            if key not in whole:
                missing.append(f"{path}.{key}")
            else:
                missing += _contains(whole[key], value, f"{path}.{key}")
        return missing
    if isinstance(part, list):
        if not isinstance(whole, list) or len(whole) != len(part):
            return [path]
        missing = []
        for index, (left, right) in enumerate(zip(whole, part, strict=True)):
            missing += _contains(left, right, f"{path}[{index}]")
        return missing
    return [] if whole == part and type(whole) is type(part) else [path]


# --- the completed §8.4 example ------------------------------------------------------------


def test_completed_example_packet_validates() -> None:
    assert packet_errors(_packet()) == []


def test_fixture_keeps_every_value_of_the_spec_example() -> None:
    example = spec.json_example("### 8.4")
    assert _contains(_packet(), example) == []


def test_fixture_adds_only_the_fields_the_example_omits() -> None:
    example = spec.json_example("### 8.4")
    packet = _packet()
    added_top = sorted(set(packet) - set(example))
    assert added_top == ["confidence_vector_ref", "gate_record", "packet_hash", "public_hash"]
    added_public = sorted(set(packet["public"]) - set(example["public"]))
    assert added_public == ["character_states", "emotion"]
    assert sorted(set(packet["public"]["outcomes"]) - set(example["public"]["outcomes"])) == [
        "forbidden"
    ]


def test_spec_example_as_printed_fails_on_exactly_its_omissions() -> None:
    """The §8.4 example is abridged; the schema names each omitted required field (ERR-2)."""
    errors = packet_errors(spec.json_example("### 8.4"))
    messages = {(path, message) for path, message in errors}
    assert ("$", "'packet_hash' is a required property") in messages
    assert ("$", "'public_hash' is a required property") in messages
    assert ("$", "'confidence_vector_ref' is a required property") in messages
    assert ("$", "'gate_record' is a required property") in messages
    assert ("$.public", "'character_states' is a required property") in messages
    assert ("$.public", "'emotion' is a required property") in messages
    assert ("$.public.outcomes", "'forbidden' is a required property") in messages
    assert len(errors) == 7, errors


# --- required structure ---------------------------------------------------------------------


def test_removing_sealed_fails_with_the_path_named() -> None:
    packet = _packet()
    del packet["sealed"]
    assert packet_errors(packet) == [("$", "'sealed' is a required property")]


def test_an_unknown_field_under_public_fails() -> None:
    packet = _packet()
    packet["public"]["drafter_notes"] = "anything"
    assert packet_errors(packet) == [
        ("$.public", "Additional properties are not allowed ('drafter_notes' was unexpected)")
    ]


@pytest.mark.parametrize(
    "path",
    [
        ("public", "pov"),
        ("public", "position", "story_time_range"),
        ("public", "threads", "hidden", 0, "manifestations", 0),
        ("public", "required_beats", 0),
        ("public", "character_states", 0, "presence"),
        ("public", "information", "known_information", 0),
        ("public", "constraints", "drafting"),
        ("public", "emotion", "narrative_pressure", "before"),
        ("sealed",),
        ("validation",),
        ("gate_record",),
    ],
    ids=lambda path: "/".join(str(p) for p in path),
)
def test_unknown_fields_fail_at_every_level(path: tuple[str | int, ...]) -> None:
    packet = _packet()
    target: Any = packet
    for key in path:
        target = target[key]
    target["unexpected"] = 1
    errors = packet_errors(packet)
    assert len(errors) == 1
    assert "'unexpected' was unexpected" in errors[0][1]


def _b3_required() -> list[list[str]]:
    return spec.yaml_required_lists(spec.b3())


B3_REQUIRED_AT: list[tuple[str, Callable[[dict[str, Any]], dict[str, Any]]]] = [
    ("top level", lambda schema: schema),
    ("public", lambda schema: schema["properties"]["public"]),
    ("sealed", lambda schema: schema["properties"]["sealed"]),
    ("validation", lambda schema: schema["properties"]["validation"]),
    (
        "leak_probe_results item",
        lambda schema: schema["properties"]["validation"]["properties"]["leak_probe_results"][
            "items"
        ],
    ),
    ("beat", lambda schema: schema["$defs"]["beat"]),
    ("manifestation", lambda schema: schema["$defs"]["manifestation"]),
]


def test_every_b3_required_list_is_kept() -> None:
    lists = _b3_required()
    assert len(lists) == len(B3_REQUIRED_AT)
    for (label, locate), required in zip(B3_REQUIRED_AT, lists, strict=True):
        missing = set(required) - set(locate(PACKET_SCHEMA)["required"])
        assert not missing, f"B.3 {label} requires {sorted(missing)}"


@pytest.mark.parametrize("field", _b3_required()[0])
def test_each_b3_top_level_field_is_required(field: str) -> None:
    packet = _packet()
    del packet[field]
    assert ("$", f"'{field}' is a required property") in packet_errors(packet)


def test_every_object_in_both_schemas_closes_additional_properties() -> None:
    open_objects: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            is_object = node.get("type") == "object"
            closed = node.get("additionalProperties") is False
            typed_map = isinstance(node.get("additionalProperties"), dict)
            if is_object and "propertyNames" not in node and not closed and not typed_map:
                open_objects.append(path)
            for key, value in node.items():
                if key not in ("if",):
                    walk(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}/{index}")

    walk(PACKET_SCHEMA, "packet")
    walk(FINDING_SCHEMA, "finding")
    assert open_objects == []


def test_both_schemas_are_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(PACKET_SCHEMA)
    Draft202012Validator.check_schema(FINDING_SCHEMA)
    assert PACKET_SCHEMA["$id"] == "nsres/scene-packet/0.1.0"
    assert FINDING_SCHEMA["$id"] == "nsres/finding/0.1.0"


# --- conditional fields ---------------------------------------------------------------------


def test_a_frozen_packet_needs_its_gate_record() -> None:
    packet = _packet()
    del packet["gate_record"]
    assert packet_errors(packet) == [("$", "'gate_record' is a required property")]
    packet["status"] = "PACKET_VALID"
    assert packet_errors(packet) == []


def test_hidden_threads_need_leak_probe_results() -> None:
    packet = _packet()
    del packet["validation"]["leak_probe_results"]
    assert packet_errors(packet) == [
        ("$.validation", "'leak_probe_results' is a required property")
    ]
    packet["public"]["threads"]["hidden"] = []
    assert packet_errors(packet) == []


def test_first_retrospective_needs_a_narrator_horizon() -> None:
    packet = _packet()
    packet["public"]["pov"]["mode"] = "FIRST_RETROSPECTIVE"
    assert packet_errors(packet) == [("$.public.pov", "'narrator_horizon' is a required property")]
    packet["public"]["pov"]["narrator_horizon"] = []
    assert packet_errors(packet) == []


def test_unreliable_narration_needs_narrator_beliefs() -> None:
    packet = _packet()
    packet["public"]["pov"]["unreliable"] = True
    assert packet_errors(packet) == [("$.public.pov", "'narrator_beliefs' is a required property")]


def test_an_analepsis_needs_a_frame_scene() -> None:
    packet = _packet()
    packet["public"]["position"]["anachrony"] = "ANALEPSIS"
    assert packet_errors(packet) == [("$.public.position", "'frame_ref' is a required property")]
    packet["public"]["position"]["frame_ref"] = "SCN-006"
    assert packet_errors(packet) == []


def test_a_reader_outcome_needs_a_delivery_mode() -> None:
    packet = _packet()
    del packet["public"]["outcomes"]["required"][0]["mode"]
    assert packet_errors(packet) == [
        ("$.public.outcomes.required[0]", "'mode' is a required property")
    ]


def test_at_least_one_thread_is_foreground() -> None:
    packet = _packet()
    for thread in packet["public"]["threads"]["active"]:
        thread["role"] = "BACKGROUND"
    errors = packet_errors(packet)
    assert len(errors) == 1
    assert errors[0][0] == "$.public.threads.active"


# --- field values -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (
            lambda p: p["public"]["required_beats"][0].update(type="MONTAGE"),
            "$.public.required_beats[0].type",
        ),
        (lambda p: p.update(flags=["DEPENDENCY:SCN-6"]), "$.flags[0]"),
        (lambda p: p.update(packet_handle="PKT-007"), "$.packet_handle"),
        (lambda p: p.update(extraction_run="RUN-R-0212"), "$.extraction_run"),
        (lambda p: p.update(packet_uuid="not-a-uuid"), "$.packet_uuid"),
        (
            lambda p: p["sealed"]["suppressed"].update({"SUP-1": "EVT-0104"}),
            "$.sealed.suppressed.SUP-1",
        ),
        (
            lambda p: p["public"]["threads"]["hidden"][0]["manifestations"][0].update(intensity=4),
            "$.public.threads.hidden[0].manifestations[0].intensity",
        ),
        (lambda p: p["public"]["pov"].update(mode="UNRELIABLE"), "$.public.pov.mode"),
        (
            lambda p: p["public"]["constraints"]["invention_policy"].update(SOMETIMES=["x"]),
            "$.public.constraints.invention_policy",
        ),
        (
            lambda p: p["validation"].update(pre_draft_checks="SOME_FAIL"),
            "$.validation.pre_draft_checks",
        ),
        (lambda p: p["gate_record"].update(gate="REVIEW"), "$.gate_record.gate"),
        (lambda p: p["gate_record"].update(time="2026-10-25 19:02"), "$.gate_record.time"),
    ],
    ids=[
        "beat type",
        "dependency flag",
        "packet handle",
        "extraction run kind",
        "packet uuid",
        "suppressed target",
        "intensity",
        "unreliable is a modifier",
        "invention class",
        "pre-draft checks",
        "gate type",
        "gate time",
    ],
)
def test_malformed_values_fail_at_their_path(
    mutate: Callable[[dict[str, Any]], None], path: str
) -> None:
    packet = _packet()
    mutate(packet)
    errors = packet_errors(packet)
    assert [error_path for error_path, _ in errors] == [path], errors


def test_validation_does_not_mutate_its_input() -> None:
    packet = _packet()
    before = copy.deepcopy(packet)
    packet_errors(packet)
    assert packet == before


# --- finding schema -----------------------------------------------------------------------


def _finding(**changes: Any) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "uuid": "01920c3e-7a41-7c2b-9d1e-5f3a8b2c4d70",
        "handle": "FND-007-01-01",
        "rev": 1,
        "provenance": "ENGINE_BRIDGE",
        "plane": "control",
        "tx": {"from": 47, "to": None},
        "rule": "AU-02",
        "severity": "BLOCKING",
        "spans": [{"draft": "DRF-007-01", "start": 140, "end": 156, "quote": "of Scotland Yard"}],
        "records": ["CHR-002"],
        "evidence": "CONTENT_READ",
        "detection_confidence": 0.99,
        "cause": "DRAFTER_VIOLATION",
        "repairs": ["Remove the affiliation"],
        "status": "OPEN",
    }
    finding.update(changes)
    return finding


def test_a_well_formed_finding_validates() -> None:
    assert finding_errors(_finding()) == []


def test_a_blocking_finding_with_metadata_evidence_is_rejected() -> None:
    errors = finding_errors(_finding(evidence="FOUND_BY_METADATA"))
    assert errors == [("$.evidence", "'CONTENT_READ' was expected")]


@pytest.mark.parametrize("evidence", ["FOUND_BY_SNIPPET", "FOUND_BY_METADATA", "CLAIM_INFERRED"])
def test_a_major_finding_may_carry_weaker_evidence(evidence: str) -> None:
    assert finding_errors(_finding(severity="MAJOR", evidence=evidence)) == []


def test_a_waived_blocking_finding_is_rejected() -> None:
    errors = finding_errors(_finding(status="WAIVED_BY_OVERRIDE"))
    assert errors == [("$.severity", "'BLOCKING' is not one of ['MAJOR', 'MINOR', 'INFO']")]


def test_a_waived_major_finding_is_accepted() -> None:
    assert finding_errors(_finding(severity="MAJOR", status="WAIVED_BY_OVERRIDE")) == []


@pytest.mark.parametrize("field", spec.yaml_required_lists(spec.b4())[0])
def test_each_b4_required_field_is_required(field: str) -> None:
    finding = _finding()
    del finding[field]
    assert ("$", f"'{field}' is a required property") in finding_errors(finding)


def test_b4_enums_and_rule_pattern_are_kept() -> None:
    block = spec.b4()
    for key in ("severity", "evidence", "cause", "status"):
        assert FINDING_SCHEMA["properties"][key]["enum"] == spec.yaml_enum(block, key)
    rule = re.search(r'rule:\s+\{ type: string, pattern: "([^"]+)" \}', block)
    assert rule is not None
    assert rule.group(1) == FINDING_SCHEMA["properties"]["rule"]["pattern"]
