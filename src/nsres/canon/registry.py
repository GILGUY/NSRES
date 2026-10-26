"""The canon registry, its L1 rules, and the gate console's isolation check (spec L1; D-017 to
D-019).

``CanonRegistry`` reads entities and canon rules, parses their structured statements, and
builds the travel network and daylight model. ``canon_rules()`` registers the L1 checks in a
``RuleRegistry``. ``isolation_check`` adapts the record-scope checks to the store's gate
console.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass

from nsres.canon.identity import collisions
from nsres.canon.metrics import DaylightModel, TravelNetwork, closure_gaps, speed_breaches
from nsres.canon.precedence import resolve
from nsres.canon.statements import (
    METRIC_FORMS,
    Calendar,
    Daylight,
    Disambiguation,
    Distance,
    Speed,
    StatementError,
    TimetableEntry,
    Travel,
    form_of,
    parse_one,
)
from nsres.domain.records import BaseRecord, CanonRule, Entity
from nsres.domain.uuid7 import Uuid7Generator
from nsres.domain.vocab import CanonRuleClass, Severity, Status
from nsres.rules.factory import FindingFactory
from nsres.rules.registry import (
    Detection,
    RuleRecord,
    RuleRegistry,
    SeveritySpec,
    Uncheckable,
)
from nsres.store.lifecycle import IsolationCheck
from nsres.store.store import Store

CONFIG_VERSION = "cp-0.1.0"
RECORD_SCOPE = ("RC-L1-0", "RC-L1-3B")
"""Checks the gate console runs on one record against the current canon (D-019)."""


@dataclass(frozen=True)
class Malformed:
    rule: str
    text: str
    error: str


def _split(text: str) -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    quoted = False
    for char in text:
        if char == '"':
            quoted = not quoted
        if char == ";" and not quoted:
            pieces.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    pieces.append("".join(current).strip())
    return [piece for piece in pieces if piece]


class CanonRegistry:
    """Entities and canon rules, with their parsed statements and derived metrics."""

    def __init__(self, records: Iterable[BaseRecord], calendar: Calendar) -> None:
        self.calendar = calendar
        self.entities: list[Entity] = []
        self.rules: list[CanonRule] = []
        self.travels: list[tuple[Travel, str]] = []
        self.distances: list[tuple[Distance, str]] = []
        self.speeds: list[tuple[Speed, str]] = []
        self.timetables: list[tuple[TimetableEntry, str]] = []
        self.daylight_rows: list[tuple[Daylight, str]] = []
        self.disambiguations: list[Disambiguation] = []
        self.unparsed: list[tuple[str, str]] = []
        self.malformed: list[Malformed] = []
        for record in sorted(records, key=lambda item: item.handle):
            if isinstance(record, Entity):
                self.entities.append(record)
            elif isinstance(record, CanonRule):
                self.rules.append(record)
                self._read(record)
        self.network = TravelNetwork(self.travels, self.timetables)
        self.daylight = DaylightModel(calendar, self.daylight_rows)

    @classmethod
    def from_store(cls, store: Store, calendar: Calendar) -> CanonRegistry:
        return cls(canon_records(store), calendar)

    def _read(self, rule: CanonRule) -> None:
        for text in _split(rule.statement_structured):
            form = form_of(text)
            if form in METRIC_FORMS and rule.rule_class is not CanonRuleClass.METRIC:
                self.malformed.append(
                    Malformed(
                        rule.handle,
                        text,
                        f"{form}() needs rule class METRIC, not {rule.rule_class}",
                    )
                )
                continue
            try:
                statement = parse_one(text)
            except StatementError as error:
                self.malformed.append(Malformed(rule.handle, text, str(error)))
                continue
            if isinstance(statement, Travel):
                self.travels.append((statement, rule.handle))
            elif isinstance(statement, Distance):
                self.distances.append((statement, rule.handle))
            elif isinstance(statement, Speed):
                self.speeds.append((statement, rule.handle))
            elif isinstance(statement, TimetableEntry):
                self.timetables.append((statement, rule.handle))
            elif isinstance(statement, Daylight):
                self.daylight_rows.append((statement, rule.handle))
            elif isinstance(statement, Disambiguation):
                self.disambiguations.append(statement)
            else:
                self.unparsed.append((rule.handle, statement))


def canon_records(store: Store) -> list[BaseRecord]:
    """The ACCEPTED and CANON entities and canon rules in a store."""
    return [
        record
        for record in store.records()
        if isinstance(record, Entity | CanonRule)
        and record.status in (Status.ACCEPTED, Status.CANON)
    ]


@dataclass(frozen=True)
class CanonContext:
    canon: CanonRegistry
    conflicts: tuple[tuple[BaseRecord, BaseRecord], ...] = ()


def _malformed(context: CanonContext) -> Iterator[Detection | Uncheckable]:
    for item in context.canon.malformed:
        yield Detection(
            records=(item.rule,), args={"rule": item.rule, "text": item.text, "error": item.error}
        )


def _identity(context: CanonContext) -> Iterator[Detection | Uncheckable]:
    for item in collisions(context.canon.entities, context.canon.disambiguations):
        yield Detection(
            records=(item.first, item.second),
            args={"first": item.first, "second": item.second, "name": item.name},
        )


def _closure(context: CanonContext) -> Iterator[Detection | Uncheckable]:
    for gap in closure_gaps(context.canon.network, context.canon.travels):
        yield Detection(
            records=(gap.source,),
            args={
                "source": gap.source,
                "mode": gap.travel.mode,
                "origin": gap.travel.origin,
                "destination": gap.travel.destination,
                "declared": gap.travel.minutes,
                "closure": gap.closure_minutes,
            },
        )


def _speed(context: CanonContext) -> Iterator[Detection | Uncheckable]:
    breaches, unchecked = speed_breaches(
        context.canon.travels, context.canon.distances, context.canon.speeds
    )
    for breach in breaches:
        yield Detection(
            records=tuple(
                dict.fromkeys((breach.source, breach.distance_source, breach.speed_source))
            ),
            args={
                "source": breach.source,
                "mode": breach.travel.mode,
                "origin": breach.travel.origin,
                "destination": breach.travel.destination,
                "declared": breach.travel.minutes,
                "minimum": breach.minimum_minutes,
            },
        )
    yield from unchecked


def _same_tier(context: CanonContext) -> Iterator[Detection | Uncheckable]:
    for first, second in context.conflicts:
        resolution = resolve(first, second)
        if resolution.needs_gate:
            assert resolution.gate is not None
            yield Detection(
                records=(first.handle, second.handle),
                args={
                    "first": first.handle,
                    "second": second.handle,
                    "tier": resolution.tiers[0].value,
                    "gate": resolution.gate.value,
                },
            )


def _record(
    rule_id: str,
    name: str,
    severity: Severity,
    logic: str,
    message: str,
    *,
    inputs: tuple[str, ...] = ("canon_rules",),
    repairs: tuple[str, ...] = (),
    uncheckable: tuple[str, ...] = (),
) -> RuleRecord:
    return RuleRecord(
        rule_id=rule_id,
        name=name,
        version="1.0.0",
        layer="L1",
        family="reconciliation",
        severity=SeveritySpec(certain=severity),
        inputs=inputs,
        logic_ref=f"nsres.canon.registry:{logic}",
        message=message,
        repair_hints=repairs,
        uncheckable_when=uncheckable,
        config_version=CONFIG_VERSION,
    )


def canon_rules() -> RuleRegistry:
    """The L1 checks of D-018, registered with their predicates."""
    registry = RuleRegistry(CONFIG_VERSION)
    registry.register(
        _record(
            "RC-L1-0",
            "Malformed structured canon statement",
            Severity.BLOCKING,
            "_malformed",
            "{rule} has a malformed structured statement {text!r}: {error}",
            repairs=("fix_statement",),
        ),
        _malformed,
    )
    registry.register(
        _record(
            "RC-L1-2",
            "Identity collision",
            Severity.MAJOR,
            "_identity",
            '{first} and {second} share the name "{name}" with no disambiguation record',
            inputs=("entities", "disambiguations"),
            repairs=("add_disambiguation_record", "change_alias"),
        ),
        _identity,
    )
    registry.register(
        _record(
            "RC-L1-3A",
            "Travel time longer than its shortest-path closure",
            Severity.MINOR,
            "_closure",
            "{source}: {mode} from {origin} to {destination} is declared as {declared} min,"
            " longer than the {closure} min shortest path",
            inputs=("travel_metrics",),
            repairs=("add_route_rule", "correct_declared_time"),
        ),
        _closure,
    )
    registry.register(
        _record(
            "RC-L1-3B",
            "Travel time faster than the speed rule",
            Severity.BLOCKING,
            "_speed",
            "{source}: {declared} min by {mode} from {origin} to {destination} is faster than"
            " the speed rule allows ({minimum:.1f} min over the declared distance)",
            inputs=("travel_metrics", "distances", "speed_rules"),
            repairs=("correct_declared_time", "correct_distance", "change_mode"),
            uncheckable=("missing_distance", "missing_speed"),
        ),
        _speed,
    )
    registry.register(
        _record(
            "RC-L1-6",
            "Same-tier conflict",
            Severity.MAJOR,
            "_same_tier",
            "{first} and {second} conflict at the same tier ({tier}); the {gate} gate decides",
            inputs=("conflicts",),
            repairs=("decide_at_gate",),
        ),
        _same_tier,
    )
    return registry


def isolation_check(
    canon: Callable[[], Iterable[BaseRecord]], calendar: Calendar, ids: Uuid7Generator
) -> IsolationCheck:
    """The gate console's check (D-019): BLOCKING record-scope findings that involve the record,
    computed against the current canon plus the record."""
    registry = canon_rules()

    def check(record: object) -> Sequence[str]:
        if not isinstance(record, Entity | CanonRule):
            return []
        others = [item for item in canon() if item.handle != record.handle]
        context = CanonContext(CanonRegistry([*others, record], calendar))
        factory = FindingFactory(ids)
        failures: list[str] = []
        for rule_id in RECORD_SCOPE:
            for finding in registry.run(rule_id, context, factory).findings:
                if finding.severity is Severity.BLOCKING and record.handle in finding.records:
                    failures.append(f"{finding.rule}: {finding.notes}")
        return failures

    return check


def store_isolation_check(store: Store, calendar: Calendar, ids: Uuid7Generator) -> IsolationCheck:
    return isolation_check(lambda: canon_records(store), calendar, ids)
