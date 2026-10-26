"""Structured canon statements, the calendar, and the parser (DECISIONS D-017).

``CanonRule.statement_structured`` may hold several statements separated by ``;``. A statement
in one of the recognized forms is parsed into a typed value; anything else is kept as text
for later engines. A recognized form with bad arguments raises ``StatementError``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from nsres.domain import handles

MINUTES_PER_DAY = 24 * 60
_CALL = re.compile(r"\s*([a-z_]+)\((.*)\)\s*", re.S)
_CLOCK = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")
_MODE = re.compile(r"[a-z][a-z_]*")
_STORY_TIME = re.compile(r"(\d{4}-\d{2}-\d{2})T([01]\d|2[0-3]):([0-5]\d)")


class StatementError(ValueError):
    """A recognized statement form with arguments that do not fit it."""


class Calendar:
    """Story-time as integer minutes from a per-work epoch, Gregorian display (plan A-09)."""

    def __init__(self, epoch: date) -> None:
        self.epoch = epoch
        self._origin = datetime(epoch.year, epoch.month, epoch.day)

    def minutes(self, text: str) -> int:
        """``YYYY-MM-DDTHH:MM`` to minutes from the epoch."""
        match = _STORY_TIME.fullmatch(text)
        if match is None:
            raise ValueError(f"{text!r} is not YYYY-MM-DDTHH:MM")
        day = date.fromisoformat(match.group(1))
        return self.day_start(day) + int(match.group(2)) * 60 + int(match.group(3))

    def day_start(self, day: date) -> int:
        return (day - self.epoch).days * MINUTES_PER_DAY

    def date_of(self, minute: int) -> date:
        return self.epoch + timedelta(days=minute // MINUTES_PER_DAY)

    def display(self, minute: int) -> str:
        return (self._origin + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M")


def clock_minutes(text: str) -> int:
    """``HH:MM`` to minutes after midnight."""
    match = _CLOCK.fullmatch(text.strip())
    if match is None:
        raise StatementError(f"{text!r} is not a clock time HH:MM")
    return int(match.group(1)) * 60 + int(match.group(2))


@dataclass(frozen=True)
class Travel:
    origin: str
    destination: str
    mode: str
    minutes: int
    oneway: bool = False


@dataclass(frozen=True)
class Distance:
    origin: str
    destination: str
    km: float


@dataclass(frozen=True)
class Speed:
    mode: str
    kmh: float


@dataclass(frozen=True)
class TimetableEntry:
    """A daily departure. ``arrive`` is minutes after midnight; at or before ``depart`` means
    the next day."""

    origin: str
    destination: str
    mode: str
    depart: int
    arrive: int

    @property
    def duration(self) -> int:
        return (self.arrive - self.depart) % MINUTES_PER_DAY or MINUTES_PER_DAY


@dataclass(frozen=True)
class Daylight:
    day: date
    first_light: int
    last_light: int


@dataclass(frozen=True)
class Disambiguation:
    first: str
    second: str
    name: str


Statement = Travel | Distance | Speed | TimetableEntry | Daylight | Disambiguation

RECOGNIZED = ("travel", "distance", "speed", "timetable", "daylight", "disambiguate")
METRIC_FORMS = ("travel", "distance", "speed", "timetable", "daylight")


def _arguments(body: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quoted = False
    for char in body:
        if char == '"':
            quoted = not quoted
            current.append(char)
        elif char == "," and not quoted:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if quoted:
        raise StatementError("unterminated quotation")
    parts.append("".join(current).strip())
    return parts


def _place(value: str) -> str:
    if not handles.is_handle("LOC", value):
        raise StatementError(f"{value!r} is not a location handle")
    return value


def _mode(value: str) -> str:
    if _MODE.fullmatch(value) is None:
        raise StatementError(f"{value!r} is not a travel mode name")
    return value


def _positive(value: str, what: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise StatementError(f"{what} {value!r} is not a number") from error
    if number <= 0:
        raise StatementError(f"{what} {value!r} must be positive")
    return number


def _count(name: str, args: list[str], *allowed: int) -> None:
    if len(args) not in allowed:
        raise StatementError(
            f"{name}() takes {' or '.join(map(str, allowed))} arguments, not {len(args)}"
        )


def parse_one(text: str) -> Statement | str:
    """Parse one statement; return the text unchanged if it is not a recognized form."""
    match = _CALL.fullmatch(text)
    if match is None or match.group(1) not in RECOGNIZED:
        return text.strip()
    name, args = match.group(1), _arguments(match.group(2))
    if name == "travel":
        _count(name, args, 4, 5)
        if len(args) == 5 and args[4] != "oneway":
            raise StatementError(f"travel() fifth argument must be 'oneway', not {args[4]!r}")
        minutes = _positive(args[3], "minutes")
        if not minutes.is_integer():
            raise StatementError(f"travel minutes {args[3]!r} must be whole")
        return Travel(
            _place(args[0]), _place(args[1]), _mode(args[2]), int(minutes), len(args) == 5
        )
    if name == "distance":
        _count(name, args, 3)
        return Distance(_place(args[0]), _place(args[1]), _positive(args[2], "km"))
    if name == "speed":
        _count(name, args, 2)
        return Speed(_mode(args[0]), _positive(args[1], "km/h"))
    if name == "timetable":
        _count(name, args, 5)
        depart, arrive = clock_minutes(args[3]), clock_minutes(args[4])
        return TimetableEntry(_place(args[0]), _place(args[1]), _mode(args[2]), depart, arrive)
    if name == "daylight":
        _count(name, args, 3)
        try:
            day = date.fromisoformat(args[0])
        except ValueError as error:
            raise StatementError(f"{args[0]!r} is not a date YYYY-MM-DD") from error
        first, last = clock_minutes(args[1]), clock_minutes(args[2])
        if first >= last:
            raise StatementError(f"first light {args[1]} is not before last light {args[2]}")
        return Daylight(day, first, last)
    _count(name, args, 3)
    one, other, label = args
    for value in (one, other):
        if handles.prefix_of(value) not in ("CHR", "LOC", "OBJ", "GRP"):
            raise StatementError(f"{value!r} is not an entity handle")
    if len(label) < 3 or not (label.startswith('"') and label.endswith('"')):
        raise StatementError(f"disambiguate() name {label!r} must be quoted")
    return Disambiguation(one, other, label[1:-1])


def parse_all(text: str) -> list[Statement | str]:
    """Every ``;``-separated statement in a structured statement field (quotes respected)."""
    pieces: list[str] = []
    current: list[str] = []
    quoted = False
    for char in text:
        if char == '"':
            quoted = not quoted
        if char == ";" and not quoted:
            pieces.append("".join(current))
            current = []
        else:
            current.append(char)
    pieces.append("".join(current))
    return [parse_one(piece) for piece in pieces if piece.strip()]


def form_of(text: str) -> str | None:
    """The recognized form name of a statement, or None."""
    match = _CALL.fullmatch(text)
    return match.group(1) if match is not None and match.group(1) in RECOGNIZED else None
