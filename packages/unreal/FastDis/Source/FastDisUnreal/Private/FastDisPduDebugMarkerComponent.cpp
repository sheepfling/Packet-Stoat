#include "FastDisPduDebugMarkerComponent.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "FastDisPduEvents.h"
#include "FastDisWorldSubsystem.h"
#include "GameFramework/Actor.h"
#include "UObject/ConstructorHelpers.h"

UFastDisPduDebugMarkerComponent::UFastDisPduDebugMarkerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        MarkerMesh = SphereMesh.Object;
    }
}

void UFastDisPduDebugMarkerComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoBind)
    {
        BindOwnerPduEvents();
    }
}

void UFastDisPduDebugMarkerComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UnbindOwnerPduEvents();
    ClearMarkers(true);
    Super::EndPlay(EndPlayReason);
}

void UFastDisPduDebugMarkerComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (MarkerLifetimeSeconds <= 0.0f)
    {
        return;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    const double Now = World->GetTimeSeconds();
    TArray<FName> ExpiredKeys;
    for (const TPair<FName, double>& Pair : MarkerExpirySeconds)
    {
        if (Pair.Value <= Now)
        {
            ExpiredKeys.Add(Pair.Key);
        }
    }

    for (const FName& Key : ExpiredKeys)
    {
        if (TWeakObjectPtr<AActor>* Marker = Markers.Find(Key))
        {
            if (Marker->IsValid())
            {
                Marker->Get()->Destroy();
            }
        }
        Markers.Remove(Key);
        MarkerExpirySeconds.Remove(Key);
    }
}

void UFastDisPduDebugMarkerComponent::BindOwnerPduEvents()
{
    AActor* Owner = GetOwner();
    UFastDisPduEventComponent* Events = Owner ? Owner->FindComponentByClass<UFastDisPduEventComponent>() : nullptr;
    if (!Events)
    {
        return;
    }

    if (BoundEvents && BoundEvents != Events)
    {
        UnbindOwnerPduEvents();
    }

    BoundEvents = Events;
    BoundEvents->OnFireDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleFire);
    BoundEvents->OnDetonationDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDetonation);
    BoundEvents->OnDesignatorDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDesignator);
    BoundEvents->OnFireDecoded.AddDynamic(this, &UFastDisPduDebugMarkerComponent::HandleFire);
    BoundEvents->OnDetonationDecoded.AddDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDetonation);
    BoundEvents->OnDesignatorDecoded.AddDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDesignator);
}

void UFastDisPduDebugMarkerComponent::ClearMarkers(bool bDestroyActors)
{
    for (const TPair<FName, TWeakObjectPtr<AActor>>& Pair : Markers)
    {
        if (bDestroyActors && Pair.Value.IsValid())
        {
            Pair.Value->Destroy();
        }
    }
    Markers.Empty();
    MarkerExpirySeconds.Empty();
}

int32 UFastDisPduDebugMarkerComponent::GetMarkerCount() const
{
    int32 Count = 0;
    for (const TPair<FName, TWeakObjectPtr<AActor>>& Pair : Markers)
    {
        Count += Pair.Value.IsValid() ? 1 : 0;
    }
    return Count;
}

void UFastDisPduDebugMarkerComponent::HandleFire(const FFastDisFireEvent& Event)
{
    UpsertMarker(
        EventKey(TEXT("Fire"), Event.FiringEntityId, Event.EventNumber),
        TEXT("FastDIS.Fire"),
        Event.WorldLocationMeters,
        FireMarkerOffset);
}

void UFastDisPduDebugMarkerComponent::HandleDetonation(const FFastDisDetonationEvent& Event)
{
    UpsertMarker(
        EventKey(TEXT("Detonation"), Event.MunitionEntityId, Event.EventNumber),
        TEXT("FastDIS.Detonation"),
        Event.WorldLocationMeters,
        DetonationMarkerOffset);
}

void UFastDisPduDebugMarkerComponent::HandleDesignator(const FFastDisDesignatorEvent& Event)
{
    UpsertMarker(
        EventKey(TEXT("Designator"), Event.DesignatingEntityId, Event.DesignatorCode),
        TEXT("FastDIS.Designator"),
        Event.SpotLocationMeters,
        DesignatorMarkerOffset);
}

void UFastDisPduDebugMarkerComponent::UnbindOwnerPduEvents()
{
    if (!BoundEvents)
    {
        return;
    }

    BoundEvents->OnFireDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleFire);
    BoundEvents->OnDetonationDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDetonation);
    BoundEvents->OnDesignatorDecoded.RemoveDynamic(this, &UFastDisPduDebugMarkerComponent::HandleDesignator);
    BoundEvents = nullptr;
}

AActor* UFastDisPduDebugMarkerComponent::UpsertMarker(
    FName MarkerKey,
    FName MarkerTag,
    const FVector& DisWorldLocationMeters,
    const FVector& Offset)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    AActor* Marker = nullptr;
    if (TWeakObjectPtr<AActor>* Existing = Markers.Find(MarkerKey))
    {
        Marker = Existing->Get();
    }

    if (!Marker)
    {
        UClass* ActorClass = MarkerActorClass ? MarkerActorClass.Get() : AActor::StaticClass();
        FActorSpawnParameters SpawnParameters;
        SpawnParameters.ObjectFlags |= RF_Transient;
        Marker = World->SpawnActor<AActor>(ActorClass, FTransform::Identity, SpawnParameters);
        if (!Marker)
        {
            return nullptr;
        }

        if (MarkerMesh && !Marker->GetRootComponent())
        {
            UStaticMeshComponent* MeshComponent = NewObject<UStaticMeshComponent>(Marker);
            MeshComponent->SetStaticMesh(MarkerMesh);
            Marker->SetRootComponent(MeshComponent);
            MeshComponent->RegisterComponent();
        }

        Marker->Tags.AddUnique(TEXT("FastDIS.EventMarker"));
        Marker->Tags.AddUnique(MarkerTag);
        Markers.Add(MarkerKey, Marker);
    }

    Marker->SetActorLocation(EventLocationToUnreal(DisWorldLocationMeters, Offset));
    Marker->SetActorScale3D(MarkerScale);
    Marker->SetActorHiddenInGame(false);

    if (MarkerLifetimeSeconds > 0.0f)
    {
        MarkerExpirySeconds.Add(MarkerKey, World->GetTimeSeconds() + MarkerLifetimeSeconds);
    }
    return Marker;
}

FVector UFastDisPduDebugMarkerComponent::EventLocationToUnreal(const FVector& DisWorldLocationMeters, const FVector& Offset) const
{
    if (DisWorldLocationMeters.IsNearlyZero())
    {
        const AActor* Owner = GetOwner();
        return (Owner ? Owner->GetActorLocation() : FVector::ZeroVector) + Offset;
    }

    const UWorld* World = GetWorld();
    const UFastDisWorldSubsystem* Subsystem = World ? World->GetSubsystem<UFastDisWorldSubsystem>() : nullptr;
    return (Subsystem ? Subsystem->DisWorldLocationToUnreal(DisWorldLocationMeters) : DisWorldLocationMeters) + Offset;
}

FName UFastDisPduDebugMarkerComponent::EventKey(const TCHAR* Prefix, const FFastDisEntityId& PrimaryId, int32 EventNumber)
{
    return FName(*FString::Printf(
        TEXT("%s.%d.%d.%d.%d"),
        Prefix,
        PrimaryId.Site,
        PrimaryId.Application,
        PrimaryId.Entity,
        EventNumber));
}
