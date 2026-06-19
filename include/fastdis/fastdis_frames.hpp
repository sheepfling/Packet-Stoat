#ifndef FASTDIS_FASTDIS_FRAMES_HPP
#define FASTDIS_FASTDIS_FRAMES_HPP

/*
 * Coordinate-frame helpers for engine adapters.
 *
 * This header is intentionally header-only and does not alter the fastdis C ABI.
 * It handles the part that is easy to get wrong when taking DIS Entity State
 * positions into game engines:
 *
 *   DIS Entity State location: geocentric Cartesian / ECEF meters
 *   Local simulation frame:    ENU meters about an explicit WGS-84 origin
 *   Unreal default frame:      +X forward/north, +Y right/east, +Z up, centimeters
 *   Godot default frame:       +X east/right, +Y up, -Z north/forward, meters
 *
 * Orientation policy is explicit. Position conversion is deterministic and
 * geodetic. Rotation conversion defaults to a conservative local yaw/pitch/roll
 * interpretation only when the caller opts into it. For authoritative exercise
 * interop, validate orientation conventions against your DIS standard/profile
 * and sample traffic before enabling orientation updates in an engine.
 */

#include <fastdis/fastdis.h>

#include <cmath>
#include <cstdint>

namespace fastdis {
namespace frames {

inline constexpr double pi = 3.141592653589793238462643383279502884;
inline constexpr double deg_to_rad = pi / 180.0;
inline constexpr double rad_to_deg = 180.0 / pi;
inline constexpr double wgs84_a_m = 6378137.0;
inline constexpr double wgs84_inv_f = 298.257223563;
inline constexpr double wgs84_f = 1.0 / wgs84_inv_f;
inline constexpr double wgs84_e2 = wgs84_f * (2.0 - wgs84_f);

struct Vec3d {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;

    constexpr Vec3d() = default;
    constexpr Vec3d(double xx, double yy, double zz) : x(xx), y(yy), z(zz) {}

    constexpr Vec3d operator+(const Vec3d& rhs) const noexcept { return Vec3d{x + rhs.x, y + rhs.y, z + rhs.z}; }
    constexpr Vec3d operator-(const Vec3d& rhs) const noexcept { return Vec3d{x - rhs.x, y - rhs.y, z - rhs.z}; }
    constexpr Vec3d operator*(double scale) const noexcept { return Vec3d{x * scale, y * scale, z * scale}; }
};

inline double dot(const Vec3d& a, const Vec3d& b) noexcept {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline Vec3d cross(const Vec3d& a, const Vec3d& b) noexcept {
    return Vec3d{a.y * b.z - a.z * b.y,
                 a.z * b.x - a.x * b.z,
                 a.x * b.y - a.y * b.x};
}

inline double norm(const Vec3d& v) noexcept { return std::sqrt(dot(v, v)); }

inline Vec3d normalized(const Vec3d& v) noexcept {
    const double n = norm(v);
    return n > 0.0 ? v * (1.0 / n) : Vec3d{};
}

inline Vec3d rotate_around_axis(const Vec3d& v, const Vec3d& axis, double radians) noexcept {
    const Vec3d unit_axis = normalized(axis);
    const double c = std::cos(radians);
    const double s = std::sin(radians);
    const Vec3d axis_cross_v = cross(unit_axis, v);
    const double axis_dot_v = dot(unit_axis, v);
    return v * c + axis_cross_v * s + unit_axis * (axis_dot_v * (1.0 - c));
}

struct Quatd {
    double w = 1.0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct Mat3d {
    // Row-major matrix.
    double m[3][3]{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}};
};

inline Mat3d identity_mat3() noexcept { return Mat3d{}; }

inline Mat3d transpose(const Mat3d& a) noexcept {
    Mat3d out{};
    for (int r = 0; r < 3; ++r) {
        for (int c = 0; c < 3; ++c) {
            out.m[r][c] = a.m[c][r];
        }
    }
    return out;
}

inline Mat3d mul(const Mat3d& a, const Mat3d& b) noexcept {
    Mat3d out{};
    for (int r = 0; r < 3; ++r) {
        for (int c = 0; c < 3; ++c) {
            out.m[r][c] = a.m[r][0] * b.m[0][c] + a.m[r][1] * b.m[1][c] + a.m[r][2] * b.m[2][c];
        }
    }
    return out;
}

inline Vec3d mul(const Mat3d& a, const Vec3d& v) noexcept {
    return Vec3d{a.m[0][0] * v.x + a.m[0][1] * v.y + a.m[0][2] * v.z,
                 a.m[1][0] * v.x + a.m[1][1] * v.y + a.m[1][2] * v.z,
                 a.m[2][0] * v.x + a.m[2][1] * v.y + a.m[2][2] * v.z};
}

inline Mat3d rotation_x(double radians) noexcept {
    const double c = std::cos(radians);
    const double s = std::sin(radians);
    Mat3d out{};
    out.m[1][1] = c;
    out.m[1][2] = -s;
    out.m[2][1] = s;
    out.m[2][2] = c;
    return out;
}

inline Mat3d rotation_y(double radians) noexcept {
    const double c = std::cos(radians);
    const double s = std::sin(radians);
    Mat3d out{};
    out.m[0][0] = c;
    out.m[0][2] = s;
    out.m[2][0] = -s;
    out.m[2][2] = c;
    return out;
}

inline Mat3d rotation_z(double radians) noexcept {
    const double c = std::cos(radians);
    const double s = std::sin(radians);
    Mat3d out{};
    out.m[0][0] = c;
    out.m[0][1] = -s;
    out.m[1][0] = s;
    out.m[1][1] = c;
    return out;
}

inline Mat3d local_yaw_pitch_roll_matrix(double psi_yaw_rad, double theta_pitch_rad, double phi_roll_rad) noexcept {
    // Conservative opt-in approximation: ENU row/column axes, yaw about Up/Z,
    // pitch about local Y, roll about local X, using ZYX composition.
    return mul(mul(rotation_z(psi_yaw_rad), rotation_y(theta_pitch_rad)), rotation_x(phi_roll_rad));
}

inline Quatd quat_from_matrix(const Mat3d& m) noexcept {
    Quatd q{};
    const double trace = m.m[0][0] + m.m[1][1] + m.m[2][2];
    if (trace > 0.0) {
        const double s = std::sqrt(trace + 1.0) * 2.0;
        q.w = 0.25 * s;
        q.x = (m.m[2][1] - m.m[1][2]) / s;
        q.y = (m.m[0][2] - m.m[2][0]) / s;
        q.z = (m.m[1][0] - m.m[0][1]) / s;
    } else if (m.m[0][0] > m.m[1][1] && m.m[0][0] > m.m[2][2]) {
        const double s = std::sqrt(1.0 + m.m[0][0] - m.m[1][1] - m.m[2][2]) * 2.0;
        q.w = (m.m[2][1] - m.m[1][2]) / s;
        q.x = 0.25 * s;
        q.y = (m.m[0][1] + m.m[1][0]) / s;
        q.z = (m.m[0][2] + m.m[2][0]) / s;
    } else if (m.m[1][1] > m.m[2][2]) {
        const double s = std::sqrt(1.0 + m.m[1][1] - m.m[0][0] - m.m[2][2]) * 2.0;
        q.w = (m.m[0][2] - m.m[2][0]) / s;
        q.x = (m.m[0][1] + m.m[1][0]) / s;
        q.y = 0.25 * s;
        q.z = (m.m[1][2] + m.m[2][1]) / s;
    } else {
        const double s = std::sqrt(1.0 + m.m[2][2] - m.m[0][0] - m.m[1][1]) * 2.0;
        q.w = (m.m[1][0] - m.m[0][1]) / s;
        q.x = (m.m[0][2] + m.m[2][0]) / s;
        q.y = (m.m[1][2] + m.m[2][1]) / s;
        q.z = 0.25 * s;
    }
    const double n = std::sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    if (n > 0.0) {
        q.w /= n;
        q.x /= n;
        q.y /= n;
        q.z /= n;
    }
    return q;
}

inline Mat3d matrix_from_quat(const Quatd& q) noexcept {
    const double xx = q.x * q.x;
    const double yy = q.y * q.y;
    const double zz = q.z * q.z;
    const double xy = q.x * q.y;
    const double xz = q.x * q.z;
    const double yz = q.y * q.z;
    const double wx = q.w * q.x;
    const double wy = q.w * q.y;
    const double wz = q.w * q.z;

    Mat3d out{};
    out.m[0][0] = 1.0 - 2.0 * (yy + zz);
    out.m[0][1] = 2.0 * (xy - wz);
    out.m[0][2] = 2.0 * (xz + wy);
    out.m[1][0] = 2.0 * (xy + wz);
    out.m[1][1] = 1.0 - 2.0 * (xx + zz);
    out.m[1][2] = 2.0 * (yz - wx);
    out.m[2][0] = 2.0 * (xz - wy);
    out.m[2][1] = 2.0 * (yz + wx);
    out.m[2][2] = 1.0 - 2.0 * (xx + yy);
    return out;
}

inline Vec3d ecef_from_geodetic_radians(double latitude_rad, double longitude_rad, double height_m) noexcept {
    const double sin_lat = std::sin(latitude_rad);
    const double cos_lat = std::cos(latitude_rad);
    const double sin_lon = std::sin(longitude_rad);
    const double cos_lon = std::cos(longitude_rad);
    const double n = wgs84_a_m / std::sqrt(1.0 - wgs84_e2 * sin_lat * sin_lat);
    return Vec3d{(n + height_m) * cos_lat * cos_lon,
                 (n + height_m) * cos_lat * sin_lon,
                 (n * (1.0 - wgs84_e2) + height_m) * sin_lat};
}

inline Vec3d ecef_from_geodetic_degrees(double latitude_deg, double longitude_deg, double height_m) noexcept {
    return ecef_from_geodetic_radians(latitude_deg * deg_to_rad, longitude_deg * deg_to_rad, height_m);
}

enum class OrientationPolicy : std::uint32_t {
    PositionOnly = 0,
    ExperimentalLocalYawPitchRoll = 1,
    LocalYawPitchRoll = ExperimentalLocalYawPitchRoll,
    ValidatedDisBodyFrame = 2,
};

enum class AssetForwardAxis : std::uint32_t {
    PositiveX = 0,
    NegativeX = 1,
    PositiveY = 2,
    NegativeY = 3,
    PositiveZ = 4,
    NegativeZ = 5,
};

enum class AssetUpAxis : std::uint32_t {
    PositiveX = 0,
    NegativeX = 1,
    PositiveY = 2,
    NegativeY = 3,
    PositiveZ = 4,
    NegativeZ = 5,
};

struct AssetBasis {
    AssetForwardAxis forward = AssetForwardAxis::PositiveX;
    AssetUpAxis up = AssetUpAxis::PositiveZ;
};

inline Vec3d canonical_forward_axis() noexcept { return Vec3d{1.0, 0.0, 0.0}; }
inline Vec3d canonical_right_axis() noexcept { return Vec3d{0.0, 1.0, 0.0}; }
inline Vec3d canonical_up_axis() noexcept { return Vec3d{0.0, 0.0, 1.0}; }

inline int asset_axis_index(AssetForwardAxis axis) noexcept {
    switch (axis) {
        case AssetForwardAxis::PositiveX:
        case AssetForwardAxis::NegativeX:
            return 0;
        case AssetForwardAxis::PositiveY:
        case AssetForwardAxis::NegativeY:
            return 1;
        case AssetForwardAxis::PositiveZ:
        case AssetForwardAxis::NegativeZ:
            return 2;
    }
    return 0;
}

inline int asset_axis_index(AssetUpAxis axis) noexcept {
    switch (axis) {
        case AssetUpAxis::PositiveX:
        case AssetUpAxis::NegativeX:
            return 0;
        case AssetUpAxis::PositiveY:
        case AssetUpAxis::NegativeY:
            return 1;
        case AssetUpAxis::PositiveZ:
        case AssetUpAxis::NegativeZ:
            return 2;
    }
    return 0;
}

inline double asset_axis_sign(AssetForwardAxis axis) noexcept {
    switch (axis) {
        case AssetForwardAxis::PositiveX:
        case AssetForwardAxis::PositiveY:
        case AssetForwardAxis::PositiveZ:
            return 1.0;
        case AssetForwardAxis::NegativeX:
        case AssetForwardAxis::NegativeY:
        case AssetForwardAxis::NegativeZ:
            return -1.0;
    }
    return 1.0;
}

inline double asset_axis_sign(AssetUpAxis axis) noexcept {
    switch (axis) {
        case AssetUpAxis::PositiveX:
        case AssetUpAxis::PositiveY:
        case AssetUpAxis::PositiveZ:
            return 1.0;
        case AssetUpAxis::NegativeX:
        case AssetUpAxis::NegativeY:
        case AssetUpAxis::NegativeZ:
            return -1.0;
    }
    return 1.0;
}

inline bool try_make_asset_basis_correction_matrix(const AssetBasis& asset_basis, Mat3d& out) noexcept {
    const int forward_index = asset_axis_index(asset_basis.forward);
    const int up_index = asset_axis_index(asset_basis.up);
    if (forward_index == up_index) {
        return false;
    }

    Vec3d columns[3]{};
    bool assigned[3]{false, false, false};

    columns[forward_index] = canonical_forward_axis() * asset_axis_sign(asset_basis.forward);
    assigned[forward_index] = true;

    columns[up_index] = canonical_up_axis() * asset_axis_sign(asset_basis.up);
    assigned[up_index] = true;

    int missing_index = 0;
    while (missing_index < 3 && assigned[missing_index]) {
        ++missing_index;
    }
    if (missing_index >= 3) {
        return false;
    }

    if (missing_index == 0) {
        columns[0] = cross(columns[1], columns[2]);
    } else if (missing_index == 1) {
        columns[1] = cross(columns[2], columns[0]);
    } else {
        columns[2] = cross(columns[0], columns[1]);
    }

    if (norm(columns[missing_index]) == 0.0) {
        return false;
    }
    columns[missing_index] = normalized(columns[missing_index]);

    out = Mat3d{};
    for (int column = 0; column < 3; ++column) {
        out.m[0][column] = columns[column].x;
        out.m[1][column] = columns[column].y;
        out.m[2][column] = columns[column].z;
    }
    return true;
}

inline bool asset_basis_is_valid(const AssetBasis& asset_basis) noexcept {
    Mat3d correction{};
    return try_make_asset_basis_correction_matrix(asset_basis, correction);
}

inline Quatd quat_from_asset_basis_correction(const AssetBasis& asset_basis) noexcept {
    Mat3d correction{};
    if (!try_make_asset_basis_correction_matrix(asset_basis, correction)) {
        return Quatd{};
    }
    return quat_from_matrix(correction);
}

struct LocalEnuFrame {
    double latitude_rad = 0.0;
    double longitude_rad = 0.0;
    double height_m = 0.0;
    Vec3d origin_ecef{};
    Vec3d east{1.0, 0.0, 0.0};
    Vec3d north{0.0, 1.0, 0.0};
    Vec3d up{0.0, 0.0, 1.0};

    static LocalEnuFrame from_radians(double latitude_rad, double longitude_rad, double height_m) noexcept {
        LocalEnuFrame frame{};
        frame.latitude_rad = latitude_rad;
        frame.longitude_rad = longitude_rad;
        frame.height_m = height_m;
        frame.origin_ecef = ecef_from_geodetic_radians(latitude_rad, longitude_rad, height_m);

        const double sin_lat = std::sin(latitude_rad);
        const double cos_lat = std::cos(latitude_rad);
        const double sin_lon = std::sin(longitude_rad);
        const double cos_lon = std::cos(longitude_rad);

        frame.east = Vec3d{-sin_lon, cos_lon, 0.0};
        frame.north = Vec3d{-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat};
        frame.up = Vec3d{cos_lat * cos_lon, cos_lat * sin_lon, sin_lat};
        return frame;
    }

    static LocalEnuFrame from_degrees(double latitude_deg, double longitude_deg, double height_m) noexcept {
        return from_radians(latitude_deg * deg_to_rad, longitude_deg * deg_to_rad, height_m);
    }

    Vec3d ecef_to_enu(const Vec3d& ecef) const noexcept {
        const Vec3d d = ecef - origin_ecef;
        return Vec3d{dot(d, east), dot(d, north), dot(d, up)};
    }

    Vec3d ecef_to_enu(const fastdis_world_coordinates_t& ecef) const noexcept {
        return ecef_to_enu(Vec3d{ecef.x, ecef.y, ecef.z});
    }

    Vec3d enu_to_ecef(const Vec3d& enu_m) const noexcept {
        return origin_ecef + east * enu_m.x + north * enu_m.y + up * enu_m.z;
    }

    Vec3d ecef_vector_to_enu(const Vec3d& vector_ecef) const noexcept {
        return Vec3d{dot(vector_ecef, east), dot(vector_ecef, north), dot(vector_ecef, up)};
    }

    Vec3d ecef_vector_to_enu(const fastdis_vec3f_t& vector_ecef) const noexcept {
        return ecef_vector_to_enu(Vec3d{static_cast<double>(vector_ecef.x),
                                        static_cast<double>(vector_ecef.y),
                                        static_cast<double>(vector_ecef.z)});
    }
};

struct UnrealPoseData {
    // Unreal units are centimeters. Axes: X=north/forward, Y=east/right, Z=up.
    double x_cm = 0.0;
    double y_cm = 0.0;
    double z_cm = 0.0;
    Quatd rotation{};
    Vec3d velocity_cm_per_s{};
};

struct GodotPoseData {
    // Godot units are meters by convention. Axes: X=east/right, Y=up, Z=-north/forward.
    double x_m = 0.0;
    double y_m = 0.0;
    double z_m = 0.0;
    Quatd rotation{};
    Vec3d velocity_m_per_s{};
};

struct LocalBodyBasisEnu {
    Vec3d forward{1.0, 0.0, 0.0};
    Vec3d right{0.0, 1.0, 0.0};
    Vec3d up{0.0, 0.0, 1.0};
};

inline Mat3d enu_to_unreal_axes_matrix() noexcept {
    Mat3d p{};
    // rows are Unreal X/Y/Z, columns are ENU E/N/U.
    p.m[0][0] = 0.0; p.m[0][1] = 1.0; p.m[0][2] = 0.0;
    p.m[1][0] = 1.0; p.m[1][1] = 0.0; p.m[1][2] = 0.0;
    p.m[2][0] = 0.0; p.m[2][1] = 0.0; p.m[2][2] = 1.0;
    return p;
}

inline Mat3d enu_to_godot_axes_matrix() noexcept {
    Mat3d p{};
    // rows are Godot X/Y/Z, columns are ENU E/N/U.
    p.m[0][0] = 1.0; p.m[0][1] = 0.0;  p.m[0][2] = 0.0;
    p.m[1][0] = 0.0; p.m[1][1] = 0.0;  p.m[1][2] = 1.0;
    p.m[2][0] = 0.0; p.m[2][1] = -1.0; p.m[2][2] = 0.0;
    return p;
}

inline Vec3d enu_to_unreal_cm(const Vec3d& enu_m) noexcept {
    return Vec3d{enu_m.y * 100.0, enu_m.x * 100.0, enu_m.z * 100.0};
}

inline Vec3d enu_to_godot_m(const Vec3d& enu_m) noexcept {
    return Vec3d{enu_m.x, enu_m.z, -enu_m.y};
}

inline LocalBodyBasisEnu experimental_local_hpr_to_body_enu(const fastdis_euler_angles_t& orientation) noexcept {
    // Experimental local orientation interpretation for engine adapters:
    // psi   = heading from local north, positive toward east
    // theta = pitch, positive climb
    // phi   = roll, positive right-bank
    const double heading = static_cast<double>(orientation.psi);
    const double pitch = static_cast<double>(orientation.theta);
    const double roll = static_cast<double>(orientation.phi);

    const Vec3d forward0{std::sin(heading), std::cos(heading), 0.0};
    const Vec3d right0{std::cos(heading), -std::sin(heading), 0.0};
    const Vec3d up0{0.0, 0.0, 1.0};

    const Vec3d forward1 = normalized(rotate_around_axis(forward0, right0, pitch));
    const Vec3d up1 = normalized(rotate_around_axis(up0, right0, pitch));
    const Vec3d right1 = normalized(right0);

    const Vec3d right2 = normalized(rotate_around_axis(right1, forward1, roll));
    const Vec3d up2 = normalized(rotate_around_axis(up1, forward1, roll));
    return LocalBodyBasisEnu{forward1, right2, up2};
}

inline Quatd unreal_quat_from_experimental_local_hpr(const fastdis_euler_angles_t& orientation) noexcept {
    const LocalBodyBasisEnu body = experimental_local_hpr_to_body_enu(orientation);
    const Vec3d forward = normalized(enu_to_unreal_cm(body.forward));
    const Vec3d right = normalized(enu_to_unreal_cm(body.right));
    const Vec3d up = normalized(enu_to_unreal_cm(body.up));

    Mat3d basis{};
    basis.m[0][0] = forward.x; basis.m[1][0] = forward.y; basis.m[2][0] = forward.z;
    basis.m[0][1] = right.x;   basis.m[1][1] = right.y;   basis.m[2][1] = right.z;
    basis.m[0][2] = up.x;      basis.m[1][2] = up.y;      basis.m[2][2] = up.z;
    return quat_from_matrix(basis);
}

inline Quatd godot_quat_from_experimental_local_hpr(const fastdis_euler_angles_t& orientation) noexcept {
    const LocalBodyBasisEnu body = experimental_local_hpr_to_body_enu(orientation);
    const Vec3d forward = normalized(enu_to_godot_m(body.forward));
    const Vec3d right = normalized(enu_to_godot_m(body.right));
    const Vec3d up = normalized(enu_to_godot_m(body.up));
    const Vec3d back = forward * -1.0;

    Mat3d basis{};
    // Godot Basis columns are x=right, y=up, z=back.
    basis.m[0][0] = right.x; basis.m[1][0] = right.y; basis.m[2][0] = right.z;
    basis.m[0][1] = up.x;    basis.m[1][1] = up.y;    basis.m[2][1] = up.z;
    basis.m[0][2] = back.x;  basis.m[1][2] = back.y;  basis.m[2][2] = back.z;
    return quat_from_matrix(basis);
}

inline Quatd identity_quat() noexcept {
    return Quatd{};
}

inline UnrealPoseData to_unreal_pose(const LocalEnuFrame& frame,
                                     const fastdis_entity_transform_t& transform,
                                     OrientationPolicy orientation_policy = OrientationPolicy::PositionOnly) noexcept {
    const Vec3d enu = frame.ecef_to_enu(transform.location);
    const Vec3d pos = enu_to_unreal_cm(enu);
    UnrealPoseData out{};
    out.x_cm = pos.x;
    out.y_cm = pos.y;
    out.z_cm = pos.z;
    out.velocity_cm_per_s = enu_to_unreal_cm(frame.ecef_vector_to_enu(transform.linear_velocity));
    if (orientation_policy == OrientationPolicy::ExperimentalLocalYawPitchRoll) {
        out.rotation = unreal_quat_from_experimental_local_hpr(transform.orientation);
    } else {
        out.rotation = identity_quat();
    }
    return out;
}

inline GodotPoseData to_godot_pose(const LocalEnuFrame& frame,
                                   const fastdis_entity_transform_t& transform,
                                   OrientationPolicy orientation_policy = OrientationPolicy::PositionOnly) noexcept {
    const Vec3d enu = frame.ecef_to_enu(transform.location);
    const Vec3d pos = enu_to_godot_m(enu);
    GodotPoseData out{};
    out.x_m = pos.x;
    out.y_m = pos.y;
    out.z_m = pos.z;
    out.velocity_m_per_s = enu_to_godot_m(frame.ecef_vector_to_enu(transform.linear_velocity));
    if (orientation_policy == OrientationPolicy::ExperimentalLocalYawPitchRoll) {
        out.rotation = godot_quat_from_experimental_local_hpr(transform.orientation);
    } else {
        out.rotation = identity_quat();
    }
    return out;
}

inline UnrealPoseData to_unreal_pose(const LocalEnuFrame& frame,
                                     const fastdis_entity_snapshot_t& snapshot,
                                     OrientationPolicy orientation_policy = OrientationPolicy::PositionOnly) noexcept {
    return to_unreal_pose(frame, snapshot.transform, orientation_policy);
}

inline GodotPoseData to_godot_pose(const LocalEnuFrame& frame,
                                   const fastdis_entity_snapshot_t& snapshot,
                                   OrientationPolicy orientation_policy = OrientationPolicy::PositionOnly) noexcept {
    return to_godot_pose(frame, snapshot.transform, orientation_policy);
}

} // namespace frames
} // namespace fastdis

#endif /* FASTDIS_FASTDIS_FRAMES_HPP */
