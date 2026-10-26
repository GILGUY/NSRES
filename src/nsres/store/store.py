"""The record store: projection, gate console, engine writer (DECISIONS D-012 to D-014).

Every write is one transaction: rows appended to the record log, then one audit line per row,
then the same rows applied to the in-memory projection through ``_apply``, the function that
also replays the log on ``Store.open``. Writing and reloading therefore share one code path,
which is what makes a reloaded store equal to the one that wrote it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

from nsres.domain.canonical import content_hash
from nsres.domain.records import (
    RECORD_TYPES,
    AuditRecord,
    BaseRecord,
    Fact,
    Finding,
    GateRecord,
    ModelVersion,
    RecordCore,
    Relation,
    TxRange,
    from_json,
    to_json,
)
from nsres.domain.uuid7 import Uuid7Generator
from nsres.domain.vocab import (
    GATE_OUTCOMES,
    AuditKind,
    FindingStatus,
    Gate,
    GateOutcome,
    ModelVersionState,
    Severity,
    Status,
)
from nsres.store.lifecycle import (
    IsolationCheck,
    Plan,
    Refusal,
    Refused,
    Rule,
    plan_decision,
)
from nsres.store.log import (
    AUDIT_FILE,
    RECORDS_FILE,
    Row,
    StoreCorruptError,
    Transaction,
    append_line,
    audit_line_hash,
    read_audit,
    read_transactions,
    verify_chain,
    verify_coverage,
)

Clock = Callable[[], str]
"""Returns the current UTC instant as ``YYYY-MM-DDTHH:MM:SSZ`` (injected, plan A-04)."""

_CLASSES: dict[str, type[Any]] = {cls.__name__: cls for cls in RECORD_TYPES}
_LIVE = (Status.PROPOSAL, Status.ACCEPTED, Status.CANON)
_FIXED_VERSION_STATES = (ModelVersionState.CONSISTENT, ModelVersionState.RELEASED)
NEW = "(new)"


@dataclass(frozen=True)
class GateResult:
    """The outcome of one write request. ``refusal`` is None when the write happened."""

    refusal: Refusal | None
    detail: str
    tx: int | None = None
    record: Any = None
    gate_record: GateRecord | None = None
    opened_version: ModelVersion | None = None

    @property
    def ok(self) -> bool:
        return self.refusal is None


def _refused(reason: Refusal, detail: str) -> GateResult:
    return GateResult(refusal=reason, detail=detail)


@dataclass(frozen=True)
class _Audit:
    kind: AuditKind
    subject: str
    trigger: str
    actor: str
    from_state: str | None = None
    to_state: str | None = None


@dataclass(frozen=True)
class Snapshot:
    """The whole in-memory state, for equality checks (WP-020 reload criterion)."""

    tx: int
    revisions: Mapping[str, tuple[Any, ...]]
    gates: tuple[GateRecord, ...]
    versions: tuple[ModelVersion, ...]
    accepted_by: Mapping[str, Gate]
    canon_rev: int
    audit_head: str | None

    def digest(self) -> str:
        return content_hash(
            {
                "tx": self.tx,
                "revisions": {
                    handle: [to_json(item) for item in items]
                    for handle, items in self.revisions.items()
                },
                "gates": [to_json(gate) for gate in self.gates],
                "versions": [to_json(version) for version in self.versions],
                "accepted_by": {handle: gate.value for handle, gate in self.accepted_by.items()},
                "canon_rev": self.canon_rev,
                "audit_head": self.audit_head,
            }
        )


def _state_label(record: Any) -> str:
    tier = getattr(record, "tier", None)
    return f"{record.status} tier {tier}" if tier is not None else str(record.status)


def _mentions(document: Any, pattern: re.Pattern[str]) -> bool:
    if isinstance(document, str):
        return pattern.search(document) is not None
    if isinstance(document, Mapping):
        return any(
            _mentions(key, pattern) or _mentions(value, pattern) for key, value in document.items()
        )
    if isinstance(document, list):
        return any(_mentions(item, pattern) for item in document)
    return False


class Store:
    """An NSRES project's record store. Use ``Store.create`` or ``Store.open``."""

    def __init__(self, root: Path, *, clock: Clock, ids: Uuid7Generator) -> None:
        self.root = root
        self._clock = clock
        self._ids = ids
        self._revisions: dict[str, list[Any]] = {}
        self._uuids: dict[str, str] = {}
        self._gates: list[GateRecord] = []
        self._gates_by_uuid: dict[str, GateRecord] = {}
        self._versions: list[ModelVersion] = []
        self._version_tx: list[int] = []
        self._accepted_by: dict[str, Gate] = {}
        self._canon_rev = 0
        self._tx = 0
        self._audit: list[dict[str, Any]] = []

    # --- lifecycle of the store itself ------------------------------------------------------

    @classmethod
    def create(cls, root: Path, *, clock: Clock, ids: Uuid7Generator) -> Store:
        """Create an empty project and open model version 1."""
        for relative in (RECORDS_FILE, AUDIT_FILE):
            path = root / relative
            if path.exists():
                raise FileExistsError(f"{path} already exists")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        store = cls(root, clock=clock, ids=ids)
        version = ModelVersion(
            uuid=ids.new_str(), number=1, state=ModelVersionState.OPEN, opened_tx=1
        )
        store._commit(
            [version],
            [
                _Audit(
                    AuditKind.TRANSITION, "model-version:1", "Store created", "store", NEW, "OPEN"
                )
            ],
        )
        return store

    @classmethod
    def open(cls, root: Path, *, clock: Clock, ids: Uuid7Generator) -> Store:
        """Load and verify a project. Raises ``StoreCorruptError`` naming the first problem."""
        transactions = read_transactions(root)
        lines = read_audit(root)
        problems = verify_chain(lines) + verify_coverage(transactions, lines)
        if problems:
            raise StoreCorruptError("; ".join(problems))
        store = cls(root, clock=clock, ids=ids)
        for line in lines:
            from_json(AuditRecord, line)  # every line must be a well-formed audit record
        store._audit = list(lines)
        for transaction in transactions:
            store._apply(transaction)
        return store

    def verify(self) -> list[str]:
        """Re-read both logs from disk and return every problem found; empty when clean."""
        try:
            transactions = read_transactions(self.root)
            lines = read_audit(self.root)
        except StoreCorruptError as error:
            return [str(error)]
        return verify_chain(lines) + verify_coverage(transactions, lines)

    # --- reads ------------------------------------------------------------------------------

    @property
    def tx(self) -> int:
        return self._tx

    def get(self, handle: str) -> Any:
        """The current revision of a record or finding, or None."""
        revisions = self._revisions.get(handle)
        return revisions[-1] if revisions else None

    def history(self, handle: str) -> tuple[Any, ...]:
        """Every revision, oldest first, with ``tx.to`` filled from the next revision."""
        revisions = self._revisions.get(handle, [])
        filled = []
        for index, revision in enumerate(revisions):
            following = revisions[index + 1].tx.from_rev if index + 1 < len(revisions) else None
            filled.append(
                replace(revision, tx=TxRange(from_rev=revision.tx.from_rev, to_rev=following))
            )
        return tuple(filled)

    def as_of(self, handle: str, tx: int) -> Any:
        """The revision that was current at transaction ``tx``, or None."""
        for revision in reversed(self.history(handle)):
            if revision.tx.from_rev <= tx and (
                revision.tx.to_rev is None or tx < revision.tx.to_rev
            ):
                return revision
        return None

    def changed_between(self, after_tx: int, upto_tx: int) -> tuple[str, ...]:
        """Handles with a revision in ``(after_tx, upto_tx]`` (spec §10.5, second query)."""
        return tuple(
            sorted(
                handle
                for handle, revisions in self._revisions.items()
                if any(after_tx < revision.tx.from_rev <= upto_tx for revision in revisions)
            )
        )

    def records(
        self, *, status: Status | None = None, kind: type[Any] | None = None
    ) -> Iterator[Any]:
        for handle in sorted(self._revisions):
            current = self._revisions[handle][-1]
            if kind is not None and not isinstance(current, kind):
                continue
            if status is not None and getattr(current, "status", None) is not status:
                continue
            yield current

    def valid_at(self, story_minute: int, *, tx: int | None = None) -> tuple[Any, ...]:
        """ACCEPTED or CANON facts and relations whose story-time validity contains the
        minute, as of transaction ``tx`` (spec §10.5, first query; half-open intervals)."""
        at = self._tx if tx is None else tx
        found = []
        for handle in sorted(self._revisions):
            revision = self.as_of(handle, at)
            if not isinstance(revision, Fact | Relation) or revision.status not in (
                Status.ACCEPTED,
                Status.CANON,
            ):
                continue
            start, end = revision.valid.from_min, revision.valid.to_min
            if (start is None or start <= story_minute) and (end is None or story_minute < end):
                found.append(revision)
        return tuple(found)

    def gate_records(self, handle: str | None = None) -> tuple[GateRecord, ...]:
        return tuple(gate for gate in self._gates if handle is None or gate.subject == handle)

    def audit_trail(self) -> tuple[AuditRecord, ...]:
        return tuple(from_json(AuditRecord, line) for line in self._audit)

    @property
    def model_version(self) -> ModelVersion:
        return self._versions[-1]

    def versions(self) -> tuple[ModelVersion, ...]:
        return tuple(self._versions)

    def accepted_by(self, handle: str) -> Gate | None:
        return self._accepted_by.get(handle)

    def dependents(self, handle: str) -> tuple[str, ...]:
        """Live records (PROPOSAL, ACCEPTED, CANON) other than ``handle`` that mention it."""
        pattern = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(handle)}(?![A-Za-z0-9])")
        found = []
        for other in self.records():
            if other.handle == handle or getattr(other, "status", None) not in _LIVE:
                continue
            if _mentions(to_json(other), pattern):
                found.append(other.handle)
        return tuple(found)

    def snapshot(self) -> Snapshot:
        return Snapshot(
            tx=self._tx,
            revisions={handle: tuple(items) for handle, items in sorted(self._revisions.items())},
            gates=tuple(self._gates),
            versions=tuple(self._versions),
            accepted_by=dict(sorted(self._accepted_by.items())),
            canon_rev=self._canon_rev,
            audit_head=self._audit[-1]["hash"] if self._audit else None,
        )

    # --- write paths ------------------------------------------------------------------------

    def engine_writer(self, actor: str) -> EngineWriter:
        return EngineWriter(self, actor)

    def gate_console(self, isolation_check: IsolationCheck) -> GateConsole:
        return GateConsole(self, isolation_check)

    def _new_uuid(self) -> str:
        return self._ids.new_str()

    def _commit(self, objects: Sequence[Any], audits: Sequence[_Audit]) -> int:
        """Write one transaction: the rows, then one audit line per row; then apply it."""
        assert len(objects) == len(audits), "one audit line per row"
        tx = self._tx + 1
        rows = tuple(Row(type=type(item).__name__, record=to_json(item)) for item in objects)
        transaction = Transaction(tx=tx, rows=rows)
        time = self._clock()
        label = self.model_version.label if self._versions else "open-1"
        lines = []
        previous = self._audit[-1]["hash"] if self._audit else None
        for offset, (row, item, audit) in enumerate(zip(rows, objects, audits, strict=True)):
            line: dict[str, Any] = {
                "seq": len(self._audit) + offset,
                "uuid": self._new_uuid(),
                "kind": audit.kind.value,
                "subject": audit.subject,
                "trigger": audit.trigger,
                "actor": audit.actor,
                "model_version": label,
                "timestamp": time,
                "prev_hash": previous,
                "tx": tx,
                "ref": item.uuid,
                "ref_hash": row.hash,
            }
            if audit.from_state is not None:
                line["from_state"] = audit.from_state
            if audit.to_state is not None:
                line["to_state"] = audit.to_state
            line["hash"] = audit_line_hash(line)
            from_json(AuditRecord, line)  # refuse to write a malformed audit line
            previous = line["hash"]
            lines.append(line)
        append_line(self.root / RECORDS_FILE, transaction.to_json())
        for line in lines:
            append_line(self.root / AUDIT_FILE, line)
        self._audit.extend(lines)
        self._apply(transaction)
        return tx

    def _apply(self, transaction: Transaction) -> None:
        """Apply one transaction to the projection (shared by writes and replay)."""
        touched_canon = False
        for row in transaction.rows:
            cls = _CLASSES.get(row.type)
            if cls is None:
                raise StoreCorruptError(f"tx {transaction.tx}: unknown row type {row.type}")
            item = from_json(cls, row.record)
            if isinstance(item, GateRecord):
                self._gates.append(item)
                self._gates_by_uuid[item.uuid] = item
            elif isinstance(item, ModelVersion):
                self._versions.append(item)
                self._version_tx.append(transaction.tx)
            elif isinstance(item, RecordCore):
                previous = self.get(item.handle)
                if previous is None:
                    if item.uuid in self._uuids:
                        raise StoreCorruptError(f"tx {transaction.tx}: uuid {item.uuid} reused")
                    self._uuids[item.uuid] = item.handle
                    self._revisions[item.handle] = []
                elif previous.uuid != item.uuid or item.rev != previous.rev + 1:
                    raise StoreCorruptError(
                        f"tx {transaction.tx}: {item.handle} revision out of order"
                    )
                self._revisions[item.handle].append(item)
                if isinstance(item, BaseRecord):
                    before = getattr(previous, "status", None)
                    if Status.CANON in (before, item.status):
                        touched_canon = True
                    if (
                        item.status is Status.ACCEPTED
                        and before is not Status.ACCEPTED
                        and item.gate
                    ):
                        self._accepted_by[item.handle] = self._gates_by_uuid[item.gate].gate
            else:  # pragma: no cover - every RECORD_TYPES entry is one of the above
                raise StoreCorruptError(f"tx {transaction.tx}: cannot store {row.type}")
        if touched_canon:
            self._canon_rev += 1
        self._tx = transaction.tx

    # --- shared helpers for the two writers -------------------------------------------------

    def _propose(self, record: Any, actor: str) -> GateResult:
        if not actor:
            return _refused(Refusal.ACTOR_REQUIRED, "a proposal names its actor")
        if not isinstance(record, BaseRecord):
            return _refused(Refusal.NOT_PROPOSAL, f"{type(record).__name__} is not a gated record")
        if (
            record.status is not Status.PROPOSAL
            or record.tier is not None
            or record.gate is not None
        ):
            return _refused(
                Refusal.NOT_PROPOSAL,
                f"{record.handle} arrives as {record.status}; every new record starts as PROPOSAL",
            )
        current = self.get(record.handle)
        tx = self._tx + 1
        stamped = replace(record, tx=TxRange(from_rev=tx, to_rev=None))
        if current is None:
            if record.uuid in self._uuids:
                return _refused(
                    Refusal.DUPLICATE_RECORD,
                    f"uuid {record.uuid} is already {self._uuids[record.uuid]}",
                )
            if record.rev != 1:
                return _refused(
                    Refusal.REVISION_MISMATCH, f"a new record starts at rev 1, not {record.rev}"
                )
            audit = _Audit(
                AuditKind.TRANSITION,
                record.handle,
                "Created by author, engine, or AI",
                actor,
                NEW,
                "PROPOSAL",
            )
        else:
            if current.status is not Status.PROPOSAL:
                return _refused(
                    Refusal.DUPLICATE_RECORD,
                    f"{record.handle} is {current.status}; change it through its gate,"
                    " not a new proposal",
                )
            if (
                type(current) is not type(record)
                or current.uuid != record.uuid
                or record.rev != current.rev + 1
            ):
                return _refused(
                    Refusal.REVISION_MISMATCH,
                    f"a revised proposal keeps class and uuid and takes rev {current.rev + 1}",
                )
            audit = _Audit(
                AuditKind.TRANSITION,
                record.handle,
                "Revised proposal",
                actor,
                "PROPOSAL",
                "PROPOSAL",
            )
        done = self._commit([stamped], [audit])
        return GateResult(refusal=None, detail="proposed", tx=done, record=self.get(record.handle))

    def _finding_change(
        self, handle: str, to: FindingStatus, actor: str, trigger: str
    ) -> GateResult:
        current = self.get(handle)
        if not isinstance(current, Finding):
            return _refused(Refusal.NOT_A_FINDING, f"{handle} is not a finding")
        if current.status is not FindingStatus.OPEN:
            return _refused(Refusal.FINDING_NOT_OPEN, f"{handle} is {current.status}, not OPEN")
        tx = self._tx + 1
        revised = replace(
            current, rev=current.rev + 1, status=to, tx=TxRange(from_rev=tx, to_rev=None)
        )
        audit = _Audit(AuditKind.TRANSITION, handle, trigger, actor, current.status.value, to.value)
        done = self._commit([revised], [audit])
        return GateResult(refusal=None, detail=str(to), tx=done, record=self.get(handle))

    def _version_change(
        self,
        to: ModelVersionState,
        *,
        allowed_from: tuple[ModelVersionState, ...],
        actor: str,
        trigger: str,
        gate: GateRecord | None = None,
    ) -> GateResult:
        current = self.model_version
        if current.state not in allowed_from:
            return _refused(
                Refusal.WRONG_VERSION_STATE,
                f"model version {current.number} is {current.state}; {trigger} needs "
                + " or ".join(state.value for state in allowed_from),
            )
        fixed = to in _FIXED_VERSION_STATES
        tx = self._tx + 1
        canon = current.canon_rev if current.canon_rev is not None else self._canon_rev
        truth = current.truth_rev if current.truth_rev is not None else tx
        updated = replace(
            current,
            state=to,
            canon_rev=canon if fixed else None,
            truth_rev=truth if fixed else None,
        )
        subject = f"model-version:{current.number}"
        objects: list[Any] = []
        audits: list[_Audit] = []
        if gate is not None:
            objects.append(gate)
            audits.append(_Audit(AuditKind.GATE, subject, trigger, actor))
        objects.append(updated)
        audits.append(
            _Audit(AuditKind.TRANSITION, subject, trigger, actor, current.state.value, to.value)
        )
        done = self._commit(objects, audits)
        return GateResult(
            refusal=None, detail=str(to), tx=done, gate_record=gate, opened_version=None
        )


class EngineWriter:
    """The only write path engines get (D-014). Nothing here can set ACCEPTED, CANON, or a tier."""

    def __init__(self, store: Store, actor: str) -> None:
        self._store = store
        self.actor = actor

    def propose(
        self, record: Any, status: Literal[Status.PROPOSAL] = Status.PROPOSAL
    ) -> GateResult:
        """Add a new PROPOSAL record, or the next revision of one (WCS REVISED_PROPOSAL)."""
        requested: object = status  # checked at runtime too, for callers mypy does not see
        if requested is not Status.PROPOSAL:
            return _refused(Refusal.NOT_PROPOSAL, f"engines may only propose, not set {requested}")
        return self._store._propose(record, self.actor)

    def record_finding(self, finding: Finding) -> GateResult:
        if not self.actor:
            return _refused(Refusal.ACTOR_REQUIRED, "a finding names its actor")
        store = self._store
        if (
            not isinstance(finding, Finding)
            or finding.status is not FindingStatus.OPEN
            or finding.rev != 1
        ):
            return _refused(
                Refusal.NOT_A_FINDING, "a new finding is a Finding at rev 1 with status OPEN"
            )
        if store.get(finding.handle) is not None or finding.uuid in store._uuids:
            return _refused(Refusal.DUPLICATE_RECORD, f"{finding.handle} already exists")
        tx = store.tx + 1
        stamped = replace(finding, tx=TxRange(from_rev=tx, to_rev=None))
        audit = _Audit(
            AuditKind.TRANSITION, finding.handle, "Finding raised", self.actor, NEW, "OPEN"
        )
        done = store._commit([stamped], [audit])
        return GateResult(
            refusal=None, detail="recorded", tx=done, record=store.get(finding.handle)
        )

    def mark_finding_resolved(self, handle: str, reason: str) -> GateResult:
        """OPEN → RESOLVED, because the finding's inputs changed (REQ-9.1.2)."""
        if not reason:
            return _refused(Refusal.REASON_REQUIRED, "say which input changed")
        return self._store._finding_change(
            handle, FindingStatus.RESOLVED, self.actor, f"Inputs changed: {reason}"
        )

    def begin_reconciliation(self) -> GateResult:
        return self._store._version_change(
            ModelVersionState.RECONCILING,
            allowed_from=(ModelVersionState.OPEN,),
            actor=self.actor,
            trigger="Reconciliation starts",
        )

    def complete_reconciliation(self, blocking_contradictions: int) -> GateResult:
        consistent = blocking_contradictions == 0
        return self._store._version_change(
            ModelVersionState.CONSISTENT if consistent else ModelVersionState.INCONSISTENT,
            allowed_from=(ModelVersionState.RECONCILING,),
            actor=self.actor,
            trigger=(
                "Run completes with zero BLOCKING contradictions"
                if consistent
                else f"Run completes with {blocking_contradictions} BLOCKING contradictions"
                " remaining"
            ),
        )


class GateConsole:
    """The typed-gate API (C15). The only path that changes a record status (plan A-08)."""

    def __init__(self, store: Store, isolation_check: IsolationCheck) -> None:
        self._store = store
        self._isolation_check = isolation_check

    def propose(self, record: Any, *, actor: str) -> GateResult:
        """An author's proposal: the same rules as ``EngineWriter.propose``."""
        return self._store._propose(record, actor)

    def decide(
        self,
        gate: Gate,
        handle: str,
        outcome: GateOutcome,
        *,
        actor: str,
        reason: str | None = None,
        revision: BaseRecord | None = None,
        override: bool = False,
        confirmation: str | None = None,
        retcon: Sequence[str] = (),
        successor: str | None = None,
    ) -> GateResult:
        store = self._store
        if not actor:
            return _refused(Refusal.ACTOR_REQUIRED, "a gate decision names its actor")
        if override and not reason:
            return _refused(Refusal.REASON_REQUIRED, "an override carries a reason (REQ-11.5.1)")
        current = store.get(handle)
        if current is None:
            return _refused(Refusal.UNKNOWN_RECORD, f"no record {handle}")
        if not isinstance(current, BaseRecord):
            return _refused(Refusal.NO_TRANSITION, f"{handle} is a finding; use waive_finding")
        planned = plan_decision(
            current,
            gate,
            outcome,
            accepted_by=store.accepted_by(handle),
            revision=revision,
            retcon=retcon,
        )
        if isinstance(planned, Refused):
            return _refused(planned.reason, planned.detail)
        problem = self._check(current, planned, revision, successor)
        if problem is not None:
            return problem

        tx = store.tx + 1
        version = store.model_version
        gate_record = GateRecord(
            uuid=store._new_uuid(),
            gate=gate,
            outcome=outcome,
            subject=handle,
            subject_uuid=current.uuid,
            subject_rev=current.rev,
            actor=actor,
            time=store._clock(),
            model_version=version.label,
            reason=reason,
            override=override,
            confirmation=confirmation,
            retcon=tuple(retcon),
            successor=successor,
        )
        objects: list[Any] = [gate_record]
        audits = [_Audit(AuditKind.GATE, handle, f"{gate} gate {outcome}", actor)]
        opened: ModelVersion | None = None
        rule = planned.rule
        if rule is not None:
            base = revision if rule.edit and revision is not None else current
            updated = replace(
                base,
                rev=current.rev + 1,
                status=planned.status,
                tier=planned.tier,
                tx=TxRange(from_rev=tx, to_rev=None),
                gate=gate_record.uuid,
            )
            objects.append(updated)
            audits.append(
                _Audit(
                    AuditKind.TRANSITION,
                    handle,
                    rule.trigger,
                    actor,
                    _state_label(current),
                    _state_label(updated),
                )
            )
            changes_reconciled = Status.ACCEPTED in (
                current.status,
                updated.status,
            ) or Status.CANON in (
                current.status,
                updated.status,
            )
            if changes_reconciled and version.state in _FIXED_VERSION_STATES:
                opened = ModelVersion(
                    uuid=store._new_uuid(),
                    number=version.number + 1,
                    state=ModelVersionState.OPEN,
                    opened_tx=tx,
                )
                objects.append(opened)
                audits.append(
                    _Audit(
                        AuditKind.TRANSITION,
                        f"model-version:{opened.number}",
                        "A gate decision changes an ACCEPTED or CANON record",
                        actor,
                        NEW,
                        "OPEN",
                    )
                )
        done = store._commit(objects, audits)
        return GateResult(
            refusal=None,
            detail=rule.trigger if rule is not None else f"{outcome}: no change",
            tx=done,
            record=store.get(handle),
            gate_record=gate_record,
            opened_version=opened,
        )

    def _check(
        self, current: BaseRecord, planned: Plan, revision: BaseRecord | None, successor: str | None
    ) -> GateResult | None:
        rule: Rule | None = planned.rule
        if rule is None:
            return None
        if rule.edit:
            assert revision is not None  # guaranteed by plan_decision
            same = (
                type(revision) is type(current)
                and revision.uuid == current.uuid
                and revision.handle == current.handle
                and revision.status is current.status
                and revision.tier is current.tier
                and revision.rev == current.rev + 1
            )
            if not same:
                return _refused(
                    Refusal.REVISION_MISMATCH,
                    "an edit keeps class, uuid, handle, status, and tier,"
                    f" and takes rev {current.rev + 1}",
                )
        if planned.status in (Status.ACCEPTED, Status.CANON):
            subject = revision if rule.edit and revision is not None else current
            failures = list(self._isolation_check(subject))
            if failures:
                return _refused(Refusal.GUARD_FAILED, "; ".join(failures))
        if planned.status is Status.DEPRECATED:
            remaining = self._store.dependents(current.handle)
            if remaining:
                return _refused(
                    Refusal.DEPENDENTS_REMAIN,
                    f"re-point these before retiring {current.handle}: {', '.join(remaining)}",
                )
            if successor is not None and self._store.get(successor) is None:
                return _refused(Refusal.UNKNOWN_RECORD, f"successor {successor} does not exist")
        return None

    def waive_finding(self, handle: str, gate: Gate, *, actor: str, reason: str) -> GateResult:
        """Set a MAJOR, MINOR, or INFO finding to WAIVED_BY_OVERRIDE (REQ-9.1.2, OQ-10)."""
        store = self._store
        if not actor:
            return _refused(Refusal.ACTOR_REQUIRED, "a waiver names its actor")
        if not reason:
            return _refused(Refusal.REASON_REQUIRED, "a waiver names its reason (REQ-9.1.2)")
        current = store.get(handle)
        if not isinstance(current, Finding):
            return _refused(Refusal.NOT_A_FINDING, f"{handle} is not a finding")
        if current.status is not FindingStatus.OPEN:
            return _refused(Refusal.FINDING_NOT_OPEN, f"{handle} is {current.status}, not OPEN")
        if current.severity is Severity.BLOCKING:
            return _refused(
                Refusal.BLOCKING_NOT_WAIVABLE,
                f"{handle} is BLOCKING; it closes only as RESOLVED or DETECTOR_ERROR (REQ-9.1.2)",
            )
        if GateOutcome.ACCEPT not in GATE_OUTCOMES[gate]:
            return _refused(
                Refusal.OUTCOME_NOT_AT_GATE, f"the {gate} gate cannot accept with an override"
            )
        tx = store.tx + 1
        gate_record = GateRecord(
            uuid=store._new_uuid(),
            gate=gate,
            outcome=GateOutcome.ACCEPT,
            subject=handle,
            subject_uuid=current.uuid,
            subject_rev=current.rev,
            actor=actor,
            time=store._clock(),
            model_version=store.model_version.label,
            reason=reason,
            override=True,
        )
        waived = replace(
            current,
            rev=current.rev + 1,
            status=FindingStatus.WAIVED_BY_OVERRIDE,
            tx=TxRange(from_rev=tx, to_rev=None),
            gate=gate_record.uuid,
        )
        done = store._commit(
            [gate_record, waived],
            [
                _Audit(AuditKind.GATE, handle, f"{gate} gate waiver", actor),
                _Audit(
                    AuditKind.TRANSITION,
                    handle,
                    f"Waived: {reason}",
                    actor,
                    "OPEN",
                    "WAIVED_BY_OVERRIDE",
                ),
            ],
        )
        return GateResult(
            refusal=None,
            detail="waived",
            tx=done,
            record=store.get(handle),
            gate_record=gate_record,
        )

    def mark_detector_error(self, handle: str, *, actor: str, reason: str) -> GateResult:
        """OPEN → DETECTOR_ERROR: a human judges that the detector was wrong (REQ-9.1.2)."""
        if not actor:
            return _refused(Refusal.ACTOR_REQUIRED, "name the actor")
        if not reason:
            return _refused(Refusal.REASON_REQUIRED, "say why the detector was wrong")
        return self._store._finding_change(
            handle, FindingStatus.DETECTOR_ERROR, actor, f"Detector error: {reason}"
        )

    def approve_resolutions(self, *, actor: str, reason: str | None = None) -> GateResult:
        """INCONSISTENT → OPEN at the INTEGRATION gate (§5.4 version lifecycle)."""
        return self._version_gate(
            ModelVersionState.OPEN,
            ModelVersionState.INCONSISTENT,
            actor,
            reason,
            "Resolutions approved",
        )

    def tag_release(self, *, actor: str, reason: str | None = None) -> GateResult:
        """CONSISTENT → RELEASED at the INTEGRATION gate (§5.4 version lifecycle)."""
        return self._version_gate(
            ModelVersionState.RELEASED, ModelVersionState.CONSISTENT, actor, reason, "Tag requested"
        )

    def _version_gate(
        self,
        to: ModelVersionState,
        required: ModelVersionState,
        actor: str,
        reason: str | None,
        trigger: str,
    ) -> GateResult:
        store = self._store
        if not actor:
            return _refused(Refusal.ACTOR_REQUIRED, "a gate decision names its actor")
        current = store.model_version
        if current.state is not required:
            return _refused(
                Refusal.WRONG_VERSION_STATE,
                f"model version {current.number} is {current.state}; {trigger} needs {required}",
            )
        gate_record = GateRecord(
            uuid=store._new_uuid(),
            gate=Gate.INTEGRATION,
            outcome=GateOutcome.ACCEPT,
            subject=f"model-version:{current.number}",
            subject_uuid=current.uuid,
            subject_rev=current.number,
            actor=actor,
            time=store._clock(),
            model_version=current.label,
            reason=reason,
        )
        return store._version_change(
            to, allowed_from=(required,), actor=actor, trigger=trigger, gate=gate_record
        )
