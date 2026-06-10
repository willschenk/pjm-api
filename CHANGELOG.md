# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-06-09

### Added
- Native Python OASIS client with stdlib mTLS authentication (default backend)
- Certificate normalization layer with optional `[pfx]` extra for PKCS#12
- `OasisClient.request()` generic template API
- Template catalog with TRANSSERV, pjmtransreq, and PJM custom template stubs
- Unified CLI: `config`, `auth-check`, `cert-doctor`, `smoke`, `template`, `templates`
- Official PJM Java CLI fallback adapter (`--backend cli`)
- Optional CLI ZIP bootstrap with checksum verification
- Three-tier testing: unit, contract, opt-in live
- Documentation in `docs/` and examples in `examples/`

## [0.1.0] - 2026-06-09

### Added
- Initial project setup with Java CLI wrapper and basic config layer
