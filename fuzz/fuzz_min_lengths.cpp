#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

void set_declared_length(std::vector<std::uint8_t>& bytes, std::uint16_t length) {
    if (bytes.size() < FASTDIS_HEADER_SIZE) {
        bytes.resize(FASTDIS_HEADER_SIZE, 0);
    }
    bytes[8] = static_cast<std::uint8_t>((length >> 8) & 0xffu);
    bytes[9] = static_cast<std::uint8_t>(length & 0xffu);
}

void exercise_case(const std::vector<std::uint8_t>& bytes) {
    fastdis_header_t header{};
    (void)fastdis_parse_header(bytes.data(), bytes.size(), 0, &header);
    (void)fastdis_parse_header(bytes.data(), bytes.size(), FASTDIS_FLAG_ALLOW_TRUNCATED, &header);

    fastdis_scan_config_t config{};
    fastdis_scan_config_init(&config);
    fastdis_scan_stats_t stats{};
    fastdis_scan_stats_init(&stats);
    (void)fastdis_scan_packet(bytes.data(), bytes.size(), &config, nullptr, nullptr, &stats);

    fastdis_packet_view_t packet{bytes.data(), bytes.size(), nullptr};
    fastdis_scan_stats_init(&stats);
    (void)fastdis_scan_packets(&packet, 1, &config, nullptr, nullptr, &stats);
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    std::vector<std::uint8_t> bytes;
    if (data != nullptr && size != 0) {
        bytes.assign(data, data + size);
    }
    if (bytes.size() < FASTDIS_HEADER_SIZE) {
        bytes.resize(FASTDIS_HEADER_SIZE, 0);
    }

    exercise_case(bytes);

    std::vector<std::uint8_t> too_small = bytes;
    set_declared_length(too_small, static_cast<std::uint16_t>(FASTDIS_HEADER_SIZE - 1u));
    exercise_case(too_small);

    std::vector<std::uint8_t> exact_header = bytes;
    set_declared_length(exact_header, static_cast<std::uint16_t>(FASTDIS_HEADER_SIZE));
    exercise_case(exact_header);

    std::vector<std::uint8_t> exact_size = bytes;
    const auto bounded_size = static_cast<std::uint16_t>(
        exact_size.size() > 0xffffu ? 0xffffu : static_cast<std::uint16_t>(exact_size.size()));
    set_declared_length(exact_size, bounded_size < FASTDIS_HEADER_SIZE ? FASTDIS_HEADER_SIZE : bounded_size);
    exercise_case(exact_size);

    std::vector<std::uint8_t> exceeds_buffer = bytes;
    const std::uint16_t longer = static_cast<std::uint16_t>(
        (exceeds_buffer.size() + 16u) > 0xffffu ? 0xffffu : (exceeds_buffer.size() + 16u));
    set_declared_length(exceeds_buffer, longer < FASTDIS_HEADER_SIZE ? FASTDIS_HEADER_SIZE : longer);
    exercise_case(exceeds_buffer);

    return 0;
}

#include "fuzz_standalone.hpp"
