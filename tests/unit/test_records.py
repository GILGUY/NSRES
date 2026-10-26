"""Record types (spec §10.2, §3.3, §17.4; DECISIONS D-005, D-007 to D-009).

Sample values come from the Harrow House running example (Appendix A) and the Drowned
Provinces example (§17.8). Story-times are minutes from a work epoch of 1893-10-01T00:00.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from nsres.domain import records as r
from nsres.domain.canonical import canonical_bytes
from nsres.domain.schemas import finding_errors
from nsres.domain.uuid7 import Uuid7Generator
from nsres.domain.vocab import (
    AuditKind,
    Band,
    BeatType,
    CanonRuleClass,
    CausalEdgeType,
    Channel,
    Confidence,
    ConservationClass,
    ConstraintKind,
    DeliveryMode,
    DraftValidationState,
    EffectAt,
    EffectOp,
    EntityKind,
    FindingCause,
    FindingEvidence,
    FindingStatus,
    Gate,
    GateOutcome,
    InteractionKind,
    MechanicAxis,
    MechanicClass,
    ParticipantRole,
    Plane,
    PovMode,
    Precision,
    Provenance,
    RenderStatus,
    Severity,
    SheetMarker,
    Significance,
    Status,
    ThreadRank,
    ThreadVisibility,
    Tier,
    TruthValue,
    Visibility,
    VisibilityClass,
)

_IDS = Uuid7Generator(lambda: 1_729_879_320_000, seed=2026)
DAY = 24 * 60


def uid() -> str:
    return _IDS.new_str()


def minutes(day: int, hour: int, minute: int) -> int:
    """Minutes from 1893-10-01T00:00 to 1893-10-<day>T<hour>:<minute>."""
    return (day - 1) * DAY + hour * 60 + minute


def core(
    handle: str, plane: Plane = Plane.REALITY, status: Status = Status.ACCEPTED
) -> dict[str, Any]:
    return {
        "uuid": uid(),
        "handle": handle,
        "rev": 1,
        "status": status,
        "provenance": Provenance.AUTHOR,
        "plane": plane,
        "tx": r.TxRange(from_rev=47, to_rev=None),
    }


def point(at: int, slack: int = 0) -> r.Window:
    return r.Window(lo=at - slack, hi=at + slack)


def samples() -> list[Any]:
    """One instance of every record type, built from spec examples."""
    night = r.StoryTime(
        start=point(minutes(14, 22, 40)), end=point(minutes(14, 22, 45)), precision=Precision.MINUTE
    )
    scene_window = r.StoryTime(
        start=point(minutes(15, 7, 40), 7),
        end=point(minutes(15, 8, 10), 7),
        precision=Precision.QUARTER_HOUR,
    )
    finding_core = {
        key: value for key, value in core("FND-007-01-01", Plane.CONTROL).items() if key != "status"
    }
    return [
        r.Entity(
            **core("CHR-001", status=Status.CANON),
            kind=EntityKind.CHARACTER,
            canonical_name="Mara Voss",
            aliases=("Mrs. Voss",),
            fixed_traits={"role": "housekeeper"},
            persistent_defaults={"location": "LOC-001c", "alive": True},
        ),
        r.Entity(
            **core("OBJ-001", status=Status.CANON),
            kind=EntityKind.OBJECT,
            canonical_name="the ledger",
            significance=Significance.PLOT_OBJECT,
            tier=Tier.PUBLISHED,
        ),
        r.CanonRule(
            **core("CAN-014", status=Status.CANON),
            rule_class=CanonRuleClass.PROHIBITION,
            statement_structured="not exists(OBJ, kind=telephone, location=LOC-001)",
            statement="There is no telephone at Harrow House",
        ),
        r.Event(
            **core("EVT-0104"),
            type="REMOVE",
            label="Jonah removes the ledger",
            time=night,
            constraints=(
                r.TemporalConstraint(
                    kind=ConstraintKind.METRIC,
                    from_ref="EVT-0104",
                    to_ref="EVT-0106",
                    bounds=(3, 10),
                ),
                r.TemporalConstraint(
                    kind=ConstraintKind.ALLEN,
                    from_ref="EVT-0104",
                    to_ref="ANCHOR-02",
                    relations=("BEFORE", "MEETS"),
                ),
            ),
            location="LOC-001a",
            participants=(r.Participant(entity="CHR-004", role=ParticipantRole.AGENT),),
            preconditions=("custody(OBJ-002) == CHR-004",),
            effects=(
                r.TransferEffect(object_ref="OBJ-001", from_ref="LOC-001a", to_ref="CHR-004"),
                r.SetEffect(target="LOC-001a", attr="lock", value="LOCKED", at=EffectAt.END),
                r.SetEffect(
                    target="CHR-004", attr="carrying", value=True, at=r.Offset(offset_min=2)
                ),
                r.GrantEffect(
                    holder="CHR-004",
                    prop="INF-002",
                    channel=Channel.WITNESSED,
                    confidence=Confidence.CERTAIN,
                ),
                r.ClaimEffect(speaker="CHR-005", prop="CLM-007", truth=False, hearers=("CHR-002",)),
                r.LifecycleEffect(op=EffectOp.CREATE, target="TRC-001"),
            ),
            visibility=r.HiddenUntil(hidden_until="RVL-02"),
            render_status=RenderStatus.DEFERRED,
        ),
        r.Fact(
            **core("INF-002"),
            subject="CHR-004",
            predicate="removed",
            object_value="OBJ-001",
            valid=r.StoryInterval(from_min=minutes(14, 22, 40), to_min=None),
            truth=TruthValue.TRUE,
            created_by="EVT-0104",
            secret=r.Secret(
                holders=("CHR-004",),
                concealed_from=("CHR-002",),
                strategy="silence",
                reveal="RVL-02",
            ),
        ),
        r.Claim(
            **core("CLM-007"),
            holder="CHR-005",
            proposition="Edmund's heart was weak",
            truth_value=TruthValue.FALSE,
        ),
        r.KnowledgeGrant(
            **core("KG-0031"),
            holder="CHR-001",
            prop="INF-006",
            time=minutes(14, 22, 45),
            channel=Channel.WITNESSED,
            confidence=Confidence.CERTAIN,
            source_event="EVT-0106",
            polarity=1,
        ),
        r.CausalEdge(
            **core("CE-0012"),
            from_ref="EVT-0101",
            to_ref="EVT-0105",
            type=CausalEdgeType.CAUSES,
            justification="The poisoned brandy kills Edmund",
            strength=0.9,
        ),
        r.Thread(
            **core("THR-02", Plane.TELLING),
            name="Jonah's claim",
            rank=ThreadRank.SECONDARY,
            dramatic_question="What is Jonah to Edmund?",
            visibility_schedule=(
                r.VisibilityStep(from_nt="1.01.1", visibility=ThreadVisibility.HIDDEN),
            ),
            nodes=(r.ThreadNode(event="EVT-0104", role="secret act", order=3),),
        ),
        r.Scene(
            **core("SCN-007", Plane.TELLING),
            nt="1.03.2",
            window=scene_window,
            location="LOC-001c",
            pov=r.ScenePov(character="CHR-001", mode=PovMode.CLOSE_THIRD),
            participants=("CHR-001", "CHR-002", "CHR-004", "CHR-006"),
            renders_nodes=("NOD-01-04", "NOD-04-02"),
            purpose="Hale questions the household; Mara chooses to hide her sighting of Jonah",
            planned_delta={"reader": ["+INF-006 SHOWN"], "opens": ["Q-03"]},
            length_target=(2000, 2800),
            pipeline_state="PACKET_FROZEN",
        ),
        r.Beat(
            **core("BT-007-04", Plane.TELLING),
            scene="SCN-007",
            order=4,
            type=BeatType.DECISION,
            actors=("CHR-001",),
            outcome="Asked whom she saw, Mara names no one",
            mandatory=True,
        ),
        r.Finding(
            **finding_core,
            rule="AU-02",
            severity=Severity.BLOCKING,
            spans=(r.Span(draft="DRF-007-01", start=140, end=156, quote="of Scotland Yard"),),
            records=("CHR-002",),
            evidence=FindingEvidence.CONTENT_READ,
            detection_confidence=0.99,
            cause=FindingCause.DRAFTER_VIOLATION,
            repairs=("Remove the affiliation",),
            status=FindingStatus.OPEN,
        ),
        r.ConfidenceVector(
            **core("CV-PKT-007-r3", Plane.CONTROL),
            subject="PKT-007-r3",
            scores=(
                r.Score(
                    type="packet_readiness",
                    factors=(
                        r.Factor(
                            name="pre_draft_checks",
                            weight=0.35,
                            raw=1.0,
                            ceiling=1.0,
                            evidence=("CC-1",),
                            reason="all PASS",
                        ),
                        r.Factor(
                            name="dependency_resolution",
                            weight=0.15,
                            raw=0.75,
                            ceiling=1.0,
                            evidence=(),
                            reason="DEPENDENCY:SCN-006",
                        ),
                    ),
                    value=0.9625,
                ),
            ),
            caps=(r.Cap(condition="open BLOCKING", cap=0.69, applied=False),),
            aggregate=0.9625,
            band=Band.READY,
        ),
        r.RevealRecord(
            **core("RVL-02", Plane.TELLING),
            targets=("INF-002",),
            nt="2.09",
            mode=DeliveryMode.STATED,
            prerequisites=("INF-006", "INF-008"),
            retro_scope=("1.01.1", "2.09"),
        ),
        r.Draft(
            **core("DRF-007-01", Plane.RENDERING, Status.PROPOSAL),
            scene="SCN-007",
            packet="PKT-007-r3",
            packet_hash="sha256:943e590aed3f7f93ccf1d3385113fac842d94c8d873b6cf17cb4f8deb7a13b52",
            drafter="drafter-a",
            text_hash="sha256:" + "1" * 64,
            emergent_details=("a candle burned down to a stub on the dresser",),
            beat_map={"BT-007-02": ("S4",), "BT-007-03": ("S5",)},
            draft_state="FAILED",
        ),
        r.ResolutionRecord(
            **core("RES-0011", Plane.CONTROL),
            findings=("FND-R-01",),
            chosen_repair="Bridge: Hale already at The Bell (EVT-0090)",
            rejected_repairs=("Move SCN-007 after 09:30",),
            records_created=("EVT-0090", "EVT-0109"),
            records_deprecated=("EVT-0098",),
        ),
        r.Substrate(
            **core("SUB-001", status=Status.CANON),
            name="the tide current",
            medium="field",
            ambient=(
                r.AmbientLevel(
                    location="LOC-201",
                    interval=r.StoryInterval(from_min=None, to_min=None),
                    level=1.0,
                ),
            ),
        ),
        r.Regime(
            **core("RGM-001", status=Status.CANON),
            name="the Drowned Provinces",
            mechanics=("MCH-001", "MCH-002"),
            locations=("LOC-201",),
            story_time=r.StoryInterval(from_min=None, to_min=None),
            precedence=1,
        ),
        r.Regime(
            **core("RGM-002", status=Status.CANON),
            name="the Saltmarsh",
            mechanics=(),
            locations=("LOC-202",),
            story_time=r.StoryInterval(from_min=None, to_min=None),
            interface_zones=("the marsh edge",),
            precedence=2,
        ),
        r.Mechanic(
            **core("MCH-001", status=Status.CANON),
            name="Binding",
            mechanic_class=MechanicClass.LEARNED,
            si=r.SheetEntry(content="Phase-locks a target object to an anchor point"),
            ep=r.SheetEntry(
                content="Non-living objects; line of sight; RGM-001 only; cancelled by Shear"
            ),
            is_=r.SheetEntry(
                content="One practitioner; one minute of contact first; 10-second casting"
            ),
            ft=r.SheetEntry(content="Cost 5, 15, or 40 by size, plus 1 per metre"),
            sr=r.SheetEntry(
                content="Fails at zero reserve or when cut by Shear; more than three locks cascade"
            ),
            di=r.SheetEntry(marker=SheetMarker.UNDETERMINED),
            hard_limits=("Cannot bind a living creature",),
            interactions=(r.Interaction(other="MCH-002", kind=InteractionKind.CANCELS),),
            reader_exposure={MechanicAxis.FT: ("RVL-04",)},
        ),
        r.MechanicsConstant(
            **core("MCC-001", status=Status.CANON),
            name="binding upkeep",
            value=2.0,
            unit="per hour",
        ),
        r.Resource(
            **core("RSV-001"),
            owner="CHR-101",
            maximum=100.0,
            regeneration_rule="5 per hour at rest; none while sustaining",
            decay="none",
            conservation_class=ConservationClass.SOURCED,
        ),
        r.Capability(**core("CAP-001"), practitioner="CHR-101", mechanic="MCH-001", proficiency=2),
        r.ActiveEffect(
            **core("EFF-001"),
            working="EVT-2120",
            mechanic="MCH-001",
            interval=r.StoryInterval(from_min=minutes(20, 18, 0), to_min=minutes(21, 4, 0)),
            upkeep_per_hour=2.0,
            funding_resource="RSV-001",
            state="HOLDING",
        ),
        r.Trace(
            **core("TRC-001"),
            what="frost-rime on the anchor",
            location="LOC-203",
            emitted_by="EVT-2120",
            decay="24 hours",
            perceptibility=("visible to anyone", "detectable by binders within 30 metres"),
        ),
        r.GateRecord(
            uuid=uid(),
            gate=Gate.STRUCTURE,
            outcome=GateOutcome.ACCEPT,
            subject="PKT-007-r3",
            subject_uuid=uid(),
            subject_rev=3,
            actor="author",
            time="2026-10-25T19:02Z",
            model_version="canon@r12/truth@r47",
        ),
        r.AuditRecord(
            seq=0,
            uuid=uid(),
            kind=AuditKind.TRANSITION,
            subject="PKT-007-r3",
            from_state="PACKET_VALID",
            to_state="FROZEN",
            trigger="STRUCTURE gate ACCEPT",
            actor="author",
            model_version="canon@r12/truth@r47",
            timestamp="2026-10-25T19:02:11Z",
            prev_hash=None,
            hash="sha256:" + "0" * 64,
        ),
        r.ExtractionRecord(
            uuid=uid(),
            handle="RUN-X-0212",
            scene="SCN-007",
            packet="PKT-007-r3",
            model_version="canon@r12/truth@r47",
            selections=("EVT-0112", "INF-006"),
            exclusions=(r.Exclusion(record="EVT-0101", reason_code="NOT_IN_WINDOW"),),
            classifications={
                "INF-006": VisibilityClass.REVEAL_NOW,
                "INF-002": VisibilityClass.SUPPRESSED,
            },
            manifestations=("SUP-1", "SUP-2"),
            scores={"SUP-1": 0.08, "SUP-2": 0.11},
            rule_trace=(r.RuleTraceEntry(rule="CC-7", result="PASS", records=("SUP-1",)),),
            sources={"constraints.continuity[0]": ("EVT-0104", "CAN-030")},
            flag_causes={"DEPENDENCY:SCN-006": "RV-2: a prerequisite is in RIS_plan only"},
        ),
        r.ValidationReport(
            uuid=uid(),
            draft="DRF-007-01",
            packet="PKT-007-r3",
            model_version="canon@r12/truth@r47",
            suites=(r.SuiteRun(suite="lexical", coverage=1.0, findings=("FND-007-01-01",)),),
            result=DraftValidationState.FAILED,
        ),
        # Appended so the index-based cases below keep their positions.
        r.Relation(
            **core("REL-0001"),
            from_entity="CHR-004",
            to_entity="CHR-003",
            type="son of",
            valid=r.StoryInterval(from_min=None, to_min=None),
            visibility="HIDDEN until RVL-03",
        ),
        r.Entity(
            **core("OBJ-201", status=Status.CANON),
            kind=EntityKind.OBJECT,
            canonical_name="the anchor stone",
            embedded_mechanics=r.EmbeddedMechanics(
                mechanics=("MCH-001",), charges=("RSV-002",), state="charged"
            ),
        ),
        r.Event(
            **core("EVT-2120"),
            type="WORKING",
            label="Ilse binds the harbour gate",
            time=r.StoryTime(
                start=point(minutes(20, 18, 0)),
                end=point(minutes(20, 18, 0)),
                precision=Precision.MINUTE,
            ),
            location="LOC-203",
            participants=(r.Participant(entity="CHR-101", role=ParticipantRole.AGENT),),
            preconditions=("reserve(RSV-001) >= 60", "regime(LOC-203) includes MCH-001"),
            effects=(
                r.ConsumeEffect(resource="RSV-001", amount=60),
                r.SustainEffect(effect="EFF-001", upkeep_per_hour=2, funding_resource="RSV-001"),
                r.EmitTraceEffect(
                    trace="TRC-001", location="LOC-203", decay="24 hours", perceptibility=("sight",)
                ),
                r.CascadeEffect(
                    mechanic="MCH-001", trigger="more than three locks", outcome="all locks fail"
                ),
                r.LearnEffect(entity="CHR-101", pattern="harbour gate", proficiency_delta=0),
                r.ReleaseEffect(effect="EFF-001"),
            ),
            visibility=Visibility.REVEALABLE,
            render_status=RenderStatus.RENDERED,
        ),
    ]


SAMPLES = samples()


def test_samples_cover_every_record_type() -> None:
    assert {type(sample) for sample in SAMPLES} == set(r.RECORD_TYPES)


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: f"{type(s).__name__}")
def test_json_round_trip_is_lossless(sample: Any) -> None:
    encoded = r.to_json(sample)
    text = canonical_bytes(encoded)
    decoded = r.from_json(type(sample), json.loads(text))
    assert decoded == sample
    assert canonical_bytes(r.to_json(decoded)) == text


def test_json_form_is_snake_case_with_spec_names() -> None:
    event = next(s for s in SAMPLES if isinstance(s, r.Event))
    encoded = r.to_json(event)
    assert encoded["render_status"] == "DEFERRED"
    assert encoded["visibility"] == {"hidden_until": "RVL-02"}
    assert encoded["effects"][0] == {
        "op": "TRANSFER",
        "object": "OBJ-001",
        "from": "LOC-001a",
        "to": "CHR-004",
    }
    assert encoded["effects"][2]["at"] == {"offset_min": 2}
    assert encoded["tx"] == {"from": 47, "to": None}
    assert "not_noticed_by" not in encoded  # optional and unset: omitted
    mechanic = next(s for s in SAMPLES if isinstance(s, r.Mechanic))
    assert set(r.to_json(mechanic)) >= {"class", "si", "ep", "is", "ft", "sr", "di"}


def test_finding_record_json_satisfies_the_finding_schema() -> None:
    finding = next(s for s in SAMPLES if isinstance(s, r.Finding))
    assert finding_errors(r.to_json(finding)) == []
    assert "tier" not in r.to_json(finding)


def test_only_objects_embed_mechanics() -> None:
    mara = SAMPLES[0]
    with pytest.raises(r.RecordError, match="only an object"):
        replace(mara, embedded_mechanics=r.EmbeddedMechanics(mechanics=("MCH-001",), state="x"))


def test_mechanics_effects_decode_by_op() -> None:
    working = SAMPLES[-1]
    assert isinstance(working, r.Event)
    decoded = r.from_json(r.Event, r.to_json(working))
    assert [type(effect).__name__ for effect in decoded.effects] == [
        "ConsumeEffect",
        "SustainEffect",
        "EmitTraceEffect",
        "CascadeEffect",
        "LearnEffect",
        "ReleaseEffect",
    ]


def test_finding_has_no_record_status() -> None:
    assert not issubclass(r.Finding, r.BaseRecord)
    assert issubclass(r.Finding, r.RecordCore)


# --- construction refuses schema-invalid records ------------------------------------------


def _finding() -> r.Finding:
    found = next(s for s in SAMPLES if isinstance(s, r.Finding))
    assert isinstance(found, r.Finding)
    return found


def test_blocking_finding_needs_content_read_evidence() -> None:
    with pytest.raises(r.RecordError, match=r"REQ-9\.1\.1"):
        replace(_finding(), evidence=FindingEvidence.FOUND_BY_METADATA)


def test_blocking_finding_cannot_be_waived() -> None:
    with pytest.raises(r.RecordError, match=r"REQ-9\.1\.2"):
        replace(_finding(), status=FindingStatus.WAIVED_BY_OVERRIDE)
    waived = replace(_finding(), severity=Severity.MAJOR, status=FindingStatus.WAIVED_BY_OVERRIDE)
    assert waived.status is FindingStatus.WAIVED_BY_OVERRIDE


@pytest.mark.parametrize(
    ("index", "changes", "message"),
    [
        (0, {"handle": "LOC-001"}, "expected CHR-"),
        (0, {"handle": "EVT-0104"}, "is not a CHR/LOC/OBJ/GRP handle"),
        (0, {"uuid": "12345678-1234-4234-8234-123456789abc"}, "not a UUIDv7"),
        (0, {"uuid": "01920C3E-7A41-7C2B-9D1E-5F3A8B2C4D6E"}, "canonical lower-case"),
        (0, {"rev": 0}, "at least 1"),
        (0, {"significance": Significance.CLUE}, "objects only"),
        (2, {"tier": Tier.PUBLISHED, "status": Status.ACCEPTED}, "PUBLISHED is a tier of CANON"),
        (3, {"location": "CHR-001"}, "not a LOC handle"),
        (6, {"polarity": 0}, "polarity"),
        (7, {"to_ref": "EVT-0101"}, "loop"),
        (9, {"length_target": (3000, 2000)}, "not a range"),
        (9, {"nt": "1-03-2"}, "narrative position"),
        (10, {"actors": ()}, "at least one actor"),
        (12, {"aggregate": 1.2}, "outside"),
        (21, {"conservation_class": "LEAKY"}, None),
        (13, {"mode": DeliveryMode.MISLED}, "RV-4"),
        (14, {"text_hash": "abc"}, "malformed"),
    ],
    ids=lambda value: str(value)[:40],
)
def test_constructors_refuse_invalid_fields(
    index: int, changes: dict[str, Any], message: str | None
) -> None:
    sample = SAMPLES[index]
    if message is None:
        encoded = r.to_json(sample)
        encoded.update(changes)
        with pytest.raises(r.RecordError):
            r.from_json(type(sample), encoded)
        return
    with pytest.raises(r.RecordError, match=message):
        replace(sample, **changes)


def test_tx_range_and_windows_are_ordered() -> None:
    with pytest.raises(r.RecordError):
        r.TxRange(from_rev=5, to_rev=5)
    with pytest.raises(r.RecordError):
        r.Window(lo=10, hi=9)
    with pytest.raises(r.RecordError):
        r.StoryInterval(from_min=10, to_min=9)
    with pytest.raises(r.RecordError, match="needs bounds"):
        r.TemporalConstraint(kind=ConstraintKind.METRIC, from_ref="EVT-0104", to_ref="EVT-0106")
    with pytest.raises(r.RecordError, match="relation"):
        r.TemporalConstraint(kind=ConstraintKind.ALLEN, from_ref="EVT-0104", to_ref="EVT-0106")


def test_sheet_entry_holds_content_or_a_marker_never_neither() -> None:
    assert r.SheetEntry(marker=SheetMarker.NOT_APPLICABLE).content is None
    with pytest.raises(r.RecordError, match="never silently empty"):
        r.SheetEntry()
    with pytest.raises(r.RecordError, match="never silently empty"):
        r.SheetEntry(content="x", marker=SheetMarker.UNDETERMINED)
    with pytest.raises(r.RecordError, match="empty"):
        r.SheetEntry(content="")


def test_mechanic_axis_lookup_covers_all_six_axes() -> None:
    mechanic = next(s for s in SAMPLES if isinstance(s, r.Mechanic))
    assert isinstance(mechanic, r.Mechanic)
    assert [mechanic.axis(axis) for axis in MechanicAxis] == [
        mechanic.si,
        mechanic.ep,
        mechanic.is_,
        mechanic.ft,
        mechanic.sr,
        mechanic.di,
    ]


def test_gate_record_outcome_must_belong_to_its_gate() -> None:
    gate = next(s for s in SAMPLES if isinstance(s, r.GateRecord))
    with pytest.raises(r.RecordError, match="not an outcome of the STRUCTURE gate"):
        replace(gate, outcome=GateOutcome.CANONIZE)
    with pytest.raises(r.RecordError, match="not an outcome of the PROPOSAL gate"):
        replace(gate, gate=Gate.PROPOSAL, outcome=GateOutcome.ACCEPT_AND_REGISTER)
    assert (
        replace(gate, gate=Gate.CANON, outcome=GateOutcome.ACCEPT_AND_REGISTER).gate is Gate.CANON
    )


def test_override_needs_a_reason() -> None:
    gate = next(s for s in SAMPLES if isinstance(s, r.GateRecord))
    with pytest.raises(r.RecordError, match=r"REQ-11\.5\.1"):
        replace(gate, override=True)
    assert replace(gate, override=True, reason="taste").override


def test_gate_time_must_be_utc() -> None:
    gate = next(s for s in SAMPLES if isinstance(s, r.GateRecord))
    with pytest.raises(r.RecordError, match="not UTC"):
        replace(gate, time="2026-10-25T19:02+01:00")


def test_audit_chain_shape() -> None:
    audit = next(s for s in SAMPLES if isinstance(s, r.AuditRecord))
    with pytest.raises(r.RecordError, match="only line 0"):
        replace(audit, seq=1)
    with pytest.raises(r.RecordError, match="from-state and to-state"):
        replace(audit, to_state=None)
    with pytest.raises(r.RecordError, match="malformed"):
        replace(audit, hash="sha256:xyz")
    assert (
        replace(audit, kind=AuditKind.GATE, from_state=None, to_state=None).kind is AuditKind.GATE
    )


def test_extraction_record_must_be_an_extraction_run() -> None:
    extraction = next(s for s in SAMPLES if isinstance(s, r.ExtractionRecord))
    with pytest.raises(r.RecordError, match="not an extraction run"):
        replace(extraction, handle="RUN-R-0047")


# --- decoding -------------------------------------------------------------------------------


def test_decoding_refuses_unknown_and_missing_fields() -> None:
    claim = next(s for s in SAMPLES if isinstance(s, r.Claim))
    encoded = r.to_json(claim)
    with pytest.raises(r.RecordError, match=r"unknown fields \['speaker'\]"):
        r.from_json(r.Claim, {**encoded, "speaker": "CHR-005"})
    del encoded["holder"]
    with pytest.raises(r.RecordError, match="missing required field 'holder'"):
        r.from_json(r.Claim, encoded)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rev", "1"),
        ("rev", True),
        ("rev", 1.5),
        ("holder", 7),
        ("status", "APPROVED"),
        ("tx", [47, None]),
    ],
)
def test_decoding_refuses_wrong_types(field: str, value: Any) -> None:
    claim = next(s for s in SAMPLES if isinstance(s, r.Claim))
    with pytest.raises(r.RecordError):
        r.from_json(r.Claim, {**r.to_json(claim), field: value})


def test_decoding_picks_the_effect_variant_by_its_op() -> None:
    event = next(s for s in SAMPLES if isinstance(s, r.Event))
    assert isinstance(event, r.Event)
    encoded = r.to_json(event)
    decoded = r.from_json(r.Event, encoded)
    assert [type(effect).__name__ for effect in decoded.effects] == [
        "TransferEffect",
        "SetEffect",
        "SetEffect",
        "GrantEffect",
        "ClaimEffect",
        "LifecycleEffect",
    ]
    encoded["effects"][0]["op"] = "TELEPORT"
    with pytest.raises(r.RecordError, match="no alternative matched"):
        r.from_json(r.Event, encoded)


def test_visibility_decodes_as_enum_or_hidden_until() -> None:
    event = next(s for s in SAMPLES if isinstance(s, r.Event))
    encoded = r.to_json(event)
    encoded["visibility"] = "PERMANENT_MYSTERY"
    assert r.from_json(r.Event, encoded).visibility is Visibility.PERMANENT_MYSTERY


def test_integral_floats_survive_canonical_form() -> None:
    constant = next(s for s in SAMPLES if isinstance(s, r.MechanicsConstant))
    assert isinstance(constant, r.MechanicsConstant)
    text = canonical_bytes(r.to_json(constant))
    assert b'"value":2' in text
    decoded = r.from_json(r.MechanicsConstant, json.loads(text))
    assert isinstance(decoded.value, float)
    assert decoded == constant
