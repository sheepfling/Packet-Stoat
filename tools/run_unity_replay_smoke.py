#!/usr/bin/env python3
"""Run a Unity replay-driven canonical scenario smoke test in a scratch project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform as host_platform
import shlex
import shutil
import subprocess
import tempfile
import time

from fastdis import replay as replay_io

import load_local_env
import run_unity_editor_tests
import unity_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_DIR = unity_env.work_root() / "unity_replay_matrix_project"
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "unity_replay_matrix"
CORE_SCENARIO_SUITE = "core_matrix"


RUNNER_SOURCE = """
using System;
using System.IO;
using System.Text;
using FastDIS.Unity;
using UnityEditor;
using UnityEngine;

public static class FastDisReplayMatrixRunner
{
    public static void Run()
    {
        string reportPath = CommandArg("-fastdisReport");
        string replayPath = CommandArg("-fastdisReplay");
        int expectedPackets = ParseInt(CommandArg("-fastdisExpectedPackets"));
        int expectedEntities = ParseInt(CommandArg("-fastdisExpectedEntities"));
        int packetBudget = Math.Max(1, ParseInt(CommandArg("-fastdisPacketBudget"), 128));

        if (string.IsNullOrEmpty(reportPath))
        {
            reportPath = Path.Combine(Environment.CurrentDirectory, "fastdis_unity_replay_matrix.json");
        }

        if (string.IsNullOrEmpty(replayPath) || !File.Exists(replayPath))
        {
            WriteFailure(reportPath, "missing replay file", 0, 0, 0, 0, 0, expectedPackets, expectedEntities);
            return;
        }

        byte[] replayBytes = File.ReadAllBytes(replayPath);
        GameObject root = new GameObject("FastDIS Replay Matrix");
        try
        {
            FastDisWorld world = root.AddComponent<FastDisWorld>();
            FastDisReplayPlayer replayPlayer = root.AddComponent<FastDisReplayPlayer>();

            replayPlayer.LoadReplay(replayBytes);
            replayPlayer.Play();

            int loadedPackets = replayPlayer.PacketCount;
            int iterations = 0;
            int packetsStepped = 0;
            int loopBudget = Math.Max(expectedPackets + 16, packetBudget * 4);
            while (iterations < loopBudget)
            {
                iterations++;
                int stepped = replayPlayer.Step();
                if (stepped <= 0)
                {
                    if (!replayPlayer.IsPlaying)
                    {
                        break;
                    }
                    continue;
                }
                packetsStepped += stepped;
                if (!replayPlayer.IsPlaying)
                {
                    break;
                }
            }

            int boundActors = world.BoundActorCount;
            int knownEntities = world.KnownEntityCount;
            int movedEntityCount = boundActors;
            bool pass = loadedPackets == expectedPackets && knownEntities >= expectedEntities && movedEntityCount >= expectedEntities;

            string json =
                "{\\n" +
                "  \\"schema\\": \\"fastdis.unity_replay_matrix_runner.v1\\",\\n" +
                $"  \\"status\\": \\"{(pass ? "pass" : "fail")}\\",\\n" +
                $"  \\"loaded_packets\\": {loadedPackets},\\n" +
                $"  \\"packets_stepped\\": {packetsStepped},\\n" +
                $"  \\"known_entities\\": {knownEntities},\\n" +
                $"  \\"bound_actor_count\\": {boundActors},\\n" +
                $"  \\"moved_entity_count\\": {movedEntityCount},\\n" +
                $"  \\"packets_processed\\": {world.PacketsProcessed},\\n" +
                $"  \\"expected_packets\\": {expectedPackets},\\n" +
                $"  \\"expected_entities\\": {expectedEntities}\\n" +
                "}\\n";
            Directory.CreateDirectory(Path.GetDirectoryName(reportPath) ?? Environment.CurrentDirectory);
            File.WriteAllText(reportPath, json, Encoding.UTF8);
            Debug.Log($"FastDIS Unity replay matrix report: {reportPath}");
            EditorApplication.Exit(pass ? 0 : 1);
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(root);
        }
    }

    private static void WriteFailure(
        string reportPath,
        string detail,
        int loadedPackets,
        int packetsStepped,
        int knownEntities,
        int boundActors,
        int movedEntityCount,
        int expectedPackets,
        int expectedEntities)
    {
        string json =
            "{\\n" +
            "  \\"schema\\": \\"fastdis.unity_replay_matrix_runner.v1\\",\\n" +
            "  \\"status\\": \\"fail\\",\\n" +
            $"  \\"detail\\": \\"{Escape(detail)}\\",\\n" +
            $"  \\"loaded_packets\\": {loadedPackets},\\n" +
            $"  \\"packets_stepped\\": {packetsStepped},\\n" +
            $"  \\"known_entities\\": {knownEntities},\\n" +
            $"  \\"bound_actor_count\\": {boundActors},\\n" +
            $"  \\"moved_entity_count\\": {movedEntityCount},\\n" +
            "  \\"packets_processed\\": 0,\\n" +
            $"  \\"expected_packets\\": {expectedPackets},\\n" +
            $"  \\"expected_entities\\": {expectedEntities}\\n" +
            "}\\n";
        Directory.CreateDirectory(Path.GetDirectoryName(reportPath) ?? Environment.CurrentDirectory);
        File.WriteAllText(reportPath, json, Encoding.UTF8);
        Debug.LogError($"FastDIS Unity replay matrix failure: {detail}");
        EditorApplication.Exit(1);
    }

    private static string CommandArg(string name)
    {
        string[] args = Environment.GetCommandLineArgs();
        for (int index = 0; index < args.Length - 1; index++)
        {
            if (args[index] == name)
            {
                return args[index + 1];
            }
        }
        return null;
    }

    private static int ParseInt(string value, int fallback = 0)
    {
        if (int.TryParse(value, out int parsed))
        {
            return parsed;
        }
        return fallback;
    }

    private static string Escape(string value)
    {
        return value.Replace("\\\\", "\\\\\\\\").Replace("\\"", "\\\\\\"");
    }
}
""".strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    parser.add_argument("--project-dir", type=Path, default=DEFAULT_PROJECT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--entity-count", type=int, required=True)
    parser.add_argument("--rate-hz", type=float, required=True)
    parser.add_argument("--packet-budget", type=int, default=128)
    parser.add_argument("--timeout", type=int, default=600)
    return parser.parse_args()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_truth_and_replay(
    *,
    replay_path: Path,
    truth_path: Path,
    count: int,
    entity_count: int,
    rate_hz: float,
) -> dict[str, object]:
    from fastdis.tools import send_entity

    send_args = argparse.Namespace(
        count=count,
        entity_count=entity_count,
        rate_hz=rate_hz,
        site=100,
        application=1,
        entity=0,
        force_id=1,
        exercise_id=3,
        marking="FASTDIS",
        lat=29.5597,
        lon=-95.0831,
        alt=100.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        print_orientation_debug=False,
        truth_out=None,
    )
    packets, _orientation_debug, truth = send_entity.build_packets(send_args)
    replay_io.write_v1_packets(replay_path, packets)
    truth_path.write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    return truth


def create_project(project_dir: Path) -> None:
    run_unity_editor_tests.create_project(project_dir)
    editor_dir = project_dir / "Assets" / "Editor"
    editor_dir.mkdir(parents=True, exist_ok=True)
    _write_text(editor_dir / "FastDisReplayMatrixRunner.cs", RUNNER_SOURCE)


def replay_matrix_unity_command(editor: str, project_dir: Path, report_path: Path, log_path: Path, replay_path: Path, expected_packets: int, expected_entities: int, packet_budget: int, *, batchmode: bool = False) -> list[str]:
    cmd = [editor]
    if batchmode:
        cmd.extend(["-batchmode", *run_unity_editor_tests.unity_graphics_args()])
    cmd.extend(
        [
            "-accept-apiupdate",
            "-quit",
            "-projectPath",
            str(project_dir),
            "-executeMethod",
            "FastDisReplayMatrixRunner.Run",
            "-fastdisReport",
            str(report_path),
            "-fastdisReplay",
            str(replay_path),
            "-fastdisExpectedPackets",
            str(expected_packets),
            "-fastdisExpectedEntities",
            str(expected_entities),
            "-fastdisPacketBudget",
            str(packet_budget),
            "-logFile",
            str(log_path),
        ]
    )
    return cmd


def replay_matrix_attempts(
    install: unity_env.UnityInstall,
    project_dir: Path,
    report_dir: Path,
    replay_path: Path,
    expected_packets: int,
    expected_entities: int,
    packet_budget: int,
) -> list[dict[str, object]]:
    result_json = report_dir / "unity_replay_matrix_runner.json"
    log_path = report_dir / "unity_replay_matrix.log"
    interactive_cmd = replay_matrix_unity_command(
        install.editor_path or "",
        project_dir,
        result_json,
        log_path,
        replay_path,
        expected_packets,
        expected_entities,
        packet_budget,
    )
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
                "launcher_log": report_dir / "unity_replay_matrix_login_shell_launcher.log",
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
                    "launcher_log": report_dir / "unity_replay_matrix_launch_services_launcher.log",
                }
            )

    batch_cmd = replay_matrix_unity_command(
        install.editor_path or "",
        project_dir,
        result_json,
        log_path,
        replay_path,
        expected_packets,
        expected_entities,
        packet_budget,
        batchmode=True,
    )
    attempts.append(
        {
            "mode": "batchmode",
            "launch": "direct",
            "cmd": batch_cmd,
            "unity_command": batch_cmd,
            "env": run_unity_editor_tests.unity_runtime_env(result_json),
            "results_json": result_json,
            "log": log_path,
            "launcher_log": report_dir / "unity_replay_matrix_direct_launcher.log",
        }
    )
    return attempts


def attempt_timeout_budget(total_timeout: int, attempts: list[dict[str, object]], index: int) -> int:
    remaining = len(attempts) - index
    if remaining <= 1:
        return max(15, total_timeout)
    launch = str(attempts[index].get("launch") or "")
    if launch != "direct":
        reserve_for_later = max(15, total_timeout - 30)
        return min(30, max(15, total_timeout - reserve_for_later))
    return max(15, total_timeout)


def extract_payload(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    load_local_env.load()
    args = parse_args()
    install = unity_env.resolve_install(args.unity_version)
    if install is None or not install.editor_path:
        raise SystemExit("Could not resolve a Unity editor for the replay matrix lane.")

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    project_dir = args.project_dir.expanduser().resolve()
    if project_dir.exists():
        shutil.rmtree(project_dir)
    create_project(project_dir)

    with tempfile.TemporaryDirectory(prefix="fastdis_unity_replay_") as tmp:
        replay_path = Path(tmp) / f"{args.scenario}.fastdispkt"
        truth_path = Path(tmp) / f"{args.scenario}.truth.json"
        truth = build_truth_and_replay(
            replay_path=replay_path,
            truth_path=truth_path,
            count=args.count,
            entity_count=args.entity_count,
            rate_hz=args.rate_hz,
        )

        attempts = replay_matrix_attempts(
            install,
            project_dir,
            out_dir,
            replay_path,
            args.count,
            args.entity_count,
            args.packet_budget,
        )
        launcher_logs = [attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)]
        for launcher_log in launcher_logs:
            if launcher_log.exists():
                launcher_log.unlink()
        result_json = out_dir / "unity_replay_matrix_runner.json"
        log_path = out_dir / "unity_replay_matrix.log"
        if result_json.exists():
            result_json.unlink()
        if log_path.exists():
            log_path.unlink()

        attempt_summaries: list[dict[str, object]] = []
        selected_attempt: dict[str, object] | None = None
        selected_payload: dict[str, object] = {}
        remaining_timeout = args.timeout
        for index, attempt in enumerate(attempts):
            result_json = attempt["results_json"]
            log_path = attempt["log"]
            launcher_log_path = attempt.get("launcher_log")
            if result_json.exists():
                result_json.unlink()
            if log_path.exists():
                log_path.unlink()
            if isinstance(launcher_log_path, Path) and launcher_log_path.exists():
                launcher_log_path.unlink()
            started = time.monotonic()
            attempt_timeout = attempt_timeout_budget(remaining_timeout, attempts, index)
            returncode, terminated_after_pass, timed_out, diagnostic_info = run_unity_editor_tests.run_editor_method_process(
                attempt["cmd"],
                result_json,
                log_path,
                env=attempt["env"],
                launcher_log_path=launcher_log_path if isinstance(launcher_log_path, Path) else None,
                timeout=attempt_timeout,
            )
            elapsed = round(time.monotonic() - started, 3)
            payload = extract_payload(result_json)
            attempt_summary = {
                "launch": attempt.get("launch"),
                "mode": attempt.get("mode"),
                "returncode": returncode,
                "elapsed_seconds": elapsed,
                "terminated_after_pass": terminated_after_pass,
                "timed_out": timed_out,
                "diagnostic": diagnostic_info,
                "status": payload.get("status", "missing") if isinstance(payload, dict) else "missing",
            }
            attempt_summaries.append(attempt_summary)
            remaining_timeout = max(60, remaining_timeout - int(elapsed))

            if isinstance(payload, dict) and payload.get("status") == "pass":
                selected_attempt = attempt
                selected_payload = payload
                break
            if isinstance(payload, dict) and payload:
                selected_attempt = attempt
                selected_payload = payload
            if (
                isinstance(diagnostic_info, dict)
                and diagnostic_info.get("status") in {"blocked_license", "package_resolution_failed", "compile_error", "unity_asset_meta_invalid"}
                and index + 1 < len(attempts)
            ):
                continue

        selected_attempt = selected_attempt or attempts[-1]
        errors: list[str] = []
        log_output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        if not selected_payload:
            errors.append("unity replay runner did not emit a report payload")
            if "attempt to write a readonly database" in log_output:
                errors.append("unity host startup hit a readonly database before the replay runner executed")
        else:
            if int(selected_payload.get("loaded_packets", 0)) != int(truth["packet_count"]):
                errors.append("loaded packet count mismatch")
            if int(selected_payload.get("known_entities", 0)) < int(truth["unique_entities"]):
                errors.append("known entity count mismatch")
            if int(selected_payload.get("moved_entity_count", 0)) < int(truth["unique_entities"]):
                errors.append("moved entity count mismatch")

        payload = {
            "surface": "unity",
            "mode": "replay",
            "scenario": args.scenario,
            "scenario_suite": CORE_SCENARIO_SUITE,
            "recv_command": selected_attempt.get("unity_command"),
            "recv_returncode": next((summary["returncode"] for summary in attempt_summaries if summary["launch"] == selected_attempt.get("launch")), None),
            "recv_output": log_output,
            "report": selected_payload,
            "errors": errors,
            "truth": truth,
            "truth_file": str(truth_path),
            "replay_file": str(replay_path),
            "attempts": attempt_summaries,
            "status": "passed" if selected_payload.get("status") == "pass" and not errors else "failed",
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
