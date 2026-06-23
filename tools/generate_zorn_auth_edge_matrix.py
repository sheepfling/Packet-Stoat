#!/usr/bin/env python3
"""Generate an auth edge matrix from the current Zorn lifecycle probe."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_JSON_PATH = ROOT / "generated" / "zorn_auth_edge_matrix.json"
DEFAULT_MD_PATH = ROOT / "docs" / "ZORN_AUTH_EDGE_MATRIX.md"
DEFAULT_REPORT_ROOT = ROOT / "build" / "verification_reports" / "alpha5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_PATH)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def _load_report(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _check_lookup(report: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    if report is None:
        return lookup
    for item in report.get("checks", []):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str):
            lookup[name] = {
                "status": str(item.get("status", "unknown")),
                "detail": str(item.get("detail", "")),
            }
    return lookup


def _first_check(lookup: dict[str, dict[str, str]], *names: str) -> dict[str, str] | None:
    for name in names:
        check = lookup.get(name)
        if check is not None:
            return check
    return None


def _row(
    *,
    surface: str,
    lane: str,
    transport: str,
    expected: str,
    check: dict[str, str] | None,
    note: str,
) -> dict[str, Any]:
    status = check["status"] if check else "missing"
    return {
        "surface": surface,
        "lane": lane,
        "transport": transport,
        "expected": expected,
        "status": status,
        "evidence": check.get("detail", "") if check else "",
        "note": note,
        "is_gap": status != "passed",
    }


def build_matrix(report_root: Path) -> dict[str, Any]:
    config = load_lattice_backend_config()
    auth_report = (
        _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_4" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_3" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle_alpha1_2" / "zorn_auth_lifecycle_probe_report.json")
        or _load_report(report_root / "lattice_zorn_auth_lifecycle" / "zorn_auth_lifecycle_probe_report.json")
    )
    checks = _check_lookup(auth_report)
    transport = config.transport
    zorn_tag = config.tag

    rows = [
        _row(
            surface="rest.static.x_api_key",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "rest_x_api_key_accepted", "rest_static_x_api_key_accepted"),
            note="Keep this edge on Zorn; the live lane can stay bearer-only or environment-token only.",
        ),
        _row(
            surface="rest.sandbox.required",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted with sandbox header, rejected without it",
            check=_first_check(checks, "rest_missing_sandbox_header_rejected"),
            note="This is the setup-heavy path that should stay explicit in Zorn probes.",
        ),
        _row(
            surface="rest.sandbox.bearer_only",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="rejected",
            check=_first_check(checks, "rest_sandbox_header_without_bearer_rejected"),
            note="Documents that sandbox headers do not replace bearer auth.",
        ),
        _row(
            surface="rest.auth_mode.none",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted without headers",
            check=_first_check(checks, "rest_auth_mode_none_accepts_without_headers"),
            note="Useful for local probe scaffolding, not for live Lattice parity.",
        ),
        _row(
            surface="rest.oauth.client_credentials",
            lane="zorn-and-live",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "rest_oauth_client_credentials"),
            note="This remains the canonical setup for real routed auth.",
        ),
        _row(
            surface="rest.oauth.issued_token",
            lane="zorn-and-live",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "rest_oauth_issued_token_accepted", "rest_oauth_issued_token"),
            note="Validates the token issued by Zorn's OAuth dev route.",
        ),
        _row(
            surface="grpc.static.x_api_key",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "grpc_x_api_key_accepted", "grpc_static_x_api_key_accepted"),
            note="Keep for probe setup parity; the live lane should prefer official bearer flows.",
        ),
        _row(
            surface="grpc.sandbox.authorization",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "grpc_sandbox_header_as_bearer_accepted"),
            note="Zorn accepts sandbox auth metadata as bearer transport; live routes may not expose this shape.",
        ),
        _row(
            surface="grpc.auth_mode.none",
            lane="zorn-only-auth-setup",
            transport=transport,
            expected="accepted without headers",
            check=_first_check(checks, "grpc_auth_mode_none_accepts_without_headers"),
            note="Useful for local setup and fault injection only.",
        ),
        _row(
            surface="grpc.oauth.issued_token",
            lane="zorn-and-live",
            transport=transport,
            expected="accepted",
            check=_first_check(checks, "grpc_oauth_issued_token_accepted", "grpc_oauth_issued_token"),
            note="Keeps the official OAuth-backed gRPC route visible.",
        ),
    ]

    gaps = [
        {
            "surface": "auth_lifecycle",
            "details": list(auth_report.get("gaps", [])) if auth_report else ["auth probe report missing"],
        }
    ]
    summary = {
        "passed": sum(1 for row in rows if row["status"] == "passed"),
        "gap": sum(1 for row in rows if row["status"] != "passed"),
        "total": len(rows),
    }
    return {
        "schema": "fastdis.zorn.auth_edge_matrix.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": transport,
        "zorn_tag": zorn_tag,
        "report_root": str(report_root),
        "rows": rows,
        "gaps": gaps,
        "summary": summary,
        "live_lattice_policy": "skip setup-heavy auth permutations; prefer environment-token and the minimal credential-gated route shape.",
    }


def _render_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Zorn Auth Edge Matrix",
        "",
        f"- backend: `{matrix.get('backend')}`",
        f"- transport: `{matrix.get('transport')}`",
        f"- zorn_tag: `{matrix.get('zorn_tag')}`",
        "",
        "## Policy",
        "",
        f"{matrix.get('live_lattice_policy', '')}",
        "",
        "## Rows",
        "",
        "| Surface | Lane | Expected | Status | Evidence | Note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix.get("rows", []):
        lines.append(
            "| `{surface}` | `{lane}` | `{expected}` | `{status}` | {evidence} | {note} |".format(
                surface=row.get("surface", ""),
                lane=row.get("lane", ""),
                expected=row.get("expected", ""),
                status=row.get("status", ""),
                evidence=row.get("evidence", "").replace("|", r"\|") or "",
                note=row.get("note", "").replace("|", r"\|"),
            )
        )
    lines.extend(["", "## Gaps", ""])
    for gap in matrix.get("gaps", []):
        details = gap.get("details", [])
        if details:
            lines.append(f"- `{gap.get('surface')}`: {details[0]}")
        else:
            lines.append(f"- `{gap.get('surface')}`")
    lines.extend(["", "## Summary", ""])
    summary = matrix.get("summary", {})
    lines.append(f"- passed: `{summary.get('passed', 0)}`")
    lines.append(f"- gap: `{summary.get('gap', 0)}`")
    lines.append(f"- total: `{summary.get('total', 0)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    matrix = build_matrix(args.report_root)
    json_payload = json.dumps(matrix, indent=2, sort_keys=True) + "\n"
    md_payload = _render_markdown(matrix)
    if args.check:
        current_json = json.loads(args.json_out.read_text(encoding="utf-8")) if args.json_out.is_file() else None
        current_md = args.md_out.read_text(encoding="utf-8") if args.md_out.is_file() else None
        normalized = dict(matrix)
        normalized.pop("generated_at", None)
        if current_json is None:
            print("zorn auth edge matrix outputs are stale")
            return 1
        current_json = dict(current_json)
        current_json.pop("generated_at", None)
        if current_json != normalized or current_md != md_payload:
            print("zorn auth edge matrix outputs are stale")
            return 1
        print("zorn auth edge matrix outputs are up to date")
        return 0
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_payload, encoding="utf-8")
    args.md_out.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"json": str(args.json_out), "markdown": str(args.md_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
