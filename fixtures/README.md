# fixtures/

This is the home for **frozen HAR fixtures** — the real evidence artifacts the benchmark
runs on. Drop a `.har` file here:

```
fixtures/<descriptive-name>.har
```

e.g. `fixtures/acme-checkout-session.har` (lowercase, no spaces).

## What a fixture is (and isn't)

- **Frozen, and local by default.** A fixture is kept **byte-identical** so reruns are
  comparable months apart and across new model releases — but this directory is
  **git-ignored**: no captures are committed, because real ones carry personal data. Bring
  your own.
- **Real, not synthetic.** One real captured session beats a made-up scenario (see the
  project brief). This is deliberately *not* the same as [`tests/data/`](../tests/data),
  which holds throwaway sample HARs used only by this repo's conventional software tests.

## ⚠️ Redact before sharing

Fixtures stay local (git-ignored), but the moment a HAR leaves your machine — sent to a
provider, or committed if you ever choose to track one — it is exposed. Real HAR captures
routinely contain **auth tokens, cookies, session IDs, API keys, and personal data** in
headers and bodies. Before you run or share one:

- **`redact`** sensitive values (secrets), and **`pseudonymize`** domain PII (VINs, plates,
  addresses…) if present — or capture against a throwaway/test account.
- Only ever commit a capture you are comfortable being **public and permanent**.
- Note: preprocessing removes *non-JSON noise*, **not secrets** — it keeps request and
  response bodies. Redaction is on you, not the tool.

`preprocess` runs a mechanical **secrets/PII scan** over the raw HAR and warns you (a
safety guardrail — it never touches the cleaned evidence). It's heuristic: a clean result
is not a guarantee, and it can flag false positives. Get the full masked report with:

```
harcompanon preprocess fixtures/<name>.har -o /dev/null --security-report report.md
```

## How it's used

```
harcompanon preprocess fixtures/<name>.har
```

strips the HAR down to its JSON API calls (mechanical noise removal only) so it can be sent,
identically, to each model at each prompt. Preprocessing never interprets or highlights the
evidence.

## Provenance

No fixtures are committed to this repo. Keep your own one-line note per local capture — where
it came from, when, and how it was sanitised (`redact` / `pseudonymize`) — so a rerun months
later is still traceable.
