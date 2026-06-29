#pragma once

#include "Components/ActorComponent.h"
#include "FastDisPduEvents.h"
#include "FastDisTypes.h"
#include "FastDisUdpReceiverComponent.generated.h"

class FSocket;

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisUdpReceiverComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisUdpReceiverComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|UDP")
    bool StartReceiver();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|UDP")
    void StopReceiver();

    UFUNCTION(BlueprintPure, Category = "FastDIS|UDP")
    bool IsReceiverRunning() const;

    UFUNCTION(BlueprintPure, Category = "FastDIS|UDP")
    FFastDisUdpStats GetStats() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    FString BindAddress = TEXT("0.0.0.0");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 Port = 3001;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP", meta = (ClampMin = "512"))
    int32 ReceiveBufferBytes = 1048576;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP", meta = (ClampMin = "1"))
    int32 MaxPacketsPerTick = 256;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    bool bAutoStart = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    bool bApplySnapshotsImmediately = true;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|UDP")
    FFastDisPduEventSignature OnPduReceived;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|UDP")
    FFastDisPduEventSignature OnMalformedPdu;

private:
    void PumpSocket(float DeltaTime);

private:
    FSocket* Socket = nullptr;
    FFastDisUdpStats Stats;
};
