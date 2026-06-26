#!/usr/bin/env python3
"""Capture a same-host GRILL Unity benchmark baseline from the public source route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import shlex
import subprocess
import time
from typing import Any

import load_local_env
import prepare_grill_source_route
import run_grill_unity_import_smoke
import run_unity_install_smoke
import unity_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_ROOT = ROOT.parent / "GRILL_DISPluginForUnity"
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "unity_grill_baseline"
CORE_SCENARIO_NAME = "entity_state_1x10hz"
CORE_TRAFFIC_MIX = "100% Entity State"
CORE_SCENE_NAME = "editor_direct_process_smoke"
DEFAULT_COUNT = 24
DEFAULT_ENTITY_COUNT = 1
DEFAULT_RATE_HZ = 10.0
ENTITY_TYPE = (1, 2, 840, 3, 4, 5, 6)

RUNNER_SOURCE = r"""
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using GRILLDIS;
using OpenDis.Core;
using OpenDis.Dis1998;
using UnityEditor;
using UnityEngine;
using UnityEngine.Events;

public static class GrillUnityBenchmarkRunner
{
    public static void Run()
    {
        string reportPath = ReportPathFromArguments();
        if (string.IsNullOrEmpty(reportPath))
        {
            reportPath = Path.Combine(System.Environment.CurrentDirectory, "grill_unity_benchmark_capture.json");
        }

        int packetCount = ReadIntEnv("FASTDIS_GRILL_BENCHMARK_COUNT", 24);
        int entityCount = ReadIntEnv("FASTDIS_GRILL_BENCHMARK_ENTITY_COUNT", 1);
        double rateHz = ReadDoubleEnv("FASTDIS_GRILL_BENCHMARK_RATE_HZ", 10.0);

        var root = new GameObject("GRILL Unity Benchmark Root");
        var parent = new GameObject("GRILL Unity Benchmark Entities");
        parent.transform.SetParent(root.transform, false);

        var georef = root.AddComponent<GeoreferenceSystem>();
        georef.EarthShape = EEarthShape.RoundEarth;
        georef.OriginLLA = new FLatLonAlt(29.5597, -95.0831, 100.0);
        InvokePrivate(georef, "SetupVars");

        var manager = root.AddComponent<DISGameManager>();
        manager.ExerciseID = 3;
        manager.SiteID = 100;
        manager.ApplicationID = 1;
        manager.DISEntityParentContainer = parent;
        manager.e_CreateDISEntity = new UnityEvent<GameObject, EntityStatePdu>();
        manager.e_DestroyDISEntity = new UnityEvent<GameObject, EDestroyCode>();
        manager.OnNoSpecificEntityDetonationPDUReceived = new UnityEvent<DetonationPdu>();
        EnsureManagerDictionaries(manager);

        var mapping = ScriptableObject.CreateInstance<DISEnumerationMappings>();
        mapping.EntityTypeMappings = new List<EntityTypeMapping>();
        var template = BuildTemplateEntity();
        mapping.EntityTypeMappings.Add(
            new EntityTypeMapping
            {
                friendlyName = "FASTDIS Canonical Entity",
                entityTypes = new List<EntityTypeEditor> { BuildEntityTypeEditor() },
                gameObject = template,
            }
        );
        manager.DISEnumerationMapping = mapping;
        InvokePrivate(manager, "InitializeEntityTypeMappings");

        var receiver = root.AddComponent<PDUReceiver>();
        SetPrivateField(receiver, "disManagerScript", manager);

        var bytes = BuildPackets(packetCount, entityCount);
        long gcBefore = GC.GetTotalMemory(false);
        var stopwatch = Stopwatch.StartNew();
        foreach (var packet in bytes)
        {
            byte pduType = packet[OpenDis.Core.PduProcessor.PDU_TYPE_POSITION];
            var pdu = OpenDis.Core.PduProcessor.UnmarshalRawPdu(pduType, packet, Endian.Big);
            InvokePrivate(receiver, "ProcessDISPacket", pdu);
        }
        stopwatch.Stop();
        long gcAfter = GC.GetTotalMemory(false);

        int spawnedEntities = parent.transform.childCount;
        Vector3 finalPosition = spawnedEntities > 0 ? parent.transform.GetChild(0).position : Vector3.zero;
        int packetsProcessed = 0;
        int lastTimestamp = 0;
        if (spawnedEntities > 0)
        {
            var receive = parent.transform.GetChild(0).GetComponent<DISReceiveComponent>();
            if (receive != null)
            {
                packetsProcessed = ReadPrivateInt(receive, "NumberEntityStatePDUsReceived");
                if (receive.MostRecentEntityStatePDU != null)
                {
                    lastTimestamp = (int)receive.MostRecentEntityStatePDU.Timestamp;
                }
            }
        }

        double elapsedSeconds = Math.Max(stopwatch.Elapsed.TotalSeconds, 0.000001);
        double packetsPerSecond = packetCount / elapsedSeconds;
        double mainThreadMsAvg = stopwatch.Elapsed.TotalMilliseconds / Math.Max(packetCount, 1);
        long gcPerPacket = Math.Max(0L, gcAfter - gcBefore) / Math.Max(packetCount, 1);

        bool success =
            packetsProcessed == packetCount
            && spawnedEntities >= Math.Min(entityCount, 1)
            && !float.IsNaN(finalPosition.x)
            && !float.IsInfinity(finalPosition.x);

        string detail = success
            ? "GRILL Unity benchmark capture completed"
            : $"processed={packetsProcessed} spawned={spawnedEntities} final=({finalPosition.x}, {finalPosition.y}, {finalPosition.z})";

        string json =
            "{\n" +
            $"  \"status\": \"{(success ? "pass" : "fail")}\",\n" +
            "  \"scenario\": \"entity_state_1x10hz\",\n" +
            $"  \"packet_count\": {packetCount},\n" +
            $"  \"entity_count\": {entityCount},\n" +
            $"  \"rate_hz\": {rateHz.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
            $"  \"packets_processed\": {packetsProcessed},\n" +
            $"  \"spawned_entities\": {spawnedEntities},\n" +
            $"  \"elapsed_seconds\": {elapsedSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
            $"  \"packets_per_sec\": {packetsPerSecond.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
            $"  \"main_thread_ms_avg\": {mainThreadMsAvg.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
            $"  \"gc_alloc_bytes_per_packet\": {gcPerPacket},\n" +
            $"  \"last_timestamp\": {lastTimestamp},\n" +
            $"  \"detail\": \"{Escape(detail)}\",\n" +
            "  \"notes\": [\n" +
            "    \"Exercises GRILL Unity parser plus entity-spawn/apply path in an editor-method benchmark loop.\",\n" +
            "    \"This capture bypasses live UDP sockets and queues; it is a direct parse-and-apply benchmark on the current host.\",\n" +
            "    \"Scenario uses canonical one-entity Entity State traffic with 24 packets at 10 Hz semantics.\"\n" +
            "  ]\n" +
            "}\n";
        File.WriteAllText(reportPath, json, Encoding.UTF8);
        UnityEngine.Debug.Log($"GRILL Unity benchmark capture report: {reportPath}");
        EditorApplication.Exit(success ? 0 : 1);
    }

    private static EntityTypeEditor BuildEntityTypeEditor()
    {
        return new EntityTypeEditor
        {
            entityKind = 1,
            domain = 2,
            country = 840,
            category = 3,
            subcategory = 4,
            specific = 5,
            extra = 6,
            useSpecific_EntityKind = true,
            useSpecific_Domain = true,
            useSpecific_Country = true,
            useSpecific_Category = true,
            useSpecific_Subcategory = true,
            useSpecific_Specific = true,
            useSpecific_Extra = true,
        };
    }

    private static GameObject BuildTemplateEntity()
    {
        var template = new GameObject("GRILL Benchmark Entity Template");
        var receive = template.AddComponent<DISReceiveComponent>();
        receive.PerformDeadReckoning = false;
        receive.PerformDeadReckoningSmoothing = false;
        receive.PerformGroundClamping = EGroundClampingMode.None;
        receive.ApplyToOwner = true;
        receive.DISTimeoutSeconds = 999.0f;
        receive.CurrentEntityType = new EntityTypeEditor();
        receive.CurrentEntityID = new EntityIDEditor();
        receive.OnDeadReckoningUpdate = new UnityEvent<EntityStatePdu>();
        receive.OnEntityStatePDUProcessed = new UnityEvent<EntityStatePdu>();
        receive.OnEntityStateUpdatePDUProcessed = new UnityEvent<EntityStateUpdatePdu>();
        receive.OnFirePDUProcessed = new UnityEvent<FirePdu>();
        receive.OnDetonationPDUProcessed = new UnityEvent<DetonationPdu>();
        receive.OnRemoveEntityPDUProcessed = new UnityEvent<RemoveEntityPdu>();
        receive.OnStopFreezePDUProcessed = new UnityEvent<StopFreezePdu>();
        receive.OnStartResumePDUProcessed = new UnityEvent<StartResumePdu>();
        receive.OnElectronicEmissionsPDUProcessed = new UnityEvent<ElectronicEmissionsPdu>();
        receive.OnSignalPDUProcessed = new UnityEvent<SignalPdu>();
        receive.OnDesignatorPDUProcessed = new UnityEvent<DesignatorPdu>();
        receive.OnGroundClampingUpdate = new UnityEvent<Vector3, Quaternion>();
        return template;
    }

    private static void EnsureManagerDictionaries(DISGameManager manager)
    {
        SetPrivateField(manager, "entityIDDictionary", new Dictionary<ulong, GameObject>());
        SetPrivateField(manager, "entityTypeDictionary", new Dictionary<ulong, GameObject>());
        SetPrivateField(manager, "entityTypeWildcardDictionary", new Dictionary<EntityTypeEditor, GameObject>());
        SetPrivateField(manager, "georeferenceScript", manager.GetComponent<GeoreferenceSystem>());
    }

    private static List<byte[]> BuildPackets(int packetCount, int entityCount)
    {
        var packets = new List<byte[]>();
        var baseEcef = Conversions.CalculateEcefXYZFromLatLonHeight(new FLatLonAlt(29.5597, -95.0831, 100.0));
        for (int index = 0; index < packetCount; index++)
        {
            int entitySlot = index % Math.Max(entityCount, 1);
            double step = (double)index / Math.Max(entityCount, 1);
            var pdu = new EntityStatePdu();
            pdu.ProtocolVersion = 7;
            pdu.ExerciseID = 3;
            pdu.EntityID = new EntityID { Site = 100, Application = 1, Entity = (ushort)(1 + entitySlot) };
            pdu.EntityType = new EntityType { EntityKind = 1, Domain = 2, Country = 840, Category = 3, Subcategory = 4, Specific = 5, Extra = 6 };
            pdu.AlternativeEntityType = pdu.EntityType;
            pdu.ForceId = 1;
            pdu.Marking = PDUUtil.getStringAsMarking("FASTDIS");
            pdu.EntityAppearance = 0;
            pdu.Capabilities = 0;
            pdu.Timestamp = 0x10000000u + (uint)index;
            pdu.EntityLocation = new Vector3Double
            {
                X = baseEcef.X + step * 10.0,
                Y = baseEcef.Y + entitySlot * 3.0,
                Z = baseEcef.Z,
            };
            pdu.EntityOrientation = new Orientation { Psi = 0.0f, Theta = 0.0f, Phi = 0.0f };
            pdu.EntityLinearVelocity = new Vector3Float { X = 0.0f, Y = 0.0f, Z = 0.0f };
            pdu.DeadReckoningParameters = new DeadReckoningParameter
            {
                DeadReckoningAlgorithm = (byte)EDeadReckoningAlgorithm.Static,
                EntityLinearAcceleration = new Vector3Float(),
                EntityAngularVelocity = new Vector3Float(),
            };

            var dos = new DataOutputStream(Endian.Big);
            pdu.MarshalAutoLengthSet(dos);
            packets.Add(dos.ConvertToBytes());
        }
        return packets;
    }

    private static void SetPrivateField(object target, string name, object value)
    {
        var field = target.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic);
        if (field != null)
        {
            field.SetValue(target, value);
        }
    }

    private static int ReadPrivateInt(object target, string name)
    {
        var field = target.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic);
        if (field == null)
        {
            return 0;
        }
        object value = field.GetValue(target);
        return value is int number ? number : 0;
    }

    private static void InvokePrivate(object target, string name, params object[] args)
    {
        var method = target.GetType().GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic);
        if (method != null)
        {
            method.Invoke(target, args);
        }
    }

    private static string ReportPathFromArguments()
    {
        string[] args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-grillReport")
            {
                return args[i + 1];
            }
        }
        return null;
    }

    private static int ReadIntEnv(string name, int fallback)
    {
        string value = System.Environment.GetEnvironmentVariable(name);
        return int.TryParse(value, out int parsed) ? parsed : fallback;
    }

    private static double ReadDoubleEnv(string name, double fallback)
    {
        string value = System.Environment.GetEnvironmentVariable(name);
        return double.TryParse(value, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double parsed) ? parsed : fallback;
    }

    private static string Escape(string value)
    {
        return (value ?? string.Empty).Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
}
"""


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--unity-version", default="6000.5.0f1")
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--entity-count", type=int, default=DEFAULT_ENTITY_COUNT)
    parser.add_argument("--rate-hz", type=float, default=DEFAULT_RATE_HZ)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--prepare-checkout", dest="prepare_checkout", action="store_true", help="Fetch and switch the local GRILL Unity source checkout onto its expected benchmark branch before capture.")
    parser.add_argument("--no-prepare-checkout", dest="prepare_checkout", action="store_false", help="Skip automatic GRILL Unity checkout preparation.")
    parser.set_defaults(prepare_checkout=None)
    return parser.parse_args(argv)


def _git_commit(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _host_payload() -> dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }


def _runner_command(editor: str, project_dir: Path, report_path: Path, log_path: Path) -> list[str]:
    return [
        editor,
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(project_dir),
        "-executeMethod",
        "GrillUnityBenchmarkRunner.Run",
        "-grillReport",
        str(report_path),
        "-logFile",
        str(log_path),
    ]


def _attempts(install: unity_env.UnityInstall, project_dir: Path, report_dir: Path) -> list[dict[str, object]]:
    result_json = report_dir / "grill_unity_benchmark_capture_runner.json"
    log_path = report_dir / "grill_unity_benchmark_capture.log"
    cmd = _runner_command(install.editor_path or "", project_dir, result_json, log_path)
    attempts: list[dict[str, object]] = []
    attempts.append(
        {
            "launch": "login-shell",
            "mode": "interactive",
            "cmd": ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in cmd)],
            "log": log_path,
            "launcher_log": report_dir / "grill_unity_benchmark_capture_login_shell_launcher.log",
            "results_json": result_json,
        }
    )
    if install.editor_app_path:
        attempts.append(
            {
                "launch": "launch-services",
                "mode": "interactive",
                "cmd": ["open", "-W", "-n", "-a", install.editor_app_path, "--args", *cmd[1:]],
                "log": log_path,
                "launcher_log": report_dir / "grill_unity_benchmark_capture_launch_services_launcher.log",
                "results_json": result_json,
            }
        )
    return attempts


def _run_attempt(cmd: list[str], *, env: dict[str, str], launcher_log_path: Path, timeout: int) -> tuple[int, bool]:
    launcher_log_path.parent.mkdir(parents=True, exist_ok=True)
    with launcher_log_path.open("w", encoding="utf-8") as handle:
        try:
            completed = subprocess.run(
                cmd,
                cwd=ROOT,
                env=env,
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
            return completed.returncode, False
        except subprocess.TimeoutExpired:
            return -15, True


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_baseline_payload(
    runner_report: dict[str, Any],
    *,
    plugin_root: Path,
    unity_version: str,
    count: int,
    entity_count: int,
    rate_hz: float,
) -> dict[str, Any]:
    notes = runner_report.get("notes") if isinstance(runner_report.get("notes"), list) else []
    notes = [str(note) for note in notes]
    notes.append("Captured automatically from the public GRILL Unity source route on the current host.")
    notes.append(
        "Benchmark scratch project explicitly enabled com.unity.modules.imgui=1.0.0 and "
        "com.unity.modules.physics=1.0.0 for Unity 6000 compatibility."
    )
    return {
        "schema": "fastdis.unity_grill_benchmark_baseline.v1",
        "product": "GRILL DIS for Unity",
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repository": {
            "url": "https://github.com/AF-GRILL/DISPluginForUnity",
            "commit": _git_commit(plugin_root),
        },
        "unity": {
            "version": unity_version,
            "render_pipeline": "builtin",
            "scripting_backend": "Mono",
        },
        "host": _host_payload(),
        "scenario": {
            "scene": CORE_SCENE_NAME,
            "traffic_mix": CORE_TRAFFIC_MIX,
            "entity_counts": [entity_count],
            "update_hz": [rate_hz],
            "notes": "Automated editor-method parser/apply benchmark on the public GRILL Unity source route.",
        },
        "results": [
            {
                "case": CORE_SCENARIO_NAME,
                "entity_count": entity_count,
                "update_hz": rate_hz,
                "packets_per_sec": runner_report.get("packets_per_sec"),
                "main_thread_ms_avg": runner_report.get("main_thread_ms_avg"),
                "gc_alloc_bytes_per_frame": runner_report.get("gc_alloc_bytes_per_packet"),
                "notes": " ".join(notes),
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "grill_unity_benchmark_baseline.json"
    md_path = args.out_dir / "grill_unity_benchmark_baseline.md"
    runner_json = args.out_dir / "grill_unity_benchmark_capture_runner.json"
    project_dir = args.project_dir or (unity_env.work_root() / "grill_unity_benchmark_capture_project")

    if json_path.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {json_path}")
    if not args.plugin_root.exists():
        raise SystemExit(f"GRILL plugin root not found: {args.plugin_root}")

    prepare_checkout = (
        args.plugin_root.expanduser().resolve() == DEFAULT_PLUGIN_ROOT.resolve()
        if args.prepare_checkout is None
        else bool(args.prepare_checkout)
    )
    if prepare_checkout and args.plugin_root.is_dir():
        prep_report = prepare_grill_source_route.build_report(
            [
                prepare_grill_source_route.RepoSpec(
                    key="unity_plugin",
                    label="GRILL Unity plugin",
                    path=args.plugin_root.expanduser().resolve(),
                    target_branch="main",
                )
            ],
            fetch=True,
            allow_dirty=False,
            update_submodules=False,
        )
        failed = [
            row
            for row in (prep_report.get("repos") if isinstance(prep_report.get("repos"), list) else [])
            if isinstance(row, dict) and row.get("status") != "prepared"
        ]
        if failed:
            raise SystemExit("GRILL Unity checkout preparation failed before benchmark capture.")

    install = unity_env.resolve_install(args.unity_version)
    if install is None or not install.editor_path:
        raise SystemExit(f"Unity editor not found for version {args.unity_version}")

    run_grill_unity_import_smoke.create_project(project_dir, args.plugin_root, install.version)
    run_grill_unity_import_smoke.enable_required_builtin_modules(project_dir)
    _write_text(project_dir / "Assets" / "Editor" / "GrillUnityBenchmarkRunner.cs", RUNNER_SOURCE)
    attempts = _attempts(install, project_dir, args.out_dir)
    run_unity_install_smoke.clear_previous_artifacts(
        json_path,
        md_path,
        runner_json,
        args.out_dir / "grill_unity_benchmark_capture.log",
        *[attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)],
    )

    selected_attempt: dict[str, object] | None = None
    runner_report: dict[str, Any] | None = None
    env = unity_env.build_env()
    env["FASTDIS_UNITY_PRESERVE_HOME"] = "1"
    env["FASTDIS_GRILL_BENCHMARK_COUNT"] = str(args.count)
    env["FASTDIS_GRILL_BENCHMARK_ENTITY_COUNT"] = str(args.entity_count)
    env["FASTDIS_GRILL_BENCHMARK_RATE_HZ"] = str(args.rate_hz)
    for attempt in attempts:
        selected_attempt = attempt
        run_unity_install_smoke.clear_previous_artifacts(runner_json, attempt["launcher_log"])
        returncode, timed_out = _run_attempt(
            attempt["cmd"],
            env=env,
            launcher_log_path=attempt["launcher_log"],
            timeout=args.timeout,
        )
        if runner_json.is_file():
            runner_report = _load_json(runner_json)
            runner_report["returncode"] = returncode
            runner_report["timed_out"] = timed_out
            runner_report["launch"] = attempt["launch"]
            break
        if not timed_out and returncode == 0:
            break

    if runner_report is None:
        raise SystemExit("GRILL Unity benchmark runner did not produce a capture report")

    baseline = build_baseline_payload(
        runner_report,
        plugin_root=args.plugin_root,
        unity_version=install.version,
        count=args.count,
        entity_count=args.entity_count,
        rate_hz=args.rate_hz,
    )
    json_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# GRILL Unity Benchmark Baseline",
        "",
        f"- scenario: `{CORE_SCENARIO_NAME}`",
        f"- status: `{runner_report.get('status')}`",
        f"- unity_version: `{install.version}`",
        f"- launch: `{selected_attempt['launch'] if selected_attempt else 'unknown'}`",
        f"- packets_per_sec: `{runner_report.get('packets_per_sec')}`",
        f"- main_thread_ms_avg: `{runner_report.get('main_thread_ms_avg')}`",
        f"- gc_alloc_bytes_per_packet: `{runner_report.get('gc_alloc_bytes_per_packet')}`",
        f"- runner_report: `{runner_json}`",
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"baseline json: {json_path}")
    print(f"baseline md: {md_path}")
    return 0 if runner_report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
