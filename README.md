# pjm-api

Python client for the PJM OASIS API.

## Sources

This project is based entirely on information that PJM and NAESB publish publicly — including PJM's browserless authentication guide, PKI authentication guide, PKI FAQ, OASIS API guide, and related system requirements. It is an unofficial client library and is not affiliated with, endorsed by, or supported by PJM. Refer to [PJM's eTools documentation](https://www.pjm.com/markets-and-operations/etools) for authoritative specifications.

## Certificate workflow

PJM uses two different certificate files:

1. **Account Manager (public cert)** — upload a public certificate (`.cer`, `.crt`) without the private key. Your CAM must approve user-uploaded certs.
2. **Runtime login (private key)** — use a PKCS#12 file (`.p12`, `.pfx`) containing your private key for browserless/API authentication.

Run `pjm-api cert-doctor` if unsure which file you have.

## Install

```bash
pip install -e ".[dev,pfx]"
```

Copy `.env.example` to `.env` and set credentials locally. Never commit secrets or certificate files.

## Quick start

```bash
pjm-api config
pjm-api cert-doctor
pjm-api auth-check
pjm-api smoke --env TRAIN
pjm-api template TRANSSERV --env TRAIN -q OUTPUT_FORMAT=DATA
```

## Backends

| Backend | Command | Requires |
|---------|---------|----------|
| `native` (default) | Pure Python mTLS | Python 3.10+, `.p12` with `[pfx]` extra |
| `cli` | Official PJM Java CLI | Java 8+, `pjm-cli.jar` |

Switch with `PJM_BACKEND=cli` or `--backend cli`.

## Module layout

- `auth` — PKI SSO authentication and session
- `certs` — certificate inspection and PKCS#12 normalization
- `oasis` — native OASIS template client
- `cli_adapter` — official Java CLI fallback
- `templates` — static template catalog metadata
- `config` — unified settings from environment variables

## Local overrides

Keep machine-specific paths in a gitignored `test.py` or `.env` file. See `examples/env_file.py`.

## Troubleshooting

1. `pjm-api config` — verify settings
2. `pjm-api cert-doctor` — verify certificate type and expiry
3. `pjm-api auth-check` — verify SSO authentication
4. `pjm-api smoke --env TRAIN` — end-to-end OASIS health check

See `docs/` for detailed guides.
