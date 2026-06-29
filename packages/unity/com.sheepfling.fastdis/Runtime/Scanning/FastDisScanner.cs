using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisScanner
    {
        public bool NativeAvailable => FastDisNative.TryGetAbiVersion(out _);

        public IReadOnlyList<FastDisPacketView> Scan(IEnumerable<byte[]> packets)
        {
            List<FastDisPacketView> views = new List<FastDisPacketView>();
            foreach (byte[] packet in packets)
            {
                if (packet != null && packet.Length >= 12)
                {
                    views.Add(new FastDisPacketView(packet));
                }
            }
            return views;
        }

        public bool TryParseEntityTransform(byte[] packet, out FastDisEntityTransform transform)
        {
            return FastDisNative.TryParseEntityTransform(packet, out transform);
        }

        public bool TryParseCreateEntity(byte[] packet, out FastDisSimulationManagementRequest request)
        {
            return FastDisNative.TryParseCreateEntity(packet, out request);
        }

        public bool TryParseFire(byte[] packet, out FastDisFire fire)
        {
            return FastDisNative.TryParseFire(packet, out fire);
        }

        public bool TryParseCollision(byte[] packet, out FastDisCollision collision)
        {
            return FastDisNative.TryParseCollision(packet, out collision);
        }

        public bool TryParseCollisionElastic(byte[] packet, out FastDisCollisionElastic collisionElastic)
        {
            return FastDisNative.TryParseCollisionElastic(packet, out collisionElastic);
        }

        public bool TryParseDesignator(byte[] packet, out FastDisDesignator designator)
        {
            return FastDisNative.TryParseDesignator(packet, out designator);
        }

        public bool TryParseTransmitter(byte[] packet, out FastDisTransmitter transmitter)
        {
            return FastDisNative.TryParseTransmitter(packet, out transmitter);
        }

        public bool TryParseOtherPdu(byte[] packet, out FastDisOtherPdu other)
        {
            return FastDisNative.TryParseOtherPdu(packet, out other);
        }

        public bool TryParseAggregateState(byte[] packet, out FastDisAggregateState aggregate)
        {
            return FastDisNative.TryParseAggregateState(packet, out aggregate);
        }

        public bool TryParseIsGroupOf(byte[] packet, out FastDisIsGroupOf group)
        {
            return FastDisNative.TryParseIsGroupOf(packet, out group);
        }

        public bool TryParseTransferControlRequest(byte[] packet, out FastDisTransferControlRequest request)
        {
            return FastDisNative.TryParseTransferControlRequest(packet, out request);
        }

        public bool TryParseTransferOwnership(byte[] packet, out FastDisTransferOwnership request)
        {
            return FastDisNative.TryParseTransferOwnership(packet, out request);
        }

        public bool TryParseIsPartOf(byte[] packet, out FastDisIsPartOf part)
        {
            return FastDisNative.TryParseIsPartOf(packet, out part);
        }

        public bool TryParseMinefieldState(byte[] packet, out FastDisMinefieldState state)
        {
            return FastDisNative.TryParseMinefieldState(packet, out state);
        }

        public bool TryParseMinefieldQuery(byte[] packet, out FastDisMinefieldQuery query)
        {
            return FastDisNative.TryParseMinefieldQuery(packet, out query);
        }

        public bool TryParseMinefieldData(byte[] packet, out FastDisMinefieldData data)
        {
            return FastDisNative.TryParseMinefieldData(packet, out data);
        }

        public bool TryParseMinefieldResponseNack(byte[] packet, out FastDisMinefieldResponseNack nack)
        {
            return FastDisNative.TryParseMinefieldResponseNack(packet, out nack);
        }

        public bool TryParseEnvironmentalProcess(byte[] packet, out FastDisEnvironmentalProcess process)
        {
            return FastDisNative.TryParseEnvironmentalProcess(packet, out process);
        }

        public bool TryParseGriddedData(byte[] packet, out FastDisGriddedData grid)
        {
            return FastDisNative.TryParseGriddedData(packet, out grid);
        }

        public bool TryParsePointObjectState(byte[] packet, out FastDisPointObjectState point)
        {
            return FastDisNative.TryParsePointObjectState(packet, out point);
        }

        public bool TryParseLinearObjectState(byte[] packet, out FastDisLinearObjectState linear)
        {
            return FastDisNative.TryParseLinearObjectState(packet, out linear);
        }

        public bool TryParseArealObjectState(byte[] packet, out FastDisArealObjectState areal)
        {
            return FastDisNative.TryParseArealObjectState(packet, out areal);
        }

        public bool TryParseTspi(byte[] packet, out FastDisTspi tspi)
        {
            return FastDisNative.TryParseTspi(packet, out tspi);
        }

        public bool TryParseLiveEntityAppearance(byte[] packet, out FastDisLiveEntityAppearance appearance)
        {
            return FastDisNative.TryParseLiveEntityAppearance(packet, out appearance);
        }

        public bool TryParseArticulatedParts(byte[] packet, out FastDisArticulatedParts parts)
        {
            return FastDisNative.TryParseArticulatedParts(packet, out parts);
        }

        public bool TryParseLeFire(byte[] packet, out FastDisLeFire fire)
        {
            return FastDisNative.TryParseLeFire(packet, out fire);
        }

        public bool TryParseLeDetonation(byte[] packet, out FastDisLeDetonation detonation)
        {
            return FastDisNative.TryParseLeDetonation(packet, out detonation);
        }

        public bool TryParseSignal(byte[] packet, out FastDisSignal signal)
        {
            return FastDisNative.TryParseSignal(packet, out signal);
        }

        public bool TryParseReceiver(byte[] packet, out FastDisReceiver receiver)
        {
            return FastDisNative.TryParseReceiver(packet, out receiver);
        }

        public bool TryParseElectronicEmissions(byte[] packet, out FastDisElectronicEmissions emissions)
        {
            return FastDisNative.TryParseElectronicEmissions(packet, out emissions);
        }

        public bool TryParseIffAtcNavAidsLayer1(byte[] packet, out FastDisIffAtcNavAidsLayer1 iff)
        {
            return FastDisNative.TryParseIffAtcNavAidsLayer1(packet, out iff);
        }

        public bool TryParseIff(byte[] packet, out FastDisIff iff)
        {
            return FastDisNative.TryParseIff(packet, out iff);
        }

        public bool TryParseUa(byte[] packet, out FastDisUa ua)
        {
            return FastDisNative.TryParseUa(packet, out ua);
        }

        public bool TryParseSees(byte[] packet, out FastDisSees sees)
        {
            return FastDisNative.TryParseSees(packet, out sees);
        }

        public bool TryParseIntercomSignal(byte[] packet, out FastDisIntercomSignal signal)
        {
            return FastDisNative.TryParseIntercomSignal(packet, out signal);
        }

        public bool TryParseIntercomControl(byte[] packet, out FastDisIntercomControl control)
        {
            return FastDisNative.TryParseIntercomControl(packet, out control);
        }

        public bool TryParseAttribute(byte[] packet, out FastDisAttribute attribute)
        {
            return FastDisNative.TryParseAttribute(packet, out attribute);
        }

        public bool TryParseDirectedEnergyFire(byte[] packet, out FastDisDirectedEnergyFire directedEnergyFire)
        {
            return FastDisNative.TryParseDirectedEnergyFire(packet, out directedEnergyFire);
        }

        public bool TryParseEntityDamageStatus(byte[] packet, out FastDisEntityDamageStatus entityDamageStatus)
        {
            return FastDisNative.TryParseEntityDamageStatus(packet, out entityDamageStatus);
        }

        public bool TryParseInformationOperationsAction(byte[] packet, out FastDisInformationOperationsAction action)
        {
            return FastDisNative.TryParseInformationOperationsAction(packet, out action);
        }

        public bool TryParseInformationOperationsReport(byte[] packet, out FastDisInformationOperationsReport report)
        {
            return FastDisNative.TryParseInformationOperationsReport(packet, out report);
        }

        public bool TryParseServiceRequest(byte[] packet, out FastDisServiceRequest request)
        {
            return FastDisNative.TryParseServiceRequest(packet, out request);
        }

        public bool TryParseResupplyOffer(byte[] packet, out FastDisResupplyOffer request)
        {
            return FastDisNative.TryParseResupplyOffer(packet, out request);
        }

        public bool TryParseResupplyReceived(byte[] packet, out FastDisResupplyReceived request)
        {
            return FastDisNative.TryParseResupplyReceived(packet, out request);
        }

        public bool TryParseResupplyCancel(byte[] packet, out FastDisResupplyCancel request)
        {
            return FastDisNative.TryParseResupplyCancel(packet, out request);
        }

        public bool TryParseRepairComplete(byte[] packet, out FastDisRepairComplete request)
        {
            return FastDisNative.TryParseRepairComplete(packet, out request);
        }

        public bool TryParseRepairResponse(byte[] packet, out FastDisRepairResponse request)
        {
            return FastDisNative.TryParseRepairResponse(packet, out request);
        }

        public bool TryParseDetonation(byte[] packet, out FastDisDetonation detonation)
        {
            return FastDisNative.TryParseDetonation(packet, out detonation);
        }

        public bool TryParseRemoveEntity(byte[] packet, out FastDisSimulationManagementRequest request)
        {
            return FastDisNative.TryParseRemoveEntity(packet, out request);
        }

        public bool TryParseStartResume(byte[] packet, out FastDisStartResume request)
        {
            return FastDisNative.TryParseStartResume(packet, out request);
        }

        public bool TryParseStopFreeze(byte[] packet, out FastDisStopFreeze request)
        {
            return FastDisNative.TryParseStopFreeze(packet, out request);
        }

        public bool TryParseAcknowledge(byte[] packet, out FastDisAcknowledge request)
        {
            return FastDisNative.TryParseAcknowledge(packet, out request);
        }

        public bool TryParseActionRequest(byte[] packet, out FastDisActionRequest request)
        {
            return FastDisNative.TryParseActionRequest(packet, out request);
        }

        public bool TryParseActionResponse(byte[] packet, out FastDisActionResponse request)
        {
            return FastDisNative.TryParseActionResponse(packet, out request);
        }

        public bool TryParseDataQuery(byte[] packet, out FastDisDataQuery request)
        {
            return FastDisNative.TryParseDataQuery(packet, out request);
        }

        public bool TryParseSetData(byte[] packet, out FastDisSetData request)
        {
            return FastDisNative.TryParseSetData(packet, out request);
        }

        public bool TryParseData(byte[] packet, out FastDisSetData request)
        {
            return FastDisNative.TryParseData(packet, out request);
        }

        public bool TryParseEventReport(byte[] packet, out FastDisEventReport request)
        {
            return FastDisNative.TryParseEventReport(packet, out request);
        }

        public bool TryParseComment(byte[] packet, out FastDisComment request)
        {
            return FastDisNative.TryParseComment(packet, out request);
        }

        public bool TryParseCreateEntityReliable(byte[] packet, out FastDisSimulationManagementReliableRequest request)
        {
            return FastDisNative.TryParseCreateEntityReliable(packet, out request);
        }

        public bool TryParseRemoveEntityReliable(byte[] packet, out FastDisSimulationManagementReliableRequest request)
        {
            return FastDisNative.TryParseRemoveEntityReliable(packet, out request);
        }

        public bool TryParseStartResumeReliable(byte[] packet, out FastDisStartResumeReliable request)
        {
            return FastDisNative.TryParseStartResumeReliable(packet, out request);
        }

        public bool TryParseStopFreezeReliable(byte[] packet, out FastDisStopFreezeReliable request)
        {
            return FastDisNative.TryParseStopFreezeReliable(packet, out request);
        }

        public bool TryParseAcknowledgeReliable(byte[] packet, out FastDisAcknowledge request)
        {
            return FastDisNative.TryParseAcknowledgeReliable(packet, out request);
        }

        public bool TryParseActionRequestReliable(byte[] packet, out FastDisActionRequestReliable request)
        {
            return FastDisNative.TryParseActionRequestReliable(packet, out request);
        }

        public bool TryParseActionResponseReliable(byte[] packet, out FastDisActionResponseReliable request)
        {
            return FastDisNative.TryParseActionResponseReliable(packet, out request);
        }

        public bool TryParseDataQueryReliable(byte[] packet, out FastDisDataQueryReliable request)
        {
            return FastDisNative.TryParseDataQueryReliable(packet, out request);
        }

        public bool TryParseSetDataReliable(byte[] packet, out FastDisSetDataReliable request)
        {
            return FastDisNative.TryParseSetDataReliable(packet, out request);
        }

        public bool TryParseDataReliable(byte[] packet, out FastDisDataReliable request)
        {
            return FastDisNative.TryParseDataReliable(packet, out request);
        }

        public bool TryParseEventReportReliable(byte[] packet, out FastDisEventReportReliable request)
        {
            return FastDisNative.TryParseEventReportReliable(packet, out request);
        }

        public bool TryParseCommentReliable(byte[] packet, out FastDisCommentReliable request)
        {
            return FastDisNative.TryParseCommentReliable(packet, out request);
        }

        public bool TryParseRecordReliable(byte[] packet, out FastDisRecordReliable request)
        {
            return FastDisNative.TryParseRecordReliable(packet, out request);
        }

        public bool TryParseSetRecordReliable(byte[] packet, out FastDisSetRecordReliable request)
        {
            return FastDisNative.TryParseSetRecordReliable(packet, out request);
        }

        public bool TryParseRecordQueryReliable(byte[] packet, out FastDisRecordQueryReliable request)
        {
            return FastDisNative.TryParseRecordQueryReliable(packet, out request);
        }

        public IReadOnlyList<FastDisEntityTransform> ScanEntityTransforms(IEnumerable<byte[]> packets)
        {
            List<FastDisEntityTransform> transforms = new List<FastDisEntityTransform>();
            foreach (byte[] packet in packets)
            {
                if (FastDisNative.TryParseEntityTransform(packet, out FastDisEntityTransform transform))
                {
                    transforms.Add(transform);
                }
            }
            return transforms;
        }
    }
}
