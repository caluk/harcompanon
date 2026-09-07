# harcompañon

A small, reproducible tool that compares how different LLMs behave as **testing companions**
when handed the *same* real evidence and the *same* prompt.

It is **not** a coding benchmark, **not** a capability leaderboard, and **not** about generating
automated checks. It measures **judgment quality** in the vocabulary of Rapid Software Testing
(RST) — see [RST vocabulary](#rst-vocabulary) below. The human is always the sole judge.

## The question it answers

When a human is testing something and is *equipped with* an LLM, does that human + AI combination
reach higher, better-grounded confidence? A **good** companion surfaces risk and invites continued
scrutiny. A **bad** one produces plausible-sounding text that invites the human to stop looking.
That difference is the thing being measured.

The word *companion* is deliberate. The model is an **instrument inside a human's sapient
process**, never a "tester." Testing requires sapience and accountability an AI cannot hold — so
**the human is always the sole judge** of response quality. The tool only prepares the evidence
and lays the responses side by side; it never scores or judges.

## How it works

```
HAR fixture ─▶ preprocess ──▶ run (providers × prompts) ──▶ per-response JSON + compare.html
   │            (strip noise,        stateless API calls          (side-by-side matrix,
   │             keep envelope)                                    auto-built on a clean run)
   ├─ redact ─▶ (mask secrets)
   └─ security scan (safety)
```

- **Preprocess** — mechanical noise removal only: keep every call's *envelope* (method, URL,
  status, timing, curated headers) and its JSON bodies; strip heavy/binary/oversized bodies to a
  `<stripped: …>` marker. A built-in **secrets/PII scan** warns about anything sensitive in the raw
  HAR.
- **Redact** — mask every scanner-detected secret value with `<REDACTED>`, producing a copy safe to
  commit *and* to send to models. (Heuristic — eyeball before publishing.)
- **Pseudonymize** — replace domain PII (VINs, plates, addresses, device IDs, UUIDs) with realistic
  synthetic values, for a capture you want to share without leaking real data.
- **Prompts** — versioned, so the *effect of an intervention* is measurable, not a single number:
  - `minimal` — bare ("what do you notice?"); no role, no structure.
  - `structured` — a required output shape: an **Overall picture** (a product model), findings each
    with an oracle and possible impact, systemic observations, the questions only a human can
    answer, coverage depth, and a self-critique.
  The `minimal→structured` gap isolates what the structure adds.
- **Providers** — Claude, OpenAI, Gemini, DeepSeek, Mistral, Kimi behind one small abstraction;
  adding a model is one class + one registry entry. Calls are stateless (comparable months apart),
  models are pinned to fixed versions, and reasoning is configured equally where each SDK allows.
  Keys load from a git-ignored `.env` (see `.env.example`).
- **A run** = one frozen fixture × the chosen providers × the chosen prompt modes. Everything is
  flat files — no database.
- **Compare** — renders a run as a self-contained `compare.html` matrix (models × prompt modes) with
  each response's latency, tokens, and reasoning tokens alongside, for side-by-side reading. A
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

You supply your own HAR — capture one from a site you're testing (DevTools → Network → "Save all as
HAR"), then `redact` (and `pseudonymize` if it holds domain PII) before use.

## Fixtures

Frozen HAR captures live in [`fixtures/`](fixtures) and are **git-ignored by default** — no captures
are committed, since real ones carry personal data. Bring your own: if it comes from a real system,
**`redact` it and review it** before it goes anywhere public. See [fixtures/README.md](fixtures/README.md).

## RST vocabulary

The vocabulary this project holds itself to — strict enough that careful RST practitioners (in the
tradition of James Bach and Michael Bolton) wouldn't find it conflated or watered down. When code,
comments, prompts, or commits use these terms, they mean *exactly* this.

- **Testing** — evaluating a product by learning about it through exploration and experimentation
  (questioning, study, modeling, observation, inference). It is open-ended, investigative, *sapient*,
  and **cannot be automated** — only *supported* by tools and checks.
- **Checking** — applying algorithmic decision rules to specific observations of a product: an
  observation, a decision rule, and the property that it runs **algorithmically**. Checks are
  valuable and embedded *within* testing. This tool does not measure whether a model can write
  checks; it measures how good the model is as a companion to a *human who is testing*. (The `pytest`
  suite under `tests/` is *checking* our own code — a separate sense from the subject matter; keep
  the two visibly distinct.)
- **Oracle** — a means by which we recognize a problem when we meet one: a heuristic with a reason
  behind it, not guaranteed truth. Oracles are plural and fallible (cf. the RST heuristic **FEW
  HICCUPPS** — Familiarity, Explainability, World, History, Image, Comparable products, Claims, User
  expectations, Product consistency, Purpose, Statutes). A finding that can't **name its oracle**
  isn't yet defensible — which is why the structured prompt asks for an oracle per finding.
- **Sapience & accountability** — the load-bearing constraint: a model is never scored *as a tester*
  (that needs sapience *and* accountability, which an AI can hold neither of), only as an instrument
  inside a human's sapient process; and **the human is the sole judge** of quality.
- **Companion** — the role being evaluated: an LLM used *alongside* a human during a focused session.
  A good companion **surfaces risk and invites continued scrutiny**, raising grounded confidence; a
  poor one produces **plausible-sounding text that invites the human to stop looking**. That contrast
  is the axis of the whole comparison.

**The evaluation ladder** (this project's own construct, *not* RST canon) — a way for the human to
place each finding, **only after checking it against the raw evidence**:

| Level | Meaning |
| --- | --- |
| **slop** | Ungrounded, fabricated, or contradicted by the evidence. Would mislead a tester. |
| **plausible** | Reads as reasonable but has **not** been checked — the danger zone that invites you to stop looking. |
| **provisional** | Checked against the evidence and currently supported, held tentatively. |
| **validated** | Checked and **defensible**: the human can own it as their own conclusion, with a **named oracle**. |

RST definitions above follow Bach & Bolton, in particular
["Testing and Checking Refined"](https://www.satisfice.com/blog/archives/856) (2013); paraphrased
here — consult the originals for authoritative wording. The **ladder** and the **companion** framing
are this project's own.

## Methodology & caveats

**The construct.** How good is an LLM as a testing companion to a human running a session-based
test — an instrument that raises the human's grounded confidence and the quality of their findings.
A good companion surfaces risk and invites scrutiny; a poor one invites the human to stop looking.
The model is never scored *as a tester*; the human is the sole judge.

**The procedure.**
- **One frozen fixture** — a real HAR, preprocessed the same way every run (mechanical noise removal
  only).
- **Stateless, direct API calls** — no chat apps, memory, or personalization, so reruns are
  comparable months apart.
- **A prompt gradient, not one prompt** — `minimal` (bare) → `structured` (a required output shape).
  **The gap is the finding, not noise to average away.**
- **Reasoning configured equally** across providers where the SDK allows (adaptive / effort / dynamic
  thinking). Mistral Large, which has no reasoning mode, is the one documented exception.
- **The human judges** — in their own notes, against the raw evidence. Nothing in the tool scores
  quality.

**Deliberate choices.**
- Sampling left at each provider's default (no temperature — current Claude models reject it, and
  forcing it on others would create an asymmetry; default sampling also serves reproducibility).
- Only JSON bodies are kept; other bodies are shown as an explicit `<stripped: …>` marker.
- Structured output stays human-readable markdown, not forced JSON.
- Models pinned to fixed, concrete versions (no floating `-latest`), for reproducibility.

**Caveat for longitudinal use.** Rerunning the same frozen fixture against new model releases gives a
longitudinal read — but **the construct itself drifts**: what counts as "good judgment," and what a
strong model finds trivial versus hard, changes as models improve. A result is only meaningful
relative to the fixture, the prompt versions, and the era it was produced in. Any published
comparison must name all three and carry this caveat.

## Status

Pre-alpha, exploratory. The pipeline is intentionally small: prepare the evidence, run the same
prompt across models, and lay the responses side by side for a human to judge.

## License

[MIT](LICENSE).
