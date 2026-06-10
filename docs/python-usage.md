# Python usage

Use pjm-api from Python after completing [setup](setup.md).

## Prerequisites

Run `pjm-api init` first. `load_settings()` reads credentials from, in order:

1. Function arguments
2. Encrypted file (`~/.pjm/credentials.enc`)
3. Environment variables

Do not hard-code usernames, passwords, or certificate paths in scripts.

## Smoke test

```python
from pjm_api import OasisClient, load_settings

with OasisClient(load_settings()) as client:
    response = client.smoke_transserv()
    print(response.text()[:500])
```

`OasisClient` as a context manager authenticates on entry and logs out on exit.

## Template request

Query TRANSSERV with explicit parameters:

```python
from pjm_api import OasisClient, load_settings

params = {
    "OUTPUT_FORMAT": "DATA",
    "PRIMARY_PROVIDER_CODE": "PJM",
    "PRIMARY_PROVIDER_DUNS": "073647877",
    "RETURN_TZ": "EP",
    "VERSION": "3.3",
}

with OasisClient(load_settings()) as client:
    response = client.request("TRANSSERV", params)
    print(response.text()[:1000])
```

Override the environment if needed:

```python
settings = load_settings(environment="TRAIN")
with OasisClient(settings) as client:
    response = client.request("TRANSSERV", params)
```

## Save response to file

```python
from pathlib import Path

from pjm_api import OasisClient, load_settings

output = Path("downloads/transserv.txt")

with OasisClient(load_settings()) as client:
    response = client.request("TRANSSERV", {"OUTPUT_FORMAT": "DATA"})
    saved = response.save(output)
    print(f"Saved: {saved}")
```

`response.save()` creates parent directories and writes raw response bytes.

## Notes

- Use `with OasisClient(...) as client:` so logout runs when the block ends.
- Set `PJM_MASTER_PASSWORD` in the environment to unlock encrypted credentials without a prompt.
- Run `pjm-api doctor` before debugging Python scripts.
- For template parameter hints, see `pjm_api.templates.suggest_params()` or `pjm-api templates info TRANSSERV`.
