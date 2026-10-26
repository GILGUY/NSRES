# NSRES

Narrative State Reconciliation Engine: the reference implementation of NSRES-SPEC v0.1.1
(`docs/spec/NSRES-SPEC.md`).

NSRES keeps a long-form story's reality, its telling, and its rendering in one reconciled model,
and compiles per-scene packets that a drafter writes from. The model proposes, deterministic
engines verify, and a human commits through typed gates.

Status: under construction. Work is tracked package by package; the current position is in
`docs/IMPLEMENTATION_STATUS.md`.

## Quickstart (developers)

```
uv sync --frozen
uv run python scripts/gate.py
uv run nsres --version
```

## Where things are

| Path | What it holds |
| --- | --- |
| `docs/IMPLEMENTATION_STATUS.md` | Where work stopped and the next exact action. Read this first |
| `docs/IMPLEMENTATION_PLAN.md` | Scope, architecture, work packages, and the verification gate |
| `docs/DECISIONS.md` | Architecture decisions, gate decisions, deviations, environment facts |
| `docs/TEST_EVIDENCE.md` | Append-only record of every command run to close each package |
| `docs/spec/NSRES-SPEC.md` | The specification (exported from the controlling doc) |
| `src/nsres/` | The package |
| `fixtures/` | Test fixtures and golden outputs |
