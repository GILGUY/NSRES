"""UUIDv7 storage keys (spec §0.3; plan A-04, A-07; RFC 9562 §5.7, §6.2)."""

from __future__ import annotations

import random
import uuid

import pytest

from nsres.domain.uuid7 import Uuid7Generator, timestamp_ms


class Clock:
    """An injected clock that returns scripted millisecond values."""

    def __init__(self, *values: int) -> None:
        self._values = list(values)
        self.last = values[0]

    def __call__(self) -> int:
        if self._values:
            self.last = self._values.pop(0)
        return self.last


def test_values_sort_in_injected_time_order() -> None:
    times = [1_700_000_000_000 + step * 37 for step in range(200)]
    generator = Uuid7Generator(Clock(*times), seed=7)
    generated = [generator.new_str() for _ in times]
    shuffled = generated[:]
    random.Random(1).shuffle(shuffled)
    assert sorted(shuffled) == generated
    assert [timestamp_ms(value) for value in generated] == times


def test_values_within_one_millisecond_keep_generation_order() -> None:
    generator = Uuid7Generator(Clock(1_700_000_000_000), seed=3)
    generated = [generator.new_str() for _ in range(5000)]
    assert generated == sorted(generated)
    assert len(set(generated)) == len(generated)


def test_a_clock_that_goes_backwards_never_breaks_ordering() -> None:
    generator = Uuid7Generator(Clock(5_000, 4_000, 4_000, 6_000, 1_000), seed=0)
    generated = [generator.new_str() for _ in range(5)]
    assert generated == sorted(generated)
    assert timestamp_ms(generated[1]) == 5_000


def test_layout_is_version_7_with_the_rfc_variant() -> None:
    value = Uuid7Generator(Clock(1_729_879_320_000), seed=1).new()
    assert value.version == 7
    assert value.variant == uuid.RFC_4122
    assert timestamp_ms(value) == 1_729_879_320_000


def test_same_seed_and_clock_give_the_same_sequence() -> None:
    first = Uuid7Generator(Clock(10, 10, 11), seed=42)
    second = Uuid7Generator(Clock(10, 10, 11), seed=42)
    assert [first.new_str() for _ in range(3)] == [second.new_str() for _ in range(3)]


def test_timestamps_outside_48_bits_are_refused() -> None:
    with pytest.raises(ValueError, match="48 bits"):
        Uuid7Generator(Clock(1 << 48)).new()
    with pytest.raises(ValueError, match="48 bits"):
        Uuid7Generator(Clock(-1)).new()


def test_timestamp_of_a_non_v7_uuid_is_refused() -> None:
    with pytest.raises(ValueError, match="not a UUIDv7"):
        timestamp_ms(uuid.UUID("12345678-1234-4234-8234-123456789abc"))
