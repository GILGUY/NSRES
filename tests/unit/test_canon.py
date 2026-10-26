"""Canon registry: statements, travel closure, timetables, speed rules, daylight, identity,
precedence (spec §3.4, L1, Appendix A; DECISIONS D-017 to D-020)."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from nsres.canon.identity import collisions
from nsres.canon.metrics import Light
from nsres.canon.precedence import resolve, tier_of
from nsres.canon.registry import CanonContext, CanonRegistry, canon_rules
from nsres.canon.statements import (
    Calendar,
    Daylight,
    Disambiguation,
    Distance,
    Speed,
    StatementError,
    TimetableEntry,
    Travel,
    parse_all,
    parse_one,
)
from nsres.domain import records as r
from nsres.domain.vocab import (
    CanonRuleClass,
    Gate,
    Plane,
    PrecedenceTier,
    Provenance,
    Severity,
    Status,
    Tier,
)
from nsres.rules.factory import FindingFactory
from nsres.rules.registry import RunStatus, Uncheckable
from tests import builders as b

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = Calendar(date(1893, 10, 1))


def harrow(status: Status = Status.CANON) -> list[Any]:
    rows = json.loads(
        (ROOT / "fixtures" / "harrow-house" / "canon.json").read_text(encoding="utf-8")
    )
    classes = {"Entity": r.Entity, "CanonRule": r.CanonRule}
    return [
        replace(r.from_json(classes[row["type"]], row["record"]), status=status) for row in rows
    ]


def canon_rule(
    handle: str, structured: str, rule_class: CanonRuleClass = CanonRuleClass.METRIC
) -> r.CanonRule:
    return r.CanonRule(
        uuid=b.IDS.new_str(),
        handle=handle,
        rev=1,
        status=Status.CANON,
        provenance=Provenance.AUTHOR,
        plane=Plane.REALITY,
        tx=r.TxRange(from_rev=0, to_rev=None),
        rule_class=rule_class,
        statement_structured=structured,
        statement=structured,
    )


def registry(*extra: Any) -> CanonRegistry:
    return CanonRegistry([*harrow(), *extra], CALENDAR)


def run(rule_id: str, canon: CanonRegistry, conflicts: tuple[tuple[Any, Any], ...] = ()) -> Any:
    return canon_rules().run(rule_id, CanonContext(canon, conflicts), FindingFactory(b.ids(5)))


# --- statements ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("travel(LOC-001, LOC-002, carriage, 20)", Travel("LOC-001", "LOC-002", "carriage", 20)),
        (
            "travel(LOC-001, LOC-002, foot, 45, oneway)",
            Travel("LOC-001", "LOC-002", "foot", 45, True),
        ),
        ("distance(LOC-001, LOC-003, 8.5)", Distance("LOC-001", "LOC-003", 8.5)),
        ("speed(carriage, 15)", Speed("carriage", 15.0)),
        (
            "timetable(LOC-004, LOC-003, rail, 07:20, 09:05)",
            TimetableEntry("LOC-004", "LOC-003", "rail", 440, 545),
        ),
        ("daylight(1893-10-15, 06:45, 17:13)", Daylight(date(1893, 10, 15), 405, 1033)),
        (
            'disambiguate(CHR-002, CHR-007, "the Inspector")',
            Disambiguation("CHR-002", "CHR-007", "the Inspector"),
        ),
    ],
)
def test_recognized_statement_forms_parse(text: str, expected: Any) -> None:
    assert parse_one(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "travel(LOC-001, LOC-002, carriage)",
        "travel(LOC-001, LOC-002, carriage, -5)",
        "travel(LOC-001, LOC-002, carriage, 20.5)",
        "travel(CHR-001, LOC-002, carriage, 20)",
        "travel(LOC-001, LOC-002, Carriage!, 20)",
        "travel(LOC-001, LOC-002, carriage, 20, twoway)",
        "timetable(LOC-004, LOC-003, rail, 7:20, 09:05)",
        "timetable(LOC-004, LOC-003, rail, 25:00, 09:05)",
        "daylight(1893-13-15, 06:45, 17:13)",
        "daylight(1893-10-15, 18:00, 06:45)",
        'disambiguate(CHR-002, EVT-0104, "the Inspector")',
        "disambiguate(CHR-002, CHR-007, the Inspector)",
        "speed(carriage, fast)",
    ],
)
def test_malformed_recognized_statements_are_errors(text: str) -> None:
    with pytest.raises(StatementError):
        parse_one(text)


def test_unrecognized_text_is_kept_and_semicolons_split_statements() -> None:
    assert parse_one("invariant(not(acts(x)) or alive(x))") == "invariant(not(acts(x)) or alive(x))"
    parsed = parse_all(
        'travel(LOC-001, LOC-002, carriage, 20); disambiguate(CHR-002, CHR-007, "a; b")'
    )
    assert parsed == [
        Travel("LOC-001", "LOC-002", "carriage", 20),
        Disambiguation("CHR-002", "CHR-007", "a; b"),
    ]


def test_timetable_arrival_at_or_before_departure_is_next_day() -> None:
    overnight = parse_one("timetable(LOC-004, LOC-003, rail, 23:30, 01:10)")
    assert isinstance(overnight, TimetableEntry)
    assert overnight.duration == 100


def test_calendar_round_trip() -> None:
    minute = CALENDAR.minutes("1893-10-15T07:40")
    assert minute == 14 * 1440 + 7 * 60 + 40
    assert CALENDAR.display(minute) == "1893-10-15T07:40"
    assert CALENDAR.date_of(minute) == date(1893, 10, 15)


# --- the Harrow House canon ------------------------------------------------------------------


def test_the_harrow_house_canon_parses_cleanly() -> None:
    canon = registry()
    assert canon.malformed == []
    assert len(canon.entities) == 19
    assert len(canon.rules) == 9
    assert len(canon.travels) == 3
    assert len(canon.timetables) == 1
    assert len(canon.daylight_rows) == 2
    assert [handle for handle, _ in canon.unparsed] == [
        "CAN-003",
        "CAN-014",
        "CAN-014",
        "CAN-030",
        "CAN-030",
        "CAN-041",
        "CAN-052",
    ]


def test_earliest_arrival_from_york_matches_appendix_a3() -> None:
    """FND-R-01: a 07:00 telegram to York gives Hale an earliest Harrow House arrival of 09:30."""
    canon = registry()
    route = canon.network.earliest_arrival(
        "LOC-004", "LOC-001", CALENDAR.minutes("1893-10-15T07:00")
    )
    assert not isinstance(route, Uncheckable)
    assert CALENDAR.display(route.arrival) == "1893-10-15T09:30"
    assert route.sources == ("CAN-060", "CAN-061")


def test_the_bell_bridge_reaches_harrow_house_before_the_interview() -> None:
    """RES-0011: fetched from The Bell at 07:05 with a 20-minute drive, Hale arrives 07:25."""
    canon = registry()
    route = canon.network.earliest_arrival(
        "LOC-002", "LOC-001", CALENDAR.minutes("1893-10-15T07:05")
    )
    assert not isinstance(route, Uncheckable)
    assert CALENDAR.display(route.arrival) == "1893-10-15T07:25"
    on_foot = canon.network.earliest_arrival(
        "LOC-002", "LOC-001", CALENDAR.minutes("1893-10-15T07:05"), ["foot"]
    )
    assert not isinstance(on_foot, Uncheckable)
    assert CALENDAR.display(on_foot.arrival) == "1893-10-15T07:50"


def test_a_missed_train_waits_for_the_next_day() -> None:
    canon = registry()
    route = canon.network.earliest_arrival(
        "LOC-004", "LOC-003", CALENDAR.minutes("1893-10-15T07:21"), ["rail"]
    )
    assert not isinstance(route, Uncheckable)
    assert CALENDAR.display(route.arrival) == "1893-10-16T09:05"


def test_missing_travel_metrics_are_uncheckable_never_pass() -> None:
    canon = registry()
    result = canon.network.earliest_arrival("LOC-001", "LOC-001f", 0)
    assert isinstance(result, Uncheckable)
    assert result.reason.startswith("missing_travel_metric")
    no_rail = canon.network.earliest_arrival("LOC-004", "LOC-001", 0, ["carriage"])
    assert isinstance(no_rail, Uncheckable)


# --- WP-030 exit criteria: closure warning and speed-rule error -------------------------------


def test_a_direct_time_longer_than_the_closure_raises_the_closure_warning() -> None:
    longer = canon_rule("CAN-080", "travel(LOC-002, LOC-003, carriage, 60)")
    result = run("RC-L1-3A", registry(longer))
    assert result.status is RunStatus.FAIL
    (finding,) = result.findings
    assert (finding.rule, finding.severity, finding.records) == (
        "RC-L1-3A",
        Severity.MINOR,
        ("CAN-080",),
    )
    assert "declared as 60 min, longer than the 45 min shortest path" in (finding.notes or "")
    assert finding.repairs == ("add_route_rule", "correct_declared_time")


def test_the_harrow_house_canon_has_no_closure_gap() -> None:
    assert run("RC-L1-3A", registry()).status is RunStatus.PASS


def test_a_time_faster_than_the_speed_rule_raises_the_speed_error() -> None:
    rules = [
        canon_rule(
            "CAN-081",
            "speed(carriage, 15); distance(LOC-001, LOC-002, 4); distance(LOC-003, LOC-001, 6)",
        ),
        canon_rule(
            "CAN-082",
            "travel(LOC-003, LOC-001, carriage, 25); travel(LOC-001, LOC-003, carriage, 5, oneway)",
        ),
    ]
    result = run("RC-L1-3B", registry(*rules))
    (finding,) = result.findings
    assert (finding.rule, finding.severity) == ("RC-L1-3B", Severity.BLOCKING)
    assert finding.records == ("CAN-082", "CAN-081")
    assert "faster than the speed rule allows (24.0 min" in (finding.notes or "")


def test_speed_checks_without_distances_are_uncheckable() -> None:
    result = run("RC-L1-3B", registry())
    assert result.status is RunStatus.UNCHECKABLE
    assert result.findings == ()
    assert {item.reason.split(":")[0] for item in result.uncheckable} == {"missing_distance"}


# --- daylight --------------------------------------------------------------------------------


def test_daylight_model_matches_the_spec_examples() -> None:
    daylight = registry().daylight
    assert daylight.light_at(CALENDAR.minutes("1893-10-14T22:40")) is Light.DARK
    assert daylight.light_at(CALENDAR.minutes("1893-10-15T06:44")) is Light.DARK
    assert daylight.light_at(CALENDAR.minutes("1893-10-15T06:45")) is Light.DAYLIGHT
    assert daylight.light_at(CALENDAR.minutes("1893-10-15T07:40")) is Light.DAYLIGHT
    missing = daylight.light_at(CALENDAR.minutes("1893-10-16T07:40"))
    assert isinstance(missing, Uncheckable)
    assert missing.reason.startswith("missing_daylight")


# --- malformed statements and rule classes ----------------------------------------------------


def test_a_metric_statement_under_another_class_is_malformed() -> None:
    wrong = canon_rule("CAN-090", "travel(LOC-001, LOC-004, carriage, 300)", CanonRuleClass.DEFAULT)
    bad = canon_rule("CAN-091", "travel(LOC-001, LOC-004, carriage)")
    result = run("RC-L1-0", registry(wrong, bad))
    assert [(f.records, f.severity) for f in result.findings] == [
        (("CAN-090",), Severity.BLOCKING),
        (("CAN-091",), Severity.BLOCKING),
    ]
    assert "needs rule class METRIC" in (result.findings[0].notes or "")


# --- WP-030 exit criterion: identity collision ------------------------------------------------


def _inspector(handle: str = "CHR-007") -> r.Entity:
    return replace(
        b.character(handle, "Silas Grey"), aliases=("The  Inspector",), status=Status.CANON
    )


def test_two_entities_sharing_an_alias_produce_an_identity_collision() -> None:
    result = run("RC-L1-2", registry(_inspector()))
    (finding,) = result.findings
    assert (finding.rule, finding.severity, finding.records) == (
        "RC-L1-2",
        Severity.MAJOR,
        ("CHR-002", "CHR-007"),
    )
    assert 'share the name "the inspector"' in (finding.notes or "")


def test_a_disambiguation_record_clears_the_collision() -> None:
    record = canon_rule(
        "CAN-100", 'disambiguate(CHR-002, CHR-007, "the Inspector")', CanonRuleClass.INVARIANT
    )
    assert run("RC-L1-2", registry(_inspector(), record)).status is RunStatus.PASS


def test_disambiguation_covers_only_its_pair_and_name() -> None:
    record = canon_rule(
        "CAN-100", 'disambiguate(CHR-002, CHR-007, "the Inspector")', CanonRuleClass.INVARIANT
    )
    third = replace(_inspector("CHR-008"), canonical_name="Abel Dunn")
    found = collisions(
        registry(_inspector(), third, record).entities, registry(record).disambiguations
    )
    assert {(c.first, c.second) for c in found} == {("CHR-002", "CHR-008"), ("CHR-007", "CHR-008")}


def test_the_harrow_house_canon_has_no_identity_collision() -> None:
    assert run("RC-L1-2", registry()).status is RunStatus.PASS


# --- WP-030 exit criterion: precedence ----------------------------------------------------------


def test_tiers_follow_section_3_4() -> None:
    rule = canon_rule("CAN-200", "x", CanonRuleClass.INVARIANT)
    default = canon_rule("CAN-201", "y", CanonRuleClass.DEFAULT)
    cases = [
        (
            replace(b.character(), status=Status.CANON, tier=Tier.PUBLISHED),
            PrecedenceTier.PUBLISHED,
        ),
        (rule, PrecedenceTier.INVARIANT),
        (replace(rule, status=Status.ACCEPTED), PrecedenceTier.ACCEPTED),
        (replace(b.character(), status=Status.CANON), PrecedenceTier.CANON),
        (replace(b.character(), status=Status.ACCEPTED), PrecedenceTier.ACCEPTED),
        (default, PrecedenceTier.DEFAULT),
        (replace(default, status=Status.ACCEPTED), PrecedenceTier.DEFAULT),
        (b.character(), PrecedenceTier.PROPOSAL),
        (replace(b.character(), status=Status.REJECTED), None),
    ]
    for record, tier in cases:
        assert tier_of(record) is tier, record.handle


def test_a_cross_tier_conflict_resolves_to_the_higher_tier() -> None:
    accepted_event_fact = replace(b.fact("INF-030"), status=Status.ACCEPTED)
    default_rule = canon_rule(
        "CAN-030", "default(LOC-001a.lock, LOCKED, night)", CanonRuleClass.DEFAULT
    )
    resolution = resolve(default_rule, accepted_event_fact)
    assert resolution.winner is accepted_event_fact
    assert resolution.loser is default_rule
    assert not resolution.needs_gate
    assert (
        run("RC-L1-6", registry(), ((default_rule, accepted_event_fact),)).status is RunStatus.PASS
    )


def test_a_same_tier_conflict_returns_a_gate_required_finding_and_picks_nothing() -> None:
    first = replace(b.fact("INF-031"), status=Status.CANON)
    second = replace(b.fact("INF-032"), status=Status.CANON)
    resolution = resolve(first, second)
    assert resolution.winner is None
    assert resolution.loser is None
    assert resolution.gate is Gate.CANON
    result = run("RC-L1-6", registry(), ((first, second),))
    (finding,) = result.findings
    assert (finding.rule, finding.severity, finding.records) == (
        "RC-L1-6",
        Severity.MAJOR,
        ("INF-031", "INF-032"),
    )
    assert "the CANON gate decides" in (finding.notes or "")


def test_a_same_tier_telling_conflict_goes_to_its_acceptance_gate() -> None:
    first = replace(b.thread("THR-02"), status=Status.ACCEPTED)
    second = replace(b.thread("THR-03"), status=Status.ACCEPTED)
    assert resolve(first, second).gate is Gate.STRUCTURE


def test_retired_records_take_no_part_in_conflicts() -> None:
    with pytest.raises(ValueError, match="takes part in no conflict"):
        resolve(
            replace(b.fact(), status=Status.DEPRECATED),
            replace(b.fact("INF-007"), status=Status.CANON),
        )
