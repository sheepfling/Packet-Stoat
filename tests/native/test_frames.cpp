#include <fastdis/fastdis_frames.hpp>

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cmath>
#include <vector>

namespace {

bool near(double a, double b, double eps = 1e-6) {
    return std::fabs(a - b) <= eps;
}

void assert_vec_near(const fastdis::frames::Vec3d& actual,
                     const fastdis::frames::Vec3d& expected,
                     double eps = 1e-6) {
    assert(near(actual.x, expected.x, eps));
    assert(near(actual.y, expected.y, eps));
    assert(near(actual.z, expected.z, eps));
}

fastdis_entity_transform_t transform_at(const fastdis::frames::Vec3d& ecef) {
    fastdis_entity_transform_t transform{};
    transform.location.x = ecef.x;
    transform.location.y = ecef.y;
    transform.location.z = ecef.z;
    return transform;
}

void assert_orthonormal(const fastdis::frames::LocalEnuFrame& frame) {
    using namespace fastdis::frames;
    assert(near(norm(frame.east), 1.0, 1e-12));
    assert(near(norm(frame.north), 1.0, 1e-12));
    assert(near(norm(frame.up), 1.0, 1e-12));
    assert(near(dot(frame.east, frame.north), 0.0, 1e-12));
    assert(near(dot(frame.east, frame.up), 0.0, 1e-12));
    assert(near(dot(frame.north, frame.up), 0.0, 1e-12));
}

void assert_roundtrip(const fastdis::frames::LocalEnuFrame& frame,
                      const fastdis::frames::Vec3d& enu) {
    const fastdis::frames::Vec3d ecef = frame.enu_to_ecef(enu);
    assert_vec_near(frame.ecef_to_enu(ecef), enu, 1e-8);
}

void assert_engine_axis_mapping(const fastdis::frames::LocalEnuFrame& frame) {
    using namespace fastdis::frames;

    const Vec3d east_ecef = frame.enu_to_ecef(Vec3d{1.0, 0.0, 0.0});
    const Vec3d north_ecef = frame.enu_to_ecef(Vec3d{0.0, 1.0, 0.0});
    const Vec3d up_ecef = frame.enu_to_ecef(Vec3d{0.0, 0.0, 1.0});

    const UnrealPoseData unreal_east = to_unreal_pose(frame, transform_at(east_ecef));
    assert(near(unreal_east.x_cm, 0.0, 1e-6));
    assert(near(unreal_east.y_cm, 100.0, 1e-6));
    assert(near(unreal_east.z_cm, 0.0, 1e-6));

    const UnrealPoseData unreal_north = to_unreal_pose(frame, transform_at(north_ecef));
    assert(near(unreal_north.x_cm, 100.0, 1e-6));
    assert(near(unreal_north.y_cm, 0.0, 1e-6));
    assert(near(unreal_north.z_cm, 0.0, 1e-6));

    const UnrealPoseData unreal_up = to_unreal_pose(frame, transform_at(up_ecef));
    assert(near(unreal_up.x_cm, 0.0, 1e-6));
    assert(near(unreal_up.y_cm, 0.0, 1e-6));
    assert(near(unreal_up.z_cm, 100.0, 1e-6));

    const GodotPoseData godot_east = to_godot_pose(frame, transform_at(east_ecef));
    assert(near(godot_east.x_m, 1.0, 1e-8));
    assert(near(godot_east.y_m, 0.0, 1e-8));
    assert(near(godot_east.z_m, 0.0, 1e-8));

    const GodotPoseData godot_north = to_godot_pose(frame, transform_at(north_ecef));
    assert(near(godot_north.x_m, 0.0, 1e-8));
    assert(near(godot_north.y_m, 0.0, 1e-8));
    assert(near(godot_north.z_m, -1.0, 1e-8));

    const GodotPoseData godot_up = to_godot_pose(frame, transform_at(up_ecef));
    assert(near(godot_up.x_m, 0.0, 1e-8));
    assert(near(godot_up.y_m, 1.0, 1e-8));
    assert(near(godot_up.z_m, 0.0, 1e-8));
}

fastdis::frames::Vec3d unreal_forward_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{m.m[0][0], m.m[1][0], m.m[2][0]};
}

fastdis::frames::Vec3d unreal_right_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{m.m[0][1], m.m[1][1], m.m[2][1]};
}

fastdis::frames::Vec3d unreal_up_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{m.m[0][2], m.m[1][2], m.m[2][2]};
}

fastdis::frames::Vec3d godot_forward_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{-m.m[0][2], -m.m[1][2], -m.m[2][2]};
}

fastdis::frames::Vec3d godot_right_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{m.m[0][0], m.m[1][0], m.m[2][0]};
}

fastdis::frames::Vec3d godot_up_from_quat(const fastdis::frames::Quatd& q) {
    const fastdis::frames::Mat3d m = fastdis::frames::matrix_from_quat(q);
    return fastdis::frames::Vec3d{m.m[0][1], m.m[1][1], m.m[2][1]};
}

void assert_engine_orientation_cases(const fastdis::frames::LocalEnuFrame& frame) {
    using namespace fastdis::frames;

    struct OrientationCase {
        fastdis_euler_angles_t orientation{};
        Vec3d unreal_forward;
        Vec3d unreal_right;
        Vec3d unreal_up;
        Vec3d godot_forward;
        Vec3d godot_right;
        Vec3d godot_up;
    };

    const std::vector<OrientationCase> cases{
        {{0.0f, 0.0f, 0.0f}, Vec3d{1.0, 0.0, 0.0}, Vec3d{0.0, 1.0, 0.0}, Vec3d{0.0, 0.0, 1.0},
                             Vec3d{0.0, 0.0, -1.0}, Vec3d{1.0, 0.0, 0.0}, Vec3d{0.0, 1.0, 0.0}},
        {{static_cast<float>(90.0 * deg_to_rad), 0.0f, 0.0f}, Vec3d{0.0, 1.0, 0.0}, Vec3d{-1.0, 0.0, 0.0}, Vec3d{0.0, 0.0, 1.0},
                                                               Vec3d{1.0, 0.0, 0.0}, Vec3d{0.0, 0.0, 1.0}, Vec3d{0.0, 1.0, 0.0}},
        {{0.0f, static_cast<float>(20.0 * deg_to_rad), 0.0f}, Vec3d{0.9396926208, 0.0, 0.3420201433}, Vec3d{0.0, 1.0, 0.0}, Vec3d{-0.3420201433, 0.0, 0.9396926208},
                                                               Vec3d{0.0, 0.3420201433, -0.9396926208}, Vec3d{1.0, 0.0, 0.0}, Vec3d{0.0, 0.9396926208, 0.3420201433}},
        {{0.0f, 0.0f, static_cast<float>(30.0 * deg_to_rad)}, Vec3d{1.0, 0.0, 0.0}, Vec3d{0.0, 0.8660254038, -0.5}, Vec3d{0.0, 0.5, 0.8660254038},
                                                               Vec3d{0.0, 0.0, -1.0}, Vec3d{0.8660254038, -0.5, 0.0}, Vec3d{0.5, 0.8660254038, 0.0}},
    };

    fastdis_entity_transform_t transform{};
    transform.location.x = frame.origin_ecef.x;
    transform.location.y = frame.origin_ecef.y;
    transform.location.z = frame.origin_ecef.z;

    for (const OrientationCase& item : cases) {
        transform.orientation = item.orientation;
        const UnrealPoseData unreal = to_unreal_pose(frame, transform, OrientationPolicy::ExperimentalLocalYawPitchRoll);
        assert_vec_near(unreal_forward_from_quat(unreal.rotation), item.unreal_forward, 1e-6);
        assert_vec_near(unreal_right_from_quat(unreal.rotation), item.unreal_right, 1e-6);
        assert_vec_near(unreal_up_from_quat(unreal.rotation), item.unreal_up, 1e-6);

        const GodotPoseData godot = to_godot_pose(frame, transform, OrientationPolicy::ExperimentalLocalYawPitchRoll);
        assert_vec_near(godot_forward_from_quat(godot.rotation), item.godot_forward, 1e-6);
        assert_vec_near(godot_right_from_quat(godot.rotation), item.godot_right, 1e-6);
        assert_vec_near(godot_up_from_quat(godot.rotation), item.godot_up, 1e-6);
    }
}

} // namespace

int main() {
    using namespace fastdis::frames;

    const LocalEnuFrame equator = LocalEnuFrame::from_degrees(0.0, 0.0, 0.0);
    const Vec3d origin = ecef_from_geodetic_degrees(0.0, 0.0, 0.0);
    assert(near(origin.x, wgs84_a_m, 1e-6));
    assert(near(origin.y, 0.0, 1e-6));
    assert(near(origin.z, 0.0, 1e-6));
    assert_orthonormal(equator);

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

    fastdis_entity_transform_t transform = transform_at(one_meter_north_ecef);

    const UnrealPoseData unreal = to_unreal_pose(equator, transform);
    assert(near(unreal.x_cm, 100.0));
    assert(near(unreal.y_cm, 0.0));
    assert(near(unreal.z_cm, 0.0));

    const GodotPoseData godot = to_godot_pose(equator, transform);
    assert(near(godot.x_m, 0.0));
    assert(near(godot.y_m, 0.0));
    assert(near(godot.z_m, -1.0));

    transform = transform_at(one_meter_east_ecef);
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
    const UnrealPoseData unreal_rot = to_unreal_pose(equator, transform, OrientationPolicy::ExperimentalLocalYawPitchRoll);
    assert(near(unreal_rot.rotation.w, 1.0));
    assert(near(unreal_rot.rotation.x, 0.0));
    assert(near(unreal_rot.rotation.y, 0.0));
    assert(near(unreal_rot.rotation.z, 0.0));

    const UnrealPoseData unreal_validated_placeholder =
        to_unreal_pose(equator, transform, OrientationPolicy::ValidatedDisBodyFrame);
    assert(near(unreal_validated_placeholder.rotation.w, 1.0));
    assert(near(unreal_validated_placeholder.rotation.x, 0.0));
    assert(near(unreal_validated_placeholder.rotation.y, 0.0));
    assert(near(unreal_validated_placeholder.rotation.z, 0.0));

    const AssetBasis default_basis{};
    assert(default_basis.forward == AssetForwardAxis::PositiveX);
    assert(default_basis.up == AssetUpAxis::PositiveZ);

    struct OriginFixture {
        double latitude_deg;
        double longitude_deg;
        double height_m;
    };

    const std::vector<OriginFixture> fixtures{
        {29.5597, -95.0831, 10.0},  // Houston / Ellington-style origin.
        {0.0, 0.0, 0.0},            // Equator and prime meridian.
        {45.0, -93.0, 250.0},       // Mid-latitude origin.
        {89.9, 45.0, 5.0},          // Near-pole stress origin.
    };

    for (const OriginFixture& fixture : fixtures) {
        const LocalEnuFrame frame =
            LocalEnuFrame::from_degrees(fixture.latitude_deg, fixture.longitude_deg, fixture.height_m);
        assert_orthonormal(frame);
        assert_roundtrip(frame, Vec3d{0.0, 0.0, 0.0});
        assert_roundtrip(frame, Vec3d{1.0, 0.0, 0.0});
        assert_roundtrip(frame, Vec3d{0.0, 1.0, 0.0});
        assert_roundtrip(frame, Vec3d{0.0, 0.0, 1.0});
        assert_roundtrip(frame, Vec3d{123.456, -78.9, 12.25});
        assert_engine_axis_mapping(frame);
        assert_engine_orientation_cases(frame);
    }

    return 0;
}
