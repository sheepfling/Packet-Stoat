"""Check generated FastDIS PDU logging coverage."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from fastdis.pdu_logging import DIAGNOSTIC_CODES, PDU_LOG_DESCRIPTORS


def coverage_payload() -> dict[str, object]:
    dis6 = sum(1 for item in PDU_LOG_DESCRIPTORS if item.version == 6)
    dis7 = sum(1 for item in PDU_LOG_DESCRIPTORS if item.version == 7)
    missing = [
        item
        for item in PDU_LOG_DESCRIPTORS
        if not item.summary_template
        or not item.default_log_level
        or not item.endpoint_unreal
        or not item.endpoint_godot
        or not item.endpoint_unity
    ]
    return {
        "schema": "fastdis.logging_check.v1",
        "overall_status": "pass" if dis6 == 68 and dis7 == 73 and not missing else "fail",
        "summary": {
            "dis6_descriptors": dis6,
            "dis7_descriptors": dis7,
            "total_descriptors": len(PDU_LOG_DESCRIPTORS),
            "unreal_descriptors": sum(1 for item in PDU_LOG_DESCRIPTORS if item.endpoint_unreal),
            "godot_descriptors": sum(1 for item in PDU_LOG_DESCRIPTORS if item.endpoint_godot),
            "unity_descriptors": sum(1 for item in PDU_LOG_DESCRIPTORS if item.endpoint_unity),
            "summary_templates": sum(1 for item in PDU_LOG_DESCRIPTORS if item.summary_template),
            "diagnostic_codes": len(DIAGNOSTIC_CODES),
        },
        "issues": [
            {
                "version": item.version,
                "pdu_type": item.pdu_type,
                "name": item.canonical_name,
                "reason": "missing descriptor field required for logging compliance",
            }
            for item in missing
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    payload = coverage_payload()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        summary = payload["summary"]
        assert isinstance(summary, dict)
        print("FastDIS PDU logging coverage")
        print(f"  DIS6 descriptors: {summary['dis6_descriptors']} / 68")
        print(f"  DIS7 descriptors: {summary['dis7_descriptors']} / 73")
        print(f"  Unreal descriptors: {summary['unreal_descriptors']} / 141")
        print(f"  Godot descriptors: {summary['godot_descriptors']} / 141")
        print(f"  Unity descriptors: {summary['unity_descriptors']} / 141")
        print(f"  Summary templates: {summary['summary_templates']} / 141")
        print(f"  Diagnostic codes: {summary['diagnostic_codes']}")
        print(f"  status: {payload['overall_status']}")
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
