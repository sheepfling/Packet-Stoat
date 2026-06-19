#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }
    fastdis_entity_transform_t transform{};
    (void)fastdis_parse_entity_transform(data, size, 0, &transform);
    (void)fastdis_parse_entity_transform(data, size, FASTDIS_FLAG_ALLOW_TRUNCATED, &transform);

    fastdis_entity_state_prefix_t entity{};
    (void)fastdis_parse_entity_state_fields(
        data,
        size,
        FASTDIS_FLAG_ALLOW_TRUNCATED,
        FASTDIS_ES_FIELD_LOCATION | FASTDIS_ES_FIELD_ORIENTATION | FASTDIS_ES_FIELD_VARIABLE_PARAMETER_COUNT,
        &entity);
    return 0;
}

#include "fuzz_standalone.hpp"
