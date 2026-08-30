# ecco-budget-badge

![ecco heat budget](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/open-science-pillars/ecco-budget-badge/main/.badges/ecco-budget.json)

A checkable "closes the budget" property for any repo that computes an
ECCO heat budget. Your notebook runs the sanctioned computation and
writes a receipt; the attester here checks the receipt against the
sanctioned code's hash and the recorded tolerances; a shields.io badge
says "closes" or "does not close". **The badge message is never
hand-set: only the attester writes it.**

## The contract (OKF v0.2 Attested Computation)

The source of truth is the Attested Computation concept in the
canonical knowledge bundle:
[`podaac/computations/ecco-heat-budget.md`](https://github.com/open-science-pillars/nasa-daac-knowledge/blob/main/podaac/computations/ecco-heat-budget.md).
This repo carries a verbatim copy of the sanctioned computation
(`computations/ecco_heat_budget.py`) at a recorded bundle commit, with
its sha256 in [`computations/MANIFEST`](computations/MANIFEST). The
tolerances the badge enforces come from that concept (residual_max at
or below 1e-10 degC/s, residual_p999 at or below 1e-11 degC/s,
absolute, pointwise); they are re-read from the concept at each
release, never edited here by hand.

Your executor produces `receipt.json`:

```json
{ "run_id": "...", "code_sha256": "...", "bound_parameters": {"year": 2010, "region": "tile1-interior"},
  "residual_max": 5.0e-11, "residual_p999": 7.3e-12, "cells_evaluated": 3341772 }
```

The attester checks, deterministically, with no network and no LLM:

- **A1** `code_sha256` equals the sha256 of the sanctioned computation
  (a rewritten or swapped computation fails mechanically),
- **A2** `bound_parameters` stay within the declared set (`year`,
  `region`); values are bound, parameters are never added,
- **A3** residuals sit within the recorded tolerances,
- **A4** a nonzero number of cells was evaluated.

Exit 0 on PASS, 1 on FAIL with the failing check named, 2 on usage
errors.

## Adopt it

1. Have your budget run write `receipt.json` (run the sanctioned
   `computations/ecco_heat_budget.py` with your `--year`/`--region`;
   it emits the receipt itself, so the hash binds automatically).
2. Add the workflow from [`ci/badge-workflow.yml`](ci/badge-workflow.yml)
   to your repo, pinning this repo **by tag** (`--branch v1`).
3. Commit or publish the badge JSON (for example `.badges/ecco-budget.json`
   on your default branch or gh-pages) and put the badge line in your
   README:

```markdown
![ecco heat budget](https://img.shields.io/endpoint?url=<raw URL to your .badges/ecco-budget.json>)
```

Run it locally the same way:

```bash
uv run ecco_budget_attest.py receipt.json \
  --computation computations/ecco_heat_budget.py \
  --tol-max 1e-10 --tol-p999 1e-11 \
  --badge .badges/ecco-budget.json --label "ecco heat budget"
```

## Why this exists

ECCO's own documentation warns, in capitals, that budgets close only
with the exact native-grid formulation. This repo turns that warning
into a property a repo can prove per run: the formulation is the
sanctioned file (hash-checked), the pass bar is the steward-signed
tolerance from the knowledge bundle, and the verdict is machine-written.
A one-character change to the computation, or a residual over the bar,
flips the badge to "does not close".

## Contributing

Apache-2.0. Sign off every commit (DCO, `git commit -s`). Tolerance or
computation changes land in the canonical bundle first; this repo only
mirrors them at tagged releases with the MANIFEST updated.
