"""A-17: every closed vocabulary equals the spec text and the JSON Schema enums.

Each vocabulary is compared with the place the spec defines it: a §10.2 TypeScript union, a
B.3 or B.4 schema enum, or a prose table or list. Where the spec defines a vocabulary in two
places, both are checked. ``tests/integration/test_vocabulary_drift.py`` proves the check
bites: it removes ``SUSTAIN`` from a copy of the code and shows this file failing.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import StrEnum
from typing import Any

import pytest

from nsres.domain import schemas, vocab
from nsres.domain.vocab import values
from tests import spec_text as spec

Source = Callable[[], list[str]]


def _upper(words: list[str]) -> list[str]:
    return [word.upper() for word in words]


def _gate_table() -> list[tuple[str, list[str]]]:
    block = spec.section("### 0.7")
    gates = spec.table_column(block, "**Typed gates.**", 0)
    outcomes = spec.table_column(block, "**Typed gates.**", 3)
    return [
        (gate, [o.strip() for o in row.split(",")])
        for gate, row in zip(gates, outcomes, strict=True)
    ]


def _micro_fact_codes() -> list[str]:
    return spec.table_column(spec.section("### 0.7"), "**Micro-fact decisions", 0)


def _pov_modes() -> list[str]:
    rows = spec.table_column(spec.section("### 7.4"), "| POV mode", 0)
    modes = [row.split(" (")[0] for row in rows]
    assert "UNRELIABLE (modifier on any mode)" in rows, "UNRELIABLE is no longer a modifier"
    return [mode for mode in modes if mode != "UNRELIABLE"]


def _model_version_states() -> list[str]:
    block = spec.section("### 5.4")
    sources = spec.table_column(block, "**Model version lifecycle.**", 0)
    targets = spec.table_column(block, "**Model version lifecycle.**", 3)
    states: set[str] = set()
    for cell in sources + targets:
        states |= set(re.findall(r"\b[A-Z]{4,}\b", cell))
    return sorted(states)


def _audit_kinds() -> list[str]:
    phrases = spec.listed(r"\| Audit log \| ([^|]+) \|", spec.section("### 10.4"))
    normalized = {
        "Gate records": "GATE",
        "RES records": "RES",
        "transitions": "TRANSITION",
        "LLM call logs": "LLM_CALL",
    }
    assert set(phrases) == set(normalized), f"§10.4 audit-log contents changed: {phrases}"
    return [normalized[phrase] for phrase in phrases]


def _pressure_components() -> list[str]:
    found = spec.listed(r"Before \(([^)]+)\)", spec.section("### 8.2"))
    return [item.split()[0] for item in found]


def _ebnf_alternatives(block: str, rule: str) -> list[str]:
    match = re.search(rf"^{re.escape(rule)}([^;]+);", block, re.M)
    assert match is not None, f"EBNF rule {rule!r} not found"
    return [name.strip().upper() for name in match.group(1).split("|")]


def _b3_flags() -> list[str]:
    match = re.search(r'pattern: "\^\((PLAN_ONLY[^)]+)\)\$"', spec.b3())
    assert match is not None, "B.3 flags pattern not found"
    return [item for item in match.group(1).split("|") if ":" not in item]


SOURCES: dict[type[StrEnum], list[tuple[str, Source]]] = {
    vocab.Status: [
        ("§10.2 type Status", lambda: spec.ts_type("Status")),
        (
            "§0.7 record statuses",
            lambda: spec.table_column(spec.section("### 0.7"), "**Record statuses.**"),
        ),
    ],
    vocab.Tier: [("§10.2 BaseRecord.tier", lambda: spec.ts_field("BaseRecord", "tier"))],
    vocab.Provenance: [("§10.2 type Provenance", lambda: spec.ts_type("Provenance"))],
    vocab.Confidence: [("§10.2 type Confidence", lambda: spec.ts_type("Confidence"))],
    vocab.Channel: [("§10.2 type Channel", lambda: spec.ts_type("Channel"))],
    vocab.Plane: [("§10.2 BaseRecord.plane", lambda: spec.ts_field("BaseRecord", "plane"))],
    vocab.EntityKind: [("§10.2 Entity.kind", lambda: spec.ts_field("Entity", "kind"))],
    vocab.Significance: [
        ("§10.2 Entity.significance", lambda: spec.ts_field("Entity", "significance"))
    ],
    vocab.Precision: [
        ("§10.2 StoryTime.precision", lambda: spec.ts_field("StoryTime", "precision"))
    ],
    vocab.ConstraintKind: [
        ("§10.2 TemporalConstraint.kind", lambda: spec.ts_field("TemporalConstraint", "kind"))
    ],
    vocab.EffectOp: [
        ("§10.2 Effect.op", spec.ts_effect_ops),
        (
            "§10.9 effect grammar",
            lambda: _ebnf_alternatives(spec.section("### 10.9"), "effect        ="),
        ),
    ],
    vocab.MechanicsEffectOp: [
        (
            "§17.4 effect-language extensions",
            lambda: _ebnf_alternatives(spec.section("### 17.4"), "effect   +="),
        )
    ],
    vocab.EffectAt: [("§10.2 Effect.at", spec.ts_effect_at)],
    vocab.ParticipantRole: [
        ("§10.2 Event.participants.role", lambda: spec.ts_inline("Event", "role"))
    ],
    vocab.RenderStatus: [
        ("§10.2 Event.renderStatus", lambda: spec.ts_field("Event", "renderStatus"))
    ],
    vocab.Visibility: [("§10.2 Event.visibility", lambda: spec.ts_field("Event", "visibility"))],
    vocab.TruthValue: [("§10.2 Fact.truth", lambda: spec.ts_field("Fact", "truth"))],
    vocab.CausalEdgeType: [("§10.2 CausalEdge.type", lambda: spec.ts_field("CausalEdge", "type"))],
    vocab.ThreadRank: [("§10.2 Thread.rank", lambda: spec.ts_field("Thread", "rank"))],
    vocab.ThreadVisibility: [
        ("§10.2 Thread.visibilitySchedule", lambda: spec.ts_inline("Thread", "visibility"))
    ],
    vocab.BeatType: [
        ("§10.2 Beat.type", lambda: spec.ts_field("Beat", "type")),
        ("B.3 beat.type", lambda: spec.yaml_enum(spec.b3(), "type")),
    ],
    vocab.Severity: [
        ("§10.2 Finding.severity", lambda: spec.ts_field("Finding", "severity")),
        ("B.4 severity", lambda: spec.yaml_enum(spec.b4(), "severity")),
    ],
    vocab.FindingEvidence: [
        ("§10.2 Finding.evidence", lambda: spec.ts_field("Finding", "evidence")),
        ("B.4 evidence", lambda: spec.yaml_enum(spec.b4(), "evidence")),
    ],
    vocab.FindingCause: [
        ("§10.2 Finding.cause", lambda: spec.ts_field("Finding", "cause")),
        ("B.4 cause", lambda: spec.yaml_enum(spec.b4(), "cause")),
    ],
    vocab.FindingStatus: [
        ("§10.2 Finding.status", lambda: spec.ts_field("Finding", "status")),
        ("B.4 status", lambda: spec.yaml_enum(spec.b4(), "status")),
    ],
    vocab.Band: [
        ("§10.2 ConfidenceVector.band", lambda: spec.ts_field("ConfidenceVector", "band"))
    ],
    vocab.PacketStatus: [("B.3 status", lambda: spec.yaml_enum(spec.b3(), "status"))],
    vocab.PacketFlag: [("B.3 flags pattern", _b3_flags)],
    vocab.Gate: [("§0.7 typed gates", lambda: [gate for gate, _ in _gate_table()])],
    vocab.GateOutcome: [
        (
            "§0.7 gate outcomes and micro-fact codes",
            lambda: sorted({o for _, row in _gate_table() for o in row} | set(_micro_fact_codes())),
        )
    ],
    vocab.ModelVersionState: [("§5.4 model version lifecycle", _model_version_states)],
    vocab.PovMode: [("§7.4 POV modes", _pov_modes)],
    vocab.DeliveryMode: [("§7.7 RV-1", lambda: spec.listed(r"planned mode \(([^)]+)\)"))],
    vocab.VisibilityClass: [
        ("§7.5 visibility classes", lambda: spec.table_column(spec.section("### 7.5"), "| Class"))
    ],
    vocab.ThreadRole: [
        ("§7.8 thread roles", lambda: spec.table_column(spec.section("### 7.8"), "| Role assigned"))
    ],
    vocab.OutcomeKind: [
        ("§8.2 K required_outcomes", lambda: spec.listed(r"\{kind ([A-Z, ]+?(?:or [A-Z]+));"))
    ],
    vocab.Anachrony: [
        ("§8.2 B anachrony", lambda: spec.listed(r"status \| ([A-Z, ]+), plus frame ref"))
    ],
    vocab.InventionClass: [
        ("§3.6 invention classes", lambda: spec.table_column(spec.section("### 3.6"), "| Class"))
    ],
    vocab.Hardness: [
        ("§17.6 hardness", lambda: spec.listed(r"A work declares ([A-Z, ]+or [A-Z]+) mechanics"))
    ],
    vocab.CanonRuleClass: [
        ("§3.3 Canon Rule class", lambda: spec.listed(r"id, class \(([A-Z, ]+)\)"))
    ],
    vocab.ConservationClass: [
        ("§17.4 Resource", lambda: spec.listed(r"conservation class \(([A-Z, ]+);"))
    ],
    vocab.MechanicClass: [
        ("§17.3 SI class", lambda: _upper(spec.listed(r"Name, class \(([a-z, ]+)\)")))
    ],
    vocab.MechanicAxis: [
        ("§17.2 load bearers", lambda: spec.listed(r"load bearers \(([A-Z, ]+)\)"))
    ],
    vocab.SheetMarker: [
        ("§17.3 sheet markers", lambda: spec.listed(r"Fields may be ([A-Z_]+ or [A-Z_]+),"))
    ],
    vocab.InteractionKind: [
        (
            "§17.3 interaction matrix",
            lambda: _upper(spec.listed(r"interaction matrix: ([a-z, ]+) \|")),
        )
    ],
    vocab.AuditKind: [("§10.4 audit log", _audit_kinds)],
    vocab.DraftValidationState: [
        ("L14 outputs", lambda: spec.listed(r"draft state ([A-Z]+ or [A-Z]+)\."))
    ],
    vocab.PressureComponent: [("§8.2 I narrative_pressure example", _pressure_components)],
}


def test_every_vocabulary_has_a_spec_source() -> None:
    assert set(SOURCES) == set(vocab.ALL_VOCABULARIES)


CASES = [
    pytest.param(vocabulary, label, source, id=f"{vocabulary.__name__}: {label}")
    for vocabulary, sources in SOURCES.items()
    for label, source in sources
]


@pytest.mark.parametrize(("vocabulary", "label", "source"), CASES)
def test_vocabulary_equals_spec(vocabulary: type[StrEnum], label: str, source: Source) -> None:
    from_spec = source()
    assert len(from_spec) == len(set(from_spec)), f"{label} lists a value twice: {from_spec}"
    code = values(vocabulary)
    assert set(code) == set(from_spec), (
        f"{vocabulary.__name__} drifted from {label}: "
        f"only in code {sorted(set(code) - set(from_spec))}, "
        f"only in spec {sorted(set(from_spec) - set(code))}"
    )


def test_gate_outcomes_per_gate_equal_spec_table() -> None:
    table = dict(_gate_table())
    for gate in vocab.Gate:
        expected = set(table[gate.value])
        if gate is vocab.Gate.CANON:
            expected |= set(_micro_fact_codes())
        assert {o.value for o in vocab.GATE_OUTCOMES[gate]} == expected, gate


def _at(document: Any, *path: str) -> Any:
    for key in path:
        document = document[key]
    return document


SCHEMA_ENUMS = [
    (vocab.PacketStatus, schemas.PACKET_SCHEMA, ("properties", "status", "enum")),
    (vocab.BeatType, schemas.PACKET_SCHEMA, ("$defs", "beat", "properties", "type", "enum")),
    (vocab.Gate, schemas.PACKET_SCHEMA, ("$defs", "gate_record", "properties", "gate", "enum")),
    (
        vocab.Channel,
        schemas.PACKET_SCHEMA,
        (
            "$defs",
            "information",
            "properties",
            "known_information",
            "items",
            "properties",
            "channel",
            "enum",
        ),
    ),
    (vocab.PovMode, schemas.PACKET_SCHEMA, ("$defs", "pov", "properties", "mode", "enum")),
    (vocab.Severity, schemas.FINDING_SCHEMA, ("properties", "severity", "enum")),
    (vocab.FindingEvidence, schemas.FINDING_SCHEMA, ("properties", "evidence", "enum")),
    (vocab.FindingCause, schemas.FINDING_SCHEMA, ("properties", "cause", "enum")),
    (vocab.FindingStatus, schemas.FINDING_SCHEMA, ("properties", "status", "enum")),
    (vocab.Provenance, schemas.FINDING_SCHEMA, ("properties", "provenance", "enum")),
    (vocab.Plane, schemas.FINDING_SCHEMA, ("properties", "plane", "enum")),
]


@pytest.mark.parametrize(
    ("vocabulary", "schema", "path"),
    SCHEMA_ENUMS,
    ids=[f"{v.__name__} at {'/'.join(p[:-1])}" for v, _, p in SCHEMA_ENUMS],
)
def test_schema_enum_equals_vocabulary(
    vocabulary: type[StrEnum], schema: dict[str, Any], path: tuple[str, ...]
) -> None:
    assert _at(schema, *path) == values(vocabulary)


def test_severity_rank_orders_most_severe_first() -> None:
    ranked = sorted(vocab.Severity, key=vocab.severity_rank)
    assert ranked == [
        vocab.Severity.BLOCKING,
        vocab.Severity.MAJOR,
        vocab.Severity.MINOR,
        vocab.Severity.INFO,
    ]
