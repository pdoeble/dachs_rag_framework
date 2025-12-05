#!/usr/bin/env bash
#SBATCH --job-name=embed_chunks
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/embed_chunks_%j.out

# defensives Bash-Setup
set -euo pipefail

# saubere Umgebung
module purge
module load devel/python/3.12.3-gnu-14.2

# Python-Umgebung aktivieren
source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

# Log-Verzeichnis im Repo sicherstellen
mkdir -p logs

# workspace_root aus config/paths/paths.json auflösen
WORKSPACE_ROOT=$(python - << 'EOF'
import json
import pathlib
import os

cfg_path = (
    pathlib.Path(os.environ["HOME"])
    / "dachs_rag_framework"
    / "config"
    / "paths"
    / "paths.json"
)

with cfg_path.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

print(cfg["workspace_root"])
EOF
)

# Zielverzeichnisse im Workspace sicherstellen
mkdir -p "$WORKSPACE_ROOT/indices/faiss" \
         "$WORKSPACE_ROOT/indices/chroma" \
         "$WORKSPACE_ROOT/logs/indices"

# Embeddings für alle Chunks erzeugen
python scripts/embed_chunks.py \
  --workspace-root "$WORKSPACE_ROOT" \
  --verbose
