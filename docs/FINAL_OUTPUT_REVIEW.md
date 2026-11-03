# Final output review

This review records the final publication decision after the matched-response
window audit and the validated v1.0.2 end-to-end run.

## Main-text figures

1. `fig_global_information_gain.pdf`
   - Keep in the main text.
   - It supports the global conclusion that mesostructural information remains
     predictive beyond polarization, including the stricter `P0 -> Pk`
     comparison after nonlinear macroscopic control.

2. `fig_local_information_scale_summary.pdf`
   - Keep in the main text.
   - **Panel A:** fixed `m=10`, matched `T=300`, comparing `N=400` and `N=1600`.
     Local gain is very small at both sizes, so this panel should be read as a
     control against over-interpreting system-size scaling.
   - **Panel B:** `N=1600`, `T=300`, comparing `m=10` with `m=160` for
     `MG -> M2`.
   - **Panel C:** the corresponding within-state control.
   - Panels B/C carry the strongest local conclusion: local descriptors become
     robustly predictive when the perturbation itself spans a larger fraction
     of the system.

The former standalone `fig_local_m10_T300_gain_vs_N` and
`fig_N1600_scale_control` plots are intentionally retired from the final
generated set because the three-panel figure presents the same evidence more
coherently and with less redundancy.

## Main-text tables

- `global_information_summary.csv`
- `local_matched_horizon_summary.csv`

For the TFM these should be rendered as compact LaTeX tables rather than copied
verbatim as CSV files.

## Supplementary / repository-only material

- `global_full_summary.csv`: transparency table including the documented
  `N=400, P0 -> P1` legacy sensitivity.
- `local_scale_summary.csv`: complete provenance table containing the
  historical unmatched-window results and the matched-`T=300` analyses.
- `reproducibility_audit.csv`: clean-pipeline versus frozen-benchmark audit.
- `input_integrity_audit.csv`: byte-level frozen-input validation.
- `response_semantics_audit.csv`: verifies response-window semantics.

## Results deliberately not used as homogeneous scaling evidence

- The historical `N=100, m=10` local benchmark has no replicate-level
  response-window audit in the minimal reproducibility set and therefore is not
  plotted as a quantitative matched-horizon scaling point.
- The historical `N=400, m=10, T=100` result remains reproduced and documented,
  but is not combined with `T=300` results in a single scaling curve.
- `N=400, P0 -> P1` remains a non-blocking legacy sensitivity and is not used
  for the main global conclusion.

## Recommended narrative

The final local result should not be phrased primarily as "local information
vanishes as N grows." With the response horizon harmonized to `T=300`, local
gains at fixed `m=10` are already very small at `N=400`.

The cleaner conclusion is that the predictive relevance of local structure is
**intervention-scale dependent**. At `N=1600`, `m=10` produces essentially no
robust local gain, whereas `m=160 (p=0.1)` produces a clear positive gain in
both standard and within-state analyses.
