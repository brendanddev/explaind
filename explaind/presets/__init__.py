from __future__ import annotations

from pathlib import Path

PRESET_MAP: dict[str, str] = {
    "philosopher": "exploratory",
    "engineer": "causal",
    "critic": "skeptical",
    "synthesiser": "balanced",
    "analyst": "compressive",
    "strategist": "causal",
}

ALLOWED_PRESETS = set(PRESET_MAP.keys())

_PRESET_DESCRIPTIONS: dict[str, str] = {
    "philosopher": "Examines foundations, resists closure",
    "engineer": "Traces mechanisms and root causes",
    "critic": "Applies maximum epistemic pressure",
    "synthesiser": "Integrates competing frameworks",
    "analyst": "Strips elaboration, targets signal",
    "strategist": "Maps leverage points and trajectories",
}

_PRESETS_DIR = Path("presets")


def load_preset(name: str) -> tuple[str, str]:
    """Validate preset name and return (ability_name, preset_description).

    Raises ValueError for unknown preset names.
    """
    if name not in ALLOWED_PRESETS:
        allowed = ", ".join(sorted(ALLOWED_PRESETS))
        raise ValueError(f"unknown preset '{name}' (allowed: {allowed})")
    ability_name = PRESET_MAP[name]
    path = _PRESETS_DIR / f"{name}.md"
    try:
        preset_description = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"preset file missing: {path}")
    return ability_name, preset_description


def preset_description(name: str) -> str:
    """Return the short one-line description for a preset."""
    return _PRESET_DESCRIPTIONS.get(name, "")
