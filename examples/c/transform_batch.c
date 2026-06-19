#include "fastdis/fastdis.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint32_t read_be32(FILE *fh, int *ok) {
    uint8_t b[4];
    if (fread(b, 1, 4, fh) != 4) {
        *ok = 0;
        return 0;
    }
    *ok = 1;
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) | ((uint32_t)b[2] << 8) | (uint32_t)b[3];
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s packets.fastdispkt\n", argv[0]);
        return 2;
    }

    FILE *fh = fopen(argv[1], "rb");
    if (!fh) {
        perror(argv[1]);
        return 2;
    }

    fastdis_scan_config_t cfg;
    fastdis_scan_config_init(&cfg);
    fastdis_scan_config_use_profile(&cfg, FASTDIS_PROFILE_ENTITY_TRANSFORM);

    fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
    if (!scanner) {
        fprintf(stderr, "could not create scanner\n");
        fclose(fh);
        return 2;
    }

    enum { BATCH_CAPACITY = 1024 };
    uint8_t *packet_storage[BATCH_CAPACITY] = {0};
    fastdis_packet_view_t packets[BATCH_CAPACITY];
    fastdis_entity_transform_t transforms[BATCH_CAPACITY];
    fastdis_entity_transform_batch_t transform_batch = {transforms, BATCH_CAPACITY, 0, 0};
    fastdis_scan_stats_t total;
    fastdis_scan_stats_init(&total);

    size_t packet_count = 0;
    int ok = 0;
    for (;;) {
        uint32_t len = read_be32(fh, &ok);
        if (!ok) {
            break;
        }
        uint8_t *data = (uint8_t *)malloc(len);
        if (!data) {
            fprintf(stderr, "out of memory\n");
            break;
        }
        if (fread(data, 1, len, fh) != len) {
            fprintf(stderr, "truncated replay file\n");
            free(data);
            break;
        }
        packet_storage[packet_count] = data;
        packets[packet_count].data = data;
        packets[packet_count].size = len;
        packets[packet_count].user = NULL;
        packet_count += 1;

        if (packet_count == BATCH_CAPACITY) {
            fastdis_scan_stats_t stats;
            fastdis_scan_stats_init(&stats);
            fastdis_status_t rc = fastdis_scanner_scan_entity_transforms_to_batch(
                scanner, packets, packet_count, &transform_batch, &stats);
            if (rc != FASTDIS_OK) {
                fprintf(stderr, "scan failed: %s\n", fastdis_status_string(rc));
                break;
            }
            total.seen += stats.seen;
            total.malformed += stats.malformed;
            total.accepted += stats.accepted;
            total.emitted += stats.emitted;
            printf("batch transforms=%zu dropped=%zu\n", transform_batch.count, transform_batch.dropped);
            for (size_t i = 0; i < packet_count; ++i) {
                free(packet_storage[i]);
                packet_storage[i] = NULL;
            }
            packet_count = 0;
        }
    }

    if (packet_count > 0) {
        fastdis_scan_stats_t stats;
        fastdis_scan_stats_init(&stats);
        fastdis_status_t rc = fastdis_scanner_scan_entity_transforms_to_batch(
            scanner, packets, packet_count, &transform_batch, &stats);
        if (rc == FASTDIS_OK) {
            total.seen += stats.seen;
            total.malformed += stats.malformed;
            total.accepted += stats.accepted;
            total.emitted += stats.emitted;
            printf("batch transforms=%zu dropped=%zu\n", transform_batch.count, transform_batch.dropped);
        }
    }

    for (size_t i = 0; i < packet_count; ++i) {
        free(packet_storage[i]);
    }
    fastdis_scanner_destroy(scanner);
    fclose(fh);
    printf("seen=%llu accepted=%llu emitted=%llu malformed=%llu\n",
           (unsigned long long)total.seen,
           (unsigned long long)total.accepted,
           (unsigned long long)total.emitted,
           (unsigned long long)total.malformed);
    return 0;
}
