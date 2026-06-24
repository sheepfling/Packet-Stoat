#include "fastdis/fastdis.h"
#include "fastdis/fastdis_pdu_catalog.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>

namespace {

void put_be16(uint8_t *p, uint16_t value) {
    p[0] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[1] = static_cast<uint8_t>(value & 0xffu);
}

void put_be32(uint8_t *p, uint32_t value) {
    p[0] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[3] = static_cast<uint8_t>(value & 0xffu);
}

void put_be64(uint8_t *p, uint64_t value) {
    p[0] = static_cast<uint8_t>((value >> 56) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 48) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 40) & 0xffu);
    p[3] = static_cast<uint8_t>((value >> 32) & 0xffu);
    p[4] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[5] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[6] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[7] = static_cast<uint8_t>(value & 0xffu);
}

void put_be_float(uint8_t *p, float value) {
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be32(p, bits);
}

void put_be_double(uint8_t *p, double value) {
    uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be64(p, bits);
}

void put_vec3f(uint8_t *p, float x, float y, float z) {
    put_be_float(p + 0, x);
    put_be_float(p + 4, y);
    put_be_float(p + 8, z);
}

void put_clock_time(uint8_t *p, uint32_t hour, uint32_t time_past_hour) {
    put_be32(p + 0, hour);
    put_be32(p + 4, time_past_hour);
}

void put_world(uint8_t *p, double x, double y, double z) {
    put_be_double(p + 0, x);
    put_be_double(p + 8, y);
    put_be_double(p + 16, z);
}

void make_pdu(uint8_t *p, uint8_t version, uint8_t pdu_type, uint16_t length = 12) {
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = pdu_type;
    p[3] = 1;
    p[4] = 0x01;
    p[5] = 0x02;
    p[6] = 0x03;
    p[7] = 0x04;
    put_be16(p + 8, length);
    if (version >= 7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
}

void make_entity_state_pdu(uint8_t *p, uint8_t version = 7, uint8_t force_id = 2) {
    make_pdu(p, version, FASTDIS_ENTITY_STATE_PDU_TYPE, FASTDIS_ENTITY_STATE_FIXED_SIZE);
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;

    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    b[6] = force_id;
    b[7] = 0;

    b[8] = 1;
    b[9] = 2;
    put_be16(b + 10, 840);
    b[12] = 3;
    b[13] = 4;
    b[14] = 5;
    b[15] = 6;

    b[16] = 9;
    b[17] = 8;
    put_be16(b + 18, 124);
    b[20] = 7;
    b[21] = 6;
    b[22] = 5;
    b[23] = 4;

    put_vec3f(b + 24, 1.25f, -2.5f, 3.75f);
    put_world(b + 36, 10.0, 20.0, 30.0);
    put_vec3f(b + 60, 0.1f, 0.2f, 0.3f);
    put_be32(b + 72, 0xAABBCCDDu);
    b[76] = 4;
    for (int i = 0; i < 15; ++i) {
        b[77 + i] = static_cast<uint8_t>(i + 1);
    }
    put_vec3f(b + 92, 0.5f, 0.6f, 0.7f);
    put_vec3f(b + 104, 1.5f, 1.6f, 1.7f);
    b[116] = 1;
    const char *marking = "TANK001";
    std::memcpy(b + 117, marking, std::strlen(marking));
    put_be32(b + 128, 0x01020304u);
}

void make_entity_state_update_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE, FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE);
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;

    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0);
    put_vec3f(b + 8, 4.0f, 5.0f, 6.0f);
    put_world(b + 20, 40.0, 50.0, 60.0);
    put_vec3f(b + 44, 0.4f, 0.5f, 0.6f);
    put_be32(b + 56, 0x11223344u);
}

void make_create_entity_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_CREATE_ENTITY_PDU_TYPE, FASTDIS_CREATE_ENTITY_FIXED_SIZE);
    p[3] = 5;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_be32(b + 12, 0xA0B0C0D0u);
}

void make_fire_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_FIRE_PDU_TYPE, FASTDIS_FIRE_FIXED_SIZE);
    p[3] = 2;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be16(b + 12, 0x0007);
    put_be16(b + 14, 0x0008);
    put_be16(b + 16, 0x0009);
    put_be16(b + 18, 0x000A);
    put_be16(b + 20, 0x000B);
    put_be16(b + 22, 0x000C);
    put_be32(b + 24, 99u);
    put_world(b + 28, 1000.5, 2000.25, 3000.75);
    b[52] = 2;
    b[53] = 1;
    put_be16(b + 54, 225);
    b[56] = 4;
    b[57] = 5;
    b[58] = 6;
    b[59] = 7;
    put_be16(b + 60, 101);
    put_be16(b + 62, 202);
    put_be16(b + 64, 3);
    put_be16(b + 66, 600);
    put_vec3f(b + 68, 1.5f, 2.5f, 3.5f);
    put_be_float(b + 80, 4444.5f);
}

void make_detonation_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_DETONATION_PDU_TYPE, FASTDIS_DETONATION_FIXED_SIZE + 16u);
    p[3] = 2;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be16(b + 12, 0x0007);
    put_be16(b + 14, 0x0008);
    put_be16(b + 16, 0x0009);
    put_be16(b + 18, 0x000A);
    put_be16(b + 20, 0x000B);
    put_be16(b + 22, 0x000C);
    put_vec3f(b + 24, 11.0f, 22.0f, 33.0f);
    put_world(b + 36, 111.5, 222.25, 333.75);
    b[60] = 2;
    b[61] = 1;
    put_be16(b + 62, 225);
    b[64] = 4;
    b[65] = 5;
    b[66] = 6;
    b[67] = 7;
    put_be16(b + 68, 101);
    put_be16(b + 70, 202);
    put_be16(b + 72, 3);
    put_be16(b + 74, 600);
    put_vec3f(b + 76, -4.0f, -5.0f, -6.0f);
    b[88] = 17;
    b[89] = 1;
    put_be16(b + 90, 0);
    for (int i = 0; i < 16; ++i) {
        b[92 + i] = static_cast<uint8_t>(i + 1);
    }
}

void make_remove_entity_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_REMOVE_ENTITY_PDU_TYPE, FASTDIS_REMOVE_ENTITY_FIXED_SIZE);
    p[3] = 5;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_be32(b + 12, 0x0BADF00Du);
}

void make_start_resume_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_START_RESUME_PDU_TYPE, FASTDIS_START_RESUME_FIXED_SIZE);
    p[3] = 5;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_clock_time(b + 12, 7u, 123456u);
    put_clock_time(b + 20, 9u, 654321u);
    put_be32(b + 28, 0x01020304u);
}

void make_stop_freeze_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_STOP_FREEZE_PDU_TYPE, FASTDIS_STOP_FREEZE_FIXED_SIZE);
    p[3] = 5;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_clock_time(b + 12, 5u, 7654321u);
    b[20] = 3;
    b[21] = 4;
    put_be16(b + 22, 0xABCDu);
    put_be32(b + 24, 0x0F1E2D3Cu);
}

void make_acknowledge_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_ACKNOWLEDGE_PDU_TYPE, FASTDIS_ACKNOWLEDGE_FIXED_SIZE);
    p[3] = 5;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_be16(b + 12, 0x1234u);
    put_be16(b + 14, 0x5678u);
    put_be32(b + 16, 0xCAFEBABEu);
}

void make_create_entity_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE, FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    b[12] = 7u;
    put_be16(b + 13, 0x1357u);
    b[15] = 9u;
    put_be32(b + 16, 0xA0B0C0D0u);
}

void make_remove_entity_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE, FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    b[12] = 8u;
    put_be16(b + 13, 0x2468u);
    b[15] = 10u;
    put_be32(b + 16, 0x0BADF00Du);
}

void make_start_resume_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_START_RESUME_RELIABLE_PDU_TYPE, FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_clock_time(b + 12, 7u, 123456u);
    put_clock_time(b + 20, 9u, 654321u);
    b[28] = 11u;
    put_be16(b + 29, 0xAAAAu);
    b[31] = 12u;
    put_be32(b + 32, 0x01020304u);
}

void make_stop_freeze_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE, FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_clock_time(b + 12, 5u, 7654321u);
    b[20] = 3u;
    b[21] = 4u;
    b[22] = 13u;
    b[23] = 14u;
    put_be32(b + 24, 0x0F1E2D3Cu);
}

void make_acknowledge_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE, FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x1111);
    put_be16(b + 2, 0x2222);
    put_be16(b + 4, 0x3333);
    put_be16(b + 6, 0x4444);
    put_be16(b + 8, 0x5555);
    put_be16(b + 10, 0x6666);
    put_be16(b + 12, 0x9ABCu);
    put_be16(b + 14, 0xDEF0u);
    put_be32(b + 16, 0xFACECAFEu);
}

void make_record_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_RECORD_RELIABLE_PDU_TYPE, FASTDIS_RECORD_RELIABLE_FIXED_SIZE + 8u);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be32(b + 12, 0x51525354u);
    b[16] = 7u;
    b[17] = 8u;
    put_be16(b + 18, 0x090Au);
    put_be32(b + 20, 2u);
    for (int i = 0; i < 8; ++i) {
        b[24 + i] = static_cast<uint8_t>(0x10 + i);
    }
}

void make_set_record_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE, FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE + 8u);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be32(b + 12, 0x61626364u);
    b[16] = 9u;
    put_be16(b + 17, 0x0B0Cu);
    b[19] = 13u;
    put_be32(b + 20, 3u);
    for (int i = 0; i < 8; ++i) {
        b[28 + i] = static_cast<uint8_t>(0x21 + i);
    }
}

void make_record_query_reliable_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE, FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE + 8u);
    p[3] = 10;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be32(b + 12, 0x71727374u);
    b[16] = 14u;
    put_be16(b + 17, 0x1516u);
    b[19] = 17u;
    put_be16(b + 20, 0x1819u);
    put_be32(b + 22, 0x1A1B1C1Du);
    put_be32(b + 26, 2u);
    for (int i = 0; i < 8; ++i) {
        b[30 + i] = static_cast<uint8_t>(0x31 + i);
    }
}

void make_service_request_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_SERVICE_REQUEST_PDU_TYPE, FASTDIS_SERVICE_REQUEST_FIXED_SIZE + 8u);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    b[12] = 7u;
    b[13] = 2u;
    put_be16(b + 14, 0x4041u);
    for (int i = 0; i < 8; ++i) {
        b[16 + i] = static_cast<uint8_t>(0x41 + i);
    }
}

void make_resupply_offer_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_RESUPPLY_OFFER_PDU_TYPE, FASTDIS_RESUPPLY_OFFER_FIXED_SIZE + 8u);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    b[12] = 2u;
    b[13] = 0x11u;
    b[14] = 0x12u;
    b[15] = 0x13u;
    for (int i = 0; i < 8; ++i) {
        b[16 + i] = static_cast<uint8_t>(0x51 + i);
    }
}

void make_resupply_received_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE, FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE + 8u);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    b[12] = 2u;
    put_be16(b + 13, 0x6162u);
    b[15] = 0x63u;
    for (int i = 0; i < 8; ++i) {
        b[16 + i] = static_cast<uint8_t>(0x61 + i);
    }
}

void make_resupply_cancel_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_RESUPPLY_CANCEL_PDU_TYPE, FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
}

void make_repair_complete_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_REPAIR_COMPLETE_PDU_TYPE, FASTDIS_REPAIR_COMPLETE_FIXED_SIZE);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    put_be16(b + 12, 0x7172u);
    put_be16(b + 14, 0x7374u);
}

void make_repair_response_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_REPAIR_RESPONSE_PDU_TYPE, FASTDIS_REPAIR_RESPONSE_FIXED_SIZE);
    p[3] = 3;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001);
    put_be16(b + 2, 0x0002);
    put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x0004);
    put_be16(b + 8, 0x0005);
    put_be16(b + 10, 0x0006);
    b[12] = 0x75u;
    put_be16(b + 13, 0x7677u);
    b[15] = 0x78u;
}

void make_designator_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_DESIGNATOR_PDU_TYPE, FASTDIS_DESIGNATOR_FIXED_SIZE);
    p[3] = 6;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001); put_be16(b + 2, 0x0002); put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x1234u);
    put_be16(b + 8, 0x0004); put_be16(b + 10, 0x0005); put_be16(b + 12, 0x0006);
    put_be16(b + 14, 0x2345u);
    put_be_float(b + 16, 12.5f);
    put_be_float(b + 20, 1.25f);
    put_vec3f(b + 24, 2.5f, 3.5f, 4.5f);
    put_world(b + 36, 100.0, 200.0, 300.0);
    b[60] = 4u;
    put_be16(b + 61, 0x3456u);
    b[63] = 0x78u;
    put_vec3f(b + 64, 5.5f, 6.5f, 7.5f);
}

void make_transmitter_pdu(uint8_t *p, uint8_t version) {
    const uint16_t length = version >= FASTDIS_PROTOCOL_VERSION_DIS7
        ? static_cast<uint16_t>(FASTDIS_TRANSMITTER_FIXED_SIZE + 24u)
        : static_cast<uint16_t>(FASTDIS_TRANSMITTER_FIXED_SIZE + 3u);
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_TRANSMITTER_PDU_TYPE;
    p[3] = 4;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80u;
        p[11] = 0x00u;
    } else {
        p[10] = 0x12u;
        p[11] = 0x34u;
    }
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x1212u);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        b[8] = 1u; b[9] = 2u; put_be16(b + 10, 840u); b[12] = 5u; b[13] = 6u; b[14] = 7u; b[15] = 8u;
        put_be16(b + 18, 2u);
    } else {
        b[8] = 1u; b[9] = 2u; put_be16(b + 10, 840u); b[12] = 5u; b[13] = 6u; put_be16(b + 14, 0x0708u);
    }
    b[16] = 9u; b[17] = 10u;
    put_world(b + 20, 10.0, 20.0, 30.0);
    put_vec3f(b + 44, 1.0f, 2.0f, 3.0f);
    put_be16(b + 56, 0x4444u);
    put_be16(b + 58, version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? 1u : 0u);
    put_be32(b + 60, 225000u);
    put_be_float(b + 64, 50.5f);
    put_be_float(b + 68, 60.5f);
    put_be16(b + 72, 1u); put_be16(b + 74, 2u); put_be16(b + 76, 3u); put_be16(b + 78, 4u);
    put_be16(b + 80, 0x5555u); put_be16(b + 82, 0x6666u);
    b[84] = version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? 1u : 3u;
    put_be16(b + 85, 0x7777u);
    b[87] = 0x88u;
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        put_vec3f(p + FASTDIS_TRANSMITTER_FIXED_SIZE + 0u, 9.0f, 10.0f, 11.0f);
        put_vec3f(p + FASTDIS_TRANSMITTER_FIXED_SIZE + 12u, 12.0f, 13.0f, 14.0f);
    } else {
        p[FASTDIS_TRANSMITTER_FIXED_SIZE + 0u] = 0x01u;
        p[FASTDIS_TRANSMITTER_FIXED_SIZE + 1u] = 0x02u;
        p[FASTDIS_TRANSMITTER_FIXED_SIZE + 2u] = 0x03u;
    }
}

void make_signal_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = version >= 7 ? static_cast<uint16_t>(FASTDIS_SIGNAL_DIS7_FIXED_SIZE + 4u)
                                         : static_cast<uint16_t>(FASTDIS_SIGNAL_DIS6_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_SIGNAL_PDU_TYPE, length);
    p[3] = 4;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    size_t offset = 0u;
    if (version < 7) {
        put_be16(b + 0, 0x0001); put_be16(b + 2, 0x0002); put_be16(b + 4, 0x0003);
        put_be16(b + 6, 0x1111u);
        offset = 8u;
    }
    put_be16(b + offset + 0, 0x2222u);
    put_be16(b + offset + 2, 0x3333u);
    put_be32(b + offset + 4, 48000u);
    put_be16(b + offset + 8, 4u);
    put_be16(b + offset + 10, 2u);
    b[offset + 12] = 0x41u;
    b[offset + 13] = 0x42u;
    b[offset + 14] = 0x43u;
    b[offset + 15] = 0x44u;
}

void make_receiver_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = version >= 7 ? FASTDIS_RECEIVER_DIS7_FIXED_SIZE : FASTDIS_RECEIVER_DIS6_FIXED_SIZE;
    make_pdu(p, version, FASTDIS_RECEIVER_PDU_TYPE, length);
    p[3] = 4;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    size_t offset = 0u;
    if (version < 7) {
        put_be16(b + 0, 0x0001); put_be16(b + 2, 0x0002); put_be16(b + 4, 0x0003);
        put_be16(b + 6, 0x1111u);
        offset = 8u;
    }
    put_be16(b + offset + 0, 0x2222u);
    put_be16(b + offset + 2, 0x3333u);
    put_be_float(b + offset + 4, 12.5f);
    put_be16(b + offset + 8, 0x0004); put_be16(b + offset + 10, 0x0005); put_be16(b + offset + 12, 0x0006);
    put_be16(b + offset + 14, 0x4444u);
}

void make_iff_atc_navaids_layer1_pdu(uint8_t *p, uint8_t version) {
    std::memset(p, 0, FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE;
    p[3] = 6;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80u; p[11] = 0x00u;
    } else {
        p[10] = 0x12u; p[11] = 0x34u;
    }
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_vec3f(b + 12, 1.0f, 2.0f, 3.0f);
    put_be16(b + 24, 0x1111u); put_be16(b + 26, 0x2222u); b[28] = 0x33u; b[29] = 0x44u;
    put_be16(b + 30, 0x5555u);
    b[32] = 1u; b[33] = 2u; b[34] = 3u; b[35] = 4u;
    put_be16(b + 36, 5u); put_be16(b + 38, 6u); put_be16(b + 40, 7u); put_be16(b + 42, 8u); put_be16(b + 44, 9u); put_be16(b + 46, 10u);
}

void make_intercom_signal_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_INTERCOM_SIGNAL_PDU_TYPE, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4u);
    p[3] = 4;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001); put_be16(b + 2, 0x0002); put_be16(b + 4, 0x0003);
    put_be16(b + 6, 0x1212u);
    put_be16(b + 8, 0x2222u);
    put_be16(b + 10, 0x3333u);
    put_be32(b + 12, 32000u);
    put_be16(b + 16, 4u);
    put_be16(b + 18, 2u);
    b[20] = 0x51u; b[21] = 0x52u; b[22] = 0x53u; b[23] = 0x54u;
}

void make_intercom_control_pdu(uint8_t *p, uint8_t version) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_INTERCOM_CONTROL_FIXED_SIZE + 4u);
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_INTERCOM_CONTROL_PDU_TYPE;
    p[3] = 4;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80u; p[11] = 0x00u;
    } else {
        p[10] = 0x12u; p[11] = 0x34u;
    }
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    b[0] = 0x11u; b[1] = 0x22u;
    put_be16(b + 2, 0x0001u); put_be16(b + 4, 0x0002u); put_be16(b + 6, 0x0003u);
    b[8] = 0x33u; b[9] = 0x44u; b[10] = 0x55u; b[11] = 0x66u; b[12] = 0x77u;
    put_be16(b + 13, 0x0004u); put_be16(b + 15, 0x0005u); put_be16(b + 17, 0x0006u);
    put_be16(b + 19, 0x8888u);
    put_be32(b + 21, 4u);
    b[25] = 0x61u; b[26] = 0x62u; b[27] = 0x63u; b[28] = 0x64u;
}

void make_other_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_OTHER_PDU_TYPE, FASTDIS_OTHER_FIXED_SIZE + 4u);
    p[3] = 0;
    p[12] = 0x4fu;
    p[13] = 0x54u;
    p[14] = 0x48u;
    p[15] = 0x52u;
}

void make_aggregate_state_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_AGGREGATE_STATE_PDU_TYPE, FASTDIS_AGGREGATE_STATE_FIXED_SIZE + 6u);
    p[3] = 7;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    b[6] = 4u;
    b[7] = 5u;
    b[8] = 1u; b[9] = 2u; put_be16(b + 10, 840u); b[12] = 3u; b[13] = 4u; b[14] = 5u; b[15] = 6u;
    put_be32(b + 16, 0x11223344u);
    b[20] = 1u;
    std::memset(b + 21, 0, 31u);
    const char *marking = "AGGREGATE-ALPHA";
    std::memcpy(b + 21, marking, std::strlen(marking));
    put_vec3f(b + 52, 1.0f, 2.0f, 3.0f);
    put_vec3f(b + 64, 0.1f, 0.2f, 0.3f);
    put_world(b + 76, 10.0, 20.0, 30.0);
    put_vec3f(b + 100, 4.0f, 5.0f, 6.0f);
    put_be16(b + 112, 7u); put_be16(b + 114, 8u); put_be16(b + 116, 9u); put_be16(b + 118, 10u);
    b[120] = 0xA1u; b[121] = 0xA2u; b[122] = 0xA3u; b[123] = 0xA4u; b[124] = 0xA5u; b[125] = 0xA6u;
}

void make_is_group_of_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_IS_GROUP_OF_PDU_TYPE, FASTDIS_IS_GROUP_OF_FIXED_SIZE + 4u);
    p[3] = 7;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    b[6] = 0x21u;
    b[7] = 0x02u;
    put_be32(b + 8, 0x10203040u);
    put_be_double(b + 12, 41.25);
    put_be_double(b + 20, -93.5);
    b[28] = 0xB1u; b[29] = 0xB2u; b[30] = 0xB3u; b[31] = 0xB4u;
}

void make_transfer_control_request_pdu(uint8_t *p, uint8_t version = 6) {
    make_pdu(p, version, FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + 4u);
    p[3] = 7;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    put_be16(b + 6, 4u); put_be16(b + 8, 5u); put_be16(b + 10, 6u);
    put_be32(b + 12, 0x11223344u);
    b[16] = 0x07u;
    b[17] = 0x08u;
    put_be16(b + 18, 7u); put_be16(b + 20, 8u); put_be16(b + 22, 9u);
    b[24] = 0x02u;
    b[25] = 0xC1u; b[26] = 0xC2u; b[27] = 0xC3u; b[28] = 0xC4u;
}

void make_transfer_ownership_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE, FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + 4u);
    p[3] = 7;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 10u); put_be16(b + 2, 11u); put_be16(b + 4, 12u);
    put_be16(b + 6, 13u); put_be16(b + 8, 14u); put_be16(b + 10, 15u);
    put_be32(b + 12, 0x55667788u);
    b[16] = 0x09u;
    b[17] = 0x0Au;
    put_be16(b + 18, 16u); put_be16(b + 20, 17u); put_be16(b + 22, 18u);
    b[24] = 0x03u;
    b[25] = 0xD1u; b[26] = 0xD2u; b[27] = 0xD3u; b[28] = 0xD4u;
}

void make_is_part_of_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_IS_PART_OF_PDU_TYPE, FASTDIS_IS_PART_OF_FIXED_SIZE);
    p[3] = 7;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    put_be16(b + 6, 4u); put_be16(b + 8, 5u); put_be16(b + 10, 6u);
    put_be16(b + 12, 0x1112u); put_be16(b + 14, 0x1314u);
    put_vec3f(b + 16, 7.0f, 8.0f, 9.0f);
    put_be16(b + 28, 0x2122u); put_be16(b + 30, 0x2324u);
    b[32] = 2u; b[33] = 3u; put_be16(b + 34, 225u); b[36] = 4u; b[37] = 5u; b[38] = 6u; b[39] = 7u;
}

void make_attribute_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ATTRIBUTE_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_ATTRIBUTE_PDU_TYPE, length);
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0101u);
    put_be16(b + 2, 0x0202u);
    put_be32(b + 4, 0x11223344u);
    put_be16(b + 8, 0x5566u);
    b[10] = 67u;
    b[11] = 7u;
    put_be32(b + 12, 0x778899AAu);
    b[16] = 0x12u;
    b[17] = 0x34u;
    put_be16(b + 18, 1u);
    b[20] = 0x61u; b[21] = 0x62u; b[22] = 0x63u; b[23] = 0x64u;
}

void make_directed_energy_fire_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE, length);
    p[3] = 2;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    b[12] = 2u; b[13] = 1u; put_be16(b + 14, 225u); b[16] = 4u; b[17] = 5u; b[18] = 6u; b[19] = 7u;
    put_clock_time(b + 20, 7u, 123456u);
    put_be_float(b + 28, 1.25f);
    put_vec3f(b + 32, 2.5f, 3.5f, 4.5f);
    put_be_float(b + 44, 5.5f);
    put_be_float(b + 48, 6.5f);
    put_be_float(b + 52, 7.5f);
    put_be_float(b + 56, 8.5f);
    put_be32(b + 60, 9012u);
    put_be32(b + 64, 0x10203040u);
    b[68] = 0x11u;
    b[69] = 0x22u;
    put_be32(b + 70, 0x33445566u);
    put_be16(b + 74, 0x7788u);
    put_be16(b + 76, 1u);
    b[78] = 0x90u; b[79] = 0x91u; b[80] = 0x92u; b[81] = 0x93u;
}

void make_entity_damage_status_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE, length);
    p[3] = 2;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_be16(b + 12, 0x0007u); put_be16(b + 14, 0x0008u); put_be16(b + 16, 0x0009u);
    put_be16(b + 18, 0x1112u);
    put_be16(b + 20, 0x1314u);
    put_be16(b + 22, 1u);
    b[24] = 0xA1u; b[25] = 0xA2u; b[26] = 0xA3u; b[27] = 0xA4u;
}

void make_iff_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_IFF_PDU_TYPE, FASTDIS_IFF_FIXED_SIZE);
    p[3] = 6;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_vec3f(b + 12, 1.0f, 2.0f, 3.0f);
    put_be16(b + 24, 0x1111u); put_be16(b + 26, 0x2222u); b[28] = 0x33u; b[29] = 0x44u;
    put_be16(b + 30, 0x5555u);
    b[32] = 1u; b[33] = 2u; b[34] = 3u; b[35] = 4u;
    put_be16(b + 36, 5u); put_be16(b + 38, 6u); put_be16(b + 40, 7u); put_be16(b + 42, 8u); put_be16(b + 44, 9u); put_be16(b + 46, 10u);
}

void make_electronic_emissions_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE + 6u);
    make_pdu(p, version, FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE, length);
    p[3] = 6;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    b[12] = 0x07u; b[13] = 0x02u; put_be16(b + 14, 0x0809u);
    b[16] = 0xE1u; b[17] = 0xE2u; b[18] = 0xE3u; b[19] = 0xE4u; b[20] = 0xE5u; b[21] = 0xE6u;
}

void make_information_operations_action_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE, length);
    p[3] = 13;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_be32(b + 12, 0x11223344u);
    put_be16(b + 16, 0x0102u); put_be16(b + 18, 0x0304u); put_be16(b + 20, 0x0506u); put_be16(b + 22, 0x0708u);
    put_be32(b + 24, 0x55667788u);
    put_be16(b + 28, 0x0007u); put_be16(b + 30, 0x0008u); put_be16(b + 32, 0x0009u);
    put_be16(b + 34, 0x000Au); put_be16(b + 36, 0x000Bu); put_be16(b + 38, 0x000Cu);
    put_be16(b + 40, 0x090Au); put_be16(b + 42, 1u);
    b[44] = 0xC1u; b[45] = 0xC2u; b[46] = 0xC3u; b[47] = 0xC4u;
}

void make_information_operations_report_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE, length);
    p[3] = 13;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0102u); b[8] = 0x03u; b[9] = 0x04u;
    put_be16(b + 10, 0x0004u); put_be16(b + 12, 0x0005u); put_be16(b + 14, 0x0006u);
    put_be16(b + 16, 0x0007u); put_be16(b + 18, 0x0008u); put_be16(b + 20, 0x0009u);
    put_be16(b + 22, 0x1112u); put_be16(b + 24, 0x1314u); put_be16(b + 26, 1u);
    b[28] = 0xD1u; b[29] = 0xD2u; b[30] = 0xD3u; b[31] = 0xD4u;
}

void make_ua_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_UA_FIXED_SIZE + 8u);
    make_pdu(p, version, FASTDIS_UA_PDU_TYPE, length);
    p[3] = 6;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    b[12] = 0x0Au; b[13] = 0x0Bu; put_be16(b + 14, 0x0C0Du);
    b[16] = 0x0Eu; b[17] = 0x01u; b[18] = 0x02u; b[19] = 0x03u;
    b[20] = 0xF1u; b[21] = 0xF2u; b[22] = 0xF3u; b[23] = 0xF4u; b[24] = 0xF5u; b[25] = 0xF6u; b[26] = 0xF7u; b[27] = 0xF8u;
}

void make_sees_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_SEES_FIXED_SIZE + 8u);
    make_pdu(p, version, FASTDIS_SEES_PDU_TYPE, length);
    p[3] = 6;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0011u); put_be16(b + 2, 0x0022u); put_be16(b + 4, 0x0033u);
    put_be16(b + 6, 0x1112u); put_be16(b + 8, 0x1314u); put_be16(b + 10, 0x1516u);
    put_be16(b + 12, 0x0002u); put_be16(b + 14, 0x0003u);
    b[16] = 0xAAu; b[17] = 0xBBu; b[18] = 0xCCu; b[19] = 0xDDu; b[20] = 0xEEu; b[21] = 0xFFu; b[22] = 0x00u; b[23] = 0x11u;
}

void make_minefield_state_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = static_cast<uint16_t>(version >= 7 ? 104u : 104u);
    make_pdu(p, version, FASTDIS_MINEFIELD_STATE_PDU_TYPE, length);
    p[3] = 8u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    if (version >= 7) {
        put_be16(b + 0, 231u); put_be16(b + 2, 232u); put_be16(b + 4, 233u);
        put_be16(b + 6, 234u); b[8] = 235u; b[9] = 2u;
        b[10] = 19u; b[11] = 20u; put_be16(b + 12, 225u); b[14] = 21u; b[15] = 22u; b[16] = 23u; b[17] = 24u;
        put_be16(b + 18, 2u);
        put_world(b + 20, 40.25, 50.5, 60.75);
        put_vec3f(b + 44, 0.4f, 0.5f, 0.6f);
        put_be16(b + 56, 236u); put_be16(b + 58, 237u);
        put_be_float(b + 60, 5.5f); put_be_float(b + 64, 6.5f); put_be_float(b + 68, 7.5f); put_be_float(b + 72, 8.5f);
        b[76] = 25u; b[77] = 26u; put_be16(b + 78, 840u); b[80] = 27u; b[81] = 28u; b[82] = 29u; b[83] = 30u;
        b[84] = 31u; b[85] = 32u; put_be16(b + 86, 124u); b[88] = 33u; b[89] = 34u; b[90] = 35u; b[91] = 36u;
    } else {
        put_be16(b + 0, 221u); put_be16(b + 2, 222u); put_be16(b + 4, 223u);
        put_be16(b + 6, 224u); b[8] = 225u; b[9] = 2u;
        b[10] = 1u; b[11] = 2u; put_be16(b + 12, 840u); b[14] = 3u; b[15] = 4u; b[16] = 5u; b[17] = 6u;
        put_be16(b + 18, 2u);
        put_world(b + 20, 10.25, 20.5, 30.75);
        put_vec3f(b + 44, 0.1f, 0.2f, 0.3f);
        put_be16(b + 56, 226u); put_be16(b + 58, 227u);
        put_be_float(b + 60, 1.5f); put_be_float(b + 64, 2.5f); put_be_float(b + 68, 3.5f); put_be_float(b + 72, 4.5f);
        b[76] = 7u; b[77] = 8u; put_be16(b + 78, 124u); b[80] = 9u; b[81] = 10u; b[82] = 11u; b[83] = 12u;
        b[84] = 13u; b[85] = 14u; put_be16(b + 86, 225u); b[88] = 15u; b[89] = 16u; b[90] = 17u; b[91] = 18u;
    }
}

void make_minefield_query_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = 60u;
    make_pdu(p, version, FASTDIS_MINEFIELD_QUERY_PDU_TYPE, length);
    p[3] = 8u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 201u); put_be16(b + 2, 202u); put_be16(b + 4, 203u);
    put_be16(b + 6, 204u); put_be16(b + 8, 205u); put_be16(b + 10, 206u);
    b[12] = 207u; b[13] = 2u; b[14] = 0u; b[15] = 2u; put_be32(b + 16, 0x01020304u);
    b[20] = 3u; b[21] = 4u; put_be16(b + 22, 225u); b[24] = 5u; b[25] = 6u; b[26] = 7u; b[27] = 8u;
    put_be_float(b + 28, 1.5f); put_be_float(b + 32, 2.5f); put_be_float(b + 36, 3.5f); put_be_float(b + 40, 4.5f);
    b[44] = 0x11u; b[45] = 0x12u; b[46] = 0x21u; b[47] = 0x22u;
}

void make_minefield_data_pdu(uint8_t *p, uint8_t version = 7) {
    const uint16_t length = 73u;
    make_pdu(p, version, FASTDIS_MINEFIELD_DATA_PDU_TYPE, length);
    p[3] = 8u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 251u); put_be16(b + 2, 252u); put_be16(b + 4, 253u);
    put_be16(b + 6, 254u); put_be16(b + 8, 255u); put_be16(b + 10, 256u);
    put_be16(b + 12, 257u); b[14] = 200u; b[15] = 3u; b[16] = 2u; b[17] = 2u; b[18] = 2u; b[19] = 0u;
    put_be32(b + 20, 0x01020304u);
    b[24] = 37u; b[25] = 38u; put_be16(b + 26, 225u); b[28] = 39u; b[29] = 40u; b[30] = 41u; b[31] = 42u;
    b[32] = 0x31u; b[33] = 0x32u; b[34] = 0x41u; b[35] = 0x42u; b[36] = 0u;
    put_vec3f(b + 37, 9.5f, 10.5f, 11.5f);
    put_vec3f(b + 49, 12.5f, 13.5f, 14.5f);
}

void make_minefield_response_nack_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = 42u;
    make_pdu(p, version, FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE, length);
    p[3] = 8u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 181u); put_be16(b + 2, 182u); put_be16(b + 4, 183u);
    put_be16(b + 6, 184u); put_be16(b + 8, 185u); put_be16(b + 10, 186u);
    b[12] = 187u; b[13] = 2u;
    for (int i = 0; i < 8; ++i) {
        b[14 + i] = static_cast<uint8_t>(i + 1);
        b[22 + i] = static_cast<uint8_t>(0x11u + i);
    }
}

void make_environmental_process_pdu(uint8_t *p, uint8_t version = 6) {
    make_pdu(p, version, FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE, static_cast<uint16_t>(FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE + 10u));
    p[3] = 9u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 211u); put_be16(b + 2, 212u); put_be16(b + 4, 213u);
    b[6] = 9u; b[7] = 10u; put_be16(b + 8, 840u); b[10] = 11u; b[11] = 12u; b[12] = 13u; b[13] = 14u;
    b[14] = 15u; b[15] = 16u; b[16] = 2u; put_be16(b + 17, 0x1718u);
    const uint8_t tail[10] = {0x31u, 0x32u, 0x33u, 0x34u, 0x35u, 0x36u, 0x37u, 0x38u, 0x39u, 0x3Au};
    std::memcpy(b + 19, tail, sizeof(tail));
}

void make_gridded_data_pdu(uint8_t *p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_GRIDDED_DATA_PDU_TYPE, static_cast<uint16_t>(FASTDIS_GRIDDED_DATA_FIXED_SIZE + 10u));
    p[3] = 9u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 261u); put_be16(b + 2, 262u); put_be16(b + 4, 263u);
    put_be16(b + 6, 264u); put_be16(b + 8, 265u); put_be16(b + 10, 266u); put_be16(b + 12, 267u);
    b[14] = 3u; b[15] = 1u;
    b[16] = 43u; b[17] = 44u; put_be16(b + 18, 840u); b[20] = 45u; b[21] = 46u; b[22] = 47u; b[23] = 48u;
    put_vec3f(b + 24, 0.7f, 0.8f, 0.9f);
    put_be64(b + 36, 0x0102030405060708ull);
    put_be32(b + 44, 269u); b[48] = 4u; put_be16(b + 49, 270u); b[51] = 0u;
    const uint8_t tail[10] = {0x51u, 0x52u, 0x53u, 0x54u, 0x55u, 0x56u, 0x57u, 0x58u, 0x59u, 0x5Au};
    std::memcpy(b + 52, tail, sizeof(tail));
}

void make_point_object_state_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = version >= 7 ? FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE : FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE;
    make_pdu(p, version, FASTDIS_POINT_OBJECT_STATE_PDU_TYPE, length);
    p[3] = 9u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    if (version >= 7) {
        put_be16(b + 0, 71u); put_be16(b + 2, 72u); put_be16(b + 4, 73u);
        put_be16(b + 6, 74u); put_be16(b + 8, 75u); put_be16(b + 10, 76u);
        put_be16(b + 12, 77u); b[14] = 78u; b[15] = 79u;
        b[16] = 4u; b[17] = 5u; b[18] = 6u; b[19] = 7u;
        put_world(b + 20, 400.25, 500.5, 600.75);
        put_vec3f(b + 44, 0.4f, 0.5f, 0.6f);
        put_be_double(b + 56, 2345.5);
        put_be16(b + 64, 80u); put_be16(b + 66, 81u); put_be16(b + 68, 82u); put_be16(b + 70, 83u);
        put_be32(b + 72, 84u);
    } else {
        put_be16(b + 0, 51u); put_be16(b + 2, 52u); put_be16(b + 4, 53u);
        put_be16(b + 6, 54u); put_be16(b + 8, 55u); put_be16(b + 10, 56u);
        put_be16(b + 12, 57u); b[14] = 58u; b[15] = 59u;
        b[16] = 1u; b[17] = 2u; put_be16(b + 18, 840u); b[20] = 3u; b[21] = 4u;
        put_world(b + 22, 100.25, 200.5, 300.75);
        put_vec3f(b + 46, 0.1f, 0.2f, 0.3f);
        put_be_double(b + 58, 1234.5);
        put_be16(b + 66, 60u); put_be16(b + 68, 61u); put_be16(b + 70, 62u); put_be16(b + 72, 63u);
        put_be32(b + 74, 64u);
    }
}

void make_linear_object_state_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = version >= 7 ? static_cast<uint16_t>(FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE)
                                         : static_cast<uint16_t>(FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE);
    make_pdu(p, version, FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE, length);
    p[3] = 9u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    if (version >= 7) {
        put_be16(b + 0, 151u); put_be16(b + 2, 152u); put_be16(b + 4, 153u);
        put_be16(b + 6, 154u); put_be16(b + 8, 155u); put_be16(b + 10, 156u);
        put_be16(b + 12, 157u); b[14] = 158u; b[15] = 2u;
        put_be16(b + 16, 159u); put_be16(b + 18, 160u); put_be16(b + 20, 161u); put_be16(b + 22, 162u);
        b[24] = 13u; b[25] = 14u; b[26] = 15u; b[27] = 16u;
        b[28] = 3u; b[29] = 4u; put_be16(b + 30, 0x0506u); put_be32(b + 32, 0x0708090Au);
        put_world(b + 36, 3000.25, 3001.5, 3002.75); put_vec3f(b + 60, 0.7f, 0.8f, 0.9f);
        put_be_float(b + 72, 45.5f); put_be_float(b + 76, 46.5f); put_be_float(b + 80, 47.5f); put_be_float(b + 84, 48.5f); put_be32(b + 88, 49u);
        b[92] = 5u; b[93] = 6u; put_be16(b + 94, 0x0B0Cu); put_be32(b + 96, 0x0D0E0F10u);
        put_world(b + 100, 4000.25, 4001.5, 4002.75); put_vec3f(b + 124, 1.0f, 1.1f, 1.2f);
        put_be_float(b + 136, 55.5f); put_be_float(b + 140, 56.5f); put_be_float(b + 144, 57.5f); put_be_float(b + 148, 58.5f); put_be32(b + 152, 59u);
    } else {
        put_be16(b + 0, 131u); put_be16(b + 2, 132u); put_be16(b + 4, 133u);
        put_be16(b + 6, 134u); put_be16(b + 8, 135u); put_be16(b + 10, 136u);
        put_be16(b + 12, 137u); b[14] = 138u; b[15] = 2u;
        put_be16(b + 16, 139u); put_be16(b + 18, 140u); put_be16(b + 20, 141u); put_be16(b + 22, 142u);
        b[24] = 9u; b[25] = 10u; put_be16(b + 26, 840u); b[28] = 11u; b[29] = 12u;
        b[30] = 1u; std::memcpy(b + 31, "\x01\x02\x03\x04\x05\x06", 6); put_world(b + 37, 1000.25, 1001.5, 1002.75); put_vec3f(b + 61, 0.1f, 0.2f, 0.3f); put_be16(b + 73, 25u); put_be16(b + 75, 26u); put_be16(b + 77, 27u); put_be16(b + 79, 28u); put_be32(b + 81, 29u);
        b[85] = 2u; std::memcpy(b + 86, "\x0A\x0B\x0C\x0D\x0E\x0F", 6); put_world(b + 92, 2000.25, 2001.5, 2002.75); put_vec3f(b + 116, 0.4f, 0.5f, 0.6f); put_be16(b + 128, 35u); put_be16(b + 130, 36u); put_be16(b + 132, 37u); put_be16(b + 134, 38u); put_be32(b + 136, 39u);
    }
}

void make_areal_object_state_pdu(uint8_t *p, uint8_t version = 6) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u);
    make_pdu(p, version, FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE, length);
    p[3] = 9u;
    uint8_t *b = p + FASTDIS_HEADER_SIZE;
    if (version >= 7) {
        put_be16(b + 0, 111u); put_be16(b + 2, 112u); put_be16(b + 4, 113u);
        put_be16(b + 6, 114u); put_be16(b + 8, 115u); put_be16(b + 10, 116u);
        put_be16(b + 12, 117u); b[14] = 118u; b[15] = 119u;
        b[16] = 6u; b[17] = 7u; put_be16(b + 18, 124u); b[20] = 8u; b[21] = 9u; b[22] = 10u; b[23] = 11u;
        put_be32(b + 24, 120u); put_be16(b + 28, 121u); put_be16(b + 30, 2u);
        put_be16(b + 32, 122u); put_be16(b + 34, 123u); put_be16(b + 36, 124u); put_be16(b + 38, 125u);
        put_world(b + 40, 7.0, 8.0, 9.0); put_world(b + 64, 10.0, 11.0, 12.0);
    } else {
        put_be16(b + 0, 91u); put_be16(b + 2, 92u); put_be16(b + 4, 93u);
        put_be16(b + 6, 94u); put_be16(b + 8, 95u); put_be16(b + 10, 96u);
        put_be16(b + 12, 97u); b[14] = 98u; b[15] = 99u;
        b[16] = 3u; b[17] = 4u; put_be16(b + 18, 225u); b[20] = 5u; b[21] = 6u; b[22] = 7u; b[23] = 8u;
        std::memcpy(b + 24, "\x01\x02\x03\x04\x05\x06", 6); put_be16(b + 30, 2u);
        put_be16(b + 32, 100u); put_be16(b + 34, 101u); put_be16(b + 36, 102u); put_be16(b + 38, 103u);
        put_world(b + 40, 1.0, 2.0, 3.0); put_world(b + 64, 4.0, 5.0, 6.0);
    }
}

bool nearf(float a, float b) {
    return std::fabs(a - b) < 0.0001f;
}

struct Counter {
    uint64_t count = 0;
    uint8_t last_type = 0;
    uint8_t last_force = 0;
};

int FASTDIS_CALL on_packet(const fastdis_header_t *header,
                           const uint8_t *data,
                           size_t size,
                           void *packet_user,
                           void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    Counter *counter = static_cast<Counter *>(callback_user);
    counter->count += 1;
    counter->last_type = header->pdu_type;
    return 0;
}

int FASTDIS_CALL on_entity_state(const fastdis_entity_state_prefix_t *entity_state,
                                 const uint8_t *data,
                                 size_t size,
                                 void *packet_user,
                                 void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    Counter *counter = static_cast<Counter *>(callback_user);
    counter->count += 1;
    counter->last_type = entity_state->header.pdu_type;
    counter->last_force = entity_state->force_id;
    return 0;
}

} // namespace

int main() {
    assert(fastdis_abi_version() == FASTDIS_ABI_VERSION);
    assert(fastdis_abi_epoch() == FASTDIS_ABI_EPOCH);
    assert(fastdis_abi_revision() == FASTDIS_ABI_REVISION);
    assert(FASTDIS_ABI_EPOCH == 0u);
    assert(FASTDIS_ABI_REVISION == 16u);
    assert(FASTDIS_ABI_VERSION == FASTDIS_ABI_REVISION);
    assert(FASTDIS_PDU_CATALOG_COUNT == 141u);

    const fastdis_pdu_catalog_entry_t *entity_state = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_ENTITY_STATE);
    assert(entity_state != nullptr);
    assert(entity_state->pdu_type == FASTDIS_ENTITY_STATE_PDU_TYPE);
    assert(entity_state->protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);
    assert(entity_state->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *entity_state_update = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_ENTITY_STATE_UPDATE);
    assert(entity_state_update != nullptr);
    assert(entity_state_update->pdu_type == FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE);
    assert(entity_state_update->protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);
    assert(entity_state_update->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *create_entity = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_CREATE_ENTITY);
    assert(create_entity != nullptr);
    assert(create_entity->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *remove_entity = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_REMOVE_ENTITY);
    assert(remove_entity != nullptr);
    assert(remove_entity->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *start_resume = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_START_RESUME);
    assert(start_resume != nullptr);
    assert(start_resume->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *stop_freeze = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_STOP_FREEZE);
    assert(stop_freeze != nullptr);
    assert(stop_freeze->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *acknowledge = fastdis_pdu_catalog_find(7, FASTDIS_ACKNOWLEDGE_PDU_TYPE);
    assert(acknowledge != nullptr);
    assert(acknowledge->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *service_request = fastdis_pdu_catalog_find(7, FASTDIS_SERVICE_REQUEST_PDU_TYPE);
    assert(service_request != nullptr);
    assert(service_request->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *resupply_offer = fastdis_pdu_catalog_find(7, FASTDIS_RESUPPLY_OFFER_PDU_TYPE);
    assert(resupply_offer != nullptr);
    assert(resupply_offer->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *resupply_received = fastdis_pdu_catalog_find(7, FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE);
    assert(resupply_received != nullptr);
    assert(resupply_received->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *resupply_cancel = fastdis_pdu_catalog_find(7, FASTDIS_RESUPPLY_CANCEL_PDU_TYPE);
    assert(resupply_cancel != nullptr);
    assert(resupply_cancel->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *repair_complete = fastdis_pdu_catalog_find(7, FASTDIS_REPAIR_COMPLETE_PDU_TYPE);
    assert(repair_complete != nullptr);
    assert(repair_complete->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *repair_response = fastdis_pdu_catalog_find(7, FASTDIS_REPAIR_RESPONSE_PDU_TYPE);
    assert(repair_response != nullptr);
    assert(repair_response->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *create_entity_reliable = fastdis_pdu_catalog_find(7, FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE);
    assert(create_entity_reliable != nullptr);
    assert(create_entity_reliable->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *remove_entity_reliable = fastdis_pdu_catalog_find(7, FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE);
    assert(remove_entity_reliable != nullptr);
    assert(remove_entity_reliable->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *start_resume_reliable = fastdis_pdu_catalog_find(7, FASTDIS_START_RESUME_RELIABLE_PDU_TYPE);
    assert(start_resume_reliable != nullptr);
    assert(start_resume_reliable->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *stop_freeze_reliable = fastdis_pdu_catalog_find(7, FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE);
    assert(stop_freeze_reliable != nullptr);
    assert(stop_freeze_reliable->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *acknowledge_reliable = fastdis_pdu_catalog_find(7, FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE);
    assert(acknowledge_reliable != nullptr);
    assert(acknowledge_reliable->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *minefield_state_entry = fastdis_pdu_catalog_find(7, FASTDIS_MINEFIELD_STATE_PDU_TYPE);
    assert(minefield_state_entry != nullptr);
    assert(minefield_state_entry->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *fire = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_FIRE);
    assert(fire != nullptr);
    assert(fire->protocol_family == 2u);
    assert(fire->has_body_decoder == 1u);

    const fastdis_pdu_catalog_entry_t *detonation = fastdis_pdu_catalog_find(7, FASTDIS_PDU_TYPE_DETONATION);
    assert(detonation != nullptr);
    assert(detonation->protocol_family == 2u);
    assert(detonation->has_body_decoder == 1u);
    assert(fastdis_pdu_catalog_find(7, 250u) == nullptr);

    uint8_t p[160];
    make_pdu(p, 7, 1);

    fastdis_header_t h;
    assert(fastdis_parse_header(p, 12, 0, &h) == FASTDIS_OK);
    assert(h.version == 7);
    assert(h.exercise_id == 3);
    assert(h.pdu_type == 1);
    assert(h.protocol_family == 1);
    assert(h.timestamp == 0x01020304u);
    assert(h.length == 12);
    assert(h.status == 0x80);
    assert(h.padding == 0);
    assert(fastdis_header_has_pdu_status(&h) == 1);
    assert(fastdis_header_pdu_status(&h) == 0x80u);
    assert(fastdis_header_padding_octet(&h) == 0u);
    assert(fastdis_header_legacy_padding(&h) == 0u);

    make_pdu(p, 6, 1);
    assert(fastdis_parse_header(p, 12, 0, &h) == FASTDIS_OK);
    assert(h.version == 6);
    assert(h.status == FASTDIS_HEADER_STATUS_UNAVAILABLE);
    assert(h.padding == 0x1234u);
    assert(fastdis_header_has_pdu_status(&h) == 0);
    assert(fastdis_header_pdu_status(&h) == 0u);
    assert(fastdis_header_padding_octet(&h) == 0u);
    assert(fastdis_header_legacy_padding(&h) == 0x1234u);
    assert(fastdis_header_has_pdu_status(nullptr) == 0);
    assert(fastdis_header_legacy_padding(nullptr) == 0u);

    make_pdu(p, 7, 1, 16);
    assert(fastdis_parse_header(p, 12, 0, &h) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_header(p, 12, FASTDIS_FLAG_ALLOW_TRUNCATED, &h) == FASTDIS_OK);

    uint8_t create_entity_pdu[64];
    uint8_t fire_pdu[128];
    uint8_t detonation_pdu[128];
    uint8_t remove_entity_pdu[64];
    uint8_t start_resume_pdu[64];
    uint8_t stop_freeze_pdu[64];
    uint8_t acknowledge_pdu[64];
    uint8_t create_entity_reliable_pdu[64];
    uint8_t remove_entity_reliable_pdu[64];
    uint8_t start_resume_reliable_pdu[64];
    uint8_t stop_freeze_reliable_pdu[64];
    uint8_t acknowledge_reliable_pdu[64];
    uint8_t record_reliable_pdu[64];
    uint8_t set_record_reliable_pdu[64];
    uint8_t record_query_reliable_pdu[64];
    uint8_t service_request_pdu[64];
    uint8_t resupply_offer_pdu[64];
    uint8_t resupply_received_pdu[64];
    uint8_t resupply_cancel_pdu[64];
    uint8_t repair_complete_pdu[64];
    uint8_t repair_response_pdu[64];
    uint8_t designator_pdu[96];
    uint8_t transmitter6_pdu[160];
    uint8_t transmitter7_pdu[160];
    uint8_t signal_pdu[64];
    uint8_t receiver_pdu[64];
    uint8_t iff_pdu[64];
    uint8_t intercom_signal_pdu[64];
    uint8_t intercom_control_pdu[64];
    uint8_t other_pdu[32];
    uint8_t aggregate_state_pdu[160];
    uint8_t is_group_of_pdu[64];
    uint8_t transfer_control_request_pdu[64];
    uint8_t transfer_ownership_pdu[64];
    uint8_t is_part_of_pdu[64];
    make_create_entity_pdu(create_entity_pdu, 7);
    make_fire_pdu(fire_pdu, 7);
    make_detonation_pdu(detonation_pdu, 6);
    make_remove_entity_pdu(remove_entity_pdu, 6);
    make_start_resume_pdu(start_resume_pdu, 7);
    make_stop_freeze_pdu(stop_freeze_pdu, 6);
    make_acknowledge_pdu(acknowledge_pdu, 7);
    make_create_entity_reliable_pdu(create_entity_reliable_pdu, 7);
    make_remove_entity_reliable_pdu(remove_entity_reliable_pdu, 6);
    make_start_resume_reliable_pdu(start_resume_reliable_pdu, 7);
    make_stop_freeze_reliable_pdu(stop_freeze_reliable_pdu, 6);
    make_acknowledge_reliable_pdu(acknowledge_reliable_pdu, 7);
    make_record_reliable_pdu(record_reliable_pdu, 7);
    make_set_record_reliable_pdu(set_record_reliable_pdu, 6);
    make_record_query_reliable_pdu(record_query_reliable_pdu, 7);
    make_service_request_pdu(service_request_pdu, 7);
    make_resupply_offer_pdu(resupply_offer_pdu, 6);
    make_resupply_received_pdu(resupply_received_pdu, 7);
    make_resupply_cancel_pdu(resupply_cancel_pdu, 7);
    make_repair_complete_pdu(repair_complete_pdu, 6);
    make_repair_response_pdu(repair_response_pdu, 7);
    make_designator_pdu(designator_pdu, 7);
    make_transmitter_pdu(transmitter6_pdu, 6);
    make_transmitter_pdu(transmitter7_pdu, 7);
    make_signal_pdu(signal_pdu, 6);
    make_receiver_pdu(receiver_pdu, 7);
    make_iff_atc_navaids_layer1_pdu(iff_pdu, 7);
    make_intercom_signal_pdu(intercom_signal_pdu, 7);
    make_intercom_control_pdu(intercom_control_pdu, 7);
    make_other_pdu(other_pdu, 6);
    make_aggregate_state_pdu(aggregate_state_pdu, 7);
    make_is_group_of_pdu(is_group_of_pdu, 6);
    make_transfer_control_request_pdu(transfer_control_request_pdu, 6);
    make_transfer_ownership_pdu(transfer_ownership_pdu, 7);
    make_is_part_of_pdu(is_part_of_pdu, 7);

    fastdis_simulation_management_request_t create_request;
    assert(fastdis_parse_create_entity(create_entity_pdu, FASTDIS_CREATE_ENTITY_FIXED_SIZE, 0, &create_request) == FASTDIS_OK);
    assert(create_request.header.pdu_type == FASTDIS_CREATE_ENTITY_PDU_TYPE);
    assert(create_request.originating_entity_id.site == 0x1111);
    assert(create_request.receiving_entity_id.entity == 0x6666);
    assert(create_request.request_id == 0xA0B0C0D0u);

    fastdis_fire_t fire_event;
    assert(fastdis_parse_fire(fire_pdu, FASTDIS_FIRE_FIXED_SIZE, 0, &fire_event) == FASTDIS_OK);
    assert(fire_event.header.pdu_type == FASTDIS_FIRE_PDU_TYPE);
    assert(fire_event.firing_entity_id.entity == 0x0003);
    assert(fire_event.target_entity_id.entity == 0x0006);
    assert(fire_event.munition_entity_id.entity == 0x0009);
    assert(fire_event.event_id.event_number == 0x000C);
    assert(fire_event.fire_mission_index == 99u);
    assert(fire_event.munition_descriptor.warhead == 101u);
    assert(nearf(fire_event.velocity.y, 2.5f));
    assert(std::fabs(fire_event.range_to_target - 4444.5f) < 0.0001f);

    fastdis_detonation_t detonation_event;
    assert(fastdis_parse_detonation(detonation_pdu, FASTDIS_DETONATION_FIXED_SIZE + 16u, 0, &detonation_event) == FASTDIS_OK);
    assert(detonation_event.header.version == 6u);
    assert(detonation_event.exploding_entity_id.entity == 0x0009);
    assert(detonation_event.event_id.event_number == 0x000C);
    assert(nearf(detonation_event.velocity.z, 33.0f));
    assert(detonation_event.munition_descriptor.rate == 600u);
    assert(nearf(detonation_event.location_in_entity_coordinates.x, -4.0f));
    assert(detonation_event.detonation_result == 17u);
    assert(detonation_event.variable_parameter_count == 1u);

    fastdis_simulation_management_request_t remove_request;
    assert(fastdis_parse_remove_entity(remove_entity_pdu, FASTDIS_REMOVE_ENTITY_FIXED_SIZE, 0, &remove_request) == FASTDIS_OK);
    assert(remove_request.header.version == 6u);
    assert(remove_request.originating_entity_id.application == 0x2222);
    assert(remove_request.request_id == 0x0BADF00Du);

    fastdis_start_resume_t start_request;
    assert(fastdis_parse_start_resume(start_resume_pdu, FASTDIS_START_RESUME_FIXED_SIZE, 0, &start_request) == FASTDIS_OK);
    assert(start_request.real_world_time.hour == 7u);
    assert(start_request.real_world_time.time_past_hour == 123456u);
    assert(start_request.simulation_time.hour == 9u);
    assert(start_request.simulation_time.time_past_hour == 654321u);
    assert(start_request.request_id == 0x01020304u);

    fastdis_stop_freeze_t stop_request;
    assert(fastdis_parse_stop_freeze(stop_freeze_pdu, FASTDIS_STOP_FREEZE_FIXED_SIZE, 0, &stop_request) == FASTDIS_OK);
    assert(stop_request.header.version == 6u);
    assert(stop_request.real_world_time.hour == 5u);
    assert(stop_request.real_world_time.time_past_hour == 7654321u);
    assert(stop_request.reason == 3u);
    assert(stop_request.frozen_behavior == 4u);
    assert(stop_request.padding1 == 0xABCDu);
    assert(stop_request.request_id == 0x0F1E2D3Cu);

    fastdis_acknowledge_t acknowledge_request;
    assert(fastdis_parse_acknowledge(acknowledge_pdu, FASTDIS_ACKNOWLEDGE_FIXED_SIZE, 0, &acknowledge_request) == FASTDIS_OK);
    assert(acknowledge_request.header.version == 7u);
    assert(acknowledge_request.acknowledge_flag == 0x1234u);
    assert(acknowledge_request.response_flag == 0x5678u);
    assert(acknowledge_request.request_id == 0xCAFEBABEu);

    fastdis_other_pdu_t other_event;
    assert(fastdis_parse_other_pdu(other_pdu, FASTDIS_OTHER_FIXED_SIZE + 4u, 0, &other_event) == FASTDIS_OK);
    assert(other_event.header.version == 6u);
    assert(other_event.header.protocol_family == 0u);
    assert(other_event.opaque_payload.bytes_size == 4u);
    assert(other_event.opaque_payload.bytes[0] == 0x4Fu);

    fastdis_aggregate_state_t aggregate_state_event;
    assert(fastdis_parse_aggregate_state(aggregate_state_pdu, FASTDIS_AGGREGATE_STATE_FIXED_SIZE + 6u, 0, &aggregate_state_event) == FASTDIS_OK);
    assert(aggregate_state_event.header.version == 7u);
    assert(aggregate_state_event.aggregate_id.entity == 3u);
    assert(aggregate_state_event.force_id == 4u);
    assert(aggregate_state_event.aggregate_state == 5u);
    assert(aggregate_state_event.aggregate_type.country == 840u);
    assert(aggregate_state_event.formation == 0x11223344u);
    assert(aggregate_state_event.aggregate_marking_character_set == 1u);
    assert(std::strncmp(reinterpret_cast<const char *>(aggregate_state_event.aggregate_marking), "AGGREGATE-ALPHA", 15) == 0);
    assert(nearf(aggregate_state_event.dimensions.y, 2.0f));
    assert(nearf(aggregate_state_event.orientation.theta, 0.2f));
    assert(std::fabs(aggregate_state_event.center_of_mass.z - 30.0) < 0.0001);
    assert(nearf(aggregate_state_event.velocity.x, 4.0f));
    assert(aggregate_state_event.number_of_dis_aggregates == 7u);
    assert(aggregate_state_event.number_of_dis_entities == 8u);
    assert(aggregate_state_event.number_of_silent_aggregate_types == 9u);
    assert(aggregate_state_event.number_of_silent_entity_types == 10u);
    assert(aggregate_state_event.aggregate_records.bytes_size == 6u);
    assert(aggregate_state_event.aggregate_records.bytes[0] == 0xA1u);

    fastdis_is_group_of_t is_group_of_event;
    assert(fastdis_parse_is_group_of(is_group_of_pdu, FASTDIS_IS_GROUP_OF_FIXED_SIZE + 4u, 0, &is_group_of_event) == FASTDIS_OK);
    assert(is_group_of_event.header.version == 6u);
    assert(is_group_of_event.group_entity_id.entity == 3u);
    assert(is_group_of_event.grouped_entity_category == 0x21u);
    assert(is_group_of_event.number_of_grouped_entities == 0x02u);
    assert(is_group_of_event.pad2 == 0x10203040u);
    assert(std::fabs(is_group_of_event.latitude - 41.25) < 0.0001);
    assert(std::fabs(is_group_of_event.longitude + 93.5) < 0.0001);
    assert(is_group_of_event.grouped_entity_descriptions.bytes_size == 4u);
    assert(is_group_of_event.grouped_entity_descriptions.bytes[0] == 0xB1u);

    fastdis_transfer_control_request_t transfer_control_request_event;
    assert(fastdis_parse_transfer_control_request(transfer_control_request_pdu, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + 4u, 0, &transfer_control_request_event) == FASTDIS_OK);
    assert(transfer_control_request_event.header.version == 6u);
    assert(transfer_control_request_event.originating_entity_id.entity == 3u);
    assert(transfer_control_request_event.receiving_entity_id.site == 4u);
    assert(transfer_control_request_event.request_id == 0x11223344u);
    assert(transfer_control_request_event.required_reliability_service == 0x07u);
    assert(transfer_control_request_event.transfer_type == 0x08u);
    assert(transfer_control_request_event.transfer_entity_id.entity == 9u);
    assert(transfer_control_request_event.number_of_record_sets == 0x02u);
    assert(transfer_control_request_event.record_sets.bytes_size == 4u);
    assert(transfer_control_request_event.record_sets.bytes[0] == 0xC1u);

    fastdis_transfer_ownership_t transfer_ownership_event;
    assert(fastdis_parse_transfer_ownership(transfer_ownership_pdu, FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + 4u, 0, &transfer_ownership_event) == FASTDIS_OK);
    assert(transfer_ownership_event.header.version == 7u);
    assert(transfer_ownership_event.originating_entity_id.site == 10u);
    assert(transfer_ownership_event.receiving_entity_id.entity == 15u);
    assert(transfer_ownership_event.request_id == 0x55667788u);
    assert(transfer_ownership_event.required_reliability_service == 0x09u);
    assert(transfer_ownership_event.transfer_type == 0x0Au);
    assert(transfer_ownership_event.transfer_entity_id.application == 17u);
    assert(transfer_ownership_event.number_of_record_sets == 0x03u);
    assert(transfer_ownership_event.record_sets.bytes_size == 4u);
    assert(transfer_ownership_event.record_sets.bytes[0] == 0xD1u);

    fastdis_is_part_of_t is_part_of_event;
    assert(fastdis_parse_is_part_of(is_part_of_pdu, FASTDIS_IS_PART_OF_FIXED_SIZE, 0, &is_part_of_event) == FASTDIS_OK);
    assert(is_part_of_event.header.version == 7u);
    assert(is_part_of_event.originating_entity_id.entity == 3u);
    assert(is_part_of_event.receiving_entity_id.site == 4u);
    assert(is_part_of_event.relationship.nature == 0x1112u);
    assert(is_part_of_event.relationship.position == 0x1314u);
    assert(nearf(is_part_of_event.part_location.y, 8.0f));
    assert(is_part_of_event.named_location.station_name == 0x2122u);
   assert(is_part_of_event.named_location.station_number == 0x2324u);
    assert(is_part_of_event.part_entity_type.country == 225u);
    assert(is_part_of_event.part_entity_type.extra == 7u);

    std::array<uint8_t, 104> minefield_state6{};
    make_minefield_state_pdu(minefield_state6.data(), 6);
    fastdis_minefield_state_t minefield_state_event{};
    assert(fastdis_parse_minefield_state(minefield_state6.data(), minefield_state6.size(), 0u, &minefield_state_event) == FASTDIS_OK);
    assert(minefield_state_event.header.version == 6u);
    assert(minefield_state_event.minefield_id.entity == 223u);
    assert(minefield_state_event.minefield_sequence == 224u);
    assert(minefield_state_event.force_id == 225u);
    assert(minefield_state_event.number_of_perimeter_points == 2u);
    assert(minefield_state_event.minefield_type.country == 840u);
    assert(minefield_state_event.number_of_mine_types == 2u);
    assert(nearf(minefield_state_event.minefield_orientation.theta, 0.2f));
    assert(minefield_state_event.appearance == 226u);
    assert(minefield_state_event.protocol_mode == 227u);
    assert(minefield_state_event.perimeter_points.bytes_size == 16u);
    assert(minefield_state_event.mine_types.bytes_size == 16u);

    std::array<uint8_t, 60> minefield_query6{};
    make_minefield_query_pdu(minefield_query6.data(), 6);
    fastdis_minefield_query_t minefield_query_event{};
    assert(fastdis_parse_minefield_query(minefield_query6.data(), minefield_query6.size(), 0u, &minefield_query_event) == FASTDIS_OK);
    assert(minefield_query_event.header.version == 6u);
    assert(minefield_query_event.minefield_id.entity == 203u);
    assert(minefield_query_event.requesting_entity_id.entity == 206u);
    assert(minefield_query_event.request_id == 207u);
    assert(minefield_query_event.number_of_perimeter_points == 2u);
    assert(minefield_query_event.number_of_sensor_types == 2u);
    assert(minefield_query_event.data_filter == 0x01020304u);
    assert(minefield_query_event.requested_mine_type.country == 225u);
    assert(minefield_query_event.requested_perimeter_points.bytes_size == 16u);
    assert(minefield_query_event.sensor_types.bytes_size == 4u);

    std::array<uint8_t, 73> minefield_data7{};
    make_minefield_data_pdu(minefield_data7.data(), 7);
    fastdis_minefield_data_t minefield_data_event{};
    assert(fastdis_parse_minefield_data(minefield_data7.data(), minefield_data7.size(), 0u, &minefield_data_event) == FASTDIS_OK);
    assert(minefield_data_event.header.version == 7u);
    assert(minefield_data_event.minefield_id.entity == 253u);
    assert(minefield_data_event.requesting_entity_id.entity == 256u);
    assert(minefield_data_event.minefield_sequence_number == 257u);
    assert(minefield_data_event.request_id == 200u);
    assert(minefield_data_event.pdu_sequence_number == 3u);
    assert(minefield_data_event.number_of_pdus == 2u);
    assert(minefield_data_event.number_of_mines_in_this_pdu == 2u);
    assert(minefield_data_event.number_of_sensor_types == 2u);
    assert(minefield_data_event.data_filter == 0x01020304u);
    assert(minefield_data_event.mine_type.country == 225u);
    assert(minefield_data_event.sensor_types.bytes_size == 4u);
    assert(minefield_data_event.mine_locations.bytes_size == 24u);

    std::array<uint8_t, 42> minefield_nack6{};
    make_minefield_response_nack_pdu(minefield_nack6.data(), 6);
    fastdis_minefield_response_nack_t minefield_nack_event{};
    assert(fastdis_parse_minefield_response_nack(minefield_nack6.data(), minefield_nack6.size(), 0u, &minefield_nack_event) == FASTDIS_OK);
    assert(minefield_nack_event.header.version == 6u);
    assert(minefield_nack_event.minefield_id.entity == 183u);
    assert(minefield_nack_event.requesting_entity_id.entity == 186u);
    assert(minefield_nack_event.request_id == 187u);
    assert(minefield_nack_event.number_of_missing_pdus == 2u);
    assert(minefield_nack_event.missing_pdu_sequence_numbers.bytes_size == 16u);

    std::array<uint8_t, FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE + 10u> environmental_process6{};
    make_environmental_process_pdu(environmental_process6.data(), 6);
    fastdis_environmental_process_t environmental_process_event{};
    assert(fastdis_parse_environmental_process(environmental_process6.data(), environmental_process6.size(), 0u, &environmental_process_event) == FASTDIS_OK);
    assert(environmental_process_event.header.version == 6u);
    assert(environmental_process_event.environmental_process_id.entity == 213u);
    assert(environmental_process_event.environment_type.country == 840u);
    assert(environmental_process_event.model_type == 15u);
    assert(environmental_process_event.environment_status == 16u);
    assert(environmental_process_event.number_of_environment_records == 2u);
    assert(environmental_process_event.sequence_number == 0x1718u);
    assert(environmental_process_event.environment_records.bytes_size == 10u);

    std::array<uint8_t, FASTDIS_GRIDDED_DATA_FIXED_SIZE + 10u> gridded_data7{};
    make_gridded_data_pdu(gridded_data7.data(), 7);
    fastdis_gridded_data_t gridded_data_event{};
    assert(fastdis_parse_gridded_data(gridded_data7.data(), gridded_data7.size(), 0u, &gridded_data_event) == FASTDIS_OK);
    assert(gridded_data_event.header.version == 7u);
    assert(gridded_data_event.environmental_simulation_application_id.entity == 263u);
    assert(gridded_data_event.field_number == 264u);
    assert(gridded_data_event.coordinate_system == 267u);
    assert(gridded_data_event.number_of_grid_axes == 3u);
    assert(gridded_data_event.constant_grid == 1u);
    assert(gridded_data_event.environment_type.country == 840u);
    assert(nearf(gridded_data_event.orientation.theta, 0.8f));
    assert(gridded_data_event.sample_time == 0x0102030405060708ull);
    assert(gridded_data_event.total_values == 269u);
    assert(gridded_data_event.vector_dimension == 4u);
    assert(gridded_data_event.padding1 == 270u);
    assert(gridded_data_event.grid_data.bytes_size == 10u);

    std::array<uint8_t, FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE> point_object_state6{};
    make_point_object_state_pdu(point_object_state6.data(), 6);
    fastdis_point_object_state_t point_object_state_event6{};
    assert(fastdis_parse_point_object_state(point_object_state6.data(), point_object_state6.size(), 0u, &point_object_state_event6) == FASTDIS_OK);
    assert(point_object_state_event6.header.version == 6u);
    assert(point_object_state_event6.object_id.entity == 53u);
    assert(point_object_state_event6.object_type.domain == 2u);
    assert(point_object_state_event6.object_type.kind == 1u);
    assert(point_object_state_event6.object_type.country == 840u);
    assert(nearf(point_object_state_event6.object_orientation.phi, 0.3f));
    assert(std::fabs(point_object_state_event6.object_appearance - 1234.5) < 0.0001);
    assert(point_object_state_event6.requester_id.site == 60u);
    assert(point_object_state_event6.receiving_id.application == 63u);
    assert(point_object_state_event6.pad2 == 64u);

    std::array<uint8_t, FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE> point_object_state7{};
    make_point_object_state_pdu(point_object_state7.data(), 7);
    fastdis_point_object_state_t point_object_state_event7{};
    assert(fastdis_parse_point_object_state(point_object_state7.data(), point_object_state7.size(), 0u, &point_object_state_event7) == FASTDIS_OK);
    assert(point_object_state_event7.object_id.entity == 73u);
    assert(point_object_state_event7.object_type.domain == 4u);
    assert(point_object_state_event7.object_type.kind == 5u);
    assert(point_object_state_event7.object_type.country == 0u);
    assert(std::fabs(point_object_state_event7.object_location.z - 600.75) < 0.0001);

    std::array<uint8_t, FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE> linear_object_state6{};
    make_linear_object_state_pdu(linear_object_state6.data(), 6);
    fastdis_linear_object_state_t linear_object_state_event6{};
    assert(fastdis_parse_linear_object_state(linear_object_state6.data(), linear_object_state6.size(), 0u, &linear_object_state_event6) == FASTDIS_OK);
    assert(linear_object_state_event6.header.version == 6u);
    assert(linear_object_state_event6.object_id.entity == 133u);
    assert(linear_object_state_event6.number_of_segments == 2u);
    assert(linear_object_state_event6.object_type.domain == 10u);
    assert(linear_object_state_event6.object_type.kind == 9u);
    assert(linear_object_state_event6.linear_segment_parameters.bytes_size == 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE);

    std::array<uint8_t, FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE> linear_object_state7{};
    make_linear_object_state_pdu(linear_object_state7.data(), 7);
    fastdis_linear_object_state_t linear_object_state_event7{};
    assert(fastdis_parse_linear_object_state(linear_object_state7.data(), linear_object_state7.size(), 0u, &linear_object_state_event7) == FASTDIS_OK);
    assert(linear_object_state_event7.header.version == 7u);
    assert(linear_object_state_event7.object_id.entity == 153u);
    assert(linear_object_state_event7.object_type.domain == 13u);
    assert(linear_object_state_event7.object_type.kind == 14u);
    assert(linear_object_state_event7.linear_segment_parameters.bytes_size == 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE);

    std::array<uint8_t, FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u> areal_object_state6{};
    make_areal_object_state_pdu(areal_object_state6.data(), 6);
    fastdis_areal_object_state_t areal_object_state_event6{};
    assert(fastdis_parse_areal_object_state(areal_object_state6.data(), areal_object_state6.size(), 0u, &areal_object_state_event6) == FASTDIS_OK);
    assert(areal_object_state_event6.header.version == 6u);
    assert(areal_object_state_event6.object_id.entity == 93u);
    assert(areal_object_state_event6.object_type.country == 225u);
    assert(areal_object_state_event6.object_appearance.bytes_size == 6u);
    assert(areal_object_state_event6.number_of_points == 2u);
    assert(areal_object_state_event6.requester_id.site == 100u);
    assert(areal_object_state_event6.receiving_id.application == 103u);
    assert(areal_object_state_event6.object_locations.bytes_size == 48u);

    std::array<uint8_t, FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u> areal_object_state7{};
    make_areal_object_state_pdu(areal_object_state7.data(), 7);
    fastdis_areal_object_state_t areal_object_state_event7{};
    assert(fastdis_parse_areal_object_state(areal_object_state7.data(), areal_object_state7.size(), 0u, &areal_object_state_event7) == FASTDIS_OK);
    assert(areal_object_state_event7.header.version == 7u);
    assert(areal_object_state_event7.object_id.entity == 113u);
    assert(areal_object_state_event7.object_type.country == 124u);
    assert(areal_object_state_event7.object_appearance.bytes_size == 6u);
    assert(areal_object_state_event7.number_of_points == 2u);
    assert(areal_object_state_event7.requester_id.site == 122u);
    assert(areal_object_state_event7.receiving_id.application == 125u);
    assert(areal_object_state_event7.object_locations.bytes_size == 48u);

    fastdis_service_request_t service_request_request;
    assert(fastdis_parse_service_request(service_request_pdu, FASTDIS_SERVICE_REQUEST_FIXED_SIZE + 8u, 0, &service_request_request) == FASTDIS_OK);
    assert(service_request_request.header.version == 7u);
    assert(service_request_request.service_type_requested == 7u);
    assert(service_request_request.number_of_supply_types == 2u);
    assert(service_request_request.service_request_padding == 0x4041u);
    assert(service_request_request.supplies.count == 2u);
    assert(service_request_request.supplies.bytes_size == 8u);
    assert(service_request_request.supplies.bytes[0] == 0x41u);

    fastdis_resupply_offer_t resupply_offer_request;
    assert(fastdis_parse_resupply_offer(resupply_offer_pdu, FASTDIS_RESUPPLY_OFFER_FIXED_SIZE + 8u, 0, &resupply_offer_request) == FASTDIS_OK);
    assert(resupply_offer_request.header.version == 6u);
    assert(resupply_offer_request.number_of_supply_types == 2u);
    assert(resupply_offer_request.padding_bytes[0] == 0x11u);
    assert(resupply_offer_request.padding_bytes[1] == 0x12u);
    assert(resupply_offer_request.padding_bytes[2] == 0x13u);
    assert(resupply_offer_request.supplies.count == 2u);
    assert(resupply_offer_request.supplies.bytes[0] == 0x51u);

    fastdis_resupply_received_t resupply_received_request;
    assert(fastdis_parse_resupply_received(resupply_received_pdu, FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE + 8u, 0, &resupply_received_request) == FASTDIS_OK);
    assert(resupply_received_request.header.version == 7u);
    assert(resupply_received_request.number_of_supply_types == 2u);
    assert(resupply_received_request.padding1 == 0x6162u);
    assert(resupply_received_request.padding2 == 0x63u);
    assert(resupply_received_request.supplies.count == 2u);
    assert(resupply_received_request.supplies.bytes[0] == 0x61u);

    fastdis_resupply_cancel_t resupply_cancel_request;
    assert(fastdis_parse_resupply_cancel(resupply_cancel_pdu, FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE, 0, &resupply_cancel_request) == FASTDIS_OK);
    assert(resupply_cancel_request.header.version == 7u);
    assert(resupply_cancel_request.receiving_entity_id.site == 0x0001u);
    assert(resupply_cancel_request.supplying_entity_id.entity == 0x0006u);

    fastdis_repair_complete_t repair_complete_request;
    assert(fastdis_parse_repair_complete(repair_complete_pdu, FASTDIS_REPAIR_COMPLETE_FIXED_SIZE, 0, &repair_complete_request) == FASTDIS_OK);
    assert(repair_complete_request.header.version == 6u);
    assert(repair_complete_request.repair == 0x7172u);
    assert(repair_complete_request.padding2 == 0x7374u);

    fastdis_repair_response_t repair_response_request;
    assert(fastdis_parse_repair_response(repair_response_pdu, FASTDIS_REPAIR_RESPONSE_FIXED_SIZE, 0, &repair_response_request) == FASTDIS_OK);
    assert(repair_response_request.header.version == 7u);
    assert(repair_response_request.repair_result == 0x75u);
    assert(repair_response_request.padding1 == 0x7677u);
    assert(repair_response_request.padding2 == 0x78u);

    fastdis_designator_t designator_request;
    assert(fastdis_parse_designator(designator_pdu, FASTDIS_DESIGNATOR_FIXED_SIZE, 0, &designator_request) == FASTDIS_OK);
    assert(designator_request.header.protocol_family == 6u);
    assert(designator_request.designating_entity_id.entity == 0x0003u);
    assert(designator_request.code_name == 0x1234u);
    assert(designator_request.designated_entity_id.entity == 0x0006u);
    assert(designator_request.designator_code == 0x2345u);
    assert(nearf(designator_request.designator_power, 12.5f));
    assert(designator_request.dead_reckoning_algorithm == 4u);
    assert(nearf(designator_request.entity_linear_acceleration.z, 7.5f));

    fastdis_transmitter_t transmitter6_request;
    assert(fastdis_parse_transmitter(transmitter6_pdu, FASTDIS_TRANSMITTER_FIXED_SIZE + 3u, 0, &transmitter6_request) == FASTDIS_OK);
    assert(transmitter6_request.header.version == 6u);
    assert(transmitter6_request.entity_id.entity == 0x0003u);
    assert(transmitter6_request.radio_id == 0x1212u);
    assert(transmitter6_request.radio_entity_type.nomenclature == 0x0708u);
    assert(transmitter6_request.modulation_parameter_count == 3u);
    assert(transmitter6_request.modulation_parameters.bytes_size == 3u);

    fastdis_transmitter_t transmitter7_request;
    assert(fastdis_parse_transmitter(transmitter7_pdu, FASTDIS_TRANSMITTER_FIXED_SIZE + 24u, 0, &transmitter7_request) == FASTDIS_OK);
    assert(transmitter7_request.header.version == 7u);
    assert(transmitter7_request.entity_type.country == 840u);
    assert(transmitter7_request.variable_transmitter_parameter_count == 2u);
    assert(transmitter7_request.frequency == 225000u);
    assert(nearf(transmitter7_request.transmit_frequency_bandwidth, 50.5f));
    assert(transmitter7_request.modulation_parameters.bytes_size == 12u);
    assert(transmitter7_request.antenna_patterns.bytes_size == 12u);

    fastdis_signal_t signal_request;
    assert(fastdis_parse_signal(signal_pdu, FASTDIS_SIGNAL_DIS6_FIXED_SIZE + 4u, 0, &signal_request) == FASTDIS_OK);
    assert(signal_request.header.version == 6u);
    assert(signal_request.entity_id.entity == 0x0003u);
    assert(signal_request.radio_id == 0x1111u);
    assert(signal_request.encoding_scheme == 0x2222u);
    assert(signal_request.tdl_type == 0x3333u);
    assert(signal_request.sample_rate == 48000u);
    assert(signal_request.data_length == 4u);
    assert(signal_request.data.bytes_size == 4u);
    assert(signal_request.data.bytes[0] == 0x41u);

    fastdis_receiver_t receiver_request;
    assert(fastdis_parse_receiver(receiver_pdu, FASTDIS_RECEIVER_DIS7_FIXED_SIZE, 0, &receiver_request) == FASTDIS_OK);
    assert(receiver_request.header.version == 7u);
    assert(receiver_request.entity_id.entity == 0u);
    assert(receiver_request.receiver_state == 0x2222u);
    assert(receiver_request.padding1 == 0x3333u);
    assert(nearf(receiver_request.received_power, 12.5f));
    assert(receiver_request.transmitter_entity_id.entity == 0x0006u);
    assert(receiver_request.transmitter_radio_id == 0x4444u);

    fastdis_iff_atc_navaids_layer1_t iff_request;
    assert(fastdis_parse_iff_atc_navaids_layer1(iff_pdu, FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE, 0, &iff_request) == FASTDIS_OK);
    assert(iff_request.header.protocol_family == 6u);
    assert(iff_request.emitting_entity_id.entity == 0x0003u);
    assert(iff_request.event_id.event_number == 0x0006u);
    assert(nearf(iff_request.location.y, 2.0f));
    assert(iff_request.system_id.system_name == 0x2222u);
    assert(iff_request.fundamental_parameters.parameter6 == 10u);

    fastdis_intercom_signal_t intercom_signal_request;
    assert(fastdis_parse_intercom_signal(intercom_signal_pdu, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4u, 0, &intercom_signal_request) == FASTDIS_OK);
    assert(intercom_signal_request.header.version == 7u);
    assert(intercom_signal_request.entity_id.entity == 0x0003u);
    assert(intercom_signal_request.communications_device_id == 0x1212u);
    assert(intercom_signal_request.encoding_scheme == 0x2222u);
    assert(intercom_signal_request.tdl_type == 0x3333u);
    assert(intercom_signal_request.sample_rate == 32000u);
    assert(intercom_signal_request.data.bytes_size == 4u);
    assert(intercom_signal_request.data.bytes[0] == 0x51u);

    fastdis_intercom_control_t intercom_control_request;
    assert(fastdis_parse_intercom_control(intercom_control_pdu, FASTDIS_INTERCOM_CONTROL_FIXED_SIZE + 4u, 0, &intercom_control_request) == FASTDIS_OK);
    assert(intercom_control_request.header.protocol_family == 4u);
    assert(intercom_control_request.control_type == 0x11u);
    assert(intercom_control_request.source_entity_id.entity == 0x0003u);
    assert(intercom_control_request.command == 0x77u);
    assert(intercom_control_request.master_communications_device_id == 0x8888u);
    assert(intercom_control_request.intercom_parameters.bytes_size == 4u);
    assert(intercom_control_request.intercom_parameters.bytes[0] == 0x61u);

    uint8_t attribute_pdu[FASTDIS_ATTRIBUTE_FIXED_SIZE + 4u];
    make_attribute_pdu(attribute_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_attribute_t attribute_request;
    assert(fastdis_parse_attribute(attribute_pdu, sizeof(attribute_pdu), 0, &attribute_request) == FASTDIS_OK);
    assert(attribute_request.header.protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);
    assert(attribute_request.originating_simulation_address.site == 0x0101u);
    assert(attribute_request.originating_simulation_address.application == 0x0202u);
    assert(attribute_request.padding1 == 0x11223344);
    assert(attribute_request.padding2 == 0x5566);
    assert(attribute_request.attribute_record_pdu_type == 67u);
    assert(attribute_request.attribute_record_protocol_version == 7u);
    assert(attribute_request.master_attribute_record_type == 0x778899AAu);
    assert(attribute_request.action_code == 0x12u);
    assert(attribute_request.padding3 == 0x34);
    assert(attribute_request.number_attribute_record_set == 1u);
    assert(attribute_request.attribute_record_sets.count == 1u);
    assert(attribute_request.attribute_record_sets.bytes_size == 4u);

    uint8_t directed_energy_fire_pdu[FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE + 4u];
    make_directed_energy_fire_pdu(directed_energy_fire_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_directed_energy_fire_t directed_energy_fire_request;
    assert(fastdis_parse_directed_energy_fire(directed_energy_fire_pdu, sizeof(directed_energy_fire_pdu), 0, &directed_energy_fire_request) == FASTDIS_OK);
    assert(directed_energy_fire_request.header.protocol_family == 2u);
    assert(directed_energy_fire_request.firing_entity_id.entity == 0x0003u);
    assert(directed_energy_fire_request.target_entity_id.entity == 0x0006u);
    assert(directed_energy_fire_request.munition_type.country == 225u);
    assert(directed_energy_fire_request.shot_start_time.hour == 7u);
    assert(directed_energy_fire_request.shot_start_time.time_past_hour == 123456u);
    assert(nearf(directed_energy_fire_request.commulative_shot_time, 1.25f));
    assert(nearf(directed_energy_fire_request.aperture_emitter_location.z, 4.5f));
    assert(nearf(directed_energy_fire_request.aperture_diameter, 5.5f));
    assert(nearf(directed_energy_fire_request.wavelength, 6.5f));
    assert(nearf(directed_energy_fire_request.peak_irradiance, 7.5f));
    assert(nearf(directed_energy_fire_request.pulse_repetition_frequency, 8.5f));
    assert(directed_energy_fire_request.pulse_width == 9012);
    assert(directed_energy_fire_request.flags == 0x10203040);
    assert(directed_energy_fire_request.pulse_shape == 0x11);
    assert(directed_energy_fire_request.padding1 == 0x22u);
    assert(directed_energy_fire_request.padding2 == 0x33445566u);
    assert(directed_energy_fire_request.padding3 == 0x7788u);
    assert(directed_energy_fire_request.number_of_de_records == 1u);
    assert(directed_energy_fire_request.de_records.count == 1u);
    assert(directed_energy_fire_request.de_records.bytes_size == 4u);

    uint8_t entity_damage_status_pdu[FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE + 4u];
    make_entity_damage_status_pdu(entity_damage_status_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_entity_damage_status_t entity_damage_status_request;
    assert(fastdis_parse_entity_damage_status(entity_damage_status_pdu, sizeof(entity_damage_status_pdu), 0, &entity_damage_status_request) == FASTDIS_OK);
    assert(entity_damage_status_request.header.protocol_family == 2u);
    assert(entity_damage_status_request.firing_entity_id.entity == 0x0003u);
    assert(entity_damage_status_request.target_entity_id.entity == 0x0006u);
    assert(entity_damage_status_request.damaged_entity_id.entity == 0x0009u);
    assert(entity_damage_status_request.padding1 == 0x1112u);
    assert(entity_damage_status_request.padding2 == 0x1314u);
    assert(entity_damage_status_request.number_of_damage_description == 1u);
    assert(entity_damage_status_request.damage_description_records.count == 1u);
    assert(entity_damage_status_request.damage_description_records.bytes_size == 4u);

    uint8_t iff_pdu7[FASTDIS_IFF_FIXED_SIZE];
    make_iff_pdu(iff_pdu7, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_iff_t iff_request_dis7;
    assert(fastdis_parse_iff(iff_pdu7, sizeof(iff_pdu7), 0, &iff_request_dis7) == FASTDIS_OK);
    assert(iff_request_dis7.header.protocol_family == 6u);
    assert(iff_request_dis7.emitting_entity_id.entity == 0x0003u);
    assert(iff_request_dis7.event_id.event_number == 0x0006u);
    assert(nearf(iff_request_dis7.location.y, 2.0f));
    assert(iff_request_dis7.system_id.system_name == 0x2222u);
    assert(iff_request_dis7.padding2 == 0x5555u);
    assert(iff_request_dis7.fundamental_parameters.parameter6 == 10u);

    uint8_t emissions_pdu[FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE + 6u];
    make_electronic_emissions_pdu(emissions_pdu, FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis_electronic_emissions_t emissions_request;
    assert(fastdis_parse_electronic_emissions(emissions_pdu, sizeof(emissions_pdu), 0, &emissions_request) == FASTDIS_OK);
    assert(emissions_request.header.protocol_family == 6u);
    assert(emissions_request.emitting_entity_id.entity == 0x0003u);
    assert(emissions_request.event_id.event_number == 0x0006u);
    assert(emissions_request.state_update_indicator == 0x07u);
    assert(emissions_request.number_of_systems == 0x02u);
    assert(emissions_request.padding1 == 0x0809u);
    assert(emissions_request.system_records.count == 2u);
    assert(emissions_request.system_records.bytes_size == 6u);

    uint8_t io_action_pdu[FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE + 4u];
    make_information_operations_action_pdu(io_action_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_information_operations_action_t io_action_request;
    assert(fastdis_parse_information_operations_action(io_action_pdu, sizeof(io_action_pdu), 0, &io_action_request) == FASTDIS_OK);
    assert(io_action_request.header.protocol_family == 13u);
    assert(io_action_request.originating_sim_id.entity == 0x0003u);
    assert(io_action_request.receiving_sim_id.entity == 0x0006u);
    assert(io_action_request.request_id == 0x11223344u);
    assert(io_action_request.io_warfare_type == 0x0102u);
    assert(io_action_request.io_simulation_source == 0x0304u);
    assert(io_action_request.io_action_type == 0x0506u);
    assert(io_action_request.io_action_phase == 0x0708u);
    assert(io_action_request.padding1 == 0x55667788u);
    assert(io_action_request.io_attacker_id.entity == 0x0009u);
    assert(io_action_request.io_primary_target_id.entity == 0x000Cu);
    assert(io_action_request.padding2 == 0x090Au);
    assert(io_action_request.number_of_io_records == 1u);
    assert(io_action_request.io_records.count == 1u);
    assert(io_action_request.io_records.bytes_size == 4u);

    uint8_t io_report_pdu[FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE + 4u];
    make_information_operations_report_pdu(io_report_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_information_operations_report_t io_report_request;
    assert(fastdis_parse_information_operations_report(io_report_pdu, sizeof(io_report_pdu), 0, &io_report_request) == FASTDIS_OK);
    assert(io_report_request.header.protocol_family == 13u);
    assert(io_report_request.originating_sim_id.entity == 0x0003u);
    assert(io_report_request.io_sim_source == 0x0102u);
    assert(io_report_request.io_report_type == 0x03u);
    assert(io_report_request.padding1 == 0x04u);
    assert(io_report_request.io_attacker_id.entity == 0x0006u);
    assert(io_report_request.io_primary_target_id.entity == 0x0009u);
    assert(io_report_request.padding2 == 0x1112u);
    assert(io_report_request.padding3 == 0x1314u);
    assert(io_report_request.number_of_io_records == 1u);
    assert(io_report_request.io_records.count == 1u);
    assert(io_report_request.io_records.bytes_size == 4u);

    uint8_t ua_pdu[FASTDIS_UA_FIXED_SIZE + 8u];
    make_ua_pdu(ua_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_ua_t ua_request;
    assert(fastdis_parse_ua(ua_pdu, sizeof(ua_pdu), 0, &ua_request) == FASTDIS_OK);
    assert(ua_request.header.protocol_family == 6u);
    assert(ua_request.emitting_entity_id.entity == 0x0003u);
    assert(ua_request.event_id.event_number == 0x0006u);
    assert(ua_request.state_change_indicator == 0x0A);
    assert(ua_request.padding1 == 0x0Bu);
    assert(ua_request.passive_parameter_index == 0x0C0Du);
    assert(ua_request.propulsion_plant_configuration == 0x0Eu);
    assert(ua_request.number_of_shafts == 1u);
    assert(ua_request.number_of_apas == 2u);
    assert(ua_request.number_of_ua_emitter_systems == 3u);
    assert(ua_request.ua_records.bytes_size == 8u);

    uint8_t sees_pdu[FASTDIS_SEES_FIXED_SIZE + 8u];
    make_sees_pdu(sees_pdu, FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis_sees_t sees_request;
    assert(fastdis_parse_sees(sees_pdu, sizeof(sees_pdu), 0, &sees_request) == FASTDIS_OK);
    assert(sees_request.header.protocol_family == 6u);
    assert(sees_request.originating_entity_id.site == 0x0011u);
    assert(sees_request.infrared_signature_representation_index == 0x1112u);
    assert(sees_request.acoustic_signature_representation_index == 0x1314u);
    assert(sees_request.radar_cross_section_signature_representation_index == 0x1516u);
    assert(sees_request.number_of_propulsion_systems == 2u);
    assert(sees_request.number_of_vectoring_nozzle_systems == 3u);
    assert(sees_request.supplemental_emission_records.bytes_size == 8u);

    fastdis_simulation_management_reliable_request_t create_reliable_request;
    assert(fastdis_parse_create_entity_reliable(create_entity_reliable_pdu, FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE, 0, &create_reliable_request) == FASTDIS_OK);
    assert(create_reliable_request.header.protocol_family == 10u);
    assert(create_reliable_request.required_reliability_service == 7u);
    assert(create_reliable_request.pad1 == 0x1357u);
    assert(create_reliable_request.pad2 == 9u);
    assert(create_reliable_request.request_id == 0xA0B0C0D0u);

    fastdis_simulation_management_reliable_request_t remove_reliable_request;
    assert(fastdis_parse_remove_entity_reliable(remove_entity_reliable_pdu, FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE, 0, &remove_reliable_request) == FASTDIS_OK);
    assert(remove_reliable_request.header.version == 6u);
    assert(remove_reliable_request.required_reliability_service == 8u);
    assert(remove_reliable_request.pad1 == 0x2468u);
    assert(remove_reliable_request.pad2 == 10u);
    assert(remove_reliable_request.request_id == 0x0BADF00Du);

    fastdis_start_resume_reliable_t start_reliable_request;
    assert(fastdis_parse_start_resume_reliable(start_resume_reliable_pdu, FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE, 0, &start_reliable_request) == FASTDIS_OK);
    assert(start_reliable_request.header.protocol_family == 10u);
    assert(start_reliable_request.real_world_time.hour == 7u);
    assert(start_reliable_request.simulation_time.time_past_hour == 654321u);
    assert(start_reliable_request.required_reliability_service == 11u);
    assert(start_reliable_request.pad1 == 0xAAAAu);
    assert(start_reliable_request.pad2 == 12u);
    assert(start_reliable_request.request_id == 0x01020304u);

    fastdis_stop_freeze_reliable_t stop_reliable_request;
    assert(fastdis_parse_stop_freeze_reliable(stop_freeze_reliable_pdu, FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE, 0, &stop_reliable_request) == FASTDIS_OK);
    assert(stop_reliable_request.header.version == 6u);
    assert(stop_reliable_request.reason == 3u);
    assert(stop_reliable_request.frozen_behavior == 4u);
    assert(stop_reliable_request.required_reliablity_service == 13u);
    assert(stop_reliable_request.pad1 == 14u);
    assert(stop_reliable_request.request_id == 0x0F1E2D3Cu);

    fastdis_acknowledge_t acknowledge_reliable_request;
    assert(fastdis_parse_acknowledge_reliable(acknowledge_reliable_pdu, FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE, 0, &acknowledge_reliable_request) == FASTDIS_OK);
    assert(acknowledge_reliable_request.header.protocol_family == 10u);
    assert(acknowledge_reliable_request.acknowledge_flag == 0x9ABCu);
    assert(acknowledge_reliable_request.response_flag == 0xDEF0u);
    assert(acknowledge_reliable_request.request_id == 0xFACECAFEu);

    fastdis_record_reliable_t record_reliable_request;
    assert(fastdis_parse_record_reliable(record_reliable_pdu, FASTDIS_RECORD_RELIABLE_FIXED_SIZE + 8u, 0, &record_reliable_request) == FASTDIS_OK);
    assert(record_reliable_request.header.version == 7u);
    assert(record_reliable_request.request_id == 0x51525354u);
    assert(record_reliable_request.required_reliability_service == 7u);
    assert(record_reliable_request.pad1 == 8u);
    assert(record_reliable_request.event_type == 0x090Au);
    assert(record_reliable_request.record_sets.count == 2u);
    assert(record_reliable_request.record_sets.bytes_size == 8u);
    assert(record_reliable_request.record_sets.bytes[0] == 0x10u);

    fastdis_set_record_reliable_t set_record_reliable_request;
    assert(fastdis_parse_set_record_reliable(set_record_reliable_pdu, FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE + 8u, 0, &set_record_reliable_request) == FASTDIS_OK);
    assert(set_record_reliable_request.header.version == 6u);
    assert(set_record_reliable_request.request_id == 0x61626364u);
    assert(set_record_reliable_request.required_reliability_service == 9u);
    assert(set_record_reliable_request.pad1 == 0x0B0Cu);
    assert(set_record_reliable_request.pad2 == 13u);
    assert(set_record_reliable_request.record_sets.count == 3u);
    assert(set_record_reliable_request.record_sets.bytes[0] == 0x21u);

    fastdis_record_query_reliable_t record_query_reliable_request;
    assert(fastdis_parse_record_query_reliable(record_query_reliable_pdu, FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE + 8u, 0, &record_query_reliable_request) == FASTDIS_OK);
    assert(record_query_reliable_request.header.version == 7u);
    assert(record_query_reliable_request.request_id == 0x71727374u);
    assert(record_query_reliable_request.required_reliability_service == 14u);
    assert(record_query_reliable_request.pad1 == 0x1516u);
    assert(record_query_reliable_request.pad2 == 17u);
    assert(record_query_reliable_request.event_type == 0x1819u);
    assert(record_query_reliable_request.time == 0x1A1B1C1Du);
    assert(record_query_reliable_request.record_ids.count == 2u);
    assert(record_query_reliable_request.record_ids.bytes[0] == 0x31u);

    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);
    const uint8_t version_7_only[1] = {7};
    const uint8_t pdu_1_only[1] = {1};
    assert(fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_VERSION, version_7_only, 1) == FASTDIS_OK);
    assert(fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_PDU_TYPE, pdu_1_only, 1) == FASTDIS_OK);
    assert(fastdis_scan_config_filter_contains(&config, FASTDIS_FILTER_VERSION, 7) == 1);
    assert(fastdis_scan_config_filter_contains(&config, FASTDIS_FILTER_VERSION, 6) == 0);
    assert(fastdis_scan_config_set_sample(&config, 2, 0) == FASTDIS_OK);

    uint8_t p1[160];
    uint8_t p2[160];
    uint8_t p3[160];
    uint8_t bad[3] = {1, 2, 3};
    make_pdu(p1, 7, 1);
    make_pdu(p2, 7, 2);
    make_pdu(p3, 7, 1);

    fastdis_packet_view_t packets[4];
    packets[0] = fastdis_packet_view_t{p1, 12, nullptr};
    packets[1] = fastdis_packet_view_t{p2, 12, nullptr};
    packets[2] = fastdis_packet_view_t{bad, sizeof(bad), nullptr};
    packets[3] = fastdis_packet_view_t{p3, 12, nullptr};

    Counter counter;
    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scan_packets(packets, 4, &config, on_packet, &counter, &stats) == FASTDIS_OK);
    assert(stats.seen == 4);
    assert(stats.malformed == 1);
    assert(stats.accepted == 2);
    assert(stats.emitted == 1);
    assert(counter.count == 1);
    assert(counter.last_type == 1);

    uint8_t espdu[160];
    make_entity_state_pdu(espdu, 7, 2);
    fastdis_entity_state_prefix_t entity;
    assert(fastdis_parse_entity_state_prefix(espdu, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &entity) == FASTDIS_OK);
    assert(entity.header.length == FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(entity.entity_id.site == 0x1111u);
    assert(entity.entity_id.application == 0x2222u);
    assert(entity.entity_id.entity == 0x3333u);
    assert(entity.force_id == 2u);
    assert(entity.variable_parameter_count == 0u);
    assert(entity.entity_type.entity_kind == 1u);
    assert(entity.entity_type.domain == 2u);
    assert(entity.entity_type.country == 840u);
    assert(entity.alternate_entity_type.entity_kind == 9u);
    assert(nearf(entity.linear_velocity.x, 1.25f));
    assert(nearf(entity.linear_velocity.y, -2.5f));
    assert(entity.location.x == 10.0);
    assert(entity.location.y == 20.0);
    assert(entity.location.z == 30.0);
    assert(nearf(entity.orientation.psi, 0.1f));
    assert(entity.appearance == 0xAABBCCDDu);
    assert(entity.dead_reckoning_algorithm == 4u);
    assert(entity.dead_reckoning_parameters[0] == 1u);
    assert(entity.dead_reckoning_parameters[14] == 15u);
    assert(nearf(entity.dead_reckoning_linear_acceleration.x, 0.5f));
    assert(nearf(entity.dead_reckoning_angular_velocity.z, 1.7f));
    assert(entity.marking_character_set == 1u);
    assert(std::memcmp(entity.marking, "TANK001", 7) == 0);
    assert(entity.marking[11] == 0u);
    assert(entity.capabilities == 0x01020304u);
    assert((entity.fields_present & FASTDIS_ES_FIELD_ALL) == FASTDIS_ES_FIELD_ALL);

    fastdis_entity_state_prefix_t pose_only;
    assert(fastdis_parse_entity_state_fields(
               espdu,
               FASTDIS_ENTITY_STATE_FIXED_SIZE,
               0,
               FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION,
               &pose_only) == FASTDIS_OK);
    assert((pose_only.fields_present & FASTDIS_ES_FIELD_HEADER) != 0u);
    assert((pose_only.fields_present & FASTDIS_ES_FIELD_FORCE_ID) != 0u);
    assert((pose_only.fields_present & FASTDIS_ES_FIELD_LOCATION) != 0u);
    assert((pose_only.fields_present & FASTDIS_ES_FIELD_ORIENTATION) != 0u);
    assert((pose_only.fields_present & FASTDIS_ES_FIELD_ENTITY_TYPE) == 0u);
    assert(pose_only.entity_id.site == 0u);
    assert(pose_only.force_id == 2u);
    assert(pose_only.location.x == 10.0);
    assert(nearf(pose_only.orientation.theta, 0.2f));
    assert(pose_only.appearance == 0u);


    uint8_t non_entity[160];
    make_pdu(non_entity, 7, 2, FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(fastdis_parse_entity_state_prefix(non_entity, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &entity) == FASTDIS_ERR_UNSUPPORTED_PDU);

    fastdis_scan_config_init(&config);
    assert(fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_VERSION, version_7_only, 1) == FASTDIS_OK);
    const uint8_t force_2_only[1] = {2};
    assert(fastdis_scan_config_filter_only(&config, FASTDIS_FILTER_ENTITY_FORCE_ID, force_2_only, 1) == FASTDIS_OK);

    uint8_t espdu_force_2[160];
    uint8_t espdu_force_3[160];
    uint8_t short_espdu[160];
    make_entity_state_pdu(espdu_force_2, 7, 2);
    make_entity_state_pdu(espdu_force_3, 7, 3);
    make_entity_state_pdu(short_espdu, 7, 2);

    fastdis_packet_view_t entity_packets[4];
    entity_packets[0] = fastdis_packet_view_t{espdu_force_2, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    entity_packets[1] = fastdis_packet_view_t{espdu_force_3, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    entity_packets[2] = fastdis_packet_view_t{non_entity, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    entity_packets[3] = fastdis_packet_view_t{short_espdu, 64, nullptr};

    Counter entity_counter;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scan_entity_state_packets(entity_packets, 4, &config, on_entity_state, &entity_counter, &stats) == FASTDIS_OK);
    assert(stats.seen == 4);
    assert(stats.malformed == 1);
    assert(stats.accepted == 1);
    assert(stats.emitted == 1);
    assert(entity_counter.count == 1);
    assert(entity_counter.last_type == FASTDIS_ENTITY_STATE_PDU_TYPE);
    assert(entity_counter.last_force == 2u);

    fastdis_scan_config_t scanner_config;
    fastdis_scan_config_init(&scanner_config);
    scanner_config.entity_state_fields = FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION;
    fastdis_scanner_t *scanner = fastdis_scanner_create(&scanner_config);
    assert(scanner != nullptr);
    const uint8_t scanner_versions[2] = {6, 7};
    assert(fastdis_scanner_filter_only(scanner, FASTDIS_FILTER_VERSION, scanner_versions, 2) == FASTDIS_OK);
    assert(fastdis_scanner_filter_contains(scanner, FASTDIS_FILTER_VERSION, 7) == 1);
    assert(fastdis_scanner_filter_contains(scanner, FASTDIS_FILTER_VERSION, 6) == 1);
    const uint8_t scanner_version_7[1] = {7};
    assert(fastdis_scanner_filter_only(scanner, FASTDIS_FILTER_VERSION, scanner_version_7, 1) == FASTDIS_OK);
    assert(fastdis_scanner_filter_contains(scanner, FASTDIS_FILTER_VERSION, 7) == 1);
    assert(fastdis_scanner_filter_contains(scanner, FASTDIS_FILTER_VERSION, 6) == 0);
    assert(fastdis_scanner_filter_only(scanner, FASTDIS_FILTER_VERSION, nullptr, 0) == FASTDIS_OK);
    assert(fastdis_scanner_filter_contains(scanner, FASTDIS_FILTER_VERSION, 6) == 1);
    assert(fastdis_scanner_filter_only(scanner, FASTDIS_FILTER_VERSION, scanner_version_7, 1) == FASTDIS_OK);
    assert(fastdis_scanner_set_sample(scanner, 1, 0) == FASTDIS_OK);
    assert(fastdis_scanner_set_entity_state_fields(scanner, FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION) == FASTDIS_OK);
    assert(fastdis_scanner_entity_id_count(scanner) == 0u);
    fastdis_entity_id_t allow_ids[1] = {{0x1111u, 0x2222u, 0x3333u}};
    fastdis_entity_id_t extra_ids[1] = {{0x9999u, 0x2222u, 0x3333u}};
    assert(fastdis_scanner_set_entity_ids(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW, allow_ids, 1) == FASTDIS_OK);
    assert(fastdis_scanner_contains_entity_id(scanner, 0x1111u, 0x2222u, 0x3333u) == 1);
    assert(fastdis_scanner_entity_id_count(scanner) == 1u);
    assert(fastdis_scanner_add_entity_ids(scanner, extra_ids, 1) == FASTDIS_OK);
    assert(fastdis_scanner_entity_id_count(scanner) == 2u);
    assert(fastdis_scanner_set_entity_ids(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW, allow_ids, 1) == FASTDIS_OK);
    assert(fastdis_scanner_entity_id_count(scanner) == 1u);
    assert(fastdis_scanner_get_entity_id_filter_mode(scanner) == FASTDIS_ENTITY_ID_FILTER_ALLOW);

    uint8_t espdu_other_entity[160];
    make_entity_state_pdu(espdu_other_entity, 7, 2);
    put_be16(espdu_other_entity + FASTDIS_HEADER_SIZE + 0, 0x9999u);

    fastdis_packet_view_t scanner_packets[2];
    scanner_packets[0] = fastdis_packet_view_t{espdu_force_2, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    scanner_packets[1] = fastdis_packet_view_t{espdu_other_entity, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    Counter scanner_counter;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scanner_scan_entity_state_packets(scanner, scanner_packets, 2, on_entity_state, &scanner_counter, &stats) == FASTDIS_OK);
    assert(stats.seen == 2);
    assert(stats.malformed == 0);
    assert(stats.accepted == 1);
    assert(stats.emitted == 1);
    assert(scanner_counter.count == 1);

    assert(fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_BLOCK) == FASTDIS_OK);
    scanner_counter = Counter{};
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scanner_scan_entity_state_packets(scanner, scanner_packets, 2, on_entity_state, &scanner_counter, &stats) == FASTDIS_OK);
    assert(stats.accepted == 1);
    assert(scanner_counter.count == 1);

    assert(fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_TRANSFORM) == FASTDIS_OK);
    assert(fastdis_scan_config_filter_contains(&config, FASTDIS_FILTER_PDU_TYPE, FASTDIS_ENTITY_STATE_PDU_TYPE) == 1);
    assert(fastdis_scan_config_filter_contains(&config, FASTDIS_FILTER_PDU_TYPE, FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE) == 1);
    assert(fastdis_scan_config_filter_contains(&config, FASTDIS_FILTER_PROTOCOL_FAMILY, FASTDIS_ENTITY_INFORMATION_FAMILY) == 1);
    assert((config.entity_state_fields & FASTDIS_ES_FIELD_LOCATION) != 0u);
    assert((config.entity_state_fields & FASTDIS_ES_FIELD_LINEAR_VELOCITY) != 0u);

    fastdis_entity_transform_t transform;
    assert(fastdis_parse_entity_transform(espdu_force_2, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &transform) == FASTDIS_OK);
    assert(transform.entity_id.site == 0x1111u);
    assert(transform.force_id == 2u);
    assert(transform.exercise_id == 3u);
    assert(transform.version == 7u);
    assert(transform.timestamp == 0x01020304u);
    assert(transform.appearance == 0xAABBCCDDu);
    assert(transform.location.x == 10.0);
    assert(nearf(transform.orientation.phi, 0.3f));
    assert(nearf(transform.linear_velocity.x, 1.25f));
    assert(transform.dead_reckoning_algorithm == FASTDIS_DR_RVW);
    assert(transform.dead_reckoning_parameters[0] == 1u);
    assert(nearf(transform.dead_reckoning_linear_acceleration.x, 0.5f));
    assert(nearf(transform.dead_reckoning_angular_velocity.z, 1.7f));

    uint8_t esu[160];
    make_entity_state_update_pdu(esu, 7);
    fastdis_entity_transform_t esu_transform;
    assert(fastdis_parse_entity_transform(esu, FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE, 0, &esu_transform) == FASTDIS_OK);
    assert(esu_transform.entity_id.site == 0x1111u);
    assert(esu_transform.entity_id.application == 0x2222u);
    assert(esu_transform.entity_id.entity == 0x3333u);
    assert(esu_transform.force_id == 0u);
    assert(esu_transform.exercise_id == 3u);
    assert(esu_transform.version == 7u);
    assert(esu_transform.timestamp == 0x01020304u);
    assert(esu_transform.appearance == 0x11223344u);
    assert(esu_transform.location.x == 40.0);
    assert(esu_transform.location.y == 50.0);
    assert(nearf(esu_transform.linear_velocity.z, 6.0f));
    assert(nearf(esu_transform.orientation.theta, 0.5f));
    assert((esu_transform.fields_present & FASTDIS_ES_FIELD_FORCE_ID) == 0u);
    assert((esu_transform.fields_present & FASTDIS_ES_FIELD_LOCATION) != 0u);

    fastdis_entity_table_t *esu_merge_table = fastdis_entity_table_create(2);
    assert(esu_merge_table != nullptr);
    fastdis_entity_snapshot_t merge_snapshot;
    assert(fastdis_entity_table_update_transform(esu_merge_table, &transform, &merge_snapshot) == FASTDIS_OK);
    assert(fastdis_entity_table_update_transform(esu_merge_table, &esu_transform, &merge_snapshot) == FASTDIS_OK);
    assert(merge_snapshot.update_count == 2u);
    assert(merge_snapshot.transform.force_id == 2u);
    assert(merge_snapshot.transform.dead_reckoning_algorithm == FASTDIS_DR_RVW);
    assert(merge_snapshot.transform.location.x == 40.0);
    assert(nearf(merge_snapshot.transform.linear_velocity.x, 4.0f));
    assert(merge_snapshot.transform.appearance == 0x11223344u);
    fastdis_entity_table_destroy(esu_merge_table);

    for (uint8_t algorithm = FASTDIS_DR_OTHER; algorithm <= FASTDIS_DR_FVB; ++algorithm) {
        assert(fastdis_dead_reckoning_algorithm_known(algorithm) == 1);
        assert(std::strlen(fastdis_dead_reckoning_algorithm_name(algorithm)) > 0u);
        transform.dead_reckoning_algorithm = algorithm;
        fastdis_entity_transform_t algorithm_out;
        assert(fastdis_extrapolate_entity_transform_dead_reckoning(&transform, 1.0, &algorithm_out) == FASTDIS_OK);
    }
    transform.dead_reckoning_algorithm = FASTDIS_DR_RVW;
    fastdis_entity_transform_t dr_transform;
    assert(fastdis_extrapolate_entity_transform_dead_reckoning(&transform, 2.0, &dr_transform) == FASTDIS_OK);
    assert(std::fabs(dr_transform.location.x - 13.5) < 0.0001);
    assert(std::fabs(dr_transform.location.y - 16.2) < 0.0001);
    assert(std::fabs(dr_transform.location.z - 38.9) < 0.0001);
    assert(nearf(dr_transform.orientation.psi, 3.1f));
    assert(nearf(dr_transform.orientation.theta, 3.4f));
    assert(nearf(dr_transform.orientation.phi, 3.7f));
    assert(fastdis_dead_reckoning_algorithm_known(10u) == 0);
    transform.dead_reckoning_algorithm = 10u;
    assert(fastdis_extrapolate_entity_transform_dead_reckoning(&transform, 1.0, &dr_transform) == FASTDIS_ERR_BAD_ARGUMENT);

    fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_STATE_POSE);
    fastdis_entity_state_prefix_t batch_entities[1];
    fastdis_entity_state_batch_t entity_batch;
    entity_batch.entities = batch_entities;
    entity_batch.capacity = 1;
    entity_batch.count = 123;
    entity_batch.dropped = 456;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scan_entity_state_to_batch(scanner_packets, 2, &config, &entity_batch, &stats) == FASTDIS_OK);
    assert(stats.seen == 2);
    assert(stats.accepted == 2);
    assert(stats.emitted == 2);
    assert(entity_batch.count == 1u);
    assert(entity_batch.dropped == 1u);
    assert(entity_batch.entities[0].entity_id.site == 0x1111u);
    assert(entity_batch.entities[0].location.x == 10.0);

    assert(fastdis_scanner_use_profile(scanner, FASTDIS_PROFILE_ENTITY_TRANSFORM) == FASTDIS_OK);
    assert(fastdis_scanner_set_entity_ids(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW, allow_ids, 1) == FASTDIS_OK);
    fastdis_packet_view_t scanner_transform_packets[3];
    scanner_transform_packets[0] = scanner_packets[0];
    scanner_transform_packets[1] = scanner_packets[1];
    scanner_transform_packets[2] = fastdis_packet_view_t{esu, FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE, nullptr};
    fastdis_entity_transform_t transforms[2];
    fastdis_entity_transform_batch_t transform_batch;
    transform_batch.transforms = transforms;
    transform_batch.capacity = 2;
    transform_batch.count = 0;
    transform_batch.dropped = 0;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scanner_scan_entity_transforms_to_batch(scanner, scanner_transform_packets, 3, &transform_batch, &stats) == FASTDIS_OK);
    assert(stats.seen == 3);
    assert(stats.accepted == 2);
    assert(stats.emitted == 2);
    assert(transform_batch.count == 2u);
    assert(transform_batch.dropped == 0u);
    assert(transform_batch.transforms[0].entity_id.entity == 0x3333u);
    assert(transform_batch.transforms[0].location.y == 20.0);
    assert(transform_batch.transforms[1].entity_id.entity == 0x3333u);
    assert(transform_batch.transforms[1].force_id == 0u);
    assert(transform_batch.transforms[1].location.x == 40.0);

    assert(fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_DISABLED) == FASTDIS_OK);
    assert(fastdis_scanner_use_profile(scanner, FASTDIS_PROFILE_ENTITY_TRANSFORM) == FASTDIS_OK);

    fastdis_entity_table_t *table = fastdis_entity_table_create(8);
    assert(table != nullptr);
    assert(fastdis_entity_table_size(table) == 0u);
    assert(fastdis_entity_table_tick(table) == 0u);

    fastdis_entity_table_update_stats_t table_stats;
    fastdis_entity_table_update_stats_init(&table_stats);
    assert(fastdis_entity_table_ingest_packets(table, scanner, scanner_packets, 2, 1, &table_stats) == FASTDIS_OK);
    assert(table_stats.scan.seen == 2u);
    assert(table_stats.scan.accepted == 2u);
    assert(table_stats.scan.emitted == 2u);
    assert(table_stats.table_updates == 2u);
    assert(table_stats.new_entities == 2u);
    assert(table_stats.changed_entities == 2u);
    assert(table_stats.entity_count == 2u);
    assert(fastdis_entity_table_size(table) == 2u);
    assert(fastdis_entity_table_tick(table) == 1u);

    fastdis_entity_snapshot_t snapshot;
    assert(fastdis_parse_header(nullptr, 12, 0, &h) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_header(p, 12, 0, nullptr) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_header(p, 0, 0, &h) == FASTDIS_ERR_SHORT_PACKET);
    make_pdu(p, 7, 1, 8);
    assert(fastdis_parse_header(p, 12, 0, &h) == FASTDIS_ERR_LENGTH_TOO_SMALL);
    make_pdu(p, 255, 1, 12);
    assert(fastdis_parse_header(p, 12, 0, &h) == FASTDIS_OK);
    assert(h.version == 255u);

    assert(fastdis_parse_entity_state_prefix(nullptr, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &entity) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_entity_state_prefix(espdu, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, nullptr) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_entity_state_prefix(espdu, 0, 0, &entity) == FASTDIS_ERR_SHORT_PACKET);
    assert(fastdis_parse_entity_state_prefix(espdu, 32, 0, &entity) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_entity_state_prefix(espdu, 32, FASTDIS_FLAG_ALLOW_TRUNCATED, &entity) == FASTDIS_ERR_SHORT_PACKET);
    uint8_t tiny_length_espdu[160];
    make_entity_state_pdu(tiny_length_espdu, 7, 2);
    put_be16(tiny_length_espdu + 8, 11u);
    assert(fastdis_parse_entity_state_prefix(tiny_length_espdu, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &entity) == FASTDIS_ERR_LENGTH_TOO_SMALL);
    uint8_t short_declared_entity[160];
    make_entity_state_pdu(short_declared_entity, 7, 2);
    put_be16(short_declared_entity + 8, 100u);
    assert(fastdis_parse_entity_state_prefix(short_declared_entity, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &entity) == FASTDIS_ERR_LENGTH_TOO_SMALL);
    uint8_t oversized_vp_count[160];
    make_entity_state_pdu(oversized_vp_count, 7, 2);
    oversized_vp_count[FASTDIS_HEADER_SIZE + 7] = 255u;
    assert(fastdis_parse_entity_state_fields(
               oversized_vp_count,
               FASTDIS_ENTITY_STATE_FIXED_SIZE,
               0,
               FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT,
               &entity) == FASTDIS_OK);
    assert(entity.variable_parameter_count == 255u);

    fastdis_scan_stats_init(&stats);
    assert(fastdis_scan_packet(nullptr, 0, &config, nullptr, nullptr, &stats) == FASTDIS_OK);
    assert(stats.seen == 1u);
    assert(stats.malformed == 1u);
    assert(fastdis_scan_packets(nullptr, 1, &config, nullptr, nullptr, &stats) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_scan_packets(packets, 0, &config, nullptr, nullptr, &stats) == FASTDIS_OK);
    assert(stats.seen == 1u);

    assert(fastdis_parse_entity_transform(nullptr, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, &transform) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_entity_transform(espdu_force_2, FASTDIS_ENTITY_STATE_FIXED_SIZE, 0, nullptr) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_fire(nullptr, FASTDIS_FIRE_FIXED_SIZE, 0, &fire_event) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_fire(fire_pdu, FASTDIS_FIRE_FIXED_SIZE, 0, nullptr) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_detonation(detonation_pdu, FASTDIS_DETONATION_FIXED_SIZE + 15u, 0, &detonation_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_create_entity(nullptr, FASTDIS_CREATE_ENTITY_FIXED_SIZE, 0, &create_request) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_create_entity(create_entity_pdu, FASTDIS_CREATE_ENTITY_FIXED_SIZE, 0, nullptr) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_parse_other_pdu(other_pdu, FASTDIS_OTHER_FIXED_SIZE + 3u, 0, &other_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_aggregate_state(aggregate_state_pdu, FASTDIS_AGGREGATE_STATE_FIXED_SIZE + 5u, 0, &aggregate_state_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_is_group_of(is_group_of_pdu, FASTDIS_IS_GROUP_OF_FIXED_SIZE + 3u, 0, &is_group_of_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_transfer_control_request(transfer_control_request_pdu, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + 3u, 0, &transfer_control_request_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_transfer_ownership(transfer_ownership_pdu, FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + 3u, 0, &transfer_ownership_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_is_part_of(is_part_of_pdu, FASTDIS_IS_PART_OF_FIXED_SIZE - 1u, 0, &is_part_of_event) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_remove_entity(remove_entity_pdu, FASTDIS_REMOVE_ENTITY_FIXED_SIZE - 1u, 0, &remove_request) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_start_resume(start_resume_pdu, FASTDIS_START_RESUME_FIXED_SIZE - 1u, 0, &start_request) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    assert(fastdis_parse_stop_freeze(stop_freeze_pdu, FASTDIS_STOP_FREEZE_FIXED_SIZE - 1u, 0, &stop_request) == FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER);
    uint8_t wrong_family[64];
    make_create_entity_pdu(wrong_family, 7);
    wrong_family[3] = 1;
    assert(fastdis_parse_create_entity(wrong_family, FASTDIS_CREATE_ENTITY_FIXED_SIZE, 0, &create_request) == FASTDIS_ERR_UNSUPPORTED_PDU);

    assert(fastdis_entity_table_get(table, 0x1111u, 0x2222u, 0x3333u, &snapshot) == FASTDIS_OK);
    assert(snapshot.transform.location.x == 10.0);
    assert(snapshot.first_seen_tick == 1u);
    assert(snapshot.last_seen_tick == 1u);
    assert((snapshot.change_flags & FASTDIS_ENTITY_CHANGE_NEW) != 0u);

    fastdis_entity_snapshot_t snapshots[4];
    fastdis_entity_snapshot_batch_t snapshot_batch;
    snapshot_batch.snapshots = snapshots;
    snapshot_batch.capacity = 4;
    snapshot_batch.count = 0;
    snapshot_batch.dropped = 0;
    fastdis_entity_snapshot_buffer_t *snapshot_buffer = fastdis_entity_snapshot_buffer_create(4);
    assert(snapshot_buffer != nullptr);
    assert(fastdis_entity_snapshot_buffer_capacity(snapshot_buffer) == 4u);
    assert(fastdis_entity_snapshot_buffer_slot_count(snapshot_buffer) == 2u);
    assert(fastdis_entity_snapshot_buffer_generation(snapshot_buffer) == 0u);
    fastdis_entity_snapshot_buffer_stats_t buffer_stats;
    fastdis_entity_snapshot_buffer_stats_init(&buffer_stats);
    assert(fastdis_entity_snapshot_buffer_get_stats(snapshot_buffer, &buffer_stats) == FASTDIS_OK);
    assert(buffer_stats.publish_attempts == 0u);
    assert(buffer_stats.publish_successes == 0u);
    assert(buffer_stats.publish_busy == 0u);

    fastdis_entity_snapshot_view_t view;
    assert(fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, table, 0, &view) == FASTDIS_OK);
    assert(view.count == 2u);
    assert(view.dropped == 0u);
    assert(view.generation == 1u);
    assert(view.snapshots != nullptr);
    assert((view.snapshots[0].change_flags & FASTDIS_ENTITY_CHANGE_NEW) != 0u);
    assert(fastdis_entity_snapshot_buffer_get_stats(snapshot_buffer, &buffer_stats) == FASTDIS_OK);
    assert(buffer_stats.publish_attempts == 1u);
    assert(buffer_stats.publish_successes == 1u);
    assert(buffer_stats.max_snapshot_count == 2u);
    assert(buffer_stats.dropped_snapshots == 0u);

    fastdis_entity_snapshot_view_t held_view;
    assert(fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(held_view.count == 2u);
    assert(held_view.generation == 1u);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_OK);
    assert(view.generation == 2u);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_ERR_BUSY);
    assert(fastdis_entity_snapshot_buffer_get_stats(snapshot_buffer, &buffer_stats) == FASTDIS_OK);
    assert(buffer_stats.publish_attempts == 3u);
    assert(buffer_stats.publish_successes == 2u);
    assert(buffer_stats.publish_busy == 1u);
    assert(buffer_stats.acquire_count == 1u);
    assert(buffer_stats.release_count == 0u);

    fastdis_entity_snapshot_t copied_snapshots[4];
    fastdis_entity_snapshot_batch_t copy_batch;
    copy_batch.snapshots = copied_snapshots;
    copy_batch.capacity = 4;
    copy_batch.count = 0;
    copy_batch.dropped = 0;
    assert(fastdis_entity_snapshot_buffer_copy_latest(snapshot_buffer, &copy_batch) == FASTDIS_OK);
    assert(copy_batch.count == 2u);
    assert(copy_batch.dropped == 0u);

    fastdis_entity_transform_t extrapolated_transform;
    assert(fastdis_extrapolate_entity_transform_linear(&copied_snapshots[0].transform, 2.0, &extrapolated_transform) == FASTDIS_OK);
    assert(std::fabs(extrapolated_transform.location.x - 12.5) < 0.0001);
    assert(std::fabs(extrapolated_transform.location.y - 15.0) < 0.0001);
    assert(std::fabs(extrapolated_transform.location.z - 37.5) < 0.0001);

    fastdis_entity_snapshot_t extrapolated_snapshot;
    assert(
        fastdis_extrapolate_entity_snapshot_linear(
            &copied_snapshots[0],
            copied_snapshots[0].last_seen_tick + 2u,
            0.5,
            &extrapolated_snapshot
        )
        == FASTDIS_OK
    );
    assert(std::fabs(extrapolated_snapshot.transform.location.x - 11.25) < 0.0001);
    assert(std::fabs(extrapolated_snapshot.transform.location.y - 17.5) < 0.0001);
    assert(std::fabs(extrapolated_snapshot.transform.location.z - 33.75) < 0.0001);
    assert((extrapolated_snapshot.change_flags & FASTDIS_ENTITY_CHANGE_EXTRAPOLATED) != 0u);
    assert(fastdis_extrapolate_entity_snapshot_linear(&copied_snapshots[0], copied_snapshots[0].last_seen_tick, -0.1, &extrapolated_snapshot) == FASTDIS_ERR_BAD_ARGUMENT);

    fastdis_entity_snapshot_t extrapolated_copied_snapshots[4];
    fastdis_entity_snapshot_batch_t extrapolated_copy_batch;
    extrapolated_copy_batch.snapshots = extrapolated_copied_snapshots;
    extrapolated_copy_batch.capacity = 4;
    extrapolated_copy_batch.count = 0;
    extrapolated_copy_batch.dropped = 0;
    assert(
        fastdis_entity_snapshot_buffer_copy_latest_extrapolated(
            snapshot_buffer,
            copied_snapshots[0].last_seen_tick + 2u,
            0.5,
            &extrapolated_copy_batch
        )
        == FASTDIS_OK
    );
    assert(extrapolated_copy_batch.count == 2u);
    assert(extrapolated_copy_batch.dropped == 0u);
    assert(std::fabs(extrapolated_copied_snapshots[0].transform.location.x - 11.25) < 0.0001);
    assert((extrapolated_copied_snapshots[0].change_flags & FASTDIS_ENTITY_CHANGE_EXTRAPOLATED) != 0u);

    fastdis_entity_snapshot_t dead_reckoned_snapshot;
    assert(
        fastdis_extrapolate_entity_snapshot_dead_reckoning(
            &copied_snapshots[0],
            copied_snapshots[0].last_seen_tick + 2u,
            0.5,
            &dead_reckoned_snapshot
        )
        == FASTDIS_OK
    );
    assert(std::fabs(dead_reckoned_snapshot.transform.location.x - 11.5) < 0.0001);
    assert(std::fabs(dead_reckoned_snapshot.transform.location.y - 17.8) < 0.0001);
    assert(std::fabs(dead_reckoned_snapshot.transform.location.z - 34.1) < 0.0001);
    assert((dead_reckoned_snapshot.change_flags & FASTDIS_ENTITY_CHANGE_EXTRAPOLATED) != 0u);

    fastdis_entity_snapshot_t dead_reckoned_copied_snapshots[4];
    fastdis_entity_snapshot_batch_t dead_reckoned_copy_batch;
    dead_reckoned_copy_batch.snapshots = dead_reckoned_copied_snapshots;
    dead_reckoned_copy_batch.capacity = 4;
    dead_reckoned_copy_batch.count = 0;
    dead_reckoned_copy_batch.dropped = 0;
    assert(
        fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned(
            snapshot_buffer,
            copied_snapshots[0].last_seen_tick + 2u,
            0.5,
            &dead_reckoned_copy_batch
        )
        == FASTDIS_OK
    );
    assert(dead_reckoned_copy_batch.count == 2u);
    assert(std::fabs(dead_reckoned_copied_snapshots[0].transform.location.x - 11.5) < 0.0001);

    assert(fastdis_entity_snapshot_buffer_release(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_get_stats(snapshot_buffer, &buffer_stats) == FASTDIS_OK);
    assert(buffer_stats.release_count == 1u);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_OK);
    assert(view.generation == 3u);
    assert(fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_resize(snapshot_buffer, 2) == FASTDIS_ERR_BUSY);
    assert(fastdis_entity_snapshot_buffer_release(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_reset_stats(snapshot_buffer) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_get_stats(snapshot_buffer, &buffer_stats) == FASTDIS_OK);
    assert(buffer_stats.publish_attempts == 0u);
    assert(buffer_stats.acquire_count == 0u);
    assert(buffer_stats.release_count == 0u);
    assert(fastdis_entity_snapshot_buffer_resize(snapshot_buffer, 2) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_capacity(snapshot_buffer) == 2u);
    fastdis_entity_snapshot_buffer_destroy(snapshot_buffer);

    fastdis_entity_snapshot_buffer_t *triple_buffer = fastdis_entity_snapshot_buffer_create_ex(4, 3);
    assert(triple_buffer != nullptr);
    assert(fastdis_entity_snapshot_buffer_slot_count(triple_buffer) == 3u);
    fastdis_entity_snapshot_view_t triple_held_a;
    fastdis_entity_snapshot_view_t triple_held_b;
    assert(fastdis_entity_snapshot_buffer_publish_all(triple_buffer, table, &view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_acquire_latest(triple_buffer, &triple_held_a) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_publish_all(triple_buffer, table, &view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_acquire_latest(triple_buffer, &triple_held_b) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_publish_all(triple_buffer, table, &view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_publish_all(triple_buffer, table, &view) == FASTDIS_ERR_BUSY);
    assert(fastdis_entity_snapshot_buffer_release(triple_buffer, &triple_held_a) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_release(triple_buffer, &triple_held_b) == FASTDIS_OK);
    fastdis_entity_snapshot_buffer_destroy(triple_buffer);

    assert(fastdis_entity_table_snapshot_changed(table, &snapshot_batch, 1) == FASTDIS_OK);
    assert(snapshot_batch.count == 2u);
    assert(snapshot_batch.dropped == 0u);
    assert((snapshot_batch.snapshots[0].change_flags & FASTDIS_ENTITY_CHANGE_NEW) != 0u);
    assert(fastdis_entity_table_snapshot_changed(table, &snapshot_batch, 0) == FASTDIS_OK);
    assert(snapshot_batch.count == 0u);

    uint8_t espdu_changed[160];
    make_entity_state_pdu(espdu_changed, 7, 2);
    put_world(espdu_changed + FASTDIS_HEADER_SIZE + 36, 100.0, 20.0, 30.0);
    fastdis_packet_view_t changed_packet[1];
    changed_packet[0] = fastdis_packet_view_t{espdu_changed, FASTDIS_ENTITY_STATE_FIXED_SIZE, nullptr};
    fastdis_entity_table_update_stats_init(&table_stats);
    assert(fastdis_entity_table_ingest_packets(table, scanner, changed_packet, 1, 1, &table_stats) == FASTDIS_OK);
    assert(table_stats.new_entities == 0u);
    assert(table_stats.changed_entities == 1u);
    assert(table_stats.unchanged_entities == 0u);
    assert(fastdis_entity_table_tick(table) == 2u);
    assert(fastdis_entity_table_get(table, 0x1111u, 0x2222u, 0x3333u, &snapshot) == FASTDIS_OK);
    assert(snapshot.transform.location.x == 100.0);
    assert(snapshot.update_count == 2u);

    assert(fastdis_entity_table_advance_tick(table, 3) == FASTDIS_OK);
    assert(fastdis_entity_table_tick(table) == 5u);
    assert(fastdis_entity_table_snapshot_stale(table, 2, &snapshot_batch) == FASTDIS_OK);
    assert(snapshot_batch.count == 2u);
    assert((snapshot_batch.snapshots[0].change_flags & FASTDIS_ENTITY_CHANGE_STALE) != 0u);

    snapshot_batch.capacity = 1;
    snapshot_batch.count = 99;
    snapshot_batch.dropped = 99;
    assert(fastdis_entity_table_evict_stale(table, 2, &snapshot_batch) == FASTDIS_OK);
    assert(snapshot_batch.count == 1u);
    assert(snapshot_batch.dropped == 1u);
    assert(fastdis_entity_table_size(table) == 0u);
    assert(fastdis_entity_table_get(table, 0x1111u, 0x2222u, 0x3333u, &snapshot) == FASTDIS_ERR_NOT_FOUND);
    assert(fastdis_entity_table_ingest_packets(nullptr, scanner, scanner_packets, 2, 1, &table_stats) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_entity_table_ingest_packets(table, nullptr, scanner_packets, 2, 1, &table_stats) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_entity_table_ingest_packets(table, scanner, nullptr, 2, 1, &table_stats) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_entity_table_ingest_packets(table, scanner, scanner_packets, 0, 1, &table_stats) == FASTDIS_OK);
    fastdis_entity_table_destroy(table);

    fastdis_entity_snapshot_buffer_t *zero_capacity_buffer = fastdis_entity_snapshot_buffer_create(0);
    assert(zero_capacity_buffer != nullptr);
    assert(fastdis_entity_snapshot_buffer_capacity(zero_capacity_buffer) == 0u);
    fastdis_entity_snapshot_buffer_destroy(zero_capacity_buffer);
    assert(fastdis_entity_snapshot_buffer_create_ex(4, 0) == nullptr);
    zero_capacity_buffer = fastdis_entity_snapshot_buffer_create_ex(0, 2);
    assert(zero_capacity_buffer != nullptr);
    assert(fastdis_entity_snapshot_buffer_capacity(zero_capacity_buffer) == 0u);
    fastdis_entity_snapshot_buffer_destroy(zero_capacity_buffer);
    assert(fastdis_entity_snapshot_buffer_publish_all(nullptr, table, &view) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_entity_snapshot_buffer_get_stats(nullptr, &buffer_stats) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_entity_snapshot_buffer_reset_stats(nullptr) == FASTDIS_ERR_BAD_ARGUMENT);

    assert(fastdis_scanner_remove_entity_id(scanner, 0x1111u, 0x2222u, 0x3333u) == FASTDIS_OK);
    assert(fastdis_scanner_entity_id_count(scanner) == 0u);
    assert(fastdis_scanner_set_entity_ids(nullptr, FASTDIS_ENTITY_ID_FILTER_ALLOW, allow_ids, 1) == FASTDIS_ERR_BAD_ARGUMENT);
    assert(fastdis_scanner_scan_entity_state_packets(nullptr, scanner_packets, 2, on_entity_state, &scanner_counter, &stats) == FASTDIS_ERR_BAD_ARGUMENT);
    fastdis_scanner_destroy(scanner);

    return 0;
}
