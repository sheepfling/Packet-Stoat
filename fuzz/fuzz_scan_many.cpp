#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>

namespace {

int FASTDIS_CALL noop_packet_callback(
    const fastdis_header_t*,
    const std::uint8_t*,
    std::size_t,
    void*,
    void*) {
    return 0;
}

void run_scan(
    const fastdis_packet_view_t* packets,
    std::size_t count,
    fastdis_scan_config_t* config) {
    fastdis_scan_stats_t stats{};
    fastdis_scan_stats_init(&stats);
    (void)fastdis_scan_packets(packets, count, config, nullptr, nullptr, &stats);
    fastdis_scan_stats_init(&stats);
    (void)fastdis_scan_packets(packets, count, config, noop_packet_callback, nullptr, &stats);
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }

    fastdis_packet_view_t packets[3]{};
    packets[0] = fastdis_packet_view_t{data, size, nullptr};

    fastdis_scan_config_t config{};
    fastdis_scan_config_init(&config);
    (void)fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_HEADER_COUNTING);
    run_scan(packets, 1, &config);

    if (size > 1) {
        const std::size_t mid = size / 2;
        packets[0] = fastdis_packet_view_t{data, mid, nullptr};
        packets[1] = fastdis_packet_view_t{data + mid, size - mid, nullptr};
        run_scan(packets, 2, &config);
    }

    fastdis_header_t header{};
    if (fastdis_parse_header(data, size, FASTDIS_FLAG_ALLOW_TRUNCATED, &header) == FASTDIS_OK) {
        fastdis_scan_config_init(&config);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_VERSIONS);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_VERSIONS, header.version);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_PDU_TYPES);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_PDU_TYPES, header.pdu_type);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_PROTOCOL_FAMILIES);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_PROTOCOL_FAMILIES, header.protocol_family);
        (void)fastdis_scan_config_filter_clear(&config, FASTDIS_FILTER_EXERCISE_IDS);
        (void)fastdis_scan_config_filter_allow(&config, FASTDIS_FILTER_EXERCISE_IDS, header.exercise_id);
        packets[0] = fastdis_packet_view_t{data, size, nullptr};
        run_scan(packets, 1, &config);
    }

    return 0;
}

#include "fuzz_standalone.hpp"
