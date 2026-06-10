# CLI Reference

## Global flags

- `--env TRAIN|PRODUCTION|TEST|STAGE`
- `--username`, `--password`, `--cert`, `--cert-password`
- `--backend native|cli`
- `--downloads PATH`
- `--oasis-url URL`
- `-v` verbose, `-q` quiet

## Commands

| Command | Description |
|---------|-------------|
| `config` | Show resolved settings |
| `cert-doctor` | Inspect certificate |
| `auth-check` | Verify SSO (`--full` runs smoke) |
| `smoke` | TRANSSERV smoke test (`--all` for batch) |
| `template NAME` | Run generic template |
| `templates list` | List catalog entries |
| `templates info NAME` | Template details |
| `cli install` | Download PJM CLI ZIP |

## Exit codes

- `0` — success
- `1` — operational failure
- `2` — configuration or certificate error
