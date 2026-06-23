#ifndef FASTDIS_SYMBOLS_H
#define FASTDIS_SYMBOLS_H

#include <stddef.h>
#include <stdint.h>

#include "fastdis/fastdis.h"

#ifdef __cplusplus
extern "C" {
#endif

#define FASTDIS_SYMBOLS_ABI_VERSION 1u

typedef struct fastdis_symbols_context_s fastdis_symbols_context_t;

typedef struct fastdis_symbols_descriptor_s {
    char standard[32];
    char sidc[32];
    char affiliation[32];
    char symbol_set[32];
    char entity_type[64];
    char label[128];
    char confidence[32];
    char rule_id[64];
    char unique_designation[64];
    char status[32];
    uint8_t has_heading_degrees;
    double heading_degrees;
    char atlas_key[128];
} fastdis_symbols_descriptor_t;

typedef struct fastdis_symbols_atlas_rect_s {
    uint32_t atlas_index;
    float u0;
    float v0;
    float u1;
    float v1;
    uint32_t width_px;
    uint32_t height_px;
} fastdis_symbols_atlas_rect_t;

uint32_t fastdis_symbols_abi_version(void);

fastdis_symbols_context_t* fastdis_symbols_create(void);
void fastdis_symbols_destroy(fastdis_symbols_context_t* context);

fastdis_status_t fastdis_symbols_resolve_from_entity_state(
    fastdis_symbols_context_t* context,
    const fastdis_entity_state_prefix_t* entity,
    fastdis_symbols_descriptor_t* out_descriptor);

fastdis_status_t fastdis_symbols_resolve_from_entity_type(
    fastdis_symbols_context_t* context,
    const fastdis_entity_type_t* entity_type,
    uint8_t force_id,
    fastdis_symbols_descriptor_t* out_descriptor);

fastdis_status_t fastdis_symbols_validate_sidc(
    const char* sidc,
    size_t sidc_size);

fastdis_status_t fastdis_symbols_lookup_atlas_rect(
    fastdis_symbols_context_t* context,
    const char* sidc,
    fastdis_symbols_atlas_rect_t* out_rect);

#ifdef __cplusplus
}
#endif

#endif
