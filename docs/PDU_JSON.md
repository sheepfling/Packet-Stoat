# FastDIS PDU JSON

FastDIS can expand a single binary DIS PDU into JSON for inspection, fixture generation, and lossless round-trip testing.

```bash
fastdis pdu inspect packet.bin
fastdis pdu to-json packet.bin --out packet.json --pretty
fastdis pdu from-json packet.json --out rebuilt.bin
```

The default JSON schema is `fastdis.packet.v1`. It includes the parsed DIS header, support metadata, diagnostics, semantic/typed observations when available, and `packet.raw_base64` for bit-exact reconstruction.

Editable Entity State JSON is available for the supported DIS 7 Entity State fixed layout:

```bash
fastdis pdu to-json entity_state.bin --editable-entity-state --out entity_state.json --pretty
fastdis pdu from-json entity_state.json --no-prefer-raw --out rebuilt_entity_state.bin
```

Raw-preserving JSON is the compatibility baseline for every PDU. Editable structured serialization is intentionally added per PDU as semantic support matures.
