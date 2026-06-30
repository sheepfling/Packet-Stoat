#!/usr/bin/env python3
"""Evaluate declarative workspace requirements against the current host."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Any


def _version_matches(requested: str, discovered: str) -> bool:
    return discovered == requested or discovered.startswith(f"{requested}.")


def interpreter_payload() -> dict[str, str]:
    return {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "implementation": getattr(sys.implementation, "name", "unknown"),
        "abi": f"{getattr(sys.implementation, 'name', 'unknown')}-{sys.version_info.major}.{sys.version_info.minor}",
    }


@dataclass(frozen=True)
class RequirementFailure:
    requirement_kind: str
    version_policy: str
    reason: str
    discovered: str
    expected: list[str]
    remediation: list[str]
    blocking: bool
    diagnostic_code: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "requirement_kind": self.requirement_kind,
            "version_policy": self.version_policy,
            "reason": self.reason,
            "discovered": self.discovered,
            "expected": list(self.expected),
            "remediation": list(self.remediation),
            "blocking": self.blocking,
            "diagnostic_code": self.diagnostic_code,
        }


def _check_interpreter(row: dict[str, Any], *, context: dict[str, Any]) -> RequirementFailure | None:
    version_policy = str(row.get("version_policy") or "broad")
    supported_versions = [str(value) for value in row.get("supported_versions") or []]
    reason = str(row.get("reason") or "interpreter requirement not satisfied")
    row_remediation = [str(value) for value in row.get("remediation") or []]
    blocking = bool(row.get("blocking", True))
    interpreter = context.get("interpreter") or interpreter_payload()
    discovered_version = str(interpreter.get("version") or "")
    discovered_impl = str(interpreter.get("implementation") or "unknown")
    discovered = f"{discovered_impl}-{discovered_version}"
    version_ok = any(_version_matches(expected, discovered_version) for expected in supported_versions)
    impl_ok = True
    if version_policy == "exact-abi":
        impl_ok = discovered_impl == "cpython"
    if version_policy in {"exact-minor", "exact-abi"}:
        version_ok = discovered_version in supported_versions
    if version_ok and impl_ok:
        return None
    diagnostic_code = "interpreter-version-mismatch"
    if version_policy == "exact-abi":
        diagnostic_code = "interpreter-abi-mismatch"
    return RequirementFailure(
        requirement_kind="interpreter",
        version_policy=version_policy,
        reason=reason,
        discovered=discovered,
        expected=supported_versions,
        remediation=row_remediation,
        blocking=blocking,
        diagnostic_code=diagnostic_code,
    )


def _check_toolchain(row: dict[str, Any], *, context: dict[str, Any]) -> RequirementFailure | None:
    tool = str(row.get("tool") or "")
    any_of_tools = [str(value) for value in row.get("any_of_tools") or []]
    expected = [tool] if tool else any_of_tools
    reason = str(row.get("reason") or "toolchain requirement not satisfied")
    row_remediation = [str(value) for value in row.get("remediation") or []]
    blocking = bool(row.get("blocking", True))
    executables = context.get("executables") or {}
    if tool:
        if executables.get(tool):
            return None
        return RequirementFailure(
            requirement_kind="toolchain",
            version_policy="presence",
            reason=reason,
            discovered="missing",
            expected=expected,
            remediation=row_remediation,
            blocking=blocking,
            diagnostic_code="toolchain-missing",
        )
    if any_of_tools and any(executables.get(name) for name in any_of_tools):
        return None
    return RequirementFailure(
        requirement_kind="toolchain",
        version_policy="presence-any",
        reason=reason,
        discovered="missing",
        expected=expected,
        remediation=row_remediation,
        blocking=blocking,
        diagnostic_code="toolchain-missing",
    )


def _check_backend(row: dict[str, Any], *, context: dict[str, Any]) -> RequirementFailure | None:
    backend = str(row.get("backend") or "")
    reason = str(row.get("reason") or "backend requirement not satisfied")
    row_remediation = [str(value) for value in row.get("remediation") or []]
    blocking = bool(row.get("blocking", True))
    backends = context.get("backends") or {}
    status = str(backends.get(backend) or "unavailable")
    if status == "ready":
        return None
    return RequirementFailure(
        requirement_kind="backend",
        version_policy="availability",
        reason=reason,
        discovered=status,
        expected=[backend],
        remediation=row_remediation,
        blocking=blocking,
        diagnostic_code="backend-unavailable",
    )


def _check_env(row: dict[str, Any], *, context: dict[str, Any]) -> RequirementFailure | None:
    name = str(row.get("name") or "")
    reason = str(row.get("reason") or "environment variable requirement not satisfied")
    row_remediation = [str(value) for value in row.get("remediation") or []]
    blocking = bool(row.get("blocking", True))
    env = context.get("env") or os.environ
    if name and env.get(name):
        return None
    return RequirementFailure(
        requirement_kind="env",
        version_policy="presence",
        reason=reason,
        discovered="unset",
        expected=[name] if name else [],
        remediation=row_remediation,
        blocking=blocking,
        diagnostic_code="env-missing",
    )


def _check_engine(row: dict[str, Any], *, context: dict[str, Any]) -> RequirementFailure | None:
    engine = str(row.get("engine") or "")
    version_policy = str(row.get("version_policy") or "broad")
    supported_versions = [str(value) for value in row.get("supported_versions") or []]
    reason = str(row.get("reason") or "engine requirement not satisfied")
    row_remediation = [str(value) for value in row.get("remediation") or []]
    blocking = bool(row.get("blocking", True))
    engines = context.get("engines") or {}
    payload = engines.get(engine) or {}
    discovered_versions = [str(value) for value in payload.get("versions") or []]
    if not supported_versions and payload.get("status") == "ready":
        return None
    if version_policy == "exact-minor":
        ok = any(discovered in supported_versions for discovered in discovered_versions)
    else:
        ok = any(_version_matches(expected, discovered) for expected in supported_versions for discovered in discovered_versions)
    if ok:
        return None
    return RequirementFailure(
        requirement_kind="engine",
        version_policy=version_policy,
        reason=reason,
        discovered=",".join(discovered_versions) or str(payload.get("status") or "missing"),
        expected=supported_versions or [engine],
        remediation=row_remediation,
        blocking=blocking,
        diagnostic_code="engine-version-mismatch" if supported_versions else "engine-missing",
    )


def evaluate_requirements(requirements: list[dict[str, Any]] | None, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = requirements or []
    resolved_context = {
        "interpreter": interpreter_payload(),
        "executables": {},
        "backends": {},
        "engines": {},
        "env": os.environ,
    }
    if context:
        resolved_context.update(context)
    if not rows:
        return {
            "status": "pass",
            "blocking": False,
            "failures": [],
            "remediation": [],
        }

    failures: list[RequirementFailure] = []
    remediation: list[str] = []
    interpreter = interpreter_payload()
    for row in rows:
        requirement_kind = str(row.get("requirement_kind") or "")
        remediation.extend([str(value) for value in row.get("remediation") or []])
        failure: RequirementFailure | None = None
        if requirement_kind == "interpreter":
            failure = _check_interpreter(row, context=resolved_context)
        elif requirement_kind == "toolchain":
            failure = _check_toolchain(row, context=resolved_context)
        elif requirement_kind == "backend":
            failure = _check_backend(row, context=resolved_context)
        elif requirement_kind == "env":
            failure = _check_env(row, context=resolved_context)
        elif requirement_kind == "engine":
            failure = _check_engine(row, context=resolved_context)
        if failure is not None:
            failures.append(failure)

    failure_dicts = [failure.as_dict() for failure in failures]
    blocking_failures = [failure for failure in failures if failure.blocking]
    status = "pass"
    if blocking_failures:
        status = "fail"
    elif failures:
        status = "warn"
    return {
        "status": status,
        "blocking": bool(blocking_failures),
        "failures": failure_dicts,
        "remediation": remediation,
    }
