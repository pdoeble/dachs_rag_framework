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

# saubere Umgebung
module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

mkdir -p logs

# Ollama-Server direkt im Job starten
export OLLAMA_HOST="0.0.0.0:11434"
ollama serve > /tmp/ollama_${SLURM_JOB_ID}.log 2>&1 &

# kurz warten, bis der Server lauscht
sleep 5

# Annotation (hier 1 Datei – Incropera –, später limit_files weg)
python scripts/annotate_semantics.py \
  --input-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/normalized/json \
  --output-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/semantic/json \
  --config config/LLM/semantic_llm.json \
  --limit-files 1 \
  --verbose
