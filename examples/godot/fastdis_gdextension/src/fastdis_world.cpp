#include "fastdis_world.h"

#include <godot_cpp/classes/file_access.hpp>
#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/variant/basis.hpp>
#include <godot_cpp/variant/quaternion.hpp>
#include <godot_cpp/variant/transform3d.hpp>
#include <godot_cpp/variant/utility_functions.hpp>
#include <godot_cpp/variant/vector3.hpp>

#include <algorithm>

namespace godot {

namespace {

int sanitize_snapshot_slots(int slots)
{
    return std::max(2, slots);
}

int sanitize_transform_mode(int mode)
{
    return std::clamp(mode, 0, 3);
}

int sanitize_orientation_mode(int mode)
{
    return std::clamp(mode, 0, 2);
}

bool read_be32(const PackedByteArray &bytes, int offset, std::uint32_t &out_value)
{
    if (offset < 0 || offset + 4 > bytes.size()) {
        return false;
    }

    out_value = (static_cast<std::uint32_t>(bytes[offset + 0]) << 24) |
                (static_cast<std::uint32_t>(bytes[offset + 1]) << 16) |
                (static_cast<std::uint32_t>(bytes[offset + 2]) << 8) |
                static_cast<std::uint32_t>(bytes[offset + 3]);
    return true;
}

} // namespace

FastDisWorld::FastDisWorld()
{
    scanner_ = std::make_unique<fastdis::Scanner>(
        fastdis::ScannerBuilder()
            .entity_transform_profile()
            .versions({ 6, 7 })
            .pdu_types({ FASTDIS_ENTITY_STATE_PDU_TYPE })
            .protocol_families({ FASTDIS_ENTITY_INFORMATION_FAMILY })
            .build());
    table_ = std::make_unique<fastdis::EntityTable>(
        fastdis::EntityTableConfig()
            .reserve(4096)
            .build());
    snapshots_ = std::make_unique<fastdis::SnapshotBuffer>(4096, static_cast<std::size_t>(snapshot_slots_));
    local_frame_ = fastdis::frames::LocalEnuFrame::from_degrees(0.0, 0.0, 0.0);
}

FastDisWorld::~FastDisWorld() = default;

void FastDisWorld::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("set_georeference", "latitude_degrees", "longitude_degrees", "height_meters"), &FastDisWorld::set_georeference);
    ClassDB::bind_method(D_METHOD("set_apply_orientation", "enabled"), &FastDisWorld::set_apply_orientation);
    ClassDB::bind_method(D_METHOD("get_apply_orientation"), &FastDisWorld::get_apply_orientation);
    ClassDB::bind_method(D_METHOD("set_orientation_mode", "mode"), &FastDisWorld::set_orientation_mode);
    ClassDB::bind_method(D_METHOD("get_orientation_mode"), &FastDisWorld::get_orientation_mode);
    ClassDB::bind_method(D_METHOD("set_auto_apply", "enabled"), &FastDisWorld::set_auto_apply);
    ClassDB::bind_method(D_METHOD("get_auto_apply"), &FastDisWorld::get_auto_apply);
    ClassDB::bind_method(D_METHOD("set_transform_mode", "mode"), &FastDisWorld::set_transform_mode);
    ClassDB::bind_method(D_METHOD("get_transform_mode"), &FastDisWorld::get_transform_mode);
    ClassDB::bind_method(D_METHOD("set_meters_to_godot_scale", "scale"), &FastDisWorld::set_meters_to_godot_scale);
    ClassDB::bind_method(D_METHOD("get_meters_to_godot_scale"), &FastDisWorld::get_meters_to_godot_scale);
    ClassDB::bind_method(D_METHOD("set_snapshot_slots", "slots"), &FastDisWorld::set_snapshot_slots);
    ClassDB::bind_method(D_METHOD("get_snapshot_slots"), &FastDisWorld::get_snapshot_slots);
    ClassDB::bind_method(D_METHOD("set_stale_after_ticks", "stale_after_ticks"), &FastDisWorld::set_stale_after_ticks);
    ClassDB::bind_method(D_METHOD("get_stale_after_ticks"), &FastDisWorld::get_stale_after_ticks);
    ClassDB::bind_method(D_METHOD("set_interpolation_speed", "speed"), &FastDisWorld::set_interpolation_speed);
    ClassDB::bind_method(D_METHOD("get_interpolation_speed"), &FastDisWorld::get_interpolation_speed);
    ClassDB::bind_method(D_METHOD("set_replay_loop", "enabled"), &FastDisWorld::set_replay_loop);
    ClassDB::bind_method(D_METHOD("get_replay_loop"), &FastDisWorld::get_replay_loop);
    ClassDB::bind_method(D_METHOD("get_last_error"), &FastDisWorld::get_last_error);
    ClassDB::bind_method(D_METHOD("register_entity", "site", "application", "entity", "node_path"), &FastDisWorld::register_entity);
    ClassDB::bind_method(D_METHOD("unregister_entity", "site", "application", "entity"), &FastDisWorld::unregister_entity);
    ClassDB::bind_method(D_METHOD("clear_entities"), &FastDisWorld::clear_entities);
    ClassDB::bind_method(D_METHOD("set_allowed_force_ids", "force_ids"), &FastDisWorld::set_allowed_force_ids);
    ClassDB::bind_method(D_METHOD("clear_allowed_force_ids"), &FastDisWorld::clear_allowed_force_ids);
    ClassDB::bind_method(D_METHOD("ingest_packet", "packet", "advance_tick"), &FastDisWorld::ingest_packet, DEFVAL(true));
    ClassDB::bind_method(D_METHOD("ingest_packet_batch", "packets", "advance_tick"), &FastDisWorld::ingest_packet_batch, DEFVAL(true));
    ClassDB::bind_method(D_METHOD("load_replay_file", "replay_path"), &FastDisWorld::load_replay_file);
    ClassDB::bind_method(D_METHOD("clear_replay"), &FastDisWorld::clear_replay);
    ClassDB::bind_method(D_METHOD("ingest_replay_frame", "packet_budget", "advance_tick"), &FastDisWorld::ingest_replay_frame, DEFVAL(64), DEFVAL(true));
    ClassDB::bind_method(D_METHOD("apply_latest_snapshots"), &FastDisWorld::apply_latest_snapshots);
    ClassDB::bind_method(D_METHOD("build_debug_transform", "heading_degrees", "pitch_degrees", "roll_degrees"), &FastDisWorld::build_debug_transform);
    ClassDB::bind_method(D_METHOD("build_debug_transform_from_dis", "psi_degrees", "theta_degrees", "phi_degrees"), &FastDisWorld::build_debug_transform_from_dis);
    ClassDB::bind_method(D_METHOD("get_loaded_replay_packet_count"), &FastDisWorld::get_loaded_replay_packet_count);
    ClassDB::bind_method(D_METHOD("get_known_entity_count"), &FastDisWorld::get_known_entity_count);

    ADD_PROPERTY(PropertyInfo(Variant::BOOL, "apply_orientation"), "set_apply_orientation", "get_apply_orientation");
    ADD_PROPERTY(PropertyInfo(Variant::INT, "orientation_mode", PROPERTY_HINT_ENUM, "Disabled,ExperimentalLocalHeadingPitchRoll,ValidatedDisBodyFrame"), "set_orientation_mode", "get_orientation_mode");
    ADD_PROPERTY(PropertyInfo(Variant::BOOL, "auto_apply"), "set_auto_apply", "get_auto_apply");
    ADD_PROPERTY(PropertyInfo(Variant::INT, "transform_mode", PROPERTY_HINT_ENUM, "PositionOnly,SnapPosition,InterpolatePosition,PositionAndExperimentalRotation"), "set_transform_mode", "get_transform_mode");
    ADD_PROPERTY(PropertyInfo(Variant::FLOAT, "meters_to_godot_scale", PROPERTY_HINT_RANGE, "0.01,1000.0,0.01"), "set_meters_to_godot_scale", "get_meters_to_godot_scale");
    ADD_PROPERTY(PropertyInfo(Variant::INT, "snapshot_slots", PROPERTY_HINT_RANGE, "2,8,1"), "set_snapshot_slots", "get_snapshot_slots");
    ADD_PROPERTY(PropertyInfo(Variant::INT, "stale_after_ticks", PROPERTY_HINT_RANGE, "0,100000,1"), "set_stale_after_ticks", "get_stale_after_ticks");
    ADD_PROPERTY(PropertyInfo(Variant::FLOAT, "interpolation_speed", PROPERTY_HINT_RANGE, "0.01,120.0,0.01"), "set_interpolation_speed", "get_interpolation_speed");
    ADD_PROPERTY(PropertyInfo(Variant::BOOL, "replay_loop"), "set_replay_loop", "get_replay_loop");
}

void FastDisWorld::_ready() {}

void FastDisWorld::_process(double delta)
{
    last_process_delta_ = delta;
    publish_stale_snapshots();
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
void FastDisWorld::set_orientation_mode(int mode) { orientation_mode_ = sanitize_orientation_mode(mode); }
int FastDisWorld::get_orientation_mode() const { return orientation_mode_; }
void FastDisWorld::set_auto_apply(bool enabled) { auto_apply_ = enabled; }
bool FastDisWorld::get_auto_apply() const { return auto_apply_; }

void FastDisWorld::set_transform_mode(int mode)
{
    transform_mode_ = sanitize_transform_mode(mode);
}

int FastDisWorld::get_transform_mode() const
{
    return transform_mode_;
}

void FastDisWorld::set_meters_to_godot_scale(double scale)
{
    meters_to_godot_scale_ = std::max(0.01, scale);
}

double FastDisWorld::get_meters_to_godot_scale() const
{
    return meters_to_godot_scale_;
}

void FastDisWorld::set_snapshot_slots(int slots)
{
    const int sanitized = sanitize_snapshot_slots(slots);
    if (sanitized == snapshot_slots_) {
        return;
    }

    snapshot_slots_ = sanitized;
    snapshots_ = std::make_unique<fastdis::SnapshotBuffer>(4096, static_cast<std::size_t>(snapshot_slots_));
}

int FastDisWorld::get_snapshot_slots() const
{
    return snapshot_slots_;
}

void FastDisWorld::set_stale_after_ticks(int stale_after_ticks)
{
    stale_after_ticks_ = std::max(0, stale_after_ticks);
}

int FastDisWorld::get_stale_after_ticks() const
{
    return stale_after_ticks_;
}

void FastDisWorld::set_interpolation_speed(double speed)
{
    interpolation_speed_ = std::max(0.01, speed);
}

double FastDisWorld::get_interpolation_speed() const
{
    return interpolation_speed_;
}

void FastDisWorld::set_replay_loop(bool enabled)
{
    replay_loop_ = enabled;
}

bool FastDisWorld::get_replay_loop() const
{
    return replay_loop_;
}

String FastDisWorld::get_last_error() const
{
    return last_error_;
}

void FastDisWorld::register_entity(int site, int application, int entity, const NodePath &node_path)
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

void FastDisWorld::set_allowed_force_ids(const PackedInt32Array &force_ids)
{
    if (!scanner_) {
        set_error("FastDisWorld set_allowed_force_ids called without an initialized scanner.");
        return;
    }

    scanner_->clear(fastdis::FilterKind::EntityForceIds);
    for (int index = 0; index < force_ids.size(); ++index) {
        const int value = force_ids[index];
        if (value < 0 || value > 255) {
            set_error("FastDisWorld set_allowed_force_ids requires values between 0 and 255.");
            return;
        }
        scanner_->allow(fastdis::FilterKind::EntityForceIds, static_cast<std::uint8_t>(value));
    }
    set_error("");
}

void FastDisWorld::clear_allowed_force_ids()
{
    if (!scanner_) {
        set_error("FastDisWorld clear_allowed_force_ids called without an initialized scanner.");
        return;
    }
    scanner_->accept_all(fastdis::FilterKind::EntityForceIds);
    set_error("");
}

int FastDisWorld::ingest_packet(const PackedByteArray &packet, bool advance_tick)
{
    if (!scanner_ || !table_ || !snapshots_ || packet.size() == 0) {
        set_error("FastDisWorld ingest_packet received an empty packet or uninitialized native state.");
        return static_cast<int>(FASTDIS_ERR_BAD_ARGUMENT);
    }

    const fastdis::PacketView view = fastdis::packet_view(packet.ptr(), static_cast<std::size_t>(packet.size()));
    return ingest_packet_views(&view, 1, advance_tick);
}

int FastDisWorld::ingest_packet_batch(const Array &packets, bool advance_tick)
{
    if (!scanner_ || !table_ || !snapshots_ || packets.is_empty()) {
        set_error("FastDisWorld ingest_packet_batch received no packets or uninitialized native state.");
        return static_cast<int>(FASTDIS_ERR_BAD_ARGUMENT);
    }

    std::vector<PackedByteArray> owned_packets;
    owned_packets.reserve(static_cast<std::size_t>(packets.size()));
    std::vector<fastdis::PacketView> views;
    views.reserve(static_cast<std::size_t>(packets.size()));

    for (int index = 0; index < packets.size(); ++index) {
        const PackedByteArray packet = packets[index];
        if (packet.is_empty()) {
            continue;
        }
        owned_packets.push_back(packet);
        const PackedByteArray &owned = owned_packets.back();
        views.push_back(fastdis::packet_view(owned.ptr(), static_cast<std::size_t>(owned.size())));
    }

    if (views.empty()) {
        set_error("FastDisWorld ingest_packet_batch received only empty packets.");
        return static_cast<int>(FASTDIS_ERR_BAD_ARGUMENT);
    }

    return ingest_packet_views(views.data(), views.size(), advance_tick);
}

bool FastDisWorld::load_replay_file(const String &replay_path)
{
    clear_replay();

    if (replay_path.is_empty()) {
        set_error("FastDisWorld load_replay_file requires a non-empty path.");
        return false;
    }

    Ref<FileAccess> file = FileAccess::open(replay_path, FileAccess::ModeFlags::READ);
    if (file.is_null()) {
        set_error("FastDisWorld could not open replay file: " + replay_path);
        return false;
    }

    const std::int64_t raw_length = file->get_length();
    if (raw_length <= 0) {
        set_error("FastDisWorld replay file is empty: " + replay_path);
        return false;
    }

    const PackedByteArray raw = file->get_buffer(static_cast<std::int32_t>(raw_length));
    int offset = 0;
    while (offset < raw.size()) {
        std::uint32_t packet_length = 0;
        if (!read_be32(raw, offset, packet_length)) {
            clear_replay();
            set_error("FastDisWorld replay file is truncated before a packet length prefix: " + replay_path);
            return false;
        }
        offset += 4;

        if (packet_length == 0 || packet_length > static_cast<std::uint32_t>(raw.size() - offset)) {
            clear_replay();
            set_error("FastDisWorld replay file has an invalid packet length: " + replay_path);
            return false;
        }

        PackedByteArray packet;
        packet.resize(static_cast<int>(packet_length));
        for (std::uint32_t i = 0; i < packet_length; ++i) {
            packet[static_cast<int>(i)] = raw[offset + static_cast<int>(i)];
        }
        replay_packets_.push_back(packet);
        offset += static_cast<int>(packet_length);
    }

    replay_packet_index_ = 0;
    set_error("");
    return !replay_packets_.empty();
}

void FastDisWorld::clear_replay()
{
    replay_packets_.clear();
    replay_packet_index_ = 0;
}

int FastDisWorld::ingest_replay_frame(int packet_budget, bool advance_tick)
{
    if (replay_packets_.empty()) {
        set_error("FastDisWorld ingest_replay_frame called without a loaded replay.");
        return 0;
    }

    const int clamped_budget = std::max(1, packet_budget);
    std::vector<fastdis::PacketView> views;
    views.reserve(static_cast<std::size_t>(clamped_budget));

    for (int index = 0; index < clamped_budget; ++index) {
        if (replay_packet_index_ >= static_cast<int>(replay_packets_.size())) {
            if (!replay_loop_) {
                break;
            }
            replay_packet_index_ = 0;
        }

        const PackedByteArray &packet = replay_packets_[static_cast<std::size_t>(replay_packet_index_)];
        views.push_back(fastdis::packet_view(packet.ptr(), static_cast<std::size_t>(packet.size())));
        ++replay_packet_index_;
    }

    if (views.empty()) {
        return 0;
    }

    return ingest_packet_views(views.data(), views.size(), advance_tick);
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
    for (const fastdis::EntitySnapshot &snapshot : view) {
        const auto it = nodes_.find(make_key(snapshot.transform.entity_id));
        if (it == nodes_.end()) {
            continue;
        }

        Node *node = get_node_or_null(it->second);
        Node3D *node3d = Object::cast_to<Node3D>(node);
        if (!node3d) {
            continue;
        }

        bool apply_rotation = false;
        const Transform3D target_transform = transform_from_snapshot(snapshot, apply_rotation);
        Transform3D next_transform = node3d->get_global_transform();

        switch (transform_mode_) {
            case TRANSFORM_INTERPOLATE_POSITION: {
                const real_t weight = static_cast<real_t>(std::clamp(last_process_delta_ * interpolation_speed_, 0.0, 1.0));
                next_transform.origin = next_transform.origin.lerp(target_transform.origin, weight);
                break;
            }
            case TRANSFORM_POSITION_AND_EXPERIMENTAL_ROTATION:
                next_transform.origin = target_transform.origin;
                if (apply_rotation) {
                    next_transform.basis = target_transform.basis;
                }
                break;
            case TRANSFORM_SNAP_POSITION:
            case TRANSFORM_POSITION_ONLY:
            default:
                next_transform.origin = target_transform.origin;
                break;
        }

        node3d->set_global_transform(next_transform);
        ++applied;
    }

    return applied;
}

int FastDisWorld::get_loaded_replay_packet_count() const
{
    return static_cast<int>(replay_packets_.size());
}

Transform3D FastDisWorld::build_debug_transform(double heading_degrees, double pitch_degrees, double roll_degrees)
{
    fastdis::EntitySnapshot snapshot{};
    snapshot.transform.location.x = local_frame_.origin_ecef.x;
    snapshot.transform.location.y = local_frame_.origin_ecef.y;
    snapshot.transform.location.z = local_frame_.origin_ecef.z;
    snapshot.transform.orientation.psi = static_cast<float>(heading_degrees * fastdis::frames::deg_to_rad);
    snapshot.transform.orientation.theta = static_cast<float>(pitch_degrees * fastdis::frames::deg_to_rad);
    snapshot.transform.orientation.phi = static_cast<float>(roll_degrees * fastdis::frames::deg_to_rad);

    bool apply_rotation = false;
    return transform_from_snapshot(snapshot, apply_rotation);
}

Transform3D FastDisWorld::build_debug_transform_from_dis(double psi_degrees, double theta_degrees, double phi_degrees)
{
    fastdis::EntitySnapshot snapshot{};
    snapshot.transform.location.x = local_frame_.origin_ecef.x;
    snapshot.transform.location.y = local_frame_.origin_ecef.y;
    snapshot.transform.location.z = local_frame_.origin_ecef.z;
    snapshot.transform.orientation.psi = static_cast<float>(psi_degrees * fastdis::frames::deg_to_rad);
    snapshot.transform.orientation.theta = static_cast<float>(theta_degrees * fastdis::frames::deg_to_rad);
    snapshot.transform.orientation.phi = static_cast<float>(phi_degrees * fastdis::frames::deg_to_rad);

    bool apply_rotation = false;
    return transform_from_snapshot(snapshot, apply_rotation);
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

std::uint64_t FastDisWorld::make_key(const fastdis_entity_id_t &id)
{
    return make_key(id.site, id.application, id.entity);
}

int FastDisWorld::ingest_packet_views(const fastdis::PacketView *views, std::size_t count, bool advance_tick)
{
    if (!scanner_ || !table_ || !snapshots_ || count == 0) {
        set_error("FastDisWorld ingest_packet_views received no packets or uninitialized native state.");
        return static_cast<int>(FASTDIS_ERR_BAD_ARGUMENT);
    }

    fastdis::EntityTableUpdateStats stats {};
    fastdis_entity_table_update_stats_init(&stats);

    fastdis::SnapshotView published;
    const fastdis::Status status = snapshots_->try_ingest_and_publish_changed(
        *table_,
        *scanner_,
        views,
        count,
        advance_tick,
        true,
        &stats,
        &published);

    if (status != FASTDIS_OK && status != FASTDIS_ERR_BUSY) {
        set_error("FastDisWorld ingest failed: " + String(fastdis::status_string(status)));
    } else {
        set_error("");
    }
    return static_cast<int>(status);
}

void FastDisWorld::publish_stale_snapshots()
{
    if (!snapshots_ || !table_ || stale_after_ticks_ <= 0) {
        return;
    }

    const fastdis::Status status = snapshots_->try_publish_evict_stale(
        *table_,
        static_cast<std::uint64_t>(stale_after_ticks_),
        nullptr);
    if (status != FASTDIS_OK && status != FASTDIS_ERR_BUSY && status != FASTDIS_ERR_NOT_FOUND) {
        set_error("FastDisWorld stale publish failed: " + String(fastdis::status_string(status)));
    }
}

void FastDisWorld::set_error(const String &error)
{
    last_error_ = error;
    if (!error.is_empty()) {
        UtilityFunctions::push_warning(error);
    }
}

Transform3D FastDisWorld::transform_from_snapshot(const fastdis::EntitySnapshot &snapshot, bool &out_apply_rotation) const
{
    auto policy = fastdis::frames::OrientationPolicy::PositionOnly;
    if (apply_orientation_) {
        if (orientation_mode_ == ORIENTATION_VALIDATED_DIS_BODY_FRAME) {
            policy = fastdis::frames::OrientationPolicy::ValidatedDisBodyFrame;
        } else if (orientation_mode_ == ORIENTATION_EXPERIMENTAL_LOCAL_YPR) {
            policy = fastdis::frames::OrientationPolicy::ExperimentalLocalYawPitchRoll;
        }
    }
    const fastdis::frames::GodotPoseData pose = fastdis::frames::to_godot_pose(local_frame_, snapshot, policy);

    Transform3D transform;
    transform.origin = Vector3(
        static_cast<real_t>(pose.x_m * meters_to_godot_scale_),
        static_cast<real_t>(pose.y_m * meters_to_godot_scale_),
        static_cast<real_t>(pose.z_m * meters_to_godot_scale_));

    out_apply_rotation = policy != fastdis::frames::OrientationPolicy::PositionOnly;
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
