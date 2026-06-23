#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisUdpSenderComponent.generated.h"

class FSocket;

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisUdpSenderComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisUdpSenderComponent();

    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|UDP")
    bool SendRawPduBytes(const TArray<uint8>& Packet);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|UDP")
    bool SendEntityState(const TArray<uint8>& Packet);

    UFUNCTION(BlueprintPure, Category = "FastDIS|UDP")
    FFastDisUdpStats GetStats() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    FString RemoteAddress = TEXT("127.0.0.1");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 RemotePort = 3001;

private:
    bool EnsureSocket();

private:
    FSocket* Socket = nullptr;
    FFastDisUdpStats Stats;
};
