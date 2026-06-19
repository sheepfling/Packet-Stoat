#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "FastDisTypes.h"

#ifdef check
#pragma push_macro("check")
#undef check
#define FASTDIS_RESTORE_UE_CHECK_MACRO 1
#endif

#include "fastdis/fastdis.hpp"
#include "fastdis/fastdis_frames.hpp"

#ifdef FASTDIS_RESTORE_UE_CHECK_MACRO
#pragma pop_macro("check")
#undef FASTDIS_RESTORE_UE_CHECK_MACRO
#endif

#include "FastDisWorldSubsystem.generated.h"

/**
 * Minimal world subsystem scaffold that consumes fastdis double-buffer snapshots
 * and applies changed Entity State transforms to registered actors.
 *
 * This intentionally does not own UDP sockets. Feed it packet bytes from your
 * preferred Unreal networking layer, custom socket receiver, replay reader, or
 * simulation bridge.
 */
UCLASS()
class FASTDISUNREAL_API UFastDisWorldSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void ConfigureRuntimeSettings(const FFastDisRuntimeSettings& InSettings);

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void ConfigureGeoreference(const FFastDisGeoreference& InGeoreference);

    UFUNCTION(BlueprintPure, Category = "FastDIS")
    FFastDisRuntimeSettings GetRuntimeSettings() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void RegisterActor(const FFastDisEntityId& EntityId, AActor* Actor);

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void UnregisterActor(const FFastDisEntityId& EntityId);

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void ClearRegisteredActors();

    // Convenience path for packet copies owned by Unreal. For the highest-rate
    // path, build fastdis_packet_view_t arrays directly from your socket buffers
    // and call IngestPacketViews from C++.
    void IngestPacketCopies(TArrayView<const TArray<uint8>> Packets, bool bAdvanceTick = true);

    void IngestPacketViews(const fastdis::PacketView* Packets, int32 PacketCount, bool bAdvanceTick = true);

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void ApplyLatestSnapshots(float DeltaTime = 0.0f);

    UFUNCTION(BlueprintPure, Category = "FastDIS")
    int32 GetKnownEntityCount() const;

    static FTransform BuildDebugTransformForLocalAttitude(const FFastDisRuntimeSettings& InSettings,
                                                          double HeadingDegrees,
                                                          double PitchDegrees,
                                                          double RollDegrees,
                                                          bool& bOutApplyRotation);
    static FTransform BuildDebugTransformForDisOrientation(const FFastDisRuntimeSettings& InSettings,
                                                           double PsiDegrees,
                                                           double ThetaDegrees,
                                                           double PhiDegrees,
                                                           bool& bOutApplyRotation);

private:
    void BuildNativeState();
    void PublishStaleSnapshots();
    FTransform SnapshotToUnrealTransform(const fastdis::EntitySnapshot& Snapshot, bool& bOutApplyRotation) const;
    static FTransform SnapshotToUnrealTransform(const fastdis::frames::LocalEnuFrame& Frame,
                                                const FFastDisRuntimeSettings& InSettings,
                                                const fastdis::EntitySnapshot& Snapshot,
                                                bool& bOutApplyRotation);
    static FFastDisEntityId MakeUnrealId(const fastdis_entity_id_t& Id);

private:
    TUniquePtr<fastdis::Scanner> Scanner;
    TUniquePtr<fastdis::EntityTable> EntityTable;
    TUniquePtr<fastdis::SnapshotBuffer> SnapshotBuffer;
    TMap<FFastDisEntityId, TWeakObjectPtr<AActor>> RegisteredActors;

    FFastDisRuntimeSettings RuntimeSettings;
    fastdis::frames::LocalEnuFrame LocalFrame;
};
