"""Generated fastdis DIS message coverage metadata."""

from __future__ import annotations

from typing import NamedTuple


class MessageCoverage(NamedTuple):
    protocol_version: int
    pdu_type: int
    protocol_family: int
    class_name: str
    name: str
    family_name: str
    c_catalog: bool
    cpp_catalog: bool
    python_catalog: bool
    unreal_catalog: bool
    godot_catalog: bool
    unity_catalog: bool
    c_body_decoder: bool
    cpp_body_decoder: bool
    python_body_decoder: bool
    unreal_adapter: bool
    godot_adapter: bool
    unity_adapter: bool
    cataloged: bool
    header_validated: bool
    min_length_known: bool
    typed_prefix_parser: bool
    full_parser: bool
    serializer: bool
    roundtrip_tested: bool
    fuzzed_shallow: bool
    fuzzed_deep: bool
    differential_oracle: str | None


MESSAGE_COVERAGE: tuple[MessageCoverage, ...] = (
    MessageCoverage(6, 1, 1, "EntityStatePdu", "Entity State", "Entity Information", True, True, True, True, True, False, True, True, True, True, True, False, True, True, True, True, True, True, True, True, True, 'open-dis-python fixture report'),
    MessageCoverage(6, 2, 2, "FirePdu", "Fire", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 3, 2, "DetonationPdu", "Detonation", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 4, 1, "CollisionPdu", "Collision", "Entity Information", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 5, 3, "ServiceRequestPdu", "Service Request", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 6, 3, "ResupplyOfferPdu", "Resupply Offer", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 7, 3, "ResupplyReceivedPdu", "Resupply Received", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 8, 3, "ResupplyCancelPdu", "Resupply Cancel", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 9, 3, "RepairCompletePdu", "Repair Complete", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 10, 3, "RepairResponsePdu", "Repair Response", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 11, 5, "CreateEntityPdu", "Create Entity", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 12, 5, "RemoveEntityPdu", "Remove Entity", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 13, 5, "StartResumePdu", "Start Resume", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 14, 5, "StopFreezePdu", "Stop Freeze", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 15, 5, "AcknowledgePdu", "Acknowledge", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 16, 5, "ActionRequestPdu", "Action Request", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 17, 5, "ActionResponsePdu", "Action Response", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 18, 5, "DataQueryPdu", "Data Query", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 19, 5, "SetDataPdu", "Set Data", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 20, 5, "DataPdu", "Data", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 21, 5, "EventReportPdu", "Event Report", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 22, 5, "CommentPdu", "Comment", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 23, 6, "ElectronicEmissionsPdu", "Electronic Emissions", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 24, 6, "DesignatorPdu", "Designator", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 25, 4, "TransmitterPdu", "Transmitter", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 26, 4, "SignalPdu", "Signal", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 27, 4, "ReceiverPdu", "Receiver", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 28, 6, "IffAtcNavAidsLayer1Pdu", "Iff Atc Nav Aids Layer1", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 29, 6, "UaPdu", "Ua", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 30, 6, "SeesPdu", "Sees", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 31, 4, "IntercomSignalPdu", "Intercom Signal", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 32, 4, "IntercomControlPdu", "Intercom Control", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 33, 7, "AggregateStatePdu", "Aggregate State", "Entity Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 34, 7, "IsGroupOfPdu", "Is Group Of", "Entity Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 35, 7, "TransferControlRequestPdu", "Transfer Control Request", "Entity Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 36, 7, "IsPartOfPdu", "Is Part Of", "Entity Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 37, 8, "MinefieldStatePdu", "Minefield State", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 38, 8, "MinefieldQueryPdu", "Minefield Query", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 39, 8, "MinefieldDataPdu", "Minefield Data", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 40, 8, "MinefieldResponseNackPdu", "Minefield Response Nack", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 41, 9, "EnvironmentalProcessPdu", "Environmental Process", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 42, 9, "GriddedDataPdu", "Gridded Data", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 43, 9, "PointObjectStatePdu", "Point Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 44, 9, "LinearObjectStatePdu", "Linear Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 45, 9, "ArealObjectStatePdu", "Areal Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 51, 10, "CreateEntityReliablePdu", "Create Entity Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 52, 10, "RemoveEntityReliablePdu", "Remove Entity Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 53, 10, "StartResumeReliablePdu", "Start Resume Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 54, 10, "StopFreezeReliablePdu", "Stop Freeze Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 55, 10, "AcknowledgeReliablePdu", "Acknowledge Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 56, 10, "ActionRequestReliablePdu", "Action Request Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 57, 10, "ActionResponseReliablePdu", "Action Response Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 58, 10, "DataQueryReliablePdu", "Data Query Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 59, 10, "SetDataReliablePdu", "Set Data Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 60, 10, "DataReliablePdu", "Data Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 61, 10, "EventReportReliablePdu", "Event Report Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 62, 10, "CommentReliablePdu", "Comment Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 64, 10, "SetRecordReliablePdu", "Set Record Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 65, 10, "RecordQueryReliablePdu", "Record Query Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 66, 1, "CollisionElasticPdu", "Collision Elastic", "Entity Information", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(6, 67, 1, "EntityStateUpdatePdu", "Entity State Update", "Entity Information", True, True, True, True, True, False, True, True, True, True, True, False, True, True, True, True, True, True, True, True, True, None),
    MessageCoverage(7, 1, 1, "EntityStatePdu", "Entity State", "Entity Information", True, True, True, True, True, False, True, True, True, True, True, False, True, True, True, True, True, True, True, True, True, 'open-dis-python fixture report'),
    MessageCoverage(7, 2, 2, "FirePdu", "Fire", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 3, 2, "DetonationPdu", "Detonation", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 4, 1, "CollisionPdu", "Collision", "Entity Information", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 5, 3, "ServiceRequestPdu", "Service Request", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 6, 3, "ResupplyOfferPdu", "Resupply Offer", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 7, 3, "ResupplyReceivedPdu", "Resupply Received", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 9, 3, "RepairCompletePdu", "Repair Complete", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 10, 3, "RepairResponsePdu", "Repair Response", "Logistics", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 11, 5, "CreateEntityPdu", "Create Entity", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 12, 5, "RemoveEntityPdu", "Remove Entity", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 13, 5, "StartResumePdu", "Start Resume", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 14, 5, "StopFreezePdu", "Stop Freeze", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 15, 5, "AcknowledgePdu", "Acknowledge", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 16, 5, "ActionRequestPdu", "Action Request", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 17, 5, "ActionResponsePdu", "Action Response", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 18, 5, "DataQueryPdu", "Data Query", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 19, 5, "SetDataPdu", "Set Data", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 20, 5, "DataPdu", "Data", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 21, 5, "EventReportPdu", "Event Report", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 22, 5, "CommentPdu", "Comment", "Simulation Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 23, 6, "ElectronicEmissionsPdu", "Electronic Emissions", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 24, 6, "DesignatorPdu", "Designator", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 25, 4, "TransmitterPdu", "Transmitter", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 26, 4, "SignalPdu", "Signal", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 27, 4, "ReceiverPdu", "Receiver", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 28, 6, "IffPdu", "Iff", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 29, 6, "UaPdu", "Ua", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 30, 6, "SeesPdu", "Sees", "Distributed Emission Regeneration", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 31, 4, "IntercomSignalPdu", "Intercom Signal", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 32, 4, "IntercomControlPdu", "Intercom Control", "Radio Communications", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 36, 7, "IsPartOfPdu", "Is Part Of", "Entity Management", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 37, 8, "MinefieldStatePdu", "Minefield State", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 40, 8, "MinefieldResponseNackPdu", "Minefield Response Nack", "Minefield", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 43, 9, "PointObjectStatePdu", "Point Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 44, 9, "LinearObjectStatePdu", "Linear Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 45, 9, "ArealObjectStatePdu", "Areal Object State", "Synthetic Environment", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 51, 10, "CreateEntityReliablePdu", "Create Entity Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 52, 10, "RemoveEntityReliablePdu", "Remove Entity Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 53, 10, "StartResumeReliablePdu", "Start Resume Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 54, 10, "StopFreezeReliablePdu", "Stop Freeze Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 55, 10, "AcknowledgeReliablePdu", "Acknowledge Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 56, 10, "ActionRequestReliablePdu", "Action Request Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 57, 10, "ActionResponseReliablePdu", "Action Response Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 58, 10, "DataQueryReliablePdu", "Data Query Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 59, 10, "SetDataReliablePdu", "Set Data Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 60, 10, "DataReliablePdu", "Data Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 61, 10, "EventReportReliablePdu", "Event Report Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 62, 10, "CommentReliablePdu", "Comment Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 65, 10, "RecordQueryReliablePdu", "Record Query Reliable", "Simulation Management with Reliability", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 66, 1, "CollisionElasticPdu", "Collision Elastic", "Entity Information", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 67, 1, "EntityStateUpdatePdu", "Entity State Update", "Entity Information", True, True, True, True, True, False, True, True, True, True, True, False, True, True, True, True, True, True, True, True, True, None),
    MessageCoverage(7, 68, 2, "DirectedEnergyFirePdu", "Directed Energy Fire", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
    MessageCoverage(7, 69, 2, "EntityDamageStatusPdu", "Entity Damage Status", "Warfare", True, True, True, True, True, False, False, False, False, False, False, False, True, True, False, False, True, True, True, True, False, None),
)

def find_message_coverage(protocol_version: int, pdu_type: int) -> MessageCoverage | None:
    for entry in MESSAGE_COVERAGE:
        if entry.protocol_version == protocol_version and entry.pdu_type == pdu_type:
            return entry
    return None

def unsupported_body_decoders(protocol_version: int | None = None) -> list[MessageCoverage]:
    return [
        entry
        for entry in MESSAGE_COVERAGE
        if (protocol_version is None or entry.protocol_version == protocol_version)
        and not entry.c_body_decoder
    ]
