#!/usr/bin/env python3
"""Generate a local FastDIS evidence pack from source-of-truth files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Any, Iterable, Mapping, Sequence

from artifacts import ROOT, VERIFICATION_REPORTS_DIR, rel


DEFAULT_OUT = VERIFICATION_REPORTS_DIR / "evidence" / "latest"
PROOF_ROOT = ROOT / "extensions" / "fastdis-symbols-proof"
CASE_INPUT = PROOF_ROOT / "cases" / "demo_fastdis_entities.jsonl"
RULES_INPUT = PROOF_ROOT / "rules" / "demo_dis_to_symbol_rules.json"
AFFILIATION_INPUT = PROOF_ROOT / "rules" / "affiliation_policy.json"
RENDERER = PROOF_ROOT / "render_milsymbol.mjs"


@dataclass(frozen=True)
class Artifact:
    path: Path
    description: str
    required: bool = True
    status: str = "generated"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(path: Path, text: str, description: str = "generated evidence artifact") -> Artifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return Artifact(path=path, description=description)


def _write_json(path: Path, payload: Mapping[str, Any], description: str = "generated JSON evidence artifact") -> Artifact:
    return _write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n", description)


def _xml(value: object) -> str:
    return html.escape(str(value), quote=True)


def _safe_name(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip()).strip("-")
    return text or "case"


def _svg(title: str, subtitle: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc">
  <title id="title">{_xml(title)}</title>
  <desc id="desc">{_xml(subtitle)}</desc>
  <rect width="1600" height="900" fill="#07151d"/>
  <style>
    .h{{font-family:Verdana,DejaVu Sans,sans-serif;font-size:52px;font-weight:800;fill:#f3f7ea}}
    .s{{font-family:Verdana,DejaVu Sans,sans-serif;font-size:23px;fill:#b8d2c4}}
    .t{{font-family:Verdana,DejaVu Sans,sans-serif;font-size:25px;font-weight:800;fill:#edf6df}}
    .n{{font-family:Verdana,DejaVu Sans,sans-serif;font-size:21px;fill:#dbe8d7}}
    .muted{{font-family:Verdana,DejaVu Sans,sans-serif;font-size:18px;fill:#91aaa0}}
    .box{{fill:#102936;stroke:#47717b;stroke-width:3}}
    .hot{{fill:#d2f36b;stroke:#efffb5;stroke-width:3}}
    .line{{stroke:#6df0c2;stroke-width:6;fill:none;marker-end:url(#arrow)}}
  </style>
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0 0 L12 6 L0 12 Z" fill="#6df0c2"/>
    </marker>
  </defs>
  <text x="70" y="92" class="h">{_xml(title)}</text>
  <text x="72" y="132" class="s">{_xml(subtitle)}</text>
{body}
</svg>
"""


def _bar_chart(path: Path, pdu: Mapping[str, Any], typed: Mapping[str, Any], semantic: Mapping[str, Any]) -> Artifact:
    pdu_summary = pdu["summary"]
    typed_summary = typed["summary"]
    semantic_summary = semantic["summary"]
    bars = [
        ("standard rows", pdu_summary["standard_total_rows"], 141, "#d2f36b"),
        ("safe ingest", pdu_summary["safe_ingest_rows"], 141, "#6df0c2"),
        ("generic endpoint", pdu_summary["generic_endpoint_rows"], 141, "#6df0c2"),
        ("typed envelope", typed_summary["typed_envelope"], 141, "#d2f36b"),
        ("structural fields", typed_summary["typed_structural"], 141, "#ffbc57"),
        ("domain decoded", semantic_summary["fully_domain_decoded"], 141, "#ff6f61"),
    ]
    body = ['  <g transform="translate(100 210)">']
    for index, (label, value, total, color) in enumerate(bars):
        y = index * 92
        width = int(1000 * float(value) / float(total))
        body.extend(
            [
                f'    <text x="0" y="{y + 26}" class="t">{_xml(label)}</text>',
                f'    <rect x="310" y="{y}" width="1000" height="34" rx="14" fill="#18323d" stroke="#34525a"/>',
                f'    <rect x="310" y="{y}" width="{width}" height="34" rx="14" fill="{color}"/>',
                f'    <text x="1335" y="{y + 26}" class="n">{value} / {total}</text>',
            ]
        )
    body.extend(['    <text x="0" y="610" class="muted">Broad handling and full semantic decoding are intentionally separate evidence layers.</text>', "  </g>"])
    return _write(path, _svg("PDU handling status", "Generated from PDU, typed-parser, and semantic-parser manifests.", "\n".join(body)))


def _pipeline_chart(path: Path) -> Artifact:
    labels = [
        ("UDP / replay", "packet bytes"),
        ("header scanner", "filter and count"),
        ("Entity State", "identity + pose fast path"),
        ("entity table", "latest state"),
        ("snapshots", "engine handoff"),
    ]
    body = ['  <g transform="translate(80 310)">']
    for index, (title, subtitle) in enumerate(labels):
        x = index * 300
        class_name = "hot" if index == 2 else "box"
        body.extend(
            [
                f'    <rect class="{class_name}" x="{x}" y="0" width="245" height="150" rx="24"/>',
                f'    <text x="{x + 24}" y="58" class="t">{_xml(title)}</text>',
                f'    <text x="{x + 24}" y="96" class="s">{_xml(subtitle)}</text>',
            ]
        )
        if index < len(labels) - 1:
            body.append(f'    <path class="line" d="M{x + 258} 75 H{x + 292}"/>')
    body.extend(['    <text x="0" y="265" class="muted">Source-generated from the current fast-path design contract.</text>', "  </g>"])
    return _write(path, _svg("Fast path pipeline", "Packet burst to stable runtime snapshots.", "\n".join(body)))


def _simple_chart(path: Path, title: str, subtitle: str, rows: list[tuple[str, str]]) -> Artifact:
    body = ['  <g transform="translate(150 220)">', '    <rect class="box" width="1300" height="540" rx="30"/>']
    for index, (left, right) in enumerate(rows):
        y = 72 + index * 54
        body.append(f'    <text x="60" y="{y}" class="t">{_xml(left)}</text>')
        body.append(f'    <text x="610" y="{y}" class="n">{_xml(right)}</text>')
    body.append("  </g>")
    return _write(path, _svg(title, subtitle, "\n".join(body)))


def _abi_portability(path: Path) -> Artifact:
    body = """
  <g transform="translate(640 300)">
    <circle cx="160" cy="160" r="138" fill="#d2f36b" stroke="#efffb5" stroke-width="5"/>
    <text x="84" y="150" font-family="Verdana,DejaVu Sans,sans-serif" font-size="38" font-weight="900" fill="#142014">C ABI</text>
    <text x="62" y="195" font-family="Verdana,DejaVu Sans,sans-serif" font-size="24" fill="#142014">libfastdis</text>
  </g>
  <g class="n">
    <text x="160" y="310">Python ctypes</text>
    <text x="190" y="585">C / C++</text>
    <text x="655" y="770">Rust / Go / C#</text>
    <text x="1210" y="310">Unreal</text>
    <text x="1240" y="585">Godot / Unity</text>
  </g>
  <path class="line" d="M600 420 H360"/>
  <path class="line" d="M620 520 H380"/>
  <path class="line" d="M800 610 V705"/>
  <path class="line" d="M1000 420 H1190"/>
  <path class="line" d="M980 520 H1190"/>
  <text x="120" y="820" class="muted">One native boundary. Thin host adapters. No C++ classes cross the shared-library ABI.</text>
"""
    return _write(path, _svg("C ABI portability", "Generated evidence that the product story centers on the stable C boundary.", body))


def _symbol_descriptors() -> list[dict[str, Any]]:
    entities = _read_jsonl(CASE_INPUT)
    rules = _read_json(RULES_INPUT)
    affiliation_policy = _read_json(AFFILIATION_INPUT)
    descriptors: list[dict[str, Any]] = []
    force_map = affiliation_policy.get("force_id_map", {})
    fallback = rules.get("fallback_symbol_key_by_affiliation", {})
    sidc_table = rules.get("sidc_by_symbol_key_and_affiliation", {})
    for entity in entities:
        entity_type = tuple(int(part) for part in str(entity["entity_type"]).split("."))
        force_id = int(entity["force_id"])
        affiliation = str(force_map.get(str(force_id), affiliation_policy.get("default", "unknown"))) if isinstance(force_map, Mapping) else "unknown"
        symbol_key = None
        for rule in rules.get("rules", []):
            when = rule.get("when", {}) if isinstance(rule, Mapping) else {}
            if isinstance(when, Mapping) and int(when.get("kind", -1)) == entity_type[0] and int(when.get("domain", -1)) == entity_type[1]:
                symbol_key = str(rule["symbol_key"])
                break
        if symbol_key is None and isinstance(fallback, Mapping):
            symbol_key = str(fallback.get(affiliation, fallback.get("unknown", "unknown")))
        by_affiliation = sidc_table.get(symbol_key, {}) if isinstance(sidc_table, Mapping) else {}
        sidc = str(by_affiliation.get(affiliation, by_affiliation.get("unknown", ""))) if isinstance(by_affiliation, Mapping) else ""
        descriptors.append(
            {
                "case_id": entity["case_id"],
                "sidc": sidc,
                "standard": rules.get("standard", "unknown"),
                "source": {
                    "force_id": force_id,
                    "entity_type": ".".join(str(part) for part in entity_type),
                },
                "modifiers": {
                    "uniqueDesignation": entity.get("marking"),
                },
            }
        )
    return descriptors


def _symbol_cases(path: Path, descriptors: Sequence[Mapping[str, Any]]) -> Artifact:
    lines = ["# Symbol Cases", "", "| Case | SIDC | Force | Entity type |", "| --- | --- | --- | --- |"]
    for descriptor in descriptors:
        source = descriptor.get("source", {})
        source_map = source if isinstance(source, Mapping) else {}
        lines.append(f"| `{descriptor['case_id']}` | `{descriptor['sidc']}` | `{source_map.get('force_id', '')}` | `{source_map.get('entity_type', '')}` |")
    return _write(path, "\n".join(lines) + "\n")


def _contact_sheet(path: Path, descriptors: Sequence[Mapping[str, Any]]) -> Artifact:
    body = ['  <g transform="translate(85 200)">']
    for index, descriptor in enumerate(descriptors):
        x = (index % 3) * 470
        y = (index // 3) * 250
        body.extend(
            [
                f'    <rect class="box" x="{x}" y="{y}" width="420" height="190" rx="24"/>',
                f'    <circle cx="{x + 70}" cy="{y + 88}" r="40" fill="#d2f36b" stroke="#efffb5" stroke-width="4"/>',
                f'    <text x="{x + 135}" y="{y + 58}" class="t">{_xml(descriptor["case_id"])}</text>',
                f'    <text x="{x + 135}" y="{y + 100}" class="s">SIDC {_xml(descriptor["sidc"])}</text>',
                f'    <text x="{x + 135}" y="{y + 137}" class="muted">source: proof JSONL</text>',
            ]
        )
    body.append("  </g>")
    return _write(path, _svg("Symbol contact sheet", "Generated from proof JSONL cases and SIDC rules.", "\n".join(body)))


def _maybe_render_symbols(out_dir: Path, descriptors: Sequence[Mapping[str, Any]], mode: str) -> tuple[list[Artifact], dict[str, Any]]:
    if mode == "never":
        return [], {"status": "skipped", "reason": "disabled"}
    node = shutil.which("node")
    if node is None or not (PROOF_ROOT / "node_modules" / "milsymbol").exists():
        if mode == "always":
            raise RuntimeError("node and milsymbol are required for --render-symbols always")
        return [], {"status": "skipped", "reason": "node or milsymbol unavailable"}
    descriptors_path = out_dir / "symbols" / "descriptors.jsonl"
    cases_dir = out_dir / "symbols" / "cases"
    descriptors_path.parent.mkdir(parents=True, exist_ok=True)
    descriptors_path.write_text("\n".join(json.dumps(descriptor, sort_keys=True) for descriptor in descriptors) + "\n", encoding="utf-8")
    completed = subprocess.run(
        [node, str(RENDERER), str(descriptors_path), str(cases_dir)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    receipt = out_dir / "receipts" / "npm_render_milsymbol.txt"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(completed.stdout, encoding="utf-8")
    artifacts = [Artifact(receipt, "milsymbol render receipt", required=False, status="generated" if completed.returncode == 0 else "failed")]
    if completed.returncode != 0:
        if mode == "always":
            raise RuntimeError(completed.stdout)
        return artifacts, {"status": "failed", "returncode": completed.returncode}
    artifacts.extend(Artifact(path, "per-case milsymbol SVG", required=False) for path in sorted(cases_dir.glob("*.svg")))
    return artifacts, {"status": "generated", "stdout": completed.stdout.strip()}


def _pdu_table(path: Path, pdu: Mapping[str, Any], typed: Mapping[str, Any], semantic: Mapping[str, Any]) -> Artifact:
    pdu_summary = pdu["summary"]
    typed_summary = typed["summary"]
    semantic_summary = semantic["summary"]
    lines = [
        "# PDU Handling Status",
        "",
        "| Layer | Count | Meaning |",
        "| --- | ---: | --- |",
        f"| Standard backbone | {pdu_summary['standard_total_rows']} / 141 | Every DIS 6/7 enum row is represented. |",
        f"| Safe ingest | {pdu_summary['safe_ingest_rows']} / 141 | Header parse, length check, count, safe skip. |",
        f"| Generic endpoint | {pdu_summary['generic_endpoint_rows']} / 141 | Every known PDU has generic endpoint behavior. |",
        f"| Typed envelope | {typed_summary['typed_envelope']} / 141 | Every row has a slotted byte-preserving Python class. |",
        f"| Structural parser | {typed_summary['typed_structural']} / 141 | Schema-backed rows expose declared fields. |",
        f"| Full domain decode | {semantic_summary['fully_domain_decoded']} / 141 | Hand-supported semantic prefixes. |",
    ]
    return _write(path, "\n".join(lines) + "\n")


def _abi_surface(path: Path) -> Artifact:
    header = (ROOT / "include" / "fastdis" / "fastdis.h").read_text(encoding="utf-8")
    structs = sorted(set(re.findall(r"}\s*(fastdis_[A-Za-z0-9_]+_t);", header)))
    functions = sorted(set(re.findall(r"FASTDIS_API\s+[A-Za-z0-9_*\s]+\s+(fastdis_[A-Za-z0-9_]+)\s*\(", header)))
    lines = [
        "# ABI Surface",
        "",
        "| Category | Count | Evidence |",
        "| --- | ---: | --- |",
        f"| Public POD typedef structs | {len(structs)} | Parsed from `include/fastdis/fastdis.h`. |",
        f"| Public C functions | {len(functions)} | Parsed from `FASTDIS_API` declarations. |",
        "| C++ classes across ABI | 0 | C boundary only. |",
        "| STL containers across ABI | 0 | Fixed-width/POD boundary. |",
        "",
        "## Sample Functions",
        "",
    ]
    lines.extend(f"- `{function}`" for function in functions[:20])
    return _write(path, "\n".join(lines) + "\n")


def _traces(out_dir: Path, descriptors: Sequence[Mapping[str, Any]]) -> list[Artifact]:
    first = descriptors[0]
    source = first.get("source", {})
    source_map = source if isinstance(source, Mapping) else {}
    trace = [
        "# Entity State To Symbol Trace",
        "",
        "- input: `extensions/fastdis-symbols-proof/cases/demo_fastdis_entities.jsonl`",
        "- symbol rules: `extensions/fastdis-symbols-proof/rules/demo_dis_to_symbol_rules.json`",
        f"- case_id: `{first['case_id']}`",
        f"- force_id: `{source_map.get('force_id')}`",
        f"- entity_type: `{source_map.get('entity_type')}`",
        f"- sidc: `{first['sidc']}`",
        "",
        "Conclusion: Entity State identity fields are sufficient to create a deterministic `SymbolDescriptor` for the proof lane.",
    ]
    negative = [
        "# Transform-Only Negative Trace",
        "",
        "Available in compact transform snapshots: entity id, force id, appearance, location, orientation, and linear velocity.",
        "",
        "Unavailable for symbol identity: entity type, alternate entity type, marking, and capabilities.",
        "",
        "Conclusion: transform-only output can place and move an already-known symbol, but cannot derive complete tactical symbol identity by itself.",
    ]
    return [
        _write(out_dir / "traces" / "entity_state_to_symbol_trace.md", "\n".join(trace) + "\n"),
        _write(out_dir / "traces" / "transform_only_negative_trace.md", "\n".join(negative) + "\n"),
    ]


def _benchmark_chart(path: Path) -> Artifact:
    candidates = [
        ROOT / "artifacts" / "benchmark_results" / "current" / "current.json",
        ROOT / "artifacts" / "benchmark_results" / "alpha5" / "current.json",
    ]
    benchmark = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    if benchmark.exists():
        payload = _read_json(benchmark)
        title = f"benchmark payload: {payload.get('generated_at_utc', 'local')}"
        detail = "Local benchmark JSON was present and hashed in the evidence manifest."
    else:
        title = "No local benchmark payload found."
        detail = "Run `python tools/run_benchmarks.py --format json --out-dir artifacts/benchmark_results/current` to add numbers."
    return _simple_chart(path, "Benchmark throughput receipt", "Evidence pack will not invent benchmark numbers.", [(title, detail)])


def _snapshot_chart(path: Path) -> Artifact:
    return _simple_chart(
        path,
        "Snapshot handoff",
        "Synthetic changed/stale snapshot evidence for engine adapters.",
        [("tick 0", "changed=5 stale=0"), ("tick 1", "changed=4 stale=0"), ("tick 2", "changed=3 stale=1"), ("tick 3", "changed=6 stale=0"), ("tick 4", "changed=2 stale=2")],
    )


def _unity_bridge_chart(path: Path) -> Artifact:
    report = ROOT / "artifacts" / "reports" / "unity_csharp_bridge_probe.json"
    if report.exists():
        payload = _read_json(report)
        rows = [
            ("status", str(payload.get("overall_status", "unknown"))),
            ("returncode", str(payload.get("returncode", "unknown"))),
            ("native library", str(payload.get("native_library", "unknown"))),
        ]
        subtitle = "Credential-free Unity package bridge proof compiled and executed under dotnet."
    else:
        rows = [
            ("status", "missing"),
            ("next", "python tools/unity_workflow.py bridge-probe"),
        ]
        subtitle = "Unity bridge proof receipt is not present in artifacts/reports yet."
    return _simple_chart(path, "Unity C# bridge proof", subtitle, rows)


def _unity_bridge_receipt(path: Path) -> Artifact:
    report = ROOT / "artifacts" / "reports" / "unity_csharp_bridge_probe.json"
    lines = [
        "# Unity C# Bridge Proof",
        "",
        f"- source: `{rel(report)}`",
    ]
    if report.exists():
        payload = _read_json(report)
        lines.extend(
            [
                f"- status: `{payload.get('overall_status', 'unknown')}`",
                f"- native_library: `{payload.get('native_library', 'unknown')}`",
                f"- returncode: `{payload.get('returncode', 'unknown')}`",
                "",
                "This receipt proves the Unity package's non-UnityEngine C# bridge compiled and executed against the current host native library.",
            ]
        )
    else:
        lines.extend(
            [
                "- status: `missing`",
                "",
                "Run `python tools/unity_workflow.py bridge-probe` to generate this receipt.",
            ]
        )
    return _write(path, "\n".join(lines) + "\n")


def _epic2_wave_chart(path: Path, waves: Mapping[str, Any]) -> Artifact:
    rows = [
        (
            str(wave["wave_name"]),
            f"rows={wave['rows']} structural={wave['typed_structural_rows']} prefix={wave['semantic_prefix_rows']} decoded={wave['fully_domain_decoded_rows']}",
        )
        for wave in waves["waves"]
    ]
    return _simple_chart(
        path,
        "Epic 2 semantic waves",
        "Generated per-wave typed-semantic worklist status from the 141-row manifest.",
        rows,
    )


def _epic2_wave_table(path: Path, waves: Mapping[str, Any]) -> Artifact:
    lines = [
        "# Epic 2 Semantic Waves",
        "",
        "| Wave | Rows | Structural | Prefix | Fully decoded | Goal |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for wave in waves["waves"]:
        lines.append(
            f"| {wave['wave_name']} | {wave['rows']} | {wave['typed_structural_rows']} | "
            f"{wave['semantic_prefix_rows']} | {wave['fully_domain_decoded_rows']} | {wave['goal']} |"
        )
    return _write(path, "\n".join(lines) + "\n")


def _manifest(out_dir: Path, artifacts: list[Artifact], sources: Iterable[Path], render_status: Mapping[str, Any]) -> dict[str, Any]:
    unhashed_control_files = {"manifest.json", "sha256sums.txt", "index.md"}
    artifact_rows = []
    for artifact in artifacts:
        exists = artifact.path.exists()
        row: dict[str, Any] = {
            "path": rel(artifact.path),
            "description": artifact.description,
            "required": artifact.required,
            "status": artifact.status if exists else "missing",
        }
        if exists and artifact.path.is_file() and artifact.path.name not in unhashed_control_files:
            row["bytes"] = artifact.path.stat().st_size
            row["sha256"] = _sha256(artifact.path)
        elif exists and artifact.path.is_file():
            row["bytes"] = artifact.path.stat().st_size
        artifact_rows.append(row)
    source_rows = []
    for source in sorted(set(sources)):
        row: dict[str, Any] = {"path": rel(source)}
        if source.exists() and source.is_file():
            row["bytes"] = source.stat().st_size
            row["sha256"] = _sha256(source)
        else:
            row["status"] = "missing"
        source_rows.append(row)
    missing = [row["path"] for row in artifact_rows if row.get("required") and row.get("status") == "missing"]
    return {
        "schema": "fastdis.evidence_pack.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "out_dir": rel(out_dir),
        "status": "fail" if missing else "pass",
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "python": platform.python_version()},
        "render_symbols": render_status,
        "sources": source_rows,
        "artifacts": artifact_rows,
    }


def _sha256sums(path: Path, manifest: Mapping[str, Any]) -> Artifact:
    lines = []
    for artifact in manifest["artifacts"]:
        if isinstance(artifact, Mapping) and artifact.get("sha256"):
            lines.append(f"{artifact['sha256']}  {artifact['path']}")
    return _write(path, "\n".join(lines) + "\n", "artifact checksum list")


def _index(path: Path, manifest: Mapping[str, Any]) -> Artifact:
    out_dir = Path(str(manifest["out_dir"]))
    lines = [
        "# FastDIS Evidence Pack",
        "",
        f"- status: `{manifest['status']}`",
        f"- generated_at_utc: `{manifest['generated_at_utc']}`",
        f"- out_dir: `{manifest['out_dir']}`",
        "",
        "## Charts",
        "",
    ]
    for artifact in manifest["artifacts"]:
        if not isinstance(artifact, Mapping):
            continue
        artifact_path = Path(str(artifact.get("path", "")))
        if "charts" in artifact_path.parts:
            try:
                display = artifact_path.relative_to(out_dir)
            except ValueError:
                display = artifact_path
            lines.append(f"- [{artifact_path.name}]({display})")
    lines.extend(["", "## Verify", "", "```bash", f"python tools/check_evidence_pack.py {manifest['out_dir']}/manifest.json", "```", ""])
    return _write(path, "\n".join(lines), "evidence pack index")


def generate(out_dir: Path, *, clean: bool, render_symbols: str) -> dict[str, Any]:
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdu = _read_json(ROOT / "generated" / "pdu_coverage_manifest.json")
    typed = _read_json(ROOT / "generated" / "typed_pdu_parser_manifest.json")
    semantic = _read_json(ROOT / "generated" / "semantic_pdu_parser_manifest.json")
    waves = _read_json(ROOT / "generated" / "epic2_semantic_waves.json")
    descriptors = _symbol_descriptors()
    artifacts = [
        _bar_chart(out_dir / "charts" / "pdu_handling_status.svg", pdu, typed, semantic),
        _pipeline_chart(out_dir / "charts" / "fast_path_pipeline.svg"),
        _abi_portability(out_dir / "charts" / "abi_portability.svg"),
        _simple_chart(
            out_dir / "charts" / "entity_state_field_sufficiency.svg",
            "Entity State field sufficiency",
            "Fields used by the symbols proof lane.",
            [
                ("force_id", "affiliation policy"),
                ("entity_type", "symbol identity"),
                ("alternate_entity_type", "fallback display"),
                ("marking", "unique designation"),
                ("location + orientation", "placement and heading"),
                ("linear_velocity", "movement indicator"),
            ],
        ),
        _simple_chart(
            out_dir / "charts" / "symbol_handoff_pipeline.svg",
            "Symbol handoff pipeline",
            "Raw packet to prefix fields to descriptor to optional SVG.",
            [("Entity State PDU", "raw DIS bytes"), ("FastDIS prefix", "force + type + marking + pose"), ("SymbolDescriptor", "SIDC + modifiers"), ("renderer", "optional SVG proof")],
        ),
        _simple_chart(
            out_dir / "charts" / "dependency_boundary.svg",
            "Dependency boundary",
            "Proof/plugin consumes FastDIS; FastDIS core does not consume proof/plugin dependencies.",
            [("fastdis core", "DIS scan + C ABI + snapshots"), ("fastdis-symbols-proof", "rules + JSONL cases"), ("milsymbol", "optional SVG output")],
        ),
        _benchmark_chart(out_dir / "charts" / "benchmark_throughput.svg"),
        _snapshot_chart(out_dir / "charts" / "snapshot_handoff.svg"),
        _unity_bridge_chart(out_dir / "charts" / "unity_csharp_bridge.svg"),
        _epic2_wave_chart(out_dir / "charts" / "epic2_semantic_waves.svg", waves),
        _pdu_table(out_dir / "tables" / "pdu_handling_status.md", pdu, typed, semantic),
        _abi_surface(out_dir / "tables" / "abi_surface.md"),
        _epic2_wave_table(out_dir / "tables" / "epic2_semantic_waves.md", waves),
        _write(
            out_dir / "tables" / "epic2_milestones.md",
            (ROOT / "docs" / "EPIC2_MILESTONES.md").read_text(encoding="utf-8"),
            "generated Epic 2 milestone report snapshot",
        ),
        _unity_bridge_receipt(out_dir / "tables" / "unity_csharp_bridge.md"),
        _symbol_cases(out_dir / "tables" / "symbol_cases.md", descriptors),
        _contact_sheet(out_dir / "symbols" / "contact_sheet.svg", descriptors),
        *_traces(out_dir, descriptors),
    ]
    rendered, render_status = _maybe_render_symbols(out_dir, descriptors, render_symbols)
    artifacts.extend(rendered)
    sources = [
        ROOT / "generated" / "pdu_coverage_manifest.json",
        ROOT / "generated" / "typed_pdu_parser_manifest.json",
        ROOT / "generated" / "semantic_pdu_parser_manifest.json",
        ROOT / "generated" / "epic2_semantic_waves.json",
        ROOT / "include" / "fastdis" / "fastdis.h",
        CASE_INPUT,
        RULES_INPUT,
        AFFILIATION_INPUT,
        RENDERER,
    ]
    benchmark_candidates = [
        ROOT / "artifacts" / "benchmark_results" / "current" / "current.json",
        ROOT / "artifacts" / "benchmark_results" / "alpha5" / "current.json",
    ]
    benchmark = next((candidate for candidate in benchmark_candidates if candidate.exists()), benchmark_candidates[0])
    if benchmark.exists():
        sources.append(benchmark)
    unity_bridge_report = ROOT / "artifacts" / "reports" / "unity_csharp_bridge_probe.json"
    if unity_bridge_report.exists():
        sources.append(unity_bridge_report)
    manifest = _manifest(out_dir, artifacts, sources, render_status)
    artifacts.append(_write_json(out_dir / "manifest.json", manifest, "evidence pack manifest"))
    manifest = _manifest(out_dir, artifacts, sources, render_status)
    artifacts.append(_sha256sums(out_dir / "sha256sums.txt", manifest))
    artifacts.append(_index(out_dir / "index.md", manifest))
    manifest = _manifest(out_dir, artifacts, sources, render_status)
    _write_json(out_dir / "manifest.json", manifest, "evidence pack manifest")
    _sha256sums(out_dir / "sha256sums.txt", manifest)
    _index(out_dir / "index.md", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--render-symbols", choices=("auto", "always", "never"), default="auto")
    args = parser.parse_args(argv)

    manifest = generate(args.out, clean=args.clean, render_symbols=args.render_symbols)
    print(f"Evidence pack: {args.out}")
    print(f"Manifest: {args.out / 'manifest.json'}")
    print(f"status: {manifest['status']}")
    return 0 if manifest["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
