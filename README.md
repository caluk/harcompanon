# harcompañon

A small, reproducible tool that compares how different LLMs behave as **testing companions**
when handed the *same* real evidence and the *same* prompt.

It is **not** a coding benchmark, **not** a capability leaderboard, and **not** about
generating automated checks. It measures **judgment quality** in the vocabulary of
[Rapid Software Testing (RST)](docs/rst-glossary.md): testing vs. checking, oracles, sapience.
See [docs/methodology.md](docs/methodology.md) for the construct and the caveats.

## The question it answers

When a human is testing something and is *equipped with* an LLM, does that human + AI
combination reach higher, better-grounded confidence? A **good** companion surfaces risk and
invites continued scrutiny. A **bad** one produces plausible-sounding text that invites the
human to stop looking. That difference is the thing being measured.

The word *companion* is deliberate. The model is an **instrument inside a human's sapient
process**, never a "tester." Testing requires sapience and accountability that an AI cannot
hold — so **the human is always the sole judge** of response quality. The tool only prepares the
evidence and lays the responses side by side; it never scores or judges.

## How it works

```
HAR fixture ─▶ preprocess ──▶ run (providers × prompts) ──▶ per-response JSON + compare.html
   │            (strip noise,        stateless API calls          (side-by-side matrix,
   │             keep envelope)                                    auto-built on a clean run)
   ├─ redact ─▶ (mask secrets)
   └─ security scan (safety)
```

- **Preprocess** — mechanical noise removal only: keep every call's *envelope* (method, URL,
  status, timing, curated headers) and its JSON bodies; strip heavy/binary/oversized bodies to
  a `<stripped: …>` marker. It never interprets or highlights the evidence. A built-in
  **secrets/PII scan** warns you about anything sensitive in the raw HAR.
- **Redact** — mask every scanner-detected secret value with `<REDACTED>`, producing a copy
  that is safe to commit *and* safe to send to models. (Heuristic — eyeball before publishing.)
- **Prompts** — versioned, so the *effect of an intervention* is measurable, not a single number:
  - `minimal` — bare ("what do you notice?"); no role, no structure.
  - `structured` — a required output shape: an **Overall picture** (a product model), findings
    each with an oracle and possible impact, systemic observations, the questions only a human
    can answer, coverage depth, and a self-critique.
  The `minimal→structured` gap isolates what the structure adds.
- **Providers** — Claude, OpenAI, Gemini, DeepSeek, Mistral, Kimi behind one small abstraction;
  adding a model is one class + one registry entry. Calls are stateless (comparable months
  apart). Keys load from a git-ignored `.env` (see `.env.example`).
- **A run** = one frozen fixture × the chosen providers × the chosen prompt modes. Everything is
  flat files — no database.
- **Compare** — renders a run as a self-contained `compare.html` matrix (models × prompt modes)
  with each response's latency, tokens and cost alongside, for side-by-side reading. It's a
  comparison surface, not a score. Auto-built when a live run finishes error-free;
  `harcompanon compare <run-dir>` rebuilds it (e.g. after `retry`).

## CLI

```bash
harcompanon preprocess <har> [-o out.json] [--security-report r.md]  # clean + scan a HAR
harcompanon redact <har> [-o out.har]                                # mask detected secrets
harcompanon pseudonymize <har> [-o out.har] [--exclude KEY]          # swap domain PII for synthetic
harcompanon run <fixture> [-p anthropic ...] [--modes ...] [--prompt-version v4]  # a run
                          [--model M] [--max-tokens N] [--out runs]  #   (--dry-run/--live)
harcompanon compare <run-dir>     # -> compare.html  (matrix; auto-built on error-free live runs)
harcompanon retry <run-dir>       # re-run only the errored responses, back into the same run
```

`run` is **live by default**; pass `--dry-run` to render the prompts and exercise the whole
pipeline without spending a token. Providers default to `anthropic`; repeat `-p` for more.

## Quickstart (dev)

```bash
pip install -e ".[dev]"
cp .env.example .env          # then add your provider keys (never committed)

harcompanon run fixtures/your-capture.har --dry-run           # no API call, no spend
harcompanon run fixtures/your-capture.har --live -p anthropic # one real run -> compare.html
harcompanon compare runs/<run-id>                             # rebuild the matrix if needed
```

You supply your own HAR — capture one from a site you're testing (DevTools → Network →
"Save all as HAR"), then `redact` (and `pseudonymize` if it holds domain PII) before use.

## Fixtures

Frozen HAR captures live in [`fixtures/`](fixtures) and are **git-ignored by default** — no
captures are committed, since real ones carry personal data. Bring your own: if it comes from
a real system, **`redact` it and review it** before it goes anywhere public. See
[fixtures/README.md](fixtures/README.md).

## Status

Pre-alpha, exploratory. The pipeline is intentionally small: prepare the evidence, run the same
prompt across models, and lay the responses side by side for a human to judge.

## Two senses of "testing" — keep them separate

Throughout this project, **"testing" means the RST sense** (the human, sapient activity the
tool studies). This repo *also* has ordinary **software tests** (`pytest`, under `tests/`),
which are *checks* on the code. The two are kept visibly distinct in code, docs, and commit
messages. See the [glossary](docs/rst-glossary.md).

## License

[MIT](LICENSE).
