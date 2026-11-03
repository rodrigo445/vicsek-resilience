# Changelog

## 1.0.3

- Consolidated the local results into one three-panel publication figure.
- Panel A shows the matched-`T=300`, fixed-`m=10` comparison between `N=400` and `N=1600`.
- Panels B and C show the `N=1600` perturbation-scale control for `MG -> M2` and within-state prediction.
- Retired the redundant standalone local figures from the generated final-output set.
- Updated the static results snapshot with the validated `N=400, m=10, T=300` results from the completed v1.0.2 run.
- Updated figure/table guidance and final-output review to reflect the final two-figure narrative.
- No scientific model, dataset, target definition or fitted result was changed.

## 1.0.2

- Added an explicit response-semantics audit for local scale comparisons.
- Preserved the historical `N=400, m=10, T=100` analysis unchanged for reproducibility.
- Added a matched-horizon `N=400, m=10, T=300` analysis using the already frozen `auc_abs_delta_phi_0_300` column.
- Excluded the historical `N=100` local benchmark from quantitative matched-horizon scaling figures because its replicate-level response semantics are not part of the minimal reproducibility set.
- Added `local_matched_horizon_summary.csv` for publication-quality local comparisons.
- Replaced the previous local-size figure with a matched-`T=300` version.
- Combined the `N=1600` perturbation-scale and within-state controls into one two-panel main figure.
- Updated scientific protocol, captions and README to make response-window provenance explicit.


## 1.0.1

- Added byte-level SHA-256 verification for the ten canonical runtime datasets.
- Removed unused historical result tables from the runtime input dependency set; retained them only as optional provenance pointers.
- Added a persistent input-integrity audit table.
- Added GitHub Actions CI for Python 3.11 tests and Ruff linting.
- Separated main publication tables from the full/legacy global audit table.
- Added a dedicated within-state perturbation-scale figure.
- Improved publication figure labels and export resolution.
- Added figure/table guidance, data-release guidance and a repository release checklist.
- Generalized public documentation so it no longer depends on one user's local Windows paths.

## 1.0.0

- Finalized the publishable pipeline after clean reproduction of the robust frozen analyses.
- Added Ridge and HGB local models with run-level bootstrap inference.
- Added complete `N=1600, m=160` scale-control reproduction and validation.
- Added bootstrap inference for within-state local prediction.
- Converted `N=400, P0 -> P1` into an explicit non-blocking legacy-sensitivity audit rather than tuning the refactor to match an unstable historical result.
- Suppressed the harmless mixed-type CSV warning for unused legacy columns by reading replicate tables with `low_memory=False`.
- Added final one-command reproduction entry point `scripts/reproduce.py`.
- Updated documentation for data provenance, scientific protocol, Windows execution and GitHub publication.
