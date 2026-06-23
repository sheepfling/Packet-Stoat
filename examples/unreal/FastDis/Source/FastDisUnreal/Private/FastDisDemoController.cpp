#include "FastDisDemoController.h"

#include "Components/SceneComponent.h"
#include "FastDisGeoreferenceAdapterComponent.h"
#include "FastDisPduDebugMarkerComponent.h"
#include "FastDisPduEvents.h"
#include "FastDisRuntimeMonitorComponent.h"
#include "FastDisSampleTrafficComponent.h"
#include "FastDisUdpReceiverComponent.h"
#include "FastDisUdpSenderComponent.h"

AFastDisDemoController::AFastDisDemoController()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;

    PduEvents = CreateDefaultSubobject<UFastDisPduEventComponent>(TEXT("PduEvents"));
    DebugMarkers = CreateDefaultSubobject<UFastDisPduDebugMarkerComponent>(TEXT("DebugMarkers"));
    GeoreferenceAdapter = CreateDefaultSubobject<UFastDisGeoreferenceAdapterComponent>(TEXT("GeoreferenceAdapter"));
    Receiver = CreateDefaultSubobject<UFastDisUdpReceiverComponent>(TEXT("UdpReceiver"));
    Sender = CreateDefaultSubobject<UFastDisUdpSenderComponent>(TEXT("UdpSender"));
    RuntimeMonitor = CreateDefaultSubobject<UFastDisRuntimeMonitorComponent>(TEXT("RuntimeMonitor"));
    SampleTraffic = CreateDefaultSubobject<UFastDisSampleTrafficComponent>(TEXT("SampleTraffic"));

    Receiver->bAutoStart = false;
    SampleTraffic->bInjectOnBeginPlay = false;
}

bool AFastDisDemoController::StartLiveReceive()
{
    return Receiver ? Receiver->StartReceiver() : false;
}

void AFastDisDemoController::StopLiveReceive()
{
    if (Receiver)
    {
        Receiver->StopReceiver();
    }
}

void AFastDisDemoController::InjectLocalEntityState(bool bApplyImmediately)
{
    if (SampleTraffic)
    {
        SampleTraffic->InjectSamplePacket(bApplyImmediately);
    }
}

bool AFastDisDemoController::SendSampleEntityState()
{
    if (!Sender || !SampleTraffic)
    {
        return false;
    }

    return Sender->SendEntityState(SampleTraffic->BuildSampleEntityStatePacket());
}

FFastDisRuntimeMonitorSnapshot AFastDisDemoController::RefreshMonitorSnapshot()
{
    return RuntimeMonitor ? RuntimeMonitor->RefreshSnapshot() : FFastDisRuntimeMonitorSnapshot();
}

FFastDisRuntimeMonitorSnapshot AFastDisDemoController::GetLastMonitorSnapshot() const
{
    return RuntimeMonitor ? RuntimeMonitor->GetLastSnapshot() : FFastDisRuntimeMonitorSnapshot();
}
