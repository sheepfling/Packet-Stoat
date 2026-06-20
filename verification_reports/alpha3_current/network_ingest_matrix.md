# Alpha 3 Network Ingest Matrix

- generated_at: `2026-06-19T20:28:19.633920+00:00`

| Surface | Mode | Status | Notes |
| --- | --- | --- | --- |
| python | localhost_udp | passed | canonical sender truth file plus Python receiver verification report |
| c | localhost_udp | passed | canonical sender truth file plus C UDP receiver verification report |
| cpp | localhost_udp | passed | canonical sender truth file plus C++ native UDP receiver verification report |
| godot | live_udp | passed | headless Godot localhost UDP smoke route using FastDisWorld; currently proven as a one-entity engine lane |
| unreal | live_udp | passed | Unreal 5.8 localhost UDP automation smoke route using UFastDisWorldSubsystem; currently proven as a one-entity engine lane |

## Route Details

### python / localhost_udp

- status: `passed`
- notes: canonical sender truth file plus Python receiver verification report
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 59162 --count 24 --entity-count 3 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_net_matrix_4z31gvuj/expected_session.json`
- recv_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.recv --bind 127.0.0.1 --port 59162 --max-packets 24 --timeout 2.0 --surface python --verify /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_net_matrix_4z31gvuj/expected_session.json`

```json
{
  "entity_state": 24,
  "errors": [],
  "latest_entities": [
    {
      "application": 1,
      "entity": 0,
      "force_id": 1,
      "location_ecef_m": [
        -491891.7483655142,
        -5530747.361055055,
        3128061.876301698
      ],
      "orientation_dis_rad": [
        -0.08871683478355408,
        -5.326247066219977e-17,
        -2.0867104530334473
      ],
      "site": 100
    },
    {
      "application": 1,
      "entity": 1,
      "force_id": 1,
      "location_ecef_m": [
        -491891.7483655142,
        -5530744.361055055,
        3128061.876301698
      ],
      "orientation_dis_rad": [
        -0.08871683478355408,
        -5.326247066219977e-17,
        -2.0867104530334473
      ],
      "site": 100
    },
    {
      "application": 1,
      "entity": 2,
      "force_id": 1,
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
      "site": 100
    }
  ],
  "malformed": 0,
  "packets_parsed": 24,
  "packets_received": 24,
  "schema": "fastdis.network_report.v1",
  "snapshots_published": 3,
  "surface": "python",
  "unique_entities": 3
}
```

### c / localhost_udp

- status: `passed`
- notes: canonical sender truth file plus C UDP receiver verification report
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 62098 --count 24 --entity-count 3 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_c_net_matrix_z5ivyqmh/expected_session.json`
- recv_command: `/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build/fastdis_udp_burst_c 62098 --max-packets 24 --idle-polls 800 --json`

```json
{
  "schema": "fastdis.c_udp_burst_report.v1",
  "surface": "c",
  "mode": "localhost_udp",
  "packets_received": 24,
  "packets_parsed": 24,
  "malformed": 0,
  "entity_state": 24,
  "burst_count": 1,
  "snapshots_published": 3,
  "unique_entities": 3,
  "latest_entities": [
    {
      "site": 100,
      "application": 1,
      "entity": 0,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530747.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    },
    {
      "site": 100,
      "application": 1,
      "entity": 1,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530744.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    },
    {
      "site": 100,
      "application": 1,
      "entity": 2,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530741.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    }
  ],
  "errors": [],
  "buffer_stats": {
    "publish_attempts": 1,
    "publish_successes": 1,
    "publish_busy": 0,
    "acquire_count": 0,
    "release_count": 0,
    "max_snapshot_count": 3,
    "dropped_snapshots": 0
  }
}
```

### cpp / localhost_udp

- status: `passed`
- notes: canonical sender truth file plus C++ native UDP receiver verification report
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 54837 --count 24 --entity-count 3 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_cpp_net_matrix_gdeq2fmi/expected_session.json`
- recv_command: `/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build/fastdis_udp_burst_cpp 54837 --max-packets 24 --idle-polls 800 --json`

```json
{
  "schema": "fastdis.cpp_udp_burst_report.v1",
  "surface": "cpp",
  "mode": "localhost_udp",
  "packets_received": 24,
  "packets_parsed": 24,
  "malformed": 0,
  "entity_state": 24,
  "burst_count": 1,
  "snapshots_published": 3,
  "unique_entities": 3,
  "latest_entities": [
    {
      "site": 100,
      "application": 1,
      "entity": 2,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530741.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    },
    {
      "site": 100,
      "application": 1,
      "entity": 1,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530744.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    },
    {
      "site": 100,
      "application": 1,
      "entity": 0,
      "force_id": 1,
      "location_ecef_m": [
        -491891.748366,
        -5530747.361055,
        3128061.876302
      ],
      "orientation_dis_rad": [
        -0.088717,
        -0.0,
        -2.08671
      ]
    }
  ],
  "errors": []
}
```

### godot / live_udp

- status: `passed`
- notes: headless Godot localhost UDP smoke route using FastDisWorld; currently proven as a one-entity engine lane
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 65153 --count 24 --entity-count 1 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_godot_udp_rfilp2xo/expected_session.json`
- recv_command: `/Applications/Godot.app/Contents/MacOS/Godot --headless --path /tmp/fastdis_godot/repo/examples/godot/fastdis_demo --script /tmp/fastdis_godot/repo/examples/godot/fastdis_demo/scripts/run_udp_smoke.gd`

```json
{
  "errors": 0,
  "known_entities": 1,
  "mode": "live_udp",
  "moved_entities": [
    {
      "distance": 243.628509521484,
      "name": "EntityA",
      "position": [
        229.095458984375,
        82.2742538452148,
        -10.0531387329102
      ]
    }
  ],
  "moved_entity_count": 1,
  "packets_received": 24,
  "schema": "fastdis.godot_udp_smoke_report.v1",
  "surface": "godot"
}
```

### unreal / live_udp

- status: `passed`
- notes: Unreal 5.8 localhost UDP automation smoke route using UFastDisWorldSubsystem; currently proven as a one-entity engine lane
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 56425 --count 24 --entity-count 1 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_unreal_udp_5t0uo69_/expected_session.json`
- recv_command: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd /tmp/fastdis_unreal/repo/examples/unreal/FastDisOrientationVerification/FastDisOrientationVerification.uproject -ExecCmds=Automation RunTests FastDis.Network.LocalhostUdpMovesActors; Quit -unattended -nop4 -nosplash -NullRHI -NoSound -stdout -FullStdOutLogOutput -abslog=/tmp/fastdis_unreal/logs/orientation/FastDisOrientationVerification.log`

```json
{
  "packets": 24,
  "expected_packets": 24,
  "known_entities": 1,
  "moved_actors": 1
}
```
