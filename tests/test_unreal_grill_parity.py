from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "packages" / "unreal" / "FastDis"
PUBLIC = PLUGIN / "Source" / "FastDisUnreal" / "Public"
PRIVATE = PLUGIN / "Source" / "FastDisUnreal" / "Private"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_unreal_plugin_descriptor_no_longer_describes_sample_only_runtime() -> None:
    descriptor = json.loads((PLUGIN / "FastDis.uplugin").read_text(encoding="utf-8"))

    assert "runtime sample plugin" not in descriptor["Description"].lower()
    assert "live udp" in descriptor["Description"].lower()
    assert "blueprint pdu event" in descriptor["Description"].lower()
    assert "entity state update" in descriptor["Description"].lower()
    assert descriptor["CanContainContent"] is True
    assert descriptor["VersionName"] == "0.17.0-alpha12"
    assert descriptor["Version"] == 12
    assert descriptor["IsBetaVersion"] is True


def test_unreal_module_declares_socket_dependencies() -> None:
    build_cs = read(PLUGIN / "Source" / "FastDisUnreal" / "FastDisUnreal.Build.cs")

    assert '"Sockets"' in build_cs
    assert '"Networking"' in build_cs
    assert '"Json"' in build_cs
    assert '"JsonUtilities"' in build_cs
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
    assert "AliasEntityTypes" in mapping_h
    assert "Priority" in mapping_h
    assert "ResolveRow" in mapping_h
    assert "ResolveRow" in mapping_cpp
    assert "AliasEntityTypes" in mapping_cpp
    assert "Specificity" in mapping_cpp
    assert "Priority > BestPriority" in mapping_cpp
    assert "RowIndex < BestRowIndex" in mapping_cpp
    assert "HandleManagedActorDestroyed" in manager_h
    assert "RegisterManagedActor" in manager_h
    assert "UnregisterManagedActor" in manager_h
    assert "GetManagedActor" in manager_h
    assert "IsManagedActorRegistered" in manager_h
    assert "bool UFastDisEntityManagerComponent::RegisterManagedActor" in manager_cpp
    assert "void UFastDisEntityManagerComponent::UnregisterManagedActor" in manager_cpp
    assert "AActor* UFastDisEntityManagerComponent::GetManagedActor" in manager_cpp
    assert "bool UFastDisEntityManagerComponent::IsManagedActorRegistered" in manager_cpp
    assert "RegisterManagedActor(Event.EntityId, Actor)" in manager_cpp
    assert "OnDestroyed.AddDynamic" in manager_cpp
    assert "OnDestroyed.RemoveDynamic" in manager_cpp
    assert "UnregisterActor(TargetId)" in manager_cpp
    assert "OnEntityUpdated" in subsystem_h
    assert "OnEntityUpdated.Broadcast" in subsystem_cpp
    assert "TryReadEntityStateIdentity" in subsystem_cpp
    assert "FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE" in subsystem_cpp


def test_unreal_entity_mapping_supports_grill_shaped_alias_and_wildcard_authoring() -> None:
    types_h = read(PUBLIC / "FastDisTypes.h")
    mapping_h = read(PUBLIC / "FastDisEntityMappingDataAsset.h")
    enum_mapping_h = read(PUBLIC / "FastDisEnumerationMappingAsset.h")
    mapping_cpp = read(PRIVATE / "FastDisEntityMappingDataAsset.cpp")
    fab_asset_cpp = read(PRIVATE / "FastDisFabAssetLibrary.cpp")
    fab_asset_h = read(PUBLIC / "FastDisFabAssetLibrary.h")
    plugin_readme = read(PLUGIN / "README.md")

    assert "bool IsWildcard() const" in types_h
    assert "AliasEntityTypes" in mapping_h
    assert "ActorClassSoftPath" in mapping_h
    assert "SourceActorClassPath" in mapping_h
    assert "SourceRowIndex = -1" in mapping_h
    assert "UFastDisEnumerationMappingAsset" in enum_mapping_h
    assert "SourceRouteLabel" in enum_mapping_h
    assert "SourceManifestPath" in enum_mapping_h
    assert "Priority = 0" in mapping_h
    assert "ResolveConfiguredActorClass" in mapping_cpp
    assert "ActorClassSoftPath.LoadSynchronous" in mapping_cpp
    assert "ResolveRow" in mapping_cpp
    assert "AliasType.Matches(EntityType)" in mapping_cpp
    assert "OutRow.ActorClass = ResolvedActorClass" in mapping_cpp
    assert "Priority > BestPriority" in mapping_cpp
    assert "RowIndex < BestRowIndex" in mapping_cpp
    assert "ExactAircraft.AliasEntityTypes.Add" in fab_asset_cpp
    assert "AirPlatformFallback.Priority" in fab_asset_cpp
    assert "GenericPlatformFallback.Priority" in fab_asset_cpp
    assert "CreateEnumerationMappingAssetFromJson" in fab_asset_h
    assert "CreateEnumerationMappingAssetFromJson" in fab_asset_cpp
    assert "CreateGameManagerActorInEditorWorld" in fab_asset_h
    assert "CreateGameManagerActorInEditorWorld" in fab_asset_cpp
    assert "UFastDisEnumerationMappingAsset" in fab_asset_cpp
    assert "ActorClassSoftPath" in fab_asset_cpp
    assert "SourceManifestPath" in fab_asset_cpp
    assert "LoadObject<UFastDisEnumerationMappingAsset>" in fab_asset_cpp
    assert "AFastDisGameManagerActor::StaticClass()" in fab_asset_cpp
    assert "alias entity types per actor class" in plugin_readme
    assert "hard actor refs or soft class paths per mapping row" in plugin_readme
    assert "wildcard matching through negative enum fields" in plugin_readme
    assert "most-specific match wins" in plugin_readme
    assert "explicit row priority breaks ties" in plugin_readme
    assert "grill-mapping-materialize" in plugin_readme
    assert "soft class paths" in read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")


def test_unreal_game_manager_actor_exposes_swappable_grill_shaped_surface() -> None:
    types_h = read(PUBLIC / "FastDisTypes.h")
    manager_h = read(PUBLIC / "FastDisGameManagerActor.h")
    manager_cpp = read(PRIVATE / "FastDisGameManagerActor.cpp")
    receive_facade_h = read(PUBLIC / "FastDisReceiveFacadeComponent.h")
    receive_facade_cpp = read(PRIVATE / "FastDisReceiveFacadeComponent.cpp")
    send_facade_h = read(PUBLIC / "FastDisSendFacadeComponent.h")
    send_facade_cpp = read(PRIVATE / "FastDisSendFacadeComponent.cpp")
    build_script = read(ROOT / "tools" / "build_unreal_plugin.py")
    plugin_readme = read(PLUGIN / "README.md")
    parity_doc = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")

    assert "FFastDisSendSocketInfo" in types_h
    assert "FFastDisReceiveSocketInfo" in types_h
    assert "IpAddress = TEXT(\"127.0.0.1\")" in types_h
    assert "IpAddress = TEXT(\"0.0.0.0\")" in types_h
    assert "ReceiveBufferBytes = 1048576" in types_h
    assert "AFastDisGameManagerActor" in manager_h
    assert "GetFastDisGameManager" in manager_h
    assert "UFastDisReceiveFacadeComponent" in manager_h
    assert "UFastDisSendFacadeComponent" in manager_h
    assert "UFastDisEntityManagerComponent" in manager_h
    assert "EntityMapping" in manager_h
    assert "ExerciseId" in manager_h
    assert "SiteId" in manager_h
    assert "ApplicationId" in manager_h
    assert "DefaultActorClass" in manager_h
    assert "RemoveEntityPolicy" in manager_h
    assert "ReceiveBindAddress" in manager_h
    assert "SendRemoteAddress" in manager_h
    assert "AutoConnectReceiveAddresses" in manager_h
    assert "ReceiveSocketsToSetup" in manager_h
    assert "AutoConnectSendAddresses" in manager_h
    assert "SendSocketsToSetup" in manager_h
    assert "ApplyManagerSettings" in manager_h
    assert "PullManagerSettingsFromComponents" in manager_h
    assert "GetManagedEntityCount" in manager_h
    assert "AddManagedEntityToMap" in manager_h
    assert "RemoveManagedEntityFromMap" in manager_h
    assert "GetManagedEntityActor" in manager_h
    assert "SetEnumerationMappingAsset" in manager_h
    assert "GetEnumerationMappingAsset" in manager_h
    assert "CreateDefaultSubobject<UFastDisEntityManagerComponent>" in manager_cpp
    assert "CreateDefaultSubobject<UFastDisReceiveFacadeComponent>" in manager_cpp
    assert "CreateDefaultSubobject<UFastDisSendFacadeComponent>" in manager_cpp
    assert "ReceiveSocketsToSetup.AddDefaulted" in manager_cpp
    assert "SendSocketsToSetup.AddDefaulted" in manager_cpp
    assert "UGameplayStatics::GetAllActorsOfClass" in manager_cpp
    assert "ApplyPrimaryReceiveSocket" in manager_cpp
    assert "ApplyPrimarySendSocket" in manager_cpp
    assert "SyncPrimaryReceiveSocket" in manager_cpp
    assert "SyncPrimarySendSocket" in manager_cpp
    assert "EntityManager->EntityMapping = EntityMapping" in manager_cpp
    assert "EntityManager->RemoveEntityPolicy = RemoveEntityPolicy" in manager_cpp
    assert "Receiver->BindAddress = ReceiveBindAddress" in manager_cpp
    assert "Sender->RemoteAddress = SendRemoteAddress" in manager_cpp
    assert "ReceiveFacade->ApplyToReceiver()" in manager_cpp
    assert "SendFacade->ApplyToSender()" in manager_cpp
    assert "RuntimeMonitor->BindOwnerFastDisComponents()" in manager_cpp
    assert "RegisterManagedActor(EntityId, Actor, bReplaceExisting)" in manager_cpp
    assert "UnregisterManagedActor(EntityId)" in manager_cpp
    assert "GetManagedActor(EntityId)" in manager_cpp
    assert "EntityMapping = MappingAsset" in manager_cpp
    assert "Cast<UFastDisEnumerationMappingAsset>(EntityMapping)" in manager_cpp
    assert "UFastDisReceiveFacadeComponent" in receive_facade_h
    assert "PullFromReceiver" in receive_facade_h
    assert "ApplyToReceiver" in receive_facade_h
    assert "bool Start()" in receive_facade_h
    assert "Receiver->StartReceiver()" in receive_facade_cpp
    assert "UFastDisSendFacadeComponent" in send_facade_h
    assert "PullFromSender" in send_facade_h
    assert "ApplyToSender" in send_facade_h
    assert "SendRawPduBytes" in send_facade_h
    assert "Sender->SendRawPduBytes(Packet)" in send_facade_cpp
    assert "FastDisGameManagerActor.h" in build_script
    assert "FastDisGameManagerActor.cpp" in build_script
    assert "FastDisEnumerationMappingAsset.h" in build_script
    assert "FastDisReceiveFacadeComponent.h" in build_script
    assert "FastDisReceiveFacadeComponent.cpp" in build_script
    assert "FastDisSendFacadeComponent.h" in build_script
    assert "FastDisSendFacadeComponent.cpp" in build_script
    assert "AFastDisGameManagerActor" in plugin_readme
    assert "UFastDisEnumerationMappingAsset" in plugin_readme
    assert "UFastDisReceiveFacadeComponent" in plugin_readme
    assert "UFastDisSendFacadeComponent" in plugin_readme
    assert "GetFastDisGameManager" in plugin_readme
    assert "SetEnumerationMappingAsset" in plugin_readme
    assert "CreateGameManagerActorInEditorWorld" in plugin_readme
    assert "ReceiveSocketsToSetup" in plugin_readme
    assert "SendSocketsToSetup" in plugin_readme
    assert "grill-swap-smoke" in plugin_readme
    assert "AFastDisGameManagerActor" in parity_doc
    assert "UFastDisEnumerationMappingAsset" in parity_doc
    assert "UFastDisReceiveFacadeComponent" in parity_doc
    assert "UFastDisSendFacadeComponent" in parity_doc
    assert "GetFastDisGameManager" in parity_doc
    assert "SetEnumerationMappingAsset" in parity_doc
    assert "CreateGameManagerActorInEditorWorld" in parity_doc
    assert "ReceiveSocketsToSetup" in parity_doc
    assert "SendSocketsToSetup" in parity_doc
    assert "grill-swap-smoke" in parity_doc


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
    assert "install-smoke --engine-version 5.8" in setup_doc
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
        / "packages"
        / "unreal"
        / "FastDisOrientationVerification"
        / "Source"
        / "FastDisOrientationTests"
        / "Private"
        / "FastDisFabShell.spec.cpp"
    )
    build_cs = read(
        ROOT
        / "packages"
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
