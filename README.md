# Vicsek Resilience

Reproducible simulation and analysis code for studying how macroscopic, mesoscopic and local structure affect resilience in the metric Vicsek model.

The repository contains the validated scientific core and the final analysis pipeline only. Exploratory notebooks, superseded calibrations and discarded analyses are intentionally excluded.

## Scientific question

How much information beyond global polarization is required to predict the collective response to a local perturbation?

The final analysis separates three descriptive scales:

- **macroscopic** — global polarization and experimental condition;
- **global mesoscopic** — interaction-graph connectivity and cluster structure;
- **local** — properties of the specific region that is perturbed.

The primary model comparisons are:

- `M0 -> M1`: global mesostructural information beyond linear polarization + condition;
- `P0 -> Pk`: mean-degree information after controlling for a condition-specific cubic relation with polarization;
- `MG -> M2`: local-region information beyond the global state;
- within-state prediction: local information after removing all between-state differences.

The central scale-control result compares `N=1600, m=10` with `N=1600, m=160 (p=0.1)` using a matched response window `T=300`. Cross-size local comparisons also use `T=300`; the earlier `N=400, T=100` analysis is retained only as a historical/reproducibility benchmark.

## Repository layout

```text
src/vicsek/                    reusable scientific implementation
scripts/                       reproducible analysis entry points
configs/final_inputs.toml      canonical runtime input registry
configs/input_manifest.toml    frozen row/size/SHA-256 checks
configs/reference_results.toml frozen pre-refactor numerical benchmarks
configs/historical_sources.toml optional provenance pointers only
tests/                         automated scientific/unit tests
docs/                          protocol, provenance, validation and publication notes
results/final/                 generated compact final tables/audits
figures/final/                 generated final figures
```

The large simulation datasets are deliberately not committed to Git. The pipeline reads a frozen data project supplied with `--project-root`. Before any analysis, it verifies the required files against `configs/input_manifest.toml`, including SHA-256 hashes.

## Installation

Python 3.11+ is required.

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

For a Conda environment on Windows, calling the interpreter directly is sufficient; activating Conda is not required:

```powershell
$PYTHON = "C:\path\to\envs\vicsek\python.exe"
& $PYTHON -m pip install -e ".[dev]"
& $PYTHON -m pytest
```

## Full reproduction

```powershell
$PYTHON = "C:\path\to\envs\vicsek\python.exe"
$DATA_ROOT = "C:\path\to\frozen\Vicsek_Resilience"
& $PYTHON scripts\reproduce.py --project-root $DATA_ROOT
```

For a faster smoke reproduction that omits the largest local dataset:

```powershell
& $PYTHON scripts\reproduce.py --project-root $DATA_ROOT --skip-m160
```

The source data project is treated as read-only. All generated outputs are written under this repository.

## Generated outputs

Key audit files:

- `results/final/input_audit.csv`
- `results/final/reference_validation.csv`
- `results/final/response_semantics_audit.csv`
- `results/final/environment_snapshot.txt` (generated on the validating machine)

Key compact tables:

- `results/final/tables/global_information_summary.csv`
- `results/final/tables/global_full_summary.csv`
- `results/final/tables/local_scale_summary.csv`
- `results/final/tables/local_matched_horizon_summary.csv`
- `results/final/tables/reproducibility_audit.csv`
- `results/final/tables/input_integrity_audit.csv`

Key figures:

- `figures/final/fig_global_information_gain.{png,pdf}`
- `figures/final/fig_local_information_scale_summary.{png,pdf}`

The second figure combines the matched-`T=300` fixed-`m=10` cross-size comparison
with the `N=1600` perturbation-scale and within-state controls so the local
result is presented as one coherent argument rather than as redundant plots.

Large OOF prediction tables remain reproducible but are ignored by Git by default.


### Response-window harmonization

The exploratory project retained more than one integrated-response window. The historical `N=400, m=10` benchmark used `AUC(0,100)`, while the final `N=1600` scale analyses use the full `T=300` response. Version 1.0.3 preserves the original `N=400, T=100` result for audit purposes and additionally recomputes `N=400, m=10` from the already stored `AUC(0,300)` column. Only matched-`T=300` results are used in cross-size local figures.

`scripts/00b_check_response_semantics.py` verifies the stored response semantics before these comparisons are generated.

## Reproducibility status

The clean pipeline reproduces the robust frozen benchmarks for:

- global information gains at `N=100, 400, 1600`;
- the nonlinear-macro robustness comparison `P0 -> Pk`;
- Ridge and HGB local prediction for `N=400, m=10`;
- Ridge and HGB local prediction for `N=1600, m=10`;
- Ridge and HGB local prediction for `N=1600, m=160`;
- corresponding within-state controls.

### Legacy sensitivity: `N=400, P0 -> P1`

The frozen Day-32 analysis reported an approximately `+3.9%` gain with substantial uncertainty. The exact historical regularized-design implementation for that unstable comparison was not retained. The clean implementation does **not** tune itself to force agreement. This comparison is retained as a non-blocking `legacy_sensitivity`; the robust `N=400` conclusion is based on `P0 -> Pk`, which is reproduced.

See:

- `docs/SCIENTIFIC_PROTOCOL.md` — exact scientific definitions;
- `docs/REFACTOR_VALIDATION.md` — equivalence checks against the exploratory implementation;
- `docs/RESULTS_SNAPSHOT.md` — final clean numerical snapshot;
- `docs/FIGURES_AND_TABLES.md` — recommended main/supplementary outputs and captions;
- `docs/FINAL_OUTPUT_REVIEW.md` — final keep/supplementary/retire decisions after visual review;
- `docs/DATA_AVAILABILITY.md` — recommended release strategy for the datasets.

## Reproducibility principle

Benchmarks were frozen before refactoring. If a robust comparison fails validation, the implementation or inputs must be investigated; the benchmark is not changed simply to fit the refactor.

## License

The source code is released under the MIT License. External/frozen datasets are not redistributed by this repository and are not covered by the code license unless they are released separately with an explicit data license.
