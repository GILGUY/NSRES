"""Identity collisions (spec L1 contradiction detection item 2; DECISIONS D-018).

Two entities collide when they share a canonical name or alias, compared case-insensitively
with whitespace collapsed, unless a ``disambiguate(...)`` canon statement covers the pair and
the name.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from nsres.canon.statements import Disambiguation
from nsres.domain.records import Entity


def normalize(name: str) -> str:
    return " ".join(name.casefold().split())


@dataclass(frozen=True)
class Collision:
    name: str
    first: str
    second: str


def collisions(
    entities: Iterable[Entity], disambiguations: Iterable[Disambiguation]
) -> list[Collision]:
    allowed = {
        (normalize(item.name), frozenset((item.first, item.second))) for item in disambiguations
    }
    holders: dict[str, list[str]] = {}
    for entity in sorted(entities, key=lambda e: e.handle):
        names = {normalize(entity.canonical_name), *(normalize(alias) for alias in entity.aliases)}
        for name in sorted(names):
            holders.setdefault(name, []).append(entity.handle)
    found = []
    for name in sorted(holders):
        handles = holders[name]
        for index, first in enumerate(handles):
            for second in handles[index + 1 :]:
                if (name, frozenset((first, second))) not in allowed:
                    found.append(Collision(name, first, second))
    return found
