#include "FastDisReceiveFacadeComponent.h"

#include "FastDisUdpReceiverComponent.h"

void UFastDisReceiveFacadeComponent::BeginPlay()
{
    Super::BeginPlay();

    if (!Receiver)
    {
        Receiver = GetOwner() ? GetOwner()->FindComponentByClass<UFastDisUdpReceiverComponent>() : nullptr;
    }

    ApplyToReceiver();
}

void UFastDisReceiveFacadeComponent::PullFromReceiver()
{
    if (!Receiver)
    {
        return;
    }

    BindAddress = Receiver->BindAddress;
    Port = Receiver->Port;
    ReceiveBufferBytes = Receiver->ReceiveBufferBytes;
    MaxPacketsPerTick = Receiver->MaxPacketsPerTick;
    bAutoStart = Receiver->bAutoStart;
    bApplySnapshotsImmediately = Receiver->bApplySnapshotsImmediately;
}

void UFastDisReceiveFacadeComponent::ApplyToReceiver()
{
    if (!Receiver)
    {
        return;
    }

    Receiver->BindAddress = BindAddress;
    Receiver->Port = Port;
    Receiver->ReceiveBufferBytes = ReceiveBufferBytes;
    Receiver->MaxPacketsPerTick = MaxPacketsPerTick;
    Receiver->bAutoStart = bAutoStart;
    Receiver->bApplySnapshotsImmediately = bApplySnapshotsImmediately;
}

bool UFastDisReceiveFacadeComponent::Start()
{
    ApplyToReceiver();
    return Receiver ? Receiver->StartReceiver() : false;
}

void UFastDisReceiveFacadeComponent::Stop()
{
    if (Receiver)
    {
        Receiver->StopReceiver();
    }
}

bool UFastDisReceiveFacadeComponent::IsRunning() const
{
    return Receiver ? Receiver->IsReceiverRunning() : false;
}

FFastDisUdpStats UFastDisReceiveFacadeComponent::GetStats() const
{
    return Receiver ? Receiver->GetStats() : FFastDisUdpStats();
}
