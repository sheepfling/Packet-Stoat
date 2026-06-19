#include "fastdis_world.h"

#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/variant/basis.hpp>
#include <godot_cpp/variant/quaternion.hpp>
#include <godot_cpp/variant/transform3d.hpp>
#include <godot_cpp/variant/utility_functions.hpp>
#include <godot_cpp/variant/vector3.hpp>

namespace godot {

FastDisWorld::FastDisWorld()
{
    fastdis::ScanConfig config = fastdis::ScanConfig::entity_transform();
    config.only_versions({6, 7})
          .only_pdu_types({FASTDIS_ENTITY_STATE_PDU_TYPE})
          .only_protocol_families({FASTDIS_ENTITY_INFORMATION_FAMILY});

    scanner_ = std::make_unique<fastdis::Scanner>(config);
    table_ = std::make_unique<fastdis::EntityTable>(4096);
    snapshots_ = std::make_unique<fastdis::SnapshotBuffer>(4096);
    local_frame_ = fastdis::frames::LocalEnuFrame::from_degrees(0.0, 0.0, 0.0);
}

FastDisWorld::~FastDisWorld() = default;

void FastDisWorld::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("set_georeference", "latitude_degrees", "longitude_degrees", "height_meters"), &FastDisWorld::set_georeference);
    ClassDB::bind_method(D_METHOD("set_apply_orientation", "enabled"), &FastDisWorld::set_apply_orientation);
    ClassDB::bind_method(D_METHOD("get_apply_orientation"), &FastDisWorld::get_apply_orientation);
    ClassDB::bind_method(D_METHOD("set_auto_apply", "enabled"), &FastDisWorld::set_auto_apply);
    ClassDB::bind_method(D_METHOD("get_auto_apply"), &FastDisWorld::get_auto_apply);
    ClassDB::bind_method(D_METHOD("register_entity", "site", "application", "entity", "node_path"), &FastDisWorld::register_entity);
    ClassDB::bind_method(D_METHOD("unregister_entity", "site", "application", "entity"), &FastDisWorld::unregister_entity);
    ClassDB::bind_method(D_METHOD("clear_entities"), &FastDisWorld::clear_entities);
    ClassDB::bind_method(D_METHOD("ingest_packet", "packet", "advance_tick"), &FastDisWorld::ingest_packet, DEFVAL(true));
    ClassDB::bind_method(D_METHOD("apply_latest_snapshots"), &FastDisWorld::apply_latest_snapshots);
    ClassDB::bind_method(D_METHOD("get_known_entity_count"), &FastDisWorld::get_known_entity_count);

    ADD_PROPERTY(PropertyInfo(Variant::BOOL, "apply_orientation"), "set_apply_orientation", "get_apply_orientation");
    ADD_PROPERTY(PropertyInfo(Variant::BOOL, "auto_apply"), "set_auto_apply", "get_auto_apply");
}

void FastDisWorld::_ready() {}

void FastDisWorld::_process(double delta)
{
    (void)delta;
    if (auto_apply_) {
        apply_latest_snapshots();
    }
}

void FastDisWorld::set_georeference(double latitude_degrees, double longitude_degrees, double height_meters)
{
    local_frame_ = fastdis::frames::LocalEnuFrame::from_degrees(latitude_degrees, longitude_degrees, height_meters);
}

void FastDisWorld::set_apply_orientation(bool enabled) { apply_orientation_ = enabled; }
bool FastDisWorld::get_apply_orientation() const { return apply_orientation_; }
void FastDisWorld::set_auto_apply(bool enabled) { auto_apply_ = enabled; }
bool FastDisWorld::get_auto_apply() const { return auto_apply_; }

void FastDisWorld::register_entity(int site, int application, int entity, const NodePath& node_path)
{
    nodes_[make_key(site, application, entity)] = node_path;
}

void FastDisWorld::unregister_entity(int site, int application, int entity)
{
    nodes_.erase(make_key(site, application, entity));
}

void FastDisWorld::clear_entities()
{
    nodes_.clear();
}

int FastDisWorld::ingest_packet(const PackedByteArray& packet, bool advance_tick)
{
    if (!scanner_ || !table_ || !snapshots_ || packet.size() == 0) {
        return static_cast<int>(FASTDIS_ERR_INVALID_ARGUMENT);
    }

    fastdis::PacketView view = fastdis::packet_view(packet.ptr(), static_cast<std::size_t>(packet.size()));
    fastdis::EntityTableUpdateStats stats{};
    fastdis_entity_table_update_stats_init(&stats);

    fastdis::SnapshotView published;
    const fastdis::Status status = snapshots_->try_ingest_and_publish_changed(
        *table_,
        *scanner_,
        &view,
        1,
        advance_tick,
        true,
        &stats,
        &published);

    return static_cast<int>(status);
}

int FastDisWorld::apply_latest_snapshots()
{
    if (!snapshots_) {
        return 0;
    }

    fastdis::ScopedSnapshotView view;
    const fastdis::Status status = snapshots_->try_acquire_latest(&view);
    if (status != FASTDIS_OK) {
        return static_cast<int>(status);
    }

    int applied = 0;
    for (const fastdis::EntitySnapshot& snapshot : view) {
        const auto it = nodes_.find(make_key(snapshot.transform.entity_id));
        if (it == nodes_.end()) {
            continue;
        }

        Node* node = get_node_or_null(it->second);
        Node3D* node3d = Object::cast_to<Node3D>(node);
        if (!node3d) {
            continue;
        }

        bool apply_rotation = false;
        Transform3D transform = transform_from_snapshot(snapshot, apply_rotation);
        if (!apply_rotation) {
            Transform3D current = node3d->get_global_transform();
            current.origin = transform.origin;
            node3d->set_global_transform(current);
        } else {
            node3d->set_global_transform(transform);
        }
        ++applied;
    }
    return applied;
}

int FastDisWorld::get_known_entity_count() const
{
    return table_ ? static_cast<int>(table_->size()) : 0;
}

std::uint64_t FastDisWorld::make_key(int site, int application, int entity)
{
    return (static_cast<std::uint64_t>(static_cast<std::uint16_t>(site)) << 32) |
           (static_cast<std::uint64_t>(static_cast<std::uint16_t>(application)) << 16) |
           static_cast<std::uint64_t>(static_cast<std::uint16_t>(entity));
}

std::uint64_t FastDisWorld::make_key(const fastdis_entity_id_t& id)
{
    return make_key(id.site, id.application, id.entity);
}

Transform3D FastDisWorld::transform_from_snapshot(const fastdis::EntitySnapshot& snapshot, bool& out_apply_rotation) const
{
    const auto policy = apply_orientation_
        ? fastdis::frames::OrientationPolicy::ExperimentalLocalYawPitchRoll
        : fastdis::frames::OrientationPolicy::PositionOnly;
    const fastdis::frames::GodotPoseData pose = fastdis::frames::to_godot_pose(local_frame_, snapshot, policy);

    Transform3D transform;
    transform.origin = Vector3(static_cast<real_t>(pose.x_m), static_cast<real_t>(pose.y_m), static_cast<real_t>(pose.z_m));

    out_apply_rotation = apply_orientation_;
    if (out_apply_rotation) {
        Quaternion q(static_cast<real_t>(pose.rotation.x),
                     static_cast<real_t>(pose.rotation.y),
                     static_cast<real_t>(pose.rotation.z),
                     static_cast<real_t>(pose.rotation.w));
        transform.basis = Basis(q);
    }
    return transform;
}

} // namespace godot
