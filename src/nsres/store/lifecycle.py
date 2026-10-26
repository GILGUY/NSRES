"""The §5.4 record lifecycle as data, and the planner that applies it (DECISIONS D-013).

``plan_decision`` is pure: given a record's current revision and a requested gate decision,
it returns either a ``Refusal`` with a reason or a ``Plan`` naming the new status and tier.
The store executes plans; it never decides a transition itself.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from nsres.domain.records import BaseRecord, Draft, ResolutionRecord
from nsres.domain.vocab import GATE_OUTCOMES, Gate, GateOutcome, Plane, Provenance, Status, Tier


class Refusal(StrEnum):
    """Why a requested write was refused. A refused request writes nothing (D-013 item 6)."""

    UNKNOWN_RECORD = "UNKNOWN_RECORD"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    NOT_PROPOSAL = "NOT_PROPOSAL"
    OUTCOME_NOT_AT_GATE = "OUTCOME_NOT_AT_GATE"
    WRONG_GATE = "WRONG_GATE"
    NO_TRANSITION = "NO_TRANSITION"
    MICRO_FACT_CODES_ONLY = "MICRO_FACT_CODES_ONLY"
    NOT_A_MICRO_FACT = "NOT_A_MICRO_FACT"
    NOT_A_REALITY_RECORD = "NOT_A_REALITY_RECORD"
    GUARD_FAILED = "GUARD_FAILED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    REVISION_NOT_EXPECTED = "REVISION_NOT_EXPECTED"
    REVISION_MISMATCH = "REVISION_MISMATCH"
    RETCON_REQUIRED = "RETCON_REQUIRED"
    DEPENDENTS_REMAIN = "DEPENDENTS_REMAIN"
    ALREADY_PUBLISHED = "ALREADY_PUBLISHED"
    ACTOR_REQUIRED = "ACTOR_REQUIRED"
    REASON_REQUIRED = "REASON_REQUIRED"
    BLOCKING_NOT_WAIVABLE = "BLOCKING_NOT_WAIVABLE"
    FINDING_NOT_OPEN = "FINDING_NOT_OPEN"
    WRONG_VERSION_STATE = "WRONG_VERSION_STATE"
    NOT_A_FINDING = "NOT_A_FINDING"


IsolationCheck = Callable[[Any], Sequence[str]]
"""Returns the rule-suite failures for one record in isolation; empty means it passes."""


def is_micro_fact(record: BaseRecord) -> bool:
    """A reality-plane PROPOSAL invented by a drafter (§0.7 Micro-Canon Rule; D-013 item 3)."""
    return record.provenance is Provenance.DRAFT_EMERGENT and record.plane is Plane.REALITY


def acceptance_gate(record: BaseRecord) -> Gate:
    """The gate that moves a PROPOSAL of this kind to ACCEPTED (D-013 item 2)."""
    if record.plane is Plane.TELLING:
        return Gate.STRUCTURE
    if isinstance(record, Draft | ResolutionRecord):
        return Gate.INTEGRATION
    return Gate.PROPOSAL


@dataclass(frozen=True)
class Rule:
    """One row of the §5.4 record-lifecycle table."""

    row: int
    spec_from: str
    trigger: str
    to_status: Status
    to_tier: Tier | None = None
    edit: bool = False


LIFECYCLE: tuple[Rule, ...] = (
    Rule(1, "(new)", "Created by author, engine, or AI", Status.PROPOSAL),
    Rule(2, "PROPOSAL", "Approved", Status.ACCEPTED),
    Rule(3, "PROPOSAL", "Declined", Status.REJECTED),
    Rule(4, "PROPOSAL", "Declined for this work, kept for reuse", Status.SLUSHED),
    Rule(5, "PROPOSAL (micro-fact)", "ACCEPT_AND_REGISTER", Status.CANON),
    Rule(6, "PROPOSAL (micro-fact)", "REJECT_MICRO_FACT", Status.REJECTED),
    Rule(7, "ACCEPTED (reality record)", "Lock", Status.CANON),
    Rule(8, "ACCEPTED", "Edit", Status.ACCEPTED, edit=True),
    Rule(9, "CANON", "Edit", Status.CANON, edit=True),
    Rule(10, "ACCEPTED or CANON", "Retire", Status.DEPRECATED),
    Rule(11, "CANON", "Segment released", Status.CANON, to_tier=Tier.PUBLISHED),
)
"""One rule per §5.4 row; ``tests/unit/test_lifecycle.py`` checks them against the spec."""

_BY_ROW = {rule.row: rule for rule in LIFECYCLE}


@dataclass(frozen=True)
class Plan:
    """What a permitted decision does. ``rule`` is None for REVISE and HOLD (no change)."""

    rule: Rule | None
    status: Status
    tier: Tier | None


@dataclass(frozen=True)
class Refused:
    reason: Refusal
    detail: str


def _deciding_gates(record: BaseRecord, accepted_by: Gate | None) -> set[Gate]:
    """Gates that can decide this record now (used for REVISE; D-013 item 6)."""
    if record.status is Status.PROPOSAL:
        return {Gate.CANON} if is_micro_fact(record) else {acceptance_gate(record), Gate.PROPOSAL}
    if record.status is Status.ACCEPTED:
        gates = {accepted_by} if accepted_by is not None else set()
        if record.plane is Plane.REALITY:
            gates.add(Gate.CANON)
        return gates
    if record.status is Status.CANON:
        return {Gate.CANON, Gate.SHIP}
    return set()


def plan_decision(
    record: BaseRecord,
    gate: Gate,
    outcome: GateOutcome,
    *,
    accepted_by: Gate | None,
    revision: BaseRecord | None,
    retcon: Sequence[str],
) -> Plan | Refused:
    """Apply the lifecycle table to one requested decision. Guards that need the rest of the
    store (isolation check, dependents) are run by the caller after a ``Plan`` comes back."""
    if outcome not in GATE_OUTCOMES[gate]:
        return Refused(
            Refusal.OUTCOME_NOT_AT_GATE, f"{outcome} is not an outcome of the {gate} gate"
        )

    status = record.status
    edit_outcome = (status is Status.ACCEPTED and outcome is GateOutcome.ACCEPT) or (
        status is Status.CANON and outcome is GateOutcome.CANONIZE
    )
    if edit_outcome and revision is None:
        return Refused(Refusal.REVISION_REQUIRED, f"an edit of a {status} record needs a revision")
    if not edit_outcome and revision is not None:
        return Refused(
            Refusal.REVISION_NOT_EXPECTED, f"{outcome} on a {status} record takes no revision"
        )

    if outcome in (GateOutcome.REVISE, GateOutcome.HOLD):
        if outcome is GateOutcome.HOLD and status is not Status.CANON:
            return Refused(Refusal.NO_TRANSITION, f"HOLD applies to CANON records, not {status}")
        if gate not in _deciding_gates(record, accepted_by):
            return Refused(
                Refusal.WRONG_GATE, f"the {gate} gate cannot decide this {status} record now"
            )
        return Plan(rule=None, status=status, tier=record.tier)

    if status is Status.PROPOSAL:
        return _plan_proposal(record, gate, outcome)
    if status is Status.ACCEPTED:
        return _plan_accepted(record, gate, outcome, accepted_by)
    if status is Status.CANON:
        return _plan_canon(record, gate, outcome, retcon)
    return Refused(Refusal.NO_TRANSITION, f"a {status} record has no outgoing transition")


def _plan_proposal(record: BaseRecord, gate: Gate, outcome: GateOutcome) -> Plan | Refused:
    micro = is_micro_fact(record)
    if outcome in (GateOutcome.ACCEPT_AND_REGISTER, GateOutcome.REJECT_MICRO_FACT):
        if not micro:
            return Refused(
                Refusal.NOT_A_MICRO_FACT,
                f"{outcome} decides micro-facts (DRAFT_EMERGENT reality records) only",
            )
        rule = _BY_ROW[5] if outcome is GateOutcome.ACCEPT_AND_REGISTER else _BY_ROW[6]
        return Plan(rule=rule, status=rule.to_status, tier=None)
    if micro:
        return Refused(
            Refusal.MICRO_FACT_CODES_ONLY,
            "the CANON gate decides a micro-fact with ACCEPT_AND_REGISTER or REJECT_MICRO_FACT",
        )
    if outcome is GateOutcome.ACCEPT:
        expected = acceptance_gate(record)
        if gate is not expected:
            return Refused(
                Refusal.WRONG_GATE, f"this record is accepted at the {expected} gate, not {gate}"
            )
        return Plan(rule=_BY_ROW[2], status=Status.ACCEPTED, tier=None)
    if outcome is GateOutcome.REJECT:
        return Plan(rule=_BY_ROW[3], status=Status.REJECTED, tier=None)
    if outcome is GateOutcome.SLUSH:
        return Plan(rule=_BY_ROW[4], status=Status.SLUSHED, tier=None)
    return Refused(Refusal.NO_TRANSITION, f"{outcome} does not apply to a PROPOSAL record")


def _plan_accepted(
    record: BaseRecord, gate: Gate, outcome: GateOutcome, accepted_by: Gate | None
) -> Plan | Refused:
    if outcome is GateOutcome.CANONIZE:
        if record.plane is not Plane.REALITY:
            return Refused(
                Refusal.NOT_A_REALITY_RECORD,
                f"only reality records are locked as CANON; this one is {record.plane}",
            )
        return Plan(rule=_BY_ROW[7], status=Status.CANON, tier=None)
    if outcome in (GateOutcome.ACCEPT, GateOutcome.REJECT):
        if gate is not accepted_by:
            return Refused(
                Refusal.WRONG_GATE,
                f"this record was accepted at the {accepted_by} gate; {outcome} must come from it",
            )
        rule = _BY_ROW[8] if outcome is GateOutcome.ACCEPT else _BY_ROW[10]
        return Plan(rule=rule, status=rule.to_status, tier=None)
    return Refused(Refusal.NO_TRANSITION, f"{outcome} does not apply to an ACCEPTED record")


def _plan_canon(
    record: BaseRecord, gate: Gate, outcome: GateOutcome, retcon: Sequence[str]
) -> Plan | Refused:
    if outcome is GateOutcome.CANONIZE:
        if record.tier is Tier.PUBLISHED and not retcon:
            return Refused(
                Refusal.RETCON_REQUIRED,
                "editing PUBLISHED canon needs a RETCON naming the passages",
            )
        return Plan(rule=_BY_ROW[9], status=Status.CANON, tier=record.tier)
    if outcome is GateOutcome.REJECT:
        if gate is not Gate.CANON:
            return Refused(
                Refusal.WRONG_GATE, f"a CANON record is retired at the CANON gate, not {gate}"
            )
        return Plan(rule=_BY_ROW[10], status=Status.DEPRECATED, tier=None)
    if outcome is GateOutcome.SHIP:
        if record.tier is Tier.PUBLISHED:
            return Refused(Refusal.ALREADY_PUBLISHED, f"{record.handle} is already PUBLISHED")
        return Plan(rule=_BY_ROW[11], status=Status.CANON, tier=Tier.PUBLISHED)
    return Refused(Refusal.NO_TRANSITION, f"{outcome} does not apply to a CANON record")
