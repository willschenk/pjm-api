# pjm-api

Python client for PJM OASIS. Unofficial — not affiliated with PJM.

## Quick start

**You need:** Python 3.10+, a login `.p12`/`.pfx` file (private key + cert), CAM-approved public cert in Account Manager.

```bash
git clone https://github.com/willschenk/pjm-api
cd pjm-api
pip install -e ".[pfx]"
pjm-api init
pjm-api doctor
pjm-api template TRANSSERV
```

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

PJM uses **two different files**. Mixing them up is the most common failure.

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

## CLI

```bash
pjm-api doctor                              # verify setup
pjm-api template TRANSSERV                  # print preview to stdout
pjm-api template TRANSSERV --outfile result.txt  # save to downloads/
pjm-api template TRANSSERV --save /tmp/result.txt  # save to exact path
pjm-api template TRANSSERV --env PRODUCTION # production (advanced)
pjm-api credentials show                    # redacted summary
```

## Troubleshooting

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

See [docs/troubleshooting.md](docs/troubleshooting.md) for error messages.

## Advanced

Java CLI backend, TEST/STAGE environments, live tests: [docs/advanced.md](docs/advanced.md)

## Sources

Based on publicly posted PJM/NAESB documentation. Authoritative specs: [PJM eTools](https://www.pjm.com/markets-and-operations/etools).
