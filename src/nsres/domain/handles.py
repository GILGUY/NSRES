"""Human-readable record handles (spec §0.3).

Every record has a UUIDv7 storage key and a prefixed handle. The digit widths below are
derived from the spec's own examples (one pattern per prefix, because the widths differ:
EVT-0104 but THR-02). ``tests/unit/test_handles.py`` checks every §0.3 example against its
pattern and against every other prefix's pattern.

Two groups:

- ``SPEC_PREFIXES``: the §0.3 identifier table.
- ``EXTENDED_PREFIXES``: handles the spec uses elsewhere without listing them in §0.3
  (suppression refs, anchors, confidence vectors, and the §17.4 mechanics records), plus
  ``REL-`` for the §3.3 Relation record, which the spec gives no prefix (DECISIONS D-010).

The §17.4 Resource record is written ``RES-`` in the spec, which collides with the §0.3
Resolution record. The code gives resources ``RSV-`` (DECISIONS D-005, spec erratum ERR-1).
"""

from __future__ import annotations

import re
from typing import Final

SPEC_PREFIXES: Final[dict[str, str]] = {
    "CAN": r"\d{3,}",
    "CHR": r"\d{3,}",
    "LOC": r"\d{3,}[a-z]?",
    "OBJ": r"\d{3,}",
    "GRP": r"\d{3,}",
    "EVT": r"\d{4,}",
    "INF": r"\d{3,}",
    "CLM": r"\d{3,}",
    "KG": r"\d{4,}",
    "CE": r"\d{4,}",
    "THR": r"\d{2,}",
    "NOD": r"\d{2,}-\d{2,}",
    "SCN": r"\d{3,}",
    "BT": r"\d{3,}-\d{2,}",
    "RVL": r"\d{2,}",
    "Q": r"\d{2,}",
    "PKT": r"\d{3,}-r\d+",
    "DRF": r"\d{3,}-\d{2,}",
    "FND": r"(?:\d{3,}-\d{2,}-\d{2,}|R-\d{2,})",
    "RUN": r"[RXA]-\d{4,}",
    "RES": r"\d{4,}",
}
"""Prefix → pattern for the part after ``PREFIX-`` (spec §0.3)."""

EXTENDED_PREFIXES: Final[dict[str, str]] = {
    "SUP": r"\d+",  # suppression reference in a packet's public section (§8.2 H, §8.4)
    "ANCHOR": r"\d{2,}",  # synchronization anchor (§6.3)
    "CV": r"[A-Z]+-[0-9A-Za-z-]+",  # confidence vector, named after its subject (§8.2 A)
    "SUB": r"\d{3,}",  # substrate (§17.4)
    "RGM": r"\d{3,}",  # regime (§17.4, §17.8)
    "MCH": r"\d{3,}",  # mechanic (§17.4, §17.8)
    "MCC": r"\d{3,}",  # mechanics constant (§17.4)
    "RSV": r"\d{3,}",  # resource (§17.4 writes RES-; see the module docstring)
    "CAP": r"\d{3,}",  # capability (§17.4)
    "EFF": r"\d{3,}",  # active effect (§17.4)
    "TRC": r"\d{3,}",  # trace (§17.4)
    "REL": r"\d{4,}",  # relation (§3.3 gives no prefix; DECISIONS D-010)
}

ALL_PREFIXES: Final[dict[str, str]] = {**SPEC_PREFIXES, **EXTENDED_PREFIXES}

_COMPILED: Final[dict[str, re.Pattern[str]]] = {
    prefix: re.compile(rf"{prefix}-{body}") for prefix, body in ALL_PREFIXES.items()
}


def pattern(prefix: str) -> str:
    """The anchored regular expression for one prefix, as used in the JSON Schemas."""
    return rf"^{prefix}-{ALL_PREFIXES[prefix]}$"


def is_handle(prefix: str, value: str) -> bool:
    """True if ``value`` is a well-formed handle with this prefix."""
    return _COMPILED[prefix].fullmatch(value) is not None


def prefix_of(value: str) -> str | None:
    """The prefix whose pattern ``value`` matches exactly, or None."""
    matches = [prefix for prefix, compiled in _COMPILED.items() if compiled.fullmatch(value)]
    if len(matches) > 1:  # pragma: no cover - guarded by tests/unit/test_handles.py
        raise ValueError(f"handle {value!r} matches several prefixes: {matches}")
    return matches[0] if matches else None


def one_of(*prefixes: str) -> str:
    """An anchored pattern matching a handle of any of the given prefixes."""
    alternatives = "|".join(f"{prefix}-{ALL_PREFIXES[prefix]}" for prefix in prefixes)
    return rf"^(?:{alternatives})$"
