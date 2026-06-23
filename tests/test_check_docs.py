from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("check_docs", ROOT / "tools" / "check_docs.py")
assert SPEC is not None
check_docs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_docs)


def test_audit_links_detects_dead_local_link() -> None:
    issues, linked = check_docs.audit_links("docs/example.md", "[Missing](NOPE.md)\n")

    assert linked == set()
    assert [issue["kind"] for issue in issues] == ["dead_local_link"]


def test_audit_absolute_paths_detects_local_machine_paths() -> None:
    text = "Use `$FASTDIS_WORK_ROOT`, not `/Users/example/project` or `C:\\fastdis`.\n"

    issues = check_docs.audit_absolute_paths("docs/example.md", text)

    assert [issue["kind"] for issue in issues] == ["absolute_local_path", "absolute_local_path"]


def test_audit_orphans_allows_front_doors_and_flags_unlinked_docs() -> None:
    paths = ["README.md", "docs/README.md", "docs/linked.md", "docs/orphan.md"]
    linked_docs = {"docs/linked.md"}

    issues = check_docs.audit_orphans(paths, linked_docs)

    assert [issue["path"] for issue in issues] == ["docs/orphan.md"]
