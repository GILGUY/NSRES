"""Canon precedence (spec §3.4 items 5 and 6; DECISIONS D-020).

Across tiers the higher tier wins automatically. Within a tier the engine never picks: the
conflict goes to a human gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from nsres.domain.records import BaseRecord, CanonRule
from nsres.domain.vocab import (
    CanonRuleClass,
    Gate,
    Plane,
    PrecedenceTier,
    Status,
    Tier,
    precedence_rank,
)
from nsres.store.lifecycle import acceptance_gate


def tier_of(record: BaseRecord) -> PrecedenceTier | None:
    """The §3.4 tier of a record, or None for REJECTED, SLUSHED, and DEPRECATED records."""
    if record.status is Status.CANON and record.tier is Tier.PUBLISHED:
        return PrecedenceTier.PUBLISHED
    if isinstance(record, CanonRule) and record.status in (Status.ACCEPTED, Status.CANON):
        if record.rule_class is CanonRuleClass.INVARIANT and record.status is Status.CANON:
            return PrecedenceTier.INVARIANT
        if record.rule_class is CanonRuleClass.DEFAULT:
            return PrecedenceTier.DEFAULT
    if record.status is Status.CANON:
        return PrecedenceTier.CANON
    if record.status is Status.ACCEPTED:
        return PrecedenceTier.ACCEPTED
    if record.status is Status.PROPOSAL:
        return PrecedenceTier.PROPOSAL
    return None


@dataclass(frozen=True)
class Resolution:
    """``winner`` is set only across tiers; a same-tier conflict names the gate instead."""

    winner: BaseRecord | None
    loser: BaseRecord | None
    tiers: tuple[PrecedenceTier, PrecedenceTier]
    gate: Gate | None

    @property
    def needs_gate(self) -> bool:
        return self.winner is None


def deciding_gate(record: BaseRecord) -> Gate:
    """The human gate for a same-tier conflict: CANON for reality records (§3.4 item 6)."""
    return Gate.CANON if record.plane is Plane.REALITY else acceptance_gate(record)


def resolve(first: BaseRecord, second: BaseRecord) -> Resolution:
    a, b = tier_of(first), tier_of(second)
    if a is None or b is None:
        retired = first if a is None else second
        raise ValueError(f"{retired.handle} is {retired.status} and takes part in no conflict")
    if a is b:
        return Resolution(None, None, (a, b), deciding_gate(first))
    if precedence_rank(a) < precedence_rank(b):
        return Resolution(first, second, (a, b), None)
    return Resolution(second, first, (a, b), None)
