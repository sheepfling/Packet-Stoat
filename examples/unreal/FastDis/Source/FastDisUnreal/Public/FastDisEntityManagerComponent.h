#pragma once

#include "Components/ActorComponent.h"
#include "FastDisEntityMappingDataAsset.h"
#include "FastDisTypes.h"
#include "FastDisEntityManagerComponent.generated.h"

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisEntityManagerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisEntityManagerComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity")
    void RegisterWithWorldSubsystem();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity")
    void ClearManagedEntities(bool bDestroyActors = true);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Entity")
    int32 GetManagedEntityCount() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity")
    bool RegisterManagedActor(const FFastDisEntityId& EntityId, AActor* Actor, bool bReplaceExisting = true);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity")
    void UnregisterManagedActor(const FFastDisEntityId& EntityId);

    UFUNCTION(BlueprintPure, Category = "FastDIS|Entity")
    AActor* GetManagedActor(const FFastDisEntityId& EntityId) const;

    UFUNCTION(BlueprintPure, Category = "FastDIS|Entity")
    bool IsManagedActorRegistered(const FFastDisEntityId& EntityId) const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity")
    void ApplyRemoveEntityEvent(const FFastDisRemoveEntityEvent& Event);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    TObjectPtr<UFastDisEntityMappingDataAsset> EntityMapping = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    TSubclassOf<AActor> DefaultActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    EFastDisRemoveEntityPolicy RemoveEntityPolicy = EFastDisRemoveEntityPolicy::Destroy;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    bool bAutoRegister = true;

private:
    UFUNCTION()
    void HandleEntityUpdated(const FFastDisEntityTransformEvent& Event);

    UFUNCTION()
    void HandleRemoveEntity(const FFastDisRemoveEntityEvent& Event);

    UFUNCTION()
    void HandleManagedActorDestroyed(AActor* DestroyedActor);

private:
    TMap<FFastDisEntityId, TWeakObjectPtr<AActor>> ManagedActors;
};
