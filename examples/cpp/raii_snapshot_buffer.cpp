#include <fastdis/fastdis.hpp>

#include "../common/replay_reader.hpp"

#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

namespace {

std::string json_report(
    std::uint64_t total_seen,
    std::uint64_t total_changed,
    std::uint64_t publish_count,
    const fastdis::EntityTable& table) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(6);
    out << "{\n"
        << "  \"schema\": \"fastdis.cpp_replay_report.v1\",\n"
        << "  \"surface\": \"cpp\",\n"
        << "  \"mode\": \"replay\",\n"
        << "  \"packets_received\": " << total_seen << ",\n"
        << "  \"packets_parsed\": " << total_seen << ",\n"
        << "  \"malformed\": 0,\n"
        << "  \"entity_state\": " << total_seen << ",\n"
        << "  \"changed_snapshots\": " << total_changed << ",\n"
        << "  \"publishes\": " << publish_count << ",\n"
        << "  \"unique_entities\": " << table.size() << ",\n"
        << "  \"latest_entities\": [";

    auto batch = table.snapshot_all(table.size());
    for (std::size_t index = 0; index < batch.size(); ++index) {
        if (index != 0) {
            out << ',';
        }
        const auto& snapshot = batch[index];
        const auto id = fastdis::snapshot_entity_id(snapshot);
        const auto& loc = fastdis::snapshot_location(snapshot);
        const auto& rot = fastdis::snapshot_orientation(snapshot);
        out << "\n    {"
            << "\"site\": " << id.site
            << ", \"application\": " << id.application
            << ", \"entity\": " << id.entity
            << ", \"force_id\": " << static_cast<unsigned>(snapshot.transform.force_id)
            << ", \"location_ecef_m\": [" << loc.x << ", " << loc.y << ", " << loc.z << "]"
            << ", \"orientation_dis_rad\": [" << rot.psi << ", " << rot.theta << ", " << rot.phi << "]"
            << "}";
    }
    if (batch.size() > 0) {
        out << '\n';
    }
    out << "  ],\n"
        << "  \"errors\": []\n"
        << "}\n";
    return out.str();
}

} // namespace

int main(int argc, char** argv) {
    bool emit_json = false;
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " packets.fastdispkt [--json]\n";
        return 2;
    }
    for (int index = 2; index < argc; ++index) {
        const std::string arg = argv[index];
        if (arg == "--json") {
            emit_json = true;
            continue;
        }
        std::cerr << "unknown argument: " << arg << '\n';
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

        if (emit_json) {
            std::cout << json_report(total_seen, total_changed, publish_count, table);
        } else {
            std::cout << "seen=" << total_seen
                      << " changed_snapshots=" << total_changed
                      << " publishes=" << publish_count
                      << " table_size=" << table.size()
                      << " generation=" << snapshots.generation()
                      << '\n';
        }
    }
#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
    catch (const fastdis::Error& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
#endif

    return 0;
}
