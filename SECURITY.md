# Security Policy

## Supported Versions

Only the latest published release on [PyPI](https://pypi.org/project/kotakneoapi/)
receives security fixes. Please upgrade before reporting an issue:

```bash
pip install --upgrade kotakneoapi
```

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**
Public issues are visible to everyone immediately, including anyone who might
exploit the report before a fix ships.

Instead, report it privately using one of these channels:

- **Email:** [support@kotakneo.com](mailto:support@kotakneo.com) — include
  "SECURITY" in the subject line.
- **GitHub Private Vulnerability Reporting:** use the
  [Report a vulnerability](https://github.com/Kotak-Neo/kotak-neo-python/security/advisories/new)
  form on this repo's Security tab (requires the feature to be enabled by a
  maintainer).

Please include:
- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a minimal proof-of-concept.
- The SDK version and Python version affected.

We aim to acknowledge reports within 3 business days and to keep you updated
as we investigate and fix the issue. Once a fix is released, we'll credit
reporters in the release notes unless you prefer to remain anonymous.

## Scope

This policy covers the `kotakneoapi` Python SDK itself — the code in this
repository. It does **not** cover:

- The Kotak Neo trading platform, mobile app, or web application.
- The Kotak Neo Trade API backend (the REST/WebSocket services this SDK
  talks to).

For issues with the platform or backend API itself, contact Kotak Securities
support directly rather than this repository.

## Handling Credentials

This SDK never stores or transmits your credentials anywhere other than
directly to Kotak's own API endpoints, as documented. A few reminders for
safe usage:

- Never commit your `consumer_key`, TOTP secret, or MPIN to version control.
  Use environment variables or a `.env` file (already excluded via
  `.gitignore`) — see `.env.example`.
- Treat your `consumer_key` and TOTP secret like passwords; rotate them via
  the Kotak Neo app if you suspect they've been exposed.
- If you're building on top of this SDK, review your own application's
  handling of these values before deploying — the SDK's job ends at the API
  boundary.
