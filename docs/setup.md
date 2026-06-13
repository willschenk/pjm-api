# Setup walkthrough

Follow this guide from zero to your first successful TRANSSERV call on TRAIN.

## What you need before starting

- **Python 3.10+**
- **Java 8+**
- **PJM Java CLI** — local `pjm-cli.jar`
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

The `[pfx]` extra installs PKCS#12 support for local certificate inspection and the optional native Python backend. The default request path uses PJM's Java CLI.

Confirm the CLI is available:

```bash
pjm-api --help
```

Install the PJM CLI jar or point to an existing copy:

```bash
pjm-api cli install --dir ~/.pjm/cli
```

`~/.pjm/cli/pjm-cli.jar` is auto-detected. If your jar is somewhere else, set `PJM_CLI_JAR_PATH=/path/to/pjm-cli.jar` or pass `--jar-path`.

If you prefer a live Python walkthrough, open [../pjm_oasis_cli_quickstart.ipynb](../pjm_oasis_cli_quickstart.ipynb) and run it top to bottom after setting the same jar, credential, and certificate values.

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
[1/3] credentials file             OK  (~/.pjm/credentials.enc)
[2/3] certificate file             OK  (expires 2027-03-15)
[3/3] TRANSSERV smoke (TRAIN)      OK

All checks passed.
```

If you are waiting for CAM approval or cannot reach PJM yet, check local files only:

```bash
pjm-api doctor --offline
```

Offline doctor skips network checks. It still checks credentials, certificate path, certificate type, decryption, and expiration when local inspection support is installed.
For the default CLI backend it also checks Java and the local `pjm-cli.jar`.

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

Production read requests show a warning. Production write or reservation-style actions are blocked unless you pass `--allow-production-write` or set `PJM_ALLOW_PRODUCTION_WRITE=1`.

`TEST` and `STAGE` are valid environment names but have blank URLs by default. Use `--oasis-url` or `PJM_OASIS_URL` if you have a private URL:

```bash
pjm-api smoke --env TEST --oasis-url https://private.example/OASIS/
```

## API call options

```bash
pjm-api guide
```

This lists smoke tests, template queries, parameter hints, and every template in the catalog.

## Common mistakes

| Mistake | What happens | Fix |
|---------|----------------|-----|
| Using `.crt` or `.cer` instead of `.p12`/`.pfx` | Init or doctor rejects the file | Upload public cert to Account Manager; point init at the login `.p12`/`.pfx` |
| Wrong environment | SSO or TRANSSERV fails | Re-run `pjm-api init` with the correct environment, or use `--env` on CLI commands |
| Missing CLI jar | CLI backend cannot start | Run `pjm-api cli install --dir ~/.pjm/cli`, set `PJM_CLI_JAR_PATH`, or pass `--jar-path` |
| Missing Java | CLI backend cannot start | Install Java 8+ or set `PJM_CLI_JAVA_PATH` |
| Missing `[pfx]` extra | PKCS#12 cannot be read | `python -m pip install -e ".[pfx]"` |
| Wrong certificate password | Init or doctor fails on decrypt | Re-run init with the correct PKCS#12 password |
| CAM approval not complete | SSO passes certificate check locally but auth fails | Wait for CAM approval of the public cert in Account Manager |

## Next steps

- [Troubleshooting](troubleshooting.md) — error messages and fixes
- [Advanced](advanced.md) — Java CLI backend, other environments, Python API usage
- [SECURITY.md](../SECURITY.md) — what not to commit and how to report issues
