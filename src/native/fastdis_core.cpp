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

static inline fastdis_entity_id_t read_entity_id(const uint8_t *p) noexcept {
    fastdis_entity_id_t out;
    out.site = be16(p + 0);
    out.application = be16(p + 2);
    out.entity = be16(p + 4);
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

static inline bool is_simulation_management_header(const fastdis_header_t *header, uint8_t pdu_type) noexcept {
    return header != nullptr &&
           header->pdu_type == pdu_type &&
           header->protocol_family == 5u;
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
