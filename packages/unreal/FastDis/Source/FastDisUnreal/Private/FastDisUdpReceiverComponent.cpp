#include "FastDisUdpReceiverComponent.h"

#include "Common/UdpSocketBuilder.h"
#include "Engine/World.h"
#include "FastDisWorldSubsystem.h"
#include "GameFramework/Actor.h"
#include "SocketSubsystem.h"
#include "Sockets.h"

#ifdef check
#pragma push_macro("check")
#undef check
#define FASTDIS_RESTORE_UE_CHECK_MACRO 1
#endif

#include "fastdis/fastdis.hpp"

#ifdef FASTDIS_RESTORE_UE_CHECK_MACRO
#pragma pop_macro("check")
#undef FASTDIS_RESTORE_UE_CHECK_MACRO
#endif

UFastDisUdpReceiverComponent::UFastDisUdpReceiverComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UFastDisUdpReceiverComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoStart)
    {
        StartReceiver();
    }
}

void UFastDisUdpReceiverComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    StopReceiver();
    Super::EndPlay(EndPlayReason);
}

void UFastDisUdpReceiverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    PumpSocket(DeltaTime);
}

bool UFastDisUdpReceiverComponent::StartReceiver()
{
    if (Socket)
    {
        return true;
    }

    FIPv4Address Address;
    if (!FIPv4Address::Parse(BindAddress, Address))
    {
        UE_LOG(LogTemp, Warning, TEXT("FastDIS UDP receiver bind address is invalid: %s"), *BindAddress);
        return false;
    }

    const FIPv4Endpoint Endpoint(Address, static_cast<uint16>(Port));
    Socket = FUdpSocketBuilder(TEXT("FastDIS UDP Receiver"))
        .AsNonBlocking()
        .AsReusable()
        .BoundToEndpoint(Endpoint)
        .WithReceiveBufferSize(ReceiveBufferBytes);

    if (!Socket)
    {
        UE_LOG(LogTemp, Warning, TEXT("FastDIS UDP receiver failed to bind %s:%d"), *BindAddress, Port);
        return false;
    }

    return true;
}

void UFastDisUdpReceiverComponent::StopReceiver()
{
    if (!Socket)
    {
        return;
    }

    ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(Socket);
    Socket = nullptr;
}

bool UFastDisUdpReceiverComponent::IsReceiverRunning() const
{
    return Socket != nullptr;
}

FFastDisUdpStats UFastDisUdpReceiverComponent::GetStats() const
{
    return Stats;
}

void UFastDisUdpReceiverComponent::PumpSocket(float DeltaTime)
{
    if (!Socket)
    {
        return;
    }

    UWorld* World = GetWorld();
    UFastDisWorldSubsystem* Subsystem = World ? World->GetSubsystem<UFastDisWorldSubsystem>() : nullptr;
    UFastDisPduEventComponent* EventComponent = GetOwner() ? GetOwner()->FindComponentByClass<UFastDisPduEventComponent>() : nullptr;

    TArray<TArray<uint8>> Packets;
    Packets.Reserve(MaxPacketsPerTick);

    for (int32 PacketIndex = 0; PacketIndex < MaxPacketsPerTick; ++PacketIndex)
    {
        uint32 PendingBytes = 0;
        if (!Socket->HasPendingData(PendingBytes))
        {
            break;
        }

        TSharedRef<FInternetAddr> Sender = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();
        TArray<uint8> Packet;
        Packet.SetNumUninitialized(static_cast<int32>(PendingBytes));

        int32 BytesRead = 0;
        if (!Socket->RecvFrom(Packet.GetData(), Packet.Num(), BytesRead, *Sender) || BytesRead <= 0)
        {
            ++Stats.DroppedPackets;
            continue;
        }

        Packet.SetNum(BytesRead);
        ++Stats.PacketsReceived;
        Stats.BytesReceived += BytesRead;
        Stats.LastEndpoint = Sender->ToString(true);

        FFastDisPduHeader Header;
        if (!UFastDisPduEventComponent::ParsePduHeader(Packet, Header))
        {
            ++Stats.MalformedPackets;
            FFastDisPduEvent Event;
            Event.SourceEndpoint = Stats.LastEndpoint;
            Event.RawBytes = Packet;
            OnMalformedPdu.Broadcast(Event);
            if (EventComponent)
            {
                EventComponent->OnMalformedPdu.Broadcast(Event);
            }
            continue;
        }

        FFastDisPduEvent Event;
        Event.Header = Header;
        Event.SourceEndpoint = Stats.LastEndpoint;
        Event.RawBytes = Packet;
        OnPduReceived.Broadcast(Event);
        if (EventComponent)
        {
            EventComponent->BroadcastPduEvent(Event);
        }

        Packets.Add(MoveTemp(Packet));
    }

    if (Subsystem && Packets.Num() > 0)
    {
        const TArrayView<const TArray<uint8>> BatchView(Packets.GetData(), Packets.Num());
        Subsystem->IngestPacketCopies(BatchView, true);
        if (bApplySnapshotsImmediately)
        {
            Subsystem->ApplyLatestSnapshots(DeltaTime);
        }
    }
}
