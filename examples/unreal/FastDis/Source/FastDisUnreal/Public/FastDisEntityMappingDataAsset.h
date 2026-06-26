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
    TArray<FFastDisEntityType> AliasEntityTypes;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    TSubclassOf<AActor> ActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    TSoftClassPtr<AActor> ActorClassSoftPath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FName DisplayName = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    float Scale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    int32 Priority = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FName SourceRouteLabel = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FString SourceActorClassPath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    int32 SourceRowIndex = -1;
};

UCLASS(BlueprintType)
class FASTDISUNREAL_API UFastDisEntityMappingDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "FastDIS|Entity Mapping")
    TSubclassOf<AActor> ResolveActorClass(const FFastDisEntityType& EntityType, TSubclassOf<AActor> FallbackClass) const;

    bool ResolveRow(const FFastDisEntityType& EntityType, FFastDisEntityMappingRow& OutRow) const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    TArray<FFastDisEntityMappingRow> Rows;
};
