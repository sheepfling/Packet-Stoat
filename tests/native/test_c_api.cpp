#include "fastdis/fastdis.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
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

void put_world(uint8_t *p, double x, double y, double z) {
    put_be_double(p + 0, x);
    put_be_double(p + 8, y);
    put_be_double(p + 16, z);
}

void make_pdu(uint8_t *p, uint8_t version, uint8_t pdu_type, uint16_t length = 12) {
    std::memset(p, 0, 160);
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
    assert(FASTDIS_ABI_VERSION == 8u);

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
    fastdis_entity_transform_t transforms[2];
    fastdis_entity_transform_batch_t transform_batch;
    transform_batch.transforms = transforms;
    transform_batch.capacity = 2;
    transform_batch.count = 0;
    transform_batch.dropped = 0;
    fastdis_scan_stats_init(&stats);
    assert(fastdis_scanner_scan_entity_transforms_to_batch(scanner, scanner_packets, 2, &transform_batch, &stats) == FASTDIS_OK);
    assert(stats.seen == 2);
    assert(stats.accepted == 1);
    assert(stats.emitted == 1);
    assert(transform_batch.count == 1u);
    assert(transform_batch.dropped == 0u);
    assert(transform_batch.transforms[0].entity_id.entity == 0x3333u);
    assert(transform_batch.transforms[0].location.y == 20.0);

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
    assert(fastdis_entity_snapshot_buffer_generation(snapshot_buffer) == 0u);

    fastdis_entity_snapshot_view_t view;
    assert(fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, table, 0, &view) == FASTDIS_OK);
    assert(view.count == 2u);
    assert(view.dropped == 0u);
    assert(view.generation == 1u);
    assert(view.snapshots != nullptr);
    assert((view.snapshots[0].change_flags & FASTDIS_ENTITY_CHANGE_NEW) != 0u);

    fastdis_entity_snapshot_view_t held_view;
    assert(fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(held_view.count == 2u);
    assert(held_view.generation == 1u);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_OK);
    assert(view.generation == 2u);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_ERR_BUSY);

    fastdis_entity_snapshot_t copied_snapshots[4];
    fastdis_entity_snapshot_batch_t copy_batch;
    copy_batch.snapshots = copied_snapshots;
    copy_batch.capacity = 4;
    copy_batch.count = 0;
    copy_batch.dropped = 0;
    assert(fastdis_entity_snapshot_buffer_copy_latest(snapshot_buffer, &copy_batch) == FASTDIS_OK);
    assert(copy_batch.count == 2u);
    assert(copy_batch.dropped == 0u);

    assert(fastdis_entity_snapshot_buffer_release(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, table, &view) == FASTDIS_OK);
    assert(view.generation == 3u);
    assert(fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_resize(snapshot_buffer, 2) == FASTDIS_ERR_BUSY);
    assert(fastdis_entity_snapshot_buffer_release(snapshot_buffer, &held_view) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_resize(snapshot_buffer, 2) == FASTDIS_OK);
    assert(fastdis_entity_snapshot_buffer_capacity(snapshot_buffer) == 2u);
    fastdis_entity_snapshot_buffer_destroy(snapshot_buffer);

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
    fastdis_entity_table_destroy(table);

    assert(fastdis_scanner_remove_entity_id(scanner, 0x1111u, 0x2222u, 0x3333u) == FASTDIS_OK);
    assert(fastdis_scanner_entity_id_count(scanner) == 0u);
    fastdis_scanner_destroy(scanner);

    return 0;
}
