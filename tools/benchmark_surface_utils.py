from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable


PREFERRED_CASE_ORDER = (
    "header_all_no_callback",
    "entity_state_1x10hz",
    "header_filter_90pct_reject",
)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def load_truth_from_route(root: Path, route: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    inline_truth = route.get("truth")
    if isinstance(inline_truth, dict):
        truth_file = route.get("truth_file")
        truth_label = None
        if isinstance(truth_file, str) and truth_file:
            truth_path = Path(truth_file).expanduser()
            truth_label = display_path(root, truth_path if truth_path.is_absolute() else (root / truth_path).resolve())
        return inline_truth, truth_label
    truth_file = route.get("truth_file")
    if not isinstance(truth_file, str) or not truth_file:
        return {}, None
    truth_path = Path(truth_file).expanduser()
    if not truth_path.is_absolute():
        truth_path = (root / truth_path).resolve()
    if not truth_path.exists():
        return {}, display_path(root, truth_path)
    loaded = load_json(truth_path)
    return (loaded or {}), display_path(root, truth_path)


def sorted_fastdis_rows(
    fastdis_payload: dict[str, Any] | None,
    *,
    preferred_order: tuple[str, ...] = PREFERRED_CASE_ORDER,
) -> list[dict[str, Any]]:
    if fastdis_payload is None:
        return []
    native_rows = (fastdis_payload.get("native") or {}).get("results") or []
    if not isinstance(native_rows, list):
        return []
    preferred_rank = {case: index for index, case in enumerate(preferred_order)}
    filtered = [row for row in native_rows if isinstance(row, dict) and isinstance(row.get("case"), str)]
    return sorted(
        filtered,
        key=lambda row: (
            preferred_rank.get(str(row.get("case")), len(preferred_rank)),
            str(row.get("case", "")),
        ),
    )


def build_scaffold_rows(
    fastdis_payload: dict[str, Any] | None,
    *,
    limit_cases: int,
    row_builder: Callable[[dict[str, Any]], dict[str, Any] | None],
    default_row: dict[str, Any],
    preferred_order: tuple[str, ...] = PREFERRED_CASE_ORDER,
) -> list[dict[str, Any]]:
    rows = sorted_fastdis_rows(fastdis_payload, preferred_order=preferred_order)
    if not rows:
        return [default_row]
    scaffolded: list[dict[str, Any]] = []
    for row in rows[: max(1, limit_cases)]:
        built = row_builder(row)
        if built is not None:
            scaffolded.append(built)
    return scaffolded or [default_row]


def report_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "latency_rows": sum(1 for row in rows if row["metrics"].get("main_thread_apply_ms") is not None),
        "runtime_metric_rows": sum(1 for row in rows if row["metrics"].get("runtime_elapsed_seconds") is not None),
        "truth_rows": sum(1 for row in rows if row["truth"].get("final_truth_match") is not None),
    }
