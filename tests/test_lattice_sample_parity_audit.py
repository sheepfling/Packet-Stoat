from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
for candidate in (TOOLS, ADAPTER_SRC):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import lattice_sample_parity_audit
from packet_stoat_lattice import NotConfiguredError, RealLatticeConfig, RealLatticePublisher


def test_real_lattice_publisher_supports_dry_run_without_credentials() -> None:
    publisher = RealLatticePublisher(RealLatticeConfig(dry_run=True))

    result = publisher.publish_entity({"entity_key": "100:1:42"})

    assert result["status"] == "dry-run"
    assert result["config"]["dry_run"] is True
    assert result["config"]["configured"] is False


def test_real_lattice_publisher_requires_config_only_for_live_mode() -> None:
    try:
        RealLatticePublisher(RealLatticeConfig(dry_run=False))
    except NotConfiguredError:
        pass
    else:
        raise AssertionError("expected NotConfiguredError for live mode without credentials")


def test_lattice_sample_parity_audit_reports_sdk_shaped_backend(tmp_path: Path) -> None:
    report = lattice_sample_parity_audit.build_report()
    json_path, md_path = lattice_sample_parity_audit.write_report(report, tmp_path)

    assert report["overall_status"] == "sdk-shaped"
    assert all(row["status"] == "pass" for row in report["parity_rows"])
    assert json.loads(json_path.read_text(encoding="utf-8"))["overall_status"] == "sdk-shaped"
    assert "Lattice Sample Parity Audit" in md_path.read_text(encoding="utf-8")
