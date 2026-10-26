"""UUIDv7 storage keys (spec §0.3, plan A-07; RFC 9562 §5.7).

Layout: 48-bit Unix time in milliseconds, version 7, 12 bits ``rand_a``, variant ``10``,
62 bits ``rand_b``. Within one millisecond the generator increments ``rand_a`` as a counter
(RFC 9562 §6.2, method 1), so keys sort in generation order even when the clock does not
advance. The clock and the random source are injected (plan A-04): engines never read the
wall clock.
"""

from __future__ import annotations

import random
import time
import uuid
from collections.abc import Callable

_MAX_TIMESTAMP = (1 << 48) - 1
_MAX_RAND_A = (1 << 12) - 1


def wall_clock_ms() -> int:
    """Milliseconds since the Unix epoch, for production callers outside the engines."""
    return time.time_ns() // 1_000_000


class Uuid7Generator:
    """Monotonic UUIDv7 generator with an injected clock and seed."""

    def __init__(self, clock_ms: Callable[[], int], seed: int | None = None) -> None:
        self._clock_ms = clock_ms
        self._rng = random.Random(seed)
        self._last_ms = -1
        self._counter = 0

    def new(self) -> uuid.UUID:
        now = self._clock_ms()
        if not 0 <= now <= _MAX_TIMESTAMP:
            raise ValueError(f"timestamp {now} ms does not fit in 48 bits")
        if now <= self._last_ms:
            # Same millisecond, or a clock that went backwards: keep the last timestamp and
            # count up, so ordering never regresses.
            now = self._last_ms
            self._counter += 1
            if self._counter > _MAX_RAND_A:
                now += 1
                self._counter = self._rng.getrandbits(11)
        else:
            self._counter = self._rng.getrandbits(11)  # leave headroom for counting
        self._last_ms = now
        rand_b = self._rng.getrandbits(62)
        value = (now << 80) | (0x7 << 76) | (self._counter << 64) | (0b10 << 62) | rand_b
        return uuid.UUID(int=value)

    def new_str(self) -> str:
        return str(self.new())


def timestamp_ms(value: uuid.UUID | str) -> int:
    """The millisecond timestamp embedded in a UUIDv7."""
    parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
    if parsed.version != 7:
        raise ValueError(f"{parsed} is not a UUIDv7")
    return parsed.int >> 80
