#include <fastdis/fastdis.hpp>
#include <fastdis/fastdis_pdu_catalog.hpp>

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>
#include <utility>

namespace {

void put_be16(uint8_t* p, uint16_t value) {
    p[0] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[1] = static_cast<uint8_t>(value & 0xffu);
}

void put_be32(uint8_t* p, uint32_t value) {
    p[0] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[3] = static_cast<uint8_t>(value & 0xffu);
}

void put_be64(uint8_t* p, uint64_t value) {
    p[0] = static_cast<uint8_t>((value >> 56) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 48) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 40) & 0xffu);
    p[3] = static_cast<uint8_t>((value >> 32) & 0xffu);
    p[4] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[5] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[6] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[7] = static_cast<uint8_t>(value & 0xffu);
}

void put_be_float(uint8_t* p, float value) {
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be32(p, bits);
}

void put_be_double(uint8_t* p, double value) {
    uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be64(p, bits);
}

void put_vec3f(uint8_t* p, float x, float y, float z) {
    put_be_float(p + 0, x);
    put_be_float(p + 4, y);
    put_be_float(p + 8, z);
}

void put_world(uint8_t* p, double x, double y, double z) {
    put_be_double(p + 0, x);
    put_be_double(p + 8, y);
    put_be_double(p + 16, z);
}

void make_entity_state_pdu(uint8_t* p,
                           uint16_t site,
                           uint16_t application,
                           uint16_t entity,
                           double x,
                           uint8_t force_id = 2,
                           uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    std::memset(p, 0, 160);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_ENTITY_STATE_PDU_TYPE;
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_ENTITY_STATE_FIXED_SIZE);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }

    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, site);
    put_be16(b + 2, application);
    put_be16(b + 4, entity);
    b[6] = force_id;
    b[7] = 0;

    b[8] = 1;
    b[9] = 2;
    put_be16(b + 10, 840);
    b[12] = 3;
    b[13] = 4;
    b[14] = 5;
    b[15] = 6;

    put_vec3f(b + 24, 1.25f, -2.5f, 3.75f);
    put_world(b + 36, x, 20.0, 30.0);
    put_vec3f(b + 60, 0.1f, 0.2f, 0.3f);
    put_be32(b + 72, 0xAABBCCDDu);
    b[76] = FASTDIS_DR_RVW;
    for (int i = 0; i < 15; ++i) {
        b[77 + i] = static_cast<uint8_t>(i + 1);
    }
    put_vec3f(b + 92, 0.5f, 0.6f, 0.7f);
    put_vec3f(b + 104, 1.5f, 1.6f, 1.7f);
}

bool nearf(float a, float b) { return std::fabs(a - b) < 0.0001f; }

void put_clock_time(uint8_t* p, uint32_t hour, uint32_t time_past_hour) {
    put_be32(p + 0, hour);
    put_be32(p + 4, time_past_hour);
}

void make_pdu(uint8_t* p, uint8_t version, uint8_t pdu_type, uint16_t length) {
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = pdu_type;
    p[3] = 1;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80u;
        p[11] = 0x00u;
    } else {
        p[10] = 0x12u;
        p[11] = 0x34u;
    }
}

void make_sim_management_pdu(uint8_t* p, uint8_t version, uint8_t pdu_type, uint8_t family, uint16_t length) {
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = pdu_type;
    p[3] = family;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
}

void make_fire_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    std::memset(p, 0, FASTDIS_FIRE_FIXED_SIZE);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_FIRE_PDU_TYPE;
    p[3] = 2;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_FIRE_FIXED_SIZE);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
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

void make_logistics_pdu(uint8_t* p, uint8_t version, uint8_t pdu_type, uint16_t length) {
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = pdu_type;
    p[3] = 3;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
}

void make_designator_pdu(uint8_t* p, uint8_t version) {
    std::memset(p, 0, FASTDIS_DESIGNATOR_FIXED_SIZE);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_DESIGNATOR_PDU_TYPE;
    p[3] = 6;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_DESIGNATOR_FIXED_SIZE);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x1234u);
    put_be16(b + 8, 0x0004u); put_be16(b + 10, 0x0005u); put_be16(b + 12, 0x0006u);
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

void make_other_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_OTHER_PDU_TYPE, FASTDIS_OTHER_FIXED_SIZE + 4u);
    p[3] = 0u;
    p[12] = 0x4Fu; p[13] = 0x54u; p[14] = 0x48u; p[15] = 0x52u;
}

void make_aggregate_state_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_AGGREGATE_STATE_PDU_TYPE, FASTDIS_AGGREGATE_STATE_FIXED_SIZE + 6u);
    p[3] = 7u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    b[6] = 4u;
    b[7] = 5u;
    b[8] = 1u; b[9] = 2u; put_be16(b + 10, 840u); b[12] = 3u; b[13] = 4u; b[14] = 5u; b[15] = 6u;
    put_be32(b + 16, 0x11223344u);
    b[20] = 1u;
    std::memset(b + 21, 0, 31u);
    const char* marking = "AGGREGATE-ALPHA";
    std::memcpy(b + 21, marking, std::strlen(marking));
    put_vec3f(b + 52, 1.0f, 2.0f, 3.0f);
    put_vec3f(b + 64, 0.1f, 0.2f, 0.3f);
    put_world(b + 76, 10.0, 20.0, 30.0);
    put_vec3f(b + 100, 4.0f, 5.0f, 6.0f);
    put_be16(b + 112, 7u); put_be16(b + 114, 8u); put_be16(b + 116, 9u); put_be16(b + 118, 10u);
    b[120] = 0xA1u; b[121] = 0xA2u; b[122] = 0xA3u; b[123] = 0xA4u; b[124] = 0xA5u; b[125] = 0xA6u;
}

void make_is_group_of_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_IS_GROUP_OF_PDU_TYPE, FASTDIS_IS_GROUP_OF_FIXED_SIZE + 4u);
    p[3] = 7u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    b[6] = 0x21u;
    b[7] = 0x02u;
    put_be32(b + 8, 0x10203040u);
    put_be_double(b + 12, 41.25);
    put_be_double(b + 20, -93.5);
    b[28] = 0xB1u; b[29] = 0xB2u; b[30] = 0xB3u; b[31] = 0xB4u;
}

void make_transfer_control_request_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + 4u);
    p[3] = 7u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    put_be16(b + 6, 4u); put_be16(b + 8, 5u); put_be16(b + 10, 6u);
    put_be32(b + 12, 0x11223344u);
    b[16] = 0x07u;
    b[17] = 0x08u;
    put_be16(b + 18, 7u); put_be16(b + 20, 8u); put_be16(b + 22, 9u);
    b[24] = 0x02u;
    b[25] = 0xC1u; b[26] = 0xC2u; b[27] = 0xC3u; b[28] = 0xC4u;
}

void make_transfer_ownership_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE, FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + 4u);
    p[3] = 7u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 10u); put_be16(b + 2, 11u); put_be16(b + 4, 12u);
    put_be16(b + 6, 13u); put_be16(b + 8, 14u); put_be16(b + 10, 15u);
    put_be32(b + 12, 0x55667788u);
    b[16] = 0x09u;
    b[17] = 0x0Au;
    put_be16(b + 18, 16u); put_be16(b + 20, 17u); put_be16(b + 22, 18u);
    b[24] = 0x03u;
    b[25] = 0xD1u; b[26] = 0xD2u; b[27] = 0xD3u; b[28] = 0xD4u;
}

void make_is_part_of_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_IS_PART_OF_PDU_TYPE, FASTDIS_IS_PART_OF_FIXED_SIZE);
    p[3] = 7u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 1u); put_be16(b + 2, 2u); put_be16(b + 4, 3u);
    put_be16(b + 6, 4u); put_be16(b + 8, 5u); put_be16(b + 10, 6u);
    put_be16(b + 12, 0x1112u); put_be16(b + 14, 0x1314u);
    put_vec3f(b + 16, 7.0f, 8.0f, 9.0f);
    put_be16(b + 28, 0x2122u); put_be16(b + 30, 0x2324u);
    b[32] = 2u; b[33] = 3u; put_be16(b + 34, 225u); b[36] = 4u; b[37] = 5u; b[38] = 6u; b[39] = 7u;
}

void make_transmitter_pdu(uint8_t* p, uint8_t version) {
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
        p[10] = 0x80u; p[11] = 0x00u;
    } else {
        p[10] = 0x12u; p[11] = 0x34u;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
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

void make_signal_pdu(uint8_t* p, uint8_t version) {
    const uint16_t length = version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? static_cast<uint16_t>(FASTDIS_SIGNAL_DIS7_FIXED_SIZE + 4u)
                                                                     : static_cast<uint16_t>(FASTDIS_SIGNAL_DIS6_FIXED_SIZE + 4u);
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_SIGNAL_PDU_TYPE;
    p[3] = 4;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    size_t offset = 0u;
    if (version < FASTDIS_PROTOCOL_VERSION_DIS7) {
        put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
        put_be16(b + 6, 0x1111u);
        offset = 8u;
    }
    put_be16(b + offset + 0, 0x2222u);
    put_be16(b + offset + 2, 0x3333u);
    put_be32(b + offset + 4, 48000u);
    put_be16(b + offset + 8, 4u);
    put_be16(b + offset + 10, 2u);
    b[offset + 12] = 0x41u; b[offset + 13] = 0x42u; b[offset + 14] = 0x43u; b[offset + 15] = 0x44u;
}

void make_receiver_pdu(uint8_t* p, uint8_t version) {
    const uint16_t length = version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? FASTDIS_RECEIVER_DIS7_FIXED_SIZE
                                                                     : FASTDIS_RECEIVER_DIS6_FIXED_SIZE;
    std::memset(p, 0, length);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_RECEIVER_PDU_TYPE;
    p[3] = 4;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, length);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    size_t offset = 0u;
    if (version < FASTDIS_PROTOCOL_VERSION_DIS7) {
        put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
        put_be16(b + 6, 0x1111u);
        offset = 8u;
    }
    put_be16(b + offset + 0, 0x2222u);
    put_be16(b + offset + 2, 0x3333u);
    put_be_float(b + offset + 4, 12.5f);
    put_be16(b + offset + 8, 0x0004u); put_be16(b + offset + 10, 0x0005u); put_be16(b + offset + 12, 0x0006u);
    put_be16(b + offset + 14, 0x4444u);
}

void make_iff_atc_navaids_layer1_pdu(uint8_t* p, uint8_t version) {
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
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_vec3f(b + 12, 1.0f, 2.0f, 3.0f);
    put_be16(b + 24, 0x1111u); put_be16(b + 26, 0x2222u); b[28] = 0x33u; b[29] = 0x44u;
    put_be16(b + 30, 0x5555u);
    b[32] = 1u; b[33] = 2u; b[34] = 3u; b[35] = 4u;
    put_be16(b + 36, 5u); put_be16(b + 38, 6u); put_be16(b + 40, 7u); put_be16(b + 42, 8u); put_be16(b + 44, 9u); put_be16(b + 46, 10u);
}

void make_intercom_signal_pdu(uint8_t* p, uint8_t version) {
    std::memset(p, 0, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4u);
    p[0] = version;
    p[1] = 3;
    p[2] = FASTDIS_INTERCOM_SIGNAL_PDU_TYPE;
    p[3] = 4;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4u);
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x1212u);
    put_be16(b + 8, 0x2222u);
    put_be16(b + 10, 0x3333u);
    put_be32(b + 12, 32000u);
    put_be16(b + 16, 4u);
    put_be16(b + 18, 2u);
    b[20] = 0x51u; b[21] = 0x52u; b[22] = 0x53u; b[23] = 0x54u;
}

void make_intercom_control_pdu(uint8_t* p, uint8_t version) {
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
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    b[0] = 0x11u; b[1] = 0x22u;
    put_be16(b + 2, 0x0001u); put_be16(b + 4, 0x0002u); put_be16(b + 6, 0x0003u);
    b[8] = 0x33u; b[9] = 0x44u; b[10] = 0x55u; b[11] = 0x66u; b[12] = 0x77u;
    put_be16(b + 13, 0x0004u); put_be16(b + 15, 0x0005u); put_be16(b + 17, 0x0006u);
    put_be16(b + 19, 0x8888u);
    put_be32(b + 21, 4u);
    b[25] = 0x61u; b[26] = 0x62u; b[27] = 0x63u; b[28] = 0x64u;
}

void make_attribute_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ATTRIBUTE_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_ATTRIBUTE_PDU_TYPE, length);
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
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

void make_directed_energy_fire_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE, length);
    p[3] = 2;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
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

void make_entity_damage_status_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE, length);
    p[3] = 2;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_be16(b + 12, 0x0007u); put_be16(b + 14, 0x0008u); put_be16(b + 16, 0x0009u);
    put_be16(b + 18, 0x1112u);
    put_be16(b + 20, 0x1314u);
    put_be16(b + 22, 1u);
    b[24] = 0xA1u; b[25] = 0xA2u; b[26] = 0xA3u; b[27] = 0xA4u;
}

void make_iff_pdu(uint8_t* p, uint8_t version = 7) {
    make_pdu(p, version, FASTDIS_IFF_PDU_TYPE, FASTDIS_IFF_FIXED_SIZE);
    p[3] = 6;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    put_vec3f(b + 12, 1.0f, 2.0f, 3.0f);
    put_be16(b + 24, 0x1111u); put_be16(b + 26, 0x2222u); b[28] = 0x33u; b[29] = 0x44u;
    put_be16(b + 30, 0x5555u);
    b[32] = 1u; b[33] = 2u; b[34] = 3u; b[35] = 4u;
    put_be16(b + 36, 5u); put_be16(b + 38, 6u); put_be16(b + 40, 7u); put_be16(b + 42, 8u); put_be16(b + 44, 9u); put_be16(b + 46, 10u);
}

void make_electronic_emissions_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE + 6u);
    make_pdu(p, version, FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE, length);
    p[3] = 6;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    b[12] = 0x07u; b[13] = 0x02u; put_be16(b + 14, 0x0809u);
    b[16] = 0xE1u; b[17] = 0xE2u; b[18] = 0xE3u; b[19] = 0xE4u; b[20] = 0xE5u; b[21] = 0xE6u;
}

void make_information_operations_action_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE, length);
    p[3] = 13;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
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

void make_information_operations_report_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE + 4u);
    make_pdu(p, version, FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE, length);
    p[3] = 13;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0102u); b[8] = 0x03u; b[9] = 0x04u;
    put_be16(b + 10, 0x0004u); put_be16(b + 12, 0x0005u); put_be16(b + 14, 0x0006u);
    put_be16(b + 16, 0x0007u); put_be16(b + 18, 0x0008u); put_be16(b + 20, 0x0009u);
    put_be16(b + 22, 0x1112u); put_be16(b + 24, 0x1314u); put_be16(b + 26, 1u);
    b[28] = 0xD1u; b[29] = 0xD2u; b[30] = 0xD3u; b[31] = 0xD4u;
}

void make_ua_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_UA_FIXED_SIZE + 8u);
    make_pdu(p, version, FASTDIS_UA_PDU_TYPE, length);
    p[3] = 6;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0001u); put_be16(b + 2, 0x0002u); put_be16(b + 4, 0x0003u);
    put_be16(b + 6, 0x0004u); put_be16(b + 8, 0x0005u); put_be16(b + 10, 0x0006u);
    b[12] = 0x0Au; b[13] = 0x0Bu; put_be16(b + 14, 0x0C0Du);
    b[16] = 0x0Eu; b[17] = 0x01u; b[18] = 0x02u; b[19] = 0x03u;
    b[20] = 0xF1u; b[21] = 0xF2u; b[22] = 0xF3u; b[23] = 0xF4u; b[24] = 0xF5u; b[25] = 0xF6u; b[26] = 0xF7u; b[27] = 0xF8u;
}

void make_sees_pdu(uint8_t* p, uint8_t version = 7) {
    const uint16_t length = static_cast<uint16_t>(FASTDIS_SEES_FIXED_SIZE + 8u);
    make_pdu(p, version, FASTDIS_SEES_PDU_TYPE, length);
    p[3] = 6;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 0x0011u); put_be16(b + 2, 0x0022u); put_be16(b + 4, 0x0033u);
    put_be16(b + 6, 0x1112u); put_be16(b + 8, 0x1314u); put_be16(b + 10, 0x1516u);
    put_be16(b + 12, 0x0002u); put_be16(b + 14, 0x0003u);
    b[16] = 0xAAu; b[17] = 0xBBu; b[18] = 0xCCu; b[19] = 0xDDu; b[20] = 0xEEu; b[21] = 0xFFu; b[22] = 0x00u; b[23] = 0x11u;
}

void make_minefield_state_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_MINEFIELD_STATE_PDU_TYPE, 104u);
    p[3] = 8u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
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

void make_minefield_query_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_MINEFIELD_QUERY_PDU_TYPE, 60u);
    p[3] = 8u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 201u); put_be16(b + 2, 202u); put_be16(b + 4, 203u);
    put_be16(b + 6, 204u); put_be16(b + 8, 205u); put_be16(b + 10, 206u);
    b[12] = 207u; b[13] = 2u; b[14] = 0u; b[15] = 2u; put_be32(b + 16, 0x01020304u);
    b[20] = 3u; b[21] = 4u; put_be16(b + 22, 225u); b[24] = 5u; b[25] = 6u; b[26] = 7u; b[27] = 8u;
    put_be_float(b + 28, 1.5f); put_be_float(b + 32, 2.5f); put_be_float(b + 36, 3.5f); put_be_float(b + 40, 4.5f);
    b[44] = 0x11u; b[45] = 0x12u; b[46] = 0x21u; b[47] = 0x22u;
}

void make_minefield_data_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_MINEFIELD_DATA_PDU_TYPE, 73u);
    p[3] = 8u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 251u); put_be16(b + 2, 252u); put_be16(b + 4, 253u);
    put_be16(b + 6, 254u); put_be16(b + 8, 255u); put_be16(b + 10, 256u);
    put_be16(b + 12, 257u); b[14] = 200u; b[15] = 3u; b[16] = 2u; b[17] = 2u; b[18] = 2u; b[19] = 0u;
    put_be32(b + 20, 0x01020304u);
    b[24] = 37u; b[25] = 38u; put_be16(b + 26, 225u); b[28] = 39u; b[29] = 40u; b[30] = 41u; b[31] = 42u;
    b[32] = 0x31u; b[33] = 0x32u; b[34] = 0x41u; b[35] = 0x42u; b[36] = 0u;
    put_vec3f(b + 37, 9.5f, 10.5f, 11.5f);
    put_vec3f(b + 49, 12.5f, 13.5f, 14.5f);
}

void make_minefield_response_nack_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE, 42u);
    p[3] = 8u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 181u); put_be16(b + 2, 182u); put_be16(b + 4, 183u);
    put_be16(b + 6, 184u); put_be16(b + 8, 185u); put_be16(b + 10, 186u);
    b[12] = 187u; b[13] = 2u;
    for (int i = 0; i < 8; ++i) {
        b[14 + i] = static_cast<uint8_t>(i + 1);
        b[22 + i] = static_cast<uint8_t>(0x11u + i);
    }
}

void make_environmental_process_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE, static_cast<uint16_t>(FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE + 10u));
    p[3] = 9u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 211u); put_be16(b + 2, 212u); put_be16(b + 4, 213u);
    b[6] = 9u; b[7] = 10u; put_be16(b + 8, 840u); b[10] = 11u; b[11] = 12u; b[12] = 13u; b[13] = 14u;
    b[14] = 15u; b[15] = 16u; b[16] = 2u; put_be16(b + 17, 0x1718u);
    std::memcpy(b + 19, "\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3A", 10);
}

void make_gridded_data_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS7) {
    make_pdu(p, version, FASTDIS_GRIDDED_DATA_PDU_TYPE, static_cast<uint16_t>(FASTDIS_GRIDDED_DATA_FIXED_SIZE + 10u));
    p[3] = 9u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, 261u); put_be16(b + 2, 262u); put_be16(b + 4, 263u);
    put_be16(b + 6, 264u); put_be16(b + 8, 265u); put_be16(b + 10, 266u); put_be16(b + 12, 267u);
    b[14] = 3u; b[15] = 1u;
    b[16] = 43u; b[17] = 44u; put_be16(b + 18, 840u); b[20] = 45u; b[21] = 46u; b[22] = 47u; b[23] = 48u;
    put_vec3f(b + 24, 0.7f, 0.8f, 0.9f);
    put_be64(b + 36, 0x0102030405060708ull);
    put_be32(b + 44, 269u); b[48] = 4u; put_be16(b + 49, 270u); b[51] = 0u;
    std::memcpy(b + 52, "\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5A", 10);
}

void make_point_object_state_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    const uint16_t length = version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE : FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE;
    make_pdu(p, version, FASTDIS_POINT_OBJECT_STATE_PDU_TYPE, length);
    p[3] = 9u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        put_be16(b + 0, 71u); put_be16(b + 2, 72u); put_be16(b + 4, 73u);
        put_be16(b + 6, 74u); put_be16(b + 8, 75u); put_be16(b + 10, 76u);
        put_be16(b + 12, 77u); b[14] = 78u; b[15] = 79u;
        b[16] = 4u; b[17] = 5u; b[18] = 6u; b[19] = 7u;
        put_world(b + 20, 400.25, 500.5, 600.75); put_vec3f(b + 44, 0.4f, 0.5f, 0.6f); put_be_double(b + 56, 2345.5);
        put_be16(b + 64, 80u); put_be16(b + 66, 81u); put_be16(b + 68, 82u); put_be16(b + 70, 83u); put_be32(b + 72, 84u);
    } else {
        put_be16(b + 0, 51u); put_be16(b + 2, 52u); put_be16(b + 4, 53u);
        put_be16(b + 6, 54u); put_be16(b + 8, 55u); put_be16(b + 10, 56u);
        put_be16(b + 12, 57u); b[14] = 58u; b[15] = 59u;
        b[16] = 1u; b[17] = 2u; put_be16(b + 18, 840u); b[20] = 3u; b[21] = 4u;
        put_world(b + 22, 100.25, 200.5, 300.75); put_vec3f(b + 46, 0.1f, 0.2f, 0.3f); put_be_double(b + 58, 1234.5);
        put_be16(b + 66, 60u); put_be16(b + 68, 61u); put_be16(b + 70, 62u); put_be16(b + 72, 63u); put_be32(b + 74, 64u);
    }
}

void make_linear_object_state_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    const uint16_t length = version >= FASTDIS_PROTOCOL_VERSION_DIS7 ? static_cast<uint16_t>(FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE)
                                                                     : static_cast<uint16_t>(FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE);
    make_pdu(p, version, FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE, length);
    p[3] = 9u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
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

void make_areal_object_state_pdu(uint8_t* p, uint8_t version = FASTDIS_PROTOCOL_VERSION_DIS6) {
    make_pdu(p, version, FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE, static_cast<uint16_t>(FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u));
    p[3] = 9u;
    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    if (version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
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

} // namespace

int main() {
    assert(fastdis_abi_version() == FASTDIS_ABI_VERSION);
    assert(fastdis::abi_version() == FASTDIS_ABI_VERSION);
    assert(fastdis::abi_epoch() == FASTDIS_ABI_EPOCH);
    assert(fastdis::abi_revision() == FASTDIS_ABI_REVISION);
    assert(fastdis::abi_epoch_constant == 0u);
    assert(fastdis::abi_revision_constant == 16u);
    assert(fastdis::abi_version_constant == fastdis::abi_revision_constant);
    assert(fastdis::pdu_catalog_count == FASTDIS_PDU_CATALOG_COUNT);
    const fastdis::PduCatalogEntry* entity_state_entry =
        fastdis::find_pdu(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_PDU_TYPE_ENTITY_STATE);
    assert(entity_state_entry != nullptr);
    assert(entity_state_entry->has_body_decoder == 1u);
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_PDU_TYPE_ENTITY_STATE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_PDU_TYPE_ENTITY_STATE_UPDATE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_PDU_TYPE_FIRE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_PDU_TYPE_DETONATION));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_ACKNOWLEDGE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_SERVICE_REQUEST_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RESUPPLY_OFFER_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RESUPPLY_CANCEL_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_REPAIR_COMPLETE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_REPAIR_RESPONSE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_START_RESUME_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RECORD_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE));
    assert(fastdis::has_body_decoder(FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_MINEFIELD_STATE_PDU_TYPE));

    std::array<uint8_t, 160> p1{};
    std::array<uint8_t, 160> p2{};
    make_entity_state_pdu(p1.data(), 0x1111u, 0x2222u, 0x3333u, 10.0);
    make_entity_state_pdu(p2.data(), 0x1111u, 0x2222u, 0x4444u, 40.0);

    fastdis::Header header = fastdis::parse_header(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(header.version == 7u);
    assert(header.pdu_type == FASTDIS_ENTITY_STATE_PDU_TYPE);
    assert(fastdis::protocol_version_dis6 == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(fastdis::protocol_version_dis7 == FASTDIS_PROTOCOL_VERSION_DIS7);
    assert(fastdis::header_status_unavailable == FASTDIS_HEADER_STATUS_UNAVAILABLE);
    assert(fastdis::header_has_pdu_status(header));
    assert(fastdis::header_pdu_status(header) == 0x80u);
    assert(fastdis::header_padding_octet(header) == 0u);
    assert(fastdis::header_legacy_padding(header) == 0u);

    std::array<uint8_t, 160> dis6{};
    make_entity_state_pdu(dis6.data(), 0x1111u, 0x2222u, 0x5555u, 70.0, 2, FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::Header dis6_header = fastdis::parse_header(dis6.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(!fastdis::header_has_pdu_status(dis6_header));
    assert(dis6_header.status == FASTDIS_HEADER_STATUS_UNAVAILABLE);
    assert(fastdis::header_pdu_status(dis6_header) == 0u);
    assert(fastdis::header_legacy_padding(dis6_header) == 0x1234u);

    fastdis::Header try_header{};
    assert(fastdis::try_parse_header(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE, try_header) == FASTDIS_OK);
    assert(try_header.protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);

    fastdis::EntityTransform transform = fastdis::parse_entity_transform(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(transform.entity_id.site == 0x1111u);
    assert(transform.location.x == 10.0);
    assert(nearf(transform.orientation.theta, 0.2f));
    assert(transform.dead_reckoning_algorithm == fastdis::dr_rvw);
    assert(fastdis::dead_reckoning_algorithm_known(transform.dead_reckoning_algorithm));
    assert(std::string(fastdis::dead_reckoning_algorithm_name(transform.dead_reckoning_algorithm)) == "DRM_RVW");
    fastdis::EntityTransform dead_reckoned_transform = fastdis::extrapolate_entity_transform_dead_reckoning(transform, 2.0);
    assert(std::fabs(dead_reckoned_transform.location.x - 13.5) < 0.0001);
    assert(std::fabs(dead_reckoned_transform.location.y - 16.2) < 0.0001);
    assert(std::fabs(dead_reckoned_transform.location.z - 38.9) < 0.0001);

    std::array<uint8_t, FASTDIS_FIRE_FIXED_SIZE> fire{};
    make_fire_pdu(fire.data());
    fastdis::Fire fire_event = fastdis::parse_fire(fire.data(), fire.size());
    assert(fire_event.header.pdu_type == FASTDIS_FIRE_PDU_TYPE);
    assert(fire_event.firing_entity_id.entity == 0x0003u);
    assert(fire_event.target_entity_id.entity == 0x0006u);
    assert(fire_event.event_id.event_number == 0x000Cu);
    assert(fire_event.munition_descriptor.rate == 600u);
    assert(nearf(fire_event.velocity.y, 2.5f));

    std::array<uint8_t, FASTDIS_OTHER_FIXED_SIZE + 4u> other6{};
    make_other_pdu(other6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::OtherPdu other_event = fastdis::parse_other_pdu(other6.data(), other6.size());
    assert(other_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(other_event.header.protocol_family == 0u);
    assert(other_event.opaque_payload.bytes_size == 4u);
    assert(other_event.opaque_payload.bytes[0] == 0x4Fu);

    std::array<uint8_t, FASTDIS_AGGREGATE_STATE_FIXED_SIZE + 6u> aggregate_state7{};
    make_aggregate_state_pdu(aggregate_state7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::AggregateState aggregate_state_event = fastdis::parse_aggregate_state(aggregate_state7.data(), aggregate_state7.size());
    assert(aggregate_state_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS7);
    assert(aggregate_state_event.aggregate_id.entity == 3u);
    assert(aggregate_state_event.force_id == 4u);
    assert(aggregate_state_event.aggregate_state == 5u);
    assert(aggregate_state_event.aggregate_type.country == 840u);
    assert(aggregate_state_event.formation == 0x11223344u);
    assert(aggregate_state_event.aggregate_marking_character_set == 1u);
    assert(std::strncmp(reinterpret_cast<const char*>(aggregate_state_event.aggregate_marking), "AGGREGATE-ALPHA", 15) == 0);
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

    std::array<uint8_t, FASTDIS_IS_GROUP_OF_FIXED_SIZE + 4u> is_group_of6{};
    make_is_group_of_pdu(is_group_of6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::IsGroupOf is_group_of_event = fastdis::parse_is_group_of(is_group_of6.data(), is_group_of6.size());
    assert(is_group_of_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(is_group_of_event.group_entity_id.entity == 3u);
    assert(is_group_of_event.grouped_entity_category == 0x21u);
    assert(is_group_of_event.number_of_grouped_entities == 0x02u);
    assert(is_group_of_event.pad2 == 0x10203040u);
    assert(std::fabs(is_group_of_event.latitude - 41.25) < 0.0001);
    assert(std::fabs(is_group_of_event.longitude + 93.5) < 0.0001);
    assert(is_group_of_event.grouped_entity_descriptions.bytes_size == 4u);
    assert(is_group_of_event.grouped_entity_descriptions.bytes[0] == 0xB1u);

    std::array<uint8_t, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE + 4u> transfer_control_request6{};
    make_transfer_control_request_pdu(transfer_control_request6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::TransferControlRequest transfer_control_request_event =
        fastdis::parse_transfer_control_request(transfer_control_request6.data(), transfer_control_request6.size());
    assert(transfer_control_request_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(transfer_control_request_event.originating_entity_id.entity == 3u);
    assert(transfer_control_request_event.receiving_entity_id.site == 4u);
    assert(transfer_control_request_event.request_id == 0x11223344u);
    assert(transfer_control_request_event.required_reliability_service == 0x07u);
    assert(transfer_control_request_event.transfer_type == 0x08u);
    assert(transfer_control_request_event.transfer_entity_id.entity == 9u);
    assert(transfer_control_request_event.number_of_record_sets == 0x02u);
    assert(transfer_control_request_event.record_sets.bytes_size == 4u);
    assert(transfer_control_request_event.record_sets.bytes[0] == 0xC1u);

    std::array<uint8_t, FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE + 4u> transfer_ownership7{};
    make_transfer_ownership_pdu(transfer_ownership7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::TransferOwnership transfer_ownership_event =
        fastdis::parse_transfer_ownership(transfer_ownership7.data(), transfer_ownership7.size());
    assert(transfer_ownership_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS7);
    assert(transfer_ownership_event.originating_entity_id.site == 10u);
    assert(transfer_ownership_event.receiving_entity_id.entity == 15u);
    assert(transfer_ownership_event.request_id == 0x55667788u);
    assert(transfer_ownership_event.required_reliability_service == 0x09u);
    assert(transfer_ownership_event.transfer_type == 0x0Au);
    assert(transfer_ownership_event.transfer_entity_id.application == 17u);
    assert(transfer_ownership_event.number_of_record_sets == 0x03u);
    assert(transfer_ownership_event.record_sets.bytes_size == 4u);
    assert(transfer_ownership_event.record_sets.bytes[0] == 0xD1u);

    std::array<uint8_t, FASTDIS_IS_PART_OF_FIXED_SIZE> is_part_of7{};
    make_is_part_of_pdu(is_part_of7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::IsPartOf is_part_of_event = fastdis::parse_is_part_of(is_part_of7.data(), is_part_of7.size());
    assert(is_part_of_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS7);
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
    make_minefield_state_pdu(minefield_state6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::MinefieldState minefield_state_event = fastdis::parse_minefield_state(minefield_state6.data(), minefield_state6.size());
    assert(minefield_state_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
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
    make_minefield_query_pdu(minefield_query6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::MinefieldQuery minefield_query_event = fastdis::parse_minefield_query(minefield_query6.data(), minefield_query6.size());
    assert(minefield_query_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
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
    make_minefield_data_pdu(minefield_data7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::MinefieldData minefield_data_event = fastdis::parse_minefield_data(minefield_data7.data(), minefield_data7.size());
    assert(minefield_data_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS7);
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
    make_minefield_response_nack_pdu(minefield_nack6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::MinefieldResponseNack minefield_nack_event = fastdis::parse_minefield_response_nack(minefield_nack6.data(), minefield_nack6.size());
    assert(minefield_nack_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(minefield_nack_event.minefield_id.entity == 183u);
    assert(minefield_nack_event.requesting_entity_id.entity == 186u);
    assert(minefield_nack_event.request_id == 187u);
    assert(minefield_nack_event.number_of_missing_pdus == 2u);
    assert(minefield_nack_event.missing_pdu_sequence_numbers.bytes_size == 16u);

    std::array<uint8_t, FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE + 10u> environmental_process6{};
    make_environmental_process_pdu(environmental_process6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::EnvironmentalProcess environmental_process_event =
        fastdis::parse_environmental_process(environmental_process6.data(), environmental_process6.size());
    assert(environmental_process_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS6);
    assert(environmental_process_event.environmental_process_id.entity == 213u);
    assert(environmental_process_event.environment_type.country == 840u);
    assert(environmental_process_event.model_type == 15u);
    assert(environmental_process_event.environment_status == 16u);
    assert(environmental_process_event.number_of_environment_records == 2u);
    assert(environmental_process_event.sequence_number == 0x1718u);
    assert(environmental_process_event.environment_records.bytes_size == 10u);

    std::array<uint8_t, FASTDIS_GRIDDED_DATA_FIXED_SIZE + 10u> gridded_data7{};
    make_gridded_data_pdu(gridded_data7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::GriddedData gridded_data_event = fastdis::parse_gridded_data(gridded_data7.data(), gridded_data7.size());
    assert(gridded_data_event.header.version == FASTDIS_PROTOCOL_VERSION_DIS7);
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
    make_point_object_state_pdu(point_object_state6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::PointObjectState point_object_state_event6 = fastdis::parse_point_object_state(point_object_state6.data(), point_object_state6.size());
    assert(point_object_state_event6.object_id.entity == 53u);
    assert(point_object_state_event6.object_type.domain == 2u);
    assert(point_object_state_event6.object_type.kind == 1u);
    assert(point_object_state_event6.object_type.country == 840u);
    assert(nearf(point_object_state_event6.object_orientation.phi, 0.3f));
    assert(std::fabs(point_object_state_event6.object_appearance - 1234.5) < 0.0001);

    std::array<uint8_t, FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE> point_object_state7{};
    make_point_object_state_pdu(point_object_state7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::PointObjectState point_object_state_event7 = fastdis::parse_point_object_state(point_object_state7.data(), point_object_state7.size());
    assert(point_object_state_event7.object_id.entity == 73u);
    assert(point_object_state_event7.object_type.domain == 4u);
    assert(point_object_state_event7.object_type.kind == 5u);
    assert(point_object_state_event7.object_type.country == 0u);
    assert(std::fabs(point_object_state_event7.object_location.z - 600.75) < 0.0001);

    std::array<uint8_t, FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE> linear_object_state6{};
    make_linear_object_state_pdu(linear_object_state6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::LinearObjectState linear_object_state_event6 = fastdis::parse_linear_object_state(linear_object_state6.data(), linear_object_state6.size());
    assert(linear_object_state_event6.object_id.entity == 133u);
    assert(linear_object_state_event6.number_of_segments == 2u);
    assert(linear_object_state_event6.object_type.domain == 10u);
    assert(linear_object_state_event6.object_type.kind == 9u);
    assert(linear_object_state_event6.linear_segment_parameters.bytes_size == 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE);

    std::array<uint8_t, FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE + 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE> linear_object_state7{};
    make_linear_object_state_pdu(linear_object_state7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::LinearObjectState linear_object_state_event7 = fastdis::parse_linear_object_state(linear_object_state7.data(), linear_object_state7.size());
    assert(linear_object_state_event7.object_id.entity == 153u);
    assert(linear_object_state_event7.object_type.domain == 13u);
    assert(linear_object_state_event7.object_type.kind == 14u);
    assert(linear_object_state_event7.linear_segment_parameters.bytes_size == 2u * FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE);

    std::array<uint8_t, FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u> areal_object_state6{};
    make_areal_object_state_pdu(areal_object_state6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::ArealObjectState areal_object_state_event6 = fastdis::parse_areal_object_state(areal_object_state6.data(), areal_object_state6.size());
    assert(areal_object_state_event6.object_id.entity == 93u);
    assert(areal_object_state_event6.object_type.country == 225u);
    assert(areal_object_state_event6.object_appearance.bytes_size == 6u);
    assert(areal_object_state_event6.number_of_points == 2u);
    assert(areal_object_state_event6.object_locations.bytes_size == 48u);

    std::array<uint8_t, FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE + 48u> areal_object_state7{};
    make_areal_object_state_pdu(areal_object_state7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::ArealObjectState areal_object_state_event7 = fastdis::parse_areal_object_state(areal_object_state7.data(), areal_object_state7.size());
    assert(areal_object_state_event7.object_id.entity == 113u);
    assert(areal_object_state_event7.object_type.country == 124u);
    assert(areal_object_state_event7.object_appearance.bytes_size == 6u);
    assert(areal_object_state_event7.number_of_points == 2u);
    assert(areal_object_state_event7.object_locations.bytes_size == 48u);

    std::array<uint8_t, FASTDIS_ACKNOWLEDGE_FIXED_SIZE> acknowledge{};
    make_sim_management_pdu(acknowledge.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_ACKNOWLEDGE_PDU_TYPE, 5u, FASTDIS_ACKNOWLEDGE_FIXED_SIZE);
    uint8_t* ab = acknowledge.data() + FASTDIS_HEADER_SIZE;
    put_be16(ab + 0, 0x1111u); put_be16(ab + 2, 0x2222u); put_be16(ab + 4, 0x3333u);
    put_be16(ab + 6, 0x4444u); put_be16(ab + 8, 0x5555u); put_be16(ab + 10, 0x6666u);
    put_be16(ab + 12, 0x1234u); put_be16(ab + 14, 0x5678u); put_be32(ab + 16, 0xCAFEBABEu);
    fastdis::Acknowledge acknowledge_event = fastdis::parse_acknowledge(acknowledge.data(), acknowledge.size());
    assert(acknowledge_event.acknowledge_flag == 0x1234u);
    assert(acknowledge_event.response_flag == 0x5678u);
    assert(acknowledge_event.request_id == 0xCAFEBABEu);

    std::array<uint8_t, FASTDIS_DESIGNATOR_FIXED_SIZE> designator{};
    make_designator_pdu(designator.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Designator designator_event = fastdis::parse_designator(designator.data(), designator.size());
    assert(designator_event.header.protocol_family == 6u);
    assert(designator_event.designating_entity_id.entity == 0x0003u);
    assert(designator_event.code_name == 0x1234u);
    assert(designator_event.designated_entity_id.entity == 0x0006u);
    assert(designator_event.designator_code == 0x2345u);
    assert(nearf(designator_event.designator_power, 12.5f));
    assert(nearf(designator_event.entity_linear_acceleration.z, 7.5f));

    std::array<uint8_t, FASTDIS_TRANSMITTER_FIXED_SIZE + 3u> transmitter6{};
    make_transmitter_pdu(transmitter6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::Transmitter transmitter_event6 = fastdis::parse_transmitter(transmitter6.data(), transmitter6.size());
    assert(transmitter_event6.header.version == 6u);
    assert(transmitter_event6.entity_id.entity == 0x0003u);
    assert(transmitter_event6.radio_id == 0x1212u);
    assert(transmitter_event6.radio_entity_type.nomenclature == 0x0708u);
    assert(transmitter_event6.modulation_parameter_count == 3u);
    assert(transmitter_event6.modulation_parameters.bytes_size == 3u);

    std::array<uint8_t, FASTDIS_TRANSMITTER_FIXED_SIZE + 24u> transmitter7{};
    make_transmitter_pdu(transmitter7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Transmitter transmitter_event7 = fastdis::parse_transmitter(transmitter7.data(), transmitter7.size());
    assert(transmitter_event7.header.version == 7u);
    assert(transmitter_event7.entity_type.country == 840u);
    assert(transmitter_event7.variable_transmitter_parameter_count == 2u);
    assert(transmitter_event7.frequency == 225000u);
    assert(nearf(transmitter_event7.transmit_frequency_bandwidth, 50.5f));
    assert(transmitter_event7.modulation_parameters.bytes_size == 12u);
    assert(transmitter_event7.antenna_patterns.bytes_size == 12u);

    std::array<uint8_t, FASTDIS_SIGNAL_DIS6_FIXED_SIZE + 4u> signal6{};
    make_signal_pdu(signal6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::Signal signal_event6 = fastdis::parse_signal(signal6.data(), signal6.size());
    assert(signal_event6.header.version == 6u);
    assert(signal_event6.entity_id.entity == 0x0003u);
    assert(signal_event6.radio_id == 0x1111u);
    assert(signal_event6.encoding_scheme == 0x2222u);
    assert(signal_event6.data.count == 4u);
    assert(signal_event6.data.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_RECEIVER_DIS7_FIXED_SIZE> receiver7{};
    make_receiver_pdu(receiver7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Receiver receiver_event7 = fastdis::parse_receiver(receiver7.data(), receiver7.size());
    assert(receiver_event7.header.version == 7u);
    assert(receiver_event7.entity_id.entity == 0u);
    assert(receiver_event7.receiver_state == 0x2222u);
    assert(nearf(receiver_event7.received_power, 12.5f));
    assert(receiver_event7.transmitter_entity_id.entity == 0x0006u);

    std::array<uint8_t, FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE> iff7{};
    make_iff_atc_navaids_layer1_pdu(iff7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::IffAtcNavAidsLayer1 iff_event7 = fastdis::parse_iff_atc_navaids_layer1(iff7.data(), iff7.size());
    assert(iff_event7.header.protocol_family == 6u);
    assert(iff_event7.emitting_entity_id.entity == 0x0003u);
    assert(iff_event7.event_id.event_number == 0x0006u);
    assert(nearf(iff_event7.location.y, 2.0f));
    assert(iff_event7.system_id.system_name == 0x2222u);
    assert(iff_event7.fundamental_parameters.parameter6 == 10u);

    std::array<uint8_t, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE + 4u> intercom7{};
    make_intercom_signal_pdu(intercom7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::IntercomSignal intercom_event7 = fastdis::parse_intercom_signal(intercom7.data(), intercom7.size());
    assert(intercom_event7.header.version == 7u);
    assert(intercom_event7.entity_id.entity == 0x0003u);
    assert(intercom_event7.communications_device_id == 0x1212u);
    assert(intercom_event7.data.count == 4u);
    assert(intercom_event7.data.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_INTERCOM_CONTROL_FIXED_SIZE + 4u> intercom_control7{};
    make_intercom_control_pdu(intercom_control7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::IntercomControl intercom_control_event7 = fastdis::parse_intercom_control(intercom_control7.data(), intercom_control7.size());
    assert(intercom_control_event7.header.protocol_family == 4u);
    assert(intercom_control_event7.control_type == 0x11u);
    assert(intercom_control_event7.source_entity_id.entity == 0x0003u);
    assert(intercom_control_event7.command == 0x77u);
    assert(intercom_control_event7.master_communications_device_id == 0x8888u);
    assert(intercom_control_event7.intercom_parameters.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_ATTRIBUTE_FIXED_SIZE + 4u> attribute7{};
    make_attribute_pdu(attribute7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Attribute attribute_event7 = fastdis::parse_attribute(attribute7.data(), attribute7.size());
    assert(attribute_event7.header.protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);
    assert(attribute_event7.originating_simulation_address.site == 0x0101u);
    assert(attribute_event7.originating_simulation_address.application == 0x0202u);
    assert(attribute_event7.padding1 == 0x11223344);
    assert(attribute_event7.padding2 == 0x5566);
    assert(attribute_event7.attribute_record_pdu_type == 67u);
    assert(attribute_event7.attribute_record_protocol_version == 7u);
    assert(attribute_event7.master_attribute_record_type == 0x778899AAu);
    assert(attribute_event7.action_code == 0x12u);
    assert(attribute_event7.padding3 == 0x34);
    assert(attribute_event7.number_attribute_record_set == 1u);
    assert(attribute_event7.attribute_record_sets.count == 1u);
    assert(attribute_event7.attribute_record_sets.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE + 4u> directed_energy_fire7{};
    make_directed_energy_fire_pdu(directed_energy_fire7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::DirectedEnergyFire directed_energy_fire_event7 = fastdis::parse_directed_energy_fire(directed_energy_fire7.data(), directed_energy_fire7.size());
    assert(directed_energy_fire_event7.header.protocol_family == 2u);
    assert(directed_energy_fire_event7.firing_entity_id.entity == 0x0003u);
    assert(directed_energy_fire_event7.target_entity_id.entity == 0x0006u);
    assert(directed_energy_fire_event7.munition_type.country == 225u);
    assert(directed_energy_fire_event7.shot_start_time.hour == 7u);
    assert(directed_energy_fire_event7.shot_start_time.time_past_hour == 123456u);
    assert(nearf(directed_energy_fire_event7.commulative_shot_time, 1.25f));
    assert(nearf(directed_energy_fire_event7.aperture_emitter_location.z, 4.5f));
    assert(nearf(directed_energy_fire_event7.aperture_diameter, 5.5f));
    assert(nearf(directed_energy_fire_event7.wavelength, 6.5f));
    assert(nearf(directed_energy_fire_event7.peak_irradiance, 7.5f));
    assert(nearf(directed_energy_fire_event7.pulse_repetition_frequency, 8.5f));
    assert(directed_energy_fire_event7.pulse_width == 9012);
    assert(directed_energy_fire_event7.flags == 0x10203040);
    assert(directed_energy_fire_event7.pulse_shape == 0x11);
    assert(directed_energy_fire_event7.padding1 == 0x22u);
    assert(directed_energy_fire_event7.padding2 == 0x33445566u);
    assert(directed_energy_fire_event7.padding3 == 0x7788u);
    assert(directed_energy_fire_event7.number_of_de_records == 1u);
    assert(directed_energy_fire_event7.de_records.count == 1u);
    assert(directed_energy_fire_event7.de_records.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE + 4u> entity_damage_status7{};
    make_entity_damage_status_pdu(entity_damage_status7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::EntityDamageStatus entity_damage_status_event7 = fastdis::parse_entity_damage_status(entity_damage_status7.data(), entity_damage_status7.size());
    assert(entity_damage_status_event7.header.protocol_family == 2u);
    assert(entity_damage_status_event7.firing_entity_id.entity == 0x0003u);
    assert(entity_damage_status_event7.target_entity_id.entity == 0x0006u);
    assert(entity_damage_status_event7.damaged_entity_id.entity == 0x0009u);
    assert(entity_damage_status_event7.padding1 == 0x1112u);
    assert(entity_damage_status_event7.padding2 == 0x1314u);
    assert(entity_damage_status_event7.number_of_damage_description == 1u);
    assert(entity_damage_status_event7.damage_description_records.count == 1u);
    assert(entity_damage_status_event7.damage_description_records.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_IFF_FIXED_SIZE> iff_pdu7{};
    make_iff_pdu(iff_pdu7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Iff iff_dis7_event = fastdis::parse_iff(iff_pdu7.data(), iff_pdu7.size());
    assert(iff_dis7_event.header.protocol_family == 6u);
    assert(iff_dis7_event.emitting_entity_id.entity == 0x0003u);
    assert(iff_dis7_event.event_id.event_number == 0x0006u);
    assert(nearf(iff_dis7_event.location.y, 2.0f));
    assert(iff_dis7_event.system_id.system_name == 0x2222u);
    assert(iff_dis7_event.padding2 == 0x5555u);
    assert(iff_dis7_event.fundamental_parameters.parameter6 == 10u);

    std::array<uint8_t, FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE + 6u> emissions6{};
    make_electronic_emissions_pdu(emissions6.data(), FASTDIS_PROTOCOL_VERSION_DIS6);
    fastdis::ElectronicEmissions emissions_event6 = fastdis::parse_electronic_emissions(emissions6.data(), emissions6.size());
    assert(emissions_event6.header.protocol_family == 6u);
    assert(emissions_event6.emitting_entity_id.entity == 0x0003u);
    assert(emissions_event6.event_id.event_number == 0x0006u);
    assert(emissions_event6.state_update_indicator == 0x07u);
    assert(emissions_event6.number_of_systems == 0x02u);
    assert(emissions_event6.padding1 == 0x0809u);
    assert(emissions_event6.system_records.count == 2u);
    assert(emissions_event6.system_records.bytes_size == 6u);

    std::array<uint8_t, FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE + 4u> io_action7{};
    make_information_operations_action_pdu(io_action7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::InformationOperationsAction io_action_event7 = fastdis::parse_information_operations_action(io_action7.data(), io_action7.size());
    assert(io_action_event7.header.protocol_family == 13u);
    assert(io_action_event7.originating_sim_id.entity == 0x0003u);
    assert(io_action_event7.receiving_sim_id.entity == 0x0006u);
    assert(io_action_event7.request_id == 0x11223344u);
    assert(io_action_event7.io_warfare_type == 0x0102u);
    assert(io_action_event7.io_simulation_source == 0x0304u);
    assert(io_action_event7.io_action_type == 0x0506u);
    assert(io_action_event7.io_action_phase == 0x0708u);
    assert(io_action_event7.padding1 == 0x55667788u);
    assert(io_action_event7.io_attacker_id.entity == 0x0009u);
    assert(io_action_event7.io_primary_target_id.entity == 0x000Cu);
    assert(io_action_event7.padding2 == 0x090Au);
    assert(io_action_event7.number_of_io_records == 1u);
    assert(io_action_event7.io_records.count == 1u);
    assert(io_action_event7.io_records.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE + 4u> io_report7{};
    make_information_operations_report_pdu(io_report7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::InformationOperationsReport io_report_event7 = fastdis::parse_information_operations_report(io_report7.data(), io_report7.size());
    assert(io_report_event7.header.protocol_family == 13u);
    assert(io_report_event7.originating_sim_id.entity == 0x0003u);
    assert(io_report_event7.io_sim_source == 0x0102u);
    assert(io_report_event7.io_report_type == 0x03u);
    assert(io_report_event7.padding1 == 0x04u);
    assert(io_report_event7.io_attacker_id.entity == 0x0006u);
    assert(io_report_event7.io_primary_target_id.entity == 0x0009u);
    assert(io_report_event7.padding2 == 0x1112u);
    assert(io_report_event7.padding3 == 0x1314u);
    assert(io_report_event7.number_of_io_records == 1u);
    assert(io_report_event7.io_records.count == 1u);
    assert(io_report_event7.io_records.bytes_size == 4u);

    std::array<uint8_t, FASTDIS_UA_FIXED_SIZE + 8u> ua7{};
    make_ua_pdu(ua7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Ua ua_event7 = fastdis::parse_ua(ua7.data(), ua7.size());
    assert(ua_event7.header.protocol_family == 6u);
    assert(ua_event7.emitting_entity_id.entity == 0x0003u);
    assert(ua_event7.event_id.event_number == 0x0006u);
    assert(ua_event7.state_change_indicator == 0x0A);
    assert(ua_event7.padding1 == 0x0Bu);
    assert(ua_event7.passive_parameter_index == 0x0C0Du);
    assert(ua_event7.propulsion_plant_configuration == 0x0Eu);
    assert(ua_event7.number_of_shafts == 1u);
    assert(ua_event7.number_of_apas == 2u);
    assert(ua_event7.number_of_ua_emitter_systems == 3u);
    assert(ua_event7.ua_records.bytes_size == 8u);

    std::array<uint8_t, FASTDIS_SEES_FIXED_SIZE + 8u> sees7{};
    make_sees_pdu(sees7.data(), FASTDIS_PROTOCOL_VERSION_DIS7);
    fastdis::Sees sees_event7 = fastdis::parse_sees(sees7.data(), sees7.size());
    assert(sees_event7.header.protocol_family == 6u);
    assert(sees_event7.originating_entity_id.site == 0x0011u);
    assert(sees_event7.infrared_signature_representation_index == 0x1112u);
    assert(sees_event7.acoustic_signature_representation_index == 0x1314u);
    assert(sees_event7.radar_cross_section_signature_representation_index == 0x1516u);
    assert(sees_event7.number_of_propulsion_systems == 2u);
    assert(sees_event7.number_of_vectoring_nozzle_systems == 3u);
    assert(sees_event7.supplemental_emission_records.bytes_size == 8u);

    std::array<uint8_t, FASTDIS_SERVICE_REQUEST_FIXED_SIZE + 8u> service_request{};
    make_logistics_pdu(service_request.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_SERVICE_REQUEST_PDU_TYPE, static_cast<uint16_t>(service_request.size()));
    uint8_t* srb = service_request.data() + FASTDIS_HEADER_SIZE;
    put_be16(srb + 0, 0x0001u); put_be16(srb + 2, 0x0002u); put_be16(srb + 4, 0x0003u);
    put_be16(srb + 6, 0x0004u); put_be16(srb + 8, 0x0005u); put_be16(srb + 10, 0x0006u);
    srb[12] = 7u; srb[13] = 2u; put_be16(srb + 14, 0x4041u);
    for (int i = 0; i < 8; ++i) { srb[16 + i] = static_cast<uint8_t>(0x41 + i); }
    fastdis::ServiceRequest service_request_event = fastdis::parse_service_request(service_request.data(), service_request.size());
    assert(service_request_event.service_type_requested == 7u);
    assert(service_request_event.number_of_supply_types == 2u);
    assert(service_request_event.service_request_padding == 0x4041u);
    assert(service_request_event.supplies.count == 2u);
    assert(service_request_event.supplies.bytes_size == 8u);

    std::array<uint8_t, FASTDIS_RESUPPLY_OFFER_FIXED_SIZE + 8u> resupply_offer{};
    make_logistics_pdu(resupply_offer.data(), FASTDIS_PROTOCOL_VERSION_DIS6, FASTDIS_RESUPPLY_OFFER_PDU_TYPE, static_cast<uint16_t>(resupply_offer.size()));
    uint8_t* rob = resupply_offer.data() + FASTDIS_HEADER_SIZE;
    put_be16(rob + 0, 0x0001u); put_be16(rob + 2, 0x0002u); put_be16(rob + 4, 0x0003u);
    put_be16(rob + 6, 0x0004u); put_be16(rob + 8, 0x0005u); put_be16(rob + 10, 0x0006u);
    rob[12] = 2u; rob[13] = 0x11u; rob[14] = 0x12u; rob[15] = 0x13u;
    for (int i = 0; i < 8; ++i) { rob[16 + i] = static_cast<uint8_t>(0x51 + i); }
    fastdis::ResupplyOffer resupply_offer_event = fastdis::parse_resupply_offer(resupply_offer.data(), resupply_offer.size());
    assert(resupply_offer_event.number_of_supply_types == 2u);
    assert(resupply_offer_event.padding_bytes[0] == 0x11u);
    assert(resupply_offer_event.padding_bytes[1] == 0x12u);
    assert(resupply_offer_event.padding_bytes[2] == 0x13u);
    assert(resupply_offer_event.supplies.count == 2u);
    assert(resupply_offer_event.supplies.bytes_size == 8u);

    std::array<uint8_t, FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE + 8u> resupply_received{};
    make_logistics_pdu(resupply_received.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE, static_cast<uint16_t>(resupply_received.size()));
    uint8_t* rrb2 = resupply_received.data() + FASTDIS_HEADER_SIZE;
    put_be16(rrb2 + 0, 0x0001u); put_be16(rrb2 + 2, 0x0002u); put_be16(rrb2 + 4, 0x0003u);
    put_be16(rrb2 + 6, 0x0004u); put_be16(rrb2 + 8, 0x0005u); put_be16(rrb2 + 10, 0x0006u);
    rrb2[12] = 2u; put_be16(rrb2 + 13, 0x6162u); rrb2[15] = 0x63u;
    for (int i = 0; i < 8; ++i) { rrb2[16 + i] = static_cast<uint8_t>(0x61 + i); }
    fastdis::ResupplyReceived resupply_received_event = fastdis::parse_resupply_received(resupply_received.data(), resupply_received.size());
    assert(resupply_received_event.number_of_supply_types == 2u);
    assert(resupply_received_event.padding1 == 0x6162u);
    assert(resupply_received_event.padding2 == 0x63u);
    assert(resupply_received_event.supplies.count == 2u);
    assert(resupply_received_event.supplies.bytes_size == 8u);

    std::array<uint8_t, FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE> resupply_cancel{};
    make_logistics_pdu(resupply_cancel.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RESUPPLY_CANCEL_PDU_TYPE, static_cast<uint16_t>(resupply_cancel.size()));
    uint8_t* rcb = resupply_cancel.data() + FASTDIS_HEADER_SIZE;
    put_be16(rcb + 0, 0x0001u); put_be16(rcb + 2, 0x0002u); put_be16(rcb + 4, 0x0003u);
    put_be16(rcb + 6, 0x0004u); put_be16(rcb + 8, 0x0005u); put_be16(rcb + 10, 0x0006u);
    fastdis::ResupplyCancel resupply_cancel_event = fastdis::parse_resupply_cancel(resupply_cancel.data(), resupply_cancel.size());
    assert(resupply_cancel_event.receiving_entity_id.site == 0x0001u);
    assert(resupply_cancel_event.supplying_entity_id.entity == 0x0006u);

    std::array<uint8_t, FASTDIS_REPAIR_COMPLETE_FIXED_SIZE> repair_complete{};
    make_logistics_pdu(repair_complete.data(), FASTDIS_PROTOCOL_VERSION_DIS6, FASTDIS_REPAIR_COMPLETE_PDU_TYPE, static_cast<uint16_t>(repair_complete.size()));
    uint8_t* rcb2 = repair_complete.data() + FASTDIS_HEADER_SIZE;
    put_be16(rcb2 + 0, 0x0001u); put_be16(rcb2 + 2, 0x0002u); put_be16(rcb2 + 4, 0x0003u);
    put_be16(rcb2 + 6, 0x0004u); put_be16(rcb2 + 8, 0x0005u); put_be16(rcb2 + 10, 0x0006u);
    put_be16(rcb2 + 12, 0x7172u); put_be16(rcb2 + 14, 0x7374u);
    fastdis::RepairComplete repair_complete_event = fastdis::parse_repair_complete(repair_complete.data(), repair_complete.size());
    assert(repair_complete_event.repair == 0x7172u);
    assert(repair_complete_event.padding2 == 0x7374u);

    std::array<uint8_t, FASTDIS_REPAIR_RESPONSE_FIXED_SIZE> repair_response{};
    make_logistics_pdu(repair_response.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_REPAIR_RESPONSE_PDU_TYPE, static_cast<uint16_t>(repair_response.size()));
    uint8_t* rrb3 = repair_response.data() + FASTDIS_HEADER_SIZE;
    put_be16(rrb3 + 0, 0x0001u); put_be16(rrb3 + 2, 0x0002u); put_be16(rrb3 + 4, 0x0003u);
    put_be16(rrb3 + 6, 0x0004u); put_be16(rrb3 + 8, 0x0005u); put_be16(rrb3 + 10, 0x0006u);
    rrb3[12] = 0x75u; put_be16(rrb3 + 13, 0x7677u); rrb3[15] = 0x78u;
    fastdis::RepairResponse repair_response_event = fastdis::parse_repair_response(repair_response.data(), repair_response.size());
    assert(repair_response_event.repair_result == 0x75u);
    assert(repair_response_event.padding1 == 0x7677u);
    assert(repair_response_event.padding2 == 0x78u);

    std::array<uint8_t, FASTDIS_RECORD_RELIABLE_FIXED_SIZE + 8u> record_reliable{};
    make_sim_management_pdu(record_reliable.data(), FASTDIS_PROTOCOL_VERSION_DIS7, FASTDIS_RECORD_RELIABLE_PDU_TYPE, 10u, static_cast<uint16_t>(record_reliable.size()));
    uint8_t* rrb = record_reliable.data() + FASTDIS_HEADER_SIZE;
    put_be16(rrb + 0, 0x0001u); put_be16(rrb + 2, 0x0002u); put_be16(rrb + 4, 0x0003u);
    put_be16(rrb + 6, 0x0004u); put_be16(rrb + 8, 0x0005u); put_be16(rrb + 10, 0x0006u);
    put_be32(rrb + 12, 0x51525354u); rrb[16] = 7u; rrb[17] = 8u; put_be16(rrb + 18, 0x090Au); put_be32(rrb + 20, 2u);
    for (int i = 0; i < 8; ++i) { rrb[24 + i] = static_cast<uint8_t>(0x10 + i); }
    fastdis::RecordReliable record_reliable_event = fastdis::parse_record_reliable(record_reliable.data(), record_reliable.size());
    assert(record_reliable_event.request_id == 0x51525354u);
    assert(record_reliable_event.required_reliability_service == 7u);
    assert(record_reliable_event.pad1 == 8u);
    assert(record_reliable_event.event_type == 0x090Au);
    assert(record_reliable_event.record_sets.count == 2u);
    assert(record_reliable_event.record_sets.bytes_size == 8u);

    fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform();
    cfg.only_versions({7})
       .only_entity_force_ids({2})
       .sample(1);
    assert(cfg.contains(fastdis::FilterKind::PduTypes, FASTDIS_ENTITY_STATE_PDU_TYPE));
    assert(cfg.contains(fastdis::FilterKind::ProtocolFamilies, FASTDIS_ENTITY_INFORMATION_FAMILY));

    fastdis::Scanner scanner = fastdis::ScannerBuilder()
        .entity_transform_profile()
        .versions({7})
        .force_ids({2})
        .sample_every(1)
        .allow_entity_ids({fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u),
                           fastdis::make_entity_id(0x1111u, 0x2222u, 0x4444u)})
        .build();
    assert(scanner);
    assert(scanner.entity_id_filter_mode() == fastdis::EntityIdFilterMode::Allow);
    assert(scanner.entity_id_count() == 2u);
    assert(scanner.contains_entity_id(fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u)));
    fastdis::Scanner try_built_scanner;
    assert(fastdis::ScannerBuilder().entity_transform_profile().try_build(try_built_scanner) == FASTDIS_OK);
    assert(try_built_scanner);

    fastdis::PacketViews packets;
    packets.add(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE)
           .add(p2.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);

    fastdis::TransformBatch transforms(4);
    fastdis::ScanStats scan_stats = scanner.scan_transforms(packets, transforms);
    assert(scan_stats.seen == 2u);
    assert(scan_stats.accepted == 2u);
    assert(transforms.size() == 2u);
    assert(transforms.dropped() == 0u);
    assert(transforms[0].location.x == 10.0);
    assert(transforms[1].location.x == 40.0);

    scanner.entity_id_filter_mode(fastdis::EntityIdFilterMode::Disabled);
    assert(scanner.entity_id_filter_mode() == fastdis::EntityIdFilterMode::Disabled);

    fastdis::EntityTable table = fastdis::EntityTableConfig()
        .reserve(8)
        .build();
    assert(table);
    fastdis::EntityTable try_built_table;
    assert(fastdis::EntityTableConfig().reserve(2).try_build(try_built_table) == FASTDIS_OK);
    assert(try_built_table);
    fastdis::EntityTableUpdateStats ingest_stats = table.ingest(scanner, packets, true);
    assert(ingest_stats.new_entities == 2u);
    assert(table.size() == 2u);
    assert(table.tick() == 1u);

    fastdis::EntitySnapshot got = table.get(fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u));
    assert(got.transform.location.x == 10.0);
    assert(fastdis::snapshot_entity_id(got).entity == 0x3333u);
    assert(fastdis::snapshot_location(got).x == 10.0);
    assert(fastdis::snapshot_orientation(got).theta == got.transform.orientation.theta);
    assert(fastdis::snapshot_linear_velocity(got).x == got.transform.linear_velocity.x);
    assert(fastdis::snapshot_is_new(got));
    assert(!fastdis::snapshot_is_stale(got));

    fastdis::SnapshotBatch changed_batch = table.snapshot_changed(4, false);
    assert(changed_batch.size() == 2u);

    fastdis::SnapshotBuffer buffer(4);
    assert(buffer);
    assert(buffer.slot_count() == 2u);
    fastdis::SnapshotBufferStats buffer_stats = buffer.stats();
    assert(buffer_stats.publish_attempts == 0u);
    fastdis::SnapshotView published = buffer.publish_changed(table, false);
    assert(published.size() == 2u);
    assert(published.generation() == 1u);
    buffer_stats = buffer.stats();
    assert(buffer_stats.publish_attempts == 1u);
    assert(buffer_stats.publish_successes == 1u);
    assert(buffer_stats.max_snapshot_count == 2u);

    {
        fastdis::ScopedSnapshotView view = buffer.acquire_latest();
        assert(view.owns_release());
        assert(view.size() == 2u);
        assert(view[0].transform.entity_id.site == 0x1111u);

        // One slot is pinned; publishing into the other slot succeeds.
        fastdis::SnapshotView second_publish;
        assert(buffer.try_publish_all(table, &second_publish) == FASTDIS_OK);
        // Both slots would be unavailable now, so the native handoff exposes back-pressure.
        assert(buffer.try_publish_all(table, &second_publish) == FASTDIS_ERR_BUSY);
        buffer_stats = buffer.stats();
        assert(buffer_stats.publish_attempts == 3u);
        assert(buffer_stats.publish_successes == 2u);
        assert(buffer_stats.publish_busy == 1u);
        assert(buffer_stats.acquire_count == 1u);
    }
    buffer_stats = buffer.stats();
    assert(buffer_stats.release_count == 1u);

    // The scoped view released on scope exit, so publishing succeeds again.
    assert(buffer.try_publish_all(table, &published) == FASTDIS_OK);
    assert(buffer.reset_stats().stats().publish_attempts == 0u);
    table.mark_all_clean();

    fastdis::SnapshotBuffer triple_buffer = fastdis::SnapshotBufferConfig()
        .capacity(4)
        .slots(3)
        .build();
    assert(triple_buffer.slot_count() == 3u);
    fastdis::SnapshotBuffer try_built_buffer;
    assert(fastdis::SnapshotBufferConfig().capacity(2).slots(3).try_build(try_built_buffer) == FASTDIS_OK);
    assert(try_built_buffer.slot_count() == 3u);
    fastdis::SnapshotView triple_published = triple_buffer.publish_all(table);
    assert(triple_published.generation() == 1u);
    fastdis::ScopedSnapshotView triple_held_a = triple_buffer.acquire_latest();
    assert(triple_buffer.try_publish_all(table, &triple_published) == FASTDIS_OK);
    fastdis::ScopedSnapshotView triple_held_b = triple_buffer.acquire_latest();
    assert(triple_buffer.try_publish_all(table, &triple_published) == FASTDIS_OK);
    assert(triple_buffer.try_publish_all(table, &triple_published) == FASTDIS_ERR_BUSY);
    triple_held_a.release();
    triple_held_b.release();

    table.mark_all_clean();

    std::array<uint8_t, 160> p1_changed{};
    make_entity_state_pdu(p1_changed.data(), 0x1111u, 0x2222u, 0x3333u, 100.0);
    fastdis::PacketViews changed_packets;
    changed_packets.add(p1_changed.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);

    fastdis::EntityTableUpdateStats combined_stats{};
    fastdis_entity_table_update_stats_init(&combined_stats);
    fastdis::SnapshotView combined_view = buffer.ingest_and_publish_changed(
        table,
        scanner,
        changed_packets,
        true,
        true,
        &combined_stats);
    assert(combined_stats.changed_entities == 1u);
    assert(combined_view.size() == 1u);
    assert(combined_view[0].transform.location.x == 100.0);

    fastdis::SnapshotBatch copied = buffer.copy_latest(4);
    assert(copied.size() == 1u);
    fastdis::SnapshotBatch dead_reckoned = buffer.copy_latest_dead_reckoned(4, copied[0].last_seen_tick + 2u, 0.5);
    assert(dead_reckoned.size() == 1u);
    assert(std::fabs(dead_reckoned[0].transform.location.x - 101.5) < 0.0001);
    assert(fastdis::snapshot_is_extrapolated(dead_reckoned[0]));

    fastdis::Scanner moved_scanner(std::move(scanner));
    assert(moved_scanner);
    assert(!scanner);

    fastdis::EntityTable moved_table(std::move(table));
    assert(moved_table);
    assert(!table);
    assert(moved_table.size() == 2u);

    return 0;
}
