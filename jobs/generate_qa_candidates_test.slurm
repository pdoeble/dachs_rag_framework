#!/usr/bin/env bash
#SBATCH --job-name=qa_candidates_test
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=/beegfs/scratch/workspace/es_phdoeble-rag_pipeline/logs/qa_candidates_test_%j.out

set -euo pipefail

WORKSPACE="/beegfs/scratch/workspace/es_phdoeble-rag_pipeline"
LOGDIR="${WORKSPACE}/logs"
mkdir -p "${LOGDIR}"

module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

source "$HOME/venv/dachs_rag_312/bin/activate"
cd "$HOME/dachs_rag_framework"

# Optional aber sinnvoll: Syntax/Indentation sofort prüfen
python -m py_compile scripts/generate_qa_candidates.py

# Fester Port reicht (kein Array)
OLLAMA_PORT=11434
export OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}"
export OLLAMA_API_URL="http://127.0.0.1:${OLLAMA_PORT}/api/chat"
export NO_PROXY="127.0.0.1,localhost"
export OLLAMA_KEEP_ALIVE=30m

OLLAMA_LOG="/tmp/ollama_${SLURM_JOB_ID}.log"
ollama serve >"${OLLAMA_LOG}" 2>&1 &
OLLAMA_PID=$!
trap 'kill "${OLLAMA_PID}" >/dev/null 2>&1 || true' EXIT

sleep 1
kill -0 "${OLLAMA_PID}" >/dev/null 2>&1 || {
  echo "ERROR: ollama crashed immediately (pid=${OLLAMA_PID}). Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  exit 1
}

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

MODEL_TAG="qwen2.5:32b-instruct-q4_K_M"
curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" | grep -q "\"${MODEL_TAG}\"" || {
  echo "ERROR: Model '${MODEL_TAG}' not found on this node. Log:" >&2
  tail -n 80 "${OLLAMA_LOG}" >&2 || true
  exit 2
}

curl -fsS -X POST "http://127.0.0.1:${OLLAMA_PORT}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"${MODEL_TAG}"'","messages":[{"role":"user","content":"Warmup. Reply OK."}],"stream":false}' \
  >/dev/null || {
    echo "ERROR: Warmup call failed. Log:" >&2
    tail -n 120 "${OLLAMA_LOG}" >&2 || true
    exit 3
  }

# Mini-Test: nur 1 shard
python scripts/generate_qa_candidates.py \
  --config config/qa/qa_generation.test.json \
  --workspace-root "${WORKSPACE}" \
  --num-shards 1 \
  --shard-id 0
