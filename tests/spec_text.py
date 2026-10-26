"""Read the exported spec for tests that check code against the spec text itself.

The spec is ``docs/spec/NSRES-SPEC.md`` (rev 126, DECISIONS D-003). These helpers locate a
section, a TypeScript declaration, a YAML enum, or a table column, and fail loudly when the
text they expect is missing, so a spec edit that moves something breaks the test instead of
silently emptying it.
"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "spec" / "NSRES-SPEC.md"


@cache
def spec_text() -> str:
    """The spec with Markdown escapes removed (``NOT\\_APPLICABLE`` becomes ``NOT_APPLICABLE``)."""
    raw = SPEC.read_text(encoding="utf-8")
    return re.sub(r"\\([_\[\]<>`*])", r"\1", raw)


def section(heading: str) -> str:
    """Text from the line starting with ``heading`` up to the next heading of equal or higher
    level."""
    text = spec_text()
    match = re.search(rf"^{re.escape(heading)}.*$", text, re.M)
    if match is None:
        raise AssertionError(f"spec heading {heading!r} not found")
    level = len(heading) - len(heading.lstrip("#"))
    rest = text[match.end() :]
    end = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return text[match.start() : match.end() + (end.start() if end else len(rest))]


def fenced(block_of: str, language: str) -> str:
    """The first fenced code block of ``language`` inside ``block_of``."""
    match = re.search(rf"```{language}\n(.*?)```", block_of, re.S)
    if match is None:
        raise AssertionError(f"no ```{language} block found")
    return match.group(1)


def typescript() -> str:
    return fenced(section("### 10.2"), "typescript")


def ts_type(name: str) -> list[str]:
    """String literals of ``type <name> = 'A' | 'B';``."""
    match = re.search(rf"^type {name} =(.*?);", typescript(), re.M | re.S)
    if match is None:
        raise AssertionError(f"TypeScript type {name} not found")
    return _literals(match.group(1))


def ts_interface(name: str) -> str:
    match = re.search(rf"^interface {name}\b[^{{]*\{{(.*?)^\}}", typescript(), re.M | re.S)
    if match is None:
        raise AssertionError(f"TypeScript interface {name} not found")
    return match.group(1)


def ts_field(interface: str, field: str) -> list[str]:
    """String literals of one field of an interface (``field?: 'A' | { ... } | 'B';``)."""
    match = re.search(rf"\b{field}\??:\s*([^;]+);", ts_interface(interface))
    if match is None:
        raise AssertionError(f"field {field} not found in interface {interface}")
    literals = _literals(match.group(1))
    if not literals:
        raise AssertionError(f"field {interface}.{field} has no string literals")
    return literals


def ts_effect_ops() -> list[str]:
    match = re.search(r"^type Effect =(.*?)\n\n", typescript(), re.M | re.S)
    if match is None:
        raise AssertionError("TypeScript type Effect not found")
    ops: list[str] = []
    for variant in re.findall(r"op: ([^;]+);", match.group(1)):
        ops += _literals(variant)
    return ops


def ts_effect_at() -> list[str]:
    match = re.search(r"\bat: ((?:'[A-Z]+' \| )+)\{", typescript())
    if match is None:
        raise AssertionError("Effect.at not found")
    return _literals(match.group(1))


def ts_inline(interface: str, field: str) -> list[str]:
    """Literals of a field inside an inline object type, e.g. ``participants: { role: ... }``."""
    match = re.search(rf"\b{field}:\s*((?:'[^']+'\s*\|?\s*)+)", ts_interface(interface))
    if match is None:
        raise AssertionError(f"inline field {field} not found in interface {interface}")
    return _literals(match.group(1))


def yaml_enum(block_of: str, key: str) -> list[str]:
    """Values of ``key: { enum: [A, B, ...] }`` in a YAML block (may span lines)."""
    match = re.search(rf"\b{key}:\s*\{{\s*enum:\s*\[([^\]]+)\]", block_of, re.S)
    if match is None:
        raise AssertionError(f"YAML enum for {key!r} not found")
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def yaml_required_lists(block_of: str) -> list[list[str]]:
    """Every ``required: [...]`` list in a YAML block, in order of appearance."""
    lists = re.findall(r"\brequired:\s*\[([^\]]+)\]", block_of, re.S)
    return [[item.strip() for item in found.split(",") if item.strip()] for found in lists]


def b3() -> str:
    return fenced(section("### B.3"), "yaml")


def b4() -> str:
    return fenced(section("### B.4"), "yaml")


def table_column(block_of: str, after: str, column: int = 0) -> list[str]:
    """One column of the first Markdown table that follows the text ``after``."""
    start = block_of.find(after)
    if start < 0:
        raise AssertionError(f"marker {after!r} not found")
    rows: list[str] = []
    in_table = False
    for line in block_of[start:].splitlines():
        if line.startswith("|"):
            in_table = True
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append(cells[column])
        elif in_table:
            break
    if len(rows) < 3:
        raise AssertionError(f"no table found after {after!r}")
    return rows[2:]  # drop the header row and the separator row


def listed(pattern: str, block_of: str | None = None) -> list[str]:
    """Words captured by ``pattern``'s first group, split on commas, "or", "and", ";"."""
    text = spec_text() if block_of is None else block_of
    match = re.search(pattern, text)
    if match is None:
        raise AssertionError(f"pattern {pattern!r} not found in the spec")
    parts = re.split(r",|;|\bor\b|\band\b", match.group(1))
    return [part.strip() for part in parts if part.strip()]


def json_example(heading: str) -> Any:
    return json.loads(fenced(section(heading), "json"))


def _literals(fragment: str) -> list[str]:
    return re.findall(r"'([^']+)'", fragment)
