# JSON Round-Trip Guarantees

FastDIS JSON has two levels:

- `fastdis.packet.v1`: lossless envelope JSON. If `packet.raw_base64` is present, `fastdis pdu from-json` and `fastdis replay from-json` rebuild the original packet bytes after validating size and SHA-256.
- `fastdis.pdu.entity_state.v1`: editable Entity State JSON. This rebuilds a semantically equivalent DIS 7 Entity State packet from structured fields, but it is not intended to preserve unmodeled bytes.

The release gate for the first JSON tranche is bit-exact replay round-trip through `fastdis.packet.v1`.
