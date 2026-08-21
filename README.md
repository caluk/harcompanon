# harcompañon

A small, reproducible tool that compares how different LLMs behave as **testing
companions** when handed the *same* real evidence and the *same* prompt.

It is **not** a coding benchmark, **not** a capability leaderboard, and **not** about
generating automated checks. It measures **judgment quality** in the vocabulary of
[Rapid Software Testing (RST)](docs/rst-glossary.md): testing vs. checking, oracles,
sapience.

## The question it answers

When a human is testing something and is *equipped with* an LLM, does that human + AI
combination reach higher, better-grounded confidence? A **good** companion surfaces risk
and invites continued scrutiny. A **bad** one produces plausible-sounding text that
invites the human to stop looking. That difference is the thing being measured.

The word *companion* is deliberate. The model is an **instrument inside a human's sapient
process**, never a "tester." Testing requires sapience and accountability that an AI
cannot hold — so **the human is always the sole judge** of response quality. The tool may
perform mechanical **post-processing** (e.g. structural conformance checks); it never
judges.

## How it works

```
HAR fixture ─▶ preprocess ─▶ run (providers × prompts) ─▶ per-response JSON + comparison index
                (strip to           stateless API calls                     │
                 JSON API calls)                                            ▼
                                          post-processing check ──▶ human judgment ──▶ close-out
                                          (structural, mechanical)  (YOU are the judge)
```

- **Prompts** come in two versioned modes — **minimal** (sparse: "what looks strange
  here?") and **structured** (a required output shape: a labelled oracle per finding, a
  self-critique, explicit human-only questions, and a "hypotheses, not findings"
  disclaimer). The gap between the two is itself a finding.
- **Providers** (Claude, OpenAI, Gemini) sit behind one small abstraction; adding a model
  is one file plus one config entry.
- **A run** = one frozen fixture × all configured providers × both prompts. Everything is
  flat files — no database.

## Status

Pre-alpha. Work is tracked with [Beans](https://github.com/hmans/beans) in `.beans/`
(`beans roadmap`). The CLI verbs are scaffolded; pipeline stages are landing incrementally.

## Quickstart (dev)

```bash
pip install -e ".[dev]"
harcompanon --help
cp .env.example .env   # then add your provider keys (never committed)
```

## Two senses of "testing" — keep them separate

Throughout this project, **"testing" means the RST sense** (the human, sapient activity the
tool studies). This repo *also* has ordinary **software tests** (`pytest`, under `tests/`),
which are *checks* on the code. The two are kept visibly distinct in code, docs, and commit
messages. See the [glossary](docs/rst-glossary.md).

## License

[MIT](LICENSE).
