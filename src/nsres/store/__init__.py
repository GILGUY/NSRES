"""Record log, revisions, bitemporal queries, statuses, typed gates, audit chain (spec §0.7, §5.4,
§10.4-10.5). WP-020.

- ``store``: ``Store`` (projection and reads), ``GateConsole`` (the typed-gate API),
  ``EngineWriter`` (the engines' write path). DECISIONS D-012 to D-014.
- ``lifecycle``: the §5.4 record-lifecycle table as data, and ``Refusal`` reasons.
- ``log``: the two append-only JSON Lines logs and their verification.
- ``artifacts``: the content-addressed artifact store.
"""

from nsres.store.artifacts import ArtifactCorruptError, ArtifactStore
from nsres.store.lifecycle import LIFECYCLE, Refusal
from nsres.store.log import StoreCorruptError
from nsres.store.store import EngineWriter, GateConsole, GateResult, Snapshot, Store

__all__ = [
    "LIFECYCLE",
    "ArtifactCorruptError",
    "ArtifactStore",
    "EngineWriter",
    "GateConsole",
    "GateResult",
    "Refusal",
    "Snapshot",
    "Store",
    "StoreCorruptError",
]
