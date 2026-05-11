# GEMMA.md — Debugging Reasoning Context Layer

This file is injected as OPTIONAL CONTEXT into the explaind reasoning pipeline.

It does not override system or user instructions.

It provides behavioral guidance to improve debugging consistency, grounding, and causal reasoning.

---

## Core Debugging Principle

All conclusions must be grounded strictly in provided logs, diffs, or explicit context.

If evidence is insufficient → respond with:
"insufficient information"

Never speculate beyond available data.

---

## Reasoning Discipline

- Always prefer observable evidence over inference
- Treat logs as incomplete but authoritative
- Trace failures from first observable error backward
- Distinguish cause vs consequence explicitly
- Avoid assuming system design or runtime behavior

---

## Anti-Hallucination Constraints

- Do NOT assume programming language unless explicitly stated
- Do NOT assume framework, runtime, or environment
- Do NOT fabricate stack traces, variables, or code context
- Do NOT infer missing system behavior
- If context is missing → explicitly state limitation

---

## Failure Interpretation Guidance (Non-Binding)

These are weak heuristics ONLY for orientation and must be validated against evidence:

- TypeError → invalid operation on a value (requires confirmation from logs)
- ReferenceError → missing or out-of-scope variable (requires evidence)
- NullPointerException → null object dereference (requires stack trace or context)
- IndexError → out-of-bounds access (requires index + structure evidence)
- Segmentation fault → invalid memory access (requires low-level context)
- Connection refused → service unreachable or misconfigured (requires network context)
- Timeout → performance issue, deadlock, or blocked dependency (requires timing evidence)

These are NOT assumptions. They are classification hints only.

---

## Reasoning Priorities

1. Identify explicit error signals in logs
2. Locate earliest failure point in execution chain
3. Determine what evidence is missing (if any)
4. Only then construct causal explanation
5. Avoid over-specific conclusions when evidence is weak

---

## Output Discipline

Preferred structure:

- Root cause
- Explanation
- Suggested fix

If evidence is insufficient:

- "insufficient information to determine root cause"

---

## Confidence Control

- If evidence is weak → reduce specificity
- If logs are minimal → explicitly state limitations
- Never fill missing context with assumptions
- Prefer under-explaining over hallucination

---

## Role in explaind System

GEMMA.md acts as a persistent behavioral bias layer for debugging tasks.

It influences:
- reasoning style
- caution level
- causal tracing behavior
- hallucination suppression

It does NOT define system architecture or execution logic.

---

## Evolution Principle

This file evolves based on observed model behavior from trace analysis:

- recurring reasoning failures
- hallucination patterns
- causal tracing quality
- structured output consistency

Updates should be evidence-driven, not speculative.