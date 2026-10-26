"""Canonical JSON and SHA-256 hashing (spec §8.1, plan A-14).

Canonical form: UTF-8, object keys sorted by code point, no insignificant whitespace, and
numbers in shortest round-trip form. A float with an integral value is written as an integer
(``1.0`` becomes ``1``), as in RFC 8785, so the bytes do not depend on whether a producer
happened to compute a whole number as a float. NaN and infinities are refused, as are
non-string keys. ``StrEnum`` members serialize as their values.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

_MAX_EXACT_INTEGER = 2**53


class CanonicalJSONError(ValueError):
    """The value cannot be written in canonical form."""


def _number(value: float) -> str:
    if not math.isfinite(value):
        raise CanonicalJSONError(f"non-finite number {value!r} has no canonical form")
    if value.is_integer() and abs(value) < _MAX_EXACT_INTEGER:
        return str(int(value))
    return repr(value)


def _string(value: str) -> str:
    out = ['"']
    for char in value:
        code = ord(char)
        if char == '"':
            out.append('\\"')
        elif char == "\\":
            out.append("\\\\")
        elif char == "\b":
            out.append("\\b")
        elif char == "\f":
            out.append("\\f")
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


def _write(value: Any, parts: list[str]) -> None:
    if isinstance(value, Enum):
        _write(value.value, parts)
    elif value is None:
        parts.append("null")
    elif value is True:
        parts.append("true")
    elif value is False:
        parts.append("false")
    elif isinstance(value, int):
        parts.append(str(value))
    elif isinstance(value, float):
        parts.append(_number(value))
    elif isinstance(value, str):
        parts.append(_string(value))
    elif isinstance(value, Mapping):
        keys = list(value.keys())
        for key in keys:
            if not isinstance(key, str):
                raise CanonicalJSONError(f"object key {key!r} is not a string")
        parts.append("{")
        for index, key in enumerate(sorted(keys)):
            if index:
                parts.append(",")
            parts.append(_string(key))
            parts.append(":")
            _write(value[key], parts)
        parts.append("}")
    elif isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        parts.append("[")
        for index, item in enumerate(value):
            if index:
                parts.append(",")
            _write(item, parts)
        parts.append("]")
    else:
        raise CanonicalJSONError(f"value of type {type(value).__name__} is not JSON")


def canonical_text(value: Any) -> str:
    """The canonical JSON text of ``value``."""
    parts: list[str] = []
    _write(value, parts)
    return "".join(parts)


def canonical_bytes(value: Any) -> bytes:
    """The canonical JSON of ``value``, UTF-8 encoded."""
    return canonical_text(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(value: Any) -> str:
    """``sha256:<hex>`` of the canonical form, as packets and the artifact store write it."""
    return f"sha256:{sha256_hex(canonical_bytes(value))}"


PACKET_HASH_FIELDS = ("packet_hash", "public_hash")


def packet_hashes(packet: Mapping[str, Any]) -> tuple[str, str]:
    """Return ``(packet_hash, public_hash)`` for a scene packet (spec §8.1, PK-9).

    ``public_hash`` covers the canonical ``public`` section. ``packet_hash`` covers the
    canonical whole packet with the two hash fields removed, since a hash cannot cover itself
    (DECISIONS D-006).
    """
    if "public" not in packet:
        raise CanonicalJSONError("a packet without a public section cannot be hashed")
    whole = {key: value for key, value in packet.items() if key not in PACKET_HASH_FIELDS}
    return content_hash(whole), content_hash(packet["public"])


def with_packet_hashes(packet: Mapping[str, Any]) -> dict[str, Any]:
    """A copy of the packet with both hash fields set."""
    packet_hash, public_hash = packet_hashes(packet)
    return {**packet, "packet_hash": packet_hash, "public_hash": public_hash}


def verify_packet_hashes(packet: Mapping[str, Any]) -> list[str]:
    """Problems with the packet's stored hashes; empty when both verify (PK-9)."""
    expected_packet, expected_public = packet_hashes(packet)
    problems = []
    if packet.get("packet_hash") != expected_packet:
        problems.append(f"packet_hash is {packet.get('packet_hash')!r}, expected {expected_packet}")
    if packet.get("public_hash") != expected_public:
        problems.append(f"public_hash is {packet.get('public_hash')!r}, expected {expected_public}")
    return problems
