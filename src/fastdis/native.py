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

FASTDIS_ABI_VERSION = 8
FASTDIS_HEADER_SIZE = 12
FASTDIS_PROTOCOL_VERSION_DIS6 = 6
FASTDIS_PROTOCOL_VERSION_DIS7 = 7
FASTDIS_HEADER_STATUS_UNAVAILABLE = -1
FASTDIS_ENTITY_INFORMATION_FAMILY = 1
FASTDIS_ENTITY_STATE_PDU_TYPE = 1
FASTDIS_ENTITY_STATE_FIXED_SIZE = 144

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
Vec3fTuple = tuple[float, float, float]
WorldCoordinatesTuple = tuple[float, float, float]
EulerAnglesTuple = tuple[float, float, float]
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


def _candidate_paths() -> Iterable[Path]:
    env = os.environ.get("FASTDIS_LIBRARY")
    if env:
        yield Path(env)

    here = Path(__file__).resolve().parent
    roots = [
        here,
        here.parent,
        Path.cwd(),
        Path.cwd() / "build",
        Path.cwd() / "build" / "cmake" / "host",
        Path.cwd() / "build" / "cmake" / "mingw-win64",
        Path.cwd() / "build" / "cmake" / "linux-x86_64",
        Path.cwd() / "build" / "native",
    ]
    for root in roots:
        for name in _library_filenames():
            yield root / name

    cwd = Path.cwd()
    for pattern in ("build/cmake/*/libfastdis.*", "build*/libfastdis.*", "cmake-build*/libfastdis.*", "out*/libfastdis.*"):
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

    def version_string(self) -> str:
        return self.lib.fastdis_version_string().decode("utf-8")

    def status_string(self, status: int) -> str:
        return self.lib.fastdis_status_string(int(status)).decode("utf-8")

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


def load_native(path: str | os.PathLike[str] | None = None) -> NativeFastDis:
    """Load the portable fastdis shared library."""

    return NativeFastDis(path)


def load_shared_library(path: str | os.PathLike[str] | None = None) -> NativeFastDis:
    """Alias for :func:`load_native`."""

    return load_native(path)


__all__ = [
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
    "FASTDIS_ENTITY_STATE_FIXED_SIZE",
    "FASTDIS_ENTITY_STATE_PDU_TYPE",
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
    "EntityStateCallback",
    "EntityTransform",
    "EntitySnapshot",
    "EntitySnapshotView",
    "EntityStatePrefix",
    "SnapshotBufferStats",
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
    "FastDisHeader",
    "FastDisPacketView",
    "FastDisScanConfig",
    "FastDisScanStats",
    "FastDisScanner",
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
