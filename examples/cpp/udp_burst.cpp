#include <fastdis/fastdis.hpp>

#include "../common/udp_receiver.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " port\n";
        return 2;
    }

    const int port = std::atoi(argv[1]);
    if (port <= 0 || port > 65535) {
        std::cerr << "invalid UDP port\n";
        return 2;
    }

    fastdis::examples::UdpReceiver receiver(static_cast<std::uint16_t>(port));
    std::string error;
    if (!receiver.open(&error)) {
        std::cerr << "could not open UDP receiver: " << error << '\n';
        return 2;
    }

    fastdis::Scanner scanner = fastdis::ScannerBuilder()
        .entity_transform_profile()
        .versions({6, 7})
        .pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
        .protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY})
        .build();

    fastdis::EntityTable table = fastdis::EntityTableConfig()
        .reserve(4096)
        .build();

    fastdis::SnapshotBuffer snapshots = fastdis::SnapshotBufferConfig()
        .capacity(4096)
        .slots(3)
        .build();

    std::uint64_t total_packets = 0;
    for (;;) {
        std::vector<std::vector<std::uint8_t>> datagrams;
        const std::size_t received = receiver.receive_burst(datagrams, 1024);
        if (received == 0) {
            continue;
        }

        fastdis::PacketViews packet_views(received);
        for (const auto& datagram : datagrams) {
            packet_views.add(datagram.data(), datagram.size());
        }

        fastdis::EntityTableUpdateStats stats = table.ingest(scanner, packet_views, true);
        fastdis::SnapshotView published = snapshots.publish_changed(table, true);
        fastdis::ScopedSnapshotView latest = snapshots.acquire_latest();

        total_packets += stats.scan.seen;
        std::cout << "burst_packets=" << received
                  << " accepted=" << stats.scan.accepted
                  << " changed_snapshots=" << published.size()
                  << " latest_view=" << latest.size()
                  << " total_seen=" << total_packets
                  << '\n';
    }
}
