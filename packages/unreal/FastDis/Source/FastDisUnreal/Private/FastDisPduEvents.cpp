#include "FastDisPduEvents.h"

namespace
{
constexpr int32 FastDisHeaderBytes = 12;

int32 ReadBe16(const uint8* Data, int32 Offset)
{
    return (static_cast<int32>(Data[Offset]) << 8) | static_cast<int32>(Data[Offset + 1]);
}

uint32 ReadBe32(const uint8* Data, int32 Offset)
{
    return (static_cast<uint32>(Data[Offset + 0]) << 24) |
           (static_cast<uint32>(Data[Offset + 1]) << 16) |
           (static_cast<uint32>(Data[Offset + 2]) << 8) |
           static_cast<uint32>(Data[Offset + 3]);
}

uint64 ReadBe64(const uint8* Data, int32 Offset)
{
    return (static_cast<uint64>(Data[Offset + 0]) << 56) |
           (static_cast<uint64>(Data[Offset + 1]) << 48) |
           (static_cast<uint64>(Data[Offset + 2]) << 40) |
           (static_cast<uint64>(Data[Offset + 3]) << 32) |
           (static_cast<uint64>(Data[Offset + 4]) << 24) |
           (static_cast<uint64>(Data[Offset + 5]) << 16) |
           (static_cast<uint64>(Data[Offset + 6]) << 8) |
           static_cast<uint64>(Data[Offset + 7]);
}

float ReadBeFloat(const uint8* Data, int32 Offset)
{
    const uint32 Bits = ReadBe32(Data, Offset);
    float Value = 0.0f;
    FMemory::Memcpy(&Value, &Bits, sizeof(Value));
    return Value;
}

double ReadBeDouble(const uint8* Data, int32 Offset)
{
    const uint64 Bits = ReadBe64(Data, Offset);
    double Value = 0.0;
    FMemory::Memcpy(&Value, &Bits, sizeof(Value));
    return Value;
}

bool HasBytes(const FFastDisPduEvent& Event, int32 BodyOffset, int32 ByteCount)
{
    const int32 Absolute = FastDisHeaderBytes + BodyOffset;
    return BodyOffset >= 0 && ByteCount >= 0 && Absolute >= FastDisHeaderBytes && Absolute + ByteCount <= Event.RawBytes.Num();
}

const uint8* BodyData(const FFastDisPduEvent& Event)
{
    return Event.RawBytes.GetData() + FastDisHeaderBytes;
}

FFastDisEntityId ReadEntityId(const uint8* Data, int32 Offset)
{
    return FFastDisEntityId(
        static_cast<uint16>(ReadBe16(Data, Offset + 0)),
        static_cast<uint16>(ReadBe16(Data, Offset + 2)),
        static_cast<uint16>(ReadBe16(Data, Offset + 4)));
}

FVector ReadVec3f(const uint8* Data, int32 Offset)
{
    return FVector(ReadBeFloat(Data, Offset + 0), ReadBeFloat(Data, Offset + 4), ReadBeFloat(Data, Offset + 8));
}

FVector ReadWorld(const uint8* Data, int32 Offset)
{
    return FVector(ReadBeDouble(Data, Offset + 0), ReadBeDouble(Data, Offset + 8), ReadBeDouble(Data, Offset + 16));
}

EFastDisPduSurface SurfaceForType(int32 PduType)
{
    switch (PduType)
    {
    case 1:
        return EFastDisPduSurface::EntityState;
    case 2:
        return EFastDisPduSurface::Fire;
    case 3:
        return EFastDisPduSurface::Detonation;
    case 7:
        return EFastDisPduSurface::StartResume;
    case 8:
        return EFastDisPduSurface::StopFreeze;
    case 12:
        return EFastDisPduSurface::RemoveEntity;
    case 23:
        return EFastDisPduSurface::ElectromagneticEmission;
    case 24:
        return EFastDisPduSurface::Designator;
    case 26:
        return EFastDisPduSurface::Signal;
    case 67:
        return EFastDisPduSurface::EntityStateUpdate;
    default:
        return EFastDisPduSurface::Unknown;
    }
}

FName NameForSurface(EFastDisPduSurface Surface)
{
    switch (Surface)
    {
    case EFastDisPduSurface::EntityState:
        return TEXT("Entity State");
    case EFastDisPduSurface::EntityStateUpdate:
        return TEXT("Entity State Update");
    case EFastDisPduSurface::RemoveEntity:
        return TEXT("Remove Entity");
    case EFastDisPduSurface::Fire:
        return TEXT("Fire");
    case EFastDisPduSurface::Detonation:
        return TEXT("Detonation");
    case EFastDisPduSurface::StartResume:
        return TEXT("Start/Resume");
    case EFastDisPduSurface::StopFreeze:
        return TEXT("Stop/Freeze");
    case EFastDisPduSurface::ElectromagneticEmission:
        return TEXT("Electromagnetic Emission");
    case EFastDisPduSurface::Signal:
        return TEXT("Signal");
    case EFastDisPduSurface::Designator:
        return TEXT("Designator");
    case EFastDisPduSurface::Unknown:
    default:
        return TEXT("Unknown");
    }
}
}

UFastDisPduEventComponent::UFastDisPduEventComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool UFastDisPduEventComponent::EmitPduEvent(const TArray<uint8>& Packet, const FString& SourceEndpoint)
{
    FFastDisPduHeader Header;
    if (!ParsePduHeader(Packet, Header))
    {
        FFastDisPduEvent Event;
        Event.SourceEndpoint = SourceEndpoint;
        Event.RawBytes = Packet;
        OnMalformedPdu.Broadcast(Event);
        return false;
    }

    FFastDisPduEvent Event;
    Event.Header = Header;
    Event.SourceEndpoint = SourceEndpoint;
    Event.RawBytes = Packet;
    BroadcastPduEvent(Event);
    return true;
}

bool UFastDisPduEventComponent::ParsePduHeader(const TArray<uint8>& Packet, FFastDisPduHeader& OutHeader)
{
    return ParsePduHeaderBytes(Packet.GetData(), Packet.Num(), OutHeader);
}

bool UFastDisPduEventComponent::ParsePduHeaderBytes(const uint8* Data, int32 Length, FFastDisPduHeader& OutHeader)
{
    if (!Data || Length < FastDisHeaderBytes)
    {
        return false;
    }

    const int32 DeclaredLength = ReadBe16(Data, 8);
    if (DeclaredLength <= 0 || DeclaredLength > Length)
    {
        return false;
    }

    OutHeader.Version = Data[0];
    OutHeader.ExerciseId = Data[1];
    OutHeader.PduType = Data[2];
    OutHeader.ProtocolFamily = Data[3];
    OutHeader.DeclaredLength = DeclaredLength;
    OutHeader.PacketSize = Length;
    OutHeader.Surface = SurfaceForType(OutHeader.PduType);
    OutHeader.PduName = NameForSurface(OutHeader.Surface);
    return true;
}

bool UFastDisPduEventComponent::ParseRemoveEntityEvent(const FFastDisPduEvent& Event, FFastDisRemoveEntityEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::RemoveEntity || !HasBytes(Event, 0, 16))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.OriginatingEntityId = ReadEntityId(Body, 0);
    OutEvent.ReceivingEntityId = ReadEntityId(Body, 6);
    OutEvent.RequestId = static_cast<int32>(ReadBe32(Body, 12));
    return true;
}

bool UFastDisPduEventComponent::ParseEntityStateUpdateEvent(const FFastDisPduEvent& Event, FFastDisEntityStateUpdateEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::EntityStateUpdate || !HasBytes(Event, 0, 60))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.EntityId = ReadEntityId(Body, 0);
    OutEvent.LinearVelocityMetersPerSecond = ReadVec3f(Body, 8);
    OutEvent.WorldLocationMeters = ReadWorld(Body, 20);
    OutEvent.DisOrientationRadians = FRotator(ReadBeFloat(Body, 48), ReadBeFloat(Body, 44), ReadBeFloat(Body, 52));
    OutEvent.Appearance = static_cast<int32>(ReadBe32(Body, 56));
    return true;
}

bool UFastDisPduEventComponent::ParseFireEvent(const FFastDisPduEvent& Event, FFastDisFireEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::Fire || !HasBytes(Event, 0, 86))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.FiringEntityId = ReadEntityId(Body, 0);
    OutEvent.TargetEntityId = ReadEntityId(Body, 6);
    OutEvent.MunitionEntityId = ReadEntityId(Body, 12);
    OutEvent.EventNumber = ReadBe16(Body, 24);
    OutEvent.FireMissionIndex = static_cast<int32>(ReadBe32(Body, 26));
    OutEvent.WorldLocationMeters = ReadWorld(Body, 30);
    OutEvent.VelocityMetersPerSecond = ReadVec3f(Body, 70);
    OutEvent.RangeMeters = ReadBeFloat(Body, 82);
    return true;
}

bool UFastDisPduEventComponent::ParseDetonationEvent(const FFastDisPduEvent& Event, FFastDisDetonationEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::Detonation || !HasBytes(Event, 0, 91))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.FiringEntityId = ReadEntityId(Body, 0);
    OutEvent.TargetEntityId = ReadEntityId(Body, 6);
    OutEvent.MunitionEntityId = ReadEntityId(Body, 12);
    OutEvent.EventNumber = ReadBe16(Body, 24);
    OutEvent.VelocityMetersPerSecond = ReadVec3f(Body, 26);
    OutEvent.WorldLocationMeters = ReadWorld(Body, 38);
    OutEvent.DetonationResult = Body[90];
    return true;
}

bool UFastDisPduEventComponent::ParseStartResumeEvent(const FFastDisPduEvent& Event, FFastDisStartResumeEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::StartResume || !HasBytes(Event, 0, 32))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.OriginatingEntityId = ReadEntityId(Body, 0);
    OutEvent.ReceivingEntityId = ReadEntityId(Body, 6);
    OutEvent.RealWorldTime = static_cast<int64>(ReadBe64(Body, 12));
    OutEvent.SimulationTime = static_cast<int64>(ReadBe64(Body, 20));
    OutEvent.RequestId = static_cast<int32>(ReadBe32(Body, 28));
    return true;
}

bool UFastDisPduEventComponent::ParseStopFreezeEvent(const FFastDisPduEvent& Event, FFastDisStopFreezeEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::StopFreeze || !HasBytes(Event, 0, 28))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.OriginatingEntityId = ReadEntityId(Body, 0);
    OutEvent.ReceivingEntityId = ReadEntityId(Body, 6);
    OutEvent.RealWorldTime = static_cast<int64>(ReadBe64(Body, 12));
    OutEvent.Reason = Body[20];
    OutEvent.FrozenBehavior = Body[21];
    OutEvent.RequestId = static_cast<int32>(ReadBe32(Body, 24));
    return true;
}

bool UFastDisPduEventComponent::ParseEmissionEvent(const FFastDisPduEvent& Event, FFastDisEmissionEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::ElectromagneticEmission || !HasBytes(Event, 0, 12))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.EmittingEntityId = ReadEntityId(Body, 0);
    OutEvent.EventNumber = ReadBe16(Body, 6);
    OutEvent.StateUpdateIndicator = Body[8];
    OutEvent.SystemCount = Body[9];
    return true;
}

bool UFastDisPduEventComponent::ParseSignalEvent(const FFastDisPduEvent& Event, FFastDisSignalEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::Signal || !HasBytes(Event, 0, 20))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.EntityId = ReadEntityId(Body, 0);
    OutEvent.RadioId = ReadBe16(Body, 6);
    OutEvent.EncodingScheme = ReadBe16(Body, 8);
    OutEvent.TdlType = ReadBe16(Body, 10);
    OutEvent.SampleRate = static_cast<int32>(ReadBe32(Body, 12));
    OutEvent.DataLengthBits = ReadBe16(Body, 16);
    OutEvent.SampleCount = ReadBe16(Body, 18);

    const int32 DataBytes = (OutEvent.DataLengthBits + 7) / 8;
    if (DataBytes > 0 && HasBytes(Event, 20, DataBytes))
    {
        OutEvent.SignalData.Append(Body + 20, DataBytes);
    }
    return true;
}

bool UFastDisPduEventComponent::ParseDesignatorEvent(const FFastDisPduEvent& Event, FFastDisDesignatorEvent& OutEvent)
{
    if (Event.Header.Surface != EFastDisPduSurface::Designator || !HasBytes(Event, 0, 60))
    {
        return false;
    }

    const uint8* Body = BodyData(Event);
    OutEvent.BaseEvent = Event;
    OutEvent.DesignatingEntityId = ReadEntityId(Body, 0);
    OutEvent.CodeName = ReadBe16(Body, 6);
    OutEvent.DesignatedEntityId = ReadEntityId(Body, 8);
    OutEvent.DesignatorCode = ReadBe16(Body, 14);
    OutEvent.Power = ReadBeFloat(Body, 16);
    OutEvent.Wavelength = ReadBeFloat(Body, 20);
    OutEvent.SpotLocationRelativeMeters = ReadVec3f(Body, 24);
    OutEvent.SpotLocationMeters = ReadWorld(Body, 36);
    return true;
}

void UFastDisPduEventComponent::BroadcastPduEvent(const FFastDisPduEvent& Event)
{
    OnPduReceived.Broadcast(Event);

    switch (Event.Header.Surface)
    {
    case EFastDisPduSurface::EntityState:
        OnEntityState.Broadcast(Event);
        break;
    case EFastDisPduSurface::EntityStateUpdate:
        OnEntityStateUpdate.Broadcast(Event);
        {
            FFastDisEntityStateUpdateEvent Decoded;
            if (ParseEntityStateUpdateEvent(Event, Decoded))
            {
                OnEntityStateUpdateDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::RemoveEntity:
        OnRemoveEntity.Broadcast(Event);
        {
            FFastDisRemoveEntityEvent Decoded;
            if (ParseRemoveEntityEvent(Event, Decoded))
            {
                OnRemoveEntityDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::Fire:
        OnFire.Broadcast(Event);
        {
            FFastDisFireEvent Decoded;
            if (ParseFireEvent(Event, Decoded))
            {
                OnFireDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::Detonation:
        OnDetonation.Broadcast(Event);
        {
            FFastDisDetonationEvent Decoded;
            if (ParseDetonationEvent(Event, Decoded))
            {
                OnDetonationDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::StartResume:
        OnStartResume.Broadcast(Event);
        {
            FFastDisStartResumeEvent Decoded;
            if (ParseStartResumeEvent(Event, Decoded))
            {
                OnStartResumeDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::StopFreeze:
        OnStopFreeze.Broadcast(Event);
        {
            FFastDisStopFreezeEvent Decoded;
            if (ParseStopFreezeEvent(Event, Decoded))
            {
                OnStopFreezeDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::ElectromagneticEmission:
        OnEmission.Broadcast(Event);
        {
            FFastDisEmissionEvent Decoded;
            if (ParseEmissionEvent(Event, Decoded))
            {
                OnEmissionDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::Signal:
        OnSignal.Broadcast(Event);
        {
            FFastDisSignalEvent Decoded;
            if (ParseSignalEvent(Event, Decoded))
            {
                OnSignalDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::Designator:
        OnDesignator.Broadcast(Event);
        {
            FFastDisDesignatorEvent Decoded;
            if (ParseDesignatorEvent(Event, Decoded))
            {
                OnDesignatorDecoded.Broadcast(Decoded);
            }
        }
        break;
    case EFastDisPduSurface::Unknown:
    default:
        break;
    }
}
