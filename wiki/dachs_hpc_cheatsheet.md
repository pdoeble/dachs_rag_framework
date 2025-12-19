# DACHS HPC – SLURM & Workspace Cheat Sheet

> Kurzreferenz der wichtigsten Kommandos für DACHS / bwUniCluster3.0  
> Fokus: Jobs starten, anzeigen, Ressourcen prüfen, Jobs beenden, Workspaces.

## 1. SLURM Grundkommandos

```bash
sbatch script.slurm      # Batch-Job einreichen
srun <cmd>               # Job/Jobstep sofort starten (interaktiv oder aus Script)
salloc                   # Interaktive Ressourcen-Allocation
squeue                   # Jobs in der Queue anzeigen
sinfo                    # Status von Partitionen/Knoten anzeigen
sinfo_t_idle             # nur freie Knoten pro Partition anzeigen (DACHS-Wrapper)
sacct                    # Accounting-Infos (fertige Jobs)
scancel <jobid>          # Job abbrechen
```

## 2. Jobs anzeigen

### Eigene Jobs anzeigen

```bash
squeue -u $USER
```

Nützliche Optionen:

```bash
squeue -u $USER -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
squeue -o %u,%a,%A,%Q
squeue -j <jobid>            # nur einen bestimmten Job
squeue --start -j JOBID      # Einschätzen, wann der Job startet erlaubt dann:
squeue -h -o %S
```

### Detailinfos zu einem Job

```bash
scontrol show job <jobid>
```

### Fertige Jobs (Accounting)

```bash
sacct -u $USER --format=JobID,JobName,Partition,Elapsed,State,MaxRSS,MaxVMSize
sacct -j <jobid> -o JobID,AllocTRES,Elapsed,State
```

## 3. Ressourcen / Partitionen anzeigen

### Überblick über Partitionen und Knoten

```bash
sinfo
sinfo -p gpu1               # nur Partition gpu1
sinfo_t_idle                # freie Knoten (DACHS-Tool)
```

Typische GPU-Partitionen auf DACHS:

- `gpu1` – 1× NVIDIA L40S
- `gpu4` – Anteile des 4× AMD MI300A APU-Knotens
- `gpu8` – Anteile des 8× NVIDIA H100-Servers

## 4. Jobs beenden

```bash
scancel <jobid>             # einzelnen Job abbrechen
scancel -u $USER            # alle eigenen Jobs abbrechen (aufpassen!)
```

Bei hängenden interaktiven `srun`-Sessions ggf. das Shell-Fenster schließen **und** den Job mit `squeue`/`scancel` aufräumen.

## 5. Interaktive Jobs

### Einfache interaktive GPU-Shell (L40S, 1 GPU)

```bash
srun --partition=gpu1 --gres=gpu:1 --pty /bin/bash
```

Danach läuft die Shell auf einem GPU-Knoten; Tests z. B.:

```bash
hostname
nvidia-smi        # auf NVIDIA-Knoten
rocm-smi          # auf AMD-APU-Knoten (gpu4)
```

### Interaktiver CPU-Job (ohne GPU, Beispiel)

Je nach Konfiguration gibt es CPU-Partitionen; allgemeines Muster:

```bash
srun --partition=<cpu-partition> --cpus-per-task=8 --mem=32G --time=02:00:00 --pty /bin/bash
```

(Partition-Namen für reine CPU-Knoten im DACHS-Wiki nachsehen.)

## 6. Batch-Jobs (SLURM-Skripte)

### Minimaler GPU-Batch-Job (L40S, 1 GPU)

`run_gpu1.slurm`:

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --partition=gpu1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%j.out

# Module laden
module purge
module load compiler/gnu
module purge
module load devel/python/3.12.3-gnu-14.2 cs/ollama/0.12.2
# ggf. weitere Module: mpi/openmpi, python, jupyter/ai, ...

# Debug-Infos (optional)
hostname
free -h
module list

# Eigentliche Anwendung
srun python my_script.py
```

Job starten:

```bash
mkdir -p logs
sbatch run_gpu1.slurm
```

### MPI-Beispiel (aus Workshop)

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=48
#SBATCH --time=00:10:00
#SBATCH --partition=gpu1

module load mpi/openmpi
mpirun ./mpi_program
```

Einreichen:

```bash
sbatch mpi_job.slurm
```

## 7. Workspaces (BeeGFS-Scratch)

**Grundsatz:** Jobs nicht aus `$HOME` starten, sondern aus einem Workspace.

### Workspace anlegen und nutzen

```bash
ws_allocate myws 30      # Workspace 'myws' für 30 Tage
ws_list                  # eigene Workspaces anzeigen
ws_find myws             # Pfad des Workspace
WSDIR=$(ws_find myws)
cd "$WSDIR"
```

### Workspace verlängern / löschen

```bash
ws_extend myws 30        # um 30 Tage verlängern
ws_release myws          # Workspace entfernen (Verzeichnis vorher leeren)
```

### Abgelaufene Workspaces wiederherstellen

```bash
ws_restore -l                     # Liste wiederherstellbarer Workspaces
ws_allocate myws_new 30           # neuen Workspace anlegen
ws_restore <old-name> myws_new    # Daten wiederherstellen
```

### Workspace teilen

```bash
ws_share myws other_user
```

## 8. Local Scratch (`$TMPDIR` / `/localscratch`)

Jeder Compute-Node hat lokalen NVMe-Scratch:

```text
$TMPDIR  ->  /localscratch/tmpdir.${SLURM_JOB_ID}
```

Typischer Ablauf im Batch-Skript:

```bash
# Daten in den lokalen Scratch kopieren
cp -r $WSDIR/input ${TMPDIR}/
cd ${TMPDIR}

# Rechnen
srun ./my_solver input/...

# Ergebnisse zurückkopieren
cp -r results $WSDIR/
```

Alles in `${TMPDIR}` wird nach Jobende gelöscht -> Resultate explizit sichern.

## 9. Module (Lmod)

### Wichtige Befehle

```bash
module avail                 # alle Module anzeigen
module avail compiler        # z. B. nur Compiler
module load compiler/gnu     # GNU-Compiler (neueste Version)
module load compiler/gnu/15.1
module list                  # geladene Module
module whatis mpi/openmpi    # Kurzinfo
module help mpi/openmpi      # ausführliche Hilfe
module purge                 # alle Module entladen
```

Module setzen u. a. `PATH`, `LD_LIBRARY_PATH`, `MANPATH` und weitere Variablen.

## 10. JupyterHub auf DACHS

JupyterHub URL:

```text
https://dachs-jupyter.hs-esslingen.de
```

Ablauf:

1. Im Browser einloggen (bwIDM).
2. Im Resource-Selection-Dialog Prozesse, RAM, Laufzeit und ggf. GPU auswählen.
3. JupyterHub startet im Hintergrund einen SLURM-Job.

Hinweise:

- Mit GPU-Auswahl wird ein kompletter GPU-Knoten reserviert.
- Interaktives Jupyter ist bequem, aber ressourcentechnisch die teuerste Nutzung.
- Für größere Produktionen Batch-Jobs bevorzugen.

## 11. Dateitransfer (bwUniCluster-Beispiele, analog für DACHS)

### `scp`

```bash
# Datei zum Cluster kopieren
scp paket.tar <user>@<cluster>:/pfad/ziel/

# Datei vom Cluster holen
scp <user>@<cluster>:/pfad/datei.tar .
```

### `sftp`

```bash
sftp <user>@<cluster>
sftp> put paket.tar
sftp> get results.tar
sftp> exit
```

---

Dieses Cheat Sheet konzentriert sich auf Kommandos, die in den bwHPC- und DACHS-Unterlagen explizit erwähnt sind bzw. direkt daraus abgeleitet werden.
