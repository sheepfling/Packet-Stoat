"""Compatibility helpers for local report and artifact path layout shifts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

_ROOT_MAPPINGS = (
    (ROOT / "artifacts" / "reports", ROOT / "build" / "reports"),
    (ROOT / "artifacts" / "benchmark_results", ROOT / "build" / "benchmark_results"),
    (ROOT / "artifacts" / "release_artifacts", ROOT / "build" / "release_artifacts"),
    (ROOT / "artifacts" / "verification_reports", ROOT / "build" / "verification_reports"),
    (ROOT / "artifacts" / "dist", ROOT / "build" / "dist"),
    (ROOT / "artifacts" / "reports", ROOT / "benchmark_reports"),
    (ROOT / "artifacts" / "benchmark_results", ROOT / "benchmark_results"),
    (ROOT / "artifacts" / "release_artifacts", ROOT / "release_artifacts"),
    (ROOT / "artifacts" / "verification_reports", ROOT / "verification_reports"),
    (ROOT / "artifacts" / "dist", ROOT / "dist"),
)


def candidate_paths(path: Path) -> list[Path]:
    """Return the canonical path first, then known equivalent local paths."""
    seen: set[Path] = set()
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        resolved = candidate
        if resolved in seen:
            return
        seen.add(resolved)
        candidates.append(resolved)

    add(path)
    for canonical_root, alternate_root in _ROOT_MAPPINGS:
        if path.is_relative_to(canonical_root):
            add(alternate_root / path.relative_to(canonical_root))
        elif path.is_relative_to(alternate_root):
            add(canonical_root / path.relative_to(alternate_root))
    return candidates


def resolve_existing(path: Path) -> Path | None:
    for candidate in candidate_paths(path):
        if candidate.is_file():
            return candidate
    return None
