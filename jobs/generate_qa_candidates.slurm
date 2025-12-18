#!/usr/bin/env bash
#SBATCH --job-name=qa_candidates
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=23:59:00
#SBATCH --array=0-19%5
#SBATCH --output=/beegfs/scratch/workspace/es_phdoeble-rag_pipeline/logs/qa_candidates_%A_%a.out

set -euo pipefail

mkdir -p /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/logs

module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

# Pro Task eigener Port (verhindert Kollisionen auf Multi-GPU-Nodes)
OLLAMA_PORT=$((11434 + SLURM_ARRAY_TASK_ID))
export OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}"
export OLLAMA_API_URL="http://127.0.0.1:${OLLAMA_PORT}/api/chat"

ollama serve >"/tmp/ollama_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log" 2>&1 &
OLLAMA_PID=$!

# Cleanup garantiert
cleanup() {
  kill "${OLLAMA_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Warten bis Server ready (max ~30s)
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

python scripts/generate_qa_candidates.py \
  --workspace-root /beegfs/scratch/workspace/es_phdoeble-rag_pipeline \
  --num-shards 20 \
  --shard-id "${SLURM_ARRAY_TASK_ID}"
