# Alpha 3 I/O Routes Report

- generated_at: `2026-06-19T18:07:07.805467+00:00`

| Route | Status | Notes |
| --- | --- | --- |
| python_net_smoke | passed | localhost UDP send/receive plus native scanner/entity-table/snapshot verification |
| godot_demo_replay_route | passed | Godot plugin/demo consumes replay emitted by the Python net smoke route |

## Route Details

### python_net_smoke

- status: `passed`
- command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.net_smoke --count 24 --entity-count 3 --site 100 --application 1 --entity 0 --write-replay /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/examples/godot/fastdis_demo/data/synthetic.fastdispkt --print-json`

```text
{
  "captured_packets": 24,
  "ingest_stats": {
    "scan": {
      "seen": 24,
      "malformed": 0,
      "accepted": 24,
      "emitted": 24
    },
    "tick": 1,
    "entity_count": 3,
    "table_updates": 24,
    "new_entities": 3,
    "changed_entities": 24,
    "unchanged_entities": 0,
    "removed_entities": 0
  },
  "snapshot_count": 3,
  "entity": [
    100,
    1,
    2
  ],
  "location_ecef_m": [
    -491891.7483655142,
    -5530741.361055055,
    3128061.876301698
  ],
  "orientation_dis_rad": [
    -0.08871683478355408,
    -5.326247066219977e-17,
    -2.0867104530334473
  ],
  "orientation_debug": {
    "location_ecef_m": [
      -491961.7483655142,
      -5530747.361055055,
      3128061.876301698
    ],
    "dis_orientation_deg": {
      "psi": -5.0831000000000035,
      "theta": -3.051714705980124e-15,
      "phi": -119.5597
    }
  }
}
```

### godot_demo_replay_route

- status: `passed`
- command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/tools/run_godot_demo_smoke.py --skip-build --skip-replay-generation`

```text
Godot Engine v4.7.stable.official.5b4e0cb0f - https://godotengine.org

Replay loaded. Registered 3 entities.
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
Replay stepping: packets=24 known_entities=3
PASS EntityA moved 100.457588
PASS EntityB moved 97.001640
PASS EntityC moved 94.093437
FastDIS Godot demo smoke passed
Replay stepping: packets=24 known_entities=3
/Applications/Godot.app/Contents/MacOS/Godot --headless --path /tmp/fastdis_godot/repo/examples/godot/fastdis_demo --script /tmp/fastdis_godot/repo/examples/godot/fastdis_demo/scripts/run_demo_smoke.gd
```
