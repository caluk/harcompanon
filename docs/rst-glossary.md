# RST glossary — the vocabulary this project holds itself to

This file is the **single source of truth** for the Rapid Software Testing (RST) terms used
everywhere in harcompañon: code, comments, prompts, docs, commit messages, and the
human-judgment workflow. When any of those use a term below, they mean *exactly* this, and
should link back here.

The discipline is deliberate. The whole point of the tool is to be strict about this
vocabulary — strict enough that careful RST practitioners (in the tradition of James Bach
and Michael Bolton) would not find it conflated or watered down. If you are tempted to
stretch a definition to make a feature easier, stop: the stretch is the bug.

> **Two senses of "testing."** In this project, **"testing" always means the RST sense
> below** — the human, sapient activity the tool studies. This repo *also* contains
> ordinary **software tests** (`pytest`, under `tests/`). Those are **checks** on our own
> code (see *Checking*), and have nothing to do with the subject matter. Keep the two uses
> visibly separate.

---

## Testing

**Testing is the process of evaluating a product by learning about it through exploration
and experimentation** — which includes, to some degree: questioning, study, modeling,
observation, inference, and more.

Testing is an open-ended, investigative, *sapient* performance (see *Sapience*). It cannot
be reduced to a fixed procedure, and it **cannot be automated** — though it can be, and
usually is, *supported* by tools and by checks.

## Checking

**Checking is the process of making evaluations by applying algorithmic decision rules to
specific observations of a product.**

A **check** has three elements:

1. an **observation** it makes of the product,
2. a **decision rule** applied to that observation, and
3. the property that it can be performed **algorithmically** — by a machine, or by a human
   following instructions without engaging judgment.

Checks are valuable. They are also *embedded within* testing: a tester decides which checks
are worth having, builds or commissions them, and — crucially — interprets what their
results mean. **You can automate a check. You cannot automate the testing around it.**

Why it matters here: producing or running checks is not what this tool measures. We are not
asking "can the model write good automated checks?" We are asking how good the model is as a
companion to a *human who is testing*.

## Oracle

**An oracle is a means by which we recognize a problem when we encounter one during
testing.** It is not a source of guaranteed truth; it is a heuristic — a principle or
mechanism that lets you say "that's a problem" with a reason behind it.

Oracles are plural and fallible. A useful reminder of where they come from is the RST
heuristic **FEW HICCUPPS** (Familiarity, Explainability, World, History, Image, Comparable
products, Claims, User expectations, Product consistency, Purpose, Statutes). A finding that
cannot **name the oracle** it rests on is not yet defensible — which is exactly why the
structured prompt requires a **labelled oracle per finding**, and why the human-judgment
step records *oracle named? (yes/no)* for every finding.

## Sapience (and accountability)

A **sapient** activity is one that requires a thinking human. Testing is sapient: it depends
on human judgment, learning, and the ability to be **accountable** for the evaluation.

This is the load-bearing constraint of the whole project:

- **A model is never scored as a "tester."** Testing requires sapience *and* accountability,
  and an AI can hold neither. A model is scored only as an **instrument inside a human's
  sapient process**.
- **The human is the sole judge** of response quality. The tool may perform mechanical
  **post-processing** (for example, checking that a structured response contains the
  required sections). Post-processing is *checking*, never *judging* — and the naming in the
  code says so on purpose.

## Companion

A **testing companion** is the role we are evaluating: an LLM used *alongside* a human
during a focused test session (RST session-based testing). A good companion **surfaces risk
and invites continued scrutiny**, raising the human's grounded confidence and the quality of
their findings. A poor companion produces **plausible-sounding text that invites the human
to stop looking**. That contrast is the axis of the whole benchmark.

---

## The evaluation ladder (this project's construct — *not* RST canon)

To keep the vocabulary honest: the four-level ladder below is **harcompañon's own
evaluation construct**, not a term from the RST body of knowledge. It exists so the human
can place each finding consistently. A model's output climbs the ladder **only after the
human checks it against the raw evidence** — never before.

| Level           | Meaning |
| --------------- | ------- |
| **slop**        | Ungrounded, fabricated, or contradicted by the evidence. Would mislead a tester. |
| **plausible**   | Reads as reasonable but has **not** been checked against the raw evidence. The danger zone — this is the text that invites you to stop looking. |
| **provisional** | Checked against the evidence and currently supported, held tentatively — a hypothesis the human is willing to defend *for now*, pending more scrutiny. |
| **validated**   | Checked against the raw evidence and **defensible**: the human can own it as their own conclusion, with a **named oracle**. |

Each finding the human evaluates gets three marks, together with a ladder position:

1. **Oracle named?** — does the finding rest on a nameable oracle?
2. **Defensible as your own?** — could the human stand behind it as their own conclusion?
3. **Ladder position** — where does it land, *once checked against the raw evidence*?

---

## Sources

The RST definitions above follow James Bach and Michael Bolton's work, in particular
["Testing and Checking Refined"](https://www.satisfice.com/blog/archives/856) (2013) and the
Rapid Software Testing namespace. Definitions are paraphrased for this glossary; consult the
originals for the authoritative wording. The **evaluation ladder** and the **companion**
framing are this project's own, and are labelled as such above.
