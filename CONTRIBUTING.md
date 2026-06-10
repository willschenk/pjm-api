# Contributing

## Setup

```bash
python -m pip install -e ".[dev,pfx]"
```

Optional, recommended before committing:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Local checks

Run these before pushing:

```bash
ruff check .
mypy src/pjm_api
pytest tests/ -m "not live"
```

`ruff format .` fixes formatting if pre-commit is not installed.

## Live tests

Live tests are opt-in. They do not run in CI or during normal `pytest` runs.

- Require real PJM access and valid TRAIN credentials
- Use `PJM_LIVE_TEST=1` to enable the `live` marker
- Use TRAIN only

```bash
export PJM_LIVE_TEST=1
export PJM_MASTER_PASSWORD=...
pytest tests/ -m live
```

Or:

```bash
make doctor-live
```

## Credential safety

Never commit certificates, keys, or local credential files.

Do not add to git:

- `.env`
- `.p12`, `.pfx`, `.pem`, `.crt`, `.cer`, `.key`
- `credentials.enc`

In tests, use temporary paths via `PJM_CREDENTIALS_FILE`. See [SECURITY.md](SECURITY.md) for the full list and reporting process.

## Commit style

- Short imperative subject line: `Fix credential unlock behavior for doctor commands`
- One focused change per commit
- Run local checks before committing

## Documentation style

Keep docs direct and plain.

- State what the user should do and what happens
- Avoid hype, filler, and AI-sounding language
- Prefer short examples over long explanations

## Main branch rule

For this project, work directly on `main` unless told otherwise. Do not open feature branches or pull requests unless the maintainer asks for them.
