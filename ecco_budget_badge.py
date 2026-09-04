#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""ecco_budget_badge: run the canonical attester on a receipt and write the
verdict as a shields.io endpoint JSON.

The verdict is the canonical bundle's, not this repo's: the attester
(attesters/budget_residual.py) is a verbatim copy of the file the ECCO
heat budget Attested Computation concept names, carrying the pass bar
inside it; this script only translates its exit status into a badge.
Deterministic, no network, no LLM. The badge message is never hand-set.

Usage:
  ecco_budget_badge.py receipt.json [--computation computations/ecco_heat_budget.py]
      [--attester attesters/budget_residual.py]
      [--badge .badges/ecco-budget.json] [--label "ecco heat budget"]

Exit status is the attester's: 0 on PASS, 1 on FAIL (the failing field
named on stdout), 2 when the receipt or a vendored file cannot be found.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def write_badge(path: Path | None, label: str, passing: bool) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
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
    ap.add_argument("--computation", type=Path,
                    default=HERE / "computations" / "ecco_heat_budget.py",
                    help="sanctioned computation the receipt's code_sha256 must match")
    ap.add_argument("--attester", type=Path,
                    default=HERE / "attesters" / "budget_residual.py",
                    help="the canonical attester (verbatim copy)")
    ap.add_argument("--badge", type=Path, default=None,
                    help="write a shields.io endpoint JSON here")
    ap.add_argument("--label", default="ecco heat budget")
    args = ap.parse_args()

    for p in (args.receipt, args.computation, args.attester):
        if not p.is_file():
            print(f"not found: {p}", file=sys.stderr)
            return 2

    verdict = subprocess.run(
        [sys.executable, str(args.attester), str(args.receipt),
         "--computation", str(args.computation)],
        capture_output=True, text=True)
    sys.stdout.write(verdict.stdout)
    sys.stderr.write(verdict.stderr)
    if verdict.returncode not in (0, 1):
        return 2
    write_badge(args.badge, args.label, verdict.returncode == 0)
    return verdict.returncode


if __name__ == "__main__":
    sys.exit(main())
