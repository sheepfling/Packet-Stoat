#include "fastdis/fastdis.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
typedef SOCKET fastdis_socket_t;
#else
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
typedef int fastdis_socket_t;
#endif

#define FASTDIS_MAX_UDP_PACKET 65535

typedef struct received_packet_s {
    uint8_t *data;
    size_t size;
} received_packet_t;

static void free_packets(received_packet_t *packets, size_t count) {
    size_t i;
    if (!packets) {
        return;
    }
    for (i = 0; i < count; ++i) {
        free(packets[i].data);
    }
    free(packets);
}

static int fastdis_set_nonblocking(fastdis_socket_t socket_fd) {
#if defined(_WIN32)
    u_long non_blocking = 1;
    return ioctlsocket(socket_fd, FIONBIO, &non_blocking) == 0 ? 0 : -1;
#else
    const int flags = fcntl(socket_fd, F_GETFL, 0);
    if (flags < 0) {
        return -1;
    }
    return fcntl(socket_fd, F_SETFL, flags | O_NONBLOCK) == 0 ? 0 : -1;
#endif
}

static void fastdis_close_socket(fastdis_socket_t socket_fd) {
#if defined(_WIN32)
    closesocket(socket_fd);
#else
    close(socket_fd);
#endif
}

static int receive_packets(
    int port,
    size_t max_packets,
    size_t idle_polls,
    received_packet_t **out_packets,
    size_t *out_count) {
    received_packet_t *packets = NULL;
    fastdis_socket_t socket_fd;
    struct sockaddr_in addr;
    size_t count = 0;
    size_t idle = 0;

#if defined(_WIN32)
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return -1;
    }
#endif

    packets = (received_packet_t *)calloc(max_packets, sizeof(*packets));
    if (!packets) {
        fprintf(stderr, "out of memory\n");
        return -1;
    }

    socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
#if defined(_WIN32)
    if (socket_fd == INVALID_SOCKET) {
#else
    if (socket_fd < 0) {
#endif
        fprintf(stderr, "socket() failed\n");
        free_packets(packets, 0);
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (bind(socket_fd, (struct sockaddr *)&addr, (socklen_t)sizeof(addr)) != 0) {
        fprintf(stderr, "bind() failed\n");
        fastdis_close_socket(socket_fd);
        free_packets(packets, 0);
        return -1;
    }

    if (fastdis_set_nonblocking(socket_fd) != 0) {
        fprintf(stderr, "failed to make UDP socket non-blocking\n");
        fastdis_close_socket(socket_fd);
        free_packets(packets, 0);
        return -1;
    }

    while (count < max_packets && idle < idle_polls) {
        uint8_t buffer[FASTDIS_MAX_UDP_PACKET];
        int received =
#if defined(_WIN32)
            recv(socket_fd, (char *)buffer, (int)sizeof(buffer), 0);
        if (received == SOCKET_ERROR) {
            const int error = WSAGetLastError();
            if (error == WSAEWOULDBLOCK) {
                ++idle;
                Sleep(5);
                continue;
            }
            fprintf(stderr, "recv() failed: %d\n", error);
            break;
        }
#else
            (int)recv(socket_fd, buffer, sizeof(buffer), 0);
        if (received < 0) {
            if (errno == EWOULDBLOCK || errno == EAGAIN) {
                ++idle;
                usleep(5000);
                continue;
            }
            perror("recv");
            break;
        }
#endif
        if (received == 0) {
            ++idle;
            continue;
        }
        packets[count].data = (uint8_t *)malloc((size_t)received);
        if (!packets[count].data) {
            fprintf(stderr, "out of memory\n");
            break;
        }
        memcpy(packets[count].data, buffer, (size_t)received);
        packets[count].size = (size_t)received;
        ++count;
        idle = 0;
    }

    fastdis_close_socket(socket_fd);
#if defined(_WIN32)
    WSACleanup();
#endif

    *out_packets = packets;
    *out_count = count;
    return 0;
}

static int packet_compare(const void *lhs, const void *rhs) {
    const fastdis_entity_snapshot_t *a = (const fastdis_entity_snapshot_t *)lhs;
    const fastdis_entity_snapshot_t *b = (const fastdis_entity_snapshot_t *)rhs;
    if (a->transform.entity_id.site != b->transform.entity_id.site) {
        return a->transform.entity_id.site < b->transform.entity_id.site ? -1 : 1;
    }
    if (a->transform.entity_id.application != b->transform.entity_id.application) {
        return a->transform.entity_id.application < b->transform.entity_id.application ? -1 : 1;
    }
    if (a->transform.entity_id.entity != b->transform.entity_id.entity) {
        return a->transform.entity_id.entity < b->transform.entity_id.entity ? -1 : 1;
    }
    if (a->transform.force_id != b->transform.force_id) {
        return a->transform.force_id < b->transform.force_id ? -1 : 1;
    }
    return 0;
}

static void emit_latest_entities(const fastdis_entity_snapshot_t *snapshots, size_t count) {
    size_t i;
    printf("\"latest_entities\":[");
    for (i = 0; i < count; ++i) {
        const fastdis_entity_snapshot_t *snapshot = &snapshots[i];
        if (i > 0) {
            printf(",");
        }
        printf(
            "{\"site\":%u,\"application\":%u,\"entity\":%u,\"force_id\":%u,"
            "\"location_ecef_m\":[%.6f,%.6f,%.6f],"
            "\"orientation_dis_rad\":[%.6f,%.6f,%.6f]}",
            (unsigned)snapshot->transform.entity_id.site,
            (unsigned)snapshot->transform.entity_id.application,
            (unsigned)snapshot->transform.entity_id.entity,
            (unsigned)snapshot->transform.force_id,
            snapshot->transform.location.x,
            snapshot->transform.location.y,
            snapshot->transform.location.z,
            snapshot->transform.orientation.psi,
            snapshot->transform.orientation.theta,
            snapshot->transform.orientation.phi);
    }
    printf("]");
}

int main(int argc, char **argv) {
    int port;
    size_t max_packets = 24;
    size_t idle_polls = 800;
    size_t i;
    received_packet_t *received_packets = NULL;
    size_t received_count = 0;
    fastdis_packet_view_t *views = NULL;
    fastdis_scan_config_t config;
    fastdis_scanner_t *scanner = NULL;
    fastdis_entity_table_t *table = NULL;
    fastdis_entity_snapshot_buffer_t *buffer = NULL;
    fastdis_entity_table_update_stats_t update_stats;
    fastdis_entity_snapshot_view_t published_view;
    fastdis_entity_snapshot_buffer_stats_t buffer_stats;
    fastdis_entity_snapshot_t *sorted_snapshots = NULL;
    fastdis_header_t header;
    size_t entity_state_count = 0;
    size_t malformed = 0;
    fastdis_status_t status;
    int exit_code = 0;

    if (argc < 2) {
        fprintf(stderr, "usage: %s PORT [--max-packets N] [--idle-polls N] [--json]\n", argv[0]);
        return 2;
    }

    port = atoi(argv[1]);
    for (i = 2; i < (size_t)argc; ++i) {
        if (strcmp(argv[i], "--max-packets") == 0 && (i + 1) < (size_t)argc) {
            max_packets = (size_t)strtoull(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--idle-polls") == 0 && (i + 1) < (size_t)argc) {
            idle_polls = (size_t)strtoull(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--json") == 0) {
            /* accepted for symmetry; JSON is always emitted */
        } else {
            fprintf(stderr, "unknown argument: %s\n", argv[i]);
            return 2;
        }
    }

    if (receive_packets(port, max_packets, idle_polls, &received_packets, &received_count) != 0) {
        return 2;
    }

    views = (fastdis_packet_view_t *)calloc(received_count ? received_count : 1, sizeof(*views));
    if (!views) {
        fprintf(stderr, "out of memory\n");
        free_packets(received_packets, received_count);
        return 2;
    }

    for (i = 0; i < received_count; ++i) {
        views[i].data = received_packets[i].data;
        views[i].size = received_packets[i].size;
        views[i].user = NULL;
        status = fastdis_parse_header(received_packets[i].data, received_packets[i].size, 0u, &header);
        if (status != FASTDIS_OK) {
            ++malformed;
            continue;
        }
        if (header.pdu_type == 1u) {
            ++entity_state_count;
        }
    }

    fastdis_scan_config_init(&config);
    fastdis_scan_config_use_profile(&config, FASTDIS_PROFILE_ENTITY_TRANSFORM);
    scanner = fastdis_scanner_create(&config);
    table = fastdis_entity_table_create(received_count ? received_count : 1u);
    buffer = fastdis_entity_snapshot_buffer_create_ex(received_count ? received_count : 1u, 3u);
    if (!scanner || !table || !buffer) {
        fprintf(stderr, "could not create fastdis scanner/table/buffer\n");
        exit_code = 2;
        goto cleanup;
    }

    fastdis_entity_table_update_stats_init(&update_stats);
    status = fastdis_entity_table_ingest_packets_publish_changed(
        table,
        scanner,
        views,
        received_count,
        1u,
        1u,
        buffer,
        &update_stats,
        &published_view);
    if (status != FASTDIS_OK) {
        fprintf(stderr, "ingest/publish failed: %s\n", fastdis_status_string(status));
        exit_code = 2;
        goto cleanup;
    }

    fastdis_entity_snapshot_buffer_stats_init(&buffer_stats);
    status = fastdis_entity_snapshot_buffer_get_stats(buffer, &buffer_stats);
    if (status != FASTDIS_OK) {
        fprintf(stderr, "buffer stats failed: %s\n", fastdis_status_string(status));
        exit_code = 2;
        goto cleanup;
    }

    if (published_view.count > 0u) {
        sorted_snapshots = (fastdis_entity_snapshot_t *)calloc(published_view.count, sizeof(*sorted_snapshots));
        if (!sorted_snapshots) {
            fprintf(stderr, "out of memory\n");
            exit_code = 2;
            goto cleanup;
        }
        memcpy(sorted_snapshots, published_view.snapshots, published_view.count * sizeof(*sorted_snapshots));
        if (published_view.count > 1u) {
            qsort(sorted_snapshots, published_view.count, sizeof(*sorted_snapshots), packet_compare);
        }
    }

    printf("{");
    printf("\"schema\":\"fastdis.c_udp_burst_report.v1\",");
    printf("\"surface\":\"c\",");
    printf("\"mode\":\"localhost_udp\",");
    printf("\"packets_received\":%zu,", received_count);
    printf("\"packets_parsed\":%zu,", received_count - malformed);
    printf("\"malformed\":%zu,", malformed);
    printf("\"entity_state\":%zu,", entity_state_count);
    printf("\"burst_count\":%u,", received_count > 0 ? 1u : 0u);
    printf("\"snapshots_published\":%zu,", published_view.count);
    printf("\"unique_entities\":%zu,", published_view.count);
    emit_latest_entities(sorted_snapshots ? sorted_snapshots : published_view.snapshots, published_view.count);
    printf(",\"errors\":[],");
    printf("\"buffer_stats\":{\"publish_attempts\":%llu,\"publish_successes\":%llu,\"publish_busy\":%llu,"
           "\"acquire_count\":%llu,\"release_count\":%llu,\"max_snapshot_count\":%llu,\"dropped_snapshots\":%llu}",
           (unsigned long long)buffer_stats.publish_attempts,
           (unsigned long long)buffer_stats.publish_successes,
           (unsigned long long)buffer_stats.publish_busy,
           (unsigned long long)buffer_stats.acquire_count,
           (unsigned long long)buffer_stats.release_count,
           (unsigned long long)buffer_stats.max_snapshot_count,
           (unsigned long long)buffer_stats.dropped_snapshots);
    printf("}\n");

cleanup:
    free(sorted_snapshots);
    fastdis_entity_snapshot_buffer_destroy(buffer);
    fastdis_entity_table_destroy(table);
    fastdis_scanner_destroy(scanner);
    free(views);
    free_packets(received_packets, received_count);
    return exit_code;
}
