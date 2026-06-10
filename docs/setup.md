# Setup walkthrough

Follow this guide from zero to your first successful TRANSSERV call on TRAIN.

## What you need before starting

- **Python 3.10+**
- **PJM login** — username and password for the environment you will use
- **Login certificate** — a `.p12` or `.pfx` file that contains your private key and certificate
- **CAM approval** — the matching public certificate (`.cer` or `.crt`) uploaded and approved in PJM Account Manager

pjm-api uses the `.p12`/`.pfx` file for runtime login. The public certificate goes to Account Manager only.

## Install

```bash
git clone https://github.com/willschenk/pjm-api
cd pjm-api
python -m pip install -e ".[dev,pfx]"
```

The `[pfx]` extra installs PKCS#12 support. Without it, `.p12` and `.pfx` files cannot be decrypted.

Confirm the CLI is available:

```bash
pjm-api --help
```

## Initialize

Create an encrypted credentials file at `~/.pjm/credentials.enc`:

```bash
pjm-api init
```

`pjm-api init` prompts for:

| Prompt | What to enter |
|--------|----------------|
| `PJM username` | Your PJM login name |
| `PJM password` | Your PJM password (hidden input) |
| `Path to login .p12/.pfx file` | Full path to your login certificate |
| `Certificate password` | Password for the PKCS#12 file (hidden input) |
| `Environment [TRAIN]` | Press Enter for TRAIN, or enter `PRODUCTION`, `TEST`, or `STAGE` |
| `Master password` | Password that encrypts `credentials.enc` (choose and remember this) |
| `Confirm master password` | Same master password again |

Init validates the certificate before saving. If the file is missing, public-only, or cannot be decrypted, init stops with an error.

If `~/.pjm/credentials.enc` already exists, init asks before overwriting. Use `pjm-api init --force` to skip the prompt in scripts.

## Verify

Run the full setup check:

```bash
pjm-api doctor
```

Expected output when everything works:

```
[1/4] credentials file             OK  (~/.pjm/credentials.enc)
[2/4] certificate file             OK  (expires 2027-03-15)
[3/4] SSO authentication           OK
[4/4] TRANSSERV smoke (TRAIN)      OK

All checks passed.
```

If you are waiting for CAM approval or cannot reach PJM yet, check local files only:

```bash
pjm-api doctor --offline
```

Offline doctor skips SSO and TRANSSERV. It still checks credentials, certificate path, certificate type, decryption, and expiration.

## First request

Run a TRANSSERV template query on TRAIN:

```bash
pjm-api template TRANSSERV
```

By default this prints a response preview to stdout. It does not save a file unless you ask:

```bash
pjm-api template TRANSSERV --outfile transserv.txt
pjm-api template TRANSSERV --save /tmp/transserv.txt
```

To save the response inside the downloads directory, use `--outfile`. To save to an exact path, use `--save`.

## Common mistakes

| Mistake | What happens | Fix |
|---------|----------------|-----|
| Using `.crt` or `.cer` instead of `.p12`/`.pfx` | Init or doctor rejects the file | Upload public cert to Account Manager; point init at the login `.p12`/`.pfx` |
| Wrong environment | SSO or TRANSSERV fails | Re-run `pjm-api init` with the correct environment, or use `--env` on CLI commands |
| Missing `[pfx]` extra | PKCS#12 cannot be read | `python -m pip install -e ".[pfx]"` |
| Wrong certificate password | Init or doctor fails on decrypt | Re-run init with the correct PKCS#12 password |
| CAM approval not complete | SSO passes certificate check locally but auth fails | Wait for CAM approval of the public cert in Account Manager |

## Next steps

- [Troubleshooting](troubleshooting.md) — error messages and fixes
- [Advanced](advanced.md) — Java CLI backend, other environments, Python API usage
- [SECURITY.md](../SECURITY.md) — what not to commit and how to report issues
