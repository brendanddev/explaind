from __future__ import annotations

import copy
import json
import re
import uuid
from dataclasses import dataclass, field


@dataclass
class ScaffoldState:
    session_id: str
    current_stage: str
    stage_history: list[str]
    raw_input: str
    claims: list[str]
    causal_graph: dict
    compressive_summary: str
    uncertainty_register: list[str]
    falsification_conditions: list[str]
    confidence_scores: dict[str, float]
    drift_detected: bool
    tokens_used: int
    total_passes: int


_SCAFFOLD_UPDATE_RE = re.compile(
    r'\[SCAFFOLD_UPDATE\]\s*(.*?)\s*\[/SCAFFOLD_UPDATE\]',
    re.DOTALL,
)

_UPDATE_EXAMPLE = (
    '{\n'
    '  "claims": ["claim1", "claim2"],\n'
    '  "causal_graph": {"nodes": [], "edges": [], "confidence": {}},\n'
    '  "compressive_summary": "...",\n'
    '  "uncertainty_register": ["uncertainty1"],\n'
    '  "falsification_conditions": ["condition1"],\n'
    '  "confidence_scores": {"claim1": 75.0}\n'
    '}'
)


def build_initial_scaffold(
    raw_input: str,
    abilities: list[str],
    session_id: str | None = None,
) -> ScaffoldState:
    if session_id is None:
        session_id = uuid.uuid4().hex[:8]
    return ScaffoldState(
        session_id=session_id,
        current_stage=abilities[0],
        stage_history=[],
        raw_input=raw_input,
        claims=[],
        causal_graph={"nodes": [], "edges": [], "confidence": {}},
        compressive_summary="",
        uncertainty_register=[],
        falsification_conditions=[],
        confidence_scores={},
        drift_detected=False,
        tokens_used=0,
        total_passes=len(abilities),
    )


def scaffold_to_injection(state: ScaffoldState) -> str:
    pass_num = len(state.stage_history) + 1
    total = state.total_passes

    claims_str = (
        "\n".join(f"- {c}" for c in state.claims)
        if state.claims else "none yet"
    )

    nodes = state.causal_graph.get("nodes", [])
    edges = state.causal_graph.get("edges", [])
    if nodes or edges:
        causal_str = f"nodes: [{', '.join(str(n) for n in nodes)}] edges: [{', '.join(str(e) for e in edges)}]"
    else:
        causal_str = "none yet"

    summary_str = state.compressive_summary if state.compressive_summary else "none yet"

    uncertainties_str = (
        "\n".join(f"- {u}" for u in state.uncertainty_register)
        if state.uncertainty_register else "none"
    )
    falsifications_str = (
        "\n".join(f"- {f}" for f in state.falsification_conditions)
        if state.falsification_conditions else "none"
    )
    confidence_str = (
        "\n".join(f"- {k}: {v}" for k, v in state.confidence_scores.items())
        if state.confidence_scores else "none"
    )

    return (
        f"[COGNITIVE SCAFFOLD — ACTIVE]\n"
        f"Session: {state.session_id}\n"
        f"Stage: {state.current_stage} (pass {pass_num} of {total})\n"
        f"Input: {state.raw_input}\n"
        "\n"
        "ESTABLISHED:\n"
        f"Claims: {claims_str}\n"
        f"Causal graph: {causal_str}\n"
        f"Summary: {summary_str}\n"
        "\n"
        "EPISTEMIC STATE:\n"
        f"Uncertainties: {uncertainties_str}\n"
        f"Falsification conditions: {falsifications_str}\n"
        f"Confidence scores: {confidence_str}\n"
        "\n"
        "[END COGNITIVE SCAFFOLD]\n"
        "\n"
        "INSTRUCTION:\n"
        "You are operating inside a persistent cognitive scaffold.\n"
        "At the end of your response, output your updates as a \n"
        "single JSON block in this exact format:\n"
        "\n"
        "[SCAFFOLD_UPDATE]\n"
        + _UPDATE_EXAMPLE + "\n"
        "[/SCAFFOLD_UPDATE]\n"
        "\n"
        "Fill all fields. Use null for fields you did not update in this pass."
    )


def parse_scaffold_update(
    output: str,
    state: ScaffoldState,
) -> tuple[ScaffoldState, str]:
    match = _SCAFFOLD_UPDATE_RE.search(output)
    if not match:
        new_state = copy.deepcopy(state)
        new_state.drift_detected = True
        return new_state, output

    json_text = match.group(1).strip()
    try:
        data = json.loads(json_text)
    except (json.JSONDecodeError, ValueError):
        new_state = copy.deepcopy(state)
        new_state.drift_detected = True
        return new_state, output

    new_state = copy.deepcopy(state)

    if "claims" in data and isinstance(data["claims"], list):
        for claim in data["claims"]:
            if claim not in new_state.claims:
                new_state.claims.append(claim)

    if "causal_graph" in data and isinstance(data["causal_graph"], dict):
        cg = data["causal_graph"]
        if "nodes" in cg and isinstance(cg["nodes"], list):
            for node in cg["nodes"]:
                if node not in new_state.causal_graph["nodes"]:
                    new_state.causal_graph["nodes"].append(node)
        if "edges" in cg and isinstance(cg["edges"], list):
            for edge in cg["edges"]:
                if edge not in new_state.causal_graph["edges"]:
                    new_state.causal_graph["edges"].append(edge)
        if "confidence" in cg and isinstance(cg["confidence"], dict):
            new_state.causal_graph["confidence"].update(cg["confidence"])

    if "compressive_summary" in data and data["compressive_summary"]:
        new_state.compressive_summary = data["compressive_summary"]

    if "uncertainty_register" in data and isinstance(data["uncertainty_register"], list):
        for item in data["uncertainty_register"]:
            if item not in new_state.uncertainty_register:
                new_state.uncertainty_register.append(item)

    if "falsification_conditions" in data and isinstance(data["falsification_conditions"], list):
        for item in data["falsification_conditions"]:
            if item not in new_state.falsification_conditions:
                new_state.falsification_conditions.append(item)

    if "confidence_scores" in data and isinstance(data["confidence_scores"], dict):
        new_state.confidence_scores.update(data["confidence_scores"])

    clean_output = _SCAFFOLD_UPDATE_RE.sub("", output).strip()
    return new_state, clean_output


def scaffold_to_export_summary(state: ScaffoldState) -> str:
    claims_str = (
        "\n".join(f"- {c}" for c in state.claims)
        if state.claims else "*(none)*"
    )

    if state.confidence_scores:
        rows = "\n".join(f"| {k} | {v} |" for k, v in state.confidence_scores.items())
        confidence_table = "| Claim | Confidence |\n| --- | --- |\n" + rows
    else:
        confidence_table = "*(none)*"

    uncertainties_str = (
        "\n".join(f"- {u}" for u in state.uncertainty_register)
        if state.uncertainty_register else "*(none)*"
    )
    falsifications_str = (
        "\n".join(f"- {f}" for f in state.falsification_conditions)
        if state.falsification_conditions else "*(none)*"
    )
    summary_str = state.compressive_summary if state.compressive_summary else "*(none)*"
    drift_str = "yes" if state.drift_detected else "no"

    return (
        "## Cognitive Scaffold Summary\n"
        "\n"
        f"**Session**: {state.session_id}  \n"
        f"**Passes completed**: {len(state.stage_history)}  \n"
        f"**Drift detected**: {drift_str}\n"
        "\n"
        "### Established Claims\n"
        f"{claims_str}\n"
        "\n"
        "### Confidence Scores\n"
        f"{confidence_table}\n"
        "\n"
        "### Uncertainty Register\n"
        f"{uncertainties_str}\n"
        "\n"
        "### Falsification Conditions\n"
        f"{falsifications_str}\n"
        "\n"
        "### Final Summary\n"
        f"{summary_str}"
    )
