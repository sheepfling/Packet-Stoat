#include <fastdis/fastdis_frames.hpp>

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cmath>

namespace {

bool near(double a, double b, double eps = 1e-6) {
    return std::fabs(a - b) <= eps;
}

} // namespace

int main() {
    using namespace fastdis::frames;

    const LocalEnuFrame equator = LocalEnuFrame::from_degrees(0.0, 0.0, 0.0);
    const Vec3d origin = ecef_from_geodetic_degrees(0.0, 0.0, 0.0);
    assert(near(origin.x, wgs84_a_m, 1e-6));
    assert(near(origin.y, 0.0, 1e-6));
    assert(near(origin.z, 0.0, 1e-6));

    const Vec3d one_meter_east_ecef = equator.origin_ecef + equator.east * 1.0;
    const Vec3d east_enu = equator.ecef_to_enu(one_meter_east_ecef);
    assert(near(east_enu.x, 1.0));
    assert(near(east_enu.y, 0.0));
    assert(near(east_enu.z, 0.0));

    const Vec3d one_meter_north_ecef = equator.origin_ecef + equator.north * 1.0;
    const Vec3d north_enu = equator.ecef_to_enu(one_meter_north_ecef);
    assert(near(north_enu.x, 0.0));
    assert(near(north_enu.y, 1.0));
    assert(near(north_enu.z, 0.0));

    const Vec3d one_meter_up_ecef = equator.origin_ecef + equator.up * 1.0;
    const Vec3d up_enu = equator.ecef_to_enu(one_meter_up_ecef);
    assert(near(up_enu.x, 0.0));
    assert(near(up_enu.y, 0.0));
    assert(near(up_enu.z, 1.0));

    fastdis_entity_transform_t transform{};
    transform.location.x = one_meter_north_ecef.x;
    transform.location.y = one_meter_north_ecef.y;
    transform.location.z = one_meter_north_ecef.z;

    const UnrealPoseData unreal = to_unreal_pose(equator, transform);
    assert(near(unreal.x_cm, 100.0));
    assert(near(unreal.y_cm, 0.0));
    assert(near(unreal.z_cm, 0.0));

    const GodotPoseData godot = to_godot_pose(equator, transform);
    assert(near(godot.x_m, 0.0));
    assert(near(godot.y_m, 0.0));
    assert(near(godot.z_m, -1.0));

    transform.location = fastdis_world_coordinates_t{one_meter_east_ecef.x, one_meter_east_ecef.y, one_meter_east_ecef.z};
    const UnrealPoseData unreal_east = to_unreal_pose(equator, transform);
    assert(near(unreal_east.x_cm, 0.0));
    assert(near(unreal_east.y_cm, 100.0));
    assert(near(unreal_east.z_cm, 0.0));

    const GodotPoseData godot_east = to_godot_pose(equator, transform);
    assert(near(godot_east.x_m, 1.0));
    assert(near(godot_east.y_m, 0.0));
    assert(near(godot_east.z_m, 0.0));

    transform.orientation.psi = 0.0f;
    transform.orientation.theta = 0.0f;
    transform.orientation.phi = 0.0f;
    const UnrealPoseData unreal_rot = to_unreal_pose(equator, transform, OrientationPolicy::LocalYawPitchRoll);
    assert(near(unreal_rot.rotation.w, 1.0));
    assert(near(unreal_rot.rotation.x, 0.0));
    assert(near(unreal_rot.rotation.y, 0.0));
    assert(near(unreal_rot.rotation.z, 0.0));

    return 0;
}
