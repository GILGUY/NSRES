# Protocols

Interfaces that more than one package depends on. Each section names its spec source and the
package that defines it. A named empty section is a visible obligation; it is filled when its
package closes, and changing it afterwards needs a `DECISIONS.md` entry first.

## P-1 Gate API

`decide(gate, record, outcome, actor, reason)` — the only way to change a record's status.
Gates and outcomes exactly as spec §0.7: PROPOSAL (ACCEPT, REVISE, REJECT, SLUSH), STRUCTURE
(ACCEPT, REVISE, REJECT), INTEGRATION (ACCEPT, REVISE, REJECT), CANON (CANONIZE, REVISE,
REJECT; micro-facts ACCEPT_AND_REGISTER, REJECT_MICRO_FACT), SHIP (SHIP, HOLD). Every call
writes a gate record and an audit record. Defined in WP-020.

## P-2 Record log line format

One canonical-JSON record revision per line (A-05, A-14). Defined in WP-010 (serialization)
and WP-020 (log).

## P-3 Audit chain

Each audit line carries the SHA-256 of the previous line. Defined in WP-020.

## P-4 Finding

The B.4 finding schema, including REQ-9.1.1 and REQ-9.1.2. Defined in WP-010; produced by
the rule registry from WP-030.

## P-5 Confidence vector

The §10.2 `ConfidenceVector` shape and the §9.6 and §11.5 scoring contract. Defined in WP-040.

## P-6 Scene packet and compiled brief

The B.3 packet schema with every `$defs` written out; the brief compiler's output (§8.5).
Defined in WP-010 (schema) and WP-140 (assembly and compilation).

## P-7 AI role ports

`typing.Protocol` interfaces for the §10.12 roles; v0.1 ships fixture adapters only (A-13).
Defined as each role is first needed, from WP-130.

## P-8 CLI

`nsres` subcommands and exit codes: 0 READY, 1 PROVISIONAL or INSUFFICIENT, 2 UNSTABLE or
FAILED, 3 contract violation (plan WP-190). WP-000 ships `--version` only.

## P-9 WCS crosswalk

The spec §0.7 state, gate, and decision tables as data, with the REQ-12.2.2 import rules.
No I/O in v0.1 (OQ-8). Defined in WP-020.
