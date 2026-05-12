# explaind — Gemma 4 DEV Challenge Debugging Intelligence System

A local-first debugging CLI powered by Gemma 4.

---

## Gemma 4 DEV Challenge Context

This project is built as part of the **Gemma 4 DEV Challenge**, demonstrating how local LLMs can be used for structured debugging reasoning rather than conversational assistance.

The goal is to show that Gemma 4 can:

- interpret software failures (logs, stack traces, diffs)
- produce structured, grounded reasoning outputs
- enforce consistent debugging schemas
- operate fully local-first (no API dependency)

---

## Overview

**explaind** is a developer tool that transforms raw software failures—logs, stack traces, and diffs—into grounded, structured explanations using local Gemma 4 models.

It helps answer:

> “Why did this break, and what actually caused it?”

Instead of unstructured AI responses, explaind produces **evidence-based debugging reasoning artifacts** that are consistent and inspectable.

---

## Core idea

Debugging is treated as a **structured reasoning problem**, not a chat problem.

Each failure is transformed into a consistent artifact:

```json
{
  "failure_type": "",
  "root_cause": "",
  "evidence": [],
  "causal_chain": "",
  "suggested_fix": ""
}
```

This makes debugging outputs:

- reproducible across runs  
- comparable between failures  
- grounded in log evidence  
- suitable for tooling or automation  

---

## GEMMA.md — persistent debugging behavior layer

explaind introduces `GEMMA.md`, a project-level reasoning guide inspired by `CLAUDE.md`.

It defines how the model should behave during debugging tasks:

- prefer grounded log evidence over inference  
- avoid hallucinating missing context  
- enforce structured output formats  
- default to “insufficient information” when uncertain  

Unlike static prompts, `GEMMA.md` is intended to be iteratively refined based on observed model behavior across real debugging runs.

---

## Why Gemma 4

Gemma 4 is used because it:

- runs locally (offline-first debugging)  
- supports structured reasoning workflows  
- responds well to strict prompt constraints  
- makes reasoning behavior observable through prompt design  

This makes it suitable for deterministic debugging pipelines.

---

## Core product

The primary experience of explaind is a CLI debugging workflow:

```bash
explaind explain error.log
```

or:

```bash
cat error.log | explaind explain
```

Output includes:

- root cause identification  
- causal chain reconstruction  
- evidence extracted from logs  
- suggested fix grounded in observed behavior  

The focus is **clarity, grounding, and reproducibility**.

---

## Structured output mode

When enabled, explaind produces structured JSON alongside human-readable explanations.

This enables:

- integration into tooling pipelines  
- reproducible debugging analysis  
- consistent evaluation of failure types  
- machine-readable debugging artifacts  

---

## Observability layer (experimental)

explaind includes an optional lightweight tracing system for inspecting model behavior.

Each trace may include:

- input log  
- model output  
- latency  
- structured metadata from analysis pipeline  

This layer is used for:

- debugging the tool itself  
- inspecting consistency across runs  
- refining prompts and `GEMMA.md` rules over time  

This is an experimental layer and not required for core functionality.

---

## What makes this different

Most tools:

AI explains your logs in natural language.

explaind:

A structured debugging pipeline that produces grounded reasoning artifacts using a local LLM (Gemma 4), with optional instrumentation to inspect and understand model behavior.

---

## Key differences

- structured outputs instead of free-form responses  
- local-first execution (no cloud dependency)  
- persistent behavior rules via `GEMMA.md`  
- evidence-grounded reasoning instead of speculation  

---

## Design principle

The system is intentionally split:

### Core product (user-facing)

- CLI debugging tool  
- structured explanations  
- reliable local inference  

### Configuration layer

- `GEMMA.md` for persistent debugging behavior rules  

### Experimental layer

- trace logging  
- output inspection  
- debugging of model reasoning behavior  

---

## Final insight

The CLI is the product.

Everything else exists to improve clarity, consistency, and grounding of debugging explanations.

The system is designed to make LLM-assisted debugging:

structured, reproducible, and evidence-based rather than conversational or speculative.