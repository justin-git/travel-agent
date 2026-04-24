from constants import get_skills_dir
from pathlib import Path
from typing import Dict, List

def get_all_skills_dirs() -> List[Path]:
    """Return all skill directories: local ``~/.hermes/skills/`` first, then external.

    The local dir is always first (and always included even if it doesn't exist
    yet — callers handle that).  External dirs follow in config order.
    """
    dirs = [get_skills_dir()]
    return dirs