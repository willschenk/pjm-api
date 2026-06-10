# Advanced

## Java CLI backend

```bash
PJM_BACKEND=cli PJM_CLI_JAR_PATH=/path/pjm-cli.jar pjm-api smoke
```

Requires Java 8+. Install JAR: `pjm-api cli install --dir ~/.pjm/cli`

**Warning:** CLI backend passes passwords on the subprocess command line. Prefer native backend.

## Environments

| Name | URL |
|------|-----|
| TRAIN | `https://oasis.ac1train.pjm.com/OASIS/` |
| PRODUCTION | `https://pjmoasis.pjm.com/OASIS/` |
| TEST | `https://oasis.test.pjm.com/OASIS/` |
| STAGE | `https://oasis.ac1stage.pjm.com/OASIS/` |

Override: `--env PRODUCTION` or `PJM_ENV=PRODUCTION`

## Plain .env fallback (deprecated)

```bash
cp .env.example .env
# edit PJM_USERNAME, PJM_PASSWORD, PJM_CERT, PJM_CERT_PASSWORD
```

Encrypted credentials (`pjm-api init`) take precedence over `.env`.

## PEM cert/key (no PKCS#12)

Set in `.env`:

```
PJM_CERT_PATH=/path/to/cert.pem
PJM_KEY_PATH=/path/to/key.pem
```

## Live integration tests

```bash
export PJM_LIVE_TEST=1
export PJM_MASTER_PASSWORD=...
make doctor-live
```

## Template catalog

```bash
pjm-api templates list
pjm-api templates info TRANSSERV
```

## Master password for automation

```bash
export PJM_MASTER_PASSWORD=...   # skips interactive unlock prompt
```

Use only in secure CI environments.

## Rotate master password

```bash
pjm-api credentials rotate-password
```
