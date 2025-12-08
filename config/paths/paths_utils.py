from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# REPO_ROOT = dachs_rag_framework/
REPO_ROOT = Path(__file__).resolve().parents[2]
PATHS_CONFIG_PATH = REPO_ROOT / "config" / "paths" / "paths.json"


def _load_paths_config() -> Dict[str, Any]:
    """
    Lädt config/paths/paths.json.

    Erwartete Struktur:
    {
      "workspace_root": "/beegfs/scratch/workspace/es_phdoeble-rag_pipeline",
      "paths": {
        "normalized_json": "normalized/json",
        "semantic_json":   "semantic/json",
        ...
      }
    }
    Fällt auf REPO_ROOT zurück, falls Datei fehlt oder Felder fehlen.
    """
    if not PATHS_CONFIG_PATH.is_file():
        # Fallback: minimale Defaults
        return {
            "workspace_root": str(REPO_ROOT),
            "paths": {
                "normalized_json": "normalized/json",
                "semantic_json": "semantic/json",
            },
        }

    with PATHS_CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "workspace_root" not in data:
        data["workspace_root"] = str(REPO_ROOT)
    if "paths" not in data:
        data["paths"] = {}

    return data


def get_path(key: str, default_relative: str | None = None) -> Path:
    """
    Liefert einen absoluten Pfad für einen Logik-Namen aus paths.json.

    - key: z.B. "normalized_json", "semantic_json"
    - default_relative: wird benutzt, wenn der key in paths.json fehlt.
      Interpretiert relativ zu workspace_root.

    Rückgabe: pathlib.Path (absolut)
    """
    cfg = _load_paths_config()
    workspace_root = Path(cfg.get("workspace_root", REPO_ROOT))
    subpaths = cfg.get("paths", {})

    rel = subpaths.get(key)
    if rel is None:
        if default_relative is None:
            raise KeyError(f"Pfad-Key '{key}' nicht in {PATHS_CONFIG_PATH} definiert und kein default_relative angegeben.")
        rel = default_relative

    return (workspace_root / rel).resolve()
