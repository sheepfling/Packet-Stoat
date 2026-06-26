#include <fastdis/fastdis.hpp>

#include "../examples/common/replay_reader.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace {

struct Args {
    std::string packet_file;
};

void usage(const char* argv0) {
    std::cerr << "Usage: " << argv0 << " --packet-file PATH\n";
}

Args parse_args(int argc, char** argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto require_value = [&](const char* name) -> const char* {
            if (i + 1 >= argc) {
                usage(argv[0]);
                std::exit(2);
            }
            (void)name;
            return argv[++i];
        };
        if (a == "--packet-file" || a == "--replay") {
            args.packet_file = require_value("--packet-file");
        } else if (a == "--help" || a == "-h") {
            usage(argv[0]);
            std::exit(0);
        } else {
            usage(argv[0]);
            std::exit(2);
        }
    }
    if (args.packet_file.empty()) {
        usage(argv[0]);
        std::exit(2);
    }
    return args;
}

std::string json_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (const char ch : value) {
        switch (ch) {
        case '\\':
            out += "\\\\";
            break;
        case '"':
            out += "\\\"";
            break;
        case '\n':
            out += "\\n";
            break;
        case '\r':
            out += "\\r";
            break;
        case '\t':
            out += "\\t";
            break;
        default:
            out.push_back(ch);
            break;
        }
    }
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    const Args args = parse_args(argc, argv);
    std::cout << std::setprecision(17);

    std::vector<std::vector<std::uint8_t>> packet_storage;
    std::string error;
    if (!fastdis::examples::load_replay_file(args.packet_file, packet_storage, &error, 0)) {
        std::cerr << "Could not load packet replay file " << args.packet_file << ": " << error << "\n";
        return 2;
    }
    if (packet_storage.empty()) {
        std::cerr << "No packets were loaded from " << args.packet_file << "\n";
        return 2;
    }

    fastdis::PacketViews packet_views;
    packet_views.reserve(packet_storage.size());
    for (const auto& packet : packet_storage) {
        packet_views.add(packet.data(), packet.size());
    }

    try {
        fastdis::Scanner scanner = fastdis::ScannerBuilder()
            .entity_transform_profile()
            .versions({6, 7})
            .pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
            .protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY})
            .build();

        fastdis::EntityTable table = fastdis::EntityTableConfig()
            .reserve(packet_storage.size())
            .build();

        fastdis::SnapshotBuffer snapshots = fastdis::SnapshotBufferConfig()
            .capacity(packet_storage.size())
            .slots(3)
            .build();

        auto started = std::chrono::steady_clock::now();
        fastdis::EntityTableUpdateStats stats{};
        fastdis::SnapshotView published = snapshots.ingest_and_publish_changed(table, scanner, packet_views, true, true, &stats);
        fastdis::SnapshotBatch latest = snapshots.copy_latest(table.size());
        auto stopped = std::chrono::steady_clock::now();
        const double elapsed_seconds = std::chrono::duration<double>(stopped - started).count();

        std::vector<fastdis::EntitySnapshot> latest_entities;
        latest_entities.reserve(latest.size());
        for (const auto& snapshot : latest) {
            latest_entities.push_back(snapshot);
        }
        std::sort(
            latest_entities.begin(),
            latest_entities.end(),
            [](const fastdis::EntitySnapshot& lhs, const fastdis::EntitySnapshot& rhs) {
                const auto& a = lhs.transform.entity_id;
                const auto& b = rhs.transform.entity_id;
                if (a.site != b.site) {
                    return a.site < b.site;
                }
                if (a.application != b.application) {
                    return a.application < b.application;
                }
                return a.entity < b.entity;
            });

        std::cout << "{\n";
        std::cout << "  \"schema\": \"fastdis.native_canonical_benchmark.v1\",\n";
        std::cout << "  \"scenario\": \"entity_state_1x10hz\",\n";
        std::cout << "  \"scenario_suite\": \"core_matrix\",\n";
        std::cout << "  \"mode\": \"replay_native_entity_table\",\n";
        std::cout << "  \"packets_received\": " << packet_storage.size() << ",\n";
        std::cout << "  \"packets_parsed\": " << (stats.scan.seen - stats.scan.malformed) << ",\n";
        std::cout << "  \"malformed\": " << stats.scan.malformed << ",\n";
        std::cout << "  \"entity_state\": " << stats.scan.accepted << ",\n";
        std::cout << "  \"unique_entities\": " << latest_entities.size() << ",\n";
        std::cout << "  \"snapshots_published\": " << published.size() << ",\n";
        std::cout << "  \"elapsed_seconds\": " << elapsed_seconds << ",\n";
        std::cout << "  \"packet_file\": \"" << json_escape(args.packet_file) << "\",\n";
        std::cout << "  \"latest_entities\": [\n";
        for (std::size_t index = 0; index < latest_entities.size(); ++index) {
            const auto& snapshot = latest_entities[index];
            const auto& t = snapshot.transform;
            std::cout << "    {\n";
            std::cout << "      \"site\": " << t.entity_id.site << ",\n";
            std::cout << "      \"application\": " << t.entity_id.application << ",\n";
            std::cout << "      \"entity\": " << t.entity_id.entity << ",\n";
            std::cout << "      \"force_id\": " << static_cast<unsigned>(t.force_id) << ",\n";
            std::cout << "      \"location_ecef_m\": [" << t.location.x << ", " << t.location.y << ", " << t.location.z << "],\n";
            std::cout << "      \"orientation_dis_rad\": [" << t.orientation.psi << ", " << t.orientation.theta << ", " << t.orientation.phi << "]\n";
            std::cout << "    }" << (index + 1 < latest_entities.size() ? "," : "") << "\n";
        }
        std::cout << "  ]\n";
        std::cout << "}\n";
    }
#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
    catch (const fastdis::Error& e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
#endif

    return 0;
}
