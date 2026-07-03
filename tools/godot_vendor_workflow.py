#!/usr/bin/env python3
"""Operator-facing Godot vendor-plugin workflow wrapper."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

import build_godot_extension
import godot_env
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIN_GODOT_VERSION = "4.1"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "godot_vendor_plugin"
DEFAULT_BUILD_TARGET = "template_release"
DEFAULT_COMPILE_TARGET = "extension"
DEFAULT_PLUGIN_SUBDIR_CANDIDATES = (
    Path("godot3dtiles") / "addons" / "cesium_godot",
    Path("addons") / "cesium_godot",
)


def vendor_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise SystemExit("Vendor id must not be empty.")
    return slug


def vendor_env_token(value: str) -> str:
    return vendor_slug(value).replace("-", "_").upper()


def _resolve_env_path(keys: list[str]) -> Path | None:
    for key in keys:
        raw = os.environ.get(key)
        if raw:
            return Path(raw).expanduser()
    return None


def resolve_plugin_root(vendor: str, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_token = vendor_env_token(vendor)
    candidate = _resolve_env_path(
        [
            f"FASTDIS_{env_token}_PLUGIN_ROOT",
            f"FASTDIS_{env_token}_GODOT_PLUGIN_ROOT",
            "FASTDIS_GODOT_VENDOR_PLUGIN_ROOT",
        ]
    )
    return None if candidate is None else candidate.resolve()


def resolve_addon_root(plugin_root: Path | None, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute() and plugin_root is not None:
            candidate = plugin_root / candidate
        return candidate.resolve()
    if plugin_root is None:
        return None
    for relative in DEFAULT_PLUGIN_SUBDIR_CANDIDATES:
        candidate = plugin_root / relative
        if candidate.is_dir():
            return candidate.resolve()
    return None


def parse_version(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    if not match:
        return ()
    return tuple(int(part) for part in match.groups(default="0"))


def version_at_least(discovered: str | None, minimum: str) -> bool:
    discovered_tuple = parse_version(discovered)
    minimum_tuple = parse_version(minimum)
    if not discovered_tuple or not minimum_tuple:
        return False
    return discovered_tuple >= minimum_tuple


def detected_godot_version() -> str | None:
    return build_godot_extension.detected_godot_version()


def _godot_root_hint() -> str:
    system = godot_env.platform.system().lower()
    if system == "windows":
        return r'FASTDIS_GODOT_ROOTS="C:\Users\Public\Godot\engines;C:\Godot;C:\Program Files\Godot"'
    if system == "darwin":
        return 'FASTDIS_GODOT_ROOTS="/Applications:$HOME/Applications:$HOME/Dev/Godot"'
    return 'FASTDIS_GODOT_ROOTS="$HOME/bin:$HOME/Dev/Godot:/usr/local/bin"'


def _selected_stable_over_newer_prerelease(host: dict[str, object], selected_version: str | None) -> str | None:
    if not selected_version:
        return None
    selected_kind = "unknown"
    selected_parsed: tuple[int, ...] = ()
    for install in host.get("installs") or []:
        if str(install.get("version") or "") != selected_version:
            continue
        selected_kind = str(install.get("version_kind") or "unknown")
        selected_parsed = parse_version(selected_version)
        break
    if selected_kind != "stable" or not selected_parsed:
        return None
    newer_prereleases: list[str] = []
    for install in host.get("installs") or []:
        version = str(install.get("version") or "")
        kind = str(install.get("version_kind") or "")
        if not kind.startswith("prerelease:"):
            continue
        if parse_version(version) > selected_parsed:
            newer_prereleases.append(version)
    if not newer_prereleases:
        return None
    return ",".join(newer_prereleases)


def doctor_payload(
    vendor: str,
    plugin_root_arg: str | None,
    addon_root_arg: str | None,
    min_godot_version: str,
) -> dict[str, object]:
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    addon_root = resolve_addon_root(plugin_root, addon_root_arg)
    godot = godot_env.resolve_godot()
    godot_version = detected_godot_version()
    host = godot_env.describe_host()

    payload: dict[str, object] = {
        "vendor": vendor_slug(vendor),
        "status": "ok",
        "plugin_root": str(plugin_root) if plugin_root is not None else None,
        "addon_root": str(addon_root) if addon_root is not None else None,
        "godot": godot,
        "godot_version": godot_version,
        "minimum_godot_version": min_godot_version,
        "host": host,
        "checks": [],
        "next_steps": [],
    }

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if plugin_root is None:
        add_check("plugin_root", "fail", f"no plugin root configured for vendor {vendor_slug(vendor)}")
    elif not plugin_root.is_dir():
        add_check("plugin_root", "fail", f"plugin root is not a directory: {plugin_root}")
    else:
        add_check("plugin_root", "ok", str(plugin_root))

    if addon_root is None:
        add_check("addon_root", "fail", "could not find addons/cesium_godot under the vendor checkout")
    elif not addon_root.is_dir():
        add_check("addon_root", "fail", f"addon root is not a directory: {addon_root}")
    else:
        add_check("addon_root", "ok", str(addon_root))

    plugin_cfg = addon_root / "plugin.cfg" if addon_root is not None else None
    gdextension = addon_root / "Godot3DTiles.gdextension" if addon_root is not None else None
    add_check(
        "plugin_cfg",
        "ok" if plugin_cfg is not None and plugin_cfg.is_file() else "fail",
        str(plugin_cfg) if plugin_cfg is not None else "missing plugin.cfg path",
    )
    add_check(
        "gdextension_descriptor",
        "ok" if gdextension is not None and gdextension.is_file() else "fail",
        str(gdextension) if gdextension is not None else "missing Godot3DTiles.gdextension path",
    )
    add_check("godot", "ok" if godot else "fail", str(godot or "missing godot executable"))
    if not godot:
        add_check("godot discovery roots", "warn", f"no install discovered; try {_godot_root_hint()}")
    add_check(
        "godot_version",
        "ok" if version_at_least(godot_version, min_godot_version) else "fail",
        f"discovered={godot_version or 'unknown'} minimum={min_godot_version}",
    )
    selected_kind = next(
        (str(install.get("version_kind") or "unknown") for install in host.get("installs") or [] if str(install.get("version") or "") == str(godot_version or "")),
        "unknown",
    )
    if godot_version:
        add_check("godot_version_kind", "ok", selected_kind)
    prerelease_note = _selected_stable_over_newer_prerelease(host, godot_version)
    if prerelease_note:
        add_check("version selection", "ok", f"selected stable {godot_version}; newer prerelease installs also exist: {prerelease_note}")

    host_platform = str(host.get("platform") or "unknown")
    host_arch = str(host.get("arch") or "unknown")
    platform_ok = host_platform in {"windows", "linux"} or (host_platform == "macos" and host_arch == "arm64")
    add_check(
        "host_platform_support",
        "ok" if platform_ok else "fail",
        f"{host_platform}/{host_arch}",
    )

    payload["checks"] = checks
    failures = [check for check in checks if check["status"] == "fail"]
    payload["status"] = "ok" if not failures else "needs-attention"
    if failures:
        payload["next_steps"] = [
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT to the 3D-Tiles-For-Godot checkout root, or pass --plugin-root.",
            "Point FASTDIS_GODOT at a Godot 4.1+ editor if auto-discovery does not find the right install.",
            f"If Godot is installed outside the standard locations, try {_godot_root_hint()}.",
            "Ensure the vendor checkout contains addons/cesium_godot/plugin.cfg and Godot3DTiles.gdextension.",
        ]
    else:
        payload["next_steps"] = [
            f"Current Godot route is compatible with the checked 3D Tiles plugin layout: Godot {godot_version}.",
            "If needed later, add a scratch-project import smoke on top of this doctor lane.",
        ]
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    print(f"Godot vendor doctor for {payload['vendor']}")
    print(f"status: {payload['status']}")
    print(f"plugin_root: {payload['plugin_root'] or 'missing'}")
    print(f"addon_root: {payload['addon_root'] or 'missing'}")
    print(f"godot: {payload['godot'] or 'missing'}")
    print(f"godot_version: {payload['godot_version'] or 'unknown'}")
    print(f"minimum_godot_version: {payload['minimum_godot_version']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def _default_report_paths(vendor: str) -> tuple[Path, Path]:
    base = DEFAULT_REPORT_DIR / vendor_slug(vendor)
    return base.with_suffix(".json"), base.with_suffix(".md")


def _default_build_paths(vendor: str) -> tuple[Path, Path, Path]:
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_build"
    return base.with_suffix(".json"), base.with_suffix(".md"), base.with_suffix(".log")


def _default_handoff_paths(vendor: str) -> tuple[Path, Path]:
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_upstream_handoff"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _build_arch_name() -> str:
    return "arm64" if godot_env.host_arch_name() == "arm64" else "x64"


def resolve_sconstruct(plugin_root: Path | None) -> Path | None:
    if plugin_root is None:
        return None
    for name in ("SConstruct", "SConstruct.py"):
        candidate = plugin_root / name
        if candidate.is_file():
            return candidate
    return None


def build_command(
    plugin_root: Path,
    *,
    scons: str,
    target: str,
    compile_target: str,
    production: bool,
    scons_jobs: int,
) -> list[str]:
    command = [scons]
    sconstruct = resolve_sconstruct(plugin_root)
    if sconstruct is not None and sconstruct.name != "SConstruct":
        command.extend(["-f", sconstruct.name])
    command.extend(
        [
            f"arch={_build_arch_name()}",
            f"compileTarget={compile_target}",
            f"target={target}",
            f"-j{max(1, scons_jobs)}",
            "buildCesium=YES",
        ]
    )
    if production:
        command.append("production=yes")
    return command


def built_artifact_candidates(plugin_root: Path, target: str) -> list[Path]:
    bin_dir = plugin_root / "godot3dtiles" / "bin"
    if not bin_dir.is_dir():
        return []
    platform_name = godot_env.host_platform_name()
    arch_name = godot_env.host_arch_name()
    if platform_name == "windows":
        patterns = [f"Godot3DTiles.windows.{target}.{arch_name}.dll"]
    elif platform_name == "macos":
        patterns = [f"libGodot3DTiles.macos.{target}.{arch_name}.dylib", f"libGodot3DTiles.macos.{target}.dylib"]
    else:
        patterns = [f"libGodot3DTiles.linux.{target}.{arch_name}.so"]
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(sorted(bin_dir.glob(pattern)))
    return [path.resolve() for path in matches if path.is_file()]


def _tail(text: str, lines: int = 20) -> list[str]:
    rows = [row for row in text.splitlines() if row.strip()]
    return rows[-lines:]


def classify_build_failure(report: dict[str, object]) -> str:
    status = str(report.get("status") or "")
    if status == "pass":
        return "verified-build"
    if status == "dry-run":
        return "dry-run"
    if not report.get("plugin_root") or not report.get("sconstruct"):
        return "checkout-layout"
    if not report.get("scons"):
        return "toolchain-missing"
    failure_text = "\n".join(str(line) for line in report.get("failure_tail", []))
    lowered = failure_text.lower()
    if any(token in lowered for token in ("error c", ": error:", "fatal error", "undefined reference", "ld:", "linker")):
        return "compile-or-link"
    if report.get("returncode") is not None:
        return "build-failed"
    return "needs-triage"


def process_provenance_for_build(target: str, compile_target: str) -> dict[str, object]:
    return {
        "leading_edge_reporting": True,
        "process_matters_as_evidence": True,
        "build_characteristics": {
            "heavy_native_build": True,
            "expected_runtime_class": "long-running native dependency bootstrap plus C++ compile",
            "doctor_should_remain_lightweight": True,
        },
        "operator_interventions": [
            {
                "kind": "build-flag",
                "value": "buildCesium=YES",
                "reason": "force noninteractive upstream native bootstrap so the lane can run unattended and report a deterministic result",
            },
            {
                "kind": "build-flag",
                "value": f"target={target}",
                "reason": "pin the Godot wrapper lane being evaluated",
            },
            {
                "kind": "build-flag",
                "value": f"compileTarget={compile_target}",
                "reason": "record the upstream build surface under test",
            },
        ],
        "reporting_expectation": "Any workaround, version-forward step, cache normalization, or manual source-prep step must be reported alongside the final pass/fail result.",
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Godot Vendor Report",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- mode: `{payload.get('mode', 'report')}`",
        f"- status: `{payload['status']}`",
        f"- plugin_root: `{payload.get('plugin_root') or ''}`",
        f"- addon_root: `{payload.get('addon_root') or ''}`",
        f"- godot: `{payload.get('godot') or ''}`",
        f"- godot_version: `{payload.get('godot_version') or 'unknown'}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks", []):
        lines.append(f"- {check['name']}: `{check['status']}` ({check['detail']})")
    lines.extend(["", "## Next Steps", ""])
    for step in payload.get("next_steps", []):
        lines.append(f"- {step}")
    return "\n".join(lines)


def write_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def render_handoff_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Cesium Godot Upstream Handoff",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- status: `{payload['status']}`",
        f"- failure_class: `{payload['failure_class']}`",
        f"- source_repo: `{payload['source_repo']}`",
        f"- build_report_json: `{payload['build_report_json']}`",
        f"- build_log: `{payload['build_log']}`",
        "",
        "## Suggested Title",
        "",
        payload["title"],
        "",
        "## Suggested Issue Body",
        "",
        payload["issue_body_markdown"].rstrip(),
        "",
    ]
    return "\n".join(lines)


def write_handoff(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_handoff_markdown(payload), encoding="utf-8")


def report_payload(
    vendor: str,
    plugin_root_arg: str | None,
    addon_root_arg: str | None,
    min_godot_version: str,
) -> dict[str, object]:
    payload = doctor_payload(vendor, plugin_root_arg, addon_root_arg, min_godot_version)
    json_out, md_out = _default_report_paths(vendor)
    return {
        "schema": "packet_stoat.godot_vendor_plugin_report.v1",
        "mode": "report",
        **payload,
        "report_json": str(json_out),
        "report_markdown": str(md_out),
        "workflow_commands": {
            "discover": "python tools/godot_vendor_workflow.py discover",
            "doctor": f"python tools/godot_vendor_workflow.py doctor --vendor {vendor_slug(vendor)}",
            "report": f"python tools/godot_vendor_workflow.py report --vendor {vendor_slug(vendor)}",
            "full": f"python tools/godot_vendor_workflow.py full --vendor {vendor_slug(vendor)}",
        },
        "fix_report": {
            "upstream_project": vendor_slug(vendor),
            "host_platform": str(payload["host"].get("platform") or "unknown"),
            "host_arch": str(payload["host"].get("arch") or "unknown"),
            "minimum_godot_version": min_godot_version,
            "current_gap": "doctor-only validation; no scratch-project import smoke yet",
            "recommended_upstream_packet": [
                "Capture addon layout or version drift against the expected cesium_godot structure.",
                "Attach this JSON/Markdown report to the upstream Cesium for Godot issue or PR.",
            ],
        },
    }


def build_payload(
    vendor: str,
    plugin_root_arg: str | None,
    addon_root_arg: str | None,
    min_godot_version: str,
    json_out_arg: str | None,
    md_out_arg: str | None,
    log_out_arg: str | None,
    target: str,
    compile_target: str,
    scons_jobs: int,
    dry_run: bool,
) -> dict[str, object]:
    doctor = doctor_payload(vendor, plugin_root_arg, addon_root_arg, min_godot_version)
    plugin_root = Path(doctor["plugin_root"]).resolve() if doctor.get("plugin_root") else None
    host = doctor["host"]
    json_out, md_out, log_out = _default_build_paths(vendor)
    if json_out_arg:
        json_out = Path(json_out_arg).expanduser().resolve()
    if md_out_arg:
        md_out = Path(md_out_arg).expanduser().resolve()
    if log_out_arg:
        log_out = Path(log_out_arg).expanduser().resolve()

    scons = str(host.get("scons") or godot_env.resolve_scons() or "")
    sconstruct = resolve_sconstruct(plugin_root)
    command = (
        build_command(
            plugin_root,
            scons=scons,
            target=target,
            compile_target=compile_target,
            production=target == "template_release",
            scons_jobs=scons_jobs,
        )
        if plugin_root is not None and scons
        else []
    )

    report: dict[str, object] = {
        "schema": "packet_stoat.godot_vendor_plugin_build.v1",
        "mode": "build",
        "vendor": doctor["vendor"],
        "status": "needs-attention",
        "doctor_status": doctor["status"],
        "plugin_root": doctor["plugin_root"],
        "addon_root": doctor["addon_root"],
        "godot": doctor["godot"],
        "godot_version": doctor["godot_version"],
        "minimum_godot_version": min_godot_version,
        "host": host,
        "target": target,
        "compile_target": compile_target,
        "scons": scons or None,
        "sconstruct": str(sconstruct) if sconstruct is not None else None,
        "build_command": command,
        "report_json": str(json_out),
        "report_markdown": str(md_out),
        "log": str(log_out),
        "returncode": None,
        "artifact_paths": [],
        "build_status": "not-run",
        "failure_tail": [],
        "doctor_checks": doctor["checks"],
        "next_steps": [],
        "process_provenance": process_provenance_for_build(target, compile_target),
        "fix_report": {
            "upstream_project": vendor_slug(vendor),
            "source_repo": "https://github.com/Battle-Road-Labs/3D-Tiles-For-Godot",
            "issue_kind": "compile-regression" if doctor["status"] == "ok" else "environment-or-layout",
            "target": target,
            "compile_target": compile_target,
            "host_platform": str(host.get("platform") or "unknown"),
            "host_arch": str(host.get("arch") or "unknown"),
            "report_log": str(log_out),
            "suggested_packet": [
                "Include the exact SCons command and the failure tail in the upstream issue or PR packet.",
                "Call out the Godot version, target lane, and whether the failure reproduces on the supported host matrix.",
            ],
        },
    }

    if plugin_root is None or not plugin_root.is_dir():
        report["next_steps"] = [
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT to the Battle-Road 3D-Tiles-For-Godot checkout root, or pass --plugin-root.",
            "Retry the build proof once the vendor checkout is present locally.",
        ]
        return report
    if not scons:
        report["next_steps"] = [
            "Install SCons or set FASTDIS_SCONS so the Battle-Road plugin build can run.",
            "Retry the build proof after SCons resolves on PATH.",
        ]
        return report
    if sconstruct is None:
        report["next_steps"] = [
            f"Expected SConstruct or SConstruct.py under {plugin_root}.",
            "Verify the checkout is Battle-Road-Labs/3D-Tiles-For-Godot and not just the addon subtree.",
        ]
        return report
    if dry_run:
        report["status"] = "dry-run"
        report["build_status"] = "dry-run"
        report["next_steps"] = [
            "Run the same command without --dry-run to capture a real build proof or compile failure report.",
        ]
        return report

    completed = subprocess.run(
        command,
        cwd=plugin_root,
        env=godot_env.build_env(),
        capture_output=True,
        text=True,
    )
    combined_log = ((completed.stdout or "") + ("\n" if completed.stdout and completed.stderr else "") + (completed.stderr or "")).strip()
    log_out.parent.mkdir(parents=True, exist_ok=True)
    log_out.write_text((combined_log + "\n") if combined_log else "", encoding="utf-8")
    artifacts = built_artifact_candidates(plugin_root, target)
    report["returncode"] = completed.returncode
    report["artifact_paths"] = [str(path) for path in artifacts]
    report["failure_tail"] = _tail(combined_log)
    report["build_status"] = "pass" if completed.returncode == 0 and artifacts else "fail"
    report["status"] = "pass" if report["build_status"] == "pass" else "fail"
    if report["status"] == "pass":
        report["next_steps"] = [
            "Copy the built addon payload into a scratch Godot project and verify plugin enablement.",
            "Attach the artifact paths to the Cesium example packet for this engine lane.",
        ]
        report["fix_report"]["issue_kind"] = "verified-build"
    else:
        report["next_steps"] = [
            "Treat this as a valid upstream regression packet if the same command fails on a supported host/toolchain.",
            "Use the captured log tail and full log file to prepare the Battle-Road issue or PR.",
        ]
    return report


def handoff_payload(
    vendor: str,
    plugin_root_arg: str | None,
    addon_root_arg: str | None,
    min_godot_version: str,
    build_json_out_arg: str | None,
    build_md_out_arg: str | None,
    log_out_arg: str | None,
    target: str,
    compile_target: str,
    scons_jobs: int,
    dry_run: bool,
) -> dict[str, object]:
    build_report = build_payload(
        vendor,
        plugin_root_arg,
        addon_root_arg,
        min_godot_version,
        build_json_out_arg,
        build_md_out_arg,
        log_out_arg,
        target,
        compile_target,
        scons_jobs,
        dry_run,
    )
    failure_class = classify_build_failure(build_report)
    handoff_json, handoff_md = _default_handoff_paths(vendor)
    host = build_report["host"]
    title = (
        f"{vendor_slug(vendor)} {target} build fails on "
        f"{host.get('platform', 'unknown')}/{host.get('arch', 'unknown')}"
        if build_report.get("status") == "fail"
        else f"{vendor_slug(vendor)} {target} build verification on {host.get('platform', 'unknown')}/{host.get('arch', 'unknown')}"
    )
    repro_command = " ".join(str(part) for part in build_report.get("build_command", [])) or "unavailable"
    body_lines = [
        "## Summary",
        f"- classification: `{failure_class}`",
        f"- vendor: `{build_report['vendor']}`",
        f"- godot_version: `{build_report.get('godot_version') or 'unknown'}`",
        f"- target: `{build_report.get('target')}`",
        f"- compile_target: `{build_report.get('compile_target')}`",
        f"- host: `{host.get('platform', 'unknown')}/{host.get('arch', 'unknown')}`",
        f"- status: `{build_report.get('status')}`",
        "",
        "## Repro",
        f"```bash\n{repro_command}\n```",
        "",
        "## Evidence",
        f"- build_report_json: `{build_report['report_json']}`",
        f"- build_report_markdown: `{build_report['report_markdown']}`",
        f"- build_log: `{build_report['log']}`",
    ]
    failure_tail = [str(line) for line in build_report.get("failure_tail", [])]
    if failure_tail:
        body_lines.extend(["", "## Failure Tail", "```text", *failure_tail, "```"])
    body_lines.extend(
        [
            "",
            "## Notes",
            "- This packet was generated from the Packet Stoat Cesium Godot vendor lane.",
            "- A nonzero build is considered valid evidence when the upstream plugin is not yet compatible with the target engine/toolchain.",
        ]
    )
    return {
        "schema": "packet_stoat.cesium_godot_upstream_handoff.v1",
        "mode": "handoff",
        "status": "ready" if failure_class in {"verified-build", "compile-or-link", "build-failed"} else "needs-attention",
        "vendor": build_report["vendor"],
        "source_repo": "https://github.com/Battle-Road-Labs/3D-Tiles-For-Godot",
        "title": title,
        "failure_class": failure_class,
        "repro_command": repro_command,
        "build_report_json": build_report["report_json"],
        "build_report_markdown": build_report["report_markdown"],
        "build_log": build_report["log"],
        "handoff_json": str(handoff_json),
        "handoff_markdown": str(handoff_md),
        "issue_body_markdown": "\n".join(body_lines) + "\n",
        "build_report": build_report,
    }


def full_payload(
    vendor: str,
    plugin_root_arg: str | None,
    addon_root_arg: str | None,
    min_godot_version: str,
    json_out_arg: str | None,
    md_out_arg: str | None,
    log_out_arg: str | None,
    target: str,
    compile_target: str,
    scons_jobs: int,
    dry_run: bool,
) -> dict[str, object]:
    report = build_payload(
        vendor,
        plugin_root_arg,
        addon_root_arg,
        min_godot_version,
        json_out_arg,
        md_out_arg,
        log_out_arg,
        target,
        compile_target,
        scons_jobs,
        dry_run,
    )
    return {
        **report,
        "schema": "packet_stoat.godot_vendor_plugin_full.v1",
        "mode": "full",
        "execution_plan": [
            "python tools/godot_vendor_workflow.py discover",
            f"python tools/godot_vendor_workflow.py doctor --vendor {vendor_slug(vendor)}",
            f"python tools/godot_vendor_workflow.py build --vendor {vendor_slug(vendor)}",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List discovered Godot/SCons tools and host settings")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Validate a vendor Godot plugin root against the current Godot install")
    doctor.add_argument("--vendor", required=True, help="Vendor id, for example cesium-godot")
    doctor.add_argument("--plugin-root", help="Vendor plugin checkout root")
    doctor.add_argument("--addon-root", help="Explicit addon root, for example addons/cesium_godot")
    doctor.add_argument("--min-godot-version", default=DEFAULT_MIN_GODOT_VERSION)
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build the vendor Godot plugin with the upstream SCons route and capture a proof report")
    build.add_argument("--vendor", required=True, help="Vendor id, for example cesium-godot")
    build.add_argument("--plugin-root", help="Vendor plugin checkout root")
    build.add_argument("--addon-root", help="Explicit addon root, for example addons/cesium_godot")
    build.add_argument("--min-godot-version", default=DEFAULT_MIN_GODOT_VERSION)
    build.add_argument("--target", default=DEFAULT_BUILD_TARGET)
    build.add_argument("--compile-target", default=DEFAULT_COMPILE_TARGET)
    build.add_argument("--scons-jobs", type=int, default=1)
    build.add_argument("--json-out", help="JSON report output path")
    build.add_argument("--md-out", help="Markdown report output path")
    build.add_argument("--log-out", help="Build log output path")
    build.add_argument("--dry-run", action="store_true")

    handoff = subparsers.add_parser("handoff", help="Generate an upstream-ready issue or PR handoff packet from the vendor build lane")
    handoff.add_argument("--vendor", required=True, help="Vendor id, for example cesium-godot")
    handoff.add_argument("--plugin-root", help="Vendor plugin checkout root")
    handoff.add_argument("--addon-root", help="Explicit addon root, for example addons/cesium_godot")
    handoff.add_argument("--min-godot-version", default=DEFAULT_MIN_GODOT_VERSION)
    handoff.add_argument("--target", default=DEFAULT_BUILD_TARGET)
    handoff.add_argument("--compile-target", default=DEFAULT_COMPILE_TARGET)
    handoff.add_argument("--scons-jobs", type=int, default=1)
    handoff.add_argument("--build-json-out", help="JSON build report output path")
    handoff.add_argument("--build-md-out", help="Markdown build report output path")
    handoff.add_argument("--log-out", help="Build log output path")
    handoff.add_argument("--json-out", help="JSON handoff output path")
    handoff.add_argument("--md-out", help="Markdown handoff output path")
    handoff.add_argument("--dry-run", action="store_true")

    for name in ("report", "full"):
        sub = subparsers.add_parser(name, help=f"Write a {name} artifact for a vendor Godot plugin lane")
        sub.add_argument("--vendor", required=True, help="Vendor id, for example cesium-godot")
        sub.add_argument("--plugin-root", help="Vendor plugin checkout root")
        sub.add_argument("--addon-root", help="Explicit addon root, for example addons/cesium_godot")
        sub.add_argument("--min-godot-version", default=DEFAULT_MIN_GODOT_VERSION)
        sub.add_argument("--json-out", help="JSON report output path")
        sub.add_argument("--md-out", help="Markdown report output path")
        if name == "full":
            sub.add_argument("--log-out", help="Build log output path")
            sub.add_argument("--target", default=DEFAULT_BUILD_TARGET)
            sub.add_argument("--compile-target", default=DEFAULT_COMPILE_TARGET)
            sub.add_argument("--scons-jobs", type=int, default=1)
            sub.add_argument("--dry-run", action="store_true")

    return parser.parse_args(argv)


def command_discover(args: argparse.Namespace) -> int:
    payload = godot_env.describe_host()
    payload["godot_version"] = detected_godot_version()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        installs = payload.get("installs") or []
        if not payload["godot"]:
            print("No Godot installs discovered.")
            print(f"Hint: try {_godot_root_hint()}")
            return 1
        print(f"godot: {payload['godot']}")
        print(f"godot_version: {payload['godot_version']}")
        print(f"scons: {payload.get('scons')}")
        for install in installs:
            print(f"{install.get('version') or 'unknown'}: {install.get('path') or install.get('install_root') or 'unknown'}")
            print(f"  version_kind: {install.get('version_kind') or 'unknown'}")
            print(f"  binary_kind: {install.get('binary_kind') or 'unknown'}")
            print(f"  source: {install.get('source') or 'unknown'}")
    return 0 if payload["godot"] else 1


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.vendor, args.plugin_root, args.addon_root, args.min_godot_version)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_report(args: argparse.Namespace) -> int:
    payload = report_payload(args.vendor, args.plugin_root, args.addon_root, args.min_godot_version)
    json_out, md_out = _default_report_paths(args.vendor)
    if args.json_out:
        json_out = Path(args.json_out).expanduser().resolve()
    if args.md_out:
        md_out = Path(args.md_out).expanduser().resolve()
    payload["report_json"] = str(json_out)
    payload["report_markdown"] = str(md_out)
    write_report(payload, json_out, md_out)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    payload = build_payload(
        args.vendor,
        args.plugin_root,
        args.addon_root,
        args.min_godot_version,
        args.json_out,
        args.md_out,
        args.log_out,
        args.target,
        args.compile_target,
        args.scons_jobs,
        args.dry_run,
    )
    write_report(payload, Path(payload["report_json"]), Path(payload["report_markdown"]))
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"pass", "dry-run"} else 2


def command_handoff(args: argparse.Namespace) -> int:
    payload = handoff_payload(
        args.vendor,
        args.plugin_root,
        args.addon_root,
        args.min_godot_version,
        args.build_json_out,
        args.build_md_out,
        args.log_out,
        args.target,
        args.compile_target,
        args.scons_jobs,
        args.dry_run,
    )
    json_out, md_out = _default_handoff_paths(args.vendor)
    if args.json_out:
        json_out = Path(args.json_out).expanduser().resolve()
    if args.md_out:
        md_out = Path(args.md_out).expanduser().resolve()
    payload["handoff_json"] = str(json_out)
    payload["handoff_markdown"] = str(md_out)
    write_handoff(payload, json_out, md_out)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "ready" else 2


def command_full(args: argparse.Namespace) -> int:
    payload = full_payload(
        args.vendor,
        args.plugin_root,
        args.addon_root,
        args.min_godot_version,
        args.json_out,
        args.md_out,
        args.log_out,
        args.target,
        args.compile_target,
        args.scons_jobs,
        args.dry_run,
    )
    write_report(payload, Path(payload["report_json"]), Path(payload["report_markdown"]))
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"pass", "dry-run"} else 2


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "handoff":
        return command_handoff(args)
    if args.command == "report":
        return command_report(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
