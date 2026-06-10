# Authentication

PJM browserless authentication uses PKI mTLS:

1. Establish two-way SSL with your login-time certificate (`.p12`/`.pfx`)
2. POST credentials to the SSO certificate-auth endpoint
3. Receive a `tokenId` in JSON
4. Send `Cookie: pjmauth={tokenId}` on OASIS requests
5. Log out when finished

## SSO endpoints

| Environment | URL |
|-------------|-----|
| TRAIN | `https://sotrain.pjm.com/access/authenticate/pjmauthcert` |
| PRODUCTION | `https://sso.pjm.com/access/authenticate/pjmauthcert` |

Override with `PJM_SSO_URL` if needed.

## Legacy note

The 2015–2016 browserless guide used username/password-only SSO. Current PKI guide supersedes it for authentication, though session cookie shape remains useful.
