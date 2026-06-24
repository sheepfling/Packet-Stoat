from datetime import datetime, timezone
import json
import os
from pathlib import Path

import unreal


REPORT_PATH = Path(os.environ["FASTDIS_PACKAGED_INSTALL_REPORT"])
MARKDOWN_PATH = Path(os.environ["FASTDIS_PACKAGED_INSTALL_MARKDOWN"])
PROJECT_DIR = Path(os.environ["FASTDIS_PACKAGED_INSTALL_PROJECT_DIR"])
PACKAGE_DIR = Path(os.environ["FASTDIS_PACKAGED_INSTALL_PACKAGE_DIR"])
DEMO_MAP = os.environ.get("FASTDIS_PACKAGED_INSTALL_DEMO_MAP", "/FastDis/Examples/FastDis_Demo")
DEMO_CONTROLLER = "/FastDis/Examples/BP_FastDisDemoController.BP_FastDisDemoController"
STATUS_WIDGET = "/FastDis/Examples/WBP_FastDisRuntimeStatus.WBP_FastDisRuntimeStatus"
MAPPING_ASSET = "/FastDis/Examples/DA_FastDisEntityMappings.DA_FastDisEntityMappings"


def write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Unreal Packaged Install Smoke",
        "",
        f"- status: `{report['status']}`",
        f"- demo_map: `{report['demo_map']}`",
        f"- project_dir: `{report['project_dir']}`",
        f"- package_dir: `{report['package_dir']}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        lines.append(f"- `{check['name']}`: `{check['status']}` {check['detail']}")
    lines.append("")
    MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.write_text("\n".join(lines), encoding="utf-8")


def asset_check(path: str) -> dict:
    exists = unreal.EditorAssetLibrary.does_asset_exist(path)
    return {
        "name": path,
        "status": "ok" if exists else "fail",
        "detail": "asset exists" if exists else "asset missing",
    }


def main() -> None:
    checks: list[dict] = []
    for asset in [DEMO_CONTROLLER, STATUS_WIDGET, MAPPING_ASSET]:
        checks.append(asset_check(asset))

    map_loaded = unreal.EditorLoadingAndSavingUtils.load_map(DEMO_MAP)
    checks.append(
        {
            "name": "load_demo_map",
            "status": "ok" if map_loaded else "fail",
            "detail": DEMO_MAP if map_loaded else f"failed to load {DEMO_MAP}",
        }
    )

    actor_count = 0
    demo_controller_count = 0
    if map_loaded:
        world = unreal.EditorLevelLibrary.get_editor_world()
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        actor_count = len(actors)
        demo_controller_count = sum(1 for actor in actors if "FastDisDemoController" in actor.get_class().get_name())
        checks.append(
            {
                "name": "demo_controller_present",
                "status": "ok" if demo_controller_count > 0 else "fail",
                "detail": f"found {demo_controller_count} FastDisDemoController actor(s)",
            }
        )

    status = "pass" if all(check["status"] == "ok" for check in checks) else "fail"
    report = {
        "schema": "fastdis.unreal_packaged_install_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "demo_map": DEMO_MAP,
        "project_dir": str(PROJECT_DIR),
        "package_dir": str(PACKAGE_DIR),
        "checks": checks,
        "world_actor_count": actor_count,
        "demo_controller_count": demo_controller_count,
    }
    write_report(report)
    unreal.log("FASTDIS_PACKAGED_INSTALL_SMOKE complete")
    if status != "pass":
        raise RuntimeError("FastDIS packaged install smoke failed")


if __name__ == "__main__":
    main()
