#!/usr/bin/env bash
#SBATCH --job-name=ingest_pdfs
#SBATCH --partition=gpu1          # <- echte Partition, kein Platzhalter mehr
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/ingest_pdfs_%j.out

# saubere Umgebung
module purge
module load devel/python/3.12.3-gnu-14.2

# Virtualenv mit Projektpaketen
source "$HOME/venv/dachs_rag_312/bin/activate"

# ins Projekt-Repo wechseln
cd "$HOME/dachs_rag_framework"

# Ingestion starten
python scripts/ingest_pdfs.py \
  --input-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/raw \
  --output-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/normalized/json \
  --max-chars 6000 \
  --min-chars 400 \
  --sentence-overlap 2 \
  --verbose
