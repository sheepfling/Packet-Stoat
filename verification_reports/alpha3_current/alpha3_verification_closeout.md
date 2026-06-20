# Alpha 3 Verification Closeout

- generated_at: `2026-06-19T20:29:45.383386+00:00`
- out_dir: `verification_reports/alpha3_current`

| Lane | Status | Command |
| --- | --- | --- |
| orientation_core | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_orientation_report.py --output-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current` |
| orientation_pipeline | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_orientation_pipeline_report.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current` |
| orientation_visual | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_orientation_visual_report.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current --engine-version 5.8` |
| network_ingest | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_network_ingest_matrix.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current --engine-entity-count 1 --unreal-engine-version 5.8` |
| sanitizer_smoke | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_alpha3_sanitizer_report.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current` |
| benchmark_matrix | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_benchmarks.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/benchmark_reports/alpha3_matrix --format json` |
| release_audit | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/run_alpha3_release_audit.py --out-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current` |
| stage_host_bundle | passed | `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 tools/stage_alpha3_host_report.py --source-dir /Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/verification_reports/alpha3_current --overwrite` |

## Artifacts

- `verification_reports/alpha3_current/orientation_verification_report.json`
- `verification_reports/alpha3_current/orientation_verification_report.md`
- `verification_reports/alpha3_current/orientation_pipeline_report.json`
- `verification_reports/alpha3_current/orientation_pipeline_report.md`
- `verification_reports/alpha3_current/orientation_visual_report.json`
- `verification_reports/alpha3_current/orientation_visual_report.md`
- `verification_reports/alpha3_current/orientation_visual_review/index.html`
- `verification_reports/alpha3_current/network_ingest_matrix.json`
- `verification_reports/alpha3_current/network_ingest_matrix.md`
- `verification_reports/alpha3_current/sanitizer_smoke_report.json`
- `verification_reports/alpha3_current/sanitizer_smoke_report.md`
- `benchmark_reports/alpha3_matrix/current.json`
- `benchmark_reports/alpha3_matrix/qualification.json`
- `benchmark_reports/alpha3_matrix/summary.md`
- `verification_reports/alpha3_current/alpha3_release_audit_report.json`
- `verification_reports/alpha3_current/alpha3_release_audit_report.md`
