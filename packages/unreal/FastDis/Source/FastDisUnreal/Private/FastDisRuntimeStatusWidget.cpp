#include "FastDisRuntimeStatusWidget.h"

#include "FastDisDemoController.h"
#include "FastDisRuntimeMonitorComponent.h"
#include "Kismet/GameplayStatics.h"

void UFastDisRuntimeStatusWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if (bAutoFindDemoController)
    {
        TryAutoBindDemoController();
    }
    RefreshSnapshot();
}

void UFastDisRuntimeStatusWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshSnapshot();
}

void UFastDisRuntimeStatusWidget::BindDemoController(AFastDisDemoController* InDemoController)
{
    DemoController = InDemoController;
    RuntimeMonitor = DemoController ? DemoController->RuntimeMonitor : nullptr;
    RefreshSnapshot();
}

void UFastDisRuntimeStatusWidget::BindRuntimeMonitor(UFastDisRuntimeMonitorComponent* InRuntimeMonitor)
{
    RuntimeMonitor = InRuntimeMonitor;
    DemoController = nullptr;
    RefreshSnapshot();
}

FFastDisRuntimeMonitorSnapshot UFastDisRuntimeStatusWidget::RefreshSnapshot()
{
    if (RuntimeMonitor)
    {
        LastSnapshot = RuntimeMonitor->RefreshSnapshot();
    }
    else if (DemoController)
    {
        LastSnapshot = DemoController->RefreshMonitorSnapshot();
    }
    return LastSnapshot;
}

FFastDisRuntimeMonitorSnapshot UFastDisRuntimeStatusWidget::GetLastSnapshot() const
{
    return LastSnapshot;
}

FText UFastDisRuntimeStatusWidget::GetStatusText() const
{
    return FormatSnapshot(LastSnapshot);
}

void UFastDisRuntimeStatusWidget::TryAutoBindDemoController()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    AActor* Actor = UGameplayStatics::GetActorOfClass(World, AFastDisDemoController::StaticClass());
    BindDemoController(Cast<AFastDisDemoController>(Actor));
}

FText UFastDisRuntimeStatusWidget::FormatSnapshot(const FFastDisRuntimeMonitorSnapshot& Snapshot)
{
    const FString Status = FString::Printf(
        TEXT("FastDIS\nReceiver: %s\nKnown entities: %d\nRX packets: %lld\nTX packets: %lld\nMalformed: %lld\nDropped: %lld\nLast PDU: %s (%d)\nEndpoint: %s"),
        Snapshot.bReceiverRunning ? TEXT("running") : TEXT("stopped"),
        Snapshot.KnownEntities,
        Snapshot.PacketsReceived,
        Snapshot.PacketsSent,
        Snapshot.MalformedPackets,
        Snapshot.DroppedPackets,
        *Snapshot.LastPduName.ToString(),
        Snapshot.LastPduType,
        *Snapshot.LastEndpoint);
    return FText::FromString(Status);
}
