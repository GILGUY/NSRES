"""Canonical JSON and packet hashing (spec §8.1, PK-9; plan A-14)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nsres.domain.canonical import (
    CanonicalJSONError,
    canonical_bytes,
    canonical_text,
    content_hash,
    packet_hashes,
    verify_packet_hashes,
    with_packet_hashes,
)
from nsres.domain.vocab import BeatType

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "fixtures" / "harrow-house" / "PKT-007-r3.example.json"


def test_objects_equal_up_to_key_order_give_identical_bytes_and_hashes() -> None:
    first = {"b": 1, "a": {"y": [1, 2], "x": "z"}, "c": None}
    second = {"c": None, "a": {"x": "z", "y": [1, 2]}, "b": 1}
    assert list(first) != list(second)
    assert canonical_bytes(first) == canonical_bytes(second)
    assert content_hash(first) == content_hash(second)
    assert canonical_text(first) == '{"a":{"x":"z","y":[1,2]},"b":1,"c":null}'


def test_keys_sort_by_code_point() -> None:
    assert canonical_text({"é": 1, "z": 2, "Z": 3, "a": 4}) == '{"Z":3,"a":4,"z":2,"é":1}'


def test_non_ascii_text_is_written_as_utf8_not_escaped() -> None:
    text = "Mrs. Dorran\u2019s kitchen \u2014 caf\u00e9, 1893"
    assert canonical_text(text) == f'"{text}"'
    assert canonical_bytes(text) == f'"{text}"'.encode()


def test_control_characters_and_quotes_are_escaped() -> None:
    assert canonical_text('a"b\\c\n\t\x01') == '"a\\"b\\\\c\\n\\t\\u0001"'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (-7, "-7"),
        (2**60, "1152921504606846976"),
        (1.0, "1"),
        (-0.0, "0"),
        (6.0, "6"),
        (0.1, "0.1"),
        (0.08, "0.08"),
        (2.5e-07, "2.5e-07"),
        (1e21, "1e+21"),
    ],
)
def test_integers_and_decimals_use_shortest_round_trip_form(value: float, expected: str) -> None:
    assert canonical_text(value) == expected
    assert json.loads(expected) == value


def test_integral_float_and_integer_hash_the_same() -> None:
    assert content_hash({"priority": 6.0}) == content_hash({"priority": 6})


def test_nested_arrays_keep_their_order() -> None:
    assert canonical_text([[3, 1], [2, [5, 4]], []]) == "[[3,1],[2,[5,4]],[]]"


def test_booleans_null_and_enums() -> None:
    assert canonical_text([True, False, None, BeatType.SUSTAIN]) == '[true,false,null,"SUSTAIN"]'


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_refused(value: float) -> None:
    with pytest.raises(CanonicalJSONError, match="non-finite"):
        canonical_text({"score": value})


@pytest.mark.parametrize("value", [{1: "a"}, {"a": b"bytes"}, {"a": {1, 2}}])
def test_non_json_values_are_refused(value: Any) -> None:
    with pytest.raises(CanonicalJSONError):
        canonical_text(value)


def test_canonical_text_matches_sorted_compact_json_for_plain_data() -> None:
    plain = {"z": [1, "two", {"k": None}], "a": "ünïcode", "m": False}
    expected = json.dumps(plain, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert canonical_text(plain) == expected


def _packet() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(PACKET.read_text(encoding="utf-8"))
    return loaded


def test_fixture_packet_hashes_verify() -> None:
    assert verify_packet_hashes(_packet()) == []


def test_editing_the_public_section_breaks_both_hashes() -> None:
    packet = _packet()
    packet["public"]["setting"]["setting_state"].append("a new detail")
    problems = verify_packet_hashes(packet)
    assert len(problems) == 2
    assert problems[0].startswith("packet_hash")
    assert problems[1].startswith("public_hash")


def test_editing_the_sealed_section_breaks_only_the_packet_hash() -> None:
    packet = _packet()
    packet["sealed"]["forbidden_propositions"].append("INF-099")
    problems = verify_packet_hashes(packet)
    assert len(problems) == 1
    assert problems[0].startswith("packet_hash")


def test_packet_hash_excludes_the_hash_fields_themselves() -> None:
    packet = _packet()
    stripped = {k: v for k, v in packet.items() if k not in ("packet_hash", "public_hash")}
    assert packet_hashes(stripped) == packet_hashes(packet)
    assert with_packet_hashes(stripped) == packet


def test_a_packet_without_public_cannot_be_hashed() -> None:
    with pytest.raises(CanonicalJSONError, match="public"):
        packet_hashes({"sealed": {}})
