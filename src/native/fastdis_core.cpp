#include "fastdis/fastdis.h"

#include <cmath>
#include <cstring>
#include <new>
#include <mutex>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct fastdis_scanner_s {
    fastdis_scan_config_t config;
    uint32_t entity_id_filter_mode;
    std::unordered_set<uint64_t> entity_ids;

    fastdis_scanner_s() : config(), entity_id_filter_mode(FASTDIS_ENTITY_ID_FILTER_DISABLED), entity_ids() {
        std::memset(&config, 0, sizeof(config));
        config.struct_size = static_cast<uint32_t>(sizeof(config));
        config.sample_every = 1;
        config.entity_state_fields = FASTDIS_ES_FIELD_ALL;
    }
};


struct fastdis_entity_table_entry_s {
    fastdis_entity_transform_t transform;
    uint64_t first_seen_tick;
    uint64_t last_seen_tick;
    uint64_t update_count;
    uint32_t change_flags;

    fastdis_entity_table_entry_s()
        : transform(), first_seen_tick(0), last_seen_tick(0), update_count(0), change_flags(0) {
        std::memset(&transform, 0, sizeof(transform));
    }
};

struct fastdis_entity_table_s {
    uint64_t tick;
    uint64_t total_updates;
    uint64_t total_new;
    uint64_t total_changed;
    uint64_t total_unchanged;
    uint64_t total_removed;
    std::unordered_map<uint64_t, fastdis_entity_table_entry_s> entries;

    explicit fastdis_entity_table_s(size_t reserve)
        : tick(0),
          total_updates(0),
          total_new(0),
          total_changed(0),
          total_unchanged(0),
          total_removed(0),
          entries() {
        if (reserve > 0) {
            entries.reserve(reserve);
        }
    }
};

struct fastdis_entity_snapshot_buffer_s {
    mutable std::mutex mutex;
    std::vector<std::vector<fastdis_entity_snapshot_t>> slots;
    std::vector<size_t> counts;
    std::vector<size_t> dropped;
    std::vector<uint64_t> generations;
    std::vector<size_t> readers;
    uint32_t read_slot;
    uint32_t next_write_hint;
    uint64_t generation;
    fastdis_entity_snapshot_buffer_stats_t stats;

    fastdis_entity_snapshot_buffer_s(size_t capacity, size_t slot_count)
        : slots(slot_count),
          counts(slot_count, 0u),
          dropped(slot_count, 0u),
          generations(slot_count, 0u),
          readers(slot_count, 0u),
          read_slot(0u),
          next_write_hint(1u),
          generation(0u),
          stats() {
        for (std::vector<fastdis_entity_snapshot_t> &slot : slots) {
            slot.resize(capacity);
        }
        std::memset(&stats, 0, sizeof(stats));
    }
};

namespace {

static inline fastdis_counted_bytes_view_t make_counted_bytes_view(
    const uint8_t *data,
    uint16_t declared_length,
    uint16_t fixed_size,
    uint32_t count) noexcept;

static inline uint16_t be16(const uint8_t *p) noexcept {
    return static_cast<uint16_t>((static_cast<uint16_t>(p[0]) << 8) |
                                 static_cast<uint16_t>(p[1]));
}

static inline uint32_t be32(const uint8_t *p) noexcept {
    return (static_cast<uint32_t>(p[0]) << 24) |
           (static_cast<uint32_t>(p[1]) << 16) |
           (static_cast<uint32_t>(p[2]) << 8) |
           static_cast<uint32_t>(p[3]);
}

static inline uint64_t be64(const uint8_t *p) noexcept {
    return (static_cast<uint64_t>(p[0]) << 56) |
           (static_cast<uint64_t>(p[1]) << 48) |
           (static_cast<uint64_t>(p[2]) << 40) |
           (static_cast<uint64_t>(p[3]) << 32) |
           (static_cast<uint64_t>(p[4]) << 24) |
           (static_cast<uint64_t>(p[5]) << 16) |
           (static_cast<uint64_t>(p[6]) << 8) |
           static_cast<uint64_t>(p[7]);
}

static inline float be_float32(const uint8_t *p) noexcept {
    const uint32_t bits = be32(p);
    float value = 0.0f;
    static_assert(sizeof(value) == sizeof(bits), "float32 size mismatch");
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

static inline double be_float64(const uint8_t *p) noexcept {
    const uint64_t bits = be64(p);
    double value = 0.0;
    static_assert(sizeof(value) == sizeof(bits), "float64 size mismatch");
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

static inline fastdis_vec3f_t read_vec3f(const uint8_t *p) noexcept {
    fastdis_vec3f_t out;
    out.x = be_float32(p + 0);
    out.y = be_float32(p + 4);
    out.z = be_float32(p + 8);
    return out;
}

static inline fastdis_world_coordinates_t read_world_coordinates(const uint8_t *p) noexcept {
    fastdis_world_coordinates_t out;
    out.x = be_float64(p + 0);
    out.y = be_float64(p + 8);
    out.z = be_float64(p + 16);
    return out;
}

static inline fastdis_euler_angles_t read_euler_angles(const uint8_t *p) noexcept {
    fastdis_euler_angles_t out;
    out.psi = be_float32(p + 0);
    out.theta = be_float32(p + 4);
    out.phi = be_float32(p + 8);
    return out;
}

static inline fastdis_clock_time_t read_clock_time(const uint8_t *p) noexcept {
    fastdis_clock_time_t out;
    out.hour = be32(p + 0);
    out.time_past_hour = be32(p + 4);
    return out;
}

static inline fastdis_event_id_t read_event_id(const uint8_t *p) noexcept {
    fastdis_event_id_t out;
    out.site = be16(p + 0);
    out.application = be16(p + 2);
    out.event_number = be16(p + 4);
    return out;
}

static inline fastdis_live_event_id_t read_live_event_id(const uint8_t *p) noexcept {
    fastdis_live_event_id_t out;
    out.site = p[0];
    out.application = p[1];
    out.event_number = be16(p + 2);
    return out;
}

static inline fastdis_simulation_address_t read_simulation_address(const uint8_t *p) noexcept {
    fastdis_simulation_address_t out;
    out.site = be16(p + 0);
    out.application = be16(p + 2);
    return out;
}

static inline fastdis_entity_id_t read_entity_id(const uint8_t *p) noexcept {
    fastdis_entity_id_t out;
    out.site = be16(p + 0);
    out.application = be16(p + 2);
    out.entity = be16(p + 4);
    return out;
}

static inline fastdis_live_entity_id_t read_live_entity_id(const uint8_t *p) noexcept {
    fastdis_live_entity_id_t out;
    out.site = p[0];
    out.application = p[1];
    out.entity = be16(p + 2);
    return out;
}

static inline fastdis_entity_type_t read_entity_type(const uint8_t *p) noexcept {
    fastdis_entity_type_t out;
    out.entity_kind = p[0];
    out.domain = p[1];
    out.country = be16(p + 2);
    out.category = p[4];
    out.subcategory = p[5];
    out.specific = p[6];
    out.extra = p[7];
    return out;
}

static inline fastdis_radio_entity_type_t read_radio_entity_type(const uint8_t *p) noexcept {
    fastdis_radio_entity_type_t out;
    out.entity_kind = p[0];
    out.domain = p[1];
    out.country = be16(p + 2);
    out.category = p[4];
    out.nomenclature_version = p[5];
    out.nomenclature = be16(p + 6);
    return out;
}

static inline fastdis_environment_object_type_t read_environment_object_type_dis6(const uint8_t *p) noexcept {
    fastdis_environment_object_type_t out;
    out.domain = p[1];
    out.kind = p[0];
    out.country = be16(p + 2);
    out.category = p[4];
    out.subcategory = p[5];
    return out;
}

static inline fastdis_environment_object_type_t read_environment_object_type_dis7(const uint8_t *p) noexcept {
    fastdis_environment_object_type_t out;
    out.domain = p[0];
    out.kind = p[1];
    out.country = 0u;
    out.category = p[2];
    out.subcategory = p[3];
    return out;
}

static inline fastdis_modulation_type_t read_modulation_type(const uint8_t *p) noexcept {
    fastdis_modulation_type_t out;
    out.spread_spectrum = be16(p + 0);
    out.major = be16(p + 2);
    out.detail = be16(p + 4);
    out.system = be16(p + 6);
    return out;
}

static inline fastdis_system_id_t read_system_id(const uint8_t *p) noexcept {
    fastdis_system_id_t out;
    out.system_type = be16(p + 0);
    out.system_name = be16(p + 2);
    out.system_mode = p[4];
    out.change_options = p[5];
    return out;
}

static inline fastdis_iff_fundamental_data_t read_iff_fundamental_data(const uint8_t *p) noexcept {
    fastdis_iff_fundamental_data_t out;
    out.system_status = p[0];
    out.alternate_parameter4 = p[1];
    out.information_layers = p[2];
    out.modifier = p[3];
    out.parameter1 = be16(p + 4);
    out.parameter2 = be16(p + 6);
    out.parameter3 = be16(p + 8);
    out.parameter4 = be16(p + 10);
    out.parameter5 = be16(p + 12);
    out.parameter6 = be16(p + 14);
    return out;
}

static inline fastdis_burst_descriptor_t read_burst_descriptor(const uint8_t *p) noexcept {
    fastdis_burst_descriptor_t out;
    out.munition_type = read_entity_type(p + 0);
    out.warhead = be16(p + 8);
    out.fuse = be16(p + 10);
    out.quantity = be16(p + 12);
    out.rate = be16(p + 14);
    return out;
}

static inline fastdis_relationship_t read_relationship(const uint8_t *p) noexcept {
    fastdis_relationship_t out;
    out.nature = be16(p + 0);
    out.position = be16(p + 2);
    return out;
}

static inline fastdis_named_location_t read_named_location(const uint8_t *p) noexcept {
    fastdis_named_location_t out;
    out.station_name = be16(p + 0);
    out.station_number = be16(p + 2);
    return out;
}

static inline uint64_t entity_key(uint16_t site, uint16_t application, uint16_t entity) noexcept {
    return (static_cast<uint64_t>(site) << 32) |
           (static_cast<uint64_t>(application) << 16) |
           static_cast<uint64_t>(entity);
}

static inline uint64_t entity_key(const fastdis_entity_id_t &id) noexcept {
    return entity_key(id.site, id.application, id.entity);
}

static inline uint64_t normalize_entity_state_fields(uint64_t fields) noexcept {
    if (fields == 0ull) {
        fields = FASTDIS_ES_FIELD_ALL;
    }
    fields |= FASTDIS_ES_FIELD_HEADER | FASTDIS_ES_FIELD_FORCE_ID;
    return fields;
}

static inline uint64_t config_entity_state_fields(const fastdis_scan_config_t *config) noexcept {
    return normalize_entity_state_fields(config != nullptr ? config->entity_state_fields : FASTDIS_ES_FIELD_ALL);
}

static inline bool config_looks_valid(const fastdis_scan_config_t *config) noexcept {
    return config != nullptr && config->struct_size >= sizeof(fastdis_scan_config_t) &&
           config->sample_every != 0;
}

static inline bool matches_filter(const fastdis_u8_filter_t *filter, uint8_t value) noexcept {
    if (filter == nullptr || filter->active == 0) {
        return true;
    }
    const uint32_t word = static_cast<uint32_t>(value >> 6);
    const uint32_t bit = static_cast<uint32_t>(value & 63u);
    return ((filter->bits[word] >> bit) & 1ull) != 0ull;
}

static inline fastdis_u8_filter_t *config_filter_ptr(fastdis_scan_config_t *config, uint32_t filter_kind) noexcept {
    if (config == nullptr) {
        return nullptr;
    }
    switch (filter_kind) {
        case FASTDIS_FILTER_VERSIONS:
            return &config->versions;
        case FASTDIS_FILTER_PDU_TYPES:
            return &config->pdu_types;
        case FASTDIS_FILTER_PROTOCOL_FAMILIES:
            return &config->protocol_families;
        case FASTDIS_FILTER_EXERCISE_IDS:
            return &config->exercise_ids;
        case FASTDIS_FILTER_ENTITY_FORCE_IDS:
            return &config->entity_force_ids;
        default:
            return nullptr;
    }
}

static inline const fastdis_u8_filter_t *config_filter_ptr_const(const fastdis_scan_config_t *config, uint32_t filter_kind) noexcept {
    return config_filter_ptr(const_cast<fastdis_scan_config_t *>(config), filter_kind);
}

static inline bool matches_config(const fastdis_header_t *header, const fastdis_scan_config_t *config) noexcept {
    if (header == nullptr) {
        return false;
    }
    if (config == nullptr) {
        return true;
    }
    return matches_filter(&config->versions, header->version) &&
           matches_filter(&config->pdu_types, header->pdu_type) &&
           matches_filter(&config->protocol_families, header->protocol_family) &&
           matches_filter(&config->exercise_ids, header->exercise_id);
}

static inline bool is_entity_state_header(const fastdis_header_t *header) noexcept {
    return header != nullptr &&
           header->pdu_type == FASTDIS_ENTITY_STATE_PDU_TYPE &&
           header->protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY;
}

static inline bool is_entity_state_update_header(const fastdis_header_t *header) noexcept {
    return header != nullptr &&
           header->pdu_type == FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE &&
           header->protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY;
}

static inline bool is_warfare_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 2u;
}

static inline bool is_entity_information_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY;
}

static inline bool is_logistics_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 3u;
}

static inline bool is_radio_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 4u;
}

static inline bool is_distributed_emissions_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 6u;
}

static inline bool is_information_operations_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 13u;
}

static inline bool is_protocol_family_zero_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 0u;
}

static inline bool is_simulation_management_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 5u;
}

static inline bool is_simulation_management_reliable_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 10u;
}

static inline bool is_entity_management_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 7u;
}

static inline bool is_minefield_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 8u;
}

static inline bool is_synthetic_environment_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 9u;
}

static inline bool is_live_entity_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 11u;
}

static inline bool is_entity_transform_header(const fastdis_header_t *header) noexcept {
    return is_entity_state_header(header) || is_entity_state_update_header(header);
}

static inline void count_malformed(fastdis_scan_stats_t *stats) noexcept {
    if (stats != nullptr) {
        stats->malformed += 1;
    }
}

static inline bool emit_this(uint64_t accepted_index, const fastdis_scan_config_t *config) noexcept {
    const uint64_t normalized_offset = config->sample_offset % config->sample_every;
    return (accepted_index % config->sample_every) == normalized_offset;
}

static inline bool need_bytes(size_t size, size_t end_offset) noexcept {
    return size >= end_offset;
}

static inline fastdis_status_t require_field_bytes(size_t size, uint64_t fields, uint64_t field_bit, size_t end_offset) noexcept {
    if ((fields & field_bit) != 0ull && !need_bytes(size, end_offset)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    return FASTDIS_OK;
}

static inline fastdis_status_t validate_entity_state_field_bytes(size_t size, uint64_t fields) noexcept {
    // All offsets below are absolute offsets from the start of the PDU.
    // Force ID is always read for routing.
    if (!need_bytes(size, FASTDIS_HEADER_SIZE + 8u)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_ENTITY_ID, FASTDIS_HEADER_SIZE + 6u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT, FASTDIS_HEADER_SIZE + 8u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_ENTITY_TYPE, FASTDIS_HEADER_SIZE + 16u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE, FASTDIS_HEADER_SIZE + 24u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_LINEAR_VELOCITY, FASTDIS_HEADER_SIZE + 36u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_LOCATION, FASTDIS_HEADER_SIZE + 60u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_ORIENTATION, FASTDIS_HEADER_SIZE + 72u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_APPEARANCE, FASTDIS_HEADER_SIZE + 76u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_DEAD_RECKONING, FASTDIS_HEADER_SIZE + 116u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_MARKING, FASTDIS_HEADER_SIZE + 128u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    if (require_field_bytes(size, fields, FASTDIS_ES_FIELD_CAPABILITIES, FASTDIS_HEADER_SIZE + 132u) != FASTDIS_OK) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    return FASTDIS_OK;
}

static inline void copy_config(fastdis_scan_config_t *dst, const fastdis_scan_config_t *src) noexcept {
    if (src != nullptr) {
        *dst = *src;
        dst->struct_size = static_cast<uint32_t>(sizeof(*dst));
        if (dst->sample_every == 0) {
            dst->sample_every = 1;
        }
        dst->entity_state_fields = normalize_entity_state_fields(dst->entity_state_fields);
    } else {
        fastdis_scan_config_init(dst);
    }
}

static inline bool scanner_entity_filter_matches(const fastdis_scanner_t *scanner, const fastdis_entity_id_t &id) noexcept {
    if (scanner == nullptr || scanner->entity_id_filter_mode == FASTDIS_ENTITY_ID_FILTER_DISABLED) {
        return true;
    }
    const bool contains = scanner->entity_ids.find(entity_key(id)) != scanner->entity_ids.end();
    if (scanner->entity_id_filter_mode == FASTDIS_ENTITY_ID_FILTER_ALLOW) {
        return contains;
    }
    if (scanner->entity_id_filter_mode == FASTDIS_ENTITY_ID_FILTER_BLOCK) {
        return !contains;
    }
    return true;
}

static inline fastdis_status_t scan_one_impl(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    fastdis_packet_callback_t callback,
    void *packet_user,
    void *callback_user,
    fastdis_scan_stats_t *stats) noexcept {

    if (stats != nullptr) {
        stats->seen += 1;
    }

    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t parsed = fastdis_parse_header(data, size, config->flags, &header);
    if (parsed != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!matches_config(&header, config)) {
        return FASTDIS_OK;
    }

    const uint64_t accepted_index = stats != nullptr ? stats->accepted : 0;
    if (stats != nullptr) {
        stats->accepted += 1;
    }

    if (!emit_this(accepted_index, config)) {
        return FASTDIS_OK;
    }

    if (stats != nullptr) {
        stats->emitted += 1;
    }

    if (callback != nullptr) {
        int stop = callback(&header, data, size, packet_user, callback_user);
        if (stop != 0) {
            return FASTDIS_ERR_CALLBACK_STOPPED;
        }
    }

    return FASTDIS_OK;
}

static inline fastdis_status_t scan_one_entity_state_impl(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_state_callback_t callback,
    void *packet_user,
    void *callback_user,
    fastdis_scan_stats_t *stats) noexcept {

    if (stats != nullptr) {
        stats->seen += 1;
    }

    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t parsed_header = fastdis_parse_header(data, size, config->flags, &header);
    if (parsed_header != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!is_entity_state_header(&header)) {
        return FASTDIS_OK;
    }

    if (!matches_config(&header, config)) {
        return FASTDIS_OK;
    }

    uint64_t fields = config_entity_state_fields(config);
    if (scanner != nullptr && scanner->entity_id_filter_mode != FASTDIS_ENTITY_ID_FILTER_DISABLED) {
        fields |= FASTDIS_ES_FIELD_ENTITY_ID;
    }
    if (config->entity_force_ids.active != 0) {
        fields |= FASTDIS_ES_FIELD_FORCE_ID;
    }

    fastdis_entity_state_prefix_t entity_state;
    fastdis_status_t parsed = fastdis_parse_entity_state_fields(data, size, config->flags, fields, &entity_state);
    if (parsed != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!matches_filter(&config->entity_force_ids, entity_state.force_id)) {
        return FASTDIS_OK;
    }

    if (!scanner_entity_filter_matches(scanner, entity_state.entity_id)) {
        return FASTDIS_OK;
    }

    const uint64_t accepted_index = stats != nullptr ? stats->accepted : 0;
    if (stats != nullptr) {
        stats->accepted += 1;
    }

    if (!emit_this(accepted_index, config)) {
        return FASTDIS_OK;
    }

    if (stats != nullptr) {
        stats->emitted += 1;
    }

    if (callback != nullptr) {
        int stop = callback(&entity_state, data, size, packet_user, callback_user);
        if (stop != 0) {
            return FASTDIS_ERR_CALLBACK_STOPPED;
        }
    }

    return FASTDIS_OK;
}

static inline fastdis_status_t scan_many_impl(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    fastdis_packet_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) noexcept {

    if (count > 0 && packets == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    for (size_t i = 0; i < count; ++i) {
        fastdis_status_t rc = scan_one_impl(
            packets[i].data,
            packets[i].size,
            config,
            callback,
            packets[i].user,
            callback_user,
            stats);
        if (rc != FASTDIS_OK) {
            return rc;
        }
    }

    return FASTDIS_OK;
}

static inline fastdis_status_t scan_many_entity_state_impl(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_state_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) noexcept {

    if (count > 0 && packets == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    for (size_t i = 0; i < count; ++i) {
        fastdis_status_t rc = scan_one_entity_state_impl(
            packets[i].data,
            packets[i].size,
            config,
            scanner,
            callback,
            packets[i].user,
            callback_user,
            stats);
        if (rc != FASTDIS_OK) {
            return rc;
        }
    }

    return FASTDIS_OK;
}


static inline void reset_entity_state_batch(fastdis_entity_state_batch_t *batch) noexcept {
    if (batch != nullptr) {
        batch->count = 0;
        batch->dropped = 0;
    }
}

static inline void reset_transform_batch(fastdis_entity_transform_batch_t *batch) noexcept {
    if (batch != nullptr) {
        batch->count = 0;
        batch->dropped = 0;
    }
}

static inline bool entity_state_batch_looks_valid(const fastdis_entity_state_batch_t *batch) noexcept {
    return batch != nullptr && (batch->capacity == 0 || batch->entities != nullptr);
}

static inline bool transform_batch_looks_valid(const fastdis_entity_transform_batch_t *batch) noexcept {
    return batch != nullptr && (batch->capacity == 0 || batch->transforms != nullptr);
}

static inline void append_entity_state_to_batch(
    fastdis_entity_state_batch_t *batch,
    const fastdis_entity_state_prefix_t &entity_state) noexcept {
    if (batch->count < batch->capacity) {
        batch->entities[batch->count++] = entity_state;
    } else {
        batch->dropped += 1;
    }
}

static inline fastdis_entity_transform_t transform_from_entity_state(
    const fastdis_entity_state_prefix_t &entity_state) noexcept {
    fastdis_entity_transform_t out;
    std::memset(&out, 0, sizeof(out));
    out.entity_id = entity_state.entity_id;
    out.force_id = entity_state.force_id;
    out.exercise_id = entity_state.header.exercise_id;
    out.version = entity_state.header.version;
    out.timestamp = entity_state.header.timestamp;
    out.appearance = entity_state.appearance;
    out.location = entity_state.location;
    out.orientation = entity_state.orientation;
    out.linear_velocity = entity_state.linear_velocity;
    out.fields_present = entity_state.fields_present;
    out.dead_reckoning_algorithm = entity_state.dead_reckoning_algorithm;
    std::memcpy(out.dead_reckoning_parameters, entity_state.dead_reckoning_parameters, sizeof(out.dead_reckoning_parameters));
    out.dead_reckoning_linear_acceleration = entity_state.dead_reckoning_linear_acceleration;
    out.dead_reckoning_angular_velocity = entity_state.dead_reckoning_angular_velocity;
    return out;
}

static inline uint64_t transform_field_mask() noexcept;

static inline fastdis_entity_transform_t merge_transform_patch(
    const fastdis_entity_transform_t &base,
    const fastdis_entity_transform_t &patch) noexcept {
    fastdis_entity_transform_t out = base;
    out.entity_id = patch.entity_id;
    out.exercise_id = patch.exercise_id;
    out.version = patch.version;
    out.timestamp = patch.timestamp;
    if ((patch.fields_present & FASTDIS_ES_FIELD_FORCE_ID) != 0ull) {
        out.force_id = patch.force_id;
    }
    if ((patch.fields_present & FASTDIS_ES_FIELD_APPEARANCE) != 0ull) {
        out.appearance = patch.appearance;
    }
    if ((patch.fields_present & FASTDIS_ES_FIELD_LOCATION) != 0ull) {
        out.location = patch.location;
    }
    if ((patch.fields_present & FASTDIS_ES_FIELD_ORIENTATION) != 0ull) {
        out.orientation = patch.orientation;
    }
    if ((patch.fields_present & FASTDIS_ES_FIELD_LINEAR_VELOCITY) != 0ull) {
        out.linear_velocity = patch.linear_velocity;
    }
    if ((patch.fields_present & FASTDIS_ES_FIELD_DEAD_RECKONING) != 0ull) {
        out.dead_reckoning_algorithm = patch.dead_reckoning_algorithm;
        std::memcpy(out.dead_reckoning_parameters, patch.dead_reckoning_parameters, sizeof(out.dead_reckoning_parameters));
        out.dead_reckoning_linear_acceleration = patch.dead_reckoning_linear_acceleration;
        out.dead_reckoning_angular_velocity = patch.dead_reckoning_angular_velocity;
    }
    out.fields_present |= patch.fields_present;
    return out;
}

static inline fastdis_status_t parse_entity_state_update_transform(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_transform_t *out_transform) noexcept {

    if (data == nullptr || out_transform == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_state_update_header(&header)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_entity_transform_t out;
    std::memset(&out, 0, sizeof(out));
    out.entity_id = read_entity_id(p + 0);
    out.exercise_id = header.exercise_id;
    out.version = header.version;
    out.timestamp = header.timestamp;
    out.linear_velocity = read_vec3f(p + 8);
    out.location = read_world_coordinates(p + 20);
    out.orientation = read_euler_angles(p + 44);
    out.appearance = be32(p + 56);
    out.fields_present = FASTDIS_ES_FIELD_HEADER |
                         FASTDIS_ES_FIELD_ENTITY_ID |
                         FASTDIS_ES_FIELD_LINEAR_VELOCITY |
                         FASTDIS_ES_FIELD_LOCATION |
                         FASTDIS_ES_FIELD_ORIENTATION |
                         FASTDIS_ES_FIELD_APPEARANCE;
    *out_transform = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_entity_transform_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_transform_t *out_transform) noexcept {
    if (out_transform == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (is_entity_state_update_header(&header)) {
        return parse_entity_state_update_transform(data, size, flags, out_transform);
    }
    if (!is_entity_state_header(&header)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }

    fastdis_entity_state_prefix_t entity_state;
    rc = fastdis_parse_entity_state_fields(data, size, flags, transform_field_mask(), &entity_state);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    *out_transform = transform_from_entity_state(entity_state);
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_fire_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_fire_t *out_fire) noexcept {
    if (data == nullptr || out_fire == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_warfare_header(&header, FASTDIS_FIRE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_FIRE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_FIRE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_fire_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_entity_id = read_entity_id(p + 0);
    out.target_entity_id = read_entity_id(p + 6);
    out.munition_entity_id = read_entity_id(p + 12);
    out.event_id = read_event_id(p + 18);
    out.fire_mission_index = be32(p + 24);
    out.world_location = read_world_coordinates(p + 28);
    out.munition_descriptor = read_burst_descriptor(p + 52);
    out.velocity = read_vec3f(p + 68);
    out.range_to_target = be_float32(p + 80);
    *out_fire = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_detonation_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_detonation_t *out_detonation) noexcept {
    if (data == nullptr || out_detonation == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_warfare_header(&header, FASTDIS_DETONATION_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DETONATION_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_DETONATION_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t variable_parameter_count = p[89];
    const uint32_t expected_length =
        static_cast<uint32_t>(FASTDIS_DETONATION_FIXED_SIZE) +
        (static_cast<uint32_t>(variable_parameter_count) * 16u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    fastdis_detonation_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_entity_id = read_entity_id(p + 0);
    out.target_entity_id = read_entity_id(p + 6);
    out.exploding_entity_id = read_entity_id(p + 12);
    out.event_id = read_event_id(p + 18);
    out.velocity = read_vec3f(p + 24);
    out.world_location = read_world_coordinates(p + 36);
    out.munition_descriptor = read_burst_descriptor(p + 60);
    out.location_in_entity_coordinates = read_vec3f(p + 76);
    out.detonation_result = p[76 + 12];
    out.variable_parameter_count = variable_parameter_count;
    out.padding1 = be16(p + 78);
    *out_detonation = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_collision_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_collision_t *out_collision) noexcept {
    if (data == nullptr || out_collision == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_warfare_header(&header, FASTDIS_COLLISION_PDU_TYPE) &&
        !(header.pdu_type == FASTDIS_COLLISION_PDU_TYPE &&
          header.protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_COLLISION_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_COLLISION_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_collision_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.issuing_entity_id = read_entity_id(p + 0);
    out.colliding_entity_id = read_entity_id(p + 6);
    out.event_id = read_event_id(p + 12);
    out.collision_type = p[18];
    out.padding1 = p[19];
    out.velocity = read_vec3f(p + 20);
    out.mass = be_float32(p + 32);
    out.location = read_vec3f(p + 36);
    *out_collision = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_collision_elastic_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_collision_elastic_t *out_collision) noexcept {
    if (data == nullptr || out_collision == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (header.pdu_type != FASTDIS_COLLISION_ELASTIC_PDU_TYPE ||
        header.protocol_family != FASTDIS_ENTITY_INFORMATION_FAMILY) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_COLLISION_ELASTIC_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_COLLISION_ELASTIC_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_collision_elastic_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.issuing_entity_id = read_entity_id(p + 0);
    out.colliding_entity_id = read_entity_id(p + 6);
    out.event_id = read_event_id(p + 12);
    out.padding1 = be16(p + 18);
    out.contact_velocity = read_vec3f(p + 20);
    out.mass = be_float32(p + 32);
    out.location = read_vec3f(p + 36);
    out.collision_result_xx = be_float32(p + 48);
    out.collision_result_xy = be_float32(p + 52);
    out.collision_result_xz = be_float32(p + 56);
    out.collision_result_yy = be_float32(p + 60);
    out.collision_result_yz = be_float32(p + 64);
    out.collision_result_zz = be_float32(p + 68);
    out.unit_surface_normal = read_vec3f(p + 72);
    out.coefficient_of_restitution = be_float32(p + 84);
    *out_collision = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_directed_energy_fire_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_directed_energy_fire_t *out_fire) noexcept {
    if (data == nullptr || out_fire == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_warfare_header(&header, FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_directed_energy_fire_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_entity_id = read_entity_id(p + 0);
    out.target_entity_id = read_entity_id(p + 6);
    out.munition_type = read_entity_type(p + 12);
    out.shot_start_time = read_clock_time(p + 20);
    out.commulative_shot_time = be_float32(p + 28);
    out.aperture_emitter_location = read_vec3f(p + 32);
    out.aperture_diameter = be_float32(p + 44);
    out.wavelength = be_float32(p + 48);
    out.peak_irradiance = be_float32(p + 52);
    out.pulse_repetition_frequency = be_float32(p + 56);
    out.pulse_width = static_cast<int32_t>(be32(p + 60));
    out.flags = static_cast<int32_t>(be32(p + 64));
    out.pulse_shape = static_cast<int8_t>(p[68]);
    out.padding1 = p[69];
    out.padding2 = be32(p + 70);
    out.padding3 = be16(p + 74);
    out.number_of_de_records = be16(p + 76);
    out.de_records = make_counted_bytes_view(data, header.length, FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE, out.number_of_de_records);
    *out_fire = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_entity_damage_status_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_damage_status_t *out_status) noexcept {
    if (data == nullptr || out_status == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_warfare_header(&header, FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_entity_damage_status_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_entity_id = read_entity_id(p + 0);
    out.target_entity_id = read_entity_id(p + 6);
    out.damaged_entity_id = read_entity_id(p + 12);
    out.padding1 = be16(p + 18);
    out.padding2 = be16(p + 20);
    out.number_of_damage_description = be16(p + 22);
    out.damage_description_records = make_counted_bytes_view(data, header.length, FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE, out.number_of_damage_description);
    *out_status = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_simulation_management_request_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    uint16_t fixed_size,
    fastdis_simulation_management_request_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, expected_pdu_type)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, fixed_size)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_simulation_management_request_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_acknowledge_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    uint16_t fixed_size,
    uint8_t expected_family,
    fastdis_acknowledge_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    const bool family_match = expected_family == 5u
        ? is_simulation_management_header(&header, expected_pdu_type)
        : is_simulation_management_reliable_header(&header, expected_pdu_type);
    if (!family_match) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, fixed_size)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_acknowledge_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.acknowledge_flag = be16(p + 12);
    out.response_flag = be16(p + 14);
    out.request_id = be32(p + 16);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_datum_record_set_view_t make_datum_record_view(
    const uint8_t *data,
    uint16_t declared_length,
    uint16_t fixed_size,
    uint32_t fixed_count,
    uint32_t variable_count) noexcept {
    fastdis_datum_record_set_view_t view;
    std::memset(&view, 0, sizeof(view));
    view.datum_record_bytes = data + fixed_size;
    view.datum_record_bytes_size = static_cast<size_t>(declared_length - fixed_size);
    view.datum_record_bytes_user = nullptr;
    view.number_of_fixed_datum_records = fixed_count;
    view.number_of_variable_datum_records = variable_count;
    return view;
}

static inline fastdis_counted_bytes_view_t make_counted_bytes_view(
    const uint8_t *data,
    uint16_t declared_length,
    uint16_t fixed_size,
    uint32_t count) noexcept {
    fastdis_counted_bytes_view_t view;
    std::memset(&view, 0, sizeof(view));
    view.bytes = data + fixed_size;
    view.bytes_size = static_cast<size_t>(declared_length - fixed_size);
    view.bytes_user = nullptr;
    view.count = count;
    return view;
}

static inline fastdis_counted_bytes_view_t make_counted_bytes_subview(
    const uint8_t *data,
    uint16_t declared_length,
    uint16_t start_offset,
    size_t byte_length,
    uint32_t count) noexcept {
    fastdis_counted_bytes_view_t view;
    std::memset(&view, 0, sizeof(view));
    if (declared_length <= start_offset) {
        view.count = count;
        return view;
    }
    const size_t available = static_cast<size_t>(declared_length - start_offset);
    const size_t used = byte_length < available ? byte_length : available;
    view.bytes = data + start_offset;
    view.bytes_size = used;
    view.bytes_user = nullptr;
    view.count = count;
    return view;
}

static inline fastdis_status_t parse_action_request_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_ACTION_REQUEST_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ACTION_REQUEST_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_action_request_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.action_id = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_ACTION_REQUEST_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_action_response_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_ACTION_RESPONSE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ACTION_RESPONSE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_action_response_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.request_status = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_ACTION_RESPONSE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_data_query_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_DATA_QUERY_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DATA_QUERY_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 28);
    const uint32_t variable_count = be32(p + 32);
    fastdis_data_query_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.time_interval = read_clock_time(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_DATA_QUERY_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_set_data_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    fastdis_set_data_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, expected_pdu_type)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_SET_DATA_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_set_data_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.padding1 = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_SET_DATA_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_event_report_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_EVENT_REPORT_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_EVENT_REPORT_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_event_report_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.event_type = be32(p + 12);
    out.padding1 = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_EVENT_REPORT_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_comment_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_comment_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_COMMENT_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_COMMENT_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 12);
    const uint32_t variable_count = be32(p + 16);
    fastdis_comment_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_COMMENT_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_simulation_management_reliable_request_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    uint16_t fixed_size,
    fastdis_simulation_management_reliable_request_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, expected_pdu_type)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, fixed_size)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_simulation_management_reliable_request_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.required_reliability_service = p[12];
    out.pad1 = be16(p + 13);
    out.pad2 = p[15];
    out.request_id = be32(p + 16);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_action_request_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_ACTION_REQUEST_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 28);
    const uint32_t variable_count = be32(p + 32);
    fastdis_action_request_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.required_reliability_service = p[12];
    out.pad1 = be16(p + 13);
    out.pad2 = p[15];
    out.request_id = be32(p + 16);
    out.action_id = be32(p + 20);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_action_response_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_ACTION_RESPONSE_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_action_response_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.response_status = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_data_query_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 28);
    const uint32_t variable_count = be32(p + 32);
    fastdis_data_query_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.required_reliability_service = p[12];
    out.pad1 = be16(p + 13);
    out.pad2 = p[15];
    out.request_id = be32(p + 16);
    out.time_interval = read_clock_time(p + 20);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_set_data_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    fastdis_set_data_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, expected_pdu_type)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_set_data_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.required_reliability_service = p[12];
    out.pad1 = be16(p + 13);
    out.pad2 = p[15];
    out.request_id = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_data_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_DATA_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DATA_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_data_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.required_reliability_service = p[16];
    out.pad1 = be16(p + 17);
    out.pad2 = p[19];
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_DATA_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_event_report_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_EVENT_REPORT_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 20);
    const uint32_t variable_count = be32(p + 24);
    fastdis_event_report_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.event_type = be32(p + 12);
    out.pad1 = be32(p + 16);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_comment_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_comment_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_COMMENT_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_COMMENT_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t fixed_count = be32(p + 12);
    const uint32_t variable_count = be32(p + 16);
    fastdis_comment_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.datum_records = make_datum_record_view(data, header.length, FASTDIS_COMMENT_RELIABLE_FIXED_SIZE, fixed_count, variable_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_record_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_record_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_RECORD_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_RECORD_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t record_set_count = be32(p + 20);
    fastdis_record_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.required_reliability_service = p[16];
    out.pad1 = p[17];
    out.event_type = be16(p + 18);
    out.record_sets = make_counted_bytes_view(data, header.length, FASTDIS_RECORD_RELIABLE_FIXED_SIZE, record_set_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_set_record_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_set_record_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t record_set_count = be32(p + 20);
    fastdis_set_record_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.required_reliability_service = p[16];
    out.pad1 = be16(p + 17);
    out.pad2 = p[19];
    out.record_sets = make_counted_bytes_view(data, header.length, FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE, record_set_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_record_query_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_record_query_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint32_t record_count = be32(p + 26);
    fastdis_record_query_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.required_reliability_service = p[16];
    out.pad1 = be16(p + 17);
    out.pad2 = p[19];
    out.event_type = be16(p + 20);
    out.time = be32(p + 22);
    out.record_ids = make_counted_bytes_view(data, header.length, FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE, record_count);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_service_request_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_service_request_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_SERVICE_REQUEST_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_SERVICE_REQUEST_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_service_request_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.requesting_entity_id = read_entity_id(p + 0);
    out.servicing_entity_id = read_entity_id(p + 6);
    out.service_type_requested = p[12];
    out.number_of_supply_types = p[13];
    out.service_request_padding = static_cast<int16_t>(be16(p + 14));
    out.supplies = make_counted_bytes_view(data, header.length, FASTDIS_SERVICE_REQUEST_FIXED_SIZE, out.number_of_supply_types);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_resupply_offer_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_offer_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_RESUPPLY_OFFER_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_RESUPPLY_OFFER_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_resupply_offer_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.receiving_entity_id = read_entity_id(p + 0);
    out.supplying_entity_id = read_entity_id(p + 6);
    out.number_of_supply_types = p[12];
    out.padding_bytes[0] = p[13];
    out.padding_bytes[1] = p[14];
    out.padding_bytes[2] = p[15];
    out.supplies = make_counted_bytes_view(data, header.length, FASTDIS_RESUPPLY_OFFER_FIXED_SIZE, out.number_of_supply_types);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_resupply_received_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_received_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_resupply_received_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.receiving_entity_id = read_entity_id(p + 0);
    out.supplying_entity_id = read_entity_id(p + 6);
    out.number_of_supply_types = p[12];
    out.padding1 = be16(p + 13);
    out.padding2 = p[15];
    out.supplies = make_counted_bytes_view(data, header.length, FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE, out.number_of_supply_types);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_resupply_cancel_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_cancel_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_RESUPPLY_CANCEL_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_resupply_cancel_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.receiving_entity_id = read_entity_id(p + 0);
    out.supplying_entity_id = read_entity_id(p + 6);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_repair_complete_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_repair_complete_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_REPAIR_COMPLETE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_REPAIR_COMPLETE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_repair_complete_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.receiving_entity_id = read_entity_id(p + 0);
    out.repairing_entity_id = read_entity_id(p + 6);
    out.repair = be16(p + 12);
    out.padding2 = static_cast<int16_t>(be16(p + 14));
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_repair_response_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_repair_response_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_logistics_header(&header, FASTDIS_REPAIR_RESPONSE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_REPAIR_RESPONSE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_repair_response_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.receiving_entity_id = read_entity_id(p + 0);
    out.repairing_entity_id = read_entity_id(p + 6);
    out.repair_result = p[12];
    out.padding1 = be16(p + 13);
    out.padding2 = p[15];
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_designator_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_designator_t *out_designator) noexcept {
    if (data == nullptr || out_designator == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_distributed_emissions_header(&header, FASTDIS_DESIGNATOR_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_DESIGNATOR_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_designator_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.designating_entity_id = read_entity_id(p + 0);
    out.code_name = be16(p + 6);
    out.designated_entity_id = read_entity_id(p + 8);
    out.designator_code = be16(p + 14);
    out.designator_power = be_float32(p + 16);
    out.designator_wavelength = be_float32(p + 20);
    out.designator_spot_wrt_designated = read_vec3f(p + 24);
    out.designator_spot_location = read_world_coordinates(p + 36);
    out.dead_reckoning_algorithm = p[60];
    out.padding1 = be16(p + 61);
    out.padding2 = p[63];
    out.entity_linear_acceleration = read_vec3f(p + 64);
    *out_designator = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_transmitter_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_transmitter_t *out_transmitter) noexcept {
    if (data == nullptr || out_transmitter == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_radio_header(&header, FASTDIS_TRANSMITTER_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_TRANSMITTER_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_transmitter_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.entity_id = read_entity_id(p + 0);
    out.radio_id = be16(p + 6);
    if (header.version < FASTDIS_PROTOCOL_VERSION_DIS7) {
        out.radio_entity_type = read_radio_entity_type(p + 8);
    } else {
        out.entity_type = read_entity_type(p + 8);
        out.variable_transmitter_parameter_count = be16(p + 18);
    }
    out.transmit_state = p[16];
    out.input_source = p[17];
    out.antenna_location = read_world_coordinates(p + 20);
    out.relative_antenna_location = read_vec3f(p + 44);
    out.antenna_pattern_type = be16(p + 56);
    out.antenna_pattern_count = be16(p + 58);
    out.frequency = be32(p + 60);
    out.transmit_frequency_bandwidth = be_float32(p + 64);
    out.power = be_float32(p + 68);
    out.modulation_type = read_modulation_type(p + 72);
    out.crypto_system = be16(p + 80);
    out.crypto_key_id = be16(p + 82);
    out.modulation_parameter_count = p[84];
    out.padding2 = be16(p + 85);
    out.padding3 = p[87];
    const size_t tail_bytes = static_cast<size_t>(header.length - FASTDIS_TRANSMITTER_FIXED_SIZE);
    size_t modulation_bytes = header.version < FASTDIS_PROTOCOL_VERSION_DIS7
        ? static_cast<size_t>(out.modulation_parameter_count)
        : static_cast<size_t>(out.modulation_parameter_count) * 12u;
    if (modulation_bytes > tail_bytes) {
        modulation_bytes = tail_bytes;
    }
    out.modulation_parameters = make_counted_bytes_subview(
        data,
        header.length,
        FASTDIS_TRANSMITTER_FIXED_SIZE,
        modulation_bytes,
        out.modulation_parameter_count);
    out.antenna_patterns = make_counted_bytes_subview(
        data,
        header.length,
        static_cast<uint16_t>(FASTDIS_TRANSMITTER_FIXED_SIZE + modulation_bytes),
        tail_bytes - modulation_bytes,
        out.antenna_pattern_count);
    *out_transmitter = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_other_pdu_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_other_pdu_t *out_other) noexcept {
    if (data == nullptr || out_other == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_protocol_family_zero_header(&header, FASTDIS_OTHER_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_OTHER_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_other_pdu_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.opaque_payload = make_counted_bytes_view(data, header.length, FASTDIS_OTHER_FIXED_SIZE, 0u);
    *out_other = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_aggregate_state_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_aggregate_state_t *out_aggregate) noexcept {
    if (data == nullptr || out_aggregate == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_management_header(&header, FASTDIS_AGGREGATE_STATE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_AGGREGATE_STATE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_aggregate_state_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.aggregate_id = read_entity_id(p + 0);
    out.force_id = p[6];
    out.aggregate_state = p[7];
    out.aggregate_type = read_entity_type(p + 8);
    out.formation = be32(p + 16);
    out.aggregate_marking_character_set = p[20];
    std::memcpy(out.aggregate_marking, p + 21, 31);
    out.aggregate_marking[31] = 0u;
    out.dimensions = read_vec3f(p + 52);
    out.orientation = read_euler_angles(p + 64);
    out.center_of_mass = read_world_coordinates(p + 76);
    out.velocity = read_vec3f(p + 100);
    out.number_of_dis_aggregates = be16(p + 112);
    out.number_of_dis_entities = be16(p + 114);
    out.number_of_silent_aggregate_types = be16(p + 116);
    out.number_of_silent_entity_types = be16(p + 118);
    out.aggregate_records = make_counted_bytes_view(data, header.length, FASTDIS_AGGREGATE_STATE_FIXED_SIZE, 0u);
    *out_aggregate = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_is_group_of_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_is_group_of_t *out_group) noexcept {
    if (data == nullptr || out_group == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_management_header(&header, FASTDIS_IS_GROUP_OF_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_IS_GROUP_OF_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_is_group_of_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.group_entity_id = read_entity_id(p + 0);
    out.grouped_entity_category = p[6];
    out.number_of_grouped_entities = p[7];
    out.pad2 = be32(p + 8);
    out.latitude = be_float64(p + 12);
    out.longitude = be_float64(p + 20);
    out.grouped_entity_descriptions = make_counted_bytes_view(data, header.length, FASTDIS_IS_GROUP_OF_FIXED_SIZE, out.number_of_grouped_entities);
    *out_group = out;
    return FASTDIS_OK;
}

template <typename T>
static inline fastdis_status_t parse_transfer_request_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint8_t expected_pdu_type,
    T *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_management_header(&header, expected_pdu_type)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    T out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.required_reliability_service = p[16];
    out.transfer_type = p[17];
    out.transfer_entity_id = read_entity_id(p + 18);
    out.number_of_record_sets = p[24];
    out.record_sets = make_counted_bytes_view(data, header.length, FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE, out.number_of_record_sets);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_is_part_of_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_is_part_of_t *out_part) noexcept {
    if (data == nullptr || out_part == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_management_header(&header, FASTDIS_IS_PART_OF_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_IS_PART_OF_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_IS_PART_OF_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_is_part_of_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.relationship = read_relationship(p + 12);
    out.part_location = read_vec3f(p + 16);
    out.named_location = read_named_location(p + 28);
    out.part_entity_type = read_entity_type(p + 32);
    *out_part = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_minefield_state_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_state_t *out_state) noexcept {
    if (data == nullptr || out_state == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_minefield_header(&header, FASTDIS_MINEFIELD_STATE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_MINEFIELD_STATE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_perimeter_points = p[9];
    const uint16_t number_of_mine_types = be16(p + 18);
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_MINEFIELD_STATE_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_perimeter_points) * 8u) +
        (static_cast<uint32_t>(number_of_mine_types) * 8u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_minefield_state_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.minefield_id = read_entity_id(p + 0);
    out.minefield_sequence = be16(p + 6);
    out.force_id = p[8];
    out.number_of_perimeter_points = number_of_perimeter_points;
    out.minefield_type = read_entity_type(p + 10);
    out.number_of_mine_types = number_of_mine_types;
    out.minefield_location = read_world_coordinates(p + 20);
    out.minefield_orientation = read_euler_angles(p + 44);
    out.appearance = be16(p + 56);
    out.protocol_mode = be16(p + 58);
    const uint16_t perimeter_offset = FASTDIS_MINEFIELD_STATE_FIXED_SIZE;
    const size_t perimeter_bytes = static_cast<size_t>(number_of_perimeter_points) * 8u;
    out.perimeter_points = make_counted_bytes_subview(data, header.length, perimeter_offset, perimeter_bytes, number_of_perimeter_points);
    out.mine_types = make_counted_bytes_subview(
        data,
        header.length,
        static_cast<uint16_t>(perimeter_offset + perimeter_bytes),
        static_cast<size_t>(number_of_mine_types) * 8u,
        number_of_mine_types);
    *out_state = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_minefield_query_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_query_t *out_query) noexcept {
    if (data == nullptr || out_query == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_minefield_header(&header, FASTDIS_MINEFIELD_QUERY_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_MINEFIELD_QUERY_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_perimeter_points = p[13];
    const uint8_t number_of_sensor_types = p[15];
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_MINEFIELD_QUERY_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_perimeter_points) * 8u) +
        (static_cast<uint32_t>(number_of_sensor_types) * 2u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_minefield_query_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.minefield_id = read_entity_id(p + 0);
    out.requesting_entity_id = read_entity_id(p + 6);
    out.request_id = p[12];
    out.number_of_perimeter_points = number_of_perimeter_points;
    out.pad2 = p[14];
    out.number_of_sensor_types = number_of_sensor_types;
    out.data_filter = be32(p + 16);
    out.requested_mine_type = read_entity_type(p + 20);
    const uint16_t perimeter_offset = FASTDIS_MINEFIELD_QUERY_FIXED_SIZE;
    const size_t perimeter_bytes = static_cast<size_t>(number_of_perimeter_points) * 8u;
    out.requested_perimeter_points = make_counted_bytes_subview(data, header.length, perimeter_offset, perimeter_bytes, number_of_perimeter_points);
    out.sensor_types = make_counted_bytes_subview(
        data,
        header.length,
        static_cast<uint16_t>(perimeter_offset + perimeter_bytes),
        static_cast<size_t>(number_of_sensor_types) * 2u,
        number_of_sensor_types);
    *out_query = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_minefield_data_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_data_t *out_data) noexcept {
    if (data == nullptr || out_data == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_minefield_header(&header, FASTDIS_MINEFIELD_DATA_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_MINEFIELD_DATA_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_mines_in_this_pdu = p[17];
    const uint8_t number_of_sensor_types = p[18];
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_MINEFIELD_DATA_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_sensor_types) * 2u) +
        1u +
        (static_cast<uint32_t>(number_of_mines_in_this_pdu) * 12u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_minefield_data_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.minefield_id = read_entity_id(p + 0);
    out.requesting_entity_id = read_entity_id(p + 6);
    out.minefield_sequence_number = be16(p + 12);
    out.request_id = p[14];
    out.pdu_sequence_number = p[15];
    out.number_of_pdus = p[16];
    out.number_of_mines_in_this_pdu = number_of_mines_in_this_pdu;
    out.number_of_sensor_types = number_of_sensor_types;
    out.pad2 = p[19];
    out.data_filter = be32(p + 20);
    out.mine_type = read_entity_type(p + 24);
    const uint16_t sensor_offset = FASTDIS_MINEFIELD_DATA_FIXED_SIZE;
    const size_t sensor_bytes = static_cast<size_t>(number_of_sensor_types) * 2u;
    out.sensor_types = make_counted_bytes_subview(data, header.length, sensor_offset, sensor_bytes, number_of_sensor_types);
    out.pad3 = *(data + sensor_offset + sensor_bytes);
    out.mine_locations = make_counted_bytes_subview(
        data,
        header.length,
        static_cast<uint16_t>(sensor_offset + sensor_bytes + 1u),
        static_cast<size_t>(number_of_mines_in_this_pdu) * 12u,
        number_of_mines_in_this_pdu);
    *out_data = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_minefield_response_nack_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_response_nack_t *out_nack) noexcept {
    if (data == nullptr || out_nack == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_minefield_header(&header, FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_missing_pdus = p[13];
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_missing_pdus) * 8u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_minefield_response_nack_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.minefield_id = read_entity_id(p + 0);
    out.requesting_entity_id = read_entity_id(p + 6);
    out.request_id = p[12];
    out.number_of_missing_pdus = number_of_missing_pdus;
    out.missing_pdu_sequence_numbers = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE,
        number_of_missing_pdus);
    *out_nack = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_environmental_process_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_environmental_process_t *out_process) noexcept {
    if (data == nullptr || out_process == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_synthetic_environment_header(&header, FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_environmental_process_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.environmental_process_id = read_entity_id(p + 0);
    out.environment_type = read_entity_type(p + 6);
    out.model_type = p[14];
    out.environment_status = p[15];
    out.number_of_environment_records = p[16];
    out.sequence_number = be16(p + 17);
    out.environment_records = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE,
        out.number_of_environment_records);
    *out_process = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_gridded_data_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_gridded_data_t *out_grid) noexcept {
    if (data == nullptr || out_grid == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_synthetic_environment_header(&header, FASTDIS_GRIDDED_DATA_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_GRIDDED_DATA_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_gridded_data_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.environmental_simulation_application_id = read_entity_id(p + 0);
    out.field_number = be16(p + 6);
    out.pdu_number = be16(p + 8);
    out.pdu_total = be16(p + 10);
    out.coordinate_system = be16(p + 12);
    out.number_of_grid_axes = p[14];
    out.constant_grid = p[15];
    out.environment_type = read_entity_type(p + 16);
    out.orientation = read_euler_angles(p + 24);
    out.sample_time = be64(p + 36);
    out.total_values = be32(p + 44);
    out.vector_dimension = p[48];
    out.padding1 = be16(p + 49);
    out.padding2 = p[51];
    out.grid_data = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_GRIDDED_DATA_FIXED_SIZE,
        out.total_values);
    *out_grid = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_point_object_state_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_point_object_state_t *out_point) noexcept {
    if (data == nullptr || out_point == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_synthetic_environment_header(&header, FASTDIS_POINT_OBJECT_STATE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    const bool is_dis7 = header.version >= FASTDIS_PROTOCOL_VERSION_DIS7;
    const uint16_t fixed_size = is_dis7
        ? FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE
        : FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE;
    const uint16_t object_type_size = is_dis7 ? 4u : 6u;
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, fixed_size)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint16_t object_type_offset = 16u;
    const uint16_t location_offset = static_cast<uint16_t>(object_type_offset + object_type_size);
    const uint16_t orientation_offset = static_cast<uint16_t>(location_offset + 24u);
    const uint16_t appearance_offset = static_cast<uint16_t>(orientation_offset + 12u);
    const uint16_t requester_offset = static_cast<uint16_t>(appearance_offset + 8u);
    const uint16_t receiving_offset = static_cast<uint16_t>(requester_offset + 4u);
    const uint16_t pad2_offset = static_cast<uint16_t>(receiving_offset + 4u);
    fastdis_point_object_state_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.object_id = read_entity_id(p + 0);
    out.referenced_object_id = read_entity_id(p + 6);
    out.update_number = be16(p + 12);
    out.force_id = p[14];
    out.modifications = p[15];
    out.object_type = is_dis7
        ? read_environment_object_type_dis7(p + object_type_offset)
        : read_environment_object_type_dis6(p + object_type_offset);
    out.object_location = read_world_coordinates(p + location_offset);
    out.object_orientation = read_euler_angles(p + orientation_offset);
    out.object_appearance = be_float64(p + appearance_offset);
    out.requester_id.site = be16(p + requester_offset);
    out.requester_id.application = be16(p + requester_offset + 2u);
    out.receiving_id.site = be16(p + receiving_offset);
    out.receiving_id.application = be16(p + receiving_offset + 2u);
    out.pad2 = be32(p + pad2_offset);
    *out_point = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_linear_object_state_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_linear_object_state_t *out_linear) noexcept {
    if (data == nullptr || out_linear == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_synthetic_environment_header(&header, FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    const bool is_dis7 = header.version >= FASTDIS_PROTOCOL_VERSION_DIS7;
    const uint16_t fixed_size = is_dis7
        ? FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE
        : FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE;
    const uint16_t segment_size = is_dis7
        ? FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE
        : FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE;
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_segments = p[15];
    const uint32_t expected_length = static_cast<uint32_t>(fixed_size) +
        (static_cast<uint32_t>(number_of_segments) * static_cast<uint32_t>(segment_size));
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_linear_object_state_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.object_id = read_entity_id(p + 0);
    out.referenced_object_id = read_entity_id(p + 6);
    out.update_number = be16(p + 12);
    out.force_id = p[14];
    out.number_of_segments = number_of_segments;
    out.requester_id.site = be16(p + 16);
    out.requester_id.application = be16(p + 18);
    out.receiving_id.site = be16(p + 20);
    out.receiving_id.application = be16(p + 22);
    out.object_type = is_dis7
        ? read_environment_object_type_dis7(p + 24)
        : read_environment_object_type_dis6(p + 24);
    out.linear_segment_parameters = make_counted_bytes_subview(
        data,
        header.length,
        fixed_size,
        static_cast<size_t>(number_of_segments) * segment_size,
        number_of_segments);
    *out_linear = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_areal_object_state_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_areal_object_state_t *out_areal) noexcept {
    if (data == nullptr || out_areal == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_synthetic_environment_header(&header, FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint16_t number_of_points = be16(p + 30);
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_points) * 24u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_areal_object_state_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.object_id = read_entity_id(p + 0);
    out.referenced_object_id = read_entity_id(p + 6);
    out.update_number = be16(p + 12);
    out.force_id = p[14];
    out.modifications = p[15];
    out.object_type = read_entity_type(p + 16);
    out.object_appearance = make_counted_bytes_subview(data, header.length, 36u, 6u, 6u);
    out.number_of_points = number_of_points;
    out.requester_id.site = be16(p + 32);
    out.requester_id.application = be16(p + 34);
    out.receiving_id.site = be16(p + 36);
    out.receiving_id.application = be16(p + 38);
    out.object_locations = make_counted_bytes_subview(
        data,
        header.length,
        52u,
        static_cast<size_t>(number_of_points) * 24u,
        number_of_points);
    *out_areal = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_tspi_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_tspi_t *out_tspi) noexcept {
    if (data == nullptr || out_tspi == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_live_entity_header(&header, FASTDIS_TSPI_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_TSPI_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t system_specific_data_length = p[43];
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_TSPI_FIXED_SIZE) +
        static_cast<uint32_t>(system_specific_data_length);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_tspi_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.live_entity_id = read_live_entity_id(p + 0);
    out.tspi_flag = p[4];
    out.entity_location = make_counted_bytes_subview(data, header.length, 17u, 6u, 1u);
    out.entity_linear_velocity = make_counted_bytes_subview(data, header.length, 23u, 6u, 1u);
    out.entity_orientation = make_counted_bytes_subview(data, header.length, 29u, 6u, 1u);
    out.position_error = make_counted_bytes_subview(data, header.length, 35u, 6u, 1u);
    out.orientation_error = make_counted_bytes_subview(data, header.length, 41u, 3u, 1u);
    out.dead_reckoning_parameters = make_counted_bytes_subview(data, header.length, 44u, 9u, 1u);
    out.measured_speed = be16(p + 41);
    out.system_specific_data_length = system_specific_data_length;
    out.system_specific_data = make_counted_bytes_subview(
        data,
        header.length,
        FASTDIS_TSPI_FIXED_SIZE,
        system_specific_data_length,
        system_specific_data_length);
    *out_tspi = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_live_entity_appearance_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_live_entity_appearance_t *out_appearance) noexcept {
    if (data == nullptr || out_appearance == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_live_entity_header(&header, FASTDIS_APPEARANCE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_APPEARANCE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_APPEARANCE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_live_entity_appearance_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.live_entity_id = read_live_entity_id(p + 0);
    out.appearance_flags = be16(p + 4);
    out.force_id = p[6];
    out.padding1 = p[7];
    out.entity_type = read_entity_type(p + 8);
    out.alternate_entity_type = read_entity_type(p + 16);
    std::memcpy(out.entity_marking, p + 24, 12);
    out.capabilities = be32(p + 36);
    out.appearance_fields = make_counted_bytes_subview(data, header.length, 52u, 4u, 1u);
    *out_appearance = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_articulated_parts_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_articulated_parts_t *out_parts) noexcept {
    if (data == nullptr || out_parts == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_live_entity_header(&header, FASTDIS_ARTICULATED_PARTS_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ARTICULATED_PARTS_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    const uint8_t number_of_parameter_records = p[4];
    const uint32_t expected_length = static_cast<uint32_t>(FASTDIS_ARTICULATED_PARTS_FIXED_SIZE) +
        (static_cast<uint32_t>(number_of_parameter_records) * 16u);
    if (header.length < expected_length) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, expected_length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    fastdis_articulated_parts_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.live_entity_id = read_live_entity_id(p + 0);
    out.number_of_parameter_records = number_of_parameter_records;
    out.padding[0] = p[5];
    out.padding[1] = p[6];
    out.padding[2] = p[7];
    out.variable_parameters = make_counted_bytes_subview(
        data,
        header.length,
        FASTDIS_ARTICULATED_PARTS_FIXED_SIZE,
        static_cast<size_t>(number_of_parameter_records) * 16u,
        number_of_parameter_records);
    *out_parts = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_le_fire_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_le_fire_t *out_fire) noexcept {
    if (data == nullptr || out_fire == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_live_entity_header(&header, FASTDIS_LE_FIRE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_LE_FIRE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_LE_FIRE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_le_fire_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_live_entity_id = read_live_entity_id(p + 0);
    out.flags = p[4];
    out.padding1 = p[5];
    out.target_live_entity_id = read_live_entity_id(p + 6);
    out.munition_live_entity_id = read_live_entity_id(p + 10);
    out.event_id = read_live_event_id(p + 14);
    out.location = make_counted_bytes_subview(data, header.length, 30u, 6u, 1u);
    out.munition_descriptor = read_burst_descriptor(p + 24);
    out.velocity = make_counted_bytes_subview(data, header.length, 52u, 6u, 1u);
    out.range = be16(p + 46);
    *out_fire = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_le_detonation_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_le_detonation_t *out_detonation) noexcept {
    if (data == nullptr || out_detonation == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_live_entity_header(&header, FASTDIS_LE_DETONATION_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_LE_DETONATION_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_LE_DETONATION_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_le_detonation_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.firing_live_entity_id = read_live_entity_id(p + 0);
    out.detonation_flag1 = p[4];
    out.detonation_flag2 = p[5];
    out.target_live_entity_id = read_live_entity_id(p + 6);
    out.munition_live_entity_id = read_live_entity_id(p + 10);
    out.event_id = read_live_event_id(p + 14);
    out.world_location = make_counted_bytes_subview(data, header.length, 30u, 6u, 1u);
    out.velocity = make_counted_bytes_subview(data, header.length, 36u, 6u, 1u);
    out.munition_orientation = make_counted_bytes_subview(data, header.length, 42u, 6u, 1u);
    out.munition_descriptor = read_burst_descriptor(p + 36);
    out.entity_location = make_counted_bytes_subview(data, header.length, 64u, 6u, 1u);
    out.detonation_result = p[58];
    out.padding1 = p[59];
    *out_detonation = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_signal_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_signal_t *out_signal) noexcept {
    if (data == nullptr || out_signal == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_radio_header(&header, FASTDIS_SIGNAL_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    const uint16_t fixed_size = header.version >= FASTDIS_PROTOCOL_VERSION_DIS7
        ? FASTDIS_SIGNAL_DIS7_FIXED_SIZE
        : FASTDIS_SIGNAL_DIS6_FIXED_SIZE;
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_signal_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    size_t offset = 0u;
    if (header.version < FASTDIS_PROTOCOL_VERSION_DIS7) {
        out.entity_id = read_entity_id(p + 0);
        out.radio_id = be16(p + 6);
        offset = 8u;
    }
    out.encoding_scheme = be16(p + offset + 0u);
    out.tdl_type = be16(p + offset + 2u);
    out.sample_rate = be32(p + offset + 4u);
    out.data_length = be16(p + offset + 8u);
    out.samples = be16(p + offset + 10u);
    out.data = make_counted_bytes_view(data, header.length, fixed_size, out.data_length);
    *out_signal = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_receiver_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_receiver_t *out_receiver) noexcept {
    if (data == nullptr || out_receiver == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_radio_header(&header, FASTDIS_RECEIVER_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    const uint16_t fixed_size = header.version >= FASTDIS_PROTOCOL_VERSION_DIS7
        ? FASTDIS_RECEIVER_DIS7_FIXED_SIZE
        : FASTDIS_RECEIVER_DIS6_FIXED_SIZE;
    if (header.length < fixed_size) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_receiver_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    size_t offset = 0u;
    if (header.version < FASTDIS_PROTOCOL_VERSION_DIS7) {
        out.entity_id = read_entity_id(p + 0);
        out.radio_id = be16(p + 6);
        offset = 8u;
    }
    out.receiver_state = be16(p + offset + 0u);
    out.padding1 = be16(p + offset + 2u);
    out.received_power = be_float32(p + offset + 4u);
    out.transmitter_entity_id = read_entity_id(p + offset + 8u);
    out.transmitter_radio_id = be16(p + offset + 14u);
    *out_receiver = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_electronic_emissions_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_electronic_emissions_t *out_emissions) noexcept {
    if (data == nullptr || out_emissions == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_distributed_emissions_header(&header, FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_electronic_emissions_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.emitting_entity_id = read_entity_id(p + 0);
    out.event_id = read_event_id(p + 6);
    out.state_update_indicator = p[12];
    out.number_of_systems = p[13];
    out.padding1 = be16(p + 14);
    out.system_records = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE,
        out.number_of_systems);
    *out_emissions = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_iff_atc_navaids_layer1_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_iff_atc_navaids_layer1_t *out_iff) noexcept {
    if (data == nullptr || out_iff == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_distributed_emissions_header(&header, FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_iff_atc_navaids_layer1_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.emitting_entity_id = read_entity_id(p + 0);
    out.event_id = read_event_id(p + 6);
    out.location = read_vec3f(p + 12);
    out.system_id = read_system_id(p + 24);
    out.padding2 = be16(p + 30);
    out.fundamental_parameters = read_iff_fundamental_data(p + 32);
    *out_iff = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_ua_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_ua_t *out_ua) noexcept {
    if (data == nullptr || out_ua == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_distributed_emissions_header(&header, FASTDIS_UA_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_UA_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_ua_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.emitting_entity_id = read_entity_id(p + 0);
    out.event_id = read_event_id(p + 6);
    out.state_change_indicator = static_cast<int8_t>(p[12]);
    out.padding1 = p[13];
    out.passive_parameter_index = be16(p + 14);
    out.propulsion_plant_configuration = p[16];
    out.number_of_shafts = p[17];
    out.number_of_apas = p[18];
    out.number_of_ua_emitter_systems = p[19];
    out.ua_records = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_UA_FIXED_SIZE,
        static_cast<uint32_t>(out.number_of_shafts) +
            static_cast<uint32_t>(out.number_of_apas) +
            static_cast<uint32_t>(out.number_of_ua_emitter_systems));
    *out_ua = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_sees_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_sees_t *out_sees) noexcept {
    if (data == nullptr || out_sees == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_distributed_emissions_header(&header, FASTDIS_SEES_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_SEES_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_sees_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.infrared_signature_representation_index = be16(p + 6);
    out.acoustic_signature_representation_index = be16(p + 8);
    out.radar_cross_section_signature_representation_index = be16(p + 10);
    out.number_of_propulsion_systems = be16(p + 12);
    out.number_of_vectoring_nozzle_systems = be16(p + 14);
    out.supplemental_emission_records = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_SEES_FIXED_SIZE,
        static_cast<uint32_t>(out.number_of_propulsion_systems) +
            static_cast<uint32_t>(out.number_of_vectoring_nozzle_systems));
    *out_sees = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_iff_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_iff_t *out_iff) noexcept {
    if (data == nullptr || out_iff == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (header.version < FASTDIS_PROTOCOL_VERSION_DIS7 ||
        !is_distributed_emissions_header(&header, FASTDIS_IFF_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_IFF_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_iff_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.emitting_entity_id = read_entity_id(p + 0);
    out.event_id = read_event_id(p + 6);
    out.location = read_vec3f(p + 12);
    out.system_id = read_system_id(p + 24);
    out.padding2 = be16(p + 30);
    out.fundamental_parameters = read_iff_fundamental_data(p + 32);
    *out_iff = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_intercom_signal_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_signal_t *out_signal) noexcept {
    if (data == nullptr || out_signal == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_radio_header(&header, FASTDIS_INTERCOM_SIGNAL_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_intercom_signal_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.entity_id = read_entity_id(p + 0);
    out.communications_device_id = be16(p + 6);
    out.encoding_scheme = be16(p + 8);
    out.tdl_type = be16(p + 10);
    out.sample_rate = be32(p + 12);
    out.data_length = be16(p + 16);
    out.samples = be16(p + 18);
    out.data = make_counted_bytes_view(data, header.length, FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE, out.data_length);
    *out_signal = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_intercom_control_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_control_t *out_control) noexcept {
    if (data == nullptr || out_control == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_radio_header(&header, FASTDIS_INTERCOM_CONTROL_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_INTERCOM_CONTROL_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_intercom_control_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.control_type = p[0];
    out.communications_channel_type = p[1];
    out.source_entity_id = read_entity_id(p + 2);
    out.source_communications_device_id = p[8];
    out.source_line_id = p[9];
    out.transmit_priority = p[10];
    out.transmit_line_state = p[11];
    out.command = p[12];
    out.master_entity_id = read_entity_id(p + 13);
    out.master_communications_device_id = be16(p + 19);
    out.intercom_parameters_length = be32(p + 21);
    out.intercom_parameters = make_counted_bytes_view(
        data,
        header.length,
        FASTDIS_INTERCOM_CONTROL_FIXED_SIZE,
        out.intercom_parameters_length);
    *out_control = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_attribute_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_attribute_t *out_attribute) noexcept {
    if (data == nullptr || out_attribute == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_information_header(&header, FASTDIS_ATTRIBUTE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ATTRIBUTE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_attribute_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_simulation_address = read_simulation_address(p + 0);
    out.padding1 = static_cast<int32_t>(be32(p + 4));
    out.padding2 = static_cast<int16_t>(be16(p + 8));
    out.attribute_record_pdu_type = p[10];
    out.attribute_record_protocol_version = p[11];
    out.master_attribute_record_type = be32(p + 12);
    out.action_code = p[16];
    out.padding3 = static_cast<int8_t>(p[17]);
    out.number_attribute_record_set = be16(p + 18);
    out.attribute_record_sets = make_counted_bytes_view(data, header.length, FASTDIS_ATTRIBUTE_FIXED_SIZE, out.number_attribute_record_set);
    *out_attribute = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_information_operations_action_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_action_t *out_action) noexcept {
    if (data == nullptr || out_action == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_information_operations_header(&header, FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_information_operations_action_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_sim_id = read_entity_id(p + 0);
    out.receiving_sim_id = read_entity_id(p + 6);
    out.request_id = be32(p + 12);
    out.io_warfare_type = be16(p + 16);
    out.io_simulation_source = be16(p + 18);
    out.io_action_type = be16(p + 20);
    out.io_action_phase = be16(p + 22);
    out.padding1 = be32(p + 24);
    out.io_attacker_id = read_entity_id(p + 28);
    out.io_primary_target_id = read_entity_id(p + 34);
    out.padding2 = be16(p + 40);
    out.number_of_io_records = be16(p + 42);
    out.io_records = make_counted_bytes_view(data, header.length, FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE, out.number_of_io_records);
    *out_action = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_information_operations_report_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_report_t *out_report) noexcept {
    if (data == nullptr || out_report == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_information_operations_header(&header, FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, header.length)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }
    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_information_operations_report_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_sim_id = read_entity_id(p + 0);
    out.io_sim_source = be16(p + 6);
    out.io_report_type = p[8];
    out.padding1 = p[9];
    out.io_attacker_id = read_entity_id(p + 10);
    out.io_primary_target_id = read_entity_id(p + 16);
    out.padding2 = be16(p + 22);
    out.padding3 = be16(p + 24);
    out.number_of_io_records = be16(p + 26);
    out.io_records = make_counted_bytes_view(data, header.length, FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE, out.number_of_io_records);
    *out_report = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_start_resume_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_START_RESUME_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_START_RESUME_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_START_RESUME_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_start_resume_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.real_world_time = read_clock_time(p + 12);
    out.simulation_time = read_clock_time(p + 20);
    out.request_id = be32(p + 28);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_stop_freeze_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_header(&header, FASTDIS_STOP_FREEZE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_STOP_FREEZE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_STOP_FREEZE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_stop_freeze_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.real_world_time = read_clock_time(p + 12);
    out.reason = p[20];
    out.frozen_behavior = p[21];
    out.padding1 = be16(p + 22);
    out.request_id = be32(p + 24);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_start_resume_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_START_RESUME_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_start_resume_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.real_world_time = read_clock_time(p + 12);
    out.simulation_time = read_clock_time(p + 20);
    out.required_reliability_service = p[28];
    out.pad1 = be16(p + 29);
    out.pad2 = p[31];
    out.request_id = be32(p + 32);
    *out_request = out;
    return FASTDIS_OK;
}

static inline fastdis_status_t parse_stop_freeze_reliable_impl(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_reliable_t *out_request) noexcept {
    if (data == nullptr || out_request == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_simulation_management_reliable_header(&header, FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if (!need_bytes(size, FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE)) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;
    fastdis_stop_freeze_reliable_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.originating_entity_id = read_entity_id(p + 0);
    out.receiving_entity_id = read_entity_id(p + 6);
    out.real_world_time = read_clock_time(p + 12);
    out.reason = p[20];
    out.frozen_behavior = p[21];
    out.required_reliablity_service = p[22];
    out.pad1 = p[23];
    out.request_id = be32(p + 24);
    *out_request = out;
    return FASTDIS_OK;
}

static inline void append_transform_to_batch(
    fastdis_entity_transform_batch_t *batch,
    const fastdis_entity_transform_t &transform) noexcept {
    if (batch->count < batch->capacity) {
        batch->transforms[batch->count++] = transform;
    } else {
        batch->dropped += 1;
    }
}

static inline uint64_t transform_field_mask() noexcept {
    return FASTDIS_ES_FIELD_HEADER |
           FASTDIS_ES_FIELD_ENTITY_ID |
           FASTDIS_ES_FIELD_FORCE_ID |
           FASTDIS_ES_FIELD_LINEAR_VELOCITY |
           FASTDIS_ES_FIELD_LOCATION |
           FASTDIS_ES_FIELD_ORIENTATION |
           FASTDIS_ES_FIELD_APPEARANCE |
           FASTDIS_ES_FIELD_DEAD_RECKONING;
}

static inline fastdis_status_t apply_profile_to_config(fastdis_scan_config_t *config, uint32_t profile_kind) noexcept {
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    const uint32_t flags = config->flags;
    const uint32_t sample_every = config->sample_every == 0u ? 1u : config->sample_every;
    const uint32_t sample_offset = config->sample_offset;

    fastdis_scan_config_init(config);
    config->flags = flags;
    config->sample_every = sample_every;
    config->sample_offset = sample_offset;

    switch (profile_kind) {
        case FASTDIS_PROFILE_HEADER_COUNTING:
            config->entity_state_fields = FASTDIS_ES_FIELD_ALL;
            return FASTDIS_OK;
        case FASTDIS_PROFILE_ENTITY_STATE_ROUTING:
            fastdis_filter_clear(&config->pdu_types);
            fastdis_filter_allow(&config->pdu_types, FASTDIS_ENTITY_STATE_PDU_TYPE);
            fastdis_filter_clear(&config->protocol_families);
            fastdis_filter_allow(&config->protocol_families, FASTDIS_ENTITY_INFORMATION_FAMILY);
            config->entity_state_fields = normalize_entity_state_fields(FASTDIS_ES_FIELD_ROUTING);
            return FASTDIS_OK;
        case FASTDIS_PROFILE_ENTITY_STATE_POSE:
            fastdis_filter_clear(&config->pdu_types);
            fastdis_filter_allow(&config->pdu_types, FASTDIS_ENTITY_STATE_PDU_TYPE);
            fastdis_filter_clear(&config->protocol_families);
            fastdis_filter_allow(&config->protocol_families, FASTDIS_ENTITY_INFORMATION_FAMILY);
            config->entity_state_fields = normalize_entity_state_fields(FASTDIS_ES_FIELD_POSE);
            return FASTDIS_OK;
        case FASTDIS_PROFILE_ENTITY_STATE_FULL:
            fastdis_filter_clear(&config->pdu_types);
            fastdis_filter_allow(&config->pdu_types, FASTDIS_ENTITY_STATE_PDU_TYPE);
            fastdis_filter_clear(&config->protocol_families);
            fastdis_filter_allow(&config->protocol_families, FASTDIS_ENTITY_INFORMATION_FAMILY);
            config->entity_state_fields = normalize_entity_state_fields(FASTDIS_ES_FIELD_ALL);
            return FASTDIS_OK;
        case FASTDIS_PROFILE_ENTITY_TRANSFORM:
            fastdis_filter_clear(&config->pdu_types);
            fastdis_filter_allow(&config->pdu_types, FASTDIS_ENTITY_STATE_PDU_TYPE);
            fastdis_filter_allow(&config->pdu_types, FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE);
            fastdis_filter_clear(&config->protocol_families);
            fastdis_filter_allow(&config->protocol_families, FASTDIS_ENTITY_INFORMATION_FAMILY);
            config->entity_state_fields = normalize_entity_state_fields(transform_field_mask());
            return FASTDIS_OK;
        default:
            return FASTDIS_ERR_BAD_ARGUMENT;
    }
}

static inline fastdis_status_t scan_one_entity_state_to_batch_impl(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_state_batch_t *batch,
    fastdis_scan_stats_t *stats) noexcept {

    if (stats != nullptr) {
        stats->seen += 1;
    }

    if (!config_looks_valid(config) || !entity_state_batch_looks_valid(batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t parsed_header = fastdis_parse_header(data, size, config->flags, &header);
    if (parsed_header != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!is_entity_state_header(&header) || !matches_config(&header, config)) {
        return FASTDIS_OK;
    }

    uint64_t fields = config_entity_state_fields(config);
    if (scanner != nullptr && scanner->entity_id_filter_mode != FASTDIS_ENTITY_ID_FILTER_DISABLED) {
        fields |= FASTDIS_ES_FIELD_ENTITY_ID;
    }
    if (config->entity_force_ids.active != 0) {
        fields |= FASTDIS_ES_FIELD_FORCE_ID;
    }

    fastdis_entity_state_prefix_t entity_state;
    fastdis_status_t parsed = fastdis_parse_entity_state_fields(data, size, config->flags, fields, &entity_state);
    if (parsed != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!matches_filter(&config->entity_force_ids, entity_state.force_id)) {
        return FASTDIS_OK;
    }
    if (!scanner_entity_filter_matches(scanner, entity_state.entity_id)) {
        return FASTDIS_OK;
    }

    const uint64_t accepted_index = stats != nullptr ? stats->accepted : 0;
    if (stats != nullptr) {
        stats->accepted += 1;
    }
    if (!emit_this(accepted_index, config)) {
        return FASTDIS_OK;
    }

    if (stats != nullptr) {
        stats->emitted += 1;
    }
    append_entity_state_to_batch(batch, entity_state);
    return FASTDIS_OK;
}

static inline fastdis_status_t scan_many_entity_state_to_batch_impl(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_state_batch_t *batch,
    fastdis_scan_stats_t *stats) noexcept {

    if (count > 0 && packets == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (!config_looks_valid(config) || !entity_state_batch_looks_valid(batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    reset_entity_state_batch(batch);

    for (size_t i = 0; i < count; ++i) {
        fastdis_status_t rc = scan_one_entity_state_to_batch_impl(
            packets[i].data,
            packets[i].size,
            config,
            scanner,
            batch,
            stats);
        if (rc != FASTDIS_OK) {
            return rc;
        }
    }
    return FASTDIS_OK;
}

static inline fastdis_status_t scan_one_entity_transform_to_batch_impl(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_transform_batch_t *batch,
    fastdis_scan_stats_t *stats) noexcept {

    if (stats != nullptr) {
        stats->seen += 1;
    }

    if (!config_looks_valid(config) || !transform_batch_looks_valid(batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t parsed_header = fastdis_parse_header(data, size, config->flags, &header);
    if (parsed_header != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if (!is_entity_transform_header(&header) || !matches_config(&header, config)) {
        return FASTDIS_OK;
    }

    fastdis_entity_transform_t transform;
    fastdis_status_t parsed = parse_entity_transform_impl(data, size, config->flags, &transform);
    if (parsed != FASTDIS_OK) {
        count_malformed(stats);
        return FASTDIS_OK;
    }

    if ((transform.fields_present & FASTDIS_ES_FIELD_FORCE_ID) != 0ull &&
        !matches_filter(&config->entity_force_ids, transform.force_id)) {
        return FASTDIS_OK;
    }
    if (!scanner_entity_filter_matches(scanner, transform.entity_id)) {
        return FASTDIS_OK;
    }

    const uint64_t accepted_index = stats != nullptr ? stats->accepted : 0;
    if (stats != nullptr) {
        stats->accepted += 1;
    }
    if (!emit_this(accepted_index, config)) {
        return FASTDIS_OK;
    }

    if (stats != nullptr) {
        stats->emitted += 1;
    }
    append_transform_to_batch(batch, transform);
    return FASTDIS_OK;
}

static inline fastdis_status_t scan_many_entity_transform_to_batch_impl(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_transform_batch_t *batch,
    fastdis_scan_stats_t *stats) noexcept {

    if (count > 0 && packets == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (!config_looks_valid(config) || !transform_batch_looks_valid(batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    reset_transform_batch(batch);

    for (size_t i = 0; i < count; ++i) {
        fastdis_status_t rc = scan_one_entity_transform_to_batch_impl(
            packets[i].data,
            packets[i].size,
            config,
            scanner,
            batch,
            stats);
        if (rc != FASTDIS_OK) {
            return rc;
        }
    }
    return FASTDIS_OK;
}


static inline void reset_snapshot_batch(fastdis_entity_snapshot_batch_t *batch) noexcept {
    if (batch != nullptr) {
        batch->count = 0;
        batch->dropped = 0;
    }
}

static inline bool snapshot_batch_looks_valid(const fastdis_entity_snapshot_batch_t *batch) noexcept {
    return batch != nullptr && (batch->capacity == 0 || batch->snapshots != nullptr);
}

static inline bool transform_equal(const fastdis_entity_transform_t &a, const fastdis_entity_transform_t &b) noexcept {
    return std::memcmp(&a, &b, sizeof(a)) == 0;
}

static inline fastdis_entity_snapshot_t snapshot_from_entry(
    const fastdis_entity_table_entry_s &entry,
    uint32_t extra_flags = FASTDIS_ENTITY_CHANGE_NONE) noexcept {
    fastdis_entity_snapshot_t out;
    std::memset(&out, 0, sizeof(out));
    out.transform = entry.transform;
    out.first_seen_tick = entry.first_seen_tick;
    out.last_seen_tick = entry.last_seen_tick;
    out.update_count = entry.update_count;
    uint32_t flags = entry.change_flags | extra_flags;
    if (flags == FASTDIS_ENTITY_CHANGE_NONE) {
        flags = FASTDIS_ENTITY_CHANGE_UNCHANGED;
    }
    out.change_flags = flags;
    return out;
}

static inline void append_snapshot_to_batch(
    fastdis_entity_snapshot_batch_t *batch,
    const fastdis_entity_snapshot_t &snapshot) noexcept {
    if (batch == nullptr) {
        return;
    }
    if (batch->count < batch->capacity) {
        batch->snapshots[batch->count++] = snapshot;
    } else {
        batch->dropped += 1;
    }
}

static inline fastdis_entity_transform_t extrapolate_transform_linear_value(
    const fastdis_entity_transform_t &transform,
    double delta_seconds) noexcept {
    fastdis_entity_transform_t out = transform;
    out.location.x += static_cast<double>(out.linear_velocity.x) * delta_seconds;
    out.location.y += static_cast<double>(out.linear_velocity.y) * delta_seconds;
    out.location.z += static_cast<double>(out.linear_velocity.z) * delta_seconds;
    return out;
}

struct fastdis_vec3d_s {
    double x;
    double y;
    double z;
};

static inline fastdis_vec3d_s vec3d_from_vec3f(const fastdis_vec3f_t &v) noexcept {
    return fastdis_vec3d_s{static_cast<double>(v.x), static_cast<double>(v.y), static_cast<double>(v.z)};
}

static inline fastdis_vec3d_s add_vec3d(const fastdis_vec3d_s &a, const fastdis_vec3d_s &b) noexcept {
    return fastdis_vec3d_s{a.x + b.x, a.y + b.y, a.z + b.z};
}

static inline fastdis_vec3d_s scale_vec3d(const fastdis_vec3d_s &v, double scale) noexcept {
    return fastdis_vec3d_s{v.x * scale, v.y * scale, v.z * scale};
}

static inline fastdis_vec3d_s body_vector_to_world_ecef(
    const fastdis_euler_angles_t &orientation,
    const fastdis_vec3f_t &body_vector) noexcept {
    const double psi = static_cast<double>(orientation.psi);
    const double theta = static_cast<double>(orientation.theta);
    const double phi = static_cast<double>(orientation.phi);
    const double cz = std::cos(psi);
    const double sz = std::sin(psi);
    const double cy = std::cos(theta);
    const double sy = std::sin(theta);
    const double cx = std::cos(phi);
    const double sx = std::sin(phi);
    const fastdis_vec3d_s v = vec3d_from_vec3f(body_vector);

    /* DIS body-to-ECEF convention used by the engine orientation helpers:
     * R = Rz(psi) * Ry(theta) * Rx(phi), with body vector columns expressed in
     * ECEF/world coordinates.
     */
    return fastdis_vec3d_s{
        ((cz * cy) * v.x) + ((cz * sy * sx - sz * cx) * v.y) + ((cz * sy * cx + sz * sx) * v.z),
        ((sz * cy) * v.x) + ((sz * sy * sx + cz * cx) * v.y) + ((sz * sy * cx - cz * sx) * v.z),
        ((-sy) * v.x) + ((cy * sx) * v.y) + ((cy * cx) * v.z),
    };
}

static inline bool dead_reckoning_algorithm_has_rotation(uint8_t algorithm) noexcept {
    return algorithm == FASTDIS_DR_RPW ||
           algorithm == FASTDIS_DR_RVW ||
           algorithm == FASTDIS_DR_RPB ||
           algorithm == FASTDIS_DR_RVB;
}

static inline bool dead_reckoning_algorithm_has_world_velocity(uint8_t algorithm) noexcept {
    return algorithm == FASTDIS_DR_RVW || algorithm == FASTDIS_DR_FVW;
}

static inline bool dead_reckoning_algorithm_has_body_velocity(uint8_t algorithm) noexcept {
    return algorithm == FASTDIS_DR_RVB || algorithm == FASTDIS_DR_FVB;
}

static inline bool dead_reckoning_algorithm_uses_acceleration(uint8_t algorithm) noexcept {
    return algorithm == FASTDIS_DR_RVW || algorithm == FASTDIS_DR_RVB;
}

static inline fastdis_entity_transform_t extrapolate_transform_dead_reckoning_value(
    const fastdis_entity_transform_t &transform,
    double delta_seconds) noexcept {
    fastdis_entity_transform_t out = transform;
    const uint8_t algorithm = transform.dead_reckoning_algorithm;
    fastdis_vec3d_s velocity{0.0, 0.0, 0.0};
    fastdis_vec3d_s acceleration{0.0, 0.0, 0.0};

    if (dead_reckoning_algorithm_has_world_velocity(algorithm)) {
        velocity = vec3d_from_vec3f(transform.linear_velocity);
        if (dead_reckoning_algorithm_uses_acceleration(algorithm)) {
            acceleration = vec3d_from_vec3f(transform.dead_reckoning_linear_acceleration);
        }
    } else if (dead_reckoning_algorithm_has_body_velocity(algorithm)) {
        velocity = body_vector_to_world_ecef(transform.orientation, transform.linear_velocity);
        if (dead_reckoning_algorithm_uses_acceleration(algorithm)) {
            acceleration = body_vector_to_world_ecef(transform.orientation, transform.dead_reckoning_linear_acceleration);
        }
    }

    const fastdis_vec3d_s offset = add_vec3d(
        scale_vec3d(velocity, delta_seconds),
        scale_vec3d(acceleration, 0.5 * delta_seconds * delta_seconds)
    );
    out.location.x += offset.x;
    out.location.y += offset.y;
    out.location.z += offset.z;

    if (dead_reckoning_algorithm_has_rotation(algorithm)) {
        out.orientation.psi += static_cast<float>(static_cast<double>(transform.dead_reckoning_angular_velocity.x) * delta_seconds);
        out.orientation.theta += static_cast<float>(static_cast<double>(transform.dead_reckoning_angular_velocity.y) * delta_seconds);
        out.orientation.phi += static_cast<float>(static_cast<double>(transform.dead_reckoning_angular_velocity.z) * delta_seconds);
    }
    return out;
}

static inline fastdis_entity_snapshot_t extrapolate_snapshot_linear_value(
    const fastdis_entity_snapshot_t &snapshot,
    uint64_t target_tick,
    double seconds_per_tick) noexcept {
    fastdis_entity_snapshot_t out = snapshot;
    const uint64_t age_ticks = target_tick >= snapshot.last_seen_tick ? target_tick - snapshot.last_seen_tick : 0u;
    out.transform = extrapolate_transform_linear_value(snapshot.transform, static_cast<double>(age_ticks) * seconds_per_tick);
    out.change_flags |= FASTDIS_ENTITY_CHANGE_EXTRAPOLATED;
    return out;
}

static inline fastdis_entity_snapshot_t extrapolate_snapshot_dead_reckoning_value(
    const fastdis_entity_snapshot_t &snapshot,
    uint64_t target_tick,
    double seconds_per_tick) noexcept {
    fastdis_entity_snapshot_t out = snapshot;
    const uint64_t age_ticks = target_tick >= snapshot.last_seen_tick ? target_tick - snapshot.last_seen_tick : 0u;
    out.transform = extrapolate_transform_dead_reckoning_value(snapshot.transform, static_cast<double>(age_ticks) * seconds_per_tick);
    out.change_flags |= FASTDIS_ENTITY_CHANGE_EXTRAPOLATED;
    return out;
}

static inline bool entity_is_stale(
    const fastdis_entity_table_t *table,
    const fastdis_entity_table_entry_s &entry,
    uint64_t stale_after_ticks) noexcept {
    if (table == nullptr) {
        return false;
    }
    if (stale_after_ticks == 0u) {
        return true;
    }
    const uint64_t age = table->tick >= entry.last_seen_tick ? table->tick - entry.last_seen_tick : 0u;
    return age >= stale_after_ticks;
}

static inline void fill_table_update_stats_totals(
    const fastdis_entity_table_t *table,
    fastdis_entity_table_update_stats_t *stats) noexcept {
    if (stats == nullptr) {
        return;
    }
    stats->tick = table != nullptr ? table->tick : 0u;
    stats->entity_count = table != nullptr ? static_cast<uint64_t>(table->entries.size()) : 0u;
}

static inline fastdis_status_t entity_table_apply_transform(
    fastdis_entity_table_t *table,
    const fastdis_entity_transform_t &transform,
    fastdis_entity_snapshot_t *out_snapshot,
    fastdis_entity_table_update_stats_t *stats) noexcept {

    if (table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    const uint64_t key = entity_key(transform.entity_id);
    try {
        auto it = table->entries.find(key);
        if (it == table->entries.end()) {
            fastdis_entity_table_entry_s entry;
            entry.transform = transform;
            entry.first_seen_tick = table->tick;
            entry.last_seen_tick = table->tick;
            entry.update_count = 1;
            entry.change_flags = FASTDIS_ENTITY_CHANGE_NEW | FASTDIS_ENTITY_CHANGE_UPDATED;
            auto result = table->entries.emplace(key, entry);
            if (!result.second) {
                return FASTDIS_ERR_OUT_OF_MEMORY;
            }
            table->total_updates += 1;
            table->total_new += 1;
            table->total_changed += 1;
            if (stats != nullptr) {
                stats->table_updates += 1;
                stats->new_entities += 1;
                stats->changed_entities += 1;
            }
            if (out_snapshot != nullptr) {
                *out_snapshot = snapshot_from_entry(result.first->second);
            }
        } else {
            fastdis_entity_table_entry_s &entry = it->second;
            const fastdis_entity_transform_t merged = merge_transform_patch(entry.transform, transform);
            const bool changed = !transform_equal(entry.transform, merged);
            entry.last_seen_tick = table->tick;
            entry.update_count += 1;
            table->total_updates += 1;
            if (stats != nullptr) {
                stats->table_updates += 1;
            }
            if (changed) {
                entry.transform = merged;
                entry.change_flags |= FASTDIS_ENTITY_CHANGE_UPDATED;
                table->total_changed += 1;
                if (stats != nullptr) {
                    stats->changed_entities += 1;
                }
            } else {
                table->total_unchanged += 1;
                if (stats != nullptr) {
                    stats->unchanged_entities += 1;
                }
            }
            if (out_snapshot != nullptr) {
                *out_snapshot = snapshot_from_entry(entry, changed ? FASTDIS_ENTITY_CHANGE_NONE : FASTDIS_ENTITY_CHANGE_UNCHANGED);
            }
        }
    } catch (...) {
        return FASTDIS_ERR_OUT_OF_MEMORY;
    }

    fill_table_update_stats_totals(table, stats);
    return FASTDIS_OK;
}

static inline fastdis_status_t scan_one_entity_transform_to_table_impl(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    fastdis_entity_table_t *table,
    fastdis_entity_table_update_stats_t *stats) noexcept {

    fastdis_scan_stats_t *scan_stats = stats != nullptr ? &stats->scan : nullptr;
    if (scan_stats != nullptr) {
        scan_stats->seen += 1;
    }

    if (!config_looks_valid(config) || table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t parsed_header = fastdis_parse_header(data, size, config->flags, &header);
    if (parsed_header != FASTDIS_OK) {
        count_malformed(scan_stats);
        return FASTDIS_OK;
    }

    if (!is_entity_transform_header(&header) || !matches_config(&header, config)) {
        return FASTDIS_OK;
    }

    fastdis_entity_transform_t transform;
    fastdis_status_t parsed = parse_entity_transform_impl(data, size, config->flags, &transform);
    if (parsed != FASTDIS_OK) {
        count_malformed(scan_stats);
        return FASTDIS_OK;
    }

    if ((transform.fields_present & FASTDIS_ES_FIELD_FORCE_ID) != 0ull &&
        !matches_filter(&config->entity_force_ids, transform.force_id)) {
        return FASTDIS_OK;
    }
    if (!scanner_entity_filter_matches(scanner, transform.entity_id)) {
        return FASTDIS_OK;
    }

    const uint64_t accepted_index = scan_stats != nullptr ? scan_stats->accepted : 0;
    if (scan_stats != nullptr) {
        scan_stats->accepted += 1;
    }
    if (!emit_this(accepted_index, config)) {
        return FASTDIS_OK;
    }

    if (scan_stats != nullptr) {
        scan_stats->emitted += 1;
    }

    return entity_table_apply_transform(table, transform, nullptr, stats);
}

static inline fastdis_status_t scan_many_entity_transform_to_table_impl(
    fastdis_entity_table_t *table,
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    const fastdis_scanner_t *scanner,
    uint32_t advance_tick,
    fastdis_entity_table_update_stats_t *stats) noexcept {

    if (table == nullptr || (count > 0 && packets == nullptr) || !config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (stats != nullptr) {
        std::memset(stats, 0, sizeof(*stats));
    }
    if (advance_tick != 0u) {
        table->tick += 1;
    }

    for (size_t i = 0; i < count; ++i) {
        fastdis_status_t rc = scan_one_entity_transform_to_table_impl(
            packets[i].data,
            packets[i].size,
            config,
            scanner,
            table,
            stats);
        if (rc != FASTDIS_OK) {
            fill_table_update_stats_totals(table, stats);
            return rc;
        }
    }
    fill_table_update_stats_totals(table, stats);
    return FASTDIS_OK;
}

} // namespace

extern "C" {

FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_version(void) {
    return FASTDIS_ABI_VERSION;
}

FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_epoch(void) {
    return FASTDIS_ABI_EPOCH;
}

FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_revision(void) {
    return FASTDIS_ABI_REVISION;
}

FASTDIS_API const char *FASTDIS_CALL fastdis_version_string(void) {
    return "0.13.0-alpha3";
}

FASTDIS_API const char *FASTDIS_CALL fastdis_status_string(fastdis_status_t status) {
    switch (status) {
        case FASTDIS_OK:
            return "ok";
        case FASTDIS_ERR_BAD_ARGUMENT:
            return "bad argument";
        case FASTDIS_ERR_SHORT_PACKET:
            return "packet shorter than required structure";
        case FASTDIS_ERR_LENGTH_TOO_SMALL:
            return "PDU length smaller than required structure";
        case FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER:
            return "PDU length exceeds supplied buffer";
        case FASTDIS_ERR_CALLBACK_STOPPED:
            return "callback stopped scan";
        case FASTDIS_ERR_UNSUPPORTED_PDU:
            return "unsupported PDU for requested parser";
        case FASTDIS_ERR_OUT_OF_MEMORY:
            return "out of memory";
        case FASTDIS_ERR_NOT_FOUND:
            return "not found";
        case FASTDIS_ERR_BUSY:
            return "snapshot buffer slot is busy";
        default:
            return "unknown fastdis status";
    }
}

FASTDIS_API void FASTDIS_CALL fastdis_filter_accept_all(fastdis_u8_filter_t *filter) {
    if (filter == nullptr) {
        return;
    }
    std::memset(filter, 0, sizeof(*filter));
    filter->active = 0;
}

FASTDIS_API void FASTDIS_CALL fastdis_filter_clear(fastdis_u8_filter_t *filter) {
    if (filter == nullptr) {
        return;
    }
    std::memset(filter, 0, sizeof(*filter));
    filter->active = 1;
}

FASTDIS_API void FASTDIS_CALL fastdis_filter_allow(fastdis_u8_filter_t *filter, uint8_t value) {
    if (filter == nullptr) {
        return;
    }
    filter->active = 1;
    const uint32_t word = static_cast<uint32_t>(value >> 6);
    const uint32_t bit = static_cast<uint32_t>(value & 63u);
    filter->bits[word] |= (1ull << bit);
}

FASTDIS_API int FASTDIS_CALL fastdis_filter_contains(const fastdis_u8_filter_t *filter, uint8_t value) {
    return matches_filter(filter, value) ? 1 : 0;
}

FASTDIS_API void FASTDIS_CALL fastdis_scan_config_init(fastdis_scan_config_t *config) {
    if (config == nullptr) {
        return;
    }
    std::memset(config, 0, sizeof(*config));
    config->struct_size = static_cast<uint32_t>(sizeof(*config));
    config->flags = 0;
    config->sample_every = 1;
    config->sample_offset = 0;
    fastdis_filter_accept_all(&config->versions);
    fastdis_filter_accept_all(&config->pdu_types);
    fastdis_filter_accept_all(&config->protocol_families);
    fastdis_filter_accept_all(&config->exercise_ids);
    fastdis_filter_accept_all(&config->entity_force_ids);
    config->entity_state_fields = FASTDIS_ES_FIELD_ALL;
}

FASTDIS_API void FASTDIS_CALL fastdis_scan_stats_init(fastdis_scan_stats_t *stats) {
    if (stats != nullptr) {
        std::memset(stats, 0, sizeof(*stats));
    }
}

FASTDIS_API void FASTDIS_CALL fastdis_entity_table_update_stats_init(fastdis_entity_table_update_stats_t *stats) {
    if (stats != nullptr) {
        std::memset(stats, 0, sizeof(*stats));
    }
}

FASTDIS_API void FASTDIS_CALL fastdis_entity_snapshot_buffer_stats_init(fastdis_entity_snapshot_buffer_stats_t *stats) {
    if (stats != nullptr) {
        std::memset(stats, 0, sizeof(*stats));
    }
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_accept_all(
    fastdis_scan_config_t *config,
    uint32_t filter_kind) {
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_u8_filter_t *filter = config_filter_ptr(config, filter_kind);
    if (filter == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_filter_accept_all(filter);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_clear(
    fastdis_scan_config_t *config,
    uint32_t filter_kind) {
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_u8_filter_t *filter = config_filter_ptr(config, filter_kind);
    if (filter == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_filter_clear(filter);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_allow(
    fastdis_scan_config_t *config,
    uint32_t filter_kind,
    uint8_t value) {
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_u8_filter_t *filter = config_filter_ptr(config, filter_kind);
    if (filter == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_filter_allow(filter, value);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_only(
    fastdis_scan_config_t *config,
    uint32_t filter_kind,
    const uint8_t *values,
    size_t count) {
    if (!config_looks_valid(config) || (count > 0 && values == nullptr)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_u8_filter_t *filter = config_filter_ptr(config, filter_kind);
    if (filter == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (count == 0) {
        fastdis_filter_accept_all(filter);
        return FASTDIS_OK;
    }
    fastdis_filter_clear(filter);
    for (size_t i = 0; i < count; ++i) {
        fastdis_filter_allow(filter, values[i]);
    }
    return FASTDIS_OK;
}

FASTDIS_API int FASTDIS_CALL fastdis_scan_config_filter_contains(
    const fastdis_scan_config_t *config,
    uint32_t filter_kind,
    uint8_t value) {
    if (!config_looks_valid(config)) {
        return 0;
    }
    const fastdis_u8_filter_t *filter = config_filter_ptr_const(config, filter_kind);
    if (filter == nullptr) {
        return 0;
    }
    return matches_filter(filter, value) ? 1 : 0;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_set_sample(
    fastdis_scan_config_t *config,
    uint32_t sample_every,
    uint32_t sample_offset) {
    if (!config_looks_valid(config) || sample_every == 0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    config->sample_every = sample_every;
    config->sample_offset = sample_offset;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_set_entity_state_fields(
    fastdis_scan_config_t *config,
    uint64_t field_mask) {
    if (!config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    config->entity_state_fields = normalize_entity_state_fields(field_mask);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_use_profile(
    fastdis_scan_config_t *config,
    uint32_t profile_kind) {
    return apply_profile_to_config(config, profile_kind);
}


FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_header(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_header_t *out_header) {

    if (data == nullptr || out_header == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (size < FASTDIS_HEADER_SIZE) {
        return FASTDIS_ERR_SHORT_PACKET;
    }

    fastdis_header_t h;
    std::memset(&h, 0, sizeof(h));
    h.version = data[0];
    h.exercise_id = data[1];
    h.pdu_type = data[2];
    h.protocol_family = data[3];
    h.timestamp = be32(data + 4);
    h.length = be16(data + 8);

    if (h.length < FASTDIS_HEADER_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }
    if ((flags & FASTDIS_FLAG_ALLOW_TRUNCATED) == 0u && static_cast<size_t>(h.length) > size) {
        return FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER;
    }

    if (h.version >= FASTDIS_PROTOCOL_VERSION_DIS7) {
        h.status = static_cast<int16_t>(data[10]);
        h.padding = static_cast<uint16_t>(data[11]);
    } else {
        h.status = static_cast<int16_t>(FASTDIS_HEADER_STATUS_UNAVAILABLE);
        h.padding = be16(data + 10);
    }

    *out_header = h;
    return FASTDIS_OK;
}

FASTDIS_API int FASTDIS_CALL fastdis_header_matches(
    const fastdis_header_t *header,
    const fastdis_scan_config_t *config) {
    if (header == nullptr) {
        return 0;
    }
    if (config == nullptr) {
        return 1;
    }
    if (!config_looks_valid(config)) {
        return 0;
    }
    return matches_config(header, config) ? 1 : 0;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_packet(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    fastdis_packet_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    return scan_one_impl(data, size, config, callback, nullptr, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_packets(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    fastdis_packet_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    return scan_many_impl(packets, count, config, callback, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_state_prefix(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_state_prefix_t *out_entity_state) {
    return fastdis_parse_entity_state_fields(data, size, flags, FASTDIS_ES_FIELD_ALL, out_entity_state);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_state_fields(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    uint64_t field_mask,
    fastdis_entity_state_prefix_t *out_entity_state) {

    if (data == nullptr || out_entity_state == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }

    fastdis_header_t header;
    fastdis_status_t rc = fastdis_parse_header(data, size, flags, &header);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    if (!is_entity_state_header(&header)) {
        return FASTDIS_ERR_UNSUPPORTED_PDU;
    }
    if (header.length < FASTDIS_ENTITY_STATE_FIXED_SIZE) {
        return FASTDIS_ERR_LENGTH_TOO_SMALL;
    }

    const uint64_t fields = normalize_entity_state_fields(field_mask);
    rc = validate_entity_state_field_bytes(size, fields);
    if (rc != FASTDIS_OK) {
        return rc;
    }

    fastdis_entity_state_prefix_t out;
    std::memset(&out, 0, sizeof(out));
    out.header = header;
    out.fields_present = FASTDIS_ES_FIELD_HEADER | FASTDIS_ES_FIELD_FORCE_ID;

    const uint8_t *p = data + FASTDIS_HEADER_SIZE;

    out.force_id = p[6];

    if ((fields & FASTDIS_ES_FIELD_ENTITY_ID) != 0ull) {
        out.entity_id = read_entity_id(p + 0);
        out.fields_present |= FASTDIS_ES_FIELD_ENTITY_ID;
    }
    if ((fields & FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT) != 0ull) {
        out.variable_parameter_count = p[7];
        out.fields_present |= FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT;
    }
    if ((fields & FASTDIS_ES_FIELD_ENTITY_TYPE) != 0ull) {
        out.entity_type = read_entity_type(p + 8);
        out.fields_present |= FASTDIS_ES_FIELD_ENTITY_TYPE;
    }
    if ((fields & FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE) != 0ull) {
        out.alternate_entity_type = read_entity_type(p + 16);
        out.fields_present |= FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE;
    }
    if ((fields & FASTDIS_ES_FIELD_LINEAR_VELOCITY) != 0ull) {
        out.linear_velocity = read_vec3f(p + 24);
        out.fields_present |= FASTDIS_ES_FIELD_LINEAR_VELOCITY;
    }
    if ((fields & FASTDIS_ES_FIELD_LOCATION) != 0ull) {
        out.location = read_world_coordinates(p + 36);
        out.fields_present |= FASTDIS_ES_FIELD_LOCATION;
    }
    if ((fields & FASTDIS_ES_FIELD_ORIENTATION) != 0ull) {
        out.orientation = read_euler_angles(p + 60);
        out.fields_present |= FASTDIS_ES_FIELD_ORIENTATION;
    }
    if ((fields & FASTDIS_ES_FIELD_APPEARANCE) != 0ull) {
        out.appearance = be32(p + 72);
        out.fields_present |= FASTDIS_ES_FIELD_APPEARANCE;
    }
    if ((fields & FASTDIS_ES_FIELD_DEAD_RECKONING) != 0ull) {
        out.dead_reckoning_algorithm = p[76];
        std::memcpy(out.dead_reckoning_parameters, p + 77, 15);
        out.dead_reckoning_linear_acceleration = read_vec3f(p + 92);
        out.dead_reckoning_angular_velocity = read_vec3f(p + 104);
        out.fields_present |= FASTDIS_ES_FIELD_DEAD_RECKONING;
    }
    if ((fields & FASTDIS_ES_FIELD_MARKING) != 0ull) {
        out.marking_character_set = p[116];
        std::memcpy(out.marking, p + 117, 11);
        out.marking[11] = 0;
        out.fields_present |= FASTDIS_ES_FIELD_MARKING;
    }
    if ((fields & FASTDIS_ES_FIELD_CAPABILITIES) != 0ull) {
        out.capabilities = be32(p + 128);
        out.fields_present |= FASTDIS_ES_FIELD_CAPABILITIES;
    }

    *out_entity_state = out;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_transform(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_transform_t *out_transform) {

    return parse_entity_transform_impl(data, size, flags, out_transform);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_fire(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_fire_t *out_fire) {

    return parse_fire_impl(data, size, flags, out_fire);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_detonation(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_detonation_t *out_detonation) {

    return parse_detonation_impl(data, size, flags, out_detonation);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_collision(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_collision_t *out_collision) {

    return parse_collision_impl(data, size, flags, out_collision);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_collision_elastic(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_collision_elastic_t *out_collision) {

    return parse_collision_elastic_impl(data, size, flags, out_collision);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_directed_energy_fire(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_directed_energy_fire_t *out_fire) {

    return parse_directed_energy_fire_impl(data, size, flags, out_fire);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_damage_status(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_entity_damage_status_t *out_status) {

    return parse_entity_damage_status_impl(data, size, flags, out_status);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_designator(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_designator_t *out_designator) {

    return parse_designator_impl(data, size, flags, out_designator);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transmitter(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_transmitter_t *out_transmitter) {

    return parse_transmitter_impl(data, size, flags, out_transmitter);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_other_pdu(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_other_pdu_t *out_other) {

    return parse_other_pdu_impl(data, size, flags, out_other);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_aggregate_state(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_aggregate_state_t *out_aggregate) {

    return parse_aggregate_state_impl(data, size, flags, out_aggregate);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_is_group_of(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_is_group_of_t *out_group) {

    return parse_is_group_of_impl(data, size, flags, out_group);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transfer_control_request(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_transfer_control_request_t *out_request) {

    return parse_transfer_request_impl(data, size, flags, FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transfer_ownership(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_transfer_ownership_t *out_request) {

    return parse_transfer_request_impl(data, size, flags, FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_is_part_of(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_is_part_of_t *out_part) {

    return parse_is_part_of_impl(data, size, flags, out_part);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_state(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_state_t *out_state) {

    return parse_minefield_state_impl(data, size, flags, out_state);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_query(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_query_t *out_query) {

    return parse_minefield_query_impl(data, size, flags, out_query);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_data(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_data_t *out_data) {

    return parse_minefield_data_impl(data, size, flags, out_data);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_response_nack(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_response_nack_t *out_nack) {

    return parse_minefield_response_nack_impl(data, size, flags, out_nack);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_environmental_process(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_environmental_process_t *out_process) {

    return parse_environmental_process_impl(data, size, flags, out_process);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_gridded_data(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_gridded_data_t *out_grid) {

    return parse_gridded_data_impl(data, size, flags, out_grid);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_point_object_state(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_point_object_state_t *out_point) {

    return parse_point_object_state_impl(data, size, flags, out_point);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_linear_object_state(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_linear_object_state_t *out_linear) {

    return parse_linear_object_state_impl(data, size, flags, out_linear);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_areal_object_state(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_areal_object_state_t *out_areal) {

    return parse_areal_object_state_impl(data, size, flags, out_areal);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_tspi(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_tspi_t *out_tspi) {

    return parse_tspi_impl(data, size, flags, out_tspi);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_live_entity_appearance(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_live_entity_appearance_t *out_appearance) {

    return parse_live_entity_appearance_impl(data, size, flags, out_appearance);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_articulated_parts(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_articulated_parts_t *out_parts) {

    return parse_articulated_parts_impl(data, size, flags, out_parts);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_le_fire(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_le_fire_t *out_fire) {

    return parse_le_fire_impl(data, size, flags, out_fire);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_le_detonation(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_le_detonation_t *out_detonation) {

    return parse_le_detonation_impl(data, size, flags, out_detonation);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_signal(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_signal_t *out_signal) {

    return parse_signal_impl(data, size, flags, out_signal);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_receiver(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_receiver_t *out_receiver) {

    return parse_receiver_impl(data, size, flags, out_receiver);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_electronic_emissions(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_electronic_emissions_t *out_emissions) {

    return parse_electronic_emissions_impl(data, size, flags, out_emissions);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_iff_atc_navaids_layer1(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_iff_atc_navaids_layer1_t *out_iff) {

    return parse_iff_atc_navaids_layer1_impl(data, size, flags, out_iff);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_iff(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_iff_t *out_iff) {

    return parse_iff_impl(data, size, flags, out_iff);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_ua(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_ua_t *out_ua) {

    return parse_ua_impl(data, size, flags, out_ua);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_sees(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_sees_t *out_sees) {

    return parse_sees_impl(data, size, flags, out_sees);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_intercom_signal(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_signal_t *out_signal) {

    return parse_intercom_signal_impl(data, size, flags, out_signal);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_intercom_control(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_control_t *out_control) {

    return parse_intercom_control_impl(data, size, flags, out_control);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_attribute(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_attribute_t *out_attribute) {

    return parse_attribute_impl(data, size, flags, out_attribute);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_information_operations_action(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_action_t *out_action) {

    return parse_information_operations_action_impl(data, size, flags, out_action);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_information_operations_report(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_report_t *out_report) {

    return parse_information_operations_report_impl(data, size, flags, out_report);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_create_entity(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_request_t *out_request) {

    return parse_simulation_management_request_impl(
        data,
        size,
        flags,
        FASTDIS_CREATE_ENTITY_PDU_TYPE,
        FASTDIS_CREATE_ENTITY_FIXED_SIZE,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_remove_entity(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_request_t *out_request) {

    return parse_simulation_management_request_impl(
        data,
        size,
        flags,
        FASTDIS_REMOVE_ENTITY_PDU_TYPE,
        FASTDIS_REMOVE_ENTITY_FIXED_SIZE,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_start_resume(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_t *out_request) {

    return parse_start_resume_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_stop_freeze(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_t *out_request) {

    return parse_stop_freeze_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_acknowledge(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_acknowledge_t *out_request) {

    return parse_acknowledge_impl(
        data,
        size,
        flags,
        FASTDIS_ACKNOWLEDGE_PDU_TYPE,
        FASTDIS_ACKNOWLEDGE_FIXED_SIZE,
        5u,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_request(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_t *out_request) {
    return parse_action_request_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_response(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_t *out_request) {
    return parse_action_response_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_query(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_t *out_request) {
    return parse_data_query_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_data(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_t *out_request) {
    return parse_set_data_impl(data, size, flags, FASTDIS_SET_DATA_PDU_TYPE, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_t *out_request) {
    return parse_set_data_impl(data, size, flags, FASTDIS_DATA_PDU_TYPE, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_event_report(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_t *out_request) {
    return parse_event_report_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_comment(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_comment_t *out_request) {
    return parse_comment_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_create_entity_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_reliable_request_t *out_request) {

    return parse_simulation_management_reliable_request_impl(
        data,
        size,
        flags,
        FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE,
        FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_remove_entity_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_reliable_request_t *out_request) {

    return parse_simulation_management_reliable_request_impl(
        data,
        size,
        flags,
        FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE,
        FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_start_resume_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_reliable_t *out_request) {

    return parse_start_resume_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_stop_freeze_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_reliable_t *out_request) {

    return parse_stop_freeze_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_acknowledge_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_acknowledge_t *out_request) {

    return parse_acknowledge_impl(
        data,
        size,
        flags,
        FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE,
        FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE,
        10u,
        out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_request_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_reliable_t *out_request) {
    return parse_action_request_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_response_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_reliable_t *out_request) {
    return parse_action_response_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_query_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_reliable_t *out_request) {
    return parse_data_query_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_data_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_reliable_t *out_request) {
    return parse_set_data_reliable_impl(data, size, flags, FASTDIS_SET_DATA_RELIABLE_PDU_TYPE, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_data_reliable_t *out_request) {
    return parse_data_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_event_report_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_reliable_t *out_request) {
    return parse_event_report_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_comment_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_comment_reliable_t *out_request) {
    return parse_comment_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_service_request(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_service_request_t *out_request) {
    return parse_service_request_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_offer(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_offer_t *out_request) {
    return parse_resupply_offer_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_received(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_received_t *out_request) {
    return parse_resupply_received_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_cancel(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_cancel_t *out_request) {
    return parse_resupply_cancel_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_repair_complete(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_repair_complete_t *out_request) {
    return parse_repair_complete_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_repair_response(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_repair_response_t *out_request) {
    return parse_repair_response_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_record_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_record_reliable_t *out_request) {
    return parse_record_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_record_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_set_record_reliable_t *out_request) {
    return parse_set_record_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_record_query_reliable(
    const uint8_t *data,
    size_t size,
    uint32_t flags,
    fastdis_record_query_reliable_t *out_request) {
    return parse_record_query_reliable_impl(data, size, flags, out_request);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_packet(
    const uint8_t *data,
    size_t size,
    const fastdis_scan_config_t *config,
    fastdis_entity_state_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    return scan_one_entity_state_impl(data, size, config, nullptr, callback, nullptr, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_packets(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    fastdis_entity_state_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    return scan_many_entity_state_impl(packets, count, config, nullptr, callback, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_to_batch(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    fastdis_entity_state_batch_t *out_batch,
    fastdis_scan_stats_t *stats) {
    return scan_many_entity_state_to_batch_impl(packets, count, config, nullptr, out_batch, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_transforms_to_batch(
    const fastdis_packet_view_t *packets,
    size_t count,
    const fastdis_scan_config_t *config,
    fastdis_entity_transform_batch_t *out_batch,
    fastdis_scan_stats_t *stats) {
    return scan_many_entity_transform_to_batch_impl(packets, count, config, nullptr, out_batch, stats);
}

FASTDIS_API fastdis_scanner_t *FASTDIS_CALL fastdis_scanner_create(const fastdis_scan_config_t *config) {
    fastdis_scanner_t *scanner = new (std::nothrow) fastdis_scanner_t();
    if (scanner == nullptr) {
        return nullptr;
    }
    if (config != nullptr) {
        if (!config_looks_valid(config)) {
            delete scanner;
            return nullptr;
        }
        copy_config(&scanner->config, config);
    }
    return scanner;
}

FASTDIS_API void FASTDIS_CALL fastdis_scanner_destroy(fastdis_scanner_t *scanner) {
    delete scanner;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_config(
    fastdis_scanner_t *scanner,
    const fastdis_scan_config_t *config) {
    if (scanner == nullptr || !config_looks_valid(config)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    copy_config(&scanner->config, config);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_get_config(
    const fastdis_scanner_t *scanner,
    fastdis_scan_config_t *out_config) {
    if (scanner == nullptr || out_config == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    *out_config = scanner->config;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_id_filter_mode(
    fastdis_scanner_t *scanner,
    uint32_t mode) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (mode != FASTDIS_ENTITY_ID_FILTER_DISABLED &&
        mode != FASTDIS_ENTITY_ID_FILTER_ALLOW &&
        mode != FASTDIS_ENTITY_ID_FILTER_BLOCK) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->entity_id_filter_mode = mode;
    return FASTDIS_OK;
}

FASTDIS_API uint32_t FASTDIS_CALL fastdis_scanner_get_entity_id_filter_mode(const fastdis_scanner_t *scanner) {
    if (scanner == nullptr) {
        return FASTDIS_ENTITY_ID_FILTER_DISABLED;
    }
    return scanner->entity_id_filter_mode;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_clear_entity_ids(fastdis_scanner_t *scanner) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->entity_ids.clear();
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_add_entity_id(
    fastdis_scanner_t *scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    try {
        scanner->entity_ids.insert(entity_key(site, application, entity));
    } catch (...) {
        return FASTDIS_ERR_OUT_OF_MEMORY;
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_remove_entity_id(
    fastdis_scanner_t *scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->entity_ids.erase(entity_key(site, application, entity));
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_add_entity_ids(
    fastdis_scanner_t *scanner,
    const fastdis_entity_id_t *ids,
    size_t count) {
    if (scanner == nullptr || (count > 0 && ids == nullptr)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    try {
        for (size_t i = 0; i < count; ++i) {
            scanner->entity_ids.insert(entity_key(ids[i]));
        }
    } catch (...) {
        return FASTDIS_ERR_OUT_OF_MEMORY;
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_ids(
    fastdis_scanner_t *scanner,
    uint32_t mode,
    const fastdis_entity_id_t *ids,
    size_t count) {
    if (scanner == nullptr || (count > 0 && ids == nullptr)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (mode != FASTDIS_ENTITY_ID_FILTER_DISABLED &&
        mode != FASTDIS_ENTITY_ID_FILTER_ALLOW &&
        mode != FASTDIS_ENTITY_ID_FILTER_BLOCK) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->entity_ids.clear();
    if (count > 0) {
        try {
            scanner->entity_ids.reserve(count);
            for (size_t i = 0; i < count; ++i) {
                scanner->entity_ids.insert(entity_key(ids[i]));
            }
        } catch (...) {
            scanner->entity_ids.clear();
            return FASTDIS_ERR_OUT_OF_MEMORY;
        }
    }
    scanner->entity_id_filter_mode = mode;
    return FASTDIS_OK;
}

FASTDIS_API int FASTDIS_CALL fastdis_scanner_contains_entity_id(
    const fastdis_scanner_t *scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity) {
    if (scanner == nullptr) {
        return 0;
    }
    return scanner->entity_ids.find(entity_key(site, application, entity)) != scanner->entity_ids.end() ? 1 : 0;
}

FASTDIS_API size_t FASTDIS_CALL fastdis_scanner_entity_id_count(const fastdis_scanner_t *scanner) {
    if (scanner == nullptr) {
        return 0;
    }
    return scanner->entity_ids.size();
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_accept_all(
    fastdis_scanner_t *scanner,
    uint32_t filter_kind) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return fastdis_scan_config_filter_accept_all(&scanner->config, filter_kind);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_clear(
    fastdis_scanner_t *scanner,
    uint32_t filter_kind) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return fastdis_scan_config_filter_clear(&scanner->config, filter_kind);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_allow(
    fastdis_scanner_t *scanner,
    uint32_t filter_kind,
    uint8_t value) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return fastdis_scan_config_filter_allow(&scanner->config, filter_kind, value);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_only(
    fastdis_scanner_t *scanner,
    uint32_t filter_kind,
    const uint8_t *values,
    size_t count) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return fastdis_scan_config_filter_only(&scanner->config, filter_kind, values, count);
}

FASTDIS_API int FASTDIS_CALL fastdis_scanner_filter_contains(
    const fastdis_scanner_t *scanner,
    uint32_t filter_kind,
    uint8_t value) {
    if (scanner == nullptr) {
        return 0;
    }
    return fastdis_scan_config_filter_contains(&scanner->config, filter_kind, value);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_sample(
    fastdis_scanner_t *scanner,
    uint32_t sample_every,
    uint32_t sample_offset) {
    if (scanner == nullptr || sample_every == 0u) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->config.sample_every = sample_every;
    scanner->config.sample_offset = sample_offset;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_state_fields(
    fastdis_scanner_t *scanner,
    uint64_t field_mask) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    scanner->config.entity_state_fields = normalize_entity_state_fields(field_mask);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_use_profile(
    fastdis_scanner_t *scanner,
    uint32_t profile_kind) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return apply_profile_to_config(&scanner->config, profile_kind);
}


FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_packets(
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    fastdis_packet_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return scan_many_impl(packets, count, &scanner->config, callback, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_state_packets(
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    fastdis_entity_state_callback_t callback,
    void *callback_user,
    fastdis_scan_stats_t *stats) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return scan_many_entity_state_impl(packets, count, &scanner->config, scanner, callback, callback_user, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_state_to_batch(
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    fastdis_entity_state_batch_t *out_batch,
    fastdis_scan_stats_t *stats) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return scan_many_entity_state_to_batch_impl(packets, count, &scanner->config, scanner, out_batch, stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_transforms_to_batch(
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    fastdis_entity_transform_batch_t *out_batch,
    fastdis_scan_stats_t *stats) {
    if (scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return scan_many_entity_transform_to_batch_impl(packets, count, &scanner->config, scanner, out_batch, stats);
}


FASTDIS_API fastdis_entity_table_t *FASTDIS_CALL fastdis_entity_table_create(size_t reserve) {
    try {
        return new (std::nothrow) fastdis_entity_table_t(reserve);
    } catch (...) {
        return nullptr;
    }
}

FASTDIS_API void FASTDIS_CALL fastdis_entity_table_destroy(fastdis_entity_table_t *table) {
    delete table;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_clear(fastdis_entity_table_t *table) {
    if (table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    table->entries.clear();
    table->tick = 0;
    table->total_updates = 0;
    table->total_new = 0;
    table->total_changed = 0;
    table->total_unchanged = 0;
    table->total_removed = 0;
    return FASTDIS_OK;
}

FASTDIS_API size_t FASTDIS_CALL fastdis_entity_table_size(const fastdis_entity_table_t *table) {
    return table != nullptr ? table->entries.size() : 0u;
}

FASTDIS_API uint64_t FASTDIS_CALL fastdis_entity_table_tick(const fastdis_entity_table_t *table) {
    return table != nullptr ? table->tick : 0u;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_advance_tick(
    fastdis_entity_table_t *table,
    uint64_t delta) {
    if (table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    table->tick += delta;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_mark_all_clean(fastdis_entity_table_t *table) {
    if (table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    for (auto &item : table->entries) {
        item.second.change_flags = FASTDIS_ENTITY_CHANGE_NONE;
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_update_transform(
    fastdis_entity_table_t *table,
    const fastdis_entity_transform_t *transform,
    fastdis_entity_snapshot_t *out_snapshot) {
    if (table == nullptr || transform == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return entity_table_apply_transform(table, *transform, out_snapshot, nullptr);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_ingest_packets(
    fastdis_entity_table_t *table,
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    uint32_t advance_tick,
    fastdis_entity_table_update_stats_t *out_stats) {
    if (table == nullptr || scanner == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    return scan_many_entity_transform_to_table_impl(
        table,
        packets,
        count,
        &scanner->config,
        scanner,
        advance_tick,
        out_stats);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_get(
    const fastdis_entity_table_t *table,
    uint16_t site,
    uint16_t application,
    uint16_t entity,
    fastdis_entity_snapshot_t *out_snapshot) {
    if (table == nullptr || out_snapshot == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    auto it = table->entries.find(entity_key(site, application, entity));
    if (it == table->entries.end()) {
        return FASTDIS_ERR_NOT_FOUND;
    }
    *out_snapshot = snapshot_from_entry(it->second);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_all(
    const fastdis_entity_table_t *table,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (table == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    reset_snapshot_batch(out_batch);
    for (const auto &item : table->entries) {
        append_snapshot_to_batch(out_batch, snapshot_from_entry(item.second));
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_changed(
    fastdis_entity_table_t *table,
    fastdis_entity_snapshot_batch_t *out_batch,
    uint32_t clear_flags) {
    if (table == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    reset_snapshot_batch(out_batch);
    for (auto &item : table->entries) {
        fastdis_entity_table_entry_s &entry = item.second;
        if (entry.change_flags == FASTDIS_ENTITY_CHANGE_NONE) {
            continue;
        }
        if (out_batch->count < out_batch->capacity) {
            out_batch->snapshots[out_batch->count++] = snapshot_from_entry(entry);
            if (clear_flags != 0u) {
                entry.change_flags = FASTDIS_ENTITY_CHANGE_NONE;
            }
        } else {
            out_batch->dropped += 1;
        }
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_stale(
    const fastdis_entity_table_t *table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (table == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    reset_snapshot_batch(out_batch);
    for (const auto &item : table->entries) {
        const fastdis_entity_table_entry_s &entry = item.second;
        if (entity_is_stale(table, entry, stale_after_ticks)) {
            append_snapshot_to_batch(out_batch, snapshot_from_entry(entry, FASTDIS_ENTITY_CHANGE_STALE));
        }
    }
    return FASTDIS_OK;
}


FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_evict_stale(
    fastdis_entity_table_t *table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (out_batch != nullptr) {
        if (!snapshot_batch_looks_valid(out_batch)) {
            return FASTDIS_ERR_BAD_ARGUMENT;
        }
        reset_snapshot_batch(out_batch);
    }

    for (auto it = table->entries.begin(); it != table->entries.end();) {
        if (entity_is_stale(table, it->second, stale_after_ticks)) {
            if (out_batch != nullptr) {
                append_snapshot_to_batch(out_batch, snapshot_from_entry(it->second, FASTDIS_ENTITY_CHANGE_STALE | FASTDIS_ENTITY_CHANGE_REMOVED));
            }
            it = table->entries.erase(it);
            table->total_removed += 1;
        } else {
            ++it;
        }
    }
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_transform_linear(
    const fastdis_entity_transform_t *transform,
    double delta_seconds,
    fastdis_entity_transform_t *out_transform) {
    if (transform == nullptr || out_transform == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (delta_seconds < 0.0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    *out_transform = extrapolate_transform_linear_value(*transform, delta_seconds);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_snapshot_linear(
    const fastdis_entity_snapshot_t *snapshot,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_t *out_snapshot) {
    if (snapshot == nullptr || out_snapshot == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (seconds_per_tick < 0.0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    *out_snapshot = extrapolate_snapshot_linear_value(*snapshot, target_tick, seconds_per_tick);
    return FASTDIS_OK;
}

FASTDIS_API const char * FASTDIS_CALL fastdis_dead_reckoning_algorithm_name(uint8_t algorithm) {
    switch (algorithm) {
        case FASTDIS_DR_OTHER: return "OTHER";
        case FASTDIS_DR_STATIC: return "STATIC";
        case FASTDIS_DR_FPW: return "DRM_FPW";
        case FASTDIS_DR_RPW: return "DRM_RPW";
        case FASTDIS_DR_RVW: return "DRM_RVW";
        case FASTDIS_DR_FVW: return "DRM_FVW";
        case FASTDIS_DR_FPB: return "DRM_FPB";
        case FASTDIS_DR_RPB: return "DRM_RPB";
        case FASTDIS_DR_RVB: return "DRM_RVB";
        case FASTDIS_DR_FVB: return "DRM_FVB";
        default: return "UNKNOWN";
    }
}

FASTDIS_API int FASTDIS_CALL fastdis_dead_reckoning_algorithm_known(uint8_t algorithm) {
    return algorithm <= FASTDIS_DR_FVB ? 1 : 0;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_transform_dead_reckoning(
    const fastdis_entity_transform_t *transform,
    double delta_seconds,
    fastdis_entity_transform_t *out_transform) {
    if (transform == nullptr || out_transform == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (delta_seconds < 0.0 || fastdis_dead_reckoning_algorithm_known(transform->dead_reckoning_algorithm) == 0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    *out_transform = extrapolate_transform_dead_reckoning_value(*transform, delta_seconds);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_snapshot_dead_reckoning(
    const fastdis_entity_snapshot_t *snapshot,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_t *out_snapshot) {
    if (snapshot == nullptr || out_snapshot == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (seconds_per_tick < 0.0 || fastdis_dead_reckoning_algorithm_known(snapshot->transform.dead_reckoning_algorithm) == 0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    *out_snapshot = extrapolate_snapshot_dead_reckoning_value(*snapshot, target_tick, seconds_per_tick);
    return FASTDIS_OK;
}


static inline void snapshot_view_from_buffer_slot(
    const fastdis_entity_snapshot_buffer_t *buffer,
    uint32_t slot,
    fastdis_entity_snapshot_view_t *out_view) noexcept {
    if (out_view == nullptr) {
        return;
    }
    std::memset(out_view, 0, sizeof(*out_view));
    out_view->snapshots = buffer->slots[slot].empty() ? nullptr : buffer->slots[slot].data();
    out_view->count = buffer->counts[slot];
    out_view->dropped = buffer->dropped[slot];
    out_view->generation = buffer->generations[slot];
    out_view->slot = slot;
}

static inline fastdis_entity_snapshot_batch_t snapshot_batch_for_buffer_slot(
    fastdis_entity_snapshot_buffer_t *buffer,
    uint32_t slot) noexcept {
    fastdis_entity_snapshot_batch_t batch;
    batch.snapshots = buffer->slots[slot].empty() ? nullptr : buffer->slots[slot].data();
    batch.capacity = buffer->slots[slot].size();
    batch.count = 0u;
    batch.dropped = 0u;
    return batch;
}

static inline uint32_t snapshot_buffer_find_writable_slot(
    const fastdis_entity_snapshot_buffer_t *buffer) noexcept {
    const size_t slot_count = buffer->slots.size();
    if (slot_count < 2u) {
        return UINT32_MAX;
    }
    size_t start = static_cast<size_t>(buffer->next_write_hint);
    if (start >= slot_count) {
        start = 0u;
    }
    for (size_t offset = 0u; offset < slot_count; ++offset) {
        const size_t candidate = (start + offset) % slot_count;
        if (candidate == static_cast<size_t>(buffer->read_slot)) {
            continue;
        }
        if (buffer->readers[candidate] == 0u) {
            return static_cast<uint32_t>(candidate);
        }
    }
    return UINT32_MAX;
}

static inline void snapshot_buffer_commit_publish_slot(
    fastdis_entity_snapshot_buffer_t *buffer,
    uint32_t slot) noexcept {
    buffer->read_slot = slot;
    const size_t slot_count = buffer->slots.size();
    if (slot_count == 0u) {
        buffer->next_write_hint = 0u;
        return;
    }
    buffer->next_write_hint = static_cast<uint32_t>((static_cast<size_t>(slot) + 1u) % slot_count);
}

static inline void snapshot_buffer_note_publish_attempt(fastdis_entity_snapshot_buffer_t *buffer) noexcept {
    buffer->stats.publish_attempts += 1u;
}

static inline fastdis_status_t snapshot_buffer_note_busy(fastdis_entity_snapshot_buffer_t *buffer) noexcept {
    buffer->stats.publish_busy += 1u;
    return FASTDIS_ERR_BUSY;
}

static inline void snapshot_buffer_note_publish_success(
    fastdis_entity_snapshot_buffer_t *buffer,
    const fastdis_entity_snapshot_batch_t &batch) noexcept {
    buffer->stats.publish_successes += 1u;
    if (batch.count > buffer->stats.max_snapshot_count) {
        buffer->stats.max_snapshot_count = batch.count;
    }
    buffer->stats.dropped_snapshots += batch.dropped;
}

FASTDIS_API fastdis_entity_snapshot_buffer_t *FASTDIS_CALL fastdis_entity_snapshot_buffer_create(size_t capacity) {
    return fastdis_entity_snapshot_buffer_create_ex(capacity, 2u);
}

FASTDIS_API fastdis_entity_snapshot_buffer_t *FASTDIS_CALL fastdis_entity_snapshot_buffer_create_ex(
    size_t capacity,
    size_t slot_count) {
    if (slot_count < 2u) {
        return nullptr;
    }
    try {
        return new (std::nothrow) fastdis_entity_snapshot_buffer_t(capacity, slot_count);
    } catch (...) {
        return nullptr;
    }
}

FASTDIS_API void FASTDIS_CALL fastdis_entity_snapshot_buffer_destroy(fastdis_entity_snapshot_buffer_t *buffer) {
    delete buffer;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_resize(
    fastdis_entity_snapshot_buffer_t *buffer,
    size_t capacity) {
    if (buffer == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    try {
        std::lock_guard<std::mutex> guard(buffer->mutex);
        for (size_t readers : buffer->readers) {
            if (readers != 0u) {
                return FASTDIS_ERR_BUSY;
            }
        }
        for (std::vector<fastdis_entity_snapshot_t> &slot : buffer->slots) {
            slot.resize(capacity);
        }
        for (size_t &count : buffer->counts) {
            count = 0u;
        }
        for (size_t &dropped : buffer->dropped) {
            dropped = 0u;
        }
        buffer->generation += 1u;
        for (uint64_t &slot_generation : buffer->generations) {
            slot_generation = buffer->generation;
        }
        buffer->read_slot = 0u;
        buffer->next_write_hint = 1u;
        return FASTDIS_OK;
    } catch (...) {
        return FASTDIS_ERR_OUT_OF_MEMORY;
    }
}

FASTDIS_API size_t FASTDIS_CALL fastdis_entity_snapshot_buffer_capacity(const fastdis_entity_snapshot_buffer_t *buffer) {
    if (buffer == nullptr) {
        return 0u;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    return buffer->slots[0].size();
}

FASTDIS_API size_t FASTDIS_CALL fastdis_entity_snapshot_buffer_slot_count(const fastdis_entity_snapshot_buffer_t *buffer) {
    if (buffer == nullptr) {
        return 0u;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    return buffer->slots.size();
}

FASTDIS_API uint64_t FASTDIS_CALL fastdis_entity_snapshot_buffer_generation(const fastdis_entity_snapshot_buffer_t *buffer) {
    if (buffer == nullptr) {
        return 0u;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    return buffer->generation;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_get_stats(
    const fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_snapshot_buffer_stats_t *out_stats) {
    if (buffer == nullptr || out_stats == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    *out_stats = buffer->stats;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_reset_stats(
    fastdis_entity_snapshot_buffer_t *buffer) {
    if (buffer == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    std::memset(&buffer->stats, 0, sizeof(buffer->stats));
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_all(
    fastdis_entity_snapshot_buffer_t *buffer,
    const fastdis_entity_table_t *table,
    fastdis_entity_snapshot_view_t *out_view) {
    if (buffer == nullptr || table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    snapshot_buffer_note_publish_attempt(buffer);
    const uint32_t slot = snapshot_buffer_find_writable_slot(buffer);
    if (slot == UINT32_MAX) {
        return snapshot_buffer_note_busy(buffer);
    }
    fastdis_entity_snapshot_batch_t batch = snapshot_batch_for_buffer_slot(buffer, slot);
    fastdis_status_t rc = fastdis_entity_table_snapshot_all(table, &batch);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    snapshot_buffer_note_publish_success(buffer, batch);
    buffer->counts[slot] = batch.count;
    buffer->dropped[slot] = batch.dropped;
    buffer->generation += 1u;
    buffer->generations[slot] = buffer->generation;
    snapshot_buffer_commit_publish_slot(buffer, slot);
    snapshot_view_from_buffer_slot(buffer, slot, out_view);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_changed(
    fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_table_t *table,
    uint32_t clear_flags,
    fastdis_entity_snapshot_view_t *out_view) {
    if (buffer == nullptr || table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    snapshot_buffer_note_publish_attempt(buffer);
    const uint32_t slot = snapshot_buffer_find_writable_slot(buffer);
    if (slot == UINT32_MAX) {
        return snapshot_buffer_note_busy(buffer);
    }
    fastdis_entity_snapshot_batch_t batch = snapshot_batch_for_buffer_slot(buffer, slot);
    fastdis_status_t rc = fastdis_entity_table_snapshot_changed(table, &batch, clear_flags);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    snapshot_buffer_note_publish_success(buffer, batch);
    buffer->counts[slot] = batch.count;
    buffer->dropped[slot] = batch.dropped;
    buffer->generation += 1u;
    buffer->generations[slot] = buffer->generation;
    snapshot_buffer_commit_publish_slot(buffer, slot);
    snapshot_view_from_buffer_slot(buffer, slot, out_view);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_stale(
    fastdis_entity_snapshot_buffer_t *buffer,
    const fastdis_entity_table_t *table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_view_t *out_view) {
    if (buffer == nullptr || table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    snapshot_buffer_note_publish_attempt(buffer);
    const uint32_t slot = snapshot_buffer_find_writable_slot(buffer);
    if (slot == UINT32_MAX) {
        return snapshot_buffer_note_busy(buffer);
    }
    fastdis_entity_snapshot_batch_t batch = snapshot_batch_for_buffer_slot(buffer, slot);
    fastdis_status_t rc = fastdis_entity_table_snapshot_stale(table, stale_after_ticks, &batch);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    snapshot_buffer_note_publish_success(buffer, batch);
    buffer->counts[slot] = batch.count;
    buffer->dropped[slot] = batch.dropped;
    buffer->generation += 1u;
    buffer->generations[slot] = buffer->generation;
    snapshot_buffer_commit_publish_slot(buffer, slot);
    snapshot_view_from_buffer_slot(buffer, slot, out_view);
    return FASTDIS_OK;
}


FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_evict_stale(
    fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_table_t *table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_view_t *out_view) {
    if (buffer == nullptr || table == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    snapshot_buffer_note_publish_attempt(buffer);
    const uint32_t slot = snapshot_buffer_find_writable_slot(buffer);
    if (slot == UINT32_MAX) {
        return snapshot_buffer_note_busy(buffer);
    }
    fastdis_entity_snapshot_batch_t batch = snapshot_batch_for_buffer_slot(buffer, slot);
    fastdis_status_t rc = fastdis_entity_table_evict_stale(table, stale_after_ticks, &batch);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    snapshot_buffer_note_publish_success(buffer, batch);
    buffer->counts[slot] = batch.count;
    buffer->dropped[slot] = batch.dropped;
    buffer->generation += 1u;
    buffer->generations[slot] = buffer->generation;
    snapshot_buffer_commit_publish_slot(buffer, slot);
    snapshot_view_from_buffer_slot(buffer, slot, out_view);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_ingest_packets_publish_changed(
    fastdis_entity_table_t *table,
    fastdis_scanner_t *scanner,
    const fastdis_packet_view_t *packets,
    size_t count,
    uint32_t advance_tick,
    uint32_t clear_flags,
    fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_table_update_stats_t *out_stats,
    fastdis_entity_snapshot_view_t *out_view) {
    if (table == nullptr || scanner == nullptr || buffer == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    fastdis_status_t rc = fastdis_entity_table_ingest_packets(table, scanner, packets, count, advance_tick, out_stats);
    if (rc != FASTDIS_OK) {
        return rc;
    }
    return fastdis_entity_snapshot_buffer_publish_changed(buffer, table, clear_flags, out_view);
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_acquire_latest(
    fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_snapshot_view_t *out_view) {
    if (buffer == nullptr || out_view == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    const uint32_t slot = buffer->read_slot;
    buffer->readers[slot] += 1u;
    buffer->stats.acquire_count += 1u;
    snapshot_view_from_buffer_slot(buffer, slot, out_view);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_release(
    fastdis_entity_snapshot_buffer_t *buffer,
    const fastdis_entity_snapshot_view_t *view) {
    if (buffer == nullptr || view == nullptr) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    const uint32_t slot = view->slot;
    if (static_cast<size_t>(slot) >= buffer->slots.size()) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (buffer->readers[slot] == 0u || buffer->generations[slot] != view->generation) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    buffer->readers[slot] -= 1u;
    buffer->stats.release_count += 1u;
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest(
    fastdis_entity_snapshot_buffer_t *buffer,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (buffer == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    reset_snapshot_batch(out_batch);
    const uint32_t slot = buffer->read_slot;
    const size_t available = buffer->counts[slot];
    const size_t to_copy = available < out_batch->capacity ? available : out_batch->capacity;
    if (to_copy > 0u) {
        std::memcpy(out_batch->snapshots, buffer->slots[slot].data(), to_copy * sizeof(fastdis_entity_snapshot_t));
    }
    out_batch->count = to_copy;
    out_batch->dropped = buffer->dropped[slot] + (available - to_copy);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest_extrapolated(
    fastdis_entity_snapshot_buffer_t *buffer,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (buffer == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (seconds_per_tick < 0.0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    reset_snapshot_batch(out_batch);
    const uint32_t slot = buffer->read_slot;
    const size_t available = buffer->counts[slot];
    const size_t to_copy = available < out_batch->capacity ? available : out_batch->capacity;
    for (size_t i = 0; i < to_copy; ++i) {
        out_batch->snapshots[i] = extrapolate_snapshot_linear_value(buffer->slots[slot][i], target_tick, seconds_per_tick);
    }
    out_batch->count = to_copy;
    out_batch->dropped = buffer->dropped[slot] + (available - to_copy);
    return FASTDIS_OK;
}

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned(
    fastdis_entity_snapshot_buffer_t *buffer,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_batch_t *out_batch) {
    if (buffer == nullptr || !snapshot_batch_looks_valid(out_batch)) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    if (seconds_per_tick < 0.0) {
        return FASTDIS_ERR_BAD_ARGUMENT;
    }
    std::lock_guard<std::mutex> guard(buffer->mutex);
    reset_snapshot_batch(out_batch);
    const uint32_t slot = buffer->read_slot;
    const size_t available = buffer->counts[slot];
    const size_t to_copy = available < out_batch->capacity ? available : out_batch->capacity;
    for (size_t i = 0; i < to_copy; ++i) {
        if (fastdis_dead_reckoning_algorithm_known(buffer->slots[slot][i].transform.dead_reckoning_algorithm) == 0) {
            return FASTDIS_ERR_BAD_ARGUMENT;
        }
        out_batch->snapshots[i] = extrapolate_snapshot_dead_reckoning_value(buffer->slots[slot][i], target_tick, seconds_per_tick);
    }
    out_batch->count = to_copy;
    out_batch->dropped = buffer->dropped[slot] + (available - to_copy);
    return FASTDIS_OK;
}

} // extern "C"
