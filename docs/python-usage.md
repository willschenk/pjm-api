# Python usage

Use pjm-api from Python after completing [setup](setup.md). The default Python path uses PJM's Java CLI through `CliBackend`.

## Prerequisites

Run `pjm-api init` first. `load_settings()` reads credentials from, in order:

1. Function arguments
2. Encrypted file (`~/.pjm/credentials.enc`)
3. Environment variables

Do not hard-code usernames, passwords, certificate paths, or certificate passwords in scripts.

## Smoke test

```python
from pjm_api import CliBackend, load_settings

backend = CliBackend(load_settings())
ok = backend.smoke_test()
print("TRANSSERV:", "OK" if ok else "FAIL")
```

`load_settings()` uses `PJM_CLI_JAR_PATH` or the `jar_path=` argument for the local `pjm-cli.jar`.

## Template request

Query TRANSSERV with explicit parameters:

```python
from pjm_api import CliBackend, load_settings

params = {
    "OUTPUT_FORMAT": "DATA",
    "PRIMARY_PROVIDER_CODE": "PJM",
    "PRIMARY_PROVIDER_DUNS": "073647877",
    "RETURN_TZ": "EP",
    "VERSION": "3.3",
}

backend = CliBackend(load_settings())
result = backend.run_template(template="TRANSSERV", params=params, outfile="transserv.txt")
print("returncode:", result.returncode)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
```

Override the environment if needed:

```python
settings = load_settings(environment="TRAIN")
backend = CliBackend(settings)
backend.run_template(template="TRANSSERV", params=params, outfile="transserv.txt")
```

## Save response to file

```python
from pjm_api import CliBackend, load_settings

backend = CliBackend(load_settings(downloads_dir="downloads"))
result = backend.run_template(
    template="TRANSSERV",
    params={"OUTPUT_FORMAT": "DATA"},
    outfile="transserv.txt",
)
print(f"Saved: {result.output_file}")
```

The Java CLI writes files under the configured downloads directory.

## Native backend

The native Python backend is still available for advanced use:

```python
from pjm_api import OasisClient, load_settings

with OasisClient(load_settings(backend="native")) as client:
    response = client.smoke_transserv()
    print(response.text()[:500])
```

## Notes

- Use `CliBackend` for the default Java CLI path.
- Use `with OasisClient(...) as client:` only for the advanced native backend.
- Set `PJM_MASTER_PASSWORD` in the environment to unlock encrypted credentials without a prompt.
- Run `pjm-api doctor` before debugging Python scripts.
- For template parameter hints, see `pjm_api.templates.suggest_params()` or `pjm-api templates info TRANSSERV`.
- Production writes are blocked by default. Set `PJM_ALLOW_PRODUCTION_WRITE=1` only for intentional production write/reservation actions.
