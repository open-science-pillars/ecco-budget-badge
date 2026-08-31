#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""ecco_budget_attest: verify that a budget-closure run used the sanctioned
computation and met the recorded tolerances, then emit the verdict and an
optional shields.io badge endpoint JSON.

The portable half of the OKF v0.2 Attested Computation contract
: the executor produces a receipt; this attester
checks it. Deterministic, no network, no LLM.

Receipt JSON (produced by the executor):
  { "run_id": str, "code_sha256": str, "bound_parameters": {..},
    "residual_max": float, "residual_p999": float, "cells_evaluated": int }

Checks:
  A1 code_sha256 matches the sha256 of --computation (the sanctioned file)
  A2 bound_parameters keys are a subset of --params-declared (agents bind
     values for declared parameters only; they never add parameters)
  A3 residual_max <= --tol-max and residual_p999 <= --tol-p999
  A4 cells_evaluated > 0

Usage:
  ecco_budget_attest.py receipt.json --computation ecco_heat_budget.py \
      --tol-max 1e-10 --tol-p999 1e-11 [--params-declared year,region] \
      [--badge badge.json] [--label "heat budget"]

Exit 0 on PASS, 1 on FAIL (failing check named), 2 on usage errors.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def fail(check: str, msg: str, badge: Path | None, label: str) -> int:
    print(f"FAIL {check}: {msg}")
    write_badge(badge, label, False)
    return 1


def write_badge(path: Path | None, label: str, passing: bool) -> None:
    if path is None:
        return
    path.write_text(json.dumps({
        "schemaVersion": 1,
        "label": label,
        "message": "closes" if passing else "does not close",
        "color": "brightgreen" if passing else "red",
    }) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receipt", type=Path)
    ap.add_argument("--computation", type=Path, required=True)
    ap.add_argument("--tol-max", type=float, required=True)
    ap.add_argument("--tol-p999", type=float, required=True)
    ap.add_argument("--params-declared", default="year,region",
                    help="comma-separated declared parameter names")
    ap.add_argument("--badge", type=Path, default=None,
                    help="write a shields.io endpoint JSON here")
    ap.add_argument("--label", default="ecco budget")
    args = ap.parse_args()

    try:
        r = json.loads(args.receipt.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"unreadable receipt: {e}", file=sys.stderr)
        return 2

    want = hashlib.sha256(args.computation.read_bytes()).hexdigest()
    if r.get("code_sha256") != want:
        return fail("A1", f"code_sha256 {str(r.get('code_sha256'))[:12]}... does not "
                    f"match sanctioned computation {want[:12]}...", args.badge, args.label)

    declared = {p.strip() for p in args.params_declared.split(",") if p.strip()}
    bound = set((r.get("bound_parameters") or {}).keys())
    extra = bound - declared
    if extra:
        return fail("A2", f"undeclared parameter(s) bound: {', '.join(sorted(extra))}",
                    args.badge, args.label)

    try:
        rmax, rp999 = float(r["residual_max"]), float(r["residual_p999"])
        cells = int(r["cells_evaluated"])
    except (KeyError, TypeError, ValueError) as e:
        print(f"receipt missing or malformed field: {e}", file=sys.stderr)
        return 2
    if rmax > args.tol_max:
        return fail("A3", f"residual_max {rmax:.3e} exceeds {args.tol_max:.1e}",
                    args.badge, args.label)
    if rp999 > args.tol_p999:
        return fail("A3", f"residual_p999 {rp999:.3e} exceeds {args.tol_p999:.1e}",
                    args.badge, args.label)
    if cells <= 0:
        return fail("A4", "no cells evaluated", args.badge, args.label)

    print(f"PASS run {r.get('run_id', '?')}: residual_max {rmax:.3e}, "
          f"p999 {rp999:.3e}, {cells} cells, sanctioned code confirmed")
    write_badge(args.badge, args.label, True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
