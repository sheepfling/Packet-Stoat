#include "fastdis/fastdis.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint32_t read_be32(FILE *f) {
    unsigned char b[4];
    if (fread(b, 1, 4, f) != 4) {
        return 0;
    }
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) | ((uint32_t)b[2] << 8) | (uint32_t)b[3];
}

static void emit_latest_entities_json(const fastdis_entity_snapshot_t *snapshots, size_t count) {
    size_t i;
    printf("\"latest_entities\":[");
    for (i = 0; i < count; ++i) {
        const fastdis_entity_snapshot_t *s = &snapshots[i];
        if (i > 0) {
            printf(",");
        }
        printf(
            "{\"site\":%u,\"application\":%u,\"entity\":%u,\"force_id\":%u,"
            "\"location_ecef_m\":[%.6f,%.6f,%.6f],"
            "\"orientation_dis_rad\":[%.6f,%.6f,%.6f]}",
            s->transform.entity_id.site,
            s->transform.entity_id.application,
            s->transform.entity_id.entity,
            s->transform.force_id,
            s->transform.location.x,
            s->transform.location.y,
            s->transform.location.z,
            s->transform.orientation.psi,
            s->transform.orientation.theta,
            s->transform.orientation.phi);
    }
    printf("]");
}

int main(int argc, char **argv) {
    const char *path = NULL;
    int emit_json = 0;
    int argi;
    if (argc < 2) {
        fprintf(stderr, "usage: %s packets.fastdispkt [--json]\n", argv[0]);
        return 2;
    }
    path = argv[1];
    for (argi = 2; argi < argc; ++argi) {
        if (strcmp(argv[argi], "--json") == 0) {
            emit_json = 1;
            continue;
        }
        fprintf(stderr, "unknown argument: %s\n", argv[argi]);
        return 2;
    }

    FILE *f = fopen(path, "rb");
    if (!f) {
        perror("fopen");
        return 2;
    }

    fastdis_scan_config_t cfg;
    fastdis_scan_config_init(&cfg);
    fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

    fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
    fastdis_entity_table_t *table = fastdis_entity_table_create(4096);
    if (!scanner || !table) {
        fprintf(stderr, "could not create scanner/table\n");
        fastdis_scanner_destroy(scanner);
        fastdis_entity_table_destroy(table);
        fclose(f);
        return 2;
    }

    uint8_t buffer[65535];
    uint64_t packets = 0;
    while (!feof(f)) {
        uint32_t n = read_be32(f);
        if (n == 0) {
            break;
        }
        if (n > sizeof(buffer)) {
            fprintf(stderr, "packet too large: %u\n", n);
            break;
        }
        if (fread(buffer, 1, n, f) != n) {
            break;
        }
        fastdis_packet_view_t view = {buffer, n, NULL};
        fastdis_entity_table_update_stats_t stats;
        fastdis_entity_table_update_stats_init(&stats);
        fastdis_status_t rc = fastdis_entity_table_ingest_packets(table, scanner, &view, 1, 1, &stats);
        if (rc != FASTDIS_OK) {
            fprintf(stderr, "ingest failed: %s\n", fastdis_status_string(rc));
            break;
        }
        packets++;
    }

    size_t count = fastdis_entity_table_size(table);
    fastdis_entity_snapshot_t *snapshots = NULL;
    if (count > 0) {
        snapshots = (fastdis_entity_snapshot_t *)calloc(count, sizeof(*snapshots));
    }
    fastdis_entity_snapshot_batch_t batch = {snapshots, count, 0, 0};
    fastdis_entity_table_snapshot_all(table, &batch);

    if (emit_json) {
        printf("{");
        printf("\"schema\":\"fastdis.c_replay_report.v1\",");
        printf("\"surface\":\"c\",");
        printf("\"mode\":\"replay\",");
        printf("\"packets_received\":%llu,", (unsigned long long)packets);
        printf("\"packets_parsed\":%llu,", (unsigned long long)packets);
        printf("\"malformed\":0,");
        printf("\"entity_state\":%llu,", (unsigned long long)packets);
        printf("\"unique_entities\":%zu,", count);
        printf("\"snapshot_count\":%zu,", batch.count);
        printf("\"dropped\":%zu,", batch.dropped);
        emit_latest_entities_json(batch.snapshots, batch.count);
        printf(",\"errors\":[]}\n");
    } else {
        printf("packets=%llu table_tick=%llu entities=%zu snapshot_count=%zu dropped=%zu\n",
               (unsigned long long)packets,
               (unsigned long long)fastdis_entity_table_tick(table),
               count,
               batch.count,
               batch.dropped);
        for (size_t i = 0; i < batch.count && i < 10; ++i) {
            const fastdis_entity_snapshot_t *s = &batch.snapshots[i];
            printf("entity=(%u,%u,%u) force=%u loc=(%.3f,%.3f,%.3f) updates=%llu last_tick=%llu flags=0x%x\n",
                   s->transform.entity_id.site,
                   s->transform.entity_id.application,
                   s->transform.entity_id.entity,
                   s->transform.force_id,
                   s->transform.location.x,
                   s->transform.location.y,
                   s->transform.location.z,
                   (unsigned long long)s->update_count,
                   (unsigned long long)s->last_seen_tick,
                   s->change_flags);
        }
    }

    free(snapshots);
    fastdis_entity_table_destroy(table);
    fastdis_scanner_destroy(scanner);
    fclose(f);
    return 0;
}
