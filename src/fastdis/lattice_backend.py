from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "configs" / "lattice_backend.json"
DEFAULT_LIVE_CONFIG_PATH = ROOT / "configs" / "lattice_backend.real.example.json"


@dataclass(frozen=True)
class LatticeBackendConfig:
    backend: str
    transport: str
    repo_url: str
    tag: str
    checkout_dir: str
    checkout_candidates: list[str]
    legacy_fallback: bool
    swappable_to_real_lattice: bool
    contract_surfaces: list[str]
    cheat_surfaces: list[str]
    command_templates: dict[str, list[str]]
    config_path: Path
    entity_events_route: str = "/api/v1/entities/events"
    entity_stream_route: str = "/api/v1/entities/stream"

    @property
    def checkout_path(self) -> Path:
        for candidate in self.checkout_candidates:
            path = (ROOT / candidate).resolve() if not Path(candidate).is_absolute() else Path(candidate)
            if path.exists():
                return path
        return (ROOT / self.checkout_dir).resolve()

    @property
    def tag_is_pinned(self) -> bool:
        return bool(self.tag)

    def command(self, name: str, context: dict[str, str]) -> list[str] | None:
        template = self.command_templates.get(name)
        if template is None:
            return None
        return [part.format_map(context) for part in template]


def _config_path() -> Path:
    override = os.environ.get("FASTDIS_LATTICE_BACKEND_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    if DEFAULT_CONFIG_PATH.is_file():
        return DEFAULT_CONFIG_PATH
    return DEFAULT_LIVE_CONFIG_PATH


def _load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"backend config at {path} must be an object")
    return payload


def load_lattice_backend_config() -> LatticeBackendConfig:
    path = _config_path()
    payload = _load_payload(path)
    return LatticeBackendConfig(
        backend=str(payload.get("backend", "missing")),
        transport=str(payload.get("transport", "missing")),
        repo_url=str(payload.get("repo_url", "")),
        tag=str(payload.get("tag", "")),
        checkout_dir=str(payload.get("checkout_dir", "build/external/zorn")),
        checkout_candidates=[str(candidate) for candidate in payload.get("checkout_candidates", []) if isinstance(candidate, str)],
        legacy_fallback=bool(payload.get("legacy_fallback", False)),
        swappable_to_real_lattice=bool(payload.get("swappable_to_real_lattice", False)),
        contract_surfaces=[str(surface) for surface in payload.get("contract_surfaces", []) if isinstance(surface, str)],
        cheat_surfaces=[str(surface) for surface in payload.get("cheat_surfaces", []) if isinstance(surface, str)],
        command_templates={
            str(key): [str(item) for item in value if isinstance(item, str)]
            for key, value in dict(payload.get("command_templates", {})).items()
            if isinstance(value, list)
        },
        config_path=path,
        entity_events_route=str(payload.get("entity_events_route", "/api/v1/entities/events")),
        entity_stream_route=str(payload.get("entity_stream_route", "/api/v1/entities/stream")),
    )


def backend_status() -> dict[str, Any]:
    config = load_lattice_backend_config()
    return {
        "backend": config.backend,
        "transport": config.transport,
        "repo_url": config.repo_url,
        "tag": config.tag,
        "tag_is_pinned": config.tag_is_pinned,
        "config_path": config.config_path,
        "checkout_path": config.checkout_path,
        "checkout_present": config.checkout_path.exists(),
        "git_checkout": (config.checkout_path / ".git").exists(),
        "configured_commands": sorted(config.command_templates),
        "contract_surfaces": config.contract_surfaces,
        "cheat_surfaces": config.cheat_surfaces,
        "legacy_fallback": config.legacy_fallback,
        "swappable_to_real_lattice": config.swappable_to_real_lattice,
        "checkout_candidates": config.checkout_candidates,
    }
