"""ctypes bindings for the portable fastdis DLL/shared-object C ABI.

This module validates and demonstrates the stable C ABI used by Unreal, Godot,
C#, Rust, Zig, and other hosts. It is intentionally not the fastest Python path;
for pure Python hot loops, prefer :func:`fastdis.scan_many`, which uses the
CPython extension when available.
"""

from __future__ import annotations

from collections.abc import Iterable
import ctypes
import ctypes.util
from dataclasses import dataclass
import os
from pathlib import Path
import platform
from typing import Callable, NamedTuple, TypeGuard, cast

FASTDIS_ABI_EPOCH = 0
FASTDIS_ABI_REVISION = 16
FASTDIS_ABI_VERSION = FASTDIS_ABI_REVISION
FASTDIS_HEADER_SIZE = 12
FASTDIS_PROTOCOL_VERSION_DIS6 = 6
FASTDIS_PROTOCOL_VERSION_DIS7 = 7
FASTDIS_HEADER_STATUS_UNAVAILABLE = -1
FASTDIS_ENTITY_INFORMATION_FAMILY = 1
FASTDIS_ENTITY_STATE_PDU_TYPE = 1
FASTDIS_ENTITY_STATE_FIXED_SIZE = 144
FASTDIS_FIRE_PDU_TYPE = 2
FASTDIS_FIRE_FIXED_SIZE = 96
FASTDIS_DETONATION_PDU_TYPE = 3
FASTDIS_DETONATION_FIXED_SIZE = 92
FASTDIS_COLLISION_PDU_TYPE = 4
FASTDIS_COLLISION_FIXED_SIZE = 60
FASTDIS_OTHER_PDU_TYPE = 0
FASTDIS_OTHER_FIXED_SIZE = 12
FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE = 23
FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE = 28
FASTDIS_DESIGNATOR_PDU_TYPE = 24
FASTDIS_DESIGNATOR_FIXED_SIZE = 88
FASTDIS_TRANSMITTER_PDU_TYPE = 25
FASTDIS_TRANSMITTER_FIXED_SIZE = 100
FASTDIS_SIGNAL_PDU_TYPE = 26
FASTDIS_SIGNAL_DIS6_FIXED_SIZE = 32
FASTDIS_SIGNAL_DIS7_FIXED_SIZE = 24
FASTDIS_RECEIVER_PDU_TYPE = 27
FASTDIS_RECEIVER_DIS6_FIXED_SIZE = 36
FASTDIS_RECEIVER_DIS7_FIXED_SIZE = 28
FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE = 28
FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE = 56
FASTDIS_IFF_PDU_TYPE = 28
FASTDIS_IFF_FIXED_SIZE = 56
FASTDIS_UA_PDU_TYPE = 29
FASTDIS_UA_FIXED_SIZE = 32
FASTDIS_SEES_PDU_TYPE = 30
FASTDIS_SEES_FIXED_SIZE = 28
FASTDIS_INTERCOM_SIGNAL_PDU_TYPE = 31
FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE = 32
FASTDIS_INTERCOM_CONTROL_PDU_TYPE = 32
FASTDIS_INTERCOM_CONTROL_FIXED_SIZE = 37
FASTDIS_AGGREGATE_STATE_PDU_TYPE = 33
FASTDIS_AGGREGATE_STATE_FIXED_SIZE = 132
FASTDIS_IS_GROUP_OF_PDU_TYPE = 34
FASTDIS_IS_GROUP_OF_FIXED_SIZE = 40
FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE = 35
FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE = 37
FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE = 35
FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE = 37
FASTDIS_IS_PART_OF_PDU_TYPE = 36
FASTDIS_IS_PART_OF_FIXED_SIZE = 52
FASTDIS_MINEFIELD_STATE_PDU_TYPE = 37
FASTDIS_MINEFIELD_STATE_FIXED_SIZE = 72
FASTDIS_MINEFIELD_QUERY_PDU_TYPE = 38
FASTDIS_MINEFIELD_QUERY_FIXED_SIZE = 40
FASTDIS_MINEFIELD_DATA_PDU_TYPE = 39
FASTDIS_MINEFIELD_DATA_FIXED_SIZE = 44
FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE = 40
FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE = 26
FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE = 41
FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE = 31
FASTDIS_GRIDDED_DATA_PDU_TYPE = 42
FASTDIS_GRIDDED_DATA_FIXED_SIZE = 64
FASTDIS_POINT_OBJECT_STATE_PDU_TYPE = 43
FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE = 90
FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE = 88
FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE = 44
FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE = 42
FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE = 40
FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE = 55
FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE = 64
FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE = 45
FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE = 52
FASTDIS_TSPI_PDU_TYPE = 46
FASTDIS_TSPI_FIXED_SIZE = 56
FASTDIS_APPEARANCE_PDU_TYPE = 47
FASTDIS_APPEARANCE_FIXED_SIZE = 56
FASTDIS_ARTICULATED_PARTS_PDU_TYPE = 48
FASTDIS_ARTICULATED_PARTS_FIXED_SIZE = 20
FASTDIS_LE_FIRE_PDU_TYPE = 49
FASTDIS_LE_FIRE_FIXED_SIZE = 60
FASTDIS_LE_DETONATION_PDU_TYPE = 50
FASTDIS_LE_DETONATION_FIXED_SIZE = 72
FASTDIS_SERVICE_REQUEST_PDU_TYPE = 5
FASTDIS_SERVICE_REQUEST_FIXED_SIZE = 28
FASTDIS_RESUPPLY_OFFER_PDU_TYPE = 6
FASTDIS_RESUPPLY_OFFER_FIXED_SIZE = 28
FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE = 7
FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE = 28
FASTDIS_RESUPPLY_CANCEL_PDU_TYPE = 8
FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE = 24
FASTDIS_REPAIR_COMPLETE_PDU_TYPE = 9
FASTDIS_REPAIR_COMPLETE_FIXED_SIZE = 28
FASTDIS_REPAIR_RESPONSE_PDU_TYPE = 10
FASTDIS_REPAIR_RESPONSE_FIXED_SIZE = 28
FASTDIS_CREATE_ENTITY_PDU_TYPE = 11
FASTDIS_CREATE_ENTITY_FIXED_SIZE = 28
FASTDIS_REMOVE_ENTITY_PDU_TYPE = 12
FASTDIS_REMOVE_ENTITY_FIXED_SIZE = 28
FASTDIS_START_RESUME_PDU_TYPE = 13
FASTDIS_START_RESUME_FIXED_SIZE = 44
FASTDIS_STOP_FREEZE_PDU_TYPE = 14
FASTDIS_STOP_FREEZE_FIXED_SIZE = 40
FASTDIS_ACKNOWLEDGE_PDU_TYPE = 15
FASTDIS_ACKNOWLEDGE_FIXED_SIZE = 30
FASTDIS_ACTION_REQUEST_PDU_TYPE = 16
FASTDIS_ACTION_REQUEST_FIXED_SIZE = 40
FASTDIS_ACTION_RESPONSE_PDU_TYPE = 17
FASTDIS_ACTION_RESPONSE_FIXED_SIZE = 40
FASTDIS_DATA_QUERY_PDU_TYPE = 18
FASTDIS_DATA_QUERY_FIXED_SIZE = 44
FASTDIS_SET_DATA_PDU_TYPE = 19
FASTDIS_SET_DATA_FIXED_SIZE = 40
FASTDIS_DATA_PDU_TYPE = 20
FASTDIS_DATA_FIXED_SIZE = 40
FASTDIS_EVENT_REPORT_PDU_TYPE = 21
FASTDIS_EVENT_REPORT_FIXED_SIZE = 40
FASTDIS_COMMENT_PDU_TYPE = 22
FASTDIS_COMMENT_FIXED_SIZE = 32
FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE = 51
FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE = 32
FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE = 52
FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE = 32
FASTDIS_START_RESUME_RELIABLE_PDU_TYPE = 53
FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE = 48
FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE = 54
FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE = 36
FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE = 55
FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE = 30
FASTDIS_ACTION_REQUEST_RELIABLE_PDU_TYPE = 56
FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE = 44
FASTDIS_ACTION_RESPONSE_RELIABLE_PDU_TYPE = 57
FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE = 40
FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE = 58
FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE = 48
FASTDIS_SET_DATA_RELIABLE_PDU_TYPE = 59
FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE = 40
FASTDIS_DATA_RELIABLE_PDU_TYPE = 60
FASTDIS_DATA_RELIABLE_FIXED_SIZE = 40
FASTDIS_EVENT_REPORT_RELIABLE_PDU_TYPE = 61
FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE = 40
FASTDIS_COMMENT_RELIABLE_PDU_TYPE = 62
FASTDIS_COMMENT_RELIABLE_FIXED_SIZE = 32
FASTDIS_RECORD_RELIABLE_PDU_TYPE = 63
FASTDIS_RECORD_RELIABLE_FIXED_SIZE = 36
FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE = 64
FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE = 40
FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE = 65
FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE = 42
FASTDIS_COLLISION_ELASTIC_PDU_TYPE = 66
FASTDIS_COLLISION_ELASTIC_FIXED_SIZE = 100
FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE = 67
FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE = 72
FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE = 68
FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE = 90
FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE = 69
FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE = 36
FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE = 70
FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE = 56
FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE = 71
FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE = 40
FASTDIS_ATTRIBUTE_PDU_TYPE = 72
FASTDIS_ATTRIBUTE_FIXED_SIZE = 32

FASTDIS_OK = 0
FASTDIS_ERR_BAD_ARGUMENT = -1
FASTDIS_ERR_SHORT_PACKET = -2
FASTDIS_ERR_LENGTH_TOO_SMALL = -3
FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER = -4
FASTDIS_ERR_CALLBACK_STOPPED = -5
FASTDIS_ERR_UNSUPPORTED_PDU = -6
FASTDIS_ERR_OUT_OF_MEMORY = -7
FASTDIS_ERR_NOT_FOUND = -8
FASTDIS_ERR_BUSY = -9
FASTDIS_FLAG_ALLOW_TRUNCATED = 1 << 0

FASTDIS_FILTER_VERSIONS = 1
FASTDIS_FILTER_PDU_TYPES = 2
FASTDIS_FILTER_PROTOCOL_FAMILIES = 3
FASTDIS_FILTER_EXERCISE_IDS = 4
FASTDIS_FILTER_ENTITY_FORCE_IDS = 5
FASTDIS_FILTER_VERSION = FASTDIS_FILTER_VERSIONS
FASTDIS_FILTER_PDU_TYPE = FASTDIS_FILTER_PDU_TYPES
FASTDIS_FILTER_PROTOCOL_FAMILY = FASTDIS_FILTER_PROTOCOL_FAMILIES
FASTDIS_FILTER_EXERCISE_ID = FASTDIS_FILTER_EXERCISE_IDS
FASTDIS_FILTER_ENTITY_FORCE_ID = FASTDIS_FILTER_ENTITY_FORCE_IDS

FASTDIS_PROFILE_HEADER_COUNTING = 1
FASTDIS_PROFILE_ENTITY_STATE_ROUTING = 2
FASTDIS_PROFILE_ENTITY_STATE_POSE = 3
FASTDIS_PROFILE_ENTITY_STATE_FULL = 4
FASTDIS_PROFILE_ENTITY_TRANSFORM = 5

_PROFILE_NAMES = {
    "header": FASTDIS_PROFILE_HEADER_COUNTING,
    "header_counting": FASTDIS_PROFILE_HEADER_COUNTING,
    "entity_state_routing": FASTDIS_PROFILE_ENTITY_STATE_ROUTING,
    "routing": FASTDIS_PROFILE_ENTITY_STATE_ROUTING,
    "entity_state_pose": FASTDIS_PROFILE_ENTITY_STATE_POSE,
    "pose": FASTDIS_PROFILE_ENTITY_STATE_POSE,
    "entity_state_full": FASTDIS_PROFILE_ENTITY_STATE_FULL,
    "full": FASTDIS_PROFILE_ENTITY_STATE_FULL,
    "entity_transform": FASTDIS_PROFILE_ENTITY_TRANSFORM,
    "transform": FASTDIS_PROFILE_ENTITY_TRANSFORM,
}

_FILTER_KIND_NAMES = {
    "version": FASTDIS_FILTER_VERSION,
    "versions": FASTDIS_FILTER_VERSION,
    "pdu_type": FASTDIS_FILTER_PDU_TYPE,
    "pdu_types": FASTDIS_FILTER_PDU_TYPE,
    "protocol_family": FASTDIS_FILTER_PROTOCOL_FAMILY,
    "protocol_families": FASTDIS_FILTER_PROTOCOL_FAMILY,
    "family": FASTDIS_FILTER_PROTOCOL_FAMILY,
    "families": FASTDIS_FILTER_PROTOCOL_FAMILY,
    "exercise_id": FASTDIS_FILTER_EXERCISE_ID,
    "exercise_ids": FASTDIS_FILTER_EXERCISE_ID,
    "entity_force_id": FASTDIS_FILTER_ENTITY_FORCE_ID,
    "entity_force_ids": FASTDIS_FILTER_ENTITY_FORCE_ID,
    "force_id": FASTDIS_FILTER_ENTITY_FORCE_ID,
    "force_ids": FASTDIS_FILTER_ENTITY_FORCE_ID,
}

FASTDIS_ES_FIELD_HEADER = 0x0000000000000001
FASTDIS_ES_FIELD_ENTITY_ID = 0x0000000000000002
FASTDIS_ES_FIELD_FORCE_ID = 0x0000000000000004
FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT = 0x0000000000000008
FASTDIS_ES_FIELD_ENTITY_TYPE = 0x0000000000000010
FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE = 0x0000000000000020
FASTDIS_ES_FIELD_LINEAR_VELOCITY = 0x0000000000000040
FASTDIS_ES_FIELD_LOCATION = 0x0000000000000080
FASTDIS_ES_FIELD_ORIENTATION = 0x0000000000000100
FASTDIS_ES_FIELD_APPEARANCE = 0x0000000000000200
FASTDIS_ES_FIELD_DEAD_RECKONING = 0x0000000000000400
FASTDIS_ES_FIELD_MARKING = 0x0000000000000800
FASTDIS_ES_FIELD_CAPABILITIES = 0x0000000000001000
FASTDIS_ES_FIELD_ROUTING = FASTDIS_ES_FIELD_HEADER | FASTDIS_ES_FIELD_ENTITY_ID | FASTDIS_ES_FIELD_FORCE_ID
FASTDIS_ES_FIELD_POSE = (
    FASTDIS_ES_FIELD_ENTITY_ID
    | FASTDIS_ES_FIELD_FORCE_ID
    | FASTDIS_ES_FIELD_LOCATION
    | FASTDIS_ES_FIELD_ORIENTATION
)
FASTDIS_ES_FIELD_KINEMATICS = FASTDIS_ES_FIELD_LINEAR_VELOCITY | FASTDIS_ES_FIELD_DEAD_RECKONING
FASTDIS_ES_FIELD_ALL = (
    FASTDIS_ES_FIELD_HEADER
    | FASTDIS_ES_FIELD_ENTITY_ID
    | FASTDIS_ES_FIELD_FORCE_ID
    | FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT
    | FASTDIS_ES_FIELD_ENTITY_TYPE
    | FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE
    | FASTDIS_ES_FIELD_LINEAR_VELOCITY
    | FASTDIS_ES_FIELD_LOCATION
    | FASTDIS_ES_FIELD_ORIENTATION
    | FASTDIS_ES_FIELD_APPEARANCE
    | FASTDIS_ES_FIELD_DEAD_RECKONING
    | FASTDIS_ES_FIELD_MARKING
    | FASTDIS_ES_FIELD_CAPABILITIES
)

FASTDIS_ENTITY_ID_FILTER_DISABLED = 0
FASTDIS_ENTITY_ID_FILTER_ALLOW = 1
FASTDIS_ENTITY_ID_FILTER_BLOCK = 2

FASTDIS_ENTITY_CHANGE_NONE = 0x00000000
FASTDIS_ENTITY_CHANGE_NEW = 0x00000001
FASTDIS_ENTITY_CHANGE_UPDATED = 0x00000002
FASTDIS_ENTITY_CHANGE_STALE = 0x00000004
FASTDIS_ENTITY_CHANGE_REMOVED = 0x00000008
FASTDIS_ENTITY_CHANGE_UNCHANGED = 0x00000010
FASTDIS_ENTITY_CHANGE_EXTRAPOLATED = 0x00000020

FASTDIS_DR_OTHER = 0
FASTDIS_DR_STATIC = 1
FASTDIS_DR_FPW = 2
FASTDIS_DR_RPW = 3
FASTDIS_DR_RVW = 4
FASTDIS_DR_FVW = 5
FASTDIS_DR_FPB = 6
FASTDIS_DR_RPB = 7
FASTDIS_DR_RVB = 8
FASTDIS_DR_FVB = 9

_ENTITY_STATE_FIELD_NAMES = {
    "header": FASTDIS_ES_FIELD_HEADER,
    "entity_id": FASTDIS_ES_FIELD_ENTITY_ID,
    "entity": FASTDIS_ES_FIELD_ENTITY_ID,
    "force_id": FASTDIS_ES_FIELD_FORCE_ID,
    "force": FASTDIS_ES_FIELD_FORCE_ID,
    "variable_parameter_count": FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT,
    "variable_parameters": FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT,
    "entity_type": FASTDIS_ES_FIELD_ENTITY_TYPE,
    "alternate_entity_type": FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE,
    "alt_entity_type": FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE,
    "linear_velocity": FASTDIS_ES_FIELD_LINEAR_VELOCITY,
    "velocity": FASTDIS_ES_FIELD_LINEAR_VELOCITY,
    "location": FASTDIS_ES_FIELD_LOCATION,
    "position": FASTDIS_ES_FIELD_LOCATION,
    "orientation": FASTDIS_ES_FIELD_ORIENTATION,
    "appearance": FASTDIS_ES_FIELD_APPEARANCE,
    "dead_reckoning": FASTDIS_ES_FIELD_DEAD_RECKONING,
    "marking": FASTDIS_ES_FIELD_MARKING,
    "capabilities": FASTDIS_ES_FIELD_CAPABILITIES,
    "routing": FASTDIS_ES_FIELD_ROUTING,
    "pose": FASTDIS_ES_FIELD_POSE,
    "kinematics": FASTDIS_ES_FIELD_KINEMATICS,
    "all": FASTDIS_ES_FIELD_ALL,
}

HeaderTuple = tuple[int, int, int, int, int, int, int, int]
EntityIdTuple = tuple[int, int, int]
EntityTypeTuple = tuple[int, int, int, int, int, int, int]
BurstDescriptorTuple = tuple[EntityTypeTuple, int, int, int, int]
Vec3fTuple = tuple[float, float, float]
WorldCoordinatesTuple = tuple[float, float, float]
EulerAnglesTuple = tuple[float, float, float]
ClockTimeTuple = tuple[int, int]
EventIdTuple = tuple[int, int, int]
PacketCallback = Callable[[int, int, int, int, int, int, int, object], object]
EntityStateCallback = Callable[["EntityStatePrefix", object], object]


class FastDisError(RuntimeError):
    """Raised when the native C ABI reports an error."""


class EntityStatePrefix(NamedTuple):
    """Python value view of the fixed Entity State PDU prefix."""

    header: HeaderTuple
    entity_id: EntityIdTuple
    force_id: int
    variable_parameter_count: int
    entity_type: EntityTypeTuple
    alternate_entity_type: EntityTypeTuple
    linear_velocity: Vec3fTuple
    location: WorldCoordinatesTuple
    orientation: EulerAnglesTuple
    appearance: int
    dead_reckoning_algorithm: int
    dead_reckoning_parameters: bytes
    dead_reckoning_linear_acceleration: Vec3fTuple
    dead_reckoning_angular_velocity: Vec3fTuple
    marking_character_set: int
    marking: bytes
    capabilities: int
    fields_present: int

    def has_field(self, field_mask: int) -> bool:
        """Return True when every bit in ``field_mask`` was decoded."""

        return (self.fields_present & int(field_mask)) == int(field_mask)

    @property
    def marking_text(self) -> str:
        """Best-effort UTF-8/ASCII marking with NUL padding stripped."""

        raw = self.marking.split(b"\x00", 1)[0]
        return raw.decode("utf-8", errors="replace")


class EntityTransform(NamedTuple):
    """Engine-shaped Entity State transform value."""

    entity_id: EntityIdTuple
    force_id: int
    exercise_id: int
    version: int
    timestamp: int
    appearance: int
    location: WorldCoordinatesTuple
    orientation: EulerAnglesTuple
    linear_velocity: Vec3fTuple
    fields_present: int
    dead_reckoning_algorithm: int
    dead_reckoning_parameters: bytes
    dead_reckoning_linear_acceleration: Vec3fTuple
    dead_reckoning_angular_velocity: Vec3fTuple


class SimulationManagementRequest(NamedTuple):
    """Python value view of Create Entity and Remove Entity PDUs."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int


class StartResume(NamedTuple):
    """Python value view of a Start/Resume PDU."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    real_world_time: ClockTimeTuple
    simulation_time: ClockTimeTuple
    request_id: int


class StopFreeze(NamedTuple):
    """Python value view of a Stop/Freeze PDU."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    real_world_time: ClockTimeTuple
    reason: int
    frozen_behavior: int
    padding1: int
    request_id: int


class Acknowledge(NamedTuple):
    """Python value view of an Acknowledge PDU."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    acknowledge_flag: int
    response_flag: int
    request_id: int


class SimulationManagementReliableRequest(NamedTuple):
    """Python value view of fixed-size reliable Create/Remove Entity PDUs."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    required_reliability_service: int
    pad1: int
    pad2: int
    request_id: int


class StartResumeReliable(NamedTuple):
    """Python value view of a Start/Resume Reliable PDU."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    real_world_time: ClockTimeTuple
    simulation_time: ClockTimeTuple
    required_reliability_service: int
    pad1: int
    pad2: int
    request_id: int


class StopFreezeReliable(NamedTuple):
    """Python value view of a Stop/Freeze Reliable PDU."""

    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    real_world_time: ClockTimeTuple
    reason: int
    frozen_behavior: int
    required_reliablity_service: int
    pad1: int
    request_id: int


class ActionRequest(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    action_id: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class ActionResponse(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    request_status: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class DataQuery(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    time_interval: ClockTimeTuple
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class SetData(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    padding1: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class EventReport(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    event_type: int
    padding1: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class Comment(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class ActionRequestReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    required_reliability_service: int
    pad1: int
    pad2: int
    request_id: int
    action_id: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class ActionResponseReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    response_status: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class DataQueryReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    required_reliability_service: int
    pad1: int
    pad2: int
    request_id: int
    time_interval: ClockTimeTuple
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class SetDataReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    required_reliability_service: int
    pad1: int
    pad2: int
    request_id: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class DataReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    pad1: int
    pad2: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class EventReportReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    event_type: int
    pad1: int
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class CommentReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    number_of_fixed_datum_records: int
    number_of_variable_datum_records: int
    datum_record_bytes: bytes


class RecordReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    pad1: int
    event_type: int
    record_set_count: int
    record_set_bytes: bytes


class SetRecordReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    pad1: int
    pad2: int
    record_set_count: int
    record_set_bytes: bytes


class RecordQueryReliable(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    pad1: int
    pad2: int
    event_type: int
    time: int
    record_id_count: int
    record_id_bytes: bytes


class Designator(NamedTuple):
    header: HeaderTuple
    designating_entity_id: EntityIdTuple
    code_name: int
    designated_entity_id: EntityIdTuple
    designator_code: int
    designator_power: float
    designator_wavelength: float
    designator_spot_wrt_designated: Vec3fTuple
    designator_spot_location: WorldCoordinatesTuple
    dead_reckoning_algorithm: int
    padding1: int
    padding2: int
    entity_linear_acceleration: Vec3fTuple


class Transmitter(NamedTuple):
    header: HeaderTuple
    entity_id: EntityIdTuple
    radio_id: int
    radio_entity_type: tuple[int, int, int, int, int, int]
    entity_type: EntityTypeTuple
    transmit_state: int
    input_source: int
    variable_transmitter_parameter_count: int
    antenna_location: WorldCoordinatesTuple
    relative_antenna_location: Vec3fTuple
    antenna_pattern_type: int
    antenna_pattern_count: int
    frequency: int
    transmit_frequency_bandwidth: float
    power: float
    modulation_type: tuple[int, int, int, int]
    crypto_system: int
    crypto_key_id: int
    modulation_parameter_count: int
    padding2: int
    padding3: int
    modulation_parameter_bytes: bytes
    antenna_pattern_bytes: bytes


class OtherPdu(NamedTuple):
    header: HeaderTuple
    opaque_payload_bytes: bytes


class AggregateState(NamedTuple):
    header: HeaderTuple
    aggregate_id: EntityIdTuple
    force_id: int
    aggregate_state: int
    aggregate_type: EntityTypeTuple
    formation: int
    aggregate_marking_character_set: int
    aggregate_marking: bytes
    dimensions: Vec3fTuple
    orientation: EulerAnglesTuple
    center_of_mass: WorldCoordinatesTuple
    velocity: Vec3fTuple
    number_of_dis_aggregates: int
    number_of_dis_entities: int
    number_of_silent_aggregate_types: int
    number_of_silent_entity_types: int
    aggregate_record_bytes: bytes


class IsGroupOf(NamedTuple):
    header: HeaderTuple
    group_entity_id: EntityIdTuple
    grouped_entity_category: int
    number_of_grouped_entities: int
    pad2: int
    latitude: float
    longitude: float
    grouped_entity_description_bytes: bytes


class TransferControlRequest(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    transfer_type: int
    transfer_entity_id: EntityIdTuple
    number_of_record_sets: int
    record_set_bytes: bytes


class TransferOwnership(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    request_id: int
    required_reliability_service: int
    transfer_type: int
    transfer_entity_id: EntityIdTuple
    number_of_record_sets: int
    record_set_bytes: bytes


class IsPartOf(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    receiving_entity_id: EntityIdTuple
    relationship: tuple[int, int]
    part_location: Vec3fTuple
    named_location: tuple[int, int]
    part_entity_type: EntityTypeTuple


class MinefieldState(NamedTuple):
    header: HeaderTuple
    minefield_id: EntityIdTuple
    minefield_sequence: int
    force_id: int
    number_of_perimeter_points: int
    minefield_type: EntityTypeTuple
    number_of_mine_types: int
    minefield_location: WorldCoordinatesTuple
    minefield_orientation: EulerAnglesTuple
    appearance: int
    protocol_mode: int
    perimeter_point_bytes: bytes
    mine_type_bytes: bytes


class MinefieldQuery(NamedTuple):
    header: HeaderTuple
    minefield_id: EntityIdTuple
    requesting_entity_id: EntityIdTuple
    request_id: int
    number_of_perimeter_points: int
    pad2: int
    number_of_sensor_types: int
    data_filter: int
    requested_mine_type: EntityTypeTuple
    requested_perimeter_point_bytes: bytes
    sensor_type_bytes: bytes


class MinefieldData(NamedTuple):
    header: HeaderTuple
    minefield_id: EntityIdTuple
    requesting_entity_id: EntityIdTuple
    minefield_sequence_number: int
    request_id: int
    pdu_sequence_number: int
    number_of_pdus: int
    number_of_mines_in_this_pdu: int
    number_of_sensor_types: int
    pad2: int
    data_filter: int
    mine_type: EntityTypeTuple
    pad3: int
    sensor_type_bytes: bytes
    mine_location_bytes: bytes


class MinefieldResponseNack(NamedTuple):
    header: HeaderTuple
    minefield_id: EntityIdTuple
    requesting_entity_id: EntityIdTuple
    request_id: int
    number_of_missing_pdus: int
    missing_pdu_sequence_number_bytes: bytes


class EnvironmentalProcess(NamedTuple):
    header: HeaderTuple
    environmental_process_id: EntityIdTuple
    environment_type: EntityTypeTuple
    model_type: int
    environment_status: int
    number_of_environment_records: int
    sequence_number: int
    environment_record_bytes: bytes


class GriddedData(NamedTuple):
    header: HeaderTuple
    environmental_simulation_application_id: EntityIdTuple
    field_number: int
    pdu_number: int
    pdu_total: int
    coordinate_system: int
    number_of_grid_axes: int
    constant_grid: int
    environment_type: EntityTypeTuple
    orientation: EulerAnglesTuple
    sample_time: int
    total_values: int
    vector_dimension: int
    padding1: int
    padding2: int
    grid_data_bytes: bytes


class PointObjectState(NamedTuple):
    header: HeaderTuple
    object_id: EntityIdTuple
    referenced_object_id: EntityIdTuple
    update_number: int
    force_id: int
    modifications: int
    object_type: tuple[int, int, int, int, int]
    object_location: WorldCoordinatesTuple
    object_orientation: EulerAnglesTuple
    object_appearance: float
    requester_id: tuple[int, int]
    receiving_id: tuple[int, int]
    pad2: int


class LinearObjectState(NamedTuple):
    header: HeaderTuple
    object_id: EntityIdTuple
    referenced_object_id: EntityIdTuple
    update_number: int
    force_id: int
    number_of_segments: int
    requester_id: tuple[int, int]
    receiving_id: tuple[int, int]
    object_type: tuple[int, int, int, int, int]
    linear_segment_parameter_bytes: bytes


class ArealObjectState(NamedTuple):
    header: HeaderTuple
    object_id: EntityIdTuple
    referenced_object_id: EntityIdTuple
    update_number: int
    force_id: int
    modifications: int
    object_type: EntityTypeTuple
    object_appearance_bytes: bytes
    number_of_points: int
    requester_id: tuple[int, int]
    receiving_id: tuple[int, int]
    object_location_bytes: bytes


class Tspi(NamedTuple):
    header: HeaderTuple
    live_entity_id: tuple[int, int, int]
    tspi_flag: int
    entity_location_bytes: bytes
    entity_linear_velocity_bytes: bytes
    entity_orientation_bytes: bytes
    position_error_bytes: bytes
    orientation_error_bytes: bytes
    dead_reckoning_parameter_bytes: bytes
    measured_speed: int
    system_specific_data_length: int
    system_specific_data: bytes


class LiveEntityAppearance(NamedTuple):
    header: HeaderTuple
    live_entity_id: tuple[int, int, int]
    appearance_flags: int
    force_id: int
    padding1: int
    entity_type: EntityTypeTuple
    alternate_entity_type: EntityTypeTuple
    entity_marking: bytes
    capabilities: int
    appearance_field_bytes: bytes


class ArticulatedParts(NamedTuple):
    header: HeaderTuple
    live_entity_id: tuple[int, int, int]
    number_of_parameter_records: int
    padding: bytes
    variable_parameter_bytes: bytes


class LeFire(NamedTuple):
    header: HeaderTuple
    firing_live_entity_id: tuple[int, int, int]
    flags: int
    padding1: int
    target_live_entity_id: tuple[int, int, int]
    munition_live_entity_id: tuple[int, int, int]
    event_id: tuple[int, int, int]
    location_bytes: bytes
    munition_descriptor: BurstDescriptorTuple
    velocity_bytes: bytes
    range: int


class LeDetonation(NamedTuple):
    header: HeaderTuple
    firing_live_entity_id: tuple[int, int, int]
    detonation_flag1: int
    detonation_flag2: int
    target_live_entity_id: tuple[int, int, int]
    munition_live_entity_id: tuple[int, int, int]
    event_id: tuple[int, int, int]
    world_location_bytes: bytes
    velocity_bytes: bytes
    munition_orientation_bytes: bytes
    munition_descriptor: BurstDescriptorTuple
    entity_location_bytes: bytes
    detonation_result: int
    padding1: int


class Signal(NamedTuple):
    header: HeaderTuple
    entity_id: EntityIdTuple
    radio_id: int
    encoding_scheme: int
    tdl_type: int
    sample_rate: int
    data_length: int
    samples: int
    data_bytes: bytes


class Receiver(NamedTuple):
    header: HeaderTuple
    entity_id: EntityIdTuple
    radio_id: int
    receiver_state: int
    padding1: int
    received_power: float
    transmitter_entity_id: EntityIdTuple
    transmitter_radio_id: int


class ElectronicEmissions(NamedTuple):
    header: HeaderTuple
    emitting_entity_id: EntityIdTuple
    event_id: EventIdTuple
    state_update_indicator: int
    number_of_systems: int
    padding1: int
    system_record_bytes: bytes


class IffAtcNavAidsLayer1(NamedTuple):
    header: HeaderTuple
    emitting_entity_id: EntityIdTuple
    event_id: EventIdTuple
    location: Vec3fTuple
    system_id: tuple[int, int, int, int]
    padding2: int
    fundamental_parameters: tuple[int, int, int, int, int, int, int, int, int, int]


class Iff(NamedTuple):
    header: HeaderTuple
    emitting_entity_id: EntityIdTuple
    event_id: EventIdTuple
    location: Vec3fTuple
    system_id: tuple[int, int, int, int]
    padding2: int
    fundamental_parameters: tuple[int, int, int, int, int, int, int, int, int, int]


class Ua(NamedTuple):
    header: HeaderTuple
    emitting_entity_id: EntityIdTuple
    event_id: EventIdTuple
    state_change_indicator: int
    padding1: int
    passive_parameter_index: int
    propulsion_plant_configuration: int
    number_of_shafts: int
    number_of_apas: int
    number_of_ua_emitter_systems: int
    ua_record_bytes: bytes


class Sees(NamedTuple):
    header: HeaderTuple
    originating_entity_id: EntityIdTuple
    infrared_signature_representation_index: int
    acoustic_signature_representation_index: int
    radar_cross_section_signature_representation_index: int
    number_of_propulsion_systems: int
    number_of_vectoring_nozzle_systems: int
    supplemental_emission_record_bytes: bytes


class IntercomSignal(NamedTuple):
    header: HeaderTuple
    entity_id: EntityIdTuple
    communications_device_id: int
    encoding_scheme: int
    tdl_type: int
    sample_rate: int
    data_length: int
    samples: int
    data_bytes: bytes


class IntercomControl(NamedTuple):
    header: HeaderTuple
    control_type: int
    communications_channel_type: int
    source_entity_id: EntityIdTuple
    source_communications_device_id: int
    source_line_id: int
    transmit_priority: int
    transmit_line_state: int
    command: int
    master_entity_id: EntityIdTuple
    master_communications_device_id: int
    intercom_parameters_length: int
    intercom_parameters_bytes: bytes


class Attribute(NamedTuple):
    header: HeaderTuple
    originating_simulation_address: tuple[int, int]
    padding1: int
    padding2: int
    attribute_record_pdu_type: int
    attribute_record_protocol_version: int
    master_attribute_record_type: int
    action_code: int
    padding3: int
    number_attribute_record_set: int
    attribute_record_set_bytes: bytes


class DirectedEnergyFire(NamedTuple):
    header: HeaderTuple
    firing_entity_id: EntityIdTuple
    target_entity_id: EntityIdTuple
    munition_type: EntityTypeTuple
    shot_start_time: ClockTimeTuple
    commulative_shot_time: float
    aperture_emitter_location: Vec3fTuple
    aperture_diameter: float
    wavelength: float
    peak_irradiance: float
    pulse_repetition_frequency: float
    pulse_width: int
    flags: int
    pulse_shape: int
    padding1: int
    padding2: int
    padding3: int
    number_of_de_records: int
    de_record_bytes: bytes


class EntityDamageStatus(NamedTuple):
    header: HeaderTuple
    firing_entity_id: EntityIdTuple
    target_entity_id: EntityIdTuple
    damaged_entity_id: EntityIdTuple
    padding1: int
    padding2: int
    number_of_damage_description: int
    damage_description_bytes: bytes


class InformationOperationsAction(NamedTuple):
    header: HeaderTuple
    originating_sim_id: EntityIdTuple
    receiving_sim_id: EntityIdTuple
    request_id: int
    io_warfare_type: int
    io_simulation_source: int
    io_action_type: int
    io_action_phase: int
    padding1: int
    io_attacker_id: EntityIdTuple
    io_primary_target_id: EntityIdTuple
    padding2: int
    number_of_io_records: int
    io_record_bytes: bytes


class InformationOperationsReport(NamedTuple):
    header: HeaderTuple
    originating_sim_id: EntityIdTuple
    io_sim_source: int
    io_report_type: int
    padding1: int
    io_attacker_id: EntityIdTuple
    io_primary_target_id: EntityIdTuple
    padding2: int
    padding3: int
    number_of_io_records: int
    io_record_bytes: bytes


class ServiceRequest(NamedTuple):
    header: HeaderTuple
    requesting_entity_id: EntityIdTuple
    servicing_entity_id: EntityIdTuple
    service_type_requested: int
    number_of_supply_types: int
    service_request_padding: int
    supply_bytes: bytes


class ResupplyOffer(NamedTuple):
    header: HeaderTuple
    receiving_entity_id: EntityIdTuple
    supplying_entity_id: EntityIdTuple
    number_of_supply_types: int
    padding_bytes: bytes
    supply_bytes: bytes


class ResupplyReceived(NamedTuple):
    header: HeaderTuple
    receiving_entity_id: EntityIdTuple
    supplying_entity_id: EntityIdTuple
    number_of_supply_types: int
    padding1: int
    padding2: int
    supply_bytes: bytes


class ResupplyCancel(NamedTuple):
    header: HeaderTuple
    receiving_entity_id: EntityIdTuple
    supplying_entity_id: EntityIdTuple


class RepairComplete(NamedTuple):
    header: HeaderTuple
    receiving_entity_id: EntityIdTuple
    repairing_entity_id: EntityIdTuple
    repair: int
    padding2: int


class RepairResponse(NamedTuple):
    header: HeaderTuple
    receiving_entity_id: EntityIdTuple
    repairing_entity_id: EntityIdTuple
    repair_result: int
    padding1: int
    padding2: int


class Fire(NamedTuple):
    """Python value view of a Fire PDU fixed body."""

    header: HeaderTuple
    firing_entity_id: EntityIdTuple
    target_entity_id: EntityIdTuple
    munition_entity_id: EntityIdTuple
    event_id: EventIdTuple
    fire_mission_index: int
    world_location: WorldCoordinatesTuple
    munition_type: EntityTypeTuple
    warhead: int
    fuse: int
    quantity: int
    rate: int
    velocity: Vec3fTuple
    range_to_target: float


class Detonation(NamedTuple):
    """Python value view of a Detonation PDU fixed body."""

    header: HeaderTuple
    firing_entity_id: EntityIdTuple
    target_entity_id: EntityIdTuple
    exploding_entity_id: EntityIdTuple
    event_id: EventIdTuple
    velocity: Vec3fTuple
    world_location: WorldCoordinatesTuple
    munition_type: EntityTypeTuple
    warhead: int
    fuse: int
    quantity: int
    rate: int
    location_in_entity_coordinates: Vec3fTuple
    detonation_result: int
    variable_parameter_count: int
    padding1: int


class Collision(NamedTuple):
    """Python value view of a Collision PDU fixed body."""

    header: HeaderTuple
    issuing_entity_id: EntityIdTuple
    colliding_entity_id: EntityIdTuple
    event_id: EventIdTuple
    collision_type: int
    padding1: int
    velocity: Vec3fTuple
    mass: float
    location: Vec3fTuple


class CollisionElastic(NamedTuple):
    """Python value view of a Collision Elastic PDU fixed body."""

    header: HeaderTuple
    issuing_entity_id: EntityIdTuple
    colliding_entity_id: EntityIdTuple
    event_id: EventIdTuple
    padding1: int
    contact_velocity: Vec3fTuple
    mass: float
    location: Vec3fTuple
    collision_result_xx: float
    collision_result_xy: float
    collision_result_xz: float
    collision_result_yy: float
    collision_result_yz: float
    collision_result_zz: float
    unit_surface_normal: Vec3fTuple
    coefficient_of_restitution: float


class EntitySnapshot(NamedTuple):
    """Latest-state table snapshot for one entity."""

    transform: EntityTransform
    first_seen_tick: int
    last_seen_tick: int
    update_count: int
    change_flags: int

    def has_change(self, flag: int) -> bool:
        return (self.change_flags & int(flag)) == int(flag)


@dataclass(frozen=True)
class EntitySnapshotView:
    """Python copy of a native double-buffer snapshot view."""

    snapshots: tuple[EntitySnapshot, ...]
    count: int
    dropped: int
    generation: int
    slot: int


class SnapshotBufferStats(NamedTuple):
    """Snapshot-buffer publish and reader pressure counters."""

    publish_attempts: int
    publish_successes: int
    publish_busy: int
    acquire_count: int
    release_count: int
    max_snapshot_count: int
    dropped_snapshots: int

    def as_dict(self) -> dict[str, int]:
        return self._asdict()


class FastDisHeader(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint8),
        ("exercise_id", ctypes.c_uint8),
        ("pdu_type", ctypes.c_uint8),
        ("protocol_family", ctypes.c_uint8),
        ("timestamp", ctypes.c_uint32),
        ("length", ctypes.c_uint16),
        ("status", ctypes.c_int16),
        ("padding", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),  # natural C padding on common ABIs
    ]

    def as_tuple(self) -> HeaderTuple:
        return (
            int(self.version),
            int(self.exercise_id),
            int(self.pdu_type),
            int(self.protocol_family),
            int(self.timestamp),
            int(self.length),
            int(self.status),
            int(self.padding),
        )

    @property
    def has_pdu_status(self) -> bool:
        return int(self.version) >= FASTDIS_PROTOCOL_VERSION_DIS7

    @property
    def pdu_status(self) -> int | None:
        return int(self.status) if self.has_pdu_status else None

    @property
    def padding_octet(self) -> int | None:
        return int(self.padding) if self.has_pdu_status else None

    @property
    def legacy_padding(self) -> int | None:
        return None if self.has_pdu_status else int(self.padding)


class FastDisEntityId(ctypes.Structure):
    _fields_ = [
        ("site", ctypes.c_uint16),
        ("application", ctypes.c_uint16),
        ("entity", ctypes.c_uint16),
    ]

    def as_tuple(self) -> EntityIdTuple:
        return (int(self.site), int(self.application), int(self.entity))


class FastDisEntityType(ctypes.Structure):
    _fields_ = [
        ("entity_kind", ctypes.c_uint8),
        ("domain", ctypes.c_uint8),
        ("country", ctypes.c_uint16),
        ("category", ctypes.c_uint8),
        ("subcategory", ctypes.c_uint8),
        ("specific", ctypes.c_uint8),
        ("extra", ctypes.c_uint8),
    ]

    def as_tuple(self) -> EntityTypeTuple:
        return (
            int(self.entity_kind),
            int(self.domain),
            int(self.country),
            int(self.category),
            int(self.subcategory),
            int(self.specific),
            int(self.extra),
        )


class FastDisVec3f(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]

    def as_tuple(self) -> Vec3fTuple:
        return (float(self.x), float(self.y), float(self.z))


class FastDisWorldCoordinates(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]

    def as_tuple(self) -> WorldCoordinatesTuple:
        return (float(self.x), float(self.y), float(self.z))


class FastDisEulerAngles(ctypes.Structure):
    _fields_ = [("psi", ctypes.c_float), ("theta", ctypes.c_float), ("phi", ctypes.c_float)]

    def as_tuple(self) -> EulerAnglesTuple:
        return (float(self.psi), float(self.theta), float(self.phi))


class FastDisClockTime(ctypes.Structure):
    _fields_ = [("hour", ctypes.c_uint32), ("time_past_hour", ctypes.c_uint32)]

    def as_tuple(self) -> ClockTimeTuple:
        return (int(self.hour), int(self.time_past_hour))


class FastDisEventId(ctypes.Structure):
    _fields_ = [
        ("site", ctypes.c_uint16),
        ("application", ctypes.c_uint16),
        ("event_number", ctypes.c_uint16),
    ]

    def as_tuple(self) -> EventIdTuple:
        return (int(self.site), int(self.application), int(self.event_number))


class FastDisLiveEntityId(ctypes.Structure):
    _fields_ = [
        ("site", ctypes.c_uint8),
        ("application", ctypes.c_uint8),
        ("entity", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int, int]:
        return (int(self.site), int(self.application), int(self.entity))


class FastDisLiveEventId(ctypes.Structure):
    _fields_ = [
        ("site", ctypes.c_uint8),
        ("application", ctypes.c_uint8),
        ("event_number", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int, int]:
        return (int(self.site), int(self.application), int(self.event_number))


class FastDisEntityStatePrefix(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("entity_id", FastDisEntityId),
        ("force_id", ctypes.c_uint8),
        ("variable_parameter_count", ctypes.c_uint8),
        ("entity_type", FastDisEntityType),
        ("alternate_entity_type", FastDisEntityType),
        ("linear_velocity", FastDisVec3f),
        ("location", FastDisWorldCoordinates),
        ("orientation", FastDisEulerAngles),
        ("appearance", ctypes.c_uint32),
        ("dead_reckoning_algorithm", ctypes.c_uint8),
        ("dead_reckoning_parameters", ctypes.c_uint8 * 15),
        ("dead_reckoning_linear_acceleration", FastDisVec3f),
        ("dead_reckoning_angular_velocity", FastDisVec3f),
        ("marking_character_set", ctypes.c_uint8),
        ("marking", ctypes.c_uint8 * 12),
        ("capabilities", ctypes.c_uint32),
        ("fields_present", ctypes.c_uint64),
    ]

    def as_value(self) -> EntityStatePrefix:
        return EntityStatePrefix(
            header=self.header.as_tuple(),
            entity_id=self.entity_id.as_tuple(),
            force_id=int(self.force_id),
            variable_parameter_count=int(self.variable_parameter_count),
            entity_type=self.entity_type.as_tuple(),
            alternate_entity_type=self.alternate_entity_type.as_tuple(),
            linear_velocity=self.linear_velocity.as_tuple(),
            location=self.location.as_tuple(),
            orientation=self.orientation.as_tuple(),
            appearance=int(self.appearance),
            dead_reckoning_algorithm=int(self.dead_reckoning_algorithm),
            dead_reckoning_parameters=bytes(self.dead_reckoning_parameters),
            dead_reckoning_linear_acceleration=self.dead_reckoning_linear_acceleration.as_tuple(),
            dead_reckoning_angular_velocity=self.dead_reckoning_angular_velocity.as_tuple(),
            marking_character_set=int(self.marking_character_set),
            marking=bytes(self.marking[:11]),
            capabilities=int(self.capabilities),
            fields_present=int(self.fields_present),
        )


class FastDisEntityTransform(ctypes.Structure):
    _fields_ = [
        ("entity_id", FastDisEntityId),
        ("force_id", ctypes.c_uint8),
        ("exercise_id", ctypes.c_uint8),
        ("version", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8),
        ("timestamp", ctypes.c_uint32),
        ("appearance", ctypes.c_uint32),
        ("location", FastDisWorldCoordinates),
        ("orientation", FastDisEulerAngles),
        ("linear_velocity", FastDisVec3f),
        ("fields_present", ctypes.c_uint64),
        ("dead_reckoning_algorithm", ctypes.c_uint8),
        ("dead_reckoning_parameters", ctypes.c_uint8 * 15),
        ("dead_reckoning_linear_acceleration", FastDisVec3f),
        ("dead_reckoning_angular_velocity", FastDisVec3f),
    ]

    def as_value(self) -> EntityTransform:
        return EntityTransform(
            entity_id=self.entity_id.as_tuple(),
            force_id=int(self.force_id),
            exercise_id=int(self.exercise_id),
            version=int(self.version),
            timestamp=int(self.timestamp),
            appearance=int(self.appearance),
            location=self.location.as_tuple(),
            orientation=self.orientation.as_tuple(),
            linear_velocity=self.linear_velocity.as_tuple(),
            fields_present=int(self.fields_present),
            dead_reckoning_algorithm=int(self.dead_reckoning_algorithm),
            dead_reckoning_parameters=bytes(self.dead_reckoning_parameters),
            dead_reckoning_linear_acceleration=self.dead_reckoning_linear_acceleration.as_tuple(),
            dead_reckoning_angular_velocity=self.dead_reckoning_angular_velocity.as_tuple(),
        )


class FastDisSimulationManagementRequest(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> SimulationManagementRequest:
        return SimulationManagementRequest(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
        )


class FastDisStartResume(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("real_world_time", FastDisClockTime),
        ("simulation_time", FastDisClockTime),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> StartResume:
        return StartResume(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            real_world_time=self.real_world_time.as_tuple(),
            simulation_time=self.simulation_time.as_tuple(),
            request_id=int(self.request_id),
        )


class FastDisStopFreeze(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("real_world_time", FastDisClockTime),
        ("reason", ctypes.c_uint8),
        ("frozen_behavior", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> StopFreeze:
        return StopFreeze(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            real_world_time=self.real_world_time.as_tuple(),
            reason=int(self.reason),
            frozen_behavior=int(self.frozen_behavior),
            padding1=int(self.padding1),
            request_id=int(self.request_id),
        )


class FastDisAcknowledge(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("acknowledge_flag", ctypes.c_uint16),
        ("response_flag", ctypes.c_uint16),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> Acknowledge:
        return Acknowledge(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            acknowledge_flag=int(self.acknowledge_flag),
            response_flag=int(self.response_flag),
            request_id=int(self.request_id),
        )


class FastDisSimulationManagementReliableRequest(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> SimulationManagementReliableRequest:
        return SimulationManagementReliableRequest(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            request_id=int(self.request_id),
        )


class FastDisStartResumeReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("real_world_time", FastDisClockTime),
        ("simulation_time", FastDisClockTime),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> StartResumeReliable:
        return StartResumeReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            real_world_time=self.real_world_time.as_tuple(),
            simulation_time=self.simulation_time.as_tuple(),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            request_id=int(self.request_id),
        )


class FastDisStopFreezeReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("real_world_time", FastDisClockTime),
        ("reason", ctypes.c_uint8),
        ("frozen_behavior", ctypes.c_uint8),
        ("required_reliablity_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
    ]

    def as_value(self) -> StopFreezeReliable:
        return StopFreezeReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            real_world_time=self.real_world_time.as_tuple(),
            reason=int(self.reason),
            frozen_behavior=int(self.frozen_behavior),
            required_reliablity_service=int(self.required_reliablity_service),
            pad1=int(self.pad1),
            request_id=int(self.request_id),
        )


class FastDisDatumRecordSetView(ctypes.Structure):
    _fields_ = [
        ("datum_record_bytes", ctypes.POINTER(ctypes.c_uint8)),
        ("datum_record_bytes_size", ctypes.c_size_t),
        ("datum_record_bytes_user", ctypes.c_void_p),
        ("number_of_fixed_datum_records", ctypes.c_uint32),
        ("number_of_variable_datum_records", ctypes.c_uint32),
    ]


class FastDisCountedBytesView(ctypes.Structure):
    _fields_ = [
        ("bytes", ctypes.POINTER(ctypes.c_uint8)),
        ("bytes_size", ctypes.c_size_t),
        ("bytes_user", ctypes.c_void_p),
        ("count", ctypes.c_uint32),
    ]


class FastDisSimulationAddress(ctypes.Structure):
    _fields_ = [
        ("site", ctypes.c_uint16),
        ("application", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int]:
        return (int(self.site), int(self.application))


class FastDisRadioEntityType(ctypes.Structure):
    _fields_ = [
        ("entity_kind", ctypes.c_uint8),
        ("domain", ctypes.c_uint8),
        ("country", ctypes.c_uint16),
        ("category", ctypes.c_uint8),
        ("nomenclature_version", ctypes.c_uint8),
        ("nomenclature", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int, int, int, int, int]:
        return (
            int(self.entity_kind),
            int(self.domain),
            int(self.country),
            int(self.category),
            int(self.nomenclature_version),
            int(self.nomenclature),
        )


class FastDisModulationType(ctypes.Structure):
    _fields_ = [
        ("spread_spectrum", ctypes.c_uint16),
        ("major", ctypes.c_uint16),
        ("detail", ctypes.c_uint16),
        ("system", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (int(self.spread_spectrum), int(self.major), int(self.detail), int(self.system))


class FastDisSystemId(ctypes.Structure):
    _fields_ = [
        ("system_type", ctypes.c_uint16),
        ("system_name", ctypes.c_uint16),
        ("system_mode", ctypes.c_uint8),
        ("change_options", ctypes.c_uint8),
    ]

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (int(self.system_type), int(self.system_name), int(self.system_mode), int(self.change_options))


class FastDisIffFundamentalData(ctypes.Structure):
    _fields_ = [
        ("system_status", ctypes.c_uint8),
        ("alternate_parameter4", ctypes.c_uint8),
        ("information_layers", ctypes.c_uint8),
        ("modifier", ctypes.c_uint8),
        ("parameter1", ctypes.c_uint16),
        ("parameter2", ctypes.c_uint16),
        ("parameter3", ctypes.c_uint16),
        ("parameter4", ctypes.c_uint16),
        ("parameter5", ctypes.c_uint16),
        ("parameter6", ctypes.c_uint16),
    ]

    def as_tuple(self) -> tuple[int, int, int, int, int, int, int, int, int, int]:
        return (
            int(self.system_status),
            int(self.alternate_parameter4),
            int(self.information_layers),
            int(self.modifier),
            int(self.parameter1),
            int(self.parameter2),
            int(self.parameter3),
            int(self.parameter4),
            int(self.parameter5),
            int(self.parameter6),
        )


class FastDisDesignator(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("designating_entity_id", FastDisEntityId),
        ("code_name", ctypes.c_uint16),
        ("designated_entity_id", FastDisEntityId),
        ("designator_code", ctypes.c_uint16),
        ("designator_power", ctypes.c_float),
        ("designator_wavelength", ctypes.c_float),
        ("designator_spot_wrt_designated", FastDisVec3f),
        ("designator_spot_location", FastDisWorldCoordinates),
        ("dead_reckoning_algorithm", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("padding2", ctypes.c_uint8),
        ("entity_linear_acceleration", FastDisVec3f),
    ]

    def as_value(self) -> Designator:
        return Designator(
            header=self.header.as_tuple(),
            designating_entity_id=self.designating_entity_id.as_tuple(),
            code_name=int(self.code_name),
            designated_entity_id=self.designated_entity_id.as_tuple(),
            designator_code=int(self.designator_code),
            designator_power=float(self.designator_power),
            designator_wavelength=float(self.designator_wavelength),
            designator_spot_wrt_designated=self.designator_spot_wrt_designated.as_tuple(),
            designator_spot_location=self.designator_spot_location.as_tuple(),
            dead_reckoning_algorithm=int(self.dead_reckoning_algorithm),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            entity_linear_acceleration=self.entity_linear_acceleration.as_tuple(),
        )


class FastDisTransmitter(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("entity_id", FastDisEntityId),
        ("radio_id", ctypes.c_uint16),
        ("radio_entity_type", FastDisRadioEntityType),
        ("entity_type", FastDisEntityType),
        ("transmit_state", ctypes.c_uint8),
        ("input_source", ctypes.c_uint8),
        ("variable_transmitter_parameter_count", ctypes.c_uint16),
        ("antenna_location", FastDisWorldCoordinates),
        ("relative_antenna_location", FastDisVec3f),
        ("antenna_pattern_type", ctypes.c_uint16),
        ("antenna_pattern_count", ctypes.c_uint16),
        ("frequency", ctypes.c_uint32),
        ("transmit_frequency_bandwidth", ctypes.c_float),
        ("power", ctypes.c_float),
        ("modulation_type", FastDisModulationType),
        ("crypto_system", ctypes.c_uint16),
        ("crypto_key_id", ctypes.c_uint16),
        ("modulation_parameter_count", ctypes.c_uint8),
        ("padding2", ctypes.c_uint16),
        ("padding3", ctypes.c_uint8),
        ("modulation_parameters", FastDisCountedBytesView),
        ("antenna_patterns", FastDisCountedBytesView),
    ]

    def as_value(self) -> Transmitter:
        return Transmitter(
            header=self.header.as_tuple(),
            entity_id=self.entity_id.as_tuple(),
            radio_id=int(self.radio_id),
            radio_entity_type=self.radio_entity_type.as_tuple(),
            entity_type=self.entity_type.as_tuple(),
            transmit_state=int(self.transmit_state),
            input_source=int(self.input_source),
            variable_transmitter_parameter_count=int(self.variable_transmitter_parameter_count),
            antenna_location=self.antenna_location.as_tuple(),
            relative_antenna_location=self.relative_antenna_location.as_tuple(),
            antenna_pattern_type=int(self.antenna_pattern_type),
            antenna_pattern_count=int(self.antenna_pattern_count),
            frequency=int(self.frequency),
            transmit_frequency_bandwidth=float(self.transmit_frequency_bandwidth),
            power=float(self.power),
            modulation_type=self.modulation_type.as_tuple(),
            crypto_system=int(self.crypto_system),
            crypto_key_id=int(self.crypto_key_id),
            modulation_parameter_count=int(self.modulation_parameter_count),
            padding2=int(self.padding2),
            padding3=int(self.padding3),
            modulation_parameter_bytes=ctypes.string_at(self.modulation_parameters.bytes, int(self.modulation_parameters.bytes_size)) if self.modulation_parameters.bytes else b"",
            antenna_pattern_bytes=ctypes.string_at(self.antenna_patterns.bytes, int(self.antenna_patterns.bytes_size)) if self.antenna_patterns.bytes else b"",
        )


class FastDisOtherPdu(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("opaque_payload", FastDisCountedBytesView),
    ]

    def as_value(self) -> OtherPdu:
        return OtherPdu(
            header=self.header.as_tuple(),
            opaque_payload_bytes=ctypes.string_at(self.opaque_payload.bytes, int(self.opaque_payload.bytes_size)) if self.opaque_payload.bytes else b"",
        )


class FastDisAggregateState(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("aggregate_id", FastDisEntityId),
        ("force_id", ctypes.c_uint8),
        ("aggregate_state", ctypes.c_uint8),
        ("aggregate_type", FastDisEntityType),
        ("formation", ctypes.c_uint32),
        ("aggregate_marking_character_set", ctypes.c_uint8),
        ("aggregate_marking", ctypes.c_uint8 * 32),
        ("dimensions", FastDisVec3f),
        ("orientation", FastDisEulerAngles),
        ("center_of_mass", FastDisWorldCoordinates),
        ("velocity", FastDisVec3f),
        ("number_of_dis_aggregates", ctypes.c_uint16),
        ("number_of_dis_entities", ctypes.c_uint16),
        ("number_of_silent_aggregate_types", ctypes.c_uint16),
        ("number_of_silent_entity_types", ctypes.c_uint16),
        ("aggregate_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> AggregateState:
        return AggregateState(
            header=self.header.as_tuple(),
            aggregate_id=self.aggregate_id.as_tuple(),
            force_id=int(self.force_id),
            aggregate_state=int(self.aggregate_state),
            aggregate_type=self.aggregate_type.as_tuple(),
            formation=int(self.formation),
            aggregate_marking_character_set=int(self.aggregate_marking_character_set),
            aggregate_marking=bytes(self.aggregate_marking[:31]),
            dimensions=self.dimensions.as_tuple(),
            orientation=self.orientation.as_tuple(),
            center_of_mass=self.center_of_mass.as_tuple(),
            velocity=self.velocity.as_tuple(),
            number_of_dis_aggregates=int(self.number_of_dis_aggregates),
            number_of_dis_entities=int(self.number_of_dis_entities),
            number_of_silent_aggregate_types=int(self.number_of_silent_aggregate_types),
            number_of_silent_entity_types=int(self.number_of_silent_entity_types),
            aggregate_record_bytes=ctypes.string_at(self.aggregate_records.bytes, int(self.aggregate_records.bytes_size)) if self.aggregate_records.bytes else b"",
        )


class FastDisIsGroupOf(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("group_entity_id", FastDisEntityId),
        ("grouped_entity_category", ctypes.c_uint8),
        ("number_of_grouped_entities", ctypes.c_uint8),
        ("pad2", ctypes.c_uint32),
        ("latitude", ctypes.c_double),
        ("longitude", ctypes.c_double),
        ("grouped_entity_descriptions", FastDisCountedBytesView),
    ]

    def as_value(self) -> IsGroupOf:
        return IsGroupOf(
            header=self.header.as_tuple(),
            group_entity_id=self.group_entity_id.as_tuple(),
            grouped_entity_category=int(self.grouped_entity_category),
            number_of_grouped_entities=int(self.number_of_grouped_entities),
            pad2=int(self.pad2),
            latitude=float(self.latitude),
            longitude=float(self.longitude),
            grouped_entity_description_bytes=ctypes.string_at(self.grouped_entity_descriptions.bytes, int(self.grouped_entity_descriptions.bytes_size)) if self.grouped_entity_descriptions.bytes else b"",
        )


class FastDisTransferControlRequest(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("required_reliability_service", ctypes.c_uint8),
        ("transfer_type", ctypes.c_uint8),
        ("transfer_entity_id", FastDisEntityId),
        ("number_of_record_sets", ctypes.c_uint8),
        ("record_sets", FastDisCountedBytesView),
    ]

    def as_value(self) -> TransferControlRequest:
        return TransferControlRequest(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            transfer_type=int(self.transfer_type),
            transfer_entity_id=self.transfer_entity_id.as_tuple(),
            number_of_record_sets=int(self.number_of_record_sets),
            record_set_bytes=ctypes.string_at(self.record_sets.bytes, int(self.record_sets.bytes_size)) if self.record_sets.bytes else b"",
        )


class FastDisTransferOwnership(ctypes.Structure):
    _fields_ = FastDisTransferControlRequest._fields_

    def as_value(self) -> TransferOwnership:
        return TransferOwnership(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            transfer_type=int(self.transfer_type),
            transfer_entity_id=self.transfer_entity_id.as_tuple(),
            number_of_record_sets=int(self.number_of_record_sets),
            record_set_bytes=ctypes.string_at(self.record_sets.bytes, int(self.record_sets.bytes_size)) if self.record_sets.bytes else b"",
        )


class FastDisIsPartOf(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("relationship_nature", ctypes.c_uint16),
        ("relationship_position", ctypes.c_uint16),
        ("part_location", FastDisVec3f),
        ("station_name", ctypes.c_uint16),
        ("station_number", ctypes.c_uint16),
        ("part_entity_type", FastDisEntityType),
    ]

    def as_value(self) -> IsPartOf:
        return IsPartOf(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            relationship=(int(self.relationship_nature), int(self.relationship_position)),
            part_location=self.part_location.as_tuple(),
            named_location=(int(self.station_name), int(self.station_number)),
            part_entity_type=self.part_entity_type.as_tuple(),
        )


class FastDisMinefieldState(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("minefield_id", FastDisEntityId),
        ("minefield_sequence", ctypes.c_uint16),
        ("force_id", ctypes.c_uint8),
        ("number_of_perimeter_points", ctypes.c_uint8),
        ("minefield_type", FastDisEntityType),
        ("number_of_mine_types", ctypes.c_uint16),
        ("minefield_location", FastDisWorldCoordinates),
        ("minefield_orientation", FastDisEulerAngles),
        ("appearance", ctypes.c_uint16),
        ("protocol_mode", ctypes.c_uint16),
        ("perimeter_points", FastDisCountedBytesView),
        ("mine_types", FastDisCountedBytesView),
    ]

    def as_value(self) -> MinefieldState:
        return MinefieldState(
            header=self.header.as_tuple(),
            minefield_id=self.minefield_id.as_tuple(),
            minefield_sequence=int(self.minefield_sequence),
            force_id=int(self.force_id),
            number_of_perimeter_points=int(self.number_of_perimeter_points),
            minefield_type=self.minefield_type.as_tuple(),
            number_of_mine_types=int(self.number_of_mine_types),
            minefield_location=self.minefield_location.as_tuple(),
            minefield_orientation=self.minefield_orientation.as_tuple(),
            appearance=int(self.appearance),
            protocol_mode=int(self.protocol_mode),
            perimeter_point_bytes=ctypes.string_at(self.perimeter_points.bytes, int(self.perimeter_points.bytes_size)) if self.perimeter_points.bytes else b"",
            mine_type_bytes=ctypes.string_at(self.mine_types.bytes, int(self.mine_types.bytes_size)) if self.mine_types.bytes else b"",
        )


class FastDisMinefieldQuery(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("minefield_id", FastDisEntityId),
        ("requesting_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint8),
        ("number_of_perimeter_points", ctypes.c_uint8),
        ("pad2", ctypes.c_uint8),
        ("number_of_sensor_types", ctypes.c_uint8),
        ("data_filter", ctypes.c_uint32),
        ("requested_mine_type", FastDisEntityType),
        ("requested_perimeter_points", FastDisCountedBytesView),
        ("sensor_types", FastDisCountedBytesView),
    ]

    def as_value(self) -> MinefieldQuery:
        return MinefieldQuery(
            header=self.header.as_tuple(),
            minefield_id=self.minefield_id.as_tuple(),
            requesting_entity_id=self.requesting_entity_id.as_tuple(),
            request_id=int(self.request_id),
            number_of_perimeter_points=int(self.number_of_perimeter_points),
            pad2=int(self.pad2),
            number_of_sensor_types=int(self.number_of_sensor_types),
            data_filter=int(self.data_filter),
            requested_mine_type=self.requested_mine_type.as_tuple(),
            requested_perimeter_point_bytes=ctypes.string_at(self.requested_perimeter_points.bytes, int(self.requested_perimeter_points.bytes_size)) if self.requested_perimeter_points.bytes else b"",
            sensor_type_bytes=ctypes.string_at(self.sensor_types.bytes, int(self.sensor_types.bytes_size)) if self.sensor_types.bytes else b"",
        )


class FastDisMinefieldData(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("minefield_id", FastDisEntityId),
        ("requesting_entity_id", FastDisEntityId),
        ("minefield_sequence_number", ctypes.c_uint16),
        ("request_id", ctypes.c_uint8),
        ("pdu_sequence_number", ctypes.c_uint8),
        ("number_of_pdus", ctypes.c_uint8),
        ("number_of_mines_in_this_pdu", ctypes.c_uint8),
        ("number_of_sensor_types", ctypes.c_uint8),
        ("pad2", ctypes.c_uint8),
        ("data_filter", ctypes.c_uint32),
        ("mine_type", FastDisEntityType),
        ("pad3", ctypes.c_uint8),
        ("sensor_types", FastDisCountedBytesView),
        ("mine_locations", FastDisCountedBytesView),
    ]

    def as_value(self) -> MinefieldData:
        return MinefieldData(
            header=self.header.as_tuple(),
            minefield_id=self.minefield_id.as_tuple(),
            requesting_entity_id=self.requesting_entity_id.as_tuple(),
            minefield_sequence_number=int(self.minefield_sequence_number),
            request_id=int(self.request_id),
            pdu_sequence_number=int(self.pdu_sequence_number),
            number_of_pdus=int(self.number_of_pdus),
            number_of_mines_in_this_pdu=int(self.number_of_mines_in_this_pdu),
            number_of_sensor_types=int(self.number_of_sensor_types),
            pad2=int(self.pad2),
            data_filter=int(self.data_filter),
            mine_type=self.mine_type.as_tuple(),
            pad3=int(self.pad3),
            sensor_type_bytes=ctypes.string_at(self.sensor_types.bytes, int(self.sensor_types.bytes_size)) if self.sensor_types.bytes else b"",
            mine_location_bytes=ctypes.string_at(self.mine_locations.bytes, int(self.mine_locations.bytes_size)) if self.mine_locations.bytes else b"",
        )


class FastDisMinefieldResponseNack(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("minefield_id", FastDisEntityId),
        ("requesting_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint8),
        ("number_of_missing_pdus", ctypes.c_uint8),
        ("missing_pdu_sequence_numbers", FastDisCountedBytesView),
    ]

    def as_value(self) -> MinefieldResponseNack:
        return MinefieldResponseNack(
            header=self.header.as_tuple(),
            minefield_id=self.minefield_id.as_tuple(),
            requesting_entity_id=self.requesting_entity_id.as_tuple(),
            request_id=int(self.request_id),
            number_of_missing_pdus=int(self.number_of_missing_pdus),
            missing_pdu_sequence_number_bytes=ctypes.string_at(self.missing_pdu_sequence_numbers.bytes, int(self.missing_pdu_sequence_numbers.bytes_size)) if self.missing_pdu_sequence_numbers.bytes else b"",
        )


class FastDisEnvironmentObjectType(ctypes.Structure):
    _fields_ = [
        ("domain", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
        ("country", ctypes.c_uint16),
        ("category", ctypes.c_uint8),
        ("subcategory", ctypes.c_uint8),
    ]

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (
            int(self.domain),
            int(self.kind),
            int(self.country),
            int(self.category),
            int(self.subcategory),
        )


class FastDisEnvironmentalProcess(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("environmental_process_id", FastDisEntityId),
        ("environment_type", FastDisEntityType),
        ("model_type", ctypes.c_uint8),
        ("environment_status", ctypes.c_uint8),
        ("number_of_environment_records", ctypes.c_uint8),
        ("sequence_number", ctypes.c_uint16),
        ("environment_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> EnvironmentalProcess:
        return EnvironmentalProcess(
            header=self.header.as_tuple(),
            environmental_process_id=self.environmental_process_id.as_tuple(),
            environment_type=self.environment_type.as_tuple(),
            model_type=int(self.model_type),
            environment_status=int(self.environment_status),
            number_of_environment_records=int(self.number_of_environment_records),
            sequence_number=int(self.sequence_number),
            environment_record_bytes=ctypes.string_at(self.environment_records.bytes, int(self.environment_records.bytes_size)) if self.environment_records.bytes else b"",
        )


class FastDisGriddedData(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("environmental_simulation_application_id", FastDisEntityId),
        ("field_number", ctypes.c_uint16),
        ("pdu_number", ctypes.c_uint16),
        ("pdu_total", ctypes.c_uint16),
        ("coordinate_system", ctypes.c_uint16),
        ("number_of_grid_axes", ctypes.c_uint8),
        ("constant_grid", ctypes.c_uint8),
        ("environment_type", FastDisEntityType),
        ("orientation", FastDisEulerAngles),
        ("sample_time", ctypes.c_uint64),
        ("total_values", ctypes.c_uint32),
        ("vector_dimension", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("padding2", ctypes.c_uint8),
        ("grid_data", FastDisCountedBytesView),
    ]

    def as_value(self) -> GriddedData:
        return GriddedData(
            header=self.header.as_tuple(),
            environmental_simulation_application_id=self.environmental_simulation_application_id.as_tuple(),
            field_number=int(self.field_number),
            pdu_number=int(self.pdu_number),
            pdu_total=int(self.pdu_total),
            coordinate_system=int(self.coordinate_system),
            number_of_grid_axes=int(self.number_of_grid_axes),
            constant_grid=int(self.constant_grid),
            environment_type=self.environment_type.as_tuple(),
            orientation=self.orientation.as_tuple(),
            sample_time=int(self.sample_time),
            total_values=int(self.total_values),
            vector_dimension=int(self.vector_dimension),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            grid_data_bytes=ctypes.string_at(self.grid_data.bytes, int(self.grid_data.bytes_size)) if self.grid_data.bytes else b"",
        )


class FastDisPointObjectState(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("object_id", FastDisEntityId),
        ("referenced_object_id", FastDisEntityId),
        ("update_number", ctypes.c_uint16),
        ("force_id", ctypes.c_uint8),
        ("modifications", ctypes.c_uint8),
        ("object_type", FastDisEnvironmentObjectType),
        ("object_location", FastDisWorldCoordinates),
        ("object_orientation", FastDisEulerAngles),
        ("object_appearance", ctypes.c_double),
        ("requester_id", FastDisSimulationAddress),
        ("receiving_id", FastDisSimulationAddress),
        ("pad2", ctypes.c_uint32),
    ]

    def as_value(self) -> PointObjectState:
        return PointObjectState(
            header=self.header.as_tuple(),
            object_id=self.object_id.as_tuple(),
            referenced_object_id=self.referenced_object_id.as_tuple(),
            update_number=int(self.update_number),
            force_id=int(self.force_id),
            modifications=int(self.modifications),
            object_type=self.object_type.as_tuple(),
            object_location=self.object_location.as_tuple(),
            object_orientation=self.object_orientation.as_tuple(),
            object_appearance=float(self.object_appearance),
            requester_id=self.requester_id.as_tuple(),
            receiving_id=self.receiving_id.as_tuple(),
            pad2=int(self.pad2),
        )


class FastDisLinearObjectState(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("object_id", FastDisEntityId),
        ("referenced_object_id", FastDisEntityId),
        ("update_number", ctypes.c_uint16),
        ("force_id", ctypes.c_uint8),
        ("number_of_segments", ctypes.c_uint8),
        ("requester_id", FastDisSimulationAddress),
        ("receiving_id", FastDisSimulationAddress),
        ("object_type", FastDisEnvironmentObjectType),
        ("linear_segment_parameters", FastDisCountedBytesView),
    ]

    def as_value(self) -> LinearObjectState:
        return LinearObjectState(
            header=self.header.as_tuple(),
            object_id=self.object_id.as_tuple(),
            referenced_object_id=self.referenced_object_id.as_tuple(),
            update_number=int(self.update_number),
            force_id=int(self.force_id),
            number_of_segments=int(self.number_of_segments),
            requester_id=self.requester_id.as_tuple(),
            receiving_id=self.receiving_id.as_tuple(),
            object_type=self.object_type.as_tuple(),
            linear_segment_parameter_bytes=ctypes.string_at(self.linear_segment_parameters.bytes, int(self.linear_segment_parameters.bytes_size)) if self.linear_segment_parameters.bytes else b"",
        )


class FastDisArealObjectState(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("object_id", FastDisEntityId),
        ("referenced_object_id", FastDisEntityId),
        ("update_number", ctypes.c_uint16),
        ("force_id", ctypes.c_uint8),
        ("modifications", ctypes.c_uint8),
        ("object_type", FastDisEntityType),
        ("object_appearance", FastDisCountedBytesView),
        ("number_of_points", ctypes.c_uint16),
        ("requester_id", FastDisSimulationAddress),
        ("receiving_id", FastDisSimulationAddress),
        ("object_locations", FastDisCountedBytesView),
    ]

    def as_value(self) -> ArealObjectState:
        return ArealObjectState(
            header=self.header.as_tuple(),
            object_id=self.object_id.as_tuple(),
            referenced_object_id=self.referenced_object_id.as_tuple(),
            update_number=int(self.update_number),
            force_id=int(self.force_id),
            modifications=int(self.modifications),
            object_type=self.object_type.as_tuple(),
            object_appearance_bytes=ctypes.string_at(self.object_appearance.bytes, int(self.object_appearance.bytes_size)) if self.object_appearance.bytes else b"",
            number_of_points=int(self.number_of_points),
            requester_id=self.requester_id.as_tuple(),
            receiving_id=self.receiving_id.as_tuple(),
            object_location_bytes=ctypes.string_at(self.object_locations.bytes, int(self.object_locations.bytes_size)) if self.object_locations.bytes else b"",
        )


class FastDisTspi(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("live_entity_id", FastDisLiveEntityId),
        ("tspi_flag", ctypes.c_uint8),
        ("entity_location", FastDisCountedBytesView),
        ("entity_linear_velocity", FastDisCountedBytesView),
        ("entity_orientation", FastDisCountedBytesView),
        ("position_error", FastDisCountedBytesView),
        ("orientation_error", FastDisCountedBytesView),
        ("dead_reckoning_parameters", FastDisCountedBytesView),
        ("measured_speed", ctypes.c_uint16),
        ("system_specific_data_length", ctypes.c_uint8),
        ("system_specific_data", FastDisCountedBytesView),
    ]

    def as_value(self) -> Tspi:
        return Tspi(
            header=self.header.as_tuple(),
            live_entity_id=self.live_entity_id.as_tuple(),
            tspi_flag=int(self.tspi_flag),
            entity_location_bytes=ctypes.string_at(self.entity_location.bytes, int(self.entity_location.bytes_size)) if self.entity_location.bytes else b"",
            entity_linear_velocity_bytes=ctypes.string_at(self.entity_linear_velocity.bytes, int(self.entity_linear_velocity.bytes_size)) if self.entity_linear_velocity.bytes else b"",
            entity_orientation_bytes=ctypes.string_at(self.entity_orientation.bytes, int(self.entity_orientation.bytes_size)) if self.entity_orientation.bytes else b"",
            position_error_bytes=ctypes.string_at(self.position_error.bytes, int(self.position_error.bytes_size)) if self.position_error.bytes else b"",
            orientation_error_bytes=ctypes.string_at(self.orientation_error.bytes, int(self.orientation_error.bytes_size)) if self.orientation_error.bytes else b"",
            dead_reckoning_parameter_bytes=ctypes.string_at(self.dead_reckoning_parameters.bytes, int(self.dead_reckoning_parameters.bytes_size)) if self.dead_reckoning_parameters.bytes else b"",
            measured_speed=int(self.measured_speed),
            system_specific_data_length=int(self.system_specific_data_length),
            system_specific_data=ctypes.string_at(self.system_specific_data.bytes, int(self.system_specific_data.bytes_size)) if self.system_specific_data.bytes else b"",
        )


class FastDisLiveEntityAppearance(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("live_entity_id", FastDisLiveEntityId),
        ("appearance_flags", ctypes.c_uint16),
        ("force_id", ctypes.c_uint8),
        ("padding1", ctypes.c_uint8),
        ("entity_type", FastDisEntityType),
        ("alternate_entity_type", FastDisEntityType),
        ("entity_marking", ctypes.c_uint8 * 12),
        ("capabilities", ctypes.c_uint32),
        ("appearance_fields", FastDisCountedBytesView),
    ]

    def as_value(self) -> LiveEntityAppearance:
        return LiveEntityAppearance(
            header=self.header.as_tuple(),
            live_entity_id=self.live_entity_id.as_tuple(),
            appearance_flags=int(self.appearance_flags),
            force_id=int(self.force_id),
            padding1=int(self.padding1),
            entity_type=self.entity_type.as_tuple(),
            alternate_entity_type=self.alternate_entity_type.as_tuple(),
            entity_marking=bytes(self.entity_marking),
            capabilities=int(self.capabilities),
            appearance_field_bytes=ctypes.string_at(self.appearance_fields.bytes, int(self.appearance_fields.bytes_size)) if self.appearance_fields.bytes else b"",
        )


class FastDisArticulatedParts(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("live_entity_id", FastDisLiveEntityId),
        ("number_of_parameter_records", ctypes.c_uint8),
        ("padding", ctypes.c_uint8 * 3),
        ("variable_parameters", FastDisCountedBytesView),
    ]

    def as_value(self) -> ArticulatedParts:
        return ArticulatedParts(
            header=self.header.as_tuple(),
            live_entity_id=self.live_entity_id.as_tuple(),
            number_of_parameter_records=int(self.number_of_parameter_records),
            padding=bytes(self.padding),
            variable_parameter_bytes=ctypes.string_at(self.variable_parameters.bytes, int(self.variable_parameters.bytes_size)) if self.variable_parameters.bytes else b"",
        )


class FastDisBurstDescriptor(ctypes.Structure):
    _fields_ = [
        ("munition_type", FastDisEntityType),
        ("warhead", ctypes.c_uint16),
        ("fuse", ctypes.c_uint16),
        ("quantity", ctypes.c_uint16),
        ("rate", ctypes.c_uint16),
    ]

    def as_tuple(self) -> BurstDescriptorTuple:
        return (
            self.munition_type.as_tuple(),
            int(self.warhead),
            int(self.fuse),
            int(self.quantity),
            int(self.rate),
        )


class FastDisLeFire(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_live_entity_id", FastDisLiveEntityId),
        ("flags", ctypes.c_uint8),
        ("padding1", ctypes.c_uint8),
        ("target_live_entity_id", FastDisLiveEntityId),
        ("munition_live_entity_id", FastDisLiveEntityId),
        ("event_id", FastDisLiveEventId),
        ("location", FastDisCountedBytesView),
        ("munition_descriptor", FastDisBurstDescriptor),
        ("velocity", FastDisCountedBytesView),
        ("range", ctypes.c_uint16),
    ]

    def as_value(self) -> LeFire:
        return LeFire(
            header=self.header.as_tuple(),
            firing_live_entity_id=self.firing_live_entity_id.as_tuple(),
            flags=int(self.flags),
            padding1=int(self.padding1),
            target_live_entity_id=self.target_live_entity_id.as_tuple(),
            munition_live_entity_id=self.munition_live_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            location_bytes=ctypes.string_at(self.location.bytes, int(self.location.bytes_size)) if self.location.bytes else b"",
            munition_descriptor=self.munition_descriptor.as_tuple(),
            velocity_bytes=ctypes.string_at(self.velocity.bytes, int(self.velocity.bytes_size)) if self.velocity.bytes else b"",
            range=int(self.range),
        )


class FastDisLeDetonation(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_live_entity_id", FastDisLiveEntityId),
        ("detonation_flag1", ctypes.c_uint8),
        ("detonation_flag2", ctypes.c_uint8),
        ("target_live_entity_id", FastDisLiveEntityId),
        ("munition_live_entity_id", FastDisLiveEntityId),
        ("event_id", FastDisLiveEventId),
        ("world_location", FastDisCountedBytesView),
        ("velocity", FastDisCountedBytesView),
        ("munition_orientation", FastDisCountedBytesView),
        ("munition_descriptor", FastDisBurstDescriptor),
        ("entity_location", FastDisCountedBytesView),
        ("detonation_result", ctypes.c_uint8),
        ("padding1", ctypes.c_uint8),
    ]

    def as_value(self) -> LeDetonation:
        return LeDetonation(
            header=self.header.as_tuple(),
            firing_live_entity_id=self.firing_live_entity_id.as_tuple(),
            detonation_flag1=int(self.detonation_flag1),
            detonation_flag2=int(self.detonation_flag2),
            target_live_entity_id=self.target_live_entity_id.as_tuple(),
            munition_live_entity_id=self.munition_live_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            world_location_bytes=ctypes.string_at(self.world_location.bytes, int(self.world_location.bytes_size)) if self.world_location.bytes else b"",
            velocity_bytes=ctypes.string_at(self.velocity.bytes, int(self.velocity.bytes_size)) if self.velocity.bytes else b"",
            munition_orientation_bytes=ctypes.string_at(self.munition_orientation.bytes, int(self.munition_orientation.bytes_size)) if self.munition_orientation.bytes else b"",
            munition_descriptor=self.munition_descriptor.as_tuple(),
            entity_location_bytes=ctypes.string_at(self.entity_location.bytes, int(self.entity_location.bytes_size)) if self.entity_location.bytes else b"",
            detonation_result=int(self.detonation_result),
            padding1=int(self.padding1),
        )


class FastDisSignal(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("entity_id", FastDisEntityId),
        ("radio_id", ctypes.c_uint16),
        ("encoding_scheme", ctypes.c_uint16),
        ("tdl_type", ctypes.c_uint16),
        ("sample_rate", ctypes.c_uint32),
        ("data_length", ctypes.c_uint16),
        ("samples", ctypes.c_uint16),
        ("data", FastDisCountedBytesView),
    ]

    def as_value(self) -> Signal:
        return Signal(
            header=self.header.as_tuple(),
            entity_id=self.entity_id.as_tuple(),
            radio_id=int(self.radio_id),
            encoding_scheme=int(self.encoding_scheme),
            tdl_type=int(self.tdl_type),
            sample_rate=int(self.sample_rate),
            data_length=int(self.data_length),
            samples=int(self.samples),
            data_bytes=ctypes.string_at(self.data.bytes, int(self.data.bytes_size)) if self.data.bytes else b"",
        )


class FastDisReceiver(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("entity_id", FastDisEntityId),
        ("radio_id", ctypes.c_uint16),
        ("receiver_state", ctypes.c_uint16),
        ("padding1", ctypes.c_uint16),
        ("received_power", ctypes.c_float),
        ("transmitter_entity_id", FastDisEntityId),
        ("transmitter_radio_id", ctypes.c_uint16),
    ]

    def as_value(self) -> Receiver:
        return Receiver(
            header=self.header.as_tuple(),
            entity_id=self.entity_id.as_tuple(),
            radio_id=int(self.radio_id),
            receiver_state=int(self.receiver_state),
            padding1=int(self.padding1),
            received_power=float(self.received_power),
            transmitter_entity_id=self.transmitter_entity_id.as_tuple(),
            transmitter_radio_id=int(self.transmitter_radio_id),
        )


class FastDisElectronicEmissions(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("emitting_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("state_update_indicator", ctypes.c_uint8),
        ("number_of_systems", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("system_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> ElectronicEmissions:
        return ElectronicEmissions(
            header=self.header.as_tuple(),
            emitting_entity_id=self.emitting_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            state_update_indicator=int(self.state_update_indicator),
            number_of_systems=int(self.number_of_systems),
            padding1=int(self.padding1),
            system_record_bytes=ctypes.string_at(self.system_records.bytes, int(self.system_records.bytes_size)) if self.system_records.bytes else b"",
        )


class FastDisIffAtcNavAidsLayer1(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("emitting_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("location", FastDisVec3f),
        ("system_id", FastDisSystemId),
        ("padding2", ctypes.c_uint16),
        ("fundamental_parameters", FastDisIffFundamentalData),
    ]

    def as_value(self) -> IffAtcNavAidsLayer1:
        return IffAtcNavAidsLayer1(
            header=self.header.as_tuple(),
            emitting_entity_id=self.emitting_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            location=self.location.as_tuple(),
            system_id=self.system_id.as_tuple(),
            padding2=int(self.padding2),
            fundamental_parameters=self.fundamental_parameters.as_tuple(),
        )


class FastDisIff(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("emitting_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("location", FastDisVec3f),
        ("system_id", FastDisSystemId),
        ("padding2", ctypes.c_uint16),
        ("fundamental_parameters", FastDisIffFundamentalData),
    ]

    def as_value(self) -> Iff:
        return Iff(
            header=self.header.as_tuple(),
            emitting_entity_id=self.emitting_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            location=self.location.as_tuple(),
            system_id=self.system_id.as_tuple(),
            padding2=int(self.padding2),
            fundamental_parameters=self.fundamental_parameters.as_tuple(),
        )


class FastDisUa(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("emitting_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("state_change_indicator", ctypes.c_int8),
        ("padding1", ctypes.c_uint8),
        ("passive_parameter_index", ctypes.c_uint16),
        ("propulsion_plant_configuration", ctypes.c_uint8),
        ("number_of_shafts", ctypes.c_uint8),
        ("number_of_apas", ctypes.c_uint8),
        ("number_of_ua_emitter_systems", ctypes.c_uint8),
        ("ua_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> Ua:
        return Ua(
            header=self.header.as_tuple(),
            emitting_entity_id=self.emitting_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            state_change_indicator=int(self.state_change_indicator),
            padding1=int(self.padding1),
            passive_parameter_index=int(self.passive_parameter_index),
            propulsion_plant_configuration=int(self.propulsion_plant_configuration),
            number_of_shafts=int(self.number_of_shafts),
            number_of_apas=int(self.number_of_apas),
            number_of_ua_emitter_systems=int(self.number_of_ua_emitter_systems),
            ua_record_bytes=ctypes.string_at(self.ua_records.bytes, int(self.ua_records.bytes_size)) if self.ua_records.bytes else b"",
        )


class FastDisSees(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("infrared_signature_representation_index", ctypes.c_uint16),
        ("acoustic_signature_representation_index", ctypes.c_uint16),
        ("radar_cross_section_signature_representation_index", ctypes.c_uint16),
        ("number_of_propulsion_systems", ctypes.c_uint16),
        ("number_of_vectoring_nozzle_systems", ctypes.c_uint16),
        ("supplemental_emission_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> Sees:
        return Sees(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            infrared_signature_representation_index=int(self.infrared_signature_representation_index),
            acoustic_signature_representation_index=int(self.acoustic_signature_representation_index),
            radar_cross_section_signature_representation_index=int(self.radar_cross_section_signature_representation_index),
            number_of_propulsion_systems=int(self.number_of_propulsion_systems),
            number_of_vectoring_nozzle_systems=int(self.number_of_vectoring_nozzle_systems),
            supplemental_emission_record_bytes=ctypes.string_at(self.supplemental_emission_records.bytes, int(self.supplemental_emission_records.bytes_size)) if self.supplemental_emission_records.bytes else b"",
        )


class FastDisIntercomSignal(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("entity_id", FastDisEntityId),
        ("communications_device_id", ctypes.c_uint16),
        ("encoding_scheme", ctypes.c_uint16),
        ("tdl_type", ctypes.c_uint16),
        ("sample_rate", ctypes.c_uint32),
        ("data_length", ctypes.c_uint16),
        ("samples", ctypes.c_uint16),
        ("data", FastDisCountedBytesView),
    ]

    def as_value(self) -> IntercomSignal:
        return IntercomSignal(
            header=self.header.as_tuple(),
            entity_id=self.entity_id.as_tuple(),
            communications_device_id=int(self.communications_device_id),
            encoding_scheme=int(self.encoding_scheme),
            tdl_type=int(self.tdl_type),
            sample_rate=int(self.sample_rate),
            data_length=int(self.data_length),
            samples=int(self.samples),
            data_bytes=ctypes.string_at(self.data.bytes, int(self.data.bytes_size)) if self.data.bytes else b"",
        )


class FastDisIntercomControl(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("control_type", ctypes.c_uint8),
        ("communications_channel_type", ctypes.c_uint8),
        ("source_entity_id", FastDisEntityId),
        ("source_communications_device_id", ctypes.c_uint8),
        ("source_line_id", ctypes.c_uint8),
        ("transmit_priority", ctypes.c_uint8),
        ("transmit_line_state", ctypes.c_uint8),
        ("command", ctypes.c_uint8),
        ("master_entity_id", FastDisEntityId),
        ("master_communications_device_id", ctypes.c_uint16),
        ("intercom_parameters_length", ctypes.c_uint32),
        ("intercom_parameters", FastDisCountedBytesView),
    ]

    def as_value(self) -> IntercomControl:
        return IntercomControl(
            header=self.header.as_tuple(),
            control_type=int(self.control_type),
            communications_channel_type=int(self.communications_channel_type),
            source_entity_id=self.source_entity_id.as_tuple(),
            source_communications_device_id=int(self.source_communications_device_id),
            source_line_id=int(self.source_line_id),
            transmit_priority=int(self.transmit_priority),
            transmit_line_state=int(self.transmit_line_state),
            command=int(self.command),
            master_entity_id=self.master_entity_id.as_tuple(),
            master_communications_device_id=int(self.master_communications_device_id),
            intercom_parameters_length=int(self.intercom_parameters_length),
            intercom_parameters_bytes=ctypes.string_at(self.intercom_parameters.bytes, int(self.intercom_parameters.bytes_size)) if self.intercom_parameters.bytes else b"",
        )


class FastDisAttribute(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_simulation_address", FastDisSimulationAddress),
        ("padding1", ctypes.c_int32),
        ("padding2", ctypes.c_int16),
        ("attribute_record_pdu_type", ctypes.c_uint8),
        ("attribute_record_protocol_version", ctypes.c_uint8),
        ("master_attribute_record_type", ctypes.c_uint32),
        ("action_code", ctypes.c_uint8),
        ("padding3", ctypes.c_int8),
        ("number_attribute_record_set", ctypes.c_uint16),
        ("attribute_record_sets", FastDisCountedBytesView),
    ]

    def as_value(self) -> Attribute:
        return Attribute(
            header=self.header.as_tuple(),
            originating_simulation_address=self.originating_simulation_address.as_tuple(),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            attribute_record_pdu_type=int(self.attribute_record_pdu_type),
            attribute_record_protocol_version=int(self.attribute_record_protocol_version),
            master_attribute_record_type=int(self.master_attribute_record_type),
            action_code=int(self.action_code),
            padding3=int(self.padding3),
            number_attribute_record_set=int(self.number_attribute_record_set),
            attribute_record_set_bytes=ctypes.string_at(self.attribute_record_sets.bytes, int(self.attribute_record_sets.bytes_size)) if self.attribute_record_sets.bytes else b"",
        )


class FastDisDirectedEnergyFire(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_entity_id", FastDisEntityId),
        ("target_entity_id", FastDisEntityId),
        ("munition_type", FastDisEntityType),
        ("shot_start_time", FastDisClockTime),
        ("commulative_shot_time", ctypes.c_float),
        ("aperture_emitter_location", FastDisVec3f),
        ("aperture_diameter", ctypes.c_float),
        ("wavelength", ctypes.c_float),
        ("peak_irradiance", ctypes.c_float),
        ("pulse_repetition_frequency", ctypes.c_float),
        ("pulse_width", ctypes.c_int32),
        ("flags", ctypes.c_int32),
        ("pulse_shape", ctypes.c_int8),
        ("padding1", ctypes.c_uint8),
        ("padding2", ctypes.c_uint32),
        ("padding3", ctypes.c_uint16),
        ("number_of_de_records", ctypes.c_uint16),
        ("de_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> DirectedEnergyFire:
        return DirectedEnergyFire(
            header=self.header.as_tuple(),
            firing_entity_id=self.firing_entity_id.as_tuple(),
            target_entity_id=self.target_entity_id.as_tuple(),
            munition_type=self.munition_type.as_tuple(),
            shot_start_time=self.shot_start_time.as_tuple(),
            commulative_shot_time=float(self.commulative_shot_time),
            aperture_emitter_location=self.aperture_emitter_location.as_tuple(),
            aperture_diameter=float(self.aperture_diameter),
            wavelength=float(self.wavelength),
            peak_irradiance=float(self.peak_irradiance),
            pulse_repetition_frequency=float(self.pulse_repetition_frequency),
            pulse_width=int(self.pulse_width),
            flags=int(self.flags),
            pulse_shape=int(self.pulse_shape),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            padding3=int(self.padding3),
            number_of_de_records=int(self.number_of_de_records),
            de_record_bytes=ctypes.string_at(self.de_records.bytes, int(self.de_records.bytes_size)) if self.de_records.bytes else b"",
        )


class FastDisEntityDamageStatus(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_entity_id", FastDisEntityId),
        ("target_entity_id", FastDisEntityId),
        ("damaged_entity_id", FastDisEntityId),
        ("padding1", ctypes.c_uint16),
        ("padding2", ctypes.c_uint16),
        ("number_of_damage_description", ctypes.c_uint16),
        ("damage_description_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> EntityDamageStatus:
        return EntityDamageStatus(
            header=self.header.as_tuple(),
            firing_entity_id=self.firing_entity_id.as_tuple(),
            target_entity_id=self.target_entity_id.as_tuple(),
            damaged_entity_id=self.damaged_entity_id.as_tuple(),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            number_of_damage_description=int(self.number_of_damage_description),
            damage_description_bytes=ctypes.string_at(self.damage_description_records.bytes, int(self.damage_description_records.bytes_size)) if self.damage_description_records.bytes else b"",
        )


class FastDisInformationOperationsAction(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_sim_id", FastDisEntityId),
        ("receiving_sim_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("io_warfare_type", ctypes.c_uint16),
        ("io_simulation_source", ctypes.c_uint16),
        ("io_action_type", ctypes.c_uint16),
        ("io_action_phase", ctypes.c_uint16),
        ("padding1", ctypes.c_uint32),
        ("io_attacker_id", FastDisEntityId),
        ("io_primary_target_id", FastDisEntityId),
        ("padding2", ctypes.c_uint16),
        ("number_of_io_records", ctypes.c_uint16),
        ("io_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> InformationOperationsAction:
        return InformationOperationsAction(
            header=self.header.as_tuple(),
            originating_sim_id=self.originating_sim_id.as_tuple(),
            receiving_sim_id=self.receiving_sim_id.as_tuple(),
            request_id=int(self.request_id),
            io_warfare_type=int(self.io_warfare_type),
            io_simulation_source=int(self.io_simulation_source),
            io_action_type=int(self.io_action_type),
            io_action_phase=int(self.io_action_phase),
            padding1=int(self.padding1),
            io_attacker_id=self.io_attacker_id.as_tuple(),
            io_primary_target_id=self.io_primary_target_id.as_tuple(),
            padding2=int(self.padding2),
            number_of_io_records=int(self.number_of_io_records),
            io_record_bytes=ctypes.string_at(self.io_records.bytes, int(self.io_records.bytes_size)) if self.io_records.bytes else b"",
        )


class FastDisInformationOperationsReport(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_sim_id", FastDisEntityId),
        ("io_sim_source", ctypes.c_uint16),
        ("io_report_type", ctypes.c_uint8),
        ("padding1", ctypes.c_uint8),
        ("io_attacker_id", FastDisEntityId),
        ("io_primary_target_id", FastDisEntityId),
        ("padding2", ctypes.c_uint16),
        ("padding3", ctypes.c_uint16),
        ("number_of_io_records", ctypes.c_uint16),
        ("io_records", FastDisCountedBytesView),
    ]

    def as_value(self) -> InformationOperationsReport:
        return InformationOperationsReport(
            header=self.header.as_tuple(),
            originating_sim_id=self.originating_sim_id.as_tuple(),
            io_sim_source=int(self.io_sim_source),
            io_report_type=int(self.io_report_type),
            padding1=int(self.padding1),
            io_attacker_id=self.io_attacker_id.as_tuple(),
            io_primary_target_id=self.io_primary_target_id.as_tuple(),
            padding2=int(self.padding2),
            padding3=int(self.padding3),
            number_of_io_records=int(self.number_of_io_records),
            io_record_bytes=ctypes.string_at(self.io_records.bytes, int(self.io_records.bytes_size)) if self.io_records.bytes else b"",
        )


class FastDisServiceRequest(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("requesting_entity_id", FastDisEntityId),
        ("servicing_entity_id", FastDisEntityId),
        ("service_type_requested", ctypes.c_uint8),
        ("number_of_supply_types", ctypes.c_uint8),
        ("service_request_padding", ctypes.c_int16),
        ("supplies", FastDisCountedBytesView),
    ]

    def as_value(self) -> ServiceRequest:
        return ServiceRequest(
            header=self.header.as_tuple(),
            requesting_entity_id=self.requesting_entity_id.as_tuple(),
            servicing_entity_id=self.servicing_entity_id.as_tuple(),
            service_type_requested=int(self.service_type_requested),
            number_of_supply_types=int(self.number_of_supply_types),
            service_request_padding=int(self.service_request_padding),
            supply_bytes=ctypes.string_at(self.supplies.bytes, int(self.supplies.bytes_size)) if self.supplies.bytes else b"",
        )


class FastDisResupplyOffer(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("receiving_entity_id", FastDisEntityId),
        ("supplying_entity_id", FastDisEntityId),
        ("number_of_supply_types", ctypes.c_uint8),
        ("padding_bytes", ctypes.c_uint8 * 3),
        ("supplies", FastDisCountedBytesView),
    ]

    def as_value(self) -> ResupplyOffer:
        return ResupplyOffer(
            header=self.header.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            supplying_entity_id=self.supplying_entity_id.as_tuple(),
            number_of_supply_types=int(self.number_of_supply_types),
            padding_bytes=bytes(self.padding_bytes),
            supply_bytes=ctypes.string_at(self.supplies.bytes, int(self.supplies.bytes_size)) if self.supplies.bytes else b"",
        )


class FastDisResupplyReceived(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("receiving_entity_id", FastDisEntityId),
        ("supplying_entity_id", FastDisEntityId),
        ("number_of_supply_types", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("padding2", ctypes.c_uint8),
        ("supplies", FastDisCountedBytesView),
    ]

    def as_value(self) -> ResupplyReceived:
        return ResupplyReceived(
            header=self.header.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            supplying_entity_id=self.supplying_entity_id.as_tuple(),
            number_of_supply_types=int(self.number_of_supply_types),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
            supply_bytes=ctypes.string_at(self.supplies.bytes, int(self.supplies.bytes_size)) if self.supplies.bytes else b"",
        )


class FastDisResupplyCancel(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("receiving_entity_id", FastDisEntityId),
        ("supplying_entity_id", FastDisEntityId),
    ]

    def as_value(self) -> ResupplyCancel:
        return ResupplyCancel(
            header=self.header.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            supplying_entity_id=self.supplying_entity_id.as_tuple(),
        )


class FastDisRepairComplete(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("receiving_entity_id", FastDisEntityId),
        ("repairing_entity_id", FastDisEntityId),
        ("repair", ctypes.c_uint16),
        ("padding2", ctypes.c_int16),
    ]

    def as_value(self) -> RepairComplete:
        return RepairComplete(
            header=self.header.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            repairing_entity_id=self.repairing_entity_id.as_tuple(),
            repair=int(self.repair),
            padding2=int(self.padding2),
        )


class FastDisRepairResponse(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("receiving_entity_id", FastDisEntityId),
        ("repairing_entity_id", FastDisEntityId),
        ("repair_result", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
        ("padding2", ctypes.c_uint8),
    ]

    def as_value(self) -> RepairResponse:
        return RepairResponse(
            header=self.header.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            repairing_entity_id=self.repairing_entity_id.as_tuple(),
            repair_result=int(self.repair_result),
            padding1=int(self.padding1),
            padding2=int(self.padding2),
        )


class FastDisActionRequest(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("action_id", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> ActionRequest:
        return ActionRequest(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            action_id=int(self.action_id),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisActionResponse(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("request_status", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> ActionResponse:
        return ActionResponse(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            request_status=int(self.request_status),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisDataQuery(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("time_interval", FastDisClockTime),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> DataQuery:
        return DataQuery(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            time_interval=self.time_interval.as_tuple(),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisSetData(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("padding1", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> SetData:
        return SetData(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            padding1=int(self.padding1),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisEventReport(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("event_type", ctypes.c_uint32),
        ("padding1", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> EventReport:
        return EventReport(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            event_type=int(self.event_type),
            padding1=int(self.padding1),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisComment(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> Comment:
        return Comment(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisActionRequestReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
        ("action_id", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> ActionRequestReliable:
        return ActionRequestReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            request_id=int(self.request_id),
            action_id=int(self.action_id),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisActionResponseReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("response_status", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> ActionResponseReliable:
        return ActionResponseReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            response_status=int(self.response_status),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisDataQueryReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
        ("time_interval", FastDisClockTime),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> DataQueryReliable:
        return DataQueryReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            request_id=int(self.request_id),
            time_interval=self.time_interval.as_tuple(),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisSetDataReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("request_id", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> SetDataReliable:
        return SetDataReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            request_id=int(self.request_id),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisDataReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> DataReliable:
        return DataReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisEventReportReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("event_type", ctypes.c_uint32),
        ("pad1", ctypes.c_uint32),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> EventReportReliable:
        return EventReportReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            event_type=int(self.event_type),
            pad1=int(self.pad1),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisCommentReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("datum_records", FastDisDatumRecordSetView),
    ]

    def as_value(self) -> CommentReliable:
        return CommentReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            number_of_fixed_datum_records=int(self.datum_records.number_of_fixed_datum_records),
            number_of_variable_datum_records=int(self.datum_records.number_of_variable_datum_records),
            datum_record_bytes=ctypes.string_at(self.datum_records.datum_record_bytes, int(self.datum_records.datum_record_bytes_size)) if self.datum_records.datum_record_bytes else b"",
        )


class FastDisRecordReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
        ("event_type", ctypes.c_uint16),
        ("record_sets", FastDisCountedBytesView),
    ]

    def as_value(self) -> RecordReliable:
        return RecordReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            event_type=int(self.event_type),
            record_set_count=int(self.record_sets.count),
            record_set_bytes=ctypes.string_at(self.record_sets.bytes, int(self.record_sets.bytes_size)) if self.record_sets.bytes else b"",
        )


class FastDisSetRecordReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("record_sets", FastDisCountedBytesView),
    ]

    def as_value(self) -> SetRecordReliable:
        return SetRecordReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            record_set_count=int(self.record_sets.count),
            record_set_bytes=ctypes.string_at(self.record_sets.bytes, int(self.record_sets.bytes_size)) if self.record_sets.bytes else b"",
        )


class FastDisRecordQueryReliable(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("originating_entity_id", FastDisEntityId),
        ("receiving_entity_id", FastDisEntityId),
        ("request_id", ctypes.c_uint32),
        ("required_reliability_service", ctypes.c_uint8),
        ("pad1", ctypes.c_uint16),
        ("pad2", ctypes.c_uint8),
        ("event_type", ctypes.c_uint16),
        ("time", ctypes.c_uint32),
        ("record_ids", FastDisCountedBytesView),
    ]

    def as_value(self) -> RecordQueryReliable:
        return RecordQueryReliable(
            header=self.header.as_tuple(),
            originating_entity_id=self.originating_entity_id.as_tuple(),
            receiving_entity_id=self.receiving_entity_id.as_tuple(),
            request_id=int(self.request_id),
            required_reliability_service=int(self.required_reliability_service),
            pad1=int(self.pad1),
            pad2=int(self.pad2),
            event_type=int(self.event_type),
            time=int(self.time),
            record_id_count=int(self.record_ids.count),
            record_id_bytes=ctypes.string_at(self.record_ids.bytes, int(self.record_ids.bytes_size)) if self.record_ids.bytes else b"",
        )


class FastDisFire(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_entity_id", FastDisEntityId),
        ("target_entity_id", FastDisEntityId),
        ("munition_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("fire_mission_index", ctypes.c_uint32),
        ("world_location", FastDisWorldCoordinates),
        ("munition_descriptor", FastDisBurstDescriptor),
        ("velocity", FastDisVec3f),
        ("range_to_target", ctypes.c_float),
    ]

    def as_value(self) -> Fire:
        return Fire(
            header=self.header.as_tuple(),
            firing_entity_id=self.firing_entity_id.as_tuple(),
            target_entity_id=self.target_entity_id.as_tuple(),
            munition_entity_id=self.munition_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            fire_mission_index=int(self.fire_mission_index),
            world_location=self.world_location.as_tuple(),
            munition_type=self.munition_descriptor.munition_type.as_tuple(),
            warhead=int(self.munition_descriptor.warhead),
            fuse=int(self.munition_descriptor.fuse),
            quantity=int(self.munition_descriptor.quantity),
            rate=int(self.munition_descriptor.rate),
            velocity=self.velocity.as_tuple(),
            range_to_target=float(self.range_to_target),
        )


class FastDisDetonation(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("firing_entity_id", FastDisEntityId),
        ("target_entity_id", FastDisEntityId),
        ("exploding_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("velocity", FastDisVec3f),
        ("world_location", FastDisWorldCoordinates),
        ("munition_descriptor", FastDisBurstDescriptor),
        ("location_in_entity_coordinates", FastDisVec3f),
        ("detonation_result", ctypes.c_uint8),
        ("variable_parameter_count", ctypes.c_uint8),
        ("padding1", ctypes.c_uint16),
    ]

    def as_value(self) -> Detonation:
        return Detonation(
            header=self.header.as_tuple(),
            firing_entity_id=self.firing_entity_id.as_tuple(),
            target_entity_id=self.target_entity_id.as_tuple(),
            exploding_entity_id=self.exploding_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            velocity=self.velocity.as_tuple(),
            world_location=self.world_location.as_tuple(),
            munition_type=self.munition_descriptor.munition_type.as_tuple(),
            warhead=int(self.munition_descriptor.warhead),
            fuse=int(self.munition_descriptor.fuse),
            quantity=int(self.munition_descriptor.quantity),
            rate=int(self.munition_descriptor.rate),
            location_in_entity_coordinates=self.location_in_entity_coordinates.as_tuple(),
            detonation_result=int(self.detonation_result),
            variable_parameter_count=int(self.variable_parameter_count),
            padding1=int(self.padding1),
        )


class FastDisCollision(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("issuing_entity_id", FastDisEntityId),
        ("colliding_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("collision_type", ctypes.c_uint8),
        ("padding1", ctypes.c_uint8),
        ("velocity", FastDisVec3f),
        ("mass", ctypes.c_float),
        ("location", FastDisVec3f),
    ]

    def as_value(self) -> Collision:
        return Collision(
            header=self.header.as_tuple(),
            issuing_entity_id=self.issuing_entity_id.as_tuple(),
            colliding_entity_id=self.colliding_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            collision_type=int(self.collision_type),
            padding1=int(self.padding1),
            velocity=self.velocity.as_tuple(),
            mass=float(self.mass),
            location=self.location.as_tuple(),
        )


class FastDisCollisionElastic(ctypes.Structure):
    _fields_ = [
        ("header", FastDisHeader),
        ("issuing_entity_id", FastDisEntityId),
        ("colliding_entity_id", FastDisEntityId),
        ("event_id", FastDisEventId),
        ("padding1", ctypes.c_uint16),
        ("contact_velocity", FastDisVec3f),
        ("mass", ctypes.c_float),
        ("location", FastDisVec3f),
        ("collision_result_xx", ctypes.c_float),
        ("collision_result_xy", ctypes.c_float),
        ("collision_result_xz", ctypes.c_float),
        ("collision_result_yy", ctypes.c_float),
        ("collision_result_yz", ctypes.c_float),
        ("collision_result_zz", ctypes.c_float),
        ("unit_surface_normal", FastDisVec3f),
        ("coefficient_of_restitution", ctypes.c_float),
    ]

    def as_value(self) -> CollisionElastic:
        return CollisionElastic(
            header=self.header.as_tuple(),
            issuing_entity_id=self.issuing_entity_id.as_tuple(),
            colliding_entity_id=self.colliding_entity_id.as_tuple(),
            event_id=self.event_id.as_tuple(),
            padding1=int(self.padding1),
            contact_velocity=self.contact_velocity.as_tuple(),
            mass=float(self.mass),
            location=self.location.as_tuple(),
            collision_result_xx=float(self.collision_result_xx),
            collision_result_xy=float(self.collision_result_xy),
            collision_result_xz=float(self.collision_result_xz),
            collision_result_yy=float(self.collision_result_yy),
            collision_result_yz=float(self.collision_result_yz),
            collision_result_zz=float(self.collision_result_zz),
            unit_surface_normal=self.unit_surface_normal.as_tuple(),
            coefficient_of_restitution=float(self.coefficient_of_restitution),
        )


class FastDisEntityStateBatch(ctypes.Structure):
    _fields_ = [
        ("entities", ctypes.POINTER(FastDisEntityStatePrefix)),
        ("capacity", ctypes.c_size_t),
        ("count", ctypes.c_size_t),
        ("dropped", ctypes.c_size_t),
    ]


class FastDisEntityTransformBatch(ctypes.Structure):
    _fields_ = [
        ("transforms", ctypes.POINTER(FastDisEntityTransform)),
        ("capacity", ctypes.c_size_t),
        ("count", ctypes.c_size_t),
        ("dropped", ctypes.c_size_t),
    ]


class FastDisEntitySnapshot(ctypes.Structure):
    _fields_ = [
        ("transform", FastDisEntityTransform),
        ("first_seen_tick", ctypes.c_uint64),
        ("last_seen_tick", ctypes.c_uint64),
        ("update_count", ctypes.c_uint64),
        ("change_flags", ctypes.c_uint32),
        ("reserved0", ctypes.c_uint32),
    ]

    def as_value(self) -> EntitySnapshot:
        return EntitySnapshot(
            transform=self.transform.as_value(),
            first_seen_tick=int(self.first_seen_tick),
            last_seen_tick=int(self.last_seen_tick),
            update_count=int(self.update_count),
            change_flags=int(self.change_flags),
        )


class FastDisEntitySnapshotBatch(ctypes.Structure):
    _fields_ = [
        ("snapshots", ctypes.POINTER(FastDisEntitySnapshot)),
        ("capacity", ctypes.c_size_t),
        ("count", ctypes.c_size_t),
        ("dropped", ctypes.c_size_t),
    ]


class FastDisEntitySnapshotView(ctypes.Structure):
    _fields_ = [
        ("snapshots", ctypes.POINTER(FastDisEntitySnapshot)),
        ("count", ctypes.c_size_t),
        ("dropped", ctypes.c_size_t),
        ("generation", ctypes.c_uint64),
        ("slot", ctypes.c_uint32),
        ("reserved0", ctypes.c_uint32),
    ]

    def as_value(self) -> EntitySnapshotView:
        if not self.snapshots or self.count == 0:
            records: tuple[EntitySnapshot, ...] = ()
        else:
            records = tuple(self.snapshots[i].as_value() for i in range(int(self.count)))
        return EntitySnapshotView(
            snapshots=records,
            count=int(self.count),
            dropped=int(self.dropped),
            generation=int(self.generation),
            slot=int(self.slot),
        )


class FastDisU8Filter(ctypes.Structure):
    _fields_ = [
        ("active", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 7),
        ("bits", ctypes.c_uint64 * 4),
    ]


class FastDisScanConfig(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("sample_every", ctypes.c_uint32),
        ("sample_offset", ctypes.c_uint32),
        ("versions", FastDisU8Filter),
        ("pdu_types", FastDisU8Filter),
        ("protocol_families", FastDisU8Filter),
        ("exercise_ids", FastDisU8Filter),
        ("entity_force_ids", FastDisU8Filter),
        ("entity_state_fields", ctypes.c_uint64),
    ]


class FastDisScanStats(ctypes.Structure):
    _fields_ = [
        ("seen", ctypes.c_uint64),
        ("malformed", ctypes.c_uint64),
        ("accepted", ctypes.c_uint64),
        ("emitted", ctypes.c_uint64),
    ]

    def as_tuple(self) -> tuple[int, int, int]:
        """Compatibility tuple: seen, accepted, emitted."""

        return (int(self.seen), int(self.accepted), int(self.emitted))

    def as_dict(self) -> dict[str, int]:
        return {str(field[0]): int(getattr(self, str(field[0]))) for field in self._fields_}


class FastDisEntityTableUpdateStats(ctypes.Structure):
    _fields_ = [
        ("scan", FastDisScanStats),
        ("tick", ctypes.c_uint64),
        ("entity_count", ctypes.c_uint64),
        ("table_updates", ctypes.c_uint64),
        ("new_entities", ctypes.c_uint64),
        ("changed_entities", ctypes.c_uint64),
        ("unchanged_entities", ctypes.c_uint64),
        ("removed_entities", ctypes.c_uint64),
    ]

    def as_dict(self) -> dict[str, int | dict[str, int]]:
        return {
            "scan": self.scan.as_dict(),
            "tick": int(self.tick),
            "entity_count": int(self.entity_count),
            "table_updates": int(self.table_updates),
            "new_entities": int(self.new_entities),
            "changed_entities": int(self.changed_entities),
            "unchanged_entities": int(self.unchanged_entities),
            "removed_entities": int(self.removed_entities),
        }


class FastDisSnapshotBufferStats(ctypes.Structure):
    _fields_ = [
        ("publish_attempts", ctypes.c_uint64),
        ("publish_successes", ctypes.c_uint64),
        ("publish_busy", ctypes.c_uint64),
        ("acquire_count", ctypes.c_uint64),
        ("release_count", ctypes.c_uint64),
        ("max_snapshot_count", ctypes.c_uint64),
        ("dropped_snapshots", ctypes.c_uint64),
    ]

    def as_value(self) -> SnapshotBufferStats:
        return SnapshotBufferStats(*(int(getattr(self, str(field[0]))) for field in self._fields_))

    def as_dict(self) -> dict[str, int]:
        return self.as_value().as_dict()


class FastDisPacketView(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
        ("user", ctypes.c_void_p),
    ]


def _packet_view_bytes(view: FastDisPacketView) -> bytes:
    size = int(view.size)
    if not view.data or size <= 0:
        return b""
    return ctypes.string_at(view.data, size)


def _raw_transform_from_value(transform: EntityTransform) -> FastDisEntityTransform:
    raw = FastDisEntityTransform()
    raw.entity_id.site = int(transform.entity_id[0])
    raw.entity_id.application = int(transform.entity_id[1])
    raw.entity_id.entity = int(transform.entity_id[2])
    raw.force_id = int(transform.force_id)
    raw.exercise_id = int(transform.exercise_id)
    raw.version = int(transform.version)
    raw.timestamp = int(transform.timestamp)
    raw.appearance = int(transform.appearance)
    raw.location.x = float(transform.location[0])
    raw.location.y = float(transform.location[1])
    raw.location.z = float(transform.location[2])
    raw.orientation.psi = float(transform.orientation[0])
    raw.orientation.theta = float(transform.orientation[1])
    raw.orientation.phi = float(transform.orientation[2])
    raw.linear_velocity.x = float(transform.linear_velocity[0])
    raw.linear_velocity.y = float(transform.linear_velocity[1])
    raw.linear_velocity.z = float(transform.linear_velocity[2])
    raw.fields_present = int(transform.fields_present)
    raw.dead_reckoning_algorithm = int(transform.dead_reckoning_algorithm)
    params = bytes(transform.dead_reckoning_parameters[:15])
    for index, value in enumerate(params):
        raw.dead_reckoning_parameters[index] = value
    raw.dead_reckoning_linear_acceleration.x = float(transform.dead_reckoning_linear_acceleration[0])
    raw.dead_reckoning_linear_acceleration.y = float(transform.dead_reckoning_linear_acceleration[1])
    raw.dead_reckoning_linear_acceleration.z = float(transform.dead_reckoning_linear_acceleration[2])
    raw.dead_reckoning_angular_velocity.x = float(transform.dead_reckoning_angular_velocity[0])
    raw.dead_reckoning_angular_velocity.y = float(transform.dead_reckoning_angular_velocity[1])
    raw.dead_reckoning_angular_velocity.z = float(transform.dead_reckoning_angular_velocity[2])
    return raw


def _raw_snapshot_from_value(snapshot: EntitySnapshot) -> FastDisEntitySnapshot:
    raw = FastDisEntitySnapshot()
    raw.transform = _raw_transform_from_value(snapshot.transform)
    raw.first_seen_tick = int(snapshot.first_seen_tick)
    raw.last_seen_tick = int(snapshot.last_seen_tick)
    raw.update_count = int(snapshot.update_count)
    raw.change_flags = int(snapshot.change_flags)
    return raw


PacketCallbackC = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.POINTER(FastDisHeader),
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_size_t,
    ctypes.c_void_p,
    ctypes.c_void_p,
)

EntityStateCallbackC = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.POINTER(FastDisEntityStatePrefix),
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_size_t,
    ctypes.c_void_p,
    ctypes.c_void_p,
)


def _library_filenames() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return ["fastdis.dll"]
    if system == "darwin":
        return ["libfastdis.dylib", "fastdis.dylib", "libfastdis.so"]
    return ["libfastdis.so", "libfastdis.so.0", "fastdis.so"]


def _is_loadable_library_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith((".so", ".so.0", ".dylib", ".dll"))


def _platform_glob_patterns() -> tuple[str, ...]:
    system = platform.system().lower()
    if system == "windows":
        return (
            "build/cmake/*/fastdis.dll",
            "build/cmake/*/Release/fastdis.dll",
            "build/cmake/*/libfastdis.dll",
            "build/cmake/*/Release/libfastdis.dll",
            "build*/fastdis.dll",
            "build*/libfastdis.dll",
            "cmake-build*/fastdis.dll",
            "cmake-build*/libfastdis.dll",
            "out*/fastdis.dll",
            "out*/libfastdis.dll",
        )
    if system == "darwin":
        return (
            "build/cmake/*/libfastdis*.dylib",
            "build*/libfastdis*.dylib",
            "cmake-build*/libfastdis*.dylib",
            "out*/libfastdis*.dylib",
        )
    return (
        "build/cmake/*/libfastdis.so*",
        "build*/libfastdis.so*",
        "cmake-build*/libfastdis.so*",
        "out*/libfastdis.so*",
    )


def _candidate_paths() -> Iterable[Path]:
    env = os.environ.get("FASTDIS_LIBRARY")
    if env:
        yield Path(env)

    here = Path(__file__).resolve().parent
    roots = [
        here,
        here.parent,
        Path.cwd(),
        Path.cwd() / "build" / "cmake" / "host",
        Path.cwd() / "build" / "cmake" / "mingw-win64",
        Path.cwd() / "build" / "cmake" / "linux-x86_64",
        Path.cwd() / "build",
        Path.cwd() / "build" / "native",
    ]
    for root in roots:
        for name in _library_filenames():
            yield root / name

    cwd = Path.cwd()
    for pattern in _platform_glob_patterns():
        yield from cwd.glob(pattern)


def find_native_library() -> str | None:
    """Return a loadable native library path/name, or None."""

    for candidate in _candidate_paths():
        if candidate.exists() and _is_loadable_library_path(candidate):
            return str(candidate)

    found = ctypes.util.find_library("fastdis")
    if found:
        return found
    return None


def _buffer_ptr(data: bytes | bytearray | memoryview):
    view = memoryview(data)
    if view.format != "B" or view.itemsize != 1:
        view = view.cast("B")
    if not view.contiguous:
        data = view.tobytes()
        view = memoryview(data)
    n = len(view)
    if n == 0:
        empty = (ctypes.c_uint8 * 1)()
        return empty, ctypes.cast(empty, ctypes.POINTER(ctypes.c_uint8)), 0
    try:
        arr_type = ctypes.c_uint8 * n
        keepalive = arr_type.from_buffer(view)  # zero-copy for writable buffers
    except TypeError:
        keepalive = ctypes.create_string_buffer(view.tobytes(), n)  # copy for bytes/read-only buffers
    ptr = ctypes.cast(keepalive, ctypes.POINTER(ctypes.c_uint8))
    return keepalive, ptr, n


def _filter_values(values: None | int | Iterable[int]) -> list[int]:
    if values is None:
        return []
    if isinstance(values, int):
        values = [values]
    out: list[int] = []
    for value in values:
        if not isinstance(value, int):
            raise TypeError("filter values must be integers")
        if not 0 <= value <= 255:
            raise ValueError("filter values must be in 0..255")
        out.append(value)
    return out



def _filter_kind(kind: int | str) -> int:
    if isinstance(kind, str):
        key = kind.strip().lower().replace("-", "_").replace(" ", "_")
        try:
            return _FILTER_KIND_NAMES[key]
        except KeyError as exc:
            raise ValueError(f"unknown fastdis filter kind: {kind!r}") from exc
    value = int(kind)
    if value not in {
        FASTDIS_FILTER_VERSION,
        FASTDIS_FILTER_PDU_TYPE,
        FASTDIS_FILTER_PROTOCOL_FAMILY,
        FASTDIS_FILTER_EXERCISE_ID,
        FASTDIS_FILTER_ENTITY_FORCE_ID,
    }:
        raise ValueError(f"unknown fastdis filter kind: {kind!r}")
    return value


def _profile_kind(profile: int | str) -> int:
    if isinstance(profile, str):
        key = profile.strip().lower().replace("-", "_").replace(" ", "_")
        try:
            return _PROFILE_NAMES[key]
        except KeyError as exc:
            raise ValueError(f"unknown fastdis profile: {profile!r}") from exc
    value = int(profile)
    if value not in set(_PROFILE_NAMES.values()):
        raise ValueError(f"unknown fastdis profile: {profile!r}")
    return value


def _is_entity_id_tuple(value: object) -> TypeGuard[EntityIdTuple]:
    return isinstance(value, tuple) and len(value) == 3 and all(isinstance(part, int) for part in value)


def _entity_ids(values: Iterable[EntityIdTuple] | EntityIdTuple) -> list[EntityIdTuple]:
    if _is_entity_id_tuple(values):
        items: Iterable[EntityIdTuple] = [values]
    else:
        items = cast(Iterable[EntityIdTuple], values)
    out: list[EntityIdTuple] = []
    for item in items:
        if len(item) != 3:
            raise ValueError("entity IDs must be (site, application, entity) triples")
        site, application, entity = (int(item[0]), int(item[1]), int(item[2]))
        for value in (site, application, entity):
            if not 0 <= value <= 0xFFFF:
                raise ValueError("entity ID components must be in 0..65535")
        out.append((site, application, entity))
    return out


def _iter_entity_state_fields(fields: Iterable[int | str | Iterable[int | str]]) -> Iterable[int | str]:
    for field in fields:
        if isinstance(field, (int, str)):
            yield field
        else:
            yield from field


def entity_state_field_mask(*fields: int | str | Iterable[int | str]) -> int:
    """Build an Entity State field mask from integers, names, or groups.

    Examples:
        entity_state_field_mask("location", "orientation")
        entity_state_field_mask("pose")
        entity_state_field_mask(FASTDIS_ES_FIELD_ENTITY_ID, "marking")
    """

    mask = 0
    for item in _iter_entity_state_fields(fields):
        if isinstance(item, str):
            key = item.strip().lower().replace("-", "_").replace(" ", "_")
            try:
                mask |= int(_ENTITY_STATE_FIELD_NAMES[key])
            except KeyError as exc:
                raise ValueError(f"unknown Entity State field: {item!r}") from exc
        else:
            mask |= int(item)
    return mask


def _entity_id_array(values: Iterable[EntityIdTuple] | EntityIdTuple):
    ids = _entity_ids(values)
    if not ids:
        return ids, None
    array_type = FastDisEntityId * len(ids)
    return ids, array_type(*(FastDisEntityId(site, application, entity) for site, application, entity in ids))


def _ctypes_transform(value: EntityTransform | FastDisEntityTransform) -> FastDisEntityTransform:
    if isinstance(value, FastDisEntityTransform):
        return value
    out = FastDisEntityTransform()
    out.entity_id = FastDisEntityId(*value.entity_id)
    out.force_id = int(value.force_id)
    out.exercise_id = int(value.exercise_id)
    out.version = int(value.version)
    out.reserved0 = 0
    out.timestamp = int(value.timestamp)
    out.appearance = int(value.appearance)
    out.location = FastDisWorldCoordinates(*value.location)
    out.orientation = FastDisEulerAngles(*value.orientation)
    out.linear_velocity = FastDisVec3f(*value.linear_velocity)
    out.fields_present = int(value.fields_present)
    out.dead_reckoning_algorithm = int(value.dead_reckoning_algorithm)
    params = bytes(value.dead_reckoning_parameters[:15])
    for index, param in enumerate(params):
        out.dead_reckoning_parameters[index] = param
    out.dead_reckoning_linear_acceleration = FastDisVec3f(*value.dead_reckoning_linear_acceleration)
    out.dead_reckoning_angular_velocity = FastDisVec3f(*value.dead_reckoning_angular_velocity)
    return out


class NativeFastDis:
    """Loaded fastdis C ABI wrapper."""

    def __init__(self, path: str | os.PathLike[str] | None = None):
        resolved = str(path) if path is not None else find_native_library()
        if not resolved:
            raise FastDisError(
                "Could not find fastdis native library. Set FASTDIS_LIBRARY to "
                "the path of libfastdis.so, libfastdis.dylib, or fastdis.dll."
            )
        self.path = resolved
        self.lib = ctypes.CDLL(resolved)
        self._configure_functions()
        abi = self.abi_version()
        if abi != FASTDIS_ABI_VERSION:
            raise FastDisError(f"Unsupported fastdis ABI {abi}; expected {FASTDIS_ABI_VERSION}")

    def _configure_functions(self) -> None:
        lib = self.lib
        lib.fastdis_abi_version.argtypes = []
        lib.fastdis_abi_version.restype = ctypes.c_uint32
        lib.fastdis_abi_epoch.argtypes = []
        lib.fastdis_abi_epoch.restype = ctypes.c_uint32
        lib.fastdis_abi_revision.argtypes = []
        lib.fastdis_abi_revision.restype = ctypes.c_uint32

        lib.fastdis_version_string.argtypes = []
        lib.fastdis_version_string.restype = ctypes.c_char_p

        lib.fastdis_status_string.argtypes = [ctypes.c_int]
        lib.fastdis_status_string.restype = ctypes.c_char_p

        lib.fastdis_scan_config_init.argtypes = [ctypes.POINTER(FastDisScanConfig)]
        lib.fastdis_scan_config_init.restype = None

        lib.fastdis_scan_stats_init.argtypes = [ctypes.POINTER(FastDisScanStats)]
        lib.fastdis_scan_stats_init.restype = None
        lib.fastdis_entity_table_update_stats_init.argtypes = [ctypes.POINTER(FastDisEntityTableUpdateStats)]
        lib.fastdis_entity_table_update_stats_init.restype = None
        lib.fastdis_entity_snapshot_buffer_stats_init.argtypes = [ctypes.POINTER(FastDisSnapshotBufferStats)]
        lib.fastdis_entity_snapshot_buffer_stats_init.restype = None

        lib.fastdis_filter_accept_all.argtypes = [ctypes.POINTER(FastDisU8Filter)]
        lib.fastdis_filter_accept_all.restype = None
        lib.fastdis_filter_clear.argtypes = [ctypes.POINTER(FastDisU8Filter)]
        lib.fastdis_filter_clear.restype = None
        lib.fastdis_filter_allow.argtypes = [ctypes.POINTER(FastDisU8Filter), ctypes.c_uint8]
        lib.fastdis_filter_allow.restype = None
        lib.fastdis_filter_contains.argtypes = [ctypes.POINTER(FastDisU8Filter), ctypes.c_uint8]
        lib.fastdis_filter_contains.restype = ctypes.c_int

        lib.fastdis_scan_config_filter_accept_all.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32]
        lib.fastdis_scan_config_filter_accept_all.restype = ctypes.c_int
        lib.fastdis_scan_config_filter_clear.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32]
        lib.fastdis_scan_config_filter_clear.restype = ctypes.c_int
        lib.fastdis_scan_config_filter_allow.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32, ctypes.c_uint8]
        lib.fastdis_scan_config_filter_allow.restype = ctypes.c_int
        lib.fastdis_scan_config_filter_only.argtypes = [
            ctypes.POINTER(FastDisScanConfig),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        lib.fastdis_scan_config_filter_only.restype = ctypes.c_int
        lib.fastdis_scan_config_filter_contains.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32, ctypes.c_uint8]
        lib.fastdis_scan_config_filter_contains.restype = ctypes.c_int
        lib.fastdis_scan_config_set_sample.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32, ctypes.c_uint32]
        lib.fastdis_scan_config_set_sample.restype = ctypes.c_int
        lib.fastdis_scan_config_set_entity_state_fields.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint64]
        lib.fastdis_scan_config_set_entity_state_fields.restype = ctypes.c_int
        lib.fastdis_scan_config_use_profile.argtypes = [ctypes.POINTER(FastDisScanConfig), ctypes.c_uint32]
        lib.fastdis_scan_config_use_profile.restype = ctypes.c_int

        lib.fastdis_parse_header.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisHeader),
        ]
        lib.fastdis_parse_header.restype = ctypes.c_int

        lib.fastdis_scan_packets.argtypes = [
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisScanConfig),
            PacketCallbackC,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scan_packets.restype = ctypes.c_int

        lib.fastdis_parse_entity_state_prefix.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntityStatePrefix),
        ]
        lib.fastdis_parse_entity_state_prefix.restype = ctypes.c_int

        lib.fastdis_parse_entity_state_fields.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.c_uint64,
            ctypes.POINTER(FastDisEntityStatePrefix),
        ]
        lib.fastdis_parse_entity_state_fields.restype = ctypes.c_int

        lib.fastdis_parse_entity_transform.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntityTransform),
        ]
        lib.fastdis_parse_entity_transform.restype = ctypes.c_int
        lib.fastdis_parse_fire.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisFire),
        ]
        lib.fastdis_parse_fire.restype = ctypes.c_int
        lib.fastdis_parse_detonation.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDetonation),
        ]
        lib.fastdis_parse_detonation.restype = ctypes.c_int
        lib.fastdis_parse_directed_energy_fire.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDirectedEnergyFire),
        ]
        lib.fastdis_parse_directed_energy_fire.restype = ctypes.c_int
        lib.fastdis_parse_entity_damage_status.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntityDamageStatus),
        ]
        lib.fastdis_parse_entity_damage_status.restype = ctypes.c_int
        lib.fastdis_parse_designator.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDesignator),
        ]
        lib.fastdis_parse_designator.restype = ctypes.c_int
        lib.fastdis_parse_transmitter.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisTransmitter),
        ]
        lib.fastdis_parse_transmitter.restype = ctypes.c_int
        lib.fastdis_parse_other_pdu.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisOtherPdu),
        ]
        lib.fastdis_parse_other_pdu.restype = ctypes.c_int
        lib.fastdis_parse_aggregate_state.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisAggregateState),
        ]
        lib.fastdis_parse_aggregate_state.restype = ctypes.c_int
        lib.fastdis_parse_is_group_of.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIsGroupOf),
        ]
        lib.fastdis_parse_is_group_of.restype = ctypes.c_int
        lib.fastdis_parse_transfer_control_request.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisTransferControlRequest),
        ]
        lib.fastdis_parse_transfer_control_request.restype = ctypes.c_int
        lib.fastdis_parse_transfer_ownership.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisTransferOwnership),
        ]
        lib.fastdis_parse_transfer_ownership.restype = ctypes.c_int
        lib.fastdis_parse_is_part_of.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIsPartOf),
        ]
        lib.fastdis_parse_is_part_of.restype = ctypes.c_int
        lib.fastdis_parse_minefield_state.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisMinefieldState),
        ]
        lib.fastdis_parse_minefield_state.restype = ctypes.c_int
        lib.fastdis_parse_minefield_query.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisMinefieldQuery),
        ]
        lib.fastdis_parse_minefield_query.restype = ctypes.c_int
        lib.fastdis_parse_minefield_data.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisMinefieldData),
        ]
        lib.fastdis_parse_minefield_data.restype = ctypes.c_int
        lib.fastdis_parse_minefield_response_nack.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisMinefieldResponseNack),
        ]
        lib.fastdis_parse_minefield_response_nack.restype = ctypes.c_int
        lib.fastdis_parse_environmental_process.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEnvironmentalProcess),
        ]
        lib.fastdis_parse_environmental_process.restype = ctypes.c_int
        lib.fastdis_parse_gridded_data.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisGriddedData),
        ]
        lib.fastdis_parse_gridded_data.restype = ctypes.c_int
        lib.fastdis_parse_point_object_state.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisPointObjectState),
        ]
        lib.fastdis_parse_point_object_state.restype = ctypes.c_int
        lib.fastdis_parse_linear_object_state.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisLinearObjectState),
        ]
        lib.fastdis_parse_linear_object_state.restype = ctypes.c_int
        lib.fastdis_parse_areal_object_state.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisArealObjectState),
        ]
        lib.fastdis_parse_areal_object_state.restype = ctypes.c_int
        lib.fastdis_parse_tspi.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisTspi),
        ]
        lib.fastdis_parse_tspi.restype = ctypes.c_int
        lib.fastdis_parse_live_entity_appearance.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisLiveEntityAppearance),
        ]
        lib.fastdis_parse_live_entity_appearance.restype = ctypes.c_int
        lib.fastdis_parse_articulated_parts.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisArticulatedParts),
        ]
        lib.fastdis_parse_articulated_parts.restype = ctypes.c_int
        lib.fastdis_parse_le_fire.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisLeFire),
        ]
        lib.fastdis_parse_le_fire.restype = ctypes.c_int
        lib.fastdis_parse_le_detonation.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisLeDetonation),
        ]
        lib.fastdis_parse_le_detonation.restype = ctypes.c_int
        lib.fastdis_parse_signal.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSignal),
        ]
        lib.fastdis_parse_signal.restype = ctypes.c_int
        lib.fastdis_parse_receiver.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisReceiver),
        ]
        lib.fastdis_parse_receiver.restype = ctypes.c_int
        lib.fastdis_parse_electronic_emissions.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisElectronicEmissions),
        ]
        lib.fastdis_parse_electronic_emissions.restype = ctypes.c_int
        lib.fastdis_parse_iff_atc_navaids_layer1.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIffAtcNavAidsLayer1),
        ]
        lib.fastdis_parse_iff_atc_navaids_layer1.restype = ctypes.c_int
        lib.fastdis_parse_iff.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIff),
        ]
        lib.fastdis_parse_iff.restype = ctypes.c_int
        lib.fastdis_parse_ua.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisUa),
        ]
        lib.fastdis_parse_ua.restype = ctypes.c_int
        lib.fastdis_parse_sees.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSees),
        ]
        lib.fastdis_parse_sees.restype = ctypes.c_int
        lib.fastdis_parse_intercom_signal.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIntercomSignal),
        ]
        lib.fastdis_parse_intercom_signal.restype = ctypes.c_int
        lib.fastdis_parse_intercom_control.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisIntercomControl),
        ]
        lib.fastdis_parse_intercom_control.restype = ctypes.c_int
        lib.fastdis_parse_attribute.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisAttribute),
        ]
        lib.fastdis_parse_attribute.restype = ctypes.c_int
        lib.fastdis_parse_information_operations_action.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisInformationOperationsAction),
        ]
        lib.fastdis_parse_information_operations_action.restype = ctypes.c_int
        lib.fastdis_parse_information_operations_report.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisInformationOperationsReport),
        ]
        lib.fastdis_parse_information_operations_report.restype = ctypes.c_int
        lib.fastdis_parse_service_request.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisServiceRequest),
        ]
        lib.fastdis_parse_service_request.restype = ctypes.c_int
        lib.fastdis_parse_resupply_offer.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisResupplyOffer),
        ]
        lib.fastdis_parse_resupply_offer.restype = ctypes.c_int
        lib.fastdis_parse_resupply_received.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisResupplyReceived),
        ]
        lib.fastdis_parse_resupply_received.restype = ctypes.c_int
        lib.fastdis_parse_resupply_cancel.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisResupplyCancel),
        ]
        lib.fastdis_parse_resupply_cancel.restype = ctypes.c_int
        lib.fastdis_parse_repair_complete.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisRepairComplete),
        ]
        lib.fastdis_parse_repair_complete.restype = ctypes.c_int
        lib.fastdis_parse_repair_response.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisRepairResponse),
        ]
        lib.fastdis_parse_repair_response.restype = ctypes.c_int
        lib.fastdis_parse_create_entity.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSimulationManagementRequest),
        ]
        lib.fastdis_parse_create_entity.restype = ctypes.c_int
        lib.fastdis_parse_remove_entity.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSimulationManagementRequest),
        ]
        lib.fastdis_parse_remove_entity.restype = ctypes.c_int
        lib.fastdis_parse_start_resume.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisStartResume),
        ]
        lib.fastdis_parse_start_resume.restype = ctypes.c_int
        lib.fastdis_parse_stop_freeze.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisStopFreeze),
        ]
        lib.fastdis_parse_stop_freeze.restype = ctypes.c_int
        lib.fastdis_parse_acknowledge.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisAcknowledge),
        ]
        lib.fastdis_parse_acknowledge.restype = ctypes.c_int
        lib.fastdis_parse_action_request.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisActionRequest),
        ]
        lib.fastdis_parse_action_request.restype = ctypes.c_int
        lib.fastdis_parse_action_response.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisActionResponse),
        ]
        lib.fastdis_parse_action_response.restype = ctypes.c_int
        lib.fastdis_parse_data_query.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDataQuery),
        ]
        lib.fastdis_parse_data_query.restype = ctypes.c_int
        lib.fastdis_parse_set_data.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSetData),
        ]
        lib.fastdis_parse_set_data.restype = ctypes.c_int
        lib.fastdis_parse_data.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSetData),
        ]
        lib.fastdis_parse_data.restype = ctypes.c_int
        lib.fastdis_parse_event_report.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEventReport),
        ]
        lib.fastdis_parse_event_report.restype = ctypes.c_int
        lib.fastdis_parse_comment.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisComment),
        ]
        lib.fastdis_parse_comment.restype = ctypes.c_int
        lib.fastdis_parse_create_entity_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSimulationManagementReliableRequest),
        ]
        lib.fastdis_parse_create_entity_reliable.restype = ctypes.c_int
        lib.fastdis_parse_remove_entity_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSimulationManagementReliableRequest),
        ]
        lib.fastdis_parse_remove_entity_reliable.restype = ctypes.c_int
        lib.fastdis_parse_start_resume_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisStartResumeReliable),
        ]
        lib.fastdis_parse_start_resume_reliable.restype = ctypes.c_int
        lib.fastdis_parse_stop_freeze_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisStopFreezeReliable),
        ]
        lib.fastdis_parse_stop_freeze_reliable.restype = ctypes.c_int
        lib.fastdis_parse_acknowledge_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisAcknowledge),
        ]
        lib.fastdis_parse_acknowledge_reliable.restype = ctypes.c_int
        lib.fastdis_parse_action_request_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisActionRequestReliable),
        ]
        lib.fastdis_parse_action_request_reliable.restype = ctypes.c_int
        lib.fastdis_parse_action_response_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisActionResponseReliable),
        ]
        lib.fastdis_parse_action_response_reliable.restype = ctypes.c_int
        lib.fastdis_parse_data_query_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDataQueryReliable),
        ]
        lib.fastdis_parse_data_query_reliable.restype = ctypes.c_int
        lib.fastdis_parse_set_data_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSetDataReliable),
        ]
        lib.fastdis_parse_set_data_reliable.restype = ctypes.c_int
        lib.fastdis_parse_data_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisDataReliable),
        ]
        lib.fastdis_parse_data_reliable.restype = ctypes.c_int
        lib.fastdis_parse_event_report_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEventReportReliable),
        ]
        lib.fastdis_parse_event_report_reliable.restype = ctypes.c_int
        lib.fastdis_parse_comment_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisCommentReliable),
        ]
        lib.fastdis_parse_comment_reliable.restype = ctypes.c_int
        lib.fastdis_parse_record_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisRecordReliable),
        ]
        lib.fastdis_parse_record_reliable.restype = ctypes.c_int
        lib.fastdis_parse_set_record_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisSetRecordReliable),
        ]
        lib.fastdis_parse_set_record_reliable.restype = ctypes.c_int
        lib.fastdis_parse_record_query_reliable.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisRecordQueryReliable),
        ]
        lib.fastdis_parse_record_query_reliable.restype = ctypes.c_int

        lib.fastdis_scan_entity_state_packets.argtypes = [
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisScanConfig),
            EntityStateCallbackC,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scan_entity_state_packets.restype = ctypes.c_int
        lib.fastdis_scan_entity_state_to_batch.argtypes = [
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisScanConfig),
            ctypes.POINTER(FastDisEntityStateBatch),
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scan_entity_state_to_batch.restype = ctypes.c_int
        lib.fastdis_scan_entity_transforms_to_batch.argtypes = [
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisScanConfig),
            ctypes.POINTER(FastDisEntityTransformBatch),
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scan_entity_transforms_to_batch.restype = ctypes.c_int

        lib.fastdis_scanner_create.argtypes = [ctypes.POINTER(FastDisScanConfig)]
        lib.fastdis_scanner_create.restype = ctypes.c_void_p
        lib.fastdis_scanner_destroy.argtypes = [ctypes.c_void_p]
        lib.fastdis_scanner_destroy.restype = None
        lib.fastdis_scanner_set_config.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisScanConfig)]
        lib.fastdis_scanner_set_config.restype = ctypes.c_int
        lib.fastdis_scanner_get_config.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisScanConfig)]
        lib.fastdis_scanner_get_config.restype = ctypes.c_int
        lib.fastdis_scanner_set_entity_id_filter_mode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.fastdis_scanner_set_entity_id_filter_mode.restype = ctypes.c_int
        lib.fastdis_scanner_get_entity_id_filter_mode.argtypes = [ctypes.c_void_p]
        lib.fastdis_scanner_get_entity_id_filter_mode.restype = ctypes.c_uint32
        lib.fastdis_scanner_clear_entity_ids.argtypes = [ctypes.c_void_p]
        lib.fastdis_scanner_clear_entity_ids.restype = ctypes.c_int
        lib.fastdis_scanner_add_entity_id.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16]
        lib.fastdis_scanner_add_entity_id.restype = ctypes.c_int
        lib.fastdis_scanner_add_entity_ids.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisEntityId), ctypes.c_size_t]
        lib.fastdis_scanner_add_entity_ids.restype = ctypes.c_int
        lib.fastdis_scanner_set_entity_ids.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntityId),
            ctypes.c_size_t,
        ]
        lib.fastdis_scanner_set_entity_ids.restype = ctypes.c_int
        lib.fastdis_scanner_remove_entity_id.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16]
        lib.fastdis_scanner_remove_entity_id.restype = ctypes.c_int
        lib.fastdis_scanner_contains_entity_id.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16]
        lib.fastdis_scanner_contains_entity_id.restype = ctypes.c_int
        lib.fastdis_scanner_entity_id_count.argtypes = [ctypes.c_void_p]
        lib.fastdis_scanner_entity_id_count.restype = ctypes.c_size_t
        lib.fastdis_scanner_filter_accept_all.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.fastdis_scanner_filter_accept_all.restype = ctypes.c_int
        lib.fastdis_scanner_filter_clear.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.fastdis_scanner_filter_clear.restype = ctypes.c_int
        lib.fastdis_scanner_filter_allow.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8]
        lib.fastdis_scanner_filter_allow.restype = ctypes.c_int
        lib.fastdis_scanner_filter_only.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        lib.fastdis_scanner_filter_only.restype = ctypes.c_int
        lib.fastdis_scanner_filter_contains.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8]
        lib.fastdis_scanner_filter_contains.restype = ctypes.c_int
        lib.fastdis_scanner_set_sample.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
        lib.fastdis_scanner_set_sample.restype = ctypes.c_int
        lib.fastdis_scanner_set_entity_state_fields.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        lib.fastdis_scanner_set_entity_state_fields.restype = ctypes.c_int
        lib.fastdis_scanner_use_profile.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.fastdis_scanner_use_profile.restype = ctypes.c_int
        lib.fastdis_scanner_scan_packets.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            PacketCallbackC,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scanner_scan_packets.restype = ctypes.c_int
        lib.fastdis_scanner_scan_entity_state_packets.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            EntityStateCallbackC,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scanner_scan_entity_state_packets.restype = ctypes.c_int
        lib.fastdis_scanner_scan_entity_state_to_batch.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisEntityStateBatch),
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scanner_scan_entity_state_to_batch.restype = ctypes.c_int
        lib.fastdis_scanner_scan_entity_transforms_to_batch.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.POINTER(FastDisEntityTransformBatch),
            ctypes.POINTER(FastDisScanStats),
        ]
        lib.fastdis_scanner_scan_entity_transforms_to_batch.restype = ctypes.c_int

        lib.fastdis_entity_table_create.argtypes = [ctypes.c_size_t]
        lib.fastdis_entity_table_create.restype = ctypes.c_void_p
        lib.fastdis_entity_table_destroy.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_table_destroy.restype = None
        lib.fastdis_entity_table_clear.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_table_clear.restype = ctypes.c_int
        lib.fastdis_entity_table_size.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_table_size.restype = ctypes.c_size_t
        lib.fastdis_entity_table_tick.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_table_tick.restype = ctypes.c_uint64
        lib.fastdis_entity_table_advance_tick.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        lib.fastdis_entity_table_advance_tick.restype = ctypes.c_int
        lib.fastdis_entity_table_mark_all_clean.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_table_mark_all_clean.restype = ctypes.c_int
        lib.fastdis_entity_table_update_transform.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisEntityTransform),
            ctypes.POINTER(FastDisEntitySnapshot),
        ]
        lib.fastdis_entity_table_update_transform.restype = ctypes.c_int
        lib.fastdis_entity_table_ingest_packets.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntityTableUpdateStats),
        ]
        lib.fastdis_entity_table_ingest_packets.restype = ctypes.c_int
        lib.fastdis_entity_table_get.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.POINTER(FastDisEntitySnapshot),
        ]
        lib.fastdis_entity_table_get.restype = ctypes.c_int
        lib.fastdis_entity_table_snapshot_all.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisEntitySnapshotBatch)]
        lib.fastdis_entity_table_snapshot_all.restype = ctypes.c_int
        lib.fastdis_entity_table_snapshot_changed.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisEntitySnapshotBatch),
            ctypes.c_uint32,
        ]
        lib.fastdis_entity_table_snapshot_changed.restype = ctypes.c_int
        lib.fastdis_entity_table_snapshot_stale.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(FastDisEntitySnapshotBatch),
        ]
        lib.fastdis_entity_table_snapshot_stale.restype = ctypes.c_int
        lib.fastdis_entity_table_evict_stale.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(FastDisEntitySnapshotBatch),
        ]
        lib.fastdis_entity_table_evict_stale.restype = ctypes.c_int
        lib.fastdis_extrapolate_entity_transform_linear.argtypes = [
            ctypes.POINTER(FastDisEntityTransform),
            ctypes.c_double,
            ctypes.POINTER(FastDisEntityTransform),
        ]
        lib.fastdis_extrapolate_entity_transform_linear.restype = ctypes.c_int
        lib.fastdis_extrapolate_entity_snapshot_linear.argtypes = [
            ctypes.POINTER(FastDisEntitySnapshot),
            ctypes.c_uint64,
            ctypes.c_double,
            ctypes.POINTER(FastDisEntitySnapshot),
        ]
        lib.fastdis_extrapolate_entity_snapshot_linear.restype = ctypes.c_int
        lib.fastdis_dead_reckoning_algorithm_name.argtypes = [ctypes.c_uint8]
        lib.fastdis_dead_reckoning_algorithm_name.restype = ctypes.c_char_p
        lib.fastdis_dead_reckoning_algorithm_known.argtypes = [ctypes.c_uint8]
        lib.fastdis_dead_reckoning_algorithm_known.restype = ctypes.c_int
        lib.fastdis_extrapolate_entity_transform_dead_reckoning.argtypes = [
            ctypes.POINTER(FastDisEntityTransform),
            ctypes.c_double,
            ctypes.POINTER(FastDisEntityTransform),
        ]
        lib.fastdis_extrapolate_entity_transform_dead_reckoning.restype = ctypes.c_int
        lib.fastdis_extrapolate_entity_snapshot_dead_reckoning.argtypes = [
            ctypes.POINTER(FastDisEntitySnapshot),
            ctypes.c_uint64,
            ctypes.c_double,
            ctypes.POINTER(FastDisEntitySnapshot),
        ]
        lib.fastdis_extrapolate_entity_snapshot_dead_reckoning.restype = ctypes.c_int

        lib.fastdis_entity_snapshot_buffer_create.argtypes = [ctypes.c_size_t]
        lib.fastdis_entity_snapshot_buffer_create.restype = ctypes.c_void_p
        lib.fastdis_entity_snapshot_buffer_create_ex.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        lib.fastdis_entity_snapshot_buffer_create_ex.restype = ctypes.c_void_p
        lib.fastdis_entity_snapshot_buffer_destroy.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_snapshot_buffer_destroy.restype = None
        lib.fastdis_entity_snapshot_buffer_resize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        lib.fastdis_entity_snapshot_buffer_resize.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_capacity.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_snapshot_buffer_capacity.restype = ctypes.c_size_t
        lib.fastdis_entity_snapshot_buffer_slot_count.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_snapshot_buffer_slot_count.restype = ctypes.c_size_t
        lib.fastdis_entity_snapshot_buffer_generation.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_snapshot_buffer_generation.restype = ctypes.c_uint64
        lib.fastdis_entity_snapshot_buffer_get_stats.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(FastDisSnapshotBufferStats),
        ]
        lib.fastdis_entity_snapshot_buffer_get_stats.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_reset_stats.argtypes = [ctypes.c_void_p]
        lib.fastdis_entity_snapshot_buffer_reset_stats.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_publish_all.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisEntitySnapshotView),
        ]
        lib.fastdis_entity_snapshot_buffer_publish_all.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_publish_changed.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(FastDisEntitySnapshotView),
        ]
        lib.fastdis_entity_snapshot_buffer_publish_changed.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_publish_stale.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(FastDisEntitySnapshotView),
        ]
        lib.fastdis_entity_snapshot_buffer_publish_stale.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_publish_evict_stale.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(FastDisEntitySnapshotView),
        ]
        lib.fastdis_entity_snapshot_buffer_publish_evict_stale.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_acquire_latest.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisEntitySnapshotView)]
        lib.fastdis_entity_snapshot_buffer_acquire_latest.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_release.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisEntitySnapshotView)]
        lib.fastdis_entity_snapshot_buffer_release.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_copy_latest.argtypes = [ctypes.c_void_p, ctypes.POINTER(FastDisEntitySnapshotBatch)]
        lib.fastdis_entity_snapshot_buffer_copy_latest.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_copy_latest_extrapolated.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_double,
            ctypes.POINTER(FastDisEntitySnapshotBatch),
        ]
        lib.fastdis_entity_snapshot_buffer_copy_latest_extrapolated.restype = ctypes.c_int
        lib.fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_double,
            ctypes.POINTER(FastDisEntitySnapshotBatch),
        ]
        lib.fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned.restype = ctypes.c_int
        lib.fastdis_entity_table_ingest_packets_publish_changed.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisPacketView),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.POINTER(FastDisEntityTableUpdateStats),
            ctypes.POINTER(FastDisEntitySnapshotView),
        ]
        lib.fastdis_entity_table_ingest_packets_publish_changed.restype = ctypes.c_int

    def abi_version(self) -> int:
        return int(self.lib.fastdis_abi_version())

    def abi_epoch(self) -> int:
        return int(self.lib.fastdis_abi_epoch())

    def abi_revision(self) -> int:
        return int(self.lib.fastdis_abi_revision())

    def version_string(self) -> str:
        return self.lib.fastdis_version_string().decode("utf-8")

    def status_string(self, status: int) -> str:
        return self.lib.fastdis_status_string(int(status)).decode("utf-8")

    def dead_reckoning_algorithm_name(self, algorithm: int) -> str:
        return self.lib.fastdis_dead_reckoning_algorithm_name(ctypes.c_uint8(int(algorithm))).decode("utf-8")

    def dead_reckoning_algorithm_known(self, algorithm: int) -> bool:
        return bool(self.lib.fastdis_dead_reckoning_algorithm_known(ctypes.c_uint8(int(algorithm))))

    def extrapolate_transform_linear(self, transform: EntityTransform, delta_seconds: float) -> EntityTransform:
        raw = _raw_transform_from_value(transform)
        out = FastDisEntityTransform()
        self.check(
            self.lib.fastdis_extrapolate_entity_transform_linear(
                ctypes.byref(raw),
                ctypes.c_double(float(delta_seconds)),
                ctypes.byref(out),
            )
        )
        return out.as_value()

    def extrapolate_transform_dead_reckoning(self, transform: EntityTransform, delta_seconds: float) -> EntityTransform:
        raw = _raw_transform_from_value(transform)
        out = FastDisEntityTransform()
        self.check(
            self.lib.fastdis_extrapolate_entity_transform_dead_reckoning(
                ctypes.byref(raw),
                ctypes.c_double(float(delta_seconds)),
                ctypes.byref(out),
            )
        )
        return out.as_value()

    def extrapolate_snapshot_linear(
        self,
        snapshot: EntitySnapshot,
        *,
        target_tick: int,
        seconds_per_tick: float,
    ) -> EntitySnapshot:
        raw = _raw_snapshot_from_value(snapshot)
        out = FastDisEntitySnapshot()
        self.check(
            self.lib.fastdis_extrapolate_entity_snapshot_linear(
                ctypes.byref(raw),
                ctypes.c_uint64(int(target_tick)),
                ctypes.c_double(float(seconds_per_tick)),
                ctypes.byref(out),
            )
        )
        return out.as_value()

    def extrapolate_snapshot_dead_reckoning(
        self,
        snapshot: EntitySnapshot,
        *,
        target_tick: int,
        seconds_per_tick: float,
    ) -> EntitySnapshot:
        raw = _raw_snapshot_from_value(snapshot)
        out = FastDisEntitySnapshot()
        self.check(
            self.lib.fastdis_extrapolate_entity_snapshot_dead_reckoning(
                ctypes.byref(raw),
                ctypes.c_uint64(int(target_tick)),
                ctypes.c_double(float(seconds_per_tick)),
                ctypes.byref(out),
            )
        )
        return out.as_value()

    def check(self, status: int) -> None:
        if status != FASTDIS_OK:
            raise FastDisError(self.status_string(status))

    def new_config(
        self,
        *,
        versions: None | int | Iterable[int] = None,
        pdu_types: None | int | Iterable[int] = None,
        families: None | int | Iterable[int] = None,
        exercise_ids: None | int | Iterable[int] = None,
        entity_force_ids: None | int | Iterable[int] = None,
        entity_state_fields: int = FASTDIS_ES_FIELD_ALL,
        sample_every: int = 1,
        sample_offset: int = 0,
        flags: int = 0,
    ) -> FastDisScanConfig:
        if sample_every < 1:
            raise ValueError("sample_every must be >= 1")
        config = FastDisScanConfig()
        self.lib.fastdis_scan_config_init(ctypes.byref(config))
        config.flags = int(flags)
        self.check(self.lib.fastdis_scan_config_set_sample(ctypes.byref(config), int(sample_every), int(sample_offset)))
        self.check(self.lib.fastdis_scan_config_set_entity_state_fields(ctypes.byref(config), int(entity_state_fields)))
        self.set_config_filter(config, FASTDIS_FILTER_VERSION, versions)
        self.set_config_filter(config, FASTDIS_FILTER_PDU_TYPE, pdu_types)
        self.set_config_filter(config, FASTDIS_FILTER_PROTOCOL_FAMILY, families)
        self.set_config_filter(config, FASTDIS_FILTER_EXERCISE_ID, exercise_ids)
        self.set_config_filter(config, FASTDIS_FILTER_ENTITY_FORCE_ID, entity_force_ids)
        return config

    def _filter_ptr(self, config: FastDisScanConfig, field_name: str):
        descriptor = getattr(FastDisScanConfig, field_name)
        return ctypes.cast(ctypes.byref(config, descriptor.offset), ctypes.POINTER(FastDisU8Filter))

    def _filter_only_ptr(self, filter_ptr, values: None | int | Iterable[int]) -> None:
        vals = _filter_values(values)
        if not vals:
            self.lib.fastdis_filter_accept_all(filter_ptr)
            return
        self.lib.fastdis_filter_clear(filter_ptr)
        for value in vals:
            self.lib.fastdis_filter_allow(filter_ptr, int(value))

    def filter_only(self, filter_obj: FastDisU8Filter, values: None | int | Iterable[int]) -> None:
        vals = _filter_values(values)
        ptr = ctypes.pointer(filter_obj)
        if not vals:
            self.lib.fastdis_filter_accept_all(ptr)
            return
        self.lib.fastdis_filter_clear(ptr)
        for value in vals:
            self.lib.fastdis_filter_allow(ptr, int(value))

    def set_config_filter(
        self,
        config: FastDisScanConfig,
        kind: int | str,
        values: None | int | Iterable[int],
    ) -> FastDisScanConfig:
        """Set a config filter by generic ABI kind/name and return ``config``.

        ``None`` means accept all; any integer or iterable means clear the slot
        and allow only those values. Useful for engine-style code that should not
        depend on the internal config struct layout.
        """

        filter_kind = _filter_kind(kind)
        vals = _filter_values(values)
        if vals:
            array_type = ctypes.c_uint8 * len(vals)
            array = array_type(*vals)
            self.check(
                self.lib.fastdis_scan_config_filter_only(
                    ctypes.byref(config),
                    filter_kind,
                    array,
                    len(vals),
                )
            )
        else:
            self.check(self.lib.fastdis_scan_config_filter_only(ctypes.byref(config), filter_kind, None, 0))
        return config

    def config_filter_contains(self, config: FastDisScanConfig, kind: int | str, value: int) -> bool:
        """Return whether a value passes a config filter slot."""

        return bool(self.lib.fastdis_scan_config_filter_contains(ctypes.byref(config), _filter_kind(kind), int(value)))

    def set_config_sample(self, config: FastDisScanConfig, sample_every: int = 1, sample_offset: int = 0) -> FastDisScanConfig:
        """Set native downsampling on a config and return ``config``."""

        if sample_every < 1:
            raise ValueError("sample_every must be >= 1")
        self.check(self.lib.fastdis_scan_config_set_sample(ctypes.byref(config), int(sample_every), int(sample_offset)))
        return config

    def set_config_entity_state_fields(self, config: FastDisScanConfig, fields: int | str | Iterable[int | str]) -> FastDisScanConfig:
        """Set Entity State field subscriptions on a config and return ``config``."""

        if isinstance(fields, (int, str)):
            mask = entity_state_field_mask(fields)
        else:
            mask = entity_state_field_mask(fields)
        self.check(self.lib.fastdis_scan_config_set_entity_state_fields(ctypes.byref(config), mask))
        return config

    def use_config_profile(self, config: FastDisScanConfig, profile: int | str) -> FastDisScanConfig:
        """Apply a native scanner/config profile and return ``config``."""

        self.check(self.lib.fastdis_scan_config_use_profile(ctypes.byref(config), _profile_kind(profile)))
        return config

    def parse_header_tuple(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> HeaderTuple:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        header = FastDisHeader()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_header(ptr, n, combined_flags, ctypes.byref(header))
        self.check(rc)
        return header.as_tuple()

    def parse_entity_state_prefix(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EntityStatePrefix:
        return self.parse_entity_state_fields(
            data,
            fields=FASTDIS_ES_FIELD_ALL,
            flags=flags,
            allow_truncated=allow_truncated,
        )

    def parse_entity_state_fields(
        self,
        data: bytes | bytearray | memoryview,
        *,
        fields: int,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EntityStatePrefix:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEntityStatePrefix()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_entity_state_fields(ptr, n, combined_flags, int(fields), ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_entity_transform(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EntityTransform:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEntityTransform()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_entity_transform(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_fire(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Fire:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisFire()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_fire(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_detonation(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Detonation:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDetonation()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_detonation(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_directed_energy_fire(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> DirectedEnergyFire:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDirectedEnergyFire()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_directed_energy_fire(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_entity_damage_status(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EntityDamageStatus:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEntityDamageStatus()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_entity_damage_status(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_designator(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Designator:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDesignator()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_designator(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_transmitter(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Transmitter:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisTransmitter()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_transmitter(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_other_pdu(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> OtherPdu:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisOtherPdu()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_other_pdu(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_aggregate_state(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> AggregateState:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisAggregateState()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_aggregate_state(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_is_group_of(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> IsGroupOf:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIsGroupOf()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_is_group_of(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_transfer_control_request(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> TransferControlRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisTransferControlRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_transfer_control_request(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_transfer_ownership(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> TransferOwnership:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisTransferOwnership()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_transfer_ownership(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_is_part_of(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> IsPartOf:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIsPartOf()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_is_part_of(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_minefield_state(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> MinefieldState:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisMinefieldState()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_minefield_state(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_minefield_query(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> MinefieldQuery:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisMinefieldQuery()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_minefield_query(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_minefield_data(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> MinefieldData:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisMinefieldData()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_minefield_data(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_minefield_response_nack(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> MinefieldResponseNack:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisMinefieldResponseNack()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_minefield_response_nack(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_environmental_process(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EnvironmentalProcess:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEnvironmentalProcess()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_environmental_process(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_gridded_data(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> GriddedData:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisGriddedData()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_gridded_data(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_point_object_state(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> PointObjectState:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisPointObjectState()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_point_object_state(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_linear_object_state(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> LinearObjectState:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisLinearObjectState()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_linear_object_state(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_areal_object_state(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ArealObjectState:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisArealObjectState()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_areal_object_state(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_tspi(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Tspi:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisTspi()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_tspi(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_live_entity_appearance(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> LiveEntityAppearance:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisLiveEntityAppearance()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_live_entity_appearance(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_articulated_parts(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ArticulatedParts:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisArticulatedParts()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_articulated_parts(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_le_fire(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> LeFire:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisLeFire()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_le_fire(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_le_detonation(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> LeDetonation:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisLeDetonation()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_le_detonation(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_signal(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Signal:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSignal()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_signal(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_receiver(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Receiver:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisReceiver()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_receiver(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_electronic_emissions(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ElectronicEmissions:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisElectronicEmissions()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_electronic_emissions(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_iff_atc_navaids_layer1(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> IffAtcNavAidsLayer1:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIffAtcNavAidsLayer1()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_iff_atc_navaids_layer1(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_iff(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Iff:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIff()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_iff(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_ua(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Ua:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisUa()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_ua(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_sees(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Sees:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSees()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_sees(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_intercom_signal(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> IntercomSignal:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIntercomSignal()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_intercom_signal(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_intercom_control(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> IntercomControl:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisIntercomControl()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_intercom_control(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_attribute(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Attribute:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisAttribute()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_attribute(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_information_operations_action(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> InformationOperationsAction:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisInformationOperationsAction()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_information_operations_action(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_information_operations_report(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> InformationOperationsReport:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisInformationOperationsReport()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_information_operations_report(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_service_request(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ServiceRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisServiceRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_service_request(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_resupply_offer(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ResupplyOffer:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisResupplyOffer()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_resupply_offer(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_resupply_received(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ResupplyReceived:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisResupplyReceived()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_resupply_received(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_resupply_cancel(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ResupplyCancel:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisResupplyCancel()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_resupply_cancel(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_repair_complete(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> RepairComplete:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisRepairComplete()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_repair_complete(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_repair_response(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> RepairResponse:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisRepairResponse()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_repair_response(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_create_entity(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SimulationManagementRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSimulationManagementRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_create_entity(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_remove_entity(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SimulationManagementRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSimulationManagementRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_remove_entity(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_start_resume(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> StartResume:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisStartResume()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_start_resume(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_stop_freeze(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> StopFreeze:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisStopFreeze()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_stop_freeze(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_acknowledge(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Acknowledge:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisAcknowledge()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_acknowledge(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_action_request(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ActionRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisActionRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_action_request(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_action_response(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ActionResponse:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisActionResponse()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_action_response(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_data_query(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> DataQuery:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDataQuery()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_data_query(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_set_data(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SetData:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSetData()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_set_data(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_data(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SetData:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSetData()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_data(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_event_report(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EventReport:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEventReport()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_event_report(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_comment(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Comment:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisComment()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_comment(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_create_entity_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SimulationManagementReliableRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSimulationManagementReliableRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_create_entity_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_remove_entity_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SimulationManagementReliableRequest:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSimulationManagementReliableRequest()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_remove_entity_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_start_resume_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> StartResumeReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisStartResumeReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_start_resume_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_stop_freeze_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> StopFreezeReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisStopFreezeReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_stop_freeze_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_acknowledge_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> Acknowledge:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisAcknowledge()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_acknowledge_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_action_request_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ActionRequestReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisActionRequestReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_action_request_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_action_response_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> ActionResponseReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisActionResponseReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_action_response_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_data_query_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> DataQueryReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDataQueryReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_data_query_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_set_data_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SetDataReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSetDataReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_set_data_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_data_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> DataReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisDataReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_data_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_event_report_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> EventReportReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisEventReportReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_event_report_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_comment_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> CommentReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisCommentReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_comment_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_record_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> RecordReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisRecordReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_record_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_set_record_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> SetRecordReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisSetRecordReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_set_record_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def parse_record_query_reliable(
        self,
        data: bytes | bytearray | memoryview,
        *,
        flags: int = 0,
        allow_truncated: bool = False,
    ) -> RecordQueryReliable:
        keepalive, ptr, n = _buffer_ptr(data)
        _ = keepalive
        out = FastDisRecordQueryReliable()
        combined_flags = int(flags) | (FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0)
        rc = self.lib.fastdis_parse_record_query_reliable(ptr, n, combined_flags, ctypes.byref(out))
        self.check(rc)
        return out.as_value()

    def _packet_views(self, packets: Iterable[bytes | bytearray | memoryview]):
        keepalives: list[object] = []
        index_handles: list[ctypes.c_size_t] = []
        original_packets: list[object] = []
        views_list: list[FastDisPacketView] = []

        for packet in packets:
            keepalive, ptr, n = _buffer_ptr(packet)
            index = len(original_packets)
            index_handle = ctypes.c_size_t(index)
            views_list.append(
                FastDisPacketView(
                    ptr,
                    n,
                    ctypes.cast(ctypes.pointer(index_handle), ctypes.c_void_p),
                )
            )
            keepalives.append(keepalive)
            index_handles.append(index_handle)
            original_packets.append(packet)

        views = (FastDisPacketView * len(views_list))(*views_list) if views_list else None
        return keepalives, index_handles, original_packets, views, len(views_list)

    def scan_packets(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        callback=None,
        *,
        config: FastDisScanConfig | None = None,
    ) -> FastDisScanStats:
        """Scan packet views using an explicit native config.

        This is closer to the C ABI than :meth:`scan_many`. The callback, when
        supplied, receives ``(header_tuple, original_packet)``.
        """
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")

        keepalives, index_handles, original_packets, views, count = self._packet_views(packets)
        _ = (keepalives, index_handles)
        cfg = config if config is not None else self.new_config()
        stats = FastDisScanStats()
        self.lib.fastdis_scan_stats_init(ctypes.byref(stats))

        if callback is None:
            cb = PacketCallbackC(0)
        else:
            def _cb(header_ptr, data_ptr, size, packet_user, callback_user):  # type: ignore[no-untyped-def]
                del data_ptr, size, callback_user
                original = None
                if packet_user:
                    index = ctypes.cast(packet_user, ctypes.POINTER(ctypes.c_size_t)).contents.value
                    original = original_packets[index]
                try:
                    callback(header_ptr.contents.as_tuple(), original)
                except Exception:
                    return 1
                return 0

            cb = PacketCallbackC(_cb)

        rc = self.lib.fastdis_scan_packets(
            views,
            count,
            ctypes.byref(cfg),
            cb,
            None,
            ctypes.byref(stats),
        )
        self.check(rc)
        return stats

    def scan_many(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        callback: PacketCallback | None = None,
        *,
        pdu_types: None | int | Iterable[int] = None,
        versions: None | int | Iterable[int] = None,
        families: None | int | Iterable[int] = None,
        exercise_ids: None | int | Iterable[int] = None,
        sample_every: int = 1,
        sample_offset: int = 0,
        allow_truncated: bool = False,
        return_stats: bool = False,
    ) -> tuple[int, int, int] | dict[str, int]:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")

        keepalives, index_handles, original_packets, views, count = self._packet_views(packets)
        _ = (keepalives, index_handles)  # keep data and packet_user pointers alive
        flags = FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0
        config = self.new_config(
            versions=versions,
            pdu_types=pdu_types,
            families=families,
            exercise_ids=exercise_ids,
            sample_every=sample_every,
            sample_offset=sample_offset,
            flags=flags,
        )
        stats = FastDisScanStats()
        self.lib.fastdis_scan_stats_init(ctypes.byref(stats))

        if callback is None:
            cb = PacketCallbackC(0)
        else:
            def _cb(header_ptr, data_ptr, size, packet_user, callback_user):  # type: ignore[no-untyped-def]
                del data_ptr, size, callback_user
                header = header_ptr.contents
                original = None
                if packet_user:
                    index = ctypes.cast(packet_user, ctypes.POINTER(ctypes.c_size_t)).contents.value
                    original = original_packets[index]
                try:
                    callback(
                        int(header.version),
                        int(header.exercise_id),
                        int(header.pdu_type),
                        int(header.protocol_family),
                        int(header.timestamp),
                        int(header.length),
                        int(header.status),
                        original,
                    )
                except Exception:
                    return 1
                return 0

            cb = PacketCallbackC(_cb)

        rc = self.lib.fastdis_scan_packets(
            views,
            count,
            ctypes.byref(config),
            cb,
            None,
            ctypes.byref(stats),
        )
        self.check(rc)
        return stats.as_dict() if return_stats else stats.as_tuple()

    def scan_entity_state_many(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        callback: EntityStateCallback | None = None,
        *,
        versions: None | int | Iterable[int] = None,
        exercise_ids: None | int | Iterable[int] = None,
        entity_force_ids: None | int | Iterable[int] = None,
        entity_state_fields: int = FASTDIS_ES_FIELD_ALL,
        sample_every: int = 1,
        sample_offset: int = 0,
        allow_truncated: bool = False,
        return_stats: bool = False,
    ) -> tuple[int, int, int] | dict[str, int]:
        """Scan only Entity State PDUs and callback with subscribed fields.

        The C layer enforces protocol family 1 and PDU type 1, decodes only the
        requested fields, filters by force ID if requested, then invokes Python
        only for retained packets.
        """
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")

        keepalives, index_handles, original_packets, views, count = self._packet_views(packets)
        _ = (keepalives, index_handles)
        flags = FASTDIS_FLAG_ALLOW_TRUNCATED if allow_truncated else 0
        config = self.new_config(
            versions=versions,
            pdu_types=None,
            families=None,
            exercise_ids=exercise_ids,
            entity_force_ids=entity_force_ids,
            entity_state_fields=entity_state_fields,
            sample_every=sample_every,
            sample_offset=sample_offset,
            flags=flags,
        )
        stats = FastDisScanStats()
        self.lib.fastdis_scan_stats_init(ctypes.byref(stats))

        if callback is None:
            cb = EntityStateCallbackC(0)
        else:
            def _cb(entity_ptr, data_ptr, size, packet_user, callback_user):  # type: ignore[no-untyped-def]
                del data_ptr, size, callback_user
                original = None
                if packet_user:
                    index = ctypes.cast(packet_user, ctypes.POINTER(ctypes.c_size_t)).contents.value
                    original = original_packets[index]
                try:
                    callback(entity_ptr.contents.as_value(), original)
                except Exception:
                    return 1
                return 0

            cb = EntityStateCallbackC(_cb)

        rc = self.lib.fastdis_scan_entity_state_packets(
            views,
            count,
            ctypes.byref(config),
            cb,
            None,
            ctypes.byref(stats),
        )
        self.check(rc)
        return stats.as_dict() if return_stats else stats.as_tuple()

    def scan_entity_state_to_batch(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        config: FastDisScanConfig | None = None,
        capacity: int | None = None,
        return_stats: bool = False,
    ):
        """Scan Entity State PDUs into a caller-owned native array, no callbacks."""

        keepalives, index_handles, _original_packets, views, count = self._packet_views(packets)
        _ = (keepalives, index_handles)
        cap = count if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntityStatePrefix * cap
        storage = array_type()
        batch = FastDisEntityStateBatch(storage, cap, 0, 0)
        cfg = config if config is not None else self.new_config(entity_state_fields=FASTDIS_ES_FIELD_POSE)
        stats = FastDisScanStats()
        self.lib.fastdis_scan_stats_init(ctypes.byref(stats))
        rc = self.lib.fastdis_scan_entity_state_to_batch(
            views,
            count,
            ctypes.byref(cfg),
            ctypes.byref(batch),
            ctypes.byref(stats),
        )
        self.check(rc)
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_stats:
            meta = stats.as_dict()
            meta.update({"stored": int(batch.count), "dropped": int(batch.dropped), "capacity": int(batch.capacity)})
            return records, meta
        return records

    def scan_entity_transforms_to_batch(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        config: FastDisScanConfig | None = None,
        capacity: int | None = None,
        return_stats: bool = False,
    ):
        """Scan Entity State PDUs into compact engine-shaped transform records."""

        keepalives, index_handles, _original_packets, views, count = self._packet_views(packets)
        _ = (keepalives, index_handles)
        cap = count if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntityTransform * cap
        storage = array_type()
        batch = FastDisEntityTransformBatch(storage, cap, 0, 0)
        if config is None:
            cfg = self.new_config()
            self.use_config_profile(cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM)
        else:
            cfg = config
        stats = FastDisScanStats()
        self.lib.fastdis_scan_stats_init(ctypes.byref(stats))
        rc = self.lib.fastdis_scan_entity_transforms_to_batch(
            views,
            count,
            ctypes.byref(cfg),
            ctypes.byref(batch),
            ctypes.byref(stats),
        )
        self.check(rc)
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_stats:
            meta = stats.as_dict()
            meta.update({"stored": int(batch.count), "dropped": int(batch.dropped), "capacity": int(batch.capacity)})
            return records, meta
        return records

    def create_scanner(self, config: FastDisScanConfig | None = None, **config_kwargs) -> "FastDisScanner":
        """Create an opaque reusable native scanner context."""

        cfg = config if config is not None else self.new_config(**config_kwargs)
        ptr = self.lib.fastdis_scanner_create(ctypes.byref(cfg))
        if not ptr:
            raise FastDisError("could not create fastdis scanner")
        return FastDisScanner(self, ptr)

    def create_entity_table(self, reserve: int = 0) -> "FastDisEntityTable":
        """Create an opaque native latest-state/entity table."""

        if reserve < 0:
            raise ValueError("reserve must be >= 0")
        ptr = self.lib.fastdis_entity_table_create(int(reserve))
        if not ptr:
            raise FastDisError("could not create fastdis entity table")
        return FastDisEntityTable(self, ptr)

    def create_snapshot_buffer(self, capacity: int, *, slots: int = 2) -> "FastDisSnapshotBuffer":
        """Create a native snapshot handoff buffer.

        ``slots=2`` preserves strict double-buffer behavior. ``slots=3`` is the
        safer engine default when render/update timing may pin two reads.
        """

        if capacity < 0:
            raise ValueError("capacity must be >= 0")
        if slots < 2:
            raise ValueError("slots must be >= 2")
        ptr = self.lib.fastdis_entity_snapshot_buffer_create_ex(int(capacity), int(slots))
        if not ptr:
            raise FastDisError("could not create fastdis snapshot buffer")
        return FastDisSnapshotBuffer(self, ptr)


class FastDisScanner:
    """Opaque scanner handle for configure-once, scan-many engine loops."""

    def __init__(self, native: NativeFastDis, ptr: int):
        self._native = native
        self._ptr = ctypes.c_void_p(ptr)
        self._closed = False

    def close(self) -> None:
        if not self._closed and self._ptr.value:
            self._native.lib.fastdis_scanner_destroy(self._ptr)
            self._closed = True
            self._ptr = ctypes.c_void_p()

    def __enter__(self) -> "FastDisScanner":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        del exc_type, exc, tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @property
    def ptr(self) -> ctypes.c_void_p:
        if self._closed or not self._ptr.value:
            raise FastDisError("fastdis scanner is closed")
        return self._ptr

    def set_config(self, config: FastDisScanConfig) -> None:
        self._native.check(self._native.lib.fastdis_scanner_set_config(self.ptr, ctypes.byref(config)))

    def get_config(self) -> FastDisScanConfig:
        config = FastDisScanConfig()
        self._native.check(self._native.lib.fastdis_scanner_get_config(self.ptr, ctypes.byref(config)))
        return config

    def set_entity_id_filter_mode(self, mode: int) -> "FastDisScanner":
        self._native.check(self._native.lib.fastdis_scanner_set_entity_id_filter_mode(self.ptr, int(mode)))
        return self

    def get_entity_id_filter_mode(self) -> int:
        return int(self._native.lib.fastdis_scanner_get_entity_id_filter_mode(self.ptr))

    def clear_entity_ids(self) -> "FastDisScanner":
        self._native.check(self._native.lib.fastdis_scanner_clear_entity_ids(self.ptr))
        return self

    def add_entity_id(self, site: int, application: int, entity: int) -> "FastDisScanner":
        self._native.check(
            self._native.lib.fastdis_scanner_add_entity_id(self.ptr, int(site), int(application), int(entity))
        )
        return self

    def add_entity_ids(self, ids: Iterable[EntityIdTuple] | EntityIdTuple) -> "FastDisScanner":
        entity_ids, array = _entity_id_array(ids)
        self._native.check(self._native.lib.fastdis_scanner_add_entity_ids(self.ptr, array, len(entity_ids)))
        return self

    def set_entity_ids(self, mode: int, ids: Iterable[EntityIdTuple] | EntityIdTuple) -> "FastDisScanner":
        entity_ids, array = _entity_id_array(ids)
        self._native.check(self._native.lib.fastdis_scanner_set_entity_ids(self.ptr, int(mode), array, len(entity_ids)))
        return self

    def remove_entity_id(self, site: int, application: int, entity: int) -> "FastDisScanner":
        self._native.check(
            self._native.lib.fastdis_scanner_remove_entity_id(self.ptr, int(site), int(application), int(entity))
        )
        return self

    def contains_entity_id(self, site: int, application: int, entity: int) -> bool:
        return bool(self._native.lib.fastdis_scanner_contains_entity_id(self.ptr, int(site), int(application), int(entity)))

    def entity_id_count(self) -> int:
        return int(self._native.lib.fastdis_scanner_entity_id_count(self.ptr))

    def set_filter(
        self,
        kind: int | str,
        values: None | int | Iterable[int],
    ) -> "FastDisScanner":
        """Set one native filter slot and return ``self`` for chaining.

        Examples:
            scanner.set_filter("versions", [6, 7]).set_filter("pdu_types", 1)
            scanner.set_filter("entity_force_ids", [1, 2])
        """

        filter_kind = _filter_kind(kind)
        vals = _filter_values(values)
        if vals:
            array_type = ctypes.c_uint8 * len(vals)
            array = array_type(*vals)
            self._native.check(self._native.lib.fastdis_scanner_filter_only(self.ptr, filter_kind, array, len(vals)))
        else:
            self._native.check(self._native.lib.fastdis_scanner_filter_only(self.ptr, filter_kind, None, 0))
        return self

    def filter_contains(self, kind: int | str, value: int) -> bool:
        return bool(self._native.lib.fastdis_scanner_filter_contains(self.ptr, _filter_kind(kind), int(value)))

    def only_versions(self, values: None | int | Iterable[int]) -> "FastDisScanner":
        return self.set_filter(FASTDIS_FILTER_VERSION, values)

    def only_pdu_types(self, values: None | int | Iterable[int]) -> "FastDisScanner":
        return self.set_filter(FASTDIS_FILTER_PDU_TYPE, values)

    def only_protocol_families(self, values: None | int | Iterable[int]) -> "FastDisScanner":
        return self.set_filter(FASTDIS_FILTER_PROTOCOL_FAMILY, values)

    def only_exercise_ids(self, values: None | int | Iterable[int]) -> "FastDisScanner":
        return self.set_filter(FASTDIS_FILTER_EXERCISE_ID, values)

    def only_entity_force_ids(self, values: None | int | Iterable[int]) -> "FastDisScanner":
        return self.set_filter(FASTDIS_FILTER_ENTITY_FORCE_ID, values)

    def set_sample(self, sample_every: int = 1, sample_offset: int = 0) -> "FastDisScanner":
        if sample_every < 1:
            raise ValueError("sample_every must be >= 1")
        self._native.check(
            self._native.lib.fastdis_scanner_set_sample(self.ptr, int(sample_every), int(sample_offset))
        )
        return self

    def set_entity_state_fields(self, fields: int | str | Iterable[int | str]) -> "FastDisScanner":
        mask = entity_state_field_mask(fields) if not isinstance(fields, int) else int(fields)
        self._native.check(self._native.lib.fastdis_scanner_set_entity_state_fields(self.ptr, mask))
        return self

    def use_profile(self, profile: int | str) -> "FastDisScanner":
        """Apply a common native scanner profile and return ``self``."""

        self._native.check(self._native.lib.fastdis_scanner_use_profile(self.ptr, _profile_kind(profile)))
        return self

    def use_header_counting_profile(self) -> "FastDisScanner":
        return self.use_profile(FASTDIS_PROFILE_HEADER_COUNTING)

    def use_entity_state_routing_profile(self) -> "FastDisScanner":
        return self.use_profile(FASTDIS_PROFILE_ENTITY_STATE_ROUTING)

    def use_entity_state_pose_profile(self) -> "FastDisScanner":
        return self.use_profile(FASTDIS_PROFILE_ENTITY_STATE_POSE)

    def use_entity_state_full_profile(self) -> "FastDisScanner":
        return self.use_profile(FASTDIS_PROFILE_ENTITY_STATE_FULL)

    def use_entity_transform_profile(self) -> "FastDisScanner":
        return self.use_profile(FASTDIS_PROFILE_ENTITY_TRANSFORM)

    def allow_entity_ids(self, ids: Iterable[EntityIdTuple] | EntityIdTuple, *, clear: bool = True) -> "FastDisScanner":
        if clear:
            self.set_entity_ids(FASTDIS_ENTITY_ID_FILTER_ALLOW, ids)
        else:
            self.add_entity_ids(ids)
            self.set_entity_id_filter_mode(FASTDIS_ENTITY_ID_FILTER_ALLOW)
        return self

    def block_entity_ids(self, ids: Iterable[EntityIdTuple] | EntityIdTuple, *, clear: bool = True) -> "FastDisScanner":
        if clear:
            self.set_entity_ids(FASTDIS_ENTITY_ID_FILTER_BLOCK, ids)
        else:
            self.add_entity_ids(ids)
            self.set_entity_id_filter_mode(FASTDIS_ENTITY_ID_FILTER_BLOCK)
        return self

    def disable_entity_id_filter(self) -> "FastDisScanner":
        self.set_entity_id_filter_mode(FASTDIS_ENTITY_ID_FILTER_DISABLED)
        return self

    def scan_many(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        callback: PacketCallback | None = None,
        *,
        return_stats: bool = False,
    ) -> tuple[int, int, int] | dict[str, int]:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")

        keepalives, index_handles, original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        stats = FastDisScanStats()
        self._native.lib.fastdis_scan_stats_init(ctypes.byref(stats))

        if callback is None:
            cb = PacketCallbackC(0)
        else:
            def _cb(header_ptr, data_ptr, size, packet_user, callback_user):  # type: ignore[no-untyped-def]
                del data_ptr, size, callback_user
                header = header_ptr.contents
                original = None
                if packet_user:
                    index = ctypes.cast(packet_user, ctypes.POINTER(ctypes.c_size_t)).contents.value
                    original = original_packets[index]
                try:
                    callback(
                        int(header.version),
                        int(header.exercise_id),
                        int(header.pdu_type),
                        int(header.protocol_family),
                        int(header.timestamp),
                        int(header.length),
                        int(header.status),
                        original,
                    )
                except Exception:
                    return 1
                return 0

            cb = PacketCallbackC(_cb)

        rc = self._native.lib.fastdis_scanner_scan_packets(
            self.ptr,
            views,
            count,
            cb,
            None,
            ctypes.byref(stats),
        )
        self._native.check(rc)
        return stats.as_dict() if return_stats else stats.as_tuple()

    def scan_entity_state_many(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        callback: EntityStateCallback | None = None,
        *,
        return_stats: bool = False,
    ) -> tuple[int, int, int] | dict[str, int]:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")

        keepalives, index_handles, original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        stats = FastDisScanStats()
        self._native.lib.fastdis_scan_stats_init(ctypes.byref(stats))

        if callback is None:
            cb = EntityStateCallbackC(0)
        else:
            def _cb(entity_ptr, data_ptr, size, packet_user, callback_user):  # type: ignore[no-untyped-def]
                del data_ptr, size, callback_user
                original = None
                if packet_user:
                    index = ctypes.cast(packet_user, ctypes.POINTER(ctypes.c_size_t)).contents.value
                    original = original_packets[index]
                try:
                    callback(entity_ptr.contents.as_value(), original)
                except Exception:
                    return 1
                return 0

            cb = EntityStateCallbackC(_cb)

        rc = self._native.lib.fastdis_scanner_scan_entity_state_packets(
            self.ptr,
            views,
            count,
            cb,
            None,
            ctypes.byref(stats),
        )
        self._native.check(rc)
        return stats.as_dict() if return_stats else stats.as_tuple()

    def scan_entity_state_to_batch(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        capacity: int | None = None,
        return_stats: bool = False,
    ):
        """Scan using this reusable scanner and return Entity State records."""

        keepalives, index_handles, _original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        cap = count if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntityStatePrefix * cap
        storage = array_type()
        batch = FastDisEntityStateBatch(storage, cap, 0, 0)
        stats = FastDisScanStats()
        self._native.lib.fastdis_scan_stats_init(ctypes.byref(stats))
        rc = self._native.lib.fastdis_scanner_scan_entity_state_to_batch(
            self.ptr,
            views,
            count,
            ctypes.byref(batch),
            ctypes.byref(stats),
        )
        self._native.check(rc)
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_stats:
            meta = stats.as_dict()
            meta.update({"stored": int(batch.count), "dropped": int(batch.dropped), "capacity": int(batch.capacity)})
            return records, meta
        return records

    def scan_entity_transforms_to_batch(
        self,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        capacity: int | None = None,
        return_stats: bool = False,
    ):
        """Scan using this reusable scanner and return compact transform records."""

        keepalives, index_handles, _original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        cap = count if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntityTransform * cap
        storage = array_type()
        batch = FastDisEntityTransformBatch(storage, cap, 0, 0)
        stats = FastDisScanStats()
        self._native.lib.fastdis_scan_stats_init(ctypes.byref(stats))
        rc = self._native.lib.fastdis_scanner_scan_entity_transforms_to_batch(
            self.ptr,
            views,
            count,
            ctypes.byref(batch),
            ctypes.byref(stats),
        )
        self._native.check(rc)
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_stats:
            meta = stats.as_dict()
            meta.update({"stored": int(batch.count), "dropped": int(batch.dropped), "capacity": int(batch.capacity)})
            return records, meta
        return records



class FastDisEntityTable:
    """Opaque native latest-state cache keyed by DIS Entity ID.

    The table stores one compact transform per entity. Ticks are caller-defined;
    the usual engine pattern is to call ``ingest(..., advance_tick=True)`` once
    per network burst or frame, then snapshot changed/stale entities.
    """

    def __init__(self, native: NativeFastDis, ptr: int):
        self._native = native
        self._ptr = ctypes.c_void_p(ptr)
        self._closed = False

    def close(self) -> None:
        if not self._closed and self._ptr.value:
            self._native.lib.fastdis_entity_table_destroy(self._ptr)
            self._closed = True
            self._ptr = ctypes.c_void_p()

    def __enter__(self) -> "FastDisEntityTable":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        del exc_type, exc, tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @property
    def ptr(self) -> ctypes.c_void_p:
        if self._closed or not self._ptr.value:
            raise FastDisError("fastdis entity table is closed")
        return self._ptr

    def size(self) -> int:
        return int(self._native.lib.fastdis_entity_table_size(self.ptr))

    def tick(self) -> int:
        return int(self._native.lib.fastdis_entity_table_tick(self.ptr))

    def clear(self) -> "FastDisEntityTable":
        self._native.check(self._native.lib.fastdis_entity_table_clear(self.ptr))
        return self

    def advance_tick(self, delta: int = 1) -> "FastDisEntityTable":
        if delta < 0:
            raise ValueError("delta must be >= 0")
        self._native.check(self._native.lib.fastdis_entity_table_advance_tick(self.ptr, int(delta)))
        return self

    def mark_all_clean(self) -> "FastDisEntityTable":
        self._native.check(self._native.lib.fastdis_entity_table_mark_all_clean(self.ptr))
        return self

    def update_transform(self, transform: EntityTransform | FastDisEntityTransform) -> EntitySnapshot:
        raw = _ctypes_transform(transform)
        snapshot = FastDisEntitySnapshot()
        self._native.check(
            self._native.lib.fastdis_entity_table_update_transform(self.ptr, ctypes.byref(raw), ctypes.byref(snapshot))
        )
        return snapshot.as_value()

    def ingest(
        self,
        scanner: FastDisScanner,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        advance_tick: bool = True,
    ) -> dict[str, int | dict[str, int]]:
        """Scan a packet burst through ``scanner`` and update latest transforms."""

        keepalives, index_handles, _original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        stats = FastDisEntityTableUpdateStats()
        self._native.lib.fastdis_entity_table_update_stats_init(ctypes.byref(stats))
        rc = self._native.lib.fastdis_entity_table_ingest_packets(
            self.ptr,
            scanner.ptr,
            views,
            count,
            1 if advance_tick else 0,
            ctypes.byref(stats),
        )
        self._native.check(rc)
        return stats.as_dict()

    def get(self, entity_id: EntityIdTuple | tuple[int, int, int]) -> EntitySnapshot | None:
        site, application, entity = _entity_ids(entity_id)[0]
        snapshot = FastDisEntitySnapshot()
        rc = self._native.lib.fastdis_entity_table_get(
            self.ptr,
            int(site),
            int(application),
            int(entity),
            ctypes.byref(snapshot),
        )
        if rc == FASTDIS_ERR_NOT_FOUND:
            return None
        self._native.check(rc)
        return snapshot.as_value()

    def _snapshot_storage(self, capacity: int | None):
        cap = self.size() if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntitySnapshot * cap
        storage = array_type()
        batch = FastDisEntitySnapshotBatch(storage, cap, 0, 0)
        return storage, batch

    def _records_and_meta(self, storage, batch: FastDisEntitySnapshotBatch, *, return_meta: bool):  # type: ignore[no-untyped-def]
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_meta:
            return records, {
                "stored": int(batch.count),
                "dropped": int(batch.dropped),
                "capacity": int(batch.capacity),
                "table_size": self.size(),
                "tick": self.tick(),
            }
        return records

    def snapshot_all(self, *, capacity: int | None = None, return_meta: bool = False):
        storage, batch = self._snapshot_storage(capacity)
        self._native.check(self._native.lib.fastdis_entity_table_snapshot_all(self.ptr, ctypes.byref(batch)))
        return self._records_and_meta(storage, batch, return_meta=return_meta)

    def snapshot_changed(
        self,
        *,
        capacity: int | None = None,
        clear: bool = True,
        return_meta: bool = False,
    ):
        storage, batch = self._snapshot_storage(capacity)
        self._native.check(
            self._native.lib.fastdis_entity_table_snapshot_changed(self.ptr, ctypes.byref(batch), 1 if clear else 0)
        )
        return self._records_and_meta(storage, batch, return_meta=return_meta)

    def snapshot_stale(self, stale_after_ticks: int, *, capacity: int | None = None, return_meta: bool = False):
        if stale_after_ticks < 0:
            raise ValueError("stale_after_ticks must be >= 0")
        storage, batch = self._snapshot_storage(capacity)
        self._native.check(
            self._native.lib.fastdis_entity_table_snapshot_stale(
                self.ptr,
                int(stale_after_ticks),
                ctypes.byref(batch),
            )
        )
        return self._records_and_meta(storage, batch, return_meta=return_meta)

    def evict_stale(self, stale_after_ticks: int, *, capacity: int | None = None, return_meta: bool = False):
        if stale_after_ticks < 0:
            raise ValueError("stale_after_ticks must be >= 0")
        storage, batch = self._snapshot_storage(capacity)
        self._native.check(
            self._native.lib.fastdis_entity_table_evict_stale(
                self.ptr,
                int(stale_after_ticks),
                ctypes.byref(batch),
            )
        )
        return self._records_and_meta(storage, batch, return_meta=return_meta)


class FastDisSnapshotRead:
    """Context-managed acquired read view from a double-buffer snapshot buffer."""

    def __init__(self, buffer: "FastDisSnapshotBuffer", raw_view: FastDisEntitySnapshotView):
        self._buffer = buffer
        self._raw_view = raw_view
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            self._buffer._release_raw_view(self._raw_view)
            self._closed = True

    def __enter__(self) -> "FastDisSnapshotRead":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        del exc_type, exc, tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @property
    def view(self) -> EntitySnapshotView:
        return self._raw_view.as_value()

    @property
    def snapshots(self) -> tuple[EntitySnapshot, ...]:
        return self.view.snapshots

    @property
    def generation(self) -> int:
        return int(self._raw_view.generation)

    @property
    def count(self) -> int:
        return int(self._raw_view.count)

    @property
    def dropped(self) -> int:
        return int(self._raw_view.dropped)


class FastDisSnapshotBuffer:
    """Native double-buffered snapshot handoff for entity-table snapshots.

    Publish methods fill the inactive native array and make it the latest read
    view. ``acquire_latest()`` pins the current read slot; if both slots are
    pinned, the next publish raises ``FastDisError('snapshot buffer slot is busy')``
    rather than allocating or overwriting data still being consumed.
    """

    def __init__(self, native: NativeFastDis, ptr: int):
        self._native = native
        self._ptr = ctypes.c_void_p(ptr)
        self._closed = False

    def close(self) -> None:
        if not self._closed and self._ptr.value:
            self._native.lib.fastdis_entity_snapshot_buffer_destroy(self._ptr)
            self._closed = True
            self._ptr = ctypes.c_void_p()

    def __enter__(self) -> "FastDisSnapshotBuffer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        del exc_type, exc, tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @property
    def ptr(self) -> ctypes.c_void_p:
        if self._closed or not self._ptr.value:
            raise FastDisError("fastdis snapshot buffer is closed")
        return self._ptr

    def capacity(self) -> int:
        return int(self._native.lib.fastdis_entity_snapshot_buffer_capacity(self.ptr))

    def slot_count(self) -> int:
        return int(self._native.lib.fastdis_entity_snapshot_buffer_slot_count(self.ptr))

    def generation(self) -> int:
        return int(self._native.lib.fastdis_entity_snapshot_buffer_generation(self.ptr))

    def stats(self) -> dict[str, int]:
        raw = FastDisSnapshotBufferStats()
        self._native.lib.fastdis_entity_snapshot_buffer_stats_init(ctypes.byref(raw))
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_get_stats(self.ptr, ctypes.byref(raw)))
        return raw.as_dict()

    def reset_stats(self) -> "FastDisSnapshotBuffer":
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_reset_stats(self.ptr))
        return self

    def resize(self, capacity: int) -> "FastDisSnapshotBuffer":
        if capacity < 0:
            raise ValueError("capacity must be >= 0")
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_resize(self.ptr, int(capacity)))
        return self

    @staticmethod
    def _view_value(raw_view: FastDisEntitySnapshotView) -> EntitySnapshotView:
        return raw_view.as_value()

    def publish_all(self, table: FastDisEntityTable) -> EntitySnapshotView:
        raw = FastDisEntitySnapshotView()
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_publish_all(self.ptr, table.ptr, ctypes.byref(raw)))
        return self._view_value(raw)

    def publish_changed(self, table: FastDisEntityTable, *, clear: bool = True) -> EntitySnapshotView:
        raw = FastDisEntitySnapshotView()
        self._native.check(
            self._native.lib.fastdis_entity_snapshot_buffer_publish_changed(self.ptr, table.ptr, 1 if clear else 0, ctypes.byref(raw))
        )
        return self._view_value(raw)

    def publish_stale(self, table: FastDisEntityTable, stale_after_ticks: int) -> EntitySnapshotView:
        if stale_after_ticks < 0:
            raise ValueError("stale_after_ticks must be >= 0")
        raw = FastDisEntitySnapshotView()
        self._native.check(
            self._native.lib.fastdis_entity_snapshot_buffer_publish_stale(self.ptr, table.ptr, int(stale_after_ticks), ctypes.byref(raw))
        )
        return self._view_value(raw)

    def publish_evict_stale(self, table: FastDisEntityTable, stale_after_ticks: int) -> EntitySnapshotView:
        if stale_after_ticks < 0:
            raise ValueError("stale_after_ticks must be >= 0")
        raw = FastDisEntitySnapshotView()
        self._native.check(
            self._native.lib.fastdis_entity_snapshot_buffer_publish_evict_stale(
                self.ptr, table.ptr, int(stale_after_ticks), ctypes.byref(raw)
            )
        )
        return self._view_value(raw)

    def ingest_and_publish_changed(
        self,
        table: FastDisEntityTable,
        scanner: FastDisScanner,
        packets: Iterable[bytes | bytearray | memoryview],
        *,
        advance_tick: bool = True,
        clear: bool = True,
        return_stats: bool = False,
    ):
        """Ingest a burst into ``table`` and publish changed snapshots in one C call."""

        keepalives, index_handles, _original_packets, views, count = self._native._packet_views(packets)
        _ = (keepalives, index_handles)
        stats = FastDisEntityTableUpdateStats()
        self._native.lib.fastdis_entity_table_update_stats_init(ctypes.byref(stats))
        raw = FastDisEntitySnapshotView()
        rc = self._native.lib.fastdis_entity_table_ingest_packets_publish_changed(
            table.ptr,
            scanner.ptr,
            views,
            count,
            1 if advance_tick else 0,
            1 if clear else 0,
            self.ptr,
            ctypes.byref(stats),
            ctypes.byref(raw),
        )
        self._native.check(rc)
        view = self._view_value(raw)
        if return_stats:
            return view, stats.as_dict()
        return view

    def acquire_latest(self) -> FastDisSnapshotRead:
        raw = FastDisEntitySnapshotView()
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_acquire_latest(self.ptr, ctypes.byref(raw)))
        return FastDisSnapshotRead(self, raw)

    def _release_raw_view(self, raw_view: FastDisEntitySnapshotView) -> None:
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_release(self.ptr, ctypes.byref(raw_view)))

    def copy_latest(self, *, capacity: int | None = None, return_meta: bool = False):
        cap = self.capacity() if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        array_type = FastDisEntitySnapshot * cap
        storage = array_type()
        batch = FastDisEntitySnapshotBatch(storage, cap, 0, 0)
        self._native.check(self._native.lib.fastdis_entity_snapshot_buffer_copy_latest(self.ptr, ctypes.byref(batch)))
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_meta:
            return records, {
                "stored": int(batch.count),
                "dropped": int(batch.dropped),
                "capacity": int(batch.capacity),
                "generation": self.generation(),
            }
        return records

    def copy_latest_extrapolated(
        self,
        *,
        target_tick: int,
        seconds_per_tick: float = 1.0,
        capacity: int | None = None,
        return_meta: bool = False,
    ):
        cap = self.capacity() if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        if seconds_per_tick < 0:
            raise ValueError("seconds_per_tick must be >= 0")
        array_type = FastDisEntitySnapshot * cap
        storage = array_type()
        batch = FastDisEntitySnapshotBatch(storage, cap, 0, 0)
        self._native.check(
            self._native.lib.fastdis_entity_snapshot_buffer_copy_latest_extrapolated(
                self.ptr,
                ctypes.c_uint64(int(target_tick)),
                ctypes.c_double(float(seconds_per_tick)),
                ctypes.byref(batch),
            )
        )
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_meta:
            return records, {
                "stored": int(batch.count),
                "dropped": int(batch.dropped),
                "capacity": int(batch.capacity),
                "generation": self.generation(),
                "target_tick": int(target_tick),
                "seconds_per_tick": float(seconds_per_tick),
            }
        return records

    def copy_latest_dead_reckoned(
        self,
        *,
        target_tick: int,
        seconds_per_tick: float = 1.0,
        capacity: int | None = None,
        return_meta: bool = False,
    ):
        cap = self.capacity() if capacity is None else int(capacity)
        if cap < 0:
            raise ValueError("capacity must be >= 0")
        if seconds_per_tick < 0:
            raise ValueError("seconds_per_tick must be >= 0")
        array_type = FastDisEntitySnapshot * cap
        storage = array_type()
        batch = FastDisEntitySnapshotBatch(storage, cap, 0, 0)
        self._native.check(
            self._native.lib.fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned(
                self.ptr,
                ctypes.c_uint64(int(target_tick)),
                ctypes.c_double(float(seconds_per_tick)),
                ctypes.byref(batch),
            )
        )
        records = [storage[i].as_value() for i in range(int(batch.count))]
        if return_meta:
            return records, {
                "stored": int(batch.count),
                "dropped": int(batch.dropped),
                "capacity": int(batch.capacity),
                "generation": self.generation(),
                "target_tick": int(target_tick),
                "seconds_per_tick": float(seconds_per_tick),
            }
        return records


def load_native(path: str | os.PathLike[str] | None = None) -> NativeFastDis:
    """Load the portable fastdis shared library."""

    return NativeFastDis(path)


def load_shared_library(path: str | os.PathLike[str] | None = None) -> NativeFastDis:
    """Alias for :func:`load_native`."""

    return load_native(path)


__all__ = [
    "FASTDIS_ABI_EPOCH",
    "FASTDIS_ABI_REVISION",
    "FASTDIS_ABI_VERSION",
    "FASTDIS_ENTITY_ID_FILTER_ALLOW",
    "FASTDIS_ENTITY_ID_FILTER_BLOCK",
    "FASTDIS_ENTITY_ID_FILTER_DISABLED",
    "FASTDIS_ENTITY_CHANGE_NONE",
    "FASTDIS_ENTITY_CHANGE_NEW",
    "FASTDIS_ENTITY_CHANGE_UPDATED",
    "FASTDIS_ENTITY_CHANGE_STALE",
    "FASTDIS_ENTITY_CHANGE_REMOVED",
    "FASTDIS_ENTITY_CHANGE_UNCHANGED",
    "FASTDIS_ENTITY_CHANGE_EXTRAPOLATED",
    "FASTDIS_ENTITY_INFORMATION_FAMILY",
    "FASTDIS_OTHER_FIXED_SIZE",
    "FASTDIS_OTHER_PDU_TYPE",
    "FASTDIS_FIRE_FIXED_SIZE",
    "FASTDIS_FIRE_PDU_TYPE",
    "FASTDIS_DETONATION_FIXED_SIZE",
    "FASTDIS_DETONATION_PDU_TYPE",
    "FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE",
    "FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE",
    "FASTDIS_DESIGNATOR_FIXED_SIZE",
    "FASTDIS_DESIGNATOR_PDU_TYPE",
    "FASTDIS_TRANSMITTER_FIXED_SIZE",
    "FASTDIS_TRANSMITTER_PDU_TYPE",
    "FASTDIS_SIGNAL_DIS6_FIXED_SIZE",
    "FASTDIS_SIGNAL_DIS7_FIXED_SIZE",
    "FASTDIS_SIGNAL_PDU_TYPE",
    "FASTDIS_RECEIVER_DIS6_FIXED_SIZE",
    "FASTDIS_RECEIVER_DIS7_FIXED_SIZE",
    "FASTDIS_RECEIVER_PDU_TYPE",
    "FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE",
    "FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE",
    "FASTDIS_IFF_FIXED_SIZE",
    "FASTDIS_IFF_PDU_TYPE",
    "FASTDIS_UA_FIXED_SIZE",
    "FASTDIS_UA_PDU_TYPE",
    "FASTDIS_SEES_FIXED_SIZE",
    "FASTDIS_SEES_PDU_TYPE",
    "FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE",
    "FASTDIS_INTERCOM_SIGNAL_PDU_TYPE",
    "FASTDIS_INTERCOM_CONTROL_FIXED_SIZE",
    "FASTDIS_INTERCOM_CONTROL_PDU_TYPE",
    "FASTDIS_AGGREGATE_STATE_FIXED_SIZE",
    "FASTDIS_AGGREGATE_STATE_PDU_TYPE",
    "FASTDIS_IS_GROUP_OF_FIXED_SIZE",
    "FASTDIS_IS_GROUP_OF_PDU_TYPE",
    "FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE",
    "FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE",
    "FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE",
    "FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE",
    "FASTDIS_IS_PART_OF_FIXED_SIZE",
    "FASTDIS_IS_PART_OF_PDU_TYPE",
    "FASTDIS_MINEFIELD_STATE_FIXED_SIZE",
    "FASTDIS_MINEFIELD_STATE_PDU_TYPE",
    "FASTDIS_MINEFIELD_QUERY_FIXED_SIZE",
    "FASTDIS_MINEFIELD_QUERY_PDU_TYPE",
    "FASTDIS_MINEFIELD_DATA_FIXED_SIZE",
    "FASTDIS_MINEFIELD_DATA_PDU_TYPE",
    "FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE",
    "FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE",
    "FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE",
    "FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE",
    "FASTDIS_GRIDDED_DATA_FIXED_SIZE",
    "FASTDIS_GRIDDED_DATA_PDU_TYPE",
    "FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE",
    "FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE",
    "FASTDIS_POINT_OBJECT_STATE_PDU_TYPE",
    "FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE",
    "FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE",
    "FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE",
    "FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE",
    "FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE",
    "FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE",
    "FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE",
    "FASTDIS_TSPI_FIXED_SIZE",
    "FASTDIS_TSPI_PDU_TYPE",
    "FASTDIS_APPEARANCE_FIXED_SIZE",
    "FASTDIS_APPEARANCE_PDU_TYPE",
    "FASTDIS_ARTICULATED_PARTS_FIXED_SIZE",
    "FASTDIS_ARTICULATED_PARTS_PDU_TYPE",
    "FASTDIS_LE_FIRE_FIXED_SIZE",
    "FASTDIS_LE_FIRE_PDU_TYPE",
    "FASTDIS_LE_DETONATION_FIXED_SIZE",
    "FASTDIS_LE_DETONATION_PDU_TYPE",
    "FASTDIS_SERVICE_REQUEST_FIXED_SIZE",
    "FASTDIS_SERVICE_REQUEST_PDU_TYPE",
    "FASTDIS_RESUPPLY_OFFER_FIXED_SIZE",
    "FASTDIS_RESUPPLY_OFFER_PDU_TYPE",
    "FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE",
    "FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE",
    "FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE",
    "FASTDIS_RESUPPLY_CANCEL_PDU_TYPE",
    "FASTDIS_REPAIR_COMPLETE_FIXED_SIZE",
    "FASTDIS_REPAIR_COMPLETE_PDU_TYPE",
    "FASTDIS_REPAIR_RESPONSE_FIXED_SIZE",
    "FASTDIS_REPAIR_RESPONSE_PDU_TYPE",
    "FASTDIS_CREATE_ENTITY_FIXED_SIZE",
    "FASTDIS_CREATE_ENTITY_PDU_TYPE",
    "FASTDIS_ENTITY_STATE_FIXED_SIZE",
    "FASTDIS_ENTITY_STATE_PDU_TYPE",
    "FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE",
    "FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE",
    "FASTDIS_REMOVE_ENTITY_FIXED_SIZE",
    "FASTDIS_REMOVE_ENTITY_PDU_TYPE",
    "FASTDIS_START_RESUME_FIXED_SIZE",
    "FASTDIS_START_RESUME_PDU_TYPE",
    "FASTDIS_STOP_FREEZE_FIXED_SIZE",
    "FASTDIS_STOP_FREEZE_PDU_TYPE",
    "FASTDIS_ACKNOWLEDGE_FIXED_SIZE",
    "FASTDIS_ACKNOWLEDGE_PDU_TYPE",
    "FASTDIS_ACTION_REQUEST_FIXED_SIZE",
    "FASTDIS_ACTION_REQUEST_PDU_TYPE",
    "FASTDIS_ACTION_RESPONSE_FIXED_SIZE",
    "FASTDIS_ACTION_RESPONSE_PDU_TYPE",
    "FASTDIS_DATA_QUERY_FIXED_SIZE",
    "FASTDIS_DATA_QUERY_PDU_TYPE",
    "FASTDIS_SET_DATA_FIXED_SIZE",
    "FASTDIS_SET_DATA_PDU_TYPE",
    "FASTDIS_DATA_FIXED_SIZE",
    "FASTDIS_DATA_PDU_TYPE",
    "FASTDIS_EVENT_REPORT_FIXED_SIZE",
    "FASTDIS_EVENT_REPORT_PDU_TYPE",
    "FASTDIS_COMMENT_FIXED_SIZE",
    "FASTDIS_COMMENT_PDU_TYPE",
    "FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE",
    "FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE",
    "FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE",
    "FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE",
    "FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE",
    "FASTDIS_START_RESUME_RELIABLE_PDU_TYPE",
    "FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE",
    "FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE",
    "FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE",
    "FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE",
    "FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE",
    "FASTDIS_ACTION_REQUEST_RELIABLE_PDU_TYPE",
    "FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE",
    "FASTDIS_ACTION_RESPONSE_RELIABLE_PDU_TYPE",
    "FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE",
    "FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE",
    "FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE",
    "FASTDIS_SET_DATA_RELIABLE_PDU_TYPE",
    "FASTDIS_DATA_RELIABLE_FIXED_SIZE",
    "FASTDIS_DATA_RELIABLE_PDU_TYPE",
    "FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE",
    "FASTDIS_EVENT_REPORT_RELIABLE_PDU_TYPE",
    "FASTDIS_COMMENT_RELIABLE_FIXED_SIZE",
    "FASTDIS_COMMENT_RELIABLE_PDU_TYPE",
    "FASTDIS_RECORD_RELIABLE_FIXED_SIZE",
    "FASTDIS_RECORD_RELIABLE_PDU_TYPE",
    "FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE",
    "FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE",
    "FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE",
    "FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE",
    "FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE",
    "FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE",
    "FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE",
    "FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE",
    "FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE",
    "FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE",
    "FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE",
    "FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE",
    "FASTDIS_ATTRIBUTE_FIXED_SIZE",
    "FASTDIS_ATTRIBUTE_PDU_TYPE",
    "FASTDIS_DR_OTHER",
    "FASTDIS_DR_STATIC",
    "FASTDIS_DR_FPW",
    "FASTDIS_DR_RPW",
    "FASTDIS_DR_RVW",
    "FASTDIS_DR_FVW",
    "FASTDIS_DR_FPB",
    "FASTDIS_DR_RPB",
    "FASTDIS_DR_RVB",
    "FASTDIS_DR_FVB",
    "FASTDIS_PROFILE_HEADER_COUNTING",
    "FASTDIS_PROFILE_ENTITY_STATE_ROUTING",
    "FASTDIS_PROFILE_ENTITY_STATE_POSE",
    "FASTDIS_PROFILE_ENTITY_STATE_FULL",
    "FASTDIS_PROFILE_ENTITY_TRANSFORM",
    "FASTDIS_ERR_BAD_ARGUMENT",
    "FASTDIS_ERR_CALLBACK_STOPPED",
    "FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER",
    "FASTDIS_ERR_LENGTH_TOO_SMALL",
    "FASTDIS_ERR_OUT_OF_MEMORY",
    "FASTDIS_ERR_NOT_FOUND",
    "FASTDIS_ERR_BUSY",
    "FASTDIS_ERR_SHORT_PACKET",
    "FASTDIS_ERR_UNSUPPORTED_PDU",
    "FASTDIS_ES_FIELD_ALL",
    "FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE",
    "FASTDIS_ES_FIELD_APPEARANCE",
    "FASTDIS_ES_FIELD_CAPABILITIES",
    "FASTDIS_ES_FIELD_DEAD_RECKONING",
    "FASTDIS_ES_FIELD_ENTITY_ID",
    "FASTDIS_ES_FIELD_ENTITY_TYPE",
    "FASTDIS_ES_FIELD_FORCE_ID",
    "FASTDIS_ES_FIELD_HEADER",
    "FASTDIS_ES_FIELD_KINEMATICS",
    "FASTDIS_ES_FIELD_LINEAR_VELOCITY",
    "FASTDIS_ES_FIELD_LOCATION",
    "FASTDIS_ES_FIELD_MARKING",
    "FASTDIS_ES_FIELD_ORIENTATION",
    "FASTDIS_ES_FIELD_POSE",
    "FASTDIS_ES_FIELD_ROUTING",
    "FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT",
    "FASTDIS_FILTER_ENTITY_FORCE_ID",
    "FASTDIS_FILTER_ENTITY_FORCE_IDS",
    "FASTDIS_FILTER_EXERCISE_IDS",
    "FASTDIS_FILTER_PDU_TYPES",
    "FASTDIS_FILTER_PROTOCOL_FAMILIES",
    "FASTDIS_FILTER_VERSIONS",
    "FASTDIS_FILTER_EXERCISE_ID",
    "FASTDIS_FILTER_PDU_TYPE",
    "FASTDIS_FILTER_PROTOCOL_FAMILY",
    "FASTDIS_FILTER_VERSION",
    "FASTDIS_FLAG_ALLOW_TRUNCATED",
    "FASTDIS_HEADER_STATUS_UNAVAILABLE",
    "FASTDIS_HEADER_SIZE",
    "FASTDIS_OK",
    "FASTDIS_PROTOCOL_VERSION_DIS6",
    "FASTDIS_PROTOCOL_VERSION_DIS7",
    "ClockTimeTuple",
    "EventIdTuple",
    "EntityStateCallback",
    "Fire",
    "Detonation",
    "Acknowledge",
    "ActionRequest",
    "ActionResponse",
    "DataQuery",
    "SetData",
    "EventReport",
    "Comment",
    "SimulationManagementRequest",
    "SimulationManagementReliableRequest",
    "StartResume",
    "StopFreeze",
    "StartResumeReliable",
    "StopFreezeReliable",
    "ActionRequestReliable",
    "ActionResponseReliable",
    "DataQueryReliable",
    "SetDataReliable",
    "DataReliable",
    "EventReportReliable",
    "CommentReliable",
    "RecordReliable",
    "SetRecordReliable",
    "RecordQueryReliable",
    "Designator",
    "Transmitter",
    "Signal",
    "Receiver",
    "ElectronicEmissions",
    "IffAtcNavAidsLayer1",
    "Iff",
    "Ua",
    "Sees",
    "IntercomSignal",
    "IntercomControl",
    "Attribute",
    "DirectedEnergyFire",
    "EntityDamageStatus",
    "OtherPdu",
    "AggregateState",
    "IsGroupOf",
    "TransferControlRequest",
    "TransferOwnership",
    "IsPartOf",
    "MinefieldState",
    "MinefieldQuery",
    "MinefieldData",
    "MinefieldResponseNack",
    "InformationOperationsAction",
    "InformationOperationsReport",
    "ServiceRequest",
    "ResupplyOffer",
    "ResupplyReceived",
    "ResupplyCancel",
    "RepairComplete",
    "RepairResponse",
    "EntityTransform",
    "EntitySnapshot",
    "EntitySnapshotView",
    "EntityStatePrefix",
    "SnapshotBufferStats",
    "FastDisBurstDescriptor",
    "FastDisClockTime",
    "FastDisDetonation",
    "FastDisDatumRecordSetView",
    "FastDisCountedBytesView",
    "FastDisRadioEntityType",
    "FastDisModulationType",
    "FastDisSystemId",
    "FastDisIffFundamentalData",
    "FastDisSimulationAddress",
    "FastDisOtherPdu",
    "FastDisAggregateState",
    "FastDisIsGroupOf",
    "FastDisTransferControlRequest",
    "FastDisTransferOwnership",
    "FastDisIsPartOf",
    "FastDisMinefieldState",
    "FastDisMinefieldQuery",
    "FastDisMinefieldData",
    "FastDisMinefieldResponseNack",
    "FastDisDesignator",
    "FastDisTransmitter",
    "FastDisSignal",
    "FastDisReceiver",
    "FastDisElectronicEmissions",
    "FastDisIffAtcNavAidsLayer1",
    "FastDisIff",
    "FastDisUa",
    "FastDisSees",
    "FastDisIntercomSignal",
    "FastDisIntercomControl",
    "FastDisAttribute",
    "FastDisDirectedEnergyFire",
    "FastDisEntityDamageStatus",
    "FastDisInformationOperationsAction",
    "FastDisInformationOperationsReport",
    "FastDisServiceRequest",
    "FastDisResupplyOffer",
    "FastDisResupplyReceived",
    "FastDisResupplyCancel",
    "FastDisRepairComplete",
    "FastDisRepairResponse",
    "FastDisEntityId",
    "FastDisEntityStatePrefix",
    "FastDisEntityStateBatch",
    "FastDisEntityTransform",
    "FastDisEntityTransformBatch",
    "FastDisEntitySnapshot",
    "FastDisEntitySnapshotBatch",
    "FastDisEntityTable",
    "FastDisSnapshotBuffer",
    "FastDisSnapshotRead",
    "FastDisEntityTableUpdateStats",
    "FastDisSnapshotBufferStats",
    "FastDisEntityType",
    "FastDisError",
    "FastDisEulerAngles",
    "FastDisEventId",
    "FastDisFire",
    "FastDisAcknowledge",
    "FastDisActionRequest",
    "FastDisActionResponse",
    "FastDisActionRequestReliable",
    "FastDisActionResponseReliable",
    "FastDisDataQuery",
    "FastDisDataQueryReliable",
    "FastDisSetData",
    "FastDisSetDataReliable",
    "FastDisDataReliable",
    "FastDisEventReport",
    "FastDisEventReportReliable",
    "FastDisComment",
    "FastDisCommentReliable",
    "FastDisRecordReliable",
    "FastDisSetRecordReliable",
    "FastDisRecordQueryReliable",
    "FastDisHeader",
    "FastDisPacketView",
    "FastDisScanConfig",
    "FastDisScanStats",
    "FastDisScanner",
    "FastDisSimulationManagementRequest",
    "FastDisSimulationManagementReliableRequest",
    "FastDisStartResume",
    "FastDisStartResumeReliable",
    "FastDisStopFreeze",
    "FastDisStopFreezeReliable",
    "FastDisU8Filter",
    "FastDisVec3f",
    "FastDisWorldCoordinates",
    "HeaderTuple",
    "NativeFastDis",
    "PacketCallback",
    "PacketCallbackC",
    "EntityStateCallbackC",
    "entity_state_field_mask",
    "find_native_library",
    "load_native",
    "load_shared_library",
]
