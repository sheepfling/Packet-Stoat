#include "../common/replay_reader.hpp"

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
using fastdis_socket_t = SOCKET;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
using fastdis_socket_t = int;
#endif

namespace {

struct Args {
    std::string host;
    int port = 0;
    std::string replay_path;
    bool json = false;
};

void print_usage(const char* argv0) {
    std::cerr << "usage: " << argv0 << " HOST PORT REPLAY.fastdispkt [--json]\n";
}

bool parse_args(int argc, char** argv, Args& out) {
    if (argc < 4) {
        return false;
    }
    out.host = argv[1];
    out.port = std::atoi(argv[2]);
    out.replay_path = argv[3];
    for (int index = 4; index < argc; ++index) {
        if (std::string(argv[index]) == "--json") {
            out.json = true;
            continue;
        }
        return false;
    }
    return true;
}

void close_socket(fastdis_socket_t socket_fd) {
#if defined(_WIN32)
    closesocket(socket_fd);
#else
    close(socket_fd);
#endif
}

} // namespace

int main(int argc, char** argv) {
    Args args{};
    if (!parse_args(argc, argv, args)) {
        print_usage(argv[0]);
        return 2;
    }

#if defined(_WIN32)
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        std::cerr << "WSAStartup failed\n";
        return 1;
    }
#endif

    fastdis::examples::ReplayReader reader(args.replay_path);
    if (!reader.is_open()) {
        std::cerr << "could not open replay file: " << args.replay_path << '\n';
        return 1;
    }

    fastdis_socket_t socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
#if defined(_WIN32)
    if (socket_fd == INVALID_SOCKET) {
#else
    if (socket_fd < 0) {
#endif
        std::cerr << "socket() failed\n";
        return 1;
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(static_cast<std::uint16_t>(args.port));
    if (inet_pton(AF_INET, args.host.c_str(), &addr.sin_addr) != 1) {
        std::cerr << "invalid host: " << args.host << '\n';
        close_socket(socket_fd);
        return 1;
    }

    std::vector<std::uint8_t> packet;
    std::size_t packets_sent = 0;
    std::size_t bytes_sent = 0;
    std::string error;
    while (reader.read_next(packet, &error)) {
#if defined(_WIN32)
        const int sent = sendto(
            socket_fd,
            reinterpret_cast<const char*>(packet.data()),
            static_cast<int>(packet.size()),
            0,
            reinterpret_cast<const sockaddr*>(&addr),
            static_cast<int>(sizeof(addr)));
        if (sent == SOCKET_ERROR) {
            std::cerr << "sendto() failed\n";
            close_socket(socket_fd);
            return 1;
        }
        bytes_sent += static_cast<std::size_t>(sent);
#else
        const ssize_t sent = sendto(
            socket_fd,
            packet.data(),
            packet.size(),
            0,
            reinterpret_cast<const sockaddr*>(&addr),
            static_cast<socklen_t>(sizeof(addr)));
        if (sent < 0) {
            perror("sendto");
            close_socket(socket_fd);
            return 1;
        }
        bytes_sent += static_cast<std::size_t>(sent);
#endif
        packets_sent += 1;
    }
    if (!error.empty()) {
        std::cerr << error << '\n';
        close_socket(socket_fd);
        return 1;
    }

    close_socket(socket_fd);
#if defined(_WIN32)
    WSACleanup();
#endif

    if (args.json) {
        std::cout
            << "{\n"
            << "  \"schema\": \"fastdis.cpp_udp_send_report.v1\",\n"
            << "  \"surface\": \"cpp\",\n"
            << "  \"mode\": \"localhost_udp\",\n"
            << "  \"packets_sent\": " << packets_sent << ",\n"
            << "  \"bytes_sent\": " << bytes_sent << ",\n"
            << "  \"errors\": []\n"
            << "}\n";
    } else {
        std::cout << "sent " << packets_sent << " replay packet(s) to " << args.host << ':' << args.port << '\n';
    }
    return 0;
}
