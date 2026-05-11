# explaind

A local-first debugging CLI powered by Gemma 4.

---

## Overview

This project has been built as part of the DEV Gemma 4 Challenge, with the goal of exploring how structured prompting, deterministic pipelines, and persistent context layers can influence and improve LLM debugging reliability.

> See [Gemma 4 DEV Challenge](https://dev.to/devteam/join-the-gemma-4-challenge-3000-prize-pool-for-ten-winners-23in?)

Rather than treating the model as a black box that produces one-off answers, this system is designed around the idea that model behavior can be shaped, measured, and iteratively improved through:

- strict input/output constraints  
- persistent reasoning context (GEMMA.md)  
- traceable execution flows  
- and feedback loops that evaluate consistency over time  

---

## What it does

So far, `explaind` turns raw software failures (logs, stack traces, git diffs) into grounded root-cause explanations using local Gemma 4 models.

It acts as a **debugging reasoning layer** over failure output:

- identifies root causes
- reconstructs causal chains
- suggests fixes
- grounds answers in evidence from logs/diffs

---

## Core idea: GEMMA.md as a model behavior spec

Unlike traditional AI tools, `explaind` treats the model as something to be **studied, not just used**.

We introduce `GEMMA.md`, a project-level file inspired by `CLAUDE.md`, which serves as:

> A living specification of how Gemma 4 behaves in debugging tasks.

But unlike static prompt files, `GEMMA.md` is **learned from observation**.

---

## Experimental loop

Each run of `explaind` can optionally log:

- raw input (logs / diffs)
- model output
- reasoning traces (when available)
- structured failure modes (hallucination, formatting errors, missing evidence, etc.)

These logs are analyzed to:

- identify recurring model behaviors
- detect failure patterns
- refine prompting strategies
- update `GEMMA.md` over time

---

## Why this matters

Gemma 4 is not treated as a black box.

Instead, we explore:

> What patterns emerge when a strong open model is consistently used for structured debugging tasks?

This turns the project into a lightweight **model behavior research tool**, not just a CLI.

---

## Why Gemma 4

We use Gemma 4 E2B locally because:

- it runs fully offline (local-first constraint)
- it handles structured reasoning tasks well
- it exposes useful intermediate reasoning traces
- it is sensitive enough to prompt design that behavior differences are observable

This makes it ideal for studying model behavior under constrained debugging prompts.

---

## What gets logged (optional experimental mode)

When enabled, `explaind` can record:

- input logs / diffs
- model responses
- reasoning traces (if exposed)
- structured evaluation of output quality

This enables iterative improvement of:

- prompts
- output schema
- GEMMA.md rules