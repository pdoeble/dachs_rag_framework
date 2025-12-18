#!/usr/bin/env bash
#SBATCH --job-name=qa_candidates
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=23:59:00
#SBATCH --array=0-4%5
#SBATCH --output=/beegfs/scratch/workspace/es_phdoeble-rag_pipeline/logs/qa_candidates_%A_%a.out

set -euo pipefail

WORKSPACE="/beegfs/scratch/workspace/es_phdoeble-rag_pipeline"
LOGDIR="${WORKSPACE}/logs"
mkdir -p "${LOGDIR}"

module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

# Pro Task eigener Port (verhindert Kollisionen auf Multi-GPU-Nodes)
OLLAMA_PORT=$((11434 + SLURM_ARRAY_TASK_ID))
export OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}"
export OLLAMA_API_URL="http://127.0.0.1:${OLLAMA_PORT}/api/chat"
export NO_PROXY="127.0.0.1,localhost"

# Ollama server starten
OLLAMA_LOG="/tmp/ollama_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"
ollama serve >"${OLLAMA_LOG}" 2>&1 &
OLLAMA_PID=$!
trap 'kill "${OLLAMA_PID}" >/dev/null 2>&1 || true' EXIT

# Fail-fast: Prozess muss leben
sleep 1
kill -0 "${OLLAMA_PID}" >/dev/null 2>&1 || {
  echo "ERROR: ollama crashed immediately (pid=${OLLAMA_PID}). Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  exit 1
}

# Warten bis Server ready (max ~60s)
READY=0
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "${READY}" -ne 1 ]]; then
  echo "ERROR: Ollama not ready on port ${OLLAMA_PORT}. Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  exit 1
fi

# Fail-fast: sicherstellen, dass *unser* PID am Port hängt (keine Port-Kollision)
ss -ltnp 2>/dev/null | grep -q "${OLLAMA_PORT}.*pid=${OLLAMA_PID}" || {
  echo "ERROR: Ollama PID ${OLLAMA_PID} is not bound to port ${OLLAMA_PORT} (port collision?). Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  ss -ltnp 2>/dev/null | grep "${OLLAMA_PORT}" || true
  exit 1
}

# Optional: Modell-Tag prüfen (empfohlen, sonst droht 404=model not found)
MODEL_TAG="qwen2.5:32b-instruct-q4_K_M"
curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" | grep -q "\"${MODEL_TAG}\"" || {
  echo "ERROR: Model '${MODEL_TAG}' not found on this node (check /api/tags). Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  exit 2
}

python scripts/generate_qa_candidates.py \
  --workspace-root "${WORKSPACE}" \
  --num-shards 5 \
  --shard-id "${SLURM_ARRAY_TASK_ID}"
