#!/usr/bin/env python3
"""Check Unity GRILL parity gates against a machine-readable matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "docs" / "research" / "unity_grill_parity.yaml"
VALID_STATUSES = {
    "missing",
    "scaffolded",
    "implemented",
    "native_verified",
    "editmode_verified",
    "playmode_verified",
    "network_verified",
    "published",
}
VERIFIED_STATUSES = {"native_verified", "editmode_verified", "playmode_verified", "network_verified", "published"}
REQUIRED_EVIDENCE_FIELDS = ("implementation", "tests", "verification", "samples", "docs")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--milestone", required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def load_structured(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Could not parse {path} as JSON and PyYAML is unavailable") from exc
        payload = yaml.safe_load(text)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Expected mapping at top level in {path}")
        return payload


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def path_exists(ref: str) -> bool:
    path = Path(ref)
    if not path.is_absolute():
        path = ROOT / ref
    return path.exists()


def feature_required_for(feature: dict[str, Any]) -> list[str]:
    return as_list(feature.get("required_for"))


def feature_bucket(status: str, field_checks: dict[str, bool]) -> str:
    if status == "missing":
        return "missing"
    if status == "scaffolded":
        return "scaffolded"
    if status in VERIFIED_STATUSES and all(field_checks.values()):
        return "verified"
    return "implemented"


def build_feature_row(name: str, feature: dict[str, Any]) -> dict[str, Any]:
    status = str(feature.get("fastdis", "missing"))
    if status not in VALID_STATUSES:
        raise RuntimeError(f"Feature {name} has invalid fastdis status: {status}")

    field_refs = {field: as_list(feature.get(field)) for field in REQUIRED_EVIDENCE_FIELDS}
    field_checks = {
        field: bool(refs) and all(path_exists(ref) for ref in refs)
        for field, refs in field_refs.items()
    }
    missing_fields = [field for field, ok in field_checks.items() if not ok]
    bucket = feature_bucket(status, field_checks)
    return {
        "name": name,
        "title": str(feature.get("title", name)),
        "summary": str(feature.get("summary", "")),
        "grill": str(feature.get("grill", "unverified")),
        "fastdis": status,
        "bucket": bucket,
        "required_for": feature_required_for(feature),
        "field_checks": field_checks,
        "missing_fields": missing_fields,
    }


def build_report(matrix_path: Path, milestone: str) -> dict[str, Any]:
    payload = load_structured(matrix_path)
    features = payload.get("features")
    if not isinstance(features, dict):
        raise RuntimeError(f"{matrix_path} is missing a top-level features map")

    milestone_rows = []
    for name, feature in features.items():
        if not isinstance(feature, dict):
            raise RuntimeError(f"Feature {name} in {matrix_path} is not a mapping")
        if milestone not in feature_required_for(feature):
            continue
        milestone_rows.append(build_feature_row(name, feature))

    milestone_rows.sort(key=lambda row: row["name"])
    counts = {"verified": 0, "implemented": 0, "scaffolded": 0, "missing": 0}
    for row in milestone_rows:
        counts[row["bucket"]] += 1

    failures = [row for row in milestone_rows if row["bucket"] != "verified"]
    return {
        "schema": "fastdis.unity_grill_parity_check.v1",
        "matrix": str(matrix_path),
        "milestone": milestone,
        "required": len(milestone_rows),
        "verified": counts["verified"],
        "implemented": counts["implemented"],
        "scaffolded": counts["scaffolded"],
        "missing": counts["missing"],
        "status": "PASS" if not failures else "FAIL",
        "features": milestone_rows,
        "failures": failures,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "Unity GRILL parity",
        f"Milestone: {report['milestone']}",
        f"Required: {report['required']}",
        f"Verified: {report['verified']}",
        f"Implemented: {report['implemented']}",
        f"Scaffolded: {report['scaffolded']}",
        f"Missing: {report['missing']}",
        f"Milestone status: {report['status']}",
    ]
    failures = report.get("failures") or []
    if failures:
        lines.append("")
        lines.append("Blocking rows:")
        for row in failures:
            detail = row["bucket"]
            if row["missing_fields"]:
                detail += f"; missing_evidence={','.join(row['missing_fields'])}"
            lines.append(f"- {row['name']}: {detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(Path(args.matrix), args.milestone)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
