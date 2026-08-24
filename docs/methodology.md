# Methodology

What this benchmark measures, how, and the caveats any write-up must carry. It complements
the [RST glossary](rst-glossary.md), which defines the vocabulary; this file describes the
*construct* and the *procedure*.

## The construct

We measure **how good an LLM is as a testing companion** to a human running a session-based
test — an instrument that raises the human's grounded confidence and the quality of their
findings. Concretely, a good companion **surfaces risk and invites continued scrutiny**; a
poor one produces plausible-sounding text that invites the human to **stop looking**. The
model is never scored *as a tester* (testing requires sapience and accountability it cannot
hold) — only as an instrument inside a human's sapient process. The human is the sole judge.

Each finding a model produces is evaluated by the human against three things (see the
judgment file the tool generates):

1. **Oracle named?** — does it rest on a nameable oracle?
2. **Defensible as your own?** — could the human stand behind it as their own conclusion?
3. **Ladder position** — slop / plausible / provisional / validated, *after* checking it
   against the raw evidence. (The ladder is this project's construct, not RST canon.)

## The procedure

- **One frozen fixture.** A real HAR, checked in byte-identical, preprocessed the same way
  every run (mechanical noise removal only — see the preprocessing module).
- **Stateless, direct API calls.** No chat apps, memory, or personalization, so reruns are
  comparable months apart. Sampling is left at each provider's default (see *Choices* below).
- **A prompt gradient, not one prompt.** `minimal` (bare) → `briefed` (instrument role +
  session/pre-go-live situation, no structure) → `structured` (a required output shape with a
  labelled oracle per finding, hypotheses-not-findings, human-only questions, self-critique).
  The gradient decomposes the effect: `minimal→briefed` isolates role + situation;
  `briefed→structured` isolates imposed structure. **The gap is the finding, not noise to
  average away.**
- **Human judgment + close-out.** The tool pre-populates a judgment form and a five-question
  debrief; the human fills them in. Nothing in the tool scores quality.

## Deliberate choices (state these in any write-up)

- **Sampling left at default (no temperature).** Current Claude models reject `temperature`
  outright, and forcing it on other providers would create an asymmetry. Default sampling also
  serves reproducibility. A temperature sweep is a possible *future* axis, not part of v1.
- **JSON-only bodies.** Preprocessing keeps every call's envelope + headers but only JSON
  request/response bodies; other bodies are shown as an explicit `<stripped: …>` marker.
- **Structured output stays human-readable markdown**, not forced JSON — so the structural
  check measures *whether the model complied*, rather than the format being guaranteed.

## Caveats for longitudinal use

Rerunning the same frozen fixture against new model releases gives a longitudinal read — but
**the construct itself may drift**: what counts as "good judgment," and what a strong model
finds trivial versus hard, changes as models improve. A score is only meaningful relative to
the fixture, the prompt versions, and the era it was produced in. Any published comparison
must name all three and carry this caveat — do not present a cross-era number as if the
measuring stick held still.
