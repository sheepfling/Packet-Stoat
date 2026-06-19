#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#if defined(_WIN32)
#define NOMINMAX
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace fastdis::examples {

class UdpReceiver {
public:
    explicit UdpReceiver(std::uint16_t port) : port_(port) {}
    ~UdpReceiver() { close(); }

    bool open(std::string* out_error = nullptr) {
        close();
#if defined(_WIN32)
        WSADATA wsa_data{};
        if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
            if (out_error) {
                *out_error = "WSAStartup failed";
            }
            return false;
        }
#endif

        socket_ = ::socket(AF_INET, SOCK_DGRAM, 0);
        if (socket_ < 0) {
            if (out_error) {
                *out_error = "socket() failed";
            }
            return false;
        }

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(INADDR_ANY);
        addr.sin_port = htons(port_);
        if (::bind(socket_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0) {
            if (out_error) {
                *out_error = "bind() failed";
            }
            close();
            return false;
        }

#if defined(_WIN32)
        u_long non_blocking = 1;
        if (ioctlsocket(socket_, FIONBIO, &non_blocking) != 0) {
            if (out_error) {
                *out_error = "ioctlsocket(FIONBIO) failed";
            }
            close();
            return false;
        }
#else
        const int flags = fcntl(socket_, F_GETFL, 0);
        if (flags < 0 || fcntl(socket_, F_SETFL, flags | O_NONBLOCK) != 0) {
            if (out_error) {
                *out_error = "fcntl(O_NONBLOCK) failed";
            }
            close();
            return false;
        }
#endif
        return true;
    }

    bool is_open() const noexcept { return socket_ >= 0; }

    std::size_t receive_burst(std::vector<std::vector<std::uint8_t>>& out_packets,
                              std::size_t max_packets,
                              std::size_t max_packet_size = 65535) {
        out_packets.clear();
        if (!is_open() || max_packets == 0 || max_packet_size == 0) {
            return 0;
        }

        std::vector<std::uint8_t> buffer(max_packet_size);
        while (out_packets.size() < max_packets) {
            const int received = static_cast<int>(::recv(socket_,
                                                         reinterpret_cast<char*>(buffer.data()),
                                                         static_cast<int>(buffer.size()),
                                                         0));
            if (received <= 0) {
                break;
            }
            out_packets.emplace_back(buffer.begin(), buffer.begin() + received);
        }
        return out_packets.size();
    }

    void close() noexcept {
        if (socket_ >= 0) {
#if defined(_WIN32)
            closesocket(socket_);
            WSACleanup();
#else
            ::close(socket_);
#endif
            socket_ = -1;
        }
    }

private:
    std::uint16_t port_ = 0;
    int socket_ = -1;
};

} // namespace fastdis::examples
