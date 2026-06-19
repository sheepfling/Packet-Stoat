#include "FastDisWorldSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"

namespace
{
int32 SanitizedSnapshotSlots(int32 RequestedSlots)
{
    return FMath::Max(2, RequestedSlots);
}
}

void UFastDisWorldSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    BuildNativeState();
    ConfigureRuntimeSettings(RuntimeSettings);
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
    PublishStaleSnapshots();
    ApplyLatestSnapshots(DeltaTime);
}

TStatId UFastDisWorldSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UFastDisWorldSubsystem, STATGROUP_Tickables);
}

void UFastDisWorldSubsystem::ConfigureRuntimeSettings(const FFastDisRuntimeSettings& InSettings)
{
    const int32 PreviousSlots = SanitizedSnapshotSlots(RuntimeSettings.SnapshotSlots);
    RuntimeSettings = InSettings;
    RuntimeSettings.SnapshotSlots = SanitizedSnapshotSlots(RuntimeSettings.SnapshotSlots);
    RuntimeSettings.MetersToUnrealScale = FMath::Max(1.0, RuntimeSettings.MetersToUnrealScale);
    RuntimeSettings.InterpolationSpeed = FMath::Max(0.01f, RuntimeSettings.InterpolationSpeed);
    RuntimeSettings.StaleAfterTicks = FMath::Max(0, RuntimeSettings.StaleAfterTicks);

    if (!SnapshotBuffer || PreviousSlots != RuntimeSettings.SnapshotSlots)
    {
        SnapshotBuffer = MakeUnique<fastdis::SnapshotBuffer>(4096, static_cast<size_t>(RuntimeSettings.SnapshotSlots));
    }

    LocalFrame = fastdis::frames::LocalEnuFrame::from_degrees(
        RuntimeSettings.Georeference.LatitudeDegrees,
        RuntimeSettings.Georeference.LongitudeDegrees,
        RuntimeSettings.Georeference.HeightMeters);
}

void UFastDisWorldSubsystem::ConfigureGeoreference(const FFastDisGeoreference& InGeoreference)
{
    FFastDisRuntimeSettings UpdatedSettings = RuntimeSettings;
    UpdatedSettings.Georeference = InGeoreference;
    ConfigureRuntimeSettings(UpdatedSettings);
}

FFastDisRuntimeSettings UFastDisWorldSubsystem::GetRuntimeSettings() const
{
    return RuntimeSettings;
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

void UFastDisWorldSubsystem::ApplyLatestSnapshots(float DeltaTime)
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
        const FVector TargetLocation = Transform.GetLocation();
        const FQuat TargetRotation = Transform.GetRotation();

        switch (RuntimeSettings.TransformMode)
        {
        case EFastDisTransformMode::InterpolatePosition:
        {
            const FVector NextLocation = FMath::VInterpTo(
                Actor->GetActorLocation(),
                TargetLocation,
                DeltaTime,
                RuntimeSettings.InterpolationSpeed);
            Actor->SetActorLocation(NextLocation, false, nullptr, ETeleportType::TeleportPhysics);
            break;
        }
        case EFastDisTransformMode::SnapPositionAndExperimentalRotation:
            if (bApplyRotation)
            {
                Actor->SetActorTransform(FTransform(TargetRotation, TargetLocation, FVector::OneVector),
                                         false,
                                         nullptr,
                                         ETeleportType::TeleportPhysics);
                break;
            }
            [[fallthrough]];
        case EFastDisTransformMode::SnapPosition:
        case EFastDisTransformMode::PositionOnly:
        default:
            Actor->SetActorLocation(TargetLocation, false, nullptr, ETeleportType::TeleportPhysics);
            break;
        }
    }
}

int32 UFastDisWorldSubsystem::GetKnownEntityCount() const
{
    return EntityTable ? static_cast<int32>(EntityTable->size()) : 0;
}

void UFastDisWorldSubsystem::BuildNativeState()
{
    Scanner = MakeUnique<fastdis::Scanner>(
        fastdis::ScannerBuilder()
            .entity_transform_profile()
            .versions({6, 7})
            .pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
            .protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY})
            .build());
    EntityTable = MakeUnique<fastdis::EntityTable>(
        fastdis::EntityTableConfig()
            .reserve(4096)
            .build());
    SnapshotBuffer = MakeUnique<fastdis::SnapshotBuffer>(4096, static_cast<size_t>(SanitizedSnapshotSlots(RuntimeSettings.SnapshotSlots)));
}

void UFastDisWorldSubsystem::PublishStaleSnapshots()
{
    if (!SnapshotBuffer || !EntityTable || RuntimeSettings.StaleAfterTicks <= 0)
    {
        return;
    }

    const fastdis::Status Status = SnapshotBuffer->try_publish_evict_stale(
        *EntityTable,
        static_cast<uint64>(RuntimeSettings.StaleAfterTicks),
        nullptr);
    if (Status != FASTDIS_OK && Status != FASTDIS_ERR_BUSY && Status != FASTDIS_ERR_NOT_FOUND)
    {
        UE_LOG(LogTemp, Warning, TEXT("fastdis publish stale failed: %s"), ANSI_TO_TCHAR(fastdis::status_string(Status)));
    }
}

FTransform UFastDisWorldSubsystem::SnapshotToUnrealTransform(const fastdis::EntitySnapshot& Snapshot, bool& bOutApplyRotation) const
{
    const fastdis::frames::OrientationPolicy Policy = RuntimeSettings.Georeference.bApplyOrientation
        ? fastdis::frames::OrientationPolicy::ExperimentalLocalYawPitchRoll
        : fastdis::frames::OrientationPolicy::PositionOnly;

    const fastdis::frames::UnrealPoseData Pose = fastdis::frames::to_unreal_pose(LocalFrame, Snapshot, Policy);
    const double ScaleFactor = RuntimeSettings.MetersToUnrealScale / 100.0;
    const FVector Location(Pose.x_cm * ScaleFactor, Pose.y_cm * ScaleFactor, Pose.z_cm * ScaleFactor);

    bOutApplyRotation = RuntimeSettings.Georeference.bApplyOrientation;
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
