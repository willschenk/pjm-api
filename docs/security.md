# Security

## Never commit

- `.env`, credentials, certificate files
- `test.py`, `GUIDANCE.md` (local only)

## Secret handling

- Native backend: secrets in HTTP headers over mTLS, not subprocess argv
- CLI backend: PJM JAR requires `-p`/`-r` flags — use native when possible
- Temp PEM files created with mode 0600 and auto-deleted
- Logs redact passwords, tokens, and cookies

## Dependencies

Enable Dependabot for CVE monitoring. Pin `cryptography` minimum version in `[pfx]` extra.
