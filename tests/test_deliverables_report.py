from __future__ import annotations

from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import list_deliverables


def test_deliverables_report_finds_expected_groups(tmp_path: Path) -> None:
    (tmp_path / "build" / "dist").mkdir(parents=True)
    (tmp_path / "build" / "dist" / "fastdis-0.0.0.tar.gz").write_bytes(b"sdist")
    (tmp_path / "build" / "cmake" / "host").mkdir(parents=True)
    (tmp_path / "build" / "cmake" / "host" / "libfastdis.so").write_bytes(b"native")
    (tmp_path / "build" / "cmake" / "host" / "fastdis_capi_tests").write_bytes(b"exe")
    (tmp_path / "packages" / "unreal" / "FastDis").mkdir(parents=True)
    (tmp_path / "packages" / "unreal" / "FastDis" / "FastDis.uplugin").write_text("{}", encoding="utf-8")
    (tmp_path / "packages" / "unity" / "com.sheepfling.fastdis").mkdir(parents=True)
    (tmp_path / "packages" / "unity" / "com.sheepfling.fastdis" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "packages" / "lattice").mkdir(parents=True)
    (tmp_path / "packages" / "lattice" / "pyproject.toml").write_text("[project]\nname='packet-stoat-lattice'\n", encoding="utf-8")
    (tmp_path / "build" / "reports").mkdir()
    (tmp_path / "build" / "reports" / "dev_check_report.json").write_text("{}", encoding="utf-8")

    report = list_deliverables.build_report(tmp_path)

    assert report["overall_status"] == "pass"
    assert report["summary"]["python_packages"]["artifact_count"] == 1
    assert report["summary"]["native_core"]["artifact_count"] == 1
    assert report["summary"]["native_tools"]["artifact_count"] == 1
    assert report["summary"]["unreal_plugin"]["artifact_count"] == 1
    assert report["summary"]["unity_package"]["artifact_count"] == 1
    assert report["summary"]["lattice_plugin"]["artifact_count"] == 1
    assert report["summary"]["verification_reports"]["artifact_count"] == 1


def test_deliverables_report_warns_on_local_duplicate_artifacts(tmp_path: Path) -> None:
    (tmp_path / "build" / "dist").mkdir(parents=True)
    (tmp_path / "build" / "dist" / "fastdis-0.0.0 2.tar.gz").write_bytes(b"duplicate")

    report = list_deliverables.build_report(tmp_path)

    assert report["overall_status"] == "warn"
    assert report["duplicate_local_artifacts"] == ["build/dist/fastdis-0.0.0 2.tar.gz"]
