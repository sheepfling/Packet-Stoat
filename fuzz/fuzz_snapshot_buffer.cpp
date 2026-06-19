#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>

namespace {

std::size_t bounded_value(std::uint8_t byte, std::size_t min_value, std::size_t span) {
    return min_value + (span == 0u ? 0u : (static_cast<std::size_t>(byte) % span));
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }

    fastdis_scan_config_t config{};
    fastdis_scan_config_init(&config);
    (void)fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_TRANSFORM);

    fastdis_scanner_t* scanner = fastdis_scanner_create(&config);
    fastdis_entity_table_t* table = fastdis_entity_table_create(bounded_value(size > 0 ? data[0] : 0u, 1u, 16u));
    if (scanner == nullptr || table == nullptr) {
        fastdis_scanner_destroy(scanner);
        fastdis_entity_table_destroy(table);
        return 0;
    }

    fastdis_packet_view_t packets[3]{};
    packets[0] = fastdis_packet_view_t{data, size, nullptr};
    std::size_t count = 1u;
    if (size > 1u) {
        const std::size_t split = size / 2u;
        packets[0] = fastdis_packet_view_t{data, split, nullptr};
        packets[1] = fastdis_packet_view_t{data + split, size - split, nullptr};
        count = 2u;
    }

    fastdis_entity_table_update_stats_t stats{};
    fastdis_entity_table_update_stats_init(&stats);
    (void)fastdis_entity_table_ingest_packets(table, scanner, packets, count, 1u, &stats);

    const std::size_t capacity = bounded_value(size > 1 ? data[1] : 0u, 0u, 16u);
    const std::size_t slots = bounded_value(size > 2 ? data[2] : 0u, 2u, 4u);
    fastdis_entity_snapshot_buffer_t* buffer = fastdis_entity_snapshot_buffer_create_ex(capacity, slots);
    if (buffer == nullptr) {
        fastdis_entity_table_destroy(table);
        fastdis_scanner_destroy(scanner);
        return 0;
    }

    fastdis_entity_snapshot_view_t view{};
    (void)fastdis_entity_snapshot_buffer_publish_all(buffer, table, &view);
    fastdis_entity_snapshot_view_t held{};
    (void)fastdis_entity_snapshot_buffer_acquire_latest(buffer, &held);
    (void)fastdis_entity_snapshot_buffer_publish_changed(buffer, table, 1u, &view);
    (void)fastdis_entity_snapshot_buffer_publish_stale(buffer, table, bounded_value(size > 3 ? data[3] : 0u, 0u, 8u), &view);
    (void)fastdis_entity_snapshot_buffer_publish_evict_stale(buffer, table, bounded_value(size > 4 ? data[4] : 0u, 0u, 8u), &view);

    fastdis_entity_snapshot_t snapshots[16]{};
    fastdis_entity_snapshot_batch_t batch{snapshots, 16u, 0u, 0u};
    (void)fastdis_entity_snapshot_buffer_copy_latest(buffer, &batch);

    fastdis_entity_snapshot_buffer_stats_t buffer_stats{};
    fastdis_entity_snapshot_buffer_stats_init(&buffer_stats);
    (void)fastdis_entity_snapshot_buffer_get_stats(buffer, &buffer_stats);
    (void)fastdis_entity_snapshot_buffer_resize(buffer, bounded_value(size > 5 ? data[5] : 0u, 0u, 16u));
    (void)fastdis_entity_snapshot_buffer_release(buffer, &held);
    (void)fastdis_entity_snapshot_buffer_reset_stats(buffer);
    (void)fastdis_entity_snapshot_buffer_get_stats(buffer, &buffer_stats);

    fastdis_entity_snapshot_buffer_destroy(buffer);
    fastdis_entity_table_destroy(table);
    fastdis_scanner_destroy(scanner);
    return 0;
}

#include "fuzz_standalone.hpp"
