# Final validated results snapshot

This snapshot records the clean-pipeline outputs obtained during the final end-to-end reproduction on 2026-10-20. Gains are fractions of baseline MSE removed.

## Global information

| N | M0 -> M1 | P0 -> Pk | P0 -> P1 |
|---:|---:|---:|---:|
| 100 | 0.307576 | 0.285580 | 0.310165 |
| 400 | 0.115627 | 0.049982 | -0.019895* |
| 1600 | 0.072949 | 0.040470 | 0.057261 |

`*` `N=400, P0 -> P1` is the documented non-blocking legacy sensitivity. The frozen historical Day-32 value was approximately `+0.039` with substantial uncertainty; the clean pipeline does not tune to reproduce it.

## Local information at fixed m=10 — matched T=300 comparison

| N | Algorithm | MG -> M2 | 95% CI | Within-state | 95% CI |
|---:|---|---:|---|---:|---|
| 400 | Ridge | 0.001883 | [0.000257, 0.003607] | 0.001838 | [0.000361, 0.003237] |
| 400 | HGB | -0.000556 | [-0.003987, 0.002969] | -0.003086 | [-0.005682, -0.000635] |
| 1600 | Ridge | 0.000587 | [-0.000429, 0.001644] | 0.000255 | [-0.000677, 0.001117] |
| 1600 | HGB | 0.000332 | [-0.003418, 0.004211] | -0.006863 | [-0.008730, -0.005172] |

These values use the same integrated-response window `T=300` at both system
sizes. They show that, for a fixed small perturbation (`m=10`), the incremental
predictive value of the local descriptors is very small at both `N=400` and
`N=1600`. The earlier `N=400, T=100` result is retained only as a historical
reproducibility benchmark in `local_scale_summary.csv`.

## N=1600 perturbation-scale control

| m | Algorithm | MG -> M2 | 95% CI | Within-state | 95% CI |
|---:|---|---:|---|---:|---|
| 10 | Ridge | 0.000587 | [-0.000429, 0.001644] | 0.000255 | [-0.000677, 0.001117] |
| 10 | HGB | 0.000332 | [-0.003418, 0.004211] | -0.006863 | [-0.008730, -0.005172] |
| 160 | Ridge | 0.032304 | [0.027910, 0.036392] | 0.032405 | [0.028250, 0.036263] |
| 160 | HGB | 0.042377 | [0.037261, 0.047376] | 0.032355 | [0.028090, 0.036831] |

This is the central scale-control result: local structure is predictive when the perturbation affects a finite fraction of the system (`m=160`, `p=0.1`), but its predictive value disappears for fixed `m=10` at `N=1600`.

## Validation status

All robust gates in `configs/reference_results.toml` were reproduced within the configured tolerance. The only recorded mismatch is the explicitly non-blocking `N=400, P0 -> P1` legacy sensitivity.
