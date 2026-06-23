#pragma once

#include "Components/ActorComponent.h"
#include "FastDisPduEvents.h"
#include "FastDisTypes.h"
#include "FastDisRuntimeMonitorComponent.generated.h"

class UFastDisUdpReceiverComponent;
class UFastDisUdpSenderComponent;

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisRuntimeMonitorComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisRuntimeMonitorComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    void BindOwnerFastDisComponents();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    FFastDisRuntimeMonitorSnapshot RefreshSnapshot();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Monitor")
    FFastDisRuntimeMonitorSnapshot GetLastSnapshot() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    void ResetEventCounters();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    bool bAutoBindOwnerComponents = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    TObjectPtr<UFastDisUdpReceiverComponent> Receiver = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    TObjectPtr<UFastDisUdpSenderComponent> Sender = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    TObjectPtr<UFastDisPduEventComponent> PduEvents = nullptr;

private:
    UFUNCTION()
    void HandlePduReceived(const FFastDisPduEvent& Event);

    UFUNCTION()
    void HandleMalformedPdu(const FFastDisPduEvent& Event);

private:
    FFastDisRuntimeMonitorSnapshot LastSnapshot;
};
