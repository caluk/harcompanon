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
hold — so **the human is always the sole judge** of response quality. The tool may perform
mechanical **post-processing** (structural checks, descriptive summaries); it never judges.

## How it works

```
HAR fixture ─▶ preprocess ──▶ run (providers × prompts) ──▶ per-response JSON + comparison index
   │            (strip noise,        stateless API calls              │
   │             keep envelope)                                       ▼
   ├─ redact ─▶ (mask secrets)                    check ──▶ judge ──▶ closeout ──▶ summary
   └─ security scan (safety)             (structural,   (YOU judge)  (5 debrief   (descriptive
                                          not a verdict)             questions)    indicators)
```

- **Preprocess** — mechanical noise removal only: keep every call's *envelope* (method, URL,
  status, timing, curated headers) and its JSON bodies; strip heavy/binary/oversized bodies to
  a `<stripped: …>` marker. It never interprets or highlights the evidence. A built-in
  **secrets/PII scan** warns you about anything sensitive in the raw HAR.
- **Redact** — mask every scanner-detected secret value with `<REDACTED>`, producing a copy
  that is safe to commit *and* safe to send to models. (Heuristic — eyeball before publishing.)
- **Prompts** — three versioned tiers, so the *effect of an intervention* is measurable, not a
  single number:
  - `minimal` — bare ("what looks strange here?"); no role, no structure.
  - `briefed` — assigns the instrument role + a session-based, pre-go-live situation.
  - `structured` — a required output shape: a labelled **oracle** per finding, hypotheses (not
    findings), the questions only a human can answer, and a self-critique.
  The `minimal→briefed` gap isolates role + situation; `briefed→structured` isolates structure.
- **Providers** — Claude, OpenAI, Gemini, DeepSeek, Mistral, Kimi behind one small abstraction;
  adding a model is one class + one registry entry. Calls are stateless (comparable months
  apart). Keys load from a git-ignored `.env` (see `.env.example`).
- **A run** = one frozen fixture × the chosen providers × the chosen prompt modes. Everything is
  flat files — no database.
- **Check / judge / closeout / summary** — post-run: a mechanical structural checklist, a
  low-friction judgment form the human fills in, a five-question RST debrief scaffold, and a
  descriptive cross-run summary. None of them score quality — that stays the human's job.

## CLI

```bash
harcompanon preprocess <har> [-o out.json] [--security-report r.md]   # clean + scan a HAR
harcompanon redact <har> [-o out.har]                                 # mask detected secrets
harcompanon run <fixture> [-p anthropic ...] [--model M] [--modes ...] # a run (--dry-run/--live)
                          [--max-tokens N] [--out runs]
harcompanon check <run-dir>       # structural conformance checklist (post-processing)
harcompanon judge <run-dir>       # -> judgment.yml  (YOU fill it in — you are the judge)
harcompanon closeout <run-dir>    # -> closeout.md   (five debrief questions)
harcompanon summary <path>...     # descriptive cross-run indicators (not a verdict)
```

`run` is **live by default**; pass `--dry-run` to render the prompts and exercise the whole
pipeline without spending a token. Providers default to `anthropic`; repeat `-p` for more.

## Quickstart (dev)

```bash
pip install -e ".[dev]"
cp .env.example .env          # then add your provider keys (never committed)

harcompanon run fixtures/dash.har --dry-run          # no API call, no spend
harcompanon run fixtures/dash.har --live -p anthropic # one real run
harcompanon check runs/<run-id>
harcompanon judge runs/<run-id>                      # then fill in judgment.yml
harcompanon closeout runs/<run-id>
```

## Fixtures

Frozen HAR captures live in [`fixtures/`](fixtures). Only safe, public-demo captures are
committed (`dash.har`, `perf.har` — the OrangeHRM demo); real/personal captures are kept
local and git-ignored. If you add a capture from a real system, **`redact` it and review it**
before it goes anywhere public. See [fixtures/README.md](fixtures/README.md).

## Status

Pre-alpha. Work is tracked with [Beans](https://github.com/hmans/beans) in `.beans/`
(`beans roadmap`). The full pipeline is built; the remaining v1 step is a committed, documented
example run.

## Two senses of "testing" — keep them separate

Throughout this project, **"testing" means the RST sense** (the human, sapient activity the
tool studies). This repo *also* has ordinary **software tests** (`pytest`, under `tests/`),
which are *checks* on the code. The two are kept visibly distinct in code, docs, and commit
messages. See the [glossary](docs/rst-glossary.md).

## License

[MIT](LICENSE).
