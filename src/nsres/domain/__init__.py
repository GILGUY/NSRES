"""Types, schemas, canonical JSON, hashing, UUIDv7 (spec §8, §10.2, B.3-B.4). WP-010.

Modules:

- ``vocab``: closed vocabularies (plan A-17).
- ``handles``: one pattern per handle prefix (spec §0.3).
- ``canonical``: canonical JSON and packet hashes (spec §8.1, plan A-14).
- ``uuid7``: UUIDv7 storage keys with an injected clock and seed (plan A-04, A-07).
- ``records``: record types and their JSON form (spec §10.2, §17.4; DECISIONS D-007 to D-011).
- ``schemas``: the packet and finding JSON Schemas (spec B.3, B.4; DECISIONS D-004).
"""
