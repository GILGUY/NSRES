"""Rule registry and finding factory (spec B.2, DEF-41, REQ-9.1.1; DECISIONS D-019, D-021),
and the canon isolation check wired into the gate console."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import fields, replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from nsres.canon.registry import CONFIG_VERSION, canon_rules, store_isolation_check
from nsres.canon.statements import Calendar
from nsres.domain import records as r
from nsres.domain.schemas import finding_errors
from nsres.domain.vocab import (
    CanonRuleClass,
    FindingEvidence,
    FindingStatus,
    Gate,
    GateOutcome,
    Plane,
    Provenance,
    Severity,
    Status,
)
from nsres.rules.factory import FindingFactory, render
from nsres.rules.registry import (
    TIGHTEN,
    Certainty,
    Detection,
    RuleRecord,
    RuleRegistry,
    RunStatus,
    SeveritySpec,
    Uncheckable,
)
from nsres.store import Refusal, Store
from tests import builders as b
from tests import spec_text as spec

RC08 = RuleRecord(
    rule_id="RC-08",
    name="Impossible movement",
    version="1.0.0",
    layer="L6",
    family="reconciliation",
    severity=SeveritySpec(certain=Severity.BLOCKING, possible=TIGHTEN),
    inputs=("presence_segments", "travel_metrics", "transport_modes", "timetables"),
    logic_ref="rules/rc08_movement.dl",
    message=(
        "{character} cannot reach {to_location} by {latest_arrival} from {from_location};"
        " minimum travel {tau} min."
    ),
    repair_hints=("move_event", "widen_window", "add_bridge_event", "change_transport_mode"),
    uncheckable_when=("missing_travel_metric",),
    evidence_required=FindingEvidence.CONTENT_READ,
    config_version="cp-2026.10.1",
)
ARGS = {
    "character": "CHR-002",
    "to_location": "LOC-001",
    "latest_arrival": "07:40",
    "from_location": "LOC-004",
    "tau": 150,
}


def test_rule_record_has_exactly_the_b2_fields() -> None:
    yaml_keys = re.findall(r"^([a-z_]+):", spec.fenced(spec.section("### B.2"), "yaml"), re.M)
    assert [field.name for field in fields(RuleRecord)] == yaml_keys


def test_the_b2_example_record_constructs() -> None:
    assert RC08.severity.possible == TIGHTEN
    with pytest.raises(ValueError, match=r"B\.4 rule pattern"):
        replace(RC08, rule_id="XX-01")
    with pytest.raises(ValueError, match="semver"):
        replace(RC08, version="1.0")


def _predicate(results: list[Detection | Uncheckable]) -> Any:
    def predicate(_: object) -> Iterator[Detection | Uncheckable]:
        yield from results

    return predicate


def _registry(results: list[Detection | Uncheckable], record: RuleRecord = RC08) -> RuleRegistry:
    registry = RuleRegistry(record.config_version)
    registry.register(record, _predicate(results))
    return registry


def test_a_certain_detection_becomes_a_blocking_finding_with_rendered_message() -> None:
    run = _registry([Detection(records=("EVT-0109",), args=ARGS)]).run(
        "RC-08", None, FindingFactory(b.ids())
    )
    assert run.status is RunStatus.FAIL
    (finding,) = run.findings
    assert (finding.handle, finding.rule, finding.severity, finding.status) == (
        "FND-R-01",
        "RC-08",
        Severity.BLOCKING,
        FindingStatus.OPEN,
    )
    assert (
        finding.notes
        == "CHR-002 cannot reach LOC-001 by 07:40 from LOC-004; minimum travel 150 min."
    )
    assert finding.repairs == RC08.repair_hints
    assert finding_errors(r.to_json(finding)) == []


def test_a_possible_detection_under_tighten_is_a_tightening_not_a_finding() -> None:
    detection = Detection(records=("EVT-0109",), args=ARGS, certainty=Certainty.POSSIBLE)
    run = _registry([detection]).run("RC-08", None, FindingFactory(b.ids()))
    assert run.findings == ()
    assert [t.detection for t in run.tightenings] == [detection]
    assert run.status is RunStatus.PASS


def test_a_possible_detection_takes_the_possible_severity() -> None:
    record = replace(
        RC08, severity=SeveritySpec(certain=Severity.BLOCKING, possible=Severity.MAJOR)
    )
    detection = Detection(records=("EVT-0109",), args=ARGS, certainty=Certainty.POSSIBLE)
    (finding,) = _registry([detection], record).run("RC-08", None, FindingFactory(b.ids())).findings
    assert finding.severity is Severity.MAJOR


def test_uncheckable_input_never_passes() -> None:
    run = _registry([Uncheckable("missing_travel_metric: LOC-004 to LOC-001")]).run(
        "RC-08", None, FindingFactory(b.ids())
    )
    assert run.status is RunStatus.UNCHECKABLE
    assert run.findings == ()
    empty = _registry([]).run("RC-08", None, FindingFactory(b.ids()))
    assert empty.status is RunStatus.PASS


def test_weak_evidence_caps_a_blocking_finding_at_major() -> None:
    detection = Detection(
        records=("EVT-0109",), args=ARGS, evidence=FindingEvidence.FOUND_BY_SNIPPET
    )
    (finding,) = _registry([detection]).run("RC-08", None, FindingFactory(b.ids())).findings
    assert finding.severity is Severity.MAJOR
    assert "capped at MAJOR" in (finding.notes or "")
    assert finding.evidence is FindingEvidence.FOUND_BY_SNIPPET


def test_handles_number_findings_in_detection_order() -> None:
    detections: list[Detection | Uncheckable] = [
        Detection(records=(f"EVT-01{n:02d}",), args=ARGS) for n in range(3)
    ]
    run = _registry(detections).run("RC-08", None, FindingFactory(b.ids()))
    assert [f.handle for f in run.findings] == ["FND-R-01", "FND-R-02", "FND-R-03"]


def test_duplicate_registration_and_foreign_config_are_refused() -> None:
    registry = _registry([])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(RC08, _predicate([]))
    with pytest.raises(ValueError, match="belongs to config"):
        registry.register(replace(RC08, rule_id="RC-09", config_version="cp-other"), _predicate([]))


def test_the_registry_digest_changes_when_a_severity_changes() -> None:
    first = _registry([]).digest()
    changed = _registry([], replace(RC08, severity=SeveritySpec(certain=Severity.MAJOR))).digest()
    assert first != changed
    assert _registry([]).digest() == first


def test_message_rendering_needs_every_argument() -> None:
    with pytest.raises(KeyError, match="tau"):
        render(RC08.message, {key: value for key, value in ARGS.items() if key != "tau"})


def test_the_canon_rules_are_registered_under_one_config() -> None:
    registry = canon_rules()
    assert registry.rule_ids() == ("RC-L1-0", "RC-L1-2", "RC-L1-3A", "RC-L1-3B", "RC-L1-6")
    assert {registry.record(rule_id).config_version for rule_id in registry.rule_ids()} == {
        CONFIG_VERSION
    }
    assert registry.record("RC-L1-3B").uncheckable_when == ("missing_distance", "missing_speed")


# --- the isolation check in the gate console (D-019) ------------------------------------------


def _metric(handle: str, structured: str) -> r.CanonRule:
    return r.CanonRule(
        uuid=b.IDS.new_str(),
        handle=handle,
        rev=1,
        status=Status.PROPOSAL,
        provenance=Provenance.AUTHOR,
        plane=Plane.REALITY,
        tx=r.TxRange(from_rev=0, to_rev=None),
        rule_class=CanonRuleClass.METRIC,
        statement_structured=structured,
        statement=structured,
    )


def test_the_gate_console_refuses_canon_that_breaks_a_speed_rule(tmp_path: Path) -> None:
    store = Store.create(tmp_path, clock=b.Clock(), ids=b.ids())
    console = store.gate_console(
        store_isolation_check(store, Calendar(date(1893, 10, 1)), b.ids(11))
    )
    limits = _metric("CAN-081", "speed(carriage, 15); distance(LOC-001, LOC-003, 6)")
    assert console.propose(limits, actor="author").ok
    assert console.decide(Gate.PROPOSAL, "CAN-081", GateOutcome.ACCEPT, actor="author").ok
    too_fast = _metric("CAN-082", "travel(LOC-003, LOC-001, carriage, 5)")
    console.propose(too_fast, actor="author")
    refused = console.decide(Gate.PROPOSAL, "CAN-082", GateOutcome.ACCEPT, actor="author")
    assert refused.refusal is Refusal.GUARD_FAILED
    assert refused.detail.startswith("RC-L1-3B: CAN-082: 5 min by carriage")
    fine = _metric("CAN-083", "travel(LOC-003, LOC-001, carriage, 25)")
    console.propose(fine, actor="author")
    assert console.decide(Gate.PROPOSAL, "CAN-083", GateOutcome.ACCEPT, actor="author").ok


def test_the_gate_console_refuses_a_malformed_metric_and_lets_minor_findings_through(
    tmp_path: Path,
) -> None:
    store = Store.create(tmp_path, clock=b.Clock(), ids=b.ids())
    console = store.gate_console(
        store_isolation_check(store, Calendar(date(1893, 10, 1)), b.ids(12))
    )
    console.propose(_metric("CAN-090", "travel(LOC-001, LOC-002, carriage)"), actor="author")
    refused = console.decide(Gate.PROPOSAL, "CAN-090", GateOutcome.ACCEPT, actor="author")
    assert refused.refusal is Refusal.GUARD_FAILED
    assert refused.detail.startswith("RC-L1-0")
    for handle, text in [
        (
            "CAN-091",
            "travel(LOC-001, LOC-002, carriage, 20); travel(LOC-002, LOC-003, carriage, 30)",
        ),
        ("CAN-092", "travel(LOC-001, LOC-003, carriage, 90)"),  # longer than 20 + 30: MINOR only
    ]:
        console.propose(_metric(handle, text), actor="author")
        assert console.decide(Gate.PROPOSAL, handle, GateOutcome.ACCEPT, actor="author").ok
    assert console.decide(Gate.CANON, "CAN-092", GateOutcome.CANONIZE, actor="author").ok


def test_non_canon_records_pass_the_canon_isolation_check(tmp_path: Path) -> None:
    store = Store.create(tmp_path, clock=b.Clock(), ids=b.ids())
    check = store_isolation_check(store, Calendar(date(1893, 10, 1)), b.ids(13))
    assert check(b.thread()) == []
    assert check(b.fact()) == []
