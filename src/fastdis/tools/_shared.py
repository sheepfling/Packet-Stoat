from __future__ import annotations

import json
import math
import socket
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3
HEADER_SIZE = 12
ENTITY_STATE_FIXED_SIZE = 144
ENTITY_INFORMATION_FAMILY = 1
ENTITY_STATE_PDU_TYPE = 1


@dataclass(frozen=True)
class EntityStateSpec:
    site: int = 100
    application: int = 1
    entity: int = 1
    force_id: int = 1
    exercise_id: int = 3
    marking: str = "FASTDIS"
    entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    alternate_entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    velocity_mps: tuple[float, float, float] = (1.0, 2.0, 3.0)
    location_ecef_m: tuple[float, float, float] = (1000.0, 2000.0, 3000.0)
    orientation_dis_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    appearance: int = 0x01020304
    dr_algorithm: int = 4
    dr_parameters: bytes = bytes(range(1, 16))
    dr_linear_accel: tuple[float, float, float] = (0.1, 0.2, 0.3)
    dr_angular_velocity: tuple[float, float, float] = (0.4, 0.5, 0.6)
    marking_character_set: int = 1
    capabilities: int = 1
    timestamp: int = 0x10000000


def geodetic_to_ecef(lat_deg: float, lon_deg: float, height_m: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (n + height_m) * cos_lat * cos_lon
    y = (n + height_m) * cos_lat * sin_lon
    z = (n * (1.0 - WGS84_E2) + height_m) * sin_lat
    return (x, y, z)


def _dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v: Iterable[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = _norm(v)
    if n <= 1e-12:
        raise ValueError("cannot normalize near-zero vector")
    return (v[0] / n, v[1] / n, v[2] / n)


def _rodrigues_rotate(v: tuple[float, float, float], axis: tuple[float, float, float], angle_rad: float) -> tuple[float, float, float]:
    ax = _normalize(axis)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    cross = _cross(ax, v)
    dot = _dot(ax, v)
    return (
        v[0] * cos_a + cross[0] * sin_a + ax[0] * dot * (1.0 - cos_a),
        v[1] * cos_a + cross[1] * sin_a + ax[1] * dot * (1.0 - cos_a),
        v[2] * cos_a + cross[2] * sin_a + ax[2] * dot * (1.0 - cos_a),
    )


def local_enu_basis(lat_deg: float, lon_deg: float) -> dict[str, tuple[float, float, float]]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    east = (-math.sin(lon), math.cos(lon), 0.0)
    north = (-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat))
    up = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))
    return {"east": east, "north": north, "up": up}


def enu_direction_to_ecef(v_enu: tuple[float, float, float], basis: dict[str, tuple[float, float, float]]) -> tuple[float, float, float]:
    east = basis["east"]
    north = basis["north"]
    up = basis["up"]
    return (
        v_enu[0] * east[0] + v_enu[1] * north[0] + v_enu[2] * up[0],
        v_enu[0] * east[1] + v_enu[1] * north[1] + v_enu[2] * up[1],
        v_enu[0] * east[2] + v_enu[1] * north[2] + v_enu[2] * up[2],
    )


def local_ned_attitude_to_body_fru_enu(heading_deg: float, pitch_deg: float, roll_deg: float) -> dict[str, tuple[float, float, float]]:
    heading = math.radians(heading_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)
    forward0 = (math.sin(heading), math.cos(heading), 0.0)
    right0 = (math.cos(heading), -math.sin(heading), 0.0)
    up0 = (0.0, 0.0, 1.0)
    forward1 = _normalize(_rodrigues_rotate(forward0, right0, pitch))
    up1 = _normalize(_rodrigues_rotate(up0, right0, pitch))
    right1 = right0
    right2 = _normalize(_rodrigues_rotate(right1, forward1, roll))
    up2 = _normalize(_rodrigues_rotate(up1, forward1, roll))
    return {"forward_enu": forward1, "right_enu": right2, "up_enu": up2}


def body_fru_enu_to_body_frd_ecef(body_fru_enu: dict[str, tuple[float, float, float]], lat_deg: float, lon_deg: float) -> dict[str, tuple[float, float, float]]:
    basis = local_enu_basis(lat_deg, lon_deg)
    forward = _normalize(enu_direction_to_ecef(body_fru_enu["forward_enu"], basis))
    right = _normalize(enu_direction_to_ecef(body_fru_enu["right_enu"], basis))
    up = enu_direction_to_ecef(body_fru_enu["up_enu"], basis)
    down = _normalize((-up[0], -up[1], -up[2]))
    return {"forward_ecef": forward, "right_ecef": right, "down_ecef": down}


def body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef: dict[str, tuple[float, float, float]]) -> tuple[float, float, float]:
    forward = body_frd_ecef["forward_ecef"]
    right = body_frd_ecef["right_ecef"]
    down = body_frd_ecef["down_ecef"]
    matrix = (
        (forward[0], right[0], down[0]),
        (forward[1], right[1], down[1]),
        (forward[2], right[2], down[2]),
    )
    theta = math.asin(-matrix[2][0])
    cos_theta = math.cos(theta)
    if abs(cos_theta) <= 1e-12:
        psi = math.atan2(-matrix[0][1], matrix[1][1])
        phi = 0.0
    else:
        psi = math.atan2(matrix[1][0], matrix[0][0])
        phi = math.atan2(matrix[2][1], matrix[2][2])
    return (math.degrees(psi), math.degrees(theta), math.degrees(phi))


def entity_state_spec_from_geodetic(
    *,
    lat_deg: float,
    lon_deg: float,
    alt_m: float,
    heading_deg: float,
    pitch_deg: float,
    roll_deg: float,
    site: int = 100,
    application: int = 1,
    entity: int = 1,
    force_id: int = 1,
    exercise_id: int = 3,
    marking: str = "FASTDIS",
    timestamp: int = 0x10000000,
) -> EntityStateSpec:
    location = geodetic_to_ecef(lat_deg, lon_deg, alt_m)
    body_fru_enu = local_ned_attitude_to_body_fru_enu(heading_deg, pitch_deg, roll_deg)
    body_frd_ecef = body_fru_enu_to_body_frd_ecef(body_fru_enu, lat_deg, lon_deg)
    dis = body_frd_ecef_to_dis_psi_theta_phi(body_frd_ecef)
    return EntityStateSpec(
        site=site,
        application=application,
        entity=entity,
        force_id=force_id,
        exercise_id=exercise_id,
        marking=marking,
        location_ecef_m=location,
        orientation_dis_deg=dis,
        timestamp=timestamp,
    )


def make_entity_state_packet(spec: EntityStateSpec) -> bytes:
    packet = bytearray(ENTITY_STATE_FIXED_SIZE)
    packet[0] = 7
    packet[1] = spec.exercise_id & 0xFF
    packet[2] = ENTITY_STATE_PDU_TYPE
    packet[3] = ENTITY_INFORMATION_FAMILY
    packet[4:8] = int(spec.timestamp & 0xFFFFFFFF).to_bytes(4, "big")
    packet[8:10] = ENTITY_STATE_FIXED_SIZE.to_bytes(2, "big")
    packet[10] = 0x80
    packet[11] = 0
    base = HEADER_SIZE
    packet[base + 0 : base + 6] = struct.pack(">HHH", spec.site, spec.application, spec.entity)
    packet[base + 6] = spec.force_id & 0xFF
    packet[base + 7] = 0
    packet[base + 8 : base + 16] = struct.pack(">BBHBBBB", *spec.entity_type)
    packet[base + 16 : base + 24] = struct.pack(">BBHBBBB", *spec.alternate_entity_type)
    packet[base + 24 : base + 36] = struct.pack(">fff", *spec.velocity_mps)
    packet[base + 36 : base + 60] = struct.pack(">ddd", *spec.location_ecef_m)
    packet[base + 60 : base + 72] = struct.pack(">fff", *[math.radians(v) for v in spec.orientation_dis_deg])
    packet[base + 72 : base + 76] = int(spec.appearance & 0xFFFFFFFF).to_bytes(4, "big")
    packet[base + 76] = spec.dr_algorithm & 0xFF
    dr = spec.dr_parameters[:15].ljust(15, b"\x00")
    packet[base + 77 : base + 92] = dr
    packet[base + 92 : base + 104] = struct.pack(">fff", *spec.dr_linear_accel)
    packet[base + 104 : base + 116] = struct.pack(">fff", *spec.dr_angular_velocity)
    packet[base + 116] = spec.marking_character_set & 0xFF
    marking = spec.marking.encode("ascii", errors="replace")[:11].ljust(11, b"\x00")
    packet[base + 117 : base + 128] = marking
    packet[base + 128 : base + 132] = int(spec.capabilities & 0xFFFFFFFF).to_bytes(4, "big")
    return bytes(packet)


def send_udp_packets(*, packets: Iterable[bytes], host: str, port: int, rate_hz: float = 0.0) -> int:
    count = 0
    delay = (1.0 / rate_hz) if rate_hz > 0 else 0.0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for packet in packets:
            sock.sendto(packet, (host, port))
            count += 1
            if delay > 0.0:
                time.sleep(delay)
    return count


def receive_udp_packets(
    *,
    bind_host: str,
    port: int,
    max_packets: int,
    timeout_s: float,
) -> list[bytes]:
    packets: list[bytes] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_host, port))
        sock.settimeout(timeout_s)
        while len(packets) < max_packets:
            try:
                data, _addr = sock.recvfrom(65535)
            except TimeoutError:
                break
            except socket.timeout:
                break
            packets.append(data)
    return packets


def session_truth_from_specs(specs: list[EntityStateSpec]) -> dict[str, object]:
    latest_by_entity: dict[tuple[int, int, int], EntityStateSpec] = {}
    for spec in specs:
        latest_by_entity[(spec.site, spec.application, spec.entity)] = spec
    latest_entities = [
        {
            "site": site,
            "application": application,
            "entity": entity,
            "force_id": spec.force_id,
            "location_ecef_m": list(spec.location_ecef_m),
            "orientation_dis_rad": [math.radians(value) for value in spec.orientation_dis_deg],
        }
        for (site, application, entity), spec in sorted(latest_by_entity.items())
    ]
    return {
        "schema": "fastdis.network_truth.v1",
        "packet_count": len(specs),
        "packets_parsed": len(specs),
        "malformed": 0,
        "entity_state": len(specs),
        "unique_entities": len(latest_entities),
        "latest_entities": latest_entities,
        "errors": [],
    }


def write_session_truth(path: Path, truth: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")


def load_session_truth(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
