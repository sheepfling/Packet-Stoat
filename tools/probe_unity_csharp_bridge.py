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
    runtime = ROOT / "packages" / "unity" / "com.sheepfling.fastdis" / "Runtime"
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
        AssertReliableSimulationManagement(scanner, 6);
        AssertReliableSimulationManagement(scanner, 7);
        AssertLogistics(scanner, 6);
        AssertLogistics(scanner, 7);
        AssertRadioAndDesignator(scanner, 6);
        AssertRadioAndDesignator(scanner, 7);
        AssertLateDis7FixedPrefix(scanner);
        AssertFire(scanner, 6);
        AssertFire(scanner, 7);
        AssertDetonation(scanner, 6);
        AssertDetonation(scanner, 7);
        AssertRemoveEntity(scanner, 6);
        AssertRemoveEntity(scanner, 7);
        AssertStartResume(scanner, 6);
        AssertStartResume(scanner, 7);
        AssertStopFreeze(scanner, 6);
        AssertStopFreeze(scanner, 7);
        AssertOtherAndEntityManagement(scanner);
        AssertMinefield(scanner);
        AssertSyntheticEnvironment(scanner);

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

    private static void AssertFire(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseFire(CreateFirePdu(version), out FastDisFire fire))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Fire");
        }

        Expect(fire.Header.PduType == 2, "fire pdu type");
        Expect(fire.Header.ProtocolFamily == 2, "fire family");
        Expect(fire.Header.Version == version, "fire version");
        Expect(fire.FiringEntityId.Entity == 0x0003, "fire firing entity");
        Expect(fire.TargetEntityId.Entity == 0x0006, "fire target entity");
        Expect(fire.MunitionEntityId.Entity == 0x0009, "fire munition entity");
        Expect(fire.EventId.EventNumber == 0x000C, "fire event number");
        Expect(fire.FireMissionIndex == 99u, "fire mission index");
        Expect(Math.Abs(fire.WorldLocation.X - 1000.5) < 0.0001, "fire world x");
        Expect(fire.MunitionDescriptor.Rate == 600, "fire descriptor rate");
        Expect(Math.Abs(fire.RangeToTarget - 4444.5f) < 0.0001f, "fire range");
    }

    private static void AssertDetonation(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseDetonation(CreateDetonationPdu(version), out FastDisDetonation detonation))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Detonation");
        }

        Expect(detonation.Header.PduType == 3, "detonation pdu type");
        Expect(detonation.Header.ProtocolFamily == 2, "detonation family");
        Expect(detonation.Header.Version == version, "detonation version");
        Expect(detonation.ExplodingEntityId.Entity == 0x0009, "detonation exploding entity");
        Expect(detonation.EventId.EventNumber == 0x000C, "detonation event number");
        Expect(Math.Abs(detonation.WorldLocation.Z - 333.75) < 0.0001, "detonation world z");
        Expect(detonation.MunitionDescriptor.Warhead == 101, "detonation warhead");
        Expect(Math.Abs(detonation.LocationInEntityCoordinates.X + 4.0f) < 0.0001f, "detonation local x");
        Expect(detonation.DetonationResult == 17, "detonation result");
        Expect(detonation.VariableParameterCount == 1, "detonation variable parameter count");
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

    private static void AssertOtherAndEntityManagement(FastDisScanner scanner)
    {
        if (!scanner.TryParseOtherPdu(CreateOtherPdu(6), out FastDisOtherPdu other))
        {
            throw new InvalidOperationException("failed to parse DIS6 Other");
        }
        Expect(other.Header.Version == 6, "other version");
        Expect(other.Header.ProtocolFamily == 0, "other family");
        Expect(other.OpaquePayloadBytes.Length == 4 && other.OpaquePayloadBytes[0] == 0x4F, "other payload");

        if (!scanner.TryParseAggregateState(CreateAggregateStatePdu(7), out FastDisAggregateState aggregate))
        {
            throw new InvalidOperationException("failed to parse DIS7 Aggregate State");
        }
        Expect(aggregate.Header.Version == 7, "aggregate version");
        Expect(aggregate.AggregateId.Entity == 3, "aggregate entity");
        Expect(aggregate.ForceId == 4, "aggregate force");
        Expect(aggregate.AggregateStateValue == 5, "aggregate state");
        Expect(aggregate.AggregateType.Country == 840, "aggregate type");
        Expect(aggregate.Formation == 0x11223344u, "aggregate formation");
        Expect(aggregate.AggregateMarkingCharacterSet == 1, "aggregate charset");
        Expect(Encoding.ASCII.GetString(aggregate.AggregateMarkingBytes).TrimEnd('\0').StartsWith("AGGREGATE-ALPHA"), "aggregate marking");
        Expect(Math.Abs(aggregate.Dimensions.Y - 2.0f) < 0.0001f, "aggregate dimensions");
        Expect(Math.Abs(aggregate.Orientation.Theta - 0.2f) < 0.0001f, "aggregate orientation");
        Expect(Math.Abs(aggregate.CenterOfMass.Z - 30.0) < 0.0001, "aggregate center");
        Expect(Math.Abs(aggregate.Velocity.X - 4.0f) < 0.0001f, "aggregate velocity");
        Expect(aggregate.NumberOfDisAggregates == 7, "aggregate dis aggregates");
        Expect(aggregate.NumberOfDisEntities == 8, "aggregate dis entities");
        Expect(aggregate.NumberOfSilentAggregateTypes == 9, "aggregate silent aggregate");
        Expect(aggregate.NumberOfSilentEntityTypes == 10, "aggregate silent entity");
        Expect(aggregate.AggregateRecordBytes.Length == 6 && aggregate.AggregateRecordBytes[0] == 0xA1, "aggregate tail");

        if (!scanner.TryParseIsGroupOf(CreateIsGroupOfPdu(6), out FastDisIsGroupOf group))
        {
            throw new InvalidOperationException("failed to parse DIS6 Is Group Of");
        }
        Expect(group.Header.Version == 6, "group version");
        Expect(group.GroupEntityId.Entity == 3, "group entity");
        Expect(group.GroupedEntityCategory == 0x21, "group category");
        Expect(group.NumberOfGroupedEntities == 0x02, "group count");
        Expect(group.Pad2 == 0x10203040u, "group pad2");
        Expect(Math.Abs(group.Latitude - 41.25) < 0.0001, "group latitude");
        Expect(Math.Abs(group.Longitude + 93.5) < 0.0001, "group longitude");
        Expect(group.GroupedEntityDescriptionBytes.Length == 4 && group.GroupedEntityDescriptionBytes[0] == 0xB1, "group tail");

        if (!scanner.TryParseTransferControlRequest(CreateTransferControlRequestPdu(6), out FastDisTransferControlRequest transferControl))
        {
            throw new InvalidOperationException("failed to parse DIS6 Transfer Control Request");
        }
        Expect(transferControl.Header.Version == 6, "transfer control version");
        Expect(transferControl.OriginatingEntityId.Entity == 3, "transfer control origin");
        Expect(transferControl.ReceivingEntityId.Site == 4, "transfer control receive");
        Expect(transferControl.RequestId == 0x11223344u, "transfer control request");
        Expect(transferControl.RequiredReliabilityService == 0x07, "transfer control reliability");
        Expect(transferControl.TransferType == 0x08, "transfer control type");
        Expect(transferControl.TransferEntityId.Entity == 9, "transfer control transfer entity");
        Expect(transferControl.NumberOfRecordSets == 0x02, "transfer control record count");
        Expect(transferControl.RecordSetBytes.Length == 4 && transferControl.RecordSetBytes[0] == 0xC1, "transfer control tail");

        if (!scanner.TryParseTransferOwnership(CreateTransferOwnershipPdu(7), out FastDisTransferOwnership transferOwnership))
        {
            throw new InvalidOperationException("failed to parse DIS7 Transfer Ownership");
        }
        Expect(transferOwnership.Header.Version == 7, "transfer ownership version");
        Expect(transferOwnership.OriginatingEntityId.Site == 10, "transfer ownership origin");
        Expect(transferOwnership.ReceivingEntityId.Entity == 15, "transfer ownership receive");
        Expect(transferOwnership.RequestId == 0x55667788u, "transfer ownership request");
        Expect(transferOwnership.RequiredReliabilityService == 0x09, "transfer ownership reliability");
        Expect(transferOwnership.TransferType == 0x0A, "transfer ownership type");
        Expect(transferOwnership.TransferEntityId.Application == 17, "transfer ownership transfer entity");
        Expect(transferOwnership.NumberOfRecordSets == 0x03, "transfer ownership record count");
        Expect(transferOwnership.RecordSetBytes.Length == 4 && transferOwnership.RecordSetBytes[0] == 0xD1, "transfer ownership tail");

        if (!scanner.TryParseIsPartOf(CreateIsPartOfPdu(7), out FastDisIsPartOf part))
        {
            throw new InvalidOperationException("failed to parse DIS7 Is Part Of");
        }
        Expect(part.Header.Version == 7, "is part of version");
        Expect(part.OriginatingEntityId.Entity == 3, "is part of origin");
        Expect(part.ReceivingEntityId.Site == 4, "is part of receive");
        Expect(part.RelationshipNature == 0x1112, "is part of nature");
        Expect(part.RelationshipPosition == 0x1314, "is part of position");
        Expect(Math.Abs(part.PartLocation.Y - 8.0f) < 0.0001f, "is part of location");
        Expect(part.StationName == 0x2122, "is part of station name");
        Expect(part.StationNumber == 0x2324, "is part of station number");
        Expect(part.PartEntityType.Country == 225, "is part of type");
        Expect(part.PartEntityType.Extra == 7, "is part of extra");
    }

    private static void AssertMinefield(FastDisScanner scanner)
    {
        if (!scanner.TryParseMinefieldState(CreateMinefieldStatePdu(6), out FastDisMinefieldState state6))
        {
            throw new InvalidOperationException("failed to parse DIS6 Minefield State");
        }
        Expect(state6.Header.Version == 6, "minefield state6 version");
        Expect(state6.MinefieldId.Entity == 223, "minefield state6 id");
        Expect(state6.MinefieldSequence == 224, "minefield state6 sequence");
        Expect(state6.ForceId == 225, "minefield state6 force");
        Expect(state6.NumberOfPerimeterPoints == 2, "minefield state6 perimeter count");
        Expect(state6.MinefieldType.Country == 840, "minefield state6 type");
        Expect(state6.NumberOfMineTypes == 2, "minefield state6 mine types");
        Expect(Math.Abs(state6.MinefieldLocation.X - 10.25) < 0.0001, "minefield state6 location");
        Expect(Math.Abs(state6.MinefieldOrientation.Theta - 0.2f) < 0.0001f, "minefield state6 orientation");
        Expect(state6.Appearance == 226, "minefield state6 appearance");
        Expect(state6.ProtocolMode == 227, "minefield state6 protocol mode");
        Expect(state6.PerimeterPointBytes.Length == 16, "minefield state6 perimeter bytes");
        Expect(state6.MineTypeBytes.Length == 16, "minefield state6 mine bytes");

        if (!scanner.TryParseMinefieldState(CreateMinefieldStatePdu(7), out FastDisMinefieldState state7))
        {
            throw new InvalidOperationException("failed to parse DIS7 Minefield State");
        }
        Expect(state7.Header.Version == 7, "minefield state7 version");
        Expect(state7.MinefieldId.Site == 231, "minefield state7 site");
        Expect(state7.MinefieldId.Application == 232, "minefield state7 app");
        Expect(state7.MinefieldId.Entity == 233, "minefield state7 entity");
        Expect(state7.MinefieldSequence == 234, "minefield state7 sequence");
        Expect(state7.ForceId == 235, "minefield state7 force");
        Expect(state7.MinefieldType.Country == 225, "minefield state7 type");

        if (!scanner.TryParseMinefieldQuery(CreateMinefieldQueryPdu(6), out FastDisMinefieldQuery query))
        {
            throw new InvalidOperationException("failed to parse DIS6 Minefield Query");
        }
        Expect(query.Header.Version == 6, "minefield query version");
        Expect(query.MinefieldId.Entity == 203, "minefield query id");
        Expect(query.RequestingEntityId.Entity == 206, "minefield query requester");
        Expect(query.RequestId == 207, "minefield query request");
        Expect(query.NumberOfPerimeterPoints == 2, "minefield query perimeter count");
        Expect(query.NumberOfSensorTypes == 2, "minefield query sensor count");
        Expect(query.DataFilter == 0x01020304u, "minefield query filter");
        Expect(query.RequestedMineType.Country == 225, "minefield query type");
        Expect(query.RequestedPerimeterPointBytes.Length == 16, "minefield query perimeter bytes");
        Expect(query.SensorTypeBytes.Length == 4, "minefield query sensor bytes");

        if (!scanner.TryParseMinefieldData(CreateMinefieldDataPdu(7), out FastDisMinefieldData data))
        {
            throw new InvalidOperationException("failed to parse DIS7 Minefield Data");
        }
        Expect(data.Header.Version == 7, "minefield data version");
        Expect(data.MinefieldId.Entity == 253, "minefield data id");
        Expect(data.RequestingEntityId.Entity == 256, "minefield data requester");
        Expect(data.MinefieldSequenceNumber == 257, "minefield data sequence");
        Expect(data.RequestId == 200, "minefield data request");
        Expect(data.PduSequenceNumber == 3, "minefield data pdu sequence");
        Expect(data.NumberOfPdus == 2, "minefield data pdus");
        Expect(data.NumberOfMinesInThisPdu == 2, "minefield data mines");
        Expect(data.NumberOfSensorTypes == 2, "minefield data sensor count");
        Expect(data.DataFilter == 0x01020304u, "minefield data filter");
        Expect(data.MineType.Country == 225, "minefield data type");
        Expect(data.SensorTypeBytes.Length == 4, "minefield data sensor bytes");
        Expect(data.MineLocationBytes.Length == 24, "minefield data location bytes");

        if (!scanner.TryParseMinefieldResponseNack(CreateMinefieldResponseNackPdu(6), out FastDisMinefieldResponseNack nack))
        {
            throw new InvalidOperationException("failed to parse DIS6 Minefield Response NACK");
        }
        Expect(nack.Header.Version == 6, "minefield nack version");
        Expect(nack.MinefieldId.Entity == 183, "minefield nack id");
        Expect(nack.RequestingEntityId.Entity == 186, "minefield nack requester");
        Expect(nack.RequestId == 187, "minefield nack request");
        Expect(nack.NumberOfMissingPdus == 2, "minefield nack missing");
        Expect(nack.MissingPduSequenceNumberBytes.Length == 16, "minefield nack bytes");
    }

    private static void AssertSyntheticEnvironment(FastDisScanner scanner)
    {
        if (!scanner.TryParseEnvironmentalProcess(CreateEnvironmentalProcessPdu(6), out FastDisEnvironmentalProcess process))
        {
            throw new InvalidOperationException("failed to parse DIS6 Environmental Process");
        }
        Expect(process.Header.Version == 6, "environmental process version");
        Expect(process.EnvironmentalProcessId.Entity == 213, "environmental process id");
        Expect(process.EnvironmentType.Country == 840, "environmental process type");
        Expect(process.ModelType == 15, "environmental process model");
        Expect(process.EnvironmentStatus == 16, "environmental process status");
        Expect(process.NumberOfEnvironmentRecords == 2, "environmental process records");
        Expect(process.SequenceNumber == 0x1718, "environmental process sequence");
        Expect(process.EnvironmentRecordBytes.Length == 10, "environmental process bytes");

        if (!scanner.TryParseGriddedData(CreateGriddedDataPdu(7), out FastDisGriddedData grid))
        {
            throw new InvalidOperationException("failed to parse DIS7 Gridded Data");
        }
        Expect(grid.Header.Version == 7, "gridded data version");
        Expect(grid.EnvironmentalSimulationApplicationId.Entity == 263, "gridded data id");
        Expect(grid.FieldNumber == 264, "gridded data field");
        Expect(grid.CoordinateSystem == 267, "gridded data coord");
        Expect(grid.NumberOfGridAxes == 3, "gridded data axes");
        Expect(grid.ConstantGrid == 1, "gridded data constant");
        Expect(grid.EnvironmentType.Country == 840, "gridded data type");
        Expect(Math.Abs(grid.Orientation.Theta - 0.8f) < 0.0001f, "gridded data orientation");
        Expect(grid.SampleTime == 0x0102030405060708ul, "gridded data sample");
        Expect(grid.TotalValues == 269u, "gridded data total values");
        Expect(grid.VectorDimension == 4, "gridded data vector dim");
        Expect(grid.Padding1 == 270, "gridded data padding1");
        Expect(grid.GridDataBytes.Length == 10, "gridded data bytes");

        if (!scanner.TryParsePointObjectState(CreatePointObjectStatePdu(6), out FastDisPointObjectState point6))
        {
            throw new InvalidOperationException("failed to parse DIS6 Point Object State");
        }
        Expect(point6.ObjectId.Entity == 53, "point object state6 id");
        Expect(point6.ObjectType.Domain == 2, "point object state6 domain");
        Expect(point6.ObjectType.Kind == 1, "point object state6 kind");
        Expect(point6.ObjectType.Country == 840, "point object state6 country");
        Expect(Math.Abs(point6.ObjectAppearance - 1234.5) < 0.0001, "point object state6 appearance");

        if (!scanner.TryParsePointObjectState(CreatePointObjectStatePdu(7), out FastDisPointObjectState point7))
        {
            throw new InvalidOperationException("failed to parse DIS7 Point Object State");
        }
        Expect(point7.ObjectId.Entity == 73, "point object state7 id");
        Expect(point7.ObjectType.Domain == 4, "point object state7 domain");
        Expect(point7.ObjectType.Kind == 5, "point object state7 kind");
        Expect(point7.ObjectType.Country == 0, "point object state7 country");

        if (!scanner.TryParseLinearObjectState(CreateLinearObjectStatePdu(6), out FastDisLinearObjectState linear6))
        {
            throw new InvalidOperationException("failed to parse DIS6 Linear Object State");
        }
        Expect(linear6.ObjectId.Entity == 133, "linear object state6 id");
        Expect(linear6.NumberOfSegments == 2, "linear object state6 segments");
        Expect(linear6.ObjectType.Domain == 10, "linear object state6 domain");
        Expect(linear6.ObjectType.Kind == 9, "linear object state6 kind");
        Expect(linear6.LinearSegmentParameterBytes.Length == 110, "linear object state6 bytes");

        if (!scanner.TryParseLinearObjectState(CreateLinearObjectStatePdu(7), out FastDisLinearObjectState linear7))
        {
            throw new InvalidOperationException("failed to parse DIS7 Linear Object State");
        }
        Expect(linear7.ObjectId.Entity == 153, "linear object state7 id");
        Expect(linear7.ObjectType.Domain == 13, "linear object state7 domain");
        Expect(linear7.ObjectType.Kind == 14, "linear object state7 kind");
        Expect(linear7.LinearSegmentParameterBytes.Length == 128, "linear object state7 bytes");

        if (!scanner.TryParseArealObjectState(CreateArealObjectStatePdu(6), out FastDisArealObjectState areal6))
        {
            throw new InvalidOperationException("failed to parse DIS6 Areal Object State");
        }
        Expect(areal6.ObjectId.Entity == 93, "areal object state6 id");
        Expect(areal6.ObjectType.Country == 225, "areal object state6 country");
        Expect(areal6.ObjectAppearanceBytes.Length == 6, "areal object state6 appearance bytes");
        Expect(areal6.NumberOfPoints == 2, "areal object state6 points");
        Expect(areal6.ObjectLocationBytes.Length == 48, "areal object state6 location bytes");

        if (!scanner.TryParseArealObjectState(CreateArealObjectStatePdu(7), out FastDisArealObjectState areal7))
        {
            throw new InvalidOperationException("failed to parse DIS7 Areal Object State");
        }
        Expect(areal7.ObjectId.Entity == 113, "areal object state7 id");
        Expect(areal7.ObjectType.Country == 124, "areal object state7 country");
        Expect(areal7.ObjectAppearanceBytes.Length == 6, "areal object state7 appearance bytes");
        Expect(areal7.NumberOfPoints == 2, "areal object state7 points");
        Expect(areal7.ObjectLocationBytes.Length == 48, "areal object state7 location bytes");
    }

    private static void AssertReliableSimulationManagement(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseAcknowledge(CreateAcknowledgePdu(version), out FastDisAcknowledge acknowledge))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Acknowledge");
        }
        Expect(acknowledge.Header.PduType == 15, "ack pdu type");
        Expect(acknowledge.Header.ProtocolFamily == 5, "ack family");
        Expect(acknowledge.AcknowledgeFlag == 0x1234, "ack flag");
        Expect(acknowledge.ResponseFlag == 0x5678, "ack response");
        Expect(acknowledge.RequestId == 0xCAFEBABEu, "ack request");

        if (!scanner.TryParseCreateEntityReliable(CreateCreateEntityReliablePdu(version), out FastDisSimulationManagementReliableRequest createReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Create Entity-R");
        }
        Expect(createReliable.Header.PduType == 51, "create-r pdu type");
        Expect(createReliable.Header.ProtocolFamily == 10, "create-r family");
        Expect(createReliable.RequiredReliabilityService == 7, "create-r reliability");
        Expect(createReliable.Pad1 == 0x1357, "create-r pad1");
        Expect(createReliable.Pad2 == 9, "create-r pad2");
        Expect(createReliable.RequestId == 0xA0B0C0D0u, "create-r request");

        if (!scanner.TryParseRemoveEntityReliable(CreateRemoveEntityReliablePdu(version), out FastDisSimulationManagementReliableRequest removeReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Remove Entity-R");
        }
        Expect(removeReliable.Header.PduType == 52, "remove-r pdu type");
        Expect(removeReliable.RequiredReliabilityService == 8, "remove-r reliability");
        Expect(removeReliable.Pad1 == 0x2468, "remove-r pad1");
        Expect(removeReliable.Pad2 == 10, "remove-r pad2");
        Expect(removeReliable.RequestId == 0x0BADF00Du, "remove-r request");

        if (!scanner.TryParseStartResumeReliable(CreateStartResumeReliablePdu(version), out FastDisStartResumeReliable startReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Start/Resume-R");
        }
        Expect(startReliable.Header.PduType == 53, "start-r pdu type");
        Expect(startReliable.RealWorldTime.Hour == 7u, "start-r real hour");
        Expect(startReliable.SimulationTime.TimePastHour == 654321u, "start-r sim past");
        Expect(startReliable.RequiredReliabilityService == 11, "start-r reliability");
        Expect(startReliable.Pad1 == 0xAAAA, "start-r pad1");
        Expect(startReliable.Pad2 == 12, "start-r pad2");
        Expect(startReliable.RequestId == 0x01020304u, "start-r request");

        if (!scanner.TryParseStopFreezeReliable(CreateStopFreezeReliablePdu(version), out FastDisStopFreezeReliable stopReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Stop/Freeze-R");
        }
        Expect(stopReliable.Header.PduType == 54, "stop-r pdu type");
        Expect(stopReliable.Reason == 3, "stop-r reason");
        Expect(stopReliable.FrozenBehavior == 4, "stop-r frozen");
        Expect(stopReliable.RequiredReliablityService == 13, "stop-r reliability");
        Expect(stopReliable.Pad1 == 14, "stop-r pad1");
        Expect(stopReliable.RequestId == 0x0F1E2D3Cu, "stop-r request");

        if (!scanner.TryParseAcknowledgeReliable(CreateAcknowledgeReliablePdu(version), out FastDisAcknowledge acknowledgeReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Acknowledge-R");
        }
        Expect(acknowledgeReliable.Header.PduType == 55, "ack-r pdu type");
        Expect(acknowledgeReliable.Header.ProtocolFamily == 10, "ack-r family");
        Expect(acknowledgeReliable.AcknowledgeFlag == 0x9ABC, "ack-r flag");
        Expect(acknowledgeReliable.ResponseFlag == 0xDEF0, "ack-r response");
        Expect(acknowledgeReliable.RequestId == 0xFACECAFEu, "ack-r request");

        if (!scanner.TryParseRecordReliable(CreateRecordReliablePdu(version), out FastDisRecordReliable recordReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Record-R");
        }
        Expect(recordReliable.Header.PduType == 63, "record-r pdu type");
        Expect(recordReliable.RequestId == 0x51525354u, "record-r request");
        Expect(recordReliable.RequiredReliabilityService == 7, "record-r reliability");
        Expect(recordReliable.Pad1 == 8, "record-r pad1");
        Expect(recordReliable.EventType == 0x090A, "record-r event");
        Expect(recordReliable.RecordSetCount == 2u, "record-r count");
        Expect(recordReliable.RecordSetBytes.Length == 8 && recordReliable.RecordSetBytes[0] == 0x10, "record-r bytes");

        if (!scanner.TryParseSetRecordReliable(CreateSetRecordReliablePdu(version), out FastDisSetRecordReliable setRecordReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} SetRecord-R");
        }
        Expect(setRecordReliable.Header.PduType == 64, "set-record-r pdu type");
        Expect(setRecordReliable.RequestId == 0x61626364u, "set-record-r request");
        Expect(setRecordReliable.RequiredReliabilityService == 9, "set-record-r reliability");
        Expect(setRecordReliable.Pad1 == 0x0B0C, "set-record-r pad1");
        Expect(setRecordReliable.Pad2 == 13, "set-record-r pad2");
        Expect(setRecordReliable.RecordSetCount == 3u, "set-record-r count");
        Expect(setRecordReliable.RecordSetBytes.Length == 8 && setRecordReliable.RecordSetBytes[0] == 0x21, "set-record-r bytes");

        if (!scanner.TryParseRecordQueryReliable(CreateRecordQueryReliablePdu(version), out FastDisRecordQueryReliable recordQueryReliable))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} RecordQuery-R");
        }
        Expect(recordQueryReliable.Header.PduType == 65, "record-query-r pdu type");
        Expect(recordQueryReliable.RequestId == 0x71727374u, "record-query-r request");
        Expect(recordQueryReliable.RequiredReliabilityService == 14, "record-query-r reliability");
        Expect(recordQueryReliable.Pad1 == 0x1516, "record-query-r pad1");
        Expect(recordQueryReliable.Pad2 == 17, "record-query-r pad2");
        Expect(recordQueryReliable.EventType == 0x1819, "record-query-r event");
        Expect(recordQueryReliable.Time == 0x1A1B1C1Du, "record-query-r time");
        Expect(recordQueryReliable.RecordIdCount == 2u, "record-query-r count");
        Expect(recordQueryReliable.RecordIdBytes.Length == 8 && recordQueryReliable.RecordIdBytes[0] == 0x31, "record-query-r bytes");
    }

    private static void AssertLogistics(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseServiceRequest(CreateServiceRequestPdu(version), out FastDisServiceRequest serviceRequest))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Service Request");
        }
        Expect(serviceRequest.Header.PduType == 5, "service-request pdu type");
        Expect(serviceRequest.Header.ProtocolFamily == 3, "service-request family");
        Expect(serviceRequest.ServiceTypeRequested == 7, "service-request type");
        Expect(serviceRequest.NumberOfSupplyTypes == 2, "service-request count");
        Expect(serviceRequest.SupplyBytes.Length == 8 && serviceRequest.SupplyBytes[0] == 0x41, "service-request bytes");

        if (!scanner.TryParseResupplyOffer(CreateResupplyOfferPdu(version), out FastDisResupplyOffer resupplyOffer))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Resupply Offer");
        }
        Expect(resupplyOffer.Header.PduType == 6, "resupply-offer pdu type");
        Expect(resupplyOffer.NumberOfSupplyTypes == 2, "resupply-offer count");
        Expect(resupplyOffer.PaddingBytes.Length == 3, "resupply-offer padding size");
        Expect(resupplyOffer.SupplyBytes.Length == 8 && resupplyOffer.SupplyBytes[0] == 0x51, "resupply-offer bytes");

        if (!scanner.TryParseResupplyReceived(CreateResupplyReceivedPdu(version), out FastDisResupplyReceived resupplyReceived))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Resupply Received");
        }
        Expect(resupplyReceived.Header.PduType == 7, "resupply-received pdu type");
        Expect(resupplyReceived.NumberOfSupplyTypes == 2, "resupply-received count");
        Expect(resupplyReceived.Padding1 == 0x6162, "resupply-received pad1");
        Expect(resupplyReceived.Padding2 == 0x63, "resupply-received pad2");
        Expect(resupplyReceived.SupplyBytes.Length == 8 && resupplyReceived.SupplyBytes[0] == 0x61, "resupply-received bytes");

        if (!scanner.TryParseResupplyCancel(CreateResupplyCancelPdu(version), out FastDisResupplyCancel resupplyCancel))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Resupply Cancel");
        }
        Expect(resupplyCancel.Header.PduType == 8, "resupply-cancel pdu type");
        Expect(resupplyCancel.ReceivingEntityId.Entity == 0x0003, "resupply-cancel recv");
        Expect(resupplyCancel.SupplyingEntityId.Entity == 0x0006, "resupply-cancel supply");

        if (!scanner.TryParseRepairComplete(CreateRepairCompletePdu(version), out FastDisRepairComplete repairComplete))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Repair Complete");
        }
        Expect(repairComplete.Header.PduType == 9, "repair-complete pdu type");
        Expect(repairComplete.Repair == 0x7172, "repair-complete repair");
        Expect(repairComplete.Padding2 == 0x7374, "repair-complete padding");

        if (!scanner.TryParseRepairResponse(CreateRepairResponsePdu(version), out FastDisRepairResponse repairResponse))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Repair Response");
        }
        Expect(repairResponse.Header.PduType == 10, "repair-response pdu type");
        Expect(repairResponse.RepairResult == 0x75, "repair-response result");
        Expect(repairResponse.Padding1 == 0x7677, "repair-response pad1");
        Expect(repairResponse.Padding2 == 0x78, "repair-response pad2");
    }

    private static void AssertRadioAndDesignator(FastDisScanner scanner, byte version)
    {
        if (!scanner.TryParseDesignator(CreateDesignatorPdu(version), out FastDisDesignator designator))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Designator");
        }
        Expect(designator.Header.PduType == 24, "designator pdu type");
        Expect(designator.Header.ProtocolFamily == 6, "designator family");
        Expect(designator.DesignatingEntityId.Entity == 0x0003, "designator source");
        Expect(designator.DesignatedEntityId.Entity == 0x0006, "designator target");
        Expect(designator.CodeName == 0x1234, "designator code name");
        Expect(designator.DesignatorCode == 0x2345, "designator code");
        Expect(Math.Abs(designator.DesignatorPower - 12.5f) < 0.0001f, "designator power");

        if (!scanner.TryParseSignal(CreateSignalPdu(version), out FastDisSignal signal))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Signal");
        }
        Expect(signal.Header.PduType == 26, "signal pdu type");
        Expect(signal.Header.ProtocolFamily == 4, "signal family");
        Expect(signal.EncodingScheme == 0x2222, "signal encoding");
        Expect(signal.TdlType == 0x3333, "signal tdl");
        Expect(signal.SampleRate == 48000u, "signal sample rate");
        Expect(signal.DataBytes.Length == 4 && signal.DataBytes[0] == 0x41, "signal bytes");

        if (!scanner.TryParseReceiver(CreateReceiverPdu(version), out FastDisReceiver receiver))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Receiver");
        }
        Expect(receiver.Header.PduType == 27, "receiver pdu type");
        Expect(receiver.Header.ProtocolFamily == 4, "receiver family");
        Expect(receiver.ReceiverState == 0x2222, "receiver state");
        Expect(receiver.Padding1 == 0x3333, "receiver padding");
        Expect(Math.Abs(receiver.ReceivedPower - 12.5f) < 0.0001f, "receiver power");
        Expect(receiver.TransmitterEntityId.Entity == 0x0006, "receiver transmitter entity");
        Expect(receiver.TransmitterRadioId == 0x4444, "receiver transmitter radio");

        if (!scanner.TryParseTransmitter(CreateTransmitterPdu(version), out FastDisTransmitter transmitter))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Transmitter");
        }
        Expect(transmitter.Header.PduType == 25, "transmitter pdu type");
        Expect(transmitter.EntityId.Entity == 0x0003, "transmitter entity");
        Expect(transmitter.RadioId == 0x1212, "transmitter radio");
        Expect(transmitter.Frequency == 225000u, "transmitter frequency");
        Expect(Math.Abs(transmitter.TransmitFrequencyBandwidth - 50.5f) < 0.0001f, "transmitter bandwidth");
        Expect(transmitter.ModulationType.System == 4, "transmitter modulation system");
        Expect(transmitter.ModulationParameterBytes.Length >= (version >= 7 ? 12 : 3), "transmitter modulation bytes");
        if (version >= 7)
        {
            Expect(transmitter.EntityType.Country == 840, "transmitter entity type country");
            Expect(transmitter.AntennaPatternBytes.Length == 12, "transmitter antenna bytes");
        }
        else
        {
            Expect(transmitter.RadioEntityType.Nomenclature == 0x0708, "transmitter radio nomenclature");
        }

        if (!scanner.TryParseIffAtcNavAidsLayer1(CreateIffAtcNavAidsLayer1Pdu(version), out FastDisIffAtcNavAidsLayer1 iff))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} IFF/ATC/NAVAIDS Layer 1");
        }
        Expect(iff.Header.PduType == 28, "iff pdu type");
        Expect(iff.Header.ProtocolFamily == 6, "iff family");
        Expect(iff.EmittingEntityId.Entity == 0x0003, "iff entity");
        Expect(iff.EventId.EventNumber == 0x0006, "iff event");
        Expect(Math.Abs(iff.Location.Y - 2.0f) < 0.0001f, "iff location");
        Expect(iff.SystemId.SystemName == 0x2222, "iff system name");
        Expect(iff.FundamentalParameters.Parameter6 == 10, "iff parameter6");

        if (!scanner.TryParseIntercomSignal(CreateIntercomSignalPdu(version), out FastDisIntercomSignal intercom))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Intercom Signal");
        }
        Expect(intercom.Header.PduType == 31, "intercom pdu type");
        Expect(intercom.Header.ProtocolFamily == 4, "intercom family");
        Expect(intercom.EntityId.Entity == 0x0003, "intercom entity");
        Expect(intercom.CommunicationsDeviceId == 0x1212, "intercom device");
        Expect(intercom.EncodingScheme == 0x2222, "intercom encoding");
        Expect(intercom.TdlType == 0x3333, "intercom tdl");
        Expect(intercom.SampleRate == 32000u, "intercom sample rate");
        Expect(intercom.DataBytes.Length == 4 && intercom.DataBytes[0] == 0x51, "intercom bytes");

        if (!scanner.TryParseIntercomControl(CreateIntercomControlPdu(version), out FastDisIntercomControl intercomControl))
        {
            throw new InvalidOperationException($"failed to parse DIS{version} Intercom Control");
        }
        Expect(intercomControl.Header.PduType == 32, "intercom-control pdu type");
        Expect(intercomControl.ControlType == 0x11, "intercom-control control type");
        Expect(intercomControl.SourceEntityId.Entity == 0x0003, "intercom-control source");
        Expect(intercomControl.Command == 0x77, "intercom-control command");
        Expect(intercomControl.MasterCommunicationsDeviceId == 0x8888, "intercom-control master device");
        Expect(intercomControl.IntercomParametersBytes.Length == 4 && intercomControl.IntercomParametersBytes[0] == 0x61, "intercom-control bytes");
    }

    private static void AssertLateDis7FixedPrefix(FastDisScanner scanner)
    {
        if (!scanner.TryParseAttribute(CreateAttributePdu(7), out FastDisAttribute attribute))
        {
            throw new InvalidOperationException("failed to parse DIS7 Attribute");
        }
        Expect(attribute.Header.PduType == 72, "attribute pdu type");
        Expect(attribute.Header.ProtocolFamily == 1, "attribute family");
        Expect(attribute.OriginatingSimulationAddress.Site == 0x0101, "attribute site");
        Expect(attribute.OriginatingSimulationAddress.Application == 0x0202, "attribute application");
        Expect(attribute.Padding1 == 0x11223344, "attribute padding1");
        Expect(attribute.Padding2 == 0x5566, "attribute padding2");
        Expect(attribute.AttributeRecordPduType == 67, "attribute record pdu type");
        Expect(attribute.AttributeRecordProtocolVersion == 7, "attribute record version");
        Expect(attribute.MasterAttributeRecordType == 0x778899AAu, "attribute master record type");
        Expect(attribute.ActionCode == 0x12, "attribute action code");
        Expect(attribute.Padding3 == 0x34, "attribute padding3");
        Expect(attribute.NumberAttributeRecordSet == 1, "attribute record set count");
        Expect(attribute.AttributeRecordSetBytes.Length == 4 && attribute.AttributeRecordSetBytes[0] == 0x61, "attribute bytes");

        if (!scanner.TryParseDirectedEnergyFire(CreateDirectedEnergyFirePdu(7), out FastDisDirectedEnergyFire directedEnergyFire))
        {
            throw new InvalidOperationException("failed to parse DIS7 Directed Energy Fire");
        }
        Expect(directedEnergyFire.Header.PduType == 68, "def pdu type");
        Expect(directedEnergyFire.Header.ProtocolFamily == 2, "def family");
        Expect(directedEnergyFire.FiringEntityId.Entity == 0x0003, "def firing entity");
        Expect(directedEnergyFire.TargetEntityId.Entity == 0x0006, "def target entity");
        Expect(directedEnergyFire.MunitionType.Country == 225, "def munition type country");
        Expect(directedEnergyFire.ShotStartTime.Hour == 7u, "def shot hour");
        Expect(directedEnergyFire.ShotStartTime.TimePastHour == 123456u, "def shot time");
        Expect(Math.Abs(directedEnergyFire.CommulativeShotTime - 1.25f) < 0.0001f, "def shot duration");
        Expect(Math.Abs(directedEnergyFire.ApertureEmitterLocation.Z - 4.5f) < 0.0001f, "def aperture location");
        Expect(Math.Abs(directedEnergyFire.ApertureDiameter - 5.5f) < 0.0001f, "def aperture diameter");
        Expect(Math.Abs(directedEnergyFire.Wavelength - 6.5f) < 0.0001f, "def wavelength");
        Expect(Math.Abs(directedEnergyFire.PeakIrradiance - 7.5f) < 0.0001f, "def peak irradiance");
        Expect(Math.Abs(directedEnergyFire.PulseRepetitionFrequency - 8.5f) < 0.0001f, "def pulse repetition");
        Expect(directedEnergyFire.PulseWidth == 9012, "def pulse width");
        Expect(directedEnergyFire.Flags == 0x10203040, "def flags");
        Expect(directedEnergyFire.PulseShape == 0x11, "def pulse shape");
        Expect(directedEnergyFire.Padding1 == 0x22, "def padding1");
        Expect(directedEnergyFire.Padding2 == 0x33445566u, "def padding2");
        Expect(directedEnergyFire.Padding3 == 0x7788, "def padding3");
        Expect(directedEnergyFire.NumberOfDeRecords == 1, "def de count");
        Expect(directedEnergyFire.DeRecordBytes.Length == 4 && directedEnergyFire.DeRecordBytes[0] == 0x90, "def bytes");

        if (!scanner.TryParseEntityDamageStatus(CreateEntityDamageStatusPdu(7), out FastDisEntityDamageStatus entityDamageStatus))
        {
            throw new InvalidOperationException("failed to parse DIS7 Entity Damage Status");
        }
        Expect(entityDamageStatus.Header.PduType == 69, "eds pdu type");
        Expect(entityDamageStatus.Header.ProtocolFamily == 2, "eds family");
        Expect(entityDamageStatus.FiringEntityId.Entity == 0x0003, "eds firing entity");
        Expect(entityDamageStatus.TargetEntityId.Entity == 0x0006, "eds target entity");
        Expect(entityDamageStatus.DamagedEntityId.Entity == 0x0009, "eds damaged entity");
        Expect(entityDamageStatus.Padding1 == 0x1112, "eds padding1");
        Expect(entityDamageStatus.Padding2 == 0x1314, "eds padding2");
        Expect(entityDamageStatus.NumberOfDamageDescription == 1, "eds description count");
        Expect(entityDamageStatus.DamageDescriptionRecordBytes.Length == 4 && entityDamageStatus.DamageDescriptionRecordBytes[0] == 0xA1, "eds bytes");

        if (!scanner.TryParseIff(CreateIffPdu(7), out FastDisIff iff))
        {
            throw new InvalidOperationException("failed to parse DIS7 IFF");
        }
        Expect(iff.Header.PduType == 28, "iff7 pdu type");
        Expect(iff.Header.ProtocolFamily == 6, "iff7 family");
        Expect(iff.EmittingEntityId.Entity == 0x0003, "iff7 entity");
        Expect(iff.EventId.EventNumber == 0x0006, "iff7 event");
        Expect(Math.Abs(iff.Location.Y - 2.0f) < 0.0001f, "iff7 location");
        Expect(iff.SystemId.SystemName == 0x2222, "iff7 system");
        Expect(iff.Padding2 == 0x5555, "iff7 padding2");
        Expect(iff.FundamentalParameters.Parameter6 == 10, "iff7 parameter6");

        if (!scanner.TryParseElectronicEmissions(CreateElectronicEmissionsPdu(7), out FastDisElectronicEmissions electronicEmissions))
        {
            throw new InvalidOperationException("failed to parse DIS7 Electronic Emissions");
        }
        Expect(electronicEmissions.Header.PduType == 23, "ee7 pdu type");
        Expect(electronicEmissions.Header.ProtocolFamily == 6, "ee7 family");
        Expect(electronicEmissions.EmittingEntityId.Entity == 0x0003, "ee7 entity");
        Expect(electronicEmissions.EventId.EventNumber == 0x0006, "ee7 event");
        Expect(electronicEmissions.StateUpdateIndicator == 0x07, "ee7 state update");
        Expect(electronicEmissions.NumberOfSystems == 0x02, "ee7 system count");
        Expect(electronicEmissions.Padding1 == 0x0809, "ee7 padding1");
        Expect(electronicEmissions.SystemRecordBytes.Length == 6 && electronicEmissions.SystemRecordBytes[0] == 0xE1, "ee7 bytes");

        if (!scanner.TryParseUa(CreateUaPdu(7), out FastDisUa ua))
        {
            throw new InvalidOperationException("failed to parse DIS7 Ua");
        }
        Expect(ua.Header.PduType == 29, "ua7 pdu type");
        Expect(ua.Header.ProtocolFamily == 6, "ua7 family");
        Expect(ua.EmittingEntityId.Entity == 0x0003, "ua7 entity");
        Expect(ua.EventId.EventNumber == 0x0006, "ua7 event");
        Expect(ua.StateChangeIndicator == 0x0A, "ua7 state change");
        Expect(ua.Padding1 == 0x0B, "ua7 padding1");
        Expect(ua.PassiveParameterIndex == 0x0C0D, "ua7 passive parameter");
        Expect(ua.PropulsionPlantConfiguration == 0x0E, "ua7 propulsion");
        Expect(ua.NumberOfShafts == 1, "ua7 shafts");
        Expect(ua.NumberOfApas == 2, "ua7 apas");
        Expect(ua.NumberOfUaEmitterSystems == 3, "ua7 emitters");
        Expect(ua.UaRecordBytes.Length == 8 && ua.UaRecordBytes[0] == 0xF1, "ua7 bytes");

        if (!scanner.TryParseSees(CreateSeesPdu(7), out FastDisSees sees))
        {
            throw new InvalidOperationException("failed to parse DIS7 Sees");
        }
        Expect(sees.Header.PduType == 30, "sees7 pdu type");
        Expect(sees.Header.ProtocolFamily == 6, "sees7 family");
        Expect(sees.OriginatingEntityId.Entity == 0x0033, "sees7 entity");
        Expect(sees.InfraredSignatureRepresentationIndex == 0x1112, "sees7 ir index");
        Expect(sees.AcousticSignatureRepresentationIndex == 0x1314, "sees7 acoustic index");
        Expect(sees.RadarCrossSectionSignatureRepresentationIndex == 0x1516, "sees7 radar index");
        Expect(sees.NumberOfPropulsionSystems == 2, "sees7 propulsion count");
        Expect(sees.NumberOfVectoringNozzleSystems == 3, "sees7 nozzle count");
        Expect(sees.SupplementalEmissionRecordBytes.Length == 8 && sees.SupplementalEmissionRecordBytes[0] == 0xAA, "sees7 bytes");

        if (!scanner.TryParseInformationOperationsAction(CreateInformationOperationsActionPdu(7), out FastDisInformationOperationsAction ioAction))
        {
            throw new InvalidOperationException("failed to parse DIS7 Information Operations Action");
        }
        Expect(ioAction.Header.PduType == 70, "ioa pdu type");
        Expect(ioAction.Header.ProtocolFamily == 13, "ioa family");
        Expect(ioAction.OriginatingSimId.Entity == 0x0003, "ioa origin");
        Expect(ioAction.ReceivingSimId.Entity == 0x0006, "ioa receive");
        Expect(ioAction.RequestId == 0x11223344u, "ioa request");
        Expect(ioAction.IoWarfareType == 0x0102, "ioa warfare");
        Expect(ioAction.IoSimulationSource == 0x0304, "ioa sim source");
        Expect(ioAction.IoActionType == 0x0506, "ioa action type");
        Expect(ioAction.IoActionPhase == 0x0708, "ioa action phase");
        Expect(ioAction.Padding1 == 0x55667788u, "ioa padding1");
        Expect(ioAction.IoAttackerId.Entity == 0x0009, "ioa attacker");
        Expect(ioAction.IoPrimaryTargetId.Entity == 0x000C, "ioa target");
        Expect(ioAction.Padding2 == 0x090A, "ioa padding2");
        Expect(ioAction.NumberOfIoRecords == 1, "ioa record count");
        Expect(ioAction.IoRecordBytes.Length == 4 && ioAction.IoRecordBytes[0] == 0xC1, "ioa bytes");

        if (!scanner.TryParseInformationOperationsReport(CreateInformationOperationsReportPdu(7), out FastDisInformationOperationsReport ioReport))
        {
            throw new InvalidOperationException("failed to parse DIS7 Information Operations Report");
        }
        Expect(ioReport.Header.PduType == 71, "ior pdu type");
        Expect(ioReport.Header.ProtocolFamily == 13, "ior family");
        Expect(ioReport.OriginatingSimId.Entity == 0x0003, "ior origin");
        Expect(ioReport.IoSimSource == 0x0102, "ior sim source");
        Expect(ioReport.IoReportType == 0x03, "ior report type");
        Expect(ioReport.Padding1 == 0x04, "ior padding1");
        Expect(ioReport.IoAttackerId.Entity == 0x0006, "ior attacker");
        Expect(ioReport.IoPrimaryTargetId.Entity == 0x0009, "ior target");
        Expect(ioReport.Padding2 == 0x1112, "ior padding2");
        Expect(ioReport.Padding3 == 0x1314, "ior padding3");
        Expect(ioReport.NumberOfIoRecords == 1, "ior record count");
        Expect(ioReport.IoRecordBytes.Length == 4 && ioReport.IoRecordBytes[0] == 0xD1, "ior bytes");
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

    private static byte[] CreateFirePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 2, 96);
        packet[3] = 2;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001);
        WriteU16(packet, body + 2, 0x0002);
        WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004);
        WriteU16(packet, body + 8, 0x0005);
        WriteU16(packet, body + 10, 0x0006);
        WriteU16(packet, body + 12, 0x0007);
        WriteU16(packet, body + 14, 0x0008);
        WriteU16(packet, body + 16, 0x0009);
        WriteU16(packet, body + 18, 0x000A);
        WriteU16(packet, body + 20, 0x000B);
        WriteU16(packet, body + 22, 0x000C);
        WriteU32(packet, body + 24, 99u);
        WriteWorld(packet, body + 28, 1000.5, 2000.25, 3000.75);
        packet[body + 52] = 2;
        packet[body + 53] = 1;
        WriteU16(packet, body + 54, 225);
        packet[body + 56] = 4;
        packet[body + 57] = 5;
        packet[body + 58] = 6;
        packet[body + 59] = 7;
        WriteU16(packet, body + 60, 101);
        WriteU16(packet, body + 62, 202);
        WriteU16(packet, body + 64, 3);
        WriteU16(packet, body + 66, 600);
        WriteVec3(packet, body + 68, 1.5f, 2.5f, 3.5f);
        WriteFloat(packet, body + 80, 4444.5f);
        return packet;
    }

    private static byte[] CreateDetonationPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 3, 108);
        packet[3] = 2;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001);
        WriteU16(packet, body + 2, 0x0002);
        WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004);
        WriteU16(packet, body + 8, 0x0005);
        WriteU16(packet, body + 10, 0x0006);
        WriteU16(packet, body + 12, 0x0007);
        WriteU16(packet, body + 14, 0x0008);
        WriteU16(packet, body + 16, 0x0009);
        WriteU16(packet, body + 18, 0x000A);
        WriteU16(packet, body + 20, 0x000B);
        WriteU16(packet, body + 22, 0x000C);
        WriteVec3(packet, body + 24, 11.0f, 22.0f, 33.0f);
        WriteWorld(packet, body + 36, 111.5, 222.25, 333.75);
        packet[body + 60] = 2;
        packet[body + 61] = 1;
        WriteU16(packet, body + 62, 225);
        packet[body + 64] = 4;
        packet[body + 65] = 5;
        packet[body + 66] = 6;
        packet[body + 67] = 7;
        WriteU16(packet, body + 68, 101);
        WriteU16(packet, body + 70, 202);
        WriteU16(packet, body + 72, 3);
        WriteU16(packet, body + 74, 600);
        WriteVec3(packet, body + 76, -4.0f, -5.0f, -6.0f);
        packet[body + 88] = 17;
        packet[body + 89] = 1;
        WriteU16(packet, body + 90, 0);
        for (int i = 0; i < 16; i++)
        {
            packet[body + 92 + i] = (byte)(i + 1);
        }
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

    private static byte[] CreateAcknowledgePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 15, 30);
        packet[3] = 5;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU16(packet, body + 12, 0x1234);
        WriteU16(packet, body + 14, 0x5678);
        WriteU32(packet, body + 16, 0xCAFEBABEu);
        return packet;
    }

    private static byte[] CreateCreateEntityReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 51, 32);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        packet[body + 12] = 7;
        WriteU16(packet, body + 13, 0x1357);
        packet[body + 15] = 9;
        WriteU32(packet, body + 16, 0xA0B0C0D0u);
        return packet;
    }

    private static byte[] CreateRemoveEntityReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 52, 32);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        packet[body + 12] = 8;
        WriteU16(packet, body + 13, 0x2468);
        packet[body + 15] = 10;
        WriteU32(packet, body + 16, 0x0BADF00Du);
        return packet;
    }

    private static byte[] CreateStartResumeReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 53, 48);
        packet[3] = 10;
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
        packet[body + 28] = 11;
        WriteU16(packet, body + 29, 0xAAAA);
        packet[body + 31] = 12;
        WriteU32(packet, body + 32, 0x01020304u);
        return packet;
    }

    private static byte[] CreateStopFreezeReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 54, 36);
        packet[3] = 10;
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
        packet[body + 22] = 13;
        packet[body + 23] = 14;
        WriteU32(packet, body + 24, 0x0F1E2D3Cu);
        return packet;
    }

    private static byte[] CreateAcknowledgeReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 55, 30);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x1111);
        WriteU16(packet, body + 2, 0x2222);
        WriteU16(packet, body + 4, 0x3333);
        WriteU16(packet, body + 6, 0x4444);
        WriteU16(packet, body + 8, 0x5555);
        WriteU16(packet, body + 10, 0x6666);
        WriteU16(packet, body + 12, 0x9ABC);
        WriteU16(packet, body + 14, 0xDEF0);
        WriteU32(packet, body + 16, 0xFACECAFEu);
        return packet;
    }

    private static byte[] CreateOtherPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 0, 16);
        packet[3] = 0;
        packet[12] = 0x4F;
        packet[13] = 0x54;
        packet[14] = 0x48;
        packet[15] = 0x52;
        return packet;
    }

    private static byte[] CreateAggregateStatePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 33, 138);
        packet[3] = 7;
        int body = 12;
        WriteU16(packet, body + 0, 1);
        WriteU16(packet, body + 2, 2);
        WriteU16(packet, body + 4, 3);
        packet[body + 6] = 4;
        packet[body + 7] = 5;
        packet[body + 8] = 1;
        packet[body + 9] = 2;
        WriteU16(packet, body + 10, 840);
        packet[body + 12] = 3;
        packet[body + 13] = 4;
        packet[body + 14] = 5;
        packet[body + 15] = 6;
        WriteU32(packet, body + 16, 0x11223344u);
        packet[body + 20] = 1;
        byte[] marking = Encoding.ASCII.GetBytes("AGGREGATE-ALPHA");
        Array.Copy(marking, 0, packet, body + 21, marking.Length);
        WriteVec3(packet, body + 52, 1.0f, 2.0f, 3.0f);
        WriteVec3(packet, body + 64, 0.1f, 0.2f, 0.3f);
        WriteWorld(packet, body + 76, 10.0, 20.0, 30.0);
        WriteVec3(packet, body + 100, 4.0f, 5.0f, 6.0f);
        WriteU16(packet, body + 112, 7);
        WriteU16(packet, body + 114, 8);
        WriteU16(packet, body + 116, 9);
        WriteU16(packet, body + 118, 10);
        packet[132] = 0xA1;
        packet[133] = 0xA2;
        packet[134] = 0xA3;
        packet[135] = 0xA4;
        packet[136] = 0xA5;
        packet[137] = 0xA6;
        return packet;
    }

    private static byte[] CreateIsGroupOfPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 34, 44);
        packet[3] = 7;
        int body = 12;
        WriteU16(packet, body + 0, 1);
        WriteU16(packet, body + 2, 2);
        WriteU16(packet, body + 4, 3);
        packet[body + 6] = 0x21;
        packet[body + 7] = 0x02;
        WriteU32(packet, body + 8, 0x10203040u);
        WriteDouble(packet, body + 12, 41.25);
        WriteDouble(packet, body + 20, -93.5);
        packet[40] = 0xB1;
        packet[41] = 0xB2;
        packet[42] = 0xB3;
        packet[43] = 0xB4;
        return packet;
    }

    private static byte[] CreateTransferControlRequestPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 35, 41);
        packet[3] = 7;
        int body = 12;
        WriteU16(packet, body + 0, 1);
        WriteU16(packet, body + 2, 2);
        WriteU16(packet, body + 4, 3);
        WriteU16(packet, body + 6, 4);
        WriteU16(packet, body + 8, 5);
        WriteU16(packet, body + 10, 6);
        WriteU32(packet, body + 12, 0x11223344u);
        packet[body + 16] = 0x07;
        packet[body + 17] = 0x08;
        WriteU16(packet, body + 18, 7);
        WriteU16(packet, body + 20, 8);
        WriteU16(packet, body + 22, 9);
        packet[body + 24] = 0x02;
        packet[37] = 0xC1;
        packet[38] = 0xC2;
        packet[39] = 0xC3;
        packet[40] = 0xC4;
        return packet;
    }

    private static byte[] CreateTransferOwnershipPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 35, 41);
        packet[3] = 7;
        int body = 12;
        WriteU16(packet, body + 0, 10);
        WriteU16(packet, body + 2, 11);
        WriteU16(packet, body + 4, 12);
        WriteU16(packet, body + 6, 13);
        WriteU16(packet, body + 8, 14);
        WriteU16(packet, body + 10, 15);
        WriteU32(packet, body + 12, 0x55667788u);
        packet[body + 16] = 0x09;
        packet[body + 17] = 0x0A;
        WriteU16(packet, body + 18, 16);
        WriteU16(packet, body + 20, 17);
        WriteU16(packet, body + 22, 18);
        packet[body + 24] = 0x03;
        packet[37] = 0xD1;
        packet[38] = 0xD2;
        packet[39] = 0xD3;
        packet[40] = 0xD4;
        return packet;
    }

    private static byte[] CreateIsPartOfPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 36, 52);
        packet[3] = 7;
        int body = 12;
        WriteU16(packet, body + 0, 1);
        WriteU16(packet, body + 2, 2);
        WriteU16(packet, body + 4, 3);
        WriteU16(packet, body + 6, 4);
        WriteU16(packet, body + 8, 5);
        WriteU16(packet, body + 10, 6);
        WriteU16(packet, body + 12, 0x1112);
        WriteU16(packet, body + 14, 0x1314);
        WriteVec3(packet, body + 16, 7.0f, 8.0f, 9.0f);
        WriteU16(packet, body + 28, 0x2122);
        WriteU16(packet, body + 30, 0x2324);
        packet[body + 32] = 2;
        packet[body + 33] = 3;
        WriteU16(packet, body + 34, 225);
        packet[body + 36] = 4;
        packet[body + 37] = 5;
        packet[body + 38] = 6;
        packet[body + 39] = 7;
        return packet;
    }

    private static byte[] CreateMinefieldStatePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 37, 104);
        packet[3] = 8;
        int body = 12;
        if (version >= 7)
        {
            WriteEntityId(packet, body + 0, 231, 232, 233);
            WriteU16(packet, body + 6, 234);
            packet[body + 8] = 235;
            packet[body + 9] = 2;
            WriteEntityType(packet, body + 10, 19, 20, 225, 21, 22, 23, 24);
            WriteU16(packet, body + 18, 2);
            WriteWorld(packet, body + 20, 40.25, 50.5, 60.75);
            WriteVec3(packet, body + 44, 0.4f, 0.5f, 0.6f);
            WriteU16(packet, body + 56, 236);
            WriteU16(packet, body + 58, 237);
            WriteFloat(packet, body + 60, 5.5f);
            WriteFloat(packet, body + 64, 6.5f);
            WriteFloat(packet, body + 68, 7.5f);
            WriteFloat(packet, body + 72, 8.5f);
            WriteEntityType(packet, body + 76, 25, 26, 840, 27, 28, 29, 30);
            WriteEntityType(packet, body + 84, 31, 32, 124, 33, 34, 35, 36);
        }
        else
        {
            WriteEntityId(packet, body + 0, 221, 222, 223);
            WriteU16(packet, body + 6, 224);
            packet[body + 8] = 225;
            packet[body + 9] = 2;
            WriteEntityType(packet, body + 10, 1, 2, 840, 3, 4, 5, 6);
            WriteU16(packet, body + 18, 2);
            WriteWorld(packet, body + 20, 10.25, 20.5, 30.75);
            WriteVec3(packet, body + 44, 0.1f, 0.2f, 0.3f);
            WriteU16(packet, body + 56, 226);
            WriteU16(packet, body + 58, 227);
            WriteFloat(packet, body + 60, 1.5f);
            WriteFloat(packet, body + 64, 2.5f);
            WriteFloat(packet, body + 68, 3.5f);
            WriteFloat(packet, body + 72, 4.5f);
            WriteEntityType(packet, body + 76, 7, 8, 124, 9, 10, 11, 12);
            WriteEntityType(packet, body + 84, 13, 14, 225, 15, 16, 17, 18);
        }
        return packet;
    }

    private static byte[] CreateMinefieldQueryPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 38, 60);
        packet[3] = 8;
        int body = 12;
        WriteEntityId(packet, body + 0, 201, 202, 203);
        WriteEntityId(packet, body + 6, 204, 205, 206);
        packet[body + 12] = 207;
        packet[body + 13] = 2;
        packet[body + 14] = 0;
        packet[body + 15] = 2;
        WriteU32(packet, body + 16, 0x01020304u);
        WriteEntityType(packet, body + 20, 3, 4, 225, 5, 6, 7, 8);
        WriteFloat(packet, body + 28, 1.5f);
        WriteFloat(packet, body + 32, 2.5f);
        WriteFloat(packet, body + 36, 3.5f);
        WriteFloat(packet, body + 40, 4.5f);
        packet[body + 44] = 0x11;
        packet[body + 45] = 0x12;
        packet[body + 46] = 0x21;
        packet[body + 47] = 0x22;
        return packet;
    }

    private static byte[] CreateMinefieldDataPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 39, 73);
        packet[3] = 8;
        int body = 12;
        WriteEntityId(packet, body + 0, 251, 252, 253);
        WriteEntityId(packet, body + 6, 254, 255, 256);
        WriteU16(packet, body + 12, 257);
        packet[body + 14] = 200;
        packet[body + 15] = 3;
        packet[body + 16] = 2;
        packet[body + 17] = 2;
        packet[body + 18] = 2;
        packet[body + 19] = 0;
        WriteU32(packet, body + 20, 0x01020304u);
        WriteEntityType(packet, body + 24, 37, 38, 225, 39, 40, 41, 42);
        packet[body + 32] = 0x31;
        packet[body + 33] = 0x32;
        packet[body + 34] = 0x41;
        packet[body + 35] = 0x42;
        packet[body + 36] = 0;
        WriteVec3(packet, body + 37, 9.5f, 10.5f, 11.5f);
        WriteVec3(packet, body + 49, 12.5f, 13.5f, 14.5f);
        return packet;
    }

    private static byte[] CreateMinefieldResponseNackPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 40, 42);
        packet[3] = 8;
        int body = 12;
        WriteEntityId(packet, body + 0, 181, 182, 183);
        WriteEntityId(packet, body + 6, 184, 185, 186);
        packet[body + 12] = 187;
        packet[body + 13] = 2;
        for (int i = 0; i < 8; i++)
        {
            packet[body + 14 + i] = (byte)(i + 1);
            packet[body + 22 + i] = (byte)(0x11 + i);
        }
        return packet;
    }

    private static byte[] CreateEnvironmentalProcessPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 41, 41);
        packet[3] = 9;
        int body = 12;
        WriteEntityId(packet, body + 0, 211, 212, 213);
        WriteEntityType(packet, body + 6, 9, 10, 840, 11, 12, 13, 14);
        packet[body + 14] = 15;
        packet[body + 15] = 16;
        packet[body + 16] = 2;
        WriteU16(packet, body + 17, 0x1718);
        packet[body + 19] = 0x31; packet[body + 20] = 0x32; packet[body + 21] = 0x33; packet[body + 22] = 0x34; packet[body + 23] = 0x35;
        packet[body + 24] = 0x36; packet[body + 25] = 0x37; packet[body + 26] = 0x38; packet[body + 27] = 0x39; packet[body + 28] = 0x3A;
        return packet;
    }

    private static byte[] CreateGriddedDataPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 42, 74);
        packet[3] = 9;
        int body = 12;
        WriteEntityId(packet, body + 0, 261, 262, 263);
        WriteU16(packet, body + 6, 264); WriteU16(packet, body + 8, 265); WriteU16(packet, body + 10, 266); WriteU16(packet, body + 12, 267);
        packet[body + 14] = 3; packet[body + 15] = 1;
        WriteEntityType(packet, body + 16, 43, 44, 840, 45, 46, 47, 48);
        WriteVec3(packet, body + 24, 0.7f, 0.8f, 0.9f);
        WriteU64(packet, body + 36, 0x0102030405060708ul);
        WriteU32(packet, body + 44, 269u); packet[body + 48] = 4; WriteU16(packet, body + 49, 270); packet[body + 51] = 0;
        packet[body + 52] = 0x51; packet[body + 53] = 0x52; packet[body + 54] = 0x53; packet[body + 55] = 0x54; packet[body + 56] = 0x55;
        packet[body + 57] = 0x56; packet[body + 58] = 0x57; packet[body + 59] = 0x58; packet[body + 60] = 0x59; packet[body + 61] = 0x5A;
        return packet;
    }

    private static byte[] CreatePointObjectStatePdu(byte version)
    {
        if (version >= 7)
        {
            byte[] packet = CreatePdu(version, 43, 88);
            packet[3] = 9;
            int body = 12;
            WriteEntityId(packet, body + 0, 71, 72, 73); WriteEntityId(packet, body + 6, 74, 75, 76);
            WriteU16(packet, body + 12, 77); packet[body + 14] = 78; packet[body + 15] = 79;
            packet[body + 16] = 4; packet[body + 17] = 5; packet[body + 18] = 6; packet[body + 19] = 7;
            WriteWorld(packet, body + 20, 400.25, 500.5, 600.75); WriteVec3(packet, body + 44, 0.4f, 0.5f, 0.6f); WriteDouble(packet, body + 56, 2345.5);
            WriteU16(packet, body + 64, 80); WriteU16(packet, body + 66, 81); WriteU16(packet, body + 68, 82); WriteU16(packet, body + 70, 83); WriteU32(packet, body + 72, 84u);
            return packet;
        }

        byte[] packet6 = CreatePdu(version, 43, 90);
        packet6[3] = 9;
        int body6 = 12;
        WriteEntityId(packet6, body6 + 0, 51, 52, 53); WriteEntityId(packet6, body6 + 6, 54, 55, 56);
        WriteU16(packet6, body6 + 12, 57); packet6[body6 + 14] = 58; packet6[body6 + 15] = 59;
        packet6[body6 + 16] = 1; packet6[body6 + 17] = 2; WriteU16(packet6, body6 + 18, 840); packet6[body6 + 20] = 3; packet6[body6 + 21] = 4;
        WriteWorld(packet6, body6 + 22, 100.25, 200.5, 300.75); WriteVec3(packet6, body6 + 46, 0.1f, 0.2f, 0.3f); WriteDouble(packet6, body6 + 58, 1234.5);
        WriteU16(packet6, body6 + 66, 60); WriteU16(packet6, body6 + 68, 61); WriteU16(packet6, body6 + 70, 62); WriteU16(packet6, body6 + 72, 63); WriteU32(packet6, body6 + 74, 64u);
        return packet6;
    }

    private static byte[] CreateLinearObjectStatePdu(byte version)
    {
        if (version >= 7)
        {
            byte[] packet = CreatePdu(version, 44, 176);
            packet[3] = 9;
            int body = 12;
            WriteEntityId(packet, body + 0, 151, 152, 153); WriteEntityId(packet, body + 6, 154, 155, 156);
            WriteU16(packet, body + 12, 157); packet[body + 14] = 158; packet[body + 15] = 2;
            WriteU16(packet, body + 16, 159); WriteU16(packet, body + 18, 160); WriteU16(packet, body + 20, 161); WriteU16(packet, body + 22, 162);
            packet[body + 24] = 13; packet[body + 25] = 14; packet[body + 26] = 15; packet[body + 27] = 16;
            packet[body + 28] = 3; packet[body + 29] = 4; WriteU16(packet, body + 30, 0x0506); WriteU32(packet, body + 32, 0x0708090Au);
            WriteWorld(packet, body + 36, 3000.25, 3001.5, 3002.75); WriteVec3(packet, body + 60, 0.7f, 0.8f, 0.9f);
            WriteFloat(packet, body + 72, 45.5f); WriteFloat(packet, body + 76, 46.5f); WriteFloat(packet, body + 80, 47.5f); WriteFloat(packet, body + 84, 48.5f); WriteU32(packet, body + 88, 49u);
            packet[body + 92] = 5; packet[body + 93] = 6; WriteU16(packet, body + 94, 0x0B0C); WriteU32(packet, body + 96, 0x0D0E0F10u);
            WriteWorld(packet, body + 100, 4000.25, 4001.5, 4002.75); WriteVec3(packet, body + 124, 1.0f, 1.1f, 1.2f);
            WriteFloat(packet, body + 136, 55.5f); WriteFloat(packet, body + 140, 56.5f); WriteFloat(packet, body + 144, 57.5f); WriteFloat(packet, body + 148, 58.5f); WriteU32(packet, body + 152, 59u);
            return packet;
        }

        byte[] packet6 = CreatePdu(version, 44, 160);
        packet6[3] = 9;
        int body6 = 12;
        WriteEntityId(packet6, body6 + 0, 131, 132, 133); WriteEntityId(packet6, body6 + 6, 134, 135, 136);
        WriteU16(packet6, body6 + 12, 137); packet6[body6 + 14] = 138; packet6[body6 + 15] = 2;
        WriteU16(packet6, body6 + 16, 139); WriteU16(packet6, body6 + 18, 140); WriteU16(packet6, body6 + 20, 141); WriteU16(packet6, body6 + 22, 142);
        packet6[body6 + 24] = 9; packet6[body6 + 25] = 10; WriteU16(packet6, body6 + 26, 840); packet6[body6 + 28] = 11; packet6[body6 + 29] = 12;
        packet6[body6 + 30] = 1; packet6[body6 + 31] = 0x01; packet6[body6 + 32] = 0x02; packet6[body6 + 33] = 0x03; packet6[body6 + 34] = 0x04; packet6[body6 + 35] = 0x05; packet6[body6 + 36] = 0x06;
        WriteWorld(packet6, body6 + 37, 1000.25, 1001.5, 1002.75); WriteVec3(packet6, body6 + 61, 0.1f, 0.2f, 0.3f); WriteU16(packet6, body6 + 73, 25); WriteU16(packet6, body6 + 75, 26); WriteU16(packet6, body6 + 77, 27); WriteU16(packet6, body6 + 79, 28); WriteU32(packet6, body6 + 81, 29u);
        packet6[body6 + 85] = 2; packet6[body6 + 86] = 0x0A; packet6[body6 + 87] = 0x0B; packet6[body6 + 88] = 0x0C; packet6[body6 + 89] = 0x0D; packet6[body6 + 90] = 0x0E; packet6[body6 + 91] = 0x0F;
        WriteWorld(packet6, body6 + 92, 2000.25, 2001.5, 2002.75); WriteVec3(packet6, body6 + 116, 0.4f, 0.5f, 0.6f); WriteU16(packet6, body6 + 128, 35); WriteU16(packet6, body6 + 130, 36); WriteU16(packet6, body6 + 132, 37); WriteU16(packet6, body6 + 134, 38); WriteU32(packet6, body6 + 136, 39u);
        return packet6;
    }

    private static byte[] CreateArealObjectStatePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 45, 100);
        packet[3] = 9;
        int body = 12;
        if (version >= 7)
        {
            WriteEntityId(packet, body + 0, 111, 112, 113); WriteEntityId(packet, body + 6, 114, 115, 116);
            WriteU16(packet, body + 12, 117); packet[body + 14] = 118; packet[body + 15] = 119;
            WriteEntityType(packet, body + 16, 6, 7, 124, 8, 9, 10, 11);
            WriteU32(packet, body + 24, 120u); WriteU16(packet, body + 28, 121); WriteU16(packet, body + 30, 2);
            WriteU16(packet, body + 32, 122); WriteU16(packet, body + 34, 123); WriteU16(packet, body + 36, 124); WriteU16(packet, body + 38, 125);
            WriteWorld(packet, body + 40, 7.0, 8.0, 9.0); WriteWorld(packet, body + 64, 10.0, 11.0, 12.0);
        }
        else
        {
            WriteEntityId(packet, body + 0, 91, 92, 93); WriteEntityId(packet, body + 6, 94, 95, 96);
            WriteU16(packet, body + 12, 97); packet[body + 14] = 98; packet[body + 15] = 99;
            WriteEntityType(packet, body + 16, 3, 4, 225, 5, 6, 7, 8);
            packet[body + 24] = 0x01; packet[body + 25] = 0x02; packet[body + 26] = 0x03; packet[body + 27] = 0x04; packet[body + 28] = 0x05; packet[body + 29] = 0x06;
            WriteU16(packet, body + 30, 2); WriteU16(packet, body + 32, 100); WriteU16(packet, body + 34, 101); WriteU16(packet, body + 36, 102); WriteU16(packet, body + 38, 103);
            WriteWorld(packet, body + 40, 1.0, 2.0, 3.0); WriteWorld(packet, body + 64, 4.0, 5.0, 6.0);
        }
        return packet;
    }

    private static byte[] CreateRecordReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 63, 44);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001);
        WriteU16(packet, body + 2, 0x0002);
        WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004);
        WriteU16(packet, body + 8, 0x0005);
        WriteU16(packet, body + 10, 0x0006);
        WriteU32(packet, body + 12, 0x51525354u);
        packet[body + 16] = 7;
        packet[body + 17] = 8;
        WriteU16(packet, body + 18, 0x090A);
        WriteU32(packet, body + 20, 2u);
        for (int i = 0; i < 8; ++i)
        {
            packet[body + 24 + i] = (byte)(0x10 + i);
        }
        return packet;
    }

    private static byte[] CreateSetRecordReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 64, 48);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001);
        WriteU16(packet, body + 2, 0x0002);
        WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004);
        WriteU16(packet, body + 8, 0x0005);
        WriteU16(packet, body + 10, 0x0006);
        WriteU32(packet, body + 12, 0x61626364u);
        packet[body + 16] = 9;
        WriteU16(packet, body + 17, 0x0B0C);
        packet[body + 19] = 13;
        WriteU32(packet, body + 20, 3u);
        for (int i = 0; i < 8; ++i)
        {
            packet[body + 28 + i] = (byte)(0x21 + i);
        }
        return packet;
    }

    private static byte[] CreateRecordQueryReliablePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 65, 50);
        packet[3] = 10;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001);
        WriteU16(packet, body + 2, 0x0002);
        WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004);
        WriteU16(packet, body + 8, 0x0005);
        WriteU16(packet, body + 10, 0x0006);
        WriteU32(packet, body + 12, 0x71727374u);
        packet[body + 16] = 14;
        WriteU16(packet, body + 17, 0x1516);
        packet[body + 19] = 17;
        WriteU16(packet, body + 20, 0x1819);
        WriteU32(packet, body + 22, 0x1A1B1C1Du);
        WriteU32(packet, body + 26, 2u);
        for (int i = 0; i < 8; ++i)
        {
            packet[body + 30 + i] = (byte)(0x31 + i);
        }
        return packet;
    }

    private static byte[] CreateServiceRequestPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 5, 36);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 7;
        packet[body + 13] = 2;
        WriteU16(packet, body + 14, 0x4041);
        for (int i = 0; i < 8; ++i) { packet[body + 16 + i] = (byte)(0x41 + i); }
        return packet;
    }

    private static byte[] CreateResupplyOfferPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 6, 36);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 2;
        packet[body + 13] = 0x11;
        packet[body + 14] = 0x12;
        packet[body + 15] = 0x13;
        for (int i = 0; i < 8; ++i) { packet[body + 16 + i] = (byte)(0x51 + i); }
        return packet;
    }

    private static byte[] CreateResupplyReceivedPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 7, 36);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 2;
        WriteU16(packet, body + 13, 0x6162);
        packet[body + 15] = 0x63;
        for (int i = 0; i < 8; ++i) { packet[body + 16 + i] = (byte)(0x61 + i); }
        return packet;
    }

    private static byte[] CreateResupplyCancelPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 8, 24);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        return packet;
    }

    private static byte[] CreateRepairCompletePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 9, 28);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        WriteU16(packet, body + 12, 0x7172);
        WriteU16(packet, body + 14, 0x7374);
        return packet;
    }

    private static byte[] CreateRepairResponsePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 10, 28);
        packet[3] = 3;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 0x75;
        WriteU16(packet, body + 13, 0x7677);
        packet[body + 15] = 0x78;
        return packet;
    }

    private static byte[] CreateDesignatorPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 24, 88);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x1234);
        WriteU16(packet, body + 8, 0x0004); WriteU16(packet, body + 10, 0x0005); WriteU16(packet, body + 12, 0x0006);
        WriteU16(packet, body + 14, 0x2345);
        WriteFloat(packet, body + 16, 12.5f);
        WriteFloat(packet, body + 20, 1.25f);
        WriteVec3(packet, body + 24, 2.5f, 3.5f, 4.5f);
        WriteWorld(packet, body + 36, 100.0, 200.0, 300.0);
        packet[body + 60] = 4;
        WriteU16(packet, body + 61, 0x3456);
        packet[body + 63] = 0x78;
        WriteVec3(packet, body + 64, 5.5f, 6.5f, 7.5f);
        return packet;
    }

    private static byte[] CreateTransmitterPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 25, (ushort)(version >= 7 ? 124 : 103));
        packet[3] = 4;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x1212);
        if (version >= 7)
        {
            packet[body + 8] = 1; packet[body + 9] = 2; WriteU16(packet, body + 10, 840);
            packet[body + 12] = 5; packet[body + 13] = 6; packet[body + 14] = 7; packet[body + 15] = 8;
            WriteU16(packet, body + 18, 2);
        }
        else
        {
            packet[body + 8] = 1; packet[body + 9] = 2; WriteU16(packet, body + 10, 840);
            packet[body + 12] = 5; packet[body + 13] = 6; WriteU16(packet, body + 14, 0x0708);
        }
        packet[body + 16] = 9;
        packet[body + 17] = 10;
        WriteWorld(packet, body + 20, 10.0, 20.0, 30.0);
        WriteVec3(packet, body + 44, 1.0f, 2.0f, 3.0f);
        WriteU16(packet, body + 56, 0x4444);
        WriteU16(packet, body + 58, version >= 7 ? (ushort)1 : (ushort)0);
        WriteU32(packet, body + 60, 225000u);
        WriteFloat(packet, body + 64, 50.5f);
        WriteFloat(packet, body + 68, 60.5f);
        WriteU16(packet, body + 72, 1); WriteU16(packet, body + 74, 2); WriteU16(packet, body + 76, 3); WriteU16(packet, body + 78, 4);
        WriteU16(packet, body + 80, 0x5555); WriteU16(packet, body + 82, 0x6666);
        packet[body + 84] = version >= 7 ? (byte)1 : (byte)3;
        WriteU16(packet, body + 85, 0x7777);
        packet[body + 87] = 0x88;
        if (version >= 7)
        {
            WriteVec3(packet, 100, 9.0f, 10.0f, 11.0f);
            WriteVec3(packet, 112, 12.0f, 13.0f, 14.0f);
        }
        else
        {
            packet[100] = 0x01; packet[101] = 0x02; packet[102] = 0x03;
        }
        return packet;
    }

    private static byte[] CreateSignalPdu(byte version)
    {
        int length = version >= 7 ? 28 : 36;
        byte[] packet = CreatePdu(version, 26, (ushort)length);
        packet[3] = 4;
        int body = 12;
        int offset = 0;
        if (version < 7)
        {
            WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x1111);
            offset = 8;
        }
        WriteU16(packet, body + offset + 0, 0x2222);
        WriteU16(packet, body + offset + 2, 0x3333);
        WriteU32(packet, body + offset + 4, 48000u);
        WriteU16(packet, body + offset + 8, 4);
        WriteU16(packet, body + offset + 10, 2);
        packet[body + offset + 12] = 0x41;
        packet[body + offset + 13] = 0x42;
        packet[body + offset + 14] = 0x43;
        packet[body + offset + 15] = 0x44;
        return packet;
    }

    private static byte[] CreateReceiverPdu(byte version)
    {
        int length = version >= 7 ? 28 : 36;
        byte[] packet = CreatePdu(version, 27, (ushort)length);
        packet[3] = 4;
        int body = 12;
        int offset = 0;
        if (version < 7)
        {
            WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x1111);
            offset = 8;
        }
        WriteU16(packet, body + offset + 0, 0x2222);
        WriteU16(packet, body + offset + 2, 0x3333);
        WriteFloat(packet, body + offset + 4, 12.5f);
        WriteU16(packet, body + offset + 8, 0x0004); WriteU16(packet, body + offset + 10, 0x0005); WriteU16(packet, body + offset + 12, 0x0006);
        WriteU16(packet, body + offset + 14, 0x4444);
        return packet;
    }

    private static byte[] CreateIffAtcNavAidsLayer1Pdu(byte version)
    {
        byte[] packet = CreatePdu(version, 28, 56);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        WriteVec3(packet, body + 12, 1.0f, 2.0f, 3.0f);
        WriteU16(packet, body + 24, 0x1111); WriteU16(packet, body + 26, 0x2222);
        packet[body + 28] = 0x33; packet[body + 29] = 0x44;
        WriteU16(packet, body + 30, 0x5555);
        packet[body + 32] = 1; packet[body + 33] = 2; packet[body + 34] = 3; packet[body + 35] = 4;
        WriteU16(packet, body + 36, 5); WriteU16(packet, body + 38, 6); WriteU16(packet, body + 40, 7);
        WriteU16(packet, body + 42, 8); WriteU16(packet, body + 44, 9); WriteU16(packet, body + 46, 10);
        return packet;
    }

    private static byte[] CreateIntercomSignalPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 31, 36);
        packet[3] = 4;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x1212);
        WriteU16(packet, body + 8, 0x2222);
        WriteU16(packet, body + 10, 0x3333);
        WriteU32(packet, body + 12, 32000u);
        WriteU16(packet, body + 16, 4);
        WriteU16(packet, body + 18, 2);
        packet[body + 20] = 0x51;
        packet[body + 21] = 0x52;
        packet[body + 22] = 0x53;
        packet[body + 23] = 0x54;
        return packet;
    }

    private static byte[] CreateIntercomControlPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 32, 41);
        packet[3] = 4;
        int body = 12;
        packet[body + 0] = 0x11; packet[body + 1] = 0x22;
        WriteU16(packet, body + 2, 0x0001); WriteU16(packet, body + 4, 0x0002); WriteU16(packet, body + 6, 0x0003);
        packet[body + 8] = 0x33; packet[body + 9] = 0x44; packet[body + 10] = 0x55; packet[body + 11] = 0x66; packet[body + 12] = 0x77;
        WriteU16(packet, body + 13, 0x0004); WriteU16(packet, body + 15, 0x0005); WriteU16(packet, body + 17, 0x0006);
        WriteU16(packet, body + 19, 0x8888);
        WriteU32(packet, body + 21, 4u);
        packet[body + 25] = 0x61; packet[body + 26] = 0x62; packet[body + 27] = 0x63; packet[body + 28] = 0x64;
        return packet;
    }

    private static byte[] CreateAttributePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 72, 36);
        packet[3] = 1;
        int body = 12;
        WriteU16(packet, body + 0, 0x0101);
        WriteU16(packet, body + 2, 0x0202);
        WriteU32(packet, body + 4, 0x11223344u);
        WriteU16(packet, body + 8, 0x5566);
        packet[body + 10] = 67;
        packet[body + 11] = 7;
        WriteU32(packet, body + 12, 0x778899AAu);
        packet[body + 16] = 0x12;
        packet[body + 17] = 0x34;
        WriteU16(packet, body + 18, 1);
        packet[body + 20] = 0x61; packet[body + 21] = 0x62; packet[body + 22] = 0x63; packet[body + 23] = 0x64;
        return packet;
    }

    private static byte[] CreateDirectedEnergyFirePdu(byte version)
    {
        byte[] packet = CreatePdu(version, 68, 94);
        packet[3] = 2;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 2; packet[body + 13] = 1; WriteU16(packet, body + 14, 225); packet[body + 16] = 4; packet[body + 17] = 5; packet[body + 18] = 6; packet[body + 19] = 7;
        WriteU32(packet, body + 20, 7u);
        WriteU32(packet, body + 24, 123456u);
        WriteFloat(packet, body + 28, 1.25f);
        WriteVec3(packet, body + 32, 2.5f, 3.5f, 4.5f);
        WriteFloat(packet, body + 44, 5.5f);
        WriteFloat(packet, body + 48, 6.5f);
        WriteFloat(packet, body + 52, 7.5f);
        WriteFloat(packet, body + 56, 8.5f);
        WriteU32(packet, body + 60, 9012u);
        WriteU32(packet, body + 64, 0x10203040u);
        packet[body + 68] = 0x11;
        packet[body + 69] = 0x22;
        WriteU32(packet, body + 70, 0x33445566u);
        WriteU16(packet, body + 74, 0x7788);
        WriteU16(packet, body + 76, 1);
        packet[body + 78] = 0x90; packet[body + 79] = 0x91; packet[body + 80] = 0x92; packet[body + 81] = 0x93;
        return packet;
    }

    private static byte[] CreateEntityDamageStatusPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 69, 40);
        packet[3] = 2;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        WriteU16(packet, body + 12, 0x0007); WriteU16(packet, body + 14, 0x0008); WriteU16(packet, body + 16, 0x0009);
        WriteU16(packet, body + 18, 0x1112);
        WriteU16(packet, body + 20, 0x1314);
        WriteU16(packet, body + 22, 1);
        packet[body + 24] = 0xA1; packet[body + 25] = 0xA2; packet[body + 26] = 0xA3; packet[body + 27] = 0xA4;
        return packet;
    }

    private static byte[] CreateIffPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 28, 56);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        WriteVec3(packet, body + 12, 1.0f, 2.0f, 3.0f);
        WriteU16(packet, body + 24, 0x1111); WriteU16(packet, body + 26, 0x2222); packet[body + 28] = 0x33; packet[body + 29] = 0x44;
        WriteU16(packet, body + 30, 0x5555);
        packet[body + 32] = 1; packet[body + 33] = 2; packet[body + 34] = 3; packet[body + 35] = 4;
        WriteU16(packet, body + 36, 5); WriteU16(packet, body + 38, 6); WriteU16(packet, body + 40, 7); WriteU16(packet, body + 42, 8); WriteU16(packet, body + 44, 9); WriteU16(packet, body + 46, 10);
        return packet;
    }

    private static byte[] CreateElectronicEmissionsPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 23, 34);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 0x07;
        packet[body + 13] = 0x02;
        WriteU16(packet, body + 14, 0x0809);
        packet[body + 16] = 0xE1; packet[body + 17] = 0xE2; packet[body + 18] = 0xE3;
        packet[body + 19] = 0xE4; packet[body + 20] = 0xE5; packet[body + 21] = 0xE6;
        return packet;
    }

    private static byte[] CreateUaPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 29, 40);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        packet[body + 12] = 0x0A;
        packet[body + 13] = 0x0B;
        WriteU16(packet, body + 14, 0x0C0D);
        packet[body + 16] = 0x0E;
        packet[body + 17] = 0x01;
        packet[body + 18] = 0x02;
        packet[body + 19] = 0x03;
        packet[body + 20] = 0xF1; packet[body + 21] = 0xF2; packet[body + 22] = 0xF3; packet[body + 23] = 0xF4;
        packet[body + 24] = 0xF5; packet[body + 25] = 0xF6; packet[body + 26] = 0xF7; packet[body + 27] = 0xF8;
        return packet;
    }

    private static byte[] CreateSeesPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 30, 36);
        packet[3] = 6;
        int body = 12;
        WriteU16(packet, body + 0, 0x0011); WriteU16(packet, body + 2, 0x0022); WriteU16(packet, body + 4, 0x0033);
        WriteU16(packet, body + 6, 0x1112); WriteU16(packet, body + 8, 0x1314); WriteU16(packet, body + 10, 0x1516);
        WriteU16(packet, body + 12, 2);
        WriteU16(packet, body + 14, 3);
        packet[body + 16] = 0xAA; packet[body + 17] = 0xBB; packet[body + 18] = 0xCC; packet[body + 19] = 0xDD;
        packet[body + 20] = 0xEE; packet[body + 21] = 0xFF; packet[body + 22] = 0x00; packet[body + 23] = 0x11;
        return packet;
    }

    private static byte[] CreateInformationOperationsActionPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 70, 60);
        packet[3] = 13;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0004); WriteU16(packet, body + 8, 0x0005); WriteU16(packet, body + 10, 0x0006);
        WriteU32(packet, body + 12, 0x11223344u);
        WriteU16(packet, body + 16, 0x0102); WriteU16(packet, body + 18, 0x0304); WriteU16(packet, body + 20, 0x0506); WriteU16(packet, body + 22, 0x0708);
        WriteU32(packet, body + 24, 0x55667788u);
        WriteU16(packet, body + 28, 0x0007); WriteU16(packet, body + 30, 0x0008); WriteU16(packet, body + 32, 0x0009);
        WriteU16(packet, body + 34, 0x000A); WriteU16(packet, body + 36, 0x000B); WriteU16(packet, body + 38, 0x000C);
        WriteU16(packet, body + 40, 0x090A); WriteU16(packet, body + 42, 1);
        packet[body + 44] = 0xC1; packet[body + 45] = 0xC2; packet[body + 46] = 0xC3; packet[body + 47] = 0xC4;
        return packet;
    }

    private static byte[] CreateInformationOperationsReportPdu(byte version)
    {
        byte[] packet = CreatePdu(version, 71, 44);
        packet[3] = 13;
        int body = 12;
        WriteU16(packet, body + 0, 0x0001); WriteU16(packet, body + 2, 0x0002); WriteU16(packet, body + 4, 0x0003);
        WriteU16(packet, body + 6, 0x0102); packet[body + 8] = 0x03; packet[body + 9] = 0x04;
        WriteU16(packet, body + 10, 0x0004); WriteU16(packet, body + 12, 0x0005); WriteU16(packet, body + 14, 0x0006);
        WriteU16(packet, body + 16, 0x0007); WriteU16(packet, body + 18, 0x0008); WriteU16(packet, body + 20, 0x0009);
        WriteU16(packet, body + 22, 0x1112); WriteU16(packet, body + 24, 0x1314); WriteU16(packet, body + 26, 1);
        packet[body + 28] = 0xD1; packet[body + 29] = 0xD2; packet[body + 30] = 0xD3; packet[body + 31] = 0xD4;
        return packet;
    }

    private static byte[] CreatePdu(byte version, byte pduType, ushort length)
    {
        byte[] packet = new byte[Math.Max(160, (int)length)];
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

    private static void WriteEntityId(byte[] packet, int offset, ushort site, ushort application, ushort entity)
    {
        WriteU16(packet, offset + 0, site);
        WriteU16(packet, offset + 2, application);
        WriteU16(packet, offset + 4, entity);
    }

    private static void WriteEntityType(byte[] packet, int offset, byte kind, byte domain, ushort country, byte category, byte subcategory, byte specific, byte extra)
    {
        packet[offset + 0] = kind;
        packet[offset + 1] = domain;
        WriteU16(packet, offset + 2, country);
        packet[offset + 4] = category;
        packet[offset + 5] = subcategory;
        packet[offset + 6] = specific;
        packet[offset + 7] = extra;
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
