# Templates

Use the generic API:

```python
client.request("TRANSSERV", {"OUTPUT_FORMAT": "DATA", "VERSION": "3.3"})
```

## Output formats

CSV, DATA, XML, JSON, XLSX, HTML, XHTML, PROTO

## NAESB version

PJM documents support through NAESB WEQ 3.3. Do not assume WEQ 004 unless PJM publishes support.

## Catalog

```bash
pjm-api templates list
pjm-api templates info TRANSSERV
```

Authoritative rules: PJM Template Builder and Data Dictionary.
