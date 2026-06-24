#!/usr/bin/env python3
"""Compile and run the Unity package's non-UnityEngine C# bridge under plain dotnet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "build" / "reports"


def _native_library_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        candidate = ROOT / "build" / "cmake" / "host" / "libfastdis.dylib"
    elif system == "Linux":
        candidate = ROOT / "build" / "cmake" / "host" / "libfastdis.so"
    elif system == "Windows":
        candidate = ROOT / "build" / "cmake" / "host" / "Release" / "fastdis.dll"
        if not candidate.exists():
            candidate = ROOT / "build" / "cmake" / "host" / "fastdis.dll"
    else:
        raise RuntimeError(f"unsupported host platform for unity bridge probe: {system}")
    if not candidate.exists():
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_native.py")], cwd=ROOT, check=True)
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    return candidate


def _csproj_text(native_library: Path) -> str:
    runtime = ROOT / "integrations" / "unity" / "com.sheepfling.fastdis" / "Runtime"
    files = [
        runtime / "Native" / "FastDisTypes.cs",
        runtime / "Native" / "FastDisNative.cs",
        runtime / "Scanning" / "FastDisPacketView.cs",
        runtime / "Scanning" / "FastDisScanner.cs",
    ]
    compile_items = "\n".join(
        f'    <Compile Include="{path}"><Link>{path.name}</Link></Compile>'
        for path in files
    )
    return f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
{compile_items}
  </ItemGroup>
  <ItemGroup>
    <None Include="{native_library}">
      <Link>{native_library.name}</Link>
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
    </None>
  </ItemGroup>
</Project>
"""


PROGRAM_TEXT = r"""using System;
using System.Text;
using FastDIS.Native;
using FastDIS.Scanning;

static class Program
{
    private const ulong FastDisEsFieldForceId = 0x0000000000000004UL;
    private const ulong FastDisEsFieldLocation = 0x0000000000000080UL;
    private const ulong FastDisEsFieldLinearVelocity = 0x0000000000000040UL;

    static int Main()
    {
        if (!FastDisNative.TryGetAbiVersion(out uint abiVersion) || abiVersion == 0)
        {
            throw new InvalidOperationException("failed to load fastdis native library");
        }

        if (abiVersion != FastDisNative.AbiVersion)
        {
            throw new InvalidOperationException($"unexpected abi version {abiVersion}");
        }

        FastDisScanner scanner = new FastDisScanner();
        AssertEntityState(scanner, 6);
        AssertEntityState(scanner, 7);
        AssertEntityStateUpdate(scanner, 6);
        AssertEntityStateUpdate(scanner, 7);
        AssertCreateEntity(scanner, 6);
        AssertCreateEntity(scanner, 7);
        AssertRemoveEntity(scanner, 6);
        AssertRemoveEntity(scanner, 7);
        AssertStartResume(scanner, 6);
        AssertStartResume(scanner, 7);
        AssertStopFreeze(scanner, 6);
        AssertStopFreeze(scanner, 7);

        var transforms = scanner.ScanEntityTransforms(new[]
        {
            CreateEntityStatePdu(7, 2),
            new byte[] { 7, 1, 2, 2, 0, 0, 0, 1, 0, 12, 0, 0 },
            CreateEntityStateUpdatePdu(7),
        });
        if (transforms.Count != 2)
        {
            throw new InvalidOperationException($"expected 2 typed transforms, found {transforms.Count}");
        }

        Console.WriteLine("{\"status\":\"pass\",\"schema\":\"fastdis.unity.csharp_bridge_probe.v1\"}");
        return 0;
    }

    private static void AssertEntityState(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseEntityTransform(CreateEntityStatePdu(version, 2), out FastDisEntityTransform transform))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Entity State");
        }

        Expect(transform.EntityId.Site == 0x1111, "entity state site");
        Expect(transform.EntityId.Application == 0x2222, "entity state application");
        Expect(transform.EntityId.Entity == 0x3333, "entity state entity");
        Expect(transform.ForceId == 2, "entity state force");
        Expect(transform.ExerciseId == 3, "entity state exercise");
        Expect(transform.Version == version, "entity state version");
        Expect(transform.Timestamp == 0x01020304u, "entity state timestamp");
        Expect(transform.Appearance == 0xAABBCCDDu, "entity state appearance");
        Expect(Math.Abs(transform.Location.X - 10.0) < 0.0001, "entity state location.x");
        Expect(Math.Abs(transform.Location.Y - 20.0) < 0.0001, "entity state location.y");
        Expect(Math.Abs(transform.Location.Z - 30.0) < 0.0001, "entity state location.z");
        Expect(Math.Abs(transform.Orientation.Phi - 0.3f) < 0.0001f, "entity state phi");
        Expect(Math.Abs(transform.LinearVelocity.X - 1.25f) < 0.0001f, "entity state velocity");
        Expect(transform.DeadReckoningAlgorithm == 4, "entity state DR algorithm");
        Expect(transform.DeadReckoningParameters.Length == 15 && transform.DeadReckoningParameters[0] == 1, "entity state DR parameters");
        Expect(Math.Abs(transform.DeadReckoningLinearAcceleration.X - 0.5f) < 0.0001f, "entity state acceleration");
        Expect(Math.Abs(transform.DeadReckoningAngularVelocity.Z - 1.7f) < 0.0001f, "entity state angular velocity");
        Expect((transform.FieldsPresent & FastDisEsFieldForceId) != 0UL, "entity state fields force");
        Expect((transform.FieldsPresent & FastDisEsFieldLocation) != 0UL, "entity state fields location");
        Expect((transform.FieldsPresent & FastDisEsFieldLinearVelocity) != 0UL, "entity state fields velocity");
    }

    private static void AssertEntityStateUpdate(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseEntityTransform(CreateEntityStateUpdatePdu(version), out FastDisEntityTransform transform))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Entity State Update");
        }

        Expect(transform.EntityId.Site == 0x1111, "esu site");
        Expect(transform.EntityId.Application == 0x2222, "esu application");
        Expect(transform.EntityId.Entity == 0x3333, "esu entity");
        Expect(transform.ForceId == 0, "esu force");
        Expect(transform.ExerciseId == 3, "esu exercise");
        Expect(transform.Version == version, "esu version");
        Expect(transform.Timestamp == 0x01020304u, "esu timestamp");
        Expect(transform.Appearance == 0x11223344u, "esu appearance");
        Expect(Math.Abs(transform.Location.X - 40.0) < 0.0001, "esu location.x");
        Expect(Math.Abs(transform.Location.Y - 50.0) < 0.0001, "esu location.y");
        Expect(Math.Abs(transform.Location.Z - 60.0) < 0.0001, "esu location.z");
        Expect(Math.Abs(transform.LinearVelocity.Z - 6.0f) < 0.0001f, "esu velocity.z");
        Expect(Math.Abs(transform.Orientation.Theta - 0.5f) < 0.0001f, "esu theta");
        Expect((transform.FieldsPresent & FastDisEsFieldForceId) == 0UL, "esu no force field");
        Expect((transform.FieldsPresent & FastDisEsFieldLocation) != 0UL, "esu location field");
        Expect((transform.FieldsPresent & FastDisEsFieldLinearVelocity) != 0UL, "esu velocity field");
    }

    private static void AssertCreateEntity(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseCreateEntity(CreateCreateEntityPdu(version), out FastDisSimulationManagementRequest request))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Create Entity");
        }

        Expect(request.Header.PduType == 11, "create pdu type");
        Expect(request.Header.ProtocolFamily == 5, "create family");
        Expect(request.Header.Version == version, "create version");
        Expect(request.OriginatingEntityId.Site == 0x1111, "create origin site");
        Expect(request.ReceivingEntityId.Entity == 0x6666, "create recv entity");
        Expect(request.RequestId == 0xA0B0C0D0u, "create request id");
    }

    private static void AssertRemoveEntity(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseRemoveEntity(CreateRemoveEntityPdu(version), out FastDisSimulationManagementRequest request))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Remove Entity");
        }

        Expect(request.Header.PduType == 12, "remove pdu type");
        Expect(request.Header.ProtocolFamily == 5, "remove family");
        Expect(request.Header.Version == version, "remove version");
        Expect(request.OriginatingEntityId.Application == 0x2222, "remove origin application");
        Expect(request.ReceivingEntityId.Site == 0x4444, "remove recv site");
        Expect(request.RequestId == 0x0BADF00Du, "remove request id");
    }

    private static void AssertStartResume(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseStartResume(CreateStartResumePdu(version), out FastDisStartResume request))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Start/Resume");
        }

        Expect(request.Header.PduType == 13, "start pdu type");
        Expect(request.Header.Version == version, "start version");
        Expect(request.RealWorldTime.Hour == 7u, "start real hour");
        Expect(request.RealWorldTime.TimePastHour == 123456u, "start real past hour");
        Expect(request.SimulationTime.Hour == 9u, "start sim hour");
        Expect(request.SimulationTime.TimePastHour == 654321u, "start sim past hour");
        Expect(request.RequestId == 0x01020304u, "start request id");
    }

    private static void AssertStopFreeze(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseStopFreeze(CreateStopFreezePdu(version), out FastDisStopFreeze request))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Stop/Freeze");
        }

        Expect(request.Header.PduType == 14, "stop pdu type");
        Expect(request.Header.Version == version, "stop version");
        Expect(request.RealWorldTime.Hour == 5u, "stop real hour");
        Expect(request.RealWorldTime.TimePastHour == 7654321u, "stop real past hour");
        Expect(request.Reason == 3, "stop reason");
        Expect(request.FrozenBehavior == 4, "stop frozen behavior");
        Expect(request.Padding1 == 0xABCD, "stop padding1");
        Expect(request.RequestId == 0x0F1E2D3Cu, "stop request id");
    }

    private static void Expect(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static byte[] CreateEntityStatePdu(byte version, byte forceId)
    {
        byte[] packet = CreatePdu(version, 1, 144);
        packet[3] = 1;
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
        WriteU16(packet, body + 6, 0);
        WriteVec3(packet, body + 8, 4.0f, 5.0f, 6.0f);
        WriteWorld(packet, body + 20, 40.0, 50.0, 60.0);
        WriteVec3(packet, body + 44, 0.4f, 0.5f, 0.6f);
        WriteU32(packet, body + 56, 0x11223344u);
        return packet;
    }

    private static byte[] CreateCreateEntityPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 11, 28);
        packet[3] = 5;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU32(packet, body + 12, 0xA0B0C0D0u);
        return packet;
    }

    private static byte[] CreateRemoveEntityPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 12, 28);
        packet[3] = 5;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU32(packet, body + 12, 0x0BADF00Du);
        return packet;
    }

    private static byte[] CreateStartResumePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 13, 44);
        packet[3] = 5;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU32(packet, body + 12, 7u);
        WriteU32(packet, body + 16, 123456u);
        WriteU32(packet, body + 20, 9u);
        WriteU32(packet, body + 24, 654321u);
        WriteU32(packet, body + 28, 0x01020304u);
        return packet;
    }

    private static byte[] CreateStopFreezePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 14, 40);
        packet[3] = 5;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU32(packet, body + 12, 5u);
        WriteU32(packet, body + 16, 7654321u);
        packet[body + 20] = 3;
        packet[body + 21] = 4;
        WriteU16(packet, body + 22, 0xABCD);
        WriteU32(packet, body + 24, 0x0F1E2D3Cu);
        return packet;
    }

    private static byte[] CreatePdu(byte version, byte pduType, ushort length)
    {
        byte[] packet = new byte[160];
        packet[0] = version;
        packet[1] = 3;
        packet[2] = pduType;
        packet[3] = 1;
        packet[4] = 0x01;
        packet[5] = 0x02;
        packet[6] = 0x03;
        packet[7] = 0x04;
        WriteU16(packet, 8, length);
        if (version >= 7)
        {
            packet[10] = 0x80;
            packet[11] = 0x00;
        }
        else
        {
            packet[10] = 0x12;
            packet[11] = 0x34;
        }
        return packet;
    }

    private static void WriteU16(byte[] packet, int offset, ushort value)
    {
        packet[offset + 0] = (byte)((value >> 8) & 0xff);
        packet[offset + 1] = (byte)(value & 0xff);
    }

    private static void WriteU32(byte[] packet, int offset, uint value)
    {
        packet[offset + 0] = (byte)((value >> 24) & 0xff);
        packet[offset + 1] = (byte)((value >> 16) & 0xff);
        packet[offset + 2] = (byte)((value >> 8) & 0xff);
        packet[offset + 3] = (byte)(value & 0xff);
    }

    private static void WriteU64(byte[] packet, int offset, ulong value)
    {
        packet[offset + 0] = (byte)((value >> 56) & 0xff);
        packet[offset + 1] = (byte)((value >> 48) & 0xff);
        packet[offset + 2] = (byte)((value >> 40) & 0xff);
        packet[offset + 3] = (byte)((value >> 32) & 0xff);
        packet[offset + 4] = (byte)((value >> 24) & 0xff);
        packet[offset + 5] = (byte)((value >> 16) & 0xff);
        packet[offset + 6] = (byte)((value >> 8) & 0xff);
        packet[offset + 7] = (byte)(value & 0xff);
    }

    private static void WriteFloat(byte[] packet, int offset, float value)
    {
        WriteU32(packet, offset, (uint)BitConverter.SingleToInt32Bits(value));
    }

    private static void WriteDouble(byte[] packet, int offset, double value)
    {
        WriteU64(packet, offset, (ulong)BitConverter.DoubleToInt64Bits(value));
    }

    private static void WriteVec3(byte[] packet, int offset, float x, float y, float z)
    {
        WriteFloat(packet, offset + 0, x);
        WriteFloat(packet, offset + 4, y);
        WriteFloat(packet, offset + 8, z);
    }

    private static void WriteWorld(byte[] packet, int offset, double x, double y, double z)
    {
        WriteDouble(packet, offset + 0, x);
        WriteDouble(packet, offset + 8, y);
        WriteDouble(packet, offset + 16, z);
    }
}
"""


def run_probe(out_dir: Path) -> dict[str, object]:
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        raise RuntimeError("dotnet is required for the Unity C# bridge probe")

    native_library = _native_library_path()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fastdis_unity_csharp_probe_") as tmp:
        tmpdir = Path(tmp)
        project = tmpdir / "FastDisUnityBridgeProbe.csproj"
        program = tmpdir / "Program.cs"
        project.write_text(_csproj_text(native_library), encoding="utf-8")
        program.write_text(PROGRAM_TEXT, encoding="utf-8")

        completed = subprocess.run(
            [dotnet, "run", "--project", str(project), "-c", "Release"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            check=False,
        )

    payload = {
        "schema": "fastdis.unity.csharp_bridge_probe.v1",
        "overall_status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "native_library": str(native_library),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    (out_dir / "unity_csharp_bridge_probe.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out_dir / "unity_csharp_bridge_probe.md").write_text(
        "\n".join(
            [
                "# Unity C# Bridge Probe",
                "",
                f"- status: `{payload['overall_status']}`",
                f"- native_library: `{payload['native_library']}`",
                f"- returncode: `{payload['returncode']}`",
                "",
                "## stdout",
                "",
                "```text",
                completed.stdout.rstrip(),
                "```",
                "",
                "## stderr",
                "",
                "```text",
                completed.stderr.rstrip(),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPORTS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run_probe(args.out_dir)
    print(f"JSON: {args.out_dir / 'unity_csharp_bridge_probe.json'}")
    print(f"Markdown: {args.out_dir / 'unity_csharp_bridge_probe.md'}")
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
