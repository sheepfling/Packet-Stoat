from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNITY_PACKAGE = ROOT / "packages" / "unity" / "com.sheepfling.fastdis"


def test_unity_upm_manifest_is_product_shaped() -> None:
    payload = json.loads((UNITY_PACKAGE / "package.json").read_text(encoding="utf-8"))

    assert payload["name"] == "com.sheepfling.fastdis"
    assert payload["displayName"] == "FastDIS for Unity"
    assert payload["version"] == "0.17.0-alpha.9"
    assert payload["unity"] == "2022.3"
    assert len(payload["samples"]) == 4


def test_unity_package_has_runtime_editor_tests_docs_and_samples() -> None:
    expected = [
        "Runtime/FastDIS.Runtime.asmdef",
        "Runtime/Native/FastDisNative.cs",
        "Runtime/Scanning/FastDisScanner.cs",
        "Runtime/Unity/FastDisTransformMapper.cs",
        "Runtime/Plugins/Windows/x86_64/README.md",
        "Runtime/Plugins/macOS/README.md",
        "Runtime/Plugins/Linux/x86_64/README.md",
        "Editor/FastDIS.Editor.asmdef",
        "Editor/FastDisPackageDoctor.cs",
        "Tests/Runtime/FastDIS.Runtime.Tests.asmdef",
        "Tests/Editor/FastDIS.Editor.Tests.asmdef",
        "Tests/Editor/FastDisNativeLoadTests.cs",
        "Documentation~/install.md",
        "Documentation~/native-plugin.md",
        "Documentation~/orientation.md",
        "Samples~/Minimal Receiver/README.md",
        "Samples~/UDP Loopback/README.md",
        "Samples~/Orientation Verification/README.md",
        "Samples~/Lattice Lab Bridge/README.md",
    ]

    for relative in expected:
        assert (UNITY_PACKAGE / relative).exists(), relative


def test_unity_transform_mapper_documents_eun_mapping() -> None:
    source = (UNITY_PACKAGE / "Runtime" / "Unity" / "FastDisTransformMapper.cs").read_text(encoding="utf-8")

    assert "StandaloneEastUpNorth" in source
    assert "new Vector3(enuMeters.x, enuMeters.z, enuMeters.y)" in source
    assert "Quaternion.LookRotation" in source
