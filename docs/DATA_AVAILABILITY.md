# Data availability and release strategy

## What the code needs

The clean pipeline requires ten unique canonical CSV files from the frozen exploratory project. Together they occupy approximately **38.8 MiB** in the audited project; the largest single file is the `N=1600, m=160` replicate dataset at approximately **28.6 MiB**.

The exact paths, row counts, byte sizes and SHA-256 digests are frozen in `configs/input_manifest.toml`.

## Recommended public release

Do **not** commit the replicate-level CSV files directly into normal Git history. Keep the GitHub repository focused on source code, documentation, compact final tables and publication figures.

For full public reproducibility, publish a separate immutable data bundle containing only the ten canonical runtime inputs. Suitable destinations include an archival research-data repository (preferred when a DOI is useful) or a versioned release asset. The repository can then point to that bundle without carrying large CSV history.

A minimal public data bundle should preserve the same relative paths used by `configs/final_inputs.toml`, so the downloaded archive can be supplied directly through `--project-root` without changing code.

## What should be versioned in Git

Recommended to keep in Git:

- source code and tests;
- configuration and frozen input hashes;
- `docs/RESULTS_SNAPSHOT.md`;
- compact final CSV tables;
- final PNG/PDF figures;
- reproducibility and input-integrity audit tables.

Recommended to keep out of normal Git history:

- replicate-level response datasets;
- full OOF prediction tables;
- exploratory notebooks and superseded outputs;
- temporary figures and cache/build files.

## Licensing

The repository's MIT license applies to the source code. The simulation datasets are not included in this repository, so no data license is assigned here. If the canonical data bundle is released separately, choose and state its data license explicitly at release time (for example, an open data license if permitted by the project/institutional context).
