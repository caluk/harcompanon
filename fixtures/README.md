# Local fixtures

Keep frozen HAR captures here, for example `fixtures/checkout.har`. HAR files and PNG
screenshots in this directory are git-ignored; no real captures are tracked. The synthetic
HARs in [`tests/data/`](../tests/data) exist only to check the repository's code.

## Prepare before use

HARs can contain credentials, cookies, personal data, and identifiers in URLs, headers,
and bodies. Sending one to a provider exposes that data just as sharing the file does.

```bash
harcompanon redact fixtures/checkout.har
# If needed, pseudonymize domain PII as well:
harcompanon pseudonymize fixtures/checkout.redacted.har
harcompanon preprocess fixtures/checkout.redacted.pseudo.har -o /dev/null --security-report /tmp/harcompanon-security.md
```

Review the resulting HAR before running or sharing it:

- `redact` replaces scanner-detected values with `<REDACTED>`. The scanner is heuristic;
  encoded bodies and unrecognized fields can retain sensitive data. A clean scan is not
  proof of safety. Literal replacements can affect matching text elsewhere, too.
- `pseudonymize` replaces recognized string identifiers with synthetic values. Numeric
  values, including coordinates, remain unchanged; free-text names may remain. Cities and
  dealer names can collapse to fixed labels, and generated names can collide, so relationships
  may change. `--exclude KEY` leaves that key out of key-based replacement; UUID/VIN patterns
  can still change its value.
- Preprocessing keeps call envelopes and JSON bodies, with size limits and selected headers.
  It masks known sensitive headers but does not sanitize body/query secrets. The `preprocess`
  command scans separately; `run` does not perform that scan.

Keep the reviewed fixture byte-identical for reruns. Record where and when it was captured
and how it was transformed in a private provenance note. Keep the original for human review;
only publish captures and outputs you are comfortable making public permanently.
