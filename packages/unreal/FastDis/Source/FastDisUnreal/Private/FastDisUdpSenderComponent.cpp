#include "FastDisUdpSenderComponent.h"

#include "FastDisPduEvents.h"
#include "SocketSubsystem.h"
#include "Sockets.h"

UFastDisUdpSenderComponent::UFastDisUdpSenderComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UFastDisUdpSenderComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (Socket)
    {
        ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(Socket);
        Socket = nullptr;
    }
    Super::EndPlay(EndPlayReason);
}

bool UFastDisUdpSenderComponent::SendRawPduBytes(const TArray<uint8>& Packet)
{
    if (Packet.Num() == 0 || !EnsureSocket())
    {
        ++Stats.DroppedPackets;
        return false;
    }

    ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
    TSharedRef<FInternetAddr> Remote = SocketSubsystem->CreateInternetAddr();
    bool bCanBindAddress = false;
    Remote->SetIp(*RemoteAddress, bCanBindAddress);
    Remote->SetPort(static_cast<uint16>(FMath::Clamp(RemotePort, 1, 65535)));
    if (!bCanBindAddress)
    {
        ++Stats.DroppedPackets;
        return false;
    }

    int32 BytesSent = 0;
    const bool bSent = Socket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *Remote);
    if (bSent && BytesSent == Packet.Num())
    {
        ++Stats.PacketsSent;
        Stats.BytesSent += BytesSent;
        Stats.LastEndpoint = FString::Printf(TEXT("%s:%d"), *RemoteAddress, RemotePort);
        return true;
    }

    ++Stats.DroppedPackets;
    return false;
}

bool UFastDisUdpSenderComponent::SendEntityState(const TArray<uint8>& Packet)
{
    FFastDisPduHeader Header;
    if (!UFastDisPduEventComponent::ParsePduHeader(Packet, Header) || Header.Surface != EFastDisPduSurface::EntityState)
    {
        ++Stats.MalformedPackets;
        return false;
    }
    return SendRawPduBytes(Packet);
}

FFastDisUdpStats UFastDisUdpSenderComponent::GetStats() const
{
    return Stats;
}

bool UFastDisUdpSenderComponent::EnsureSocket()
{
    if (Socket)
    {
        return true;
    }

    Socket = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateSocket(NAME_DGram, TEXT("FastDIS UDP Sender"), false);
    return Socket != nullptr;
}
