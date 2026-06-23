#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisPduDebugMarkerComponent.generated.h"

class UFastDisPduEventComponent;
class UStaticMesh;

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisPduDebugMarkerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisPduDebugMarkerComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Debug")
    void BindOwnerPduEvents();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Debug")
    void ClearMarkers(bool bDestroyActors = true);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Debug")
    int32 GetMarkerCount() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Debug")
    void HandleFire(const FFastDisFireEvent& Event);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Debug")
    void HandleDetonation(const FFastDisDetonationEvent& Event);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Debug")
    void HandleDesignator(const FFastDisDesignatorEvent& Event);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    bool bAutoBind = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    TSubclassOf<AActor> MarkerActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    TObjectPtr<UStaticMesh> MarkerMesh = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    FVector MarkerScale = FVector(35.0, 35.0, 35.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    float MarkerLifetimeSeconds = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    FVector FireMarkerOffset = FVector(0.0, 0.0, 80.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    FVector DetonationMarkerOffset = FVector(0.0, 0.0, 130.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Debug")
    FVector DesignatorMarkerOffset = FVector(0.0, 0.0, 180.0);

private:
    void UnbindOwnerPduEvents();
    AActor* UpsertMarker(FName MarkerKey, FName MarkerTag, const FVector& DisWorldLocationMeters, const FVector& Offset);
    FVector EventLocationToUnreal(const FVector& DisWorldLocationMeters, const FVector& Offset) const;
    static FName EventKey(const TCHAR* Prefix, const FFastDisEntityId& PrimaryId, int32 EventNumber);

private:
    UPROPERTY(Transient)
    TObjectPtr<UFastDisPduEventComponent> BoundEvents = nullptr;

    TMap<FName, TWeakObjectPtr<AActor>> Markers;
    TMap<FName, double> MarkerExpirySeconds;
};
