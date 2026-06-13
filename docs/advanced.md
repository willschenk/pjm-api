# Advanced

The normal path is documented in the README:

```bash
python -m pip install -e ".[pfx]"
pjm-api init
pjm-api doctor
```

Use this page only for fallback and automation scenarios.

## Java CLI backend

The Java CLI backend is the default backend. It matches PJM's CLI behavior and is the recommended path for normal OASIS requests.

Install the PJM CLI zip into a local directory:

```bash
pjm-api cli install --dir ~/.pjm/cli
```

The default install path, `~/.pjm/cli/pjm-cli.jar`, is auto-detected. Set `PJM_CLI_JAR_PATH` only when the jar lives somewhere else.

Run a smoke test through the CLI backend:

```bash
pjm-api smoke
```

Requires Java 8 or newer. Override Java with `PJM_CLI_JAVA_PATH` or `--java-path` when `java` is not on PATH.

Use the native backend only when you intentionally want the Python mTLS implementation:

```bash
PJM_BACKEND=native pjm-api smoke
pjm-api template TRANSSERV --backend native
```

## Environments

| Name | URL |
|------|-----|
| TRAIN | `https://oasisrefreshtrain.pjm.com/OASIS/` |
| PRODUCTION | `https://pjmoasis.pjm.com/OASIS/` |
| TEST | blank by default; pass a private URL with `--oasis-url` or `PJM_OASIS_URL` |
| STAGE | blank by default; pass a private URL with `--oasis-url` or `PJM_OASIS_URL` |

Use one of:

```bash
pjm-api doctor --env PRODUCTION
PJM_ENV=PRODUCTION pjm-api doctor
pjm-api smoke --env TEST --oasis-url https://private.example/OASIS/
```

Start in `TRAIN`. Move to `PRODUCTION` only after `pjm-api doctor` passes in training.

Production read requests print a warning. Production write or reservation-style actions are blocked unless you set `PJM_ALLOW_PRODUCTION_WRITE=1` or pass `--allow-production-write`. Disable only the warning with `PJM_DISABLE_PRODUCTION_WARNING=1` or `--no-production-warning`.

## Plain environment fallback

Encrypted credentials from `pjm-api init` are preferred. Plain environment variables remain available for controlled automation and compatibility.

```bash
cp .env.example .env
```

The encrypted credentials file takes precedence over `.env` unless settings are supplied directly by CLI arguments.

## Certificate formats

Preferred:

```text
.p12 or .pfx containing both private key and certificate
```

Currently supported PEM shape:

```text
one PEM file containing both the certificate and the private key
```

Separate certificate and private-key paths are not yet wired through the public configuration loader. Do not document or rely on `PJM_KEY_PATH` until code support and tests are added.

## Live integration tests

Live tests require real PJM access and must be explicitly enabled.

```bash
export PJM_LIVE_TEST=1
pytest tests/live
```

Use a local encrypted credentials file or controlled environment variables. Do not commit certificates.

## Template catalog

```bash
pjm-api templates list
pjm-api templates info TRANSSERV
```

## Rotate local master key

```bash
pjm-api credentials rotate-password
```
