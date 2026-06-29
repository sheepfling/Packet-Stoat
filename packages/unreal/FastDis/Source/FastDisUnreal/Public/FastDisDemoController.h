#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FastDisTypes.h"
#include "FastDisDemoController.generated.h"

class UFastDisPduEventComponent;
class UFastDisPduDebugMarkerComponent;
class UFastDisGeoreferenceAdapterComponent;
class UFastDisRuntimeMonitorComponent;
class UFastDisSampleTrafficComponent;
class UFastDisUdpReceiverComponent;
class UFastDisUdpSenderComponent;
class USceneComponent;

UCLASS(BlueprintType, Blueprintable)
class FASTDISUNREAL_API AFastDisDemoController : public AActor
{
    GENERATED_BODY()

public:
    AFastDisDemoController();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Demo")
    bool StartLiveReceive();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Demo")
    void StopLiveReceive();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Demo")
    void InjectLocalEntityState(bool bApplyImmediately = true);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Demo")
    bool SendSampleEntityState();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Demo")
    FFastDisRuntimeMonitorSnapshot RefreshMonitorSnapshot();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Demo")
    FFastDisRuntimeMonitorSnapshot GetLastMonitorSnapshot() const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisUdpReceiverComponent> Receiver;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisUdpSenderComponent> Sender;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisPduEventComponent> PduEvents;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisPduDebugMarkerComponent> DebugMarkers;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisGeoreferenceAdapterComponent> GeoreferenceAdapter;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisRuntimeMonitorComponent> RuntimeMonitor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Demo")
    TObjectPtr<UFastDisSampleTrafficComponent> SampleTraffic;
};
