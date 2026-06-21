# FastDIS Logging

FastDIS logging is generated from the standard-backed PDU coverage manifest.
Every DIS 6/7 PDU row has a descriptor, support level, endpoint behavior,
default severity, summary template, and JSONL-compatible event shape.

## Commands

```bash
fastdis logging check
fastdis logging check --json
```

The check is also part of `tools/dev_check.py`.

## Event Shape

Runtime packet logging uses `fastdis.log.pdu.v1`:

```json
{
  "schema": "fastdis.log.pdu.v1",
  "source": "unity",
  "stream_id": "udp:0.0.0.0:3001",
  "event_kind": "pdu.received",
  "level": "debug",
  "code": "FDIS0100_PACKET_RECEIVED",
  "version": 7,
  "exercise_id": 1,
  "pdu_type": 1,
  "pdu_name": "Entity State",
  "declared_length": 144,
  "packet_size": 144,
  "support_level": "production_supported",
  "endpoint_behavior": "entitystateevent",
  "diagnostics": []
}
```

Human summaries are compact:

```text
[FastDIS] rx DIS7 Entity State pdu=1 ex=1 len=144 behavior=entitystateevent
```

Malformed packets are explicit:

```text
[FastDIS] drop malformed packet reason=DIS PDU is shorter than the 12-byte header size=2
```

## Defaults

- Console logging should default to `info` and above.
- Monitor/ring-buffer logging should keep `debug` and above.
- JSONL file sinks should default to `warning` and above.
- Per-packet trace logging should remain opt-in for high-rate traffic.
- Unsupported known PDUs should log once and aggregate by PDU type.

## Coverage

See `docs/PDU_LOGGING_COVERAGE.md` for the generated 141-row matrix.
