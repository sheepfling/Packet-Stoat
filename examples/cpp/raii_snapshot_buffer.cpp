#include <fastdis/fastdis.hpp>

#include "../common/replay_reader.hpp"

#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " packets.fastdispkt\n";
        return 2;
    }

    fastdis::examples::ReplayReader reader(argv[1]);
    if (!reader.is_open()) {
        std::cerr << "could not open " << argv[1] << '\n';
        return 2;
    }

    try {
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

        constexpr std::size_t kBatchCapacity = 1024;
        std::vector<std::vector<std::uint8_t>> packet_storage;
        fastdis::PacketViews packet_views;
        packet_storage.reserve(kBatchCapacity);
        packet_views.reserve(kBatchCapacity);

        std::uint64_t total_seen = 0;
        std::uint64_t total_changed = 0;
        std::uint64_t publish_count = 0;

        auto flush = [&]() {
            if (packet_views.empty()) {
                return;
            }

            fastdis::EntityTableUpdateStats stats = table.ingest(scanner, packet_views, true);
            fastdis::SnapshotView published = snapshots.publish_changed(
                table,
                true);

            total_seen += stats.scan.seen;
            total_changed += published.size();
            publish_count += 1;

            // Engine/render side shape: pin latest view for this scope. The
            // destructor releases the double-buffer read slot automatically.
            fastdis::ScopedSnapshotView view = snapshots.acquire_latest();
            for (const auto& snapshot : view) {
                const fastdis::EntityId id = fastdis::snapshot_entity_id(snapshot);
                const fastdis::WorldCoordinates& loc = fastdis::snapshot_location(snapshot);
                const fastdis::EulerAngles& rot = fastdis::snapshot_orientation(snapshot);
                (void)id;
                (void)loc;
                (void)rot;
                // Unreal/Godot: update actor/node transform here.
            }

            packet_storage.clear();
            packet_views.clear();
        };

        for (;;) {
            std::vector<std::uint8_t> packet;
            std::string error;
            if (!reader.read_next(packet, &error)) {
                if (!error.empty()) {
                    std::cerr << error << '\n';
                    return 1;
                }
                break;
            }
            if (packet.empty()) {
                return 1;
            }

            packet_storage.push_back(std::move(packet));
            const auto& stored = packet_storage.back();
            packet_views.add(stored.data(), stored.size());

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
