"""Deterministic simulation regression comparison utilities."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import json
import math
from pathlib import Path
import shutil
from typing import Any


SCHEMA = "fastdis.simtest.report.v1"
DEFAULT_TOLERANCES = {
    "position_m": 0.01,
    "orientation_deg": 0.05,
    "velocity_mps": 0.02,
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    delta: float | None = None
    tolerance: float | None = None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# FastDIS Simtest Report",
        "",
        f"- status: `{report['status']}`",
        f"- scenario: `{report['scenario'].get('name', 'unnamed')}`",
        f"- run: `{report['run_dir']}`",
        f"- baseline: `{report['baseline_dir']}`",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "| check | status | delta | tolerance | detail |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for check in report["checks"]:
        delta = "" if check.get("delta") is None else f"{check['delta']:.6g}"
        tolerance = "" if check.get("tolerance") is None else f"{check['tolerance']:.6g}"
        lines.append(f"| `{check['name']}` | `{check['status']}` | {delta} | {tolerance} | {check['detail']} |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def _scenario(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "name": "default",
            "tolerances": DEFAULT_TOLERANCES,
            "crops": {},
        }
    payload = _load_json(path)
    tolerances = dict(DEFAULT_TOLERANCES)
    tolerances.update(payload.get("tolerances", {}))
    payload["tolerances"] = tolerances
    payload.setdefault("crops", {})
    return payload


def _meta_files(root: Path) -> dict[str, Path]:
    return {path.stem.removeprefix("meta_"): path for path in sorted(root.glob("meta_*.json"))}


def _entities(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entities = payload.get("entities", [])
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(entities, list):
        return result
    for entity in entities:
        if isinstance(entity, dict) and "id" in entity:
            result[str(entity["id"])] = entity
    return result


def _vector(entity: dict[str, Any], *names: str) -> list[float] | None:
    for name in names:
        value = entity.get(name)
        if isinstance(value, list | tuple) and len(value) >= 3:
            return [float(value[0]), float(value[1]), float(value[2])]
        if isinstance(value, dict):
            keys = ("x", "y", "z")
            if all(key in value for key in keys):
                return [float(value[key]) for key in keys]
    return None


def _max_abs_delta(a: list[float], b: list[float]) -> float:
    return max(abs(left - right) for left, right in zip(a, b))


def _quat_angle_deg(a: list[float], b: list[float]) -> float:
    if len(a) < 4 or len(b) < 4:
        return _max_abs_delta(a[:3], b[:3])
    dot = abs(sum(left * right for left, right in zip(a[:4], b[:4])))
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(2.0 * math.acos(dot))


def _compare_metadata(run_dir: Path, baseline_dir: Path, scenario: dict[str, Any]) -> list[CheckResult]:
    run_meta = _meta_files(run_dir)
    baseline_meta = _meta_files(baseline_dir)
    checks: list[CheckResult] = []
    missing = sorted(set(baseline_meta) - set(run_meta))
    extra = sorted(set(run_meta) - set(baseline_meta))
    checks.append(
        CheckResult(
            "metadata.file_set",
            "pass" if not missing and not extra else "fail",
            f"missing={missing or []} extra={extra or []}",
        )
    )

    tolerances = scenario["tolerances"]
    for stamp in sorted(set(run_meta) & set(baseline_meta)):
        run_payload = _load_json(run_meta[stamp])
        base_payload = _load_json(baseline_meta[stamp])
        run_entities = _entities(run_payload)
        base_entities = _entities(base_payload)
        missing_ids = sorted(set(base_entities) - set(run_entities))
        extra_ids = sorted(set(run_entities) - set(base_entities))
        checks.append(
            CheckResult(
                f"metadata.{stamp}.entity_ids",
                "pass" if not missing_ids and not extra_ids else "fail",
                f"missing={missing_ids or []} extra={extra_ids or []}",
            )
        )
        for entity_id in sorted(set(run_entities) & set(base_entities)):
            run_entity = run_entities[entity_id]
            base_entity = base_entities[entity_id]
            pairs = [
                ("position_m", tolerances["position_m"], _vector(run_entity, "pos", "position", "position_m"), _vector(base_entity, "pos", "position", "position_m")),
                ("velocity_mps", tolerances["velocity_mps"], _vector(run_entity, "vel", "velocity", "velocity_mps"), _vector(base_entity, "vel", "velocity", "velocity_mps")),
                ("orientation_deg", tolerances["orientation_deg"], _vector(run_entity, "rot", "rotation", "orientation", "orientation_quat"), _vector(base_entity, "rot", "rotation", "orientation", "orientation_quat")),
            ]
            for field, tolerance, run_vec, base_vec in pairs:
                if run_vec is None and base_vec is None:
                    continue
                if run_vec is None or base_vec is None:
                    checks.append(CheckResult(f"metadata.{stamp}.{entity_id}.{field}", "fail", "field missing on one side"))
                    continue
                delta = _quat_angle_deg(run_vec, base_vec) if field == "orientation_deg" else _max_abs_delta(run_vec, base_vec)
                checks.append(
                    CheckResult(
                        f"metadata.{stamp}.{entity_id}.{field}",
                        "pass" if delta <= float(tolerance) else "fail",
                        "within tolerance" if delta <= float(tolerance) else "outside tolerance",
                        delta=delta,
                        tolerance=float(tolerance),
                    )
                )
    return checks


def _load_image(path: Path) -> Any:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on optional runtime dependency.
        raise SystemExit("Pillow is required for crop comparisons. Install fastdis[dev].") from exc
    return Image.open(path).convert("RGB")


def _crop_l1(path_a: Path, path_b: Path) -> float:
    with _load_image(path_a) as image_a, _load_image(path_b) as image_b:
        if image_a.size != image_b.size:
            return float("inf")
        pixels_a = list(image_a.getdata())
        pixels_b = list(image_b.getdata())
        total = len(pixels_a) * 3
        return sum(abs(left - right) for px_a, px_b in zip(pixels_a, pixels_b) for left, right in zip(px_a, px_b)) / total


def _compare_crops(run_dir: Path, baseline_dir: Path, scenario: dict[str, Any]) -> list[CheckResult]:
    checks: list[CheckResult] = []
    crop_specs = scenario.get("crops", {})
    baseline_crops = baseline_dir / "crops"
    run_crops = run_dir / "crops"
    if not crop_specs and not baseline_crops.exists() and not run_crops.exists():
        return checks
    for name, spec in sorted(crop_specs.items()):
        pattern = f"{name}_*.png"
        for base_path in sorted(baseline_crops.glob(pattern)):
            run_path = run_crops / base_path.name
            if not run_path.is_file():
                checks.append(CheckResult(f"crop.{base_path.stem}", "fail", "missing run crop"))
                continue
            metric = str(spec.get("metric", "l1"))
            if metric != "l1":
                checks.append(CheckResult(f"crop.{base_path.stem}", "fail", f"unsupported metric: {metric}"))
                continue
            delta = _crop_l1(run_path, base_path)
            tolerance = float(spec.get("max", 2.0))
            checks.append(
                CheckResult(
                    f"crop.{base_path.stem}.l1",
                    "pass" if delta <= tolerance else "fail",
                    "within tolerance" if delta <= tolerance else "outside tolerance",
                    delta=delta,
                    tolerance=tolerance,
                )
            )
    return checks


def compare(run_dir: Path, baseline_dir: Path, scenario_path: Path | None, report_path: Path | None) -> dict[str, Any]:
    scenario = _scenario(scenario_path)
    checks = [
        *_compare_metadata(run_dir, baseline_dir, scenario),
        *_compare_crops(run_dir, baseline_dir, scenario),
    ]
    failures = [check for check in checks if check.status != "pass"]
    report = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failures else "fail",
        "scenario": scenario,
        "run_dir": _rel(run_dir),
        "baseline_dir": _rel(baseline_dir),
        "summary": {
            "checks": len(checks),
            "passed": len(checks) - len(failures),
            "failed": len(failures),
        },
        "checks": [check.__dict__ for check in checks],
    }
    if report_path is not None:
        _write_json(report_path.with_suffix(".json"), report)
        _write_markdown(report_path.with_suffix(".md"), report)
    return report


def bless(run_dir: Path, baseline_dir: Path) -> dict[str, Any]:
    if baseline_dir.exists():
        shutil.rmtree(baseline_dir)
    shutil.copytree(run_dir, baseline_dir)
    return {
        "schema": "fastdis.simtest.bless.v1",
        "status": "pass",
        "run_dir": _rel(run_dir),
        "baseline_dir": _rel(baseline_dir),
    }


def inspect(root: Path) -> dict[str, Any]:
    meta = _meta_files(root)
    crops = sorted((root / "crops").glob("*.png")) if (root / "crops").exists() else []
    return {
        "schema": "fastdis.simtest.inspect.v1",
        "root": _rel(root),
        "meta_count": len(meta),
        "meta_stamps": sorted(meta),
        "crop_count": len(crops),
        "crops": [_rel(path) for path in crops],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare", help="Compare a run directory to a baseline")
    compare_parser.add_argument("run_dir", type=Path)
    compare_parser.add_argument("baseline_dir", type=Path)
    compare_parser.add_argument("--scenario", type=Path)
    compare_parser.add_argument("--report", type=Path, help="Report path prefix or .json/.md path")

    bless_parser = subparsers.add_parser("bless", help="Copy a known-good run into a baseline directory")
    bless_parser.add_argument("run_dir", type=Path)
    bless_parser.add_argument("baseline_dir", type=Path)

    inspect_parser = subparsers.add_parser("inspect", help="Summarize simtest artifacts in a run or baseline directory")
    inspect_parser.add_argument("root", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "compare":
        report_path = args.report
        if report_path is not None and report_path.suffix in {".json", ".md"}:
            report_path = report_path.with_suffix("")
        report = compare(args.run_dir, args.baseline_dir, args.scenario, report_path)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    if args.command == "bless":
        print(json.dumps(bless(args.run_dir, args.baseline_dir), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect":
        print(json.dumps(inspect(args.root), indent=2, sort_keys=True))
        return 0
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
