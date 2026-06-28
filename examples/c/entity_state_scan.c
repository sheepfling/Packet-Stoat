#include "fastdis/fastdis.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t read_be32(FILE *f) {
    unsigned char b[4];
    if (fread(b, 1, 4, f) != 4) {
        return 0;
    }
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) | ((uint32_t)b[2] << 8) | (uint32_t)b[3];
}

static void emit_entities_json(const fastdis_entity_state_prefix_t *entities, size_t count) {
    size_t i;
    printf("\"latest_entities\":[");
    for (i = 0; i < count; ++i) {
        const fastdis_entity_state_prefix_t *entity = &entities[i];
        if (i > 0) {
            printf(",");
        }
        printf(
            "{\"site\":%u,\"application\":%u,\"entity\":%u,\"force_id\":%u,"
            "\"location_ecef_m\":[%.6f,%.6f,%.6f],"
            "\"orientation_dis_rad\":[%.6f,%.6f,%.6f]}",
            entity->entity_id.site,
            entity->entity_id.application,
            entity->entity_id.entity,
            entity->force_id,
            entity->location.x,
            entity->location.y,
            entity->location.z,
            entity->orientation.psi,
            entity->orientation.theta,
            entity->orientation.phi);
    }
    printf("]");
}

int main(int argc, char **argv) {
    const char *path = NULL;
    uint8_t allowed_force_ids[32];
    size_t allowed_force_id_count = 0;
    int emit_json = 0;
    int argi;
    FILE *f = NULL;
    fastdis_packet_view_t *packets = NULL;
    uint8_t **owned_packets = NULL;
    size_t packet_count = 0;
    size_t packet_capacity = 0;
    fastdis_entity_state_prefix_t *entities = NULL;
    int exit_code = 0;

    if (argc < 2) {
        fprintf(stderr, "usage: %s packets.fastdispkt [--json] [--allow-force-id N]\n", argv[0]);
        return 2;
    }
    path = argv[1];
    for (argi = 2; argi < argc; ++argi) {
        if (strcmp(argv[argi], "--json") == 0) {
            emit_json = 1;
            continue;
        }
        if (strcmp(argv[argi], "--allow-force-id") == 0) {
            if (argi + 1 >= argc) {
                fprintf(stderr, "missing value for --allow-force-id\n");
                return 2;
            }
            if (allowed_force_id_count >= (sizeof(allowed_force_ids) / sizeof(allowed_force_ids[0]))) {
                fprintf(stderr, "too many --allow-force-id values\n");
                return 2;
            }
            allowed_force_ids[allowed_force_id_count++] = (uint8_t)strtoul(argv[++argi], NULL, 10);
            continue;
        }
        fprintf(stderr, "unknown argument: %s\n", argv[argi]);
        return 2;
    }

    f = fopen(path, "rb");
    if (!f) {
        perror("fopen");
        return 2;
    }

    while (!feof(f)) {
        uint32_t n = read_be32(f);
        uint8_t *buffer;
        if (n == 0) {
            break;
        }
        if (packet_count == packet_capacity) {
            size_t next_capacity = packet_capacity == 0 ? 64u : packet_capacity * 2u;
            fastdis_packet_view_t *next_packets = (fastdis_packet_view_t *)realloc(packets, next_capacity * sizeof(*packets));
            uint8_t **next_owned = (uint8_t **)realloc(owned_packets, next_capacity * sizeof(*owned_packets));
            if (!next_packets || !next_owned) {
                fprintf(stderr, "out of memory growing replay storage\n");
                free(next_packets);
                free(next_owned);
                exit_code = 2;
                goto cleanup;
            }
            packets = next_packets;
            owned_packets = next_owned;
            packet_capacity = next_capacity;
        }
        buffer = (uint8_t *)malloc(n);
        if (!buffer) {
            fprintf(stderr, "out of memory reading replay packet\n");
            exit_code = 2;
            goto cleanup;
        }
        if (fread(buffer, 1, n, f) != n) {
            free(buffer);
            fprintf(stderr, "truncated replay packet\n");
            exit_code = 2;
            goto cleanup;
        }
        packets[packet_count].data = buffer;
        packets[packet_count].size = n;
        packets[packet_count].user = NULL;
        owned_packets[packet_count] = buffer;
        packet_count++;
    }

    if (packet_count == 0) {
        fprintf(stderr, "no replay packets loaded\n");
        exit_code = 2;
        goto cleanup;
    }

    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);
    fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_STATE_POSE);
    if (allowed_force_id_count > 0) {
        size_t i;
        fastdis_filter_clear(&config.entity_force_ids);
        for (i = 0; i < allowed_force_id_count; ++i) {
            fastdis_filter_allow(&config.entity_force_ids, allowed_force_ids[i]);
        }
    }

    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);
    entities = (fastdis_entity_state_prefix_t *)calloc(packet_count, sizeof(*entities));
    if (!entities) {
        fprintf(stderr, "out of memory allocating entity batch\n");
        exit_code = 2;
        goto cleanup;
    }
    fastdis_entity_state_batch_t batch;
    batch.entities = entities;
    batch.capacity = packet_count;
    batch.count = 0;
    batch.dropped = 0;

    {
        fastdis_status_t rc = fastdis_scan_entity_state_to_batch(
            packets,
            packet_count,
            &config,
            &batch,
            &stats);
        if (rc != FASTDIS_OK) {
            fprintf(stderr, "fastdis error: %s\n", fastdis_status_string(rc));
            exit_code = 1;
            goto cleanup;
        }
    }

    if (emit_json) {
        unsigned long long rejected = (unsigned long long)(stats.seen - stats.accepted - stats.malformed);
        printf("{");
        printf("\"schema\":\"fastdis.c_filter_report.v1\",");
        printf("\"surface\":\"c\",");
        printf("\"mode\":\"filtering\",");
        printf("\"packets_received\":%llu,", (unsigned long long)packet_count);
        printf("\"packets_parsed\":%llu,", (unsigned long long)stats.seen);
        printf("\"packets_accepted\":%llu,", (unsigned long long)stats.accepted);
        printf("\"packets_rejected\":%llu,", rejected);
        printf("\"malformed\":%llu,", (unsigned long long)stats.malformed);
        printf("\"unique_entities\":%zu,", batch.count);
        emit_entities_json(batch.entities, batch.count);
        printf(",\"errors\":[]}\n");
    } else {
        fprintf(stderr, "seen=%llu malformed=%llu accepted=%llu emitted=%llu\n",
                (unsigned long long)stats.seen,
                (unsigned long long)stats.malformed,
                (unsigned long long)stats.accepted,
                (unsigned long long)stats.emitted);
    }

cleanup:
    if (owned_packets) {
        size_t i;
        for (i = 0; i < packet_count; ++i) {
            free(owned_packets[i]);
        }
    }
    free(entities);
    free(owned_packets);
    free(packets);
    if (f) {
        fclose(f);
    }
    return exit_code;
}
