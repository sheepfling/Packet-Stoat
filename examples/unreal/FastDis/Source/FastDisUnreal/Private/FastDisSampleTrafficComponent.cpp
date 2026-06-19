#include "FastDisSampleTrafficComponent.h"

#include "Engine/World.h"
#include "FastDisWorldSubsystem.h"
#include "GameFramework/Actor.h"

#ifdef check
#pragma push_macro("check")
#undef check
#define FASTDIS_RESTORE_UE_CHECK_MACRO 1
#endif

#include "fastdis/fastdis.h"
#include "fastdis/fastdis_frames.hpp"

#ifdef FASTDIS_RESTORE_UE_CHECK_MACRO
#pragma pop_macro("check")
#undef FASTDIS_RESTORE_UE_CHECK_MACRO
#endif

namespace
{
void PutBe16(TArray<uint8>& Buffer, int32 Offset, uint16 Value)
{
    Buffer[Offset + 0] = static_cast<uint8>((Value >> 8) & 0xFFu);
    Buffer[Offset + 1] = static_cast<uint8>(Value & 0xFFu);
}

void PutBe32(TArray<uint8>& Buffer, int32 Offset, uint32 Value)
{
    Buffer[Offset + 0] = static_cast<uint8>((Value >> 24) & 0xFFu);
    Buffer[Offset + 1] = static_cast<uint8>((Value >> 16) & 0xFFu);
    Buffer[Offset + 2] = static_cast<uint8>((Value >> 8) & 0xFFu);
    Buffer[Offset + 3] = static_cast<uint8>(Value & 0xFFu);
}

void PutBeFloat(TArray<uint8>& Buffer, int32 Offset, float Value)
{
    uint32 Bits = 0;
    FMemory::Memcpy(&Bits, &Value, sizeof(Bits));
    PutBe32(Buffer, Offset, Bits);
}

void PutBeDouble(TArray<uint8>& Buffer, int32 Offset, double Value)
{
    uint64 Bits = 0;
    FMemory::Memcpy(&Bits, &Value, sizeof(Bits));
    Buffer[Offset + 0] = static_cast<uint8>((Bits >> 56) & 0xFFull);
    Buffer[Offset + 1] = static_cast<uint8>((Bits >> 48) & 0xFFull);
    Buffer[Offset + 2] = static_cast<uint8>((Bits >> 40) & 0xFFull);
    Buffer[Offset + 3] = static_cast<uint8>((Bits >> 32) & 0xFFull);
    Buffer[Offset + 4] = static_cast<uint8>((Bits >> 24) & 0xFFull);
    Buffer[Offset + 5] = static_cast<uint8>((Bits >> 16) & 0xFFull);
    Buffer[Offset + 6] = static_cast<uint8>((Bits >> 8) & 0xFFull);
    Buffer[Offset + 7] = static_cast<uint8>(Bits & 0xFFull);
}

void PutVec3f(TArray<uint8>& Buffer, int32 Offset, float X, float Y, float Z)
{
    PutBeFloat(Buffer, Offset + 0, X);
    PutBeFloat(Buffer, Offset + 4, Y);
    PutBeFloat(Buffer, Offset + 8, Z);
}

void PutWorld(TArray<uint8>& Buffer, int32 Offset, const fastdis::frames::Vec3d& EcefMeters)
{
    PutBeDouble(Buffer, Offset + 0, EcefMeters.x);
    PutBeDouble(Buffer, Offset + 8, EcefMeters.y);
    PutBeDouble(Buffer, Offset + 16, EcefMeters.z);
}

TArray<uint8> MakeEntityStatePacket(const UFastDisSampleTrafficComponent& Component)
{
    TArray<uint8> Packet;
    Packet.SetNumZeroed(static_cast<int32>(FASTDIS_ENTITY_STATE_FIXED_SIZE));

    Packet[0] = 7;
    Packet[1] = Component.ExerciseId;
    Packet[2] = FASTDIS_ENTITY_STATE_PDU_TYPE;
    Packet[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    PutBe32(Packet, 4, 0x01020304u);
    PutBe16(Packet, 8, FASTDIS_ENTITY_STATE_FIXED_SIZE);
    Packet[10] = 0x80;
    Packet[11] = 0x00;

    const int32 Body = static_cast<int32>(FASTDIS_HEADER_SIZE);
    PutBe16(Packet, Body + 0, static_cast<uint16>(FMath::Clamp(Component.EntityId.Site, 0, 0xFFFF)));
    PutBe16(Packet, Body + 2, static_cast<uint16>(FMath::Clamp(Component.EntityId.Application, 0, 0xFFFF)));
    PutBe16(Packet, Body + 4, static_cast<uint16>(FMath::Clamp(Component.EntityId.Entity, 0, 0xFFFF)));
    Packet[Body + 6] = Component.ForceId;
    Packet[Body + 7] = 0;

    Packet[Body + 8] = 1;
    Packet[Body + 9] = 1;
    PutBe16(Packet, Body + 10, 840);
    Packet[Body + 12] = 1;
    Packet[Body + 13] = 1;
    Packet[Body + 14] = 1;
    Packet[Body + 15] = 0;

    const fastdis::frames::LocalEnuFrame Frame = fastdis::frames::LocalEnuFrame::from_degrees(
        Component.Georeference.LatitudeDegrees,
        Component.Georeference.LongitudeDegrees,
        Component.Georeference.HeightMeters);
    const fastdis::frames::Vec3d EcefMeters =
        Frame.origin_ecef +
        Frame.north * static_cast<double>(Component.LocalOffsetMeters.X) +
        Frame.east * static_cast<double>(Component.LocalOffsetMeters.Y) +
        Frame.up * static_cast<double>(Component.LocalOffsetMeters.Z);

    PutVec3f(Packet, Body + 24, 0.0f, 0.0f, 0.0f);
    PutWorld(Packet, Body + 36, EcefMeters);
    PutVec3f(Packet, Body + 60, 0.0f, 0.0f, 0.0f);
    PutBe32(Packet, Body + 72, 0u);
    Packet[Body + 76] = 0;
    Packet[Body + 116] = 1;
    static const ANSICHAR Marking[] = "FASTDIS";
    FMemory::Memcpy(Packet.GetData() + Body + 117, Marking, sizeof(Marking) - 1);
    PutBe32(Packet, Body + 128, 0u);

    return Packet;
}
}

UFastDisSampleTrafficComponent::UFastDisSampleTrafficComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UFastDisSampleTrafficComponent::BeginPlay()
{
    Super::BeginPlay();

    if (bRegisterOnBeginPlay)
    {
        RegisterOwnerWithFastDis();
    }

    if (bInjectOnBeginPlay)
    {
        InjectSamplePacket(true);
    }
}

void UFastDisSampleTrafficComponent::RegisterOwnerWithFastDis()
{
    UWorld* World = GetWorld();
    AActor* Owner = GetOwner();
    if (!World || !Owner)
    {
        return;
    }

    if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
    {
        Subsystem->ConfigureGeoreference(Georeference);
        Subsystem->RegisterActor(EntityId, Owner);
    }
}

void UFastDisSampleTrafficComponent::InjectSamplePacket(bool bApplyImmediately)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>();
    if (!Subsystem)
    {
        return;
    }

    RegisterOwnerWithFastDis();

    const TArray<uint8> Packet = MakeEntityStatePacket(*this);
    const fastdis::PacketView View = fastdis::packet_view(Packet.GetData(), static_cast<size_t>(Packet.Num()));
    Subsystem->IngestPacketViews(&View, 1, true);

    if (bApplyImmediately)
    {
        Subsystem->ApplyLatestSnapshots();
    }
}
