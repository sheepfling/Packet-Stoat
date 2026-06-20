#include <fastdis/fastdis_frames.hpp>
#include <fastdis/fastdis_orientation.hpp>

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

double scalar_from_bytes(const std::uint8_t* data, std::size_t size, std::size_t offset, double scale) {
    if (offset + sizeof(std::uint32_t) > size) {
        return 0.0;
    }
    std::uint32_t bits = 0u;
    std::memcpy(&bits, data + offset, sizeof(bits));
    return static_cast<double>(static_cast<std::int32_t>(bits)) / scale;
}

fastdis_world_coordinates_t world_from_bytes(const std::uint8_t* data, std::size_t size, std::size_t offset, double scale) {
    return fastdis_world_coordinates_t{
        scalar_from_bytes(data, size, offset + 0u, scale),
        scalar_from_bytes(data, size, offset + 4u, scale),
        scalar_from_bytes(data, size, offset + 8u, scale),
    };
}

fastdis_vec3f_t vec3f_from_bytes(const std::uint8_t* data, std::size_t size, std::size_t offset, double scale) {
    return fastdis_vec3f_t{
        static_cast<float>(scalar_from_bytes(data, size, offset + 0u, scale)),
        static_cast<float>(scalar_from_bytes(data, size, offset + 4u, scale)),
        static_cast<float>(scalar_from_bytes(data, size, offset + 8u, scale)),
    };
}

float angle_from_bytes(const std::uint8_t* data, std::size_t size, std::size_t offset) {
    return static_cast<float>(scalar_from_bytes(data, size, offset, 1000000.0));
}

double clamp(double v, double min_v, double max_v) {
    return v < min_v ? min_v : (v > max_v ? max_v : v);
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    using namespace fastdis::frames;
    using namespace fastdis::orientation;

    if (data == nullptr) {
        return 0;
    }

    const double lat_deg = clamp(scalar_from_bytes(data, size, 0u, 100000.0), -89.999, 89.999);
    const double lon_deg = clamp(scalar_from_bytes(data, size, 4u, 100000.0), -180.0, 180.0);
    const double height_m = clamp(scalar_from_bytes(data, size, 8u, 10.0), -1000.0, 100000.0);
    const LocalEnuFrame frame = LocalEnuFrame::from_degrees(lat_deg, lon_deg, height_m);

    fastdis_entity_transform_t transform{};
    transform.location = world_from_bytes(data, size, 12u, 4.0);
    transform.linear_velocity = vec3f_from_bytes(data, size, 24u, 1000.0);
    transform.orientation.psi = angle_from_bytes(data, size, 36u);
    transform.orientation.theta = angle_from_bytes(data, size, 40u);
    transform.orientation.phi = angle_from_bytes(data, size, 44u);

    (void)to_unreal_pose(frame, transform, OrientationPolicy::PositionOnly);
    (void)to_unreal_pose(frame, transform, OrientationPolicy::ExperimentalLocalYawPitchRoll);
    (void)to_unreal_pose(frame, transform, OrientationPolicy::ValidatedDisBodyFrame);
    (void)to_godot_pose(frame, transform, OrientationPolicy::PositionOnly);
    (void)to_godot_pose(frame, transform, OrientationPolicy::ExperimentalLocalYawPitchRoll);
    (void)to_godot_pose(frame, transform, OrientationPolicy::ValidatedDisBodyFrame);

    const BodyFrdBasisEcef body = dis_orientation_to_body_frd_ecef(transform.orientation);
    const BodyFruBasisEnu body_enu = body_frd_ecef_to_body_fru_enu(body, frame);
    const TargetFrame targets[] = {
        TargetFrame::StandaloneUnrealNorthEastUp,
        TargetFrame::StandaloneUnityEastUpNorth,
        TargetFrame::StandaloneGodotEastUpMinusNorth,
        TargetFrame::CesiumJsEastNorthUp,
        TargetFrame::CesiumUnityEastUpNorth,
        TargetFrame::CesiumUnrealEastSouthUp,
    };
    for (TargetFrame target : targets) {
        const TargetBasis basis = map_body_fru_enu_to_target_basis(body_enu, target);
        (void)quat_from_target_basis(basis);
    }

    const fastdis_entity_snapshot_t snapshot{
        transform,
        0u,
        1u,
        1u,
        FASTDIS_ENTITY_CHANGE_NEW | FASTDIS_ENTITY_CHANGE_UPDATED,
        0u,
    };
    (void)to_unreal_pose(frame, snapshot, OrientationPolicy::ValidatedDisBodyFrame);
    (void)to_godot_pose(frame, snapshot, OrientationPolicy::ValidatedDisBodyFrame);
    return 0;
}

#include "fuzz_standalone.hpp"
