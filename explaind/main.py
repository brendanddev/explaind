import sys
import ollama
from explaind.prompts import SYSTEM_PROMPT

MODEL = "gemma4-e2b_q4_k_m:latest"

def load_input(path: str | None):
    if path:
        with open(path, "r") as f:
            return f.read()
    return sys.stdin.read()

def build_prompt(log_text: str) -> str:
    return f"""
Analyze this failure:

=== LOG ===
{log_text}

TASK:
1. Identify root cause
2. Explain causal chain
3. Suggest fix
"""

def run_model(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    return response["message"]["content"]


def run(file: str | None):
    log_text = load_input(file)
    prompt = build_prompt(log_text)
    return run_model(prompt)