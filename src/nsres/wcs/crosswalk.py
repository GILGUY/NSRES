"""The spec §0.7 WCS crosswalk as data, and its import rule (DECISIONS D-016; OQ-8, OQ-9).

Pure data and one pure function. Nothing here reads or writes WCS folders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from nsres.domain.vocab import Gate, GateOutcome, Status


class WcsArtifactState(StrEnum):
    """WCS ``ArtifactState`` (11 values; §0.7 crosswalk)."""

    RAW = "RAW"
    INTAKE = "INTAKE"
    PROPOSAL = "PROPOSAL"
    REVISED_PROPOSAL = "REVISED_PROPOSAL"
    ACCEPTED = "ACCEPTED"
    CANON = "CANON"
    SLUSH = "SLUSH"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    FORK = "FORK"
    SHIP = "SHIP"


class WcsGateType(StrEnum):
    """WCS ``GateType`` (8 values; §0.7 crosswalk)."""

    INTAKE_GATE = "INTAKE_GATE"
    PROPOSAL_GATE = "PROPOSAL_GATE"
    REVISION_GATE = "REVISION_GATE"
    STRUCTURE_GATE = "STRUCTURE_GATE"
    CANON_GATE = "CANON_GATE"
    INTEGRATION_GATE = "INTEGRATION_GATE"
    DELETE_GATE = "DELETE_GATE"
    SHIP_GATE = "SHIP_GATE"


class WcsDecision(StrEnum):
    """WCS gate decisions (8 values; §0.7 crosswalk)."""

    ACCEPT = "ACCEPT"
    ACCEPT_AS_CANON = "ACCEPT_AS_CANON"
    REVISE = "REVISE"
    REDIRECT = "REDIRECT"
    FORK = "FORK"
    SLUSH = "SLUSH"
    REJECT = "REJECT"
    REVERT = "REVERT"


TELLING_CANON_TYPES = frozenset({"story_spine", "story_blueprint", "recut_proposal"})
"""WCS artifacts that WCS calls CANON but NSRES keeps at ACCEPTED, structure-locked (OQ-9)."""


class Admission(StrEnum):
    """What ``import_decision`` concludes for one WCS artifact."""

    RECORD = "RECORD"
    GATE_OUTCOME = "GATE_OUTCOME"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class StateRow:
    wcs_state: WcsArtifactState
    applies_to: str
    nsres_status: Status | None
    structure_locked: bool = False
    next_rev: bool = False
    successor_required: bool = False
    admission: Admission = Admission.RECORD
    rule: str = ""


STATE_ROWS: tuple[StateRow, ...] = (
    StateRow(
        WcsArtifactState.RAW,
        "any",
        None,
        admission=Admission.REFUSED,
        rule="NSRES never reads RAW material (REQ-12.2.2)",
    ),
    StateRow(
        WcsArtifactState.INTAKE,
        "any",
        None,
        admission=Admission.REFUSED,
        rule="NSRES does not import INTAKE copies (REQ-12.2.2)",
    ),
    StateRow(
        WcsArtifactState.PROPOSAL, "any", Status.PROPOSAL, rule="A PROPOSAL record, never a fact"
    ),
    StateRow(
        WcsArtifactState.REVISED_PROPOSAL,
        "any",
        Status.PROPOSAL,
        next_rev=True,
        rule="PROPOSAL, next rev",
    ),
    StateRow(WcsArtifactState.ACCEPTED, "any", Status.ACCEPTED, rule="Approved for working use"),
    StateRow(
        WcsArtifactState.CANON,
        "fact, entity, or world rule",
        Status.CANON,
        rule="A locked reality record",
    ),
    StateRow(
        WcsArtifactState.CANON,
        "story_spine, story_blueprint, or recut_proposal",
        Status.ACCEPTED,
        structure_locked=True,
        rule="Telling records top out at ACCEPTED (OQ-9)",
    ),
    StateRow(WcsArtifactState.SLUSH, "any", Status.SLUSHED, rule="Only the name differs"),
    StateRow(WcsArtifactState.REJECTED, "any", Status.REJECTED, rule="Kept for audit"),
    StateRow(
        WcsArtifactState.SUPERSEDED,
        "any",
        Status.DEPRECATED,
        successor_required=True,
        rule="Successor named",
    ),
    StateRow(
        WcsArtifactState.FORK,
        "any",
        None,
        admission=Admission.REFUSED,
        rule="Canon branches are outside v0.1 (§12.8)",
    ),
    StateRow(
        WcsArtifactState.SHIP,
        "any",
        None,
        admission=Admission.GATE_OUTCOME,
        rule="A SHIP-gate outcome; PUBLISHED tier on the CANON records the segment renders",
    ),
)


@dataclass(frozen=True)
class GateRow:
    wcs_gate: WcsGateType
    nsres_gate: Gate | None
    next_rev: bool = False
    reject_at_holding_gate: bool = False
    rule: str = ""


GATE_ROWS: tuple[GateRow, ...] = (
    GateRow(WcsGateType.INTAKE_GATE, None, rule="Classification inside WCS; no NSRES counterpart"),
    GateRow(WcsGateType.PROPOSAL_GATE, Gate.PROPOSAL, rule="Whether a proposal enters the work"),
    GateRow(
        WcsGateType.REVISION_GATE,
        Gate.PROPOSAL,
        next_rev=True,
        rule=(
            "PROPOSAL on the next rev; a revision of a STRUCTURE or INTEGRATION output"
            " keeps that gate"
        ),
    ),
    GateRow(
        WcsGateType.STRUCTURE_GATE, Gate.STRUCTURE, rule="Result is ACCEPTED and structure-locked"
    ),
    GateRow(WcsGateType.CANON_GATE, Gate.CANON, rule="One candidate per gate, never batched"),
    GateRow(
        WcsGateType.INTEGRATION_GATE, Gate.INTEGRATION, rule="Edits to ACCEPTED text follow §12.3"
    ),
    GateRow(
        WcsGateType.DELETE_GATE,
        None,
        reject_at_holding_gate=True,
        rule="The REJECT outcome of the gate that holds the record; slushing is not a delete",
    ),
    GateRow(WcsGateType.SHIP_GATE, Gate.SHIP, rule="Releases a segment"),
)


@dataclass(frozen=True)
class DecisionRow:
    wcs_decision: WcsDecision
    nsres_outcomes: tuple[GateOutcome, ...]
    in_scope: bool = True
    rule: str = ""


DECISION_ROWS: tuple[DecisionRow, ...] = (
    DecisionRow(WcsDecision.ACCEPT, (GateOutcome.ACCEPT,)),
    DecisionRow(
        WcsDecision.ACCEPT_AS_CANON,
        (GateOutcome.ACCEPT, GateOutcome.CANONIZE),
        rule="Two separate decisions; NSRES never combines them in one confirmation",
    ),
    DecisionRow(WcsDecision.REVISE, (GateOutcome.REVISE,)),
    DecisionRow(
        WcsDecision.REDIRECT, (), rule="No outcome; the record stays PROPOSAL and is routed again"
    ),
    DecisionRow(WcsDecision.FORK, (), in_scope=False, rule="A canon branch (outside v0.1)"),
    DecisionRow(WcsDecision.SLUSH, (GateOutcome.SLUSH,)),
    DecisionRow(WcsDecision.REJECT, (GateOutcome.REJECT,), rule="Through DELETE_GATE inside WCS"),
    DecisionRow(
        WcsDecision.REVERT,
        (),
        rule="A new PROPOSAL that restores an earlier revision; nothing is erased",
    ),
)


def state_row(state: WcsArtifactState, artifact_type: str) -> StateRow:
    """The one crosswalk row for an artifact (the CANON state splits by artifact type)."""
    if state is WcsArtifactState.CANON:
        return STATE_ROWS[6] if artifact_type in TELLING_CANON_TYPES else STATE_ROWS[5]
    matches = [row for row in STATE_ROWS if row.wcs_state is state]
    assert len(matches) == 1, f"crosswalk has {len(matches)} rows for {state}"
    return matches[0]


def gate_row(gate: WcsGateType) -> GateRow:
    return next(row for row in GATE_ROWS if row.wcs_gate is gate)


def decision_row(decision: WcsDecision) -> DecisionRow:
    return next(row for row in DECISION_ROWS if row.wcs_decision is decision)


@dataclass(frozen=True)
class ImportDecision:
    admission: Admission
    status: Status | None
    structure_locked: bool
    next_rev: bool
    reason: str


def import_decision(
    state: WcsArtifactState,
    artifact_type: str,
    *,
    validator_failed: bool = False,
    successor: str | None = None,
) -> ImportDecision:
    """How one WCS artifact maps into NSRES. Pure; writes nothing (D-016)."""
    if validator_failed:
        return ImportDecision(
            Admission.REFUSED,
            None,
            False,
            False,
            "WCS validator FAIL: quarantined, not imported (REQ-12.2.2)",
        )
    row = state_row(state, artifact_type)
    if row.admission is not Admission.RECORD:
        return ImportDecision(row.admission, None, False, False, row.rule)
    if row.successor_required and not successor:
        return ImportDecision(
            Admission.REFUSED, None, False, False, "SUPERSEDED needs its successor reference"
        )
    return ImportDecision(
        Admission.RECORD, row.nsres_status, row.structure_locked, row.next_rev, row.rule
    )
