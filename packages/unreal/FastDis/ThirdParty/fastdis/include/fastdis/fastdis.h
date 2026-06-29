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
 *   - Add fields only at the end of structs and bump FASTDIS_ABI_REVISION while unpublished.
 *   - Reset FASTDIS_ABI_EPOCH to 1 and revision to 0 for the first public native ABI preview.
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

#define FASTDIS_ABI_EPOCH 0u
#define FASTDIS_ABI_REVISION 16u
#define FASTDIS_ABI_VERSION FASTDIS_ABI_REVISION
#define FASTDIS_HEADER_SIZE 12u
#define FASTDIS_PROTOCOL_VERSION_DIS6 6u
#define FASTDIS_PROTOCOL_VERSION_DIS7 7u
#define FASTDIS_HEADER_STATUS_UNAVAILABLE (-1)
#define FASTDIS_ENTITY_INFORMATION_FAMILY 1u
#define FASTDIS_OTHER_PDU_TYPE 0u
#define FASTDIS_OTHER_FIXED_SIZE 12u
#define FASTDIS_ENTITY_STATE_PDU_TYPE 1u
#define FASTDIS_ENTITY_STATE_FIXED_SIZE 144u
#define FASTDIS_FIRE_PDU_TYPE 2u
#define FASTDIS_FIRE_FIXED_SIZE 96u
#define FASTDIS_DETONATION_PDU_TYPE 3u
#define FASTDIS_DETONATION_FIXED_SIZE 92u
#define FASTDIS_COLLISION_PDU_TYPE 4u
#define FASTDIS_COLLISION_FIXED_SIZE 60u
#define FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE 23u
#define FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE 28u
#define FASTDIS_DESIGNATOR_PDU_TYPE 24u
#define FASTDIS_DESIGNATOR_FIXED_SIZE 88u
#define FASTDIS_TRANSMITTER_PDU_TYPE 25u
#define FASTDIS_TRANSMITTER_FIXED_SIZE 100u
#define FASTDIS_SIGNAL_PDU_TYPE 26u
#define FASTDIS_SIGNAL_DIS6_FIXED_SIZE 32u
#define FASTDIS_SIGNAL_DIS7_FIXED_SIZE 24u
#define FASTDIS_RECEIVER_PDU_TYPE 27u
#define FASTDIS_RECEIVER_DIS6_FIXED_SIZE 36u
#define FASTDIS_RECEIVER_DIS7_FIXED_SIZE 28u
#define FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE 28u
#define FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE 56u
#define FASTDIS_IFF_PDU_TYPE 28u
#define FASTDIS_IFF_FIXED_SIZE 56u
#define FASTDIS_UA_PDU_TYPE 29u
#define FASTDIS_UA_FIXED_SIZE 32u
#define FASTDIS_SEES_PDU_TYPE 30u
#define FASTDIS_SEES_FIXED_SIZE 28u
#define FASTDIS_INTERCOM_SIGNAL_PDU_TYPE 31u
#define FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE 32u
#define FASTDIS_INTERCOM_CONTROL_PDU_TYPE 32u
#define FASTDIS_INTERCOM_CONTROL_FIXED_SIZE 37u
#define FASTDIS_AGGREGATE_STATE_PDU_TYPE 33u
#define FASTDIS_AGGREGATE_STATE_FIXED_SIZE 132u
#define FASTDIS_IS_GROUP_OF_PDU_TYPE 34u
#define FASTDIS_IS_GROUP_OF_FIXED_SIZE 40u
#define FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE 35u
#define FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE 37u
#define FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE 35u
#define FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE 37u
#define FASTDIS_IS_PART_OF_PDU_TYPE 36u
#define FASTDIS_IS_PART_OF_FIXED_SIZE 52u
#define FASTDIS_MINEFIELD_STATE_PDU_TYPE 37u
#define FASTDIS_MINEFIELD_STATE_FIXED_SIZE 72u
#define FASTDIS_MINEFIELD_QUERY_PDU_TYPE 38u
#define FASTDIS_MINEFIELD_QUERY_FIXED_SIZE 40u
#define FASTDIS_MINEFIELD_DATA_PDU_TYPE 39u
#define FASTDIS_MINEFIELD_DATA_FIXED_SIZE 44u
#define FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE 40u
#define FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE 26u
#define FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE 41u
#define FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE 31u
#define FASTDIS_GRIDDED_DATA_PDU_TYPE 42u
#define FASTDIS_GRIDDED_DATA_FIXED_SIZE 64u
#define FASTDIS_POINT_OBJECT_STATE_PDU_TYPE 43u
#define FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE 90u
#define FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE 88u
#define FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE 44u
#define FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE 42u
#define FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE 40u
#define FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE 55u
#define FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE 64u
#define FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE 45u
#define FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE 52u
#define FASTDIS_TSPI_PDU_TYPE 46u
#define FASTDIS_TSPI_FIXED_SIZE 56u
#define FASTDIS_APPEARANCE_PDU_TYPE 47u
#define FASTDIS_APPEARANCE_FIXED_SIZE 56u
#define FASTDIS_ARTICULATED_PARTS_PDU_TYPE 48u
#define FASTDIS_ARTICULATED_PARTS_FIXED_SIZE 20u
#define FASTDIS_LE_FIRE_PDU_TYPE 49u
#define FASTDIS_LE_FIRE_FIXED_SIZE 60u
#define FASTDIS_LE_DETONATION_PDU_TYPE 50u
#define FASTDIS_LE_DETONATION_FIXED_SIZE 72u
#define FASTDIS_SERVICE_REQUEST_PDU_TYPE 5u
#define FASTDIS_SERVICE_REQUEST_FIXED_SIZE 28u
#define FASTDIS_RESUPPLY_OFFER_PDU_TYPE 6u
#define FASTDIS_RESUPPLY_OFFER_FIXED_SIZE 28u
#define FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE 7u
#define FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE 28u
#define FASTDIS_RESUPPLY_CANCEL_PDU_TYPE 8u
#define FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE 24u
#define FASTDIS_REPAIR_COMPLETE_PDU_TYPE 9u
#define FASTDIS_REPAIR_COMPLETE_FIXED_SIZE 28u
#define FASTDIS_REPAIR_RESPONSE_PDU_TYPE 10u
#define FASTDIS_REPAIR_RESPONSE_FIXED_SIZE 28u
#define FASTDIS_CREATE_ENTITY_PDU_TYPE 11u
#define FASTDIS_CREATE_ENTITY_FIXED_SIZE 28u
#define FASTDIS_REMOVE_ENTITY_PDU_TYPE 12u
#define FASTDIS_REMOVE_ENTITY_FIXED_SIZE 28u
#define FASTDIS_START_RESUME_PDU_TYPE 13u
#define FASTDIS_START_RESUME_FIXED_SIZE 44u
#define FASTDIS_STOP_FREEZE_PDU_TYPE 14u
#define FASTDIS_STOP_FREEZE_FIXED_SIZE 40u
#define FASTDIS_ACKNOWLEDGE_PDU_TYPE 15u
#define FASTDIS_ACKNOWLEDGE_FIXED_SIZE 30u
#define FASTDIS_ACTION_REQUEST_PDU_TYPE 16u
#define FASTDIS_ACTION_REQUEST_FIXED_SIZE 40u
#define FASTDIS_ACTION_RESPONSE_PDU_TYPE 17u
#define FASTDIS_ACTION_RESPONSE_FIXED_SIZE 40u
#define FASTDIS_DATA_QUERY_PDU_TYPE 18u
#define FASTDIS_DATA_QUERY_FIXED_SIZE 44u
#define FASTDIS_SET_DATA_PDU_TYPE 19u
#define FASTDIS_SET_DATA_FIXED_SIZE 40u
#define FASTDIS_DATA_PDU_TYPE 20u
#define FASTDIS_DATA_FIXED_SIZE 40u
#define FASTDIS_EVENT_REPORT_PDU_TYPE 21u
#define FASTDIS_EVENT_REPORT_FIXED_SIZE 40u
#define FASTDIS_COMMENT_PDU_TYPE 22u
#define FASTDIS_COMMENT_FIXED_SIZE 32u
#define FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE 51u
#define FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE 32u
#define FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE 52u
#define FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE 32u
#define FASTDIS_START_RESUME_RELIABLE_PDU_TYPE 53u
#define FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE 48u
#define FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE 54u
#define FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE 36u
#define FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE 55u
#define FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE 30u
#define FASTDIS_ACTION_REQUEST_RELIABLE_PDU_TYPE 56u
#define FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE 44u
#define FASTDIS_ACTION_RESPONSE_RELIABLE_PDU_TYPE 57u
#define FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE 40u
#define FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE 58u
#define FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE 48u
#define FASTDIS_SET_DATA_RELIABLE_PDU_TYPE 59u
#define FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE 40u
#define FASTDIS_DATA_RELIABLE_PDU_TYPE 60u
#define FASTDIS_DATA_RELIABLE_FIXED_SIZE 40u
#define FASTDIS_EVENT_REPORT_RELIABLE_PDU_TYPE 61u
#define FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE 40u
#define FASTDIS_COMMENT_RELIABLE_PDU_TYPE 62u
#define FASTDIS_COMMENT_RELIABLE_FIXED_SIZE 32u
#define FASTDIS_RECORD_RELIABLE_PDU_TYPE 63u
#define FASTDIS_RECORD_RELIABLE_FIXED_SIZE 36u
#define FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE 64u
#define FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE 40u
#define FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE 65u
#define FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE 42u
#define FASTDIS_COLLISION_ELASTIC_PDU_TYPE 66u
#define FASTDIS_COLLISION_ELASTIC_FIXED_SIZE 100u
#define FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE 67u
#define FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE 72u
#define FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE 68u
#define FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE 90u
#define FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE 69u
#define FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE 36u
#define FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE 70u
#define FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE 56u
#define FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE 71u
#define FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE 40u
#define FASTDIS_ATTRIBUTE_PDU_TYPE 72u
#define FASTDIS_ATTRIBUTE_FIXED_SIZE 32u

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
#define FASTDIS_ENTITY_CHANGE_EXTRAPOLATED 0x00000020u

/* DIS Entity State dead-reckoning algorithm values. */
#define FASTDIS_DR_OTHER 0u
#define FASTDIS_DR_STATIC 1u
#define FASTDIS_DR_FPW 2u
#define FASTDIS_DR_RPW 3u
#define FASTDIS_DR_RVW 4u
#define FASTDIS_DR_FVW 5u
#define FASTDIS_DR_FPB 6u
#define FASTDIS_DR_RPB 7u
#define FASTDIS_DR_RVB 8u
#define FASTDIS_DR_FVB 9u

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

typedef struct fastdis_live_entity_id_s {
    uint8_t site;
    uint8_t application;
    uint16_t entity;
} fastdis_live_entity_id_t;

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

typedef struct fastdis_clock_time_s {
    uint32_t hour;
    uint32_t time_past_hour;
} fastdis_clock_time_t;

typedef struct fastdis_event_id_s {
    uint16_t site;
    uint16_t application;
    uint16_t event_number;
} fastdis_event_id_t;

typedef struct fastdis_live_event_id_s {
    uint8_t site;
    uint8_t application;
    uint16_t event_number;
} fastdis_live_event_id_t;

typedef struct fastdis_simulation_address_s {
    uint16_t site;
    uint16_t application;
} fastdis_simulation_address_t;

typedef struct fastdis_radio_entity_type_s {
    uint8_t entity_kind;
    uint8_t domain;
    uint16_t country;
    uint8_t category;
    uint8_t nomenclature_version;
    uint16_t nomenclature;
} fastdis_radio_entity_type_t;

typedef struct fastdis_modulation_type_s {
    uint16_t spread_spectrum;
    uint16_t major;
    uint16_t detail;
    uint16_t system;
} fastdis_modulation_type_t;

typedef struct fastdis_system_id_s {
    uint16_t system_type;
    uint16_t system_name;
    uint8_t system_mode;
    uint8_t change_options;
} fastdis_system_id_t;

typedef struct fastdis_iff_fundamental_data_s {
    uint8_t system_status;
    uint8_t alternate_parameter4;
    uint8_t information_layers;
    uint8_t modifier;
    uint16_t parameter1;
    uint16_t parameter2;
    uint16_t parameter3;
    uint16_t parameter4;
    uint16_t parameter5;
    uint16_t parameter6;
} fastdis_iff_fundamental_data_t;

typedef struct fastdis_burst_descriptor_s {
    fastdis_entity_type_t munition_type;
    uint16_t warhead;
    uint16_t fuse;
    uint16_t quantity;
    uint16_t rate;
} fastdis_burst_descriptor_t;

typedef struct fastdis_relationship_s {
    uint16_t nature;
    uint16_t position;
} fastdis_relationship_t;

typedef struct fastdis_named_location_s {
    uint16_t station_name;
    uint16_t station_number;
} fastdis_named_location_t;

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
    uint8_t dead_reckoning_algorithm;
    uint8_t dead_reckoning_parameters[15];
    fastdis_vec3f_t dead_reckoning_linear_acceleration;
    fastdis_vec3f_t dead_reckoning_angular_velocity;
} fastdis_entity_transform_t;

typedef struct fastdis_entity_transform_batch_s {
    fastdis_entity_transform_t* transforms;
    size_t capacity;
    size_t count;
    size_t dropped;
} fastdis_entity_transform_batch_t;

typedef struct fastdis_datum_record_set_view_s {
    const uint8_t* datum_record_bytes;
    size_t datum_record_bytes_size;
    void* datum_record_bytes_user;
    uint32_t number_of_fixed_datum_records;
    uint32_t number_of_variable_datum_records;
} fastdis_datum_record_set_view_t;

typedef struct fastdis_counted_bytes_view_s {
    const uint8_t* bytes;
    size_t bytes_size;
    void* bytes_user;
    uint32_t count;
} fastdis_counted_bytes_view_t;

typedef struct fastdis_signal_s {
    fastdis_header_t header;
    fastdis_entity_id_t entity_id;
    uint16_t radio_id;
    uint16_t encoding_scheme;
    uint16_t tdl_type;
    uint32_t sample_rate;
    uint16_t data_length;
    uint16_t samples;
    fastdis_counted_bytes_view_t data;
} fastdis_signal_t;

typedef struct fastdis_receiver_s {
    fastdis_header_t header;
    fastdis_entity_id_t entity_id;
    uint16_t radio_id;
    uint16_t receiver_state;
    uint16_t padding1;
    float received_power;
    fastdis_entity_id_t transmitter_entity_id;
    uint16_t transmitter_radio_id;
} fastdis_receiver_t;

typedef struct fastdis_intercom_signal_s {
    fastdis_header_t header;
    fastdis_entity_id_t entity_id;
    uint16_t communications_device_id;
    uint16_t encoding_scheme;
    uint16_t tdl_type;
    uint32_t sample_rate;
    uint16_t data_length;
    uint16_t samples;
    fastdis_counted_bytes_view_t data;
} fastdis_intercom_signal_t;

typedef struct fastdis_designator_s {
    fastdis_header_t header;
    fastdis_entity_id_t designating_entity_id;
    uint16_t code_name;
    fastdis_entity_id_t designated_entity_id;
    uint16_t designator_code;
    float designator_power;
    float designator_wavelength;
    fastdis_vec3f_t designator_spot_wrt_designated;
    fastdis_world_coordinates_t designator_spot_location;
    uint8_t dead_reckoning_algorithm;
    uint16_t padding1;
    uint8_t padding2;
    fastdis_vec3f_t entity_linear_acceleration;
} fastdis_designator_t;

typedef struct fastdis_transmitter_s {
    fastdis_header_t header;
    fastdis_entity_id_t entity_id;
    uint16_t radio_id;
    fastdis_radio_entity_type_t radio_entity_type;
    fastdis_entity_type_t entity_type;
    uint8_t transmit_state;
    uint8_t input_source;
    uint16_t variable_transmitter_parameter_count;
    fastdis_world_coordinates_t antenna_location;
    fastdis_vec3f_t relative_antenna_location;
    uint16_t antenna_pattern_type;
    uint16_t antenna_pattern_count;
    uint32_t frequency;
    float transmit_frequency_bandwidth;
    float power;
    fastdis_modulation_type_t modulation_type;
    uint16_t crypto_system;
    uint16_t crypto_key_id;
    uint8_t modulation_parameter_count;
    uint16_t padding2;
    uint8_t padding3;
    fastdis_counted_bytes_view_t modulation_parameters;
    fastdis_counted_bytes_view_t antenna_patterns;
} fastdis_transmitter_t;

typedef struct fastdis_other_pdu_s {
    fastdis_header_t header;
    fastdis_counted_bytes_view_t opaque_payload;
} fastdis_other_pdu_t;

typedef struct fastdis_aggregate_state_s {
    fastdis_header_t header;
    fastdis_entity_id_t aggregate_id;
    uint8_t force_id;
    uint8_t aggregate_state;
    fastdis_entity_type_t aggregate_type;
    uint32_t formation;
    uint8_t aggregate_marking_character_set;
    uint8_t aggregate_marking[32];
    fastdis_vec3f_t dimensions;
    fastdis_euler_angles_t orientation;
    fastdis_world_coordinates_t center_of_mass;
    fastdis_vec3f_t velocity;
    uint16_t number_of_dis_aggregates;
    uint16_t number_of_dis_entities;
    uint16_t number_of_silent_aggregate_types;
    uint16_t number_of_silent_entity_types;
    fastdis_counted_bytes_view_t aggregate_records;
} fastdis_aggregate_state_t;

typedef struct fastdis_is_group_of_s {
    fastdis_header_t header;
    fastdis_entity_id_t group_entity_id;
    uint8_t grouped_entity_category;
    uint8_t number_of_grouped_entities;
    uint32_t pad2;
    double latitude;
    double longitude;
    fastdis_counted_bytes_view_t grouped_entity_descriptions;
} fastdis_is_group_of_t;

typedef struct fastdis_transfer_control_request_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint8_t transfer_type;
    fastdis_entity_id_t transfer_entity_id;
    uint8_t number_of_record_sets;
    fastdis_counted_bytes_view_t record_sets;
} fastdis_transfer_control_request_t;

typedef struct fastdis_transfer_ownership_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint8_t transfer_type;
    fastdis_entity_id_t transfer_entity_id;
    uint8_t number_of_record_sets;
    fastdis_counted_bytes_view_t record_sets;
} fastdis_transfer_ownership_t;

typedef struct fastdis_is_part_of_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_relationship_t relationship;
    fastdis_vec3f_t part_location;
    fastdis_named_location_t named_location;
    fastdis_entity_type_t part_entity_type;
} fastdis_is_part_of_t;

typedef struct fastdis_minefield_state_s {
    fastdis_header_t header;
    fastdis_entity_id_t minefield_id;
    uint16_t minefield_sequence;
    uint8_t force_id;
    uint8_t number_of_perimeter_points;
    fastdis_entity_type_t minefield_type;
    uint16_t number_of_mine_types;
    fastdis_world_coordinates_t minefield_location;
    fastdis_euler_angles_t minefield_orientation;
    uint16_t appearance;
    uint16_t protocol_mode;
    fastdis_counted_bytes_view_t perimeter_points;
    fastdis_counted_bytes_view_t mine_types;
} fastdis_minefield_state_t;

typedef struct fastdis_minefield_query_s {
    fastdis_header_t header;
    fastdis_entity_id_t minefield_id;
    fastdis_entity_id_t requesting_entity_id;
    uint8_t request_id;
    uint8_t number_of_perimeter_points;
    uint8_t pad2;
    uint8_t number_of_sensor_types;
    uint32_t data_filter;
    fastdis_entity_type_t requested_mine_type;
    fastdis_counted_bytes_view_t requested_perimeter_points;
    fastdis_counted_bytes_view_t sensor_types;
} fastdis_minefield_query_t;

typedef struct fastdis_minefield_data_s {
    fastdis_header_t header;
    fastdis_entity_id_t minefield_id;
    fastdis_entity_id_t requesting_entity_id;
    uint16_t minefield_sequence_number;
    uint8_t request_id;
    uint8_t pdu_sequence_number;
    uint8_t number_of_pdus;
    uint8_t number_of_mines_in_this_pdu;
    uint8_t number_of_sensor_types;
    uint8_t pad2;
    uint32_t data_filter;
    fastdis_entity_type_t mine_type;
    uint8_t pad3;
    fastdis_counted_bytes_view_t sensor_types;
    fastdis_counted_bytes_view_t mine_locations;
} fastdis_minefield_data_t;

typedef struct fastdis_minefield_response_nack_s {
    fastdis_header_t header;
    fastdis_entity_id_t minefield_id;
    fastdis_entity_id_t requesting_entity_id;
    uint8_t request_id;
    uint8_t number_of_missing_pdus;
    fastdis_counted_bytes_view_t missing_pdu_sequence_numbers;
} fastdis_minefield_response_nack_t;

typedef struct fastdis_environment_object_type_s {
    uint8_t domain;
    uint8_t kind;
    uint16_t country;
    uint8_t category;
    uint8_t subcategory;
} fastdis_environment_object_type_t;

typedef struct fastdis_environmental_process_s {
    fastdis_header_t header;
    fastdis_entity_id_t environmental_process_id;
    fastdis_entity_type_t environment_type;
    uint8_t model_type;
    uint8_t environment_status;
    uint8_t number_of_environment_records;
    uint16_t sequence_number;
    fastdis_counted_bytes_view_t environment_records;
} fastdis_environmental_process_t;

typedef struct fastdis_gridded_data_s {
    fastdis_header_t header;
    fastdis_entity_id_t environmental_simulation_application_id;
    uint16_t field_number;
    uint16_t pdu_number;
    uint16_t pdu_total;
    uint16_t coordinate_system;
    uint8_t number_of_grid_axes;
    uint8_t constant_grid;
    fastdis_entity_type_t environment_type;
    fastdis_euler_angles_t orientation;
    uint64_t sample_time;
    uint32_t total_values;
    uint8_t vector_dimension;
    uint16_t padding1;
    uint8_t padding2;
    fastdis_counted_bytes_view_t grid_data;
} fastdis_gridded_data_t;

typedef struct fastdis_point_object_state_s {
    fastdis_header_t header;
    fastdis_entity_id_t object_id;
    fastdis_entity_id_t referenced_object_id;
    uint16_t update_number;
    uint8_t force_id;
    uint8_t modifications;
    fastdis_environment_object_type_t object_type;
    fastdis_world_coordinates_t object_location;
    fastdis_euler_angles_t object_orientation;
    double object_appearance;
    fastdis_simulation_address_t requester_id;
    fastdis_simulation_address_t receiving_id;
    uint32_t pad2;
} fastdis_point_object_state_t;

typedef struct fastdis_linear_object_state_s {
    fastdis_header_t header;
    fastdis_entity_id_t object_id;
    fastdis_entity_id_t referenced_object_id;
    uint16_t update_number;
    uint8_t force_id;
    uint8_t number_of_segments;
    fastdis_simulation_address_t requester_id;
    fastdis_simulation_address_t receiving_id;
    fastdis_environment_object_type_t object_type;
    fastdis_counted_bytes_view_t linear_segment_parameters;
} fastdis_linear_object_state_t;

typedef struct fastdis_areal_object_state_s {
    fastdis_header_t header;
    fastdis_entity_id_t object_id;
    fastdis_entity_id_t referenced_object_id;
    uint16_t update_number;
    uint8_t force_id;
    uint8_t modifications;
    fastdis_entity_type_t object_type;
    fastdis_counted_bytes_view_t object_appearance;
    uint16_t number_of_points;
    fastdis_simulation_address_t requester_id;
    fastdis_simulation_address_t receiving_id;
    fastdis_counted_bytes_view_t object_locations;
} fastdis_areal_object_state_t;

typedef struct fastdis_tspi_s {
    fastdis_header_t header;
    fastdis_live_entity_id_t live_entity_id;
    uint8_t tspi_flag;
    fastdis_counted_bytes_view_t entity_location;
    fastdis_counted_bytes_view_t entity_linear_velocity;
    fastdis_counted_bytes_view_t entity_orientation;
    fastdis_counted_bytes_view_t position_error;
    fastdis_counted_bytes_view_t orientation_error;
    fastdis_counted_bytes_view_t dead_reckoning_parameters;
    uint16_t measured_speed;
    uint8_t system_specific_data_length;
    fastdis_counted_bytes_view_t system_specific_data;
} fastdis_tspi_t;

typedef struct fastdis_live_entity_appearance_s {
    fastdis_header_t header;
    fastdis_live_entity_id_t live_entity_id;
    uint16_t appearance_flags;
    uint8_t force_id;
    uint8_t padding1;
    fastdis_entity_type_t entity_type;
    fastdis_entity_type_t alternate_entity_type;
    uint8_t entity_marking[12];
    uint32_t capabilities;
    fastdis_counted_bytes_view_t appearance_fields;
} fastdis_live_entity_appearance_t;

typedef struct fastdis_articulated_parts_s {
    fastdis_header_t header;
    fastdis_live_entity_id_t live_entity_id;
    uint8_t number_of_parameter_records;
    uint8_t padding[3];
    fastdis_counted_bytes_view_t variable_parameters;
} fastdis_articulated_parts_t;

typedef struct fastdis_le_fire_s {
    fastdis_header_t header;
    fastdis_live_entity_id_t firing_live_entity_id;
    uint8_t flags;
    uint8_t padding1;
    fastdis_live_entity_id_t target_live_entity_id;
    fastdis_live_entity_id_t munition_live_entity_id;
    fastdis_live_event_id_t event_id;
    fastdis_counted_bytes_view_t location;
    fastdis_burst_descriptor_t munition_descriptor;
    fastdis_counted_bytes_view_t velocity;
    uint16_t range;
} fastdis_le_fire_t;

typedef struct fastdis_le_detonation_s {
    fastdis_header_t header;
    fastdis_live_entity_id_t firing_live_entity_id;
    uint8_t detonation_flag1;
    uint8_t detonation_flag2;
    fastdis_live_entity_id_t target_live_entity_id;
    fastdis_live_entity_id_t munition_live_entity_id;
    fastdis_live_event_id_t event_id;
    fastdis_counted_bytes_view_t world_location;
    fastdis_counted_bytes_view_t velocity;
    fastdis_counted_bytes_view_t munition_orientation;
    fastdis_burst_descriptor_t munition_descriptor;
    fastdis_counted_bytes_view_t entity_location;
    uint8_t detonation_result;
    uint8_t padding1;
} fastdis_le_detonation_t;

typedef struct fastdis_electronic_emissions_s {
    fastdis_header_t header;
    fastdis_entity_id_t emitting_entity_id;
    fastdis_event_id_t event_id;
    uint8_t state_update_indicator;
    uint8_t number_of_systems;
    uint16_t padding1;
    fastdis_counted_bytes_view_t system_records;
} fastdis_electronic_emissions_t;

typedef struct fastdis_iff_atc_navaids_layer1_s {
    fastdis_header_t header;
    fastdis_entity_id_t emitting_entity_id;
    fastdis_event_id_t event_id;
    fastdis_vec3f_t location;
    fastdis_system_id_t system_id;
    uint16_t padding2;
    fastdis_iff_fundamental_data_t fundamental_parameters;
} fastdis_iff_atc_navaids_layer1_t;

typedef struct fastdis_iff_s {
    fastdis_header_t header;
    fastdis_entity_id_t emitting_entity_id;
    fastdis_event_id_t event_id;
    fastdis_vec3f_t location;
    fastdis_system_id_t system_id;
    uint16_t padding2;
    fastdis_iff_fundamental_data_t fundamental_parameters;
} fastdis_iff_t;

typedef struct fastdis_ua_s {
    fastdis_header_t header;
    fastdis_entity_id_t emitting_entity_id;
    fastdis_event_id_t event_id;
    int8_t state_change_indicator;
    uint8_t padding1;
    uint16_t passive_parameter_index;
    uint8_t propulsion_plant_configuration;
    uint8_t number_of_shafts;
    uint8_t number_of_apas;
    uint8_t number_of_ua_emitter_systems;
    fastdis_counted_bytes_view_t ua_records;
} fastdis_ua_t;

typedef struct fastdis_sees_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    uint16_t infrared_signature_representation_index;
    uint16_t acoustic_signature_representation_index;
    uint16_t radar_cross_section_signature_representation_index;
    uint16_t number_of_propulsion_systems;
    uint16_t number_of_vectoring_nozzle_systems;
    fastdis_counted_bytes_view_t supplemental_emission_records;
} fastdis_sees_t;

typedef struct fastdis_intercom_control_s {
    fastdis_header_t header;
    uint8_t control_type;
    uint8_t communications_channel_type;
    fastdis_entity_id_t source_entity_id;
    uint8_t source_communications_device_id;
    uint8_t source_line_id;
    uint8_t transmit_priority;
    uint8_t transmit_line_state;
    uint8_t command;
    fastdis_entity_id_t master_entity_id;
    uint16_t master_communications_device_id;
    uint32_t intercom_parameters_length;
    fastdis_counted_bytes_view_t intercom_parameters;
} fastdis_intercom_control_t;

typedef struct fastdis_attribute_s {
    fastdis_header_t header;
    fastdis_simulation_address_t originating_simulation_address;
    int32_t padding1;
    int16_t padding2;
    uint8_t attribute_record_pdu_type;
    uint8_t attribute_record_protocol_version;
    uint32_t master_attribute_record_type;
    uint8_t action_code;
    int8_t padding3;
    uint16_t number_attribute_record_set;
    fastdis_counted_bytes_view_t attribute_record_sets;
} fastdis_attribute_t;

typedef struct fastdis_directed_energy_fire_s {
    fastdis_header_t header;
    fastdis_entity_id_t firing_entity_id;
    fastdis_entity_id_t target_entity_id;
    fastdis_entity_type_t munition_type;
    fastdis_clock_time_t shot_start_time;
    float commulative_shot_time;
    fastdis_vec3f_t aperture_emitter_location;
    float aperture_diameter;
    float wavelength;
    float peak_irradiance;
    float pulse_repetition_frequency;
    int32_t pulse_width;
    int32_t flags;
    int8_t pulse_shape;
    uint8_t padding1;
    uint32_t padding2;
    uint16_t padding3;
    uint16_t number_of_de_records;
    fastdis_counted_bytes_view_t de_records;
} fastdis_directed_energy_fire_t;

typedef struct fastdis_entity_damage_status_s {
    fastdis_header_t header;
    fastdis_entity_id_t firing_entity_id;
    fastdis_entity_id_t target_entity_id;
    fastdis_entity_id_t damaged_entity_id;
    uint16_t padding1;
    uint16_t padding2;
    uint16_t number_of_damage_description;
    fastdis_counted_bytes_view_t damage_description_records;
} fastdis_entity_damage_status_t;

typedef struct fastdis_information_operations_action_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_sim_id;
    fastdis_entity_id_t receiving_sim_id;
    uint32_t request_id;
    uint16_t io_warfare_type;
    uint16_t io_simulation_source;
    uint16_t io_action_type;
    uint16_t io_action_phase;
    uint32_t padding1;
    fastdis_entity_id_t io_attacker_id;
    fastdis_entity_id_t io_primary_target_id;
    uint16_t padding2;
    uint16_t number_of_io_records;
    fastdis_counted_bytes_view_t io_records;
} fastdis_information_operations_action_t;

typedef struct fastdis_information_operations_report_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_sim_id;
    uint16_t io_sim_source;
    uint8_t io_report_type;
    uint8_t padding1;
    fastdis_entity_id_t io_attacker_id;
    fastdis_entity_id_t io_primary_target_id;
    uint16_t padding2;
    uint16_t padding3;
    uint16_t number_of_io_records;
    fastdis_counted_bytes_view_t io_records;
} fastdis_information_operations_report_t;

typedef struct fastdis_simulation_management_request_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
} fastdis_simulation_management_request_t;

typedef struct fastdis_start_resume_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_clock_time_t real_world_time;
    fastdis_clock_time_t simulation_time;
    uint32_t request_id;
} fastdis_start_resume_t;

typedef struct fastdis_stop_freeze_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_clock_time_t real_world_time;
    uint8_t reason;
    uint8_t frozen_behavior;
    uint16_t padding1;
    uint32_t request_id;
} fastdis_stop_freeze_t;

typedef struct fastdis_acknowledge_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint16_t acknowledge_flag;
    uint16_t response_flag;
    uint32_t request_id;
} fastdis_acknowledge_t;

typedef struct fastdis_simulation_management_reliable_request_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint32_t request_id;
} fastdis_simulation_management_reliable_request_t;

typedef struct fastdis_start_resume_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_clock_time_t real_world_time;
    fastdis_clock_time_t simulation_time;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint32_t request_id;
} fastdis_start_resume_reliable_t;

typedef struct fastdis_stop_freeze_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_clock_time_t real_world_time;
    uint8_t reason;
    uint8_t frozen_behavior;
    uint8_t required_reliablity_service;
    uint8_t pad1;
    uint32_t request_id;
} fastdis_stop_freeze_reliable_t;

typedef struct fastdis_action_request_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint32_t action_id;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_action_request_t;

typedef struct fastdis_action_response_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint32_t request_status;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_action_response_t;

typedef struct fastdis_data_query_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    fastdis_clock_time_t time_interval;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_data_query_t;

typedef struct fastdis_set_data_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint32_t padding1;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_set_data_t;

typedef struct fastdis_event_report_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t event_type;
    uint32_t padding1;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_event_report_t;

typedef struct fastdis_comment_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_comment_t;

typedef struct fastdis_action_request_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint32_t request_id;
    uint32_t action_id;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_action_request_reliable_t;

typedef struct fastdis_action_response_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint32_t response_status;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_action_response_reliable_t;

typedef struct fastdis_data_query_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint32_t request_id;
    fastdis_clock_time_t time_interval;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_data_query_reliable_t;

typedef struct fastdis_set_data_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint32_t request_id;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_set_data_reliable_t;

typedef struct fastdis_data_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_data_reliable_t;

typedef struct fastdis_event_report_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t event_type;
    uint32_t pad1;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_event_report_reliable_t;

typedef struct fastdis_comment_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_datum_record_set_view_t datum_records;
} fastdis_comment_reliable_t;

typedef struct fastdis_service_request_s {
    fastdis_header_t header;
    fastdis_entity_id_t requesting_entity_id;
    fastdis_entity_id_t servicing_entity_id;
    uint8_t service_type_requested;
    uint8_t number_of_supply_types;
    int16_t service_request_padding;
    fastdis_counted_bytes_view_t supplies;
} fastdis_service_request_t;

typedef struct fastdis_resupply_offer_s {
    fastdis_header_t header;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_entity_id_t supplying_entity_id;
    uint8_t number_of_supply_types;
    uint8_t padding_bytes[3];
    fastdis_counted_bytes_view_t supplies;
} fastdis_resupply_offer_t;

typedef struct fastdis_resupply_received_s {
    fastdis_header_t header;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_entity_id_t supplying_entity_id;
    uint8_t number_of_supply_types;
    uint16_t padding1;
    uint8_t padding2;
    fastdis_counted_bytes_view_t supplies;
} fastdis_resupply_received_t;

typedef struct fastdis_resupply_cancel_s {
    fastdis_header_t header;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_entity_id_t supplying_entity_id;
} fastdis_resupply_cancel_t;

typedef struct fastdis_repair_complete_s {
    fastdis_header_t header;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_entity_id_t repairing_entity_id;
    uint16_t repair;
    int16_t padding2;
} fastdis_repair_complete_t;

typedef struct fastdis_repair_response_s {
    fastdis_header_t header;
    fastdis_entity_id_t receiving_entity_id;
    fastdis_entity_id_t repairing_entity_id;
    uint8_t repair_result;
    uint16_t padding1;
    uint8_t padding2;
} fastdis_repair_response_t;

typedef struct fastdis_record_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint8_t pad1;
    uint16_t event_type;
    fastdis_counted_bytes_view_t record_sets;
} fastdis_record_reliable_t;

typedef struct fastdis_set_record_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    fastdis_counted_bytes_view_t record_sets;
} fastdis_set_record_reliable_t;

typedef struct fastdis_record_query_reliable_s {
    fastdis_header_t header;
    fastdis_entity_id_t originating_entity_id;
    fastdis_entity_id_t receiving_entity_id;
    uint32_t request_id;
    uint8_t required_reliability_service;
    uint16_t pad1;
    uint8_t pad2;
    uint16_t event_type;
    uint32_t time;
    fastdis_counted_bytes_view_t record_ids;
} fastdis_record_query_reliable_t;

typedef struct fastdis_fire_s {
    fastdis_header_t header;
    fastdis_entity_id_t firing_entity_id;
    fastdis_entity_id_t target_entity_id;
    fastdis_entity_id_t munition_entity_id;
    fastdis_event_id_t event_id;
    uint32_t fire_mission_index;
    fastdis_world_coordinates_t world_location;
    fastdis_burst_descriptor_t munition_descriptor;
    fastdis_vec3f_t velocity;
    float range_to_target;
} fastdis_fire_t;

typedef struct fastdis_detonation_s {
    fastdis_header_t header;
    fastdis_entity_id_t firing_entity_id;
    fastdis_entity_id_t target_entity_id;
    fastdis_entity_id_t exploding_entity_id;
    fastdis_event_id_t event_id;
    fastdis_vec3f_t velocity;
    fastdis_world_coordinates_t world_location;
    fastdis_burst_descriptor_t munition_descriptor;
    fastdis_vec3f_t location_in_entity_coordinates;
    uint8_t detonation_result;
    uint8_t variable_parameter_count;
    uint16_t padding1;
} fastdis_detonation_t;

typedef struct fastdis_collision_s {
    fastdis_header_t header;
    fastdis_entity_id_t issuing_entity_id;
    fastdis_entity_id_t colliding_entity_id;
    fastdis_event_id_t event_id;
    uint8_t collision_type;
    uint8_t padding1;
    fastdis_vec3f_t velocity;
    float mass;
    fastdis_vec3f_t location;
} fastdis_collision_t;

typedef struct fastdis_collision_elastic_s {
    fastdis_header_t header;
    fastdis_entity_id_t issuing_entity_id;
    fastdis_entity_id_t colliding_entity_id;
    fastdis_event_id_t event_id;
    uint16_t padding1;
    fastdis_vec3f_t contact_velocity;
    float mass;
    fastdis_vec3f_t location;
    float collision_result_xx;
    float collision_result_xy;
    float collision_result_xz;
    float collision_result_yy;
    float collision_result_yz;
    float collision_result_zz;
    fastdis_vec3f_t unit_surface_normal;
    float coefficient_of_restitution;
} fastdis_collision_elastic_t;

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
FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_epoch(void);
FASTDIS_API uint32_t FASTDIS_CALL fastdis_abi_revision(void);
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

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_fire(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_fire_t* out_fire);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_detonation(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_detonation_t* out_detonation);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_collision(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_collision_t* out_collision);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_collision_elastic(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_collision_elastic_t* out_collision);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_directed_energy_fire(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_directed_energy_fire_t* out_fire);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_entity_damage_status(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_entity_damage_status_t* out_status);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_designator(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_designator_t* out_designator);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transmitter(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_transmitter_t* out_transmitter);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_other_pdu(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_other_pdu_t* out_other);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_aggregate_state(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_aggregate_state_t* out_aggregate);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_is_group_of(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_is_group_of_t* out_group);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transfer_control_request(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_transfer_control_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_transfer_ownership(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_transfer_ownership_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_is_part_of(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_is_part_of_t* out_part);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_state(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_state_t* out_state);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_query(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_query_t* out_query);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_data(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_data_t* out_data);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_minefield_response_nack(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_minefield_response_nack_t* out_nack);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_environmental_process(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_environmental_process_t* out_process);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_gridded_data(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_gridded_data_t* out_grid);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_point_object_state(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_point_object_state_t* out_point);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_linear_object_state(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_linear_object_state_t* out_linear);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_areal_object_state(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_areal_object_state_t* out_areal);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_tspi(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_tspi_t* out_tspi);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_live_entity_appearance(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_live_entity_appearance_t* out_appearance);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_articulated_parts(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_articulated_parts_t* out_parts);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_le_fire(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_le_fire_t* out_fire);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_le_detonation(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_le_detonation_t* out_detonation);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_signal(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_signal_t* out_signal);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_receiver(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_receiver_t* out_receiver);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_electronic_emissions(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_electronic_emissions_t* out_emissions);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_iff_atc_navaids_layer1(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_iff_atc_navaids_layer1_t* out_iff);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_iff(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_iff_t* out_iff);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_ua(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_ua_t* out_ua);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_sees(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_sees_t* out_sees);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_intercom_signal(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_signal_t* out_signal);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_intercom_control(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_intercom_control_t* out_control);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_attribute(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_attribute_t* out_attribute);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_information_operations_action(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_action_t* out_action);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_information_operations_report(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_information_operations_report_t* out_report);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_create_entity(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_remove_entity(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_start_resume(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_stop_freeze(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_acknowledge(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_acknowledge_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_request(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_response(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_query(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_data(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_event_report(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_comment(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_comment_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_create_entity_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_reliable_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_remove_entity_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_simulation_management_reliable_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_start_resume_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_start_resume_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_stop_freeze_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_stop_freeze_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_acknowledge_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_acknowledge_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_request_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_action_request_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_action_response_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_action_response_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_query_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_data_query_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_data_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_set_data_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_data_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_data_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_event_report_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_event_report_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_comment_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_comment_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_service_request(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_service_request_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_offer(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_offer_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_received(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_received_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_resupply_cancel(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_resupply_cancel_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_repair_complete(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_repair_complete_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_repair_response(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_repair_response_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_record_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_record_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_set_record_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_set_record_reliable_t* out_request);

FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_parse_record_query_reliable(
    const uint8_t* data,
    size_t size,
    uint32_t flags,
    fastdis_record_query_reliable_t* out_request);

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

/* Linear predictive extrapolation.
 *
 * This first-stage extrapolator is intentionally conservative: it only advances
 * ECEF location by the retained linear velocity (`location += velocity * dt`)
 * and ORs FASTDIS_ENTITY_CHANGE_EXTRAPOLATED into the output. It does not yet
 * apply DIS algorithm-specific dead-reckoning acceleration/angular velocity.
 */
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_transform_linear(
    const fastdis_entity_transform_t* transform,
    double delta_seconds,
    fastdis_entity_transform_t* out_transform);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_snapshot_linear(
    const fastdis_entity_snapshot_t* snapshot,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_t* out_snapshot);
FASTDIS_API const char* FASTDIS_CALL fastdis_dead_reckoning_algorithm_name(uint8_t algorithm);
FASTDIS_API int FASTDIS_CALL fastdis_dead_reckoning_algorithm_known(uint8_t algorithm);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_transform_dead_reckoning(
    const fastdis_entity_transform_t* transform,
    double delta_seconds,
    fastdis_entity_transform_t* out_transform);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_extrapolate_entity_snapshot_dead_reckoning(
    const fastdis_entity_snapshot_t* snapshot,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_t* out_snapshot);

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
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest_extrapolated(
    fastdis_entity_snapshot_buffer_t* buffer,
    uint64_t target_tick,
    double seconds_per_tick,
    fastdis_entity_snapshot_batch_t* out_batch);
FASTDIS_API fastdis_status_t FASTDIS_CALL fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned(
    fastdis_entity_snapshot_buffer_t* buffer,
    uint64_t target_tick,
    double seconds_per_tick,
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
