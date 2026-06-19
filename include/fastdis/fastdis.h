#ifndef FASTDIS_FASTDIS_H
#define FASTDIS_FASTDIS_H

/*
 * fastdis native ABI
 *
 * The implementation may be C++, but this public boundary is C. That gives us
 * a simple DLL/shared-object interface for Python, Unreal, Godot/GDExtension,
 * C#, Rust, Zig, and other FFI callers.
 *
 * ABI rules:
 *   - Do not expose C++ classes, templates, STL containers, or exceptions.
 *   - Use POD structs with fixed-width integer fields.
 *   - Add fields only at the end of structs and bump FASTDIS_ABI_VERSION.
 *   - Opaque handles are allocated/destroyed only by fastdis functions.
 */

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
  #define FASTDIS_CALL __cdecl
  #ifdef FASTDIS_EXPORTS
    #define FASTDIS_API __declspec(dllexport)
  #else
    #define FASTDIS_API __declspec(dllimport)
  #endif
#else
  #define FASTDIS_CALL
  #if defined(__GNUC__) || defined(__clang__)
    #define FASTDIS_API __attribute__((visibility("default")))
  #else
    #define FASTDIS_API
  #endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define FASTDIS_ABI_VERSION 8u
#define FASTDIS_HEADER_SIZE 12u
#define FASTDIS_PROTOCOL_VERSION_DIS6 6u
#define FASTDIS_PROTOCOL_VERSION_DIS7 7u
#define FASTDIS_HEADER_STATUS_UNAVAILABLE (-1)
#define FASTDIS_ENTITY_INFORMATION_FAMILY 1u
#define FASTDIS_ENTITY_STATE_PDU_TYPE 1u
#define FASTDIS_ENTITY_STATE_FIXED_SIZE 144u

/* Parse flags. */
#define FASTDIS_FLAG_ALLOW_TRUNCATED 0x00000001u
/* Entity State field-subscription mask. Non-requested fields are zero-filled.
 * The scanner always fills HEADER and FORCE_ID because those are required for
 * routing and optional force filtering.
 */
#define FASTDIS_ES_FIELD_HEADER                  0x0000000000000001ull
#define FASTDIS_ES_FIELD_ENTITY_ID               0x0000000000000002ull
#define FASTDIS_ES_FIELD_FORCE_ID                0x0000000000000004ull
#define FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT 0x0000000000000008ull
#define FASTDIS_ES_FIELD_ENTITY_TYPE             0x0000000000000010ull
#define FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE   0x0000000000000020ull
#define FASTDIS_ES_FIELD_LINEAR_VELOCITY         0x0000000000000040ull
#define FASTDIS_ES_FIELD_LOCATION                0x0000000000000080ull
#define FASTDIS_ES_FIELD_ORIENTATION             0x0000000000000100ull
#define FASTDIS_ES_FIELD_APPEARANCE              0x0000000000000200ull
#define FASTDIS_ES_FIELD_DEAD_RECKONING          0x0000000000000400ull
#define FASTDIS_ES_FIELD_MARKING                 0x0000000000000800ull
#define FASTDIS_ES_FIELD_CAPABILITIES            0x0000000000001000ull
#define FASTDIS_ES_FIELD_ROUTING                 (FASTDIS_ES_FIELD_HEADER | FASTDIS_ES_FIELD_ENTITY_ID | FASTDIS_ES_FIELD_FORCE_ID)
#define FASTDIS_ES_FIELD_POSE                    (FASTDIS_ES_FIELD_ENTITY_ID | FASTDIS_ES_FIELD_FORCE_ID | FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION)
#define FASTDIS_ES_FIELD_KINEMATICS              (FASTDIS_ES_FIELD_LINEAR_VELOCITY | FASTDIS_ES_FIELD_DEAD_RECKONING)
#define FASTDIS_ES_FIELD_ALL                     (FASTDIS_ES_FIELD_HEADER | FASTDIS_ES_FIELD_ENTITY_ID | FASTDIS_ES_FIELD_FORCE_ID | FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT | FASTDIS_ES_FIELD_ENTITY_TYPE | FASTDIS_ES_FIELD_ALTERNATE_ENTITY_TYPE | FASTDIS_ES_FIELD_LINEAR_VELOCITY | FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION | FASTDIS_ES_FIELD_APPEARANCE | FASTDIS_ES_FIELD_DEAD_RECKONING | FASTDIS_ES_FIELD_MARKING | FASTDIS_ES_FIELD_CAPABILITIES)

/* Opaque scanner entity-ID set modes. */
#define FASTDIS_ENTITY_ID_FILTER_DISABLED 0u
#define FASTDIS_ENTITY_ID_FILTER_ALLOW    1u
#define FASTDIS_ENTITY_ID_FILTER_BLOCK    2u

/* Generic filter slots for ABI helpers. Engines can use these helpers instead
 * of depending on the layout of fastdis_scan_config_t.
 */
#define FASTDIS_FILTER_VERSIONS           1u
#define FASTDIS_FILTER_PDU_TYPES          2u
#define FASTDIS_FILTER_PROTOCOL_FAMILIES  3u
#define FASTDIS_FILTER_EXERCISE_IDS       4u
#define FASTDIS_FILTER_ENTITY_FORCE_IDS   5u
/* Singular aliases are easier to read when adding one value. */
#define FASTDIS_FILTER_VERSION            FASTDIS_FILTER_VERSIONS
#define FASTDIS_FILTER_PDU_TYPE           FASTDIS_FILTER_PDU_TYPES
#define FASTDIS_FILTER_PROTOCOL_FAMILY    FASTDIS_FILTER_PROTOCOL_FAMILIES
#define FASTDIS_FILTER_EXERCISE_ID        FASTDIS_FILTER_EXERCISE_IDS
#define FASTDIS_FILTER_ENTITY_FORCE_ID    FASTDIS_FILTER_ENTITY_FORCE_IDS


/* Latest-state/entity-table change flags. Snapshots may OR these bits. */
#define FASTDIS_ENTITY_CHANGE_NONE       0x00000000u
#define FASTDIS_ENTITY_CHANGE_NEW        0x00000001u
#define FASTDIS_ENTITY_CHANGE_UPDATED    0x00000002u
#define FASTDIS_ENTITY_CHANGE_STALE      0x00000004u
#define FASTDIS_ENTITY_CHANGE_REMOVED    0x00000008u
#define FASTDIS_ENTITY_CHANGE_UNCHANGED  0x00000010u

/* Scanner/config profiles for common engine and benchmark cases. */
#define FASTDIS_PROFILE_HEADER_COUNTING        1u
#define FASTDIS_PROFILE_ENTITY_STATE_ROUTING   2u
#define FASTDIS_PROFILE_ENTITY_STATE_POSE      3u
#define FASTDIS_PROFILE_ENTITY_STATE_FULL      4u
#define FASTDIS_PROFILE_ENTITY_TRANSFORM       5u

typedef enum fastdis_status_e {
    FASTDIS_OK = 0,
    FASTDIS_ERR_BAD_ARGUMENT = -1,
    FASTDIS_ERR_SHORT_PACKET = -2,
    FASTDIS_ERR_LENGTH_TOO_SMALL = -3,
    FASTDIS_ERR_LENGTH_EXCEEDS_BUFFER = -4,
    FASTDIS_ERR_CALLBACK_STOPPED = -5,
    FASTDIS_ERR_UNSUPPORTED_PDU = -6,
    FASTDIS_ERR_OUT_OF_MEMORY = -7,
    FASTDIS_ERR_NOT_FOUND = -8,
    FASTDIS_ERR_BUSY = -9
} fastdis_status_t;

/* Parsed fixed DIS PDU header.
 *
 * DIS 7+:
 *   status  = byte 10
 *   padding = byte 11
 *
 * DIS 6 / earlier:
 *   status  = -1
 *   padding = big-endian uint16 from bytes 10..11
 */
typedef struct fastdis_header_s {
    uint8_t version;
    uint8_t exercise_id;
    uint8_t pdu_type;
    uint8_t protocol_family;
    uint32_t timestamp;
    uint16_t length;
    int16_t status;
    uint16_t padding;
} fastdis_header_t;

static inline int fastdis_header_has_pdu_status(const fastdis_header_t* header) {
    return header != NULL && header->version >= FASTDIS_PROTOCOL_VERSION_DIS7;
}

static inline uint8_t fastdis_header_pdu_status(const fastdis_header_t* header) {
    return fastdis_header_has_pdu_status(header) ? (uint8_t)header->status : 0u;
}

static inline uint8_t fastdis_header_padding_octet(const fastdis_header_t* header) {
    return fastdis_header_has_pdu_status(header) ? (uint8_t)(header->padding & 0xffu) : 0u;
}

static inline uint16_t fastdis_header_legacy_padding(const fastdis_header_t* header) {
    return fastdis_header_has_pdu_status(header) ? 0u : (header != NULL ? header->padding : 0u);
}

typedef struct fastdis_entity_id_s {
    uint16_t site;
    uint16_t application;
    uint16_t entity;
} fastdis_entity_id_t;

typedef struct fastdis_entity_type_s {
    uint8_t entity_kind;
    uint8_t domain;
    uint16_t country;
    uint8_t category;
    uint8_t subcategory;
    uint8_t specific;
    uint8_t extra;
} fastdis_entity_type_t;

typedef struct fastdis_vec3f_s {
    float x;
    float y;
    float z;
} fastdis_vec3f_t;

typedef struct fastdis_world_coordinates_s {
    double x;
    double y;
    double z;
} fastdis_world_coordinates_t;

typedef struct fastdis_euler_angles_s {
    float psi;
    float theta;
    float phi;
} fastdis_euler_angles_t;

/* Fixed prefix of an Entity State PDU.
 *
 * Field masks let the native scanner decode only the fields a caller subscribed
 * to. Non-requested fields are zero. `fields_present` tells the callback exactly
 * what was filled; HEADER and FORCE_ID are always present for routing.
 */
typedef struct fastdis_entity_state_prefix_s {
    fastdis_header_t header;
    fastdis_entity_id_t entity_id;
    uint8_t force_id;
    uint8_t variable_parameter_count;
    fastdis_entity_type_t entity_type;
    fastdis_entity_type_t alternate_entity_type;
    fastdis_vec3f_t linear_velocity;
    fastdis_world_coordinates_t location;
    fastdis_euler_angles_t orientation;
    uint32_t appearance;
    uint8_t dead_reckoning_algorithm;
    uint8_t dead_reckoning_parameters[15];
    fastdis_vec3f_t dead_reckoning_linear_acceleration;
    fastdis_vec3f_t dead_reckoning_angular_velocity;
    uint8_t marking_character_set;
    uint8_t marking[12]; /* 11 DIS bytes plus a NUL convenience byte. */
    uint32_t capabilities;
    uint64_t fields_present;
} fastdis_entity_state_prefix_t;

/* Caller-owned output buffer for callback-free Entity State scans.
 * Functions reset count and dropped on entry. stats.emitted counts records that
 * survived filters/downsampling; dropped counts emitted records not stored
 * because capacity was exhausted.
 */
typedef struct fastdis_entity_state_batch_s {
    fastdis_entity_state_prefix_t* entities;
    size_t capacity;
    size_t count;
    size_t dropped;
} fastdis_entity_state_batch_t;

/* Engine-shaped pose/transform output. This is intentionally smaller and less
 * protocol-shaped than fastdis_entity_state_prefix_t. It is the preferred output
 * for Unreal/Godot actor-table updates.
 */
typedef struct fastdis_entity_transform_s {
    fastdis_entity_id_t entity_id;
    uint8_t force_id;
    uint8_t exercise_id;
    uint8_t version;
    uint8_t reserved0;
    uint32_t timestamp;
    uint32_t appearance;
    fastdis_world_coordinates_t location;
    fastdis_euler_angles_t orientation;
    fastdis_vec3f_t linear_velocity;
    uint64_t fields_present;
} fastdis_entity_transform_t;

typedef struct fastdis_entity_transform_batch_s {
    fastdis_entity_transform_t* transforms;
    size_t capacity;
    size_t count;
    size_t dropped;
} fastdis_entity_transform_batch_t;

/* Snapshot record returned by the native latest-state/entity table.
 * `first_seen_tick` and `last_seen_tick` are table ticks, not wall-clock time.
 * A typical engine calls ingest with advance_tick=1 once per frame/network burst.
 */
typedef struct fastdis_entity_snapshot_s {
    fastdis_entity_transform_t transform;
    uint64_t first_seen_tick;
    uint64_t last_seen_tick;
    uint64_t update_count;
    uint32_t change_flags;
    uint32_t reserved0;
} fastdis_entity_snapshot_t;

typedef struct fastdis_entity_snapshot_batch_s {
    fastdis_entity_snapshot_t* snapshots;
    size_t capacity;
    size_t count;
    size_t dropped;
} fastdis_entity_snapshot_batch_t;

/* Compact 0..255 allow-list. If active == 0, all values match. If active != 0,
 * only set bits match. Four uint64 words cover 256 possible byte values.
 */
typedef struct fastdis_u8_filter_s {
    uint8_t active;
    uint8_t reserved[7];
    uint64_t bits[4];
} fastdis_u8_filter_t;

/* Header/entity scan configuration. Initialize with fastdis_scan_config_init. */
typedef struct fastdis_scan_config_s {
    uint32_t struct_size;
    uint32_t flags;
    uint32_t sample_every;
    uint32_t sample_offset;
    fastdis_u8_filter_t versions;
    fastdis_u8_filter_t pdu_types;
    fastdis_u8_filter_t protocol_families;
    fastdis_u8_filter_t exercise_ids;
    /* Applied by entity-state scans after parsing the fixed ESPDU prefix. */
    fastdis_u8_filter_t entity_force_ids;
    /* Entity State field mask. 0 means FASTDIS_ES_FIELD_ALL. */
    uint64_t entity_state_fields;
} fastdis_scan_config_t;

/* Non-owning packet view. user is passed to the callback for this packet. */
typedef struct fastdis_packet_view_s {
    const uint8_t* data;
    size_t size;
    void* user;
} fastdis_packet_view_t;

typedef struct fastdis_scan_stats_s {
    uint64_t seen;
    uint64_t malformed;
    uint64_t accepted;
    uint64_t emitted;
} fastdis_scan_stats_t;

/* Per-ingest entity-table update stats. `scan` uses normal scanner semantics:
 * seen/malformed/accepted/emitted. Table counters describe retained transforms
 * that were actually applied to the latest-state cache.
 */
typedef struct fastdis_entity_table_update_stats_s {
    fastdis_scan_stats_t scan;
    uint64_t tick;
    uint64_t entity_count;
    uint64_t table_updates;
    uint64_t new_entities;
    uint64_t changed_entities;
    uint64_t unchanged_entities;
    uint64_t removed_entities;
} fastdis_entity_table_update_stats_t;

/* Snapshot-buffer pressure counters.
 * publish_busy counts publish calls rejected because the next write slot is
 * still pinned by a reader. dropped_snapshots counts record-level drops caused
 * by snapshot capacity limits, not busy publish attempts.
 */
typedef struct fastdis_entity_snapshot_buffer_stats_s {
    uint64_t publish_attempts;
    uint64_t publish_successes;
    uint64_t publish_busy;
    uint64_t acquire_count;
    uint64_t release_count;
    uint64_t max_snapshot_count;
    uint64_t dropped_snapshots;
} fastdis_entity_snapshot_buffer_stats_t;

typedef struct fastdis_scanner_s fastdis_scanner_t;
typedef struct fastdis_entity_table_s fastdis_entity_table_t;
typedef struct fastdis_entity_snapshot_buffer_s fastdis_entity_snapshot_buffer_t;

/* Borrowed view into a fastdis_entity_snapshot_buffer_t read slot.
 * The pointer is owned by the buffer. It is valid until the next publish unless
 * acquired with fastdis_entity_snapshot_buffer_acquire_latest(), in which case
 * the caller must release it with fastdis_entity_snapshot_buffer_release().
 */
typedef struct fastdis_entity_snapshot_view_s {
    const fastdis_entity_snapshot_t* snapshots;
    size_t count;
    size_t dropped;
    uint64_t generation;
    uint32_t slot;
    uint32_t reserved0;
} fastdis_entity_snapshot_view_t;

/* Callback return convention:
 *   0     continue
 *   != 0  stop scan and return FASTDIS_ERR_CALLBACK_STOPPED
 */
typedef int (FASTDIS_CALL *fastdis_packet_callback_t)(
    const fastdis_header_t* header,
    const uint8_t* data,
    size_t size,
    void* packet_user,
    void* callback_user);

typedef int (FASTDIS_CALL *fastdis_entity_state_callback_t)(
    const fastdis_entity_state_prefix_t* entity_state,
    const uint8_t* data,
    size_t size,
    void* packet_user,
    void* callback_user);

FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_version(void);
FASTDIS_API const char* FASTDIS_CALL fastdis_version_string(void);
FASTDIS_API const char* FASTDIS_CALL fastdis_status_string(fastdis_status_t status);

FASTDIS_API void FASTDIS_CALL fastdis_filter_accept_all(fastdis_u8_filter_t* filter);
FASTDIS_API void FASTDIS_CALL fastdis_filter_clear(fastdis_u8_filter_t* filter);
FASTDIS_API void FASTDIS_CALL fastdis_filter_allow(fastdis_u8_filter_t* filter, uint8_t value);
FASTDIS_API int FASTDIS_CALL fastdis_filter_contains(const fastdis_u8_filter_t* filter, uint8_t value);

FASTDIS_API void FASTDIS_CALL fastdis_scan_config_init(fastdis_scan_config_t* config);
FASTDIS_API void FASTDIS_CALL fastdis_scan_stats_init(fastdis_scan_stats_t* stats);
FASTDIS_API void FASTDIS_CALL fastdis_entity_table_update_stats_init(fastdis_entity_table_update_stats_t* stats);
FASTDIS_API void FASTDIS_CALL fastdis_entity_snapshot_buffer_stats_init(fastdis_entity_snapshot_buffer_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_accept_all(
    fastdis_scan_config_t* config,
    uint32_t filter_kind);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_clear(
    fastdis_scan_config_t* config,
    uint32_t filter_kind);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_allow(
    fastdis_scan_config_t* config,
    uint32_t filter_kind,
    uint8_t value);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_filter_only(
    fastdis_scan_config_t* config,
    uint32_t filter_kind,
    const uint8_t* values,
    size_t count);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_set_sample(
    fastdis_scan_config_t* config,
    uint32_t sample_every,
    uint32_t sample_offset);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_set_entity_state_fields(
    fastdis_scan_config_t* config,
    uint64_t field_mask);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_config_use_profile(
    fastdis_scan_config_t* config,
    uint32_t profile_kind);

FASTDIS_API int FASTDIS_CALL fastdis_scan_config_filter_contains(
    const fastdis_scan_config_t* config,
    uint32_t filter_kind,
    uint8_t value);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_header(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_header_t* out_header);

FASTDIS_API int FASTDIS_CALL fastdis_header_matches(
    const fastdis_header_t* header,
    const fastdis_scan_config_t* config);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_packet(
    const uint8_t* data,
    size_t size,
    const fastdis_scan_config_t* config,
    fastdis_packet_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_packets(
    const fastdis_packet_view_t* packets,
    size_t count,
    const fastdis_scan_config_t* config,
    fastdis_packet_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_state_prefix(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_entity_state_prefix_t* out_entity_state);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_state_fields(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    uint64_t field_mask,
    fastdis_entity_state_prefix_t* out_entity_state);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_transform(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_entity_transform_t* out_transform);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_packet(
    const uint8_t* data,
    size_t size,
    const fastdis_scan_config_t* config,
    fastdis_entity_state_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_packets(
    const fastdis_packet_view_t* packets,
    size_t count,
    const fastdis_scan_config_t* config,
    fastdis_entity_state_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_state_to_batch(
    const fastdis_packet_view_t* packets,
    size_t count,
    const fastdis_scan_config_t* config,
    fastdis_entity_state_batch_t* out_batch,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scan_entity_transforms_to_batch(
    const fastdis_packet_view_t* packets,
    size_t count,
    const fastdis_scan_config_t* config,
    fastdis_entity_transform_batch_t* out_batch,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_scanner_t* FASTDIS_CALL fastdis_scanner_create(
    const fastdis_scan_config_t* config);
FASTDIS_API void FASTDIS_CALL fastdis_scanner_destroy(fastdis_scanner_t* scanner);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_config(
    fastdis_scanner_t* scanner,
    const fastdis_scan_config_t* config);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_get_config(
    const fastdis_scanner_t* scanner,
    fastdis_scan_config_t* out_config);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_id_filter_mode(
    fastdis_scanner_t* scanner,
    uint32_t mode);
FASTDIS_API uint32_t FASTDIS_CALL fastdis_scanner_get_entity_id_filter_mode(
    const fastdis_scanner_t* scanner);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_clear_entity_ids(
    fastdis_scanner_t* scanner);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_add_entity_id(
    fastdis_scanner_t* scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_add_entity_ids(
    fastdis_scanner_t* scanner,
    const fastdis_entity_id_t* ids,
    size_t count);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_ids(
    fastdis_scanner_t* scanner,
    uint32_t mode,
    const fastdis_entity_id_t* ids,
    size_t count);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_remove_entity_id(
    fastdis_scanner_t* scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity);
FASTDIS_API int FASTDIS_CALL fastdis_scanner_contains_entity_id(
    const fastdis_scanner_t* scanner,
    uint16_t site,
    uint16_t application,
    uint16_t entity);
FASTDIS_API size_t FASTDIS_CALL fastdis_scanner_entity_id_count(
    const fastdis_scanner_t* scanner);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_accept_all(
    fastdis_scanner_t* scanner,
    uint32_t filter_kind);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_clear(
    fastdis_scanner_t* scanner,
    uint32_t filter_kind);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_allow(
    fastdis_scanner_t* scanner,
    uint32_t filter_kind,
    uint8_t value);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_filter_only(
    fastdis_scanner_t* scanner,
    uint32_t filter_kind,
    const uint8_t* values,
    size_t count);
FASTDIS_API int FASTDIS_CALL fastdis_scanner_filter_contains(
    const fastdis_scanner_t* scanner,
    uint32_t filter_kind,
    uint8_t value);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_sample(
    fastdis_scanner_t* scanner,
    uint32_t sample_every,
    uint32_t sample_offset);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_set_entity_state_fields(
    fastdis_scanner_t* scanner,
    uint64_t field_mask);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_use_profile(
    fastdis_scanner_t* scanner,
    uint32_t profile_kind);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_packets(
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    fastdis_packet_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_state_packets(
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    fastdis_entity_state_callback_t callback,
    void* callback_user,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_state_to_batch(
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    fastdis_entity_state_batch_t* out_batch,
    fastdis_scan_stats_t* stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_scanner_scan_entity_transforms_to_batch(
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    fastdis_entity_transform_batch_t* out_batch,
    fastdis_scan_stats_t* stats);


/* Native latest-state/entity table. The table owns only latest compact
 * transform records keyed by Entity ID. It is intentionally opaque so the ABI
 * remains stable while the implementation can switch hash tables later.
 */
FASTDIS_API fastdis_entity_table_t* FASTDIS_CALL fastdis_entity_table_create(size_t reserve);
FASTDIS_API void FASTDIS_CALL fastdis_entity_table_destroy(fastdis_entity_table_t* table);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_clear(fastdis_entity_table_t* table);
FASTDIS_API size_t FASTDIS_CALL fastdis_entity_table_size(const fastdis_entity_table_t* table);
FASTDIS_API uint64_t FASTDIS_CALL fastdis_entity_table_tick(const fastdis_entity_table_t* table);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_advance_tick(
    fastdis_entity_table_t* table,
    uint64_t delta);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_mark_all_clean(fastdis_entity_table_t* table);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_update_transform(
    fastdis_entity_table_t* table,
    const fastdis_entity_transform_t* transform,
    fastdis_entity_snapshot_t* out_snapshot);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_ingest_packets(
    fastdis_entity_table_t* table,
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    uint32_t advance_tick,
    fastdis_entity_table_update_stats_t* out_stats);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_get(
    const fastdis_entity_table_t* table,
    uint16_t site,
    uint16_t application,
    uint16_t entity,
    fastdis_entity_snapshot_t* out_snapshot);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_all(
    const fastdis_entity_table_t* table,
    fastdis_entity_snapshot_batch_t* out_batch);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_changed(
    fastdis_entity_table_t* table,
    fastdis_entity_snapshot_batch_t* out_batch,
    uint32_t clear_flags);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_snapshot_stale(
    const fastdis_entity_table_t* table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_batch_t* out_batch);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_evict_stale(
    fastdis_entity_table_t* table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_batch_t* out_batch);

/* Snapshot handoff. The default create function owns two reusable snapshot
 * arrays. create_ex allows 3+ slots for engine frame timing tolerance. Publish
 * writes table snapshots into an inactive unpinned slot, swaps it to become the
 * latest read slot, and returns a borrowed view. acquire_latest/release pins a
 * read slot so a producer will not overwrite it; if no inactive slot is
 * available, publish returns FASTDIS_ERR_BUSY instead of allocating or blocking.
 */
FASTDIS_API fastdis_entity_snapshot_buffer_t* FASTDIS_CALL fastdis_entity_snapshot_buffer_create(size_t capacity);
FASTDIS_API fastdis_entity_snapshot_buffer_t* FASTDIS_CALL fastdis_entity_snapshot_buffer_create_ex(
    size_t capacity,
    size_t slot_count);
FASTDIS_API void FASTDIS_CALL fastdis_entity_snapshot_buffer_destroy(fastdis_entity_snapshot_buffer_t* buffer);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_resize(
    fastdis_entity_snapshot_buffer_t* buffer,
    size_t capacity);
FASTDIS_API size_t FASTDIS_CALL fastdis_entity_snapshot_buffer_capacity(const fastdis_entity_snapshot_buffer_t* buffer);
FASTDIS_API size_t FASTDIS_CALL fastdis_entity_snapshot_buffer_slot_count(const fastdis_entity_snapshot_buffer_t* buffer);
FASTDIS_API uint64_t FASTDIS_CALL fastdis_entity_snapshot_buffer_generation(const fastdis_entity_snapshot_buffer_t* buffer);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_get_stats(
    const fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_snapshot_buffer_stats_t* out_stats);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_reset_stats(
    fastdis_entity_snapshot_buffer_t* buffer);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_all(
    fastdis_entity_snapshot_buffer_t* buffer,
    const fastdis_entity_table_t* table,
    fastdis_entity_snapshot_view_t* out_view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_changed(
    fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_table_t* table,
    uint32_t clear_flags,
    fastdis_entity_snapshot_view_t* out_view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_stale(
    fastdis_entity_snapshot_buffer_t* buffer,
    const fastdis_entity_table_t* table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_view_t* out_view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_publish_evict_stale(
    fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_table_t* table,
    uint64_t stale_after_ticks,
    fastdis_entity_snapshot_view_t* out_view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_acquire_latest(
    fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_snapshot_view_t* out_view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_release(
    fastdis_entity_snapshot_buffer_t* buffer,
    const fastdis_entity_snapshot_view_t* view);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest(
    fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_snapshot_batch_t* out_batch);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_table_ingest_packets_publish_changed(
    fastdis_entity_table_t* table,
    fastdis_scanner_t* scanner,
    const fastdis_packet_view_t* packets,
    size_t count,
    uint32_t advance_tick,
    uint32_t clear_flags,
    fastdis_entity_snapshot_buffer_t* buffer,
    fastdis_entity_table_update_stats_t* out_stats,
    fastdis_entity_snapshot_view_t* out_view);


#ifdef __cplusplus
} /* extern C */
#endif

#endif /* FASTDIS_FASTDIS_H */
