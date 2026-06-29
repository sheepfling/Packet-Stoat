#pragma once

#include "FastDisEntityMappingDataAsset.h"
#include "FastDisEnumerationMappingAsset.generated.h"

/**
 * GRILL-shaped authoring surface for enumeration-to-actor mappings.
 *
 * This keeps the FastDIS runtime/backend unchanged while giving migration and
 * level-authoring workflows a more familiar asset name.
 */
UCLASS(BlueprintType)
class FASTDISUNREAL_API UFastDisEnumerationMappingAsset : public UFastDisEntityMappingDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FName SourceRouteLabel = TEXT("FastDIS");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity Mapping")
    FString SourceManifestPath;
};
