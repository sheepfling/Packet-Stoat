#include "Misc/AutomationTest.h"

#include "FastDisReplayActor.h"
#include "FastDisWorldSubsystem.h"

#include "Editor.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
FString ResolveReplayFile()
{
    FString ReplayPath = FPlatformMisc::GetEnvironmentVariable(TEXT("FASTDIS_UNREAL_REPLAY_FILE"));
    if (!ReplayPath.IsEmpty())
    {
        return ReplayPath;
    }
    return TEXT("");
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FFastDisUnrealReplaySmokeSpec,
    "FastDis.Demo.ReplayMovesActors",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FFastDisUnrealReplaySmokeSpec::RunTest(const FString& Parameters)
{
    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    if (!TestNotNull(TEXT("editor world"), World))
    {
        return false;
    }

    UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>();
    if (!TestNotNull(TEXT("FastDisWorldSubsystem"), Subsystem))
    {
        return false;
    }

    const FString ReplayPath = ResolveReplayFile();
    if (!TestFalse(TEXT("FASTDIS_UNREAL_REPLAY_FILE is configured"), ReplayPath.IsEmpty()))
    {
        return false;
    }
    if (!TestTrue(TEXT("replay file exists"), FPaths::FileExists(ReplayPath)))
    {
        return false;
    }

    FFastDisRuntimeSettings Settings;
    Settings.Georeference.LatitudeDegrees = 29.5597;
    Settings.Georeference.LongitudeDegrees = -95.0831;
    Settings.Georeference.HeightMeters = 0.0;
    Settings.Georeference.bApplyOrientation = false;
    Settings.TransformMode = EFastDisTransformMode::PositionOnly;
    Settings.SnapshotSlots = 3;
    Settings.StaleAfterTicks = 120;
    Settings.MetersToUnrealScale = 100.0;

    Subsystem->ConfigureRuntimeSettings(Settings);
    Subsystem->ClearRegisteredActors();

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.ObjectFlags |= RF_Transient;

    TArray<AActor*> SpawnedActors;
    SpawnedActors.Reserve(3);
    for (int32 Index = 0; Index < 3; ++Index)
    {
        AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, SpawnParameters);
        if (!TestNotNull(*FString::Printf(TEXT("spawned actor %d"), Index), Actor))
        {
            for (AActor* Spawned : SpawnedActors)
            {
                if (Spawned)
                {
                    Spawned->Destroy();
                }
            }
            return false;
        }
        USceneComponent* Root = NewObject<USceneComponent>(Actor);
        if (!TestNotNull(*FString::Printf(TEXT("root component %d"), Index), Root))
        {
            Actor->Destroy();
            for (AActor* Spawned : SpawnedActors)
            {
                if (Spawned)
                {
                    Spawned->Destroy();
                }
            }
            return false;
        }
        Actor->SetRootComponent(Root);
        Root->RegisterComponent();
        Actor->SetActorLocation(FVector(static_cast<double>(Index) * 100.0, 0.0, 0.0));
        SpawnedActors.Add(Actor);
    }

    AFastDisReplayActor* ReplayActor = World->SpawnActor<AFastDisReplayActor>(
        AFastDisReplayActor::StaticClass(),
        FTransform::Identity,
        SpawnParameters);
    if (!TestNotNull(TEXT("spawned replay actor"), ReplayActor))
    {
        for (AActor* Spawned : SpawnedActors)
        {
            if (Spawned)
            {
                Spawned->Destroy();
            }
        }
        return false;
    }

    ReplayActor->RuntimeSettings = Settings;
    ReplayActor->ReplayFile.FilePath = ReplayPath;
    ReplayActor->PacketsPerTick = 24;
    ReplayActor->bAutoLoadOnBeginPlay = false;
    ReplayActor->bAutoStartOnBeginPlay = false;
    ReplayActor->bLoopReplay = false;
    ReplayActor->bApplySnapshotsImmediately = true;
    ReplayActor->ActorBindings.Reset();
    for (int32 Index = 0; Index < SpawnedActors.Num(); ++Index)
    {
        FFastDisActorBinding Binding;
        Binding.EntityId = FFastDisEntityId(100, 1, static_cast<uint16>(Index));
        Binding.Actor = SpawnedActors[Index];
        ReplayActor->ActorBindings.Add(Binding);
    }

    ReplayActor->RegisterBindings();
    TestTrue(TEXT("replay file loaded"), ReplayActor->LoadReplayFile());
    TestTrue(TEXT("replay packet count"), ReplayActor->GetLoadedPacketCount() >= 24);

    TArray<FVector> InitialLocations;
    InitialLocations.Reserve(SpawnedActors.Num());
    for (AActor* Actor : SpawnedActors)
    {
        InitialLocations.Add(Actor->GetActorLocation());
    }

    ReplayActor->StartReplay();
    for (int32 TickIndex = 0; TickIndex < 4; ++TickIndex)
    {
        ReplayActor->Tick(1.0f / 60.0f);
    }

    TestTrue(TEXT("known entities populated"), Subsystem->GetKnownEntityCount() >= 3);
    for (int32 Index = 0; Index < SpawnedActors.Num(); ++Index)
    {
        const double Distance = FVector::Distance(InitialLocations[Index], SpawnedActors[Index]->GetActorLocation());
        TestTrue(*FString::Printf(TEXT("actor %d moved"), Index), Distance > 1.0);
    }

    ReplayActor->Destroy();
    for (AActor* Actor : SpawnedActors)
    {
        if (Actor)
        {
            Actor->Destroy();
        }
    }
    Subsystem->ClearRegisteredActors();
    return true;
}

#endif
