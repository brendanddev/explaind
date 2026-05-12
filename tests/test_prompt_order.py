from explaind.prompts import build_prompt, SYSTEM_PROMPT
from explaind.main import run


def test_gemma_before_ability():
    prompt = build_prompt(
        "input",
        gemma_md="GEMMA_MARKER",
        ability_name="balanced",
        ability_content="ABILITY_MARKER",
    )
    assert prompt.index("GEMMA_MARKER") < prompt.index("ABILITY_MARKER")


def test_ability_before_bias_field():
    prompt = build_prompt(
        "input",
        gemma_md="GEMMA_MARKER",
        ability_name="balanced",
        ability_content="ABILITY_MARKER",
    )
    assert prompt.index("ABILITY_MARKER") < prompt.index("BIAS FIELD")


def test_bias_field_before_input():
    prompt = build_prompt("input")
    assert prompt.index("BIAS FIELD") < prompt.index("<input>")


def test_dry_run_system_prompt_is_first():
    result, _ = run("test input", dry_run=True)
    system_pos = result.index("=== SYSTEM PROMPT ===")
    bias_pos = result.index("BIAS FIELD")
    input_pos = result.index("<input>")
    assert system_pos < bias_pos
    assert system_pos < input_pos


def test_no_triple_newline_separators():
    prompt = build_prompt(
        "input",
        gemma_md="G",
        ability_name="balanced",
        ability_content="A",
    )
    assert "\n\n\n" not in prompt
