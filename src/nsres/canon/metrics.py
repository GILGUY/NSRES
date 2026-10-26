"""Canon metrics: the travel network with shortest-path closure, timetables as earliest-arrival
functions, speed rules, and the table-driven daylight model (spec L1 "Metrics"; D-017, D-018).

Missing data is never treated as a pass: a query the metrics cannot answer returns
``Uncheckable`` (spec L1 failure modes: "the engine MUST report UNCHECKABLE, never PASS").
"""

from __future__ import annotations

import heapq
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from nsres.canon.statements import (
    MINUTES_PER_DAY,
    Calendar,
    Daylight,
    Distance,
    Speed,
    TimetableEntry,
    Travel,
)
from nsres.rules.registry import Uncheckable


@dataclass(frozen=True)
class Leg:
    origin: str
    destination: str
    mode: str
    minutes: int
    source: str  # the canon rule handle that declared it


@dataclass(frozen=True)
class Service:
    entry: TimetableEntry
    source: str

    def earliest_arrival(self, ready_at: int) -> tuple[int, int]:
        """(departure, arrival) of the first departure at or after ``ready_at`` (minutes)."""
        day_start = ready_at - ready_at % MINUTES_PER_DAY
        departure = day_start + self.entry.depart
        if departure < ready_at:
            departure += MINUTES_PER_DAY
        return departure, departure + self.entry.duration


@dataclass(frozen=True)
class Route:
    """An earliest-arrival answer: when, and through which canon rules."""

    arrival: int
    sources: tuple[str, ...]


class TravelNetwork:
    """Directed travel legs by mode, plus daily timetable services."""

    def __init__(
        self,
        travels: Iterable[tuple[Travel, str]],
        services: Iterable[tuple[TimetableEntry, str]] = (),
    ) -> None:
        self.legs: list[Leg] = []
        for travel, source in travels:
            self.legs.append(
                Leg(travel.origin, travel.destination, travel.mode, travel.minutes, source)
            )
            if not travel.oneway:
                self.legs.append(
                    Leg(travel.destination, travel.origin, travel.mode, travel.minutes, source)
                )
        self.services = [Service(entry, source) for entry, source in services]
        self.places = sorted(
            {leg.origin for leg in self.legs}
            | {leg.destination for leg in self.legs}
            | {s.entry.origin for s in self.services}
            | {s.entry.destination for s in self.services}
        )

    def modes(self) -> tuple[str, ...]:
        return tuple(
            sorted({leg.mode for leg in self.legs} | {s.entry.mode for s in self.services})
        )

    def closure(self, mode: str) -> dict[tuple[str, str], int]:
        """All-pairs shortest travel times for one mode (Floyd-Warshall over direct legs)."""
        nodes = sorted(
            {leg.origin for leg in self.legs if leg.mode == mode}
            | {leg.destination for leg in self.legs if leg.mode == mode}
        )
        best: dict[tuple[str, str], int] = {}
        for leg in self.legs:
            if leg.mode == mode:
                key = (leg.origin, leg.destination)
                best[key] = min(best.get(key, leg.minutes), leg.minutes)
        for via in nodes:
            for start in nodes:
                first = best.get((start, via))
                if first is None:
                    continue
                for end in nodes:
                    second = best.get((via, end))
                    if second is None or start == end:
                        continue
                    if first + second < best.get((start, end), first + second + 1):
                        best[(start, end)] = first + second
        return best

    def earliest_arrival(
        self, origin: str, destination: str, ready_at: int, modes: Iterable[str] | None = None
    ) -> Route | Uncheckable:
        """Earliest arrival using travel legs and timetabled services of the allowed modes.

        Time-dependent Dijkstra; correct because waiting for a later departure never makes an
        earlier arrival possible (every leg and service is first-in, first-out).
        """
        allowed = set(self.modes() if modes is None else modes)
        if origin == destination:
            return Route(ready_at, ())
        best: dict[str, int] = {origin: ready_at}
        trail: dict[str, tuple[str, str]] = {}
        queue: list[tuple[int, str]] = [(ready_at, origin)]
        while queue:
            time, place = heapq.heappop(queue)
            if time > best.get(place, time):
                continue
            if place == destination:
                return Route(time, self._sources(trail, destination))
            for leg in self.legs:
                if leg.origin == place and leg.mode in allowed:
                    self._relax(
                        best, trail, queue, leg.destination, time + leg.minutes, place, leg.source
                    )
            for service in self.services:
                if service.entry.origin == place and service.entry.mode in allowed:
                    _, arrival = service.earliest_arrival(time)
                    self._relax(
                        best,
                        trail,
                        queue,
                        service.entry.destination,
                        arrival,
                        place,
                        service.source,
                    )
        return Uncheckable(
            f"missing_travel_metric: no canon route from {origin} to {destination}"
            f" by {sorted(allowed)}",
            (origin, destination),
        )

    @staticmethod
    def _relax(
        best: dict[str, int],
        trail: dict[str, tuple[str, str]],
        queue: list[tuple[int, str]],
        place: str,
        time: int,
        previous: str,
        source: str,
    ) -> None:
        if time < best.get(place, time + 1):
            best[place] = time
            trail[place] = (previous, source)
            heapq.heappush(queue, (time, place))

    @staticmethod
    def _sources(trail: dict[str, tuple[str, str]], destination: str) -> tuple[str, ...]:
        sources: list[str] = []
        place = destination
        while place in trail:
            place, source = trail[place]
            sources.append(source)
        return tuple(reversed(sources))


@dataclass(frozen=True)
class ClosureGap:
    """A declared direct time longer than the closure (the L1 WARNING, RC-L1-3A)."""

    travel: Travel
    source: str
    closure_minutes: int


@dataclass(frozen=True)
class SpeedBreach:
    """A declared time shorter than the speed rule allows (the L1 ERROR, RC-L1-3B)."""

    travel: Travel
    source: str
    minimum_minutes: float
    distance_source: str
    speed_source: str


def closure_gaps(network: TravelNetwork, travels: Iterable[tuple[Travel, str]]) -> list[ClosureGap]:
    gaps = []
    closures = {mode: network.closure(mode) for mode in network.modes()}
    for travel, source in travels:
        shortest = closures.get(travel.mode, {}).get((travel.origin, travel.destination))
        if shortest is not None and shortest < travel.minutes:
            gaps.append(ClosureGap(travel, source, shortest))
    return gaps


def speed_breaches(
    travels: Iterable[tuple[Travel, str]],
    distances: Iterable[tuple[Distance, str]],
    speeds: Iterable[tuple[Speed, str]],
) -> tuple[list[SpeedBreach], list[Uncheckable]]:
    """Breaches, and the travel declarations that cannot be checked for want of data."""
    by_pair: dict[frozenset[str], tuple[Distance, str]] = {}
    for distance, source in distances:
        by_pair[frozenset((distance.origin, distance.destination))] = (distance, source)
    by_mode = {speed.mode: (speed, source) for speed, source in speeds}
    breaches: list[SpeedBreach] = []
    unchecked: list[Uncheckable] = []
    for travel, source in travels:
        declared = by_pair.get(frozenset((travel.origin, travel.destination)))
        limit = by_mode.get(travel.mode)
        if declared is None:
            unchecked.append(Uncheckable(f"missing_distance: {source} has no distance", (source,)))
            continue
        if limit is None:
            unchecked.append(
                Uncheckable(f"missing_speed: no speed rule for {travel.mode} ({source})", (source,))
            )
            continue
        minimum = declared[0].km / limit[0].kmh * 60
        if travel.minutes < minimum:
            breaches.append(SpeedBreach(travel, source, minimum, declared[1], limit[1]))
    return breaches, unchecked


class Light(StrEnum):
    """Natural light at a story-time, from the daylight model."""

    DAYLIGHT = "DAYLIGHT"
    DARK = "DARK"


class DaylightModel:
    """First and last light per date, from ``daylight(...)`` canon statements."""

    def __init__(self, calendar: Calendar, rows: Iterable[tuple[Daylight, str]]) -> None:
        self.calendar = calendar
        self.rows: dict[object, tuple[Daylight, str]] = {}
        for row, source in rows:
            self.rows[row.day] = (row, source)

    def light_at(self, minute: int) -> Light | Uncheckable:
        day = self.calendar.date_of(minute)
        found = self.rows.get(day)
        if found is None:
            return Uncheckable(f"missing_daylight: no daylight row for {day.isoformat()}")
        row = found[0]
        clock = minute % MINUTES_PER_DAY
        return Light.DAYLIGHT if row.first_light <= clock < row.last_light else Light.DARK
