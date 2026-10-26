"""The §5.4 record lifecycle: the table as data, and every (status, gate, outcome) combination.

``plan_decision`` is checked against an oracle written separately here from the spec rows and
DECISIONS D-013, over every record kind, status, tier, gate, and outcome. Every combination
the oracle forbids must come back refused with a named reason.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

from nsres.domain.records import BaseRecord
from nsres.domain.vocab import GATE_OUTCOMES, Gate, GateOutcome, Provenance, Status, Tier
from nsres.store.lifecycle import LIFECYCLE, Plan, Refusal, Refused, acceptance_gate, plan_decision
from tests import builders as b
from tests import spec_text as spec

# --- the table against the spec ---------------------------------------------------------------


def _spec_rows() -> list[tuple[str, str, str]]:
    block = spec.section("### 5.4")
    marker = "**Record lifecycle.**"
    return list(
        zip(
            spec.table_column(block, marker, 0),
            spec.table_column(block, marker, 1),
            spec.table_column(block, marker, 3),
            strict=True,
        )
    )


def test_one_rule_per_spec_row_with_the_spec_wording() -> None:
    rows = _spec_rows()
    assert len(rows) == len(LIFECYCLE) == 11
    for rule, (spec_from, trigger, spec_to) in zip(LIFECYCLE, rows, strict=True):
        assert rule.spec_from == spec_from, rule
        assert rule.trigger == trigger, rule
        assert spec_to.split()[0].rstrip(";,") == rule.to_status.value, (rule, spec_to)
        assert (rule.to_tier is Tier.PUBLISHED) == ("PUBLISHED" in spec_to), rule


def test_spec_gate_column_names_only_known_gates() -> None:
    block = spec.section("### 5.4")
    for cell in spec.table_column(block, "**Record lifecycle.**", 2):
        for gate in re.findall(r"\b([A-Z]+) gate\b", cell):
            assert gate in {g.value for g in Gate}, cell


# --- the planner against an independent oracle -----------------------------------------------

KINDS: dict[str, Callable[[], BaseRecord]] = {
    "reality": lambda: b.character(),
    "micro-fact": lambda: b.character("CHR-050", "a candle", provenance=Provenance.DRAFT_EMERGENT),
    "telling": lambda: b.thread(),
    "draft": lambda: b.draft(),
    "resolution": lambda: b.resolution(),
}
ACCEPT_GATE = {
    "reality": Gate.PROPOSAL,
    "micro-fact": Gate.PROPOSAL,
    "telling": Gate.STRUCTURE,
    "draft": Gate.INTEGRATION,
    "resolution": Gate.INTEGRATION,
}
REALITY_KINDS = {"reality", "micro-fact"}


def _oracle(
    kind: str, status: Status, tier: Tier | None, gate: Gate, outcome: GateOutcome
) -> tuple[Status, Tier | None] | None:
    """The permitted result, or None when the combination must be refused."""
    if outcome not in GATE_OUTCOMES[gate]:
        return None
    unchanged = (status, tier)
    accept_gate = ACCEPT_GATE[kind]
    if status is Status.PROPOSAL:
        if kind == "micro-fact":
            if gate is Gate.CANON:
                return {
                    GateOutcome.ACCEPT_AND_REGISTER: (Status.CANON, None),
                    GateOutcome.REJECT_MICRO_FACT: (Status.REJECTED, None),
                    GateOutcome.REVISE: unchanged,
                }.get(outcome)
            return None
        if outcome is GateOutcome.ACCEPT:
            return (Status.ACCEPTED, None) if gate is accept_gate else None
        if outcome is GateOutcome.REJECT:
            return (Status.REJECTED, None)
        if outcome is GateOutcome.SLUSH:
            return (Status.SLUSHED, None)
        if outcome is GateOutcome.REVISE:
            return unchanged if gate in (accept_gate, Gate.PROPOSAL) else None
        return None
    if status is Status.ACCEPTED:
        if outcome is GateOutcome.CANONIZE:
            return (Status.CANON, None) if kind in REALITY_KINDS else None
        if outcome is GateOutcome.ACCEPT:  # edit
            return unchanged if gate is accept_gate else None
        if outcome is GateOutcome.REJECT:  # retire
            return (Status.DEPRECATED, None) if gate is accept_gate else None
        if outcome is GateOutcome.REVISE:
            ok = gate is accept_gate or (gate is Gate.CANON and kind in REALITY_KINDS)
            return unchanged if ok else None
        return None
    if status is Status.CANON:
        if outcome is GateOutcome.CANONIZE:  # edit, with a RETCON when PUBLISHED
            return unchanged
        if outcome is GateOutcome.REJECT:  # retire, at the gate matching CANON status
            return (Status.DEPRECATED, None) if gate is Gate.CANON else None
        if outcome is GateOutcome.SHIP:
            return (Status.CANON, Tier.PUBLISHED) if tier is None else None
        if outcome is GateOutcome.HOLD:
            return unchanged
        if outcome is GateOutcome.REVISE:
            return unchanged if gate is Gate.CANON else None
        return None
    return None


def _states(kind: str) -> list[tuple[Status, Tier | None]]:
    states: list[tuple[Status, Tier | None]] = [
        (Status.PROPOSAL, None),
        (Status.ACCEPTED, None),
        (Status.REJECTED, None),
        (Status.SLUSHED, None),
        (Status.DEPRECATED, None),
    ]
    if kind in REALITY_KINDS:
        states += [(Status.CANON, None), (Status.CANON, Tier.PUBLISHED)]
    return states


CASES = [
    (kind, status, tier, gate, outcome)
    for kind in KINDS
    for status, tier in _states(kind)
    for gate in Gate
    for outcome in GateOutcome
]


def _is_edit(status: Status, outcome: GateOutcome) -> bool:
    return (status is Status.ACCEPTED and outcome is GateOutcome.ACCEPT) or (
        status is Status.CANON and outcome is GateOutcome.CANONIZE
    )


def test_case_count() -> None:
    # 5 kinds; reality kinds have 7 states, others 5; 5 gates; 9 outcomes.
    assert len(CASES) == (2 * 7 + 3 * 5) * 5 * 9


@pytest.mark.parametrize(("kind", "status", "tier", "gate", "outcome"), CASES)
def test_planner_matches_the_oracle(
    kind: str, status: Status, tier: Tier | None, gate: Gate, outcome: GateOutcome
) -> None:
    record: Any = replace(KINDS[kind](), status=status, tier=tier)
    accepted_by = ACCEPT_GATE[kind] if status is Status.ACCEPTED else None
    edit = _is_edit(status, outcome)
    revision = replace(record, rev=record.rev + 1) if edit else None
    retcon = ("DRF-001-01 S3",) if tier is Tier.PUBLISHED else ()
    planned = plan_decision(
        record, gate, outcome, accepted_by=accepted_by, revision=revision, retcon=retcon
    )
    expected = _oracle(kind, status, tier, gate, outcome)
    if expected is None:
        assert isinstance(planned, Refused), planned
        assert isinstance(planned.reason, Refusal)
        assert planned.detail
    else:
        assert isinstance(planned, Plan), planned
        assert (planned.status, planned.tier) == expected


def _accepted(record: BaseRecord) -> Any:
    return replace(record, status=Status.ACCEPTED)


def test_an_edit_needs_a_revision_and_other_outcomes_refuse_one() -> None:
    record = _accepted(b.character())
    missing = plan_decision(
        record,
        Gate.PROPOSAL,
        GateOutcome.ACCEPT,
        accepted_by=Gate.PROPOSAL,
        revision=None,
        retcon=(),
    )
    assert isinstance(missing, Refused)
    assert missing.reason is Refusal.REVISION_REQUIRED
    extra = plan_decision(
        record,
        Gate.CANON,
        GateOutcome.CANONIZE,
        accepted_by=Gate.PROPOSAL,
        revision=record,
        retcon=(),
    )
    assert isinstance(extra, Refused)
    assert extra.reason is Refusal.REVISION_NOT_EXPECTED


def test_editing_published_canon_needs_a_retcon() -> None:
    record = replace(b.character(), status=Status.CANON, tier=Tier.PUBLISHED)
    planned = plan_decision(
        record, Gate.CANON, GateOutcome.CANONIZE, accepted_by=None, revision=record, retcon=()
    )
    assert isinstance(planned, Refused)
    assert planned.reason is Refusal.RETCON_REQUIRED


@pytest.mark.parametrize(
    ("record", "gate"),
    [
        (b.character(), Gate.PROPOSAL),
        (b.thread(), Gate.STRUCTURE),
        (b.draft(), Gate.INTEGRATION),
        (b.resolution(), Gate.INTEGRATION),
    ],
    ids=["reality", "telling", "draft", "resolution"],
)
def test_acceptance_gate_by_record_kind(record: BaseRecord, gate: Gate) -> None:
    assert acceptance_gate(record) is gate


def test_named_reasons_for_typical_refusals() -> None:
    proposal = b.character()
    micro = b.character("CHR-050", "a candle", provenance=Provenance.DRAFT_EMERGENT)
    cases = [
        (proposal, Gate.SHIP, GateOutcome.ACCEPT, Refusal.OUTCOME_NOT_AT_GATE),
        (proposal, Gate.STRUCTURE, GateOutcome.ACCEPT, Refusal.WRONG_GATE),
        (proposal, Gate.CANON, GateOutcome.CANONIZE, Refusal.NO_TRANSITION),
        (proposal, Gate.CANON, GateOutcome.ACCEPT_AND_REGISTER, Refusal.NOT_A_MICRO_FACT),
        (micro, Gate.PROPOSAL, GateOutcome.ACCEPT, Refusal.MICRO_FACT_CODES_ONLY),
        (_accepted(b.thread()), Gate.CANON, GateOutcome.CANONIZE, Refusal.NOT_A_REALITY_RECORD),
        (
            replace(proposal, status=Status.REJECTED),
            Gate.PROPOSAL,
            GateOutcome.ACCEPT,
            Refusal.NO_TRANSITION,
        ),
    ]
    for record, gate, outcome, reason in cases:
        accepted_by = acceptance_gate(record) if record.status is Status.ACCEPTED else None
        planned = plan_decision(
            record, gate, outcome, accepted_by=accepted_by, revision=None, retcon=()
        )
        assert isinstance(planned, Refused), (record.handle, gate, outcome)
        assert planned.reason is reason, (record.handle, gate, outcome, planned)
