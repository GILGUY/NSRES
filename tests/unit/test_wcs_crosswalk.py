"""The §0.7 WCS crosswalk as data (DECISIONS D-016; OQ-8, OQ-9; REQ-12.2.2)."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path

import pytest

from nsres.domain.vocab import Gate, GateOutcome, Status, values
from nsres.wcs.crosswalk import (
    DECISION_ROWS,
    GATE_ROWS,
    STATE_ROWS,
    TELLING_CANON_TYPES,
    Admission,
    WcsArtifactState,
    WcsDecision,
    WcsGateType,
    decision_row,
    gate_row,
    import_decision,
    state_row,
)
from tests import spec_text as spec

ROOT = Path(__file__).resolve().parents[2]
MODULES = json.loads((ROOT / "fixtures" / "wcs" / "modules.json").read_text(encoding="utf-8"))[
    "modules"
]
PRIMARY_ARTIFACTS = sorted(module["primary_artifact"] for module in MODULES)


def _table(marker: str, column: int) -> list[str]:
    return spec.table_column(spec.section("### 0.7"), marker, column)


STATE_MARKER = "| WCS artifact state"
GATE_MARKER = "| WCS gate type"
DECISION_MARKER = "| WCS gate decision"


@pytest.mark.parametrize(
    ("vocabulary", "marker"),
    [(WcsArtifactState, STATE_MARKER), (WcsGateType, GATE_MARKER), (WcsDecision, DECISION_MARKER)],
    ids=["states", "gate types", "decisions"],
)
def test_wcs_vocabularies_equal_the_spec_tables(vocabulary: type[StrEnum], marker: str) -> None:
    names = [cell.split(":")[0] for cell in _table(marker, 0)]
    assert sorted(set(names)) == sorted(values(vocabulary))


def test_vocabulary_sizes_match_the_crosswalk_text() -> None:
    assert (len(WcsArtifactState), len(WcsGateType), len(WcsDecision)) == (11, 8, 8)


def test_modules_json_uses_only_known_states_and_gates() -> None:
    states = {state for module in MODULES for state in module["accepted_input_states"]}
    gates = {module["default_gate"] for module in MODULES}
    assert states <= set(values(WcsArtifactState))
    assert gates <= set(values(WcsGateType))
    assert set(TELLING_CANON_TYPES) <= set(PRIMARY_ARTIFACTS)
    assert len(MODULES) == 23


NO_STATUS_CELLS = {
    WcsArtifactState.RAW: "none",
    WcsArtifactState.INTAKE: "none",
    WcsArtifactState.FORK: "canon branch",
    WcsArtifactState.SHIP: "SHIP-gate outcome",
}


def test_state_rows_match_the_spec_rows() -> None:
    cells = list(zip(_table(STATE_MARKER, 0), _table(STATE_MARKER, 1), strict=True))
    assert len(cells) == len(STATE_ROWS) == 12
    for row, (wcs_cell, nsres_cell) in zip(STATE_ROWS, cells, strict=True):
        assert wcs_cell.startswith(row.wcs_state.value), (row, wcs_cell)
        if row.nsres_status is None:
            assert nsres_cell.startswith(NO_STATUS_CELLS[row.wcs_state]), (row, nsres_cell)
        else:
            assert nsres_cell.startswith(row.nsres_status.value), (row, nsres_cell)
        assert row.structure_locked == ("structure-locked" in nsres_cell)
        assert row.next_rev == ("next `rev`" in nsres_cell)
        assert row.successor_required == ("successor" in nsres_cell)


def test_gate_rows_match_the_spec_rows() -> None:
    cells = list(zip(_table(GATE_MARKER, 0), _table(GATE_MARKER, 1), strict=True))
    assert len(cells) == len(GATE_ROWS) == 8
    for row, (wcs_cell, nsres_cell) in zip(GATE_ROWS, cells, strict=True):
        assert wcs_cell == row.wcs_gate.value
        if row.nsres_gate is None:
            assert nsres_cell.startswith(("none", "the REJECT outcome")), nsres_cell
        else:
            assert nsres_cell.split(",")[0].split()[0] == row.nsres_gate.value, nsres_cell
        assert row.reject_at_holding_gate == nsres_cell.startswith("the REJECT outcome")
        assert row.next_rev == ("next `rev`" in nsres_cell)


def test_decision_rows_match_the_spec_rows() -> None:
    cells = list(zip(_table(DECISION_MARKER, 0), _table(DECISION_MARKER, 1), strict=True))
    assert len(cells) == len(DECISION_ROWS) == 8
    for row, (wcs_cell, nsres_cell) in zip(DECISION_ROWS, cells, strict=True):
        assert wcs_cell == row.wcs_decision.value
        mentioned = {
            outcome for outcome in GateOutcome if re.search(rf"\b{outcome.value}\b", nsres_cell)
        }
        assert set(row.nsres_outcomes) == mentioned, (row, nsres_cell)
        assert row.in_scope == ("outside the v0.1 build scope" not in nsres_cell)


@pytest.mark.parametrize("state", list(WcsArtifactState))
@pytest.mark.parametrize("artifact_type", PRIMARY_ARTIFACTS)
def test_each_state_maps_to_exactly_one_row_for_every_artifact_type(
    state: WcsArtifactState, artifact_type: str
) -> None:
    row = state_row(state, artifact_type)
    candidates = [candidate for candidate in STATE_ROWS if candidate.wcs_state is state]
    assert row in candidates
    if state is not WcsArtifactState.CANON:
        assert candidates == [row]


@pytest.mark.parametrize("gate", list(WcsGateType))
def test_each_gate_type_maps_to_exactly_one_row(gate: WcsGateType) -> None:
    assert [row for row in GATE_ROWS if row.wcs_gate is gate] == [gate_row(gate)]


@pytest.mark.parametrize("decision", list(WcsDecision))
def test_each_decision_maps_to_exactly_one_row(decision: WcsDecision) -> None:
    assert [row for row in DECISION_ROWS if row.wcs_decision is decision] == [
        decision_row(decision)
    ]


@pytest.mark.parametrize("state", [WcsArtifactState.RAW, WcsArtifactState.INTAKE])
@pytest.mark.parametrize("artifact_type", PRIMARY_ARTIFACTS)
def test_raw_and_intake_material_is_refused(state: WcsArtifactState, artifact_type: str) -> None:
    decision = import_decision(state, artifact_type)
    assert decision.admission is Admission.REFUSED
    assert decision.status is None
    assert "REQ-12.2.2" in decision.reason


@pytest.mark.parametrize("artifact_type", sorted(TELLING_CANON_TYPES))
def test_wcs_canon_telling_artifacts_import_as_accepted_and_structure_locked(
    artifact_type: str,
) -> None:
    decision = import_decision(WcsArtifactState.CANON, artifact_type)
    assert (decision.admission, decision.status, decision.structure_locked) == (
        Admission.RECORD,
        Status.ACCEPTED,
        True,
    )


def test_other_wcs_canon_imports_as_canon() -> None:
    decision = import_decision(WcsArtifactState.CANON, "production_bible_proposal")
    assert (decision.status, decision.structure_locked) == (Status.CANON, False)


def test_proposals_import_as_proposals_never_as_facts() -> None:
    assert import_decision(WcsArtifactState.PROPOSAL, "connection_map").status is Status.PROPOSAL
    revised = import_decision(WcsArtifactState.REVISED_PROPOSAL, "connection_map")
    assert (revised.status, revised.next_rev) == (Status.PROPOSAL, True)


def test_a_failed_validator_quarantines_the_artifact() -> None:
    decision = import_decision(WcsArtifactState.PROPOSAL, "spark_card", validator_failed=True)
    assert decision.admission is Admission.REFUSED
    assert "quarantined" in decision.reason


def test_superseded_needs_a_successor_and_maps_to_deprecated() -> None:
    assert (
        import_decision(WcsArtifactState.SUPERSEDED, "story_spine").admission is Admission.REFUSED
    )
    decision = import_decision(
        WcsArtifactState.SUPERSEDED, "story_spine", successor="wcs_story_spine_01"
    )
    assert decision.status is Status.DEPRECATED


def test_fork_is_out_of_scope_and_ship_is_a_gate_outcome() -> None:
    assert import_decision(WcsArtifactState.FORK, "story_spine").admission is Admission.REFUSED
    assert (
        import_decision(WcsArtifactState.SHIP, "final_cut_decision").admission
        is Admission.GATE_OUTCOME
    )


def test_gate_and_decision_mappings() -> None:
    assert gate_row(WcsGateType.CANON_GATE).nsres_gate is Gate.CANON
    assert gate_row(WcsGateType.INTAKE_GATE).nsres_gate is None
    assert gate_row(WcsGateType.DELETE_GATE).reject_at_holding_gate
    assert gate_row(WcsGateType.REVISION_GATE).next_rev
    assert decision_row(WcsDecision.ACCEPT_AS_CANON).nsres_outcomes == (
        GateOutcome.ACCEPT,
        GateOutcome.CANONIZE,
    )
    assert decision_row(WcsDecision.REDIRECT).nsres_outcomes == ()
    assert not decision_row(WcsDecision.FORK).in_scope
