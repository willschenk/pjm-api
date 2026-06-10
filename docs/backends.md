# Backends

## Native (default)

Pure Python using stdlib `ssl` and `urllib`. No Java required.

```bash
PJM_BACKEND=native pjm-api smoke --env TRAIN
```

Requires `pip install pjm-api[pfx]` for `.p12`/`.pfx` files.

## CLI fallback

Official PJM Java CLI via subprocess.

```bash
PJM_BACKEND=cli PJM_CLI_JAR_PATH=/path/pjm-cli.jar pjm-api smoke
```

**Note:** CLI backend passes credentials on the subprocess command line. Prefer native when possible.

Install JAR manually or: `pjm-api cli install --dir ~/.pjm/cli`
