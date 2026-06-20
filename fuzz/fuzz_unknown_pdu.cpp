#include "fastdis/fastdis.h"
#include "fastdis/fastdis_pdu_catalog.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

void exercise_unknown(std::uint8_t version, std::uint8_t family, const std::uint8_t* data, std::size_t size) {
    std::vector<std::uint8_t> bytes;
    if (data != nullptr && size != 0) {
        bytes.assign(data, data + size);
    }
    if (bytes.size() < FASTDIS_HEADER_SIZE) {
        bytes.resize(FASTDIS_HEADER_SIZE, 0);
    }
    bytes[0] = version;
    bytes[1] = 1u;
    bytes[2] = 250u;
    bytes[3] = family;
    bytes[8] = 0u;
    bytes[9] = FASTDIS_HEADER_SIZE;
    bytes[10] = 0u;
    bytes[11] = 0u;

    fastdis_header_t header{};
    (void)fastdis_parse_header(bytes.data(), bytes.size(), 0, &header);
    (void)fastdis_parse_header(bytes.data(), bytes.size(), FASTDIS_FLAG_ALLOW_TRUNCATED, &header);
    (void)fastdis_pdu_catalog_find(version, 250u);

    fastdis_scan_config_t config{};
    fastdis_scan_config_init(&config);
    fastdis_scan_stats_t stats{};
    fastdis_scan_stats_init(&stats);
    (void)fastdis_scan_packet(bytes.data(), bytes.size(), &config, nullptr, nullptr, &stats);
    (void)fastdis_parse_entity_state_prefix(bytes.data(), bytes.size(), FASTDIS_FLAG_ALLOW_TRUNCATED, nullptr);

    fastdis_entity_state_prefix_t entity{};
    (void)fastdis_parse_entity_state_fields(bytes.data(), bytes.size(), FASTDIS_FLAG_ALLOW_TRUNCATED, FASTDIS_ES_FIELD_ALL, &entity);
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    exercise_unknown(FASTDIS_PROTOCOL_VERSION_DIS6, 1u, data, size);
    exercise_unknown(FASTDIS_PROTOCOL_VERSION_DIS7, 13u, data, size);
    return 0;
}

#include "fuzz_standalone.hpp"
