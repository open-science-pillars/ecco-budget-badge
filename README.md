# ecco-budget-badge

![ecco heat budget](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/open-science-pillars/ecco-budget-badge/main/.badges/ecco-budget.json)

A checkable "closes the budget" property for any repo that computes an
ECCO heat budget. Your notebook runs the sanctioned computation and
writes a receipt; the canonical attester, carried here verbatim, checks
the receipt against the sanctioned code's hash, the verified data tree
it names, and the pass bar; a shields.io badge says "closes" or "does
not close". **The badge message is never hand-set: it is written from
the attester's verdict and nothing else.**

## The contract (OKF v0.2 Attested Computation)

The source of truth is the Attested Computation concept in the
canonical knowledge bundle:
[`knowledge/podaac/computations/ecco-heat-budget.md`](https://github.com/open-science-pillars/nasa-daac-knowledge/blob/main/knowledge/podaac/computations/ecco-heat-budget.md).
This repo carries verbatim copies of the two files that concept names,
at a recorded bundle commit, with their sha256 in
[`MANIFEST`](MANIFEST): the sanctioned computation
(`computations/ecco_heat_budget.py`) and the deterministic attester
(`attesters/budget_residual.py`). The pass bar the badge enforces
(residual_max at or below 1e-10 degC/s, residual_p999 at or below
1e-11 degC/s, absolute, pointwise) lives inside the attester, where the
concept put it; this repo never restates it as a flag, so the copy
cannot drift from the concept between releases. The badge writer,
`ecco_budget_badge.py`, runs the attester and translates its exit
status into the badge; it has no opinion of its own.

Your executor produces `receipt.json` (the sanctioned computation
emits it):

```json
{ "run_id": "...", "code_sha256": "...",
  "data": { "data_root": "...", "record": { "record": "...", "manifest_sha256": "...", "verified_utc": "...", "report_sha256": "...", "granules": 144 } },
  "bound_parameters": {"year": 2010, "region": "tile1-interior"},
  "residual_max": 5.0e-11, "residual_p999": 7.3e-12, "cells_evaluated": 3341772 }
```

The attester checks, deterministically, with no network and no LLM:

- every declared receipt field is present;
- `code_sha256` equals the sha256 of the sanctioned computation (a
  rewritten or swapped computation fails mechanically);
- `data.record` is the `RECORD.json` stamp the bundle's verify tool
  leaves in a data tree it has checked against its manifest (nothing
  is attested against unmanifested data);
- `bound_parameters` match the declared set (`year`, integer,
  required; `region`, string, optional); values are bound, parameters
  are never added;
- both residuals sit within the pass bar.

Exit 0 on PASS, 1 on FAIL with the failing field named, 2 when a file
cannot be found.

## Adopt it

1. Have your budget run write `receipt.json` (run the sanctioned
   `computations/ecco_heat_budget.py` with your `--year`/`--region`
   against a data tree the bundle's verify tool has stamped; it emits
   the receipt itself, so the hash and the tree bind automatically).
2. Add the workflow from [`ci/badge-workflow.yml`](ci/badge-workflow.yml)
   to your repo, pinning this repo **by tag** (`--branch v2`).
3. Commit or publish the badge JSON (for example `.badges/ecco-budget.json`
   on your default branch or gh-pages) and put the badge line in your
   README:

```markdown
![ecco heat budget](https://img.shields.io/endpoint?url=<raw URL to your .badges/ecco-budget.json>)
```

Run it locally the same way:

```bash
uv run ecco_budget_badge.py receipt.json \
  --badge .badges/ecco-budget.json --label "ecco heat budget"
```

The badge on this README is the verdict of that command on a receipt
from the sanctioned computation over the bundle's stamped 2010 fixture
tree, re-run at each release.

## Why this exists

ECCO's own documentation warns, in capitals, that budgets close only
with the exact native-grid formulation. This repo turns that warning
into a property a repo can prove per run: the formulation is the
sanctioned file (hash-checked), the pass bar is the one the
steward-signed concept's attester carries, the data tree is one the
bundle has manifested and verified, and the verdict is machine-written.
A one-character change to the computation, a residual over the bar, or
an unstamped tree flips the badge to "does not close".

## Contributing

Apache-2.0. Sign off every commit (DCO, `git commit -s`). Pass bar,
attester or computation changes land in the canonical bundle first;
this repo only mirrors them at tagged releases with the MANIFEST
updated, and the badge is re-run on the release's receipt.
