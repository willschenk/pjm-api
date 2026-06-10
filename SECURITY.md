# Security

## Never commit these files

Do not add these to git, paste them in issues, or share them in chat:

- `.env`
- `.p12`, `.pfx`, `.pem`, `.crt`, `.cer`, `.key`
- `credentials.enc`

They contain PJM login credentials, private keys, or certificate passwords.

## Local credentials storage

`pjm-api init` stores your PJM username, password, certificate path, certificate password, and environment in an encrypted file at `~/.pjm/credentials.enc` (or the path in `PJM_CREDENTIALS_FILE`).

The file is encrypted with a master password you choose at init time. Anyone with the master password can decrypt it. Protect that password the same way you would protect your PJM login.

## Certificates: two different files

PJM uses two certificate roles:

| File | Where it goes |
|------|----------------|
| `.cer` / `.crt` (public only) | Upload to **PJM Account Manager** for CAM approval |
| `.p12` / `.pfx` (private key + cert) | Keep local; point `pjm-api init` at this login file |

Public certificates are not login credentials. The `.p12`/`.pfx` login file must stay on your machine and out of version control.

## Reporting security issues

If you find a vulnerability in pjm-api:

1. **Preferred:** open a [private security advisory](https://github.com/willschenk/pjm-api/security/advisories/new) on GitHub if repository security advisories are enabled.
2. **Otherwise:** contact the repository maintainer directly through a private channel (do not file a public issue with exploit details).

Please include steps to reproduce, affected versions, and impact. We will acknowledge receipt and work on a fix before public disclosure when possible.
