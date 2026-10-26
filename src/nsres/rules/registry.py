"""Rule Registry (C16; spec B.2, plan A-11, DECISIONS D-021).

A rule is a versioned ``RuleRecord`` with the B.2 fields plus a Python predicate. Running a
rule turns the predicate's detections into findings through the finding factory, and reports
UNCHECKABLE when the predicate could not check something; a run is PASS only when it found
nothing and nothing was uncheckable.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

from nsres.domain.canonical import content_hash
from nsres.domain.records import Finding, Span, to_json
from nsres.domain.vocab import FindingEvidence, Severity

if TYPE_CHECKING:
    from nsres.rules.factory import FindingFactory

TIGHTEN: Literal["TIGHTEN"] = "TIGHTEN"
_SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_RULE_ID = re.compile(r"(RC|CC|PK|EX|AU|MC|CX|ED)-?[A-Z0-9-]+")


class Certainty(StrEnum):
    """Whether a contradiction holds in every feasible placement or only some (§3.5)."""

    CERTAIN = "CERTAIN"
    POSSIBLE = "POSSIBLE"


class RunStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCHECKABLE = "UNCHECKABLE"


@dataclass(frozen=True, kw_only=True)
class SeveritySpec:
    """B.2 ``severity``: one severity, or separate ones for CERTAIN and POSSIBLE results."""

    certain: Severity
    possible: Severity | Literal["TIGHTEN"] | None = None


@dataclass(frozen=True, kw_only=True)
class RuleRecord:
    """The B.2 Rule Registry record."""

    rule_id: str
    name: str
    version: str
    layer: str
    family: str
    severity: SeveritySpec
    inputs: tuple[str, ...]
    logic_ref: str
    message: str
    repair_hints: tuple[str, ...] = ()
    uncheckable_when: tuple[str, ...] = ()
    evidence_required: FindingEvidence = FindingEvidence.CONTENT_READ
    config_version: str

    def __post_init__(self) -> None:
        if _RULE_ID.fullmatch(self.rule_id) is None:
            raise ValueError(f"rule id {self.rule_id!r} does not fit the B.4 rule pattern")
        if _SEMVER.fullmatch(self.version) is None:
            raise ValueError(f"rule {self.rule_id} version {self.version!r} is not semver")
        if not self.message:
            raise ValueError(f"rule {self.rule_id} has no message template")


@dataclass(frozen=True, kw_only=True)
class Detection:
    """One problem a predicate found. ``args`` fill the rule's message template."""

    records: tuple[str, ...]
    args: Mapping[str, Any] = field(default_factory=dict)
    certainty: Certainty = Certainty.CERTAIN
    evidence: FindingEvidence = FindingEvidence.CONTENT_READ
    detection_confidence: float = 1.0
    spans: tuple[Span, ...] = ()
    repairs: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Uncheckable:
    """Something the predicate could not check, with the B.2 ``uncheckable_when`` reason."""

    reason: str
    records: tuple[str, ...] = ()


Predicate = Callable[[Any], Iterable[Detection | Uncheckable]]


@dataclass(frozen=True)
class Tightening:
    """A POSSIBLE result whose rule says TIGHTEN: a constraint to add, not a finding."""

    rule_id: str
    detection: Detection


@dataclass(frozen=True)
class RuleRun:
    rule_id: str
    status: RunStatus
    findings: tuple[Finding, ...]
    uncheckable: tuple[Uncheckable, ...]
    tightenings: tuple[Tightening, ...]


class RuleRegistry:
    """The registered rules of one control-plane configuration version."""

    def __init__(self, config_version: str) -> None:
        self.config_version = config_version
        self._rules: dict[str, tuple[RuleRecord, Predicate]] = {}

    def register(self, record: RuleRecord, predicate: Predicate) -> None:
        if record.rule_id in self._rules:
            raise ValueError(
                f"rule {record.rule_id} is already registered; issue a new version instead"
            )
        if record.config_version != self.config_version:
            raise ValueError(
                f"rule {record.rule_id} belongs to config {record.config_version},"
                f" not {self.config_version}"
            )
        self._rules[record.rule_id] = (record, predicate)

    def record(self, rule_id: str) -> RuleRecord:
        return self._rules[rule_id][0]

    def rule_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._rules))

    def digest(self) -> str:
        """Content hash of every registered rule record (the configuration's identity)."""
        return content_hash([to_json_rule(self._rules[rule_id][0]) for rule_id in self.rule_ids()])

    def run(self, rule_id: str, context: Any, factory: FindingFactory) -> RuleRun:
        record, predicate = self._rules[rule_id]
        findings: list[Finding] = []
        uncheckable: list[Uncheckable] = []
        tightenings: list[Tightening] = []
        for result in predicate(context):
            if isinstance(result, Uncheckable):
                uncheckable.append(result)
                continue
            severity = record.severity.certain
            if result.certainty is Certainty.POSSIBLE:
                possible = record.severity.possible
                if possible == TIGHTEN:
                    tightenings.append(Tightening(rule_id, result))
                    continue
                severity = possible if isinstance(possible, Severity) else severity
            findings.append(factory.make(record, result, severity))
        if findings:
            status = RunStatus.FAIL
        elif uncheckable:
            status = RunStatus.UNCHECKABLE
        else:
            status = RunStatus.PASS
        return RuleRun(rule_id, status, tuple(findings), tuple(uncheckable), tuple(tightenings))

    def run_all(self, context: Any, factory: FindingFactory) -> tuple[RuleRun, ...]:
        return tuple(self.run(rule_id, context, factory) for rule_id in self.rule_ids())


def to_json_rule(record: RuleRecord) -> dict[str, Any]:
    document: dict[str, Any] = to_json(record)
    return document
