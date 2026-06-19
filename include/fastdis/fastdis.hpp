#ifndef FASTDIS_FASTDIS_HPP
#define FASTDIS_FASTDIS_HPP

/*
 * Header-only C++ convenience wrappers for the stable fastdis C ABI.
 *
 * This file intentionally does not define or export any ABI of its own. It is
 * a zero/low-cost C++ ownership and ergonomics layer over fastdis.h, meant for
 * first-class C++ consumers such as Unreal modules, Godot GDExtensions, native
 * simulation tools, and tests.
 *
 * Design rules:
 *   - The shared-library/DLL boundary remains the plain C ABI in fastdis.h.
 *   - Opaque C handles are owned by move-only RAII classes.
 *   - Borrowed snapshot-buffer views are released by ScopedSnapshotView.
 *   - Methods named try_* return fastdis_status_t and never throw.
 *   - Convenience methods check status. By default they throw fastdis::Error;
 *     define FASTDIS_CPP_NO_EXCEPTIONS to make them assert instead.
 */

#include <fastdis/fastdis.h>

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <string>
#include <utility>
#include <vector>

#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
#include <stdexcept>
#endif

namespace fastdis {

using Status = fastdis_status_t;
using Header = fastdis_header_t;
using EntityId = fastdis_entity_id_t;
using EntityType = fastdis_entity_type_t;
using Vec3f = fastdis_vec3f_t;
using WorldCoordinates = fastdis_world_coordinates_t;
using EulerAngles = fastdis_euler_angles_t;
using EntityStatePrefix = fastdis_entity_state_prefix_t;
using EntityTransform = fastdis_entity_transform_t;
using EntitySnapshot = fastdis_entity_snapshot_t;
using SnapshotViewNative = fastdis_entity_snapshot_view_t;
using ScanStats = fastdis_scan_stats_t;
using EntityTableUpdateStats = fastdis_entity_table_update_stats_t;
using SnapshotBufferStats = fastdis_entity_snapshot_buffer_stats_t;
using PacketView = fastdis_packet_view_t;

inline constexpr std::uint32_t abi_version_constant = FASTDIS_ABI_VERSION;
inline constexpr std::uint32_t header_size = FASTDIS_HEADER_SIZE;
inline constexpr std::uint32_t protocol_version_dis6 = FASTDIS_PROTOCOL_VERSION_DIS6;
inline constexpr std::uint32_t protocol_version_dis7 = FASTDIS_PROTOCOL_VERSION_DIS7;
inline constexpr std::int16_t header_status_unavailable = FASTDIS_HEADER_STATUS_UNAVAILABLE;
inline constexpr std::uint32_t entity_information_family = FASTDIS_ENTITY_INFORMATION_FAMILY;
inline constexpr std::uint32_t entity_state_pdu_type = FASTDIS_ENTITY_STATE_PDU_TYPE;
inline constexpr std::uint32_t entity_state_fixed_size = FASTDIS_ENTITY_STATE_FIXED_SIZE;

inline constexpr std::uint64_t es_field_header = FASTDIS_ES_FIELD_HEADER;
inline constexpr std::uint64_t es_field_entity_id = FASTDIS_ES_FIELD_ENTITY_ID;
inline constexpr std::uint64_t es_field_force_id = FASTDIS_ES_FIELD_FORCE_ID;
inline constexpr std::uint64_t es_field_location = FASTDIS_ES_FIELD_LOCATION;
inline constexpr std::uint64_t es_field_orientation = FASTDIS_ES_FIELD_ORIENTATION;
inline constexpr std::uint64_t es_field_linear_velocity = FASTDIS_ES_FIELD_LINEAR_VELOCITY;
inline constexpr std::uint64_t es_field_routing = FASTDIS_ES_FIELD_ROUTING;
inline constexpr std::uint64_t es_field_pose = FASTDIS_ES_FIELD_POSE;
inline constexpr std::uint64_t es_field_kinematics = FASTDIS_ES_FIELD_KINEMATICS;
inline constexpr std::uint64_t es_field_all = FASTDIS_ES_FIELD_ALL;

inline const char* version_string() noexcept { return fastdis_version_string(); }
inline std::uint32_t abi_version() noexcept { return fastdis_abi_version(); }
inline bool abi_matches() noexcept { return fastdis_abi_version() == FASTDIS_ABI_VERSION; }
inline const char* status_string(Status status) noexcept { return fastdis_status_string(status); }
inline bool succeeded(Status status) noexcept { return status == FASTDIS_OK; }
inline bool failed(Status status) noexcept { return status != FASTDIS_OK; }
inline bool header_has_pdu_status(const Header& header) noexcept { return fastdis_header_has_pdu_status(&header) != 0; }
inline std::uint8_t header_pdu_status(const Header& header) noexcept { return fastdis_header_pdu_status(&header); }
inline std::uint8_t header_padding_octet(const Header& header) noexcept { return fastdis_header_padding_octet(&header); }
inline std::uint16_t header_legacy_padding(const Header& header) noexcept { return fastdis_header_legacy_padding(&header); }

inline EntityId make_entity_id(std::uint16_t site, std::uint16_t application, std::uint16_t entity) noexcept {
    return EntityId{site, application, entity};
}

enum class FilterKind : std::uint32_t {
    Versions = FASTDIS_FILTER_VERSIONS,
    PduTypes = FASTDIS_FILTER_PDU_TYPES,
    ProtocolFamilies = FASTDIS_FILTER_PROTOCOL_FAMILIES,
    ExerciseIds = FASTDIS_FILTER_EXERCISE_IDS,
    EntityForceIds = FASTDIS_FILTER_ENTITY_FORCE_IDS,
};

enum class EntityIdFilterMode : std::uint32_t {
    Disabled = FASTDIS_ENTITY_ID_FILTER_DISABLED,
    Allow = FASTDIS_ENTITY_ID_FILTER_ALLOW,
    Block = FASTDIS_ENTITY_ID_FILTER_BLOCK,
};

enum class Profile : std::uint32_t {
    HeaderCounting = FASTDIS_PROFILE_HEADER_COUNTING,
    EntityStateRouting = FASTDIS_PROFILE_ENTITY_STATE_ROUTING,
    EntityStatePose = FASTDIS_PROFILE_ENTITY_STATE_POSE,
    EntityStateFull = FASTDIS_PROFILE_ENTITY_STATE_FULL,
    EntityTransform = FASTDIS_PROFILE_ENTITY_TRANSFORM,
};

#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
class Error : public std::runtime_error {
public:
    Error(Status status, const char* operation)
        : std::runtime_error(make_message(status, operation)), status_(status), operation_(operation ? operation : "fastdis") {}

    Status status() const noexcept { return status_; }
    const std::string& operation() const noexcept { return operation_; }

private:
    static std::string make_message(Status status, const char* operation) {
        std::string message = operation ? operation : "fastdis";
        message += " failed: ";
        message += fastdis_status_string(status);
        message += " (";
        message += std::to_string(static_cast<int>(status));
        message += ")";
        return message;
    }

    Status status_;
    std::string operation_;
};
#endif

namespace detail {

inline void check(Status status, const char* operation) {
    if (status == FASTDIS_OK) {
        return;
    }
#if !defined(FASTDIS_CPP_NO_EXCEPTIONS)
    throw Error(status, operation);
#else
    (void)operation;
    assert(status == FASTDIS_OK);
#endif
}

inline const std::uint8_t* values_data(std::initializer_list<std::uint8_t> values) noexcept {
    return values.size() == 0 ? nullptr : values.begin();
}

inline const EntityId* ids_data(std::initializer_list<EntityId> ids) noexcept {
    return ids.size() == 0 ? nullptr : ids.begin();
}

} // namespace detail

inline Header parse_header(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Header header{};
    detail::check(fastdis_parse_header(static_cast<const std::uint8_t*>(data), size, flags, &header), "fastdis_parse_header");
    return header;
}

inline Status try_parse_header(const void* data, std::size_t size, Header& out_header, std::uint32_t flags = 0) noexcept {
    return fastdis_parse_header(static_cast<const std::uint8_t*>(data), size, flags, &out_header);
}

inline EntityTransform parse_entity_transform(const void* data, std::size_t size, std::uint32_t flags = 0) {
    EntityTransform transform{};
    detail::check(fastdis_parse_entity_transform(static_cast<const std::uint8_t*>(data), size, flags, &transform),
                  "fastdis_parse_entity_transform");
    return transform;
}

inline Status try_parse_entity_transform(const void* data,
                                         std::size_t size,
                                         EntityTransform& out_transform,
                                         std::uint32_t flags = 0) noexcept {
    return fastdis_parse_entity_transform(static_cast<const std::uint8_t*>(data), size, flags, &out_transform);
}

inline PacketView make_packet_view(const void* data, std::size_t size, void* user = nullptr) noexcept {
    return PacketView{static_cast<const std::uint8_t*>(data), size, user};
}

inline PacketView packet_view(const void* data, std::size_t size, void* user = nullptr) noexcept {
    return make_packet_view(data, size, user);
}

class PacketViews {
public:
    PacketViews() = default;
    explicit PacketViews(std::size_t reserve_count) { packets_.reserve(reserve_count); }

    PacketViews& reserve(std::size_t count) {
        packets_.reserve(count);
        return *this;
    }

    PacketViews& clear() noexcept {
        packets_.clear();
        return *this;
    }

    PacketViews& add(const void* data, std::size_t size, void* user = nullptr) {
        packets_.push_back(make_packet_view(data, size, user));
        return *this;
    }

    template <class ByteContainer>
    PacketViews& add_buffer(const ByteContainer& buffer, void* user = nullptr) {
        return add(buffer.data(), buffer.size(), user);
    }

    const PacketView* data() const noexcept { return packets_.data(); }
    PacketView* data() noexcept { return packets_.data(); }
    std::size_t size() const noexcept { return packets_.size(); }
    bool empty() const noexcept { return packets_.empty(); }

    const PacketView& operator[](std::size_t index) const noexcept { return packets_[index]; }
    PacketView& operator[](std::size_t index) noexcept { return packets_[index]; }

private:
    std::vector<PacketView> packets_;
};

class ScanConfig {
public:
    ScanConfig() { fastdis_scan_config_init(&config_); }
    explicit ScanConfig(Profile profile) : ScanConfig() { use_profile(profile); }

    static ScanConfig header_counting() { return ScanConfig(Profile::HeaderCounting); }
    static ScanConfig entity_state_pose() { return ScanConfig(Profile::EntityStatePose); }
    static ScanConfig entity_state_full() { return ScanConfig(Profile::EntityStateFull); }
    static ScanConfig entity_transform() { return ScanConfig(Profile::EntityTransform); }

    const fastdis_scan_config_t& native() const noexcept { return config_; }
    fastdis_scan_config_t& native() noexcept { return config_; }
    const fastdis_scan_config_t* native_ptr() const noexcept { return &config_; }
    fastdis_scan_config_t* native_ptr() noexcept { return &config_; }

    Status try_use_profile(Profile profile) noexcept {
        return fastdis_scan_config_use_profile(&config_, static_cast<std::uint32_t>(profile));
    }

    ScanConfig& use_profile(Profile profile) {
        detail::check(try_use_profile(profile), "fastdis_scan_config_use_profile");
        return *this;
    }

    ScanConfig& use_entity_transform_profile() { return use_profile(Profile::EntityTransform); }
    ScanConfig& use_entity_state_pose_profile() { return use_profile(Profile::EntityStatePose); }
    ScanConfig& use_entity_state_full_profile() { return use_profile(Profile::EntityStateFull); }
    ScanConfig& use_header_counting_profile() { return use_profile(Profile::HeaderCounting); }

    Status try_accept_all(FilterKind kind) noexcept {
        return fastdis_scan_config_filter_accept_all(&config_, static_cast<std::uint32_t>(kind));
    }

    ScanConfig& accept_all(FilterKind kind) {
        detail::check(try_accept_all(kind), "fastdis_scan_config_filter_accept_all");
        return *this;
    }

    Status try_clear(FilterKind kind) noexcept {
        return fastdis_scan_config_filter_clear(&config_, static_cast<std::uint32_t>(kind));
    }

    ScanConfig& clear(FilterKind kind) {
        detail::check(try_clear(kind), "fastdis_scan_config_filter_clear");
        return *this;
    }

    Status try_allow(FilterKind kind, std::uint8_t value) noexcept {
        return fastdis_scan_config_filter_allow(&config_, static_cast<std::uint32_t>(kind), value);
    }

    ScanConfig& allow(FilterKind kind, std::uint8_t value) {
        detail::check(try_allow(kind, value), "fastdis_scan_config_filter_allow");
        return *this;
    }

    Status try_only(FilterKind kind, const std::uint8_t* values, std::size_t count) noexcept {
        return fastdis_scan_config_filter_only(&config_, static_cast<std::uint32_t>(kind), values, count);
    }

    Status try_only(FilterKind kind, std::initializer_list<std::uint8_t> values) noexcept {
        return try_only(kind, detail::values_data(values), values.size());
    }

    ScanConfig& only(FilterKind kind, const std::uint8_t* values, std::size_t count) {
        detail::check(try_only(kind, values, count), "fastdis_scan_config_filter_only");
        return *this;
    }

    ScanConfig& only(FilterKind kind, std::initializer_list<std::uint8_t> values) {
        return only(kind, detail::values_data(values), values.size());
    }

    ScanConfig& only_versions(std::initializer_list<std::uint8_t> values) { return only(FilterKind::Versions, values); }
    ScanConfig& only_pdu_types(std::initializer_list<std::uint8_t> values) { return only(FilterKind::PduTypes, values); }
    ScanConfig& only_protocol_families(std::initializer_list<std::uint8_t> values) { return only(FilterKind::ProtocolFamilies, values); }
    ScanConfig& only_exercise_ids(std::initializer_list<std::uint8_t> values) { return only(FilterKind::ExerciseIds, values); }
    ScanConfig& only_entity_force_ids(std::initializer_list<std::uint8_t> values) { return only(FilterKind::EntityForceIds, values); }

    Status try_sample(std::uint32_t every, std::uint32_t offset = 0) noexcept {
        return fastdis_scan_config_set_sample(&config_, every, offset);
    }

    ScanConfig& sample(std::uint32_t every, std::uint32_t offset = 0) {
        detail::check(try_sample(every, offset), "fastdis_scan_config_set_sample");
        return *this;
    }

    Status try_entity_state_fields(std::uint64_t mask) noexcept {
        return fastdis_scan_config_set_entity_state_fields(&config_, mask);
    }

    ScanConfig& entity_state_fields(std::uint64_t mask) {
        detail::check(try_entity_state_fields(mask), "fastdis_scan_config_set_entity_state_fields");
        return *this;
    }

    bool contains(FilterKind kind, std::uint8_t value) const noexcept {
        return fastdis_scan_config_filter_contains(&config_, static_cast<std::uint32_t>(kind), value) != 0;
    }

private:
    fastdis_scan_config_t config_{};
};

class EntityStateBatch {
public:
    explicit EntityStateBatch(std::size_t capacity = 0) : storage_(capacity) { reset_for_write(); }

    void resize_capacity(std::size_t capacity) {
        storage_.resize(capacity);
        reset_for_write();
    }

    void reset_for_write() noexcept {
        batch_.entities = storage_.empty() ? nullptr : storage_.data();
        batch_.capacity = storage_.size();
        batch_.count = 0;
        batch_.dropped = 0;
    }

    fastdis_entity_state_batch_t* native_for_write() noexcept {
        reset_for_write();
        return &batch_;
    }

    const EntityStatePrefix* data() const noexcept { return storage_.data(); }
    const EntityStatePrefix* begin() const noexcept { return storage_.data(); }
    const EntityStatePrefix* end() const noexcept { return storage_.data() + batch_.count; }
    const EntityStatePrefix& operator[](std::size_t index) const noexcept { return storage_[index]; }

    std::size_t size() const noexcept { return batch_.count; }
    std::size_t capacity() const noexcept { return storage_.size(); }
    std::size_t dropped() const noexcept { return batch_.dropped; }
    bool empty() const noexcept { return batch_.count == 0; }

private:
    std::vector<EntityStatePrefix> storage_;
    fastdis_entity_state_batch_t batch_{};
};

class TransformBatch {
public:
    explicit TransformBatch(std::size_t capacity = 0) : storage_(capacity) { reset_for_write(); }

    void resize_capacity(std::size_t capacity) {
        storage_.resize(capacity);
        reset_for_write();
    }

    void reset_for_write() noexcept {
        batch_.transforms = storage_.empty() ? nullptr : storage_.data();
        batch_.capacity = storage_.size();
        batch_.count = 0;
        batch_.dropped = 0;
    }

    fastdis_entity_transform_batch_t* native_for_write() noexcept {
        reset_for_write();
        return &batch_;
    }

    const EntityTransform* data() const noexcept { return storage_.data(); }
    const EntityTransform* begin() const noexcept { return storage_.data(); }
    const EntityTransform* end() const noexcept { return storage_.data() + batch_.count; }
    const EntityTransform& operator[](std::size_t index) const noexcept { return storage_[index]; }

    std::size_t size() const noexcept { return batch_.count; }
    std::size_t capacity() const noexcept { return storage_.size(); }
    std::size_t dropped() const noexcept { return batch_.dropped; }
    bool empty() const noexcept { return batch_.count == 0; }

private:
    std::vector<EntityTransform> storage_;
    fastdis_entity_transform_batch_t batch_{};
};

class SnapshotBatch {
public:
    explicit SnapshotBatch(std::size_t capacity = 0) : storage_(capacity) { reset_for_write(); }

    void resize_capacity(std::size_t capacity) {
        storage_.resize(capacity);
        reset_for_write();
    }

    void reset_for_write() noexcept {
        batch_.snapshots = storage_.empty() ? nullptr : storage_.data();
        batch_.capacity = storage_.size();
        batch_.count = 0;
        batch_.dropped = 0;
    }

    fastdis_entity_snapshot_batch_t* native_for_write() noexcept {
        reset_for_write();
        return &batch_;
    }

    const EntitySnapshot* data() const noexcept { return storage_.data(); }
    const EntitySnapshot* begin() const noexcept { return storage_.data(); }
    const EntitySnapshot* end() const noexcept { return storage_.data() + batch_.count; }
    const EntitySnapshot& operator[](std::size_t index) const noexcept { return storage_[index]; }

    std::size_t size() const noexcept { return batch_.count; }
    std::size_t capacity() const noexcept { return storage_.size(); }
    std::size_t dropped() const noexcept { return batch_.dropped; }
    bool empty() const noexcept { return batch_.count == 0; }

private:
    std::vector<EntitySnapshot> storage_;
    fastdis_entity_snapshot_batch_t batch_{};
};

class Scanner {
public:
    Scanner() : Scanner(ScanConfig{}) {}

    explicit Scanner(const ScanConfig& config)
        : handle_(fastdis_scanner_create(config.native_ptr())) {
        if (!handle_) {
            detail::check(FASTDIS_ERR_OUT_OF_MEMORY, "fastdis_scanner_create");
        }
    }

    ~Scanner() { reset(); }

    Scanner(const Scanner&) = delete;
    Scanner& operator=(const Scanner&) = delete;

    Scanner(Scanner&& other) noexcept : handle_(other.handle_) { other.handle_ = nullptr; }

    Scanner& operator=(Scanner&& other) noexcept {
        if (this != &other) {
            reset();
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

    explicit operator bool() const noexcept { return handle_ != nullptr; }
    fastdis_scanner_t* native() noexcept { return handle_; }
    const fastdis_scanner_t* native() const noexcept { return handle_; }

    fastdis_scanner_t* release() noexcept {
        fastdis_scanner_t* tmp = handle_;
        handle_ = nullptr;
        return tmp;
    }

    void reset(fastdis_scanner_t* handle = nullptr) noexcept {
        if (handle_) {
            fastdis_scanner_destroy(handle_);
        }
        handle_ = handle;
    }

    Status try_set_config(const ScanConfig& config) noexcept {
        return fastdis_scanner_set_config(handle_, config.native_ptr());
    }

    Scanner& set_config(const ScanConfig& config) {
        detail::check(try_set_config(config), "fastdis_scanner_set_config");
        return *this;
    }

    ScanConfig config() const {
        ScanConfig out;
        detail::check(fastdis_scanner_get_config(handle_, out.native_ptr()), "fastdis_scanner_get_config");
        return out;
    }

    Scanner& use_profile(Profile profile) {
        detail::check(fastdis_scanner_use_profile(handle_, static_cast<std::uint32_t>(profile)), "fastdis_scanner_use_profile");
        return *this;
    }

    Scanner& use_entity_transform_profile() { return use_profile(Profile::EntityTransform); }
    Scanner& use_entity_state_pose_profile() { return use_profile(Profile::EntityStatePose); }
    Scanner& use_entity_state_full_profile() { return use_profile(Profile::EntityStateFull); }
    Scanner& use_header_counting_profile() { return use_profile(Profile::HeaderCounting); }

    Scanner& only(FilterKind kind, std::initializer_list<std::uint8_t> values) {
        detail::check(fastdis_scanner_filter_only(handle_, static_cast<std::uint32_t>(kind), detail::values_data(values), values.size()),
                      "fastdis_scanner_filter_only");
        return *this;
    }

    Scanner& only_versions(std::initializer_list<std::uint8_t> values) { return only(FilterKind::Versions, values); }
    Scanner& only_pdu_types(std::initializer_list<std::uint8_t> values) { return only(FilterKind::PduTypes, values); }
    Scanner& only_protocol_families(std::initializer_list<std::uint8_t> values) { return only(FilterKind::ProtocolFamilies, values); }
    Scanner& only_exercise_ids(std::initializer_list<std::uint8_t> values) { return only(FilterKind::ExerciseIds, values); }
    Scanner& only_entity_force_ids(std::initializer_list<std::uint8_t> values) { return only(FilterKind::EntityForceIds, values); }

    Scanner& allow(FilterKind kind, std::uint8_t value) {
        detail::check(fastdis_scanner_filter_allow(handle_, static_cast<std::uint32_t>(kind), value), "fastdis_scanner_filter_allow");
        return *this;
    }

    Scanner& clear(FilterKind kind) {
        detail::check(fastdis_scanner_filter_clear(handle_, static_cast<std::uint32_t>(kind)), "fastdis_scanner_filter_clear");
        return *this;
    }

    Scanner& accept_all(FilterKind kind) {
        detail::check(fastdis_scanner_filter_accept_all(handle_, static_cast<std::uint32_t>(kind)), "fastdis_scanner_filter_accept_all");
        return *this;
    }

    bool contains(FilterKind kind, std::uint8_t value) const noexcept {
        return fastdis_scanner_filter_contains(handle_, static_cast<std::uint32_t>(kind), value) != 0;
    }

    Scanner& sample(std::uint32_t every, std::uint32_t offset = 0) {
        detail::check(fastdis_scanner_set_sample(handle_, every, offset), "fastdis_scanner_set_sample");
        return *this;
    }

    Scanner& entity_state_fields(std::uint64_t field_mask) {
        detail::check(fastdis_scanner_set_entity_state_fields(handle_, field_mask), "fastdis_scanner_set_entity_state_fields");
        return *this;
    }

    Scanner& entity_id_filter_mode(EntityIdFilterMode mode) {
        detail::check(fastdis_scanner_set_entity_id_filter_mode(handle_, static_cast<std::uint32_t>(mode)),
                      "fastdis_scanner_set_entity_id_filter_mode");
        return *this;
    }

    EntityIdFilterMode entity_id_filter_mode() const noexcept {
        return static_cast<EntityIdFilterMode>(fastdis_scanner_get_entity_id_filter_mode(handle_));
    }

    Scanner& clear_entity_ids() {
        detail::check(fastdis_scanner_clear_entity_ids(handle_), "fastdis_scanner_clear_entity_ids");
        return *this;
    }

    Scanner& add_entity_id(EntityId id) {
        detail::check(fastdis_scanner_add_entity_id(handle_, id.site, id.application, id.entity), "fastdis_scanner_add_entity_id");
        return *this;
    }

    Scanner& add_entity_id(std::uint16_t site, std::uint16_t application, std::uint16_t entity) {
        return add_entity_id(make_entity_id(site, application, entity));
    }

    Scanner& add_entity_ids(std::initializer_list<EntityId> ids) {
        detail::check(fastdis_scanner_add_entity_ids(handle_, detail::ids_data(ids), ids.size()), "fastdis_scanner_add_entity_ids");
        return *this;
    }

    Scanner& set_entity_ids(EntityIdFilterMode mode, const EntityId* ids, std::size_t count) {
        detail::check(fastdis_scanner_set_entity_ids(handle_, static_cast<std::uint32_t>(mode), ids, count),
                      "fastdis_scanner_set_entity_ids");
        return *this;
    }

    Scanner& set_entity_ids(EntityIdFilterMode mode, std::initializer_list<EntityId> ids) {
        return set_entity_ids(mode, detail::ids_data(ids), ids.size());
    }

    Scanner& allow_entity_ids(std::initializer_list<EntityId> ids) { return set_entity_ids(EntityIdFilterMode::Allow, ids); }
    Scanner& block_entity_ids(std::initializer_list<EntityId> ids) { return set_entity_ids(EntityIdFilterMode::Block, ids); }

    Scanner& remove_entity_id(EntityId id) {
        detail::check(fastdis_scanner_remove_entity_id(handle_, id.site, id.application, id.entity), "fastdis_scanner_remove_entity_id");
        return *this;
    }

    bool contains_entity_id(EntityId id) const noexcept {
        return fastdis_scanner_contains_entity_id(handle_, id.site, id.application, id.entity) != 0;
    }

    std::size_t entity_id_count() const noexcept { return fastdis_scanner_entity_id_count(handle_); }

    Status try_scan_entity_states(const PacketView* packets, std::size_t count, EntityStateBatch& batch, ScanStats* stats = nullptr) noexcept {
        return fastdis_scanner_scan_entity_state_to_batch(handle_, packets, count, batch.native_for_write(), stats);
    }

    ScanStats scan_entity_states(const PacketView* packets, std::size_t count, EntityStateBatch& batch) {
        ScanStats stats{};
        fastdis_scan_stats_init(&stats);
        detail::check(try_scan_entity_states(packets, count, batch, &stats), "fastdis_scanner_scan_entity_state_to_batch");
        return stats;
    }

    ScanStats scan_entity_states(const PacketViews& packets, EntityStateBatch& batch) {
        return scan_entity_states(packets.data(), packets.size(), batch);
    }

    Status try_scan_transforms(const PacketView* packets, std::size_t count, TransformBatch& batch, ScanStats* stats = nullptr) noexcept {
        return fastdis_scanner_scan_entity_transforms_to_batch(handle_, packets, count, batch.native_for_write(), stats);
    }

    ScanStats scan_transforms(const PacketView* packets, std::size_t count, TransformBatch& batch) {
        ScanStats stats{};
        fastdis_scan_stats_init(&stats);
        detail::check(try_scan_transforms(packets, count, batch, &stats), "fastdis_scanner_scan_entity_transforms_to_batch");
        return stats;
    }

    ScanStats scan_transforms(const PacketViews& packets, TransformBatch& batch) {
        return scan_transforms(packets.data(), packets.size(), batch);
    }

private:
    fastdis_scanner_t* handle_ = nullptr;
};

class SnapshotView {
public:
    SnapshotView() = default;
    explicit SnapshotView(const fastdis_entity_snapshot_view_t& view) : view_(view) {}

    const EntitySnapshot* data() const noexcept { return view_.snapshots; }
    const EntitySnapshot* begin() const noexcept { return view_.snapshots; }
    const EntitySnapshot* end() const noexcept { return view_.snapshots ? view_.snapshots + view_.count : nullptr; }
    const EntitySnapshot& operator[](std::size_t index) const noexcept { return view_.snapshots[index]; }

    std::size_t size() const noexcept { return view_.count; }
    std::size_t dropped() const noexcept { return view_.dropped; }
    std::uint64_t generation() const noexcept { return view_.generation; }
    std::uint32_t slot() const noexcept { return view_.slot; }
    bool empty() const noexcept { return view_.count == 0; }
    explicit operator bool() const noexcept { return view_.snapshots != nullptr || view_.generation != 0; }

    const fastdis_entity_snapshot_view_t& native() const noexcept { return view_; }

protected:
    fastdis_entity_snapshot_view_t view_{};
};

class ScopedSnapshotView : public SnapshotView {
public:
    ScopedSnapshotView() = default;
    ScopedSnapshotView(fastdis_entity_snapshot_buffer_t* buffer, const fastdis_entity_snapshot_view_t& view)
        : SnapshotView(view), buffer_(buffer) {}

    ~ScopedSnapshotView() { release(); }

    ScopedSnapshotView(const ScopedSnapshotView&) = delete;
    ScopedSnapshotView& operator=(const ScopedSnapshotView&) = delete;

    ScopedSnapshotView(ScopedSnapshotView&& other) noexcept
        : SnapshotView(other.view_), buffer_(other.buffer_) {
        other.buffer_ = nullptr;
        other.view_ = fastdis_entity_snapshot_view_t{};
    }

    ScopedSnapshotView& operator=(ScopedSnapshotView&& other) noexcept {
        if (this != &other) {
            release();
            view_ = other.view_;
            buffer_ = other.buffer_;
            other.buffer_ = nullptr;
            other.view_ = fastdis_entity_snapshot_view_t{};
        }
        return *this;
    }

    Status release_status() noexcept {
        if (!buffer_) {
            return FASTDIS_OK;
        }
        Status status = fastdis_entity_snapshot_buffer_release(buffer_, &view_);
        buffer_ = nullptr;
        view_ = fastdis_entity_snapshot_view_t{};
        return status;
    }

    void release() noexcept { (void)release_status(); }
    bool owns_release() const noexcept { return buffer_ != nullptr; }

private:
    fastdis_entity_snapshot_buffer_t* buffer_ = nullptr;
};

class EntityTable {
public:
    explicit EntityTable(std::size_t reserve = 0)
        : handle_(fastdis_entity_table_create(reserve)) {
        if (!handle_) {
            detail::check(FASTDIS_ERR_OUT_OF_MEMORY, "fastdis_entity_table_create");
        }
    }

    ~EntityTable() { reset(); }

    EntityTable(const EntityTable&) = delete;
    EntityTable& operator=(const EntityTable&) = delete;

    EntityTable(EntityTable&& other) noexcept : handle_(other.handle_) { other.handle_ = nullptr; }

    EntityTable& operator=(EntityTable&& other) noexcept {
        if (this != &other) {
            reset();
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

    explicit operator bool() const noexcept { return handle_ != nullptr; }
    fastdis_entity_table_t* native() noexcept { return handle_; }
    const fastdis_entity_table_t* native() const noexcept { return handle_; }

    fastdis_entity_table_t* release() noexcept {
        fastdis_entity_table_t* tmp = handle_;
        handle_ = nullptr;
        return tmp;
    }

    void reset(fastdis_entity_table_t* handle = nullptr) noexcept {
        if (handle_) {
            fastdis_entity_table_destroy(handle_);
        }
        handle_ = handle;
    }

    Status try_clear() noexcept { return fastdis_entity_table_clear(handle_); }
    void clear() { detail::check(try_clear(), "fastdis_entity_table_clear"); }
    std::size_t size() const noexcept { return fastdis_entity_table_size(handle_); }
    std::uint64_t tick() const noexcept { return fastdis_entity_table_tick(handle_); }

    Status try_advance_tick(std::uint64_t delta = 1) noexcept { return fastdis_entity_table_advance_tick(handle_, delta); }
    EntityTable& advance_tick(std::uint64_t delta = 1) {
        detail::check(try_advance_tick(delta), "fastdis_entity_table_advance_tick");
        return *this;
    }

    EntityTable& mark_all_clean() {
        detail::check(fastdis_entity_table_mark_all_clean(handle_), "fastdis_entity_table_mark_all_clean");
        return *this;
    }

    Status try_update_transform(const EntityTransform& transform, EntitySnapshot* out_snapshot = nullptr) noexcept {
        return fastdis_entity_table_update_transform(handle_, &transform, out_snapshot);
    }

    EntitySnapshot update_transform(const EntityTransform& transform) {
        EntitySnapshot snapshot{};
        detail::check(try_update_transform(transform, &snapshot), "fastdis_entity_table_update_transform");
        return snapshot;
    }

    Status try_ingest(Scanner& scanner,
                      const PacketView* packets,
                      std::size_t count,
                      bool advance_tick = true,
                      EntityTableUpdateStats* out_stats = nullptr) noexcept {
        return fastdis_entity_table_ingest_packets(handle_, scanner.native(), packets, count, advance_tick ? 1u : 0u, out_stats);
    }

    EntityTableUpdateStats ingest(Scanner& scanner,
                                  const PacketView* packets,
                                  std::size_t count,
                                  bool advance_tick = true) {
        EntityTableUpdateStats stats{};
        fastdis_entity_table_update_stats_init(&stats);
        detail::check(try_ingest(scanner, packets, count, advance_tick, &stats), "fastdis_entity_table_ingest_packets");
        return stats;
    }

    EntityTableUpdateStats ingest(Scanner& scanner, const PacketViews& packets, bool advance_tick = true) {
        return ingest(scanner, packets.data(), packets.size(), advance_tick);
    }

    Status try_get(EntityId id, EntitySnapshot& out_snapshot) const noexcept {
        return fastdis_entity_table_get(handle_, id.site, id.application, id.entity, &out_snapshot);
    }

    EntitySnapshot get(EntityId id) const {
        EntitySnapshot snapshot{};
        detail::check(try_get(id, snapshot), "fastdis_entity_table_get");
        return snapshot;
    }

    Status try_snapshot_all(SnapshotBatch& batch) const noexcept {
        return fastdis_entity_table_snapshot_all(handle_, batch.native_for_write());
    }

    SnapshotBatch snapshot_all(std::size_t capacity) const {
        SnapshotBatch batch(capacity);
        detail::check(try_snapshot_all(batch), "fastdis_entity_table_snapshot_all");
        return batch;
    }

    Status try_snapshot_changed(SnapshotBatch& batch, bool clear_flags = true) noexcept {
        return fastdis_entity_table_snapshot_changed(handle_, batch.native_for_write(), clear_flags ? 1u : 0u);
    }

    SnapshotBatch snapshot_changed(std::size_t capacity, bool clear_flags = true) {
        SnapshotBatch batch(capacity);
        detail::check(try_snapshot_changed(batch, clear_flags), "fastdis_entity_table_snapshot_changed");
        return batch;
    }

    Status try_snapshot_stale(std::uint64_t stale_after_ticks, SnapshotBatch& batch) const noexcept {
        return fastdis_entity_table_snapshot_stale(handle_, stale_after_ticks, batch.native_for_write());
    }

    SnapshotBatch snapshot_stale(std::uint64_t stale_after_ticks, std::size_t capacity) const {
        SnapshotBatch batch(capacity);
        detail::check(try_snapshot_stale(stale_after_ticks, batch), "fastdis_entity_table_snapshot_stale");
        return batch;
    }

    Status try_evict_stale(std::uint64_t stale_after_ticks, SnapshotBatch& batch) noexcept {
        return fastdis_entity_table_evict_stale(handle_, stale_after_ticks, batch.native_for_write());
    }

    SnapshotBatch evict_stale(std::uint64_t stale_after_ticks, std::size_t capacity) {
        SnapshotBatch batch(capacity);
        detail::check(try_evict_stale(stale_after_ticks, batch), "fastdis_entity_table_evict_stale");
        return batch;
    }

private:
    fastdis_entity_table_t* handle_ = nullptr;
};

class SnapshotBuffer {
public:
    explicit SnapshotBuffer(std::size_t capacity)
        : handle_(fastdis_entity_snapshot_buffer_create(capacity)) {
        if (!handle_) {
            detail::check(FASTDIS_ERR_OUT_OF_MEMORY, "fastdis_entity_snapshot_buffer_create");
        }
    }

    ~SnapshotBuffer() { reset(); }

    SnapshotBuffer(const SnapshotBuffer&) = delete;
    SnapshotBuffer& operator=(const SnapshotBuffer&) = delete;

    SnapshotBuffer(SnapshotBuffer&& other) noexcept : handle_(other.handle_) { other.handle_ = nullptr; }

    SnapshotBuffer& operator=(SnapshotBuffer&& other) noexcept {
        if (this != &other) {
            reset();
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

    explicit operator bool() const noexcept { return handle_ != nullptr; }
    fastdis_entity_snapshot_buffer_t* native() noexcept { return handle_; }
    const fastdis_entity_snapshot_buffer_t* native() const noexcept { return handle_; }

    fastdis_entity_snapshot_buffer_t* release_handle() noexcept {
        fastdis_entity_snapshot_buffer_t* tmp = handle_;
        handle_ = nullptr;
        return tmp;
    }

    void reset(fastdis_entity_snapshot_buffer_t* handle = nullptr) noexcept {
        if (handle_) {
            fastdis_entity_snapshot_buffer_destroy(handle_);
        }
        handle_ = handle;
    }

    std::size_t capacity() const noexcept { return fastdis_entity_snapshot_buffer_capacity(handle_); }
    std::uint64_t generation() const noexcept { return fastdis_entity_snapshot_buffer_generation(handle_); }

    Status try_get_stats(SnapshotBufferStats& out_stats) const noexcept {
        return fastdis_entity_snapshot_buffer_get_stats(handle_, &out_stats);
    }

    SnapshotBufferStats stats() const {
        SnapshotBufferStats out{};
        fastdis_entity_snapshot_buffer_stats_init(&out);
        detail::check(try_get_stats(out), "fastdis_entity_snapshot_buffer_get_stats");
        return out;
    }

    Status try_reset_stats() noexcept { return fastdis_entity_snapshot_buffer_reset_stats(handle_); }

    SnapshotBuffer& reset_stats() {
        detail::check(try_reset_stats(), "fastdis_entity_snapshot_buffer_reset_stats");
        return *this;
    }

    Status try_resize(std::size_t capacity) noexcept { return fastdis_entity_snapshot_buffer_resize(handle_, capacity); }
    SnapshotBuffer& resize(std::size_t capacity) {
        detail::check(try_resize(capacity), "fastdis_entity_snapshot_buffer_resize");
        return *this;
    }

    Status try_publish_all(const EntityTable& table, SnapshotView* out_view = nullptr) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_snapshot_buffer_publish_all(handle_, table.native(), &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = SnapshotView(native_view);
        }
        return status;
    }

    SnapshotView publish_all(const EntityTable& table) {
        SnapshotView view;
        detail::check(try_publish_all(table, &view), "fastdis_entity_snapshot_buffer_publish_all");
        return view;
    }

    Status try_publish_changed(EntityTable& table, bool clear_flags = true, SnapshotView* out_view = nullptr) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_snapshot_buffer_publish_changed(handle_, table.native(), clear_flags ? 1u : 0u, &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = SnapshotView(native_view);
        }
        return status;
    }

    SnapshotView publish_changed(EntityTable& table, bool clear_flags = true) {
        SnapshotView view;
        detail::check(try_publish_changed(table, clear_flags, &view), "fastdis_entity_snapshot_buffer_publish_changed");
        return view;
    }

    Status try_publish_stale(const EntityTable& table,
                             std::uint64_t stale_after_ticks,
                             SnapshotView* out_view = nullptr) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_snapshot_buffer_publish_stale(handle_, table.native(), stale_after_ticks, &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = SnapshotView(native_view);
        }
        return status;
    }

    SnapshotView publish_stale(const EntityTable& table, std::uint64_t stale_after_ticks) {
        SnapshotView view;
        detail::check(try_publish_stale(table, stale_after_ticks, &view), "fastdis_entity_snapshot_buffer_publish_stale");
        return view;
    }

    Status try_publish_evict_stale(EntityTable& table,
                                   std::uint64_t stale_after_ticks,
                                   SnapshotView* out_view = nullptr) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_snapshot_buffer_publish_evict_stale(handle_, table.native(), stale_after_ticks, &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = SnapshotView(native_view);
        }
        return status;
    }

    SnapshotView publish_evict_stale(EntityTable& table, std::uint64_t stale_after_ticks) {
        SnapshotView view;
        detail::check(try_publish_evict_stale(table, stale_after_ticks, &view), "fastdis_entity_snapshot_buffer_publish_evict_stale");
        return view;
    }

    Status try_acquire_latest(ScopedSnapshotView* out_view) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_snapshot_buffer_acquire_latest(handle_, &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = ScopedSnapshotView(handle_, native_view);
        }
        return status;
    }

    ScopedSnapshotView acquire_latest() {
        ScopedSnapshotView view;
        detail::check(try_acquire_latest(&view), "fastdis_entity_snapshot_buffer_acquire_latest");
        return view;
    }

    ScopedSnapshotView publish_all_and_acquire(const EntityTable& table) {
        (void)publish_all(table);
        return acquire_latest();
    }

    ScopedSnapshotView publish_changed_and_acquire(EntityTable& table, bool clear_flags = true) {
        (void)publish_changed(table, clear_flags);
        return acquire_latest();
    }

    SnapshotBatch copy_latest(std::size_t capacity) {
        SnapshotBatch batch(capacity);
        detail::check(fastdis_entity_snapshot_buffer_copy_latest(handle_, batch.native_for_write()),
                      "fastdis_entity_snapshot_buffer_copy_latest");
        return batch;
    }

    Status try_ingest_and_publish_changed(EntityTable& table,
                                          Scanner& scanner,
                                          const PacketView* packets,
                                          std::size_t count,
                                          bool advance_tick = true,
                                          bool clear_flags = true,
                                          EntityTableUpdateStats* out_stats = nullptr,
                                          SnapshotView* out_view = nullptr) noexcept {
        fastdis_entity_snapshot_view_t native_view{};
        Status status = fastdis_entity_table_ingest_packets_publish_changed(table.native(),
                                                                            scanner.native(),
                                                                            packets,
                                                                            count,
                                                                            advance_tick ? 1u : 0u,
                                                                            clear_flags ? 1u : 0u,
                                                                            handle_,
                                                                            out_stats,
                                                                            &native_view);
        if (status == FASTDIS_OK && out_view) {
            *out_view = SnapshotView(native_view);
        }
        return status;
    }

    SnapshotView ingest_and_publish_changed(EntityTable& table,
                                            Scanner& scanner,
                                            const PacketView* packets,
                                            std::size_t count,
                                            bool advance_tick = true,
                                            bool clear_flags = true,
                                            EntityTableUpdateStats* out_stats = nullptr) {
        SnapshotView view;
        detail::check(try_ingest_and_publish_changed(table, scanner, packets, count, advance_tick, clear_flags, out_stats, &view),
                      "fastdis_entity_table_ingest_packets_publish_changed");
        return view;
    }

    SnapshotView ingest_and_publish_changed(EntityTable& table,
                                            Scanner& scanner,
                                            const PacketViews& packets,
                                            bool advance_tick = true,
                                            bool clear_flags = true,
                                            EntityTableUpdateStats* out_stats = nullptr) {
        return ingest_and_publish_changed(table, scanner, packets.data(), packets.size(), advance_tick, clear_flags, out_stats);
    }

    ScopedSnapshotView ingest_publish_changed_and_acquire(EntityTable& table,
                                                          Scanner& scanner,
                                                          const PacketView* packets,
                                                          std::size_t count,
                                                          bool advance_tick = true,
                                                          bool clear_flags = true,
                                                          EntityTableUpdateStats* out_stats = nullptr) {
        (void)ingest_and_publish_changed(table, scanner, packets, count, advance_tick, clear_flags, out_stats);
        return acquire_latest();
    }

    ScopedSnapshotView ingest_publish_changed_and_acquire(EntityTable& table,
                                                          Scanner& scanner,
                                                          const PacketViews& packets,
                                                          bool advance_tick = true,
                                                          bool clear_flags = true,
                                                          EntityTableUpdateStats* out_stats = nullptr) {
        return ingest_publish_changed_and_acquire(table, scanner, packets.data(), packets.size(), advance_tick, clear_flags, out_stats);
    }

private:
    fastdis_entity_snapshot_buffer_t* handle_ = nullptr;
};

} // namespace fastdis

#endif /* FASTDIS_FASTDIS_HPP */
