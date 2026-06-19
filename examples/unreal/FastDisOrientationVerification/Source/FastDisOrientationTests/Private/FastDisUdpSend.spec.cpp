#include "Misc/AutomationTest.h"

#include "HAL/PlatformMisc.h"
#include "IPAddress.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Misc/FileHelper.h"
#include "SocketSubsystem.h"
#include "Sockets.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
int32 EnvInt(const TCHAR* Name, int32 DefaultValue)
{
    const FString Value = FPlatformMisc::GetEnvironmentVariable(Name);
    return Value.IsEmpty() ? DefaultValue : FCString::Atoi(*Value);
}

FString EnvString(const TCHAR* Name)
{
    return FPlatformMisc::GetEnvironmentVariable(Name);
}

bool ReadBe32(const TArray<uint8>& Bytes, int32 Offset, uint32& OutValue)
{
    if (Offset < 0 || Offset + 4 > Bytes.Num())
    {
        return false;
    }

    OutValue = (static_cast<uint32>(Bytes[Offset + 0]) << 24) |
               (static_cast<uint32>(Bytes[Offset + 1]) << 16) |
               (static_cast<uint32>(Bytes[Offset + 2]) << 8) |
               static_cast<uint32>(Bytes[Offset + 3]);
    return true;
}

bool LoadReplayPackets(const FString& ReplayPath, TArray<TArray<uint8>>& OutPackets, FString& OutError)
{
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes, *ReplayPath, FILEREAD_Silent))
    {
        OutError = FString::Printf(TEXT("Could not open replay file: %s"), *ReplayPath);
        return false;
    }

    int32 Offset = 0;
    while (Offset < Bytes.Num())
    {
        uint32 PacketLength = 0;
        if (!ReadBe32(Bytes, Offset, PacketLength))
        {
            OutError = TEXT("Replay file is truncated before a packet length prefix");
            return false;
        }
        Offset += 4;

        if (PacketLength == 0 || PacketLength > static_cast<uint32>(Bytes.Num() - Offset))
        {
            OutError = FString::Printf(TEXT("Invalid replay packet length: %u"), PacketLength);
            return false;
        }

        TArray<uint8> Packet;
        Packet.Append(Bytes.GetData() + Offset, static_cast<int32>(PacketLength));
        OutPackets.Add(MoveTemp(Packet));
        Offset += static_cast<int32>(PacketLength);
    }

    return OutPackets.Num() > 0;
}

bool SendUdpPackets(const FString& Host, int32 Port, const TArray<TArray<uint8>>& Packets, int64& OutBytesSent, FString& OutError)
{
    ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
    if (!SocketSubsystem)
    {
        OutError = TEXT("No socket subsystem");
        return false;
    }

    FSocket* Socket = SocketSubsystem->CreateSocket(NAME_DGram, TEXT("FastDisUdpSendSmoke"), false);
    if (!Socket)
    {
        OutError = TEXT("CreateSocket failed");
        return false;
    }

    TSharedRef<FInternetAddr> Address = SocketSubsystem->CreateInternetAddr();
    bool bIsValidIp = false;
    Address->SetIp(*Host, bIsValidIp);
    if (!bIsValidIp)
    {
        OutError = FString::Printf(TEXT("Invalid destination host: %s"), *Host);
        SocketSubsystem->DestroySocket(Socket);
        return false;
    }
    Address->SetPort(static_cast<uint32>(Port));

    Socket->SetReuseAddr(true);

    for (const TArray<uint8>& Packet : Packets)
    {
        int32 BytesSent = 0;
        if (!Socket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *Address))
        {
            OutError = FString::Printf(TEXT("SendTo failed after %lld bytes"), OutBytesSent);
            Socket->Close();
            SocketSubsystem->DestroySocket(Socket);
            return false;
        }
        OutBytesSent += BytesSent;
    }

    Socket->Close();
    SocketSubsystem->DestroySocket(Socket);
    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FFastDisUnrealUdpSendSmokeSpec,
    "FastDis.Network.OutboundReplaySend",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FFastDisUnrealUdpSendSmokeSpec::RunTest(const FString& Parameters)
{
    const FString Host = EnvString(TEXT("FASTDIS_UNREAL_SEND_HOST"));
    const FString ReplayPath = EnvString(TEXT("FASTDIS_UNREAL_SEND_REPLAY_PATH"));
    const int32 Port = EnvInt(TEXT("FASTDIS_UNREAL_SEND_PORT"), 0);
    const int32 ExpectedPackets = EnvInt(TEXT("FASTDIS_UNREAL_SEND_EXPECTED_PACKETS"), 0);

    if (!TestTrue(TEXT("FASTDIS_UNREAL_SEND_HOST is configured"), !Host.IsEmpty()))
    {
        return false;
    }
    if (!TestTrue(TEXT("FASTDIS_UNREAL_SEND_REPLAY_PATH is configured"), !ReplayPath.IsEmpty()))
    {
        return false;
    }
    if (!TestTrue(TEXT("FASTDIS_UNREAL_SEND_PORT is configured"), Port > 0))
    {
        return false;
    }

    TArray<TArray<uint8>> Packets;
    FString Error;
    if (!TestTrue(TEXT("replay fixture loaded"), LoadReplayPackets(ReplayPath, Packets, Error)))
    {
        AddError(Error);
        return false;
    }

    int64 BytesSent = 0;
    if (!TestTrue(TEXT("UDP replay packets sent"), SendUdpPackets(Host, Port, Packets, BytesSent, Error)))
    {
        AddError(Error);
        return false;
    }

    AddInfo(FString::Printf(
        TEXT("FASTDIS_UDP_SEND_SMOKE packets_sent=%d expected_packets=%d bytes_sent=%lld"),
        Packets.Num(),
        ExpectedPackets,
        BytesSent));

    TestEqual(TEXT("expected packet count sent"), Packets.Num(), ExpectedPackets);
    return true;
}

#endif
