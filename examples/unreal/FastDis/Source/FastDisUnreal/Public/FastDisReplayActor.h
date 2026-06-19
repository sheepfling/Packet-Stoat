#pragma once

#include "CoreMinimal.h"
#include "Misc/FilePath.h"
#include "FastDisTypes.h"
#include "GameFramework/Actor.h"
#include "FastDisReplayActor.generated.h"

UCLASS(BlueprintType, Blueprintable)
class FASTDISUNREAL_API AFastDisReplayActor : public AActor
{
    GENERATED_BODY()

public:
    AFastDisReplayActor();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaTime) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    bool LoadReplayFile();

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void StartReplay();

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void StopReplay();

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void ResetReplay();

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void RegisterBindings();

    UFUNCTION(BlueprintPure, Category = "FastDIS")
    int32 GetLoadedPacketCount() const;

private:
    bool LoadReplayFileInternal();
    void RegisterBindingsWithSubsystem() const;

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FFastDisRuntimeSettings RuntimeSettings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    TArray<FFastDisActorBinding> ActorBindings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay", meta = (RelativeToGameContentDir))
    FFilePath ReplayFile;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay", meta = (ClampMin = "1", UIMin = "1"))
    int32 PacketsPerTick = 64;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay")
    bool bAutoLoadOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay")
    bool bAutoStartOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay")
    bool bLoopReplay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Replay")
    bool bApplySnapshotsImmediately = true;

private:
    TArray<TArray<uint8>> ReplayPackets;
    int32 NextPacketIndex = 0;
    bool bReplayActive = false;
};
