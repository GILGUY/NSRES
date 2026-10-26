"""The record store: lifecycle rows end to end, audit chain, reload, bitemporal reads, model
versions, waivers, and the engine write path (spec §0.7, §5.4, §10.4-10.5; D-012 to D-014)."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from nsres.domain import records as r
from nsres.domain.vocab import (
    AuditKind,
    FindingStatus,
    Gate,
    GateOutcome,
    ModelVersionState,
    Provenance,
    Severity,
    Status,
    Tier,
)
from nsres.store import (
    ArtifactCorruptError,
    ArtifactStore,
    GateConsole,
    Refusal,
    Store,
    StoreCorruptError,
)
from nsres.store.log import (
    AUDIT_FILE,
    RECORDS_FILE,
    audit_line_hash,
    read_audit,
    read_transactions,
    verify_chain,
    verify_coverage,
)
from tests import builders as b

HUMAN = "author"


def _accept(console: GateConsole, record: Any, gate: Gate = Gate.PROPOSAL) -> Any:
    assert console.propose(record, actor=HUMAN).ok
    result = console.decide(gate, record.handle, GateOutcome.ACCEPT, actor=HUMAN)
    assert result.ok, result
    return result.record


def _canon(console: GateConsole, record: Any) -> Any:
    _accept(console, record)
    result = console.decide(Gate.CANON, record.handle, GateOutcome.CANONIZE, actor=HUMAN)
    assert result.ok, result
    return result.record


def _state(store: Store) -> ModelVersionState:
    """Read the version state through a call, so each assertion sees a fresh value."""
    return store.model_version.state


def _sizes(store: Store) -> tuple[int, int]:
    return ((store.root / RECORDS_FILE).stat().st_size, (store.root / AUDIT_FILE).stat().st_size)


# --- each §5.4 record-lifecycle row is a passing test ----------------------------------------


def test_row_01_new_record_is_proposal(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    result = console.propose(b.character(), actor=HUMAN)
    assert result.ok
    assert result.record.status is Status.PROPOSAL
    trail = store.audit_trail()[-1]
    assert (trail.kind, trail.from_state, trail.to_state) == (
        AuditKind.TRANSITION,
        "(new)",
        "PROPOSAL",
    )
    assert trail.trigger == "Created by author, engine, or AI"


@pytest.mark.parametrize(
    ("make", "gate"),
    [
        (b.character, Gate.PROPOSAL),
        (b.thread, Gate.STRUCTURE),
        (b.draft, Gate.INTEGRATION),
        (b.resolution, Gate.INTEGRATION),
    ],
    ids=[
        "reality at PROPOSAL",
        "telling at STRUCTURE",
        "draft at INTEGRATION",
        "RES at INTEGRATION",
    ],
)
def test_row_02_proposal_approved_becomes_accepted(tmp_path: Path, make: Any, gate: Gate) -> None:
    store, console = b.new_store(tmp_path)
    record = _accept(console, make(), gate)
    assert record.status is Status.ACCEPTED
    assert record.rev == 2
    assert store.accepted_by(record.handle) is gate
    gate_record = store.gate_records(record.handle)[-1]
    assert (gate_record.gate, gate_record.outcome, gate_record.actor) == (
        gate,
        GateOutcome.ACCEPT,
        HUMAN,
    )
    assert record.gate == gate_record.uuid


def test_row_02_guard_rule_suite_must_pass(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    console.propose(b.character(notes=b.FAIL_MARK), actor=HUMAN)
    before = _sizes(store)
    result = console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.ACCEPT, actor=HUMAN)
    assert result.refusal is Refusal.GUARD_FAILED
    assert "rule suite fails in isolation" in result.detail
    assert _sizes(store) == before
    assert store.get("CHR-001").status is Status.PROPOSAL


@pytest.mark.parametrize("gate", [Gate.PROPOSAL, Gate.STRUCTURE, Gate.INTEGRATION, Gate.CANON])
def test_row_03_proposal_declined_at_any_gate(tmp_path: Path, gate: Gate) -> None:
    _, console = b.new_store(tmp_path)
    console.propose(b.character(), actor=HUMAN)
    result = console.decide(
        gate, "CHR-001", GateOutcome.REJECT, actor=HUMAN, reason="not this book"
    )
    assert result.ok
    assert result.record.status is Status.REJECTED


def test_row_04_proposal_slushed(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    console.propose(b.character(), actor=HUMAN)
    result = console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.SLUSH, actor=HUMAN)
    assert result.ok
    assert result.record.status is Status.SLUSHED


def _micro_fact() -> r.Entity:
    return b.obj("OBJ-012", "candle stub on the dresser", provenance=Provenance.DRAFT_EMERGENT)


def test_row_05_micro_fact_accept_and_register_becomes_canon(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    console.propose(_micro_fact(), actor="engine:autopsy")
    result = console.decide(Gate.CANON, "OBJ-012", GateOutcome.ACCEPT_AND_REGISTER, actor=HUMAN)
    assert result.ok
    assert result.record.status is Status.CANON


def test_row_06_micro_fact_reject(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    console.propose(_micro_fact(), actor="engine:autopsy")
    result = console.decide(Gate.CANON, "OBJ-012", GateOutcome.REJECT_MICRO_FACT, actor=HUMAN)
    assert result.ok
    assert result.record.status is Status.REJECTED


def test_row_07_accepted_reality_record_locked_as_canon(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    record = _canon(console, b.character())
    assert record.status is Status.CANON
    assert record.rev == 3


def test_row_08_accepted_edit_at_the_gate_that_accepted_it(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    accepted = _accept(console, b.thread(), Gate.STRUCTURE)
    edit = b.next_revision(accepted, dramatic_question="Who is Jonah's father?")
    wrong = console.decide(Gate.PROPOSAL, "THR-02", GateOutcome.ACCEPT, actor=HUMAN, revision=edit)
    assert wrong.refusal is Refusal.WRONG_GATE
    result = console.decide(
        Gate.STRUCTURE, "THR-02", GateOutcome.ACCEPT, actor=HUMAN, revision=edit
    )
    assert result.ok
    assert result.record.status is Status.ACCEPTED
    assert result.record.dramatic_question == "Who is Jonah's father?"
    assert [rev.rev for rev in store.history("THR-02")] == [1, 2, 3]


def test_row_09_canon_edit_and_retcon_for_published(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    canon = _canon(console, b.character(traits={"role": "housekeeper"}))
    edit = b.next_revision(canon, fixed_traits={"role": "head housekeeper"})
    result = console.decide(Gate.CANON, "CHR-001", GateOutcome.CANONIZE, actor=HUMAN, revision=edit)
    assert result.ok
    assert result.record.fixed_traits == {"role": "head housekeeper"}
    shipped = console.decide(Gate.SHIP, "CHR-001", GateOutcome.SHIP, actor=HUMAN).record
    published_edit = b.next_revision(shipped, fixed_traits={"role": "housekeeper"})
    refused = console.decide(
        Gate.CANON, "CHR-001", GateOutcome.CANONIZE, actor=HUMAN, revision=published_edit
    )
    assert refused.refusal is Refusal.RETCON_REQUIRED
    allowed = console.decide(
        Gate.CANON,
        "CHR-001",
        GateOutcome.CANONIZE,
        actor=HUMAN,
        revision=published_edit,
        retcon=("DRF-003-02 S4",),
    )
    assert allowed.ok
    assert allowed.record.tier is Tier.PUBLISHED
    assert allowed.gate_record is not None
    assert allowed.gate_record.retcon == ("DRF-003-02 S4",)


def test_row_10_retire_accepted_and_canon_after_dependents_are_repointed(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    _accept(console, b.character("CHR-004", "Jonah Pell"))
    _canon(console, b.character())
    fact = _accept(console, b.fact(subject="CHR-004"))
    blocked = console.decide(Gate.PROPOSAL, "CHR-004", GateOutcome.REJECT, actor=HUMAN)
    assert blocked.refusal is Refusal.DEPENDENTS_REMAIN
    assert "INF-006" in blocked.detail
    console.decide(
        Gate.PROPOSAL,
        "INF-006",
        GateOutcome.ACCEPT,
        actor=HUMAN,
        revision=b.next_revision(fact, subject="CHR-001", object_value="OBJ-001"),
    )
    retired = console.decide(
        Gate.PROPOSAL, "CHR-004", GateOutcome.REJECT, actor=HUMAN, successor="CHR-001"
    )
    assert retired.ok
    assert retired.record.status is Status.DEPRECATED
    assert store.get("CHR-001").status is Status.CANON
    console.decide(Gate.PROPOSAL, "INF-006", GateOutcome.REJECT, actor=HUMAN)
    wrong_gate = console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.REJECT, actor=HUMAN)
    assert wrong_gate.refusal is Refusal.WRONG_GATE
    retired_canon = console.decide(Gate.CANON, "CHR-001", GateOutcome.REJECT, actor=HUMAN)
    assert retired_canon.ok
    assert retired_canon.record.status is Status.DEPRECATED


def test_row_11_segment_released_sets_the_published_tier(tmp_path: Path) -> None:
    _, console = b.new_store(tmp_path)
    _canon(console, b.character())
    result = console.decide(Gate.SHIP, "CHR-001", GateOutcome.SHIP, actor=HUMAN)
    assert result.ok
    assert (result.record.status, result.record.tier) == (Status.CANON, Tier.PUBLISHED)
    again = console.decide(Gate.SHIP, "CHR-001", GateOutcome.SHIP, actor=HUMAN)
    assert again.refusal is Refusal.ALREADY_PUBLISHED


def test_revise_and_hold_record_a_gate_decision_without_changing_status(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    console.propose(b.character(), actor=HUMAN)
    revise = console.decide(
        Gate.PROPOSAL, "CHR-001", GateOutcome.REVISE, actor=HUMAN, reason="name the role"
    )
    assert revise.ok
    assert revise.record.rev == 1
    assert store.gate_records("CHR-001")[-1].outcome is GateOutcome.REVISE
    _canon(console, b.character("CHR-002", "Teodor Hale"))
    hold = console.decide(Gate.SHIP, "CHR-002", GateOutcome.HOLD, actor=HUMAN)
    assert hold.ok
    assert hold.record.tier is None


def test_every_refusal_writes_nothing(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    console.propose(b.character(), actor=HUMAN)
    before = (_sizes(store), store.tx, store.snapshot().digest())
    attempts = [
        console.decide(Gate.SHIP, "CHR-001", GateOutcome.ACCEPT, actor=HUMAN),
        console.decide(Gate.SHIP, "CHR-001", GateOutcome.SHIP, actor=HUMAN),
        console.decide(Gate.PROPOSAL, "CHR-999", GateOutcome.ACCEPT, actor=HUMAN),
        console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.ACCEPT, actor=""),
        console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.ACCEPT, actor=HUMAN, override=True),
        console.decide(Gate.CANON, "CHR-001", GateOutcome.CANONIZE, actor=HUMAN),
        console.propose(b.character(), actor=HUMAN),
    ]
    assert [attempt.refusal for attempt in attempts] == [
        Refusal.OUTCOME_NOT_AT_GATE,
        Refusal.NO_TRANSITION,
        Refusal.UNKNOWN_RECORD,
        Refusal.ACTOR_REQUIRED,
        Refusal.REASON_REQUIRED,
        Refusal.NO_TRANSITION,
        Refusal.REVISION_MISMATCH,
    ]
    assert (_sizes(store), store.tx, store.snapshot().digest()) == before


def test_revised_proposal_keeps_the_earlier_row(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    first = console.propose(b.character(), actor=HUMAN).record
    revised = console.propose(
        b.next_revision(first, canonical_name="Mara Voss, housekeeper"), actor=HUMAN
    )
    assert revised.ok
    assert [rev.canonical_name for rev in store.history("CHR-001")] == [
        "Mara Voss",
        "Mara Voss, housekeeper",
    ]
    assert store.audit_trail()[-1].trigger == "Revised proposal"


# --- audit chain --------------------------------------------------------------------------


def _busy_store(root: Path) -> Store:
    store, console = b.new_store(root)
    writer = store.engine_writer("engine:reconcile")
    _canon(console, b.character())
    _accept(console, b.thread(), Gate.STRUCTURE)
    writer.propose(b.character("CHR-004", "Jonah Pell"))
    writer.record_finding(b.finding())
    console.waive_finding("FND-007-01-02", Gate.INTEGRATION, actor=HUMAN, reason="taste")
    writer.begin_reconciliation()
    writer.complete_reconciliation(0)
    console.tag_release(actor=HUMAN)
    console.decide(Gate.SHIP, "CHR-001", GateOutcome.SHIP, actor=HUMAN)
    return store


def _rewrite_line(path: Path, index: int, change: Any) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    document = json.loads(lines[index])
    change(document)
    lines[index] = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_a_fresh_store_verifies(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    assert store.verify() == []
    assert len(store.audit_trail()) == 20


def test_altering_any_audit_line_fails_verification_at_that_line(tmp_path: Path) -> None:
    original = tmp_path / "original"
    store = _busy_store(original)
    count = len(store.audit_trail())
    for index in range(count):
        copy = tmp_path / f"copy-{index}"
        shutil.copytree(original, copy)

        def alter(document: dict[str, Any]) -> None:
            document["actor"] = document["actor"] + " (edited)"

        _rewrite_line(copy / AUDIT_FILE, index, alter)
        reopened_problems = _verify_copy(copy)
        assert reopened_problems == [f"audit line {index + 1}: hash does not match its content"]
        with pytest.raises(StoreCorruptError, match=f"audit line {index + 1}"):
            Store.open(copy, clock=b.Clock(), ids=b.ids())


def _verify_copy(root: Path) -> list[str]:
    transactions, lines = read_transactions(root), read_audit(root)
    return verify_chain(lines) + verify_coverage(transactions, lines)


def test_rehashing_an_edited_line_moves_the_failure_to_the_next_link(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    index = 5

    def alter(document: dict[str, Any]) -> None:
        document["actor"] = "someone else"
        document["hash"] = audit_line_hash(document)

    _rewrite_line(store.root / AUDIT_FILE, index, alter)
    assert store.verify() == [f"audit line {index + 2}: prev_hash does not match line {index + 1}"]


def test_editing_a_record_log_row_is_detected(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")

    def alter(document: dict[str, Any]) -> None:
        document["rows"][-1]["record"]["canonical_name"] = "Someone Else"

    lines = (store.root / RECORDS_FILE).read_text(encoding="utf-8").splitlines()
    target = next(i for i, line in enumerate(lines) if '"canonical_name":"Mara Voss"' in line)
    _rewrite_line(store.root / RECORDS_FILE, target, alter)
    problems = store.verify()
    assert any("covers no row" in problem for problem in problems)
    assert any("has 0 audit lines" in problem for problem in problems)


def test_a_torn_final_line_is_refused_with_its_location(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    path = store.root / RECORDS_FILE
    lines = path.read_bytes().count(b"\n")
    with path.open("ab") as handle:
        handle.write(b'{"tx": 99, "rows": [')
    with pytest.raises(StoreCorruptError, match=f"line {lines + 1} is torn"):
        Store.open(store.root, clock=b.Clock(), ids=b.ids())


def test_a_transaction_missing_its_audit_lines_is_refused(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    path = store.root / AUDIT_FILE
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(StoreCorruptError, match="has 0 audit lines"):
        Store.open(store.root, clock=b.Clock(), ids=b.ids())


# --- reload -------------------------------------------------------------------------------


def test_reloading_yields_a_deep_equal_and_hash_equal_state(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    reloaded = Store.open(store.root, clock=b.Clock(), ids=b.ids(seed=1))
    assert reloaded.snapshot() == store.snapshot()
    assert reloaded.snapshot().digest() == store.snapshot().digest()
    assert reloaded.audit_trail() == store.audit_trail()
    assert reloaded.model_version == store.model_version


def test_a_reloaded_store_keeps_writing_a_valid_chain(tmp_path: Path) -> None:
    store = _busy_store(tmp_path / "p")
    reloaded = Store.open(store.root, clock=b.Clock(), ids=b.ids(seed=2))
    console = reloaded.gate_console(b.isolation_check)
    assert console.decide(Gate.PROPOSAL, "CHR-004", GateOutcome.ACCEPT, actor=HUMAN).ok
    assert reloaded.verify() == []
    assert (
        Store.open(store.root, clock=b.Clock(), ids=b.ids(seed=3)).snapshot() == reloaded.snapshot()
    )


def test_create_refuses_an_existing_project(tmp_path: Path) -> None:
    b.new_store(tmp_path)
    with pytest.raises(FileExistsError):
        Store.create(tmp_path, clock=b.Clock(), ids=b.ids())


# --- bitemporal reads ---------------------------------------------------------------------


def test_history_and_as_of_follow_transaction_time(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    console.propose(b.character(), actor=HUMAN)
    proposed_at = store.tx
    console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.ACCEPT, actor=HUMAN)
    accepted_at = store.tx
    history = store.history("CHR-001")
    assert [(rev.tx.from_rev, rev.tx.to_rev) for rev in history] == [
        (proposed_at, accepted_at),
        (accepted_at, None),
    ]
    assert store.as_of("CHR-001", proposed_at).status is Status.PROPOSAL
    assert store.as_of("CHR-001", accepted_at).status is Status.ACCEPTED
    assert store.as_of("CHR-001", proposed_at - 1) is None
    assert store.changed_between(proposed_at - 1, proposed_at) == ("CHR-001",)
    assert store.changed_between(accepted_at, accepted_at + 5) == ()


def test_valid_at_uses_half_open_story_time_and_only_reconciled_records(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    _accept(console, b.fact("INF-006", valid_from=100, valid_to=200))
    console.propose(b.fact("INF-007", valid_from=0, valid_to=None), actor=HUMAN)
    assert [f.handle for f in store.valid_at(100)] == ["INF-006"]
    assert [f.handle for f in store.valid_at(199)] == ["INF-006"]
    assert store.valid_at(200) == ()
    assert store.valid_at(150, tx=1) == ()


# --- model versions -----------------------------------------------------------------------


def test_model_version_lifecycle(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    writer = store.engine_writer("engine:reconcile")
    assert _state(store) is ModelVersionState.OPEN
    assert store.model_version.label == "open-1"
    _canon(console, b.character())
    assert writer.complete_reconciliation(0).refusal is Refusal.WRONG_VERSION_STATE
    assert writer.begin_reconciliation().ok
    assert writer.complete_reconciliation(2).ok
    assert _state(store) is ModelVersionState.INCONSISTENT
    assert console.tag_release(actor=HUMAN).refusal is Refusal.WRONG_VERSION_STATE
    approved = console.approve_resolutions(actor=HUMAN, reason="RES-0011 applied")
    assert approved.ok
    assert approved.gate_record is not None
    assert approved.gate_record.gate is Gate.INTEGRATION
    assert _state(store) is ModelVersionState.OPEN
    writer.begin_reconciliation()
    consistent = writer.complete_reconciliation(0)
    version = store.model_version
    assert version.state is ModelVersionState.CONSISTENT
    assert version.label == f"canon@r1/truth@r{consistent.tx}"
    assert console.tag_release(actor=HUMAN).ok
    assert _state(store) is ModelVersionState.RELEASED
    assert store.model_version.label == version.label


def test_changing_reconciled_canon_opens_a_new_version_and_keeps_the_old_readable(
    tmp_path: Path,
) -> None:
    store, console = b.new_store(tmp_path)
    writer = store.engine_writer("engine:reconcile")
    _canon(console, b.character())
    writer.begin_reconciliation()
    writer.complete_reconciliation(0)
    released_label = store.model_version.label
    writer.propose(b.character("CHR-004", "Jonah Pell"))
    assert store.model_version.number == 1  # a proposal does not touch reconciled state
    result = console.decide(Gate.PROPOSAL, "CHR-004", GateOutcome.ACCEPT, actor=HUMAN)
    assert result.opened_version is not None
    assert (store.model_version.number, store.model_version.state) == (2, ModelVersionState.OPEN)
    assert result.gate_record is not None
    assert result.gate_record.model_version == released_label
    assert [v.number for v in store.versions()].count(1) == 3  # OPEN, RECONCILING, CONSISTENT


# --- findings and waivers (REQ-9.1.2, OQ-10) ------------------------------------------------


def test_a_blocking_finding_cannot_be_waived_and_stays_open(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    store.engine_writer("engine:validate").record_finding(b.finding(severity=Severity.BLOCKING))
    before = (_sizes(store), store.snapshot().digest())
    result = console.waive_finding(
        "FND-007-01-02", Gate.INTEGRATION, actor=HUMAN, reason="I like it"
    )
    assert result.refusal is Refusal.BLOCKING_NOT_WAIVABLE
    assert store.get("FND-007-01-02").status is FindingStatus.OPEN
    assert (_sizes(store), store.snapshot().digest()) == before


def test_a_major_finding_is_waived_through_an_override_gate_record(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    store.engine_writer("engine:validate").record_finding(b.finding(severity=Severity.MAJOR))
    assert (
        console.waive_finding("FND-007-01-02", Gate.INTEGRATION, actor=HUMAN, reason="").refusal
        is Refusal.REASON_REQUIRED
    )
    assert (
        console.waive_finding("FND-007-01-02", Gate.SHIP, actor=HUMAN, reason="x").refusal
        is Refusal.OUTCOME_NOT_AT_GATE
    )
    result = console.waive_finding(
        "FND-007-01-02", Gate.INTEGRATION, actor=HUMAN, reason="intended echo"
    )
    assert result.ok
    assert result.record.status is FindingStatus.WAIVED_BY_OVERRIDE
    assert result.gate_record is not None
    assert (result.gate_record.override, result.gate_record.reason) == (True, "intended echo")
    again = console.waive_finding("FND-007-01-02", Gate.INTEGRATION, actor=HUMAN, reason="x")
    assert again.refusal is Refusal.FINDING_NOT_OPEN


def test_blocking_findings_close_only_as_resolved_or_detector_error(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    writer = store.engine_writer("engine:validate")
    writer.record_finding(b.finding("FND-007-01-01", Severity.BLOCKING))
    writer.record_finding(b.finding("FND-007-01-02", Severity.BLOCKING))
    assert writer.mark_finding_resolved(
        "FND-007-01-01", reason="DRF-007-02 removed the affiliation"
    ).ok
    assert console.mark_detector_error(
        "FND-007-01-02", actor=HUMAN, reason="the probe misread S5"
    ).ok
    assert store.get("FND-007-01-01").status is FindingStatus.RESOLVED
    assert store.get("FND-007-01-02").status is FindingStatus.DETECTOR_ERROR
    decide = console.decide(Gate.INTEGRATION, "FND-007-01-01", GateOutcome.ACCEPT, actor=HUMAN)
    assert decide.refusal is Refusal.NO_TRANSITION


# --- the engine write path (plan A-08, D-014) ------------------------------------------------


def test_engine_writer_refuses_any_status_but_proposal_at_runtime(tmp_path: Path) -> None:
    store, _ = b.new_store(tmp_path)
    writer = store.engine_writer("engine:extract")
    as_accepted = writer.propose(b.character(), Status.ACCEPTED)  # type: ignore[arg-type]
    assert as_accepted.refusal is Refusal.NOT_PROPOSAL
    canon_record = replace(b.character("CHR-002", "Hale"), status=Status.CANON)
    assert writer.propose(canon_record).refusal is Refusal.NOT_PROPOSAL
    published = replace(b.character("CHR-003", "Edmund"), status=Status.CANON, tier=Tier.PUBLISHED)
    assert writer.propose(published).refusal is Refusal.NOT_PROPOSAL
    assert not hasattr(writer, "decide")
    assert list(store.records(status=Status.CANON)) == []


def test_engine_writer_refuses_to_overwrite_a_gated_record(tmp_path: Path) -> None:
    store, console = b.new_store(tmp_path)
    accepted = _accept(console, b.character())
    writer = store.engine_writer("engine:bridge")
    result = writer.propose(
        replace(accepted, rev=accepted.rev + 1, status=Status.PROPOSAL, gate=None)
    )
    assert result.refusal is Refusal.DUPLICATE_RECORD
    assert store.get("CHR-001").status is Status.ACCEPTED


# --- artifact store -----------------------------------------------------------------------


def test_artifact_store_round_trip_and_tamper_detection(tmp_path: Path) -> None:
    artifacts = ArtifactStore(tmp_path)
    packet = {"packet_handle": "PKT-007-r3", "public": {"x": [1, 2]}}
    ref = artifacts.put(packet)
    assert artifacts.put({"public": {"x": [1, 2]}, "packet_handle": "PKT-007-r3"}) == ref
    assert ref in artifacts
    assert artifacts.get(ref) == packet
    path = tmp_path / "artifacts" / "sha256" / f"{ref.removeprefix('sha256:')}.json"
    path.write_bytes(path.read_bytes().replace(b"PKT-007-r3", b"PKT-007-r4"))
    with pytest.raises(ArtifactCorruptError):
        artifacts.get(ref)
    with pytest.raises(ValueError, match="not a sha256"):
        artifacts.get("md5:abc")


def test_every_log_line_is_fsynced_before_the_write_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, console = b.new_store(tmp_path)
    calls: list[int] = []
    real_fsync = os.fsync

    def counting_fsync(descriptor: int) -> None:
        calls.append(descriptor)
        real_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", counting_fsync)
    records_before = (store.root / RECORDS_FILE).read_bytes().count(b"\n")
    audit_before = (store.root / AUDIT_FILE).read_bytes().count(b"\n")
    console.propose(b.character(), actor=HUMAN)
    console.decide(Gate.PROPOSAL, "CHR-001", GateOutcome.ACCEPT, actor=HUMAN)
    written = (store.root / RECORDS_FILE).read_bytes().count(b"\n") - records_before
    written += (store.root / AUDIT_FILE).read_bytes().count(b"\n") - audit_before
    assert written == 5  # 2 transaction lines, 3 audit lines
    assert len(calls) == written
