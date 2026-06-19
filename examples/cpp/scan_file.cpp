#include <fastdis/fastdis.h>

#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>

static int FASTDIS_CALL on_packet(const fastdis_header_t* h,
                                  const uint8_t* data,
                                  size_t size,
                                  void* packet_user,
                                  void* callback_user) {
    (void)data;
    (void)packet_user;
    (void)callback_user;
    std::cout << "version=" << static_cast<unsigned>(h->version)
              << " exercise=" << static_cast<unsigned>(h->exercise_id)
              << " pdu_type=" << static_cast<unsigned>(h->pdu_type)
              << " family=" << static_cast<unsigned>(h->protocol_family)
              << " timestamp=" << h->timestamp
              << " length=" << h->length
              << " status=" << h->status
              << " size=" << size << '\n';
    return 0;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " packet.bin\n";
        return 2;
    }

    std::ifstream in(argv[1], std::ios::binary);
    std::vector<uint8_t> packet((std::istreambuf_iterator<char>(in)), {});
    if (packet.empty()) {
        std::cerr << "empty or unreadable file\n";
        return 1;
    }

    fastdis_scan_config_t cfg;
    fastdis_scan_config_init(&cfg);
    fastdis_filter_clear(&cfg.versions);
    fastdis_filter_allow(&cfg.versions, 6);
    fastdis_filter_allow(&cfg.versions, 7);

    fastdis_scan_stats_t stats;
    fastdis_scan_stats_init(&stats);
    fastdis_status_t rc = fastdis_scan_packet(packet.data(), packet.size(), &cfg, on_packet, nullptr, &stats);
    if (rc != FASTDIS_OK) {
        std::cerr << "scan failed: " << fastdis_status_string(rc) << '\n';
        return 1;
    }
    std::cerr << "seen=" << stats.seen
              << " malformed=" << stats.malformed
              << " accepted=" << stats.accepted
              << " emitted=" << stats.emitted << '\n';
    return 0;
}
