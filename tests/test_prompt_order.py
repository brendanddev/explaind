from explaind.context import build_context_window_block
from explaind.prompts import assemble_prompt, build_bias_field, format_ability, SYSTEM_PROMPT
from explaind.main import run


def _prompt(user_input="input", gemma_md=None, ability_name=None, ability_content=None):
    ability = format_ability(ability_name, ability_content) if ability_content else None
    bias_field = build_bias_field(ability_name or "balanced")
    return assemble_prompt(
        system=SYSTEM_PROMPT,
        gemma_md=gemma_md,
        ability=ability,
        context_window=build_context_window_block(),
        bias_field=bias_field,
        user_input=user_input,
    )


def test_system_before_gemma():
    prompt = _prompt(gemma_md="GEMMA_MARKER")
    assert prompt.index("=== SYSTEM PROMPT ===") < prompt.index("GEMMA_MARKER")


def test_gemma_before_ability():
    prompt = _prompt(gemma_md="GEMMA_MARKER", ability_name="balanced", ability_content="ABILITY_MARKER")
    assert prompt.index("GEMMA_MARKER") < prompt.index("ABILITY_MARKER")


def test_ability_before_bias_field():
    prompt = _prompt(gemma_md="GEMMA_MARKER", ability_name="balanced", ability_content="ABILITY_MARKER")
    assert prompt.index("ABILITY_MARKER") < prompt.index("BIAS FIELD")


def test_context_window_before_bias_field():
    prompt = _prompt(gemma_md="GEMMA_MARKER")
    assert prompt.index("[CONTEXT WINDOW LAYERS]") < prompt.index("BIAS FIELD")


def test_context_window_after_ability():
    prompt = _prompt(gemma_md="GEMMA_MARKER", ability_name="balanced", ability_content="ABILITY_MARKER")
    assert prompt.index("ABILITY_MARKER") < prompt.index("[CONTEXT WINDOW LAYERS]")


def test_bias_field_before_input():
    prompt = _prompt()
    assert prompt.index("BIAS FIELD") < prompt.index("<user_input>")


def test_dry_run_system_prompt_is_first():
    result, _ = run("test input", dry_run=True)
    system_pos = result.index("=== SYSTEM PROMPT ===")
    bias_pos = result.index("BIAS FIELD")
    input_pos = result.index("<user_input>")
    assert system_pos < bias_pos
    assert system_pos < input_pos


def test_no_triple_newline_separators():
    prompt = _prompt(gemma_md="G", ability_name="balanced", ability_content="A")
    assert "\n\n\n" not in prompt


def test_layer_separator_is_double_newline():
    from explaind.prompts import LAYER_SEPARATOR
    assert LAYER_SEPARATOR == "\n\n"


def test_assemble_prompt_is_byte_stable():
    bias = build_bias_field("causal")
    ability = format_ability("causal", "CAUSAL CONTENT")
    ctx = build_context_window_block()
    kwargs = dict(system="S", gemma_md="G", ability=ability, context_window=ctx, bias_field=bias, user_input="U")
    assert assemble_prompt(**kwargs) == assemble_prompt(**kwargs)
