# explaind

`explaind` is a local-first cognitive steering layer for Gemma 4 and a submission for the **Gemma 4 DEV Challenge**.

It is not an agent, not a chatbot wrapper, and not a RAG system. It is a deterministic prompt harness that biases Gemma 4's reasoning trajectory by assembling a fixed stack of instruction layers, invariants, context scaffolding, and an ability-specific bias field before a single model call.

The core claim of the project is simple: for **Gemma 4**, prompt structure is not presentation polish. It is control surface. If the model is sensitive to framing, ordering, recency, and harness design, then those properties should be treated as first-class software, not ad hoc prompt text.

---

## What explaind is

`explaind` treats **Gemma 4** as a stochastic reasoning engine whose behavior can be steered without fine-tuning. The software does not patch model weights, maintain memory, run tool loops, or build an autonomous workflow around the model. It performs one deterministic prompt assembly, sends that prompt to a local backend, and returns the model output.

In the current codebase, that means:

- input from stdin or a positional file path
- whitelist-based loading of one of five ability files
- deterministic prompt construction with fixed layer ordering
- a runtime `BIAS FIELD` injected immediately before user input
- an always-present `CONTEXT WINDOW LAYERS` block
- optional `--dry-run`, `--trace`, `--compare`, and `--think` execution modes
- local model invocation through Ollama

This is prompt physics, not agent orchestration.

---

## Why It Exists

Gemma 4 is unusually explicit about prompt structure and model-specific controls. The official model card documents native `system` support, configurable thinking mode via the `<|think|>` token, and long-context operation up to 128K or 256K tokens depending on model size. Independent evaluation also shows that prompting protocol materially changes outcome quality: a recent benchmark measured Gemma 4 under zero-shot, chain-of-thought, and few-shot chain-of-thought settings and found meaningful prompt sensitivity across tasks. Separately, Georgi Gerganov's March 30, 2026 observation on local-model quality captured the operational reality: the harness, chat template, and prompt-construction chain are often the fragile part.

That is the design premise behind `explaind`. Behavior improves significantly with inference tweaks and custom harnesses; raw chat use exposes more flaws. So instead of pretending the harness is incidental, `explaind` makes the harness the product.

The table below maps observed or commonly reported Gemma 4 failure patterns to the current design response in this repository:

| Gemma 4 Failure Mode | explaind Response |
|---|---|
| Weak system prompt adherence | `BIAS FIELD` redundant signal injection immediately before user input |
| Overconfidence / shallow elaboration | `skeptical` ability adds epistemic friction and pressures unsupported claims |
| Reasoning collapse without harness | Strict layer ordering plus invariant constraints from `GEMMA.md` |
| Prefers parametric knowledge over prompt | Structured context injection through file input and the always-present `CONTEXT WINDOW LAYERS` block |
| "Sounds smarter than it is" | `compressive` ability forces density over elaboration |

Two implementation notes matter here:

- Scratchpad-style context injection is now available via `--scratchpad` and `--context` flags, which fill the `[SCRATCHPAD]` and `[REFERENCE CONTEXT]` fields in the context window block.
- `--file PATH` is now implemented as an alternative to the positional file argument. Both are accepted; `--file` takes precedence when both are provided.

---

## How It Works

Conceptually, `explaind` is built around a five-layer steering stack:

`SYSTEM PROMPT -> GEMMA.md -> ABILITY -> BIAS FIELD -> USER INPUT`

In the current codebase, that five-layer design is rendered as six concrete blocks because a deterministic context scaffold is always inserted between the ability and the bias field:

`SYSTEM PROMPT -> GEMMA.md -> ABILITY -> CONTEXT WINDOW LAYERS -> BIAS FIELD -> USER INPUT`

That concrete ordering is enforced in `explaind/prompts/__init__.py`, exercised by `explaind/main.py`, and locked down by prompt-order and golden-file tests.

### 1. SYSTEM PROMPT

The system layer defines the base role: a reasoning assistant that responds clearly, directly, and accurately, adapts reasoning style to the task, and does not assume a default task type. This is the broadest behavioral substrate. It sets the base operating conditions before any invariant or bias-specific steering is applied.

### 2. GEMMA.md

`GEMMA.md` is the invariant reasoning layer. It tells the model what it must not do: hallucinate facts, collapse uncertainty, conflate observation with inference, or silently invent missing context. This layer is static. It is not memory, not fine-tuning, and not session state. It is the stable constraint surface inside the prompt stack.

### 3. ABILITY

An ability is a reasoning bias vector loaded from `abilities/<name>.md`. It does not replace the invariants. It changes what the model pays attention to, what it suppresses, and what inferential direction it prefers. In code, abilities are whitelist-only and restricted to `balanced`, `skeptical`, `causal`, `compressive`, and `exploratory`.

### 4. CONTEXT WINDOW LAYERS

This block is a concrete implementation detail of the current repository, not just a future idea. It always appears in the assembled prompt and contains:

- `[SCRATCHPAD]`
- `[REASONING TRACE]`
- `[COMPETING INTERPRETATIONS]`
- `[CONTEXT INSTRUCTION]`

Right now the CLI does not fill those fields dynamically, so they default to `none` unless the builder is called directly with values. Even so, the block matters. It reserves stable address space in the prompt for working-memory style context and tells the model to treat it as persistent within the current inference.

### 5. BIAS FIELD

The `BIAS FIELD` is the runtime reinforcement block injected immediately before the user input. It is derived from the active ability name alone and currently carries:

- active bias label
- reasoning trajectory
- epistemic stance
- invariant status

This is the most important control detail in the system. The same signal appears redundantly in both the ability file and the late prompt tail because recency matters. If Gemma 4 underweights earlier instructions or flattens behavior over long prompts, the late bias field reasserts the intended trajectory right before generation pressure hits the user task.

### 6. USER INPUT

The final layer is the raw user content wrapped in XML-style tags:

```xml
<user_input>
...
</user_input>
```

Placing the user input last ensures every prior layer is in scope when the model reaches the task itself.

### Why The Ordering Matters

The order is not cosmetic.

- `SYSTEM PROMPT` comes first because it defines the base operating frame.
- `GEMMA.md` comes next so invariants are upstream of all bias-specific steering.
- `ABILITY` follows because reasoning direction should be applied inside invariant bounds.
- `CONTEXT WINDOW LAYERS` sit after ability so working-memory hints inherit the active steering regime.
- `BIAS FIELD` appears late because redundant signal injection near the tail is a deliberate defense against instruction dilution.
- `USER INPUT` comes last because it is the object the entire stack is meant to shape.

---

## Presets

Presets are named reasoning personalities that map to a curated ability and bias configuration. They are a higher-level interface on top of abilities — use them when the task calls for a recognisable reasoning posture rather than a raw ability name.

| Preset | Maps to | Description |
|---|---|---|
| `philosopher` | `exploratory` | Examines foundational assumptions, resists closure, pursues depth over resolution |
| `engineer` | `causal` | Traces mechanisms and root causes; treats every problem as a system |
| `critic` | `skeptical` | Applies maximum epistemic pressure; default posture is interrogation |
| `synthesiser` | `balanced` | Holds competing frameworks simultaneously, seeks integration |
| `analyst` | `compressive` | Strips elaboration, targets signal; output is dense by design |
| `strategist` | `causal` | Maps causal terrain for leverage points and second-order effects |

### Usage

```bash
echo "Is consciousness an illusion?" | explaind --preset philosopher
echo "Why did this service fail?" | explaind --preset engineer --dry-run
echo "What are the assumptions here?" | explaind --preset critic
explaind --preset analyst --scratchpad notes.md "Summarise the key finding"
```

### Listing presets

```bash
explaind --list-presets
```

Output:

```
philosopher  →  exploratory   Examines foundations, resists closure
engineer     →  causal        Traces mechanisms and root causes
critic       →  skeptical     Applies maximum epistemic pressure
synthesiser  →  balanced      Integrates competing frameworks
analyst      →  compressive   Strips elaboration, targets signal
strategist   →  causal        Maps leverage points and trajectories
```

`--preset` is mutually exclusive with `--ability` and `--compare`. All other flags (`--think`, `--scratchpad`, `--context`, `--dry-run`, `--trace`) work with `--preset`.

---

## The Five Abilities

### `balanced`

`balanced` is the neutral prior. It applies no directional pressure and attempts to weight available evidence evenly. Use it when the task does not clearly call for skepticism, causal tracing, compression, or exploratory synthesis, or when you want the cleanest baseline before comparing other trajectories.

### `skeptical`

`skeptical` replaces default explanation with examination. It interrogates the framing of the question itself, pressures unsupported claims, and treats consensus as something to justify rather than inherit. Use it when the biggest risk is overconfident reasoning, causal handwaving, or quietly accepting the user's premises without inspecting them first.

### `causal`

`causal` biases the model toward mechanism tracing. It follows temporal order, state transitions, and the difference between triggering conditions and root conditions. Use it when you want the model to explain how one condition produced another rather than merely listing symptoms, correlations, or adjacent factors.

### `compressive`

`compressive` is not a brevity mode. It is a high-selectivity reasoning filter that forces the model to identify the highest-information signals and stop spending tokens on low-yield elaboration. Use it when the model is likely to sound persuasive by being expansive, when you want the shortest path to grounded inference, or when the task benefits from signal density over discursiveness.

### `exploratory`

`exploratory` is the opposite of closure. It pushes the model toward heterodox framings, underexplored questions, and reframings that the original prompt may exclude. Use it when the task is synthesis, hypothesis generation, or conceptual expansion rather than convergence on a final answer.

---

## CLI Surface

The parser in `explaind/cli.py` exposes the following interface today.

### Implemented inputs and flags

| Interface | What it does | Example |
|---|---|---|
| `file` (positional) | Reads input from a file path. If omitted, `explaind` reads stdin. File input takes precedence over stdin when both are present. | `explaind logs/error.txt` |
| `--ability NAME` | Loads one ability file and runs a single steered inference or dry-run. | `echo "What is this failure?" \| explaind --ability skeptical` |
| `--compare NAME...` | Runs the same input through two or more abilities in sequence. Mutually exclusive with `--ability`. | `echo "What causes inflation?" \| explaind --compare skeptical causal compressive` |
| `--think` | Injects Gemma 4's thinking token into the system layer before prompt assembly. | `echo "Trace the argument" \| explaind --think` |
| `--dry-run` | Prints the fully assembled prompt to stdout and skips model invocation. | `echo "Explain this output" \| explaind --dry-run` |
| `--trace` | Prints a prompt-construction trace to stderr, including model settings and prompt size. | `echo "Explain this output" \| explaind --trace --dry-run` |
| `--file PATH` | Reads input from a file path. Equivalent to the positional argument — use whichever form is more ergonomic. `--file` takes precedence when both are supplied. | `explaind --file logs/error.txt --ability causal` |
| `--scratchpad FILE` | Injects a markdown file as active working memory into the `[SCRATCHPAD]` field of the context window. Use for hypotheses, partial reasoning, or working notes. Forces Gemma 4 to reason from this content rather than defaulting to parametric knowledge. | `explaind --ability causal --scratchpad hypothesis.md "What should we conclude?"` |
| `--context FILE` | Injects a markdown file as reference material into the context window. Use for prior outputs, background documents, or domain-specific material. Instructs the model to prefer this content over general knowledge where they conflict. | `explaind --scratchpad hypothesis.md --context prior_analysis.md "What should we conclude?"` |
| `--preset NAME` | Loads a named reasoning preset, selecting the mapped ability and injecting a `[PRESET: NAME]` marker into the bias field. Mutually exclusive with `--ability` and `--compare`. | `echo "Why did this fail?" \| explaind --preset engineer` |
| `--list-presets` | Prints all available presets with their mapped ability and one-line description, then exits. | `explaind --list-presets` |
| `--export [FILE]` | Saves reasoning output to a Markdown file after the run. If a filename is given, writes to that path. If omitted, generates a timestamped filename (`explaind_YYYYMMDD_HHMMSS.md`). Works with `--ability`, `--compare`, `--preset`, and `--think`. The exported file includes a blank **Summary Notes** section for user annotation. | `echo "What causes inflation?" \| explaind --compare skeptical causal --export chain.md` |
| `--honest` | Two-pass honest mode: runs balanced first, then applies skeptical critique to the initial response. Surfaces where Gemma 4's confidence outruns its evidence. Mutually exclusive with `--compare` and `--preset`. Works with `--think`, `--scratchpad`, `--context`, `--export`, `--dry-run`, and `--trace`. | `echo "What causes inflation?" \| explaind --honest` |
| `--chain NAME [NAME ...]` | Sequential ability pipeline: each ability runs in order, and each pass feeds its output as scratchpad input to the next. Each pass transforms the previous output rather than answering the original question fresh. Mutually exclusive with `--ability`, `--compare`, `--preset`, and `--honest`. Requires at least 2 ability names. | `echo "What caused the 2008 financial crisis?" \| explaind --chain causal compressive skeptical` |

### `--chain` usage

Each pass receives the previous pass's output as scratchpad input. The first pass sees the original user input (and any user-supplied `--scratchpad`). Pass 2 onwards receive a structured `[REASONING HANDOFF]` block that names the incoming and outgoing ability, the previous output, and an instruction to transform rather than summarise. Scratchpad content is truncated to 8000 characters per pass to prevent context window overflow on long chains.

```bash
echo "What caused the 2008 financial crisis?" | explaind --chain causal compressive skeptical
echo "Evaluate this argument" | explaind --chain exploratory balanced compressive --export chain.md
explaind --chain causal skeptical --dry-run "What is the hard problem of consciousness?"
```

### `--honest` usage

```bash
echo "What causes inflation?" | explaind --honest
echo "Is consciousness an illusion?" | explaind --honest --think
explaind --honest --scratchpad notes.md --export review.md "Evaluate this argument"
explaind --honest --dry-run "What is the hard problem of consciousness?"
```

Both `--scratchpad` and `--context` are optional and can be combined with each other and with `--ability`, `--compare`, `--think`, and `--dry-run`:

```bash
explaind --ability causal \
         --scratchpad hypothesis.md \
         --context prior_analysis.md \
         "What should we conclude?"
```

### Behavioral details worth knowing

- `--compare` requires at least two ability names.
- `--compare` and `--ability` are mutually exclusive.
- `--dry-run` never invokes the model backend.
- `--trace` can be combined with `--dry-run` or regular execution.
- The default backend is `ollama`.
- `llamacpp` is accepted by config validation but not implemented by the invoker.

## `--compare` showcase

The following was observed on May 13, 2026 using the current default config:

- backend: `ollama`
- model: `gemma4-e2b_q4_k_m:latest`
- prompt: `What causes inflation?`

Command:

```bash
echo "What causes inflation?" | explaind --compare skeptical causal compressive
```

What changed across the three runs was not the question. It was the reasoning pressure applied to the same question.

| Ability | Observed output shape |
|---|---|
| `skeptical` | Opened by challenging the framing of the question itself, arguing that inflation is not a single unified phenomenon and that the question smuggles in assumptions about coherence, causality, and definition stability. |
| `causal` | Reorganized the answer into explicit causal chains, separating demand-pull, cost-push, and expectation-driven mechanisms and tracing each from root condition to effect. |
| `compressive` | Collapsed the explanation to two dominant mechanisms, demand-pull and cost-push, and ended with a short summary instead of extended qualification. |

The stable point is visible immediately: `skeptical` interrogates assumptions, `causal` traces mechanisms, and `compressive` strips the answer down to the load-bearing structure. Exact phrasing will still vary with model build, quantization, and inference stack.

---

## `--think` and Gemma 4 thinking mode

Gemma 4 exposes a model-specific thinking mode rather than relying on generic chain-of-thought prompting conventions. The official model card documents a native `<|think|>` token and a corresponding thought channel in the model's output format. That matters because `explaind` is explicitly designed around Gemma 4's actual control surface, not around generic "LLMs like to reason step by step" assumptions.

In the current implementation, `--think` injects `<|think|>` into the system prompt block before the rest of the layers are assembled. Tests confirm that the token appears inside the system layer and upstream of the bias field and user input. In practical terms, `explaind` treats thinking mode as a first-class model capability that can be toggled deterministically and inspected with `--dry-run` and `--trace`.

This is intentionally Gemma 4-specific. If the model exposes a native reasoning control token, the harness should use the token the model was built to understand.

---

## Installation and Setup

### Requirements

- Python 3.11+
- Ollama running locally
- a local Gemma 4 model available to Ollama

### Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
ollama pull gemma4-e2b_q4_k_m:latest
```

The package metadata currently declares:

- package name: `explaind`
- version: `0.6.2`
- Python requirement: `>=3.11`

### Configure `explaind.toml`

Configuration is optional. If `explaind.toml` is absent, the code uses built-in defaults:

```toml
model_backend = "ollama"
model_name = "gemma4-e2b_q4_k_m:latest"
max_tokens = 2048
temperature = 0.0
```

Current config behavior:

- missing config file falls back to defaults
- unknown keys raise `ConfigError`
- `model_backend` must be `ollama` or `llamacpp`
- `llamacpp` is parsed successfully but execution is not implemented yet
- `temperature` must be between `0.0` and `2.0`
- `max_tokens` must be a positive integer

---

## Repository Layout

The current repository layout is:

```text
explaind/
├── abilities/
│   ├── balanced.md
│   ├── causal.md
│   ├── compressive.md
│   ├── exploratory.md
│   └── skeptical.md
├── explaind/
│   ├── cli.py
│   ├── color.py
│   ├── config.py
│   ├── context.py
│   ├── errors.py
│   ├── gemma.py
│   ├── invoker.py
│   ├── loader.py
│   ├── main.py
│   ├── prompts/
│   │   └── __init__.py
│   └── trace.py
├── GEMMA.md
├── pyproject.toml
├── README.md
└── tests/
```

One naming detail is worth making explicit: the prompt assembler currently lives in `explaind/prompts/__init__.py`. There is no standalone `assembler.py` module in the present codebase.

---

## Current Status

What is implemented today:

- deterministic prompt assembly with enforced layer order
- whitelist-only ability loading
- invariant injection from `GEMMA.md`
- runtime `BIAS FIELD` generation
- fixed `CONTEXT WINDOW LAYERS` rendering
- input loading from stdin or positional file path
- config loading and strict validation
- compare mode, dry-run mode, trace mode, and think mode
- Ollama invocation with local HTTP transport
- test coverage for ordering, golden prompts, config validation, compare mode, thinking mode, trace output, context rendering, and input loading

What is not implemented today:

- a `--version` flag
- llama.cpp execution backend
- agent loops
- tool use
- retrieval or memory

---

## Design Philosophy

`explaind` is stateless on purpose. Each invocation is a fresh reasoning trajectory. The project assumes that if you want reliable steering, the cleanest baseline is to remove hidden carry-over state and make the full control surface inspectable inside a single prompt. This keeps the system analyzable and makes prompt diffs meaningful.

It also refuses the usual local-LLM move of wrapping everything in an agent. That is not because Gemma 4 lacks useful capabilities. The Gemma 4 model card explicitly exposes system prompts, thinking mode, and function-calling support. The point here is narrower: local agent stacks add another fragile layer of tool formatting, planner logic, and orchestration behavior on top of an already prompt-sensitive model. A one-shot harness makes it easier to isolate prompt-level steering effects and see what the prompt itself is doing.

The redundant `BIAS FIELD` exists because instruction following is not binary. A model can understand a direction early in the prompt and still drift later under long-context pressure, user wording, or flattening toward a generic assistant style. Reasserting the active trajectory immediately before the task is therefore a deliberate recency hack, not duplication by accident.

Finally, `explaind` treats Gemma 4 as stochastic and only partially instruction-following by design. That is a realistic stance for open-weight local models. The right response is not to pretend the model is deterministic if prompted politely enough. The right response is to build a harness that constrains variance, makes reasoning pressure legible, and exposes the exact prompt that produced the output.

---

## References

- Google DeepMind, Gemma 4 model card: [https://huggingface.co/google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it)
- Gemma 4 prompting and performance sensitivity benchmark: [https://arxiv.org/abs/2604.07035](https://arxiv.org/abs/2604.07035)
- Georgi Gerganov on harness and prompt-construction fragility: [https://simonwillison.net/2026/Mar/30/georgi-gerganov/](https://simonwillison.net/2026/Mar/30/georgi-gerganov/)
