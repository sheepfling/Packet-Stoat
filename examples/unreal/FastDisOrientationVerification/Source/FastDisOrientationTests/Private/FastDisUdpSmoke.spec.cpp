#include "Misc/AutomationTest.h"

#include "FastDisTypes.h"
#include "FastDisWorldSubsystem.h"

#include "Components/SceneComponent.h"
#include "Editor.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/PlatformMisc.h"
#include "IPAddress.h"
#include "Interfaces/IPv4/IPv4Address.h"
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

bool ReceiveUdpPackets(int32 Port, int32 ExpectedPackets, TArray<TArray<uint8>>& OutPackets, FString& OutError)
{
    ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
    if (!SocketSubsystem)
    {
        OutError = TEXT("No socket subsystem");
        return false;
    }

    FSocket* Socket = SocketSubsystem->CreateSocket(NAME_DGram, TEXT("FastDisUdpSmoke"), false);
    if (!Socket)
    {
        OutError = TEXT("CreateSocket failed");
        return false;
    }

    TSharedRef<FInternetAddr> BindAddress = SocketSubsystem->CreateInternetAddr();
    bool bIsValidIp = false;
    BindAddress->SetIp(TEXT("127.0.0.1"), bIsValidIp);
    if (!bIsValidIp)
    {
        OutError = TEXT("127.0.0.1 is not a valid bind address");
        SocketSubsystem->DestroySocket(Socket);
        return false;
    }
    BindAddress->SetPort(static_cast<uint32>(Port));

    Socket->SetReuseAddr(true);
    Socket->SetNonBlocking(true);
    if (!Socket->Bind(*BindAddress))
    {
        OutError = TEXT("Bind failed");
        Socket->Close();
        SocketSubsystem->DestroySocket(Socket);
        return false;
    }

    const double Deadline = FPlatformTime::Seconds() + 5.0;
    while (OutPackets.Num() < ExpectedPackets && FPlatformTime::Seconds() < Deadline)
    {
        uint32 Pending = 0;
        while (Socket->HasPendingData(Pending))
        {
            TArray<uint8> Packet;
            Packet.SetNumUninitialized(FMath::Clamp<int32>(static_cast<int32>(Pending), 1, 65535));
            int32 BytesRead = 0;
            TSharedRef<FInternetAddr> Sender = SocketSubsystem->CreateInternetAddr();
            if (Socket->RecvFrom(Packet.GetData(), Packet.Num(), BytesRead, *Sender))
            {
                Packet.SetNum(BytesRead);
                OutPackets.Add(Packet);
            }
            else
            {
                break;
            }
        }
        FPlatformProcess::Sleep(0.01f);
    }

    Socket->Close();
    SocketSubsystem->DestroySocket(Socket);
    if (OutPackets.Num() < ExpectedPackets)
    {
        OutError = FString::Printf(TEXT("Expected %d packets, received %d"), ExpectedPackets, OutPackets.Num());
        return false;
    }
    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FFastDisUnrealUdpSmokeSpec,
    "FastDis.Network.LocalhostUdpMovesActors",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FFastDisUnrealUdpSmokeSpec::RunTest(const FString& Parameters)
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

    const int32 Port = EnvInt(TEXT("FASTDIS_UNREAL_UDP_PORT"), 0);
    const int32 ExpectedPackets = EnvInt(TEXT("FASTDIS_UNREAL_EXPECTED_PACKETS"), 0);
    const int32 ExpectedEntities = EnvInt(TEXT("FASTDIS_UNREAL_EXPECTED_ENTITIES"), 0);
    if (!TestTrue(TEXT("FASTDIS_UNREAL_UDP_PORT is configured"), Port > 0))
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
    SpawnedActors.Reserve(FMath::Max(3, ExpectedEntities));
    for (int32 Index = 0; Index < FMath::Max(3, ExpectedEntities); ++Index)
    {
        AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, SpawnParameters);
        if (!TestNotNull(*FString::Printf(TEXT("spawned actor %d"), Index), Actor))
        {
            return false;
        }
        USceneComponent* Root = NewObject<USceneComponent>(Actor);
        Actor->SetRootComponent(Root);
        Root->RegisterComponent();
        Actor->SetActorLocation(FVector::ZeroVector);
        Subsystem->RegisterActor(FFastDisEntityId(100, 1, static_cast<uint16>(Index)), Actor);
        SpawnedActors.Add(Actor);
    }

    TArray<TArray<uint8>> Packets;
    FString Error;
    if (!TestTrue(TEXT("localhost UDP packets received"), ReceiveUdpPackets(Port, ExpectedPackets, Packets, Error)))
    {
        AddError(Error);
        for (AActor* Actor : SpawnedActors)
        {
            if (Actor)
            {
                Actor->Destroy();
            }
        }
        return false;
    }

    Subsystem->IngestPacketCopies(Packets, true);
    Subsystem->ApplyLatestSnapshots();

    int32 MovedActors = 0;
    for (int32 Index = 0; Index < SpawnedActors.Num(); ++Index)
    {
        if (!SpawnedActors[Index])
        {
            continue;
        }
        const double Distance = SpawnedActors[Index]->GetActorLocation().Size();
        if (Distance > 1.0)
        {
            MovedActors += 1;
        }
    }

    const int32 KnownEntities = Subsystem->GetKnownEntityCount();
    AddInfo(FString::Printf(
        TEXT("FASTDIS_UDP_SMOKE packets=%d expected_packets=%d known_entities=%d moved_actors=%d"),
        Packets.Num(),
        ExpectedPackets,
        KnownEntities,
        MovedActors));

    TestTrue(TEXT("known entities populated"), KnownEntities >= ExpectedEntities);
    TestTrue(TEXT("actors moved"), MovedActors >= ExpectedEntities);

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
