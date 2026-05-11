# explaind

A local-first debugging CLI powered by Gemma 4.

---

## Overview

**explaind** is a developer tool that turns raw software failures (logs, stack traces, and diffs) into grounded, structured explanations using local Gemma 4 models.

It helps answer:

> “Why did this break, and what actually caused it?”

Instead of unstructured AI responses, explaind produces **evidence-based debugging reasoning**:

- root cause identification  
- causal chain reconstruction  
- fix suggestions grounded in logs  
- structured, inspectable output  

---

## Core idea

At its core, explaind treats debugging as a **structured reasoning problem**, not a chat problem.

Each failure is transformed into a consistent artifact:

{
  "failure_type": "",
  "root_cause": "",
  "evidence": [],
  "causal_chain": "",
  "suggested_fix": ""
}

This makes debugging outputs:
- reproducible  
- comparable  
- inspectable over time  

---

## GEMMA.md — persistent debugging behavior layer

explaind introduces `GEMMA.md`, a project-level reasoning guide inspired by `CLAUDE.md`.

It defines how the model should behave during debugging tasks:

- prefer grounded evidence over inference  
- avoid hallucinating missing context  
- enforce structured reasoning output  
- bias toward “insufficient information” when uncertain  

Unlike a static prompt, `GEMMA.md` is designed to be **iteratively refined based on observed failures in real outputs**.

---

## Why Gemma 4

Gemma 4 is used because it:

- runs locally (offline-first debugging)
- handles structured reasoning reliably
- produces useful intermediate reasoning signals
- is sensitive enough to prompt structure to make behavior changes observable

This makes it ideal for structured debugging pipelines.

---

## Observability (lightweight experimental layer)

Each run of explaind optionally records a **trace session**, including:

- input log
- model output
- latency
- structured metadata

These traces are used to:
- inspect model consistency
- identify recurring failure patterns
- refine prompts and GEMMA.md rules over time

This is an **experimental layer**, not required for core functionality.

---

## What makes this different

Most tools:
AI explains your logs

explaind:
A deterministic debugging pipeline that produces structured reasoning artifacts using a local LLM, with optional instrumentation to study and improve its behavior over time

---

## Design principle

The system is intentionally split:

### Core product (must work)
- CLI debugging tool
- structured explanations
- reliable local inference

### Experimental layer (bonus)
- trace logging
- GEMMA.md refinement
- output analysis metrics

---

## Final insight

The CLI is the product.

The reasoning instrumentation is the twist.