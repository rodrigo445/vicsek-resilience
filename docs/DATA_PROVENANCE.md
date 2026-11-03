# Data provenance

The repository does not bundle the large exploratory datasets. Runtime inputs are registered explicitly in `configs/final_inputs.toml` and are read from a frozen exploratory project supplied through `--project-root`.

A second file, `configs/input_manifest.toml`, freezes the expected row counts, byte sizes and SHA-256 digests of every unique runtime input. `scripts/00_check_inputs.py` verifies these before analysis. This protects the final reproduction against both superseded filenames and silently modified files.

The ten unique canonical runtime inputs comprise:

- the final state-level global-response data for `N=100`;
- state tables, state-level responses and preserved outer-fold assignments for `N=400` and `N=1600`;
- replicate-level local perturbation data for `N=400, m=10`, `N=1600, m=10`, and `N=1600, m=160`.

Historical exploratory result tables are **not runtime dependencies**. Optional pointers to those files are retained separately in `configs/historical_sources.toml` for provenance only. Numerical pre-refactor benchmarks used by the validation gates are frozen in `configs/reference_results.toml`.

Historical seed bookkeeping for reused `N=1600` states is encapsulated in the clean perturbation utilities. Where a `legacy_state_index` is required to reproduce historical perturbation centres, it is handled as provenance rather than as an ad-hoc correction in the analysis scripts.

The exploratory project must be treated as read-only during final reproduction. See `docs/DATA_AVAILABILITY.md` for the recommended public release strategy.
