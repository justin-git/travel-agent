import os
from pathlib import Path

def get_home_dir()-> Path:
    val = os.environ.get("TRAVEL_AGENT_HOME", "").strip()
    return Path(val) if val else Path.home()

def get_skills_dir() -> Path:
    """Return the path to the skills directory under HERMES_HOME."""
    return get_home_dir() / "skills"