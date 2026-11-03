# Final figures and tables: recommended use

This note separates the figures and tables that carry the scientific narrative
from reproducibility/audit material.

## Response-window convention

The exploratory project retained more than one integrated response window.
The reproduced historical `N=400, m=10` benchmark uses `AUC(0,100)`, whereas
the final `N=1600` local datasets encode the full `T=300` response.

For publication-quality local comparisons, the pipeline also runs
`N400_m10_T300` using the already stored `auc_abs_delta_phi_0_300` column.
Only matched-`T=300` results are used in the final local figure.

The historical `N=400, T=100` result remains in the repository for
reproducibility. The frozen `N=100` local benchmark is retained as historical
context only because its replicate-level response-window semantics are not in
the minimal reproducibility set.

## Main figures

### Figure 1 — Global structural information

File: `fig_global_information_gain.pdf`

**Purpose.** Shows how much predictive information remains in global
mesostructure beyond polarization. `M0 -> M1` is the linear macro/meso
comparison; `P0 -> Pk` is the stricter nonlinear-macro control focused on mean
degree.

**Suggested caption.**

> Predictive information contributed by global mesoscopic structure as system size increases. Points show the fraction of out-of-fold baseline MSE removed by adding all global mesoscopic descriptors to the linear macrostate (`M0 -> M1`) and by adding mean degree after controlling for a condition-specific cubic dependence on polarization (`P0 -> Pk`). Error bars show 95% run-level, condition-stratified bootstrap intervals. The positive `P0 -> Pk` gain at all three system sizes indicates that mean degree contains predictive information not reducible to a nonlinear transformation of global polarization.

### Figure 2 — Local information and perturbation scale

File: `fig_local_information_scale_summary.pdf`

**Purpose.** Presents the complete local-scale argument in one figure.

- **A:** fixed small perturbation (`m=10`) across `N=400` and `N=1600`,
  with a common `T=300` response definition;
- **B:** `N=1600`, `T=300`, comparing `m=10` and `m=160` for `MG -> M2`;
- **C:** the corresponding within-state comparison.

**Suggested caption.**

> Local predictive information depends on perturbation scale. (A) At fixed absolute perturbation size (`m=10`) and matched response window (`T=300`), adding local target descriptors to the global model produces only very small gains at both `N=400` and `N=1600`. (B) At fixed `N=1600` and `T=300`, the same local descriptors provide essentially no robust gain for `m=10` but a clear positive gain for `m=160` (`p=0.1`). (C) The within-state analysis shows the same contrast after removing all between-state differences, demonstrating that for the larger perturbation the response depends on which region of a given microstate is perturbed. Points show Ridge and HGB estimates; error bars are 95% run-level, condition-stratified bootstrap intervals.

For a short article, panel A can be described briefly while panels B/C carry
the central intervention-scale result. For the TFM, retain all three panels.

## Main tables

### `global_information_summary.csv`

Compact global-results table containing the two comparisons that carry the
main argument: `M0 -> M1` and `P0 -> Pk`, with confidence intervals and
bootstrap sign probabilities.

### `local_matched_horizon_summary.csv`

Preferred local-results table for the TFM/article. It contains only
clean-pipeline `T=300` results:

- `N=400, m=10`;
- `N=1600, m=10`;
- `N=1600, m=160`;

for both `MG -> M2` and within-state analyses.

## Supplementary / historical tables

### `local_scale_summary.csv`

Full local audit table. It includes the frozen historical `N=100` benchmark,
the reproduced `N=400, T=100` benchmark, and the matched-`T=300` analyses.
Use this for provenance, not as a single homogeneous scaling table.

### `global_full_summary.csv`

Contains `P0 -> P1` in addition to the main global comparisons. The
`N=400, P0 -> P1` row is explicitly labelled `legacy_sensitivity` and should
not be used as a blocking scientific benchmark.

### `reproducibility_audit.csv`

Engineering/scientific audit comparing clean outputs with frozen pre-refactor
benchmarks. Appropriate for the repository or supplementary material, not the
main TFM results table.

### `input_integrity_audit.csv`

Byte-level data-integrity record. Keep in the repository/reproducibility
appendix.

### `response_semantics_audit.csv`

Records the checks used to verify that the final local scale comparisons use
the intended `T=300` response semantics. This is reproducibility material, not
a primary scientific result.

## OOF and fold-level outputs

OOF predictions and outer-fold diagnostics remain generated artifacts for
independent checking and future re-analysis. They are not primary
figures/tables in the TFM.
