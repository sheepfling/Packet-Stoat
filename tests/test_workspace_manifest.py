from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import workspace_manifest


def test_workspace_manifest_exposes_surfaces_and_routes() -> None:
    manifest = workspace_manifest.load_manifest()

    assert manifest["schema"] == "packet_stoat.workspace_manifest.v1"
    surface_ids = {surface["id"] for surface in workspace_manifest.surface_specs(manifest)}
    route_ids = {route["id"] for route in workspace_manifest.route_specs(manifest)}

    assert {"python", "unity", "godot", "unreal"} <= surface_ids
    assert {"python-core", "unity-linux-cross-direct", "windows-cross-mingw"} <= route_ids
    assert workspace_manifest.canonical_surface_hooks(manifest) == [
        "discover",
        "doctor",
        "bootstrap",
        "build",
        "verify",
        "demo",
        "full",
        "package",
        "install-smoke",
    ]
    assert workspace_manifest.canonical_hook_categories(manifest) == {
        "discover": "lifecycle",
        "doctor": "lifecycle",
        "bootstrap": "lifecycle",
        "build": "proof",
        "verify": "proof",
        "demo": "demo",
        "full": "proof",
        "package": "packaging",
        "install-smoke": "install",
    }
    assert "fastdis-bootstrap" in workspace_manifest.route_task_templates(manifest)
    assert "fastdis-build" in workspace_manifest.route_task_templates(manifest)
    assert "grill-package-proof" in workspace_manifest.route_task_templates(manifest)
    assert "workspace-verify" in workspace_manifest.route_task_templates(manifest)

    unity = workspace_manifest.surface_spec("unity", manifest)
    godot = workspace_manifest.surface_spec("godot", manifest)
    python = workspace_manifest.surface_spec("python", manifest)
    unreal = workspace_manifest.surface_spec("unreal", manifest)
    unity_hooks = workspace_manifest.surface_hooks(unity, manifest)
    godot_hooks = workspace_manifest.surface_hooks(godot, manifest)
    python_hooks = workspace_manifest.surface_hooks(python, manifest)
    unreal_hooks = workspace_manifest.surface_hooks(unreal, manifest)
    unreal_versions = workspace_manifest.surface_versions(unreal, manifest)
    python_versions = workspace_manifest.surface_versions(python, manifest)

    assert unity_hooks["doctor"]["command"] == "fastdis engine unity doctor --unity-version 6000.5"
    assert unity_hooks["doctor"]["category"] == "lifecycle"
    assert unity_hooks["full"]["status"] == "supported"
    assert godot_hooks["bootstrap"]["command"] == "fastdis engine godot bootstrap"
    assert godot_hooks["verify"]["status"] == "supported"
    assert python_hooks["discover"]["status"] == "unsupported"
    assert python_hooks["package"]["category"] == "packaging"
    assert python_hooks["package"]["status"] == "partial"
    assert python_hooks["package"]["requirements"][0]["version_policy"] == "exact-abi"
    assert python_hooks["package"]["requirements"][0]["supported_versions"] == ["3.14"]
    assert unity_hooks["doctor"]["requirements"][0]["requirement_kind"] == "engine"
    assert unity_hooks["doctor"]["requirements"][0]["version_policy"] == "exact-minor"
    assert unity_hooks["doctor"]["requirements"][0]["supported_versions"] == ["6000.5"]
    assert unreal_hooks["doctor"]["requirements"][0]["requirement_kind"] == "engine"
    assert unreal_hooks["doctor"]["requirements"][0]["version_policy"] == "exact-minor"
    assert unreal_hooks["doctor"]["requirements"][0]["supported_versions"] == ["5.8"]
    assert workspace_manifest.surface_preferred_version(unity, manifest) == "6000.5"
    assert workspace_manifest.surface_preferred_version(unreal, manifest) == "5.8"
    assert [row["version"] for row in unreal_versions] == ["5.7", "5.8"]
    assert unreal_versions[1]["preferred"] is True
    assert [row["version"] for row in python_versions] == ["3.12", "3.13", "3.14"]
    assert python_versions[-1]["status"] == "preferred"


def test_workspace_manifest_host_specific_install_metadata() -> None:
    route = workspace_manifest.route_spec("unity-linux-cross-direct")
    unity_docker_route = workspace_manifest.route_spec("unity-linux-docker")
    unity_native_route = workspace_manifest.route_spec("unity-native")
    godot_route = workspace_manifest.route_spec("godot-native")
    unreal_route = workspace_manifest.route_spec("unreal-native")
    unreal_linux_docker = workspace_manifest.route_spec("unreal-linux-docker")
    mingw_route = workspace_manifest.route_spec("windows-cross-mingw")
    python_route = workspace_manifest.route_spec("python-core")

    assert workspace_manifest.route_supported_on_host(route, "windows") is True
    assert workspace_manifest.route_supported_on_host(route, "linux") is False
    assert workspace_manifest.route_installs(route, "windows") == ["zig", "cmake"]
    assert workspace_manifest.route_install_commands(route, "windows") == ["scoop install zig cmake"]
    assert workspace_manifest.route_preferred_surface_version(route) == "6000.5"
    assert workspace_manifest.route_commands(unity_native_route) == [
        "fastdis engine unity discover --format json",
        "fastdis engine unity doctor --unity-version 6000.5",
    ]
    assert workspace_manifest.route_commands(route) == [
        "python tools/build_unity_native_matrix.py doctor",
        "python tools/build_unity_native_matrix.py build --targets linux --linux-backend direct",
    ]
    assert workspace_manifest.route_evidence_commands(route) == [
        "python tools/build_unity_native_matrix.py doctor"
    ]
    assert workspace_manifest.route_commands(unity_docker_route) == [
        "python tools/build_unity_native_matrix.py doctor",
        "python tools/build_unity_native_matrix.py build --targets linux --linux-backend docker",
    ]
    assert workspace_manifest.route_supported_surface_versions(unreal_route) == ["5.7", "5.8"]
    assert workspace_manifest.route_bootstrap_capable(workspace_manifest.route_spec("godot-native")) is True
    assert workspace_manifest.route_bootstrap_capable(workspace_manifest.route_spec("windows-cross-mingw")) is False
    assert workspace_manifest.route_commands(godot_route) == [
        "fastdis engine godot doctor",
        "fastdis engine godot bootstrap",
        "fastdis engine godot full",
    ]
    assert workspace_manifest.route_commands(mingw_route) == [
        "python tools/windows_wheel_workflow.py doctor",
        "python tools/windows_wheel_workflow.py full --no-isolation",
    ]
    assert workspace_manifest.route_commands(python_route) == [
        "fastdis doctor",
        "python -m pytest",
    ]
    assert workspace_manifest.route_commands(unreal_linux_docker) == [
        "fastdis engine unreal linux-verify --engine-version 5.8 --docker"
    ]
    assert workspace_manifest.route_evidence_commands(unreal_linux_docker) == [
        "fastdis engine unreal linux-verify --engine-version 5.8 --docker"
    ]
    tasks = workspace_manifest.route_tasks(unreal_linux_docker)
    assert [task["id"] for task in tasks] == [
        "fastdis-linux-proof",
        "fastdis-linux-verify",
        "fastdis-linux-demo",
        "grill-linux-proof",
    ]
    assert all(task["parallel_safe"] is True for task in tasks)
    assert {task["route_family"] for task in tasks} == {"fastdis", "grill-dis"}
    assert tasks[0]["commands"] == ["python tools/unreal_workflow.py linux-proof"]
    assert tasks[0]["artifacts"] == [
        "artifacts/verification_reports/unreal_fastdis_baseline/fastdis_unreal_linux_proof.json",
        "artifacts/verification_reports/unreal_fastdis_baseline/fastdis_unreal_linux_proof.md",
    ]
    assert tasks[-1]["artifacts"] == [
        "artifacts/verification_reports/unreal_grill_baseline/grill_unreal_linux_build_proof.json",
        "artifacts/verification_reports/unreal_grill_baseline/grill_unreal_linux_build_proof.md",
    ]
    unity_direct_tasks = workspace_manifest.route_tasks(route)
    assert [task["id"] for task in unity_direct_tasks] == [
        "unity-linux-cross-direct-doctor",
        "unity-linux-cross-direct-build",
    ]
    assert unity_direct_tasks[1]["commands"] == [
        "python tools/build_unity_native_matrix.py build --targets linux --linux-backend direct"
    ]
    unity_docker_tasks = workspace_manifest.route_tasks(unity_docker_route)
    assert [task["id"] for task in unity_docker_tasks] == [
        "unity-linux-docker-doctor",
        "unity-linux-docker-build",
    ]
    assert unity_docker_tasks[1]["commands"] == [
        "python tools/build_unity_native_matrix.py build --targets linux --linux-backend docker"
    ]
    godot_tasks = workspace_manifest.route_tasks(godot_route)
    assert [task["id"] for task in godot_tasks] == [
        "godot-native-doctor",
        "godot-native-bootstrap",
        "godot-native-full",
    ]
    assert godot_tasks[1]["commands"] == ["fastdis engine godot bootstrap"]
    unity_native_tasks = workspace_manifest.route_tasks(unity_native_route)
    assert [task["id"] for task in unity_native_tasks] == [
        "unity-native-discover",
        "unity-native-doctor",
        "unity-native-build",
        "unity-native-verify",
        "unity-native-demo",
    ]
    assert unity_native_tasks[3]["commands"] == [
        "fastdis engine unity runtime-verify --unity-version 6000.5"
    ]
    python_tasks = workspace_manifest.route_tasks(python_route)
    assert [task["id"] for task in python_tasks] == [
        "python-core-doctor",
        "python-core-verify",
    ]
    assert python_tasks[1]["commands"] == ["python -m pytest"]
    mingw_tasks = workspace_manifest.route_tasks(mingw_route)
    assert [task["id"] for task in mingw_tasks] == [
        "windows-cross-mingw-doctor",
        "windows-cross-mingw-full",
    ]
    assert mingw_tasks[1]["commands"] == ["python tools/windows_wheel_workflow.py full --no-isolation"]
    unreal_native_tasks = workspace_manifest.route_tasks(unreal_route)
    assert [task["id"] for task in unreal_native_tasks] == [
        "unreal-native-discover",
        "unreal-native-doctor",
        "unreal-native-build",
        "unreal-native-verify",
        "unreal-native-demo",
    ]
