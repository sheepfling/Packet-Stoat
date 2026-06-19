#include <fastdis/fastdis.hpp>

#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>

static bool read_be32(std::ifstream& in, std::uint32_t& out) {
    std::uint8_t b[4];
    if (!in.read(reinterpret_cast<char*>(b), 4)) {
        return false;
    }
    out = (static_cast<std::uint32_t>(b[0]) << 24) |
          (static_cast<std::uint32_t>(b[1]) << 16) |
          (static_cast<std::uint32_t>(b[2]) << 8) |
          static_cast<std::uint32_t>(b[3]);
    return true;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " packets.fastdispkt\n";
        return 2;
    }

    std::ifstream in(argv[1], std::ios::binary);
    if (!in) {
        std::cerr << "could not open " << argv[1] << '\n';
        return 2;
    }

    try {
        auto cfg = fastdis::ScanConfig::entity_transform()
                       .only_versions({6, 7})
                       .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
                       .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY});

        fastdis::Scanner scanner(cfg);
        fastdis::EntityTable table(4096);
        fastdis::SnapshotBuffer snapshots(4096);

        constexpr std::size_t kBatchCapacity = 1024;
        std::vector<std::vector<std::uint8_t>> packet_storage;
        std::vector<fastdis::PacketView> packet_views;
        packet_storage.reserve(kBatchCapacity);
        packet_views.reserve(kBatchCapacity);

        std::uint64_t total_seen = 0;
        std::uint64_t total_changed = 0;
        std::uint64_t publish_count = 0;

        auto flush = [&]() {
            if (packet_views.empty()) {
                return;
            }

            fastdis::EntityTableUpdateStats stats{};
            fastdis_entity_table_update_stats_init(&stats);
            fastdis::SnapshotView published = snapshots.ingest_and_publish_changed(
                table,
                scanner,
                packet_views.data(),
                packet_views.size(),
                true,   // advance entity-table tick once for this burst
                true,   // clear emitted change flags after publishing
                &stats);

            total_seen += stats.scan.seen;
            total_changed += published.size();
            publish_count += 1;

            // Engine/render side shape: pin latest view for this scope. The
            // destructor releases the double-buffer read slot automatically.
            fastdis::ScopedSnapshotView view = snapshots.acquire_latest();
            for (const auto& snapshot : view) {
                const auto& id = snapshot.transform.entity_id;
                const auto& loc = snapshot.transform.location;
                const auto& rot = snapshot.transform.orientation;
                (void)id;
                (void)loc;
                (void)rot;
                // Unreal/Godot: update actor/node transform here.
            }

            packet_storage.clear();
            packet_views.clear();
        };

        for (;;) {
            std::uint32_t len = 0;
            if (!read_be32(in, len)) {
                break;
            }
            std::vector<std::uint8_t> packet(len);
            if (!in.read(reinterpret_cast<char*>(packet.data()), len)) {
                std::cerr << "truncated replay file\n";
                return 1;
            }

            packet_storage.push_back(std::move(packet));
            const auto& stored = packet_storage.back();
            packet_views.push_back(fastdis::packet_view(stored.data(), stored.size()));

            if (packet_views.size() == kBatchCapacity) {
                flush();
            }
        }

        flush();

        std::cout << "seen=" << total_seen
                  << " changed_snapshots=" << total_changed
                  << " publishes=" << publish_count
                  << " table_size=" << table.size()
                  << " generation=" << snapshots.generation()
                  << '\n';
    }
#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
    catch (const fastdis::Error& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
#endif

    return 0;
}
