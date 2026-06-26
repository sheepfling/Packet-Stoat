#!/usr/bin/env python3
"""Adopt a Unity install-smoke report from another host into the local report set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import run_unity_install_smoke


VALID_HOSTS = ("macos", "windows", "linux")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=VALID_HOSTS, help="Host label for the adopted report")
    parser.add_argument("--report", required=True, type=Path, help="Path to a unity_install_smoke.json file from another host")
    parser.add_argument("--log", type=Path, help="Optional companion Unity log to copy beside the adopted report")
    parser.add_argument("--out-dir", type=Path, default=run_unity_install_smoke.DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def load_report(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise SystemExit(f"report not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"report is not valid JSON: {path}: {exc}") from exc


def validate_report(report: dict[str, object], source: Path, host: str) -> dict[str, object]:
    schema = str(report.get("schema") or "")
    if schema != "fastdis.unity_install_smoke.v1":
        raise SystemExit(f"unexpected schema in {source}: {schema or 'missing'}")
    status = str(report.get("status") or "")
    if status not in {"pass", "fail", "skip"}:
        raise SystemExit(f"unexpected status in {source}: {status or 'missing'}")
    adopted = dict(report)
    adopted["host_platform"] = host
    adopted["adopted_from"] = str(source.resolve())
    return adopted


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = validate_report(load_report(args.report), args.report, args.host)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    host_json_path = args.out_dir / f"unity_install_smoke_{args.host}.json"
    host_md_path = args.out_dir / f"unity_install_smoke_{args.host}.md"

    if args.log is not None:
        if not args.log.is_file():
            raise SystemExit(f"log not found: {args.log}")
        adopted_log_path = args.out_dir / f"unity_install_smoke_{args.host}.log"
        shutil.copyfile(args.log, adopted_log_path)
        report["log"] = str(adopted_log_path)

    host_json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    host_md_path.write_text(run_unity_install_smoke.render_markdown(report), encoding="utf-8")
    print(f"JSON: {host_json_path}")
    print(f"Markdown: {host_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
