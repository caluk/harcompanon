# harcompañon

Compare how LLMs behave as **testing companions** when given the same frozen evidence
and prompt. harcompañon prepares a HAR capture, calls providers, and lays their responses
out in a self-contained `compare.html` matrix for a human to read.

This is not a coding benchmark, capability leaderboard, automated evaluation, or LLM-as-judge.
The tool never scores quality. The question for the human is whether a companion surfaces
useful risks and invites further investigation, or produces plausible text that encourages
them to stop looking.

## Quickstart

Requires Python 3.11 or newer. From a checkout:

```bash
pip install -e ".[dev]"
cp .env.example .env  # add keys for the providers you use

# Supply your own capture; review the redacted copy before sending it anywhere.
harcompanon redact fixtures/session.har
harcompanon preprocess fixtures/session.redacted.har -o /dev/null --security-report /tmp/harcompanon-security.md
harcompanon run fixtures/session.redacted.har --dry-run
harcompanon run fixtures/session.redacted.har -p anthropic -p openai
```

`run` is **live by default**. `--dry-run` renders prompts and writes placeholder responses
without API calls or credentials; it does not save the rendered prompts. The default provider
is `anthropic`, the prompt modes are `minimal,structured`, and the prompt version is `v5`.
Keys load from the environment or a local `.env` (see [.env.example](.env.example)).

Real captures and run outputs stay local. `redact` and `pseudonymize` are heuristics, not
anonymity guarantees. Review the resulting HAR before sending it to a provider or publishing
it. See [fixtures/README.md](fixtures/README.md) for preparation and limitations.

## Pipeline

```text
HAR → redact / pseudonymize → review → preprocess → providers × prompt modes
                                                  → run.json + response JSON + compare.html
```

- **Preprocess** keeps every valid call's method, URL, status, timing, content types,
  and selected headers. Recognized sensitive header values are masked. JSON bodies are kept;
  other present bodies, base64 bodies, and bodies over 20,000 characters become
  `<stripped: …>` markers. Responses to HEAD and statuses 1xx, 204, and 304 have no body.
  The `preprocess` command also scans the raw HAR and reports separately; `run` preprocesses
  internally but does **not** run that scan or redact body/query secrets.
- **Prompts** are [versioned Markdown files](src/harcompanon/prompts): `minimal` is a bare
  probe; `structured` adds RST framing, a product overview, findings, systemic observations,
  questions for a human, coverage depth, and a self-critique. In v5, findings distinguish
  observation, interpretation, and next investigation, with oracles and impact when useful.
- **Providers** are Anthropic, OpenAI, Gemini, DeepSeek, Mistral, and Kimi. Each receives a
  stateless request with the same rendered prompt for a given mode.
- **Storage** is flat files: `run.json` and `responses/<provider>__<mode>.json`. An error-free
  live run also creates `compare.html`, with models as columns and prompt modes as rows.
  It includes latency, token counts, and reasoning tokens where reported. No database or server.

```bash
harcompanon preprocess <har> [-o cleaned.json] [--security-report report.md]
harcompanon redact <har> [-o redacted.har]
harcompanon pseudonymize <har> [-o synthetic.har] [--exclude KEY]
harcompanon run <har> [-p PROVIDER] [--modes minimal,structured] [--prompt-version v5]
harcompanon compare <run-dir>                 # build or rebuild compare.html
harcompanon retry <run-dir> [--fixture <har>] # retry errored responses in place
```

Run options include `--model`, `--max-tokens` (default 32,000), and `--out` (default `runs`).
Repeat `-p` for more providers. A model override applies to every selected provider; use it
with a single provider unless the ID is valid for all of them. After `retry`, rebuild the
matrix with `compare`. Retry needs the original, unchanged fixture; its default lookup is
`fixtures/<original-filename>`.

## Method and limits

Freeze the reviewed fixture and retain the code revision, prompt version, model IDs, run date,
and invocation when comparing results. The manifest records model IDs and prompt versions,
but does not archive the fixture, rendered prompts, or all request settings. Retry re-reads
the fixture without checking that it is unchanged.

Default model IDs are centralized in [config.py](src/harcompanon/config.py). Explicit IDs
and versioned prompts help trace a run, but do not guarantee immutable provider deployments
or identical responses. Sampling uses provider defaults. Anthropic requests adaptive thinking,
OpenAI high reasoning effort, and Gemini a dynamic thinking budget; compatible APIs receive
no explicit reasoning setting. These are different controls, not equal reasoning budgets.
Token accounting also differs by provider.

The minimal/structured comparison explores the effect of the **whole prompt intervention**,
including framing and instructions, not structure alone. A single run cannot separate that
effect from response variability. Redaction and pseudonymization can alter relationships in
the evidence; missing bodies and selected headers also limit what can be inferred.

Judge responses against the original evidence and product context in your own notes.
Longitudinal comparisons should name the fixture, prompt/model versions, and date: both the
models and what humans consider useful judgment can change.

## RST vocabulary

This project follows James Bach and Michael Bolton's distinction in
[“Testing and Checking Refined”](https://www.satisfice.com/blog/archives/856), paraphrased here:

- **Testing** evaluates a product through human learning, exploration, and experimentation.
  Tools support that work; they do not take responsibility for the judgment.
- **Checking** applies algorithmic rules to observations. The pytest suite checks this
  repository's code; it does not evaluate model response quality.
- **Oracle** is a fallible means of recognizing a possible problem: an expectation and a
  reason for it. It is a basis for investigation, not guaranteed truth.
- **Companion** is this project's framing for an LLM used within a human's testing process.
  The human retains judgment and accountability.

The following **evaluation ladder is this project's own construct**, not RST terminology
or an automated scoring system. It is for a human's notes:

| Level | Meaning |
| --- | --- |
| **slop** | Ungrounded, fabricated, or contradicted by the evidence. |
| **plausible** | Reads reasonably but has not been checked against the evidence. |
| **provisional** | Checked against the evidence and tentatively supported. |
| **validated** | Checked and defensible, with a named oracle; the human owns the conclusion. |

## Development

```bash
ruff check .
ruff format --check .
mypy
pytest
```

The suite uses synthetic HARs and fake providers, without live API calls.
Pre-alpha and exploratory. Licensed under [MIT](LICENSE).
