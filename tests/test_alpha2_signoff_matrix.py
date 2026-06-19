from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_alpha2_signoff_matrix


def write_host_report_set(base: Path, *, unreal_ok: bool = True, godot_ok: bool = True, runtime_ok: bool = True, visual_ok: bool = True, compat_ok: bool = True) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "unreal_version_matrix.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "version": "5.7",
                        "plugin_build": {"status": "passed" if unreal_ok else "failed"},
                        "orientation": {"status": "passed" if unreal_ok else "failed"},
                        "demo": {"status": "passed" if unreal_ok else "failed"},
                    },
                    {
                        "version": "5.8",
                        "plugin_build": {"status": "passed" if unreal_ok else "failed"},
                        "orientation": {"status": "passed" if unreal_ok else "failed"},
                        "demo": {"status": "passed" if unreal_ok else "failed"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (base / "godot_workflow_report.json").write_text(
        json.dumps(
            {
                "lanes": {
                    "build": {"status": "passed" if godot_ok else "failed"},
                    "verify": {"status": "passed" if godot_ok else "failed"},
                    "demo": {"status": "passed" if godot_ok else "failed"},
                    "missing_lib": {"status": "passed" if godot_ok else "failed"},
                }
            }
        ),
        encoding="utf-8",
    )
    (base / "orientation_runtime_report.json").write_text(
        json.dumps(
            {
                "lanes": {
                    "unreal": {
                        "5.7": {"status": "passed" if runtime_ok else "failed"},
                        "5.8": {"status": "passed" if runtime_ok else "failed"},
                    },
                    "godot": {"status": "passed" if runtime_ok else "failed"},
                }
            }
        ),
        encoding="utf-8",
    )
    (base / "orientation_visual_report.json").write_text(
        json.dumps(
            {
                "lanes": {
                    "unreal": {
                        "5.7": {"status": "passed" if visual_ok else "failed"},
                        "5.8": {"status": "passed" if visual_ok else "failed"},
                    },
                    "godot": {"status": "passed" if visual_ok else "failed"},
                }
            }
        ),
        encoding="utf-8",
    )
    (base / "unreal_host_compat_report.json").write_text(
        json.dumps(
            {
                "lanes": [
                    {"version": "5.7", "probe": {"status": "ok" if compat_ok else "fail"}},
                    {"version": "5.8", "probe": {"status": "ok" if compat_ok else "fail"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    (base / "alpha2_release_audit_report.json").write_text(
        json.dumps({"overall_status": "not-fully-signed-off"}),
        encoding="utf-8",
    )
    (base / "host_report_manifest.json").write_text(
        json.dumps(
            {
                "host_label": base.name,
                "hostname": f"{base.name}.example",
                "platform": "macOS-15-arm64",
                "host_fingerprint": f"fingerprint-{base.name}",
                "report_digest_sha256": f"digest-{base.name}",
            }
        ),
        encoding="utf-8",
    )


def test_overall_status_marks_single_ready_host_as_host_ready() -> None:
    status = run_alpha2_signoff_matrix.overall_status([{"host_ready": True}], 1)
    assert status == "host-ready"


def test_overall_status_marks_single_host_as_host_sample_only_for_cross_host_gate() -> None:
    status = run_alpha2_signoff_matrix.overall_status([{"host_ready": True}], 2)
    assert status == "host-sample-only"


def test_main_writes_signoff_matrix(tmp_path: Path, monkeypatch) -> None:
    host_a = tmp_path / "host_a"
    host_b = tmp_path / "host_b"
    write_host_report_set(host_a)
    write_host_report_set(host_b)

    monkeypatch.setattr(
        run_alpha2_signoff_matrix,
        "parse_args",
        lambda: run_alpha2_signoff_matrix.argparse.Namespace(
            report_dirs=[str(host_a), str(host_b)],
            out_dir=str(tmp_path / "out"),
            min_host_count=2,
            required_unreal_versions=["5.7", "5.8"],
        ),
    )
    monkeypatch.setattr(run_alpha2_signoff_matrix.load_local_env, "load", lambda: None)

    rc = run_alpha2_signoff_matrix.main()

    assert rc == 0
    payload = json.loads((tmp_path / "out" / "alpha2_signoff_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "cross-host-ready"
    assert len(payload["hosts"]) == 2
    markdown = (tmp_path / "out" / "alpha2_signoff_matrix.md").read_text(encoding="utf-8")
    assert "Alpha 2 Signoff Matrix" in markdown
    assert "| " in markdown


def test_main_writes_host_ready_signoff_when_one_ready_host_satisfies_macos_scope(tmp_path: Path, monkeypatch) -> None:
    host_a = tmp_path / "host_a"
    write_host_report_set(host_a)

    monkeypatch.setattr(
        run_alpha2_signoff_matrix,
        "parse_args",
        lambda: run_alpha2_signoff_matrix.argparse.Namespace(
            report_dirs=[str(host_a)],
            report_root=str(tmp_path / "hosts"),
            out_dir=str(tmp_path / "out"),
            min_host_count=1,
            required_unreal_versions=["5.7", "5.8"],
        ),
    )
    monkeypatch.setattr(run_alpha2_signoff_matrix.load_local_env, "load", lambda: None)

    rc = run_alpha2_signoff_matrix.main()

    assert rc == 0
    payload = json.loads((tmp_path / "out" / "alpha2_signoff_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "host-ready"
    markdown = (tmp_path / "out" / "alpha2_signoff_matrix.md").read_text(encoding="utf-8")
    assert "host-ready" in markdown


def test_main_marks_partial_when_only_one_host_exists(tmp_path: Path, monkeypatch) -> None:
    host_a = tmp_path / "host_a"
    write_host_report_set(host_a)
    monkeypatch.setattr(
        run_alpha2_signoff_matrix,
        "parse_args",
        lambda: run_alpha2_signoff_matrix.argparse.Namespace(
            report_dirs=[str(host_a)],
            out_dir=str(tmp_path / "out"),
            min_host_count=2,
            required_unreal_versions=["5.7", "5.8"],
        ),
    )
    monkeypatch.setattr(run_alpha2_signoff_matrix.load_local_env, "load", lambda: None)

    rc = run_alpha2_signoff_matrix.main()

    assert rc == 2
    payload = json.loads((tmp_path / "out" / "alpha2_signoff_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "host-sample-only"


def test_discover_report_dirs_prefers_staged_host_root(tmp_path: Path) -> None:
    host_root = tmp_path / "hosts"
    host_a = host_root / "host_a"
    host_b = host_root / "host_b"
    write_host_report_set(host_a)
    write_host_report_set(host_b)

    discovered = run_alpha2_signoff_matrix.discover_report_dirs(None, host_root)

    assert discovered == [host_a.resolve(), host_b.resolve()]


def test_main_uses_manifest_label_in_markdown(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    host_a = host_root / "host_a"
    write_host_report_set(host_a)
    monkeypatch.setattr(
        run_alpha2_signoff_matrix,
        "parse_args",
        lambda: run_alpha2_signoff_matrix.argparse.Namespace(
            report_dirs=None,
            report_root=str(host_root),
            out_dir=str(tmp_path / "out"),
            min_host_count=2,
            required_unreal_versions=["5.7", "5.8"],
        ),
    )
    monkeypatch.setattr(run_alpha2_signoff_matrix.load_local_env, "load", lambda: None)

    rc = run_alpha2_signoff_matrix.main()

    assert rc == 2
    markdown = (tmp_path / "out" / "alpha2_signoff_matrix.md").read_text(encoding="utf-8")
    assert "| host_a | macOS-15-arm64 |" in markdown


def test_duplicate_host_identity_does_not_count_toward_signoff(tmp_path: Path, monkeypatch) -> None:
    host_root = tmp_path / "hosts"
    host_a = host_root / "host_a"
    host_b = host_root / "host_b"
    write_host_report_set(host_a)
    write_host_report_set(host_b)
    duplicate_manifest = json.loads((host_b / "host_report_manifest.json").read_text(encoding="utf-8"))
    duplicate_manifest["host_fingerprint"] = "fingerprint-host_a"
    (host_b / "host_report_manifest.json").write_text(json.dumps(duplicate_manifest), encoding="utf-8")
    monkeypatch.setattr(
        run_alpha2_signoff_matrix,
        "parse_args",
        lambda: run_alpha2_signoff_matrix.argparse.Namespace(
            report_dirs=None,
            report_root=str(host_root),
            out_dir=str(tmp_path / "out"),
            min_host_count=2,
            required_unreal_versions=["5.7", "5.8"],
        ),
    )
    monkeypatch.setattr(run_alpha2_signoff_matrix.load_local_env, "load", lambda: None)

    rc = run_alpha2_signoff_matrix.main()

    assert rc == 2
    payload = json.loads((tmp_path / "out" / "alpha2_signoff_matrix.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "cross-host-partial"
    assert payload["hosts"][0]["identity_unique"] is False
    assert payload["hosts"][1]["identity_unique"] is False
