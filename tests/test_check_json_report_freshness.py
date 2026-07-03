from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_passes_for_fresh_enveloped_report(tmp_path: Path) -> None:
    module = _load_module("check_json_report_freshness", ROOT / "tools" / "check_json_report_freshness.py")
    report_path = tmp_path / "benchmark_matrix.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_matrix.v1",
                "generated_at_utc": module.utc_now(),
                "report_meta": {
                    "canonical_format": "json",
                    "markdown_policy": "leaf-only",
                    "generated_at_field": "generated_at_utc",
                    "generated_at": module.utc_now(),
                    "producer": "tools/example.py",
                    "report_path": "artifacts/reports/benchmark_matrix/benchmark_matrix.json",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    args = module.parse_args(["--path", str(report_path), "--max-age-hours", "1", "--ignore-missing"])
    rows, issues = module.audit(args)

    assert rows[0]["status"] == "pass"
    assert issues == []


def test_audit_fails_for_missing_metadata_and_stale_timestamp(tmp_path: Path) -> None:
    module = _load_module("check_json_report_freshness", ROOT / "tools" / "check_json_report_freshness.py")
    report_path = tmp_path / "benchmark_claim_summary.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.benchmark_claim_summary.v1",
                "generated_at_utc": "2020-01-01T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    args = module.parse_args(["--path", str(report_path), "--max-age-hours", "1"])
    rows, issues = module.audit(args)

    assert rows[0]["status"] == "fail"
    reasons = [row["reason"] for row in issues]
    assert any("missing report_meta" in reason for reason in reasons)
    assert any("stale report" in reason for reason in reasons)


def test_main_writes_enveloped_audit_report(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("check_json_report_freshness", ROOT / "tools" / "check_json_report_freshness.py")
    report_path = tmp_path / "benchmark_matrix.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_matrix.v1",
                "generated_at_utc": module.utc_now(),
                "report_meta": {
                    "canonical_format": "json",
                    "markdown_policy": "leaf-only",
                    "generated_at_field": "generated_at_utc",
                    "generated_at": module.utc_now(),
                    "producer": "tools/example.py",
                    "report_path": "artifacts/reports/benchmark_matrix/benchmark_matrix.json",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    json_out = tmp_path / "json_report_freshness_audit.json"
    md_out = tmp_path / "json_report_freshness_audit.md"
    monkeypatch.setattr(module, "REPORT_JSON", json_out)
    monkeypatch.setattr(module, "REPORT_MD", md_out)

    rc = module.main(["--path", str(report_path), "--max-age-hours", "1", "--ignore-missing"])

    assert rc == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.json_report_freshness_audit.v1"
    assert payload["report_meta"]["canonical_format"] == "json"
    assert payload["report_meta"]["markdown_policy"] == "leaf-only"
    assert payload["report_meta"]["producer"] == "tools/check_json_report_freshness.py"
    assert payload["report_meta"]["report_path"].endswith("json_report_freshness_audit.json")
    assert md_out.is_file()
