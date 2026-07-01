#!/usr/bin/env python3
"""Canonical local evidence layout for raw captures and staged host bundles."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
VERIFICATION_REPORTS_DIR = ARTIFACTS_DIR / "verification_reports"

ALPHA2_SAMPLE_DIR = VERIFICATION_REPORTS_DIR / "alpha2_sample"
ALPHA2_HOSTS_DIR = VERIFICATION_REPORTS_DIR / "alpha2_hosts"

ALPHA3_CURRENT_DIR = VERIFICATION_REPORTS_DIR / "alpha3_current"
ALPHA3_HOSTS_DIR = VERIFICATION_REPORTS_DIR / "alpha3_hosts"

UNITY_HOSTS_DIR = VERIFICATION_REPORTS_DIR / "unity_hosts"
