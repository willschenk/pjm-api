# pjm-api

Python client for PJM OASIS. Unofficial — not affiliated with PJM.

## Quick start

**Full walkthrough:** [docs/setup.md](docs/setup.md) — zero to first TRANSSERV call.

**You need:** Python 3.10+, a login `.p12`/`.pfx` file (private key + cert), CAM-approved public cert in Account Manager.

```bash
git clone https://github.com/willschenk/pjm-api
cd pjm-api
python -m pip install -e ".[pfx]"
pjm-api init
pjm-api doctor
pjm-api template TRANSSERV
```

No network yet? Run `pjm-api doctor --offline` to check local credentials and certificate only.

Expected `doctor` output:

```
[1/4] credentials file             OK  (~/.pjm/credentials.enc)
[2/4] certificate file             OK  (expires 2027-03-15)
[3/4] SSO authentication           OK
[4/4] TRANSSERV smoke (TRAIN)      OK

All checks passed.
```

### Setup flow

```mermaid
sequenceDiagram
    participant You
    participant Init as pjm_api_init
    participant File as credentials_enc
    participant PJM as PJM_SSO

    You->>Init: pjm-api init
    Init->>You: username password cert path
    Init->>File: encrypt and save
    You->>Init: pjm-api doctor
    Init->>File: decrypt
    Init->>PJM: mTLS plus credentials
    PJM-->>Init: tokenId
    Init-->>You: PASS
```

## Certificates

PJM uses two certificate files. Do not point init at a public `.crt` or `.cer`.

```mermaid
flowchart LR
    subgraph wrong [Wrong for pjm-api]
        PublicCert[".cer / .crt\npublic key only"]
    end
    subgraph right [Correct for pjm-api]
        P12[".p12 / .pfx\nprivate key plus cert"]
    end
    PublicCert -->|"Upload here"| AM[Account Manager]
    P12 -->|"Set at pjm-api init"| Login[Runtime login]
```

| File | Use |
|------|-----|
| `.cer` / `.crt` | Upload to Account Manager (public key only) |
| `.p12` / `.pfx` | Point `pjm-api init` here (login file) |

## Python

```python
from pjm_api import OasisClient, load_settings

with OasisClient(load_settings()) as client:
    print(client.smoke_transserv().text()[:500])
```

See [docs/python-usage.md](docs/python-usage.md) for template queries, saving responses, and credential handling.

## CLI

```bash
pjm-api doctor                              # verify setup (network checks)
pjm-api doctor --offline                    # local credentials and cert only
pjm-api smoke                               # TRANSSERV smoke test
pjm-api template TRANSSERV                  # print preview to stdout
pjm-api template TRANSSERV --preview-chars 500  # shorter preview
pjm-api template TRANSSERV --outfile result.txt  # save to downloads/
pjm-api template TRANSSERV --save /tmp/result.txt  # save to exact path
pjm-api template TRANSSERV --env PRODUCTION # production (see advanced docs)
pjm-api credentials show                    # redacted summary
```

## Troubleshooting

```bash
pjm-api doctor --offline
```

```mermaid
flowchart TD
    start[doctor failed] --> s1{credentials file?}
    s1 -->|no| f1["pjm-api init"]
    s1 -->|yes| s2{cert file exists?}
    s2 -->|no| f2["re-run pjm-api init with correct path"]
    s2 -->|yes| s3{file is .p12 not .crt?}
    s3 -->|no| f3["use login .p12 not public .crt"]
    s3 -->|yes| s4{CAM approved cert?}
    s4 -->|no| f4["wait for CAM approval"]
    s4 -->|yes| f5["check username and password"]
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for error messages and fixes.

## Documentation

- [Setup walkthrough](docs/setup.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Python usage](docs/python-usage.md)
- [Advanced](docs/advanced.md)
- [Security](SECURITY.md)

## Advanced

Java CLI backend, TEST/STAGE environments, live tests: [docs/advanced.md](docs/advanced.md)

## Sources

Based on publicly posted PJM/NAESB documentation. Authoritative specs: [PJM eTools](https://www.pjm.com/markets-and-operations/etools).
