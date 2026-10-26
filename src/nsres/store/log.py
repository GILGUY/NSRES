"""The two append-only logs and their verification (DECISIONS D-012).

``records.jsonl`` holds one line per transaction; ``audit.jsonl`` holds one hash-chained line
per row. Lines are canonical JSON and are fsynced before a write returns. Reading verifies
everything it can: line syntax, consecutive transaction numbers, the audit chain, and that
every row has exactly one audit line whose ``ref_hash`` matches it.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nsres.domain.canonical import canonical_bytes, content_hash

RECORDS_FILE = Path("log") / "records.jsonl"
AUDIT_FILE = Path("log") / "audit.jsonl"


class StoreCorruptError(Exception):
    """The on-disk logs fail verification. The message names the file and line."""


@dataclass(frozen=True)
class Row:
    """One row of a transaction: a record revision, a gate record, or a model version."""

    type: str
    record: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {"type": self.type, "record": self.record}

    @property
    def hash(self) -> str:
        return content_hash(self.to_json())


@dataclass(frozen=True)
class Transaction:
    tx: int
    rows: tuple[Row, ...]

    def to_json(self) -> dict[str, Any]:
        return {"tx": self.tx, "rows": [row.to_json() for row in self.rows]}


def audit_line_hash(line: Mapping[str, Any]) -> str:
    """The chain hash of an audit line: its content hash without the ``hash`` field."""
    return content_hash({key: value for key, value in line.items() if key != "hash"})


def append_line(path: Path, document: Mapping[str, Any]) -> None:
    """Append one canonical JSON line and fsync it."""
    data = canonical_bytes(document) + b"\n"
    with path.open("ab") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _read_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise StoreCorruptError(f"{path}: missing")
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        count = raw.count(b"\n") + 1
        raise StoreCorruptError(f"{path}: line {count} is torn (no final newline)")
    documents: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), start=1):
        try:
            document = json.loads(line)
        except json.JSONDecodeError as error:
            raise StoreCorruptError(f"{path}: line {number} is not JSON ({error.msg})") from error
        if not isinstance(document, dict):
            raise StoreCorruptError(f"{path}: line {number} is not an object")
        documents.append(document)
    return documents


def read_transactions(root: Path) -> list[Transaction]:
    path = root / RECORDS_FILE
    transactions: list[Transaction] = []
    for number, document in enumerate(_read_lines(path), start=1):
        if set(document) != {"tx", "rows"} or not isinstance(document["rows"], list):
            raise StoreCorruptError(f"{path}: line {number} is not a transaction")
        if document["tx"] != number:
            raise StoreCorruptError(
                f"{path}: line {number} holds tx {document['tx']}, expected {number}"
            )
        rows = []
        for item in document["rows"]:
            if not isinstance(item, dict) or set(item) != {"type", "record"}:
                raise StoreCorruptError(f"{path}: line {number} has a malformed row")
            rows.append(Row(type=item["type"], record=item["record"]))
        transactions.append(Transaction(tx=number, rows=tuple(rows)))
    return transactions


def read_audit(root: Path) -> list[dict[str, Any]]:
    return _read_lines(root / AUDIT_FILE)


def verify_chain(lines: Sequence[Mapping[str, Any]]) -> list[str]:
    """Chain problems, each naming its 1-based line; empty when the chain verifies.

    An edited line fails its own hash check. An edited line whose hash was recomputed fails
    at the next line, whose ``prev_hash`` no longer matches.
    """
    problems: list[str] = []
    previous: str | None = None
    for number, line in enumerate(lines, start=1):
        if line.get("seq") != number - 1:
            problems.append(f"audit line {number}: seq {line.get('seq')!r}, expected {number - 1}")
        if line.get("prev_hash") != previous:
            problems.append(f"audit line {number}: prev_hash does not match line {number - 1}")
        if line.get("hash") != audit_line_hash(line):
            problems.append(f"audit line {number}: hash does not match its content")
        stored = line.get("hash")
        previous = stored if isinstance(stored, str) else None
    return problems


def verify_coverage(
    transactions: Sequence[Transaction], lines: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Every row has exactly one audit line with its tx and ``ref_hash``, and nothing else."""
    problems: list[str] = []
    expected: dict[tuple[int, str], int] = {}
    for transaction in transactions:
        for row in transaction.rows:
            key = (transaction.tx, row.hash)
            expected[key] = expected.get(key, 0) + 1
    seen: dict[tuple[int, str], int] = {}
    for number, line in enumerate(lines, start=1):
        tx, ref_hash = line.get("tx"), line.get("ref_hash")
        if not isinstance(tx, int) or not isinstance(ref_hash, str):
            problems.append(f"audit line {number}: no tx or ref_hash")
            continue
        key = (tx, ref_hash)
        if key not in expected:
            problems.append(f"audit line {number}: covers no row of tx {tx} (ref_hash {ref_hash})")
        seen[key] = seen.get(key, 0) + 1
    for key, count in sorted(expected.items()):
        if seen.get(key, 0) != count:
            problems.append(
                f"tx {key[0]}: row {key[1]} has {seen.get(key, 0)} audit lines, expected {count}"
            )
    return problems
