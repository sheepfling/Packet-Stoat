#include "fastdis/fastdis.h"

#include <stdio.h>
#include <stdint.h>

/* Minimal sketch: wire this to your own UDP receive burst. */
static void apply_snapshot_view(const fastdis_entity_snapshot_view_t *view) {
    for (size_t i = 0; i < view->count; ++i) {
        const fastdis_entity_snapshot_t *s = &view->snapshots[i];
        printf("entity=(%u,%u,%u) loc=(%.3f,%.3f,%.3f) flags=0x%x\n",
               s->transform.entity_id.site,
               s->transform.entity_id.application,
               s->transform.entity_id.entity,
               s->transform.location.x,
               s->transform.location.y,
               s->transform.location.z,
               s->change_flags);
    }
}

int main(void) {
    fastdis_scan_config_t cfg;
    fastdis_scan_config_init(&cfg);
    fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

    fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
    fastdis_entity_table_t *table = fastdis_entity_table_create(4096);
    fastdis_entity_snapshot_buffer_t *snapshots = fastdis_entity_snapshot_buffer_create(4096);
    if (!scanner || !table || !snapshots) {
        fprintf(stderr, "could not create fastdis objects\n");
        fastdis_entity_snapshot_buffer_destroy(snapshots);
        fastdis_entity_table_destroy(table);
        fastdis_scanner_destroy(scanner);
        return 2;
    }

    /* Replace this empty burst with your engine/network packet array. */
    fastdis_packet_view_t *packets = NULL;
    size_t packet_count = 0;

    fastdis_entity_table_update_stats_t stats;
    fastdis_entity_snapshot_view_t published;
    fastdis_entity_table_update_stats_init(&stats);

    fastdis_status_t rc = fastdis_entity_table_ingest_packets_publish_changed(
        table,
        scanner,
        packets,
        packet_count,
        1,          /* advance table tick */
        1,          /* clear table change flags after publish */
        snapshots,
        &stats,
        &published);
    if (rc != FASTDIS_OK) {
        fprintf(stderr, "ingest/publish failed: %s\n", fastdis_status_string(rc));
        fastdis_entity_snapshot_buffer_destroy(snapshots);
        fastdis_entity_table_destroy(table);
        fastdis_scanner_destroy(scanner);
        return 2;
    }

    fastdis_entity_snapshot_view_t read_view;
    rc = fastdis_entity_snapshot_buffer_acquire_latest(snapshots, &read_view);
    if (rc == FASTDIS_OK) {
        apply_snapshot_view(&read_view);
        fastdis_entity_snapshot_buffer_release(snapshots, &read_view);
    }

    fastdis_entity_snapshot_buffer_destroy(snapshots);
    fastdis_entity_table_destroy(table);
    fastdis_scanner_destroy(scanner);
    return 0;
}
