from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastdis.lattice import MockLatticePublisher, MockPublishConfig, load_canonical_entities, mock_publish_report_to_dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "Publish canonical entities into the mock Lattice adapter.")
    parser.add_argument("fixture", type=Path, help="Path to a canonical entity fixture JSON file.")
    parser.add_argument("--reject-entity-key", action="append", default=[])
    parser.add_argument("--reject-stale", action="store_true")
    parser.add_argument("--fail-after", type=int)
    parser.add_argument("--timeout-after", type=int)
    parser.add_argument("--report-out", type=Path)
    parser.add_argument("--payload-log-out", type=Path)
    return parser.parse_args()

def main(argv: list[str] | None = None) -> int:
    _ = argv
    args = parse_args()
    entities = load_canonical_entities(args.fixture)
    publisher = MockLatticePublisher(
        MockPublishConfig(
            reject_entity_keys=frozenset(str(value) for value in args.reject_entity_key),
            reject_stale=bool(args.reject_stale),
            fail_after=args.fail_after,
            timeout_after=args.timeout_after,
        )
    )
    report = publisher.publish(entities)
    report_payload = mock_publish_report_to_dict(report)
    if args.report_out is not None:
        args.report_out.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    if args.payload_log_out is not None:
        args.payload_log_out.write_text(json.dumps(publisher.published_payloads, indent=2), encoding="utf-8")
    print(json.dumps(report_payload, indent=2))
    return 0 if not report.timed_out and report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
