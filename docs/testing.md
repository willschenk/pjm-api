# Testing

## Unit and contract (CI)

```bash
pytest tests/ -m "not live"
```

## Live integration (opt-in)

Requires real PJM credentials and TRAIN access:

```bash
export PJM_LIVE_TEST=1
export PJM_USERNAME=...
export PJM_PASSWORD=...
export PJM_CERT=/path/to/cert.p12
export PJM_CERT_PASSWORD=...
pytest tests/live -m live
```

Never run live tests against PRODUCTION in CI.
