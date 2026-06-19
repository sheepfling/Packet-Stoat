#pragma once

#include <godot_cpp/classes/node.hpp>
#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/node_path.hpp>
#include <godot_cpp/variant/packed_byte_array.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/transform3d.hpp>

#include <fastdis/fastdis.hpp>
#include <fastdis/fastdis_frames.hpp>

#include <cstddef>
#include <cstdint>
#include <memory>
#include <unordered_map>
#include <vector>

namespace godot {

class FastDisWorld : public Node {
    GDCLASS(FastDisWorld, Node)

public:
    FastDisWorld();
    ~FastDisWorld() override;

    void _ready() override;
    void _process(double delta) override;

    void set_georeference(double latitude_degrees, double longitude_degrees, double height_meters);
    void set_apply_orientation(bool enabled);
    bool get_apply_orientation() const;

    void set_auto_apply(bool enabled);
    bool get_auto_apply() const;

    void set_transform_mode(int mode);
    int get_transform_mode() const;

    void set_meters_to_godot_scale(double scale);
    double get_meters_to_godot_scale() const;

    void set_snapshot_slots(int slots);
    int get_snapshot_slots() const;

    void set_stale_after_ticks(int stale_after_ticks);
    int get_stale_after_ticks() const;

    void set_interpolation_speed(double speed);
    double get_interpolation_speed() const;

    void set_replay_loop(bool enabled);
    bool get_replay_loop() const;

    String get_last_error() const;

    void register_entity(int site, int application, int entity, const NodePath& node_path);
    void unregister_entity(int site, int application, int entity);
    void clear_entities();

    // Demo-friendly API. For the highest-rate path, write a native socket bridge
    // that builds fastdis_packet_view_t arrays and calls ingest_packet_views().
    int ingest_packet(const PackedByteArray& packet, bool advance_tick = true);
    bool load_replay_file(const String& replay_path);
    void clear_replay();
    int ingest_replay_frame(int packet_budget = 64, bool advance_tick = true);
    int apply_latest_snapshots();
    Transform3D build_debug_transform(double heading_degrees, double pitch_degrees, double roll_degrees);
    int get_loaded_replay_packet_count() const;
    int get_known_entity_count() const;

protected:
    static void _bind_methods();

private:
    enum TransformMode {
        TRANSFORM_POSITION_ONLY = 0,
        TRANSFORM_SNAP_POSITION = 1,
        TRANSFORM_INTERPOLATE_POSITION = 2,
        TRANSFORM_POSITION_AND_EXPERIMENTAL_ROTATION = 3,
    };

    static std::uint64_t make_key(int site, int application, int entity);
    static std::uint64_t make_key(const fastdis_entity_id_t& id);
    int ingest_packet_views(const fastdis::PacketView* views, std::size_t count, bool advance_tick);
    void publish_stale_snapshots();
    void set_error(const String& error);
    Transform3D transform_from_snapshot(const fastdis::EntitySnapshot& snapshot, bool& out_apply_rotation) const;

private:
    std::unique_ptr<fastdis::Scanner> scanner_;
    std::unique_ptr<fastdis::EntityTable> table_;
    std::unique_ptr<fastdis::SnapshotBuffer> snapshots_;
    std::unordered_map<std::uint64_t, NodePath> nodes_;

    fastdis::frames::LocalEnuFrame local_frame_;
    bool apply_orientation_ = false;
    bool auto_apply_ = true;
    int transform_mode_ = TRANSFORM_POSITION_ONLY;
    double meters_to_godot_scale_ = 1.0;
    int snapshot_slots_ = 3;
    int stale_after_ticks_ = 120;
    double interpolation_speed_ = 8.0;
    bool replay_loop_ = true;
    String last_error_;
    double last_process_delta_ = 0.0;
    std::vector<PackedByteArray> replay_packets_;
    int replay_packet_index_ = 0;
};

} // namespace godot
