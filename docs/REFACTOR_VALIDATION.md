# Refactor validation

The clean implementation was compared directly against the exploratory `src/vicsek` implementation on the same 40-particle microstate and the same random seeds.

The following quantities matched exactly (within floating-point comparison; the Vicsek step itself had maximum absolute difference `0.0`):

- positions after one Vicsek step;
- orientations after one Vicsek step;
- periodic interaction pairs;
- particle degrees;
- connected-component labels and sizes;
- polarization;
- number of components and LCC fraction;
- component entropy;
- mean degree and local-density dispersion;
- nearest-`m` target indices under periodic geometry;
- effective target radius;
- mean distance to perturbation centre;
- selected polarization;
- selected mean degree;
- selected fraction in the LCC.

The automated test suite additionally checks periodic geometry, update conventions, mesoscopic observables, perturbation selection, grouped validation, condition-specific cubic features, within-state centring, nested-Ridge OOF prediction, and frozen-input integrity utilities.

## End-to-end validation

The final clean pipeline was subsequently run against the frozen full data project. Its robust OOF information-gain comparisons reproduce the pre-refactor benchmarks within the configured tolerance. The clean numerical outputs are recorded in `docs/RESULTS_SNAPSHOT.md`.

The sole intentionally non-blocking discrepancy is `N=400, P0 -> P1`. The exact historical regularized-design implementation for this unstable comparison was not retained, and the historical estimate had substantial uncertainty. It is therefore recorded as `legacy_sensitivity` rather than tuned to match.

## Input integrity

The publication-ready pipeline also freezes SHA-256 digests for every canonical runtime input in `configs/input_manifest.toml`. A reproduction run now fails before analysis if a required dataset is missing or differs from the audited frozen file.
