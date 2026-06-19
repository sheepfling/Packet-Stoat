# Alpha 3 Network Send Matrix

- generated_at: `2026-06-19T20:42:37.446106+00:00`

| Surface | Mode | Status | Notes |
| --- | --- | --- | --- |
| python | localhost_udp_send | passed | truth-based sender verification route |
| c | localhost_udp_send | passed | truth-based sender verification route |
| cpp | localhost_udp_send | passed | truth-based sender verification route |

## Route Details

### python / localhost_udp_send

- status: `passed`
- send_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.send_entity --dst 127.0.0.1 --port 49677 --count 24 --entity-count 3 --entity 0 --truth-out /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_py_fxos_pul/expected_session.json`
- recv_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.recv --bind 127.0.0.1 --port 49677 --max-packets 24 --timeout 2.0 --surface send-matrix --verify /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_py_fxos_pul/expected_session.json`

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
  "surface": "send-matrix",
  "unique_entities": 3
}
```

### c / localhost_udp_send

- status: `passed`
- send_command: `/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build/fastdis_udp_send_c 127.0.0.1 50021 /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_c_789jiaso/expected_session.fastdispkt --json`
- recv_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.recv --bind 127.0.0.1 --port 50021 --max-packets 24 --timeout 2.0 --surface send-matrix --verify /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_c_789jiaso/expected_session.json`

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
  "surface": "send-matrix",
  "unique_entities": 3
}
```

### cpp / localhost_udp_send

- status: `passed`
- send_command: `/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/build/fastdis_udp_send_cpp 127.0.0.1 53297 /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_cpp_dy1xwm_s/expected_session.fastdispkt --json`
- recv_command: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m fastdis.tools.recv --bind 127.0.0.1 --port 53297 --max-packets 24 --timeout 2.0 --surface send-matrix --verify /var/folders/v8/h5gvd6pd54x7vhtkwqh5s34w0000gn/T/fastdis_send_matrix_cpp_dy1xwm_s/expected_session.json`

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
  "surface": "send-matrix",
  "unique_entities": 3
}
```
