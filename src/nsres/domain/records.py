"""Record types (spec §10.2, extended per plan §6 and DECISIONS D-007 to D-011).

Every class is a frozen, keyword-only dataclass. Construction validates shape (handle prefix,
UUIDv7 key, ranges, the REQ-9.1.1 and REQ-9.1.2 finding rules) and raises ``RecordError`` for
schema-invalid input (plan A-15). Domain rules that need other records (reachability,
conservation, contradiction) are not checked here; engines report them as findings.

Serialization (D-007): ``to_json`` writes snake_case keys and omits optional fields that are
None; ``from_json`` reads that form back and refuses unknown keys. Story-time is integer
minutes from the work's epoch (A-09); transaction time is integer model revisions (A-06).

Three families:

- ``RecordCore`` and ``BaseRecord``: gated records with a §0.3 handle. ``Finding`` extends
  ``RecordCore`` rather than ``BaseRecord`` because its lifecycle status is not a record
  status (D-008, spec erratum ERR-5).
- Mechanics records (§17.4), also ``BaseRecord`` subclasses.
- Control-plane entries: ``GateRecord``, ``AuditRecord``, ``ExtractionRecord``,
  ``ValidationReport``. These are immutable once written and are never gated themselves, so
  they carry no status or revision (D-009, spec erratum ERR-6).
"""

from __future__ import annotations

import re
import types
import uuid as uuid_module
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from enum import Enum, StrEnum
from typing import Any, ClassVar, Literal, Union, get_args, get_origin, get_type_hints

from nsres.domain import handles
from nsres.domain.vocab import (
    GATE_OUTCOMES,
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
    MechanicsEffectOp,
    ModelVersionState,
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

_SHA256_REF = re.compile(r"sha256:[0-9a-f]{64}")
_INSTANT_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z")
_NARRATIVE_POSITION = re.compile(r"\d+(?:\.\d+){1,3}")
_RULE_CODE = re.compile(r"(RC|CC|PK|EX|AU|MC|CX|ED)-?[A-Z0-9-]+")


class RecordError(ValueError):
    """A record is schema-invalid. Raised at construction or decoding, with the reason."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordError(message)


def _json(name: str) -> dict[str, str]:
    """Field metadata giving the JSON key where it differs from the Python name."""
    return {"json": name}


def _check_handle(value: str, *prefixes: str, what: str) -> None:
    _require(
        any(handles.is_handle(prefix, value) for prefix in prefixes),
        f"{what} {value!r} is not a {'/'.join(prefixes)} handle",
    )


def _check_handles(values: tuple[str, ...], *prefixes: str, what: str) -> None:
    for value in values:
        _check_handle(value, *prefixes, what=what)


def _check_uuid7(value: str, what: str) -> None:
    try:
        parsed = uuid_module.UUID(value)
    except ValueError as error:
        raise RecordError(f"{what} {value!r} is not a UUID") from error
    _require(parsed.version == 7, f"{what} {value!r} is not a UUIDv7")
    _require(str(parsed) == value, f"{what} {value!r} is not in canonical lower-case form")


def _check_unit(value: float, what: str) -> None:
    _require(0.0 <= value <= 1.0, f"{what} {value} is outside [0, 1]")


# --- shared value objects -----------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class TxRange:
    """Transaction-time validity: the model revisions that contain this row (§10.5)."""

    from_rev: int = field(metadata=_json("from"))
    to_rev: int | None = field(metadata=_json("to"))

    def __post_init__(self) -> None:
        _require(self.from_rev >= 0, f"tx.from {self.from_rev} is negative")
        _require(
            self.to_rev is None or self.to_rev > self.from_rev,
            f"tx.to {self.to_rev} does not follow tx.from {self.from_rev}",
        )


@dataclass(frozen=True, kw_only=True)
class StoryInterval:
    """Half-open story-time interval in minutes; either end may be open (§3.4 item 2)."""

    from_min: int | None = field(metadata=_json("from"))
    to_min: int | None = field(metadata=_json("to"))

    def __post_init__(self) -> None:
        _require(
            self.from_min is None or self.to_min is None or self.to_min >= self.from_min,
            f"interval ends at {self.to_min} before it starts at {self.from_min}",
        )


@dataclass(frozen=True, kw_only=True)
class Window:
    """Feasible window for one time point, in minutes (§10.2 ``{lo, hi}``)."""

    lo: int
    hi: int

    def __post_init__(self) -> None:
        _require(self.lo <= self.hi, f"window lo {self.lo} is after hi {self.hi}")


@dataclass(frozen=True, kw_only=True)
class StoryTime:
    """§10.2 ``StoryTime``: windows for the start and end points, and a precision tag."""

    start: Window
    end: Window
    precision: Precision

    def __post_init__(self) -> None:
        _require(self.start.lo <= self.end.hi, "story time ends before it can start")


# --- gated records ------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class RecordCore:
    """Fields every gated record carries, except status (§10.2 ``BaseRecord`` minus status)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ()

    uuid: str
    handle: str
    rev: int
    provenance: Provenance
    plane: Plane
    tx: TxRange
    gate: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _check_uuid7(self.uuid, "uuid")
        _require(bool(self.PREFIXES), f"{type(self).__name__} declares no handle prefix")
        _check_handle(self.handle, *self.PREFIXES, what="handle")
        _require(self.rev >= 1, f"rev {self.rev} must be at least 1")
        if self.gate is not None:
            _check_uuid7(self.gate, "gate")


@dataclass(frozen=True, kw_only=True)
class BaseRecord(RecordCore):
    """§10.2 ``BaseRecord``. ``tier`` is set only on CANON records (§0.7)."""

    status: Status
    tier: Tier | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(
            self.tier is None or self.status is Status.CANON,
            f"tier {self.tier} is set on a {self.status} record; PUBLISHED is a tier of CANON",
        )


_ENTITY_PREFIX: dict[EntityKind, str] = {
    EntityKind.CHARACTER: "CHR",
    EntityKind.LOCATION: "LOC",
    EntityKind.OBJECT: "OBJ",
    EntityKind.GROUP: "GRP",
}
ENTITY_PREFIXES: tuple[str, ...] = tuple(_ENTITY_PREFIX.values())


@dataclass(frozen=True, kw_only=True)
class EmbeddedMechanics:
    """The §17.4 Artifact: an object (OBJ) with embedded mechanics, charges, and state.

    Charges are Resource records (RSV-) owned by the object, so the resource ledger tracks
    them like any other reserve.
    """

    mechanics: tuple[str, ...]
    charges: tuple[str, ...] = ()
    state: str

    def __post_init__(self) -> None:
        _require(bool(self.mechanics), "an artifact embeds at least one mechanic")
        _check_handles(self.mechanics, "MCH", what="embedded mechanic")
        _check_handles(self.charges, "RSV", what="artifact charge")


@dataclass(frozen=True, kw_only=True)
class Entity(BaseRecord):
    """§10.2 ``Entity`` (CHR, LOC, OBJ, GRP). ``embedded_mechanics`` makes an object a §17.4
    Artifact."""

    PREFIXES: ClassVar[tuple[str, ...]] = ENTITY_PREFIXES

    kind: EntityKind
    canonical_name: str
    aliases: tuple[str, ...] = ()
    fixed_traits: dict[str, str] = field(default_factory=dict)
    persistent_defaults: dict[str, Any] = field(default_factory=dict)
    significance: Significance | None = None
    embedded_mechanics: EmbeddedMechanics | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        expected = _ENTITY_PREFIX[self.kind]
        _require(
            handles.is_handle(expected, self.handle),
            f"{self.kind} entity has handle {self.handle!r}; expected {expected}-",
        )
        _require(bool(self.canonical_name), "canonical_name is empty")
        _require(
            self.significance is None or self.kind is EntityKind.OBJECT,
            "significance applies to objects only",
        )
        _require(
            self.embedded_mechanics is None or self.kind is EntityKind.OBJECT,
            "only an object can embed mechanics (§17.4 Artifact)",
        )


@dataclass(frozen=True, kw_only=True)
class CanonRule(BaseRecord):
    """Canon rule (§3.3 catalog; L1 outputs)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("CAN",)

    rule_class: CanonRuleClass = field(metadata=_json("class"))
    statement_structured: str
    statement: str
    scope: str | None = None
    exceptions: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class TemporalConstraint:
    """§10.2 ``TemporalConstraint``. ``bounds`` are minutes (METRIC)."""

    kind: ConstraintKind
    from_ref: str = field(metadata=_json("from"))
    to_ref: str = field(metadata=_json("to"))
    bounds: tuple[int, int] | None = None
    relations: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind is ConstraintKind.METRIC:
            _require(self.bounds is not None, "a METRIC constraint needs bounds")
        if self.bounds is not None:
            _require(self.bounds[0] <= self.bounds[1], f"bounds {self.bounds} are reversed")
        if self.kind is ConstraintKind.ALLEN:
            _require(bool(self.relations), "an ALLEN constraint needs at least one relation")


@dataclass(frozen=True, kw_only=True)
class Offset:
    """``Effect.at`` as an offset from the event start, in minutes."""

    offset_min: int


@dataclass(frozen=True, kw_only=True)
class SetEffect:
    op: Literal[EffectOp.SET] = EffectOp.SET
    target: str
    attr: str
    value: Any
    at: EffectAt | Offset


@dataclass(frozen=True, kw_only=True)
class TransferEffect:
    op: Literal[EffectOp.TRANSFER] = EffectOp.TRANSFER
    object_ref: str = field(metadata=_json("object"))
    from_ref: str = field(metadata=_json("from"))
    to_ref: str = field(metadata=_json("to"))


@dataclass(frozen=True, kw_only=True)
class GrantEffect:
    op: Literal[EffectOp.GRANT] = EffectOp.GRANT
    holder: str
    prop: str
    channel: Channel
    confidence: Confidence
    premises: tuple[str, ...] | None = None


@dataclass(frozen=True, kw_only=True)
class ClaimEffect:
    op: Literal[EffectOp.CLAIM] = EffectOp.CLAIM
    speaker: str
    prop: str
    truth: bool
    hearers: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class LifecycleEffect:
    op: Literal[EffectOp.CREATE, EffectOp.DESTROY]
    target: str


@dataclass(frozen=True, kw_only=True)
class ConsumeEffect:
    """§17.4 ``consume(resource, amount)``."""

    op: Literal[MechanicsEffectOp.CONSUME] = MechanicsEffectOp.CONSUME
    resource: str
    amount: float

    def __post_init__(self) -> None:
        _check_handle(self.resource, "RSV", what="consumed resource")
        _require(self.amount >= 0, f"consumed amount {self.amount} is negative")


@dataclass(frozen=True, kw_only=True)
class SustainEffect:
    """§17.4 ``sustain(effect, upkeep_per_hour, funding_resource)``."""

    op: Literal[MechanicsEffectOp.SUSTAIN] = MechanicsEffectOp.SUSTAIN
    effect: str
    upkeep_per_hour: float
    funding_resource: str

    def __post_init__(self) -> None:
        _check_handle(self.effect, "EFF", what="sustained effect")
        _check_handle(self.funding_resource, "RSV", what="funding resource")
        _require(self.upkeep_per_hour >= 0, "upkeep is negative")


@dataclass(frozen=True, kw_only=True)
class ReleaseEffect:
    """§17.4 ``release(effect)``."""

    op: Literal[MechanicsEffectOp.RELEASE] = MechanicsEffectOp.RELEASE
    effect: str

    def __post_init__(self) -> None:
        _check_handle(self.effect, "EFF", what="released effect")


@dataclass(frozen=True, kw_only=True)
class EmitTraceEffect:
    """§17.4 ``emit_trace(trace, location, decay, perceptibility)``."""

    op: Literal[MechanicsEffectOp.EMIT_TRACE] = MechanicsEffectOp.EMIT_TRACE
    trace: str
    location: str
    decay: str
    perceptibility: tuple[str, ...]

    def __post_init__(self) -> None:
        _check_handle(self.trace, "TRC", what="emitted trace")
        _check_handle(self.location, "LOC", "OBJ", what="trace location")


@dataclass(frozen=True, kw_only=True)
class CascadeEffect:
    """§17.4 ``cascade(mechanic, trigger, outcome)``."""

    op: Literal[MechanicsEffectOp.CASCADE] = MechanicsEffectOp.CASCADE
    mechanic: str
    trigger: str
    outcome: str

    def __post_init__(self) -> None:
        _check_handle(self.mechanic, "MCH", what="cascading mechanic")


@dataclass(frozen=True, kw_only=True)
class LearnEffect:
    """§17.4 ``learn(entity, pattern, proficiency_delta)``."""

    op: Literal[MechanicsEffectOp.LEARN] = MechanicsEffectOp.LEARN
    entity: str
    pattern: str
    proficiency_delta: int

    def __post_init__(self) -> None:
        _check_handle(self.entity, "CHR", what="learner")


Effect = (
    SetEffect
    | TransferEffect
    | GrantEffect
    | ClaimEffect
    | LifecycleEffect
    | ConsumeEffect
    | SustainEffect
    | ReleaseEffect
    | EmitTraceEffect
    | CascadeEffect
    | LearnEffect
)
"""§10.2 ``Effect``, extended by the §17.4 effect-language operations. Parsing the textual
effect language (§10.9) belongs to ``nsres.effects``."""


@dataclass(frozen=True, kw_only=True)
class Participant:
    entity: str
    role: ParticipantRole

    def __post_init__(self) -> None:
        _check_handle(self.entity, *ENTITY_PREFIXES, what="participant")


@dataclass(frozen=True, kw_only=True)
class HiddenUntil:
    """§10.2 ``Event.visibility`` as ``{hiddenUntil: <reveal>}``."""

    hidden_until: str


@dataclass(frozen=True, kw_only=True)
class Event(BaseRecord):
    """§10.2 ``Event``. A WORKING (§17.4) is an event whose ``type`` is ``WORKING``."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("EVT",)

    type: str
    label: str
    time: StoryTime
    constraints: tuple[TemporalConstraint, ...] = ()
    location: str
    participants: tuple[Participant, ...]
    preconditions: tuple[str, ...] = ()
    effects: tuple[Effect, ...] = ()
    visibility: Visibility | HiddenUntil
    render_status: RenderStatus
    not_noticed_by: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.location, "LOC", what="event location")


@dataclass(frozen=True, kw_only=True)
class Secret:
    holders: tuple[str, ...]
    concealed_from: tuple[str, ...]
    strategy: str
    reveal: str | None = None


@dataclass(frozen=True, kw_only=True)
class Fact(BaseRecord):
    """§10.2 ``Fact`` (INF): a proposition with interval validity and a truth value."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("INF",)

    subject: str
    predicate: str
    object_value: str | int | float | bool = field(metadata=_json("object"))
    qualifiers: dict[str, str] | None = None
    valid: StoryInterval
    truth: TruthValue
    created_by: str | None = None
    secret: Secret | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.created_by is not None:
            _check_handle(self.created_by, "EVT", what="created_by")


@dataclass(frozen=True, kw_only=True)
class Claim(BaseRecord):
    """Claim (CLM; §3.3 catalog): a proposition asserted or believed by an entity."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("CLM",)

    holder: str
    proposition: str
    truth_value: TruthValue
    origin_event: str | None = None
    distortion_of: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.holder, *ENTITY_PREFIXES, what="claim holder")


@dataclass(frozen=True, kw_only=True)
class KnowledgeGrant(BaseRecord):
    """§10.2 ``KnowledgeGrant`` (KG). ``time`` is minutes."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("KG",)

    holder: str
    prop: str
    time: int
    channel: Channel
    confidence: Confidence
    source_event: str
    source_entity: str | None = None
    premises: tuple[str, ...] | None = None
    polarity: int

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(self.polarity in (1, -1), f"polarity {self.polarity} is not 1 or -1")
        _check_handle(self.source_event, "EVT", what="source_event")


@dataclass(frozen=True, kw_only=True)
class Relation(BaseRecord):
    """Relation between two entities (§3.3 catalog). The spec gives no handle prefix; the code
    uses ``REL-`` (DECISIONS D-010, spec erratum ERR-7)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("REL",)

    from_entity: str
    to_entity: str
    type: str
    valid: StoryInterval
    visibility: str | None = None
    asymmetry_note: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.from_entity, *ENTITY_PREFIXES, what="relation from")
        _check_handle(self.to_entity, *ENTITY_PREFIXES, what="relation to")


@dataclass(frozen=True, kw_only=True)
class CausalEdge(BaseRecord):
    """§10.2 ``CausalEdge`` (CE); ``strength`` from the §3.3 catalog."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("CE",)

    from_ref: str = field(metadata=_json("from"))
    to_ref: str = field(metadata=_json("to"))
    type: CausalEdgeType
    justification: str
    required_state: str | None = None
    strength: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.from_ref, "EVT", what="causal edge from")
        _check_handle(self.to_ref, "EVT", what="causal edge to")
        _require(self.from_ref != self.to_ref, "a causal edge cannot loop on one event")


@dataclass(frozen=True, kw_only=True)
class VisibilityStep:
    from_nt: str
    visibility: ThreadVisibility
    reveal: str | None = None

    def __post_init__(self) -> None:
        _require(
            _NARRATIVE_POSITION.fullmatch(self.from_nt) is not None,
            f"from_nt {self.from_nt!r} is not a narrative position",
        )


@dataclass(frozen=True, kw_only=True)
class ThreadNode:
    event: str
    role: str
    order: int


@dataclass(frozen=True, kw_only=True)
class Thread(BaseRecord):
    """§10.2 ``Thread`` (THR)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("THR",)

    name: str
    rank: ThreadRank
    dramatic_question: str
    visibility_schedule: tuple[VisibilityStep, ...] = ()
    nodes: tuple[ThreadNode, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ScenePov:
    character: str
    mode: PovMode

    def __post_init__(self) -> None:
        _check_handle(self.character, "CHR", what="POV character")


@dataclass(frozen=True, kw_only=True)
class Scene(BaseRecord):
    """§10.2 ``Scene`` (SCN). ``pov.mode`` is closed to the §7.4 modes (D-007)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("SCN",)

    nt: str
    window: StoryTime
    location: str
    pov: ScenePov
    participants: tuple[str, ...]
    renders_nodes: tuple[str, ...] = ()
    purpose: str
    planned_delta: Any
    length_target: tuple[int, int]
    pipeline_state: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(
            _NARRATIVE_POSITION.fullmatch(self.nt) is not None,
            f"nt {self.nt!r} is not a narrative position",
        )
        _check_handle(self.location, "LOC", what="scene location")
        _check_handles(self.participants, *ENTITY_PREFIXES, what="participant")
        low, high = self.length_target
        _require(0 <= low <= high, f"length_target {self.length_target} is not a range")


@dataclass(frozen=True, kw_only=True)
class Beat(BaseRecord):
    """§10.2 ``Beat`` (BT)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("BT",)

    scene: str
    order: int
    type: BeatType
    actors: tuple[str, ...]
    outcome: str
    events: tuple[str, ...] = ()
    mandatory: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.scene, "SCN", what="beat scene")
        _require(bool(self.actors), "a beat needs at least one actor")
        _require(bool(self.outcome), "a beat needs an outcome")
        _check_handles(self.events, "EVT", what="beat event")


@dataclass(frozen=True, kw_only=True)
class Span:
    draft: str
    start: int
    end: int
    quote: str

    def __post_init__(self) -> None:
        _check_handle(self.draft, "DRF", what="span draft")
        _require(0 <= self.start <= self.end, f"span [{self.start}, {self.end}) is invalid")
        _require(bool(self.quote), "a span needs its exact quote")


@dataclass(frozen=True, kw_only=True)
class Finding(RecordCore):
    """§10.2 ``Finding`` with B.4's rules. ``status`` is the finding lifecycle (D-008)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("FND",)

    rule: str
    severity: Severity
    spans: tuple[Span, ...] = ()
    records: tuple[str, ...]
    evidence: FindingEvidence
    detection_confidence: float
    cause: FindingCause | None = None
    repairs: tuple[str, ...] = ()
    status: FindingStatus

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(
            _RULE_CODE.fullmatch(self.rule) is not None, f"rule {self.rule!r} is not a rule code"
        )
        _require(bool(self.records), "a finding cites at least one record")
        _check_unit(self.detection_confidence, "detection_confidence")
        _require(
            self.severity is not Severity.BLOCKING or self.evidence is FindingEvidence.CONTENT_READ,
            f"a BLOCKING finding needs CONTENT_READ evidence, not {self.evidence} (REQ-9.1.1)",
        )
        _require(
            not (
                self.severity is Severity.BLOCKING
                and self.status is FindingStatus.WAIVED_BY_OVERRIDE
            ),
            "a BLOCKING finding cannot be WAIVED_BY_OVERRIDE (REQ-9.1.2)",
        )


@dataclass(frozen=True, kw_only=True)
class Factor:
    name: str
    weight: float
    raw: float
    ceiling: float
    evidence: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require(self.weight >= 0, f"factor {self.name} has negative weight")
        _check_unit(self.raw, f"factor {self.name} raw")
        _check_unit(self.ceiling, f"factor {self.name} ceiling")


@dataclass(frozen=True, kw_only=True)
class Penalty:
    reason: str
    value: float


@dataclass(frozen=True, kw_only=True)
class Score:
    type: str
    factors: tuple[Factor, ...]
    penalties: tuple[Penalty, ...] = ()
    value: float

    def __post_init__(self) -> None:
        _check_unit(self.value, f"score {self.type}")


@dataclass(frozen=True, kw_only=True)
class Cap:
    condition: str
    cap: float
    applied: bool

    def __post_init__(self) -> None:
        _check_unit(self.cap, f"cap {self.condition}")


@dataclass(frozen=True, kw_only=True)
class ConfidenceVector(BaseRecord):
    """§10.2 ``ConfidenceVector`` (CV)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("CV",)

    subject: str
    scores: tuple[Score, ...]
    caps: tuple[Cap, ...] = ()
    aggregate: float
    band: Band

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_unit(self.aggregate, "aggregate")


@dataclass(frozen=True, kw_only=True)
class RevealRecord(BaseRecord):
    """Reveal record (RVL; §6.9): targets, position, mode, prerequisites, delivering scene and
    beat, and the retro-consistency scope. MISLED needs a correction (RV-4); a retelling is
    tagged (RV-5)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("RVL",)

    targets: tuple[str, ...]
    nt: str
    mode: DeliveryMode
    prerequisites: tuple[str, ...] = ()
    delivering_scene: str | None = None
    delivering_beat: str | None = None
    retro_scope: tuple[str, str] | None = None
    correction: str | None = None
    retelling: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(bool(self.targets), "a reveal names at least one target proposition")
        _check_handles(self.targets, "INF", what="reveal target")
        _check_handles(self.prerequisites, "INF", what="reveal prerequisite")
        _require(
            _NARRATIVE_POSITION.fullmatch(self.nt) is not None,
            f"nt {self.nt!r} is not a narrative position",
        )
        if self.delivering_scene is not None:
            _check_handle(self.delivering_scene, "SCN", what="delivering scene")
        if self.delivering_beat is not None:
            _check_handle(self.delivering_beat, "BT", what="delivering beat")
        _require(
            self.mode is not DeliveryMode.MISLED or self.correction is not None,
            "MISLED delivery needs a registered correction (RV-4)",
        )


@dataclass(frozen=True, kw_only=True)
class Draft(BaseRecord):
    """Draft record (DRF; §8.5 output contract, §10.13 ``draft(packet, drafter)``). The prose
    lives in the artifact store under ``text_hash``; the emergent-detail list and beat map are
    the drafter's testimony, which autopsy verifies (§8.5 item 4)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("DRF",)

    scene: str
    packet: str
    packet_hash: str
    drafter: str
    text_hash: str
    emergent_details: tuple[str, ...] = ()
    beat_map: dict[str, tuple[str, ...]] = field(default_factory=dict)
    draft_state: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.scene, "SCN", what="draft scene")
        _check_handle(self.packet, "PKT", what="draft packet")
        for value, what in ((self.packet_hash, "packet_hash"), (self.text_hash, "text_hash")):
            _require(_SHA256_REF.fullmatch(value) is not None, f"{what} {value!r} is malformed")
        for beat in self.beat_map:
            _check_handle(beat, "BT", what="beat map key")


@dataclass(frozen=True, kw_only=True)
class ResolutionRecord(BaseRecord):
    """Resolution record (RES; §0.3, §6.11, Appendix A). Decided at the INTEGRATION gate."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("RES",)

    findings: tuple[str, ...]
    chosen_repair: str
    rejected_repairs: tuple[str, ...] = ()
    records_created: tuple[str, ...] = ()
    records_deprecated: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        _require(bool(self.findings), "a resolution resolves at least one finding")
        _check_handles(self.findings, "FND", what="resolved finding")


# --- mechanics records (§17.4) ------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class AmbientLevel:
    location: str
    interval: StoryInterval
    level: float

    def __post_init__(self) -> None:
        _check_handle(self.location, "LOC", what="ambient location")


@dataclass(frozen=True, kw_only=True)
class Substrate(BaseRecord):
    PREFIXES: ClassVar[tuple[str, ...]] = ("SUB",)

    name: str
    medium: str
    ambient: tuple[AmbientLevel, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Regime(BaseRecord):
    """Laws in force, scope, interface zones, precedence. An empty ``mechanics`` is a null zone."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("RGM",)

    name: str
    mechanics: tuple[str, ...]
    locations: tuple[str, ...]
    story_time: StoryInterval
    interface_zones: tuple[str, ...] = ()
    precedence: int

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handles(self.mechanics, "MCH", what="regime mechanic")
        _check_handles(self.locations, "LOC", what="regime location")


@dataclass(frozen=True, kw_only=True)
class SheetEntry:
    """One mechanic-sheet field: content, or a marker saying why there is none (§17.3)."""

    content: str | None = None
    marker: SheetMarker | None = None

    def __post_init__(self) -> None:
        _require(
            (self.content is None) != (self.marker is None),
            "a sheet field holds content or a marker, exactly one (never silently empty)",
        )
        _require(self.content != "", "a sheet field's content is empty")


@dataclass(frozen=True, kw_only=True)
class Interaction:
    other: str
    kind: InteractionKind

    def __post_init__(self) -> None:
        _check_handle(self.other, "MCH", what="interaction partner")


@dataclass(frozen=True, kw_only=True)
class Mechanic(BaseRecord):
    """The six-axis mechanic sheet (§17.3). ``is_`` is the IS axis (``is`` in JSON)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("MCH",)

    name: str
    mechanic_class: MechanicClass = field(metadata=_json("class"))
    si: SheetEntry
    ep: SheetEntry
    is_: SheetEntry = field(metadata=_json("is"))
    ft: SheetEntry
    sr: SheetEntry
    di: SheetEntry
    hard_limits: tuple[str, ...] = ()
    interactions: tuple[Interaction, ...] = ()
    reader_exposure: dict[MechanicAxis, tuple[str, ...]] = field(default_factory=dict)

    def axis(self, axis: MechanicAxis) -> SheetEntry:
        return {
            MechanicAxis.SI: self.si,
            MechanicAxis.EP: self.ep,
            MechanicAxis.IS: self.is_,
            MechanicAxis.FT: self.ft,
            MechanicAxis.SR: self.sr,
            MechanicAxis.DI: self.di,
        }[axis]


@dataclass(frozen=True, kw_only=True)
class MechanicsConstant(BaseRecord):
    PREFIXES: ClassVar[tuple[str, ...]] = ("MCC",)

    name: str
    value: float
    unit: str


@dataclass(frozen=True, kw_only=True)
class Resource(BaseRecord):
    """A reserve or field (§17.4 writes ``RES-``; the code uses ``RSV-``, D-005)."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("RSV",)

    owner: str
    maximum: float
    regeneration_rule: str
    decay: str
    conservation_class: ConservationClass

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.owner, *ENTITY_PREFIXES, what="resource owner")
        _require(self.maximum >= 0, f"resource maximum {self.maximum} is negative")


@dataclass(frozen=True, kw_only=True)
class Capability(BaseRecord):
    """A practitioner's capability with one mechanic (§17.4), anchored to learning events."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("CAP",)

    practitioner: str
    mechanic: str
    proficiency: int
    affinity: str | None = None
    known_patterns: tuple[str, ...] = ()
    impairing_conditions: tuple[str, ...] = ()
    anchored_to: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.practitioner, "CHR", what="practitioner")
        _check_handle(self.mechanic, "MCH", what="capability mechanic")
        _require(self.proficiency >= 0, f"proficiency {self.proficiency} is negative")
        _check_handles(self.anchored_to, "EVT", what="learning event")


@dataclass(frozen=True, kw_only=True)
class ActiveEffect(BaseRecord):
    """A sustained working (§17.4), derived from L5."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("EFF",)

    working: str
    mechanic: str
    interval: StoryInterval
    upkeep_per_hour: float
    funding_resource: str
    state: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.working, "EVT", what="working")
        _check_handle(self.mechanic, "MCH", what="effect mechanic")
        _check_handle(self.funding_resource, "RSV", what="funding resource")
        _require(self.upkeep_per_hour >= 0, "upkeep is negative")


@dataclass(frozen=True, kw_only=True)
class Trace(BaseRecord):
    """A residue fact (§17.4): what, where, decay, who can perceive it and how."""

    PREFIXES: ClassVar[tuple[str, ...]] = ("TRC",)

    what: str
    location: str
    emitted_by: str
    decay: str
    perceptibility: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _check_handle(self.location, "LOC", "OBJ", what="trace location")
        _check_handle(self.emitted_by, "EVT", what="emitting working")


# --- control-plane entries (D-009) --------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class GateRecord:
    """One gate decision (§0.7). ``time`` is a UTC instant supplied by the caller (A-04)."""

    uuid: str
    gate: Gate
    outcome: GateOutcome
    subject: str
    subject_uuid: str
    subject_rev: int
    actor: str
    time: str
    model_version: str
    reason: str | None = None
    override: bool = False
    confirmation: str | None = None
    retcon: tuple[str, ...] = ()
    successor: str | None = None

    def __post_init__(self) -> None:
        _check_uuid7(self.uuid, "uuid")
        _check_uuid7(self.subject_uuid, "subject_uuid")
        _require(
            self.outcome in GATE_OUTCOMES[self.gate],
            f"{self.outcome} is not an outcome of the {self.gate} gate",
        )
        _require(bool(self.actor), "a gate record names its actor")
        _require(_INSTANT_UTC.fullmatch(self.time) is not None, f"time {self.time!r} is not UTC")
        _require(
            not self.override or bool(self.reason),
            "an override carries a reason (REQ-11.5.1)",
        )


@dataclass(frozen=True, kw_only=True)
class AuditRecord:
    """One line of the hash-chained audit log (§10.4, REQ-5.4.1).

    ``tx``, ``ref``, and ``ref_hash`` tie the line to the record-log row it covers (D-012,
    D-015); ``nsres.store`` always sets them.
    """

    seq: int
    uuid: str
    kind: AuditKind
    subject: str
    from_state: str | None = None
    to_state: str | None = None
    trigger: str
    actor: str
    model_version: str
    timestamp: str
    prev_hash: str | None
    hash: str
    tx: int | None = None
    ref: str | None = None
    ref_hash: str | None = None

    def __post_init__(self) -> None:
        _require(self.seq >= 0, f"seq {self.seq} is negative")
        _require(
            self.ref_hash is None or _SHA256_REF.fullmatch(self.ref_hash) is not None,
            f"ref_hash {self.ref_hash!r} is malformed",
        )
        _check_uuid7(self.uuid, "uuid")
        _require(_INSTANT_UTC.fullmatch(self.timestamp) is not None, "timestamp is not UTC")
        _require(_SHA256_REF.fullmatch(self.hash) is not None, f"hash {self.hash!r} is malformed")
        _require(
            self.prev_hash is None or _SHA256_REF.fullmatch(self.prev_hash) is not None,
            f"prev_hash {self.prev_hash!r} is malformed",
        )
        _require((self.seq == 0) == (self.prev_hash is None), "only line 0 has no prev_hash")
        if self.kind is AuditKind.TRANSITION:
            _require(
                self.from_state is not None and self.to_state is not None,
                "a transition records its from-state and to-state",
            )


@dataclass(frozen=True, kw_only=True)
class ModelVersion:
    """One state of a model version (§5.4 version lifecycle; DECISIONS D-012 item 6)."""

    uuid: str
    number: int
    state: ModelVersionState
    opened_tx: int
    canon_rev: int | None = None
    truth_rev: int | None = None

    def __post_init__(self) -> None:
        _check_uuid7(self.uuid, "uuid")
        _require(self.number >= 1, f"version number {self.number} must be at least 1")
        fixed = self.state in (ModelVersionState.CONSISTENT, ModelVersionState.RELEASED)
        _require(
            fixed == (self.canon_rev is not None and self.truth_rev is not None),
            "a version fixes its revision counters exactly when it is CONSISTENT or RELEASED",
        )

    @property
    def label(self) -> str:
        if self.canon_rev is None or self.truth_rev is None:
            return f"open-{self.number}"
        return f"canon@r{self.canon_rev}/truth@r{self.truth_rev}"


@dataclass(frozen=True, kw_only=True)
class Exclusion:
    record: str
    reason_code: str


@dataclass(frozen=True, kw_only=True)
class RuleTraceEntry:
    rule: str
    result: str
    records: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ExtractionRecord:
    """The RUN-X record behind a packet (§7.12): selections, exclusions, classifications,
    manifestations, scores, rule traces, and the §8.2 group M ``sources`` map."""

    uuid: str
    handle: str
    scene: str
    packet: str
    model_version: str
    selections: tuple[str, ...]
    exclusions: tuple[Exclusion, ...] = ()
    classifications: dict[str, VisibilityClass] = field(default_factory=dict)
    manifestations: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)
    rule_trace: tuple[RuleTraceEntry, ...] = ()
    sources: dict[str, tuple[str, ...]] = field(default_factory=dict)
    flag_causes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _check_uuid7(self.uuid, "uuid")
        _require(self.handle.startswith("RUN-X-"), f"{self.handle!r} is not an extraction run")
        _check_handle(self.handle, "RUN", what="handle")
        _check_handle(self.scene, "SCN", what="scene")
        _check_handle(self.packet, "PKT", what="packet")


@dataclass(frozen=True, kw_only=True)
class SuiteRun:
    suite: str
    coverage: float
    findings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _check_unit(self.coverage, f"suite {self.suite} coverage")
        _check_handles(self.findings, "FND", what="suite finding")


@dataclass(frozen=True, kw_only=True)
class ValidationReport:
    """L14 validation report (REQ-5.4.3): suites run, their coverage, and findings."""

    uuid: str
    draft: str
    packet: str
    model_version: str
    suites: tuple[SuiteRun, ...]
    result: DraftValidationState

    def __post_init__(self) -> None:
        _check_uuid7(self.uuid, "uuid")
        _check_handle(self.draft, "DRF", what="draft")
        _check_handle(self.packet, "PKT", what="packet")
        _require(bool(self.suites), "a validation report lists the suites run")


RECORD_TYPES: tuple[type[Any], ...] = (
    Entity,
    CanonRule,
    Event,
    Fact,
    Claim,
    KnowledgeGrant,
    Relation,
    CausalEdge,
    Thread,
    Scene,
    Beat,
    Finding,
    ConfidenceVector,
    RevealRecord,
    Draft,
    ResolutionRecord,
    Substrate,
    Regime,
    Mechanic,
    MechanicsConstant,
    Resource,
    Capability,
    ActiveEffect,
    Trace,
    GateRecord,
    AuditRecord,
    ModelVersion,
    ExtractionRecord,
    ValidationReport,
)


# --- serialization ------------------------------------------------------------------------


def _json_name(item: Any) -> str:
    name: str = item.metadata.get("json", item.name)
    return name


def to_json(value: Any) -> Any:
    """The snake_case JSON form of a record or value (D-007)."""
    if is_dataclass(value) and not isinstance(value, type):
        out: dict[str, Any] = {}
        for item in fields(value):
            current = getattr(value, item.name)
            if current is None and item.default is None:
                continue
            out[_json_name(item)] = to_json(current)
        return out
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple | list):
        return [to_json(item) for item in value]
    if isinstance(value, Mapping):
        return {
            to_json(key) if isinstance(key, Enum) else key: to_json(item)
            for key, item in value.items()
        }
    return value


_HINTS: dict[type[Any], dict[str, Any]] = {}


def _hints(cls: type[Any]) -> dict[str, Any]:
    if cls not in _HINTS:
        _HINTS[cls] = get_type_hints(cls)
    return _HINTS[cls]


def from_json[T](cls: type[T], data: Any, path: str = "$") -> T:
    """Decode the ``to_json`` form back into ``cls``; unknown keys are refused."""
    _require(isinstance(data, Mapping), f"{path}: expected an object for {cls.__name__}")
    hints = _hints(cls)
    by_json = {_json_name(item): item for item in fields(cls) if item.init}  # type: ignore[arg-type]
    unknown = sorted(set(data) - set(by_json))
    _require(not unknown, f"{path}: unknown fields {unknown} for {cls.__name__}")
    kwargs: dict[str, Any] = {}
    for name, item in by_json.items():
        if name in data:
            kwargs[item.name] = _decode(hints[item.name], data[name], f"{path}.{name}")
        else:
            _require(
                item.default is not MISSING or item.default_factory is not MISSING,
                f"{path}: missing required field {name!r} for {cls.__name__}",
            )
    try:
        return cls(**kwargs)
    except TypeError as error:  # pragma: no cover - guarded by the missing-field check
        raise RecordError(f"{path}: {error}") from error


def _decode(hint: Any, value: Any, path: str) -> Any:
    origin = get_origin(hint)
    args = get_args(hint)
    if hint is Any:
        return value
    if origin is Union or origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        errors = []
        for candidate in (arg for arg in args if arg is not type(None)):
            try:
                return _decode(candidate, value, path)
            except RecordError as error:
                errors.append(str(error))
        raise RecordError(f"{path}: no alternative matched ({'; '.join(errors)})")
    if origin is Literal:
        for arg in args:
            if value == arg:
                return arg
        raise RecordError(f"{path}: {value!r} is not one of {list(args)}")
    if origin is tuple:
        _require(isinstance(value, list | tuple), f"{path}: expected an array")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(
                _decode(args[0], item, f"{path}[{index}]") for index, item in enumerate(value)
            )
        _require(len(value) == len(args), f"{path}: expected {len(args)} items")
        return tuple(
            _decode(arg, item, f"{path}[{index}]")
            for index, (arg, item) in enumerate(zip(args, value, strict=True))
        )
    if origin is dict:
        _require(isinstance(value, Mapping), f"{path}: expected an object")
        key_hint, value_hint = args
        return {
            _decode(key_hint, key, f"{path}.{key}"): _decode(value_hint, item, f"{path}.{key}")
            for key, item in value.items()
        }
    if isinstance(hint, type) and issubclass(hint, StrEnum):
        try:
            return hint(value)
        except (ValueError, TypeError) as error:
            raise RecordError(f"{path}: {value!r} is not a {hint.__name__}") from error
    if isinstance(hint, type) and is_dataclass(hint):
        return from_json(hint, value, path)
    if hint is bool:
        _require(isinstance(value, bool), f"{path}: expected a boolean")
        return value
    if hint is int:
        _require(
            isinstance(value, int) and not isinstance(value, bool), f"{path}: expected an integer"
        )
        return value
    if hint is float:
        _require(
            isinstance(value, int | float) and not isinstance(value, bool),
            f"{path}: expected a number",
        )
        return float(value)
    if hint is str:
        _require(isinstance(value, str), f"{path}: expected a string")
        return value
    raise RecordError(f"{path}: cannot decode type {hint!r}")  # pragma: no cover
