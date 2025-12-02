# Using the Datenanalysis Cluster der HAWen (DACHS) – Teil 2

Zusammenfassung der Folien 18–44 der Präsentation **„Using the Datenanalysis Cluster der HAWen (DACHS) – HPC @ HAW, 14.03.2025“**.

---

## Folie 18 – First steps using Linux

- Kapitel-Überschrift.
- Einleitung in die ersten Schritte mit Linux auf DACHS:
  - Arbeiten auf der Kommandozeile.
  - Nutzung der Bash-Shell.
  - Basis für späteres Arbeiten mit SLURM, Workspaces und Ollama.

---

## Folie 19 – Bash (Grundlagen)

- **Thema:** Interaktive Arbeit mit der *Bourne Again Shell* (Bash).
- Kommandos werden nach dem Prompt `$` eingegeben; `#` leitet Kommentare ein.

**Typische Befehle:**

```bash
cd ./directory       # Verzeichnis wechseln
ls -la               # Dateien anzeigen (-l = long, -a = all inkl. versteckter Dateien)
NAME="Peter"         # Variable NAME setzen
echo "Hi $NAME"      # Ausgabe: Hi Peter
./program arg1 arg2 arg3
sbatch your_job.sh   # SLURM-Jobskript einreichen
```

- Dokumentation steht in den Manual Pages zur Verfügung:

```bash
man ls           # Hilfe zu 'ls'
man -k printf    # Suche in Manpages nach Stichwort 'printf'
```

---

## Folie 20 – Bash (Umgebungsvariablen und Aliases)

- **Umgebungsvariablen** werden in der Shell gesetzt und an Unterprozesse weitergegeben.
- Alle aktuellen Umgebungsvariablen anzeigen:

```bash
env
```

- Neue Umgebungsvariable setzen:

```bash
export NAME="Peter"
```

- **Aliases / Shortcuts** definieren:

```bash
alias ll='ls -l'   # 'll' führt jetzt 'ls -l' aus
```

- **Spezielle Variable:**

```bash
echo $?            # Rückgabecode des letzten Kommandos anzeigen
```

- Hinweis: Viele weitere Spezialvariablen und Funktionen sind in `man bash` beschrieben.

---

## Folie 21 – Linux Hierarchical File System

- Darstellung des hierarchischen Unix-Dateisystems auf DACHS, beginnend bei `/` als Wurzel.
- Wichtige Verzeichnisse und ihre Funktion:

```text
/                     # Root des Dateisystems
├── beegfs            # Paralleles Dateisystem
│   ├── bwhpc
│   │   └── common
│   └── scratch
│       └── workspace
├── bin -> usr/bin    # Ausführbare Programme (Symlink)
├── etc               # Konfigurationsdateien
├── home              # Home-Verzeichnisse der Nutzer
│   ├── aa            # nach Organisation/HS gruppiert
│   ├── as
│   ├── es
│   └── of
├── localscratch      # Knoten-lokaler Scratch (~1 TB pro Compute-Node)
├── opt               # Zusätzlich installierte Software
├── tmp               # Temporäre Dateien/Verzeichnisse
└── usr               # Userland: Libraries, Binaries, Doku
```

- **Wesentliche Punkte:**
  - Benutzer arbeiten primär in ihrem Home-Verzeichnis unter `/home/<org>/<account>`.
  - Für performante I/O-Workloads stehen `/beegfs/...` (Workspaces) und `/localscratch/...` zur Verfügung.
  - Systemsoftware und Konfiguration liegen in `/usr`, `/bin`, `/opt`, `/etc`.

---

## Folie 22 – Bash (Kapiteltrenner)

- Titel-Folie „Bash“ als Übergang zwischen Basisbefehlen und weiteren Datei- und Moduloperationen.

---

## Folie 23 – Bash (Dateioperationen, Module, E‑Learning)

**Weitere Dateioperationen:**

```bash
chmod 700 test.sh     # Lese-/Schreib-/Ausführ-Rechte (rwx) nur für Besitzer
rm test.sh            # Datei löschen
mkdir directory-name  # Verzeichnis anlegen
```

- Rechtekodierung:
  - `read = 4`, `write = 2`, `execute = 1`.
  - Kombination zu z.B. `7 = 4+2+1` (rwx).

**Symbolische Links (Softlinks) erstellen:**

```bash
ln -s target/file/path linkname
```

**Software-Module (Environment Modules):**

```bash
module avail               # Verfügbare Software-Module anzeigen
module load compiler/gnu   # Aktuellen GCC-Compiler laden
module list                # Geladene Module anzeigen
```

**Weiterführendes Lernmaterial:**

- E‑Learning-Modul „Linux Basics“:
  - URL: <https://training.bwhpc.de/ilias.php?baseClass=illmpresentationgui&cmd=resume&ref_id=310>

---

## Folie 24 – SLURM Queueing System

- Kapitel-Überschrift.
- Überleitung von den ersten Linux-Schritten zu SLURM als Batch- und Ressourcensystem auf DACHS.

---

## Folie 25 – SLURM: Overview Queuing System

- Beim Login arbeiten Nutzer auf **Login-Nodes**, dort sind erlaubt:
  - Vorbereitung: Editieren, Programmieren, Datentransfer.
  - Kompilieren der eigenen Anwendungen.
  - Anlegen von Workspaces und Kopieren von Dateien.
- Auf Login-Nodes **nicht erlaubt**:
  - Länger laufende Jobs mit hoher CPU- und RAM-Nutzung.

- Für die faire Nutzung der Compute-Nodes wird **SLURM** als Batch-Scheduler eingesetzt.

**Ziele von SLURM:**

- Faire Ressourcenverteilung (Accounting pro Partnerorganisation).
- **Korrekte Ressourcenallokation** – man bekommt genau das, was man anfordert:
  - Exklusive Nutzung der 1‑GPU-Knoten mit NVIDIA L40S.
  - Geeignete Shared-Nutzung der 4‑Socket-APU- und 8‑GPU-Server.
  - Nur die tatsächlich angeforderte Menge an Speicher und generischen Ressourcen.

- SLURM-Kommandos beginnen typischerweise mit `s...` (z.B. `srun`, `sbatch`, `squeue`).
- Nach einem ersten `srun`-Aufruf lassen sich SLURM-Variablen prüfen, z. B.:

```bash
echo $SLURM_JOBID
```

- Kommentar auf der Folie: Auch aggressives Parallel-Build (`make -j 48`) ist auf Compute-Nodes in Ordnung.

---

## Folie 26 – SLURM: Resource Allocation (Interaktive Jobs)

- Es existieren drei **SLURM-Partitionen** für unterschiedliche GPU-Hardware:

  - `gpu1` – Knoten mit **1× NVIDIA L40S**.
  - `gpu4` – Anteile des 4× AMD MI300A APU-Knotens.
  - `gpu8` – Anteile des 8× NVIDIA H100-Servers.

- Interaktives Arbeiten auf einem GPU-Knoten (Beispiel, ein Prozess, eine GPU):

```bash
srun --partition=gpu1 --gres=gpu:1 --pty /bin/bash
```

**Bedeutung der Optionen:**

- `--partition=gpu1` (`-p gpu1`): Auswahl der Partition und damit eines passenden Knotens.
- `--gres=gpu:1`: Anforderung einer „Generic Resource“ – hier **1 GPU**; ohne diese Option läuft der Prozess nur auf CPUs.
  - Verfügbarkeit der GPU kann mit `nvidia-smi` (NVIDIA) oder `rocm-smi` (AMD) geprüft werden.
- `--pty /bin/bash`: Startet eine interaktive Bash-Shell:
  - Standardausgabe und -fehler des ersten Prozesses werden ins aktuelle Terminal geleitet.
  - Von dort können weitere Programme gestartet werden.

- SLURM bindet den erzeugten UNIX-Prozess an einen CPU-Core und setzt Speicherlimits entsprechend der Standardkonfiguration.

---

## Folie 27 – SLURM: Batch Processes

- Hauptvorteile von **Batch-Skripten** gegenüber rein interaktivem Arbeiten:

  - Bessere Planbarkeit im Gesamtsystem (Scheduler kann Jobs passend einreihen).
  - **Reproduzierbarkeit** von Berechnungen und Ergebnissen über Skripte.
  - Laufende Verbesserung der Skripte; SLURM-Logs enthalten wertvolle Metadaten.

**Beispiel-Skript `run.slurm` (für die `gpu8`-Partition):**

```bash
#!/bin/bash
#SBATCH --partition=gpu8
#SBATCH --gres=gpu:h100:8
#SBATCH --time=2:0:0
#SBATCH --nodes=1
#SBATCH --ntasks=96
#SBATCH --mem=1400G
#SBATCH --output=run%j.out

# Start processes/threads
```

**Erklärung der Direktiven:**

- `#!/bin/bash` – Shebang: Skript soll mit Bash interpretiert werden.
- `--partition=gpu8`: Job läuft auf einem der 8‑GPU-H100-Knoten.
- `--gres=gpu:h100:8`: Anforderung von **8 GPUs** vom Typ H100.
- `--time=2:0:0`: Maximale Laufzeit 2 Stunden (wichtig für Scheduling).
- `--nodes=1`: Ein ganzer Knoten.
- `--ntasks=96`: 96 Tasks (entspricht allen CPU-Cores auf diesem Knoten, 2×48).
- `--mem=1400G`: 1,4 TB Hauptspeicher.
- `--output=run%j.out`: Standardausgabe in Datei mit Job-ID (`%j`).

- Jobstart via:

```bash
sbatch run.slurm
```

- Beispielskript (für `gpu1`) ist online verfügbar:
  - Download-Link: <https://www2.hs-esslingen.de/~rakeller/run_example.slurm>
  - Alternativ direkt kopieren: `cp /tmp/run_example.slurm ~/`

---

## Folie 28 – SLURM: More Information

- Ein **Job** in SLURM kann aus mehreren **Job Steps** bestehen:
  - Einreichen via `sbatch`, Start von Steps im Job via `srun`.
- Ein **Job Step**:
  - Kann eigene Ressourcenanforderungen haben (z. B. eigene Anzahl Tasks).
- **Tasks** sind die eigentlichen Ausführungseinheiten:
  - Einzelne Prozesse (z. B. MPI-Ranks) oder Threads.

- SLURM erlaubt sehr genaue Kontrolle der Ressourcen:
  - Verteilung von Tasks auf Kerne und Nodes.
  - Bindung von Prozessen/Threads an physische Kerne (CPU-Binding).

**Nützliche Kommandos:**

- `squeue` – Überblick über laufende/queued Jobs (standardmäßig eigene Jobs).
- `sinfo_t_idle` – Zeigt freie (idle) Knoten pro Partition an (ähnlich wie auf bwUniCluster).

**Debug-Information im Beispielskript:**

- `free` – Zeigt verfügbare und belegte Speicherarten auf dem Knoten.
- `ulimit -a` – Übersicht über Ressourcenlimits (z. B. maximal nutzbarer Speicher).
- `module list` – Liste der aktuellen Software-Module.
- `env` – Alle Umgebungsvariablen (besonders interessant: `SLURM_*`).
- `ibstat` – Status des InfiniBand-Links (z. B. Erkennen von Link-Problemen).

---

## Folie 29 – SLURM: Multi-node Jobs / MPI

**Vorbereitung eines MPI-Jobs:**

```bash
cp /tmp/mpi_stub.c $HOME/
cp /tmp/mpi_stub.slurm $HOME/
module load mpi/openmpi
mpicc -Wall -O2 -o mpi_stub mpi_stub.c
```

- Anschließend kann:
  - Der MPI-Prozess direkt per `srun` gestartet werden:

    ```bash
    srun --mpi=pmix --nodes=2 --ntasks-per-node=48 ./mpi_stub
    ```

  - Oder das SLURM-Skript per `sbatch` eingereicht werden:

    ```bash
    sbatch mpi_stub.slurm
    ```

**Beispiel `mpi_stub.slurm`:**

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=48
#SBATCH --time=1
#SBATCH --mail-user=me@i.de

module load mpi/openmpi
mpirun ~/mpi_stub
```

**Bedeutung:**

- `--nodes=2`: Zwei Knoten (Partition egal, sofern passend).
- `--ntasks-per-node=48`: Je 48 Tasks pro Knoten (alle Kerne der `gpu1`-Knoten).
- `--time=1`: Laufzeit 1 Minute (Format: Stunden, wenn ohne `:` angegeben).
- `--mail-user=...`: SLURM sendet Mail bei Start, Fehler, Ende.
- `module load mpi/openmpi`: Gleiche MPI-Version wie beim Kompilieren laden.
- `mpirun ~/mpi_stub`: MPI startet die parallelen Prozesse; SLURM stellt Hostliste etc. bereit.

---

## Folie 30 – SLURM: Multi-node Jobs / MPI + OpenMP

- Beispiel für **Hybrid-Parallele** Jobs (MPI + OpenMP, oft „MPI+X“ genannt).

**Vorbereitung:**

```bash
cp /tmp/mpi_openmp.c $HOME/
cp /tmp/mpi_openmp.slurm $HOME/
module load mpi/openmpi
mpicc -Wall -O2 -fopenmp -o mpi_openmp mpi_openmp.c
```

- Einreichen:

```bash
sbatch mpi_openmp.slurm
```

**Beispiel `mpi_openmp.slurm`:**

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --sockets-per-node=2
#SBATCH --cores-per-socket=24
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=24

module load mpi/openmpi
export OMP_NUM_THREADS=24
mpirun -np 4 ~/mpi_openmp
```

**Interpretation:**

- `--nodes=2`: Zwei Knoten.
- `--sockets-per-node=2`: Auswahl von Knoten mit 2 CPU-Sockets.
- `--cores-per-socket=24`: Auswahl von Knoten mit 24 Cores pro Socket (insgesamt 48 Cores/Knoten).
- `--ntasks-per-node=2`: Pro Knoten zwei MPI-Tasks.
- `--cpus-per-task=24`: Jeder Task bekommt 24 CPU-Cores → ideal für 24 OpenMP-Threads.
- `OMP_NUM_THREADS=24`: Anzahl Threads pro Task wird auf 24 gesetzt.
- `mpirun -np 4`: Insgesamt 4 MPI-Prozesse (2 Knoten × 2 Tasks/Knoten).

---

## Folie 31 – SLURM: Advanced Options

- SLURM bietet weitere Features für komplexe Szenarien:

**Mögliche Anfragen:**

- **Lizenzen** (z. B. ANSYS), um Software-Lizenzkontingente über SLURM zu steuern.
- Nutzung unterschiedlicher **Accounts** (z. B. Industrieprojekte) – Einrichtung via Admins.
- **Reservierungen** für Lehrveranstaltungen:
  - z. B. 8 Knoten für einen bestimmten Zeitraum.

- Unterstützung von **Jobketten** (Job-Dependencies).

**CPU-Verteilung und Binding:**

- Gute Performance erfordert sinnvolle Verteilung und Bindung von Tasks/Threads:

  - Standard auf Multi-Core/-Thread-Systemen ist äquivalent zu:
    - `-m block:cyclic` mit `--cpu-bind=thread`.

- Beispiele:

```bash
--cpu-bind=socket   # sinnvoll für MPI+OpenMP (Tasks auf Sockets verteilen)
--cpu-bind=verbose  # Diagnoseausgabe zur aktuellen Bindung
```

**Weitere nützliche Kommandos:**

- `scontrol show job` – detaillierte Infos zum Job (Ressourcen, Nodes, Status).
- `squeue --start` – prognostiziert voraussichtlich geplanten Startzeitpunkt eines Jobs.

---

## Folie 32 – Work Spaces and LocalScratch

- Kapitel-Überschrift.
- Überleitung zu Workspaces auf BeeGFS und zum lokalen Scratch-Speicher der Compute-Nodes.

---

## Folie 33 – Workspace Tools (Grundlagen)

- Workspaces liegen auf dem parallelen BeeGFS-Dateisystem.
- **Standard-Laufzeit:** 30 Tage (verlängerbar bis 90 Tage).

**Basis-Kommandos:**

- Workspace anlegen:

```bash
ws_allocate <name> <days>
```

- Workspace verlängern:

```bash
ws_extend <name> <days>
```

- Workspace löschen:

```bash
ws_release <name>
```

- Pfad zu einem Workspace ermitteln:

```bash
ws_find <name>
# Beispielausgabe:
# /beegfs/scratch/workspace/xx_use-test_workspace
```

- Alle eigenen Workspaces auflisten:

```bash
ws_list
```

---

## Folie 34 – Workspace Tools (Ablauf & Wiederherstellung)

- **E-Mail-Erinnerungen:**

  - Eine Woche vor Ablauf eines Workspaces wird eine Erinnerung per E-Mail verschickt.
  - Nach Ablauf bleibt der Workspace weitere **14 Tage** im „Grace“-Zustand erhalten.

- Wiederherstellung abgelaufener Workspaces mit `ws_restore`:

```bash
ws_restore -l            # Liste der wiederherstellbaren Workspaces
ws_allocate new-ws       # neuen Workspace anlegen
ws_restore <old> new-ws  # abgelaufenen Workspace unter neuem Namen wiederherstellen
```

- Weitere Beispiele und Details finden sich im User Guide:
  - <https://github.com/holgerBerger/hpc-workspace/blob/master/user-guide.md>

---

## Folie 35 – Local Scratch

- Jeder Compute-Node besitzt etwa **1 TB NVMe-SSD** als lokalen Scratch-Speicher.
- Dieser ist für user-spezifische Jobs verfügbar.
- XFS-Dateisystem, gemountet unter:

```text
/localscratch/tmpdir.${SLURM_JOB_ID}
```

- Empfehlung:
  - Für Jobs mit **vielen I/O-Operationen** oder **zahlreichen kleinen Dateien** eignet sich Local Scratch besonders gut.
  - Typische Workflows: Daten aus Workspace/Home auf Local Scratch kopieren, dort arbeiten, Ergebnisse zurückschreiben.

**Beispiele:**

- Verzeichnis aus `$HOME` rekursiv nach Local Scratch kopieren:

```bash
cp -r $HOME/dir /localscratch/tmpdir.${SLURM_JOB_ID}
```

- ZIP-Datei aus einem Workspace in Local Scratch entpacken (zweizeilig):

```bash
unzip `ws_find my_workspace`/file.zip \
  -d /localscratch/tmpdir.${SLURM_JOB_ID}
```

---

## Folie 36 – Best practices using Ollama

- Kapitel-Überschrift.
- Einführung in Best Practices beim Einsatz von **Ollama** (LLM-Server basierend auf `llama.cpp`) auf DACHS.

---

## Folie 37 – Ollama: Preparations

- **Ollama**:
  - Frontend/Server für verschiedene LLMs (auf Basis von `llama.cpp`).
  - Unterstützt mehrere Modelle parallel; kann CPU und GPU nutzen.

- Achtung: Modelle können sehr groß sein (Beispiel: 404 GB).

- **Wichtige Empfehlung:**
  - Modelle **nicht** im Home-Verzeichnis unter `~/.ollama` speichern:
    - Pro-User Soft-Quota: 200 GB.

- Stattdessen:

  1. Workspace für Modelle anlegen (z. B. 60 Tage):

     ```bash
     ws_allocate ollama_models 60
     ```

  2. Softlink auf dieses Verzeichnis als `~/.ollama` anlegen:

     ```bash
     ln -s `ws_find ollama_models`/ ~/.ollama
     ```

  3. Alternativ statt Symlink eine Umgebungsvariable setzen:

     ```bash
     export OLLAMA_MODELS=`ws_find ollama_models`/models/
     ```

- Hinweis: Das reduzierte Modell `deepseek-r1:70b` passt gut in den GPU-Speicher einer NVIDIA L40S.

---

## Folie 38 – Ollama: Running the Server (Batch-Job)

- Beispiel-SLURM-Skript `ollama_example.slurm` zum Start des Ollama-Servers:

```bash
#!/bin/bash
#SBATCH --partition=gpu1
#SBATCH --gres=gpu
#SBATCH --nodes=1
#SBATCH --time=2:0:0
#SBATCH --ntasks=48
#SBATCH --mem=350G
#SBATCH --job-name=ollama
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=m@me.de

module load cs/ollama
export OLLAMA_HOST=0.0.0.0
export OLLAMA_LOAD_TIMEOUT=0
export OLLAMA_KEEP_ALIVE=0

ollama serve
```

**Erläuterung:**

- `--partition=gpu1`, `--gres=gpu`: Ein Knoten mit einer L40S-GPU, alle Cores (48) und 350 GB Speicher für 2 Stunden.
- `--job-name=ollama`: Jobname im Scheduler.
- `--mail-type=BEGIN`, `--mail-user=...`: E-Mail beim Jobstart.
- `module load cs/ollama`: Neueste Ollama-Version laden (z. B. 0.5.13, je nach System).
- `export OLLAMA_HOST=0.0.0.0`:
  - Server hört auf allen Interfaces im Cluster.
- `export OLLAMA_LOAD_TIMEOUT=0`:
  - Kein Timeout für das Laden großer Modelle.
- `export OLLAMA_KEEP_ALIVE=0`:
  - Kein automatisches Entladen des Modells (Standard wäre nach 5 Minuten Inaktivität).
- `ollama serve`:
  - Startet den Ollama-Serverprozess.

---

## Folie 39 – Ollama: Running the Client (auf DACHS)

- In einer zweiten Shell/Session kann der Client auf den laufenden Server zugreifen.

**Schritte:**

```bash
module load cs/ollama
export OLLAMA_HOST=gpu101
ollama pull deepseek-r1:70b
ollama list
ollama run deepseek-r1:70b
```

- `module load cs/ollama`: Client-Tools laden (gleiche Version wie Server).
- `export OLLAMA_HOST=gpu101`:
  - Hostname des GPU-Knotens, auf dem `ollama serve` läuft.
  - Muss ggf. an den tatsächlich zugewiesenen Node angepasst werden.
- `ollama pull deepseek-r1:70b`:
  - Modell-Download.
- `ollama list`:
  - Liste aller lokal bekannten LLM-Modelle.
- `ollama run deepseek-r1:70b`:
  - Start einer interaktiven Session mit dem Modell.

**Beispiel-Dialog nach dem Laden (ca. 240 s Ladezeit):**

```text
>>> When did Elvis die?
Elvis Presley died on August 16, 1977.

>>> Where did he die?
Elvis Presley died at his home, Graceland, in Memphis, TN.

>>> Was he married at that time?
At the time of his death, Elvis Presley was not married. His divorce from
Priscilla Ann Beaulieu had been finalized on October 3, 1973.
```

- Hinweis: Jeder Client hat eigenen Kontext, nutzt aber dieselben Serverressourcen.

- Zusatzhinweis: Modelle lassen sich alternativ aus vorbereiteten ZIP-Dateien entpacken, z. B.:

```bash
unzip /tmp/ollama_deepseek_r1_70b.zip
```

---

## Folie 40 – Ollama: Connecting from your Laptop

- Ziel: Nutzung der GPU-Ressourcen des Clusters vom eigenen Rechner zu Hause.

**SSH-Port-Forwarding:**

```bash
ssh -L 11434:gpu101:11434 HS_ACCOUNT@dachs-login.hs-esslingen.de
```

- Erstellt auf dem lokalen Laptop eine TCP-Verbindung:
  - Port `11434` lokal → getunnelt nach `gpu101:11434` im Cluster.
- Danach kann die lokale Maschine den Ollama-Server so ansprechen, als liefe er auf `localhost:11434`.

**Wichtiger Hinweis:**

- Ports auf Compute-Nodes sind innerhalb des Clusters offen:
  - Andere Nutzer können sich mit dem Ollama-Server verbinden und **Ressourcen mitbenutzen**.
  - Jeder Client hat aber einen eigenen Konversationskontext.

**Beispiel: Python-Client lokal verwenden**

1. Virtuelle Umgebung anlegen:

   ```bash
   python -m venv ollama_test
   source ollama_test/bin/activate
   python -m pip install ollama
   ```

2. Python-Code zum Zugriff auf den getunnelten Server:

   ```python
   import ollama

   response = ollama.chat(
       model="deepseek-r1:70b",
       messages=[{"role": "user", "content": "why is the sky blue?"}],
   )
   print(response)
   ```

- Verbindung nutzt lokal Port `11434`, der via SSH auf den GPU-Knoten weitergeleitet wird.

---

## Folie 41 – Ollama: Open WebUI

- Hinweis auf **Open WebUI**:
  - Docker-basierter, lokaler Web-Frontend-Client für LLMs.
  - Kann auf dem eigenen Rechner laufen und via Netzwerk/Port-Forwarding auf den Ollama-Server zugreifen.
- Folie zeigt vor allem den Hinweis, dass Open WebUI als Browser-GUI verwendet werden kann.
- Konkrete Kommandos/URLs sind nicht im Text der Folie angegeben.

---

## Folie 42 – More Information (Kapiteltrenner)

- Zwischenüberschrift „More information“.
- Überleitung zu allgemeinen Hinweisen, Dokumentation und Support-Angeboten zu DACHS.

---

## Folie 43 – DACHS: More Information (Best Practices & Support)

- Wichtige Hinweise und Best Practices:

  - Im **Home-Verzeichnis** nur die wichtigsten Daten speichern:
    - Es existiert ein **hartes Quota pro Organisation**.
    - Pro Nutzer wird bei Erreichen der Soft-Quota von **200 GB** gewarnt.
  - Für größere Datenmengen bitte **Workspaces auf BeeGFS** nutzen:
    - Verwaltung mit `ws_allocate`, `ws_extend`, `ws_release`, `ws_find`, `ws_list`.
  - Für maximale Performance bei AI-Workloads:
    - Dateizugriff nach Möglichkeit über **knoten-lokalen `/localscratch`**.

- Auf den **Login-Nodes**:

  - Keine lang laufenden Prozesse.
  - Keine sehr speicherintensiven Jobs.
  - Stattdessen Jobs über SLURM auf Compute-Nodes starten.

- Weitere Empfehlungen:

  - SLURM-Batchjobs verwenden.
    - Hilfreiche Kommandos: `squeue`, `sinfo_t_idle` (siehe auch Manual Pages).
  - Software und Module über Environment Modules pflegen:
    - `module avail`, `module load`, `module list`, etc.

- **Support & Dokumentation:**

  - DACHS-Wiki (Details, Anleitungen; Link im Umfeld der Folie).
  - Support per E-Mail:

    - `dachs-admin@hs-esslingen.de`

  - Für Softwareinstallationen und erweiterten Support:
    - Ticket im Support-Portal eröffnen:
      - <https://www.bwhpc.de/supportportal/>
      - Support Unit: **DACHS** auswählen.

  - E‑Training-Plattform:
    - <https://training.bwhpc.de>

---

## Folie 44 – Fragen? (Kontakt)

- Abschlussfolie mit Kontakthinweisen:

  - Für Fragen:  
    **E-Mail:** `dachs-admin@hs-esslingen.de`
  - Support-Tickets:  
    **Supportportal:** <https://www.bwhpc.de/supportportal/>

- Förderhinweis:
  - Förderträger: <http://www.bwhpc.de>

---

_Ende der Zusammenfassung der Folien 18–44 der DACHS-Workshop-Präsentation vom 14.03.2025._
