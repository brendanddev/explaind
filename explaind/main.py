import ollama
from explaind.prompts import SYSTEM_PROMPT

MODEL = "gemma4-e2b_q4_k_m:latest"


def build_prompt(log_text: str) -> str:
    return f"""
Analyze this software failure:

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


def run(input_text: str) -> str:
    prompt = build_prompt(input_text)
    return run_model(prompt)