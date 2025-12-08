#!/usr/bin/env bash
#SBATCH --job-name=annotate_incropera
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/annotate_incropera_%j.out

# defensives Bash-Setup
set -euo pipefail

# saubere Umgebung
module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

# Python-Umgebung aktivieren
source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

# Log-Verzeichnis im Repo sicherstellen
mkdir -p logs

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

# Ollama-Server direkt im Job starten
export OLLAMA_HOST="0.0.0.0:11434"
ollama serve > "/tmp/ollama_${SLURM_JOB_ID}.log" 2>&1 &

# kurz warten, bis der Server lauscht
sleep 5

# Annotation (hier 1 Datei – Incropera –, später --limit-files entfernen/variabel setzen)
python scripts/annotate_semantics.py \
  --input-dir "$INPUT_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --config config/LLM/semantic_llm.json \
  --limit-files 10000 \
  --verbose
