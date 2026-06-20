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
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
typedef int fastdis_socket_t;
#endif

#define FASTDIS_MAX_REPLAY_PACKET (16u * 1024u * 1024u)

typedef struct send_stats_s {
    size_t packets_sent;
    size_t bytes_sent;
} send_stats_t;

static void print_usage(const char *argv0) {
    fprintf(stderr, "usage: %s HOST PORT REPLAY.fastdispkt [--json]\n", argv0);
}

static void fastdis_close_socket(fastdis_socket_t socket_fd) {
#if defined(_WIN32)
    closesocket(socket_fd);
#else
    close(socket_fd);
#endif
}

static int read_be32(FILE *handle, uint32_t *out_length) {
    uint8_t bytes[4];
    if (fread(bytes, 1, 4, handle) != 4) {
        return 0;
    }
    *out_length = ((uint32_t)bytes[0] << 24) |
                  ((uint32_t)bytes[1] << 16) |
                  ((uint32_t)bytes[2] << 8) |
                  (uint32_t)bytes[3];
    return 1;
}

static int send_replay(const char *host, int port, const char *replay_path, send_stats_t *out_stats) {
    fastdis_socket_t socket_fd;
    struct sockaddr_in addr;
    FILE *handle = NULL;
    uint8_t *packet = NULL;
    send_stats_t stats = {0u, 0u};

#if defined(_WIN32)
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }
#endif

    handle = fopen(replay_path, "rb");
    if (!handle) {
        fprintf(stderr, "could not open replay file: %s\n", replay_path);
        return 1;
    }

    socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
#if defined(_WIN32)
    if (socket_fd == INVALID_SOCKET) {
#else
    if (socket_fd < 0) {
#endif
        fprintf(stderr, "socket() failed\n");
        fclose(handle);
        return 1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        fprintf(stderr, "invalid host: %s\n", host);
        fastdis_close_socket(socket_fd);
        fclose(handle);
        return 1;
    }

    for (;;) {
        uint32_t length = 0;
        size_t sent;
        if (!read_be32(handle, &length)) {
            if (feof(handle)) {
                break;
            }
            fprintf(stderr, "truncated replay file before packet length\n");
            free(packet);
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
        if (length == 0u || length > FASTDIS_MAX_REPLAY_PACKET) {
            fprintf(stderr, "invalid replay packet length: %u\n", (unsigned)length);
            free(packet);
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
        packet = (uint8_t *)realloc(packet, (size_t)length);
        if (!packet) {
            fprintf(stderr, "out of memory\n");
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
        if (fread(packet, 1, (size_t)length, handle) != (size_t)length) {
            fprintf(stderr, "truncated replay file\n");
            free(packet);
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
#if defined(_WIN32)
        sent = (size_t)sendto(socket_fd, (const char *)packet, (int)length, 0, (const struct sockaddr *)&addr, (int)sizeof(addr));
        if ((int)sent == SOCKET_ERROR) {
            fprintf(stderr, "sendto() failed\n");
            free(packet);
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
#else
        sent = (size_t)sendto(socket_fd, packet, (size_t)length, 0, (const struct sockaddr *)&addr, (socklen_t)sizeof(addr));
        if ((ssize_t)sent < 0) {
            perror("sendto");
            free(packet);
            fastdis_close_socket(socket_fd);
            fclose(handle);
            return 1;
        }
#endif
        stats.packets_sent += 1u;
        stats.bytes_sent += sent;
    }

    free(packet);
    fastdis_close_socket(socket_fd);
    fclose(handle);
#if defined(_WIN32)
    WSACleanup();
#endif
    *out_stats = stats;
    return 0;
}

int main(int argc, char **argv) {
    const char *host;
    int port;
    const char *replay_path;
    int json = 0;
    send_stats_t stats;

    if (argc < 4) {
        print_usage(argv[0]);
        return 2;
    }
    host = argv[1];
    port = atoi(argv[2]);
    replay_path = argv[3];
    if (argc > 4 && strcmp(argv[4], "--json") == 0) {
        json = 1;
    }

    if (send_replay(host, port, replay_path, &stats) != 0) {
        return 1;
    }

    if (json) {
        printf(
            "{\n"
            "  \"schema\": \"fastdis.c_udp_send_report.v1\",\n"
            "  \"surface\": \"c\",\n"
            "  \"mode\": \"localhost_udp\",\n"
            "  \"packets_sent\": %zu,\n"
            "  \"bytes_sent\": %zu,\n"
            "  \"errors\": []\n"
            "}\n",
            stats.packets_sent,
            stats.bytes_sent);
    } else {
        printf("sent %zu replay packet(s) to %s:%d\n", stats.packets_sent, host, port);
    }
    return 0;
}
