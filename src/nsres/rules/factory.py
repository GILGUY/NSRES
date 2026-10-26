"""Finding factory (spec DEF-41, B.4; DECISIONS D-018, D-021).

Turns a rule record and one detection into a ``Finding``: a fresh UUIDv7, the next
``FND-R-nn`` handle, the rendered message in ``notes``, the rule's repair hints, and the
severity capped at MAJOR when the evidence is weaker than CONTENT_READ (REQ-9.1.1).
"""

from __future__ import annotations

from string import Formatter
from typing import TYPE_CHECKING, Any

from nsres.domain.records import Finding, TxRange
from nsres.domain.uuid7 import Uuid7Generator
from nsres.domain.vocab import FindingEvidence, FindingStatus, Plane, Provenance, Severity

if TYPE_CHECKING:
    from nsres.rules.registry import Detection, RuleRecord


def render(template: str, args: dict[str, Any]) -> str:
    """Fill a B.2 message template; a missing argument is a programmer error."""
    names = {name for _, name, _, _ in Formatter().parse(template) if name}
    missing = sorted(names - set(args))
    if missing:
        raise KeyError(f"message template needs {missing}")
    return template.format_map(args)


class FindingFactory:
    """Builds findings for one run. Handles are ``FND-R-01``, ``FND-R-02``, ..."""

    def __init__(self, ids: Uuid7Generator, *, first: int = 1) -> None:
        self._ids = ids
        self._next = first

    def make(self, rule: RuleRecord, detection: Detection, severity: Severity) -> Finding:
        capped = severity
        note = render(rule.message, dict(detection.args))
        if severity is Severity.BLOCKING and detection.evidence is not FindingEvidence.CONTENT_READ:
            capped = Severity.MAJOR
            note += f" [severity capped at MAJOR: evidence {detection.evidence} (REQ-9.1.1)]"
        handle = f"FND-R-{self._next:02d}"
        self._next += 1
        return Finding(
            uuid=self._ids.new_str(),
            handle=handle,
            rev=1,
            provenance=Provenance.ENGINE_BRIDGE,
            plane=Plane.CONTROL,
            tx=TxRange(from_rev=0, to_rev=None),
            notes=note,
            rule=rule.rule_id,
            severity=capped,
            spans=detection.spans,
            records=detection.records,
            evidence=detection.evidence,
            detection_confidence=detection.detection_confidence,
            repairs=detection.repairs if detection.repairs is not None else rule.repair_hints,
            status=FindingStatus.OPEN,
        )
