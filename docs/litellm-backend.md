# The LiteLLM backend — an optional, exploratory alternative (and a small lesson)

> **This is a for-fun learning experiment, not a core feature.** harcompañon's real, supported path
> is the **native** per-vendor providers. This backend routes the same models through
> [LiteLLM](https://github.com/BerriAI/litellm) instead, so you can see the trade-offs first-hand.
> It's opt-in, isolated to one file, and off by default. Don't read the repo as "big" because of it —
> the tool underneath is deliberately small.

## TL;DR — how to try it
```bash
pip install -e ".[litellm]"          # the optional extra (not installed by default)
harcompanon run fixtures/<f>.har -p anthropic -p openai --modes structured --backend litellm --live
```
`--backend native` (the default) uses each vendor's SDK; `--backend litellm` uses LiteLLM. Everything
else — prompts, storage, `compare`, `check`, `retry` — is identical, because both go through the same
tiny `Provider` seam.

---

## 1. What LiteLLM actually is
LiteLLM is a **provider adapter** (a "universal power plug"), not a framework. Its core promise: call
**any** of 100+ models with **one** function, in the **OpenAI message format**, and get an
OpenAI-shaped response back. That's basically the whole surface:

```python
import litellm
resp = litellm.completion(
    model="anthropic/claude-opus-4-8",                 # "<provider>/<model>"
    messages=[{"role": "user", "content": "hi"}],
    max_tokens=1024,
)
resp.choices[0].message.content        # text
resp.choices[0].finish_reason          # 'stop' | 'length' | ...
resp.usage.prompt_tokens / completion_tokens
litellm.completion_cost(completion_response=resp)      # USD, from LiteLLM's pricing DB
```

It reads each provider's **standard key env var** (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, `MOONSHOT_API_KEY`) — exactly the ones already
in your `.env`. That's why this backend needed *zero* new key handling.

**One naming quirk worth knowing:** our provider `kimi` is LiteLLM's `moonshot` — so `kimi-k3`
routes as `moonshot/kimi-k3`. (Kimi is Moonshot AI's model; LiteLLM keys the route on the company.)

## 2. Two things both called "LiteLLM"
- **The SDK** (what this backend uses): a Python library, `import litellm`. A thin in-process
  translation layer. No server, no infra.
- **The Proxy**: a separate gateway *server* you run in front of your models — for team key
  management, budgets, rate-limit/load-balancing, logging, and a single OpenAI-compatible endpoint
  your apps point at. Great for a company; overkill for a single-user research tool. We use the SDK.

## 3. How it slots into harcompañon (why it was a one-file change)
Everything downstream depends only on the `Provider` protocol:
```python
class Provider(Protocol):
    name: str
    model: str
    def complete(self, prompt: str) -> RawResponse: ...
```
So the native path (four modules: `anthropic.py`, `openai.py`, `gemini.py`, `openai_compat.py`) and
the LiteLLM path (`litellm_provider.py`, one class) are interchangeable. `build_provider(..., backend=...)`
picks one. **This is the lesson about abstraction seams:** a good protocol boundary means you can swap
the entire vendor layer without touching the pipeline, the prompts, or the reports.

## 4. Native SDKs vs LiteLLM — the real trade-off
| | Native per-vendor SDKs (default) | LiteLLM backend (opt-in) |
|---|---|---|
| Lines of provider code | ~4 modules | 1 class |
| Add a model | new class + registry entry | a string |
| Cost accounting | our small hand-kept table (Anthropic only) | LiteLLM's pricing DB (**all** providers) |
| Per-vendor control | **explicit** (e.g. OpenAI via the *Responses* API; Anthropic *streaming*; no temperature for comparability) | abstracted (LiteLLM decides the endpoint/params) |
| New/flagship model IDs | you call them directly | may lag in LiteLLM's model map |
| Debugging a quirk | in the raw SDK | through LiteLLM's layer |

For a **comparison harness**, that "per-vendor control" row is the crux. The native code deliberately
sends **no temperature/top_p** (so differences reflect the models, not our knobs) and uses specific
endpoints per vendor. LiteLLM trades that explicitness for uniformity — which is exactly why it's a
great convenience tool but why, *here*, native remains the source of truth for the published results.

## 5. …and how it differs from a *framework* (e.g. LangChain)
Different category entirely:
- **LiteLLM = adapter.** Does one job (talk to models uniformly). Low commitment; easy to remove.
- **LangChain = orchestration framework.** Chains, agents, tools, memory, prompt templates, output
  parsers, retrievers, LCEL, hundreds of integrations. Calling providers is a small corner of it, and
  you structure your app around *its* abstractions.

harcompañon wants none of the framework parts — it's one-shot, no tools, no memory, no RAG — so
LiteLLM is both the *simpler* and the *correct-category* choice. LangChain would be a lot of concepts
to do a job the 6-line `Provider` protocol already does.

## 6. Security notes (deliberate)
- **Keys come from the environment only** (the git-ignored `.env`), never passed as arguments,
  never printed. LiteLLM reads them the same way the native SDKs do.
- **Telemetry is turned off** in code (`litellm.telemetry = False`) so a published repo doesn't phone
  home when someone tries this backend.
- **Nothing here logs** the prompt, the response, or any credential. (If you enable LiteLLM's own
  debug/verbose logging yourself, be aware it can print request payloads — don't do that with real
  keys in a shared terminal.)

## 7. The learning exercise: A/B the two backends
Because native stays the default, you can run the **same** fixture and model both ways and compare:
```bash
harcompanon run fixtures/lexus.pseudo.har -p anthropic --modes structured --live                    # native
harcompanon run fixtures/lexus.pseudo.har -p anthropic --modes structured --live --backend litellm  # litellm
harcompanon compare runs/<the-litellm-run>
```
Then ask: does the **output** differ? the **cost** figure? the **latency**? the **`stop_reason`**
handling on a truncated answer? Any difference is the abstraction layer making a decision the native
code made explicitly — which is the whole point of doing this by hand once.

## 8. Known gotchas to verify if you push on it
- **OpenAI surface:** native uses the *Responses* API; LiteLLM routes OpenAI through *chat/completions*.
  For gpt-5.x reasoning this can behave differently — check before trusting an A/B.
- **Very new model IDs** may need the explicit `provider/model` form, and `completion_cost()` can
  return `None`/0 for a model it hasn't priced yet (we fall back to our own table when it does).
- **Slow reasoners** (Kimi, DeepSeek): consider `stream=True` or a generous timeout so LiteLLM doesn't
  time the client out on a multi-minute response.
