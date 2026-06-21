# FastDIS Replay JSONL

`.fastdispkt` replays are length-prefixed binary packet streams. FastDIS converts them to newline-delimited JSON so large captures can be inspected, diffed, filtered, and rebuilt.

```bash
fastdis replay inspect capture.fastdispkt
fastdis replay to-json capture.fastdispkt --out capture.jsonl
fastdis replay from-json capture.jsonl --out rebuilt.fastdispkt
fastdis replay roundtrip capture.fastdispkt --out roundtrip.fastdispkt
fastdis replay diff capture.fastdispkt roundtrip.fastdispkt
```

Use `--raw-policy include` for lossless conversion. Each JSONL line is a `fastdis.packet.v1` record containing `packet.raw_base64`, `packet.size`, and `packet.sha256`.

Coverage meaning:

- Header JSON is available for every safely ingestible DIS packet.
- Lossless JSON round-trip works whenever `raw_base64` is present.
- Typed and semantic JSON are emitted through the generated PDU entry points.
- Editable JSON serializers are added explicitly by PDU type, starting with Entity State.
