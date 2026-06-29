#ifndef FASTDIS_FASTDIS_ORIENTATION_HPP
#define FASTDIS_FASTDIS_ORIENTATION_HPP

/*
 * Experimental orientation convention helpers.
 *
 * This header is intentionally header-only and does not alter the fastdis C ABI.
 * The stable default path remains position-only. Orientation should not be
 * enabled in engine adapters until golden DIS fixtures, oracle tests, and engine
 * basis checks pass.
 */

#include <fastdis/fastdis_frames.hpp>

#include <cstdint>

namespace fastdis {
namespace orientation {

using frames::Mat3d;
using frames::Quatd;
using frames::Vec3d;

struct BodyFrdBasisEcef {
    Vec3d forward_ecef; // body +X: nose / forward
    Vec3d right_ecef;   // body +Y: starboard / right wing
    Vec3d down_ecef;    // body +Z: belly / down
};

struct BodyFruBasisEnu {
    Vec3d forward_enu;
    Vec3d right_enu;
    Vec3d up_enu;
};

enum class TargetFrame : std::uint32_t {
    StandaloneUnrealNorthEastUp = 0,
    StandaloneUnityEastUpNorth = 1,
    StandaloneGodotEastUpMinusNorth = 2,
    CesiumJsEastNorthUp = 3,
    CesiumUnityEastUpNorth = 4,
    CesiumUnrealEastSouthUp = 5,
};

inline double determinant(const Vec3d& x, const Vec3d& y, const Vec3d& z) noexcept {
    return frames::dot(x, frames::cross(y, z));
}

inline double determinant(const Mat3d& m) noexcept {
    return m.m[0][0] * (m.m[1][1] * m.m[2][2] - m.m[1][2] * m.m[2][1]) -
           m.m[0][1] * (m.m[1][0] * m.m[2][2] - m.m[1][2] * m.m[2][0]) +
           m.m[0][2] * (m.m[1][0] * m.m[2][1] - m.m[1][1] * m.m[2][0]);
}

inline BodyFrdBasisEcef dis_psi_theta_phi_to_body_frd_ecef(double psi_rad,
                                                           double theta_rad,
                                                           double phi_rad) noexcept {
    // DIS orientation convention: start with body axes coincident with ECEF XYZ,
    // rotate psi about ECEF Z, theta about the rotated Y, and phi about the
    // latest rotated X. Matrix columns are body +X/+Y/+Z expressed in ECEF.
    const Mat3d r = frames::mul(frames::mul(frames::rotation_z(psi_rad),
                                           frames::rotation_y(theta_rad)),
                                frames::rotation_x(phi_rad));
    return BodyFrdBasisEcef{
        Vec3d{r.m[0][0], r.m[1][0], r.m[2][0]},
        Vec3d{r.m[0][1], r.m[1][1], r.m[2][1]},
        Vec3d{r.m[0][2], r.m[1][2], r.m[2][2]},
    };
}

inline BodyFrdBasisEcef dis_orientation_to_body_frd_ecef(const fastdis_euler_angles_t& orientation) noexcept {
    return dis_psi_theta_phi_to_body_frd_ecef(static_cast<double>(orientation.psi),
                                             static_cast<double>(orientation.theta),
                                             static_cast<double>(orientation.phi));
}

inline BodyFruBasisEnu body_frd_ecef_to_body_fru_enu(const BodyFrdBasisEcef& body,
                                                     const frames::LocalEnuFrame& frame) noexcept {
    return BodyFruBasisEnu{
        frame.ecef_vector_to_enu(body.forward_ecef),
        frame.ecef_vector_to_enu(body.right_ecef),
        frame.ecef_vector_to_enu(body.down_ecef * -1.0),
    };
}

inline Vec3d map_enu_direction_to_target(const Vec3d& enu, TargetFrame target) noexcept {
    switch (target) {
        case TargetFrame::StandaloneUnrealNorthEastUp:
            return Vec3d{enu.y, enu.x, enu.z};
        case TargetFrame::StandaloneUnityEastUpNorth:
        case TargetFrame::CesiumUnityEastUpNorth:
            return Vec3d{enu.x, enu.z, enu.y};
        case TargetFrame::StandaloneGodotEastUpMinusNorth:
            return Vec3d{enu.x, enu.z, -enu.y};
        case TargetFrame::CesiumJsEastNorthUp:
            return Vec3d{enu.x, enu.y, enu.z};
        case TargetFrame::CesiumUnrealEastSouthUp:
            return Vec3d{enu.x, -enu.y, enu.z};
    }
    return enu;
}

struct TargetBasis {
    Vec3d forward;
    Vec3d right;
    Vec3d up;
};

inline TargetBasis map_body_fru_enu_to_target_basis(const BodyFruBasisEnu& body, TargetFrame target) noexcept {
    return TargetBasis{
        map_enu_direction_to_target(body.forward_enu, target),
        map_enu_direction_to_target(body.right_enu, target),
        map_enu_direction_to_target(body.up_enu, target),
    };
}

inline Quatd quat_from_target_basis(const TargetBasis& basis) noexcept {
    Mat3d m{};
    // Matrix columns are forward, right, up in target coordinates. This is a
    // diagnostic quaternion path; engine adapters should prefer native
    // basis/matrix constructors and validate axis queries.
    m.m[0][0] = basis.forward.x;
    m.m[1][0] = basis.forward.y;
    m.m[2][0] = basis.forward.z;
    m.m[0][1] = basis.right.x;
    m.m[1][1] = basis.right.y;
    m.m[2][1] = basis.right.z;
    m.m[0][2] = basis.up.x;
    m.m[1][2] = basis.up.y;
    m.m[2][2] = basis.up.z;
    return frames::quat_from_matrix(m);
}

} // namespace orientation
} // namespace fastdis

#endif /* FASTDIS_FASTDIS_ORIENTATION_HPP */
