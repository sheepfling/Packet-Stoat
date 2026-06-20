#include <fastdis/fastdis.hpp>

#include "../common/udp_receiver.hpp"

#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace {

struct Args {
    int port = 0;
    std::size_t max_packets = 0;
    std::size_t idle_polls = 200;
    bool json = false;
};

void print_usage(const char* argv0) {
    std::cerr << "usage: " << argv0 << " port [--max-packets N] [--idle-polls N] [--json]\n";
}

bool parse_args(int argc, char** argv, Args& out) {
    if (argc < 2) {
        return false;
    }

    out.port = std::atoi(argv[1]);
    for (int index = 2; index < argc; ++index) {
        const std::string arg = argv[index];
        if (arg == "--json") {
            out.json = true;
            continue;
        }
        if ((arg == "--max-packets" || arg == "--idle-polls") && index + 1 < argc) {
            const auto value = static_cast<std::size_t>(std::strtoull(argv[index + 1], nullptr, 10));
            if (arg == "--max-packets") {
                out.max_packets = value;
            } else {
                out.idle_polls = value;
            }
            index += 1;
            continue;
        }
        return false;
    }
    return true;
}

std::string json_escape(const std::string& value) {
    std::ostringstream out;
    for (char ch : value) {
        switch (ch) {
        case '\\':
            out << "\\\\";
            break;
        case '"':
            out << "\\\"";
            break;
        case '\n':
            out << "\\n";
            break;
        default:
            out << ch;
            break;
        }
    }
    return out.str();
}

} // namespace

int main(int argc, char** argv) {
    Args args{};
    if (!parse_args(argc, argv, args)) {
        print_usage(argv[0]);
        return 2;
    }

    if (args.port <= 0 || args.port > 65535) {
        std::cerr << "invalid UDP port\n";
        return 2;
    }

    fastdis::examples::UdpReceiver receiver(static_cast<std::uint16_t>(args.port));
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
    std::uint64_t accepted_packets = 0;
    std::uint64_t published_snapshots = 0;
    std::uint64_t malformed_packets = 0;
    std::uint64_t idle_poll_count = 0;
    std::size_t burst_count = 0;
    for (;;) {
        std::vector<std::vector<std::uint8_t>> datagrams;
        const std::size_t received = receiver.receive_burst(datagrams, 1024);
        if (received == 0) {
            idle_poll_count += 1;
            if (args.max_packets > 0 && total_packets >= args.max_packets) {
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
            if (args.max_packets > 0 && idle_poll_count >= args.idle_polls) {
                break;
            }
            continue;
        }
        idle_poll_count = 0;
        burst_count += 1;

        fastdis::PacketViews packet_views(received);
        for (const auto& datagram : datagrams) {
            packet_views.add(datagram.data(), datagram.size());
        }

        fastdis::EntityTableUpdateStats stats = table.ingest(scanner, packet_views, true);
        fastdis::SnapshotView published = snapshots.publish_changed(table, true);
        fastdis::ScopedSnapshotView latest = snapshots.acquire_latest();

        total_packets += stats.scan.seen;
        accepted_packets += stats.scan.accepted;
        malformed_packets += (stats.scan.seen - stats.scan.accepted);
        published_snapshots += published.size();
        if (args.json) {
            if (args.max_packets > 0 && total_packets >= args.max_packets) {
                break;
            }
            continue;
        }
        std::cout << "burst_packets=" << received
                  << " accepted=" << stats.scan.accepted
                  << " changed_snapshots=" << published.size()
                  << " latest_view=" << latest.size()
                  << " total_seen=" << total_packets
                  << '\n';
    }

    if (args.json) {
        std::ostringstream out;
        out << "{\n"
            << "  \"schema\": \"fastdis.cpp_udp_burst_report.v1\",\n"
            << "  \"surface\": \"cpp\",\n"
            << "  \"mode\": \"localhost_udp\",\n"
            << "  \"packets_received\": " << total_packets << ",\n"
            << "  \"packets_parsed\": " << accepted_packets << ",\n"
            << "  \"malformed\": " << malformed_packets << ",\n"
            << "  \"entity_state\": " << accepted_packets << ",\n"
            << "  \"burst_count\": " << burst_count << ",\n"
            << "  \"snapshots_published\": " << published_snapshots << ",\n"
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
                << ", \"location_ecef_m\": [" << std::fixed << std::setprecision(6)
                << loc.x << ", " << loc.y << ", " << loc.z << "]"
                << ", \"orientation_dis_rad\": ["
                << rot.psi << ", " << rot.theta << ", " << rot.phi << "]"
                << "}";
        }
        if (batch.size() > 0) {
            out << '\n';
        }
        out << "  ],\n"
            << "  \"errors\": []\n"
            << "}\n";
        std::cout << out.str();
    }
}
