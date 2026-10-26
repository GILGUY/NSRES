#!/usr/bin/env python3
"""Factorized, auditable, action-gating confidence scoring. No dependencies."""

import json
import sys
from typing import Any, Dict, List, Tuple

BANDS: List[Tuple[float, str, str]] = [
    (0.95, "ACT", "Act without further context."),
    (0.85, "ACT_QUEUED", "Act with a plan-queue entry; flag residual factors."),
    (0.70, "PROPOSE_ONLY", "Propose only. Gather the named missing evidence before acting."),
    (0.00, "BLOCKED", "Do not act. State the gap, the failed factor, and the test that would raise it."),
]

WEAK_EVIDENCE = {"FOUND_BY_METADATA", "FOUND_BY_SNIPPET", "CLAIM_INFERRED", "NOT_FOUND", "GAP_IDENTIFIED"}
STRONG_EVIDENCE = {"CONTENT_READ", "CLAIM_CONFIRMED"}
HARD_CAP_NAMES = {"scope_compliance", "safety", "scope", "reconcile"}
EXIT = {"ACT": 0, "ACT_QUEUED": 0, "PROPOSE_ONLY": 1, "BLOCKED": 2}


class ScoreError(ValueError):
    pass


def _band(value: float) -> Tuple[str, str]:
    for lo, label, action in BANDS:
        if value >= lo:
            return label, action
    return "BLOCKED", BANDS[-1][2]


def _validate(spec: Dict[str, Any]) -> None:
    if not isinstance(spec.get("factors"), list) or not spec["factors"]:
        raise ScoreError("at least one factor is required — a score with no factors is a feeling")
    for i, f in enumerate(spec["factors"]):
        for key in ("name", "weight", "raw"):
            if key not in f:
                raise ScoreError(f"factor[{i}] missing required key '{key}'")
        if not 0.0 <= float(f["raw"]) <= 1.0:
            raise ScoreError(f"factor '{f['name']}': raw must be in [0,1], got {f['raw']}")
        if float(f["weight"]) < 0:
            raise ScoreError(f"factor '{f['name']}': weight must be non-negative")
        if not f.get("evidence"):
            raise ScoreError(
                f"factor '{f['name']}': no evidence refs. A factor with no evidence is an "
                f"opinion with a number attached — cite the source or drop the factor."
            )


def _evidence_warnings(factors: List[Dict[str, Any]]) -> List[str]:
    out = []
    for f in factors:
        refs = f.get("evidence") or []
        labels = {str(r).split(":", 1)[0].strip().upper() for r in refs}
        weak = labels & WEAK_EVIDENCE
        strong = labels & STRONG_EVIDENCE
        raw = float(f["raw"])
        if weak and not strong and raw > 0.85:
            out.append(
                f"factor '{f['name']}' scores {raw:.2f} on {'/'.join(sorted(weak))} evidence only — "
                f"metadata-grade evidence cannot support a >0.85 factor; re-read the source or lower the raw."
            )
        if not labels & (WEAK_EVIDENCE | STRONG_EVIDENCE):
            out.append(
                f"factor '{f['name']}' evidence refs carry no substrate-intake label "
                f"(CONTENT_READ / FOUND_BY_METADATA / ...) — unlabeled evidence silently reads as strong."
            )
    return out


def compute(spec: Dict[str, Any]) -> Dict[str, Any]:
    _validate(spec)
    factors = spec["factors"]
    total_weight = sum(float(f["weight"]) for f in factors)
    if total_weight <= 0:
        raise ScoreError("total weight is zero")

    contributions = []
    weighted_sum = 0.0
    for f in factors:
        w, r = float(f["weight"]), float(f["raw"])
        c = w * r
        weighted_sum += c
        contributions.append({
            "name": f["name"], "category": f.get("category", ""),
            "weight": w, "normalized_weight": w / total_weight, "raw": r,
            "contribution": c, "normalized_contribution": c / total_weight,
            "evidence": f.get("evidence", []), "reason": f.get("reason", ""),
        })

    base = weighted_sum / total_weight
    penalties = spec.get("conflict_penalties", []) or []
    penalty_total = sum(float(p.get("amount", 0)) for p in penalties)
    after_penalty = max(0.0, base - penalty_total)

    applied_caps = []
    final = after_penalty
    for cap in (spec.get("caps", []) or []):
        cv = float(cap.get("value", 1.0))
        if cv < final:
            applied_caps.append({
                "name": cap.get("name", "unnamed"), "value": cv,
                "reason": cap.get("reason", ""),
                "hard": cap.get("name", "").lower() in HARD_CAP_NAMES,
            })
            final = cv

    label, action = _band(final)
    weakest = min(contributions, key=lambda c: c["raw"])
    return {
        "score_name": spec.get("score_name", "unnamed_score"),
        "base_weighted": round(base, 4), "penalty_total": round(penalty_total, 4),
        "after_penalties": round(after_penalty, 4), "final": round(final, 4),
        "band": label, "required_next_action": action, "factors": contributions,
        "conflict_penalties": penalties, "caps_applied": applied_caps,
        "weakest_factor": weakest["name"], "weakest_raw": weakest["raw"],
        "warnings": _evidence_warnings(factors), "capped": bool(applied_caps),
    }


def render(result: Dict[str, Any]) -> str:
    L = [f"SCORE: {result['score_name']} = {result['final']:.2f}", "FACTORS:"]
    for f in sorted(result["factors"], key=lambda x: -x["normalized_contribution"]):
        L.append(f"  {f['name']} | {f['category'] or '-'} | weight {f['weight']:.2f} "
                 f"| raw {f['raw']:.2f} | contribution {f['normalized_contribution']:.3f}")
        if f["evidence"]:
            L.append(f"      evidence: {'; '.join(str(e) for e in f['evidence'])}")
        if f["reason"]:
            L.append(f"      reason: {f['reason']}")

    if result["conflict_penalties"]:
        L.append("CONFLICT PENALTIES:")
        for p in result["conflict_penalties"]:
            L.append(f"  -{float(p.get('amount', 0)):.2f}  {p.get('name', '')} — {p.get('reason', '')}")
    else:
        L.append("CONFLICT PENALTIES: none")

    if result["caps_applied"]:
        L.append("CAPS APPLIED:")
        for c in result["caps_applied"]:
            L.append(f"  {'HARD CAP' if c['hard'] else 'cap'} {c['name']} = {c['value']:.2f} — {c['reason']}")
        L.append(f"  (base was {result['after_penalties']:.2f}; the cap is the binding constraint)")
    else:
        L.append("CAPS APPLIED: none")

    L.append(f"THRESHOLD RESULT: {result['band']}")
    L.append(f"REQUIRED NEXT ACTION: {result['required_next_action']}")
    if result["capped"]:
        b = result["caps_applied"][-1]
        L.append(f"FIX FIRST: the {b['name']} cap ({b['value']:.2f}). It is the binding constraint — "
                 f"no factor improvement moves the score until it clears.")
        L.append(f"  (weakest factor is {result['weakest_factor']} at raw {result['weakest_raw']:.2f}, "
                 f"but fixing it changes nothing while the cap holds)")
    else:
        L.append(f"FIX FIRST: {result['weakest_factor']} (raw {result['weakest_raw']:.2f}) — weakest factor")

    if result["warnings"]:
        L.append("WARNINGS:")
        for w in result["warnings"]:
            L.append(f"  ! {w}")
    return "\n".join(L)


def main(argv: List[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 3
    try:
        if argv[1] == "-":
            spec = json.load(sys.stdin)
        else:
            with open(argv[1], "r", encoding="utf-8") as fh:
                spec = json.load(fh)
        result = compute(spec)
    except ScoreError as e:
        print(f"CONTRACT VIOLATION: {e}", file=sys.stderr)
        return 3
    except (OSError, json.JSONDecodeError) as e:
        print(f"INPUT ERROR: {e}", file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2) if "--json" in argv else render(result))
    return EXIT.get(result["band"], 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
