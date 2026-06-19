#include <fastdis/fastdis.h>

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static int FASTDIS_CALL on_packet(const fastdis_header_t* h,
                                  const uint8_t* data,
                                  size_t size,
                                  void* packet_user,
                                  void* callback_user) {
    (void)data;
    (void)packet_user;
    (void)callback_user;
    printf("version=%u exercise=%u pdu_type=%u family=%u timestamp=%u length=%u status=%d size=%zu\n",
           (unsigned)h->version,
           (unsigned)h->exercise_id,
           (unsigned)h->pdu_type,
           (unsigned)h->protocol_family,
           (unsigned)h->timestamp,
           (unsigned)h->length,
           (int)h->status,
           size);
    return 0;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s packet.bin\n", argv[0]);
        return 2;
    }

    FILE* f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }
    if (fseek(f, 0, SEEK_END) != 0) {
        perror("fseek");
        fclose(f);
        return 1;
    }
    long n = ftell(f);
    if (n < 0) {
        perror("ftell");
        fclose(f);
        return 1;
    }
    rewind(f);

    uint8_t* buf = (uint8_t*)malloc((size_t)n);
    if (!buf) {
        fclose(f);
        return 1;
    }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n) {
        fprintf(stderr, "short read\n");
        free(buf);
        return 1;
    }

    fastdis_scan_config_t cfg;
    fastdis_scan_config_init(&cfg);

    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);

    fastdis_status_t rc = fastdis_scan_packet(buf, (size_t)n, &cfg, on_packet, NULL, &stats);
    if (rc != FASTDIS_OK) {
        fprintf(stderr, "scan failed: %s\n", fastdis_status_string(rc));
        free(buf);
        return 1;
    }

    fprintf(stderr, "seen=%llu malformed=%llu accepted=%llu emitted=%llu\n",
            (unsigned long long)stats.seen,
            (unsigned long long)stats.malformed,
            (unsigned long long)stats.accepted,
            (unsigned long long)stats.emitted);
    free(buf);
    return 0;
}
