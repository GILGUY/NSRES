"""Content-addressed artifact store (spec §10.4; plan A-05).

Packets, drafts, reports, and bundles are stored as canonical JSON under
``artifacts/sha256/<hex>.json``. The key is the hash of the bytes, so a stored artifact cannot
change without changing its key, and every read re-checks the hash.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from nsres.domain.canonical import canonical_bytes, sha256_hex

ARTIFACT_DIR = Path("artifacts") / "sha256"
_REF = re.compile(r"sha256:([0-9a-f]{64})")


class ArtifactCorruptError(Exception):
    """A stored artifact's bytes no longer match its key."""


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.directory = root / ARTIFACT_DIR

    def put(self, document: Any) -> str:
        """Store a JSON document; return its ``sha256:<hex>`` key. Storing twice is a no-op."""
        data = canonical_bytes(document)
        digest = sha256_hex(data)
        path = self.directory / f"{digest}.json"
        if not path.exists():
            self.directory.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".partial")
            with partial.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            partial.replace(path)
        return f"sha256:{digest}"

    def get(self, ref: str) -> Any:
        match = _REF.fullmatch(ref)
        if match is None:
            raise ValueError(f"{ref!r} is not a sha256: reference")
        path = self.directory / f"{match.group(1)}.json"
        data = path.read_bytes()
        if sha256_hex(data) != match.group(1):
            raise ArtifactCorruptError(f"{path} does not match its key")
        return json.loads(data)

    def __contains__(self, ref: object) -> bool:
        if not isinstance(ref, str):
            return False
        match = _REF.fullmatch(ref)
        return match is not None and (self.directory / f"{match.group(1)}.json").exists()
