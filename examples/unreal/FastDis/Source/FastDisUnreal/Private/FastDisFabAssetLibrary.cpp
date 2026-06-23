#include "FastDisFabAssetLibrary.h"

#include "FastDisEntityMappingDataAsset.h"
#include "Components/SceneCaptureComponent2D.h"
#include "GameFramework/Actor.h"
#include "ImageUtils.h"
#include "TextureResource.h"
#include "Engine/TextureRenderTarget2D.h"

#if WITH_EDITOR
#include "Editor.h"
#include "FileHelpers.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "RenderingThread.h"
#include "Serialization/BufferArchive.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
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
    Asset->Rows.Add(ExactAircraft);

    FFastDisEntityMappingRow AirPlatformFallback;
    AirPlatformFallback.EntityType.Kind = 1;
    AirPlatformFallback.EntityType.Domain = 2;
    AirPlatformFallback.ActorClass = AActor::StaticClass();
    AirPlatformFallback.DisplayName = TEXT("Demo Air Platform Fallback");
    AirPlatformFallback.Scale = 1.0f;
    Asset->Rows.Add(AirPlatformFallback);

    FFastDisEntityMappingRow GenericPlatformFallback;
    GenericPlatformFallback.EntityType.Kind = 1;
    GenericPlatformFallback.ActorClass = AActor::StaticClass();
    GenericPlatformFallback.DisplayName = TEXT("Demo Platform Fallback");
    GenericPlatformFallback.Scale = 1.0f;
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
