from pathlib import Path
import json

CONFIG_PATHS = Path(__file__).resolve().parent / "paths.json"

def load_paths() -> dict:
    with open(CONFIG_PATHS, "r", encoding="utf-8") as f:
        return json.load(f)

def get_path(key: str) -> Path:
    cfg = load_paths()
    root = Path(cfg["workspace_root"])
    rel = cfg["paths"].get(key)
    if rel is None:
        raise KeyError(f"Pfad '{key}' ist nicht in paths.json definiert.")
    return (root / rel).resolve()
