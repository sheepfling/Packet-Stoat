#include "fastdis/fastdis.h"
#include "fastdis/fastdis_frames.hpp"
#include "../examples/common/replay_reader.hpp"

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <functional>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr std::size_t kPduSize = FASTDIS_ENTITY_STATE_FIXED_SIZE;
volatile std::uint64_t g_sink = 0;

void require_ok(fastdis_status_t rc, const char *what) {
    if (rc != FASTDIS_OK) {
        std::cerr << what << " failed: " << fastdis_status_string(rc) << "\n";
        std::exit(2);
    }
}

void require_true(bool ok, const char *what) {
    if (!ok) {
        std::cerr << what << " failed\n";
        std::exit(2);
    }
}

void put_be16(std::uint8_t *p, std::uint16_t value) {
    p[0] = static_cast<std::uint8_t>((value >> 8) & 0xffu);
    p[1] = static_cast<std::uint8_t>(value & 0xffu);
}

void put_be32(std::uint8_t *p, std::uint32_t value) {
    p[0] = static_cast<std::uint8_t>((value >> 24) & 0xffu);
    p[1] = static_cast<std::uint8_t>((value >> 16) & 0xffu);
    p[2] = static_cast<std::uint8_t>((value >> 8) & 0xffu);
    p[3] = static_cast<std::uint8_t>(value & 0xffu);
}

void put_be64(std::uint8_t *p, std::uint64_t value) {
    p[0] = static_cast<std::uint8_t>((value >> 56) & 0xffu);
    p[1] = static_cast<std::uint8_t>((value >> 48) & 0xffu);
    p[2] = static_cast<std::uint8_t>((value >> 40) & 0xffu);
    p[3] = static_cast<std::uint8_t>((value >> 32) & 0xffu);
    p[4] = static_cast<std::uint8_t>((value >> 24) & 0xffu);
    p[5] = static_cast<std::uint8_t>((value >> 16) & 0xffu);
    p[6] = static_cast<std::uint8_t>((value >> 8) & 0xffu);
    p[7] = static_cast<std::uint8_t>(value & 0xffu);
}

void put_be_float(std::uint8_t *p, float value) {
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be32(p, bits);
}

void put_be_double(std::uint8_t *p, double value) {
    std::uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be64(p, bits);
}

void put_vec3f(std::uint8_t *p, float x, float y, float z) {
    put_be_float(p + 0, x);
    put_be_float(p + 4, y);
    put_be_float(p + 8, z);
}

void put_world(std::uint8_t *p, double x, double y, double z) {
    put_be_double(p + 0, x);
    put_be_double(p + 8, y);
    put_be_double(p + 16, z);
}

struct PacketStore {
    std::vector<std::vector<std::uint8_t>> storage;
    std::vector<fastdis_packet_view_t> views;

    void rebuild_views() {
        views.clear();
        views.reserve(storage.size());
        for (std::size_t i = 0; i < storage.size(); ++i) {
            views.push_back(fastdis_packet_view_t{storage[i].data(), storage[i].size(), reinterpret_cast<void *>(i)});
        }
    }
};

std::vector<std::uint8_t> make_entity_state_packet(
    std::size_t i,
    std::size_t entities = 1024,
    std::uint8_t version = 7,
    std::uint8_t exercise_id = 3,
    std::uint8_t pdu_type = FASTDIS_ENTITY_STATE_PDU_TYPE,
    std::uint8_t family = FASTDIS_ENTITY_INFORMATION_FAMILY,
    std::uint16_t declared_length = FASTDIS_ENTITY_STATE_FIXED_SIZE) {

    std::vector<std::uint8_t> p(kPduSize, 0);
    p[0] = version;
    p[1] = exercise_id;
    p[2] = pdu_type;
    p[3] = family;
    put_be32(p.data() + 4, static_cast<std::uint32_t>(0x10000000u + (i & 0x00ffffffu)));
    put_be16(p.data() + 8, declared_length);
    if (version >= 7) {
        p[10] = 0x80;
        p[11] = 0x00;
    } else {
        p[10] = 0x12;
        p[11] = 0x34;
    }

    std::uint8_t *b = p.data() + FASTDIS_HEADER_SIZE;
    const std::uint16_t site = 100;
    const std::uint16_t application = 1;
    const std::uint16_t entity = static_cast<std::uint16_t>(i % std::max<std::size_t>(1, entities));
    put_be16(b + 0, site);
    put_be16(b + 2, application);
    put_be16(b + 4, entity);
    b[6] = static_cast<std::uint8_t>(1 + (i % 4));
    b[7] = 0;

    b[8] = 1;
    b[9] = 2;
    put_be16(b + 10, 840);
    b[12] = 3;
    b[13] = 4;
    b[14] = 5;
    b[15] = 6;

    b[16] = 1;
    b[17] = 2;
    put_be16(b + 18, 840);
    b[20] = 3;
    b[21] = 4;
    b[22] = 5;
    b[23] = 6;

    const float base = static_cast<float>(i % 1000) * 0.001f;
    put_vec3f(b + 24, base + 1.0f, base + 2.0f, base + 3.0f);
    put_world(b + 36, 1000.0 + static_cast<double>(i % 1000), 2000.0, 3000.0);
    put_vec3f(b + 60, base + 0.1f, base + 0.2f, base + 0.3f);
    put_be32(b + 72, 0x01020304u + static_cast<std::uint32_t>(i & 0xffu));
    b[76] = 4;
    for (int j = 0; j < 15; ++j) {
        b[77 + j] = static_cast<std::uint8_t>(j + 1);
    }
    put_vec3f(b + 92, 0.5f, 0.6f, 0.7f);
    put_vec3f(b + 104, 1.5f, 1.6f, 1.7f);
    b[116] = 1;
    const char *marking = "FASTDIS";
    std::memcpy(b + 117, marking, std::strlen(marking));
    put_be32(b + 128, 0x0f0e0d0cu);
    return p;
}

PacketStore make_all_entity(std::size_t count) {
    PacketStore out;
    out.storage.reserve(count);
    for (std::size_t i = 0; i < count; ++i) {
        out.storage.push_back(make_entity_state_packet(i, 1024));
    }
    out.rebuild_views();
    return out;
}

PacketStore make_all_entity_with_cardinality(std::size_t count, std::size_t entities) {
    PacketStore out;
    out.storage.reserve(count);
    for (std::size_t i = 0; i < count; ++i) {
        out.storage.push_back(make_entity_state_packet(i, entities));
    }
    out.rebuild_views();
    return out;
}

PacketStore make_header_mixed_10pct_accept(std::size_t count) {
    PacketStore out;
    out.storage.reserve(count);
    for (std::size_t i = 0; i < count; ++i) {
        if ((i % 10) == 0) {
            out.storage.push_back(make_entity_state_packet(i, 1024));
        } else if ((i % 3) == 0) {
            out.storage.push_back(make_entity_state_packet(i, 1024, 7, 3, 2, FASTDIS_ENTITY_INFORMATION_FAMILY));
        } else if ((i % 3) == 1) {
            out.storage.push_back(make_entity_state_packet(i, 1024, 7, 3, FASTDIS_ENTITY_STATE_PDU_TYPE, 2));
        } else {
            out.storage.push_back(make_entity_state_packet(i, 1024, 6, 4, 2, 2));
        }
    }
    out.rebuild_views();
    return out;
}

PacketStore make_10pct_malformed(std::size_t count) {
    PacketStore out;
    out.storage.reserve(count);
    for (std::size_t i = 0; i < count; ++i) {
        if ((i % 10) == 0) {
            out.storage.push_back(std::vector<std::uint8_t>{7, 3, 1});
        } else {
            out.storage.push_back(make_entity_state_packet(i, 1024));
        }
    }
    out.rebuild_views();
    return out;
}


PacketStore load_packet_file(const std::string &path, std::size_t limit) {
    std::vector<std::vector<std::uint8_t>> packets;
    std::string error;
    if (!fastdis::examples::load_replay_file(path, packets, &error, limit)) {
        std::cerr << "Could not load packet replay file " << path << ": " << error << "\n";
        std::exit(2);
    }
    PacketStore out;
    out.storage = std::move(packets);
    out.rebuild_views();
    return out;
}

void only(fastdis_scan_config_t &config, std::uint32_t kind, std::initializer_list<std::uint8_t> values) {
    std::vector<std::uint8_t> tmp(values.begin(), values.end());
    require_ok(fastdis_scan_config_filter_only(&config, kind, tmp.data(), tmp.size()), "fastdis_scan_config_filter_only");
}

void set_sample(fastdis_scan_config_t &config, std::uint32_t every, std::uint32_t offset = 0) {
    require_ok(fastdis_scan_config_set_sample(&config, every, offset), "fastdis_scan_config_set_sample");
}

void set_fields(fastdis_scan_config_t &config, std::uint64_t fields) {
    require_ok(fastdis_scan_config_set_entity_state_fields(&config, fields), "fastdis_scan_config_set_entity_state_fields");
}

fastdis_scan_config_t config_header_accept_all() {
    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);
    return config;
}

fastdis_scan_config_t config_header_entity_only() {
    fastdis_scan_config_t config;
    fastdis_scan_config_init(&config);
    only(config, FASTDIS_FILTER_VERSION, {7});
    only(config, FASTDIS_FILTER_EXERCISE_ID, {3});
    only(config, FASTDIS_FILTER_PDU_TYPE, {FASTDIS_ENTITY_STATE_PDU_TYPE});
    only(config, FASTDIS_FILTER_PROTOCOL_FAMILY, {FASTDIS_ENTITY_INFORMATION_FAMILY});
    return config;
}

fastdis_scan_config_t config_entity_fields(std::uint64_t fields) {
    fastdis_scan_config_t config = config_header_entity_only();
    set_fields(config, fields);
    return config;
}

fastdis_scan_config_t config_entity_force_one(std::uint64_t fields) {
    fastdis_scan_config_t config = config_entity_fields(fields);
    only(config, FASTDIS_FILTER_ENTITY_FORCE_ID, {1});
    return config;
}

int FASTDIS_CALL on_header_callback(const fastdis_header_t *header,
                                    const std::uint8_t *data,
                                    std::size_t size,
                                    void *packet_user,
                                    void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    (void)callback_user;
    g_sink = g_sink + header->pdu_type + header->version;
    return 0;
}

int FASTDIS_CALL on_entity_callback(const fastdis_entity_state_prefix_t *entity,
                                    const std::uint8_t *data,
                                    std::size_t size,
                                    void *packet_user,
                                    void *callback_user) {
    (void)data;
    (void)size;
    (void)packet_user;
    (void)callback_user;
    g_sink = g_sink + entity->force_id + entity->entity_id.entity + static_cast<std::uint64_t>(entity->fields_present & 0xffu);
    return 0;
}

struct CaseResult {
    std::string name;
    std::string notes;
    std::size_t packets = 0;
    int rounds = 0;
    double best_ms = 0.0;
    double avg_ms = 0.0;
    double best_mpps = 0.0;
    double avg_mpps = 0.0;
    fastdis_scan_stats_t stats{};
};

std::vector<fastdis_entity_snapshot_t> snapshot_all_entities(fastdis_entity_table_t *table) {
    const std::size_t count = fastdis_entity_table_size(table);
    std::vector<fastdis_entity_snapshot_t> snapshots(count);
    fastdis_entity_snapshot_batch_t batch{snapshots.data(), snapshots.size(), 0, 0};
    require_ok(fastdis_entity_table_snapshot_all(table, &batch), "fastdis_entity_table_snapshot_all");
    snapshots.resize(batch.count);
    return snapshots;
}

std::uint64_t convert_snapshots_to_unreal(const std::vector<fastdis_entity_snapshot_t> &snapshots,
                                          fastdis::frames::OrientationPolicy policy) {
    const auto frame = fastdis::frames::LocalEnuFrame::from_degrees(29.5597, -95.0831, 0.0);
    std::uint64_t sink = 0;
    for (const auto &snapshot : snapshots) {
        const auto pose = fastdis::frames::to_unreal_pose(frame, snapshot, policy);
        sink += static_cast<std::uint64_t>(pose.x_cm) + static_cast<std::uint64_t>(pose.y_cm) + static_cast<std::uint64_t>(pose.z_cm);
    }
    return sink;
}

using BenchFn = std::function<fastdis_status_t(fastdis_scan_stats_t *)>;

CaseResult run_case(std::string name,
                    std::string notes,
                    std::size_t packets,
                    int rounds,
                    const BenchFn &fn) {
    fastdis_scan_stats_t warm_stats;
    fastdis_scan_stats_init(&warm_stats);
    const auto warm = fn(&warm_stats);
    if (warm != FASTDIS_OK) {
        std::cerr << "warmup failed for " << name << ": " << fastdis_status_string(warm) << "\n";
        std::exit(2);
    }

    double best_ms = std::numeric_limits<double>::infinity();
    double total_ms = 0.0;
    fastdis_scan_stats_t last_stats{};
    for (int round = 0; round < rounds; ++round) {
        fastdis_scan_stats_t stats;
        fastdis_scan_stats_init(&stats);
        const auto start = std::chrono::steady_clock::now();
        const auto rc = fn(&stats);
        const auto stop = std::chrono::steady_clock::now();
        if (rc != FASTDIS_OK) {
            std::cerr << "benchmark failed for " << name << ": " << fastdis_status_string(rc) << "\n";
            std::exit(2);
        }
        const double ms = std::chrono::duration<double, std::milli>(stop - start).count();
        best_ms = std::min(best_ms, ms);
        total_ms += ms;
        last_stats = stats;
    }

    const double avg_ms = total_ms / static_cast<double>(rounds);
    CaseResult result;
    result.name = std::move(name);
    result.notes = std::move(notes);
    result.packets = packets;
    result.rounds = rounds;
    result.best_ms = best_ms;
    result.avg_ms = avg_ms;
    result.best_mpps = (static_cast<double>(packets) / 1'000'000.0) / (best_ms / 1000.0);
    result.avg_mpps = (static_cast<double>(packets) / 1'000'000.0) / (avg_ms / 1000.0);
    result.stats = last_stats;
    return result;
}

std::string json_escape(const std::string &input) {
    std::ostringstream out;
    for (char c : input) {
        switch (c) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default: out << c; break;
        }
    }
    return out.str();
}

void print_table(const std::vector<CaseResult> &results) {
    std::cout << "fastdis native benchmark ABI=" << fastdis_abi_version()
              << " version=" << fastdis_version_string()
              << " sink=" << g_sink << "\n\n";
    std::cout << std::left << std::setw(38) << "case"
              << std::right << std::setw(11) << "best Mpps"
              << std::setw(11) << "avg Mpps"
              << std::setw(11) << "best ms"
              << std::setw(11) << "accepted"
              << std::setw(11) << "emitted"
              << std::setw(11) << "malformed"
              << "  notes\n";
    std::cout << std::string(120, '-') << "\n";
    for (const auto &r : results) {
        std::cout << std::left << std::setw(38) << r.name
                  << std::right << std::setw(11) << std::fixed << std::setprecision(2) << r.best_mpps
                  << std::setw(11) << std::fixed << std::setprecision(2) << r.avg_mpps
                  << std::setw(11) << std::fixed << std::setprecision(2) << r.best_ms
                  << std::setw(11) << r.stats.accepted
                  << std::setw(11) << r.stats.emitted
                  << std::setw(11) << r.stats.malformed
                  << "  " << r.notes << "\n";
    }
}

void print_csv(const std::vector<CaseResult> &results) {
    std::cout << "case,packets,rounds,best_ms,avg_ms,best_mpps,avg_mpps,seen,malformed,accepted,emitted,notes\n";
    for (const auto &r : results) {
        std::cout << r.name << ','
                  << r.packets << ','
                  << r.rounds << ','
                  << std::fixed << std::setprecision(6) << r.best_ms << ','
                  << std::fixed << std::setprecision(6) << r.avg_ms << ','
                  << std::fixed << std::setprecision(6) << r.best_mpps << ','
                  << std::fixed << std::setprecision(6) << r.avg_mpps << ','
                  << r.stats.seen << ','
                  << r.stats.malformed << ','
                  << r.stats.accepted << ','
                  << r.stats.emitted << ','
                  << '"' << json_escape(r.notes) << '"' << "\n";
    }
}

void print_json(const std::vector<CaseResult> &results) {
    std::cout << "{\n  \"abi\": " << fastdis_abi_version()
              << ",\n  \"version\": \"" << json_escape(fastdis_version_string()) << "\",\n  \"results\": [\n";
    for (std::size_t i = 0; i < results.size(); ++i) {
        const auto &r = results[i];
        std::cout << "    {\"case\": \"" << json_escape(r.name)
                  << "\", \"packets\": " << r.packets
                  << ", \"rounds\": " << r.rounds
                  << ", \"best_ms\": " << std::fixed << std::setprecision(6) << r.best_ms
                  << ", \"avg_ms\": " << std::fixed << std::setprecision(6) << r.avg_ms
                  << ", \"best_mpps\": " << std::fixed << std::setprecision(6) << r.best_mpps
                  << ", \"avg_mpps\": " << std::fixed << std::setprecision(6) << r.avg_mpps
                  << ", \"seen\": " << r.stats.seen
                  << ", \"malformed\": " << r.stats.malformed
                  << ", \"accepted\": " << r.stats.accepted
                  << ", \"emitted\": " << r.stats.emitted
                  << ", \"notes\": \"" << json_escape(r.notes) << "\"}";
        if (i + 1 != results.size()) {
            std::cout << ',';
        }
        std::cout << "\n";
    }
    std::cout << "  ]\n}\n";
}

struct Args {
    std::size_t packets = 1'000'000;
    int rounds = 5;
    std::string format = "table";
    std::string packet_file;
};

void usage(const char *argv0) {
    std::cerr << "Usage: " << argv0 << " [--packets N] [--rounds N] [--format table|csv|json] [--packet-file PATH]\n";
}

Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto require_value = [&](const char *name) -> const char * {
            if (i + 1 >= argc) {
                usage(argv[0]);
                std::exit(2);
            }
            (void)name;
            return argv[++i];
        };
        if (a == "--packets") {
            args.packets = static_cast<std::size_t>(std::stoull(require_value("--packets")));
        } else if (a == "--rounds") {
            args.rounds = std::stoi(require_value("--rounds"));
        } else if (a == "--format") {
            args.format = require_value("--format");
        } else if (a == "--packet-file" || a == "--replay") {
            args.packet_file = require_value("--packet-file");
        } else if (a == "--help" || a == "-h") {
            usage(argv[0]);
            std::exit(0);
        } else {
            usage(argv[0]);
            std::exit(2);
        }
    }
    if ((args.packets == 0 && args.packet_file.empty()) || args.rounds <= 0) {
        usage(argv[0]);
        std::exit(2);
    }
    if (args.format != "table" && args.format != "csv" && args.format != "json") {
        usage(argv[0]);
        std::exit(2);
    }
    return args;
}

} // namespace

int main(int argc, char **argv) {
    const Args args = parse_args(argc, argv);

    PacketStore all = args.packet_file.empty() ? make_all_entity(args.packets) : load_packet_file(args.packet_file, args.packets);
    PacketStore one_entity = make_all_entity_with_cardinality(args.packets, 1);
    PacketStore hundred_entities = make_all_entity_with_cardinality(args.packets, 100);
    PacketStore tenk_entities = make_all_entity_with_cardinality(args.packets, 10'000);
    const std::size_t packet_count = all.views.size();
    if (packet_count == 0) {
        std::cerr << "No packets to benchmark\n";
        return 2;
    }
    PacketStore mixed = make_header_mixed_10pct_accept(packet_count);
    PacketStore malformed = make_10pct_malformed(packet_count);

    fastdis_scan_config_t header_all = config_header_accept_all();
    fastdis_scan_config_t header_entity = config_header_entity_only();
    fastdis_scan_config_t header_entity_sampled = config_header_entity_only();
    set_sample(header_entity_sampled, 100);

    fastdis_scan_config_t entity_routing = config_entity_fields(FASTDIS_ES_FIELD_ROUTING);
    fastdis_scan_config_t entity_pose = config_entity_fields(FASTDIS_ES_FIELD_POSE);
    fastdis_scan_config_t entity_all = config_entity_fields(FASTDIS_ES_FIELD_ALL);
    fastdis_scan_config_t entity_pose_sampled = config_entity_fields(FASTDIS_ES_FIELD_POSE);
    set_sample(entity_pose_sampled, 100);
    fastdis_scan_config_t entity_force_one = config_entity_force_one(FASTDIS_ES_FIELD_ROUTING);

    fastdis_scanner_t *scanner_pose = fastdis_scanner_create(&entity_pose);
    require_true(scanner_pose != nullptr, "fastdis_scanner_create(scanner_pose)");

    fastdis_scanner_t *scanner_allow = fastdis_scanner_create(&entity_routing);
    require_true(scanner_allow != nullptr, "fastdis_scanner_create(scanner_allow)");
    std::vector<fastdis_entity_id_t> allow_ids;
    allow_ids.reserve(32);
    for (std::uint16_t id = 0; id < 32; ++id) {
        allow_ids.push_back(fastdis_entity_id_t{100u, 1u, id});
    }
    require_ok(fastdis_scanner_set_entity_ids(scanner_allow, FASTDIS_ENTITY_ID_FILTER_ALLOW, allow_ids.data(), allow_ids.size()),
               "fastdis_scanner_set_entity_ids");

    fastdis_scanner_t *scanner_allow_1024 = fastdis_scanner_create(&entity_routing);
    require_true(scanner_allow_1024 != nullptr, "fastdis_scanner_create(scanner_allow_1024)");
    std::vector<fastdis_entity_id_t> allow_ids_1024;
    allow_ids_1024.reserve(1024);
    for (std::uint16_t id = 0; id < 1024; ++id) {
        allow_ids_1024.push_back(fastdis_entity_id_t{100u, 1u, id});
    }
    require_ok(fastdis_scanner_set_entity_ids(scanner_allow_1024,
                                              FASTDIS_ENTITY_ID_FILTER_ALLOW,
                                              allow_ids_1024.data(),
                                              allow_ids_1024.size()),
               "fastdis_scanner_set_entity_ids(scanner_allow_1024)");

    std::vector<fastdis_entity_state_prefix_t> entity_batch_storage(packet_count);
    fastdis_entity_state_batch_t entity_batch{entity_batch_storage.data(), entity_batch_storage.size(), 0, 0};
    std::vector<fastdis_entity_transform_t> transform_batch_storage(packet_count);
    fastdis_entity_transform_batch_t transform_batch{transform_batch_storage.data(), transform_batch_storage.size(), 0, 0};
    std::vector<fastdis_entity_transform_t> small_transform_storage(packet_count / 2 + 1);
    fastdis_entity_transform_batch_t small_transform_batch{small_transform_storage.data(), small_transform_storage.size(), 0, 0};

    fastdis_entity_table_t *state_table = fastdis_entity_table_create(2048);
    require_true(state_table != nullptr, "fastdis_entity_table_create");
    fastdis_entity_table_t *dirty_table = fastdis_entity_table_create(2048);
    require_true(dirty_table != nullptr, "fastdis_entity_table_create(dirty_table)");
    fastdis_entity_table_update_stats_t dirty_table_stats;
    fastdis_entity_table_update_stats_init(&dirty_table_stats);
    require_ok(
        fastdis_entity_table_ingest_packets(dirty_table, scanner_pose, all.views.data(), all.views.size(), 1, &dirty_table_stats),
        "prefill dirty_table");
    const std::size_t dirty_entity_count = fastdis_entity_table_size(dirty_table);

    fastdis_entity_snapshot_buffer_t *snapshot_buffer = fastdis_entity_snapshot_buffer_create(2048);
    require_true(snapshot_buffer != nullptr, "fastdis_entity_snapshot_buffer_create");
    fastdis_entity_snapshot_buffer_t *snapshot_buffer_triple = fastdis_entity_snapshot_buffer_create_ex(2048, 3);
    require_true(snapshot_buffer_triple != nullptr, "fastdis_entity_snapshot_buffer_create_ex");

    const std::vector<fastdis_entity_snapshot_t> dirty_snapshots = snapshot_all_entities(dirty_table);

    std::vector<CaseResult> results;
    results.reserve(40);

    results.push_back(run_case(
        "header_all_no_callback",
        "12-byte header only; no Python/engine callback",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(all.views.data(), all.views.size(), &header_all, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "synthetic_header_only",
        "Alpha 2 synthetic header-only baseline",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(all.views.data(), all.views.size(), &header_all, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "header_all_callback_every",
        "header callback on every valid packet",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(all.views.data(), all.views.size(), &header_all, on_header_callback, nullptr, stats);
        }));

    results.push_back(run_case(
        "header_filter_90pct_reject",
        "version/exercise/type/family filter; 10% accepted",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(mixed.views.data(), mixed.views.size(), &header_entity, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "mixed_pdu_noise",
        "Alpha 2 mixed-PDU noise workload with 10% accepted entity traffic",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(mixed.views.data(), mixed.views.size(), &header_entity, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "header_filter_90pct_reject_cb",
        "same filter; callback only for accepted 10%",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(mixed.views.data(), mixed.views.size(), &header_entity, on_header_callback, nullptr, stats);
        }));

    results.push_back(run_case(
        "header_downsample_1pct_cb",
        "all accepted; callback every 100th packet",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(all.views.data(), all.views.size(), &header_entity_sampled, on_header_callback, nullptr, stats);
        }));

    results.push_back(run_case(
        "header_10pct_malformed",
        "short packets counted as malformed",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_packets(malformed.views.data(), malformed.views.size(), &header_all, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_routing_no_callback",
        "Entity State fixed prefix: id + force only",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_routing, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_pose_no_callback",
        "Entity State id + force + location + orientation",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_pose, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "synthetic_entity_state_1_entity",
        "Entity State transform workload with one hot entity",
        one_entity.views.size(),
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(one_entity.views.data(), one_entity.views.size(), &entity_pose, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "synthetic_entity_state_100_entities",
        "Entity State transform workload with 100 active entities",
        hundred_entities.views.size(),
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(hundred_entities.views.data(), hundred_entities.views.size(), &entity_pose, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "synthetic_entity_state_10k_entities",
        "Entity State transform workload with 10k active entities",
        tenk_entities.views.size(),
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(tenk_entities.views.data(), tenk_entities.views.size(), &entity_pose, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_all_no_callback",
        "Entity State full fixed prefix",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_all, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_pose_callback_every",
        "pose decode plus callback every packet",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_pose, on_entity_callback, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_pose_downsample_1pct_cb",
        "pose decode; callback every 100th packet",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_pose_sampled, on_entity_callback, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_force_filter_25pct",
        "native force-id filter; force==1",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_force_one, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "filtered_force_ids",
        "Alpha 2 named force-ID filter workload",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_packets(all.views.data(), all.views.size(), &entity_force_one, nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "scanner_reuse_pose_no_callback",
        "opaque scanner context reused across rounds",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scanner_scan_entity_state_packets(scanner_pose, all.views.data(), all.views.size(), nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "scanner_entity_id_allow_32",
        "native unordered_set allowlist: 32 of 1024 entity IDs",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scanner_scan_entity_state_packets(scanner_allow, all.views.data(), all.views.size(), nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_allowlist_32",
        "Alpha 2 named entity allowlist workload with 32 IDs",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scanner_scan_entity_state_packets(scanner_allow, all.views.data(), all.views.size(), nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_allowlist_1024",
        "Alpha 2 named entity allowlist workload with 1024 IDs",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scanner_scan_entity_state_packets(scanner_allow_1024, all.views.data(), all.views.size(), nullptr, nullptr, stats);
        }));

    results.push_back(run_case(
        "entity_pose_to_batch",
        "callback-free Entity State pose decode into caller-owned array",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_state_to_batch(all.views.data(), all.views.size(), &entity_pose, &entity_batch, stats);
        }));

    results.push_back(run_case(
        "entity_transform_to_batch",
        "callback-free compact engine transform output",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_transforms_to_batch(all.views.data(), all.views.size(), &entity_pose, &transform_batch, stats);
        }));

    results.push_back(run_case(
        "entity_transform_to_batch_50pct_capacity",
        "compact transform output with undersized output buffer",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scan_entity_transforms_to_batch(all.views.data(), all.views.size(), &entity_pose, &small_transform_batch, stats);
        }));

    results.push_back(run_case(
        "scanner_transform_to_batch_allow_32",
        "scanner allowlist plus callback-free compact transform output",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            return fastdis_scanner_scan_entity_transforms_to_batch(scanner_allow, all.views.data(), all.views.size(), &transform_batch, stats);
        }));

    results.push_back(run_case(
        "entity_table_ingest_latest",
        "scan transforms directly into native latest-state entity table",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_table_update_stats_t table_stats;
            fastdis_entity_table_update_stats_init(&table_stats);
            fastdis_status_t rc = fastdis_entity_table_ingest_packets(
                state_table, scanner_pose, all.views.data(), all.views.size(), 1, &table_stats);
            if (rc == FASTDIS_OK && stats != nullptr) {
                *stats = table_stats.scan;
                g_sink += fastdis_entity_table_size(state_table);
            }
            return rc;
        }));

    results.push_back(run_case(
        "entity_snapshot_publish_changed_dirty",
        "publish already-dirty changed snapshots into double buffer; no packet scan",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t view;
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, dirty_table, 0, &view);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = view.count + view.dropped;
                stats->emitted = view.count;
                g_sink += view.count + view.dropped;
            }
            return rc;
        }));

    results.push_back(run_case(
        "snapshot_publish_changed",
        "Alpha 2 named changed-snapshot publish workload",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t view;
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, dirty_table, 0, &view);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = view.count + view.dropped;
                stats->emitted = view.count;
                g_sink += view.count + view.dropped;
            }
            return rc;
        }));

    results.push_back(run_case(
        "entity_snapshot_publish_all",
        "publish all latest-state snapshots into double buffer; no packet scan",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t view;
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, dirty_table, &view);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = view.count + view.dropped;
                stats->emitted = view.count;
                g_sink += view.count + view.dropped;
            }
            return rc;
        }));

    results.push_back(run_case(
        "snapshot_publish_all",
        "Alpha 2 named publish-all snapshot workload",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t view;
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_all(snapshot_buffer, dirty_table, &view);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = view.count + view.dropped;
                stats->emitted = view.count;
                g_sink += view.count + view.dropped;
            }
            return rc;
        }));

    results.push_back(run_case(
        "snapshot_acquire_release",
        "publish changed snapshots, then acquire/release latest view without rescanning packets",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t published{};
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, dirty_table, 0, &published);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t acquired{};
            rc = fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &acquired);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            g_sink += acquired.count + acquired.dropped;
            rc = fastdis_entity_snapshot_buffer_release(snapshot_buffer, &acquired);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = published.count + published.dropped;
                stats->emitted = acquired.count;
            }
            return rc;
        }));

    results.push_back(run_case(
        "snapshot_delayed_reader_double",
        "double-slot buffer under delayed reader pressure",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t pinned{};
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, dirty_table, 0, &pinned);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t latest{};
            rc = fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &latest);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t second_publish{};
            rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, dirty_table, 0, &second_publish);
            fastdis_entity_snapshot_buffer_release(snapshot_buffer, &latest);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = second_publish.count + second_publish.dropped;
                stats->emitted = second_publish.count;
            } else if (rc == FASTDIS_ERR_BUSY && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->malformed = 1;
            }
            return FASTDIS_OK;
        }));

    results.push_back(run_case(
        "snapshot_delayed_reader_triple",
        "triple-slot buffer under delayed reader pressure",
        dirty_entity_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_snapshot_view_t pinned{};
            fastdis_status_t rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer_triple, dirty_table, 0, &pinned);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t latest{};
            rc = fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer_triple, &latest);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t second_publish{};
            rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer_triple, dirty_table, 0, &second_publish);
            fastdis_entity_snapshot_buffer_release(snapshot_buffer_triple, &latest);
            if (rc == FASTDIS_OK && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->accepted = second_publish.count + second_publish.dropped;
                stats->emitted = second_publish.count;
            } else if (rc == FASTDIS_ERR_BUSY && stats != nullptr) {
                stats->seen = dirty_entity_count;
                stats->malformed = 1;
            }
            return FASTDIS_OK;
        }));

    results.push_back(run_case(
        "entity_table_ingest_publish_changed",
        "ingest latest-state table, then publish changed snapshots into double buffer",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_table_update_stats_t table_stats;
            fastdis_entity_table_update_stats_init(&table_stats);
            fastdis_status_t rc = fastdis_entity_table_ingest_packets(
                state_table, scanner_pose, all.views.data(), all.views.size(), 1, &table_stats);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t view;
            rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, state_table, 1, &view);
            if (rc == FASTDIS_OK && stats != nullptr) {
                *stats = table_stats.scan;
                g_sink += view.count + view.dropped;
            }
            return rc;
        }));

    results.push_back(run_case(
        "entity_table_ingest_publish_acquire_release",
        "ingest, publish changed snapshots, acquire/release latest view",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_table_update_stats_t table_stats;
            fastdis_entity_table_update_stats_init(&table_stats);
            fastdis_status_t rc = fastdis_entity_table_ingest_packets(
                state_table, scanner_pose, all.views.data(), all.views.size(), 1, &table_stats);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t view;
            rc = fastdis_entity_snapshot_buffer_publish_changed(snapshot_buffer, state_table, 1, &view);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            fastdis_entity_snapshot_view_t acquired;
            rc = fastdis_entity_snapshot_buffer_acquire_latest(snapshot_buffer, &acquired);
            if (rc != FASTDIS_OK) {
                return rc;
            }
            g_sink += acquired.count + acquired.dropped;
            fastdis_status_t release_rc = fastdis_entity_snapshot_buffer_release(snapshot_buffer, &acquired);
            if (release_rc != FASTDIS_OK) {
                return release_rc;
            }
            if (stats != nullptr) {
                *stats = table_stats.scan;
            }
            return FASTDIS_OK;
        }));

    results.push_back(run_case(
        "entity_table_ingest_publish_combined",
        "single ABI call: ingest latest-state table and publish changed double-buffer snapshot",
        packet_count,
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            fastdis_entity_table_update_stats_t table_stats;
            fastdis_entity_table_update_stats_init(&table_stats);
            fastdis_entity_snapshot_view_t view;
            fastdis_status_t rc = fastdis_entity_table_ingest_packets_publish_changed(
                state_table,
                scanner_pose,
                all.views.data(),
                all.views.size(),
                1,
                1,
                snapshot_buffer,
                &table_stats,
                &view);
            if (rc == FASTDIS_OK) {
                g_sink += view.count + view.dropped;
                if (stats != nullptr) {
                    *stats = table_stats.scan;
                }
            }
            return rc;
        }));

    results.push_back(run_case(
        "frame_transform_off",
        "snapshot walk without frame conversion",
        dirty_snapshots.size(),
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            for (const auto &snapshot : dirty_snapshots) {
                g_sink += snapshot.transform.entity_id.entity + static_cast<std::uint64_t>(snapshot.change_flags);
            }
            if (stats != nullptr) {
                stats->seen = dirty_snapshots.size();
                stats->accepted = dirty_snapshots.size();
                stats->emitted = dirty_snapshots.size();
            }
            return FASTDIS_OK;
        }));

    results.push_back(run_case(
        "frame_transform_on",
        "snapshot walk with ENU-to-Unreal pose conversion",
        dirty_snapshots.size(),
        args.rounds,
        [&] (fastdis_scan_stats_t *stats) {
            g_sink += convert_snapshots_to_unreal(dirty_snapshots, fastdis::frames::OrientationPolicy::PositionOnly);
            if (stats != nullptr) {
                stats->seen = dirty_snapshots.size();
                stats->accepted = dirty_snapshots.size();
                stats->emitted = dirty_snapshots.size();
            }
            return FASTDIS_OK;
        }));

    fastdis_entity_snapshot_buffer_destroy(snapshot_buffer_triple);
    fastdis_entity_snapshot_buffer_destroy(snapshot_buffer);
    fastdis_entity_table_destroy(dirty_table);
    fastdis_entity_table_destroy(state_table);
    fastdis_scanner_destroy(scanner_pose);
    fastdis_scanner_destroy(scanner_allow);
    fastdis_scanner_destroy(scanner_allow_1024);

    if (args.format == "table") {
        print_table(results);
    } else if (args.format == "csv") {
        print_csv(results);
    } else {
        print_json(results);
    }

    return 0;
}
