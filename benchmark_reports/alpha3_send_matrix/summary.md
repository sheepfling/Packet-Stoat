# Alpha 3 Outbound Benchmark Report

- generated_at: `2026-06-19T21:03:16.463902+00:00`

| case | status | best Mpps | avg Mpps | p50 ms | p95 ms | MiB/s | packets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| python_send_entity | passed | 0.005 | 0.005 | 106.683 | 115.810 | 0.71 | 500 |
| python_replay_send | passed | 0.006 | 0.006 | 80.271 | 80.917 | 0.86 | 500 |
| c_udp_send | passed | 0.048 | 0.035 | 14.380 | 18.008 | 6.64 | 500 |
| cpp_udp_send | passed | 0.054 | 0.032 | 15.508 | 21.199 | 7.48 | 500 |
| godot_udp_send | passed | 0.001 | 0.001 | 448.997 | 480.063 | 0.17 | 500 |

## Notes

- These are localhost end-to-end sender benchmarks, not core parser hot-path benchmarks.
- Unreal outbound remains a verification/smoke lane and is not included in this report.
