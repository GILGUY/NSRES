"""Small record builders and a deterministic store for the WP-020 tests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count
from pathlib import Path
from typing import Any

from nsres.domain import records as r
from nsres.domain.uuid7 import Uuid7Generator
from nsres.domain.vocab import (
    EntityKind,
    FindingEvidence,
    FindingStatus,
    Plane,
    Provenance,
    Severity,
    Status,
    ThreadRank,
    TruthValue,
)
from nsres.store import GateConsole, Store

FAIL_MARK = "fails isolation"


class Clock:
    """A UTC clock that advances one second per reading."""

    def __init__(self) -> None:
        self._ticks = count()

    def __call__(self) -> str:
        second = next(self._ticks)
        return f"2026-10-25T19:{second // 60 % 60:02d}:{second % 60:02d}Z"


def ids(seed: int = 7) -> Uuid7Generator:
    ticks = count(1_729_879_320_000)
    return Uuid7Generator(lambda: next(ticks), seed=seed)


IDS = ids(99)


def isolation_check(record: Any) -> Sequence[str]:
    """Passes unless the record's notes carry the failure mark."""
    return [f"{record.handle}: rule suite fails in isolation"] if record.notes == FAIL_MARK else []


def new_store(root: Path) -> tuple[Store, GateConsole]:
    store = Store.create(root, clock=Clock(), ids=ids())
    return store, store.gate_console(isolation_check)


def _core(handle: str, plane: Plane, provenance: Provenance, notes: str | None) -> dict[str, Any]:
    return {
        "uuid": IDS.new_str(),
        "handle": handle,
        "rev": 1,
        "status": Status.PROPOSAL,
        "provenance": provenance,
        "plane": plane,
        "tx": r.TxRange(from_rev=0, to_rev=None),
        "notes": notes,
    }


def character(
    handle: str = "CHR-001",
    name: str = "Mara Voss",
    *,
    provenance: Provenance = Provenance.AUTHOR,
    notes: str | None = None,
    traits: dict[str, str] | None = None,
) -> r.Entity:
    return r.Entity(
        **_core(handle, Plane.REALITY, provenance, notes),
        kind=EntityKind.CHARACTER,
        canonical_name=name,
        fixed_traits=traits or {},
    )


def obj(handle: str, name: str, *, provenance: Provenance = Provenance.AUTHOR) -> r.Entity:
    return r.Entity(
        **_core(handle, Plane.REALITY, provenance, None),
        kind=EntityKind.OBJECT,
        canonical_name=name,
    )


def fact(
    handle: str = "INF-006",
    subject: str = "CHR-001",
    *,
    valid_from: int | None = None,
    valid_to: int | None = None,
) -> r.Fact:
    return r.Fact(
        **_core(handle, Plane.REALITY, Provenance.AUTHOR, None),
        subject=subject,
        predicate="saw",
        object_value="CHR-004",
        valid=r.StoryInterval(from_min=valid_from, to_min=valid_to),
        truth=TruthValue.TRUE,
    )


def thread(handle: str = "THR-02") -> r.Thread:
    return r.Thread(
        **_core(handle, Plane.TELLING, Provenance.AUTHOR, None),
        name="Jonah's claim",
        rank=ThreadRank.SECONDARY,
        dramatic_question="What is Jonah to Edmund?",
    )


def draft(handle: str = "DRF-007-02") -> r.Draft:
    return r.Draft(
        **_core(handle, Plane.RENDERING, Provenance.AI_PROPOSAL, None),
        scene="SCN-007",
        packet="PKT-007-r3",
        packet_hash="sha256:" + "a" * 64,
        drafter="drafter-a",
        text_hash="sha256:" + "b" * 64,
        draft_state="VALIDATED",
    )


def resolution(handle: str = "RES-0011") -> r.ResolutionRecord:
    return r.ResolutionRecord(
        **_core(handle, Plane.CONTROL, Provenance.ENGINE_BRIDGE, None),
        findings=("FND-R-01",),
        chosen_repair="Bridge: Hale already at The Bell",
    )


def finding(handle: str = "FND-007-01-02", severity: Severity = Severity.MAJOR) -> r.Finding:
    core = {
        key: value
        for key, value in _core(handle, Plane.CONTROL, Provenance.ENGINE_BRIDGE, None).items()
        if key != "status"
    }
    return r.Finding(
        **core,
        rule="AU-34",
        severity=severity,
        records=("INF-002",),
        evidence=FindingEvidence.CONTENT_READ,
        detection_confidence=0.9,
        status=FindingStatus.OPEN,
    )


def next_revision(current: Any, **changes: Any) -> Any:
    """The edit a human would submit: same identity, rev one higher."""
    return replace(current, rev=current.rev + 1, **changes)
