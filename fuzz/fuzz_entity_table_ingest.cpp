#include "fastdis/fastdis.h"

#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) {
        return 0;
    }

    fastdis_scan_config_t config{};
    fastdis_scan_config_init(&config);
    (void)fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_TRANSFORM);

    fastdis_scanner_t* scanner = fastdis_scanner_create(&config);
    fastdis_entity_table_t* table = fastdis_entity_table_create(8);
    if (scanner == nullptr || table == nullptr) {
        fastdis_scanner_destroy(scanner);
        fastdis_entity_table_destroy(table);
        return 0;
    }

    fastdis_packet_view_t packet{data, size, nullptr};
    fastdis_entity_table_update_stats_t stats{};
    fastdis_entity_table_update_stats_init(&stats);
    (void)fastdis_entity_table_ingest_packets(table, scanner, &packet, 1, 1, &stats);

    fastdis_entity_snapshot_t snapshots[8]{};
    fastdis_entity_snapshot_batch_t batch{snapshots, 8, 0, 0};
    (void)fastdis_entity_table_snapshot_all(table, &batch);

    fastdis_entity_snapshot_buffer_t* buffer = fastdis_entity_snapshot_buffer_create_ex(8, 3);
    if (buffer != nullptr) {
        fastdis_entity_snapshot_view_t view{};
        (void)fastdis_entity_snapshot_buffer_publish_changed(buffer, table, 1, &view);
        (void)fastdis_entity_snapshot_buffer_publish_evict_stale(buffer, table, 1, &view);
        fastdis_entity_snapshot_buffer_destroy(buffer);
    }

    fastdis_entity_table_destroy(table);
    fastdis_scanner_destroy(scanner);
    return 0;
}

#include "fuzz_standalone.hpp"
