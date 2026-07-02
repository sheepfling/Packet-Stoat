# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

import unreal


REPORT_PATH = Path(os.environ["FASTDIS_VENDOR_INSTALL_REPORT"])
MARKDOWN_PATH = Path(os.environ["FASTDIS_VENDOR_INSTALL_MARKDOWN"])
PROJECT_DIR = Path(os.environ["FASTDIS_VENDOR_INSTALL_PROJECT_DIR"])
PACKAGE_DIR = Path(os.environ["FASTDIS_VENDOR_INSTALL_PACKAGE_DIR"])
PLUGIN_NAME = os.environ["FASTDIS_VENDOR_INSTALL_PLUGIN_NAME"]
UPLUGIN_PATH = Path(os.environ["FASTDIS_VENDOR_INSTALL_UPLUGIN"])
VENDOR_ID = os.environ.get("FASTDIS_VENDOR_INSTALL_VENDOR", "vendor")


def write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Unreal Vendor Install Smoke",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- plugin_name: `{report['plugin_name']}`",
        f"- status: `{report['status']}`",
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


def main() -> None:
    checks: list[dict] = []
    package_descriptor_exists = UPLUGIN_PATH.is_file()
    checks.append(
        {
            "name": "package_descriptor_present",
            "status": "ok" if package_descriptor_exists else "fail",
            "detail": str(UPLUGIN_PATH),
        }
    )

    world = unreal.EditorLevelLibrary.get_editor_world()
    checks.append(
        {
            "name": "editor_world_available",
            "status": "ok" if world is not None else "fail",
            "detail": world.get_name() if world is not None else "editor world unavailable",
        }
    )

    project_descriptor_path = next(PROJECT_DIR.glob("*.uproject"), None)
    plugin_enabled = False
    if project_descriptor_path is not None and project_descriptor_path.is_file():
        try:
            payload = json.loads(project_descriptor_path.read_text(encoding="utf-8"))
            plugins = payload.get("Plugins") if isinstance(payload, dict) else None
            if isinstance(plugins, list):
                plugin_enabled = any(
                    isinstance(plugin, dict)
                    and plugin.get("Name") == PLUGIN_NAME
                    and plugin.get("Enabled") is True
                    for plugin in plugins
                )
        except Exception:
            plugin_enabled = False
    checks.append(
        {
            "name": "plugin_enabled_in_project",
            "status": "ok" if plugin_enabled else "fail",
            "detail": PLUGIN_NAME if plugin_enabled else f"{PLUGIN_NAME} not enabled in scratch project",
        }
    )

    status = "pass" if all(check["status"] == "ok" for check in checks) else "fail"
    report = {
        "schema": "packet_stoat.unreal_vendor_install_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vendor": VENDOR_ID,
        "plugin_name": PLUGIN_NAME,
        "status": status,
        "project_dir": str(PROJECT_DIR),
        "package_dir": str(PACKAGE_DIR),
        "checks": checks,
    }
    write_report(report)
    unreal.log("FASTDIS_VENDOR_INSTALL_SMOKE complete")
    if status != "pass":
        raise RuntimeError("Unreal vendor install smoke failed")


if __name__ == "__main__":
    main()
