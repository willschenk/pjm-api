# Changelog

## [1.1.0] - 2026-06-09

### Added
- Encrypted credentials file via `pjm-api init` (`~/.pjm/credentials.enc`)
- `pjm-api doctor` — single 4-step setup gate
- `pjm-api credentials show` and `credentials rotate-password`
- README with setup, certificate, and troubleshooting diagrams
- `docs/advanced.md` and `docs/troubleshooting.md`

### Changed
- Credentials file takes precedence over `.env`
- Exception messages include `Fix:` hints
- Public API trimmed to `OasisClient` and `load_settings`
- `.env.example` deprecated in favor of `pjm-api init`

## [1.0.0] - 2026-06-09

### Added
- Native Python OASIS client with stdlib mTLS authentication
- Certificate normalization with optional `[pfx]` extra
- Unified CLI and Java CLI fallback backend

## [0.1.0] - 2026-06-09

### Added
- Initial project setup
