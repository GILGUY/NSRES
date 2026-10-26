"""Closed vocabularies (plan A-17).

Every enumeration the spec fixes is defined here once, as a ``StrEnum``. The JSON Schemas in
``nsres.domain.schemas`` are generated from these classes, and
``tests/unit/test_vocabulary_spec.py`` checks each one against the spec text itself (§10.2
type unions, the B.3 and B.4 schema enums, and the prose tables), so a vocabulary that drifts
from the spec fails the gate.

Values are the spec's spellings exactly, including the lower-case ``Plane`` and ``ThreadRank``
values of §10.2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import assert_never


class Status(StrEnum):
    """Record status (§0.7, §10.2 ``Status``)."""

    PROPOSAL = "PROPOSAL"
    ACCEPTED = "ACCEPTED"
    CANON = "CANON"
    REJECTED = "REJECTED"
    SLUSHED = "SLUSHED"
    DEPRECATED = "DEPRECATED"


class Tier(StrEnum):
    """A tier on CANON records (§0.7). Not a status."""

    PUBLISHED = "PUBLISHED"


class Provenance(StrEnum):
    """Where a record came from (§10.2 ``Provenance``)."""

    AUTHOR = "AUTHOR"
    LIFTED_FROM_BEAT = "LIFTED_FROM_BEAT"
    ENGINE_BRIDGE = "ENGINE_BRIDGE"
    AI_PROPOSAL = "AI_PROPOSAL"
    IMPORTED = "IMPORTED"
    DRAFT_EMERGENT = "DRAFT_EMERGENT"


class Confidence(StrEnum):
    """Confidence of a held proposition (§10.2 ``Confidence``)."""

    CERTAIN = "CERTAIN"
    BELIEVED = "BELIEVED"
    SUSPECTED = "SUSPECTED"


class Channel(StrEnum):
    """Knowledge channel (§10.2 ``Channel``; L9 table; DETECTED from §17.5)."""

    WITNESSED = "WITNESSED"
    TOLD = "TOLD"
    READ = "READ"
    INFERRED = "INFERRED"
    RUMOR = "RUMOR"
    ASSUMED = "ASSUMED"
    DETECTED = "DETECTED"


class Plane(StrEnum):
    """The domain a record belongs to (§3.1, §10.2 ``BaseRecord.plane``)."""

    REALITY = "reality"
    TELLING = "telling"
    RENDERING = "rendering"
    CONTROL = "control"


class EntityKind(StrEnum):
    """§10.2 ``Entity.kind``."""

    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    OBJECT = "OBJECT"
    GROUP = "GROUP"


class Significance(StrEnum):
    """§10.2 ``Entity.significance`` (objects)."""

    ORDINARY = "ORDINARY"
    CLUE = "CLUE"
    PLOT_OBJECT = "PLOT_OBJECT"


class Precision(StrEnum):
    """Story-time precision tag (§0.4, §10.2 ``StoryTime.precision``)."""

    MINUTE = "MINUTE"
    QUARTER_HOUR = "QUARTER_HOUR"
    HOUR = "HOUR"
    PART_OF_DAY = "PART_OF_DAY"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    SEASON = "SEASON"
    YEAR = "YEAR"


class ConstraintKind(StrEnum):
    """§10.2 ``TemporalConstraint.kind``."""

    METRIC = "METRIC"
    ALLEN = "ALLEN"
    ANCHOR = "ANCHOR"


class EffectOp(StrEnum):
    """§10.2 ``Effect.op``."""

    SET = "SET"
    TRANSFER = "TRANSFER"
    GRANT = "GRANT"
    CLAIM = "CLAIM"
    CREATE = "CREATE"
    DESTROY = "DESTROY"


class MechanicsEffectOp(StrEnum):
    """Effect-language extensions for world mechanics (§17.4 EBNF, lower case in the spec)."""

    CONSUME = "CONSUME"
    SUSTAIN = "SUSTAIN"
    RELEASE = "RELEASE"
    EMIT_TRACE = "EMIT_TRACE"
    CASCADE = "CASCADE"
    LEARN = "LEARN"


class EffectAt(StrEnum):
    """§10.2 ``Effect.at`` when it is not an offset."""

    START = "START"
    END = "END"


class ParticipantRole(StrEnum):
    """§10.2 ``Event.participants[].role``."""

    AGENT = "AGENT"
    PATIENT = "PATIENT"
    WITNESS = "WITNESS"
    PRESENT = "PRESENT"
    REMOTE = "REMOTE"


class RenderStatus(StrEnum):
    """§10.2 ``Event.renderStatus``."""

    RENDERED = "RENDERED"
    DEFERRED = "DEFERRED"
    IMPLIED = "IMPLIED"
    CAUSAL_UNRENDERED = "CAUSAL_UNRENDERED"
    AMBIENT = "AMBIENT"


class Visibility(StrEnum):
    """§10.2 ``Event.visibility`` (the third form, ``hiddenUntil``, is a record)."""

    REVEALABLE = "REVEALABLE"
    PERMANENT_MYSTERY = "PERMANENT_MYSTERY"


class TruthValue(StrEnum):
    """§10.2 ``Fact.truth``."""

    TRUE = "TRUE"
    FALSE = "FALSE"
    UNDETERMINED = "UNDETERMINED"
    PERMANENTLY_UNDETERMINED = "PERMANENTLY_UNDETERMINED"


class CausalEdgeType(StrEnum):
    """§10.2 ``CausalEdge.type``."""

    CAUSES = "CAUSES"
    ENABLES = "ENABLES"
    MOTIVATES = "MOTIVATES"
    PREVENTS = "PREVENTS"
    INFORMS = "INFORMS"


class ThreadRank(StrEnum):
    """§10.2 ``Thread.rank``."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class ThreadVisibility(StrEnum):
    """§10.2 ``Thread.visibilitySchedule[].visibility``."""

    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


class BeatType(StrEnum):
    """Beat type (DEF-25, L4 table, §10.2 ``Beat.type``, B.3 ``beat.type``)."""

    ACTION = "ACTION"
    EXCHANGE = "EXCHANGE"
    PERCEPTION = "PERCEPTION"
    REVELATION = "REVELATION"
    DECISION = "DECISION"
    REVERSAL = "REVERSAL"
    INTERIOR = "INTERIOR"
    TRANSITION = "TRANSITION"
    PLANT = "PLANT"
    PAYOFF = "PAYOFF"
    SUSTAIN = "SUSTAIN"


class Severity(StrEnum):
    """Finding severity (§10.2, B.4)."""

    BLOCKING = "BLOCKING"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


def severity_rank(severity: Severity) -> int:
    """Sort key, most severe first (0). Exhaustive under ``mypy --strict`` (plan A-17)."""
    match severity:
        case Severity.BLOCKING:
            return 0
        case Severity.MAJOR:
            return 1
        case Severity.MINOR:
            return 2
        case Severity.INFO:
            return 3
        case _:
            assert_never(severity)


class FindingEvidence(StrEnum):
    """Evidence label carried by a finding (§10.2, B.4)."""

    CONTENT_READ = "CONTENT_READ"
    FOUND_BY_SNIPPET = "FOUND_BY_SNIPPET"
    FOUND_BY_METADATA = "FOUND_BY_METADATA"
    CLAIM_INFERRED = "CLAIM_INFERRED"


class FindingCause(StrEnum):
    """Root-cause class (§9.7, §10.2, B.4)."""

    MODEL_GAP = "MODEL_GAP"
    MODEL_ERROR = "MODEL_ERROR"
    PACKET_ERROR = "PACKET_ERROR"
    BRIEF_ERROR = "BRIEF_ERROR"
    DRAFTER_VIOLATION = "DRAFTER_VIOLATION"
    DETECTOR_ERROR = "DETECTOR_ERROR"


class FindingStatus(StrEnum):
    """Finding lifecycle (B.4; REQ-9.1.2 limits WAIVED_BY_OVERRIDE)."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    WAIVED_BY_OVERRIDE = "WAIVED_BY_OVERRIDE"
    DETECTOR_ERROR = "DETECTOR_ERROR"


class Band(StrEnum):
    """Confidence band (§11.5, §10.2 ``ConfidenceVector.band``)."""

    READY = "READY"
    PROVISIONAL = "PROVISIONAL"
    INSUFFICIENT = "INSUFFICIENT"
    UNSTABLE = "UNSTABLE"
    FAILED = "FAILED"


class PacketStatus(StrEnum):
    """Scene packet lifecycle (§5.4, B.3 ``status``)."""

    EXTRACTED = "EXTRACTED"
    PACKET_VALID = "PACKET_VALID"
    FROZEN = "FROZEN"
    STALE = "STALE"


class PacketFlag(StrEnum):
    """Packet flags without an argument (§8.2 group A, B.3 ``flags``).

    ``DEPENDENCY:<scene>`` carries a scene handle and is matched by pattern instead.
    """

    PLAN_ONLY = "PLAN_ONLY"
    CHEAT_RISK = "CHEAT_RISK"
    INFORMED_DRAFTING = "INFORMED_DRAFTING"


class Gate(StrEnum):
    """Typed gate (§0.7)."""

    PROPOSAL = "PROPOSAL"
    STRUCTURE = "STRUCTURE"
    INTEGRATION = "INTEGRATION"
    CANON = "CANON"
    SHIP = "SHIP"


class GateOutcome(StrEnum):
    """Every gate outcome code (§0.7 typed gates and micro-fact decisions)."""

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"
    SLUSH = "SLUSH"
    CANONIZE = "CANONIZE"
    SHIP = "SHIP"
    HOLD = "HOLD"
    ACCEPT_AND_REGISTER = "ACCEPT_AND_REGISTER"
    REJECT_MICRO_FACT = "REJECT_MICRO_FACT"


GATE_OUTCOMES: dict[Gate, frozenset[GateOutcome]] = {
    Gate.PROPOSAL: frozenset(
        {GateOutcome.ACCEPT, GateOutcome.REVISE, GateOutcome.REJECT, GateOutcome.SLUSH}
    ),
    Gate.STRUCTURE: frozenset({GateOutcome.ACCEPT, GateOutcome.REVISE, GateOutcome.REJECT}),
    Gate.INTEGRATION: frozenset({GateOutcome.ACCEPT, GateOutcome.REVISE, GateOutcome.REJECT}),
    Gate.CANON: frozenset(
        {
            GateOutcome.CANONIZE,
            GateOutcome.REVISE,
            GateOutcome.REJECT,
            GateOutcome.ACCEPT_AND_REGISTER,
            GateOutcome.REJECT_MICRO_FACT,
        }
    ),
    Gate.SHIP: frozenset({GateOutcome.SHIP, GateOutcome.HOLD}),
}
"""Outcomes allowed at each gate (§0.7). Micro-fact codes are decided at the CANON gate."""


class PovMode(StrEnum):
    """POV mode (§7.4). UNRELIABLE is a modifier, carried as ``pov.unreliable``."""

    FIRST_EXPERIENCING = "FIRST_EXPERIENCING"
    FIRST_RETROSPECTIVE = "FIRST_RETROSPECTIVE"
    CLOSE_THIRD = "CLOSE_THIRD"
    DISTANT_THIRD = "DISTANT_THIRD"
    OMNISCIENT = "OMNISCIENT"
    CAMERA = "CAMERA"


class DeliveryMode(StrEnum):
    """Reader delivery mode (§7.7 RV-1)."""

    STATED = "STATED"
    SHOWN = "SHOWN"
    IMPLIED = "IMPLIED"
    HINTED = "HINTED"
    MISLED = "MISLED"


class VisibilityClass(StrEnum):
    """Packet visibility class of a fact (§7.5)."""

    PERMANENTLY_UNDETERMINED = "PERMANENTLY_UNDETERMINED"
    FORBIDDEN = "FORBIDDEN"
    REVEAL_NOW = "REVEAL_NOW"
    HINT = "HINT"
    ALREADY_KNOWN = "ALREADY_KNOWN"
    IRONY = "IRONY"
    UNKNOWN_TO_POV = "UNKNOWN_TO_POV"
    SUPPRESSED = "SUPPRESSED"
    PERCEIVABLE = "PERCEIVABLE"


class ThreadRole(StrEnum):
    """Role a thread plays in a scene (§7.8)."""

    FOREGROUND = "FOREGROUND"
    BACKGROUND = "BACKGROUND"
    SUPPRESSED = "SUPPRESSED"
    DORMANT = "DORMANT"


class OutcomeKind(StrEnum):
    """Kind of a required or forbidden outcome (§8.2 group K)."""

    WORLD = "WORLD"
    CHARACTER = "CHARACTER"
    READER = "READER"


class Anachrony(StrEnum):
    """Flashback or flash-forward status (§8.2 group B)."""

    NONE = "NONE"
    ANALEPSIS = "ANALEPSIS"
    PROLEPSIS = "PROLEPSIS"


class InventionClass(StrEnum):
    """Invention policy class (§3.6)."""

    FREE = "FREE"
    CONSTRAINED = "CONSTRAINED"
    LOCKED = "LOCKED"


class Hardness(StrEnum):
    """Mechanics hardness setting of a work (§17.6)."""

    SOFT = "SOFT"
    FIRM = "FIRM"
    HARD = "HARD"


class CanonRuleClass(StrEnum):
    """Canon rule class (§3.3 record catalog)."""

    INVARIANT = "INVARIANT"
    CONDITIONAL = "CONDITIONAL"
    DEFAULT = "DEFAULT"
    PROHIBITION = "PROHIBITION"
    METRIC = "METRIC"


class ConservationClass(StrEnum):
    """Resource conservation class (§17.4; must be declared)."""

    CONSERVED = "CONSERVED"
    SOURCED = "SOURCED"
    UNBOUNDED = "UNBOUNDED"


class MechanicClass(StrEnum):
    """Mechanic class on the SI axis (§17.3; the spec writes the values in lower case)."""

    INNATE = "INNATE"
    LEARNED = "LEARNED"
    RITUAL = "RITUAL"
    TECHNOLOGICAL = "TECHNOLOGICAL"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class MechanicAxis(StrEnum):
    """The six orthogonal axes of the mechanic sheet (§17.2, §17.3)."""

    SI = "SI"
    EP = "EP"
    IS = "IS"
    FT = "FT"
    SR = "SR"
    DI = "DI"


class SheetMarker(StrEnum):
    """A mechanic-sheet field that is deliberately not specified (§17.3)."""

    UNDETERMINED = "UNDETERMINED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class InteractionKind(StrEnum):
    """Interaction-matrix entry between two mechanics (§17.3; lower case in the spec)."""

    AMPLIFIES = "AMPLIFIES"
    CANCELS = "CANCELS"
    BLOCKS = "BLOCKS"
    TRANSMUTES = "TRANSMUTES"


class AuditKind(StrEnum):
    """What an audit-log entry records (§10.4 audit log row)."""

    GATE = "GATE"
    RES = "RES"
    TRANSITION = "TRANSITION"
    LLM_CALL = "LLM_CALL"


class DraftValidationState(StrEnum):
    """Draft state a validation report leads to (L14, "Outputs and state created")."""

    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class PressureComponent(StrEnum):
    """Narrative pressure vector components (§7.8): questions, deadlines, threats, setups,
    irony."""

    Q = "Q"
    D = "D"
    T = "T"
    S = "S"
    I = "I"  # noqa: E741 - the spec's own component name


ALL_VOCABULARIES: tuple[type[StrEnum], ...] = (
    Status,
    Tier,
    Provenance,
    Confidence,
    Channel,
    Plane,
    EntityKind,
    Significance,
    Precision,
    ConstraintKind,
    EffectOp,
    MechanicsEffectOp,
    EffectAt,
    ParticipantRole,
    RenderStatus,
    Visibility,
    TruthValue,
    CausalEdgeType,
    ThreadRank,
    ThreadVisibility,
    BeatType,
    Severity,
    FindingEvidence,
    FindingCause,
    FindingStatus,
    Band,
    PacketStatus,
    PacketFlag,
    Gate,
    GateOutcome,
    PovMode,
    DeliveryMode,
    VisibilityClass,
    ThreadRole,
    OutcomeKind,
    Anachrony,
    InventionClass,
    Hardness,
    CanonRuleClass,
    ConservationClass,
    MechanicClass,
    MechanicAxis,
    SheetMarker,
    InteractionKind,
    AuditKind,
    DraftValidationState,
    PressureComponent,
)


def values(vocabulary: type[StrEnum]) -> list[str]:
    """The vocabulary's values, in declaration order."""
    return [member.value for member in vocabulary]
