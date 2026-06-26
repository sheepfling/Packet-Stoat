#include "FastDisGameManagerActor.h"

#include "Components/SceneComponent.h"
#include "Engine/Engine.h"
#include "FastDisEntityManagerComponent.h"
#include "FastDisEnumerationMappingAsset.h"
#include "FastDisGeoreferenceAdapterComponent.h"
#include "FastDisPduEvents.h"
#include "FastDisReceiveFacadeComponent.h"
#include "FastDisRuntimeMonitorComponent.h"
#include "FastDisSendFacadeComponent.h"
#include "FastDisUdpReceiverComponent.h"
#include "FastDisUdpSenderComponent.h"
#include "Kismet/GameplayStatics.h"

namespace
{
void ApplyPrimaryReceiveSocket(AFastDisGameManagerActor& Manager)
{
    if (!Manager.AutoConnectReceiveAddresses || Manager.ReceiveSocketsToSetup.IsEmpty())
    {
        return;
    }

    const FFastDisReceiveSocketInfo& Socket = Manager.ReceiveSocketsToSetup[0];
    Manager.ReceiveBindAddress = Socket.IpAddress;
    Manager.ReceivePort = Socket.Port;
    Manager.ReceiveBufferBytes = Socket.ReceiveBufferBytes;
    Manager.MaxPacketsPerTick = Socket.MaxPacketsPerTick;
    Manager.bAutoStartReceiver = Socket.bAutoStart;
    Manager.bApplySnapshotsImmediately = Socket.bApplySnapshotsImmediately;
}

void ApplyPrimarySendSocket(AFastDisGameManagerActor& Manager)
{
    if (!Manager.AutoConnectSendAddresses || Manager.SendSocketsToSetup.IsEmpty())
    {
        return;
    }

    const FFastDisSendSocketInfo& Socket = Manager.SendSocketsToSetup[0];
    Manager.SendRemoteAddress = Socket.IpAddress;
    Manager.SendRemotePort = Socket.Port;
}

void SyncPrimaryReceiveSocket(AFastDisGameManagerActor& Manager)
{
    if (!Manager.AutoConnectReceiveAddresses)
    {
        return;
    }

    FFastDisReceiveSocketInfo& Socket = Manager.ReceiveSocketsToSetup.IsEmpty()
        ? Manager.ReceiveSocketsToSetup.AddDefaulted_GetRef()
        : Manager.ReceiveSocketsToSetup[0];
    Socket.IpAddress = Manager.ReceiveBindAddress;
    Socket.Port = Manager.ReceivePort;
    Socket.ReceiveBufferBytes = Manager.ReceiveBufferBytes;
    Socket.MaxPacketsPerTick = Manager.MaxPacketsPerTick;
    Socket.bAutoStart = Manager.bAutoStartReceiver;
    Socket.bApplySnapshotsImmediately = Manager.bApplySnapshotsImmediately;
}

void SyncPrimarySendSocket(AFastDisGameManagerActor& Manager)
{
    if (!Manager.AutoConnectSendAddresses)
    {
        return;
    }

    FFastDisSendSocketInfo& Socket = Manager.SendSocketsToSetup.IsEmpty()
        ? Manager.SendSocketsToSetup.AddDefaulted_GetRef()
        : Manager.SendSocketsToSetup[0];
    Socket.IpAddress = Manager.SendRemoteAddress;
    Socket.Port = Manager.SendRemotePort;
}
}

AFastDisGameManagerActor::AFastDisGameManagerActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;

    PduEvents = CreateDefaultSubobject<UFastDisPduEventComponent>(TEXT("PduEvents"));
    EntityManager = CreateDefaultSubobject<UFastDisEntityManagerComponent>(TEXT("EntityManager"));
    GeoreferenceAdapter = CreateDefaultSubobject<UFastDisGeoreferenceAdapterComponent>(TEXT("GeoreferenceAdapter"));
    Receiver = CreateDefaultSubobject<UFastDisUdpReceiverComponent>(TEXT("UdpReceiver"));
    ReceiveFacade = CreateDefaultSubobject<UFastDisReceiveFacadeComponent>(TEXT("ReceiveFacade"));
    Sender = CreateDefaultSubobject<UFastDisUdpSenderComponent>(TEXT("UdpSender"));
    SendFacade = CreateDefaultSubobject<UFastDisSendFacadeComponent>(TEXT("SendFacade"));
    RuntimeMonitor = CreateDefaultSubobject<UFastDisRuntimeMonitorComponent>(TEXT("RuntimeMonitor"));

    RuntimeMonitor->bAutoBindOwnerComponents = true;

    ReceiveSocketsToSetup.AddDefaulted();
    SendSocketsToSetup.AddDefaulted();
}

AFastDisGameManagerActor* AFastDisGameManagerActor::GetFastDisGameManager(UObject* WorldContextObject)
{
    if (WorldContextObject == nullptr)
    {
        return nullptr;
    }

    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
    if (World == nullptr)
    {
        return nullptr;
    }

    TArray<AActor*> Actors;
    UGameplayStatics::GetAllActorsOfClass(World, AFastDisGameManagerActor::StaticClass(), Actors);
    if (Actors.Num() != 1)
    {
        return nullptr;
    }

    return Cast<AFastDisGameManagerActor>(Actors[0]);
}

void AFastDisGameManagerActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyManagerSettings();
}

void AFastDisGameManagerActor::BeginPlay()
{
    ApplyManagerSettings();
    Super::BeginPlay();
}

void AFastDisGameManagerActor::ApplyManagerSettings()
{
    ApplyPrimaryReceiveSocket(*this);
    ApplyPrimarySendSocket(*this);

    if (EntityManager)
    {
        EntityManager->EntityMapping = EntityMapping;
        EntityManager->DefaultActorClass = DefaultActorClass;
        EntityManager->RemoveEntityPolicy = RemoveEntityPolicy;
    }

    if (Receiver)
    {
        Receiver->BindAddress = ReceiveBindAddress;
        Receiver->Port = ReceivePort;
        Receiver->ReceiveBufferBytes = ReceiveBufferBytes;
        Receiver->MaxPacketsPerTick = MaxPacketsPerTick;
        Receiver->bAutoStart = bAutoStartReceiver;
        Receiver->bApplySnapshotsImmediately = bApplySnapshotsImmediately;
    }

    if (ReceiveFacade)
    {
        ReceiveFacade->Receiver = Receiver;
        ReceiveFacade->BindAddress = ReceiveBindAddress;
        ReceiveFacade->Port = ReceivePort;
        ReceiveFacade->ReceiveBufferBytes = ReceiveBufferBytes;
        ReceiveFacade->MaxPacketsPerTick = MaxPacketsPerTick;
        ReceiveFacade->bAutoStart = bAutoStartReceiver;
        ReceiveFacade->bApplySnapshotsImmediately = bApplySnapshotsImmediately;
        ReceiveFacade->ApplyToReceiver();
    }

    if (Sender)
    {
        Sender->RemoteAddress = SendRemoteAddress;
        Sender->RemotePort = SendRemotePort;
    }

    if (SendFacade)
    {
        SendFacade->Sender = Sender;
        SendFacade->RemoteAddress = SendRemoteAddress;
        SendFacade->RemotePort = SendRemotePort;
        SendFacade->ApplyToSender();
    }

    if (RuntimeMonitor)
    {
        RuntimeMonitor->Receiver = Receiver;
        RuntimeMonitor->Sender = Sender;
        RuntimeMonitor->PduEvents = PduEvents;
        RuntimeMonitor->BindOwnerFastDisComponents();
    }

    SyncPrimaryReceiveSocket(*this);
    SyncPrimarySendSocket(*this);
}

void AFastDisGameManagerActor::PullManagerSettingsFromComponents()
{
    if (ReceiveFacade)
    {
        ReceiveFacade->PullFromReceiver();
        ReceiveBindAddress = ReceiveFacade->BindAddress;
        ReceivePort = ReceiveFacade->Port;
        ReceiveBufferBytes = ReceiveFacade->ReceiveBufferBytes;
        MaxPacketsPerTick = ReceiveFacade->MaxPacketsPerTick;
        bAutoStartReceiver = ReceiveFacade->bAutoStart;
        bApplySnapshotsImmediately = ReceiveFacade->bApplySnapshotsImmediately;
    }

    if (SendFacade)
    {
        SendFacade->PullFromSender();
        SendRemoteAddress = SendFacade->RemoteAddress;
        SendRemotePort = SendFacade->RemotePort;
    }

    SyncPrimaryReceiveSocket(*this);
    SyncPrimarySendSocket(*this);
}

bool AFastDisGameManagerActor::StartLiveReceive()
{
    ApplyManagerSettings();
    return Receiver ? Receiver->StartReceiver() : false;
}

void AFastDisGameManagerActor::StopLiveReceive()
{
    if (Receiver)
    {
        Receiver->StopReceiver();
    }
}

bool AFastDisGameManagerActor::IsLiveReceiveRunning() const
{
    return Receiver ? Receiver->IsReceiverRunning() : false;
}

FFastDisRuntimeMonitorSnapshot AFastDisGameManagerActor::RefreshMonitorSnapshot()
{
    return RuntimeMonitor ? RuntimeMonitor->RefreshSnapshot() : FFastDisRuntimeMonitorSnapshot();
}

FFastDisRuntimeMonitorSnapshot AFastDisGameManagerActor::GetLastMonitorSnapshot() const
{
    return RuntimeMonitor ? RuntimeMonitor->GetLastSnapshot() : FFastDisRuntimeMonitorSnapshot();
}

int32 AFastDisGameManagerActor::GetManagedEntityCount() const
{
    return EntityManager ? EntityManager->GetManagedEntityCount() : 0;
}

bool AFastDisGameManagerActor::AddManagedEntityToMap(const FFastDisEntityId& EntityId, AActor* Actor, bool bReplaceExisting)
{
    return EntityManager ? EntityManager->RegisterManagedActor(EntityId, Actor, bReplaceExisting) : false;
}

bool AFastDisGameManagerActor::RemoveManagedEntityFromMap(const FFastDisEntityId& EntityId)
{
    if (!EntityManager || !EntityManager->IsManagedActorRegistered(EntityId))
    {
        return false;
    }

    EntityManager->UnregisterManagedActor(EntityId);
    return true;
}

AActor* AFastDisGameManagerActor::GetManagedEntityActor(const FFastDisEntityId& EntityId) const
{
    return EntityManager ? EntityManager->GetManagedActor(EntityId) : nullptr;
}

void AFastDisGameManagerActor::SetEnumerationMappingAsset(UFastDisEnumerationMappingAsset* MappingAsset)
{
    EntityMapping = MappingAsset;
    ApplyManagerSettings();
}

UFastDisEnumerationMappingAsset* AFastDisGameManagerActor::GetEnumerationMappingAsset() const
{
    return Cast<UFastDisEnumerationMappingAsset>(EntityMapping);
}
