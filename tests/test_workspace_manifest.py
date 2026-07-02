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
    workspace = workspace_manifest.workspace_metadata(manifest)
    trees = workspace_manifest.product_trees(manifest)

    assert manifest["schema"] == "packet_stoat.workspace_manifest.v1"
    assert workspace["id"] == "packet-stoat"
    assert workspace["core_package"] == "fastdis"
    assert [tree["id"] for tree in trees] == ["fastdis", "grill-dis", "cesium", "fastdis-lattice"]
    assert trees[0]["label"] == "FastDIS"
    assert "src/fastdis" in trees[0]["primary_paths"]
    assert any("Competitor baselines" in ownership for ownership in trees[1]["owns"])
    assert "extensions/cesium" in trees[2]["primary_paths"]
    assert "packages/lattice" in trees[3]["primary_paths"]
    surface_ids = {surface["id"] for surface in workspace_manifest.surface_specs(manifest)}
    route_ids = {route["id"] for route in workspace_manifest.route_specs(manifest)}

    assert {"python", "lattice", "unity", "godot", "unreal", "cesium-unreal", "cesium-unity", "cesium-godot", "cesium-unreal-example", "cesium-unity-example", "cesium-godot-example"} <= surface_ids
    assert {"python-core", "lattice-zorn-surrogate", "unity-linux-cross-direct", "windows-cross-mingw", "cesium-unreal-vendor", "cesium-unity-vendor", "cesium-godot-vendor", "cesium-unreal-example", "cesium-unity-example", "cesium-godot-example"} <= route_ids
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
    lattice = workspace_manifest.surface_spec("lattice", manifest)
    python = workspace_manifest.surface_spec("python", manifest)
    unreal = workspace_manifest.surface_spec("unreal", manifest)
    cesium_unreal = workspace_manifest.surface_spec("cesium-unreal", manifest)
    cesium_unity = workspace_manifest.surface_spec("cesium-unity", manifest)
    cesium_godot = workspace_manifest.surface_spec("cesium-godot", manifest)
    cesium_unreal_example = workspace_manifest.surface_spec("cesium-unreal-example", manifest)
    cesium_unity_example = workspace_manifest.surface_spec("cesium-unity-example", manifest)
    cesium_godot_example = workspace_manifest.surface_spec("cesium-godot-example", manifest)
    unity_hooks = workspace_manifest.surface_hooks(unity, manifest)
    godot_hooks = workspace_manifest.surface_hooks(godot, manifest)
    lattice_hooks = workspace_manifest.surface_hooks(lattice, manifest)
    python_hooks = workspace_manifest.surface_hooks(python, manifest)
    unreal_hooks = workspace_manifest.surface_hooks(unreal, manifest)
    cesium_unreal_hooks = workspace_manifest.surface_hooks(cesium_unreal, manifest)
    cesium_unity_hooks = workspace_manifest.surface_hooks(cesium_unity, manifest)
    cesium_godot_hooks = workspace_manifest.surface_hooks(cesium_godot, manifest)
    cesium_unreal_example_hooks = workspace_manifest.surface_hooks(cesium_unreal_example, manifest)
    cesium_unity_example_hooks = workspace_manifest.surface_hooks(cesium_unity_example, manifest)
    cesium_godot_example_hooks = workspace_manifest.surface_hooks(cesium_godot_example, manifest)
    unreal_versions = workspace_manifest.surface_versions(unreal, manifest)
    cesium_unreal_versions = workspace_manifest.surface_versions(cesium_unreal, manifest)
    cesium_unity_versions = workspace_manifest.surface_versions(cesium_unity, manifest)
    cesium_godot_versions = workspace_manifest.surface_versions(cesium_godot, manifest)
    cesium_unreal_example_versions = workspace_manifest.surface_versions(cesium_unreal_example, manifest)
    python_versions = workspace_manifest.surface_versions(python, manifest)
    lattice_versions = workspace_manifest.surface_versions(lattice, manifest)

    assert unity_hooks["doctor"]["command"] == "fastdis-engine unity doctor --unity-version 6000.5"
    assert unity_hooks["doctor"]["category"] == "lifecycle"
    assert unity_hooks["full"]["status"] == "supported"
    assert godot_hooks["bootstrap"]["command"] == "fastdis-engine godot bootstrap"
    assert lattice_hooks["doctor"]["command"] == "fastdis-lattice doctor"
    assert lattice_hooks["verify"]["command"] == "fastdis-lattice verify"
    assert lattice_hooks["demo"]["command"] == "fastdis-lattice showcase"
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
    assert unreal_hooks["doctor"]["requirements"][0]["supported_versions"] == ["5.7"]
    assert cesium_unreal_hooks["doctor"]["command"] == "python tools/unreal_vendor_workflow.py doctor --vendor cesium"
    assert cesium_unreal_hooks["build"]["command"] == "python tools/unreal_vendor_workflow.py build --vendor cesium --engine-version 5.7"
    assert cesium_unreal_hooks["install-smoke"]["status"] == "supported"
    assert cesium_unreal_hooks["install-smoke"]["command"] == "python tools/unreal_vendor_workflow.py install-smoke --vendor cesium --engine-version 5.7"
    assert cesium_unreal_hooks["doctor"]["requirements"][0]["requirement_kind"] == "env"
    assert cesium_unreal_hooks["full"]["requirements"][1]["version_policy"] == "broad"
    assert cesium_unity_hooks["doctor"]["command"] == "python tools/unity_vendor_workflow.py doctor --vendor cesium-unity --unity-version 6000.5"
    assert cesium_unity_hooks["build"]["command"] == "python tools/unity_vendor_workflow.py build --vendor cesium-unity --unity-version 6000.5"
    assert cesium_unity_hooks["install-smoke"]["status"] == "supported"
    assert cesium_godot_hooks["doctor"]["command"] == "python tools/godot_vendor_workflow.py doctor --vendor cesium-godot"
    assert cesium_godot_hooks["full"]["command"] == "python tools/godot_vendor_workflow.py doctor --vendor cesium-godot"
    assert cesium_unreal_example_hooks["doctor"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py doctor --engine unreal"
    assert cesium_unity_example_hooks["doctor"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py doctor --engine unity"
    assert cesium_godot_example_hooks["doctor"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py doctor --engine godot"
    assert cesium_unreal_example_hooks["full"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py full --engine unreal"
    assert cesium_unity_example_hooks["full"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py full --engine unity"
    assert cesium_godot_example_hooks["full"]["command"] == "python extensions/cesium/tools/cesium_example_workflow.py full --engine godot"
    assert workspace_manifest.surface_preferred_version(unity, manifest) == "6000.5"
    assert workspace_manifest.surface_preferred_version(unreal, manifest) == "5.7"
    assert workspace_manifest.surface_preferred_version(cesium_unreal, manifest) == "5.7"
    assert workspace_manifest.surface_preferred_version(cesium_unity, manifest) == "6000.5"
    assert workspace_manifest.surface_preferred_version(cesium_godot, manifest) == "4.7"
    assert workspace_manifest.surface_preferred_version(cesium_unreal_example, manifest) == "5.7"
    assert [row["version"] for row in unreal_versions] == ["5.7", "5.8"]
    assert [row["version"] for row in cesium_unreal_versions] == ["5.7", "5.8"]
    assert [row["version"] for row in cesium_unity_versions] == ["6000.5"]
    assert [row["version"] for row in cesium_godot_versions] == ["4.7"]
    assert [row["version"] for row in cesium_unreal_example_versions] == ["5.7", "5.8"]
    assert unreal_versions[0]["preferred"] is True
    assert [row["version"] for row in python_versions] == ["3.12", "3.13", "3.14"]
    assert python_versions[-1]["status"] == "preferred"
    assert [row["version"] for row in lattice_versions] == ["0.15.0a5"]


def test_workspace_manifest_host_specific_install_metadata() -> None:
    route = workspace_manifest.route_spec("unity-linux-cross-direct")
    unity_docker_route = workspace_manifest.route_spec("unity-linux-docker")
    unity_native_route = workspace_manifest.route_spec("unity-native")
    lattice_route = workspace_manifest.route_spec("lattice-zorn-surrogate")
    godot_route = workspace_manifest.route_spec("godot-native")
    unreal_route = workspace_manifest.route_spec("unreal-native")
    cesium_unreal_route = workspace_manifest.route_spec("cesium-unreal-vendor")
    cesium_unity_route = workspace_manifest.route_spec("cesium-unity-vendor")
    cesium_godot_route = workspace_manifest.route_spec("cesium-godot-vendor")
    cesium_unreal_example_route = workspace_manifest.route_spec("cesium-unreal-example")
    cesium_unity_example_route = workspace_manifest.route_spec("cesium-unity-example")
    cesium_godot_example_route = workspace_manifest.route_spec("cesium-godot-example")
    unreal_linux_docker = workspace_manifest.route_spec("unreal-linux-docker")
    mingw_route = workspace_manifest.route_spec("windows-cross-mingw")
    python_route = workspace_manifest.route_spec("python-core")

    assert workspace_manifest.route_supported_on_host(route, "windows") is True
    assert workspace_manifest.route_supported_on_host(route, "linux") is False
    assert workspace_manifest.route_installs(route, "windows") == ["zig", "cmake"]
    assert workspace_manifest.route_install_commands(route, "windows") == ["scoop install zig cmake"]
    assert workspace_manifest.route_preferred_surface_version(route) == "6000.5"
    assert workspace_manifest.route_lane_kind(python_route) == "core"
    assert workspace_manifest.route_claim_level(python_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(lattice_route) == "surrogate"
    assert workspace_manifest.route_claim_level(lattice_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(godot_route) == "native"
    assert workspace_manifest.route_claim_level(godot_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(unity_native_route) == "native"
    assert workspace_manifest.route_claim_level(unity_native_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(unreal_route) == "native"
    assert workspace_manifest.route_claim_level(unreal_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(route) == "cross-build"
    assert workspace_manifest.route_claim_level(route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(unity_docker_route) == "cross-build"
    assert workspace_manifest.route_claim_level(unity_docker_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(unreal_linux_docker) == "cross-build"
    assert workspace_manifest.route_claim_level(unreal_linux_docker) == "proof-ready"
    assert workspace_manifest.route_lane_kind(cesium_unreal_route) == "vendor"
    assert workspace_manifest.route_claim_level(cesium_unreal_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(cesium_unity_route) == "vendor"
    assert workspace_manifest.route_claim_level(cesium_unity_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(cesium_godot_route) == "vendor"
    assert workspace_manifest.route_claim_level(cesium_godot_route) == "proof-ready"
    assert workspace_manifest.route_lane_kind(cesium_unreal_example_route) == "example"
    assert workspace_manifest.route_claim_level(cesium_unreal_example_route) == "report-ready"
    assert workspace_manifest.route_lane_kind(cesium_unity_example_route) == "example"
    assert workspace_manifest.route_claim_level(cesium_unity_example_route) == "report-ready"
    assert workspace_manifest.route_lane_kind(cesium_godot_example_route) == "example"
    assert workspace_manifest.route_claim_level(cesium_godot_example_route) == "report-ready"
    assert workspace_manifest.route_commands(lattice_route) == [
        "fastdis-lattice doctor",
        "fastdis-lattice full",
    ]
    assert workspace_manifest.route_commands(unity_native_route) == [
        "fastdis-engine unity discover --format json",
        "fastdis-engine unity doctor --unity-version 6000.5",
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
        "fastdis-engine godot doctor",
        "fastdis-engine godot bootstrap",
        "fastdis-engine godot full",
    ]
    assert workspace_manifest.route_commands(mingw_route) == [
        "python tools/windows_wheel_workflow.py doctor",
        "python tools/windows_wheel_workflow.py full --no-isolation",
    ]
    assert workspace_manifest.route_commands(python_route) == [
        "fastdis doctor",
        "python -m pytest",
    ]
    assert workspace_manifest.route_evidence_commands(lattice_route) == [
        "fastdis-lattice discover",
        "fastdis-lattice doctor",
    ]
    assert workspace_manifest.route_commands(unreal_linux_docker) == [
        "fastdis-engine unreal linux-verify --engine-version 5.7 --docker"
    ]
    assert workspace_manifest.route_commands(cesium_unreal_route) == [
        "python tools/unreal_vendor_workflow.py doctor --vendor cesium",
        "python tools/unreal_vendor_workflow.py full --vendor cesium",
    ]
    assert workspace_manifest.route_commands(cesium_unity_route) == [
        "python tools/unity_vendor_workflow.py doctor --vendor cesium-unity --unity-version 6000.5",
        "python tools/unity_vendor_workflow.py full --vendor cesium-unity --unity-version 6000.5",
    ]
    assert workspace_manifest.route_commands(cesium_godot_route) == [
        "python tools/godot_vendor_workflow.py doctor --vendor cesium-godot",
        "python tools/godot_vendor_workflow.py full --vendor cesium-godot",
    ]
    assert workspace_manifest.route_evidence_commands(cesium_godot_route) == [
        "python tools/godot_vendor_workflow.py build --vendor cesium-godot"
    ]
    assert workspace_manifest.route_commands(cesium_unreal_example_route) == [
        "python extensions/cesium/tools/cesium_example_workflow.py discover --engine unreal",
        "python extensions/cesium/tools/cesium_example_workflow.py full --engine unreal",
    ]
    assert workspace_manifest.route_commands(cesium_unity_example_route) == [
        "python extensions/cesium/tools/cesium_example_workflow.py discover --engine unity",
        "python extensions/cesium/tools/cesium_example_workflow.py full --engine unity",
    ]
    assert workspace_manifest.route_commands(cesium_godot_example_route) == [
        "python extensions/cesium/tools/cesium_example_workflow.py discover --engine godot",
        "python extensions/cesium/tools/cesium_example_workflow.py full --engine godot",
    ]
    assert workspace_manifest.route_evidence_commands(cesium_unreal_example_route) == [
        "python extensions/cesium/tools/cesium_example_workflow.py discover --engine unreal",
        "python extensions/cesium/tools/cesium_example_workflow.py doctor --engine unreal",
    ]
    assert workspace_manifest.route_evidence_commands(unreal_linux_docker) == [
        "fastdis-engine unreal linux-verify --engine-version 5.7 --docker"
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
    lattice_tasks = workspace_manifest.route_tasks(lattice_route)
    assert [task["id"] for task in lattice_tasks] == [
        "lattice-zorn-surrogate-discover",
        "lattice-zorn-surrogate-doctor",
        "lattice-zorn-surrogate-full",
    ]
    assert lattice_tasks[0]["commands"] == ["fastdis-lattice discover"]
    assert lattice_tasks[2]["commands"] == ["fastdis-lattice full"]
    assert unity_docker_tasks[1]["commands"] == [
        "python tools/build_unity_native_matrix.py build --targets linux --linux-backend docker"
    ]
    godot_tasks = workspace_manifest.route_tasks(godot_route)
    assert [task["id"] for task in godot_tasks] == [
        "godot-native-doctor",
        "godot-native-bootstrap",
        "godot-native-full",
    ]
    assert godot_tasks[1]["commands"] == ["fastdis-engine godot bootstrap"]
    unity_native_tasks = workspace_manifest.route_tasks(unity_native_route)
    assert [task["id"] for task in unity_native_tasks] == [
        "unity-native-discover",
        "unity-native-doctor",
        "unity-native-build",
        "unity-native-verify",
        "unity-native-demo",
    ]
    assert unity_native_tasks[3]["commands"] == [
        "fastdis-engine unity runtime-verify --unity-version 6000.5"
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
    cesium_tasks = workspace_manifest.route_tasks(cesium_unreal_route)
    assert [task["id"] for task in cesium_tasks] == [
        "cesium-unreal-vendor-doctor",
        "cesium-unreal-vendor-install-smoke",
        "cesium-unreal-vendor-matrix",
    ]
    assert cesium_tasks[1]["commands"] == ["python tools/unreal_vendor_workflow.py install-smoke --vendor cesium --engine-version 5.7"]
    assert cesium_tasks[2]["commands"] == ["python tools/unreal_vendor_workflow.py full --vendor cesium"]
    cesium_unity_tasks = workspace_manifest.route_tasks(cesium_unity_route)
    assert [task["id"] for task in cesium_unity_tasks] == [
        "cesium-unity-vendor-doctor",
        "cesium-unity-vendor-build",
    ]
    assert cesium_unity_tasks[1]["commands"] == ["python tools/unity_vendor_workflow.py build --vendor cesium-unity --unity-version 6000.5"]
    cesium_godot_tasks = workspace_manifest.route_tasks(cesium_godot_route)
    assert [task["id"] for task in cesium_godot_tasks] == [
        "cesium-godot-vendor-doctor",
        "cesium-godot-vendor-report",
        "cesium-godot-vendor-full",
    ]
    assert cesium_godot_tasks[1]["commands"] == ["python tools/godot_vendor_workflow.py report --vendor cesium-godot"]
    assert cesium_godot_tasks[2]["commands"] == ["python tools/godot_vendor_workflow.py full --vendor cesium-godot"]
    assert cesium_godot_tasks[0]["commands"] == ["python tools/godot_vendor_workflow.py doctor --vendor cesium-godot"]
    cesium_unreal_example_tasks = workspace_manifest.route_tasks(cesium_unreal_example_route)
    assert [task["id"] for task in cesium_unreal_example_tasks] == ["cesium-unreal-example-discover", "cesium-unreal-example-full"]
    assert cesium_unreal_example_tasks[1]["artifacts"] == [
        "artifacts/reports/cesium_examples/cesium_unreal_example.json",
        "artifacts/reports/cesium_examples/cesium_unreal_example.md",
    ]
    cesium_unity_example_tasks = workspace_manifest.route_tasks(cesium_unity_example_route)
    assert [task["id"] for task in cesium_unity_example_tasks] == ["cesium-unity-example-discover", "cesium-unity-example-full"]
    cesium_godot_example_tasks = workspace_manifest.route_tasks(cesium_godot_example_route)
    assert [task["id"] for task in cesium_godot_example_tasks] == ["cesium-godot-example-discover", "cesium-godot-example-full"]
