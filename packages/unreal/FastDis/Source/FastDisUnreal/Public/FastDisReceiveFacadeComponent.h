#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisReceiveFacadeComponent.generated.h"

class UFastDisUdpReceiverComponent;

/**
 * GRILL-shaped receive facade that mirrors the level-facing UDP settings while
 * delegating transport work to the shared FastDIS receiver component.
 */
UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisReceiveFacadeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    void PullFromReceiver();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    void ApplyToReceiver();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    bool Start();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    void Stop();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Facade")
    bool IsRunning() const;

    UFUNCTION(BlueprintPure, Category = "FastDIS|Facade")
    FFastDisUdpStats GetStats() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    TObjectPtr<UFastDisUdpReceiverComponent> Receiver = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    FString BindAddress = TEXT("0.0.0.0");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 Port = 3001;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade", meta = (ClampMin = "512"))
    int32 ReceiveBufferBytes = 1048576;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade", meta = (ClampMin = "1"))
    int32 MaxPacketsPerTick = 256;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    bool bAutoStart = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    bool bApplySnapshotsImmediately = true;
};
