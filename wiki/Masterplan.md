# Projektplan / Lastenheft  

**Domänenspezifisches KI-System mit „Verstehendem RAG“ und Instruction-Tuning auf DACHS**

---

## 1. Ziel und Gesamtbild

### 1.1 Ziel des Projekts

Ziel des Projekts ist der Aufbau eines internen, domänenspezifischen KI-Systems für Engineering-Aufgaben, das:

- auf dem DACHS-Cluster betrieben wird,
- ausschließlich interne Daten verarbeitet (kein Datenabfluss an externe Dienste),
- technische Inhalte (Deutsch und Englisch) aus Büchern, Papern, Exceltabellen, PowerPoints, Code, GT-Power-Modellen und Erfahrungsdokumenten versteht,
- typische Arbeitsweisen im Engineering abbildet und unterstützt,
- einen universellen Frage–Antwort-Trainingsdatensatz erzeugt, der auch zukünftige Modelle (noch nicht verfügbar) trainieren kann.

Das System soll über reines Dokumenten-Retrieval hinausgehen: Die Modelle sollen nicht nur nachschlagen, sondern domänenspezifische Zusammenhänge und Arbeitsprozesse „verstanden“ haben (Verstehendes RAG + Instruction-Tuning).

### 1.2 Anwendungsfälle (Core-Tasks)

Die folgenden Aufgaben müssen mit hoher Qualität unterstützt werden:

1. **Auslegung von Kühlsystemen**  
   - Unterstützung bei thermischen Auslegungen (Kühlsysteme von Komponenten und Gesamtsystemen).
   - Nutzung von Erfahrungswissen, Versuchsdaten, Simulationsergebnissen und Normen.

2. **Erstellen von Skripten in Python und KNIME**  
   - Vorschläge für Skriptstrukturen, Code-Snippets, KNIME-Workflows.
   - Einbettung in bestehende Toolchains und Datenquellen.

3. **Verstehen von und Kommunikation mit Konzern-Infrastruktur**  
   - Unterstützung bei Anbindung an Datenbanken und interne Systeme.
   - Hilfestellung bei Nutzung interner Schnittstellen (APIs, DB-Schemata, ETL-Pfade).

4. **Hilfestellung bei GT-Power**  
   - Unterstützung bei Modellaufbau, Parametrierung, Auswertung von Ergebnissen.
   - Einbettung in Entwicklungsprozesse (Kalibrierung, Variantenmanagement).

5. **Verstehen von Entwicklungsabläufen und Korrelation von Daten**  
   - Erklären und Strukturieren typischer Entwicklungsprozesse (z. B. vom Konzept über Simulation bis zum Fahrversuch).
   - Unterstützung bei der Korrelation von Messergebnissen, Simulationsergebnissen und Zielwerten.

Für alle anderen Aufgaben ist „gute“ Qualität ausreichend. Die oben genannten Kernaufgaben sollen hingegen möglichst robust und verlässlich abgedeckt werden.

### 1.3 Abgrenzung

Das System:

- **tut**:
  - interne Dokumente strukturieren, semantisch anreichern und für Training und RAG aufbereiten,
  - domänenspezifische Frage–Antwort-Paare (Instruction-Daten) erzeugen,
  - große offene Modelle auf DACHS feinabstimmen (Instruction-Tuning) und für Inferenz bereitstellen,
  - Vektorindices (FAISS/Chroma) für KNIME-basierte RAG-Workflows bereitstellen.

- **tut nicht**:
  - externe Cloud-Modelle (OpenAI, Azure o. ä.) ansprechen,
  - als generischer Chatbot ohne Domänenfokus fungieren,
  - produktive Systemlandschaften (z. B. Konzern-Datenbanken) technisch verändern oder administrieren,
  - komplette Pretrains von Grund auf durchführen (kein Training von „Scratch-Modellen“).

### 1.4 Qualitätsziel: „Verstehendes RAG“ + Instruction-Tuning

Der Zielzustand ist eine Kombination aus:

- **Verstehendem RAG**:
  - Die Dokumentbasis wird nicht nur in Chunks geschnitten, sondern inhaltlich typisiert, mit Metadaten versehen und in Relation gesetzt (z. B. Messdaten ↔ Normen ↔ Richtlinien ↔ Simulationen).
  - RAG-Antworten nutzen diese strukturierten Informationen und sind dadurch erklärbarer und besser steuerbar.

- **Instruction-Tuning**:
  - Aus den strukturierten Daten werden Frage–Antwort-Beispiele generiert.
  - Ein oder mehrere große Modelle (z. B. 30–70B Parameter, je nach Ressourcen) werden auf DACHS feinabgestimmt, um Arbeitsweise und Kommunikationsstil abzubilden.
  - Der zentrale Trainingsdatensatz (Frage–Antwort + Metadaten) ist modellunabhängig und kann für zukünftige Modellgenerationen wiederverwendet werden.

---

## 2. Rahmenbedingungen und Infrastruktur

### 2.1 DACHS-Cluster / bwHPC-Umgebung (Kurzüberblick)

- Nutzung ausschließlich über SSH und Jupyter (JupyterHub auf DACHS).
- Login-Knoten nur für leichte Aufgaben (Editieren, Job-Submission, Monitoring).
- Berechnung erfolgt auf Compute-Knoten, die per SLURM-Job (Batch oder interaktiv) zugewiesen werden.
- Workspaces (Scratch-Bereiche) für große Datenmengen auf parallelen Dateisystemen (z. B. BeeGFS).
- Interaktive Langläufer und KI-Workloads auf den entsprechenden GPU-Partitionen.

Details zur Benutzung (Login, OTP, SSH, Workspaces, SLURM) werden im Projektplan nur dort referenziert, wo sie für konkrete Arbeitsschritte relevant sind.

### 2.2 Ressourcenklassen

- **CPU-Knoten**:
  - Für ETL, Parsing, Dokument-Normalisierung, kleinere LLM-Inferenz-Jobs.
- **GPU-Knoten** (Partitionen z. B. `gpu1`, `gpu4`, `gpu8` auf DACHS):
  - Für LLM-Inferenz in Batch-Jobs (Semantik-Anreicherung, Q/A-Erzeugung).
  - Für Fine-Tuning (Instruction-Tuning) großer Modelle.
- **Speicher**:
  - Workspaces für große Datenmengen (Rohdaten, Normalformen, Embeddings).
  - Lokaler Scratch (`/localscratch`) für temporäre Daten während Trainingsjobs.

### 2.3 Betriebsmodus: reine On-Premise-Lösung

- Sämtliche Datenverarbeitung findet auf DACHS (und ggf. internen Workstations) statt.
- Es werden keine externen KI-APIs verwendet.
- Ausgehende Verbindungen ins Internet zu LLM-Endpoints sind im Rahmen dieser Lösung nicht vorgesehen.
- Modelle werden ausschließlich aus internen oder rechtlich unkritischen Quellen bezogen (z. B. öffentlich verfügbare Open-Source-Modelle, die lokal installiert werden).

### 2.4 Rollen und Zielgruppen

- **Engineering-Anwender**:
  - Nutzen später RAG/LLM-Funktionen (z. B. über KNIME, Jupyter, interne Tools).
  - Liefern ggf. Feedback zu Antworten und gewünschten Workflows.

- **Data Engineers / ML Engineers**:
  - Implementieren die Pipeline (Ingestion, Normalisierung, Anreicherung, Q/A-Erzeugung).
  - Pflegen Workspaces, Skripte, Trainingsdatensätze und Vektorindices.

- **HPC-/System-Administratoren**:
  - Stellen DACHS-Ressourcen bereit (Partitionen, Module, Workspaces).
  - Unterstützen beim Betrieb von LLM-Inferenz- und Trainingsjobs (z. B. SLURM-Konfiguration, Module wie `cs/ollama`).

---

## 3. Zielarchitektur „Verstehendes RAG + Instruction-Tuning“

### 3.1 Komponentenübersicht

Die Lösung besteht aus folgenden Hauptkomponenten:

1. **Datenquellen**  
   - Bücher (PDF, ggf. gescannte Dokumente mit OCR).
   - Wissenschaftliche Paper.
   - Normen und Richtlinien.
   - PowerPoints (Management- und Expertenpräsentationen).
   - Excel-Tabellen (Messdaten, Kennfelder, Parameterlisten).
   - Erfahrungsberichte, Testprotokolle, Memos.
   - GT-Power-Modelle und zugehörige Dokumentation.
   - Code (Python, KNIME-Workflows, Skripte) und Software-Handbücher.

2. **Ingestion- und Normalisierungsschicht**  
   - Parser für unterschiedliche Dateitypen.
   - Konvertierung in eine einheitliche, normalisierte JSON-Struktur („normalized documents“).

3. **Semantische Anreicherungs- und Typisierungsschicht**  
   - LLM-gestützte Klassifikation (`content_type`, `domain`, `artifact_role`, `trust_level`).
   - Erkennung von Zusammenhängen zwischen Dokumenten (z. B. Versuch ↔ Auswertung ↔ Richtlinie).

4. **Q/A-Generierungsschicht („Instruction-Generator“)**
   - LLM-basierte Generierung von Frage–Antwort-Beispielen aus den semantisch angereicherten Dokumenten.
   - Spezialisierung auf die definierten Core-Tasks (Cooling, GT-Power, Skripte, Konzern-Infrastruktur, Entwicklungsabläufe, Datenkorrelation).

5. **Zentrales Q/A-Trainings-Repository**
   - Modellunabhängiger, versionierter JSONL-Datensatz mit Instruction-Triples (Instruction, Input, Output) und Metadaten.
   - Wird als Grundlage für verschiedene Fine-Tunes und zukünftige Modelle verwendet.

6. **RAG-Schicht (Vektorindices)**
   - Erstellung von Embeddings für relevante Dokument-Chunks.
   - Aufbau von FAISS/Chroma-Indizes, die in KNIME und anderen Tools genutzt werden können.

7. **Fine-Tuning- und Inferenz-Schicht**
   - Fine-Tuning großer Modelle (LLM) auf DACHS mit dem Q/A-Datensatz (Instruction-Tuning).
   - Bereitstellung der Modelle für Inferenz auf GPU-Knoten (Batch/Service, je nach Setup).

## 3.2 Gesamtübersicht der Pipeline (aktualisierte Fassung)

Die Verarbeitungspipeline für einen Workspace (z. B. `es_phdoeble-rag_pipeline`) besteht aus folgenden Hauptschritten:

1. **Ingestion (`raw/ → normalized/json/`)**  
   - Rohdokumente (PDF, DOCX, etc.) werden eingelesen, in Text überführt und in ein einheitliches JSON/JSONL-Schema gebracht.  
   - Ergebnis: pro Quelle eine Datei unter `normalized/json/`, in der **jedes Chunk als JSON-Objekt** vorliegt (bei JSONL: eine Zeile = ein Chunk).

2. **Normalisierung & Basis-Metadaten (`normalized/json/`)**  
   - Vereinheitlichung von Feldern wie `doc_id`, `chunk_id`, `source_type`, `language`, Seiten-/Abschnittsangaben usw.  
   - Sicherstellen, dass **jedes Chunk** eine eindeutige `chunk_id` und eine `doc_id` besitzt (Pflichtfelder).  
   - Optional: erste heuristische Labels (z. B. „Titel“, „Abschnittsüberschrift“, „Fließtext“).

3. **Semantische Anreicherung (`normalized/json/ → semantic/json/`)**  
   - LLM-basierte Anreicherung der Chunks, z. B.:
     - `chunk_role` (exercise, explanation, derivation, table, figure, …),  
     - domänenspezifische Labels / Taxonomie (`content_type`, `domain`, `artifact_role`, `trust_level`),  
     - kurze Zusammenfassungen, Key-Quantities, Formeln.  
   - Ergebnis: angereicherte Chunks in `semantic/json/` mit gefülltem `semantic`-Block.  
   - Optional kann dieser Schritt bereits **Retrieval-Kontext** aus einem vorhandenen FAISS-Kontextindex nutzen (zweiter Durchlauf, siehe unten).

4. **Kontext- und RAG-Indizes (`semantic/json/ → indices/faiss/`, optional `indices/chroma/`)**  
   - Aufbau eines **globalen Chunk-Kontextindex** über alle semantisch angereicherten Chunks des Workspaces:  
     - Skript: `scripts/embed_chunks.py`  
     - Input: `semantic/json/`  
     - Output unter `indices/faiss/`:  
       - `contextual.index` – FAISS-Vektorindex (z. B. `IndexFlatIP` oder `IndexFlatL2`),  
       - `contextual_meta.jsonl` – Metadaten je Vektor/Chunk,  
       - `contextual_config.json` – kleine JSON-Konfiguration zum Index (Modell, Dimension, Pfade, Erstellungszeitpunkt usw.).  
   - Jede Zeile in `contextual_meta.jsonl` enthält u. a.:  
     - `faiss_id` (0-basierte Position des Vektors im FAISS-Index),  
     - `doc_id`, `chunk_id`, `source_path`, `source_type`, `language`,  
     - `meta` (zusätzliche technische Informationen),  
     - `semantic` (kompletter Semantik-Block),  
     - flache Convenience-Felder wie `trust_level`, `content_type`, `domain` (redundant zu `semantic`, aber einfacher für Filter).  
   - `embed_chunks.py` führt vor dem Index-Bau einfache Konsistenz-Checks durch (z. B. doppelte `chunk_id`s, Längen-Mismatch zwischen Embeddings und Metadaten) und loggt diese in `logs/indices/`.

5. **Q/A-Kandidaten-Generierung (`semantic/json/ → qa_candidates/jsonl/`)**  
   - LLM erzeugt Frage–Antwort-Paare auf Basis von semantisch angereicherten Chunks und deren Nachbarschaft im Kontextindex.  
   - Nutzung des FAISS-Kontextindex für Multi-Chunk-Kontext (z. B. Aufgabe + Erklärung + zentrale Formel).

6. **Filterung & Qualitätssicherung (`qa_candidates/jsonl/ → qa_final/jsonl/`)**  
   - Heuristische und LLM-basierte Filter (z. B. Konsistenzchecks, Dubletten, Verständlichkeit, Groundedness).  
   - Optional: Verwendung des Kontextindex, um zu prüfen, ob Antworten wirklich im lokalen Kontext (Chunk + Nachbarn) verankert sind.

7. **Training / Fine-Tuning & Serving**  
   - Verwendung von `qa_final/jsonl/` für Instruction-Tuning bzw. Fine-Tuning domänenspezifischer Modelle (HuggingFace Transformers + PEFT/LoRA o. Ä.).  
   - Deployment/Serving auf DACHS bzw. lokal (z. B. über vLLM, Ollama, KNIME-Pipelines).

### 3.3 Bilingualität und Sprachmix

- Die Dokumente können Deutsch und Englisch enthalten; teilweise mischen sich die Sprachen in einem Dokument (z. B. deutsche Beschreibung mit englischen Code-Kommentaren).
- Das System soll:
  - beide Sprachen verstehen,
  - Antworten bevorzugt in der Sprache des Nutzers bzw. der Frage geben,
  - Fachbegriffe, Code, Funktionsnamen u. ä. auf Englisch belassen, wo es sinnvoll ist.
- Im Trainingsdatensatz wird für jedes Beispiel ein Attribut `language` gepflegt (z. B. `"de"`, `"en"`, `"mixed"`).
- Bilinguale Testfälle sollen sicherstellen, dass:
  - deutsche Fragen zu englischen Dokumenten korrekt beantwortet werden,
  - englische Fragen zu deutschen Dokumenten (mit englischen Begriffen) ebenfalls korrekt beantwortet werden.

### 3.4 Integration mit KNIME

- Die Vektorindizes (FAISS/Chroma) und ggf. vorberechnete Embeddings werden so erzeugt, dass sie:
  - direkt von KNIME-Vektorstore-Nodes genutzt werden können,
  - oder via KNIME-Workflows (z. B. über Python-Skripte) angebunden werden.
- KNIME-Workflows können:
  - Rohdaten oder vorverarbeitete Daten in Workspaces einspeisen,
  - RAG-Anfragen gegen die Indizes stellen,
  - lokale LLM-Endpunkte (auf DACHS laufend, z. B. via Portforwarding oder Service-API innerhalb des Clusters) nutzen.

---

## 4. Normierte Datenstrukturen und Namenskonventionen

### Software-Umgebung auf DACHS

**Ziel:** Einheitliche, reproduzierbare Python-Umgebung für alle Skripte und SLURM-Jobs des Projekts.

**Festlegungen:**

- Cluster-Python-Modul: `devel/python/3.12.3-gnu-14.2`
- Projekt-venv: `~/venv/dachs_rag_312`
- Projekt-Repo: `~/dachs_rag_framework`
- Env-Struktur im Repo:
  - `env/requirements.txt` – zentrale Paketliste
  - `env/bootstrap_env.sh` – Skript zum Erzeugen/Aktualisieren der Umgebung
  - `logs/` – Standard-Logverzeichnis für Test- und Arbeitsjobs

**Bootstrap-Skript (einmalig und bei Paketänderungen):**

```bash
cd ~/dachs_rag_framework
chmod +x env/bootstrap_env.sh
./env/bootstrap_env.sh
```
Das Skript:
* lädt devel/python/3.12.3-gnu-14.2,
* legt ~/venv/dachs_rag_312 an (falls nicht vorhanden),
* aktualisiert pip, setuptools, wheel,
* installiert alle Pakete aus env/requirements.txt.


Manuelle Aktivierung der Projekt-Umgebung (Shell oder im SLURM-Skript):

```bash
module purge
module load devel/python/3.12.3-gnu-14.2
source "$HOME/venv/dachs_rag_312/bin/activate"
```

Test-SLURM-Job (CPU/FAISS-Sanity-Check):

```bash
sbatch env/test_env_cpu.slurm
```

Der Job prüft:

Python-Version,

Imports von torch, transformers, faiss,

einfachen FAISS-Index-Aufbau + Query.

# Daten-Workspace (BeeGFS)
```bash
/beegfs/scratch/workspace/es_phdoeble-rag_pipeline
├─ raw/                      # Rohdaten (PDFs, Docs, etc.)
├─ normalized/               # normalisierte Dokumente (einheitliches JSON-Schema)
│  └─ json/
│     └─ archive/            # ältere/archivierte Normalisierungen
├─ semantic/                 # semantisch annotierte Daten
│  └─ json/
│     └─ archive/            # ältere/archivierte Annotationen
├─ qa_candidates/            # Roh-Kandidaten für Q&A
│  └─ jsonl/                 # eine Zeile = ein Q&A-Kandidat
├─ qa_final/                 # finale Q&A-Datensätze
│  └─ jsonl/                 # eine Zeile = fertiges Q&A-Sample
├─ indices/                  # Suchindizes für RAG
│  ├─ faiss/                 # FAISS-Vektordatenbank
│  └─ chroma/                # Chroma-DB Index
└─ logs/                     # Logs der Pipeline-Jobs
```


# Home-Verzeichnis (Code, Umgebungen, Tools)
```bash
/home/es/es_es/es_phdoeble
├─ dachs_rag_framework/          # RAG-Framework (Git-Repo, Codebasis)
│  ├─ config/                    # Konfigurationen
│  │  ├─ LLM/                    # Modell-/LLM-Settings
│  │  ├─ pipeline/               # Pipeline-Config (Stages, Pfade)
│  │  ├─ qa/                     # Q/A-Generierung (generate_qa_candidates; Filter, Nachbarschaft, LLM-Config)
│  │  └─ taxonomy/               # Taxonomien, Label-Schemata
│  ├─ env/                       # Env-/Setup-Skripte
│  ├─ jobs/                      # SLURM-Jobskripte (*.slurm)
│  ├─ logs/                      # Framework-Logs (nicht die Daten-Logs)
│  ├─ scripts/                   # Python-Skripte (annotate, ingest, qa, indices …)
│  └─ wiki/                      # Doku, Workshop-Notizen, Masterplan (Markdown)
│  ( .git/ und Unterordner → Git-Metadaten, hier weggelassen )
│
├─ venv/
│  └─ dachs_rag_312/             # Virtuelle Umgebung für Projekt
│     ├─ bin/                    # python, pip, Konsoleinträge
│     ├─ lib/python3.12/
│     │  └─ site-packages/       # installierte Python-Pakete
│     └─ share/
│
├─ .vscode-server/               # VS Code Server (Extensions, Logs, Workspaces)
├─ .ssh/                         # SSH-Keys und Config
├─ .ollama/                      # Lokale Ollama-Modelldaten
├─ .cache/                       # Pip-/Tool-Caches
└─ .local/                       # weitere User-spezifische Tool-Daten
```

## 4.1 Normalisierte Dokumentstruktur („normalized documents“)

Jedes normalisierte Dokument (oder Chunk) wird im JSON-Format gespeichert. Ein generisches Schema (Beispiel):

```json
{
  "doc_id": "tp_textbook_2019_01",
  "chunk_id": "tp_textbook_2019_01_c0005",
  "source_type": "pdf",
  "source_path": "raw/textbooks/thermo/textbook_2019_01.pdf",
  "title": "2.3 Heat Transfer in Cooling Systems",
  "language": "en",
  "content": "Here we describe the fundamentals of heat transfer relevant for cooling system design...",
  "meta": {
    "page_start": 45,
    "page_end": 48,
    "num_pages": 870,
    "block_types": ["heading", "paragraph", "formula"],
    "has_table": false,
    "has_formula": true,
    "has_heading": true,
    "tags": ["cooling_system", "heat_transfer"]
  },
  "semantic": {}
}
```

Pflichtfelder:

- `doc_id`: eindeutige Dokument-ID.
- `chunk_id`: eindeutige Chunk-ID (Dokument + Abschnitt/Seite/Paragraf).
- `source_type`: ursprünglicher Dateityp (`pdf`, `pptx`, `xlsx`, `docx`, `code`, `log`, …).
- `source_path`: Pfad im thematischen Workspace (z. B. `raw/textbooks/…`).
- `content`: extrahierter Text (oder serialisierte Struktur z. B. für Tabellen/Code).
- `language`: Primärsprache des Chunks (`"de"`, `"en"`, `"mixed"`).
- `meta`: Objekt für zusätzliche Metadaten (Seiten, Blocktypen, Tags usw.).
- `semantic`: Objekt für semantische Annotationen (wird in Schritt 2 der Pipeline gefüllt).

Typische `meta`-Felder bei PDFs:

- `page_start`, `page_end`: 0-basierter Seitenbereich des Chunks.
- `num_pages`: Gesamtseitenzahl des Ursprungsdokuments.
- `block_types`: Menge der im Chunk vorkommenden Blocktypen, z. B. `["paragraph", "formula", "table"]`.
- `has_table`, `has_formula`, `has_heading`: schnelle Booleans zur Filterung.
- optionale Felder wie `tags`, `created_at`, `workspace` usw. je nach Workspace.

Chunks werden je nach Dateityp nach sinnvollen Einheiten geschnitten, z. B.:

- **PDFs**: satzbasiertes Chunking mit:
  - Entfernung wiederkehrender Kopf-/Fußzeilen,
  - Heuristiken für Überschriften (`heading`), Tabellen (`table`) und Formeln (`formula`),
  - Chunks aus aufeinanderfolgenden Sätzen bis zu einer Zielgröße (z. B. ~6000 Zeichen),
  - kleinen Satz-Overlaps zwischen Chunks (1–2 Sätze), um Kontext an Chunk-Grenzen zu erhalten.
- **PowerPoints**: einzelne Folien (`slide_id`) bzw. logisch zusammengehörige Foliengruppen.
- **Excel**: Tabellen/Sheets plus ggf. Zeilen-/Spaltenbereiche.
- **Code**: Dateien plus Funktionen/Blöcke.
- **Protokolle/Logs**: Abschnitte nach Datum/Agenda.

Das Schema der Felder bleibt für alle Dateitypen gleich, damit nachgelagerte Schritte (Semantik, Q/A, Embeddings) generisch implementiert werden können.

### 4.1.1 Speicherformat

Normalisierte Dokumente werden im Workspace unter

```text
normalized/json/
```

abgelegt. In der Praxis wird überwiegend das **JSON Lines-Format (`.jsonl`)** verwendet:

- Pro Quell-Dokument eine Datei `pdf_<Titel>_<hash>.jsonl`  
- **Eine Zeile = ein Chunk** (ein JSON-Objekt).
- Alternativ können für kleine Tests oder Sonderfälle auch `.json`-Dateien genutzt werden (z. B. ein Dokument mit `chunks`-Liste).

### 4.1.2 Chunk-Schema (pro JSON-Objekt / Zeile)

Jede Zeile einer `.jsonl`-Datei entspricht einem Chunk und folgt einem einheitlichen Schema (Beispiel):

```json
{
  "doc_id": "pdf_Incropera_2006_3fe640ba",
  "chunk_id": "pdf_Incropera_2006_3fe640ba_c0260",
  "source_type": "pdf",
  "source_path": "Incropera 2006 - Fundamentals of Heat and Mass Transfer.pdf",
  "page_range": [260, 261],
  "title": "4.3.2 Convection from a Flat Plate",
  "content": "Der eigentliche Text dieses Chunks ...",
  "language": "de",
  "meta": {
    "section": "Chapter 4",
    "subsection": "4.3 External Flow",
    "keywords": ["convection", "flat plate", "boundary layer"]
  },
  "semantic": {
    "chunk_role": null,
    "content_type": null,
    "domain": null
  }
}
```

Wichtige Punkte:

- **`doc_id` (Pflicht)**: eindeutige Dokument-ID, konsistent mit vorherigen Pipeline-Schritten (Ingestion).  
- **`chunk_id` (Pflicht)**: eindeutige Chunk-ID, global im Workspace einzigartig. Sie wird u. a. als Schlüssel im FAISS-Index verwendet.  
- **`content` (Pflicht)**: der eigentliche Text des Chunks (i. d. R. ein oder mehrere Sätze, ggf. auch Formeln/Tabellen als Textrepräsentation).  
- **`source_path`**: Originalquelle (z. B. PDF-Dateiname), optional mit Zusatzinfos.  
- **`semantic`**: Platzhalter für spätere semantische Anreicherung (LLM), initial meist `null` oder leer.

Die oben gezeigte JSON-Struktur entspricht **genau einem Eintrag in einer `.jsonl`-Datei**. Eine Datei besteht dann aus vielen dieser Zeilen.

---

### 4.2 Metadaten-Schema

`content_type`, `domain`, `artifact_role`, `trust_level`

Zusätzlich zur Normalform werden semantische Metadaten gepflegt. Diese werden nach der semantischen Anreicherung im Chunk als Block `semantic` abgelegt (unter Beibehaltung von `doc_id` / `chunk_id`). Beispiel:

```json
{
  "doc_id": "tp_textbook_2019_01",
  "chunk_id": "tp_textbook_2019_01_ch2_sec3_par5",
  "source_type": "pdf",
  "source_path": "raw/textbooks/thermo/textbook_2019_01.pdf",
  "title": "2.3 Heat Transfer in Cooling Systems",
  "language": "en",
  "content": "Here we describe the fundamentals of heat transfer relevant for cooling system design...",
  "meta": {
    "has_heading": false,
    "has_table": false
  },
  "semantic": {
    "content_type": ["textbook"],
    "domain": ["thermodynamics"],
    "artifact_role": ["statement"],
    "trust_level": "high",
    "chunk_role": ["explanation"],
    "summary_short": "Short 1–3 sentence summary of this chunk.",
    "equations": [],
    "key_quantities": ["heat_transfer_coefficient"],
    "meta": {
      "mode": "llm",
      "used_prev_next": true,
      "used_faiss": false,
      "faiss_neighbors": [],
      "empty_reasons": {
        "content_type": null,
        "domain": null,
        "artifact_role": null,
        "summary_short": null
      }
    }
  }
}
```

**`semantic.meta` (Provenance + Debugbarkeit)**  
Zusätzlich zu den eigentlichen semantischen Feldern wird ein Provenance-Block gepflegt, um Ergebnisse reproduzierbar, evaluierbar und debuggbar zu machen:

- `semantic.meta.mode`  
  Kennzeichnet den Pfad, über den der Chunk annotiert wurde, z. B.:
  - `llm` (normaler LLM-Aufruf)
  - `structural_rule1_short` / `structural_rule1_numeric` / `structural_rule1_label` (Chunk wurde als strukturell erkannt, kein LLM-Call)

- `semantic.meta.used_prev_next: true|false`  
  Ob lokaler Nachbar-Kontext (previous/next) im Prompt genutzt wurde.

- `semantic.meta.used_faiss: true|false`  
  Ob FAISS-Retrieval-Kontext im Prompt genutzt wurde.

- `semantic.meta.faiss_neighbors: [] | [{chunk_id, score, doc_id?}, ...]`  
  Schlanke Nachbarschaftsliste (ohne Volltext), um später exakte Retrieval-Situationen nachzuvollziehen.

- `semantic.meta.empty_reasons`  
  Explizite Unterscheidung, warum ein Feld leer ist (Analytics trennt Ursachen):
  - `llm_empty` → Modell konnte/hat nichts gesetzt (oder nach Taxonomie-Filterung leer)
  - `structural_rule1` → Feld bewusst leer gesetzt, weil Chunk strukturell/inhaltlos
  - `rule4_suppressed` → `summary_short` bewusst unterdrückt (Heuristik)

**Kontext- und RAG-Indizes (`semantic/json/ → indices/faiss/`, optional `indices/chroma/`)**  
- Aufbau eines **globalen Chunk-Kontextindex** über alle Chunks des Workspaces:  
  - Skript: `scripts/build_embeddings.py`  
  - Input: `semantic/json/`  
  - Output:  
    - `indices/faiss/contextual.index` (FAISS-Vektorindex),  
    - `indices/faiss/contextual_meta.jsonl` (Metadaten je Vektor: `faiss_id`, `chunk_id`, `doc_id`, `source_path`, `language`, `meta`, `semantic`, …),  
    - `indices/faiss/contextual_config.json` (Konfiguration: Embedding-Modell, Index-Typ, Pfade, Erstellungszeitpunkt, Normalisierungsmodus).  

- **`faiss_id`** entspricht der Position des Vektors im FAISS-Index und wird verwendet, um Trefferergebnisse (`faiss_id`) wieder auf `chunk_id`/`doc_id` zu mappen.  
- Die Config-Datei wird automatisch erzeugt und kann in späteren Schritten genutzt werden, um Modell/Index-Parameter ohne harten Code zu lesen.

---

### 4.2.0 Taxonomie-Konfiguration (config/taxonomy)

Die zulässigen Werte der semantischen Felder

- `content_type`
- `domain`
- `artifact_role`
- `trust_level`

werden **nicht im Code**, sondern in zentralen JSON-Konfigurationsdateien im Home-Verzeichnis gepflegt:

- `~/dachs_rag_framework/config/taxonomy/content_type.json`
- `~/dachs_rag_framework/config/taxonomy/domain.json`
- `~/dachs_rag_framework/config/taxonomy/artifact_role.json`
- `~/dachs_rag_framework/config/taxonomy/trust_level.json`

Jede Datei enthält eine Liste von Objekten mit mindestens:

- `id` – maschinenlesbarer Schlüssel, der später im JSON der Dokumente verwendet wird  
- `label` (optional) – lesbarer Name  
- `description` – kurze verbale Beschreibung  
- optional `examples` – typische Beispiele aus der Domäne

Alle Skripte, die mit semantischen Feldern arbeiten (z. B. `annotate_semantics.py`, `generate_qa_candidates.py`), lesen diese Dateien zur Laufzeit ein und validieren ihre Ausgaben gegen diese Taxonomie.  

Die folgenden Unterkapitel (4.2.1 ff.) zeigen **Beispiele** für Einträge, sind aber nur erläuternd – maßgeblich ist immer der Inhalt der JSON-Dateien.

#### 4.2.1 content_type (Dokument-/Inhaltstyp)

Die zulässigen `content_type`-Werte werden in
`~/dachs_rag_framework/config/taxonomy/content_type.json`
gepflegt. Typische Einträge sind z. B.:

- `textbook` – Lehrbuchartige, systematisch aufgebaute Darstellung
- `paper` – wissenschaftlicher Fachartikel
- `norm` – Normen/Standards
- `software_handbook` – Software-/API-Handbuch
- `guideline` – Richtlinien, Vorgehensmodelle
- `best_practice_doc` – Best-Practice-Dokument
- `meeting_notice` – Einladung/Agenda
- `management_ppt` – Management-Präsentation
- `expert_ppt` – Experten-Präsentation
- `code_internal` – interner Code
- `code_external` – externer Code
- `experiment_supplier_doc` – Lieferantendokumentation zu Versuchen
- `experiment_internal_doc` – interne Versuchs-/Labordokumentation
- `spreadsheet` – Tabellen, Kennfelder, Messdatentabellen
- `lab_report` – Laborberichte
- `simulation_report` – Simulationsberichte


#### 4.2.2 domain (Fachgebiet / Kontext)

Die zulässigen Werte für `domain` werden in
`~/dachs_rag_framework/config/taxonomy/domain.json` definiert.
Typische Einträge sind z. B. `simulation`, `gt_power`, `cfd`,
`test_driving`, `laboratory`, `programming`, `thermodynamics`, `hpc` usw.


#### 4.2.3 artifact_role (Rolle im Entwicklungsprozess)

Beispiele:

Die zulässigen Werte für `artifact_role` werden in
`~/dachs_rag_framework/config/taxonomy/artifact_role.json` gepflegt.
Beispiele sind `measurement_data`, `simulation_result`, `test_result`,
`assumption`, `target_spec`, `statement`, `procedure`, `report_summary` usw.


#### 4.2.4 trust_level (Vertrauensniveau)

Beispiele:

Die zulässigen Werte für `trust_level` werden in
`~/dachs_rag_framework/config/taxonomy/trust_level.json` gepflegt.
Im aktuellen Setup werden z. B. drei Stufen verwendet:
`high`, `medium`, `low`.


### 4.3 Q/A-Trainingsformat (Instruction-Tuning-Schema)

Der zentrale Trainingsdatensatz wird als JSONL-Datei geführt, wobei jede Zeile ein vollständig beschriebenes Frage–Antwort-Beispiel enthält. Generisches Schema:

```json
{
  "id": "gtp_00123_q1",
  "topic": "gt_power_cooling",
  "workspace": "GT_Power_Models",
  "source_ids": [
    "doc:gtp_model_2023_01#sec4_par2",
    "xls:cooling_limits_2022#sheet1_row27"
  ],
  "instruction": "Erkläre einem erfahrenen Ingenieur, warum bei Motorvariante X die maximale Kühlmitteltemperatur auf 105°C begrenzt ist.",
  "input": "Relevante Auszüge aus dem GT-Power-Modell und der Tabelle mit Grenzwerten der Kühlmitteltemperaturen.",
  "output": "Die Begrenzung auf 105°C ergibt sich aus der Kombination aus Materialgrenzen des Zylinderkopfs, der Dichtungen und der maximal zulässigen Öltemperatur. Die Analyse der Variante X zeigt, dass höhere Kühlmitteltemperaturen zu unzulässigen Spannungen im Zylinderkopf führen würden...",
  "language": "de",
  "content_type": [
    "simulation_report",
    "spreadsheet"
  ],
  "domain": [
    "gt_power",
    "thermodynamics"
  ],
  "artifact_role": [
    "simulation_result",
    "target_spec"
  ],
  "trust_level": "high",
  "tags": [
    "cooling_system",
    "temperature_limit",
    "material_limits"
  ],
  "created_by": "llm_auto",
  "created_at": "2025-12-01",
  "difficulty": "senior_engineer",
  "style": "concise_technical",
  "version": 1
}
```

Empfohlene Pflichtfelder:

- `id`: eindeutige ID des Q/A-Beispiels.
- `instruction`: eigentliche Aufgabe/Frage an das Modell.
- `input`: der Kontext / Ausschnitt aus den Dokumenten (falls nötig, sonst leer oder kurz).
- `output`: die gewünschte ideale Antwort.
- `language`: `"de"`, `"en"` oder `"mixed"` (Sprache der Antwort).
- `workspace`: thematischer Workspace, aus dem das Beispiel stammt.

Optionale, aber empfohlene Felder:

- `topic`: grobe Themenzuordnung (z. B. `gt_power_cooling`, `test_driving_correlation`).
- `source_ids`: Referenzen auf Chunks in `normalized`/`semantic` (für Nachvollziehbarkeit).
- `content_type`, `domain`, `artifact_role`, `trust_level`: Übernahme aus den Quellchunks (ggf. vereinigt).
- `tags`: freie Schlagworte.
- `created_by`: `"llm_auto"`, `"llm+human_review"`, `"human_only"`.
- `created_at`: Erzeugungsdatum.
- `difficulty`: Zielniveau (`"junior"`, `"intermediate"`, `"senior_engineer"`).
- `style`: z. B. `"concise_technical"`, `"detailed_explainer"`.
- `version`: numerische Versionsnummer zur späteren Pflege.

Dieses Schema ist mit gängigen Instruction-Tuning-Frameworks kompatibel (Transformers, TRL, PEFT, Ollama-Formate etc.) und kann auch für zukünftige Modellgenerationen unverändert weiterverwendet werden.

### 4.4 Konventionen (IDs, Namen, Versionierung)

Um ein konsistentes Arbeiten zu ermöglichen, gelten folgende Konventionen:

- **Dokument-IDs (`doc_id`)**  
  Aufbau: `<workspace-prefix>_<typ>_<jahr>_<laufnummer>`  
  Beispiele:  
  - `tp_textbook_2019_01`  
  - `gtp_model_2023_02`  
  - `td_report_2022_05`

- **Chunk-IDs (`chunk_id`)**  
  Aufbau: `<doc_id>_<struktur>`  
  Beispiele:  
  - `tp_textbook_2019_01_ch2_sec3_par5`  
  - `ppt_mgmt_2024_01_slide7`  
  - `xls_cooling_2021_03_sheet1_row42`

- **Q/A-IDs (`id`)**  
  Aufbau: `<workspace-abbr>_<laufnummer>_q<n>`  
  Beispiele:  
  - `gtp_00123_q1`  
  - `thermo_00005_q3`

- **Workspaces**  
  Benennung exakt wie in der Logik der thematischen Workspaces (siehe Kapitel 5), z. B. `GT_Power_Models`, `Thermodynamics_Textbooks`.

- **Versionierung**  
  Trainingsdatensätze (`qa_final`) werden mit Versionsnummern geführt (z. B. `qa_final_v1.jsonl`, `qa_final_v2.jsonl`).  
  Änderungen werden in einer kurzen Changelog-Datei im gleichen Ordner festgehalten (`CHANGELOG.md`).

---

## 5. Themen-Workspaces und Ordnerstrukturen

#### Workspaces sind temporär (Scratch, kein Archiv)

Workspaces sind explizit **temporäre** Bereiche auf schnellen Scratch-Dateisystemen. Sie sind gedacht für:

- laufende Jobs und Jobkampagnen
- große Zwischenstände (z. B. normalisierte JSONs, Embeddings, Indizes)
- Experimente, die später konsolidiert oder gelöscht werden

Sie sind **nicht** für langfristige Archivierung gedacht. Jeder Workspace hat eine begrenzte Lebensdauer und wird nach Ablauf entweder automatisch bereinigt oder muss vorher vom Benutzer auf langsamere, dauerhafte Storage-Systeme ausgelagert werden. Die RAG-Pipeline ist daher so konzipiert, dass alle Zwischenergebnisse in Workspaces liegen, aber wichtige Endergebnisse (z. B. trainierte Modelle, finaler QA-Datensatz, „frozen“ Indizes) in ein dauerhaftes Storage verschoben und dort versioniert werden.

#### Gemeinsame Nutzung von Workspaces (optional)

Für gemeinsame Projekte (z. B. mehrere Personen arbeiten an denselben Textkorpora, Indizes oder Modellen) können Group-Workspaces und Sharing genutzt werden:

- `ws_allocate -g <ID> <DAYS>`  
  legt einen Workspace an, der von Mitgliedern derselben Gruppe gelesen werden kann.

- `ws_allocate -G <group> <ID> <DAYS>`  
  legt einen Workspace an, der gruppenschreibbar ist (Sticky-Bit, gemeinsamer Schreibzugriff).

Zusätzlich können Workspaces – abhängig vom Dateisystem und ACL-Unterstützung – mit `ws_share` mit einzelnen Benutzern geteilt werden:

```bash
ws_share share   <workspace> <user>   # Lesezugriff gewähren
ws_share unshare <workspace> <user>   # Zugriff entziehen
```
Für die DACHS-RAG-Pipeline bedeutet das: gesamte Teams können gemeinsame Workspaces für

Korpora (raw/, normalized/, semantic/),

abgeleitete QA-Datensätze (qa_candidates/, qa_final/),

und Indizes (indices/)

nutzen, ohne dass jeder Benutzer eigene Kopien dieser Daten halten muss.

### 5.1 Übersicht der Workspaces

Für die erste Ausbaustufe werden fünf thematische Workspaces vorgesehen:

1. `GT_Power_Models`  
   - GT-Power-Modelle, zugehörige Dokumentation, Skripte und Berichte.

2. `Thermodynamics_Textbooks`  
   - Lehrbücher, Skripte, Paper mit Grundlagen und Vertiefungen zur Thermodynamik und Kühlsystemen.

3. `Test_Driving_Reports`  
   - Fahrversuchsberichte, Auswertungen, Management- und Expertenpräsentationen zum Testbetrieb.

4. `Laboratory_Measurements`  
   - Laborversuche, Messdaten, Kennfelder, interne Protokolle.

5. `Management_Strategy`  
   - Management-Präsentationen, Strategiepapiere, Richtlinien und Roadmaps.

Für weitere Themenbereiche können später zusätzliche Workspaces nach dem gleichen Muster eingerichtet werden.

### 5.2 Standard-Ordnerlayout je Workspace

Jeder thematische Workspace folgt dem gleichen Layout (analog, unabhängig vom konkreten Thema):

```text
<Workspace-Root>/
  raw/
    pdf/
    pptx/
    xlsx/
    docx/
    code/
    other/
  normalized/
    json/
  semantic/
    json/
  qa_candidates/
    jsonl/
  qa_final/
    jsonl/
  indices/
    faiss/
    chroma/
  logs/
    ingestion/
    semantic/
    qa_generation/
    indices/
```

Erläuterung:

- `raw/`  
  Ablage der Originaldateien, ggf. nach Typ getrennt.

- `normalized/json/`  
  normalisierte Dokument-Chunks (ein JSON pro Chunk oder pro Dokument, je nach Design).

- `semantic/json/`  
  normalisierte Dokumente, erweitert um `semantic`-Block (content_type, domain, artifact_role, trust_level etc.).

- `qa_candidates/jsonl/`  
  automatisch erzeugte Q/A-Beispiele (Vorstufe, inkl. evtl. nicht akzeptierter Kandidaten).

- `qa_final/jsonl/`  
  bereinigte, zusammengeführte Trainingsdatensätze, versioniert (z. B. `qa_final_v1.jsonl`).

- `indices/faiss/`, `indices/chroma/`  
  Vektorindices inkl. Metadaten, die von KNIME oder anderen Tools geladen werden können.

- `logs/...`  
  Pro Pipeline-Schritt eigene Log-Dateien (Ingestion, Semantik, Q/A-Generierung, Index-Aufbau).

### 5.3 Nutzung der Workspace-Tools

Workspaces auf DACHS werden mit den bereitgestellten Workspace-Tools angelegt und verwaltet. Für die RAG-Pipeline werden typischerweise mehrere thematische Workspaces verwendet, z. B.:

- `Thermodynamics_Textbooks`
- `GT_Power_Models`
- `Test_Driving_Reports`
- `Laboratory_Measurements`
- `Management_Strategy`

#### Anlegen und wiederverwenden von Workspaces

Ein Workspace wird mit `ws_allocate` angelegt. Die Laufzeit wird in Tagen angegeben:

```bash
ws_allocate GT_Power_Models 180
ws_allocate Thermodynamics_Textbooks 180
ws_allocate Test_Driving_Reports 180
ws_allocate Laboratory_Measurements 180
ws_allocate Management_Strategy 180
```

Wichtig: `ws_allocate` ist idempotent. Wird ein Workspace mit derselben ID erneut angelegt, erhält man lediglich erneut den Pfad des bestehenden Workspaces zurück. Dieses Muster ist explizit für Batch-Jobs gedacht:

```bash
SCR=$(ws_allocate Thermodynamics_Textbooks 180)
cd "$SCR"
```

Dieses Pattern kann in jedem Job wiederverwendet werden (z. B. in einer Jobkampagne), ohne dass neue Workspaces erzeugt werden.

Pfad und Übersicht
Pfad eines Workspaces bestimmen:

```bash
Copy code
ws_find GT_Power_Models
Eigene Workspaces auflisten:
```

```bash
Copy code
ws_list
```
Je nach Optionen (-t, -v, -l etc.) können weitere Details (Restlaufzeit, verfügbare Verlängerungen, Speicherorte) angezeigt werden.

Verlängerung der Lebensdauer
Die Laufzeit eines Workspaces kann im Rahmen der vom Cluster gesetzten Limits verlängert werden:

```bash
Copy code
ws_extend GT_Power_Models 60
```
Alternativ sind je nach Clusterkonfiguration auch Varianten mit ws_allocate -x möglich. Die Anzahl möglicher Verlängerungen und maximale Laufzeit sind systemseitig vorgegeben.

Freigeben und Lebenszyklus eines Workspaces
Ein Workspace wird freigegeben, wenn er nicht mehr benötigt wird:

```bash
Copy code
ws_release GT_Power_Models
Der Lebenszyklus eines Workspaces umfasst typischerweise drei Phasen:
```

**1. Aktiv**

Workspace ist regulär nutzbar.

Sichtbar in ws_list.

Pfad wird über ws_find zurückgegeben.

**2. Released / wiederherstellbar**

Nach ws_release <ID> ist der Workspace nicht mehr direkt nutzbar, die Daten werden jedoch im Hintergrund verschoben (z. B. in ein verstecktes Verzeichnis).

Solange die durch den Cluster definierte Aufbewahrungszeit (keeptime) nicht überschritten ist, können Daten mit ws_restore wiederhergestellt werden.

**3. Endgültig gelöscht**

Nach Ablauf der Aufbewahrungszeit werden die Daten vom Cleaner, der regelmäßig per Cron-Job ausgeführt wird, endgültig entfernt.

Eine Wiederherstellung ist dann nicht mehr möglich.

Wiederherstellung (wenn vom System unterstützt):

``` bash
Copy code
ws_restore -l             # Liste der wiederherstellbaren Workspaces
ws_allocate <new-ws>      # neuen Workspace anlegen
ws_restore <old> <new-ws> # abgelaufenen Workspace unter neuem Namen wiederherstellen
```

Quota-Aspekt
Daten in einem freigegebenen Workspace können weiterhin auf das Nutzer-Quota angerechnet werden, solange sie physisch noch im „gelöschten“ Bereich liegen. Wer Speicherplatz freigeben möchte, sollte:

Daten innerhalb des Workspaces löschen und erst danach ws_release ausführen oder

bei bereits freigegebenem Workspace zunächst ws_restore verwenden, die Daten löschen und den Workspace anschließend erneut freigeben.

E-Mail-Reminder und Defaults (optional)
Clusterseitig kann konfiguriert sein, dass vor Ablauf eines Workspaces Erinnerungsmails verschickt werden. Nutzer können über Optionen wie -m (Mailadresse) und -r (Reminder-Tage) bei ws_allocate oder über eine persönliche Konfigurationsdatei ~/.ws_user.conf Defaultwerte (z. B. Standarddauer, Reminder, Standard-Gruppe) setzen.

Die Skripte der Pipeline (Ingestion, Semantik, Q/A, Indizes) werden so geschrieben, dass sie den Workspace-Pfad als Parameter akzeptieren und auf alle Workspaces mit identischer Struktur (siehe Abschnitt 5.2) anwendbar sind.


### 5.4 $HOME, Workspace und $TMPDIR / localscratch

Empfehlungen:

- `$HOME` nur für:
  - Skripte,
  - Konfigurationen (z. B. virtuelle Umgebungen, Module),
  - kleine Testdaten und Ergebnis-Samples.

- Workspaces (`ws_*`) für:
  - alle Rohdaten (GB-Bereich),
  - normalisierte und semantische JSONs,
  - Q/A-Datensätze,
  - Vektorindices.

- `$TMPDIR` / `/localscratch` für:
  - temporäre Daten während größerer Jobs (z. B. beim Fine-Tuning oder Embedding-Erzeugung),
  - Zwischenergebnisse, die nach Jobende nicht mehr benötigt werden.

---

## 6. Verarbeitungspipeline: Schritte und Skripte


## 6.1 Schritt 1: Ingestion & Normalisierung

**Ziele:**

- Einlesen aller relevanten Dateien aus `raw/`.
- Typabhängige Extraktion von Text/Struktur.
- Schreiben normalisierter JSON-Dokumente nach `normalized/json/`.

**Typische Skripte:**

- `scripts/ingest_pdfs.py`
- `scripts/ingest_pptx.py`
- `scripts/ingest_xlsx.py`
- `scripts/ingest_docx.py`
- `scripts/ingest_code.py`

**Verhalten von `ingest_pdfs.py` (konkret umgesetzt):**

- Extrahiert Text seitenweise mit `pypdf`.
- Entfernt wiederkehrende Kopf- und Fußzeilen heuristisch (Seitenüberschriften, Seitennummern, etc.).
- Zerlegt jede Seite in Zeilen und Sätze.
- Klassifiziert jede Zeile grob in Blocktypen:
  - `heading` (Kapitel-/Abschnittstitel),
  - `table` (Tabellenzeilen mit typischer Spaltenstruktur),
  - `formula` (Zeilen mit Gleichungen/typischen Mathe-Symbolen),
  - `paragraph` (normaler Fließtext).
- Baut Chunks als Sequenz von Sätzen:
  - Schneidet **nur an Satzgrenzen**.
  - Zielt auf eine maximale Chunkgröße (Default: `--max-chars 6000`).
  - Fügt eine kleine Satz-Überlappung zwischen Chunks ein (Default: `--sentence-overlap 2`).
  - Verhindert Mikro-Chunks am Dokumentende mit einem `--min-chars`-Schwellwert (Default: 400).
  - Erzwingt Chunkgrenzen an Überschriften, soweit sinnvoll.
- Schreibt pro PDF **eine JSONL-Datei** nach `normalized/json/`, in der jede Zeile ein Chunk ist.
- Füllt `meta.page_start`, `meta.page_end`, `meta.num_pages`, `meta.block_types`, `meta.has_table`, `meta.has_formula`, `meta.has_heading`.

**CLI-Schnittstelle (aktueller Stand `ingest_pdfs.py`):**

```bash
python scripts/ingest_pdfs.py   --input-dir  /beegfs/scratch/workspace/<workspace-name>/raw   --output-dir /beegfs/scratch/workspace/<workspace-name>/normalized/json   --max-chars 6000   --min-chars 400   --sentence-overlap 2   --verbose
```

- `--input-dir`: Wurzelverzeichnis der Rohdaten (PDFs) im Workspace (`raw/`).
- `--output-dir`: Zielverzeichnis für normalisierte JSONL-Dateien (`normalized/json/`).
- `--max-chars`: Zielgröße eines Chunks (weiche Obergrenze).
- `--min-chars`: minimale sinnvolle Chunk-Länge; zu kleine Rest-Chunks werden gemerged.
- `--sentence-overlap`: Anzahl der überlappenden Sätze zwischen aufeinanderfolgenden Chunks.
- `--verbose`: ausführlichere Logging-Ausgabe.

Andere `ingest_*`-Skripte folgen demselben Grundmuster (Einlesen aus `raw/`, Normalisierung nach `normalized/json/`), verwenden aber jeweils typ-spezifische Strategien für Chunking und Struktur (Slides, Tabellen, Code-Blöcke usw.).

## 6.2 Semantische Anreicherung (aktualisiert, inkl. Retrieval-Kontext)

Die semantische Anreicherung (`annotate_semantics.py`) liest normalisierte Chunks aus

```text
normalized/json/
```

und schreibt für jedes Chunk eine angereicherte Variante nach

```text
semantic/json/
```

### 6.2.1 Ziel der Anreicherung

Für jeden Chunk werden u. a. folgende Felder befüllt/ergänzt:

- `semantic.chunk_role` – z. B. `exercise`, `explanation`, `definition`, `derivation`, `figure_caption`, …
- `semantic.content_type` – grober Dokument-/Inhaltstyp gemäß Taxonomie (z. B. `textbook`, `paper`, `guideline`, `software_handbook`).
- `semantic.domain` – domänenspezifische Kategorien / Themenbereiche.
- `semantic.artifact_role` – Rolle des Chunks im Dokument (z. B. `statement`, `assumption`, `heading`, `table`, `figure_caption`).
- `semantic.trust_level` – Zuverlässigkeit des Inhalts gemäß Taxonomie (z. B. `high`, `medium`, `low`).
- `semantic.summary_short` – sehr kurze, chunk-spezifische Zusammenfassung; kann bei rein strukturellen Chunks bewusst leer sein.
- `semantic.equations` – Liste erkannter Gleichungen inkl. Variablen, Beschreibung, Einheiten.
- `semantic.key_quantities` – Liste der wichtigsten physikalischen / technischen Größen, die im Chunk vorkommen.

Nicht alle Felder sind für jeden Chunk sinnvoll befüllbar. Insbesondere bei strukturellen Fragmenten werden `content_type`/`domain` im Zweifel bewusst leer gelassen und nur einfache Rollen wie `artifact_role = ["structural"]` bzw. `["heading"]`, `["table"]` vergeben.

**Neu: Provenance & „Empty“-Ursachen für Debug/Evaluation**  
Zusätzlich wird ein Provenance-Block gepflegt:

- `semantic.meta.mode` (z. B. `llm` oder `structural_rule1_*`)
- `semantic.meta.used_prev_next` (ob lokaler Nachbar-Kontext genutzt wurde)
- `semantic.meta.used_faiss` + `semantic.meta.faiss_neighbors` (Retrieval-Nutzung und Nachbarschaftsliste)
- `semantic.meta.empty_reasons` (warum Felder leer sind: `llm_empty` vs. `structural_rule1` vs. `rule4_suppressed`)

Damit kann später klar ausgewertet werden, ob „empty“-Werte fachlich bedingt sind (LLM konnte nichts bestimmen) oder bewusst durch Heuristiken/Regeln erzeugt wurden.

#### 6.2.2 LLM-Aufruf mit optionalem Retrieval-Kontext

Statt jeden Chunk isoliert zu betrachten, kann die semantische Anreicherung optional Retrieval-Kontext aus dem globalen FAISS-Kontextindex nutzen.

Technischer Weg:

- Für jeden Ziel-Chunk `C` ist `chunk_id` eindeutig in `semantic/json/` vergeben.
- Über den Helfer `FaissRetriever` (Modul `scripts/faiss_retriever.py`) wird der Kontextindex geladen:
  - `contextual.index` (FAISS-Index),
  - `contextual_meta.jsonl` (Metadaten mit `faiss_id`, `chunk_id`, `doc_id`, `semantic`, …).
- Der Retriever bildet intern eine Map `chunk_id → faiss_id` und führt über FAISS eine k-NN-Suche durch.

Ablauf bei aktiviertem Retrieval (z. B. `use_retrieval_for_semantics = true` in `config/pipeline/semantic_config.json`):

1. **Ziel-Chunk bestimmen**  
   - `annotate_semantics.py` iteriert über alle Chunks in `normalized/json/` (inkl. Wiederaufnahme über bereits existierende Einträge in `semantic/json/`).

2. **Nachbarn über FAISS holen**  
   - Für `chunk_id` von `C` ruft das Skript den Retriever auf (Top-K).
   - Der Retriever liefert eine Liste von Treffern inkl. `score` und Metadaten.

3. **Nachbarn filtern / kürzen (optional)**  
   - Optional werden Nachbarn verworfen, wenn:
     - der Score unter einen Schwellwert fällt (`similarity_threshold`),
     - `trust_level` nicht zu gewünschten Werten gehört,
     - `content_type`/`domain` nicht konsistent sind.
   - Zusätzlich werden Nachbartexte für den Prompt begrenzt (z. B. `max_context_chars_per_neighbor`).

4. **Prompt erweitern**  
   - Die Nachbartexte werden als zusätzlicher Kontext in den User-Prompt eingefügt (ohne diese Nachbarn separat zu klassifizieren).

**Provenance bei Retrieval (C)**  
Bei aktivem Retrieval wird die verwendete Nachbarschaft im Output gespeichert:
- `semantic.meta.used_faiss = true`
- `semantic.meta.faiss_neighbors = [{chunk_id, score, doc_id?}, ...]`

Wenn Retrieval deaktiviert ist, bleibt:
- `semantic.meta.used_faiss = false`
- `semantic.meta.faiss_neighbors = []`

**Heuristiken & „Empty“-Markierung (C)**  
Vor und nach dem LLM-Aufruf werden heuristische Regeln angewandt (z. B. Skip rein struktureller Chunks; Unterdrückung zu kurzer Summaries). Diese Regeln werden transparent gemacht über:
- `semantic.meta.mode = structural_rule1_*` (kein LLM-Call)
- `semantic.meta.empty_reasons.summary_short = rule4_suppressed` (Summary bewusst unterdrückt)
- `semantic.meta.empty_reasons.* = llm_empty` (LLM konnte Feld nicht befüllen oder Ergebnis wurde durch Taxonomie-Filterung leer)


## 6.2.3 Ein- und Ausgabeformate

- **Input:** Chunks aus `normalized/json/` (JSON/JSONL, Schema siehe 4.1).  
- **Output:** Angereicherte Chunks mit gefülltem `semantic`-Block unter `semantic/json/`, gleiche `doc_id`/`chunk_id`.

Standardmäßig läuft die semantische Anreicherung ohne Retrieval, d. h. das LLM sieht nur den Ziel-Chunk und ggf. lokale Nachbarn im Dokument.  

Wenn bereits ein FAISS-Kontextindex für den Workspace existiert (siehe 6.5.1), kann die Anreicherung in einem zweiten Lauf mit `use_retrieval_for_semantics = true` betrieben werden. In diesem Fall werden für jeden Chunk Top-k-Nachbarn aus dem Kontextindex geholt und als zusätzlicher Kontext in den Prompt gegeben (siehe 6.2.2).

Der FAISS-Kontextindex selbst wird in der Regel aus den semantisch angereicherten Chunks in `semantic/json/` aufgebaut (siehe 6.5.1). Er steht dann insbesondere für:

- Retrieval-unterstützte semantische Anreicherung in einem zweiten Lauf,  
- Q/A-Kandidaten-Generierung und deren Qualitätssicherung,  
- nachgelagerte RAG-Workflows (z. B. KNIME, interaktive Assistenten)

zur Verfügung.

Zusätzlich gelten folgende Konventionen für Sonderfälle im Output:

- **Nicht-informative / strukturelle Chunks**  
  Chunks, die praktisch keinen fachlichen Inhalt tragen (z. B. einzelne Punkte, reine Abschnittsnummern, Kapitelmarker wie „12.4.2“, reine Tabellen-/Abbildungslabels), werden bereits im Skript vor dem LLM-Aufruf erkannt. Für diese Chunks wird ohne LLM-Call ein minimalistischer `semantic`-Block gesetzt:

  - `language = "unknown"`,
  - `content_type = []`, `domain = []`,
  - `artifact_role = ["structural"]` und ggf. zusätzlich `["heading"]` bzw. `["table"]` abhängig von `meta.has_heading` / `meta.has_table`,
  - `summary_short = ""`,
  - `equations = []`, `key_quantities = []`,
  - `chunk_role = []` (oder `["heading"]` für reine Überschrift-Chunks).

- **Kurztexte / Layoutfragmente**  
  Für Chunks mit sehr kurzem Text (`len(content) < 40`) oder klarer Layout-Funktion (Heading, Table) dürfen `summary_short`, `content_type` und `domain` bewusst leer bleiben, auch wenn andere Chunks desselben Dokuments voll annotiert sind. Das ist eine gewünschte Design-Entscheidung und kein Qualitätsmangel.

## 6.2.4 Heuristiken für strukturelle und schwache Chunks

Um LLM-Kapazität nicht an layoutbedingte Fragmente zu verschwenden und die Statistiken interpretierbar zu halten, wendet `annotate_semantics.py` vor und nach dem LLM-Aufruf eine Reihe einfacher Heuristiken an:

1. **Pre-Filter für „Müll-Chunks“ (kein LLM-Aufruf)**  
   Ein Chunk wird gar nicht erst an das LLM geschickt, sondern direkt minimal annotiert, wenn eine der folgenden Bedingungen erfüllt ist:
   - `len(content.strip()) < 5`, oder
   - `content` besteht nur aus Ziffern, Punkten, Bindestrichen und Leerzeichen (typische Kapitelnummern), oder
   - `content` ist ein einfaches Label wie „Figure 3.1“, „Table 2.4“ usw.

   In diesen Fällen setzt das Skript:
   - `language = "unknown"`,
   - `artifact_role = ["structural"]` (ggf. plus `["heading"]`),
   - alle anderen Listen (inkl. `content_type`, `domain`, `chunk_role`, `key_quantities`, `equations`) leer,
   - `trust_level = "low"`.

2. **Heading-spezifische Kontext-Erweiterung**  
   Für Chunks mit `meta.has_heading = true` und kurzem Text (`len(content) < 80`) wird der LLM-Prompt um den Inhalt der folgenden 1–2 Chunks erweitert („NEIGHBORING CONTEXT“). Dadurch können Überschrift-Chunks sinnvoll mit `domain`, `content_type` und didaktischen Rollen (`chunk_role`) versehen werden, ohne dass der eigentliche Abschnitt in mehrere unabhängige Sinnfragmente zerfällt.

3. **Default-Rollen für strukturelle Chunks**  
   Nach dem LLM-Aufruf ergänzt das Skript `artifact_role` anhand der Metadaten:
   - wenn `meta.has_heading = true` → `artifact_role` enthält mindestens `"heading"`,
   - wenn `meta.has_table = true` → `artifact_role` enthält mindestens `"table"`.

   Bereits vom LLM gesetzte Rollen werden nicht überschrieben, sondern nur ergänzt.

4. **Unterdrückung von `summary_short` bei strukturellen / ultrakurzen Chunks**  
   Für Chunks, die
   - als Heading oder Table markiert sind (`meta.has_heading` / `meta.has_table`), oder
   - nur sehr kurzen Text (`len(content) < 40`) enthalten,

   setzt das Skript `semantic.summary_short` explizit auf den leeren String `""`, selbst wenn das LLM eine Mini-Zusammenfassung geliefert hat. Damit wird verhindert, dass Überschriften, Nummern oder Tabellenfragmente als „Inhalt“ erscheinen.

5. **Konsistente LLM-Regeln für nicht-informative Chunks**  
   Der System-Prompt des LLM enthält zusätzlich die Vorgabe, für klar nicht-informative MAIN CHUNKS (kurzer/leerzeichendominierter Text, nur Zahlen/Interpunktion) leere Taxonomie-Listen, `language = "unknown"`, `trust_level = "low"` und `summary_short = ""` zurückzugeben und keine Semantik zu halluzinieren. In Kombination mit dem Pre-Filter (1) sorgt das für robuste, deterministische Behandlung von Layout-Fragmenten.

## 6.3 Generierung von Q/A-Kandidaten (aktualisiert, FAISS-basiert)

Die Q/A-Kandidaten-Generierung (`scripts/generate_qa_candidates.py`) nutzt semantisch annotierte Chunks aus

```text
semantic/json/
```

und erzeugt daraus erste Frage–Antwort-Paare als **Roh-Kandidaten**, die anschließend durch Filter-/Merge-Schritte bereinigt und zu einem finalen Trainingsdatensatz zusammengeführt werden.

Der Schritt arbeitet strikt **workspace-lokal**:

- Input: `semantic/json/*.jsonl` (oder `.json`)
- Output: `qa_candidates/jsonl/*.jsonl`
- Kontext: globaler Chunk-Kontextindex unter `indices/faiss/` (geladen über `FaissRetriever`)

### 6.3.1 Überblick (Kernidee)

Für jeden geeigneten Anker-Chunk `C`:

1. Kandidatenfilter anwenden (Sprache, Trust-Level, Content-Type, Mindesttextlänge, ggf. Artefaktrollen).
2. Kontextgruppe bilden:
   - lokale Nachbarn im Dokument (vor/nach `C`),
   - semantische Nachbarn über FAISS (k-NN in Chunk-Embedding-Space),
   - Deduplizieren und auf `min_group_size`/`max_group_size` begrenzen.
3. LLM mit der Kontextgruppe prompten und **mehrere** Q/A-Paare erzeugen.
4. Streng als JSON-Array parsen und als JSONL schreiben (resume-fähig pro Eingabedatei).

### 6.3.2 Kontextgruppenbildung (lokal + FAISS)

1) **Lokale Nachbarn**  
Um Dokumentkohärenz zu erhöhen, werden Chunks direkt vor/nach `C` ergänzt (konfigurierbar, z. B. 1 vor + 1 nach).

2) **Semantische Nachbarn über FAISS**  
Der Retriever wird wie folgt genutzt:

```python
neighbors = retriever.get_neighbors_for_chunk(
    chunk_id_or_uid=C["chunk_id"],
    top_k=TOP_K,
    include_self=False,
)
```

Jeder Nachbar enthält u. a.:

- `chunk_id`, optional `chunk_uid`, `doc_id`, `source_path`, `language`,
- kompletten `semantic`-Block (falls in den Metadaten enthalten),
- Convenience-Felder (`trust_level`, `content_type`, `domain`) falls vorhanden,
- `score` (Rohwert aus FAISS `index.search()`).

**Wichtig: Score-Richtung / Metrik**  
Die Interpretation von `score` (Ähnlichkeit vs. Distanz) ist **indexabhängig** und muss aus
`indices/faiss/contextual_config.json` abgeleitet werden (siehe Abschnitt 6.5.3):

- `metric == "IP"` / `IndexFlatIP`: **höher = besser**
- `metric == "L2"` / `IndexFlatL2`: **kleiner = besser**

Filter (Threshold) und Sortierung dürfen daher nicht hardcoded sein.

3) **Nachbarn filtern**  
Beispiele für Filterlogik:

- nur erlaubte Sprachen,
- nur zulässige `trust_level`,
- nur erlaubte `content_type`,
- optional `artifact_role`-Ausschluss (z. B. rein strukturelle Chunks),
- Domain-Overlap (wenn Domain bekannt),
- Score-Threshold (mit korrekter Richtung aus der Index-Metrik),
- Begrenzung auf `max_neighbors` (z. B. 8).

### 6.3.3 LLM-Prompt und Ausgabeformat

Die Prompts werden bevorzugt aus Dateien geladen:

- `config/prompts/qa_generation_system.txt`
- `config/prompts/qa_generation_user.txt`

Falls diese Dateien fehlen, nutzt das Skript interne Defaults.

**Anforderungen an den Default-Prompt (Dataset-Factory-Qualität):**

- Striktes Grounding: nur Information aus den Chunks, keine externen Ergänzungen.
- Skip-Regel: Wenn kein vollständig belegbares Q/A erzeugbar ist, muss das Modell `[]` zurückgeben.
- Diversity: bei mehreren Q/A pro Gruppe keine Near-Duplicates.
- Längenlimits: kurze, trainierbare Q/A (Frage max. ~2 Sätze, Antwort kompakt).
- Output streng maschinenlesbar: JSON-Array, exakt definierte Keys.

**Output-Schema des LLM (Top-Level-Array):**

```json
[
  {"question": "...", "answer": "...", "difficulty": "intermediate"},
  {"question": "...", "answer": "...", "difficulty": "advanced"}
]
```

`generate_qa_candidates.py` extrahiert dieses Array (auch wenn die Antwort „drumherum“ Text enthält), validiert Minimalanforderungen und schreibt pro Element einen Q/A-Kandidaten-Datensatz.

### 6.3.4 Output (JSONL) und Provenance

Pro Zeile in `qa_candidates/jsonl/*.jsonl`:

- `anchor_chunk_id`, `anchor_doc_id`
- `source_chunks` (Chunk-IDs der Kontextgruppe)
- `question`, `answer`, `difficulty`
- zentrale Semantikfelder (z. B. `language`, `content_type`, `domain`, `trust_level`)
- `workspace_file` (Inputdatei)

**ID-Strategie (robust beim Merge):**  
Eindeutige IDs sollten deterministisch aus Inhalt/Anker abgeleitet werden (z. B. `anchor_chunk_id` + Hash über `question+answer`), um Kollisionen bei späterem Merge zu vermeiden.

**Empfohlene Provenance (Debugbarkeit):**  
Optional werden technische Provenance-Daten mitgeschrieben, z. B.:

- FAISS-Metrik (`metric`, `index_type`, `normalized`),
- IDs/Score-Liste der FAISS-Nachbarn (nach Filter),
- lokale Nachbar-IDs,
- Hash der aktiven Config und Prompts,
- LLM-Parameter (Modell, Temperature, `max_tokens`).

Damit lässt sich später nachvollziehen, *warum* ein Sample entstanden ist (und wie man systematisch verbessert).

### 6.3.5 LLM-Backend (Ollama) und Robustheit

Das Skript nutzt standardmäßig das Ollama-Chat-API (`/api/chat`) über HTTP.

- `max_tokens` wird in Ollama über `options.num_predict` begrenzt.
- Für Stabilität werden `max_retries` und `retry_backoff_s` unterstützt (Retry + Exponential Backoff).
- Bei Parse-/HTTP-Fehlern wird das jeweilige Sample übersprungen (Logging).

## 6.3.6 Konfiguration und CLI von `generate_qa_candidates.py` (Pfad-SSOT)

Gesteuert über:

```text
config/qa/qa_generation.default.json
```

**Wichtig (neu): Pfade sind nicht mehr in der QA-Config zu duplizieren.**  
Alle Workspace- und Verzeichnis-Pfade kommen aus:

```text
config/paths/paths.json
```

Die QA-Config referenziert dafür nur noch `paths.paths_file` und enthält ansonsten ausschließlich *Regler* (Filter, Neighbors, Grouping, Sampling, LLM, Runtime, Output).

### Pfadauflösung (aus `paths.json`)

Erwartete Keys in `paths.json`:

- `workspace_root`
- `paths.semantic_json`  → Input für Kandidaten
- `paths.qa_candidates`  → Output der Kandidaten
- `paths.faiss_index` / `paths.faiss_meta` → Kontextindex + Metadaten

Damit ist `config/paths/paths.json` die **Single Source of Truth**, und QA-Config-Drift wird verhindert.

### Relevante Schlüssel (QA-Config)

- `paths`:
  - `paths_file` (Pfad zu `config/paths/paths.json`)
  - `prompt_system_file`, `prompt_user_template_file`
- `filters`:
  - `languages_allowed`, `trust_levels_allowed`, `content_types_allowed`
  - `chunk_roles_allowed` (z. B. `definition`, `explanation`, `example`, …)
- `neighbors`:
  - `top_k_faiss`, `max_neighbors`
  - `similarity_threshold` (Interpretation hängt von Indexmetrik ab)
  - `max_local_neighbors_before`, `max_local_neighbors_after`
- `grouping`:
  - `min_group_size`, `max_group_size`, `max_tokens_context`
- `sampling`:
  - `max_qa_per_group`, `max_groups_per_chunk`, `max_qa_per_document`, `global_qa_limit`
- `llm`:
  - `backend`, `model`, `temperature`, `top_p`, `max_tokens`
  - `request_timeout_s`, `max_retries`, `retry_backoff_s`
- `runtime`:
  - `num_workers`, `shuffle_files`, `resume_mode`, `dry_run`, `log_level`
- `output`:
  - `qa_schema_version`, `include_source_text`, `include_semantic_tags`
  - `output_file_pattern`

### CLI (Beispiele)

Minimal:

```bash
python scripts/generate_qa_candidates.py \
  --config config/qa/qa_generation.default.json
```

Debug (nur wenige Input-Dateien):

```bash
python scripts/generate_qa_candidates.py \
  --config config/qa/qa_generation.default.json \
  --limit-num-files 3 \
  --log-level DEBUG
```

## 6.4 Schritt 6: Qualitätssicherung und Dataset-Build (`qa_candidates/jsonl/ → qa_final/jsonl/`)

**Ziel:** Aus LLM-generierten Kandidaten einen **sauberen, deduplizierten, versionierten Trainingsdatensatz** bauen.

Skript (neu, ersetzt den bisherigen Platzhalter `qa_filter_and_merge.py`):

- `scripts/generate_qa_dataset.py`

Konfiguration (neu):

```text
config/qa/qa_dataset.default.json
```

Pfad-SSOT (wie oben):

```text
config/paths/paths.json
```

### 6.4.1 Input / Output

- **Input:** JSONL-Dateien in `paths.qa_candidates` (aus `paths.json`)
  - pro Zeile ein Kandidat (`dict`)
  - Pflichtfelder: `question`, `answer`
  - optional: `language`, `trust_level`, `content_type`, `domain`, `source_chunks`, `anchor_chunk_id`, `provenance`, …
- **Output:** versioniertes JSONL in `paths.qa_final`
  - z. B. `qa_final_v1.jsonl`, `qa_final_v2.jsonl`, …
  - optional zusätzlich:
    - `qa_rejects_vN.jsonl` (Drop-Gründe)
    - `CHANGELOG.md` (Version-Historie)

### 6.4.2 Kernfunktionen

1. **Robuster JSONL-Load**
   - kaputte Zeilen werden geloggt und übersprungen (kein harter Abbruch).

2. **Heuristische Filter (konfigurierbar)**
   - Pflichtfelder (`question`, `answer`)
   - Längenfilter (min/max chars für Frage/Antwort)
   - Quellenpflicht: `source_chunks` muss existieren und nicht leer sein (optional)
   - Label-Filter (falls im Kandidat vorhanden):
     - `languages_allowed`
     - `trust_levels_allowed`
     - `content_types_allowed`
   - optional: sehr einfache Sprach-Heuristik gegen Label (`drop_if_language_mismatch`)

3. **Dedup (exact)**
   - entfernt Duplikate über `dedup.keys` (typisch: `instruction`+`output`).

4. **Mapping ins Trainingsschema (Instruction-Tuning)**
   - `instruction` ← `question`
   - `input` ← konstanter Wert (default: `""`)
   - `output` ← `answer`
   - zusätzlich Metadaten + Provenance (Auditability)

5. **Versionierung + Changelog**
   - `version=auto` ⇒ nimmt das höchste vorhandene `qa_final_vN.jsonl` und erzeugt `v(N+1)`
   - schreibt pro Release einen Eintrag in `CHANGELOG.md` (kept/read/dropped/dupes + Filtersettings)

### 6.4.3 Output-Schema (pro Zeile)

Jedes Sample ist ein JSON-Objekt mit Kernfeldern:

- `id` (konfigurierbare Strategie)
- `instruction`, `input`, `output`
- `language`, `content_type` (Liste), `domain` (Liste), `trust_level`
- `source_ids` (z. B. `chunk:<chunk_id>`)
- `created_by`, `created_at`, `version`
- `provenance`, `candidate_id`, `anchor_chunk_id`, `anchor_doc_id`, `difficulty`, …

### 6.4.4 ID-Strategie und Resume

**ID-Strategie** (Config: `id.strategy`):

- `sequential` (Default): `ws_00001_q1` (Zero-Pad konfigurierbar)
- `candidate`: übernimmt `candidate_id` wenn vorhanden
- `hash`: SHA1-basierter Kurzhash aus (anchor + instruction + output)

**Resume / Overwrite** (Config: `runtime.resume_mode`):

- `overwrite` (Default): Output neu schreiben
- `append`: an bestehende Datei anhängen
- `resume`: existierende IDs aus Output laden und überspringen

### 6.4.5 CLI (Beispiele)

Minimal:

```bash
python scripts/generate_qa_dataset.py \
  --config config/qa/qa_dataset.default.json
```

Explizite Version + Dry-Run:

```bash
python scripts/generate_qa_dataset.py \
  --config config/qa/qa_dataset.default.json \
  --version v3 \
  --dry-run
```

Debug (limit):

```bash
python scripts/generate_qa_dataset.py \
  --config config/qa/qa_dataset.default.json \
  --limit-num-files 2 \
  --limit-num-examples 200
```

### 6.4.6 Abgrenzung (bewusst)

- Kein LLM-Scoring/„Reranking“ in diesem Schritt.
- Kein FAISS-basiertes Groundedness-Checking (nur Quellen-Presence + optionale Heuristik).
- Dedup aktuell „exact“ (kein fuzzy/semantic dedup).

## 6.5 Aufbau von Vektorindizes (aufgeteilt in Kontext- und RAG-Indizes)

## 6.5.1 Skript `embed_chunks.py` (Kontextindex)

Dieses Skript baut den FAISS-Kontextindex auf und speichert Metadaten und Index-Konfiguration.

**Input / Output**

- **Input:**  
  - Semantisch angereicherte Chunks aus `semantic/json/` (JSON/JSONL, Schema siehe 4.1/4.2).  
- **Output (`indices/faiss/`):**  
  - `contextual.index` – FAISS-Index (`IndexFlatIP` bei normalisierten Embeddings, sonst `IndexFlatL2`).  
  - `contextual_meta.jsonl` – pro Zeile die Metadaten zu einem Vektor mit:
    - `faiss_id` (0-basierte Position im Index),  
    - `doc_id`, `chunk_id`, `source_path`, `source_type`, `language`,  
    - `meta`, `semantic`, ggf. flache Convenience-Felder (`trust_level`, `content_type`, `domain`).  
  - `contextual_config.json` – Konfigurationsdatei mit:
    - `build_timestamp`,  
    - `workspace_root`, `index_path`, `meta_path`,  
    - `index_type` (z. B. `IndexFlatIP` oder `IndexFlatL2`),  
    - `model_name`, `embedding_dim`,  
    - `num_vectors`,  
    - `normalized` (bool),  
    - `device` (z. B. `cuda` oder `cpu`).
    - `metric` (`IP` oder `L2`) – Interpretation der Retrieval-Scores (Ähnlichkeit vs. Distanz).


**Score-Richtung (wichtig für Sortierung / Filtering)**

- Wenn `metric == "IP"` / `index_type == "IndexFlatIP"`:
  - FAISS liefert **Inner Product**. Bei `normalized == true` ist das cosine-ähnliche Ähnlichkeit.
  - **höher = besser** (absteigend sortieren).
- Wenn `metric == "L2"` / `index_type == "IndexFlatL2"`:
  - FAISS liefert **L2-Distanz**.
  - **kleiner = besser** (aufsteigend sortieren).

**Verbindliche Regel:** Downstream-Module dürfen die Sortierreihenfolge nicht hardcoden (z. B. „immer absteigend“), sondern müssen sie aus `indices/faiss/contextual_config.json` ableiten.

**Wichtige CLI-Argumente**

- `--workspace-root` – Wurzel des Workspaces (z. B. `/beegfs/scratch/workspace/es_phdoeble-rag_pipeline`).  
- `--model-name` – Name des Sentence-Transformer-Modells.  
- `--device` – Zielgerät (`cuda`/cpu).  
- `--batch-size` – Batchgröße für die Embedding-Berechnung.  
- `--normalize` – aktiviert L2-Normalisierung der Embeddings und `IndexFlatIP` (Cosine-ähnliche Suche).  
- `--max-chunks` – optionales Limit für die Anzahl der Chunks (Testläufe).  
- `--index-name` – Dateiname des FAISS-Index (Standard: `contextual.index`).  
- `--meta-name` – Dateiname der Meta-JSONL (Standard: `contextual_meta.jsonl`).  
- `--config-name` – Dateiname der Konfig-JSON (Standard: `contextual_config.json`).

**Robustheits-Checks und Logging**

- Das Skript loggt nach `logs/indices/embed_chunks_*.log` und auf STDOUT.  
- Vor dem Index-Bau prüft es u. a.:

  - **Konsistenz Längen:**  
    - Anzahl `texts` == Anzahl `metas` == Anzahl `chunk_ids`.  
    - Anzahl Embeddings (`embeddings.shape[0]`) == Anzahl Metadaten.  
    - Bei Abweichungen: `ERROR`-Log und Abbruch (`return 1`).

  - **doppelte `chunk_id`s:**  
    - Zählt Vorkommen von `chunk_id`.  
    - Bei Duplikaten: `WARNING` mit Anzahl und Beispiel-IDs.  

  - **Embedding-Shape:**  
    - Embeddings müssen 2D sein (N × D); bei Abweichung wird ein `ValueError` geworfen.  
    - Dimension `D` wird im Log und in `contextual_config.json` abgelegt.

- Zusätzlich wird der verwendete Index-Typ (IP vs. L2), die Gesamtzahl der Vektoren und die Pfade der erzeugten Dateien geloggt.


### 6.5.2 Zusätzliche RAG-Indizes (optional)

Neben dem globalen Kontextindex können weitere spezialisierte Indizes aufgebaut werden, z. B.:

- Index nur über Chunks aus bestimmten Quellen (`source_type`, `doc_id`-Whitelist).  
- Index nur über „vertrauenswürdige“ Chunks (z. B. Normen, Lehrbücher).  
- Index auf Dokumentebene (Aggregat-Embeddings pro Dokument oder Kapitel).

Ein generisches Skript (Platzhalter: `embed_chunks.py`) kann auf Basis von:

- `semantic/json/`  
- oder bereits produzierten `qa_final/jsonl/`

solche Indizes aufbauen. Dabei können Embeddings wiederverwendet werden (z. B. Einlesen aus `contextual_meta.jsonl` + Subset-Selektion), um Rechenzeit zu sparen.

---

### 6.5.3 Retrieval-API auf FAISS-Basis (`faiss_retriever.py`)

Der Kontextindex aus 6.5.1 wird für Semantik (6.2) und Q/A (6.3) über ein zentrales Helfermodul angebunden:

- Modul/Skript: `scripts/faiss_retriever.py`
- Kernklasse: `FaissRetriever`

**Aufgaben von `FaissRetriever`:**

- Laden des Kontextindex aus einem Workspace:
  - `indices/faiss/contextual.index`,
  - `indices/faiss/contextual_meta.jsonl`,
  - optional: `indices/faiss/contextual_config.json` (Index-Typ / Metrik / Normalisierung).
- Aufbau einer Map `chunk_id → faiss_id` (und optional `chunk_uid → faiss_id`) aus den Metadaten.
- Konsistenzprüfung:
  - Anzahl Metadatensätze == `index.ntotal`.
- Bereitstellen von Methoden für:
  - Lookup der Indexposition (`faiss_id`) zu einer gegebenen `chunk_id` / `chunk_uid`,
  - Rekonstruktion einzelner Vektoren (für FLAT-Indizes),
  - k-NN-Suche in „Chunk-Space“ für einen gegebenen Chunk.

**Zentrales API (Python):**

```python
from scripts.faiss_retriever import FaissRetriever

retriever = FaissRetriever(workspace_root="/beegfs/scratch/workspace/es_phdoeble-rag_pipeline")

# 1) faiss_id zu chunk_id
faiss_id = retriever.get_faiss_id_for_chunk("some_chunk_id")

# 2) Vektor rekonstruieren (FLAT-Index)
vec = retriever.reconstruct_vector(faiss_id)  # Shape: (1, dim)

# 3) Nachbarn für einen Chunk holen
neighbors = retriever.get_neighbors_for_chunk(
    chunk_id_or_uid="some_chunk_id",
    top_k=5,
    include_self=False,
)
```

Jeder Eintrag in `neighbors` ist ein Dict mit:

- `faiss_id` – Indexposition im FAISS-Index,
- `score` – Distanz oder Ähnlichkeit (abhängig vom Index-Typ),
- Metadaten aus `contextual_meta.jsonl` (z. B. `chunk_id`, `chunk_uid`, `doc_id`, `source_path`, `source_type`, `language`, `meta`, `semantic`),
- optional flache Convenience-Felder (`trust_level`, `content_type`, `domain`), falls in `contextual_meta.jsonl` vorhanden.

#### Score-Semantik und Sortierung

- `FaissRetriever` gibt den von FAISS `index.search()` gelieferten Wert **roh** als `score` zurück (keine Transformation wie `-distance`, `1-distance`, …).
- Interpretation hängt ausschließlich vom Index-Typ ab (Quelle: `indices/faiss/contextual_config.json`):
  - `IndexFlatIP` / `metric == "IP"`: `score` ist **Ähnlichkeit (Inner Product)** ⇒ **höher = besser**.
  - `IndexFlatL2` / `metric == "L2"`: `score` ist **Distanz (L2)** ⇒ **kleiner = besser**.
- Jede Komponente, die Nachbarn sortiert/filtern will (z. B. `generate_qa_candidates.py: filter_faiss_neighbors()`), muss die Richtung aus `contextual_config.json` ableiten und darf sie nicht hardcoden.

#### Verifizierte Erkenntnis im aktuellen Workspace (es_phdoeble-rag_pipeline)

Im Workspace `/beegfs/scratch/workspace/es_phdoeble-rag_pipeline` ist der Index wie folgt gebaut:

- `metric`: `IP`
- `normalized`: `true`
- `index_type`: `IndexFlatIP`

Konsequenz:

- `score` ist Similarity (Inner Product auf normalisierten Vektoren, praktisch cosine-ähnlich) ⇒ **höher = besser**.
- Absteigende Sortierung und ein Filter der Form `if score < similarity_threshold: skip` sind für diesen Workspace korrekt.
- Trotzdem bleibt die Anforderung bestehen, die Richtung immer aus `contextual_config.json` zu lesen, um Index-Wechsel (IP ↔ L2) sicher zu unterstützen.

**Backward-Kompatibilität:**

- Ältere Indizes, deren Meta-Datei noch `vector_id` statt `faiss_id` enthält, werden weiterhin unterstützt:
  - `FaissRetriever` liest `faiss_id` **oder** `vector_id` und behandelt beide als Indexposition.

**CLI-Testmodus:**

```bash
python scripts/faiss_retriever.py   --workspace-root /beegfs/scratch/workspace/es_phdoeble-rag_pipeline   --chunk-id SOME_CHUNK_ID_OR_UID   --top-k 5
```

Ausgabe (Beispiel, pro Treffer eine Zeile):

- Score (Distanz/Ähnlichkeit),
- `faiss_id`,
- `doc_id`,
- `chunk_id` / `chunk_uid`,
- `source_path`.

**Nutzung in anderen Modulen:**

- `annotate_semantics.py`:
  - nutzt `FaissRetriever.get_neighbors_for_chunk(...)`, um Retrieval-Kontext für die semantische Anreicherung zu holen.
- `generate_qa_candidates.py`:
  - nutzt denselben Retriever für die Bildung semantischer Kontextgruppen (ähnliche Chunks + lokale Nachbarn).
- Optionale weitere Komponenten können ebenfalls über `FaissRetriever` auf den Kontextindex zugreifen, ohne selbst FAISS- und Meta-Handling implementieren zu müssen.

## 6.6 (optional) Labelpropagation & Nachbarschafts-Konsistenz

Dieser Abschnitt ist optional, beschreibt aber sinnvolle FAISS-basierte Erweiterungen.

### 6.6.1 Labelpropagation

Nach der ersten semantischen Anreicherung können über den Kontextindex einfache *Labelpropagation*-Strategien umgesetzt werden:

- Für jeden Chunk:
  - Hole Top-k Nachbarn aus dem Kontextindex.  
  - Betrachte z. B. deren `semantic.chunk_role` und `semantic.content_type`.  
- Wenn ein Chunk kein Label hat, aber ≥80 % seiner Nachbarn ein konsistentes Label tragen, kann dieses Label vorgeschlagen oder automatisch übernommen werden.  
- Falls ein Chunk ein Label hat, seine Nachbarn aber überwiegend ein anderes Label tragen, kann er als **inkonsistent** markiert werden (Flag für manuelle Prüfung).

Implementierbar als separates Skript, z. B.:

```text
scripts/label_propagation.py
```

### 6.6.2 QA-Konsistenz-Check über Nachbarschaft

Für generierte Q/A-Kandidaten kann der Kontextindex ebenfalls zur **Qualitätssicherung** eingesetzt werden:

- Zu jeder Frage–Antwort-Kombination sind die verwendeten `source_chunks` bekannt.  
- Über den Kontextindex lassen sich weitere Nachbarn dieser Chunks finden.  
- Ein LLM- oder regelbasierter Check kann prüfen, ob die Antwort tatsächlich im Umfeld dieser Chunks verankert ist (Groundedness).  
- Q/A-Paare, die sich durch keinen der Nachbarn stützen lassen, können verworfen oder zur manuellen Prüfung flaggen.

Ein solches Skript könnte z. B. `scripts/qa_consistency_filter.py` heißen und zwischen `qa_candidates/jsonl/` und `qa_final/jsonl/` laufen.

---

## 7. Tool- und Ressourcenwahl

### 7.1 Programmiersprachen und Frameworks

- **Python**:
  - zentrale Sprache für alle Pipeline-Skripte.
  - Nutzung üblicher Bibliotheken für Parsing, JSON-Verarbeitung, LLM-Anbindung.

- **KNIME**:
  - Aufbau von RAG-Workflows,
  - Verbindung zu Datenbanken,
  - Integration mit Vektorindices (FAISS/Chroma),
  - optional Triggern von DACHS-Pipeline-Schritten (z. B. per SSH).

- **LLM-Frameworks**:
  - je nach Auswahl der Basismodelle (Transformers, PEFT, TRL usw.).

### 7.2 Modell-Serving und -Nutzung auf DACHS

- Nutzung der auf dem Cluster verfügbaren LLM-Infrastruktur (z. B. Ollama-Module, eigene Inferenzserver).
- Aufruf der Modelle:
  - innerhalb von SLURM-Jobs (Batch),
  - oder interaktiv (z. B. für Entwicklung und Tests).

### 7.3 Speicher- und Dateisysteme

- `ws_*`-Workspaces als primäre Speicherorte für Projekt- und Trainingsdaten.
- `$TMPDIR` bzw. `/localscratch` für temporäre Dateien während rechenintensiver Jobs.
- `$HOME` nur für Skripte, Konfigurationen und kleine Ergebnisse.

### 7.4 Umgebungen

- Nutzung von Environment Modules und/oder Conda-Umgebungen für reproduzierbare Laufzeitumgebungen.
- Dokumentation der Abhängigkeiten (z. B. `requirements.txt`, `environment.yml`) je Pipeline-Stufe.

## 7.5 Konfiguration & Jobs (Ergänzungen)

### 7.5.1 Embedding-Konfiguration

Neue Konfigurationsdatei (Beispiel):

```text
config/pipeline/embeddings.json
```

mit u. a.:

```json
{
  "model_name": "sentence-transformers/all-mpnet-base-v2",
  "batch_size": 64,
  "device": "cuda",
  "normalize_embeddings": true,
  "index_name": "contextual.index",
  "meta_name": "contextual_meta.jsonl"
}
```

### 7.5.2 SLURM-Job für Embeddings

Jobskript:

```text
jobs/embed_chunks.slurm
```

- liest `workspace_root` aus `config/paths/paths.json`,  
- sorgt dafür, dass `indices/faiss/` und `logs/indices/` existieren,  
- ruft `scripts/embed_chunks.py` mit der gewünschten Konfiguration auf (z. B. `--normalize`, optional `--max-chunks` für Tests).

Dieses Jobskript lässt sich bei Bedarf später erweitern (z. B. um einen CPU-only-Modus oder andere Embedding-Modelle).

---

## 8. Qualitäts- und Evaluationskonzept

### 8.1 Automatische Qualitätsmetriken für Q/A-Daten

- Statistiken:
  - Anzahl Q/A-Beispiele je Workspace, content_type, domain, artifact_role, trust_level.
  - Verteilung nach Sprache (`de`, `en`, `mixed`).
- Checks:
  - Länge von `instruction`, `input`, `output`.
  - Anteil der Daten mit `trust_level = high`.

### 8.2 Modellevaluation

- Nutzung eines Teils der automatisch generierten Beispiele als Validierung.
- Später: Aufbau eines „Gold-Subsets“ mit manuell geprüften Q/A-Beispielen für:
  - Auslegung von Kühlsystemen,
  - GT-Power,
  - KNIME/Python-Skripting,
  - Datenbank-/Infrastrukturkommunikation,
  - Entwicklungsprozesse und Datenkorrelation.

### 8.3 Fehlerklassen und Feedback-Loop

- Typische Fehlerklassen:
  - physikalisch falsche Aussagen (z. B. Energiesaldo, Einheiten),
  - falsche Nutzung von GT-Power-APIs oder KNIME-Nodes,
  - falsche Schlussfolgerungen aus Messdaten,
  - Missverständnisse in Prozessabläufen.
- Mechanismen:
  - Logging auffälliger Antworten,
  - Nachjustieren der Q/A-Generierung und der Filterlogik,
  - gezielte Ergänzung neuer Trainingsbeispiele.

---

## 9. Sicherheits-, Datenschutz- und Governance-Aspekte

### 9.1 Datenklassen

- Klassifikation der Eingangs- und Trainingsdaten nach internen Richtlinien (z. B. vertraulich, intern, öffentlich).
- Dokumentation, welche Daten in welchen Workspaces liegen.

### 9.2 Zugriffskontrolle

- Nutzung von UNIX-Rechten/ACLs pro Workspace.
- Rechtevergabe nach Rollen (z. B. nur bestimmte Gruppen dürfen Trainingsdaten/Modelle verändern).

### 9.3 Kein externer Datenabfluss

- Keine Nutzung externer KI-APIs innerhalb der Projektpipelines.
- Keine Übertragung der Trainingsdaten oder Modelle außerhalb der internen Umgebung ohne explizite Freigabe.

### 9.4 Protokollierung und Nachvollziehbarkeit

- Pro Pipeline-Schritt Logging:
  - welche Rohdaten sind eingeflossen,
  - welche Q/A-Beispiele wurden generiert,
  - welche Versionen gelangten in welche Trainingsläufe.
- Ablage der Logs im jeweiligen `logs/`-Unterordner.

---

## 10. Betriebs- und Wartungskonzept

### 10.1 Regelmäßige Rebuilds der RAG-Indices

- Definition von Triggers:
  - neue Dokumente in `raw/`,
  - aktualisierte Normen/Reports,
  - geänderte semantische Annotationen.
- SLURM-Jobs zum Neuaufbau der Indizes in `indices/`.

### 10.2 Pflege der Q/A-Datensätze

- Versionierung der `qa_final`-Dateien.
- Umgang mit veralteten oder fehlerhaften Beispielen:
  - Markierung als deprecated oder Entfernung in neuen Versionen.
- Dokumentation der Änderungen in `CHANGELOG.md`.

### 10.3 Erweiterung auf neue Themen und Modelle

- Vorgehen beim Hinzufügen neuer Workspaces:
  - Anlegen des Workspaces,
  - Kopieren der Standard-Ordnerstruktur,
  - Anpassen der Konfiguration (z. B. Tags, Domains).
- Nutzung des zentralen Q/A-Schemas für zusätzliche Modelle (größer, multimodal usw.).

### 10.4 Monitoring und Ressourcennutzung

- Überwachung der GPU-Nutzung und Workspace-Quotas.
- Anpassung der Jobgrößen (Laufzeit, Speicherkontingent) an die tatsächliche Nutzung.

---

## 11. Roadmap und nächste Schritte

### 11.1 MVP (Minimal Viable Pipeline)

- Auswahl eines Pilot-Workspaces (z. B. `Thermodynamics_Textbooks`).
- End-to-End-Aufbau:
  - Ingestion ⇒ Normalisierung ⇒ Semantik ⇒ Q/A-Kandidaten ⇒ Q/A-Final ⇒ einfacher Fine-Tune.

### 11.2 Erweiterung auf andere Workspaces

- Übertrag des MVP-Prozesses auf:
  - `GT_Power_Models`,
  - `Test_Driving_Reports`,
  - `Laboratory_Measurements`,
  - `Management_Strategy`.

### 11.3 Einführung manueller Q/A-Kurierung

- Aufbau eines kleinen Gold-Subsets (100–300 Beispiele) mit manuell geprüften Antworten.
- Nutzung als Referenz für Evaluierung und späteres Feintuning.

### 11.4 Vorbereitung auf zukünftige Modelle

- Sicherstellen, dass:
  - das Trainingsschema stabil bleibt,
  - alle relevanten Metadaten gepflegt werden,
  - Modellwechsel (neue LLM-Generationen) ohne großes Re-Engineering möglich sind.

---

## 12. Glossar und Referenzen

### 12.1 Glossar (Beispiele)

- **DACHS**: gemeinsamer Datenanalyse-Cluster der Hochschulen in Baden-Württemberg.
- **Workspace (ws_*)**: temporärer Speicherbereich auf dem Cluster für projektspezifische Daten.
- **RAG (Retrieval-Augmented Generation)**: Kombination aus Dokumentensuche und LLM-Antworterzeugung.
- **Instruction-Tuning**: Feinabstimmung eines LLM mit Frage–Antwort-Beispielen.
- **Q/A-Datensatz**: strukturierte Sammlung von Frage–Antwort-Paaren (mit Kontext und Metadaten) zur Modellanpassung.
- **FAISS/Chroma**: Vektor-Datenbanken zur effizienten Ähnlichkeitssuche über Embeddings.

### 12.2 Referenzen

- interne DACHS-/bwHPC-Dokumentation,
- interne Richtlinien zu Datenschutz, Informationssicherheit und Modellnutzung,
- Dokumentation der verwendeten Open-Source-Modelle und -Frameworks.
