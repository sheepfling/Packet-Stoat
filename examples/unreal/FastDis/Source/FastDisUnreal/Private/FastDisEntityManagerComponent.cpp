#include "FastDisEntityManagerComponent.h"

#include "Engine/World.h"
#include "FastDisPduEvents.h"
#include "FastDisWorldSubsystem.h"
#include "GameFramework/Actor.h"

UFastDisEntityManagerComponent::UFastDisEntityManagerComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UFastDisEntityManagerComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoRegister)
    {
        RegisterWithWorldSubsystem();
    }
}

void UFastDisEntityManagerComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
        {
            Subsystem->OnEntityUpdated.RemoveDynamic(this, &UFastDisEntityManagerComponent::HandleEntityUpdated);
        }
    }

    if (AActor* Owner = GetOwner())
    {
        if (UFastDisPduEventComponent* Events = Owner->FindComponentByClass<UFastDisPduEventComponent>())
        {
            Events->OnRemoveEntityDecoded.RemoveDynamic(this, &UFastDisEntityManagerComponent::HandleRemoveEntity);
        }
    }

    Super::EndPlay(EndPlayReason);
}

void UFastDisEntityManagerComponent::RegisterWithWorldSubsystem()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
    {
        Subsystem->OnEntityUpdated.RemoveDynamic(this, &UFastDisEntityManagerComponent::HandleEntityUpdated);
        Subsystem->OnEntityUpdated.AddDynamic(this, &UFastDisEntityManagerComponent::HandleEntityUpdated);
    }

    if (AActor* Owner = GetOwner())
    {
        if (UFastDisPduEventComponent* Events = Owner->FindComponentByClass<UFastDisPduEventComponent>())
        {
            Events->OnRemoveEntityDecoded.RemoveDynamic(this, &UFastDisEntityManagerComponent::HandleRemoveEntity);
            Events->OnRemoveEntityDecoded.AddDynamic(this, &UFastDisEntityManagerComponent::HandleRemoveEntity);
        }
    }
}

void UFastDisEntityManagerComponent::ClearManagedEntities(bool bDestroyActors)
{
    for (const TPair<FFastDisEntityId, TWeakObjectPtr<AActor>>& Pair : ManagedActors)
    {
        if (bDestroyActors && Pair.Value.IsValid())
        {
            Pair.Value->Destroy();
        }
    }
    ManagedActors.Empty();
}

int32 UFastDisEntityManagerComponent::GetManagedEntityCount() const
{
    return ManagedActors.Num();
}

void UFastDisEntityManagerComponent::ApplyRemoveEntityEvent(const FFastDisRemoveEntityEvent& Event)
{
    HandleRemoveEntity(Event);
}

void UFastDisEntityManagerComponent::HandleEntityUpdated(const FFastDisEntityTransformEvent& Event)
{
    TWeakObjectPtr<AActor>* Existing = ManagedActors.Find(Event.EntityId);
    if (Existing && Existing->IsValid())
    {
        Existing->Get()->SetActorTransform(Event.Transform, false, nullptr, ETeleportType::TeleportPhysics);
        return;
    }

    UWorld* World = GetWorld();
    TSubclassOf<AActor> ActorClass = EntityMapping
        ? EntityMapping->ResolveActorClass(Event.EntityType, DefaultActorClass)
        : DefaultActorClass;

    if (!World || !ActorClass)
    {
        return;
    }

    AActor* Actor = World->SpawnActor<AActor>(ActorClass, Event.Transform);
    if (!Actor)
    {
        return;
    }

    ManagedActors.Add(Event.EntityId, Actor);
    if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
    {
        Subsystem->RegisterActor(Event.EntityId, Actor);
    }
}

void UFastDisEntityManagerComponent::HandleRemoveEntity(const FFastDisRemoveEntityEvent& Event)
{
    if (RemoveEntityPolicy == EFastDisRemoveEntityPolicy::Ignore)
    {
        return;
    }

    const FFastDisEntityId TargetId = Event.ReceivingEntityId.Entity != 0
        ? Event.ReceivingEntityId
        : Event.OriginatingEntityId;

    TWeakObjectPtr<AActor>* ActorPtr = ManagedActors.Find(TargetId);
    if (!ActorPtr || !ActorPtr->IsValid())
    {
        return;
    }

    AActor* Actor = ActorPtr->Get();
    switch (RemoveEntityPolicy)
    {
    case EFastDisRemoveEntityPolicy::Destroy:
        Actor->Destroy();
        ManagedActors.Remove(TargetId);
        break;
    case EFastDisRemoveEntityPolicy::Hide:
        Actor->SetActorHiddenInGame(true);
        Actor->SetActorEnableCollision(false);
        ManagedActors.Remove(TargetId);
        break;
    case EFastDisRemoveEntityPolicy::MarkStale:
        Actor->Tags.AddUnique(TEXT("FastDIS.Stale"));
        break;
    case EFastDisRemoveEntityPolicy::Ignore:
    default:
        break;
    }

    if (UWorld* World = GetWorld())
    {
        if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
        {
            Subsystem->UnregisterActor(TargetId);
        }
    }
}
