#!/usr/bin/env python3
"""Install the Unity package from a temporary git repo and smoke native load/runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform as host_platform
import re
import shlex
import shutil
import subprocess
import time

import load_local_env
import run_unity_editor_tests
import unity_env


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "packages" / "unity" / "com.sheepfling.fastdis"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"
PACKAGE_CACHE_PATTERN = re.compile(r"Library/PackageCache/com\.sheepfling\.fastdis@[^\s)]+")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def install_criteria(report: dict[str, object]) -> dict[str, bool]:
    checks = {
        str(entry.get("name")): str(entry.get("status"))
        for entry in report.get("checks", [])
        if isinstance(entry, dict)
    }
    cache_locations = report.get("package_cache_locations") or []
    return {
        "native_abi_loads": checks.get("native_abi_loads") == "pass",
        "world_processes_entity_state_packet": checks.get("world_processes_entity_state_packet") == "pass",
        "world_auto_spawns_and_positions_actor": checks.get("world_auto_spawns_and_positions_actor") == "pass",
        "replay_player_steps_world_state": checks.get("replay_player_steps_world_state") == "pass",
        "receiver_socket_loopback_feeds_world": checks.get("receiver_socket_loopback_feeds_world") == "pass",
        "git_package_cache_detected": bool(cache_locations),
    }


def host_label() -> str:
    system = host_platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def git_package_url(repo_root: Path) -> str:
    return repo_root.resolve().as_uri() + "?path=packages/unity/com.sheepfling.fastdis"


def plugin_inventory(package_root: Path) -> dict[str, bool]:
    return {
        "macos": (package_root / "Runtime" / "Plugins" / "macOS" / "libfastdis.dylib").is_file(),
        "windows": (package_root / "Runtime" / "Plugins" / "Windows" / "x86_64" / "fastdis.dll").is_file(),
        "linux": (package_root / "Runtime" / "Plugins" / "Linux" / "x86_64" / "libfastdis.so").is_file(),
    }


def package_cache_locations(log_path: Path) -> list[str]:
    if not log_path.is_file():
        return []
    matches = PACKAGE_CACHE_PATTERN.findall(log_path.read_text(encoding="utf-8", errors="ignore"))
    deduped: list[str] = []
    for match in matches:
        if match not in deduped:
            deduped.append(match)
    return deduped


def project_state(project_dir: Path) -> dict[str, object]:
    library_dir = project_dir / "Library"
    package_cache_dir = library_dir / "PackageCache"
    script_assemblies_dir = library_dir / "ScriptAssemblies"
    return {
        "library_exists": library_dir.is_dir(),
        "package_cache_exists": package_cache_dir.is_dir(),
        "script_assemblies_exists": script_assemblies_dir.is_dir(),
    }


def failure_classification(report: dict[str, object]) -> dict[str, str]:
    project = report.get("project_state") or {}
    attempts = report.get("attempts") or []
    launch = str(report.get("launch") or "unknown")
    if report.get("status") == "pass":
        return {"failure_stage": "none", "failure_reason": "none"}
    if isinstance(project, dict) and not project.get("library_exists", False):
        return {"failure_stage": "host-startup", "failure_reason": "project-import-never-started"}
    if launch == "launch-services":
        return {"failure_stage": "host-launch", "failure_reason": "launch-services-open-failed"}
    if isinstance(attempts, list):
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            if attempt.get("launch") == "launch-services" and str(attempt.get("status")) == "fail":
                return {"failure_stage": "host-launch", "failure_reason": "launch-services-open-failed"}
    if not report.get("package_cache_locations"):
        return {"failure_stage": "package-install", "failure_reason": "package-cache-missing"}
    return {"failure_stage": "runtime-proof", "failure_reason": "install-smoke-checks-failed"}


def build_startup_blocked_report(startup_probe_report: dict[str, object], out_dir: Path) -> dict[str, object]:
    host = str(startup_probe_report.get("host_platform") or host_label())
    report = {
        "schema": "fastdis.unity_install_smoke.v1",
        "status": "fail",
        "unity_version": startup_probe_report.get("unity_version", "unknown"),
        "abi_version": 0,
        "detail": (
            "Unity startup probe failed before install smoke could begin; "
            "the host never started importing the scratch Unity project."
        ),
        "requested_version": startup_probe_report.get("requested_version"),
        "host_platform": host,
        "editor": startup_probe_report.get("editor"),
        "manifest_git_url": "",
        "plugin_inventory": plugin_inventory(PACKAGE_ROOT),
        "package_cache_locations": [],
        "repo_root": "",
        "project_dir": str(startup_probe_report.get("project_dir", "")),
        "returncode": startup_probe_report.get("returncode", -15),
        "elapsed_seconds": startup_probe_report.get("elapsed_seconds", 0),
        "terminated_after_pass": False,
        "timed_out": True,
        "log": str(out_dir / "unity_install_smoke.log"),
        "launch": startup_probe_report.get("launch", "unknown"),
        "mode": startup_probe_report.get("mode", "unknown"),
        "launcher_log": startup_probe_report.get("launcher_log"),
        "attempts": startup_probe_report.get("attempts", []),
        "project_state": startup_probe_report.get("project_state", {}),
        "install_criteria": {
            "native_abi_loads": False,
            "world_processes_entity_state_packet": False,
            "world_auto_spawns_and_positions_actor": False,
            "replay_player_steps_world_state": False,
            "receiver_socket_loopback_feeds_world": False,
            "git_package_cache_detected": False,
        },
    }
    report.update(failure_classification(report))
    return report


def clear_previous_artifacts(*paths: Path) -> None:
    for path in paths:
        if path.is_file():
            path.unlink()


def copy_git_package_source(repo_root: Path) -> Path:
    if repo_root.exists():
        shutil.rmtree(repo_root)
    package_target = repo_root / "packages" / "unity" / PACKAGE_ROOT.name
    package_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PACKAGE_ROOT, package_target)
    return package_target


def init_git_repo(repo_root: Path) -> None:
    commands = [
        ["git", "init", "-b", "main", str(repo_root)],
        ["git", "-C", str(repo_root), "config", "user.name", "FastDIS Install Smoke"],
        ["git", "-C", str(repo_root), "config", "user.email", "fastdis-install-smoke@example.invalid"],
        ["git", "-C", str(repo_root), "add", "."],
        ["git", "-C", str(repo_root), "commit", "-m", "unity install smoke snapshot"],
    ]
    for cmd in commands:
        completed = subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if completed.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} failed:\n{completed.stdout}")


def create_project(project_dir: Path, repo_root: Path) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    (project_dir / "Assets" / "Editor").mkdir(parents=True)
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    manifest = {
        "dependencies": {
            "com.sheepfling.fastdis": git_package_url(repo_root),
        }
    }
    _write_text(project_dir / "Packages" / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    _write_text(
        project_dir / "ProjectSettings" / "ProjectVersion.txt",
        "m_EditorVersion: 6000.5.0f1\nm_EditorVersionWithRevision: 6000.5.0f1\n",
    )
    _write_text(
        project_dir / "Assets" / "Editor" / "FastDisInstallSmokeRunner.cs",
        """
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using FastDIS.Native;
using FastDIS.Unity;
using UnityEditor;
using UnityEngine;

public static class FastDisInstallSmokeRunner
{
    public static void Run()
    {
        string reportPath = ReportPathFromArguments();
        if (string.IsNullOrEmpty(reportPath))
        {
            reportPath = Path.Combine(Environment.CurrentDirectory, "fastdis_unity_install_smoke.json");
        }

        int total = 0;
        int failed = 0;
        uint abiVersion = 0;
        string detail = "install smoke checks passed";
        StringBuilder checks = new StringBuilder();

        Check("native_abi_loads", FastDisNative.TryGetAbiVersion(out abiVersion) && abiVersion > 0, ref total, ref failed, checks);

        GameObject root = new GameObject("FastDIS Install Smoke");
        try
        {
            FastDisWorld world = root.AddComponent<FastDisWorld>();
            FastDisNetworkReceiver receiver = root.AddComponent<FastDisNetworkReceiver>();
            FastDisReplayPlayer replayPlayer = root.AddComponent<FastDisReplayPlayer>();
            FastDIS.Unity.FastDisEntityId entityId = new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 };

            Check(
                "world_processes_entity_state_packet",
                world.ProcessPacket(CreateEntityStatePdu(7, 2)) && world.KnownEntityCount == 1 && world.BoundActorCount == 1 && world.PacketsProcessed == 1,
                ref total,
                ref failed,
                checks);
            Check(
                "world_auto_spawns_and_positions_actor",
                world.TryGetBoundActor(entityId, out Transform actor) &&
                Mathf.Approximately(actor.localPosition.x, 10.0f) &&
                Mathf.Approximately(actor.localPosition.y, 30.0f) &&
                Mathf.Approximately(actor.localPosition.z, 20.0f),
                ref total,
                ref failed,
                checks);

            replayPlayer.LoadReplay(BuildReplay(CreateEntityStatePdu(7, 2), CreateEntityStateUpdatePdu(7)));
            replayPlayer.Play();
            int replaySteps = replayPlayer.Step();
            Debug.Log($"FastDIS install smoke replay state: packets={replayPlayer.PacketCount} steps={replaySteps} known={world.KnownEntityCount}");
            Check(
                "replay_player_steps_world_state",
                replayPlayer.PacketCount == 2 && replaySteps >= 1 && world.KnownEntityCount == 1,
                ref total,
                ref failed,
                checks);

            world.ClearRuntimeState();
            Check(
                "receiver_socket_loopback_feeds_world",
                SendLoopbackPacket(receiver, CreateEntityStatePdu(6, 1)) && receiver.PacketsReceived == 1 && world.KnownEntityCount == 1,
                ref total,
                ref failed,
                checks);
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(root);
        }

        if (failed != 0)
        {
            detail = "one or more git-installed package install smoke checks failed";
        }

        string directory = Path.GetDirectoryName(reportPath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        string status = failed == 0 ? "pass" : "fail";
        string json =
            "{\\n" +
            "  \\"schema\\": \\"fastdis.unity_install_smoke.v1\\",\\n" +
            $"  \\"status\\": \\"{status}\\",\\n" +
            $"  \\"unity_version\\": \\"{Escape(Application.unityVersion)}\\",\\n" +
            $"  \\"abi_version\\": {abiVersion},\\n" +
            $"  \\"total\\": {total},\\n" +
            $"  \\"passed\\": {total - failed},\\n" +
            $"  \\"failed\\": {failed},\\n" +
            $"  \\"detail\\": \\"{Escape(detail)}\\",\\n" +
            "  \\"checks\\": [\\n" +
            checks.ToString() +
            "  ]\\n" +
            "}\\n";
        File.WriteAllText(reportPath, json, Encoding.UTF8);
        Debug.Log($"FastDIS install smoke report: {reportPath}");
        EditorApplication.Exit(failed == 0 ? 0 : 1);
    }

    private static void Check(string name, bool ok, ref int total, ref int failed, StringBuilder checks)
    {
        if (total > 0)
        {
            checks.Append(",\\n");
        }

        total++;
        if (!ok)
        {
            failed++;
        }

        checks.Append("    { \\"name\\": \\"");
        checks.Append(Escape(name));
        checks.Append("\\", \\"status\\": \\"");
        checks.Append(ok ? "pass" : "fail");
        checks.Append("\\" }");
    }

    private static string ReportPathFromArguments()
    {
        string[] args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-fastdisReport")
            {
                return args[i + 1];
            }
        }
        return null;
    }

    private static string Escape(string value)
    {
        return value.Replace("\\\\", "\\\\\\\\").Replace("\\"", "\\\\\\"");
    }

    private static byte[] CreateEntityStatePdu(byte version, byte forceId)
    {
        byte[] packet = CreatePdu(version, 1, 144);
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        packet[body + 6] = forceId;
        packet[body + 7] = 0;
        packet[body + 8] = 1;
        packet[body + 9] = 2;
        WriteU16(packet, body + 10, 840);
        packet[body + 12] = 3;
        packet[body + 13] = 4;
        packet[body + 14] = 5;
        packet[body + 15] = 6;
        packet[body + 16] = 9;
        packet[body + 17] = 8;
        WriteU16(packet, body + 18, 124);
        packet[body + 20] = 7;
        packet[body + 21] = 6;
        packet[body + 22] = 5;
        packet[body + 23] = 4;
        WriteVec3(packet, body + 24, 1.25f, -2.5f, 3.75f);
        WriteWorld(packet, body + 36, 10.0, 20.0, 30.0);
        WriteVec3(packet, body + 60, 0.1f, 0.2f, 0.3f);
        WriteU32(packet, body + 72, 0xAABBCCDDu);
        packet[body + 76] = 4;
        for (int i = 0; i < 15; i++)
        {
            packet[body + 77 + i] = (byte)(i + 1);
        }
        WriteVec3(packet, body + 92, 0.5f, 0.6f, 0.7f);
        WriteVec3(packet, body + 104, 1.5f, 1.6f, 1.7f);
        packet[body + 116] = 1;
        byte[] marking = Encoding.ASCII.GetBytes("TANK001");
        Array.Copy(marking, 0, packet, body + 117, marking.Length);
        WriteU32(packet, body + 128, 0x01020304u);
        return packet;
    }

    private static byte[] CreateEntityStateUpdatePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 67, 72);
        packet[3] = 1;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU32(packet, body + 8, 0x0000001Fu);
        WriteWorld(packet, body + 12, 40.0, 50.0, 60.0);
        WriteVec3(packet, body + 36, 4.0f, 5.0f, 6.0f);
        WriteVec3(packet, body + 48, 0.4f, 0.5f, 0.6f);
        return packet;
    }

    private static byte[] BuildReplay(params byte[][] packets)
    {
        using (MemoryStream stream = new MemoryStream())
        {
            stream.Write(Encoding.ASCII.GetBytes("FDPKT1"), 0, 6);
            stream.WriteByte((byte)((packets.Length >> 8) & 0xFF));
            stream.WriteByte((byte)(packets.Length & 0xFF));
            foreach (byte[] packet in packets)
            {
                stream.WriteByte((byte)((packet.Length >> 24) & 0xFF));
                stream.WriteByte((byte)((packet.Length >> 16) & 0xFF));
                stream.WriteByte((byte)((packet.Length >> 8) & 0xFF));
                stream.WriteByte((byte)(packet.Length & 0xFF));
                stream.Write(packet, 0, packet.Length);
            }
            return stream.ToArray();
        }
    }

    private static bool SendLoopbackPacket(FastDisNetworkReceiver receiver, byte[] packet)
    {
        ushort loopbackPort = ReserveLoopbackPort();
        receiver.ConfigureEndpoint("127.0.0.1", loopbackPort);
        receiver.StartReceiver();
        try
        {
            using (UdpClient sender = new UdpClient())
            {
                sender.Send(packet, packet.Length, new IPEndPoint(IPAddress.Loopback, loopbackPort));
            }

            for (int attempt = 0; attempt < 20; attempt++)
            {
                if (receiver.PumpAvailable() > 0)
                {
                    return true;
                }
                Thread.Sleep(10);
            }

            return false;
        }
        finally
        {
            receiver.StopReceiver();
        }
    }

    private static ushort ReserveLoopbackPort()
    {
        using (Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
        {
            socket.Bind(new IPEndPoint(IPAddress.Loopback, 0));
            return (ushort)((IPEndPoint)socket.LocalEndPoint).Port;
        }
    }

    private static byte[] CreatePdu(byte version, byte pduType, ushort length)
    {
        byte[] packet = new byte[length];
        packet[0] = version;
        packet[1] = 1;
        packet[2] = pduType;
        packet[3] = 1;
        WriteU16(packet, 8, length);
        return packet;
    }

    private static void WriteU16(byte[] packet, int offset, int value)
    {
        packet[offset] = (byte)((value >> 8) & 0xFF);
        packet[offset + 1] = (byte)(value & 0xFF);
    }

    private static void WriteU32(byte[] packet, int offset, uint value)
    {
        packet[offset] = (byte)((value >> 24) & 0xFF);
        packet[offset + 1] = (byte)((value >> 16) & 0xFF);
        packet[offset + 2] = (byte)((value >> 8) & 0xFF);
        packet[offset + 3] = (byte)(value & 0xFF);
    }

    private static void WriteFloat(byte[] packet, int offset, float value)
    {
        byte[] bytes = BitConverter.GetBytes(value);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(bytes);
        }
        Array.Copy(bytes, 0, packet, offset, 4);
    }

    private static void WriteVec3(byte[] packet, int offset, float x, float y, float z)
    {
        WriteFloat(packet, offset, x);
        WriteFloat(packet, offset + 4, y);
        WriteFloat(packet, offset + 8, z);
    }

    private static void WriteDouble(byte[] packet, int offset, double value)
    {
        byte[] bytes = BitConverter.GetBytes(value);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(bytes);
        }
        Array.Copy(bytes, 0, packet, offset, 8);
    }

    private static void WriteWorld(byte[] packet, int offset, double x, double y, double z)
    {
        WriteDouble(packet, offset, x);
        WriteDouble(packet, offset + 8, y);
        WriteDouble(packet, offset + 16, z);
    }
}
""".strip()
        + "\n",
    )


def render_markdown(report: dict[str, object]) -> str:
    cache_locations = report.get("package_cache_locations") or []
    inventory = report.get("plugin_inventory") or {}
    criteria = install_criteria(report)
    state = report.get("project_state") or {}
    classification = failure_classification(report)
    lines = [
        "# Unity Install Smoke Report",
        "",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report.get('host_platform', 'unknown')}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- abi_version: `{report.get('abi_version', 0)}`",
        f"- detail: `{report.get('detail', '')}`",
        f"- manifest_git_url: `{report.get('manifest_git_url', '')}`",
        f"- repo: `{report.get('repo_root', '')}`",
        f"- project_dir: `{report.get('project_dir', '')}`",
        f"- log: `{report.get('log', '')}`",
        f"- launch: `{report.get('launch', 'unknown')}`",
        f"- launcher_log: `{report.get('launcher_log', '')}`",
        f"- failure_stage: `{classification['failure_stage']}`",
        f"- failure_reason: `{classification['failure_reason']}`",
        "",
    ]
    if report.get("total") is not None:
        lines.append("## Checks")
        lines.append("")
        lines.append(f"- total: `{report.get('total', 0)}`")
        lines.append(f"- passed: `{report.get('passed', 0)}`")
        lines.append(f"- failed: `{report.get('failed', 0)}`")
        for check in report.get("checks", []):
            if isinstance(check, dict):
                lines.append(f"- check `{check.get('name', 'unknown')}`: `{check.get('status', 'unknown')}`")
        lines.append("")
    lines.append("## Install Criteria")
    lines.append("")
    lines.append(f"- native_abi_loads: `{criteria['native_abi_loads']}`")
    lines.append(f"- world_processes_entity_state_packet: `{criteria['world_processes_entity_state_packet']}`")
    lines.append(f"- world_auto_spawns_and_positions_actor: `{criteria['world_auto_spawns_and_positions_actor']}`")
    lines.append(f"- replay_player_steps_world_state: `{criteria['replay_player_steps_world_state']}`")
    lines.append(f"- receiver_socket_loopback_feeds_world: `{criteria['receiver_socket_loopback_feeds_world']}`")
    lines.append(f"- git_package_cache_detected: `{criteria['git_package_cache_detected']}`")
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    lines.append(f"- package_cache_locations: `{len(cache_locations)}`")
    if state:
        lines.append(f"- project_state.library_exists: `{state.get('library_exists', False)}`")
        lines.append(f"- project_state.package_cache_exists: `{state.get('package_cache_exists', False)}`")
        lines.append(f"- project_state.script_assemblies_exists: `{state.get('script_assemblies_exists', False)}`")
    for location in cache_locations:
        lines.append(f"- package_cache: `{location}`")
    lines.append(f"- plugin_inventory.macos: `{inventory.get('macos', False)}`")
    lines.append(f"- plugin_inventory.windows: `{inventory.get('windows', False)}`")
    lines.append(f"- plugin_inventory.linux: `{inventory.get('linux', False)}`")
    attempts = report.get("attempts")
    if isinstance(attempts, list) and attempts:
        lines.append("")
        lines.append("## Attempts")
        lines.append("")
        for attempt in attempts:
            if isinstance(attempt, dict):
                lines.append(
                    f"- launch={attempt.get('launch', 'unknown')} status={attempt.get('status', 'unknown')} "
                    f"returncode={attempt.get('returncode', 'unknown')} timed_out={attempt.get('timed_out', False)} "
                    f"elapsed={attempt.get('elapsed_seconds', 0)}"
                )
    lines.append("")
    return "\n".join(lines)


def install_smoke_unity_command(
    editor: str,
    project_dir: Path,
    report_path: Path,
    log_path: Path,
    *,
    batchmode: bool = False,
) -> list[str]:
    cmd = [
        editor,
    ]
    if batchmode:
        cmd.extend(["-batchmode", *run_unity_editor_tests.unity_graphics_args()])
    cmd.extend(
        [
            "-accept-apiupdate",
            "-quit",
            "-projectPath",
            str(project_dir),
            "-executeMethod",
            "FastDisInstallSmokeRunner.Run",
            "-fastdisReport",
            str(report_path),
            "-logFile",
            str(log_path),
        ]
    )
    return cmd


def install_smoke_attempts(
    install: unity_env.UnityInstall,
    project_dir: Path,
    report_dir: Path,
) -> list[dict[str, object]]:
    result_json = report_dir / "unity_install_smoke.json"
    log_path = report_dir / "unity_install_smoke.log"
    launcher_root = report_dir

    interactive_cmd = install_smoke_unity_command(install.editor_path or "", project_dir, result_json, log_path)
    attempts: list[dict[str, object]] = []
    if host_platform.system().lower() == "darwin":
        attempts.append(
            {
                "mode": "interactive",
                "launch": "login-shell",
                "cmd": ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in interactive_cmd)],
                "unity_command": interactive_cmd,
                "env": None,
                "results_json": result_json,
                "log": log_path,
                "launcher_log": launcher_root / "unity_install_smoke_login_shell_launcher.log",
            }
        )
        if install.editor_app_path:
            attempts.append(
                {
                    "mode": "interactive",
                    "launch": "launch-services",
                    "cmd": ["open", "-W", "-n", "-a", install.editor_app_path, "--args", *interactive_cmd[1:]],
                    "unity_command": [install.editor_app_path, *interactive_cmd[1:]],
                    "env": None,
                    "results_json": result_json,
                    "log": log_path,
                    "launcher_log": launcher_root / "unity_install_smoke_launch_services_launcher.log",
                }
            )

    batch_cmd = install_smoke_unity_command(install.editor_path or "", project_dir, result_json, log_path, batchmode=True)
    attempts.append(
        {
            "mode": "batchmode",
            "launch": "direct",
            "cmd": batch_cmd,
            "unity_command": batch_cmd,
            "env": run_unity_editor_tests.unity_runtime_env(result_json),
            "results_json": result_json,
            "log": log_path,
            "launcher_log": launcher_root / "unity_install_smoke_direct_launcher.log",
        }
    )
    return attempts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--project-dir", type=Path, help="Scratch Unity project path")
    parser.add_argument("--repo-dir", type=Path, help="Temporary git repo path")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=600)
    return parser.parse_args(argv)


def _fallback_detail(diagnostic_info: dict[str, object] | None, timeout: int, launch: str) -> str:
    if isinstance(diagnostic_info, dict):
        detail = diagnostic_info.get("detail")
        if isinstance(detail, str) and detail:
            return detail
    if launch:
        return f"Unity did not complete the install smoke on the {launch} launcher within {timeout} seconds."
    return f"Unity did not write an install smoke report within {timeout} seconds."


def enrich_failure_detail(report: dict[str, object], project_dir: Path) -> None:
    if report.get("status") == "pass":
        return
    state = project_state(project_dir)
    report["project_state"] = state
    if not state["library_exists"]:
        detail = (
            "Unity did not begin importing the scratch project before the install smoke timed out; "
            "the project Library/ directory was never created."
        )
        launcher_log = report.get("launcher_log")
        log_path = Path(launcher_log) if isinstance(launcher_log, str) and launcher_log else None
        hint = None
        if log_path and log_path.is_file():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if "kLSNoExecutableErr" in text or "The executable is missing" in text:
                hint = "launch-services reported kLSNoExecutableErr; verify the Unity.app bundle path and executable layout"
            elif "attempt to write a readonly database" in text:
                hint = "Unity hit a readonly database while starting; verify the macOS Unity Hub / licensing cache and home-directory write access"
        report["detail"] = detail + (f" Diagnostic hint: {hint}." if hint else "")


def attempt_timeout_budget(total_timeout: int, attempts: list[dict[str, object]], index: int) -> int:
    remaining = len(attempts) - index
    if remaining <= 1:
        return max(60, total_timeout)
    launch = str(attempts[index].get("launch") or "")
    if launch != "direct":
        reserve_for_later = max(60, total_timeout - 45)
        return min(45, max(30, total_timeout - reserve_for_later))
    return max(60, total_timeout)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    install = unity_env.resolve_install(args.unity_version)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    host = host_label()
    json_path = args.out_dir / "unity_install_smoke.json"
    host_json_path = args.out_dir / f"unity_install_smoke_{host}.json"
    md_path = args.out_dir / "unity_install_smoke.md"
    host_md_path = args.out_dir / f"unity_install_smoke_{host}.md"
    log_path = args.out_dir / "unity_install_smoke.log"
    repo_root = args.repo_dir or (unity_env.work_root() / "unity_install_smoke_repo.git")
    project_dir = args.project_dir or (unity_env.work_root() / "unity_install_smoke_project")
    manifest_git_url = git_package_url(repo_root)
    repo_package_root = repo_root / "packages" / "unity" / PACKAGE_ROOT.name

    if install is None or not install.editor_path:
        report = {
            "schema": "fastdis.unity_install_smoke.v1",
            "status": "skip",
            "requested_version": args.unity_version,
            "host_platform": host,
            "detail": "Unity editor not found",
            "manifest_git_url": manifest_git_url,
            "repo_root": str(repo_root),
            "project_dir": str(project_dir),
            "log": str(log_path),
        }
        report["install_criteria"] = install_criteria(report)
        for path in (json_path, host_json_path):
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for path in (md_path, host_md_path):
            path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 2

    copy_git_package_source(repo_root)
    init_git_repo(repo_root)
    create_project(project_dir, repo_root)

    attempts = install_smoke_attempts(install, project_dir, args.out_dir)
    launcher_logs = [attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)]
    clear_previous_artifacts(json_path, host_json_path, md_path, host_md_path, log_path, *launcher_logs)

    attempt_summaries: list[dict[str, object]] = []
    report: dict[str, object] | None = None
    selected_attempt: dict[str, object] | None = None
    selected_returncode = 1
    selected_elapsed = 0.0
    selected_terminated_after_pass = False
    selected_timed_out = False
    selected_diagnostic_info: dict[str, object] | None = None

    remaining_timeout = args.timeout
    for index, attempt in enumerate(attempts):
        result_json = attempt["results_json"]
        attempt_log_path = attempt["log"]
        launcher_log_path = attempt.get("launcher_log")
        attempt_timeout = attempt_timeout_budget(remaining_timeout, attempts, index)
        clear_previous_artifacts(
            result_json,
            attempt_log_path,
            launcher_log_path if isinstance(launcher_log_path, Path) else Path("/nonexistent"),
        )
        started = time.monotonic()
        returncode, terminated_after_pass, timed_out, early_diagnostic_info = run_unity_editor_tests.run_editor_method_process(
            attempt["cmd"],
            result_json,
            attempt_log_path,
            env=attempt["env"] if isinstance(attempt.get("env"), dict) or attempt.get("env") is None else None,
            launcher_log_path=launcher_log_path if isinstance(launcher_log_path, Path) else None,
            timeout=attempt_timeout,
        )
        elapsed = round(time.monotonic() - started, 3)
        remaining_timeout = max(60, remaining_timeout - attempt_timeout)
        payload = json.loads(result_json.read_text(encoding="utf-8-sig")) if result_json.is_file() else None
        diagnostic_info = early_diagnostic_info or run_unity_editor_tests.analyze_log(attempt_log_path)
        attempt_status = str(payload.get("status")) if isinstance(payload, dict) else ("timeout" if timed_out else "fail")
        attempt_summaries.append(
            {
                "launch": attempt["launch"],
                "mode": attempt["mode"],
                "status": attempt_status,
                "returncode": returncode,
                "timed_out": timed_out,
                "terminated_after_pass": terminated_after_pass,
                "elapsed_seconds": elapsed,
                "timeout_budget_seconds": attempt_timeout,
                "diagnostic_code": diagnostic_info.get("code") if isinstance(diagnostic_info, dict) else None,
            }
        )
        if isinstance(payload, dict):
            report = payload
            selected_attempt = attempt
            selected_returncode = returncode
            selected_elapsed = elapsed
            selected_terminated_after_pass = terminated_after_pass
            selected_timed_out = timed_out
            selected_diagnostic_info = diagnostic_info
            if payload.get("status") == "pass":
                break
        elif attempt["launch"] == "direct" or timed_out or (isinstance(diagnostic_info, dict) and diagnostic_info.get("status")):
            selected_attempt = attempt
            selected_returncode = returncode
            selected_elapsed = elapsed
            selected_terminated_after_pass = terminated_after_pass
            selected_timed_out = timed_out
            selected_diagnostic_info = diagnostic_info

    if report is None:
        selected_attempt = selected_attempt or attempts[-1]
        launch = str(selected_attempt.get("launch") or "unknown")
        report = {
            "schema": "fastdis.unity_install_smoke.v1",
            "status": "fail",
            "unity_version": install.version,
            "abi_version": 0,
            "detail": _fallback_detail(selected_diagnostic_info, args.timeout, launch),
        }

    report["requested_version"] = args.unity_version
    report["host_platform"] = host
    report["editor"] = install.editor_path
    report["manifest_git_url"] = manifest_git_url
    report["plugin_inventory"] = plugin_inventory(repo_package_root)
    report["package_cache_locations"] = package_cache_locations(log_path)
    report["install_criteria"] = install_criteria(report)
    report["repo_root"] = str(repo_root)
    report["project_dir"] = str(project_dir)
    report["returncode"] = selected_returncode
    report["elapsed_seconds"] = selected_elapsed
    report["terminated_after_pass"] = selected_terminated_after_pass
    report["timed_out"] = selected_timed_out
    report["log"] = str(log_path)
    report["launch"] = str(selected_attempt.get("launch") or "unknown") if selected_attempt else "unknown"
    report["mode"] = str(selected_attempt.get("mode") or "unknown") if selected_attempt else "unknown"
    if selected_attempt and isinstance(selected_attempt.get("launcher_log"), Path):
        report["launcher_log"] = str(selected_attempt["launcher_log"])
    report["attempts"] = attempt_summaries
    report["project_state"] = project_state(project_dir)
    if report.get("status") == "pass" and not report["package_cache_locations"]:
        report["status"] = "fail"
        report["detail"] = "Unity did not show a PackageCache install for the git dependency."
        report["install_criteria"] = install_criteria(report)
    enrich_failure_detail(report, project_dir)
    report.update(failure_classification(report))

    for path in (json_path, host_json_path):
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for path in (md_path, host_md_path):
        path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if report.get("status") == "pass" and not timed_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
