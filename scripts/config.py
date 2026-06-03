import json
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    return json.loads((_REPO_ROOT / "config.json").read_text())
