from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import stage_unity_host_report


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_unity_host_bundle(root: Path, host_label: str, host_platform: str) -> None:
    host_dir = root / host_label
    host_dir.mkdir(parents=True)
    manifest = {
        "host_label": host_label,
        "host_platform": host_platform,
        "unity_workflow_status": "pass",
        "unity_runtime_status": "pass",
        "unity_orientation_status": "pass",
        "unity_startup_probe_status": "pass",
        "unity_install_status": "pass",
        "host_fingerprint": f"{host_label}-fingerprint",
        "report_digest_sha256": f"{host_label}-digest",
    }
    (host_dir / stage_unity_host_report.HOST_MANIFEST).write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    (host_dir / stage_unity_host_report.HOST_MANIFEST_MD).write_text("# manifest\n", encoding="utf-8")


def _write_alpha2_host_report_set(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "unreal_version_matrix.json").write_text(
        json.dumps(
            {
                "results": [
                    {"version": "5.7", "plugin_build": {"status": "passed"}, "orientation": {"status": "passed"}, "demo": {"status": "passed"}},
                    {"version": "5.8", "plugin_build": {"status": "passed"}, "orientation": {"status": "passed"}, "demo": {"status": "passed"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    (base / "godot_workflow_report.json").write_text(
        json.dumps({"lanes": {"build": {"status": "passed"}, "verify": {"status": "passed"}, "demo": {"status": "passed"}, "missing_lib": {"status": "passed"}}}),
        encoding="utf-8",
    )
    (base / "orientation_runtime_report.json").write_text(
        json.dumps({"lanes": {"unreal": {"5.7": {"status": "passed"}, "5.8": {"status": "passed"}}, "godot": {"status": "passed"}}}),
        encoding="utf-8",
    )
    (base / "orientation_visual_report.json").write_text(
        json.dumps({"lanes": {"unreal": {"5.7": {"status": "passed"}, "5.8": {"status": "passed"}}, "godot": {"status": "passed"}}}),
        encoding="utf-8",
    )
    (base / "unreal_host_compat_report.json").write_text(
        json.dumps({"lanes": [{"version": "5.7", "probe": {"status": "ok"}}, {"version": "5.8", "probe": {"status": "ok"}}]}),
        encoding="utf-8",
    )
    (base / "alpha2_release_audit_report.json").write_text(json.dumps({"overall_status": "not-fully-signed-off"}), encoding="utf-8")
    (base / "host_report_manifest.json").write_text(
        json.dumps(
            {
                "host_label": base.name,
                "hostname": f"{base.name}.example",
                "platform": "windows-x64",
                "host_fingerprint": f"fingerprint-{base.name}",
                "report_digest_sha256": f"digest-{base.name}",
            }
        ),
        encoding="utf-8",
    )


def test_build_phase2_host_evidence_summary_combines_unity_and_alpha2(tmp_path: Path) -> None:
    module = _load_module("build_phase2_host_evidence_summary", ROOT / "tools" / "build_phase2_host_evidence_summary.py")
    unity_root = tmp_path / "unity_hosts"
    alpha2_root = tmp_path / "alpha2_hosts"
    out_dir = tmp_path / "out"
    _write_unity_host_bundle(unity_root, "mac-host", "macos")
    _write_unity_host_bundle(unity_root, "win-host", "windows")
    _write_alpha2_host_report_set(alpha2_root / "host-a")

    unity_report, alpha2_report, report = module.build_report(
        unity_host_root=unity_root,
        alpha2_host_root=alpha2_root,
        out_dir=out_dir,
        alpha2_min_host_count=2,
        alpha2_required_unreal_versions=["5.7", "5.8"],
    )

    assert unity_report["overall_status"] == "cross-host-incomplete"
    assert alpha2_report["overall_status"] == "host-sample-only"
    assert report["schema"] == "fastdis.phase2_host_evidence_summary.v1"
    assert report["summary"]["unity_host_count"] == 2
    assert report["summary"]["alpha2_host_count"] == 1
    assert {row["lane"] for row in report["lanes"]} == {"unity", "alpha2"}
    assert any(host["lane"] == "unity" for host in report["hosts"])
    assert any(host["lane"] == "alpha2" for host in report["hosts"])


def test_main_writes_phase2_host_evidence_outputs(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_phase2_host_evidence_summary", ROOT / "tools" / "build_phase2_host_evidence_summary.py")
    unity_root = tmp_path / "unity_hosts"
    alpha2_root = tmp_path / "alpha2_hosts"
    out_dir = tmp_path / "out"
    _write_unity_host_bundle(unity_root, "mac-host", "macos")
    _write_alpha2_host_report_set(alpha2_root / "host-a")

    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda argv=None: module.argparse.Namespace(
            unity_host_root=unity_root,
            alpha2_host_root=alpha2_root,
            out_dir=out_dir,
            alpha2_min_host_count=2,
            alpha2_required_unreal_versions=["5.7", "5.8"],
        ),
    )

    assert module.main() == 0
    payload = json.loads((out_dir / "phase2_host_evidence_summary.json").read_text(encoding="utf-8"))
    assert payload["summary"]["unity_host_count"] == 1
    assert payload["summary"]["alpha2_host_count"] == 1
    assert (out_dir / "unity_host_matrix.json").is_file()
    assert (out_dir / "alpha2_signoff_matrix.json").is_file()
    assert "Phase 2 Host Evidence Summary" in (out_dir / "phase2_host_evidence_summary.md").read_text(encoding="utf-8")
