#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "FastDisFabAssetLibrary.generated.h"

UCLASS()
class FASTDISUNREAL_API UFastDisFabAssetLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "FastDIS|Fab")
    static bool CreateExampleEntityMappingAsset(const FString& PackagePath);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Fab")
    static bool CreateEnumerationMappingAssetFromJson(const FString& PackagePath, const FString& JsonManifestPath);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Fab")
    static bool CreateGameManagerActorInEditorWorld(const FString& ActorLabel = TEXT("FastDIS Game Manager"), const FString& MappingAssetPath = TEXT(""));

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Fab")
    static bool CaptureExampleScenePng(const FString& OutputPath, int32 Width = 1280, int32 Height = 720);
};
