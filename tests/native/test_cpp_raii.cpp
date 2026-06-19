#include <fastdis/fastdis.hpp>

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <utility>

namespace {

void put_be16(uint8_t* p, uint16_t value) {
    p[0] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[1] = static_cast<uint8_t>(value & 0xffu);
}

void put_be32(uint8_t* p, uint32_t value) {
    p[0] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[3] = static_cast<uint8_t>(value & 0xffu);
}

void put_be64(uint8_t* p, uint64_t value) {
    p[0] = static_cast<uint8_t>((value >> 56) & 0xffu);
    p[1] = static_cast<uint8_t>((value >> 48) & 0xffu);
    p[2] = static_cast<uint8_t>((value >> 40) & 0xffu);
    p[3] = static_cast<uint8_t>((value >> 32) & 0xffu);
    p[4] = static_cast<uint8_t>((value >> 24) & 0xffu);
    p[5] = static_cast<uint8_t>((value >> 16) & 0xffu);
    p[6] = static_cast<uint8_t>((value >> 8) & 0xffu);
    p[7] = static_cast<uint8_t>(value & 0xffu);
}

void put_be_float(uint8_t* p, float value) {
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be32(p, bits);
}

void put_be_double(uint8_t* p, double value) {
    uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    put_be64(p, bits);
}

void put_vec3f(uint8_t* p, float x, float y, float z) {
    put_be_float(p + 0, x);
    put_be_float(p + 4, y);
    put_be_float(p + 8, z);
}

void put_world(uint8_t* p, double x, double y, double z) {
    put_be_double(p + 0, x);
    put_be_double(p + 8, y);
    put_be_double(p + 16, z);
}

void make_entity_state_pdu(uint8_t* p,
                           uint16_t site,
                           uint16_t application,
                           uint16_t entity,
                           double x,
                           uint8_t force_id = 2) {
    std::memset(p, 0, 160);
    p[0] = 7;
    p[1] = 3;
    p[2] = FASTDIS_ENTITY_STATE_PDU_TYPE;
    p[3] = FASTDIS_ENTITY_INFORMATION_FAMILY;
    put_be32(p + 4, 0x01020304u);
    put_be16(p + 8, FASTDIS_ENTITY_STATE_FIXED_SIZE);
    p[10] = 0x80;
    p[11] = 0x00;

    uint8_t* b = p + FASTDIS_HEADER_SIZE;
    put_be16(b + 0, site);
    put_be16(b + 2, application);
    put_be16(b + 4, entity);
    b[6] = force_id;
    b[7] = 0;

    b[8] = 1;
    b[9] = 2;
    put_be16(b + 10, 840);
    b[12] = 3;
    b[13] = 4;
    b[14] = 5;
    b[15] = 6;

    put_vec3f(b + 24, 1.25f, -2.5f, 3.75f);
    put_world(b + 36, x, 20.0, 30.0);
    put_vec3f(b + 60, 0.1f, 0.2f, 0.3f);
    put_be32(b + 72, 0xAABBCCDDu);
}

bool nearf(float a, float b) { return std::fabs(a - b) < 0.0001f; }

} // namespace

int main() {
    assert(fastdis_abi_version() == FASTDIS_ABI_VERSION);
    assert(fastdis::abi_version() == FASTDIS_ABI_VERSION);
    assert(fastdis::abi_version_constant == 8u);

    std::array<uint8_t, 160> p1{};
    std::array<uint8_t, 160> p2{};
    make_entity_state_pdu(p1.data(), 0x1111u, 0x2222u, 0x3333u, 10.0);
    make_entity_state_pdu(p2.data(), 0x1111u, 0x2222u, 0x4444u, 40.0);

    fastdis::Header header = fastdis::parse_header(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(header.version == 7u);
    assert(header.pdu_type == FASTDIS_ENTITY_STATE_PDU_TYPE);

    fastdis::Header try_header{};
    assert(fastdis::try_parse_header(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE, try_header) == FASTDIS_OK);
    assert(try_header.protocol_family == FASTDIS_ENTITY_INFORMATION_FAMILY);

    fastdis::EntityTransform transform = fastdis::parse_entity_transform(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);
    assert(transform.entity_id.site == 0x1111u);
    assert(transform.location.x == 10.0);
    assert(nearf(transform.orientation.theta, 0.2f));

    fastdis::ScanConfig cfg = fastdis::ScanConfig::entity_transform();
    cfg.only_versions({7})
       .only_entity_force_ids({2})
       .sample(1);
    assert(cfg.contains(fastdis::FilterKind::PduTypes, FASTDIS_ENTITY_STATE_PDU_TYPE));
    assert(cfg.contains(fastdis::FilterKind::ProtocolFamilies, FASTDIS_ENTITY_INFORMATION_FAMILY));

    fastdis::Scanner scanner(cfg);
    assert(scanner);
    scanner.allow_entity_ids({fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u),
                              fastdis::make_entity_id(0x1111u, 0x2222u, 0x4444u)});
    assert(scanner.entity_id_filter_mode() == fastdis::EntityIdFilterMode::Allow);
    assert(scanner.entity_id_count() == 2u);
    assert(scanner.contains_entity_id(fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u)));

    fastdis::PacketViews packets;
    packets.add(p1.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE)
           .add(p2.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);

    fastdis::TransformBatch transforms(4);
    fastdis::ScanStats scan_stats = scanner.scan_transforms(packets, transforms);
    assert(scan_stats.seen == 2u);
    assert(scan_stats.accepted == 2u);
    assert(transforms.size() == 2u);
    assert(transforms.dropped() == 0u);
    assert(transforms[0].location.x == 10.0);
    assert(transforms[1].location.x == 40.0);

    scanner.entity_id_filter_mode(fastdis::EntityIdFilterMode::Disabled);
    assert(scanner.entity_id_filter_mode() == fastdis::EntityIdFilterMode::Disabled);

    fastdis::EntityTable table(8);
    assert(table);
    fastdis::EntityTableUpdateStats ingest_stats = table.ingest(scanner, packets, true);
    assert(ingest_stats.new_entities == 2u);
    assert(table.size() == 2u);
    assert(table.tick() == 1u);

    fastdis::EntitySnapshot got = table.get(fastdis::make_entity_id(0x1111u, 0x2222u, 0x3333u));
    assert(got.transform.location.x == 10.0);

    fastdis::SnapshotBatch changed_batch = table.snapshot_changed(4, false);
    assert(changed_batch.size() == 2u);

    fastdis::SnapshotBuffer buffer(4);
    assert(buffer);
    fastdis::SnapshotView published = buffer.publish_changed(table, false);
    assert(published.size() == 2u);
    assert(published.generation() == 1u);

    {
        fastdis::ScopedSnapshotView view = buffer.acquire_latest();
        assert(view.owns_release());
        assert(view.size() == 2u);
        assert(view[0].transform.entity_id.site == 0x1111u);

        // One slot is pinned; publishing into the other slot succeeds.
        fastdis::SnapshotView second_publish;
        assert(buffer.try_publish_all(table, &second_publish) == FASTDIS_OK);
        // Both slots would be unavailable now, so the native handoff exposes back-pressure.
        assert(buffer.try_publish_all(table, &second_publish) == FASTDIS_ERR_BUSY);
    }

    // The scoped view released on scope exit, so publishing succeeds again.
    assert(buffer.try_publish_all(table, &published) == FASTDIS_OK);
    table.mark_all_clean();

    table.mark_all_clean();

    std::array<uint8_t, 160> p1_changed{};
    make_entity_state_pdu(p1_changed.data(), 0x1111u, 0x2222u, 0x3333u, 100.0);
    fastdis::PacketViews changed_packets;
    changed_packets.add(p1_changed.data(), FASTDIS_ENTITY_STATE_FIXED_SIZE);

    fastdis::EntityTableUpdateStats combined_stats{};
    fastdis_entity_table_update_stats_init(&combined_stats);
    fastdis::SnapshotView combined_view = buffer.ingest_and_publish_changed(
        table,
        scanner,
        changed_packets,
        true,
        true,
        &combined_stats);
    assert(combined_stats.changed_entities == 1u);
    assert(combined_view.size() == 1u);
    assert(combined_view[0].transform.location.x == 100.0);

    fastdis::SnapshotBatch copied = buffer.copy_latest(4);
    assert(copied.size() == 1u);

    fastdis::Scanner moved_scanner(std::move(scanner));
    assert(moved_scanner);
    assert(!scanner);

    fastdis::EntityTable moved_table(std::move(table));
    assert(moved_table);
    assert(!table);
    assert(moved_table.size() == 2u);

    return 0;
}
