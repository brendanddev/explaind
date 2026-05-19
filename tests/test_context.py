from explaind.context import build_context_window_block


def test_header_always_present():
    assert "[CONTEXT WINDOW LAYERS]" in build_context_window_block()


def test_context_instruction_always_present():
    result = build_context_window_block()
    assert "[CONTEXT INSTRUCTION]" in result
    assert "persistent working memory" in result
    assert "ABILITY + BIAS FIELD priority" in result


def test_all_none_renders_none_placeholders():
    result = build_context_window_block()
    assert "[SCRATCHPAD]\nnone" in result
    assert "[REASONING TRACE]\nnone" in result
    assert "[COMPETING INTERPRETATIONS]\nnone" in result


def test_trace_content_included():
    result = build_context_window_block(trace="step A → step B")
    assert "step A → step B" in result
    assert "[REASONING TRACE]\nstep A → step B" in result


def test_scratchpad_content_included():
    result = build_context_window_block(scratchpad="working value: 42")
    assert "working value: 42" in result
    assert "[SCRATCHPAD]\nworking value: 42" in result


def test_interpretations_content_included():
    result = build_context_window_block(interpretations="A: x, B: y")
    assert "A: x, B: y" in result
    assert "[COMPETING INTERPRETATIONS]\nA: x, B: y" in result


def test_whitespace_stripped_from_content():
    result = build_context_window_block(trace="  trimmed  ")
    assert "[REASONING TRACE]\ntrimmed" in result


def test_no_leading_newline():
    result = build_context_window_block()
    assert not result.startswith("\n")


def test_no_trailing_newline():
    result = build_context_window_block()
    assert not result.endswith("\n")


def test_no_triple_newlines():
    result = build_context_window_block(
        trace="T",
        scratchpad="S",
        interpretations="I",
    )
    assert "\n\n\n" not in result


def test_pure_function_same_inputs_same_output():
    a = build_context_window_block(trace="X", scratchpad="Y")
    b = build_context_window_block(trace="X", scratchpad="Y")
    assert a == b
