# Contributing

## Setup

```bash
pip install -e ".[dev,pfx]"
pytest tests/ -m "not live"
```

## Credentials in tests

Use temporary `PJM_CREDENTIALS_FILE` paths — never commit real credentials.

## Live tests

```bash
export PJM_LIVE_TEST=1
export PJM_MASTER_PASSWORD=...
make doctor-live
```

Use TRAIN only. Never commit `.p12`, `.env`, or `credentials.enc`.
