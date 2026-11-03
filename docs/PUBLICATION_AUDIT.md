# Publication-readiness audit — 2026-10-20

This audit records the final GitHub/TFM publication checks after the validated
v1.0.2 end-to-end run and the v1.0.3 presentation cleanup.

## Scientific core

No scientific-definition changes were made in v1.0.3. The implementation
preserves the validated conventions for periodic metric neighbours,
self-inclusion in the Vicsek alignment average, uniform angular noise,
orientation-before-position updates, graph observables, local target
construction and common-random-number paired trajectories.

## Validated checks

On the user's frozen data project:

- all ten canonical runtime CSVs matched their frozen row counts, byte sizes and
  SHA-256 hashes;
- the response-semantics audit passed;
- 15 automated tests passed;
- the complete v1.0.2 reproduction pipeline completed successfully;
- all robust reference gates passed at the configured one-percentage-point
  tolerance;
- the documented `N=400, P0 -> P1` mismatch remained correctly classified as
  non-blocking `legacy_sensitivity`;
- matched-`T=300` local results were generated for `N=400, m=10`,
  `N=1600, m=10` and `N=1600, m=160`;
- final publication tables and figures were generated successfully.

In the final audit environment:

- the v1.0.3 source/tests pass all 15 tests when the local `src` tree is used;
- the final figure-generation script compiles and completes against the real
  v1.0.2 result tables included in the hand-off archive;
- the final publication figures export as both PNG and PDF.

## Publication decisions

1. Runtime inputs are distinct from optional historical provenance files.
2. The ten canonical runtime CSVs are frozen by row count, byte size and
   SHA-256 hash.
3. Cross-size local comparisons use a common `T=300` response window.
4. The historical `N=400, m=10, T=100` result is retained for reproducibility
   but not mixed with `T=300` points in a homogeneous scaling curve.
5. The historical `N=100` local result is retained as context only because its
   replicate-level response-window semantics are not part of the minimal
   reproducibility set.
6. The main global conclusion is carried by `M0 -> M1` and the stricter
   `P0 -> Pk` comparison.
7. The main local conclusion is intervention-scale dependence: at `N=1600`,
   local descriptors are essentially uninformative for `m=10` but clearly
   informative for `m=160 (p=0.1)`, including within-state.
8. The local evidence is consolidated into one three-panel figure to avoid
   redundant standalone plots.

## Remaining release step

Before creating the public GitHub tag/release, capture the exact validated
software environment with:

```bash
python scripts/06_capture_environment.py
```

and review `docs/DATA_AVAILABILITY.md` to decide whether the frozen datasets,
compact derived tables, or neither will be distributed publicly.
