#include <fastdis/fastdis_orientation.hpp>

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cmath>
#include <vector>

namespace {

bool near(double a, double b, double eps = 1e-12) {
    return std::fabs(a - b) <= eps;
}

void assert_unit(const fastdis::frames::Vec3d& v) {
    assert(near(fastdis::frames::norm(v), 1.0));
}

void assert_orthogonal(const fastdis::frames::Vec3d& a, const fastdis::frames::Vec3d& b) {
    assert(near(fastdis::frames::dot(a, b), 0.0));
}

void assert_body_basis(const fastdis::orientation::BodyFrdBasisEcef& body) {
    assert_unit(body.forward_ecef);
    assert_unit(body.right_ecef);
    assert_unit(body.down_ecef);
    assert_orthogonal(body.forward_ecef, body.right_ecef);
    assert_orthogonal(body.right_ecef, body.down_ecef);
    assert_orthogonal(body.down_ecef, body.forward_ecef);
    assert(near(fastdis::orientation::determinant(body.forward_ecef, body.right_ecef, body.down_ecef), 1.0));
}

void assert_target_basis(const fastdis::orientation::TargetBasis& basis, double expected_det_abs = 1.0) {
    assert_unit(basis.forward);
    assert_unit(basis.right);
    assert_unit(basis.up);
    assert_orthogonal(basis.forward, basis.right);
    assert_orthogonal(basis.right, basis.up);
    assert_orthogonal(basis.up, basis.forward);
    assert(near(std::fabs(fastdis::orientation::determinant(basis.forward, basis.right, basis.up)), expected_det_abs));
}

} // namespace

int main() {
    using namespace fastdis::frames;
    using namespace fastdis::orientation;

    const BodyFrdBasisEcef identity = dis_psi_theta_phi_to_body_frd_ecef(0.0, 0.0, 0.0);
    assert_body_basis(identity);
    assert(near(identity.forward_ecef.x, 1.0));
    assert(near(identity.right_ecef.y, 1.0));
    assert(near(identity.down_ecef.z, 1.0));

    const std::vector<BodyFrdBasisEcef> bodies{
        identity,
        dis_psi_theta_phi_to_body_frd_ecef(45.0 * deg_to_rad, 0.0, 0.0),
        dis_psi_theta_phi_to_body_frd_ecef(0.0, 20.0 * deg_to_rad, 0.0),
        dis_psi_theta_phi_to_body_frd_ecef(0.0, 0.0, 30.0 * deg_to_rad),
        dis_psi_theta_phi_to_body_frd_ecef(-123.0 * deg_to_rad, 47.8 * deg_to_rad, -29.7 * deg_to_rad),
    };
    for (const BodyFrdBasisEcef& body : bodies) {
        assert_body_basis(body);
    }

    const LocalEnuFrame equator = LocalEnuFrame::from_degrees(0.0, 0.0, 0.0);
    assert(near(equator.east.x, 0.0));
    assert(near(equator.east.y, 1.0));
    assert(near(equator.east.z, 0.0));
    assert(near(equator.north.x, 0.0));
    assert(near(equator.north.y, 0.0));
    assert(near(equator.north.z, 1.0));
    assert(near(equator.up.x, 1.0));
    assert(near(equator.up.y, 0.0));
    assert(near(equator.up.z, 0.0));

    const BodyFrdBasisEcef north_level_ecef{
        equator.north,
        equator.east,
        equator.up * -1.0,
    };
    assert_body_basis(north_level_ecef);
    const BodyFruBasisEnu north_level_enu = body_frd_ecef_to_body_fru_enu(north_level_ecef, equator);
    assert(near(north_level_enu.forward_enu.x, 0.0));
    assert(near(north_level_enu.forward_enu.y, 1.0));
    assert(near(north_level_enu.forward_enu.z, 0.0));
    assert(near(north_level_enu.right_enu.x, 1.0));
    assert(near(north_level_enu.right_enu.y, 0.0));
    assert(near(north_level_enu.right_enu.z, 0.0));
    assert(near(north_level_enu.up_enu.x, 0.0));
    assert(near(north_level_enu.up_enu.y, 0.0));
    assert(near(north_level_enu.up_enu.z, 1.0));

    const TargetBasis unreal = map_body_fru_enu_to_target_basis(north_level_enu, TargetFrame::StandaloneUnrealNorthEastUp);
    assert(near(unreal.forward.x, 1.0));
    assert(near(unreal.right.y, 1.0));
    assert(near(unreal.up.z, 1.0));
    assert_target_basis(unreal);

    const TargetBasis unity = map_body_fru_enu_to_target_basis(north_level_enu, TargetFrame::StandaloneUnityEastUpNorth);
    assert(near(unity.forward.z, 1.0));
    assert(near(unity.right.x, 1.0));
    assert(near(unity.up.y, 1.0));
    assert_target_basis(unity);

    const TargetBasis godot = map_body_fru_enu_to_target_basis(north_level_enu, TargetFrame::StandaloneGodotEastUpMinusNorth);
    assert(near(godot.forward.z, -1.0));
    assert(near(godot.right.x, 1.0));
    assert(near(godot.up.y, 1.0));
    assert_target_basis(godot);

    const TargetBasis cesium_js = map_body_fru_enu_to_target_basis(north_level_enu, TargetFrame::CesiumJsEastNorthUp);
    assert(near(cesium_js.forward.y, 1.0));
    assert(near(cesium_js.right.x, 1.0));
    assert(near(cesium_js.up.z, 1.0));
    assert_target_basis(cesium_js);

    const TargetBasis cesium_unreal = map_body_fru_enu_to_target_basis(north_level_enu, TargetFrame::CesiumUnrealEastSouthUp);
    assert(near(cesium_unreal.forward.y, -1.0));
    assert(near(cesium_unreal.right.x, 1.0));
    assert(near(cesium_unreal.up.z, 1.0));
    assert_target_basis(cesium_unreal);

    const Quatd q = quat_from_target_basis(unreal);
    assert(std::isfinite(q.w));
    assert(std::isfinite(q.x));
    assert(std::isfinite(q.y));
    assert(std::isfinite(q.z));

    return 0;
}
