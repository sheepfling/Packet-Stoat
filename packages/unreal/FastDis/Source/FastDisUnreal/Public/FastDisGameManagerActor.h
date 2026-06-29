#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FastDisTypes.h"
#include "FastDisGameManagerActor.generated.h"

class UFastDisEntityManagerComponent;
class UFastDisEntityMappingDataAsset;
class UFastDisEnumerationMappingAsset;
class UFastDisGeoreferenceAdapterComponent;
class UFastDisPduEventComponent;
class UFastDisReceiveFacadeComponent;
class UFastDisRuntimeMonitorComponent;
class UFastDisSendFacadeComponent;
class UFastDisUdpReceiverComponent;
class UFastDisUdpSenderComponent;
class USceneComponent;

/**
 * GRILL-shaped manager surface that bundles the common FastDIS runtime
 * components onto one level-facing actor.
 */
UCLASS(BlueprintType, Blueprintable)
class FASTDISUNREAL_API AFastDisGameManagerActor : public AActor
{
    GENERATED_BODY()

public:
    AFastDisGameManagerActor();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager", meta = (WorldContext = "WorldContextObject"))
    static AFastDisGameManagerActor* GetFastDisGameManager(UObject* WorldContextObject);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    void ApplyManagerSettings();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    void PullManagerSettingsFromComponents();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    bool StartLiveReceive();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    void StopLiveReceive();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager")
    bool IsLiveReceiveRunning() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    FFastDisRuntimeMonitorSnapshot RefreshMonitorSnapshot();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager")
    FFastDisRuntimeMonitorSnapshot GetLastMonitorSnapshot() const;

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager")
    int32 GetManagedEntityCount() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    bool AddManagedEntityToMap(const FFastDisEntityId& EntityId, AActor* Actor, bool bReplaceExisting = true);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    bool RemoveManagedEntityFromMap(const FFastDisEntityId& EntityId);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager")
    AActor* GetManagedEntityActor(const FFastDisEntityId& EntityId) const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Manager")
    void SetEnumerationMappingAsset(UFastDisEnumerationMappingAsset* MappingAsset);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Manager")
    UFastDisEnumerationMappingAsset* GetEnumerationMappingAsset() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisEntityMappingDataAsset> EntityMapping = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    int32 ExerciseId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    int32 SiteId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    int32 ApplicationId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    TSubclassOf<AActor> DefaultActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    EFastDisRemoveEntityPolicy RemoveEntityPolicy = EFastDisRemoveEntityPolicy::Destroy;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    FString ReceiveBindAddress = TEXT("0.0.0.0");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 ReceivePort = 3001;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager", meta = (ClampMin = "512"))
    int32 ReceiveBufferBytes = 1048576;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager", meta = (ClampMin = "1"))
    int32 MaxPacketsPerTick = 256;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    bool bAutoStartReceiver = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    bool bApplySnapshotsImmediately = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager")
    FString SendRemoteAddress = TEXT("127.0.0.1");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 SendRemotePort = 3001;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Networking")
    bool AutoConnectReceiveAddresses = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Networking", meta = (EditCondition = "AutoConnectReceiveAddresses"))
    TArray<FFastDisReceiveSocketInfo> ReceiveSocketsToSetup;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Networking")
    bool AutoConnectSendAddresses = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Networking", meta = (EditCondition = "AutoConnectSendAddresses"))
    TArray<FFastDisSendSocketInfo> SendSocketsToSetup;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisUdpReceiverComponent> Receiver;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisReceiveFacadeComponent> ReceiveFacade;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisUdpSenderComponent> Sender;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisSendFacadeComponent> SendFacade;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisPduEventComponent> PduEvents;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisEntityManagerComponent> EntityManager;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisGeoreferenceAdapterComponent> GeoreferenceAdapter;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS|Manager")
    TObjectPtr<UFastDisRuntimeMonitorComponent> RuntimeMonitor;
};
