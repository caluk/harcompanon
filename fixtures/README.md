# fixtures/

This is the home for **frozen HAR fixtures** — the real evidence artifacts the benchmark
runs on. Drop a `.har` file here:

```
fixtures/<descriptive-name>.har
```

e.g. `fixtures/acme-checkout-session.har` (lowercase, no spaces).

## What a fixture is (and isn't)

- **Frozen and committed.** A fixture is checked into the repo **byte-identical** and never
  changes. That is what makes reruns comparable months apart, and across new model releases.
- **Real, not synthetic.** One real captured session beats a made-up scenario (see the
  project brief). This is deliberately *not* the same as [`tests/data/`](../tests/data),
  which holds throwaway sample HARs used only by this repo's conventional software tests.

## ⚠️ Redact before committing

This is a **public repo**, and a fixture is committed as-is. Real HAR captures routinely
contain **auth tokens, cookies, session IDs, API keys, and personal data** in headers and
bodies. Before adding a fixture:

- Only commit a capture you are comfortable being **public and permanent**.
- **Redact** sensitive values first (or capture against a throwaway/test account).
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

One line per fixture — where it came from.

- `dash.har` — captured 2026-06-18 from the **public OrangeHRM demo**
  (`opensource-demo.orangehrmlive.com`), admin session, Dashboard page load. Throwaway demo
  data. Security scan: 0 high / 0 medium (1 low = a vendor support email baked into
  OrangeHRM's own public `app.js`). ~4 MB. The primary fixture — 7 distinct dashboard
  endpoints (time-at-work, action-summary, shortcuts, Buzz feed, leaves, subunit, locations).
- `perf.har` — same session/source, navigated to the Performance module. Secondary fixture;
  note the `workweek` and `holidays` calls each fire twice (a curious quirk to scrutinise).

Both are safe to commit: public demo, no real user data. If you add a fixture from a real
system, redact it first (see the warning above).
