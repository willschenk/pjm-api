# Contributing

Thank you for contributing to pjm-api.

## Security

Never commit:

- `.env` files or credentials
- Certificate files (`.p12`, `.pfx`, `.pem`, `.key`, `.crt`)
- Private local scripts (`test.py`, `GUIDANCE.md`)

## Running tests

```bash
pip install -e ".[dev]"
pytest                    # unit + contract tests
pytest -m live            # opt-in live PJM tests (requires credentials)
```

Live tests require `PJM_LIVE_TEST=1` and valid `PJM_USERNAME`, `PJM_PASSWORD`, and `PJM_CERT` environment variables. Use TRAIN environment only for CI and development.

## Code style

- Run `ruff check .` and `ruff format .` before submitting
- Keep the core package stdlib-first; optional extras for heavier dependencies
- Match existing module conventions in `src/pjm_api/`
