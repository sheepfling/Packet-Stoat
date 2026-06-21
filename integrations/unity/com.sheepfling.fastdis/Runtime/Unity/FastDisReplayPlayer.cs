using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisReplayPlayer : MonoBehaviour
    {
        [SerializeField]
        private TextAsset replayBytes;

        [SerializeField]
        private bool loop;

        public TextAsset ReplayBytes => replayBytes;
        public bool Loop => loop;
    }
}
