#include <fastdis/fastdis.hpp>

#include "../common/replay_reader.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

void emit_latest_entities_json(const fastdis::EntityStateBatch& batch) {
    std::cout << "\"latest_entities\":[";
    for (std::size_t i = 0; i < batch.size(); ++i) {
        const auto& entity = batch[i];
        if (i > 0) {
            std::cout << ',';
        }
        std::cout << "{\"site\":" << entity.entity_id.site
                  << ",\"application\":" << entity.entity_id.application
                  << ",\"entity\":" << entity.entity_id.entity
                  << ",\"force_id\":" << static_cast<unsigned>(entity.force_id)
                  << ",\"location_ecef_m\":[" << entity.location.x << ',' << entity.location.y << ',' << entity.location.z << ']'
                  << ",\"orientation_dis_rad\":[" << entity.orientation.psi << ',' << entity.orientation.theta << ',' << entity.orientation.phi << "]}";
    }
    std::cout << ']';
}

}  // namespace

int main(int argc, char** argv) {
    std::string replay_path;
    std::vector<std::uint8_t> allowed_force_ids;
    bool emit_json = false;

    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " packets.fastdispkt [--json] [--allow-force-id N]\n";
        return 2;
    }
    replay_path = argv[1];
    for (int argi = 2; argi < argc; ++argi) {
        const std::string arg = argv[argi];
        if (arg == "--json") {
            emit_json = true;
            continue;
        }
        if (arg == "--allow-force-id") {
            if (argi + 1 >= argc) {
                std::cerr << "missing value for --allow-force-id\n";
                return 2;
            }
            allowed_force_ids.push_back(static_cast<std::uint8_t>(std::stoul(argv[++argi])));
            continue;
        }
        std::cerr << "unknown argument: " << arg << '\n';
        return 2;
    }

    std::vector<std::vector<std::uint8_t>> packets_storage;
    std::string replay_error;
    if (!fastdis::examples::load_replay_file(replay_path, packets_storage, &replay_error) || packets_storage.empty()) {
        std::cerr << (replay_error.empty() ? "empty or unreadable replay" : replay_error) << '\n';
        return 1;
    }

    fastdis::PacketViews packets(packets_storage.size());
    for (const auto& packet : packets_storage) {
        packets.add(packet.data(), packet.size());
    }

    fastdis::ScanConfig config;
    config.use_entity_state_pose_profile();
    if (!allowed_force_ids.empty()) {
        config.only(fastdis::FilterKind::EntityForceIds, allowed_force_ids.data(), allowed_force_ids.size());
    }

    fastdis::Scanner scanner(config);
    fastdis::EntityStateBatch batch(packets.size());
    fastdis::ScanStats stats{};
    fastdis_scan_stats_init(&stats);
    const auto rc = scanner.try_scan_entity_states(packets.data(), packets.size(), batch, &stats);
    if (rc != FASTDIS_OK) {
        std::cerr << "scan failed: " << fastdis_status_string(rc) << '\n';
        return 1;
    }

    if (emit_json) {
        const auto rejected = static_cast<unsigned long long>(stats.seen - stats.accepted - stats.malformed);
        std::cout << "{"
                  << "\"schema\":\"fastdis.cpp_filter_report.v1\","
                  << "\"surface\":\"cpp\","
                  << "\"mode\":\"filtering\","
                  << "\"packets_received\":" << packets.size() << ','
                  << "\"packets_parsed\":" << stats.seen << ','
                  << "\"packets_accepted\":" << stats.accepted << ','
                  << "\"packets_rejected\":" << rejected << ','
                  << "\"malformed\":" << stats.malformed << ','
                  << "\"unique_entities\":" << batch.size() << ',';
        emit_latest_entities_json(batch);
        std::cout << ",\"errors\":[]}\n";
    } else {
        std::cerr << "seen=" << stats.seen
                  << " malformed=" << stats.malformed
                  << " accepted=" << stats.accepted
                  << " emitted=" << stats.emitted << '\n';
    }
    return 0;
}
