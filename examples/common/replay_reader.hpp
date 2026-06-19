#pragma once

#include <fastdis/fastdis.hpp>

#include <cstdint>
#include <fstream>
#include <ios>
#include <string>
#include <utility>
#include <vector>

namespace fastdis::examples {

class ReplayReader {
public:
    explicit ReplayReader(std::string path) : path_(std::move(path)), in_(path_, std::ios::binary) {}

    bool is_open() const noexcept { return in_.is_open(); }
    const std::string& path() const noexcept { return path_; }

    bool read_next(std::vector<std::uint8_t>& out_packet, std::string* out_error = nullptr) {
        out_packet.clear();
        if (!in_) {
            return false;
        }

        std::uint32_t length = 0;
        if (!read_be32(length)) {
            if (in_.eof()) {
                return false;
            }
            if (out_error) {
                *out_error = "could not read replay packet length";
            }
            return false;
        }
        if (length == 0 || length > (16u * 1024u * 1024u)) {
            if (out_error) {
                *out_error = "invalid replay packet length";
            }
            return false;
        }

        out_packet.resize(length);
        if (!in_.read(reinterpret_cast<char*>(out_packet.data()), static_cast<std::streamsize>(out_packet.size()))) {
            out_packet.clear();
            if (out_error) {
                *out_error = "truncated replay file";
            }
            return false;
        }
        return true;
    }

    std::vector<std::vector<std::uint8_t>> read_all(std::size_t limit = 0, std::string* out_error = nullptr) {
        std::vector<std::vector<std::uint8_t>> packets;
        std::vector<std::uint8_t> packet;
        while (limit == 0 || packets.size() < limit) {
            std::string error;
            if (!read_next(packet, &error)) {
                if (!error.empty() && out_error) {
                    *out_error = error;
                }
                break;
            }
            packets.push_back(packet);
        }
        return packets;
    }

private:
    bool read_be32(std::uint32_t& out) {
        std::uint8_t b[4];
        if (!in_.read(reinterpret_cast<char*>(b), 4)) {
            return false;
        }
        out = (static_cast<std::uint32_t>(b[0]) << 24) |
              (static_cast<std::uint32_t>(b[1]) << 16) |
              (static_cast<std::uint32_t>(b[2]) << 8) |
              static_cast<std::uint32_t>(b[3]);
        return true;
    }

    std::string path_;
    std::ifstream in_;
};

inline bool load_replay_file(const std::string& path,
                             std::vector<std::vector<std::uint8_t>>& out_packets,
                             std::string* out_error = nullptr,
                             std::size_t limit = 0) {
    ReplayReader reader(path);
    if (!reader.is_open()) {
        if (out_error) {
            *out_error = "could not open replay file";
        }
        return false;
    }
    out_packets = reader.read_all(limit, out_error);
    return out_error == nullptr || out_error->empty();
}

} // namespace fastdis::examples
