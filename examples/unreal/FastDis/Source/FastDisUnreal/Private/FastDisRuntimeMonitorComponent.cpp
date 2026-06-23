#include "FastDisRuntimeMonitorComponent.h"

#include "Engine/World.h"
#include "FastDisUdpReceiverComponent.h"
#include "FastDisUdpSenderComponent.h"
#include "FastDisWorldSubsystem.h"
#include "GameFramework/Actor.h"

UFastDisRuntimeMonitorComponent::UFastDisRuntimeMonitorComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UFastDisRuntimeMonitorComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoBindOwnerComponents)
    {
        BindOwnerFastDisComponents();
    }
    RefreshSnapshot();
}

void UFastDisRuntimeMonitorComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    RefreshSnapshot();
}

void UFastDisRuntimeMonitorComponent::BindOwnerFastDisComponents()
{
    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }

    if (!Receiver)
    {
        Receiver = Owner->FindComponentByClass<UFastDisUdpReceiverComponent>();
    }
    if (!Sender)
    {
        Sender = Owner->FindComponentByClass<UFastDisUdpSenderComponent>();
    }
    if (!PduEvents)
    {
        PduEvents = Owner->FindComponentByClass<UFastDisPduEventComponent>();
    }

    if (PduEvents)
    {
        PduEvents->OnPduReceived.RemoveDynamic(this, &UFastDisRuntimeMonitorComponent::HandlePduReceived);
        PduEvents->OnPduReceived.AddDynamic(this, &UFastDisRuntimeMonitorComponent::HandlePduReceived);
        PduEvents->OnMalformedPdu.RemoveDynamic(this, &UFastDisRuntimeMonitorComponent::HandleMalformedPdu);
        PduEvents->OnMalformedPdu.AddDynamic(this, &UFastDisRuntimeMonitorComponent::HandleMalformedPdu);
    }
}

FFastDisRuntimeMonitorSnapshot UFastDisRuntimeMonitorComponent::RefreshSnapshot()
{
    if (Receiver)
    {
        const FFastDisUdpStats ReceiverStats = Receiver->GetStats();
        LastSnapshot.bReceiverRunning = Receiver->IsReceiverRunning();
        LastSnapshot.PacketsReceived = ReceiverStats.PacketsReceived;
        LastSnapshot.BytesReceived = ReceiverStats.BytesReceived;
        LastSnapshot.MalformedPackets = ReceiverStats.MalformedPackets;
        LastSnapshot.DroppedPackets = ReceiverStats.DroppedPackets;
        LastSnapshot.LastEndpoint = ReceiverStats.LastEndpoint;
    }
    else
    {
        LastSnapshot.bReceiverRunning = false;
        LastSnapshot.PacketsReceived = 0;
        LastSnapshot.BytesReceived = 0;
        LastSnapshot.MalformedPackets = 0;
        LastSnapshot.DroppedPackets = 0;
    }

    if (Sender)
    {
        const FFastDisUdpStats SenderStats = Sender->GetStats();
        LastSnapshot.PacketsSent = SenderStats.PacketsSent;
        LastSnapshot.BytesSent = SenderStats.BytesSent;
    }
    else
    {
        LastSnapshot.PacketsSent = 0;
        LastSnapshot.BytesSent = 0;
    }

    UWorld* World = GetWorld();
    UFastDisWorldSubsystem* Subsystem = World ? World->GetSubsystem<UFastDisWorldSubsystem>() : nullptr;
    LastSnapshot.KnownEntities = Subsystem ? Subsystem->GetKnownEntityCount() : 0;
    return LastSnapshot;
}

FFastDisRuntimeMonitorSnapshot UFastDisRuntimeMonitorComponent::GetLastSnapshot() const
{
    return LastSnapshot;
}

void UFastDisRuntimeMonitorComponent::ResetEventCounters()
{
    LastSnapshot.PduEvents = 0;
    LastSnapshot.PduMalformedEvents = 0;
    LastSnapshot.LastPduType = 0;
    LastSnapshot.LastPduName = NAME_None;
}

void UFastDisRuntimeMonitorComponent::HandlePduReceived(const FFastDisPduEvent& Event)
{
    ++LastSnapshot.PduEvents;
    LastSnapshot.LastPduType = Event.Header.PduType;
    LastSnapshot.LastPduName = Event.Header.PduName;
    LastSnapshot.LastEndpoint = Event.SourceEndpoint;
}

void UFastDisRuntimeMonitorComponent::HandleMalformedPdu(const FFastDisPduEvent& Event)
{
    ++LastSnapshot.PduMalformedEvents;
    LastSnapshot.LastPduType = 0;
    LastSnapshot.LastPduName = TEXT("Malformed");
    LastSnapshot.LastEndpoint = Event.SourceEndpoint;
}
