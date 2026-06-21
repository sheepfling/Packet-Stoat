# Publishing Bootstrap

This is the human account and first-publish checklist for Alpha5. These steps
cannot be completed by CI or by another developer without the account owner.

Do not commit secrets, API tokens, recovery codes, client secrets, screenshots
with account data, or marketplace private drafts.

## Public Identity

- Product: `FastDIS`
- Repository codename: `Packet Stoat`
- Python distribution target: `fastdis`
- Python import package: `fastdis`
- Primary CLI: `fastdis`
- Maintainer/public publisher: `SheepFling Labs`

Account usernames do not need to match. Public docs and release notes should
consistently say that FastDIS is maintained by SheepFling Labs.

## Immediate Account Actions

1. Create or verify a PyPI account.
2. Create or verify a TestPyPI account with the same email.
3. Enable 2FA on both accounts.
4. Store recovery codes in a password manager.
5. Configure Trusted Publishing after the GitHub Actions workflow exists.
6. Create Epic/Fab publisher profile as SheepFling Labs.
7. Create Godot Asset Library / Asset Store account as SheepFling Labs.
8. Optionally reserve `fastdis.dev` before spending time on logos or marketplace
   polish.

## PyPI Name Check

Check while logged in:

```text
https://pypi.org/project/fastdis/
https://test.pypi.org/project/fastdis/
```

Also check the JSON API:

```bash
curl -fsSL https://pypi.org/pypi/fastdis/json
```

Interpretation:

- JSON `404` usually means the project is not published on PyPI.
- The project HTML page may still return a PyPI anti-abuse or placeholder page,
  so do not rely on HTTP status from the HTML page alone.
- Availability is not guaranteed until the package is successfully published
  from your account.

If `fastdis` is unavailable or cannot be transferred, use this fallback:

- Distribution: `packet-stoat`
- Import package: `fastdis`
- CLI: `fastdis`

Do not rename the import package or native library just because the distribution
name changes.

## First Publish Rule

Do not publish an empty or deceptive package just to squat a name.

If reserving the package before Alpha5 is fully publishable, publish a real
minimal alpha that contains:

- the actual `fastdis` Python package,
- the `fastdis doctor` CLI,
- the license,
- the README with alpha limitations,
- version `0.0.1a0` or another clearly pre-Alpha5 version.

Before publishing:

```bash
python -m pip install -e '.[dev]'
python -m build --outdir build/dist
twine check build/dist/*
```

Clean install smoke:

```bash
python -m venv /tmp/fastdis-pypi-smoke
/tmp/fastdis-pypi-smoke/bin/python -m pip install build/dist/fastdis-*.whl
/tmp/fastdis-pypi-smoke/bin/fastdis doctor
```

## Alpha5 Publish Order

1. Build and smoke the local package.
2. Publish to TestPyPI.
3. Clean-install from TestPyPI and run `fastdis doctor`.
4. Publish to PyPI.
5. Clean-install from PyPI and run `fastdis doctor`.
6. Publish GitHub prerelease artifacts.
7. Publish GHCR Lattice Lab container, if enabled.
8. Prepare Fab/Godot marketplace drafts, but do not submit until plugin zips
   survive clean install testing.

## What Matters Most

The highest-value external proof is:

```bash
python -m pip install fastdis
fastdis doctor
fastdis send-entity --dst 127.0.0.1 --port 3001 --count 10
fastdis recv --bind 127.0.0.1 --port 3001 --max-packets 10
```

Everything else is secondary until that install path is boring.
