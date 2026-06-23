from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "examples" / "unreal" / "FastDis"
PUBLIC = PLUGIN / "Source" / "FastDisUnreal" / "Public"
PRIVATE = PLUGIN / "Source" / "FastDisUnreal" / "Private"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_unreal_plugin_descriptor_no_longer_describes_sample_only_runtime() -> None:
    descriptor = json.loads((PLUGIN / "FastDis.uplugin").read_text(encoding="utf-8"))

    assert "runtime sample plugin" not in descriptor["Description"].lower()
    assert "live udp" in descriptor["Description"].lower()
    assert "blueprint pdu event" in descriptor["Description"].lower()
    assert descriptor["CanContainContent"] is True


def test_unreal_module_declares_socket_dependencies() -> None:
    build_cs = read(PLUGIN / "Source" / "FastDisUnreal" / "FastDisUnreal.Build.cs")

    assert '"Sockets"' in build_cs
    assert '"Networking"' in build_cs
    assert '"UMG"' in build_cs


def test_unreal_live_udp_components_exist_and_feed_shared_ingest_path() -> None:
    receiver_h = read(PUBLIC / "FastDisUdpReceiverComponent.h")
    receiver_cpp = read(PRIVATE / "FastDisUdpReceiverComponent.cpp")
    sender_h = read(PUBLIC / "FastDisUdpSenderComponent.h")
    sender_cpp = read(PRIVATE / "FastDisUdpSenderComponent.cpp")

    assert "UFastDisUdpReceiverComponent" in receiver_h
    assert "StartReceiver" in receiver_h
    assert "StopReceiver" in receiver_h
    assert "IsReceiverRunning" in receiver_h
    assert "UFastDisWorldSubsystem" in receiver_cpp
    assert "IngestPacketCopies" in receiver_cpp
    assert "FUdpSocketBuilder" in receiver_cpp
    assert "UFastDisUdpSenderComponent" in sender_h
    assert "SendRawPduBytes" in sender_h
    assert "SendEntityState" in sender_h
    assert "SendTo" in sender_cpp


def test_unreal_pdu_event_component_covers_grill_surface() -> None:
    events_h = read(PUBLIC / "FastDisPduEvents.h")
    events_cpp = read(PRIVATE / "FastDisPduEvents.cpp")

    for delegate in [
        "OnEntityState",
        "OnEntityStateUpdate",
        "OnRemoveEntity",
        "OnFire",
        "OnDetonation",
        "OnStartResume",
        "OnStopFreeze",
        "OnEmission",
        "OnSignal",
        "OnDesignator",
        "OnMalformedPdu",
    ]:
        assert delegate in events_h

    for pdu_type in ["case 1:", "case 2:", "case 3:", "case 7:", "case 8:", "case 12:", "case 23:", "case 24:", "case 26:", "case 67:"]:
        assert pdu_type in events_cpp


def test_unreal_entity_manager_auto_spawns_from_entity_state_snapshot_events() -> None:
    manager_h = read(PUBLIC / "FastDisEntityManagerComponent.h")
    manager_cpp = read(PRIVATE / "FastDisEntityManagerComponent.cpp")
    mapping_h = read(PUBLIC / "FastDisEntityMappingDataAsset.h")
    mapping_cpp = read(PRIVATE / "FastDisEntityMappingDataAsset.cpp")
    subsystem_h = read(PUBLIC / "FastDisWorldSubsystem.h")
    subsystem_cpp = read(PRIVATE / "FastDisWorldSubsystem.cpp")

    assert "UFastDisEntityManagerComponent" in manager_h
    assert "EntityMapping" in manager_h
    assert "DefaultActorClass" in manager_h
    assert "EFastDisRemoveEntityPolicy" in manager_h
    assert "HandleEntityUpdated" in manager_h
    assert "HandleRemoveEntity" in manager_h
    assert "SpawnActor" in manager_cpp
    assert "ResolveActorClass" in manager_cpp
    assert "UFastDisEntityMappingDataAsset" in mapping_h
    assert "Specificity" in mapping_cpp
    assert "RegisterActor(Event.EntityId, Actor)" in manager_cpp
    assert "UnregisterActor(TargetId)" in manager_cpp
    assert "OnEntityUpdated" in subsystem_h
    assert "OnEntityUpdated.Broadcast" in subsystem_cpp
    assert "TryReadEntityStateIdentity" in subsystem_cpp
    assert "FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE" in subsystem_cpp


def test_unreal_runtime_monitor_component_supports_demo_status_ui() -> None:
    types_h = read(PUBLIC / "FastDisTypes.h")
    monitor_h = read(PUBLIC / "FastDisRuntimeMonitorComponent.h")
    monitor_cpp = read(PRIVATE / "FastDisRuntimeMonitorComponent.cpp")
    build_script = read(ROOT / "tools" / "build_unreal_plugin.py")
    doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")
    readme = read(PLUGIN / "README.md")

    assert "FFastDisRuntimeMonitorSnapshot" in types_h
    for field in [
        "bReceiverRunning",
        "KnownEntities",
        "PacketsReceived",
        "PacketsSent",
        "MalformedPackets",
        "DroppedPackets",
        "LastPduType",
        "LastPduName",
    ]:
        assert field in types_h

    assert "UFastDisRuntimeMonitorComponent" in monitor_h
    assert "BindOwnerFastDisComponents" in monitor_h
    assert "RefreshSnapshot" in monitor_h
    assert "GetLastSnapshot" in monitor_h
    assert "ResetEventCounters" in monitor_h
    assert "OnPduReceived.AddDynamic" in monitor_cpp
    assert "OnMalformedPdu.AddDynamic" in monitor_cpp
    assert "GetKnownEntityCount" in monitor_cpp
    assert "FastDisRuntimeMonitorComponent.h" in build_script
    assert "FastDisRuntimeMonitorComponent.cpp" in build_script
    assert "UFastDisRuntimeMonitorComponent" in doc
    assert "UFastDisRuntimeMonitorComponent" in readme


def test_unreal_demo_controller_and_setup_docs_support_fab_package_shape() -> None:
    controller_h = read(PUBLIC / "FastDisDemoController.h")
    controller_cpp = read(PRIVATE / "FastDisDemoController.cpp")
    markers_h = read(PUBLIC / "FastDisPduDebugMarkerComponent.h")
    markers_cpp = read(PRIVATE / "FastDisPduDebugMarkerComponent.cpp")
    sample_h = read(PUBLIC / "FastDisSampleTrafficComponent.h")
    sample_cpp = read(PRIVATE / "FastDisSampleTrafficComponent.cpp")
    build_script = read(ROOT / "tools" / "build_unreal_plugin.py")
    setup_doc = read(PLUGIN / "Docs" / "FIVE_MINUTE_SETUP.md")
    content_readme = read(PLUGIN / "Content" / "Examples" / "README.md")
    parity_doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")
    plugin_readme = read(PLUGIN / "README.md")
    georef_h = read(PUBLIC / "FastDisGeoreferenceAdapterComponent.h")
    georef_cpp = read(PRIVATE / "FastDisGeoreferenceAdapterComponent.cpp")

    assert "AFastDisDemoController" in controller_h
    for call in [
        "StartLiveReceive",
        "StopLiveReceive",
        "InjectLocalEntityState",
        "SendSampleEntityState",
        "RefreshMonitorSnapshot",
    ]:
        assert call in controller_h
        assert call in controller_cpp

    for component in [
        "UFastDisUdpReceiverComponent",
        "UFastDisUdpSenderComponent",
        "UFastDisPduEventComponent",
        "UFastDisPduDebugMarkerComponent",
        "UFastDisGeoreferenceAdapterComponent",
        "UFastDisRuntimeMonitorComponent",
        "UFastDisSampleTrafficComponent",
    ]:
        assert component in controller_h
        assert component in controller_cpp

    assert "BuildSampleEntityStatePacket" in sample_h
    assert "BuildSampleEntityStatePacket" in sample_cpp
    assert "FastDisDemoController.h" in build_script
    assert "FastDisDemoController.cpp" in build_script
    assert "FastDisPduDebugMarkerComponent.h" in build_script
    assert "FastDisPduDebugMarkerComponent.cpp" in build_script
    assert "Docs/FAB_DRAFT.md" in build_script
    assert "FastDisGeoreferenceAdapterComponent.h" in build_script
    assert "FastDisGeoreferenceAdapterComponent.cpp" in build_script
    assert "Docs/FIVE_MINUTE_SETUP.md" in build_script
    assert "Content/Examples/README.md" in build_script
    for packaged_asset in [
        "Content/Examples/FastDis_Demo.umap",
        "Content/Examples/WBP_FastDisRuntimeStatus.uasset",
        "Content/Examples/BP_FastDisDemoController.uasset",
        "Content/Examples/DA_FastDisEntityMappings.uasset",
        "Content/Examples/Screenshots/live_udp_status.png",
        "Content/Examples/Screenshots/entity_spawn.png",
        "Content/Examples/Screenshots/pdu_event_marker.png",
        "Content/Examples/Screenshots/setup_view.png",
    ]:
        assert packaged_asset in build_script
    assert "AFastDisDemoController" in setup_doc
    assert "AFastDisDemoController" in content_readme
    assert "AFastDisDemoController" in parity_doc
    assert "AFastDisDemoController" in plugin_readme
    assert "Docs/FAB_DRAFT.md" in plugin_readme
    assert "UFastDisGeoreferenceAdapterComponent" in georef_h
    assert "ApplyFromSourceObject" in georef_h
    assert "ReadSourceGeoreference" in georef_h
    assert "FindPropertyByName" in georef_cpp
    assert "ConfigureGeoreference" in georef_cpp
    assert "Unreal/Cesium" in setup_doc
    assert "UFastDisGeoreferenceAdapterComponent" in plugin_readme
    assert "UFastDisGeoreferenceAdapterComponent" in parity_doc
    assert "tools/check_unreal_fab_readiness.py" in parity_doc
    assert "UFastDisPduDebugMarkerComponent" in markers_h
    assert "HandleFire" in markers_h
    assert "HandleDetonation" in markers_h
    assert "HandleDesignator" in markers_h
    assert "OnFireDecoded.AddDynamic" in markers_cpp
    assert "OnDetonationDecoded.AddDynamic" in markers_cpp
    assert "OnDesignatorDecoded.AddDynamic" in markers_cpp
    assert "DisWorldLocationToUnreal" in markers_cpp
    assert "UFastDisPduDebugMarkerComponent" in setup_doc
    assert "UFastDisPduDebugMarkerComponent" in content_readme
    assert "UFastDisPduDebugMarkerComponent" in parity_doc
    assert "UFastDisPduDebugMarkerComponent" in plugin_readme


def test_unreal_runtime_status_widget_provides_code_backed_demo_ui() -> None:
    widget_h = read(PUBLIC / "FastDisRuntimeStatusWidget.h")
    widget_cpp = read(PRIVATE / "FastDisRuntimeStatusWidget.cpp")
    build_script = read(ROOT / "tools" / "build_unreal_plugin.py")
    setup_doc = read(PLUGIN / "Docs" / "FIVE_MINUTE_SETUP.md")
    content_readme = read(PLUGIN / "Content" / "Examples" / "README.md")
    parity_doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")
    plugin_readme = read(PLUGIN / "README.md")

    assert "UFastDisRuntimeStatusWidget" in widget_h
    assert "UUserWidget" in widget_h
    assert "BindDemoController" in widget_h
    assert "BindRuntimeMonitor" in widget_h
    assert "RefreshSnapshot" in widget_h
    assert "GetStatusText" in widget_h
    assert "NativeTick" in widget_h
    assert "UGameplayStatics::GetActorOfClass" in widget_cpp
    assert "FormatSnapshot" in widget_cpp
    assert "FastDisRuntimeStatusWidget.h" in build_script
    assert "FastDisRuntimeStatusWidget.cpp" in build_script
    assert "UFastDisRuntimeStatusWidget" in setup_doc
    assert "UFastDisRuntimeStatusWidget" in content_readme
    assert "UFastDisRuntimeStatusWidget" in parity_doc
    assert "UFastDisRuntimeStatusWidget" in plugin_readme


def test_unreal_demo_source_shell_has_automation_coverage() -> None:
    spec = read(
        ROOT
        / "examples"
        / "unreal"
        / "FastDisOrientationVerification"
        / "Source"
        / "FastDisOrientationTests"
        / "Private"
        / "FastDisFabShell.spec.cpp"
    )
    build_cs = read(
        ROOT
        / "examples"
        / "unreal"
        / "FastDisOrientationVerification"
        / "Source"
        / "FastDisOrientationTests"
        / "FastDisOrientationTests.Build.cs"
    )
    readiness = read(ROOT / "tools" / "check_unreal_fab_readiness.py")
    parity_doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")

    assert "FastDis.Demo.FabSourceShell" in spec
    for symbol in [
        "AFastDisDemoController",
        "UFastDisRuntimeStatusWidget",
        "UFastDisGeoreferenceAdapterComponent",
        "UFastDisPduDebugMarkerComponent",
        "UFastDisPduEventComponent::ParsePduHeader",
        "BuildSampleEntityStatePacket",
        "InjectLocalEntityState",
    ]:
        assert symbol in spec

    assert '"UMG"' in build_cs
    assert "demo_source_shell_automation" in readiness
    assert "FastDis.Demo.FabSourceShell" in parity_doc


def test_unreal_grill_parity_doc_tracks_surface_vs_body_depth() -> None:
    doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")

    assert "Runtime surface" in doc
    assert "Body depth" in doc
    assert "decoded typed summary + raw sidecar" in doc
    assert "native compact transform patch" in doc
    assert "native Entity State prefix/snapshot" in doc
    assert "Remove Entity lifecycle" in doc


def test_unreal_decoded_pdu_events_cover_lifecycle_warfare_and_esu() -> None:
    types_h = read(PUBLIC / "FastDisTypes.h")
    events_h = read(PUBLIC / "FastDisPduEvents.h")
    events_cpp = read(PRIVATE / "FastDisPduEvents.cpp")

    for struct_name in [
        "FFastDisRemoveEntityEvent",
        "FFastDisEntityStateUpdateEvent",
        "FFastDisFireEvent",
        "FFastDisDetonationEvent",
        "FFastDisStartResumeEvent",
        "FFastDisStopFreezeEvent",
        "FFastDisEmissionEvent",
        "FFastDisSignalEvent",
        "FFastDisDesignatorEvent",
    ]:
        assert struct_name in types_h

    for delegate in [
        "OnRemoveEntityDecoded",
        "OnEntityStateUpdateDecoded",
        "OnFireDecoded",
        "OnDetonationDecoded",
        "OnStartResumeDecoded",
        "OnStopFreezeDecoded",
        "OnEmissionDecoded",
        "OnSignalDecoded",
        "OnDesignatorDecoded",
    ]:
        assert delegate in events_h
        assert delegate in events_cpp

    for parser in [
        "ParseRemoveEntityEvent",
        "ParseEntityStateUpdateEvent",
        "ParseFireEvent",
        "ParseDetonationEvent",
        "ParseStartResumeEvent",
        "ParseStopFreezeEvent",
        "ParseEmissionEvent",
        "ParseSignalEvent",
        "ParseDesignatorEvent",
    ]:
        assert parser in events_h
        assert parser in events_cpp


def test_unreal_grill_parity_doc_tracks_typed_summaries_with_raw_sidecars() -> None:
    doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")

    for pdu_name in [
        "Fire",
        "Detonation",
        "Start/Resume",
        "Stop/Freeze",
        "Remove Entity",
        "Electromagnetic Emission",
        "Designator",
        "Signal",
    ]:
        assert f"| {pdu_name} |" in doc

    assert doc.count("decoded typed summary + raw sidecar") >= 8
    assert "richer semantic body models" in doc
