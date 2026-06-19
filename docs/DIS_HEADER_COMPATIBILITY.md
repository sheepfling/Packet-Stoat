# DIS 6 / DIS 7 Header Compatibility

fastdis keeps the public boundary as a C ABI, but its DIS 6 and DIS 7 header
semantics are cross-checked against Open-DIS as a practical reference model.

Open-DIS is not exposed through the fastdis ABI. It is used to confirm binary
field intent:

- Open-DIS DIS6 `Pdu` includes protocol version, exercise ID, PDU type,
  protocol family, timestamp, length, and a 16-bit padding field.
- Open-DIS DIS7 splits the common header into `PduSuperclass` plus `Pdu`; the
  DIS7 `Pdu` adds a one-byte PDU Status field and a one-byte padding field.
- Open-DIS DIS7 also represents PDU Status as a byte-sized bit-field record.

fastdis maps those forms into one stable POD struct:

```c
typedef struct fastdis_header_s {
    uint8_t version;
    uint8_t exercise_id;
    uint8_t pdu_type;
    uint8_t protocol_family;
    uint32_t timestamp;
    uint16_t length;
    int16_t status;
    uint16_t padding;
} fastdis_header_t;
```

Interpretation:

| Protocol version | Byte 10 | Byte 11 | `status` | `padding` |
|---|---:|---:|---:|---:|
| DIS 6 and earlier | padding high byte | padding low byte | `FASTDIS_HEADER_STATUS_UNAVAILABLE` | 16-bit big-endian padding |
| DIS 7 and later | PDU Status | padding octet | PDU Status byte | padding octet |

Use the helpers instead of manually checking tuple offsets:

```c
if (fastdis_header_has_pdu_status(&header)) {
    uint8_t status = fastdis_header_pdu_status(&header);
    uint8_t padding = fastdis_header_padding_octet(&header);
} else {
    uint16_t padding = fastdis_header_legacy_padding(&header);
}
```

C++ wrappers mirror the same helpers:

```cpp
if (fastdis::header_has_pdu_status(header)) {
    auto status = fastdis::header_pdu_status(header);
}
```

Python named headers expose properties:

```python
header = fastdis.parse_header(packet)
header.has_pdu_status
header.pdu_status
header.padding_octet
header.legacy_padding
```

The tuple API remains unchanged for hot paths:

```text
(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, padding)
```

## References

- `open-dis/open-dis-cpp/src/dis6/Pdu.h`
- `open-dis/open-dis-cpp/src/dis7/PduSuperclass.h`
- `open-dis/open-dis-cpp/src/dis7/Pdu.h`
- `open-dis/open-dis-cpp/src/dis7/PduStatus.h`
- `open-dis/open-dis-cpp/src/dis6/EntityStatePdu.h`
- `open-dis/open-dis-cpp/src/dis7/EntityStatePdu.h`
