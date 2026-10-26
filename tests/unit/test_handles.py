"""Handle patterns (spec §0.3), checked against the spec's own examples."""

from __future__ import annotations

import re

import pytest

from nsres.domain import handles
from tests import spec_text as spec


def _spec_table() -> list[tuple[str, str]]:
    block = spec.section("### 0.3")
    prefixes = spec.table_column(block, "| Prefix", 0)
    examples = spec.table_column(block, "| Prefix", 2)
    rows = []
    for prefix, example in zip(prefixes, examples, strict=True):
        match = re.match(rf"{re.escape(prefix)}\S+", example)
        assert match is not None, f"§0.3 example {example!r} does not start with {prefix}"
        rows.append((prefix.rstrip("-"), match.group(0)))
    return rows


SPEC_ROWS = _spec_table()

# Handles the spec uses outside §0.3, with where each example comes from.
EXTENDED_EXAMPLES = [
    ("SUP", "SUP-1"),  # §8.4 public.threads.hidden
    ("SUP", "SUP-2"),  # §8.4
    ("ANCHOR", "ANCHOR-02"),  # §6.3
    ("CV", "CV-PKT-007-r3"),  # §8.2 A confidence_vector_ref
    ("RGM", "RGM-001"),  # §17.8
    ("RGM", "RGM-002"),  # §17.8
    ("MCH", "MCH-001"),  # §17.8
    ("MCH", "MCH-002"),  # §17.8
    # §17.4 names these prefixes without an example; the widths follow MCH- and RGM-.
    ("SUB", "SUB-001"),
    ("MCC", "MCC-001"),
    ("RSV", "RSV-001"),  # §17.4 writes RES-; D-005
    ("CAP", "CAP-001"),
    ("EFF", "EFF-001"),
    ("TRC", "TRC-001"),
    ("REL", "REL-0001"),  # §3.3 gives Relation no prefix; D-010
]

# Every other example the spec gives for a §0.3 prefix, beyond the table's own.
MORE_SPEC_EXAMPLES = [
    ("LOC", "LOC-001c"),  # §8.4
    ("EVT", "EVT-0104"),
    ("KG", "KG-0031"),
    ("CE", "CE-0012"),
    ("NOD", "NOD-01-04"),  # §8.4
    ("BT", "BT-007-04"),
    ("PKT", "PKT-007-r3"),
    ("DRF", "DRF-007-01"),  # Appendix A.6
    ("FND", "FND-007-01-05"),  # Appendix A.7
    ("FND", "FND-R-01"),  # Appendix A.3
    ("RUN", "RUN-X-0212"),  # §8.4
    ("RUN", "RUN-R-0047"),
    ("RES", "RES-0011"),
    ("CHR", "CHR-101"),  # §17.8
    ("SCN", "SCN-212"),  # §17.8
    ("Q", "Q-03"),
    ("THR", "THR-04"),
]

ALL_EXAMPLES = SPEC_ROWS + EXTENDED_EXAMPLES + MORE_SPEC_EXAMPLES


def test_spec_prefixes_equal_the_section_0_3_table() -> None:
    assert [prefix for prefix, _ in SPEC_ROWS] == list(handles.SPEC_PREFIXES)


def test_extended_prefixes_do_not_redefine_spec_prefixes() -> None:
    assert not set(handles.EXTENDED_PREFIXES) & set(handles.SPEC_PREFIXES)


@pytest.mark.parametrize(("prefix", "example"), ALL_EXAMPLES, ids=[e for _, e in ALL_EXAMPLES])
def test_example_matches_its_own_prefix(prefix: str, example: str) -> None:
    assert handles.is_handle(prefix, example)
    assert re.fullmatch(handles.pattern(prefix), example)
    assert handles.prefix_of(example) == prefix


@pytest.mark.parametrize(("prefix", "example"), ALL_EXAMPLES, ids=[e for _, e in ALL_EXAMPLES])
def test_example_is_rejected_by_every_other_prefix(prefix: str, example: str) -> None:
    accepted_by = [other for other in handles.ALL_PREFIXES if handles.is_handle(other, example)]
    assert accepted_by == [prefix]


@pytest.mark.parametrize(
    "value",
    [
        "CHR-1",
        "chr-001",
        "CHR001",
        "CHR-001 ",
        "EVT-104",
        "PKT-007",
        "PKT-007-3",
        "FND-07-01-05",
        "LOC-001AB",
        "",
    ],
)
def test_malformed_handles_match_no_prefix(value: str) -> None:
    assert handles.prefix_of(value) is None


def test_one_of_accepts_only_the_listed_prefixes() -> None:
    entity = re.compile(handles.one_of("CHR", "LOC", "OBJ", "GRP"))
    assert entity.fullmatch("OBJ-004")
    assert entity.fullmatch("LOC-001c")
    assert not entity.fullmatch("EVT-0104")


def test_resolution_and_resource_handles_do_not_collide() -> None:
    assert handles.prefix_of("RES-0019") == "RES"
    assert handles.prefix_of("RSV-001") == "RSV"
    assert not handles.is_handle("RSV", "RES-0019")
