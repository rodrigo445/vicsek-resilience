# Scientific protocol encoded by the final pipeline

## State description

The main macroscopic observable is global polarization `phi_0`. Each state is also represented by an undirected metric interaction graph under periodic boundary conditions. The final global mesoscopic descriptors are mean degree, fraction in the largest connected component, local-density dispersion, components per particle and component entropy.

## Perturbation

A spatial centre is sampled and the `m` nearest particles under periodic geometry are selected. Their orientations are rotated by `pi/2`. Perturbed and control trajectories share the same future random noise. The response is an integrated absolute polarization difference. For the final scale comparisons, the response window is harmonized to `T=300`. The historical `N=400, m=10` benchmark based on `AUC(0,100)` is retained only for reproducibility and is not used as the matched cross-size estimate.

## Global predictive models

- `M0`: polarization + condition.
- `Mk`: `M0` + mean degree.
- `M1`: `M0` + the final global mesoscopic descriptors.
- `P0`: condition-specific cubic dependence on polarization.
- `Pk`: `P0` + mean degree.
- `P1`: `P0` + all final global mesoscopic descriptors.

The primary nonlinear-macro robustness comparison is `P0 -> Pk`.

## Local predictive models

- `MG`: global polarization, global mean degree, global LCC fraction and condition.
- `M2`: `MG` plus selected-region polarization, selected-region mean degree, selected-region LCC fraction, effective target radius and mean distance to perturbation centre.

The within-state analysis centres both the response and local descriptors by state before prediction. It therefore asks whether different perturbation locations within the same microstate have predictably different consequences.

## Validation

Outer cross-validation is grouped by `run_id`; states from the same simulation run never appear in both train and test. Preserved historical fold assignments are reused when available. Model comparison uses OOF predictions only.

Information gain is reported as

```text
(MSE_baseline - MSE_candidate) / MSE_baseline
```

Uncertainty is estimated with a bootstrap at run level, stratified by condition.

## Perturbation-scale control

Two `N=1600` local analyses are retained, both with response window `T=300`:

- `m=10`: fixed absolute perturbation size;
- `m=160`: `p=0.1`, a perturbation affecting a fixed fraction of the system.

Their contrast is central to the conclusion that the predictive relevance of local structure depends on perturbation scale. For the cross-size `m=10` comparison, `N=400` is recomputed from its stored `AUC(0,300)` column so that `N=400` and `N=1600` use the same response window.
