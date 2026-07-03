from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

report_contract_spec = importlib.util.spec_from_file_location("report_contract", ROOT / "tools" / "report_contract.py")
assert report_contract_spec is not None
report_contract = importlib.util.module_from_spec(report_contract_spec)
assert report_contract_spec.loader is not None
report_contract_spec.loader.exec_module(report_contract)

check_spec = importlib.util.spec_from_file_location("check_report_inputs", ROOT / "tools" / "check_report_inputs.py")
assert check_spec is not None
check_report_inputs = importlib.util.module_from_spec(check_spec)
assert check_spec.loader is not None
check_spec.loader.exec_module(check_report_inputs)


def test_is_report_markdown_path_only_matches_report_markdown() -> None:
    assert report_contract.is_report_markdown_path("artifacts/reports/unity_workflow_report.md")
    assert report_contract.is_report_markdown_path("artifacts/verification_reports/foo/bar.md")
    assert not report_contract.is_report_markdown_path("docs/README.md")
    assert not report_contract.is_report_markdown_path("artifacts/reports/unity_workflow_report.json")


def test_audit_file_flags_markdown_report_consumption(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "from pathlib import Path\n"
        "text = (Path('artifacts/reports') / 'unity_workflow_report.md').read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )

    issues = check_report_inputs.audit_file(source)

    assert len(issues) == 1
    assert "consume the sibling JSON instead" in str(issues[0]["detail"])


def test_audit_file_ignores_markdown_outputs_and_docs(tmp_path: Path) -> None:
    source = tmp_path / "writer.py"
    source.write_text(
        "from pathlib import Path\n"
        "Path('artifacts/reports/unity_workflow_report.md').write_text('hi', encoding='utf-8')\n"
        "Path('docs/README.md').read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )

    issues = check_report_inputs.audit_file(source)

    assert issues == []
