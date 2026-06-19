#pragma once

#include <godot_cpp/classes/node.hpp>
#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/node_path.hpp>
#include <godot_cpp/variant/packed_byte_array.hpp>

#include <fastdis/fastdis.hpp>
#include <fastdis/fastdis_frames.hpp>

#include <cstdint>
#include <memory>
#include <unordered_map>

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

    void register_entity(int site, int application, int entity, const NodePath& node_path);
    void unregister_entity(int site, int application, int entity);
    void clear_entities();

    // Demo-friendly API. For the highest-rate path, write a native socket bridge
    // that builds fastdis_packet_view_t arrays and calls ingest_packet_views().
    int ingest_packet(const PackedByteArray& packet, bool advance_tick = true);
    int apply_latest_snapshots();
    int get_known_entity_count() const;

protected:
    static void _bind_methods();

private:
    static std::uint64_t make_key(int site, int application, int entity);
    static std::uint64_t make_key(const fastdis_entity_id_t& id);
    Transform3D transform_from_snapshot(const fastdis::EntitySnapshot& snapshot, bool& out_apply_rotation) const;

private:
    std::unique_ptr<fastdis::Scanner> scanner_;
    std::unique_ptr<fastdis::EntityTable> table_;
    std::unique_ptr<fastdis::SnapshotBuffer> snapshots_;
    std::unordered_map<std::uint64_t, NodePath> nodes_;

    fastdis::frames::LocalEnuFrame local_frame_;
    bool apply_orientation_ = false;
    bool auto_apply_ = true;
};

} // namespace godot
