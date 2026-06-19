# Alpha 3 Network Ingest Matrix

- generated_at: `2026-06-19T18:25:30.439604+00:00`

| Surface | Mode | Status | Notes |
| --- | --- | --- | --- |
| python | localhost_udp | passed | canonical sender truth file plus Python receiver verification report |
| godot | live_udp | pending | replay-driven demo route exists, but live UDP engine ingest verification is not yet wired |
| unreal | live_udp | pending | replay/demo harness exists, but live UDP plugin ingest verification is not yet wired |
| cpp | localhost_udp | pending | UDP burst example exists; canonical truth-file verification contract not yet implemented for native CLI output |
| c | localhost_udp | pending | no canonical C receiver verification tool exists yet |

## Route Details

### python / localhost_udp

- status: `passed`
- notes: canonical sender truth file plus Python receiver verification report
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 51742 --count 24 --entity-count 3 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_net_matrix_d3saol3q/expected_session.json`
- recv_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.recv --bind 127.0.0.1 --port 51742 --max-packets 24 --timeout 2.0 --surface python --verify /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_net_matrix_d3saol3q/expected_session.json`

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

### godot / live_udp

- status: `pending`
- notes: replay-driven demo route exists, but live UDP engine ingest verification is not yet wired

### unreal / live_udp

- status: `pending`
- notes: replay/demo harness exists, but live UDP plugin ingest verification is not yet wired

### cpp / localhost_udp

- status: `pending`
- notes: UDP burst example exists; canonical truth-file verification contract not yet implemented for native CLI output

### c / localhost_udp

- status: `pending`
- notes: no canonical C receiver verification tool exists yet
