from pathlib import Path

from vicsek.datasets import InputRegistry, audit_canonical_inputs, load_input_manifest, sha256_file


def test_sha256_file_known_content(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_bytes(b"a,b\n1,2\n")
    assert sha256_file(path) == "492d5ea496056f1a6a6592241032fab764c321596317930b4fa0e1e8bc3b7470"


def test_input_audit_detects_exact_file(tmp_path: Path):
    data = tmp_path / "data.csv"
    data.write_bytes(b"x\n1\n2\n")

    config = tmp_path / "inputs.toml"
    config.write_text('[global.N100]\nstate_response = "data.csv"\nfold_assignment = ""\n')
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        "[[file]]\n"
        'label = "global.N100.state_response"\n'
        'path = "data.csv"\n'
        "rows = 2\n"
        f"size_bytes = {data.stat().st_size}\n"
        f'sha256 = "{sha256_file(data)}"\n'
    )

    audit = audit_canonical_inputs(
        tmp_path,
        InputRegistry.from_file(config),
        frozen_manifest=load_input_manifest(manifest_path),
    )
    assert len(audit) == 1
    assert bool(audit.iloc[0]["valid"])


def test_input_audit_ignores_analysis_metadata_fields(tmp_path: Path):
    data = tmp_path / "data.csv"
    data.write_bytes(b"x\n1\n")

    config = tmp_path / "inputs.toml"
    config.write_text(
        '[local.N400_m10]\n'
        'states = "data.csv"\n'
        'replicates = "data.csv"\n'
        'target = "x"\n'
        'response_window = 300\n'
    )
    audit = audit_canonical_inputs(
        tmp_path,
        InputRegistry.from_file(config),
        frozen_manifest=None,
        verify_hashes=False,
    )
    assert len(audit) == 1
    assert audit.iloc[0]["relative_path"] == "data.csv"
    assert bool(audit.iloc[0]["valid"])
