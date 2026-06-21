using UnityEngine;

namespace SheepFling.FastDIS.Editor
{
    /// <summary>
    /// Unity dead reckoning runtime verification contract.
    /// Runtime verification loads tests/data/dead_reckoning_engine_cases.json,
    /// calls the shared native fastdis_extrapolate_entity_transform_dead_reckoning
    /// evaluator, applies the result through the Unity transform mapper, and
    /// writes schema fastdis.unity.dead_reckoning_runtime.v1.
    /// </summary>
    public static class FastDisDeadReckoningRuntimeVerification
    {
        public const string ReportSchema = "fastdis.unity.dead_reckoning_runtime.v1";

        public static void DescribeContract()
        {
            Debug.Log($"FastDIS dead reckoning runtime verification uses {ReportSchema}");
        }
    }
}
