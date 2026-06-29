#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisSendFacadeComponent.generated.h"

class UFastDisUdpSenderComponent;

/**
 * GRILL-shaped send facade that keeps the level-facing destination settings
 * separate from the transport implementation.
 */
UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisSendFacadeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    void PullFromSender();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    void ApplyToSender();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    bool SendRawPduBytes(const TArray<uint8>& Packet);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Facade")
    bool SendEntityState(const TArray<uint8>& Packet);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Facade")
    FFastDisUdpStats GetStats() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    TObjectPtr<UFastDisUdpSenderComponent> Sender = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade")
    FString RemoteAddress = TEXT("127.0.0.1");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Facade", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 RemotePort = 3001;
};
