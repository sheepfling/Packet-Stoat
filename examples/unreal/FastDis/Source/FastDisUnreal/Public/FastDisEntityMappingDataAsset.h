#pragma once

#include "Engine/DataAsset.h"
#include "FastDisTypes.h"
#include "FastDisEntityMappingDataAsset.generated.h"

class AActor;

USTRUCT(BlueprintType)
struct FFastDisEntityMappingRow
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FFastDisEntityType EntityType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    TSubclassOf<AActor> ActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FName DisplayName = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    float Scale = 1.0f;
};

UCLASS(BlueprintType)
class FASTDISUNREAL_API UFastDisEntityMappingDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity Mapping")
    TSubclassOf<AActor> ResolveActorClass(const FFastDisEntityType& EntityType, TSubclassOf<AActor> FallbackClass) const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    TArray<FFastDisEntityMappingRow> Rows;
};
