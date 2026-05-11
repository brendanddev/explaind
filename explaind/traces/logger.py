import json
import dataclasses
from pathlib import Path

from explaind.traces.models import TraceSession

SESSIONS_DIR = Path("traces/sessions")


def save_session(session: TraceSession) -> Path:
    """Serialize a TraceSession to JSON and persist it under traces/sessions/.

    The filename encodes the session timestamp so files sort chronologically.
    Returns the path written.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    safe_ts = session.timestamp.replace(":", "-").replace(".", "-")
    path = SESSIONS_DIR / f"session_{safe_ts}.json"

    with open(path, "w") as f:
        json.dump(dataclasses.asdict(session), f, indent=2)

    return path
