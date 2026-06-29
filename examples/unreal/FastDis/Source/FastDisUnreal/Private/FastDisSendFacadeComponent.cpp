#include "FastDisSendFacadeComponent.h"

#include "GameFramework/Actor.h"

#include "FastDisUdpSenderComponent.h"

void UFastDisSendFacadeComponent::BeginPlay()
{
    Super::BeginPlay();

    if (!Sender)
    {
        Sender = GetOwner() ? GetOwner()->FindComponentByClass<UFastDisUdpSenderComponent>() : nullptr;
    }

    ApplyToSender();
}

void UFastDisSendFacadeComponent::PullFromSender()
{
    if (!Sender)
    {
        return;
    }

    RemoteAddress = Sender->RemoteAddress;
    RemotePort = Sender->RemotePort;
}

void UFastDisSendFacadeComponent::ApplyToSender()
{
    if (!Sender)
    {
        return;
    }

    Sender->RemoteAddress = RemoteAddress;
    Sender->RemotePort = RemotePort;
}

bool UFastDisSendFacadeComponent::SendRawPduBytes(const TArray<uint8>& Packet)
{
    ApplyToSender();
    return Sender ? Sender->SendRawPduBytes(Packet) : false;
}

bool UFastDisSendFacadeComponent::SendEntityState(const TArray<uint8>& Packet)
{
    ApplyToSender();
    return Sender ? Sender->SendEntityState(Packet) : false;
}

FFastDisUdpStats UFastDisSendFacadeComponent::GetStats() const
{
    return Sender ? Sender->GetStats() : FFastDisUdpStats();
}
