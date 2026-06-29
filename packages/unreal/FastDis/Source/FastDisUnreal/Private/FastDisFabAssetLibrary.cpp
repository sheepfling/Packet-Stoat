#include "FastDisFabAssetLibrary.h"

#include "FastDisEntityMappingDataAsset.h"
#include "FastDisEnumerationMappingAsset.h"
#include "FastDisGameManagerActor.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "ImageUtils.h"
#include "TextureResource.h"
#include "Engine/TextureRenderTarget2D.h"

#if WITH_EDITOR
#include "Editor.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "FileHelpers.h"
#include "HAL/FileManager.h"
#include "JsonObjectConverter.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "RenderingThread.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/BufferArchive.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#endif

#if WITH_EDITOR
namespace
{
bool TryReadEntityTypeField(const TSharedPtr<FJsonObject>& Object, const TCHAR* FieldName, int32& OutValue)
{
    if (!Object.IsValid())
    {
        return false;
    }

    double NumberValue = 0.0;
    if (!Object->TryGetNumberField(FieldName, NumberValue))
    {
        return false;
    }

    OutValue = static_cast<int32>(NumberValue);
    return true;
}

bool ReadEntityType(const TSharedPtr<FJsonObject>& Object, FFastDisEntityType& OutType)
{
    return TryReadEntityTypeField(Object, TEXT("Kind"), OutType.Kind) &&
           TryReadEntityTypeField(Object, TEXT("Domain"), OutType.Domain) &&
           TryReadEntityTypeField(Object, TEXT("Country"), OutType.Country) &&
           TryReadEntityTypeField(Object, TEXT("Category"), OutType.Category) &&
           TryReadEntityTypeField(Object, TEXT("Subcategory"), OutType.Subcategory) &&
           TryReadEntityTypeField(Object, TEXT("Specific"), OutType.Specific) &&
           TryReadEntityTypeField(Object, TEXT("Extra"), OutType.Extra);
}

bool ReadMappingRow(const TSharedPtr<FJsonObject>& Object, FFastDisEntityMappingRow& OutRow)
{
    if (!Object.IsValid())
    {
        return false;
    }

    FString DisplayName;
    if (!Object->TryGetStringField(TEXT("DisplayName"), DisplayName))
    {
        return false;
    }
    OutRow.DisplayName = FName(*DisplayName);

    FString ActorClassPath;
    Object->TryGetStringField(TEXT("ActorClassSoftPath"), ActorClassPath);
    if (!ActorClassPath.IsEmpty())
    {
        OutRow.ActorClassSoftPath = TSoftClassPtr<AActor>(FSoftObjectPath(ActorClassPath));
    }

    Object->TryGetStringField(TEXT("SourceActorClassPath"), OutRow.SourceActorClassPath);

    FString SourceRouteLabel;
    if (Object->TryGetStringField(TEXT("SourceRouteLabel"), SourceRouteLabel))
    {
        OutRow.SourceRouteLabel = FName(*SourceRouteLabel);
    }

    double NumberValue = 0.0;
    if (Object->TryGetNumberField(TEXT("Priority"), NumberValue))
    {
        OutRow.Priority = static_cast<int32>(NumberValue);
    }
    if (Object->TryGetNumberField(TEXT("SourceRowIndex"), NumberValue))
    {
        OutRow.SourceRowIndex = static_cast<int32>(NumberValue);
    }

    const TSharedPtr<FJsonObject>* EntityTypeObject = nullptr;
    if (!Object->TryGetObjectField(TEXT("EntityType"), EntityTypeObject) || !ReadEntityType(*EntityTypeObject, OutRow.EntityType))
    {
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* AliasValues = nullptr;
    if (Object->TryGetArrayField(TEXT("AliasEntityTypes"), AliasValues))
    {
        for (const TSharedPtr<FJsonValue>& AliasValue : *AliasValues)
        {
            const TSharedPtr<FJsonObject> AliasObject = AliasValue.IsValid() ? AliasValue->AsObject() : nullptr;
            FFastDisEntityType AliasType;
            if (!ReadEntityType(AliasObject, AliasType))
            {
                return false;
            }
            OutRow.AliasEntityTypes.Add(AliasType);
        }
    }

    return true;
}
}
#endif

bool UFastDisFabAssetLibrary::CreateExampleEntityMappingAsset(const FString& PackagePath)
{
#if WITH_EDITOR
    if (PackagePath.IsEmpty() || !FPackageName::IsValidLongPackageName(PackagePath))
    {
        return false;
    }

    UPackage* Package = CreatePackage(*PackagePath);
    if (Package == nullptr)
    {
        return false;
    }

    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    UFastDisEntityMappingDataAsset* Asset = FindObject<UFastDisEntityMappingDataAsset>(Package, *AssetName);
    if (Asset == nullptr)
    {
        Asset = NewObject<UFastDisEntityMappingDataAsset>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
    }
    if (Asset == nullptr)
    {
        return false;
    }

    Asset->Rows.Reset();

    FFastDisEntityMappingRow ExactAircraft;
    ExactAircraft.EntityType.Kind = 1;
    ExactAircraft.EntityType.Domain = 2;
    ExactAircraft.EntityType.Country = 225;
    ExactAircraft.EntityType.Category = 1;
    ExactAircraft.EntityType.Subcategory = 1;
    ExactAircraft.EntityType.Specific = 3;
    ExactAircraft.EntityType.Extra = 0;
    ExactAircraft.ActorClass = AActor::StaticClass();
    ExactAircraft.DisplayName = TEXT("Demo Friendly Aircraft Exact");
    ExactAircraft.Scale = 1.0f;
    ExactAircraft.Priority = 20;
    FFastDisEntityType ExactAlias;
    ExactAlias.Kind = 1;
    ExactAlias.Domain = 2;
    ExactAlias.Country = 225;
    ExactAlias.Category = 1;
    ExactAlias.Subcategory = 1;
    ExactAlias.Specific = 4;
    ExactAlias.Extra = 0;
    ExactAircraft.AliasEntityTypes.Add(ExactAlias);
    Asset->Rows.Add(ExactAircraft);

    FFastDisEntityMappingRow AirPlatformFallback;
    AirPlatformFallback.EntityType.Kind = 1;
    AirPlatformFallback.EntityType.Domain = 2;
    AirPlatformFallback.ActorClass = AActor::StaticClass();
    AirPlatformFallback.DisplayName = TEXT("Demo Air Platform Fallback");
    AirPlatformFallback.Scale = 1.0f;
    AirPlatformFallback.Priority = 10;
    Asset->Rows.Add(AirPlatformFallback);

    FFastDisEntityMappingRow GenericPlatformFallback;
    GenericPlatformFallback.EntityType.Kind = 1;
    GenericPlatformFallback.ActorClass = AActor::StaticClass();
    GenericPlatformFallback.DisplayName = TEXT("Demo Platform Fallback");
    GenericPlatformFallback.Scale = 1.0f;
    GenericPlatformFallback.Priority = 0;
    Asset->Rows.Add(GenericPlatformFallback);

    Asset->MarkPackageDirty();
    Package->MarkPackageDirty();

    const FString FileName = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_None;
    return UPackage::SavePackage(Package, Asset, *FileName, SaveArgs);
#else
    return false;
#endif
}

bool UFastDisFabAssetLibrary::CreateEnumerationMappingAssetFromJson(const FString& PackagePath, const FString& JsonManifestPath)
{
#if WITH_EDITOR
    if (PackagePath.IsEmpty() || !FPackageName::IsValidLongPackageName(PackagePath) || JsonManifestPath.IsEmpty())
    {
        return false;
    }

    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *JsonManifestPath))
    {
        return false;
    }

    TSharedPtr<FJsonObject> RootObject;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
    {
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* RowValues = nullptr;
    if (!RootObject->TryGetArrayField(TEXT("rows"), RowValues) || RowValues == nullptr)
    {
        return false;
    }

    UPackage* Package = CreatePackage(*PackagePath);
    if (Package == nullptr)
    {
        return false;
    }

    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    UFastDisEnumerationMappingAsset* Asset = FindObject<UFastDisEnumerationMappingAsset>(Package, *AssetName);
    if (Asset == nullptr)
    {
        Asset = NewObject<UFastDisEnumerationMappingAsset>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
    }
    if (Asset == nullptr)
    {
        return false;
    }

    Asset->Rows.Reset();
    Asset->SourceManifestPath = JsonManifestPath;
    Asset->SourceRouteLabel = TEXT("FastDIS");

    for (const TSharedPtr<FJsonValue>& RowValue : *RowValues)
    {
        const TSharedPtr<FJsonObject> RowObject = RowValue.IsValid() ? RowValue->AsObject() : nullptr;
        FFastDisEntityMappingRow Row;
        if (!ReadMappingRow(RowObject, Row))
        {
            return false;
        }

        if (!Row.SourceRouteLabel.IsNone())
        {
            Asset->SourceRouteLabel = Row.SourceRouteLabel;
        }
        Asset->Rows.Add(Row);
    }

    Asset->MarkPackageDirty();
    Package->MarkPackageDirty();

    const FString FileName = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_None;
    return UPackage::SavePackage(Package, Asset, *FileName, SaveArgs);
#else
    return false;
#endif
}

bool UFastDisFabAssetLibrary::CreateGameManagerActorInEditorWorld(const FString& ActorLabel, const FString& MappingAssetPath)
{
#if WITH_EDITOR
    if (GEditor == nullptr)
    {
        return false;
    }

    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (World == nullptr)
    {
        return false;
    }

    AFastDisGameManagerActor* Manager = World->SpawnActor<AFastDisGameManagerActor>(
        AFastDisGameManagerActor::StaticClass(),
        FTransform::Identity);
    if (Manager == nullptr)
    {
        return false;
    }

    const FString Label = ActorLabel.IsEmpty() ? TEXT("FastDIS Game Manager") : ActorLabel;
    Manager->SetActorLabel(Label);

    if (!MappingAssetPath.IsEmpty())
    {
        UFastDisEnumerationMappingAsset* MappingAsset = LoadObject<UFastDisEnumerationMappingAsset>(nullptr, *MappingAssetPath);
        if (MappingAsset == nullptr)
        {
            Manager->Destroy();
            return false;
        }

        Manager->SetEnumerationMappingAsset(MappingAsset);
    }
    else
    {
        Manager->ApplyManagerSettings();
    }

    return true;
#else
    return false;
#endif
}

bool UFastDisFabAssetLibrary::CaptureExampleScenePng(const FString& OutputPath, int32 Width, int32 Height)
{
#if WITH_EDITOR
    if (OutputPath.IsEmpty() || Width <= 0 || Height <= 0 || GEditor == nullptr)
    {
        return false;
    }

    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (World == nullptr)
    {
        return false;
    }

    IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutputPath), true);

    UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>(GetTransientPackage());
    if (RenderTarget == nullptr)
    {
        return false;
    }
    RenderTarget->RenderTargetFormat = RTF_RGBA8;
    RenderTarget->ClearColor = FLinearColor(0.02f, 0.025f, 0.03f, 1.0f);
    RenderTarget->InitAutoFormat(Width, Height);
    RenderTarget->UpdateResourceImmediate(true);

    AActor* CaptureActor = World->SpawnActor<AActor>();
    if (CaptureActor == nullptr)
    {
        return false;
    }
    CaptureActor->SetActorLabel(TEXT("FastDIS Fab RenderTarget Capture"));
    CaptureActor->SetActorLocation(FVector(-520.0, 0.0, 220.0));
    CaptureActor->SetActorRotation(FRotator(-4.0, 0.0, 0.0));

    USceneCaptureComponent2D* Capture = NewObject<USceneCaptureComponent2D>(CaptureActor);
    if (Capture == nullptr)
    {
        CaptureActor->Destroy();
        return false;
    }
    Capture->RegisterComponent();
    CaptureActor->AddInstanceComponent(Capture);
    Capture->TextureTarget = RenderTarget;
    Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
    Capture->FOVAngle = 60.0f;
    Capture->bCaptureEveryFrame = false;
    Capture->bCaptureOnMovement = false;
    Capture->SetWorldLocation(CaptureActor->GetActorLocation());
    Capture->SetWorldRotation(CaptureActor->GetActorRotation());

    Capture->CaptureScene();
    FlushRenderingCommands();

    FBufferArchive Buffer;
    const bool bExported = FImageUtils::ExportRenderTarget2DAsPNG(RenderTarget, Buffer);
    const bool bSaved = bExported && FFileHelper::SaveArrayToFile(Buffer, *OutputPath);

    CaptureActor->Destroy();
    return bSaved;
#else
    return false;
#endif
}
