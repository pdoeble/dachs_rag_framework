#!/usr/bin/env bash
#SBATCH --job-name=ingest_pdfs
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/ingest_pdfs_%j.out

# defensives Bash-Setup
set -euo pipefail

# saubere Umgebung
module purge
module load devel/python/3.12.3-gnu-14.2

# Virtualenv mit Projektpaketen
source "$HOME/venv/dachs_rag_312/bin/activate"

# ins Projekt-Repo wechseln
cd "$HOME/dachs_rag_framework"

# Pfade aus config/paths/paths.json auflösen:
#  - workspace_root
#  - paths.normalized_json
#  - paths.semantic_json
readarray -t DACHS_PATHS < <(python - << 'EOF'
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

root = pathlib.Path(cfg["workspace_root"])
norm = root / cfg["paths"]["normalized_json"]
sem = root / cfg["paths"]["semantic_json"]

print(norm)
print(sem)
EOF
)
INPUT_DIR="${DACHS_PATHS[0]}"
OUTPUT_DIR="${DACHS_PATHS[1]}"


# Ingestion starten
python scripts/ingest_pdfs.py \
  --input-dir "$INPUT_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --max-chars 6000 \
  --min-chars 400 \
  --sentence-overlap 2 \
  --verbose
