# SISO Enum Coverage

FastDIS treats SISO-REF-010 as a versioned data dependency for labels and
mapping hints. Binary packet parsing preserves numeric values first; labels are
attached when the local enum catalog knows them.

Current Alpha5 scope:

- PDU type labels from the 141-row DIS 6/7 standard backbone.
- Protocol family labels for routing/logging.
- Force ID core labels for overlays, filters, and Lattice Lab metadata.
- Dead reckoning algorithm labels for dispatch and diagnostics.
- Entity Type seven-tuple description with progressive fallback keys.
- Unknown/local values preserved as `Unknown(value)`.

Full SISO-REF-010 import is still tracked by `standards/registry.yaml` and
`docs/STANDARDS_STATUS.md`; this file documents the operator-facing API that is
available now.

## Commands

Check enum coverage:

```bash
fastdis enums check
```

Lookup a PDU type:

```bash
fastdis enums lookup pdu_type 1 --version 7
```

Lookup core fields:

```bash
fastdis enums lookup force_id 1
fastdis enums lookup dead_reckoning_algorithm 4
fastdis enums lookup protocol_family 1
```

Describe an entity type:

```bash
fastdis enums entity-type 1 2 225 1 1 3 0
```

Describe header fields:

```bash
fastdis enums describe-header --version 7 --pdu-type 1 --protocol-family 1 --force-id 1
```

## Unknown Value Policy

FastDIS does not reject a packet because an enum value is not in the local
catalog. Every enum lookup returns:

```json
{
  "family": "force_id",
  "value": 99,
  "label": "Unknown(99)",
  "known": false,
  "source": "siso-ref-010-v32"
}
```

That behavior is intentional. SISO-REF-010 evolves, local ranges exist, and
SISO-REF-010.1 describes implicit entity-type behavior. FastDIS preserves the
numeric value and makes the uncertainty visible in logs and reports.

## Entity Type Fallback

Entity types are represented as:

```text
kind.domain.country.category.subcategory.specific.extra
```

FastDIS returns exact and progressive fallback keys:

```text
1.2.225.1.1.3.0
1.2.225.1.1.3.*
1.2.225.1.1.*
1.2.225.1.*
1.2.225.*
1.2.*
```

Engine adapters should use these keys for actor/prefab mapping so a scenario
does not require every platform variant to be explicitly enumerated.
