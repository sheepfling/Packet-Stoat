from __future__ import annotations

from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_unity_host_handoff


def test_export_unity_host_handoff_archive_contains_expected_payload(tmp_path: Path) -> None:
    archive_path = tmp_path / "out" / f"fastdis-unity-host-handoff-{export_unity_host_handoff.package_version()}.zip"

    export_unity_host_handoff.export_archive(archive_path)

    assert archive_path.is_file()
    prefix = f"fastdis-unity-host-handoff-{export_unity_host_handoff.package_version()}/"
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert prefix + "README.md" in names
        assert prefix + "docs/UNITY_CROSS_HOST_SIGNOFF.md" in names
        assert prefix + "tools/unity_workflow.py" in names
        assert prefix + "tools/capture_unity_host_report.py" in names
        assert prefix + "tools/run_unity_startup_probe.py" in names
        assert prefix + "tools/run_unity_install_smoke.py" in names
        assert prefix + "tools/import_unity_host_report.py" in names
        assert prefix + "tools/sync_unity_host_reports.py" in names
        assert prefix + "tools/run_unity_host_matrix.py" in names
        assert prefix + "tools/run_unity_signoff.py" in names
        assert prefix + "packages/unity/com.sheepfling.fastdis/package.json" in names
        readme = archive.read(prefix + "README.md").decode("utf-8")
        assert "--skip-native-build" in readme
        assert "run_unity_startup_probe.py" in readme
        assert "capture_unity_host_report.py" in readme
        assert "import_unity_host_report.py" in readme
        assert "sync_unity_host_reports.py" in readme
        assert "run_unity_host_matrix.py" in readme
        assert "run_unity_signoff.py" in readme
