# Repository release checklist

Use this checklist immediately before creating the public GitHub repository or a tagged release.

- [ ] Run `python -m pytest` successfully in Python 3.11.
- [ ] Run `python -m ruff check .` successfully.
- [ ] Run the complete `scripts/reproduce.py` pipeline against the frozen data root.
- [ ] Run `scripts/06_capture_environment.py` on the validating machine and keep the snapshot.
- [ ] Confirm every row in `results/final/input_audit.csv` has `valid=True`.
- [ ] Confirm every `robust_gate` row in `results/final/reference_validation.csv` passes.
- [ ] Inspect the four final PDF figures visually.
- [ ] Confirm `docs/RESULTS_SNAPSHOT.md` matches the final clean outputs.
- [ ] Keep `N=400, P0 -> P1` labelled as non-blocking `legacy_sensitivity`.
- [ ] Decide where the canonical ~38.8 MiB data bundle will be archived.
- [ ] Assign an explicit license to the data bundle if it is released.
- [ ] Add repository URL / DOI metadata after those identifiers exist.
- [ ] Create a tagged release only after the TFM/article numbers are frozen.

## Response semantics

- [ ] `scripts/00b_check_response_semantics.py` passes on the frozen data root.
- [ ] Main cross-size local figures use only matched `T=300` results.
- [ ] Historical `N=100` and `N=400, T=100` local benchmarks are labelled as historical/audit material rather than homogeneous scaling points.
