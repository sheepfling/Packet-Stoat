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

#if __cplusplus >= 202002L
#include <span>
#endif

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
using ClockTime = fastdis_clock_time_t;
using EventId = fastdis_event_id_t;
using BurstDescriptor = fastdis_burst_descriptor_t;
using EntityStatePrefix = fastdis_entity_state_prefix_t;
using EntityTransform = fastdis_entity_transform_t;
using SimulationManagementRequest = fastdis_simulation_management_request_t;
using StartResume = fastdis_start_resume_t;
using StopFreeze = fastdis_stop_freeze_t;
using Acknowledge = fastdis_acknowledge_t;
using SimulationManagementReliableRequest = fastdis_simulation_management_reliable_request_t;
using StartResumeReliable = fastdis_start_resume_reliable_t;
using StopFreezeReliable = fastdis_stop_freeze_reliable_t;
using DatumRecordSetView = fastdis_datum_record_set_view_t;
using CountedBytesView = fastdis_counted_bytes_view_t;
using ActionRequest = fastdis_action_request_t;
using ActionResponse = fastdis_action_response_t;
using DataQuery = fastdis_data_query_t;
using SetData = fastdis_set_data_t;
using EventReport = fastdis_event_report_t;
using Comment = fastdis_comment_t;
using ActionRequestReliable = fastdis_action_request_reliable_t;
using ActionResponseReliable = fastdis_action_response_reliable_t;
using DataQueryReliable = fastdis_data_query_reliable_t;
using SetDataReliable = fastdis_set_data_reliable_t;
using DataReliable = fastdis_data_reliable_t;
using EventReportReliable = fastdis_event_report_reliable_t;
using CommentReliable = fastdis_comment_reliable_t;
using RecordReliable = fastdis_record_reliable_t;
using SetRecordReliable = fastdis_set_record_reliable_t;
using RecordQueryReliable = fastdis_record_query_reliable_t;
using RadioEntityType = fastdis_radio_entity_type_t;
using ModulationType = fastdis_modulation_type_t;
using SystemId = fastdis_system_id_t;
using IffFundamentalData = fastdis_iff_fundamental_data_t;
using Designator = fastdis_designator_t;
using Transmitter = fastdis_transmitter_t;
using OtherPdu = fastdis_other_pdu_t;
using AggregateState = fastdis_aggregate_state_t;
using IsGroupOf = fastdis_is_group_of_t;
using TransferControlRequest = fastdis_transfer_control_request_t;
using TransferOwnership = fastdis_transfer_ownership_t;
using IsPartOf = fastdis_is_part_of_t;
using MinefieldState = fastdis_minefield_state_t;
using MinefieldQuery = fastdis_minefield_query_t;
using MinefieldData = fastdis_minefield_data_t;
using MinefieldResponseNack = fastdis_minefield_response_nack_t;
using EnvironmentObjectType = fastdis_environment_object_type_t;
using EnvironmentalProcess = fastdis_environmental_process_t;
using GriddedData = fastdis_gridded_data_t;
using PointObjectState = fastdis_point_object_state_t;
using LinearObjectState = fastdis_linear_object_state_t;
using ArealObjectState = fastdis_areal_object_state_t;
using Tspi = fastdis_tspi_t;
using LiveEntityAppearance = fastdis_live_entity_appearance_t;
using ArticulatedParts = fastdis_articulated_parts_t;
using LeFire = fastdis_le_fire_t;
using LeDetonation = fastdis_le_detonation_t;
using Signal = fastdis_signal_t;
using Receiver = fastdis_receiver_t;
using ElectronicEmissions = fastdis_electronic_emissions_t;
using IffAtcNavAidsLayer1 = fastdis_iff_atc_navaids_layer1_t;
using Iff = fastdis_iff_t;
using Ua = fastdis_ua_t;
using Sees = fastdis_sees_t;
using IntercomSignal = fastdis_intercom_signal_t;
using IntercomControl = fastdis_intercom_control_t;
using Attribute = fastdis_attribute_t;
using DirectedEnergyFire = fastdis_directed_energy_fire_t;
using EntityDamageStatus = fastdis_entity_damage_status_t;
using InformationOperationsAction = fastdis_information_operations_action_t;
using InformationOperationsReport = fastdis_information_operations_report_t;
using ServiceRequest = fastdis_service_request_t;
using ResupplyOffer = fastdis_resupply_offer_t;
using ResupplyReceived = fastdis_resupply_received_t;
using ResupplyCancel = fastdis_resupply_cancel_t;
using RepairComplete = fastdis_repair_complete_t;
using RepairResponse = fastdis_repair_response_t;
using Fire = fastdis_fire_t;
using Detonation = fastdis_detonation_t;
using Collision = fastdis_collision_t;
using CollisionElastic = fastdis_collision_elastic_t;
using EntitySnapshot = fastdis_entity_snapshot_t;
using SnapshotViewNative = fastdis_entity_snapshot_view_t;
using ScanStats = fastdis_scan_stats_t;
using EntityTableUpdateStats = fastdis_entity_table_update_stats_t;
using SnapshotBufferStats = fastdis_entity_snapshot_buffer_stats_t;
using PacketView = fastdis_packet_view_t;

inline constexpr std::uint32_t abi_version_constant = FASTDIS_ABI_VERSION;
inline constexpr std::uint32_t abi_epoch_constant = FASTDIS_ABI_EPOCH;
inline constexpr std::uint32_t abi_revision_constant = FASTDIS_ABI_REVISION;
inline constexpr std::uint32_t header_size = FASTDIS_HEADER_SIZE;
inline constexpr std::uint32_t protocol_version_dis6 = FASTDIS_PROTOCOL_VERSION_DIS6;
inline constexpr std::uint32_t protocol_version_dis7 = FASTDIS_PROTOCOL_VERSION_DIS7;
inline constexpr std::int16_t header_status_unavailable = FASTDIS_HEADER_STATUS_UNAVAILABLE;
inline constexpr std::uint32_t entity_information_family = FASTDIS_ENTITY_INFORMATION_FAMILY;
inline constexpr std::uint32_t other_pdu_type = FASTDIS_OTHER_PDU_TYPE;
inline constexpr std::uint32_t other_fixed_size = FASTDIS_OTHER_FIXED_SIZE;
inline constexpr std::uint32_t entity_state_pdu_type = FASTDIS_ENTITY_STATE_PDU_TYPE;
inline constexpr std::uint32_t entity_state_fixed_size = FASTDIS_ENTITY_STATE_FIXED_SIZE;
inline constexpr std::uint32_t fire_pdu_type = FASTDIS_FIRE_PDU_TYPE;
inline constexpr std::uint32_t fire_fixed_size = FASTDIS_FIRE_FIXED_SIZE;
inline constexpr std::uint32_t detonation_pdu_type = FASTDIS_DETONATION_PDU_TYPE;
inline constexpr std::uint32_t detonation_fixed_size = FASTDIS_DETONATION_FIXED_SIZE;
inline constexpr std::uint32_t collision_pdu_type = FASTDIS_COLLISION_PDU_TYPE;
inline constexpr std::uint32_t collision_fixed_size = FASTDIS_COLLISION_FIXED_SIZE;
inline constexpr std::uint32_t electronic_emissions_pdu_type = FASTDIS_ELECTRONIC_EMISSIONS_PDU_TYPE;
inline constexpr std::uint32_t electronic_emissions_fixed_size = FASTDIS_ELECTRONIC_EMISSIONS_FIXED_SIZE;
inline constexpr std::uint32_t designator_pdu_type = FASTDIS_DESIGNATOR_PDU_TYPE;
inline constexpr std::uint32_t designator_fixed_size = FASTDIS_DESIGNATOR_FIXED_SIZE;
inline constexpr std::uint32_t transmitter_pdu_type = FASTDIS_TRANSMITTER_PDU_TYPE;
inline constexpr std::uint32_t transmitter_fixed_size = FASTDIS_TRANSMITTER_FIXED_SIZE;
inline constexpr std::uint32_t signal_pdu_type = FASTDIS_SIGNAL_PDU_TYPE;
inline constexpr std::uint32_t signal_dis6_fixed_size = FASTDIS_SIGNAL_DIS6_FIXED_SIZE;
inline constexpr std::uint32_t signal_dis7_fixed_size = FASTDIS_SIGNAL_DIS7_FIXED_SIZE;
inline constexpr std::uint32_t receiver_pdu_type = FASTDIS_RECEIVER_PDU_TYPE;
inline constexpr std::uint32_t receiver_dis6_fixed_size = FASTDIS_RECEIVER_DIS6_FIXED_SIZE;
inline constexpr std::uint32_t receiver_dis7_fixed_size = FASTDIS_RECEIVER_DIS7_FIXED_SIZE;
inline constexpr std::uint32_t iff_atc_navaids_layer1_pdu_type = FASTDIS_IFF_ATC_NAVAIDS_LAYER1_PDU_TYPE;
inline constexpr std::uint32_t iff_atc_navaids_layer1_fixed_size = FASTDIS_IFF_ATC_NAVAIDS_LAYER1_FIXED_SIZE;
inline constexpr std::uint32_t iff_pdu_type = FASTDIS_IFF_PDU_TYPE;
inline constexpr std::uint32_t iff_fixed_size = FASTDIS_IFF_FIXED_SIZE;
inline constexpr std::uint32_t ua_pdu_type = FASTDIS_UA_PDU_TYPE;
inline constexpr std::uint32_t ua_fixed_size = FASTDIS_UA_FIXED_SIZE;
inline constexpr std::uint32_t sees_pdu_type = FASTDIS_SEES_PDU_TYPE;
inline constexpr std::uint32_t sees_fixed_size = FASTDIS_SEES_FIXED_SIZE;
inline constexpr std::uint32_t intercom_signal_pdu_type = FASTDIS_INTERCOM_SIGNAL_PDU_TYPE;
inline constexpr std::uint32_t intercom_signal_fixed_size = FASTDIS_INTERCOM_SIGNAL_FIXED_SIZE;
inline constexpr std::uint32_t intercom_control_pdu_type = FASTDIS_INTERCOM_CONTROL_PDU_TYPE;
inline constexpr std::uint32_t intercom_control_fixed_size = FASTDIS_INTERCOM_CONTROL_FIXED_SIZE;
inline constexpr std::uint32_t aggregate_state_pdu_type = FASTDIS_AGGREGATE_STATE_PDU_TYPE;
inline constexpr std::uint32_t aggregate_state_fixed_size = FASTDIS_AGGREGATE_STATE_FIXED_SIZE;
inline constexpr std::uint32_t is_group_of_pdu_type = FASTDIS_IS_GROUP_OF_PDU_TYPE;
inline constexpr std::uint32_t is_group_of_fixed_size = FASTDIS_IS_GROUP_OF_FIXED_SIZE;
inline constexpr std::uint32_t transfer_control_request_pdu_type = FASTDIS_TRANSFER_CONTROL_REQUEST_PDU_TYPE;
inline constexpr std::uint32_t transfer_control_request_fixed_size = FASTDIS_TRANSFER_CONTROL_REQUEST_FIXED_SIZE;
inline constexpr std::uint32_t transfer_ownership_pdu_type = FASTDIS_TRANSFER_OWNERSHIP_PDU_TYPE;
inline constexpr std::uint32_t transfer_ownership_fixed_size = FASTDIS_TRANSFER_OWNERSHIP_FIXED_SIZE;
inline constexpr std::uint32_t is_part_of_pdu_type = FASTDIS_IS_PART_OF_PDU_TYPE;
inline constexpr std::uint32_t is_part_of_fixed_size = FASTDIS_IS_PART_OF_FIXED_SIZE;
inline constexpr std::uint32_t minefield_state_pdu_type = FASTDIS_MINEFIELD_STATE_PDU_TYPE;
inline constexpr std::uint32_t minefield_state_fixed_size = FASTDIS_MINEFIELD_STATE_FIXED_SIZE;
inline constexpr std::uint32_t minefield_query_pdu_type = FASTDIS_MINEFIELD_QUERY_PDU_TYPE;
inline constexpr std::uint32_t minefield_query_fixed_size = FASTDIS_MINEFIELD_QUERY_FIXED_SIZE;
inline constexpr std::uint32_t minefield_data_pdu_type = FASTDIS_MINEFIELD_DATA_PDU_TYPE;
inline constexpr std::uint32_t minefield_data_fixed_size = FASTDIS_MINEFIELD_DATA_FIXED_SIZE;
inline constexpr std::uint32_t minefield_response_nack_pdu_type = FASTDIS_MINEFIELD_RESPONSE_NACK_PDU_TYPE;
inline constexpr std::uint32_t minefield_response_nack_fixed_size = FASTDIS_MINEFIELD_RESPONSE_NACK_FIXED_SIZE;
inline constexpr std::uint32_t environmental_process_pdu_type = FASTDIS_ENVIRONMENTAL_PROCESS_PDU_TYPE;
inline constexpr std::uint32_t environmental_process_fixed_size = FASTDIS_ENVIRONMENTAL_PROCESS_FIXED_SIZE;
inline constexpr std::uint32_t gridded_data_pdu_type = FASTDIS_GRIDDED_DATA_PDU_TYPE;
inline constexpr std::uint32_t gridded_data_fixed_size = FASTDIS_GRIDDED_DATA_FIXED_SIZE;
inline constexpr std::uint32_t point_object_state_pdu_type = FASTDIS_POINT_OBJECT_STATE_PDU_TYPE;
inline constexpr std::uint32_t point_object_state_dis6_fixed_size = FASTDIS_POINT_OBJECT_STATE_DIS6_FIXED_SIZE;
inline constexpr std::uint32_t point_object_state_dis7_fixed_size = FASTDIS_POINT_OBJECT_STATE_DIS7_FIXED_SIZE;
inline constexpr std::uint32_t linear_object_state_pdu_type = FASTDIS_LINEAR_OBJECT_STATE_PDU_TYPE;
inline constexpr std::uint32_t linear_object_state_dis6_fixed_size = FASTDIS_LINEAR_OBJECT_STATE_DIS6_FIXED_SIZE;
inline constexpr std::uint32_t linear_object_state_dis7_fixed_size = FASTDIS_LINEAR_OBJECT_STATE_DIS7_FIXED_SIZE;
inline constexpr std::uint32_t linear_segment_parameter_dis6_size = FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS6_SIZE;
inline constexpr std::uint32_t linear_segment_parameter_dis7_size = FASTDIS_LINEAR_SEGMENT_PARAMETER_DIS7_SIZE;
inline constexpr std::uint32_t areal_object_state_pdu_type = FASTDIS_AREAL_OBJECT_STATE_PDU_TYPE;
inline constexpr std::uint32_t areal_object_state_fixed_size = FASTDIS_AREAL_OBJECT_STATE_FIXED_SIZE;
inline constexpr std::uint32_t tspi_pdu_type = FASTDIS_TSPI_PDU_TYPE;
inline constexpr std::uint32_t tspi_fixed_size = FASTDIS_TSPI_FIXED_SIZE;
inline constexpr std::uint32_t appearance_pdu_type = FASTDIS_APPEARANCE_PDU_TYPE;
inline constexpr std::uint32_t appearance_fixed_size = FASTDIS_APPEARANCE_FIXED_SIZE;
inline constexpr std::uint32_t articulated_parts_pdu_type = FASTDIS_ARTICULATED_PARTS_PDU_TYPE;
inline constexpr std::uint32_t articulated_parts_fixed_size = FASTDIS_ARTICULATED_PARTS_FIXED_SIZE;
inline constexpr std::uint32_t le_fire_pdu_type = FASTDIS_LE_FIRE_PDU_TYPE;
inline constexpr std::uint32_t le_fire_fixed_size = FASTDIS_LE_FIRE_FIXED_SIZE;
inline constexpr std::uint32_t le_detonation_pdu_type = FASTDIS_LE_DETONATION_PDU_TYPE;
inline constexpr std::uint32_t le_detonation_fixed_size = FASTDIS_LE_DETONATION_FIXED_SIZE;
inline constexpr std::uint32_t service_request_pdu_type = FASTDIS_SERVICE_REQUEST_PDU_TYPE;
inline constexpr std::uint32_t service_request_fixed_size = FASTDIS_SERVICE_REQUEST_FIXED_SIZE;
inline constexpr std::uint32_t resupply_offer_pdu_type = FASTDIS_RESUPPLY_OFFER_PDU_TYPE;
inline constexpr std::uint32_t resupply_offer_fixed_size = FASTDIS_RESUPPLY_OFFER_FIXED_SIZE;
inline constexpr std::uint32_t resupply_received_pdu_type = FASTDIS_RESUPPLY_RECEIVED_PDU_TYPE;
inline constexpr std::uint32_t resupply_received_fixed_size = FASTDIS_RESUPPLY_RECEIVED_FIXED_SIZE;
inline constexpr std::uint32_t resupply_cancel_pdu_type = FASTDIS_RESUPPLY_CANCEL_PDU_TYPE;
inline constexpr std::uint32_t resupply_cancel_fixed_size = FASTDIS_RESUPPLY_CANCEL_FIXED_SIZE;
inline constexpr std::uint32_t repair_complete_pdu_type = FASTDIS_REPAIR_COMPLETE_PDU_TYPE;
inline constexpr std::uint32_t repair_complete_fixed_size = FASTDIS_REPAIR_COMPLETE_FIXED_SIZE;
inline constexpr std::uint32_t repair_response_pdu_type = FASTDIS_REPAIR_RESPONSE_PDU_TYPE;
inline constexpr std::uint32_t repair_response_fixed_size = FASTDIS_REPAIR_RESPONSE_FIXED_SIZE;
inline constexpr std::uint32_t create_entity_pdu_type = FASTDIS_CREATE_ENTITY_PDU_TYPE;
inline constexpr std::uint32_t create_entity_fixed_size = FASTDIS_CREATE_ENTITY_FIXED_SIZE;
inline constexpr std::uint32_t remove_entity_pdu_type = FASTDIS_REMOVE_ENTITY_PDU_TYPE;
inline constexpr std::uint32_t remove_entity_fixed_size = FASTDIS_REMOVE_ENTITY_FIXED_SIZE;
inline constexpr std::uint32_t start_resume_pdu_type = FASTDIS_START_RESUME_PDU_TYPE;
inline constexpr std::uint32_t start_resume_fixed_size = FASTDIS_START_RESUME_FIXED_SIZE;
inline constexpr std::uint32_t stop_freeze_pdu_type = FASTDIS_STOP_FREEZE_PDU_TYPE;
inline constexpr std::uint32_t stop_freeze_fixed_size = FASTDIS_STOP_FREEZE_FIXED_SIZE;
inline constexpr std::uint32_t acknowledge_pdu_type = FASTDIS_ACKNOWLEDGE_PDU_TYPE;
inline constexpr std::uint32_t acknowledge_fixed_size = FASTDIS_ACKNOWLEDGE_FIXED_SIZE;
inline constexpr std::uint32_t action_request_pdu_type = FASTDIS_ACTION_REQUEST_PDU_TYPE;
inline constexpr std::uint32_t action_request_fixed_size = FASTDIS_ACTION_REQUEST_FIXED_SIZE;
inline constexpr std::uint32_t action_response_pdu_type = FASTDIS_ACTION_RESPONSE_PDU_TYPE;
inline constexpr std::uint32_t action_response_fixed_size = FASTDIS_ACTION_RESPONSE_FIXED_SIZE;
inline constexpr std::uint32_t data_query_pdu_type = FASTDIS_DATA_QUERY_PDU_TYPE;
inline constexpr std::uint32_t data_query_fixed_size = FASTDIS_DATA_QUERY_FIXED_SIZE;
inline constexpr std::uint32_t set_data_pdu_type = FASTDIS_SET_DATA_PDU_TYPE;
inline constexpr std::uint32_t set_data_fixed_size = FASTDIS_SET_DATA_FIXED_SIZE;
inline constexpr std::uint32_t data_pdu_type = FASTDIS_DATA_PDU_TYPE;
inline constexpr std::uint32_t data_fixed_size = FASTDIS_DATA_FIXED_SIZE;
inline constexpr std::uint32_t event_report_pdu_type = FASTDIS_EVENT_REPORT_PDU_TYPE;
inline constexpr std::uint32_t event_report_fixed_size = FASTDIS_EVENT_REPORT_FIXED_SIZE;
inline constexpr std::uint32_t comment_pdu_type = FASTDIS_COMMENT_PDU_TYPE;
inline constexpr std::uint32_t comment_fixed_size = FASTDIS_COMMENT_FIXED_SIZE;
inline constexpr std::uint32_t create_entity_reliable_pdu_type = FASTDIS_CREATE_ENTITY_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t create_entity_reliable_fixed_size = FASTDIS_CREATE_ENTITY_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t remove_entity_reliable_pdu_type = FASTDIS_REMOVE_ENTITY_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t remove_entity_reliable_fixed_size = FASTDIS_REMOVE_ENTITY_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t start_resume_reliable_pdu_type = FASTDIS_START_RESUME_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t start_resume_reliable_fixed_size = FASTDIS_START_RESUME_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t stop_freeze_reliable_pdu_type = FASTDIS_STOP_FREEZE_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t stop_freeze_reliable_fixed_size = FASTDIS_STOP_FREEZE_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t acknowledge_reliable_pdu_type = FASTDIS_ACKNOWLEDGE_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t acknowledge_reliable_fixed_size = FASTDIS_ACKNOWLEDGE_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t action_request_reliable_pdu_type = FASTDIS_ACTION_REQUEST_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t action_request_reliable_fixed_size = FASTDIS_ACTION_REQUEST_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t action_response_reliable_pdu_type = FASTDIS_ACTION_RESPONSE_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t action_response_reliable_fixed_size = FASTDIS_ACTION_RESPONSE_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t data_query_reliable_pdu_type = FASTDIS_DATA_QUERY_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t data_query_reliable_fixed_size = FASTDIS_DATA_QUERY_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t set_data_reliable_pdu_type = FASTDIS_SET_DATA_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t set_data_reliable_fixed_size = FASTDIS_SET_DATA_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t data_reliable_pdu_type = FASTDIS_DATA_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t data_reliable_fixed_size = FASTDIS_DATA_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t event_report_reliable_pdu_type = FASTDIS_EVENT_REPORT_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t event_report_reliable_fixed_size = FASTDIS_EVENT_REPORT_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t comment_reliable_pdu_type = FASTDIS_COMMENT_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t comment_reliable_fixed_size = FASTDIS_COMMENT_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t record_reliable_pdu_type = FASTDIS_RECORD_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t record_reliable_fixed_size = FASTDIS_RECORD_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t set_record_reliable_pdu_type = FASTDIS_SET_RECORD_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t set_record_reliable_fixed_size = FASTDIS_SET_RECORD_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t record_query_reliable_pdu_type = FASTDIS_RECORD_QUERY_RELIABLE_PDU_TYPE;
inline constexpr std::uint32_t record_query_reliable_fixed_size = FASTDIS_RECORD_QUERY_RELIABLE_FIXED_SIZE;
inline constexpr std::uint32_t collision_elastic_pdu_type = FASTDIS_COLLISION_ELASTIC_PDU_TYPE;
inline constexpr std::uint32_t collision_elastic_fixed_size = FASTDIS_COLLISION_ELASTIC_FIXED_SIZE;
inline constexpr std::uint32_t entity_state_update_pdu_type = FASTDIS_ENTITY_STATE_UPDATE_PDU_TYPE;
inline constexpr std::uint32_t entity_state_update_fixed_size = FASTDIS_ENTITY_STATE_UPDATE_FIXED_SIZE;
inline constexpr std::uint32_t directed_energy_fire_pdu_type = FASTDIS_DIRECTED_ENERGY_FIRE_PDU_TYPE;
inline constexpr std::uint32_t directed_energy_fire_fixed_size = FASTDIS_DIRECTED_ENERGY_FIRE_FIXED_SIZE;
inline constexpr std::uint32_t entity_damage_status_pdu_type = FASTDIS_ENTITY_DAMAGE_STATUS_PDU_TYPE;
inline constexpr std::uint32_t entity_damage_status_fixed_size = FASTDIS_ENTITY_DAMAGE_STATUS_FIXED_SIZE;
inline constexpr std::uint32_t information_operations_action_pdu_type = FASTDIS_INFORMATION_OPERATIONS_ACTION_PDU_TYPE;
inline constexpr std::uint32_t information_operations_action_fixed_size = FASTDIS_INFORMATION_OPERATIONS_ACTION_FIXED_SIZE;
inline constexpr std::uint32_t information_operations_report_pdu_type = FASTDIS_INFORMATION_OPERATIONS_REPORT_PDU_TYPE;
inline constexpr std::uint32_t information_operations_report_fixed_size = FASTDIS_INFORMATION_OPERATIONS_REPORT_FIXED_SIZE;
inline constexpr std::uint32_t attribute_pdu_type = FASTDIS_ATTRIBUTE_PDU_TYPE;
inline constexpr std::uint32_t attribute_fixed_size = FASTDIS_ATTRIBUTE_FIXED_SIZE;

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
inline constexpr std::uint32_t entity_change_extrapolated = FASTDIS_ENTITY_CHANGE_EXTRAPOLATED;

inline constexpr std::uint8_t dr_other = FASTDIS_DR_OTHER;
inline constexpr std::uint8_t dr_static = FASTDIS_DR_STATIC;
inline constexpr std::uint8_t dr_fpw = FASTDIS_DR_FPW;
inline constexpr std::uint8_t dr_rpw = FASTDIS_DR_RPW;
inline constexpr std::uint8_t dr_rvw = FASTDIS_DR_RVW;
inline constexpr std::uint8_t dr_fvw = FASTDIS_DR_FVW;
inline constexpr std::uint8_t dr_fpb = FASTDIS_DR_FPB;
inline constexpr std::uint8_t dr_rpb = FASTDIS_DR_RPB;
inline constexpr std::uint8_t dr_rvb = FASTDIS_DR_RVB;
inline constexpr std::uint8_t dr_fvb = FASTDIS_DR_FVB;

inline const char* version_string() noexcept { return fastdis_version_string(); }
inline std::uint32_t abi_version() noexcept { return fastdis_abi_version(); }
inline std::uint32_t abi_epoch() noexcept { return fastdis_abi_epoch(); }
inline std::uint32_t abi_revision() noexcept { return fastdis_abi_revision(); }
inline bool abi_matches() noexcept { return fastdis_abi_version() == FASTDIS_ABI_VERSION; }
inline const char* status_string(Status status) noexcept { return fastdis_status_string(status); }
inline bool succeeded(Status status) noexcept { return status == FASTDIS_OK; }
inline bool failed(Status status) noexcept { return status != FASTDIS_OK; }
inline bool header_has_pdu_status(const Header& header) noexcept { return fastdis_header_has_pdu_status(&header) != 0; }
inline std::uint8_t header_pdu_status(const Header& header) noexcept { return fastdis_header_pdu_status(&header); }
inline std::uint8_t header_padding_octet(const Header& header) noexcept { return fastdis_header_padding_octet(&header); }
inline std::uint16_t header_legacy_padding(const Header& header) noexcept { return fastdis_header_legacy_padding(&header); }
inline const char* dead_reckoning_algorithm_name(std::uint8_t algorithm) noexcept {
    return fastdis_dead_reckoning_algorithm_name(algorithm);
}
inline bool dead_reckoning_algorithm_known(std::uint8_t algorithm) noexcept {
    return fastdis_dead_reckoning_algorithm_known(algorithm) != 0;
}

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

inline Fire parse_fire(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Fire fire{};
    detail::check(fastdis_parse_fire(static_cast<const std::uint8_t*>(data), size, flags, &fire),
                  "fastdis_parse_fire");
    return fire;
}

inline Status try_parse_fire(const void* data,
                             std::size_t size,
                             Fire& out_fire,
                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_fire(static_cast<const std::uint8_t*>(data), size, flags, &out_fire);
}

inline Detonation parse_detonation(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Detonation detonation{};
    detail::check(fastdis_parse_detonation(static_cast<const std::uint8_t*>(data), size, flags, &detonation),
                  "fastdis_parse_detonation");
    return detonation;
}

inline Status try_parse_detonation(const void* data,
                                   std::size_t size,
                                   Detonation& out_detonation,
                                   std::uint32_t flags = 0) noexcept {
    return fastdis_parse_detonation(static_cast<const std::uint8_t*>(data), size, flags, &out_detonation);
}

inline Collision parse_collision(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Collision collision{};
    detail::check(fastdis_parse_collision(static_cast<const std::uint8_t*>(data), size, flags, &collision),
                  "fastdis_parse_collision");
    return collision;
}

inline Status try_parse_collision(const void* data,
                                  std::size_t size,
                                  Collision& out_collision,
                                  std::uint32_t flags = 0) noexcept {
    return fastdis_parse_collision(static_cast<const std::uint8_t*>(data), size, flags, &out_collision);
}

inline CollisionElastic parse_collision_elastic(const void* data, std::size_t size, std::uint32_t flags = 0) {
    CollisionElastic collision{};
    detail::check(fastdis_parse_collision_elastic(static_cast<const std::uint8_t*>(data), size, flags, &collision),
                  "fastdis_parse_collision_elastic");
    return collision;
}

inline Status try_parse_collision_elastic(const void* data,
                                          std::size_t size,
                                          CollisionElastic& out_collision,
                                          std::uint32_t flags = 0) noexcept {
    return fastdis_parse_collision_elastic(static_cast<const std::uint8_t*>(data), size, flags, &out_collision);
}

inline DirectedEnergyFire parse_directed_energy_fire(const void* data, std::size_t size, std::uint32_t flags = 0) {
    DirectedEnergyFire value{};
    detail::check(fastdis_parse_directed_energy_fire(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_directed_energy_fire");
    return value;
}

inline Status try_parse_directed_energy_fire(const void* data,
                                             std::size_t size,
                                             DirectedEnergyFire& out_value,
                                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_directed_energy_fire(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline EntityDamageStatus parse_entity_damage_status(const void* data, std::size_t size, std::uint32_t flags = 0) {
    EntityDamageStatus value{};
    detail::check(fastdis_parse_entity_damage_status(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_entity_damage_status");
    return value;
}

inline Status try_parse_entity_damage_status(const void* data,
                                             std::size_t size,
                                             EntityDamageStatus& out_value,
                                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_entity_damage_status(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Designator parse_designator(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Designator value{};
    detail::check(fastdis_parse_designator(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_designator");
    return value;
}

inline Status try_parse_designator(const void* data,
                                   std::size_t size,
                                   Designator& out_value,
                                   std::uint32_t flags = 0) noexcept {
    return fastdis_parse_designator(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Transmitter parse_transmitter(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Transmitter value{};
    detail::check(fastdis_parse_transmitter(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_transmitter");
    return value;
}

inline Status try_parse_transmitter(const void* data,
                                    std::size_t size,
                                    Transmitter& out_value,
                                    std::uint32_t flags = 0) noexcept {
    return fastdis_parse_transmitter(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline OtherPdu parse_other_pdu(const void* data, std::size_t size, std::uint32_t flags = 0) {
    OtherPdu value{};
    detail::check(fastdis_parse_other_pdu(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_other_pdu");
    return value;
}

inline Status try_parse_other_pdu(const void* data,
                                  std::size_t size,
                                  OtherPdu& out_value,
                                  std::uint32_t flags = 0) noexcept {
    return fastdis_parse_other_pdu(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline AggregateState parse_aggregate_state(const void* data, std::size_t size, std::uint32_t flags = 0) {
    AggregateState value{};
    detail::check(fastdis_parse_aggregate_state(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_aggregate_state");
    return value;
}

inline Status try_parse_aggregate_state(const void* data,
                                        std::size_t size,
                                        AggregateState& out_value,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_aggregate_state(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline IsGroupOf parse_is_group_of(const void* data, std::size_t size, std::uint32_t flags = 0) {
    IsGroupOf value{};
    detail::check(fastdis_parse_is_group_of(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_is_group_of");
    return value;
}

inline Status try_parse_is_group_of(const void* data,
                                    std::size_t size,
                                    IsGroupOf& out_value,
                                    std::uint32_t flags = 0) noexcept {
    return fastdis_parse_is_group_of(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline TransferControlRequest parse_transfer_control_request(const void* data, std::size_t size, std::uint32_t flags = 0) {
    TransferControlRequest value{};
    detail::check(fastdis_parse_transfer_control_request(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_transfer_control_request");
    return value;
}

inline Status try_parse_transfer_control_request(const void* data,
                                                 std::size_t size,
                                                 TransferControlRequest& out_value,
                                                 std::uint32_t flags = 0) noexcept {
    return fastdis_parse_transfer_control_request(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline TransferOwnership parse_transfer_ownership(const void* data, std::size_t size, std::uint32_t flags = 0) {
    TransferOwnership value{};
    detail::check(fastdis_parse_transfer_ownership(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_transfer_ownership");
    return value;
}

inline Status try_parse_transfer_ownership(const void* data,
                                           std::size_t size,
                                           TransferOwnership& out_value,
                                           std::uint32_t flags = 0) noexcept {
    return fastdis_parse_transfer_ownership(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline IsPartOf parse_is_part_of(const void* data, std::size_t size, std::uint32_t flags = 0) {
    IsPartOf value{};
    detail::check(fastdis_parse_is_part_of(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_is_part_of");
    return value;
}

inline Status try_parse_is_part_of(const void* data,
                                   std::size_t size,
                                   IsPartOf& out_value,
                                   std::uint32_t flags = 0) noexcept {
    return fastdis_parse_is_part_of(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline MinefieldState parse_minefield_state(const void* data, std::size_t size, std::uint32_t flags = 0) {
    MinefieldState value{};
    detail::check(fastdis_parse_minefield_state(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_minefield_state");
    return value;
}

inline Status try_parse_minefield_state(const void* data,
                                        std::size_t size,
                                        MinefieldState& out_value,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_minefield_state(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline MinefieldQuery parse_minefield_query(const void* data, std::size_t size, std::uint32_t flags = 0) {
    MinefieldQuery value{};
    detail::check(fastdis_parse_minefield_query(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_minefield_query");
    return value;
}

inline Status try_parse_minefield_query(const void* data,
                                        std::size_t size,
                                        MinefieldQuery& out_value,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_minefield_query(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline MinefieldData parse_minefield_data(const void* data, std::size_t size, std::uint32_t flags = 0) {
    MinefieldData value{};
    detail::check(fastdis_parse_minefield_data(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_minefield_data");
    return value;
}

inline Status try_parse_minefield_data(const void* data,
                                       std::size_t size,
                                       MinefieldData& out_value,
                                       std::uint32_t flags = 0) noexcept {
    return fastdis_parse_minefield_data(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline MinefieldResponseNack parse_minefield_response_nack(const void* data, std::size_t size, std::uint32_t flags = 0) {
    MinefieldResponseNack value{};
    detail::check(fastdis_parse_minefield_response_nack(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_minefield_response_nack");
    return value;
}

inline Status try_parse_minefield_response_nack(const void* data,
                                                std::size_t size,
                                                MinefieldResponseNack& out_value,
                                                std::uint32_t flags = 0) noexcept {
    return fastdis_parse_minefield_response_nack(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline EnvironmentalProcess parse_environmental_process(const void* data, std::size_t size, std::uint32_t flags = 0) {
    EnvironmentalProcess value{};
    detail::check(fastdis_parse_environmental_process(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_environmental_process");
    return value;
}

inline Status try_parse_environmental_process(const void* data,
                                              std::size_t size,
                                              EnvironmentalProcess& out_value,
                                              std::uint32_t flags = 0) noexcept {
    return fastdis_parse_environmental_process(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline GriddedData parse_gridded_data(const void* data, std::size_t size, std::uint32_t flags = 0) {
    GriddedData value{};
    detail::check(fastdis_parse_gridded_data(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_gridded_data");
    return value;
}

inline Status try_parse_gridded_data(const void* data,
                                     std::size_t size,
                                     GriddedData& out_value,
                                     std::uint32_t flags = 0) noexcept {
    return fastdis_parse_gridded_data(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline PointObjectState parse_point_object_state(const void* data, std::size_t size, std::uint32_t flags = 0) {
    PointObjectState value{};
    detail::check(fastdis_parse_point_object_state(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_point_object_state");
    return value;
}

inline Status try_parse_point_object_state(const void* data,
                                           std::size_t size,
                                           PointObjectState& out_value,
                                           std::uint32_t flags = 0) noexcept {
    return fastdis_parse_point_object_state(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline LinearObjectState parse_linear_object_state(const void* data, std::size_t size, std::uint32_t flags = 0) {
    LinearObjectState value{};
    detail::check(fastdis_parse_linear_object_state(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_linear_object_state");
    return value;
}

inline Status try_parse_linear_object_state(const void* data,
                                            std::size_t size,
                                            LinearObjectState& out_value,
                                            std::uint32_t flags = 0) noexcept {
    return fastdis_parse_linear_object_state(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline ArealObjectState parse_areal_object_state(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ArealObjectState value{};
    detail::check(fastdis_parse_areal_object_state(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_areal_object_state");
    return value;
}

inline Status try_parse_areal_object_state(const void* data,
                                           std::size_t size,
                                           ArealObjectState& out_value,
                                           std::uint32_t flags = 0) noexcept {
    return fastdis_parse_areal_object_state(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Tspi parse_tspi(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Tspi value{};
    detail::check(fastdis_parse_tspi(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_tspi");
    return value;
}

inline Status try_parse_tspi(const void* data,
                             std::size_t size,
                             Tspi& out_value,
                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_tspi(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline LiveEntityAppearance parse_live_entity_appearance(const void* data, std::size_t size, std::uint32_t flags = 0) {
    LiveEntityAppearance value{};
    detail::check(fastdis_parse_live_entity_appearance(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_live_entity_appearance");
    return value;
}

inline Status try_parse_live_entity_appearance(const void* data,
                                               std::size_t size,
                                               LiveEntityAppearance& out_value,
                                               std::uint32_t flags = 0) noexcept {
    return fastdis_parse_live_entity_appearance(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline ArticulatedParts parse_articulated_parts(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ArticulatedParts value{};
    detail::check(fastdis_parse_articulated_parts(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_articulated_parts");
    return value;
}

inline Status try_parse_articulated_parts(const void* data,
                                          std::size_t size,
                                          ArticulatedParts& out_value,
                                          std::uint32_t flags = 0) noexcept {
    return fastdis_parse_articulated_parts(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline LeFire parse_le_fire(const void* data, std::size_t size, std::uint32_t flags = 0) {
    LeFire value{};
    detail::check(fastdis_parse_le_fire(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_le_fire");
    return value;
}

inline Status try_parse_le_fire(const void* data,
                                std::size_t size,
                                LeFire& out_value,
                                std::uint32_t flags = 0) noexcept {
    return fastdis_parse_le_fire(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline LeDetonation parse_le_detonation(const void* data, std::size_t size, std::uint32_t flags = 0) {
    LeDetonation value{};
    detail::check(fastdis_parse_le_detonation(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_le_detonation");
    return value;
}

inline Status try_parse_le_detonation(const void* data,
                                      std::size_t size,
                                      LeDetonation& out_value,
                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_le_detonation(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Signal parse_signal(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Signal value{};
    detail::check(fastdis_parse_signal(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_signal");
    return value;
}

inline Status try_parse_signal(const void* data,
                               std::size_t size,
                               Signal& out_value,
                               std::uint32_t flags = 0) noexcept {
    return fastdis_parse_signal(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Receiver parse_receiver(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Receiver value{};
    detail::check(fastdis_parse_receiver(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_receiver");
    return value;
}

inline Status try_parse_receiver(const void* data,
                                 std::size_t size,
                                 Receiver& out_value,
                                 std::uint32_t flags = 0) noexcept {
    return fastdis_parse_receiver(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline ElectronicEmissions parse_electronic_emissions(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ElectronicEmissions value{};
    detail::check(fastdis_parse_electronic_emissions(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_electronic_emissions");
    return value;
}

inline Status try_parse_electronic_emissions(const void* data,
                                             std::size_t size,
                                             ElectronicEmissions& out_value,
                                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_electronic_emissions(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline IffAtcNavAidsLayer1 parse_iff_atc_navaids_layer1(const void* data, std::size_t size, std::uint32_t flags = 0) {
    IffAtcNavAidsLayer1 value{};
    detail::check(fastdis_parse_iff_atc_navaids_layer1(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_iff_atc_navaids_layer1");
    return value;
}

inline Status try_parse_iff_atc_navaids_layer1(const void* data,
                                               std::size_t size,
                                               IffAtcNavAidsLayer1& out_value,
                                               std::uint32_t flags = 0) noexcept {
    return fastdis_parse_iff_atc_navaids_layer1(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Iff parse_iff(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Iff value{};
    detail::check(fastdis_parse_iff(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_iff");
    return value;
}

inline Status try_parse_iff(const void* data,
                            std::size_t size,
                            Iff& out_value,
                            std::uint32_t flags = 0) noexcept {
    return fastdis_parse_iff(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Ua parse_ua(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Ua value{};
    detail::check(fastdis_parse_ua(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_ua");
    return value;
}

inline Status try_parse_ua(const void* data,
                           std::size_t size,
                           Ua& out_value,
                           std::uint32_t flags = 0) noexcept {
    return fastdis_parse_ua(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Sees parse_sees(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Sees value{};
    detail::check(fastdis_parse_sees(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_sees");
    return value;
}

inline Status try_parse_sees(const void* data,
                             std::size_t size,
                             Sees& out_value,
                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_sees(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline IntercomSignal parse_intercom_signal(const void* data, std::size_t size, std::uint32_t flags = 0) {
    IntercomSignal value{};
    detail::check(fastdis_parse_intercom_signal(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_intercom_signal");
    return value;
}

inline Status try_parse_intercom_signal(const void* data,
                                        std::size_t size,
                                        IntercomSignal& out_value,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_intercom_signal(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline IntercomControl parse_intercom_control(const void* data, std::size_t size, std::uint32_t flags = 0) {
    IntercomControl value{};
    detail::check(fastdis_parse_intercom_control(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_intercom_control");
    return value;
}

inline Status try_parse_intercom_control(const void* data,
                                         std::size_t size,
                                         IntercomControl& out_value,
                                         std::uint32_t flags = 0) noexcept {
    return fastdis_parse_intercom_control(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline Attribute parse_attribute(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Attribute value{};
    detail::check(fastdis_parse_attribute(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_attribute");
    return value;
}

inline Status try_parse_attribute(const void* data,
                                  std::size_t size,
                                  Attribute& out_value,
                                  std::uint32_t flags = 0) noexcept {
    return fastdis_parse_attribute(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline InformationOperationsAction parse_information_operations_action(const void* data, std::size_t size, std::uint32_t flags = 0) {
    InformationOperationsAction value{};
    detail::check(fastdis_parse_information_operations_action(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_information_operations_action");
    return value;
}

inline Status try_parse_information_operations_action(const void* data,
                                                      std::size_t size,
                                                      InformationOperationsAction& out_value,
                                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_information_operations_action(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline InformationOperationsReport parse_information_operations_report(const void* data, std::size_t size, std::uint32_t flags = 0) {
    InformationOperationsReport value{};
    detail::check(fastdis_parse_information_operations_report(static_cast<const std::uint8_t*>(data), size, flags, &value),
                  "fastdis_parse_information_operations_report");
    return value;
}

inline Status try_parse_information_operations_report(const void* data,
                                                      std::size_t size,
                                                      InformationOperationsReport& out_value,
                                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_information_operations_report(static_cast<const std::uint8_t*>(data), size, flags, &out_value);
}

inline ServiceRequest parse_service_request(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ServiceRequest request{};
    detail::check(fastdis_parse_service_request(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_service_request");
    return request;
}

inline Status try_parse_service_request(const void* data,
                                        std::size_t size,
                                        ServiceRequest& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_service_request(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ResupplyOffer parse_resupply_offer(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ResupplyOffer request{};
    detail::check(fastdis_parse_resupply_offer(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_resupply_offer");
    return request;
}

inline Status try_parse_resupply_offer(const void* data,
                                       std::size_t size,
                                       ResupplyOffer& out_request,
                                       std::uint32_t flags = 0) noexcept {
    return fastdis_parse_resupply_offer(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ResupplyReceived parse_resupply_received(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ResupplyReceived request{};
    detail::check(fastdis_parse_resupply_received(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_resupply_received");
    return request;
}

inline Status try_parse_resupply_received(const void* data,
                                          std::size_t size,
                                          ResupplyReceived& out_request,
                                          std::uint32_t flags = 0) noexcept {
    return fastdis_parse_resupply_received(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ResupplyCancel parse_resupply_cancel(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ResupplyCancel request{};
    detail::check(fastdis_parse_resupply_cancel(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_resupply_cancel");
    return request;
}

inline Status try_parse_resupply_cancel(const void* data,
                                        std::size_t size,
                                        ResupplyCancel& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_resupply_cancel(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline RepairComplete parse_repair_complete(const void* data, std::size_t size, std::uint32_t flags = 0) {
    RepairComplete request{};
    detail::check(fastdis_parse_repair_complete(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_repair_complete");
    return request;
}

inline Status try_parse_repair_complete(const void* data,
                                        std::size_t size,
                                        RepairComplete& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_repair_complete(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline RepairResponse parse_repair_response(const void* data, std::size_t size, std::uint32_t flags = 0) {
    RepairResponse request{};
    detail::check(fastdis_parse_repair_response(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_repair_response");
    return request;
}

inline Status try_parse_repair_response(const void* data,
                                        std::size_t size,
                                        RepairResponse& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_repair_response(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SimulationManagementRequest parse_create_entity(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SimulationManagementRequest request{};
    detail::check(fastdis_parse_create_entity(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_create_entity");
    return request;
}

inline Status try_parse_create_entity(const void* data,
                                      std::size_t size,
                                      SimulationManagementRequest& out_request,
                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_create_entity(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SimulationManagementRequest parse_remove_entity(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SimulationManagementRequest request{};
    detail::check(fastdis_parse_remove_entity(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_remove_entity");
    return request;
}

inline Status try_parse_remove_entity(const void* data,
                                      std::size_t size,
                                      SimulationManagementRequest& out_request,
                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_remove_entity(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline StartResume parse_start_resume(const void* data, std::size_t size, std::uint32_t flags = 0) {
    StartResume request{};
    detail::check(fastdis_parse_start_resume(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_start_resume");
    return request;
}

inline Status try_parse_start_resume(const void* data,
                                     std::size_t size,
                                     StartResume& out_request,
                                     std::uint32_t flags = 0) noexcept {
    return fastdis_parse_start_resume(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline StopFreeze parse_stop_freeze(const void* data, std::size_t size, std::uint32_t flags = 0) {
    StopFreeze request{};
    detail::check(fastdis_parse_stop_freeze(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_stop_freeze");
    return request;
}

inline Status try_parse_stop_freeze(const void* data,
                                    std::size_t size,
                                    StopFreeze& out_request,
                                    std::uint32_t flags = 0) noexcept {
    return fastdis_parse_stop_freeze(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline Acknowledge parse_acknowledge(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Acknowledge request{};
    detail::check(fastdis_parse_acknowledge(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_acknowledge");
    return request;
}

inline Status try_parse_acknowledge(const void* data,
                                    std::size_t size,
                                    Acknowledge& out_request,
                                    std::uint32_t flags = 0) noexcept {
    return fastdis_parse_acknowledge(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ActionRequest parse_action_request(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ActionRequest request{};
    detail::check(fastdis_parse_action_request(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_action_request");
    return request;
}

inline Status try_parse_action_request(const void* data,
                                       std::size_t size,
                                       ActionRequest& out_request,
                                       std::uint32_t flags = 0) noexcept {
    return fastdis_parse_action_request(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ActionResponse parse_action_response(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ActionResponse request{};
    detail::check(fastdis_parse_action_response(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_action_response");
    return request;
}

inline Status try_parse_action_response(const void* data,
                                        std::size_t size,
                                        ActionResponse& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_action_response(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline DataQuery parse_data_query(const void* data, std::size_t size, std::uint32_t flags = 0) {
    DataQuery request{};
    detail::check(fastdis_parse_data_query(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_data_query");
    return request;
}

inline Status try_parse_data_query(const void* data,
                                   std::size_t size,
                                   DataQuery& out_request,
                                   std::uint32_t flags = 0) noexcept {
    return fastdis_parse_data_query(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SetData parse_set_data(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SetData request{};
    detail::check(fastdis_parse_set_data(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_set_data");
    return request;
}

inline Status try_parse_set_data(const void* data,
                                 std::size_t size,
                                 SetData& out_request,
                                 std::uint32_t flags = 0) noexcept {
    return fastdis_parse_set_data(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SetData parse_data(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SetData request{};
    detail::check(fastdis_parse_data(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_data");
    return request;
}

inline Status try_parse_data(const void* data,
                             std::size_t size,
                             SetData& out_request,
                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_data(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline EventReport parse_event_report(const void* data, std::size_t size, std::uint32_t flags = 0) {
    EventReport request{};
    detail::check(fastdis_parse_event_report(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_event_report");
    return request;
}

inline Status try_parse_event_report(const void* data,
                                     std::size_t size,
                                     EventReport& out_request,
                                     std::uint32_t flags = 0) noexcept {
    return fastdis_parse_event_report(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline Comment parse_comment(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Comment request{};
    detail::check(fastdis_parse_comment(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_comment");
    return request;
}

inline Status try_parse_comment(const void* data,
                                std::size_t size,
                                Comment& out_request,
                                std::uint32_t flags = 0) noexcept {
    return fastdis_parse_comment(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SimulationManagementReliableRequest parse_create_entity_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SimulationManagementReliableRequest request{};
    detail::check(fastdis_parse_create_entity_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_create_entity_reliable");
    return request;
}

inline Status try_parse_create_entity_reliable(const void* data,
                                               std::size_t size,
                                               SimulationManagementReliableRequest& out_request,
                                               std::uint32_t flags = 0) noexcept {
    return fastdis_parse_create_entity_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SimulationManagementReliableRequest parse_remove_entity_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SimulationManagementReliableRequest request{};
    detail::check(fastdis_parse_remove_entity_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_remove_entity_reliable");
    return request;
}

inline Status try_parse_remove_entity_reliable(const void* data,
                                               std::size_t size,
                                               SimulationManagementReliableRequest& out_request,
                                               std::uint32_t flags = 0) noexcept {
    return fastdis_parse_remove_entity_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline StartResumeReliable parse_start_resume_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    StartResumeReliable request{};
    detail::check(fastdis_parse_start_resume_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_start_resume_reliable");
    return request;
}

inline Status try_parse_start_resume_reliable(const void* data,
                                              std::size_t size,
                                              StartResumeReliable& out_request,
                                              std::uint32_t flags = 0) noexcept {
    return fastdis_parse_start_resume_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline StopFreezeReliable parse_stop_freeze_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    StopFreezeReliable request{};
    detail::check(fastdis_parse_stop_freeze_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_stop_freeze_reliable");
    return request;
}

inline Status try_parse_stop_freeze_reliable(const void* data,
                                             std::size_t size,
                                             StopFreezeReliable& out_request,
                                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_stop_freeze_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline Acknowledge parse_acknowledge_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    Acknowledge request{};
    detail::check(fastdis_parse_acknowledge_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_acknowledge_reliable");
    return request;
}

inline Status try_parse_acknowledge_reliable(const void* data,
                                             std::size_t size,
                                             Acknowledge& out_request,
                                             std::uint32_t flags = 0) noexcept {
    return fastdis_parse_acknowledge_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ActionRequestReliable parse_action_request_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ActionRequestReliable request{};
    detail::check(fastdis_parse_action_request_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_action_request_reliable");
    return request;
}

inline Status try_parse_action_request_reliable(const void* data,
                                                std::size_t size,
                                                ActionRequestReliable& out_request,
                                                std::uint32_t flags = 0) noexcept {
    return fastdis_parse_action_request_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline ActionResponseReliable parse_action_response_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    ActionResponseReliable request{};
    detail::check(fastdis_parse_action_response_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_action_response_reliable");
    return request;
}

inline Status try_parse_action_response_reliable(const void* data,
                                                 std::size_t size,
                                                 ActionResponseReliable& out_request,
                                                 std::uint32_t flags = 0) noexcept {
    return fastdis_parse_action_response_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline DataQueryReliable parse_data_query_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    DataQueryReliable request{};
    detail::check(fastdis_parse_data_query_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_data_query_reliable");
    return request;
}

inline Status try_parse_data_query_reliable(const void* data,
                                            std::size_t size,
                                            DataQueryReliable& out_request,
                                            std::uint32_t flags = 0) noexcept {
    return fastdis_parse_data_query_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SetDataReliable parse_set_data_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SetDataReliable request{};
    detail::check(fastdis_parse_set_data_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_set_data_reliable");
    return request;
}

inline Status try_parse_set_data_reliable(const void* data,
                                          std::size_t size,
                                          SetDataReliable& out_request,
                                          std::uint32_t flags = 0) noexcept {
    return fastdis_parse_set_data_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline DataReliable parse_data_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    DataReliable request{};
    detail::check(fastdis_parse_data_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_data_reliable");
    return request;
}

inline Status try_parse_data_reliable(const void* data,
                                      std::size_t size,
                                      DataReliable& out_request,
                                      std::uint32_t flags = 0) noexcept {
    return fastdis_parse_data_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline EventReportReliable parse_event_report_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    EventReportReliable request{};
    detail::check(fastdis_parse_event_report_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_event_report_reliable");
    return request;
}

inline Status try_parse_event_report_reliable(const void* data,
                                              std::size_t size,
                                              EventReportReliable& out_request,
                                              std::uint32_t flags = 0) noexcept {
    return fastdis_parse_event_report_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline CommentReliable parse_comment_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    CommentReliable request{};
    detail::check(fastdis_parse_comment_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_comment_reliable");
    return request;
}

inline Status try_parse_comment_reliable(const void* data,
                                         std::size_t size,
                                         CommentReliable& out_request,
                                         std::uint32_t flags = 0) noexcept {
    return fastdis_parse_comment_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline RecordReliable parse_record_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    RecordReliable request{};
    detail::check(fastdis_parse_record_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_record_reliable");
    return request;
}

inline Status try_parse_record_reliable(const void* data,
                                        std::size_t size,
                                        RecordReliable& out_request,
                                        std::uint32_t flags = 0) noexcept {
    return fastdis_parse_record_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline SetRecordReliable parse_set_record_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    SetRecordReliable request{};
    detail::check(fastdis_parse_set_record_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_set_record_reliable");
    return request;
}

inline Status try_parse_set_record_reliable(const void* data,
                                            std::size_t size,
                                            SetRecordReliable& out_request,
                                            std::uint32_t flags = 0) noexcept {
    return fastdis_parse_set_record_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline RecordQueryReliable parse_record_query_reliable(const void* data, std::size_t size, std::uint32_t flags = 0) {
    RecordQueryReliable request{};
    detail::check(fastdis_parse_record_query_reliable(static_cast<const std::uint8_t*>(data), size, flags, &request),
                  "fastdis_parse_record_query_reliable");
    return request;
}

inline Status try_parse_record_query_reliable(const void* data,
                                              std::size_t size,
                                              RecordQueryReliable& out_request,
                                              std::uint32_t flags = 0) noexcept {
    return fastdis_parse_record_query_reliable(static_cast<const std::uint8_t*>(data), size, flags, &out_request);
}

inline PacketView make_packet_view(const void* data, std::size_t size, void* user = nullptr) noexcept {
    return PacketView{static_cast<const std::uint8_t*>(data), size, user};
}

inline PacketView packet_view(const void* data, std::size_t size, void* user = nullptr) noexcept {
    return make_packet_view(data, size, user);
}

inline EntityId snapshot_entity_id(const EntitySnapshot& snapshot) noexcept { return snapshot.transform.entity_id; }
inline const WorldCoordinates& snapshot_location(const EntitySnapshot& snapshot) noexcept { return snapshot.transform.location; }
inline const EulerAngles& snapshot_orientation(const EntitySnapshot& snapshot) noexcept { return snapshot.transform.orientation; }
inline const Vec3f& snapshot_linear_velocity(const EntitySnapshot& snapshot) noexcept { return snapshot.transform.linear_velocity; }
inline bool snapshot_is_new(const EntitySnapshot& snapshot) noexcept { return (snapshot.change_flags & FASTDIS_ENTITY_CHANGE_NEW) != 0u; }
inline bool snapshot_is_updated(const EntitySnapshot& snapshot) noexcept { return (snapshot.change_flags & FASTDIS_ENTITY_CHANGE_UPDATED) != 0u; }
inline bool snapshot_is_stale(const EntitySnapshot& snapshot) noexcept { return (snapshot.change_flags & FASTDIS_ENTITY_CHANGE_STALE) != 0u; }
inline bool snapshot_is_removed(const EntitySnapshot& snapshot) noexcept { return (snapshot.change_flags & FASTDIS_ENTITY_CHANGE_REMOVED) != 0u; }
inline bool snapshot_is_extrapolated(const EntitySnapshot& snapshot) noexcept { return (snapshot.change_flags & FASTDIS_ENTITY_CHANGE_EXTRAPOLATED) != 0u; }

inline Status try_extrapolate_entity_transform_linear(const EntityTransform& transform,
                                                     double delta_seconds,
                                                     EntityTransform& out_transform) noexcept {
    return fastdis_extrapolate_entity_transform_linear(&transform, delta_seconds, &out_transform);
}

inline EntityTransform extrapolate_entity_transform_linear(const EntityTransform& transform, double delta_seconds) {
    EntityTransform out{};
    detail::check(try_extrapolate_entity_transform_linear(transform, delta_seconds, out),
                  "fastdis_extrapolate_entity_transform_linear");
    return out;
}

inline Status try_extrapolate_entity_snapshot_linear(const EntitySnapshot& snapshot,
                                                    std::uint64_t target_tick,
                                                    double seconds_per_tick,
                                                    EntitySnapshot& out_snapshot) noexcept {
    return fastdis_extrapolate_entity_snapshot_linear(&snapshot, target_tick, seconds_per_tick, &out_snapshot);
}

inline EntitySnapshot extrapolate_entity_snapshot_linear(const EntitySnapshot& snapshot,
                                                        std::uint64_t target_tick,
                                                        double seconds_per_tick) {
    EntitySnapshot out{};
    detail::check(try_extrapolate_entity_snapshot_linear(snapshot, target_tick, seconds_per_tick, out),
                  "fastdis_extrapolate_entity_snapshot_linear");
    return out;
}

inline Status try_extrapolate_entity_transform_dead_reckoning(const EntityTransform& transform,
                                                             double delta_seconds,
                                                             EntityTransform& out_transform) noexcept {
    return fastdis_extrapolate_entity_transform_dead_reckoning(&transform, delta_seconds, &out_transform);
}

inline EntityTransform extrapolate_entity_transform_dead_reckoning(const EntityTransform& transform, double delta_seconds) {
    EntityTransform out{};
    detail::check(try_extrapolate_entity_transform_dead_reckoning(transform, delta_seconds, out),
                  "fastdis_extrapolate_entity_transform_dead_reckoning");
    return out;
}

inline Status try_extrapolate_entity_snapshot_dead_reckoning(const EntitySnapshot& snapshot,
                                                            std::uint64_t target_tick,
                                                            double seconds_per_tick,
                                                            EntitySnapshot& out_snapshot) noexcept {
    return fastdis_extrapolate_entity_snapshot_dead_reckoning(&snapshot, target_tick, seconds_per_tick, &out_snapshot);
}

inline EntitySnapshot extrapolate_entity_snapshot_dead_reckoning(const EntitySnapshot& snapshot,
                                                                std::uint64_t target_tick,
                                                                double seconds_per_tick) {
    EntitySnapshot out{};
    detail::check(try_extrapolate_entity_snapshot_dead_reckoning(snapshot, target_tick, seconds_per_tick, out),
                  "fastdis_extrapolate_entity_snapshot_dead_reckoning");
    return out;
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

#if __cplusplus >= 202002L
    Status try_scan_entity_states(std::span<const PacketView> packets, EntityStateBatch& batch, ScanStats* stats = nullptr) noexcept {
        return try_scan_entity_states(packets.data(), packets.size(), batch, stats);
    }

    ScanStats scan_entity_states(std::span<const PacketView> packets, EntityStateBatch& batch) {
        return scan_entity_states(packets.data(), packets.size(), batch);
    }
#endif

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

#if __cplusplus >= 202002L
    Status try_scan_transforms(std::span<const PacketView> packets, TransformBatch& batch, ScanStats* stats = nullptr) noexcept {
        return try_scan_transforms(packets.data(), packets.size(), batch, stats);
    }

    ScanStats scan_transforms(std::span<const PacketView> packets, TransformBatch& batch) {
        return scan_transforms(packets.data(), packets.size(), batch);
    }
#endif

private:
    fastdis_scanner_t* handle_ = nullptr;
};

class ScannerBuilder {
public:
    ScannerBuilder() = default;

    ScannerBuilder& profile(Profile profile) {
        config_.use_profile(profile);
        return *this;
    }

    ScannerBuilder& entity_transform_profile() { return profile(Profile::EntityTransform); }
    ScannerBuilder& entity_state_pose_profile() { return profile(Profile::EntityStatePose); }
    ScannerBuilder& entity_state_full_profile() { return profile(Profile::EntityStateFull); }
    ScannerBuilder& header_counting_profile() { return profile(Profile::HeaderCounting); }

    ScannerBuilder& versions(std::initializer_list<std::uint8_t> values) {
        config_.only_versions(values);
        return *this;
    }

    ScannerBuilder& pdu_types(std::initializer_list<std::uint8_t> values) {
        config_.only_pdu_types(values);
        return *this;
    }

    ScannerBuilder& protocol_families(std::initializer_list<std::uint8_t> values) {
        config_.only_protocol_families(values);
        return *this;
    }

    ScannerBuilder& exercise_ids(std::initializer_list<std::uint8_t> values) {
        config_.only_exercise_ids(values);
        return *this;
    }

    ScannerBuilder& force_ids(std::initializer_list<std::uint8_t> values) {
        config_.only_entity_force_ids(values);
        return *this;
    }

    ScannerBuilder& sample_every(std::uint32_t every, std::uint32_t offset = 0) {
        config_.sample(every, offset);
        return *this;
    }

    ScannerBuilder& entity_state_fields(std::uint64_t mask) {
        config_.entity_state_fields(mask);
        return *this;
    }

    ScannerBuilder& allow_entity_ids(std::initializer_list<EntityId> ids) {
        entity_id_mode_ = EntityIdFilterMode::Allow;
        entity_ids_.assign(ids.begin(), ids.end());
        return *this;
    }

    ScannerBuilder& block_entity_ids(std::initializer_list<EntityId> ids) {
        entity_id_mode_ = EntityIdFilterMode::Block;
        entity_ids_.assign(ids.begin(), ids.end());
        return *this;
    }

    const ScanConfig& config() const noexcept { return config_; }

    Status try_build(Scanner& out) const {
        fastdis_scanner_t* handle = fastdis_scanner_create(config_.native_ptr());
        if (!handle) {
            return FASTDIS_ERR_OUT_OF_MEMORY;
        }
        if (entity_id_mode_ != EntityIdFilterMode::Disabled) {
            const EntityId* ids = entity_ids_.empty() ? nullptr : entity_ids_.data();
            Status status = fastdis_scanner_set_entity_ids(handle, static_cast<std::uint32_t>(entity_id_mode_), ids, entity_ids_.size());
            if (status != FASTDIS_OK) {
                fastdis_scanner_destroy(handle);
                return status;
            }
        }
        out.reset(handle);
        return FASTDIS_OK;
    }

    Scanner build() const {
        Scanner scanner(config_);
        if (entity_id_mode_ != EntityIdFilterMode::Disabled) {
            const EntityId* ids = entity_ids_.empty() ? nullptr : entity_ids_.data();
            detail::check(fastdis_scanner_set_entity_ids(scanner.native(), static_cast<std::uint32_t>(entity_id_mode_), ids, entity_ids_.size()),
                          "fastdis_scanner_set_entity_ids");
        }
        return scanner;
    }

private:
    ScanConfig config_{};
    EntityIdFilterMode entity_id_mode_ = EntityIdFilterMode::Disabled;
    std::vector<EntityId> entity_ids_;
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

#if __cplusplus >= 202002L
    Status try_ingest(Scanner& scanner,
                      std::span<const PacketView> packets,
                      bool advance_tick = true,
                      EntityTableUpdateStats* out_stats = nullptr) noexcept {
        return try_ingest(scanner, packets.data(), packets.size(), advance_tick, out_stats);
    }

    EntityTableUpdateStats ingest(Scanner& scanner, std::span<const PacketView> packets, bool advance_tick = true) {
        return ingest(scanner, packets.data(), packets.size(), advance_tick);
    }
#endif

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

class EntityTableConfig {
public:
    EntityTableConfig& reserve(std::size_t value) noexcept {
        reserve_ = value;
        return *this;
    }

    std::size_t reserve() const noexcept { return reserve_; }

    Status try_build(EntityTable& out) const {
        fastdis_entity_table_t* handle = fastdis_entity_table_create(reserve_);
        if (!handle) {
            return FASTDIS_ERR_OUT_OF_MEMORY;
        }
        out.reset(handle);
        return FASTDIS_OK;
    }

    EntityTable build() const {
        return EntityTable(reserve_);
    }

private:
    std::size_t reserve_ = 0u;
};

class SnapshotBuffer {
public:
    SnapshotBuffer() = default;

    explicit SnapshotBuffer(std::size_t capacity)
        : handle_(fastdis_entity_snapshot_buffer_create(capacity)) {
        if (!handle_) {
            detail::check(FASTDIS_ERR_OUT_OF_MEMORY, "fastdis_entity_snapshot_buffer_create");
        }
    }

    SnapshotBuffer(std::size_t capacity, std::size_t slot_count)
        : handle_(fastdis_entity_snapshot_buffer_create_ex(capacity, slot_count)) {
        if (!handle_) {
            detail::check(FASTDIS_ERR_BAD_ARGUMENT, "fastdis_entity_snapshot_buffer_create_ex");
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
    std::size_t slot_count() const noexcept { return fastdis_entity_snapshot_buffer_slot_count(handle_); }
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

    SnapshotBatch copy_latest_extrapolated(std::size_t capacity, std::uint64_t target_tick, double seconds_per_tick) {
        SnapshotBatch batch(capacity);
        detail::check(
            fastdis_entity_snapshot_buffer_copy_latest_extrapolated(
                handle_,
                target_tick,
                seconds_per_tick,
                batch.native_for_write()
            ),
            "fastdis_entity_snapshot_buffer_copy_latest_extrapolated"
        );
        return batch;
    }

    SnapshotBatch copy_latest_dead_reckoned(std::size_t capacity, std::uint64_t target_tick, double seconds_per_tick) {
        SnapshotBatch batch(capacity);
        detail::check(
            fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned(
                handle_,
                target_tick,
                seconds_per_tick,
                batch.native_for_write()
            ),
            "fastdis_entity_snapshot_buffer_copy_latest_dead_reckoned"
        );
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

#if __cplusplus >= 202002L
    Status try_ingest_and_publish_changed(EntityTable& table,
                                          Scanner& scanner,
                                          std::span<const PacketView> packets,
                                          bool advance_tick = true,
                                          bool clear_flags = true,
                                          EntityTableUpdateStats* out_stats = nullptr,
                                          SnapshotView* out_view = nullptr) noexcept {
        return try_ingest_and_publish_changed(table, scanner, packets.data(), packets.size(), advance_tick, clear_flags, out_stats, out_view);
    }

    SnapshotView ingest_and_publish_changed(EntityTable& table,
                                            Scanner& scanner,
                                            std::span<const PacketView> packets,
                                            bool advance_tick = true,
                                            bool clear_flags = true,
                                            EntityTableUpdateStats* out_stats = nullptr) {
        return ingest_and_publish_changed(table, scanner, packets.data(), packets.size(), advance_tick, clear_flags, out_stats);
    }
#endif

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

#if __cplusplus >= 202002L
    ScopedSnapshotView ingest_publish_changed_and_acquire(EntityTable& table,
                                                          Scanner& scanner,
                                                          std::span<const PacketView> packets,
                                                          bool advance_tick = true,
                                                          bool clear_flags = true,
                                                          EntityTableUpdateStats* out_stats = nullptr) {
        return ingest_publish_changed_and_acquire(table, scanner, packets.data(), packets.size(), advance_tick, clear_flags, out_stats);
    }
#endif

private:
    fastdis_entity_snapshot_buffer_t* handle_ = nullptr;
};

class SnapshotBufferConfig {
public:
    SnapshotBufferConfig& capacity(std::size_t value) noexcept {
        capacity_ = value;
        return *this;
    }

    SnapshotBufferConfig& slots(std::size_t value) noexcept {
        slots_ = value;
        return *this;
    }

    std::size_t capacity() const noexcept { return capacity_; }
    std::size_t slots() const noexcept { return slots_; }

    Status try_build(SnapshotBuffer& out) const {
        fastdis_entity_snapshot_buffer_t* handle = fastdis_entity_snapshot_buffer_create_ex(capacity_, slots_);
        if (!handle) {
            return slots_ < 2u ? FASTDIS_ERR_BAD_ARGUMENT : FASTDIS_ERR_OUT_OF_MEMORY;
        }
        out.reset(handle);
        return FASTDIS_OK;
    }

    SnapshotBuffer build() const {
        return SnapshotBuffer(capacity_, slots_);
    }

private:
    std::size_t capacity_ = 0u;
    std::size_t slots_ = 2u;
};

} // namespace fastdis

#endif /* FASTDIS_FASTDIS_HPP */
