#include "fastdis/fastdis.h"

#include <stdio.h>
#include <stdint.h>

static int FASTDIS_CALL on_entity_state(const fastdis_entity_state_prefix_t *entity,
                                        const uint8_t *data,
                                        size_t size,
                                        void *packet_user,
                                        void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    (void)callback_user;

    printf("entity=%u/%u/%u force=%u loc=(%.3f, %.3f, %.3f) orient=(%.3f, %.3f, %.3f) fields=0x%llx\n",
           (unsigned)entity->entity_id.site,
           (unsigned)entity->entity_id.application,
           (unsigned)entity->entity_id.entity,
           (unsigned)entity->force_id,
           entity->location.x,
           entity->location.y,
           entity->location.z,
           entity->orientation.psi,
           entity->orientation.theta,
           entity->orientation.phi,
           (unsigned long long)entity->fields_present);
    return 0;
}

void scan_entity_state_burst(const fastdis_packet_view_t *packets, size_t count) {
    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);

    fastdis_filter_clear(&config.versions);
    fastdis_filter_allow(&config.versions, 6);
    fastdis_filter_allow(&config.versions, 7);

    /* Example: only keep blue-ish/local force IDs 1 and 2 before callback. */
    fastdis_filter_clear(&config.entity_force_ids);
    fastdis_filter_allow(&config.entity_force_ids, 1);
    fastdis_filter_allow(&config.entity_force_ids, 2);

    /* Decode only the fields a pose replication layer needs. */
    config.entity_state_fields = FASTDIS_ES_FIELD_POSE;
    config.sample_every = 1;

    fastdis_scanner_t *scanner = fastdis_scanner_create(&config);
    if (scanner == NULL) {
        fputs("could not create fastdis scanner\n", stderr);
        return;
    }

    /* Optional large native-side entity-ID allowlist. */
    fastdis_scanner_add_entity_id(scanner, 0x1111u, 0x2222u, 0x3333u);
    fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW);

    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);

    fastdis_status_t rc = fastdis_scanner_scan_entity_state_packets(
        scanner,
        packets,
        count,
        on_entity_state,
        NULL,
        &stats);

    fastdis_scanner_destroy(scanner);

    if (rc != FASTDIS_OK) {
        fprintf(stderr, "fastdis error: %s\n", fastdis_status_string(rc));
        return;
    }

    fprintf(stderr, "seen=%llu malformed=%llu accepted=%llu emitted=%llu\n",
            (unsigned long long)stats.seen,
            (unsigned long long)stats.malformed,
            (unsigned long long)stats.accepted,
            (unsigned long long)stats.emitted);
}

int main(void) {
    puts("entity_state_scan.c is a scanner/callback example; feed packet views from your engine or UDP loop.");
    return 0;
}
