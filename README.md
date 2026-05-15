# explaind

`explaind` is a local-first cognitive steering layer and reasoning observatory for Gemma 4, built as part of the **Gemma 4 DEV Challenge**.

It is not a chatbot wrapper, not an agent system, and not a RAG tool. It is a deterministic prompt-assembly harness that shapes reasoning trajectories, exposes the steering surface for inspection, measures how that steering behaves under repeated runs, and documents failure modes honestly. The project is built around Gemma 4's prompt sensitivity, harness dependence, and context-position effects rather than pretending those properties do not matter.

The software runs one prompt or a tightly controlled family of prompts against a local backend. It does not add tool loops, hidden memory, autonomous planning, or runtime prompt mutation. The core claim is narrower and more testable: for Gemma 4, prompt structure is part of the system design, not presentation.

## What explaind Is

- A deterministic prompt-physics layer for Gemma 4.
- A repository of structured reasoning abilities implemented as bias vectors, not personas.
- A reasoning observatory with `--dry-run`, `--trace`, `--compare`, `--honest`, `--chain`, `--scaffold`, `--consensus`, and Markdown export.
- A local CLI that currently targets Ollama with the default model `gemma4-e2b_q4_k_m:latest`.
- A codebase with explicit prompt-order tests, golden prompt fixtures, scaffold tests, and consensus tests.

## What explaind Is Not

- Not an agent framework.
- Not a tool-using runtime.
- Not a memory system.
- Not a fine-tuning pipeline.
- Not a retrieval system.
- Not a claim that prompt engineering "solves" Gemma 4.

## Why It Exists

Gemma 4 is strong enough to be useful locally and sensitive enough to be misread if the harness is sloppy. The public model card emphasizes reasoning mode controls, multi-turn formatting, and on-device deployment for the Gemma 4 family. At the same time, practitioner reports from April 2026 repeatedly describe brittle system-prompt adherence, inconsistent thinking toggles, a tendency to privilege parametric knowledge over injected context, and large quality swings depending on chat template and harness details. Georgi Gerganov summarized the broader local-model problem on March 30, 2026: what users observe is often a property of the harness, template, and prompt-construction chain as much as the model itself.

`explaind` treats those reports as design input. It does not fight Gemma 4 by piling on more orchestration. It narrows the surface area, makes the steering visible, and turns the harness into a first-class software artifact.

The table below separates the observed failure pattern from the design response:

| Gemma 4 Failure Mode | explaind Response | Research Basis |
|---|---|---|
| Weak system prompt adherence | Three-position BIAS FIELD: primacy anchor, periodic refresh, recency field | Transformer attention and long-context position research; prompt-format sensitivity work |
| Overconfidence / shallow elaboration | `calibrator` ability and `--honest` two-pass critique | Gemma 4 community reports; confidence-calibration framing |
| Prefers parametric knowledge over input | `--scratchpad` and `--context` injection with semantic headers and explicit preference instructions | Gemma 4 community reports; structured prompt grounding |
| Stochastic output variance | `--consensus N` self-consistency aggregation | Wang et al. (2022) |
| Reasoning collapse without harness | Deterministic prompt ordering plus optional cognitive scaffold across `--chain` passes | Harness fragility reports; long-context steering research |
| "Sounds smarter than it is" | `devil` adversarial pressure, `skeptical` and `calibrator` audit paths, structured ability specs | Gemma 4 community reports; prompt-structure research |

Observed Gemma 4 failure patterns here come from practitioner evidence, not a formal benchmark of Gemma 4 alone: LocalLLaMA threads on system prompts, thinking toggles, and context override; Hacker News discussion around local harnesses; and Simon Willison's March 30, 2026 note quoting Georgi Gerganov on prompt-construction fragility.

## Current Implementation Surface

As of this repository version:

- Prompt assembly is deterministic and byte-stable for identical inputs.
- Eight abilities are implemented and whitelisted.
- Six presets are implemented as curated ability mappings plus a preset marker in the recency field.
- `--compare`, `--honest`, `--chain`, `--scaffold`, `--consensus`, `--scratchpad`, `--context`, `--trace`, `--dry-run`, and `--export` are implemented.
- `--list-presets` is implemented.
- `--list-abilities` is not implemented.
- `--auto` is not implemented.
- `model_backend = "llamacpp"` parses in config validation but live execution is not implemented.

That distinction matters throughout this README. Anything described below is either implemented in the current codebase or explicitly marked as planned.

## Prompt Physics Architecture

The logical steering stack is:

```text
SYSTEM -> GEMMA.md -> ABILITY -> BIAS FIELD -> USER INPUT
```

The actual rendered prompt in this repository is more specific:

```text
SYSTEM PROMPT
  primacy anchor injected inside system block
GEMMA.md
  periodic refresh #1
ABILITY
  periodic refresh #2
CONTEXT WINDOW LAYERS
COGNITIVE SCAFFOLD (optional; only with --chain --scaffold)
BIAS FIELD
<user_input>...</user_input>
```

The implementation lives in [explaind/prompts/__init__.py](./explaind/prompts/__init__.py), [explaind/main.py](./explaind/main.py), [explaind/context.py](./explaind/context.py), and [explaind/scaffold.py](./explaind/scaffold.py). Prompt order is locked down by `tests/test_prompt_order.py`, `tests/test_three_position_bias.py`, and `tests/test_golden.py`.

### Layer-by-layer

#### 1. System prompt

`SYSTEM_PROMPT` defines the neutral substrate: a reasoning assistant that responds clearly, directly, and accurately, adapts reasoning style to the task, and does not assume a default task type.

#### 2. GEMMA.md invariant layer

`GEMMA.md` is static and always upstream of steering. It enforces:

- no hallucinated facts
- preserved uncertainty
- separation of observation from inference
- explicit naming of missing context and weak evidence

This is the hard floor of the system. Abilities do not override it.

#### 3. Ability layer

Ability files in `abilities/*.md` are structured bias vectors. They are not free-form personas. Every ability file follows a deliberate format:

- `INVARIANTS`
- `SPECIFICATION`
- `EXAMPLES`
- `AMPLIFIES`
- `SUPPRESSES`
- `SELF-VERIFICATION`
- `REASONING EFFECT`

That format matters. It gives the model a task, a method, and an explicit knowledge or control frame rather than a loose prose role. This is where the repository draws on Task-Method-Knowledge style decomposition and prompt-structure research.

#### 4. Context window layers

`CONTEXT WINDOW LAYERS` is always present, even when the fields are empty. In the current implementation it includes:

- `[SCRATCHPAD]`
- `[REASONING TRACE]`
- `[COMPETING INTERPRETATIONS]`
- optional `[REFERENCE CONTEXT]`
- `[CONTEXT INSTRUCTION]`

The stable slotting is intentional. Empty fields render as the literal string `none`, which keeps prompt geometry stable across runs. `--scratchpad` and `--context` populate this block with semantically headed content:

- `[ACTIVE WORKING MEMORY]` for scratchpad material
- `[REFERENCE CONTEXT]` for supporting documents

#### 5. Cognitive scaffold

When `--chain` and `--scaffold` are both active, a scaffold injection is inserted between the context block and the recency bias field. This is not persistent memory across sessions; it is persistent state inside a single chained invocation.

#### 6. Recency bias field

`build_bias_field()` renders the final steering block immediately before user input. It contains the active reasoning mode, mode-specific instructions, invariant activation, and optional `[PRESET: NAME]` marker.

#### 7. User input

The final payload is wrapped in XML-style tags:

```xml
<user_input>
...
</user_input>
```

This is the task object the rest of the stack is trying to shape.

## The Three-Position BIAS FIELD

This is the repository's main steering differentiator.

The "three-position BIAS FIELD" is not the same text pasted three times. It is a coordinated steering system with three jobs:

### Primacy

The first steering signal is a short, ability-specific anchor prepended inside the system block. This is implemented by `_PRIMACY_ANCHORS`. Its job is to bias the initial interpretive frame before the model sees invariants, context, or user input.

Examples:

- `skeptical`: "Default to doubt."
- `causal`: "Map causal relationships rigorously."
- `compressive`: "Distill to core essence."

### Periodic refresh

The second steering position is a refresh sentence injected after `GEMMA.md` and again after the ability block when present. This is implemented by `_PERIODIC_REFRESHES`.

Its job is not style. Its job is anti-drift. Once the prompt grows longer, the model is asked to re-activate the steering regime at two interior positions instead of relying on the opening bias alone.

### Recency

The final steering signal is the explicit `BIAS FIELD` immediately before `<user_input>`. This is implemented by `_RECENCY_FIELDS` and is the most forceful instruction block in the system.

For example, `skeptical` becomes:

```text
BIAS FIELD
[REASONING MODE: SKEPTICAL]
Activate full skeptical filter now...
[INVARIANTS: ACTIVE]
END BIAS FIELD
```

### Why these positions

This design is backed by two lines of evidence:

- Position bias in long-context models is real. "Lost in the Middle" showed that relevant information is often used more effectively when it appears near the beginning or end of context than when it sits in the middle.
- Prompt formatting is not neutral. Prompt-format sensitivity work showed large performance differences across meaning-preserving formats, and more recent structured-prompt work reported substantial gains from explicit prompt structure on reasoning tasks.

`explaind` turns those findings into software:

- primacy anchor for first-frame bias
- periodic refresh for interior reinforcement
- recency field for late control pressure

The system does not guarantee instruction following. It increases the odds that the intended reasoning direction stays active under long prompts and stochastic decoding.

## Structured Ability Files and TMK Framing

Each ability file is deliberately more like a compact task specification than a persona card.

The mapping to a TMK-style decomposition is loose but intentional:

- Task: what kind of reasoning problem is being posed
- Method: the process steps in `SPECIFICATION`
- Knowledge and control: invariants, amplifies, suppresses, examples, and self-checks

That is why the ability files are structured the way they are. They are not trying to "sound like" a thinker. They are trying to constrain the method the model uses.

This also explains why the abilities outperform a vague "act like a skeptic" prompt in principle. The model receives:

- explicit non-negotiables
- a concrete process
- examples of correct steering
- a list of what to amplify
- a list of what to suppress
- a verification checklist

That level of structure is closer to a control interface than to roleplay.

## The Cognitive Scaffold

The cognitive scaffold is the most original mechanism in the repository.

It is activated only with:

```bash
explaind --chain ... --scaffold
```

### What it does

The scaffold maintains structured state across a chained reasoning run. The state is represented by `ScaffoldState` and currently tracks:

- `session_id`
- `current_stage`
- `stage_history`
- `raw_input`
- `claims`
- `causal_graph`
- `compressive_summary`
- `uncertainty_register`
- `falsification_conditions`
- `confidence_scores`
- `drift_detected`
- `tokens_used`
- `total_passes`

The scaffold injection tells the model it is operating inside a persistent reasoning architecture and asks it to emit a single machine-readable update block:

```text
[SCAFFOLD_UPDATE]
{
  "claims": [...],
  "causal_graph": {...},
  "compressive_summary": "...",
  "uncertainty_register": [...],
  "falsification_conditions": [...],
  "confidence_scores": {...}
}
[/SCAFFOLD_UPDATE]
```

### How it is updated

`parse_scaffold_update()` looks for the block, parses the JSON, merges updates into the persistent scaffold state, and strips the update block from the visible output. Merging is conservative:

- claims are appended without duplication
- causal graph nodes and edges are merged
- confidence dictionaries are updated by key
- summaries are replaced only when present

### Graceful degradation

The model is not assumed to comply perfectly.

If the block is missing or malformed:

- the output is preserved as-is
- the scaffold is not destroyed
- `drift_detected` is set to `True`

That is the right failure mode for an LLM harness. When the model refuses the protocol, the chain still produces usable text and the scaffold reports the drift rather than pretending state was updated.

### Why it exists

Without a scaffold, `--chain` is just sequential prompting with handoff text. With a scaffold, each pass can inherit an explicit evolving state: extracted claims, causal structure, compressive summary, uncertainty, falsifiers, and confidence. This makes `--chain causal calibrator compressive` materially different from three independent runs.

### Important boundary

The scaffold is persistent only inside one CLI chain. `explaind` is still stateless across invocations.

## Self-Consistency Aggregation

`--consensus N` implements a lightweight self-consistency layer inspired by Wang et al. (2022).

### Research basis

Wang et al. reported that sampling multiple reasoning paths and selecting the most consistent answer improved chain-of-thought accuracy by:

- +17.9 on GSM8K
- +11.0 on SVAMP
- +12.2 on AQuA
- +6.4 on StrategyQA
- +3.9 on ARC-challenge

That is the main research justification for `--consensus N`.

### Current implementation

The code in [explaind/consensus.py](./explaind/consensus.py) does the following:

1. Assemble one prompt under the chosen ability or preset.
2. Invoke the backend `N` times.
3. Tokenize each output as lowercase word sets.
4. Compute pairwise Jaccard similarity.
5. Count another run as agreeing when similarity is greater than `0.6`.
6. Pick the output with the highest agreement score.
7. Break ties by choosing the longer output.
8. Label confidence as:
   - `HIGH` when agreement percentage is at least `80`
   - `MEDIUM` when agreement percentage is at least `60`
   - `LOW` otherwise

### Why it compounds with ability steering

Consensus does not replace steering. It samples repeated outputs under the same steering regime. If the active ability is `causal`, the repeated outputs are multiple causal attempts. If it is `skeptical`, the repeated outputs are multiple skeptical attempts. The ability shapes the trajectory; consensus stabilizes variance within that trajectory.

### Current caveats

- The implementation is heuristic, not a theorem about correctness.
- Agreement is lexical Jaccard, not semantic equivalence.
- The default config uses `temperature = 0.0`. If the backend behaves deterministically at that temperature, `--consensus` may sample nearly identical paths and mainly expose backend nondeterminism rather than true reasoning diversity.
- Small `N` is conservative. Because agreement counts agreeing peer runs, `N=2` can never exceed `50%` in the current metric. In practice, `N>=3` is the meaningful regime.

## The Eight Abilities

These mappings are design analogies, not claims that Gemma 4 literally instantiates human cognitive modules. The point is to borrow stable reasoning patterns from cognitive science and epistemology and turn them into explicit prompt controls.

### Core steering abilities

| Ability | What it does | Primary failure mode addressed | Cognitive grounding |
|---|---|---|---|
| `balanced` | Holds competing evidence without forcing premature closure | Bias from over-steering or single-frame dominance | Experimental control prior more than a human-cognition analog |
| `skeptical` | Audits assumptions, evidence quality, and confidence inflation | Overconfidence, shallow explanation, soft endorsement | Deliberative System 2 style checking in the Kahneman sense |
| `causal` | Traces mechanisms, separates trigger from root cause, finds first-failure points | Symptom description without mechanism | Causal-model and mechanistic reasoning traditions |
| `compressive` | Reduces to the highest-information path with minimal redundancy | Verbose but shallow answers, "sounds smart" inflation | Bounded-attention and signal-selection framing |
| `exploratory` | Reopens the question, reframes assumptions, expands possibility space | Premature closure and standard-answer lock-in | Generative, associative, System 1 style divergence |

### Research-grounded extensions

| Ability | What it does | Primary failure mode addressed | Cognitive grounding |
|---|---|---|---|
| `calibrator` | Forces explicit confidence, unknowns, and falsification conditions | Overconfidence and vague hedging | Metacognitive confidence monitoring and calibration |
| `devil` | Constructs the strongest adversarial case against the dominant framing | Sycophancy, agreement-seeking, under-tested claims | Adversarial evaluation and counterargument generation |
| `updater` | Explicitly models prior -> evidence -> update -> posterior | Parametric override and silent belief revision | Bayesian belief revision, predictive processing, active inference |

### File-level notes

- All eight ability files are loadable and enforced by whitelist in `ALLOWED_ABILITIES`.
- Three-position steering is implemented for all eight abilities.
- Golden prompt fixtures currently exist for the original five core abilities.
- `trace` currently has explicit interpretation-map labels for the original five core abilities; extension abilities share the same steering machinery but fall back to `unknown ability` in the interpretation map.

## The Six Presets

Presets are a higher-level interface for users who want a named reasoning posture instead of a raw ability name.

Important implementation detail: in the current code, a preset is not a second prompt module. It is:

- an ability mapping defined in `PRESET_MAP`
- a short preset description for listing and validation
- a `[PRESET: NAME]` marker injected into the recency bias field

The prose inside `presets/*.md` is present in the repository and validated by tests, but it is not separately appended as its own prompt layer.

| Preset | Runtime mapping | When to use it | Example domains |
|---|---|---|---|
| `philosopher` | `exploratory` | Reframe assumptions, open conceptual space, avoid premature closure | philosophy, legal theory, social theory, speculative research |
| `engineer` | `causal` | Trace mechanisms and failure chains | incidents, debugging, reliability, differential reasoning in medicine |
| `critic` | `skeptical` | Interrogate evidence, premises, and hidden assumptions | peer review, policy critique, legal argument review, model audit |
| `synthesiser` | `balanced` | Integrate multiple frameworks without forcing a winner | literature reviews, interdisciplinary research, policy synthesis |
| `analyst` | `compressive` | Produce dense signal with minimal elaboration | security triage, intelligence summaries, chart-note compression |
| `strategist` | `causal` | Map leverage points and second-order effects | security planning, operations, policy strategy, product bets |

The `strategist` prose mentions exploratory secondary framing, but the runtime mapping is still a single `causal` ability in the current code.

## Execution Modes

The CLI has several distinct execution modes:

| Mode | What it does |
|---|---|
| Single run | One prompt under one ability or preset |
| Comparison | Same input, multiple abilities, independent runs |
| Honest mode | Fixed two-pass `balanced -> skeptical` critique pipeline |
| Chain mode | Sequential transformation pipeline where each pass hands off to the next |
| Scaffolded chain | Chain mode plus persistent JSON state |
| Consensus mode | Repeated runs of the same assembled prompt with self-consistency aggregation |

## Complete CLI Reference

### Implemented interfaces

| Flag / interface | What it does | Research basis | Compatible with | Example |
|---|---|---|---|---|
| positional `file` | Reads input from a file. If omitted, stdin is used. | - | All runtime modes | `explaind notes.txt --ability skeptical` |
| `--file PATH` | Alternative file input flag. Takes precedence over positional file when both are present. | - | All runtime modes | `explaind --file notes.txt --dry-run` |
| `--ability NAME` | Runs one ability directly. If omitted outside other modes, behavior defaults to `balanced`. | Ability steering architecture | `--think`, `--trace`, `--scratchpad`, `--context`, `--export`, `--dry-run`, `--consensus` | `echo "Why?" | explaind --ability causal` |
| `--preset NAME` | Maps a named preset to its ability and inserts `[PRESET: NAME]` in the recency field. | Preset abstraction over ability steering | Same as `--ability`, plus `--consensus`; not with `--ability`, `--compare`, `--chain`, `--honest` | `echo "Evaluate this strategy" | explaind --preset strategist` |
| `--compare NAME...` | Runs the same input through 2 or more abilities independently and prints each result under its own header. | Comparative steering evaluation | `--think`, `--trace`, `--scratchpad`, `--context`, `--export`, `--dry-run`; not with `--ability`, `--preset`, `--honest`, `--chain`, `--consensus` | `echo "What caused this?" | explaind --compare skeptical causal compressive` |
| `--honest` | Fixed two-pass mode: first `balanced`, then `skeptical` self-critique of the first response. Any user-supplied `--ability` is ignored. | Confidence calibration and adversarial self-audit | `--think`, `--trace`, `--scratchpad`, `--context`, `--export`, `--dry-run`; not with `--compare`, `--preset`, `--chain`, `--consensus` | `echo "Assess this claim" | explaind --honest` |
| `--chain NAME [NAME ...]` | Sequentially transforms the question through 2 or more abilities. Each later pass receives a structured reasoning handoff from the previous pass. | Multi-stage steering | `--think`, `--trace`, `--scratchpad`, `--context`, `--export`, `--dry-run`, optional `--scaffold`; not with `--ability`, `--compare`, `--preset`, `--honest`, `--consensus` | `echo "What happened?" | explaind --chain causal calibrator compressive` |
| `--scaffold` | Activates persistent scaffold state during a chain run. Requires `--chain`. | Workspace-style persistent reasoning state | Only with `--chain`; also works with `--trace`, `--export`, `--dry-run`, `--scratchpad`, `--context`, `--think` | `echo "Analyze this failure" | explaind --chain causal calibrator compressive --scaffold` |
| `--consensus N` | Repeats the same assembled prompt `N` times, chooses the most consistent output, prints an agreement report, and can export consensus analysis. Valid range: `2-10`. | Wang et al. (2022) self-consistency | `--ability` or `--preset`, `--think`, `--trace`, `--scratchpad`, `--context`, `--export`, `--dry-run`; not with `--compare`, `--chain`, `--honest` | `echo "Explain this failure" | explaind --ability skeptical --consensus 5` |
| `--think` | Injects Gemma 4's `<|think|>` token inside the system block before the rest of the prompt is assembled. | Gemma 4 native thinking mode | All execution modes except listing commands | `echo "Trace the mechanism" | explaind --ability causal --think` |
| `--scratchpad FILE` | Loads a Markdown file as `[ACTIVE WORKING MEMORY]` and injects it into `[SCRATCHPAD]`. | Grounding and parametric-override mitigation | Single, compare, honest, chain, scaffolded chain, consensus, dry-run, trace, export | `explaind --ability causal --scratchpad notes.md question.txt` |
| `--context FILE` | Loads a Markdown file as `[REFERENCE CONTEXT]` and injects it into the context block with explicit preference instructions. | Grounding and parametric-override mitigation | Same as `--scratchpad` | `explaind --context prior.md --preset critic question.txt` |
| `--export [FILE]` | Writes Markdown output. If no filename is provided, creates `explaind_YYYYMMDD_HHMMSS.md`. Supports chain, honest, scaffold, and consensus summaries. | Reproducibility and observability | All runtime modes | `echo "Why?" | explaind --compare skeptical causal --export runs.md` |
| `--dry-run` | Prints the assembled prompt instead of calling the model. In consensus mode it prints the prompt once plus a note. In honest and chain modes it prints prompt blocks, not simulated model outputs. | Prompt observability | All runtime modes | `echo "Inspect me" | explaind --ability devil --dry-run` |
| `--trace` | Prints a prompt-construction trace to stderr, including model settings, prompt size, layer presence, and scratchpad/context lengths. | Observability | All runtime modes except listing commands | `echo "Inspect me" | explaind --ability updater --trace --dry-run` |
| `--list-presets` | Prints all six presets and exits without requiring input. | - | Standalone listing command | `explaind --list-presets` |

### Planned but not implemented

| Flag | Status | Notes |
|---|---|---|
| `--list-abilities` | Not implemented | The runtime whitelist exists in code, but there is no CLI flag yet. |
| `--auto` | Not implemented | No parser entry or runtime behavior exists in the current codebase. |

### Compatibility notes that matter in practice

- `--compare` requires at least two ability names.
- `--chain` requires at least two ability names.
- `--scaffold` requires `--chain`.
- `--honest` always runs `balanced` then `skeptical` even if `--ability` is present.
- `--preset` is mutually exclusive with `--ability` and `--compare`.
- `--consensus` is mutually exclusive with `--compare`, `--chain`, and `--honest`.
- `--file` overrides positional file input when both are supplied.

## What the Tests Actually Verify

The repository does more than unit-test helpers. The test suite verifies the prompt geometry and most of the user-facing CLI behavior:

- `tests/test_prompt_order.py`: deterministic ordering of system, GEMMA, ability, context, bias field, and user input
- `tests/test_three_position_bias.py`: primacy anchor, periodic refresh, and recency field across all eight abilities
- `tests/test_golden.py` plus `tests/golden/*.txt`: golden prompt fixtures for balanced, skeptical, causal, compressive, and exploratory
- `tests/test_scratchpad_context.py`: semantic header injection and CLI integration for `--scratchpad` and `--context`
- `tests/test_think.py`: `<|think|>` placement inside the system block
- `tests/test_compare.py`, `tests/test_honest.py`, `tests/test_chain.py`, `tests/test_scaffold.py`, `tests/test_consensus.py`: execution-mode behavior and mutual exclusions
- `tests/test_export.py`: Markdown export, including scaffold and consensus summaries
- `tests/test_config.py`, `tests/test_input_loader.py`, `tests/test_invoker.py`: config, input, and backend behavior
- `tests/test_presets.py`: preset loading, marker insertion, and listing
- `tests/test_trace.py`: trace output shape and content

This is part of the "reasoning observatory" story. `explaind` does not just steer prompts; it keeps the steering inspectable.

## Installation and Setup

### Requirements

- Python `3.11+`
- Ollama running locally
- A Gemma 4 model available to Ollama

### Why the default model is `gemma4-e2b_q4_k_m:latest`

The repository default is the Ollama quantized build `gemma4-e2b_q4_k_m:latest`. That is a deployment choice, not the canonical Hugging Face model identifier. It was chosen for the local edge story: it is small enough to run on 8 GB unified-memory machines while still exposing the Gemma 4 control surface the project is designed around.

### Recommended install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

For tests:

```bash
pip install -e .[dev]
```

Then pull the default model:

```bash
ollama pull gemma4-e2b_q4_k_m:latest
```

If Ollama is not already running:

```bash
ollama serve
```

### Configuration

Configuration is optional. If `explaind.toml` does not exist, the built-in defaults are:

```toml
model_backend = "ollama"
model_name = "gemma4-e2b_q4_k_m:latest"
max_tokens = 2048
temperature = 0.0
```

You can create `explaind.toml` with:

```toml
model_backend = "ollama"
model_name = "gemma4-e2b_q4_k_m:latest"
max_tokens = 2048
temperature = 0.2
```

Important current behavior:

- unknown config keys raise `ConfigError`
- valid backends are `ollama` and `llamacpp`
- `llamacpp` validates but does not execute yet
- `max_tokens` must be a positive integer
- `temperature` must be between `0.0` and `2.0`

`pyproject.toml` is the authoritative dependency definition. `requirements.txt` currently only lists `ollama`, so editable install from the project metadata is the safer path.

## Repository Structure

The current repository layout is:

```text
explaind/
├── abilities/
│   ├── balanced.md
│   ├── calibrator.md
│   ├── causal.md
│   ├── compressive.md
│   ├── devil.md
│   ├── exploratory.md
│   ├── skeptical.md
│   └── updater.md
├── presets/
│   ├── analyst.md
│   ├── critic.md
│   ├── engineer.md
│   ├── philosopher.md
│   ├── strategist.md
│   └── synthesiser.md
├── explaind/
│   ├── cli.py
│   ├── color.py
│   ├── config.py
│   ├── consensus.py
│   ├── context.py
│   ├── errors.py
│   ├── exporter.py
│   ├── gemma.py
│   ├── invoker.py
│   ├── loader.py
│   ├── main.py
│   ├── presets/
│   │   └── __init__.py
│   ├── prompts/
│   │   └── __init__.py
│   ├── scaffold.py
│   └── trace.py
├── tests/
│   ├── conftest.py
│   ├── golden/
│   │   ├── prompt_balanced.txt
│   │   ├── prompt_causal.txt
│   │   ├── prompt_compressive.txt
│   │   ├── prompt_exploratory.txt
│   │   └── prompt_skeptical.txt
│   ├── test_bias_field.py
│   ├── test_chain.py
│   ├── test_compare.py
│   ├── test_config.py
│   ├── test_consensus.py
│   ├── test_context.py
│   ├── test_dry_run.py
│   ├── test_export.py
│   ├── test_file_flag.py
│   ├── test_golden.py
│   ├── test_honest.py
│   ├── test_input_loader.py
│   ├── test_invoker.py
│   ├── test_loader.py
│   ├── test_presets.py
│   ├── test_prompt_order.py
│   ├── test_scaffold.py
│   ├── test_scratchpad_context.py
│   ├── test_think.py
│   ├── test_three_position_bias.py
│   └── test_trace.py
├── GEMMA.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

Two structure details are easy to miss:

- The prompt assembler currently lives in `explaind/prompts/__init__.py`; there is no separate `assembler.py`.
- Preset content lives at repo root in `presets/*.md`, while preset mappings live in `explaind/presets/__init__.py`.

## Where explaind Fails

This section is intentionally blunt.

- The model may ignore scaffold update instructions. The repository handles this by setting `drift_detected = True` and preserving the visible output, but the scaffold can still fail to accumulate state cleanly.
- Ability steering changes reasoning style more reliably than it changes factual accuracy. A well-steered wrong answer is still wrong.
- `--consensus` at `N > 3` is slow on 8 GB-class local hardware, especially with the larger Gemma 4 variants or longer prompts.
- The three-position BIAS FIELD improves consistency but cannot guarantee instruction following. Position helps; it does not eliminate stochastic drift.
- Long `--chain` runs with `--scaffold` can exceed practical context budgets on complex topics, especially when prior pass output is large.
- The default `temperature = 0.0` makes consensus conservative. If your backend is near-deterministic, multiple runs may not generate the kind of diverse reasoning paths Wang-style self-consistency assumes.
- Presets are lighter-weight than they may look. In the current code they are ability aliases plus a preset marker, not fully separate prompt modules.

These are not marketing-friendly statements. They are important if you want to evaluate the project honestly.

## Design Philosophy

`explaind` is stateless per invocation on purpose. Hidden carry-over state makes prompt experiments hard to interpret and failure analysis hard to trust. A fresh run means the full steering surface is visible in one place.

It also refuses the standard "just wrap it in an agent" move. Agents are useful, but they mix multiple uncertainties at once: prompt formatting, tool schemas, parser behavior, retry logic, memory policy, and planner quality. This project is narrower. It asks what can be learned by making the prompt and harness themselves the object of engineering.

The system is honest about stochastic behavior because that is the right stance for local open-weight models. You do not get reliability by pretending a model is deterministic if asked politely enough. You get reliability by constraining the prompt geometry, inspecting the assembled prompt, measuring variance, and reporting when the model drifted anyway.

The failure modes are not bugs to hand-wave away. They are part of the operating environment. Weak instruction adherence, context-position effects, and preference for parametric priors are exactly the reasons a steering layer is interesting in the first place.

Finally, this project chooses prompt physics over fine-tuning because it is trying to characterize and steer reasoning behavior at inference time, on-device, with a transparent control surface. Fine-tuning can be useful, but it changes the model. `explaind` is about steering the model you already have.

## References

1. Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., and Zhou, D. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. arXiv:2203.11171. <https://arxiv.org/abs/2203.11171>
2. Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., and Liang, P. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. TACL. <https://arxiv.org/abs/2307.03172>
3. Sclar, M., Choi, Y., Tsvetkov, Y., and Suhr, A. (2024). *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*. ICLR 2024. <https://arxiv.org/abs/2310.11324>
4. Zhou, J., Adeseye, A., Virtanen, S., Hakkala, A., and Isoaho, J. (2026). *Strengthening Human-Centric Chain-of-Thought Reasoning Integrity in LLMs via a Structured Prompt Framework*. arXiv:2604.04852. <https://arxiv.org/abs/2604.04852>
5. Google DeepMind. *google/gemma-4-E2B-it model card*. Hugging Face. <https://huggingface.co/google/gemma-4-E2B-it>
6. Simon Willison (March 30, 2026), quoting Georgi Gerganov on local-model harness and prompt-construction fragility. <https://simonwillison.net/2026/Mar/30/>
7. LocalLLaMA thread: *Gemma 4 is terrible with system prompts and tools* (April 2026). <https://www.reddit.com/r/LocalLLaMA/comments/1sh1bwv/gemma_4_is_terrible_with_system_prompts_and_tools/>
8. LocalLLaMA thread: *Gemma 4 thinking system prompt* (April 2026). <https://www.reddit.com/r/LocalLLaMA/comments/1sfjhsx/gemma_4_thinking_system_prompt/>
9. LocalLLaMA thread: *Gemma 4 - lazy model or am I crazy?* (April 2026). <https://www.reddit.com/r/LocalLLaMA/comments/1sjyzmi/gemma_4_lazy_model_or_am_i_crazy_bit_of_a_rant/>
10. LocalLLaMA thread: *Gemma 4 31B sweeps the floor with GLM 5.1* (April 2026). <https://www.reddit.com/r/LocalLLaMA/comments/1sbtr5i/gemma_4_31b_sweeps_the_floor_with_glm_51/>
11. Hacker News discussion: *Google releases Gemma 4 open models* (April 2026), including practitioner reports about harness size, template bugs, and tool-calling instability under launch-day stacks. <https://news.ycombinator.com/item?id=47616361>
12. Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
13. Friston, K. (2010). *The free-energy principle: a unified brain theory?* *Nature Reviews Neuroscience*, 11, 127-138. <https://www.nature.com/articles/nrn2787>
14. Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.
15. Dehaene, S., and Naccache, L. (2001). *Towards a Cognitive Neuroscience of Consciousness: Basic Evidence and a Workspace Framework*. *Cognition*, 79(1-2), 1-37. <https://www.unicog.org/publications/DehaeneNaccache_WorkspaceModel_Cognition2001.pdf>
16. Chandrasekaran, B. (1987). *Generic Tasks as Building Blocks for Knowledge-Based Systems: The Diagnosis and Routine Design Examples*. *The Knowledge Engineering Review*. <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/C1551D1A1FC6DC0027B74702DFCCD744/S0269888900004458a.pdf/generic_tasks_as_building_blocks_for_knowledgebased_systems_the_diagnosis_and_routine_design_examples.pdf>
17. Murdock, J. W., and Goel, A. (2008). *Meta-case-based reasoning: Self-improvement through self-understanding*. Introduces TMKL, a Task-Method-Knowledge language. <https://research.ibm.com/publications/meta-case-based-reasoning-self-improvement-through-self-understanding>
