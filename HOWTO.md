# DACHS RAG-Pipeline: Ingest & Annotation

Dieses Howto beschreibt den Ablauf von:
1. PDF-Ingestion (CPU, kein GPU nötig)
2. Semantische Annotation mit Ollama (GPU-Node)

---

## 1. Ingest (PDF → normalized JSON)

### 1.1 Umgebung aktivieren (Login- oder CPU-Knoten)

```bash
# saubere Modul-Umgebung
module purge

# feste Python-Basis (Cluster-Modul)
module load devel/python/3.12.3-gnu-14.2

# eigenes Virtualenv mit allen Python-Paketen des Projekts
source "$HOME/venv/dachs_rag_312/bin/activate"

# ins Projekt-Repo wechseln
cd ~/dachs_rag_framework
```
### 1.2 PDFs einlesen und nach JSON normalisieren
```bash
python scripts/ingest_pdfs.py \
  --input-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/raw \
  --output-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/normalized/json \
  --verbose
```

* raw/ : enthält die PDF-Dateien (Eingabe).
* normalized/json/ : enthält danach pro PDF eine .jsonl-Datei mit Chunks.

## 2. Annotation (normalized JSON → semantic JSON mit LLM/Ollama)
### 2.1 Interaktive GPU-Session holen (vom Login-Knoten)
#### auf einem Login-Node ausführen
```bash
srun --partition=gpu1 --gres=gpu:1 --cpus-per-task=8 --mem=64G --time=06:00:00 --pty /bin/bash
```

* Startet eine interaktive Shell auf einem GPU-Knoten (z.B. gpu110).
* Alle folgenden Schritte in dieser GPU-Shell ausführen.

### 2.2 Module + Virtualenv + Projekt laden (auf dem GPU-Node)
#### saubere Umgebung
```bash
module purge

#### Python + Ollama-Modul laden
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2

#### Virtualenv mit Projektabhängigkeiten aktivieren
source "$HOME/venv/dachs_rag_312/bin/activate"

#### ins Projekt-Repo wechseln
cd ~/dachs_rag_framework
```

### 2.3 Ollama-Server starten und Modell bereitstellen

Hinweis:
* Server muss bei jeder neuen GPU-Session gestartet werden.
* Modell-Pull ist pro Node & User in der Regel nur einmal nötig.
```bash
# (optional) Server auf allen Interfaces lauschen lassen,
# z.B. wenn man später per SSH-Tunnel von außen zugreifen will.
# Für die lokale Nutzung durch annotate_semantics.py NICHT zwingend nötig.
export OLLAMA_HOST=0.0.0.0:11434

# Ollama-Server im Hintergrund starten (läuft auf Port 11434)
ollama serve > /tmp/ollama_${HOSTNAME}_semantic.log 2>&1 &

# kurz warten, bis der Server oben ist
sleep 3

# prüfen, ob der Server antwortet
ollama list
```
Falls ollama list ohne Fehler läuft, ist der Server aktiv.

#### (Einmalig pro Node/User) Modell ziehen
```bash
# Beispiel: Llama 3.1 8B (Name muss zu semantic_llm.json passen)
ollama pull llama3.1:8b
```

* Lädt das Modell auf den GPU-Node.
* Kann je nach Modellgröße einige Minuten dauern.
* Bei späteren Sessions reicht ollama list, Pull nur bei fehlendem Modell.


### 2.4 Semantische Annotation starten
```bash
module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2
source "$HOME/venv/dachs_rag_312/bin/activate"
cd ~/dachs_rag_framework

python scripts/annotate_semantics.py \
  --input-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/normalized/json \
  --output-dir /beegfs/scratch/workspace/es_phdoeble-rag_pipeline/semantic/json \
  --config config/LLM/semantic_llm.json \
  --limit-files 1 \
  --verbose
```


--limit-files 1:
* Erst Testlauf auf einer Datei (z.B. ein Buch).
* Wenn alles passt, Option entfernen oder erhöhen, um alle Dateien zu annotieren.


semantic/json/:
* enthält danach .jsonl-Dateien mit gefülltem semantic-Block
* (content_type, domain, artifact_role, trust_level, language).

