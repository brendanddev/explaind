# explaind

`explaind` is a local-first Python CLI for steering Gemma 4 reasoning through deterministic prompt construction. The current implementation reads input from stdin or an optional file argument, assembles a fixed prompt stack, sends that prompt to a local Gemma 4 runtime through the Ollama REST API, and prints the model's returned text to stdout.

The project does not fine-tune, patch, wrap, or otherwise modify the model. Its control surface is prompt design: system instructions, invariant reasoning constraints, ability-defined bias vectors, structured context layers, and a runtime bias field are composed in a strict order to shape how Gemma 4 reasons within a single inference.

---

## Gemma 4 Challenge

This project is built for the DEV Gemma 4 Challenge.

`explaind` aligns with that challenge by treating Gemma 4 as reasoning infrastructure inside a real CLI application rather than as a chat wrapper or fine-tuned system. The implementation focuses on:

- intentional use of Gemma 4's long context window as a structured prompt surface
- technical implementation quality through deterministic prompt assembly and golden-file tests
- creative model usage without fine-tuning, agents, tools, or retrieval layers
- practical CLI usability for local inference workflows

---

## Current Implemented State

Today, `explaind` is a local CLI that does four things:

1. accepts input from stdin or a positional file path
2. loads optional reasoning constraints and an optional ability module
3. assembles a prompt in a fixed, byte-stable order
4. invokes Gemma 4 locally through Ollama and prints the returned result

This is not an agent runtime. There are no tool loops, no orchestration layer, no RAG pipeline, and no external memory system. The model is treated as a stochastic reasoning engine whose behavior is shaped entirely by prompt composition.

---

## Gemma 4 Integration

The current model path is local-only:

- backend: Ollama REST API at `http://localhost:11434/api/generate`
- default model: `gemma4-e2b_q4_k_m:latest`
- prompt transport: a single assembled prompt sent as one request
- output behavior: the current implementation requests `stream: false` and prints the returned response text directly to stdout

There is no fine-tuning step, no tool calling, no retrieval augmentation, and no agent layer between the CLI and the model. `explaind` assumes the model already has the reasoning capacity; the software's job is to steer that capacity with structured prompt layers.

---

## CLI Usage

Install the package in a Python 3.11+ environment, then run:

```bash
explaind path/to/input.txt
cat path/to/input.txt | explaind
echo "Explain this failure" | explaind --ability skeptical
echo "Explain this failure" | explaind --dry-run
```

Current flags:

- `--ability NAME` loads one of the whitelisted ability files from `abilities/`
- `--dry-run` prints the fully assembled prompt and skips model invocation

Accepted ability names:

- `balanced`
- `skeptical`
- `causal`
- `compressive`
- `exploratory`

If no file is passed, the CLI reads stdin. Input is stripped and validated before prompt assembly. When the model is invoked, the response is printed to stdout and the model name plus latency are written to stderr.

---

## Core Architecture

The prompt pipeline is deterministic and currently assembled in this exact order:

1. `SYSTEM PROMPT`
2. `GEMMA.md`
3. `ABILITY`
4. `CONTEXT WINDOW LAYERS`
5. `BIAS FIELD`
6. `USER INPUT`

That order is enforced in code and covered by tests.

### 1. System Prompt

The system prompt is embedded in the Python package and defines the base role: a reasoning assistant that responds clearly, directly, and accurately without assuming a default task type.

### 2. GEMMA.md

`GEMMA.md` is loaded from the project root when present and injected as the invariant reasoning layer. It defines constraints such as preserving uncertainty, avoiding fabricated facts, and separating observation from inference. This layer is static and does not change per request.

### 3. Ability

When `--ability` is provided, the CLI loads the matching markdown file from `abilities/` and inserts it after `GEMMA.md`. Ability loading is whitelist-based and limited to the five supported names.

### 4. Context Window Layers

The prompt then inserts a structured `CONTEXT WINDOW LAYERS` block. In the current implementation, this block is always present and contains:

- `SCRATCHPAD`
- `REASONING TRACE`
- `COMPETING INTERPRETATIONS`
- `CONTEXT INSTRUCTION`

When no values are supplied, each reasoning state field is rendered as the literal string `none`.

### 5. Bias Field

A deterministic `BIAS FIELD` block is injected immediately before user input. It is derived from the active ability name and reinforces:

- bias label
- reasoning trajectory
- epistemic stance
- invariant status

### 6. User Input

The final layer is the raw user content wrapped in XML-style tags:

```xml
<user_input>
...
</user_input>
```

---

## Context Window as Control Surface

`explaind` treats Gemma 4's long context window, including the 128K context capacity associated with Gemma 4, as a structured working-memory surface rather than a passive token budget.

In the current codebase, that idea appears as the `CONTEXT WINDOW LAYERS` block:

- `scratchpad`
- `reasoning trace`
- `competing interpretations`

Right now these fields are populated with placeholders unless explicit values are passed into the context builder, so this is not yet a dynamic memory system. What is implemented today is the control surface itself: a stable prompt location where structured reasoning state can live within a single inference, with an instruction telling the model to treat that block as persistent working memory for that run.

---

## Ability System

Abilities in `explaind` are bias vectors, not personas.

The five implemented abilities are:

- `balanced`
- `skeptical`
- `causal`
- `compressive`
- `exploratory`

Each ability is a markdown file that changes reasoning direction by emphasizing some signals and suppressing others. For example:

- `skeptical` increases epistemic pressure and pushes the model to question unsupported claims
- `causal` prioritizes mechanism tracing and state-transition reasoning
- `compressive` pushes toward high-signal inference and reduced low-yield elaboration
- `exploratory` expands the possibility space before convergence
- `balanced` acts as the neutral default prior

The runtime `BIAS FIELD` sits immediately before the XML-wrapped user input and reinforces the active trajectory so that the intended reasoning pressure remains explicit at the end of the assembled prompt.

---

## Design Philosophy

The prompt is the program. Gemma 4 behavior is shaped entirely through structured prompt physics, not model modification.

In practical terms, that means:

- reasoning behavior is controlled by prompt layers, not by changing model weights
- invariants live in `GEMMA.md`, not in a learned memory system
- abilities steer trajectory, but do not override invariant constraints
- the context window is used as a deliberate reasoning surface
- the CLI performs deterministic assembly before a single model call

---

## Why This Fits the Gemma 4 Challenge

This project is a direct example of building with Gemma 4 by using the model's existing capabilities intentionally instead of abstracting them away.

Against the challenge criteria, the current implementation demonstrates:

- technical implementation quality: the prompt assembler is deterministic, ability loading is whitelist-based, and prompt structure is covered by tests including golden files
- intentional model usage: Gemma 4 is used as a reasoning engine whose behavior is steered through ordered prompt layers rather than post hoc wrappers
- creativity in using the context window: the prompt reserves explicit working-memory sections for scratchpad state, reasoning trace, and competing interpretations
- usability: the interface is a straightforward local CLI that accepts stdin or file input and supports dry-run inspection of the exact prompt sent to the model

This keeps the project grounded in the actual strengths of open models: local execution, inspectable behavior, and controllable reasoning through prompt structure.

---

## Repository Layout

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
│   ├── config.py
│   ├── context.py
│   ├── errors.py
│   ├── gemma.py
│   ├── invoker.py
│   ├── main.py
│   └── prompts/
│       └── __init__.py
├── tests/
├── GEMMA.md
├── pyproject.toml
└── README.md
```

---

## Verification Notes

The current behavior described above is reflected in the implementation and tests:

- prompt layer order is asserted in `tests/test_prompt_order.py`
- context window block structure is asserted in `tests/test_context.py`
- bias field values are asserted in `tests/test_bias_field.py`
- byte-stable prompt outputs are checked with golden files in `tests/test_golden.py`
