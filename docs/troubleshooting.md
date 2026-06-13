# Troubleshooting

Every error prints a `Fix:` line. Start with `pjm-api doctor`.

## Credentials

| Error | Fix |
|-------|-----|
| Credentials file not found | `pjm-api init` |
| Wrong master password | Re-enter password or `pjm-api credentials rotate-password` |
| Missing: username, password, cert_path | `pjm-api init` |
| PJM CLI jar not configured | `pjm-api cli install --dir ~/.pjm/cli`, or set `PJM_CLI_JAR_PATH=/path/to/pjm-cli.jar` |
| Java runtime not found | Install Java 8+ or set `PJM_CLI_JAVA_PATH=/path/to/java` |

## Certificate

| Error | Fix |
|-------|-----|
| Certificate not found | Re-run `pjm-api init` with correct path |
| Public certificate only | Use `.p12` login file, not `.crt` from Account Manager |
| PKCS#12 requires [pfx] extra | `pip install pjm-api[pfx]` |
| Certificate expired | Renew cert with your CA, update path in init |
| Failed to decrypt PKCS#12 | Check certificate password |

## Authentication

| Error | Fix |
|-------|-----|
| Authentication failed (401) | Check username and password |
| No tokenId in response | Verify CAM approved your public cert in Account Manager |
| SSO authentication FAIL in doctor | Same as above; confirm TRAIN vs PRODUCTION env |

## OASIS

| Error | Fix |
|-------|-----|
| OASIS request failed (4xx) | Check template params; run `pjm-api templates info NAME` |
| TRANSSERV smoke FAIL | Run `pjm-api doctor` first; fix earlier steps |
| OASIS URL for TEST/STAGE is not public | Pass `--oasis-url` or set `PJM_OASIS_URL` to your private URL |
| Blocked PRODUCTION write/reservation action | Use TRAIN, or set `PJM_ALLOW_PRODUCTION_WRITE=1` only for intentional production writes |

## Still stuck?

1. `pjm-api credentials show` — confirm username and cert path
2. `pjm-api doctor` — find which step fails
3. Confirm public cert is CAM-approved in Account Manager
4. Confirm login `.p12` matches the approved public cert
