#include "fastdis/fastdis.h"
#include "fastdis/fastdis_pdu_catalog.h"

#include <cstddef>
#include <cstdint>
#include <vector>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }

    fastdis_header_t header{};
    const fastdis_status_t strict = fastdis_parse_header(data, size, 0, &header);
    const fastdis_status_t truncated = fastdis_parse_header(data, size, FASTDIS_FLAG_ALLOW_TRUNCATED, &header);
    (void)fastdis_status_string(strict);
    (void)fastdis_status_string(truncated);

    if (truncated == FASTDIS_OK) {
        (void)fastdis_pdu_catalog_find(header.version, header.pdu_type);

        fastdis_scan_config_t config{};
        fastdis_scan_config_init(&config);
        (void)fastdis_header_matches(&header, &config);

        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_VERSIONS);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_VERSIONS, header.version);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_PDU_TYPES);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_PDU_TYPES, header.pdu_type);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_PROTOCOL_FAMILIES);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_PROTOCOL_FAMILIES, header.protocol_family);
        (void)fastdis_header_matches(&header, &config);

        std::vector<std::uint8_t> unknown(data, data + size);
        if (unknown.size() < FASTDIS_HEADER_SIZE) {
            unknown.resize(FASTDIS_HEADER_SIZE, 0);
        }
        unknown[0] = header.version;
        unknown[1] = header.exercise_id;
        unknown[2] = 250u;
        unknown[3] = header.protocol_family;
        unknown[8] = 0;
        unknown[9] = FASTDIS_HEADER_SIZE;
        fastdis_header_t unknown_header{};
        if (fastdis_parse_header(unknown.data(), unknown.size(), FASTDIS_FLAG_ALLOW_TRUNCATED, &unknown_header) == FASTDIS_OK) {
            (void)fastdis_pdu_catalog_find(unknown_header.version, unknown_header.pdu_type);
            (void)fastdis_header_matches(&unknown_header, &config);
        }
    }

    return 0;
}

#include "fuzz_standalone.hpp"
