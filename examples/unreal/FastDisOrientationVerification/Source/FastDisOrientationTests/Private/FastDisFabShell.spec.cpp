#include "Misc/AutomationTest.h"

#include "FastDisDemoController.h"
#include "FastDisGeoreferenceAdapterComponent.h"
#include "FastDisPduDebugMarkerComponent.h"
#include "FastDisPduEvents.h"
#include "FastDisRuntimeMonitorComponent.h"
#include "FastDisRuntimeStatusWidget.h"
#include "FastDisSampleTrafficComponent.h"
#include "FastDisTypes.h"
#include "FastDisUdpReceiverComponent.h"
#include "FastDisUdpSenderComponent.h"
#include "FastDisWorldSubsystem.h"

#include "Editor.h"
#include "Engine/World.h"
#include "UObject/Package.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FFastDisUnrealFabShellSpec,
    "FastDis.Demo.FabSourceShell",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FFastDisUnrealFabShellSpec::RunTest(const FString& Parameters)
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

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.ObjectFlags |= RF_Transient;

    AFastDisDemoController* Demo = World->SpawnActor<AFastDisDemoController>(
        AFastDisDemoController::StaticClass(),
        FTransform::Identity,
        SpawnParameters);
    if (!TestNotNull(TEXT("spawned demo controller"), Demo))
    {
        return false;
    }

    TestNotNull(TEXT("UDP receiver component"), Demo->Receiver.Get());
    TestNotNull(TEXT("UDP sender component"), Demo->Sender.Get());
    TestNotNull(TEXT("PDU event component"), Demo->PduEvents.Get());
    TestNotNull(TEXT("debug marker component"), Demo->DebugMarkers.Get());
    TestNotNull(TEXT("georeference adapter component"), Demo->GeoreferenceAdapter.Get());
    TestNotNull(TEXT("runtime monitor component"), Demo->RuntimeMonitor.Get());
    TestNotNull(TEXT("sample traffic component"), Demo->SampleTraffic.Get());

    if (!Demo->Receiver || !Demo->Sender || !Demo->PduEvents || !Demo->DebugMarkers || !Demo->GeoreferenceAdapter ||
        !Demo->RuntimeMonitor || !Demo->SampleTraffic)
    {
        Demo->Destroy();
        return false;
    }

    TestTrue(TEXT("receiver component type"), Demo->Receiver->IsA(UFastDisUdpReceiverComponent::StaticClass()));
    TestTrue(TEXT("sender component type"), Demo->Sender->IsA(UFastDisUdpSenderComponent::StaticClass()));
    TestTrue(TEXT("PDU event component type"), Demo->PduEvents->IsA(UFastDisPduEventComponent::StaticClass()));
    TestTrue(TEXT("debug marker component type"), Demo->DebugMarkers->IsA(UFastDisPduDebugMarkerComponent::StaticClass()));
    TestTrue(
        TEXT("georeference adapter component type"),
        Demo->GeoreferenceAdapter->IsA(UFastDisGeoreferenceAdapterComponent::StaticClass()));
    TestTrue(TEXT("runtime monitor component type"), Demo->RuntimeMonitor->IsA(UFastDisRuntimeMonitorComponent::StaticClass()));
    TestTrue(TEXT("sample traffic component type"), Demo->SampleTraffic->IsA(UFastDisSampleTrafficComponent::StaticClass()));

    TestFalse(TEXT("receiver does not auto-start in demo shell"), Demo->Receiver->bAutoStart);
    TestFalse(TEXT("sample traffic does not auto-inject in demo shell"), Demo->SampleTraffic->bInjectOnBeginPlay);

    TArray<uint8> Packet = Demo->SampleTraffic->BuildSampleEntityStatePacket();
    TestTrue(TEXT("sample Entity State packet has DIS header and body"), Packet.Num() >= 144);

    FFastDisPduHeader Header;
    TestTrue(TEXT("sample packet parses as PDU header"), UFastDisPduEventComponent::ParsePduHeader(Packet, Header));
    TestEqual(TEXT("sample packet PDU type"), Header.PduType, 1);
    TestEqual(
        TEXT("sample packet surface"),
        static_cast<uint8>(Header.Surface),
        static_cast<uint8>(EFastDisPduSurface::EntityState));
    TestEqual(TEXT("sample packet declared length"), Header.DeclaredLength, Packet.Num());

    FFastDisGeoreference Georeference;
    Georeference.LatitudeDegrees = 29.5597;
    Georeference.LongitudeDegrees = -95.0831;
    Georeference.HeightMeters = 7.0;
    Georeference.bApplyOrientation = false;
    Demo->GeoreferenceAdapter->ManualGeoreference = Georeference;
    TestTrue(TEXT("manual georeference applies through subsystem"), Demo->GeoreferenceAdapter->ApplyManualGeoreference());

    Subsystem->ClearRegisteredActors();
    Demo->InjectLocalEntityState(true);
    const FFastDisRuntimeMonitorSnapshot Snapshot = Demo->RefreshMonitorSnapshot();
    TestTrue(TEXT("demo injection reaches entity table"), Snapshot.KnownEntities >= 1);

    UFastDisRuntimeStatusWidget* Widget = NewObject<UFastDisRuntimeStatusWidget>(GetTransientPackage());
    if (!TestNotNull(TEXT("runtime status widget object"), Widget))
    {
        Demo->Destroy();
        Subsystem->ClearRegisteredActors();
        return false;
    }
    Widget->BindDemoController(Demo);
    const FText StatusText = Widget->GetStatusText();
    TestTrue(TEXT("status widget formats FastDIS status"), StatusText.ToString().Contains(TEXT("FastDIS")));
    TestTrue(TEXT("status widget includes known entity count"), StatusText.ToString().Contains(TEXT("Known entities")));

    Demo->Destroy();
    Subsystem->ClearRegisteredActors();
    return true;
}

#endif
