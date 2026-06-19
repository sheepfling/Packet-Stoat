#include "FastDisReplayActor.h"

#include "FastDisWorldSubsystem.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace
{
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
}

AFastDisReplayActor::AFastDisReplayActor()
{
    PrimaryActorTick.bCanEverTick = true;
}

void AFastDisReplayActor::BeginPlay()
{
    Super::BeginPlay();

    if (UWorld* World = GetWorld())
    {
        if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
        {
            Subsystem->ConfigureRuntimeSettings(RuntimeSettings);
        }
    }

    RegisterBindingsWithSubsystem();

    if (bAutoLoadOnBeginPlay)
    {
        LoadReplayFileInternal();
    }

    if (bAutoStartOnBeginPlay && ReplayPackets.Num() > 0)
    {
        StartReplay();
    }
}

void AFastDisReplayActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>())
        {
            for (const FFastDisActorBinding& Binding : ActorBindings)
            {
                Subsystem->UnregisterActor(Binding.EntityId);
            }
        }
    }

    Super::EndPlay(EndPlayReason);
}

void AFastDisReplayActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (!bReplayActive || ReplayPackets.Num() == 0)
    {
        return;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>();
    if (!Subsystem)
    {
        return;
    }

    const int32 BatchCount = FMath::Clamp(PacketsPerTick, 1, ReplayPackets.Num());
    TArray<TArray<uint8>> BatchPackets;
    BatchPackets.Reserve(BatchCount);

    for (int32 PacketIndex = 0; PacketIndex < BatchCount; ++PacketIndex)
    {
        if (NextPacketIndex >= ReplayPackets.Num())
        {
            if (!bLoopReplay)
            {
                bReplayActive = false;
                break;
            }
            NextPacketIndex = 0;
        }

        BatchPackets.Add(ReplayPackets[NextPacketIndex]);
        ++NextPacketIndex;
    }

    if (BatchPackets.Num() == 0)
    {
        return;
    }

    const TArrayView<const TArray<uint8>> BatchView(BatchPackets.GetData(), BatchPackets.Num());
    Subsystem->ConfigureRuntimeSettings(RuntimeSettings);
    Subsystem->IngestPacketCopies(BatchView, true);
    if (bApplySnapshotsImmediately)
    {
        Subsystem->ApplyLatestSnapshots(DeltaTime);
    }
}

bool AFastDisReplayActor::LoadReplayFile()
{
    return LoadReplayFileInternal();
}

void AFastDisReplayActor::StartReplay()
{
    if (ReplayPackets.Num() == 0 && !LoadReplayFileInternal())
    {
        return;
    }
    bReplayActive = ReplayPackets.Num() > 0;
}

void AFastDisReplayActor::StopReplay()
{
    bReplayActive = false;
}

void AFastDisReplayActor::ResetReplay()
{
    NextPacketIndex = 0;
}

void AFastDisReplayActor::RegisterBindings()
{
    RegisterBindingsWithSubsystem();
}

int32 AFastDisReplayActor::GetLoadedPacketCount() const
{
    return ReplayPackets.Num();
}

bool AFastDisReplayActor::LoadReplayFileInternal()
{
    ReplayPackets.Reset();
    NextPacketIndex = 0;
    bReplayActive = false;

    const FString ReplayPath = ReplayFile.FilePath;
    if (ReplayPath.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("FastDIS replay actor has no replay file configured."));
        return false;
    }

    const FString ResolvedReplayPath = FPaths::IsRelative(ReplayPath)
        ? FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir(), ReplayPath)
        : ReplayPath;

    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes, *ResolvedReplayPath, FILEREAD_Silent))
    {
        UE_LOG(LogTemp, Warning, TEXT("FastDIS replay actor could not load replay file: %s"), *ResolvedReplayPath);
        return false;
    }

    int32 Offset = 0;
    while (Offset < Bytes.Num())
    {
        uint32 PacketLength = 0;
        if (!ReadBe32(Bytes, Offset, PacketLength))
        {
            UE_LOG(LogTemp, Warning, TEXT("FastDIS replay file is truncated before length prefix: %s"), *ResolvedReplayPath);
            ReplayPackets.Reset();
            return false;
        }
        Offset += 4;

        if (PacketLength == 0 || PacketLength > static_cast<uint32>(Bytes.Num() - Offset))
        {
            UE_LOG(LogTemp, Warning, TEXT("FastDIS replay file has an invalid packet length: %s"), *ResolvedReplayPath);
            ReplayPackets.Reset();
            return false;
        }

        TArray<uint8> Packet;
        Packet.Append(Bytes.GetData() + Offset, static_cast<int32>(PacketLength));
        ReplayPackets.Add(MoveTemp(Packet));
        Offset += static_cast<int32>(PacketLength);
    }

    UE_LOG(LogTemp, Log, TEXT("FastDIS replay actor loaded %d packets from %s"), ReplayPackets.Num(), *ResolvedReplayPath);
    return ReplayPackets.Num() > 0;
}

void AFastDisReplayActor::RegisterBindingsWithSubsystem() const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UFastDisWorldSubsystem* Subsystem = World->GetSubsystem<UFastDisWorldSubsystem>();
    if (!Subsystem)
    {
        return;
    }

    Subsystem->ConfigureRuntimeSettings(RuntimeSettings);
    for (const FFastDisActorBinding& Binding : ActorBindings)
    {
        if (Binding.Actor)
        {
            Subsystem->RegisterActor(Binding.EntityId, Binding.Actor);
        }
    }
}
