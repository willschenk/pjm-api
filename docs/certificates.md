# Certificates

## Account Manager vs runtime login

| Purpose | File type | Contains private key? |
|---------|-----------|------------------------|
| Account Manager upload | `.cer`, `.crt` (public) | No |
| Runtime login | `.p12`, `.pfx` | Yes |

## Export from PKCS#12

```bash
openssl pkcs12 -in cert.p12 -clcerts -nokeys -out public.crt
openssl pkcs12 -in cert.p12 -nocerts -out private.key
```

## Inspection

```bash
pjm-api cert-doctor --cert /path/to/cert.p12
pjm-api cert-doctor --json
```

Install PKCS#12 support: `pip install pjm-api[pfx]`
