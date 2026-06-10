# Advanced

The normal path is documented in the README:

```bash
python -m pip install -e ".[pfx]"
pj m-api init
pjm-api doctor
```

Use this page only for fallback and automation scenarios.

## Java CLI backend

Native Python is the default backend. Use the Java CLI backend only when you need to match PJM's CLI behavior exactly.

Install the PJM CLI zip into a local directory:

```bash
pjm-api cli install --dir ~/.pjm/cli
```

Run a smoke test through the CLI backend:

```bash
PJM_BACKEND=cli PJM_CLI_JAR_PATH=/path/to/pjm-cli.jar pjm-api smoke
```

Requires Java 8 or newer.

Warning: the CLI backend passes secrets to a subprocess. Prefer the native backend for normal use.

## Environments

| Name | URL |
|------|-----|
| TRAIN | `https://oasis.ac1train.pjm.com/OASIS/` |
| PRODUCTION | `https://pjmoasis.pjm.com/OASIS/` |
| TEST | `https://oasis.test.pjm.com/OASIS/` |
| STAGE | `https://oasis.ac1stage.pjm.com/OASIS/` |

Use one of:

```bash
pjm-api doctor --env PRODUCTION
PJM_ENV=PRODUCTION pjm-api doctor
```

Start in `TRAIN`. Move to `PRODUCTION` only after `pjm-api doctor` passes in training.

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

Use a local encrypted credentials file or controlled environment variables. Do not commit secrets or certificates.

## Template catalog

```bash
pjm-api templates list
pjm-api templates info TRANSSERV
```

## Rotate local master key

```bash
pjm-api credentials rotate-password
```
