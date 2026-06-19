#include "FastDisWorldSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"

void UFastDisWorldSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    fastdis::ScanConfig Config = fastdis::ScanConfig::entity_transform();
    Config.only_versions({6, 7})
          .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
          .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY});

    Scanner = MakeUnique<fastdis::Scanner>(Config);
    EntityTable = MakeUnique<fastdis::EntityTable>(4096);
    SnapshotBuffer = MakeUnique<fastdis::SnapshotBuffer>(4096);
    ConfigureGeoreference(Georeference);
}

void UFastDisWorldSubsystem::Deinitialize()
{
    RegisteredActors.Empty();
    SnapshotBuffer.Reset();
    EntityTable.Reset();
    Scanner.Reset();
    Super::Deinitialize();
}

void UFastDisWorldSubsystem::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    ApplyLatestSnapshots();
}

TStatId UFastDisWorldSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UFastDisWorldSubsystem, STATGROUP_Tickables);
}

void UFastDisWorldSubsystem::ConfigureGeoreference(const FFastDisGeoreference& InGeoreference)
{
    Georeference = InGeoreference;
    LocalFrame = fastdis::frames::LocalEnuFrame::from_degrees(
        Georeference.LatitudeDegrees,
        Georeference.LongitudeDegrees,
        Georeference.HeightMeters);
}

void UFastDisWorldSubsystem::RegisterActor(const FFastDisEntityId& EntityId, AActor* Actor)
{
    if (Actor)
    {
        RegisteredActors.Add(EntityId, Actor);
    }
}

void UFastDisWorldSubsystem::UnregisterActor(const FFastDisEntityId& EntityId)
{
    RegisteredActors.Remove(EntityId);
}

void UFastDisWorldSubsystem::ClearRegisteredActors()
{
    RegisteredActors.Empty();
}

void UFastDisWorldSubsystem::IngestPacketCopies(TArrayView<const TArray<uint8>> Packets, bool bAdvanceTick)
{
    fastdis::PacketViews Views(static_cast<size_t>(Packets.Num()));
    for (const TArray<uint8>& Packet : Packets)
    {
        Views.add(Packet.GetData(), static_cast<size_t>(Packet.Num()));
    }
    IngestPacketViews(Views.data(), static_cast<int32>(Views.size()), bAdvanceTick);
}

void UFastDisWorldSubsystem::IngestPacketViews(const fastdis::PacketView* Packets, int32 PacketCount, bool bAdvanceTick)
{
    if (!Scanner || !EntityTable || !SnapshotBuffer || PacketCount <= 0)
    {
        return;
    }

    fastdis::EntityTableUpdateStats Stats{};
    fastdis_entity_table_update_stats_init(&Stats);

    fastdis::SnapshotView Published;
    const fastdis::Status Status = SnapshotBuffer->try_ingest_and_publish_changed(
        *EntityTable,
        *Scanner,
        Packets,
        static_cast<size_t>(PacketCount),
        bAdvanceTick,
        true,
        &Stats,
        &Published);

    // FASTDIS_ERR_BUSY means a reader still holds both double-buffer slots.
    // Do not block the network path; the next frame/burst can publish again.
    if (Status != FASTDIS_OK && Status != FASTDIS_ERR_BUSY)
    {
        UE_LOG(LogTemp, Warning, TEXT("fastdis ingest/publish failed: %s"), ANSI_TO_TCHAR(fastdis::status_string(Status)));
    }
}

void UFastDisWorldSubsystem::ApplyLatestSnapshots()
{
    if (!SnapshotBuffer)
    {
        return;
    }

    fastdis::ScopedSnapshotView View;
    const fastdis::Status Status = SnapshotBuffer->try_acquire_latest(&View);
    if (Status != FASTDIS_OK)
    {
        return;
    }

    for (const fastdis::EntitySnapshot& Snapshot : View)
    {
        const FFastDisEntityId Key = MakeUnrealId(Snapshot.transform.entity_id);
        TWeakObjectPtr<AActor>* ActorPtr = RegisteredActors.Find(Key);
        if (!ActorPtr || !ActorPtr->IsValid())
        {
            continue;
        }

        bool bApplyRotation = false;
        const FTransform Transform = SnapshotToUnrealTransform(Snapshot, bApplyRotation);
        AActor* Actor = ActorPtr->Get();
        if (bApplyRotation)
        {
            Actor->SetActorTransform(Transform, false, nullptr, ETeleportType::TeleportPhysics);
        }
        else
        {
            Actor->SetActorLocation(Transform.GetLocation(), false, nullptr, ETeleportType::TeleportPhysics);
        }
    }
}

int32 UFastDisWorldSubsystem::GetKnownEntityCount() const
{
    return EntityTable ? static_cast<int32>(EntityTable->size()) : 0;
}

FTransform UFastDisWorldSubsystem::SnapshotToUnrealTransform(const fastdis::EntitySnapshot& Snapshot, bool& bOutApplyRotation) const
{
    const fastdis::frames::OrientationPolicy Policy = Georeference.bApplyOrientation
        ? fastdis::frames::OrientationPolicy::ExperimentalLocalYawPitchRoll
        : fastdis::frames::OrientationPolicy::PositionOnly;

    const fastdis::frames::UnrealPoseData Pose = fastdis::frames::to_unreal_pose(LocalFrame, Snapshot, Policy);
    const FVector Location(Pose.x_cm, Pose.y_cm, Pose.z_cm);

    bOutApplyRotation = Georeference.bApplyOrientation;
    if (bOutApplyRotation)
    {
        const FQuat Rotation(Pose.rotation.x, Pose.rotation.y, Pose.rotation.z, Pose.rotation.w);
        return FTransform(Rotation, Location, FVector::OneVector);
    }

    return FTransform(FQuat::Identity, Location, FVector::OneVector);
}

FFastDisEntityId UFastDisWorldSubsystem::MakeUnrealId(const fastdis_entity_id_t& Id)
{
    return FFastDisEntityId(Id.site, Id.application, Id.entity);
}
