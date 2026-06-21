# Security Policy

FastDIS is prerelease software. Treat all network inputs, replay files, and
integration credentials as potentially sensitive.

## Reporting

Do not post secrets, tokens, credentials, or private packet captures in public
issues.

Report security-sensitive issues privately to the maintainers through the
repository security reporting mechanism when available, or through direct
maintainer contact.

## Scope

Relevant issues include:

- out-of-bounds parsing or memory safety defects
- unsafe artifact publishing or release-manifest defects
- accidental secret exposure in docs, scripts, or CI
- credential handling defects in optional Lattice workflows

## Expectations

- Live vendor credentials are optional and must never be committed.
- `.env.example` files should contain placeholders only.
- Release artifacts should include checksums and a manifest.
