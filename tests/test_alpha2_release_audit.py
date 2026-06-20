from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_alpha2_release_audit


def test_classify_overall_marks_partial_as_not_fully_signed_off() -> None:
    status = run_alpha2_release_audit.classify_overall(
        [
            {"status": "complete"},
            {"status": "partial"},
        ],
        "host-ready",
    )
    assert status == "not-fully-signed-off"


def test_classify_overall_marks_all_complete_as_ready() -> None:
    status = run_alpha2_release_audit.classify_overall(
        [
            {"status": "complete"},
            {"status": "complete"},
        ],
        "host-ready",
    )
    assert status == "ready"


def test_classify_overall_requires_ready_signoff_status() -> None:
    status = run_alpha2_release_audit.classify_overall(
        [
            {"status": "complete"},
            {"status": "complete"},
        ],
        "host-partial",
    )
    assert status == "not-fully-signed-off"


def test_render_markdown_lists_non_complete_items() -> None:
    report = {
        "generated_at": "2026-06-19T12:00:00Z",
        "overall_status": "not-fully-signed-off",
        "signoff_matrix_status": "host-ready",
        "success_criteria": [
            {
                "name": "A",
                "status": "complete",
                "evidence_ok": True,
                "note": "ok",
            },
            {
                "name": "B",
                "status": "partial",
                "evidence_ok": True,
                "note": "host sample only",
            },
        ],
        "workseries": [
            {"name": "WS1", "status": "complete", "evidence_ok": True},
            {"name": "WS5", "status": "partial", "evidence_ok": True},
        ],
    }
    markdown = run_alpha2_release_audit.render_markdown(report)
    assert "# Alpha 2 Release Audit Report" in markdown
    assert "- signoff_matrix_status: `host-ready`" in markdown
    assert "| B | partial | yes | host sample only |" in markdown
    assert "- B: `partial`" in markdown


def test_main_writes_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_alpha2_release_audit,
        "SUCCESS_CRITERIA",
        [
            {
                "name": "criterion",
                "status": "complete",
                "evidence": ["docs/releases/ALPHA2_AUDIT.md"],
                "note": "host ready",
            }
        ],
    )
    monkeypatch.setattr(
        run_alpha2_release_audit,
        "WORKSERIES",
        [("WS5", "complete", ["docs/releases/ALPHA2_AUDIT.md"])],
    )
    monkeypatch.setattr(
        run_alpha2_release_audit,
        "parse_args",
        lambda: run_alpha2_release_audit.argparse.Namespace(out_dir=str(tmp_path)),
    )
    monkeypatch.setattr(run_alpha2_release_audit.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_alpha2_release_audit, "load_signoff_status", lambda _path: "host-ready")

    rc = run_alpha2_release_audit.main()

    assert rc == 0
    payload = json.loads((tmp_path / "alpha2_release_audit_report.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "ready"
    assert payload["signoff_matrix_status"] in {"missing", "host-ready", "host-partial", "host-sample-only", "cross-host-partial", "cross-host-ready", "invalid", "missing-status"}
    assert payload["success_criteria"][0]["evidence_ok"] is True
    assert "Alpha 2 Release Audit Report" in (tmp_path / "alpha2_release_audit_report.md").read_text(encoding="utf-8")


def test_load_signoff_status_reads_overall_status(tmp_path: Path) -> None:
    payload = tmp_path / "alpha2_signoff_matrix.json"
    payload.write_text(json.dumps({"overall_status": "cross-host-partial"}), encoding="utf-8")
    assert run_alpha2_release_audit.load_signoff_status(payload) == "cross-host-partial"
