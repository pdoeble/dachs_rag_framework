# Tutorial: Compiling, Makefile, Parallel Jobs

Zusammenfassung der Präsentation „Tutorial: Compiling, Makefile, Parallel jobs“  
Hartmut Häfner, Steinbuch Centre for Computing (SCC), 06/12/2016  
Funding / Projektseite: <http://www.bwhpc-c5.de>

---

## Slide 1 – Titel

- **Institution:** Steinbuch Centre for Computing (SCC)
- **Funding:** <http://www.bwhpc-c5.de>
- **Titel:** *Tutorial: Compiling, Makefile, Parallel jobs*
- **Autor:** Hartmut Häfner

---

## Slide 2 – Outline

Themenüberblick des Tutorials:

- Compiler + Numerical Libraries
- Compiler commands
- Linking
- Makefile
  - Intro
  - Syntax (Explicit Rules, Implicit Rules, …)
- Parallelising
- Batch jobs for:
  - OpenMP
  - MPI
  - Hybrid (OpenMP + MPI)

---

## Slide 3 – Abschnittsüberschrift

**1. Compilation**

(Übergang von der Einleitung zum Kapitel „Compilation“.)

---

## Slide 4 – Object files (Direktes Kompilieren)

- Thema: Zusammenhang zwischen Quellen und ausführbarem Programm.
- Quellen: `src1.c`, `src2.c`, `src3.c` (Dateityp: `.c`)
- Ausführbare Datei: `exec.x` (Dateityp: `.x`)

Beispiel (Direktkompilierung und -linken in einem Schritt):

```bash
gcc -o exec.x src1.c src2.c src3.c
./exec.x
```

---

## Slide 5 – Object files (Getrenntes Kompilieren und Linken)

- Aussage: Änderungen in einer einzelnen Quelldatei erfordern **nicht** die Neukompilation des gesamten Quellcodes.
- Einführung von **Object files** (`*.o`) als Zwischenschritt.
- Getrennte Phasen:
  - **compiling**: Quellen → Objektdateien
  - **linking**: Objektdateien → Executable

Beispiel:

```bash
# Kompilieren
gcc -c src1.c
gcc -c src2.c
gcc -c src3.c

# Linken
gcc -o exec.x src1.o src2.o src3.o
```

- Ergebnis:
  - Ausführbare Datei: `exec.x`
  - Quellen: `src*.c`
  - Objektdateien: `src*.o`

---

## Slide 6 – Include files (Header-Dateien)

- Thema: **Header files** (`*.h`)
- Funktionen von Header-Dateien:
  - Deklaration von Variablen
  - Definition von `static` Variablen
  - Deklaration von Funktionen/Subroutinen
  - Weitere Deklarationen (`...`)

- Beispiel: Einbinden einer Header-Datei

  - Header-Datei liegt z. B. unter: `/home/myincs/header.h`
  - Im Quelltext wird eine Präprozessor-Direktive (`#include ...`) verwendet.
  - Der Header-Suchpfad wird beim Kompilieren erweitert über:
    ```bash
    -I <include_directory>
    ```

- Im Beispielprojekt werden die Module `hello.o` und `hello_fct.o` erzeugt und dann zu einer ausführbaren Datei `hello` gelinkt:

```bash
# Objekte bauen
# (Konkretisierung erfolgt auf späteren Folien mit dem hello-Beispiel)

# Ausführbare Datei bauen
./hello
```

---

## Slide 7 – Beispiel „Hello“ (C-Programm mit Header)

**Beispielprogramm-Aufbau:**

- Datei `hello_fct.c`:

```c
#include <stdio.h>

int print_hello(void) {
    printf("hello!\n");
    return 0;
}
```

- Datei `hello.c`:

```c
#include "hello.h"

int main(void) {
    print_hello();
    return 0;
}
```

- Header-Datei `hello.h` (Deklarationen, Include-Guard):

```c
#ifndef _HELLO_H_
#define _HELLO_H_

int print_hello(void);

#endif
```

- Zuordnung:
  - **Header (Declarations)**: `hello.h`
  - **Main Program / Functions (Definitions)**: `hello.c`, `hello_fct.c`

**Übung „hello“:**

- Baue die Objektdateien:
  - `hello.o`
  - `hello_fct.o`
- Linke die Objekte zu einem Executable:
  - `hello`
- Führe das Programm aus:

```bash
./hello
```

---

## Slide 8 – Shared Object Files und Libraries (Grundlagen)

- **Motivation:** Funktionen/Programmteile von mehreren Executables wiederverwenden.
- Eine **Library** enthält:
  - Programmparts (Subroutinen, Klassen, Typdefinitionen, …)
  - Diese können von unterschiedlichen Executables genutzt werden.

Arten von Libraries:

- **Shared library**:
  - Wird zur Laufzeit geladen.
- **Static library**:
  - Wird beim Linken des Executables eingebunden.

---

## Slide 9 – Shared Object Files und Libraries (Beispiel)

- Aufbau: Executable (`.x`) – Objektdateien (`.o`) – Libraries (`.so`).

**Beispiel Shared Library:**

- Gemeinsam genutzte MPI-Bibliothek, z. B.:
  - `/opt/bwhpc/common/mpi/openmpi/2.0.1-intel-16.0/lib/libmpi.so`

**Beispiel: Executable mit eigener statischer Library:**

- Bibliotheksverzeichnis hinzufügen:

  ```bash
  -L<library_directory>
  ```

- Bibliothek laden:

  ```bash
  -l<library_name>
  ```

- Reihenfolge: Quell-/Objektdateien **vor** der `-l`-Angabe.

**Konkret:**

```bash
gcc -o exec.x src1.o src2.o -L /home/mylibs -lexample
./exec.x
```

---

## Slide 10 – Module Files (Umgebungsmodul-System)

**Aufgabe von Module Files:**

- Setzen/Präparieren von Umgebungsvariablen, u. a.:

  - `*_LIB_DIR = <library_directory>`
  - `*_INC_DIR = <include_directory>`
  - `LD_LIBRARY_PATH`

- Anzeigen des Inhalts eines Modul-Files:

  ```bash
  module show <module_file>
  ```

**Beispiel: Linken einer (Shared) MPI Library**

- **Build Executable:**

  ```bash
  module load mpi/openmpi      # lädt automatisch den passenden Intel-Compiler
  mpicc -o hello_mpi hello_mpi.c
  ```

- **Ausführen:**

  ```bash
  mpirun -np 4 hello_mpi
  ```

---

## Slide 11 – Abschnittsüberschrift

**2. Makefile**

(Übergang vom Kapitel „Compilation“ zum Kapitel „Makefile“.)

---

## Slide 12 – Motivation für Makefiles

Vergleich verschiedener Vorgehensweisen:

1. **Interaktives Kompilieren**

   ```bash
   gcc -o hello -I. hello.c hello_fct.c
   ```

   - Funktioniert, solange die Shell-History verfügbar ist.
   - Fehleranfällig bei vielen Dateien/Schritten.

2. **Shell-Skript**

   ```bash
   ./compile.sh
   ```

   - Führt immer eine vollständige Neukompilation durch (alle Dateien).

3. **Makefile**

   ```bash
   make
   ```

   - Bessere Organisation des Kompilierprozesses.
   - Kompiliert nur geänderte Dateien neu.
   - Typische Ausgabe, wenn nichts zu tun ist:
     ```text
     make: `hello' is up to date.
     ```

---

## Slide 13 – Makefile-Grundlagen und Beispiel (Makefile.1 / Makefile.2)

### Aufruf und Grundkonzept

- Standardaufruf:

  ```bash
  make [<target>]
  ```

- `make` sucht nach einer Datei mit Namen **`Makefile`** oder **`makefile`**.
- Ohne explizites Target wird **die erste Regel** im Makefile ausgeführt.

### Regeldefinition (Syntax)

- Allgemeines Format:

  ```make
  target: prerequisites
      <TAB> command
  ```

  - Wichtig: Die Zeile mit `command` **muss** mit einem **Tabulator** beginnen.

### Beispiel: `Makefile.1`

```make
hello: hello.h hello.c hello_fct.c
    gcc -o hello -I. hello.c hello_fct.c
```

- Die Regel ist anzuwenden, wenn **eine der Dateien** `hello.h`, `hello.c` oder `hello_fct.c` geändert wurde.
- Um die Regel anzuwenden, wird der zugehörige `gcc`-Befehl ausgeführt.

**Übung (Makefile.1):**

- Definiere eine zweite Regel namens `clean`, die das Executable entfernt.

### Beispiel: `Makefile.2` (Variablen-Nutzung)

```make
CC ?= gcc
CFLAGS = -I.
INC := hello.h
OBJ := hello.o
OBJ += hello_fct.o
EXE := hello

${EXE}: ${INC} ${OBJ}
    ${CC} -o ${EXE} ${CFLAGS} ${OBJ}

.PHONY: clean
clean:
    rm -f ${OBJ} ${EXE}
```

- **Hinweis/Übung (Makefile.2):**
  - Es soll zudem abgebildet werden, dass `hello.o` auch von `hello.h` abhängt („`hello.o` depends on `hello.h`“).
  - Aufgabe: eine passende Regel ergänzen.

---

## Slide 14 – Regelarten in Makefiles

**Explizite Regeln**

- Beispiel: `hello.o: ...`  
  → spezifische Regel für genau ein Target.

**Wildcards**

- Beispiel:

  ```make
  hello: *.c
  ```

  - `hello` hängt von allen Dateien mit Suffix `.c` im aktuellen Verzeichnis ab.

**Pattern Rules**

- Allgemeine Form:

  ```make
  %.o: ...
  ```

  - Regel für alle Targets mit Suffix `.o`.

- Beispiel für Quell-/Objekt-Zuordnung:

  ```make
  %.o: %.c
      # Kommandos
  ```

  - `%` im Target und in den Abhängigkeiten repräsentiert denselben Basenamen.

**Phony Targets**

- Beispiel:

  ```make
  .PHONY: clean

  clean:
      # Befehle, die nichts „bauen“
  ```

- `clean` ist kein echtes Dateitarget, sondern nur ein „Aufräum-Target“.

---

## Slide 15 – Variablen in Makefiles (Überblick)

- Thema: **Variable assignment** in Makefiles.
- Beispielhafte Variablen (siehe `Makefile.2`):

  ```make
  CC ?= gcc
  CFLAGS = -I.
  INC := hello.h
  OBJ := hello.o
  OBJ += hello_fct.o
  EXE := hello

  ${EXE}: ${INC} ${OBJ}
      ${CC} -o ${EXE} ${CFLAGS} ${OBJ}

  .PHONY: clean
  clean:
      rm -f ${OBJ} ${EXE}
  ```

- Die Folie verweist erneut auf `Makefile.2` und die Übung, eine Regel für die Abhängigkeit von `hello.o` auf `hello.h` zu ergänzen.

---

## Slide 16 – Automatic Variables

**Automatische Variablen (werden von `make` je nach Regel gesetzt):**

- `$@` – Name des Targets
- `$<` – Erste Abhängigkeit (first prerequisite)
- `$^` – Alle Abhängigkeiten (all prerequisites, durch Leerzeichen getrennt)

**Übung: `Makefile.3`**

- Aufgabe: Automatische Variablen in der Regel zum Bau von `hello` verwenden.

**Kontext-Beispiel (Verwendung in Makefile.4, siehe auch Folien 18):**

- `make.inc.gnu` und `make.inc.intel` enthalten compiler-spezifische Makefile-Anweisungen.
- In `Makefile.4` soll abhängig von `${CC}` die jeweils passende Datei eingebunden werden.

Beispielausschnitt:

```make
include make.inc.gnu

hello_omp: hello_omp.o
    ${CC} -o $@ ${CFLAGS} $<
```

- Ziel: Nutzung der automatischen Variablen `$@` (Target) und `$<` (erste Abhängigkeit) beim Linken von `hello_omp`.

---

## Slide 17 – Directives (Bedingte Anweisungen in Makefiles)

**Direktiven zur bedingten Auswertung:**

1. **Prüfen, ob eine Variable definiert ist**

   - `ifdef VAR`
   - `ifndef VAR`
   - Blockstruktur:

     ```make
     ifdef VAR
         ...
     else
         ...
     endif
     ```

2. **Vergleich von Werten**

   - `ifeq (A,B)`
   - `ifneq (A,B)`

   Blockstruktur analog:

   ```make
   ifeq (A,B)
       ...
   else
       ...
   endif
   ```

**Beispiel – Bedingte Zuweisung (entspricht `CC ?= gcc`):**

```make
ifndef CC
    CC = gcc
endif
```

- Wenn `CC` **nicht** gesetzt ist, wird `CC = gcc` gesetzt.

---

## Slide 18 – Include (Makefile-Teile auslagern)

**Motivation:**

- Teile eines Makefiles können ausgelagert werden, z. B.:
  - Plattform- oder Compiler-spezifische Einstellungen.

**Einbindung externer Makefile-Fragmente:**

- Allgemein:

  ```make
  include make.inc
  ```

**Beispiel: Compiler-spezifische Einstellungen**

- `make.inc.gnu`:

  ```make
  CC     = gcc
  CFLAGS = -I. -fopenmp
  ```

- `make.inc.intel`:

  ```make
  CC     = icc
  CFLAGS = -I. -openmp
  ```

**Übung: `hello_omp` (Makefile.4)**

- `make.inc.gnu` und `make.inc.intel` enthalten compiler-spezifische Statements.
- Aufgabe:
  - `Makefile.4` so anpassen, dass abhängig von `${CC}` die passende Datei eingebunden wird.
  - Typischer Ablauf:

    ```bash
    module load compiler/gnu
    make

    module load compiler/intel
    make
    ```

- Beispielausschnitt `Makefile.4`:

  ```make
  include make.inc.gnu

  hello_omp: hello_omp.o
      ${CC} -o $@ ${CFLAGS} $<
  ```

---

## Slide 19 – Abschnittsüberschrift

**3. Parallel jobs**

(Übergang vom Kapitel „Makefile“ zum Kapitel „Parallel jobs“ auf dem Cluster.)

---

## Slide 20 – Submitting Serial Jobs via Script (MOAB)

**Ziel:**

- Einen seriellen Job (ein CPU-Core, 3000 MB RAM, 5 Minuten Laufzeit) über MOAB einreichen, um das Programm `hello` auszuführen.

**Einreichung:**

```bash
msub 01_jobuc.sh
```

**Beispielskript `01_jobuc.sh`:**

```bash
#!/bin/bash
#MSUB -l nodes=1:ppn=1
#MSUB -l walltime=0:05:00
#MSUB -l mem=3000mb
#MSUB -q singlenode
#MSUB -N serial-test
#MSUB -m bea
#MSUB -M me@provider.de

./hello
#sleep 60
```

**Erläuterung:**

- **Interpreter-Zeile:** `#!/bin/bash`
- **Header mit MSUB-Optionen:**
  - `nodes=1:ppn=1` – 1 Knoten, 1 Prozess/CPU
  - `walltime=0:05:00` – 5 Minuten Laufzeit
  - `mem=3000mb` – 3000 MB Hauptspeicher
  - `q=singlenode` – Queue für Single-Node-Jobs
  - `N=serial-test` – Jobname
  - `-m bea` – E-Mail-Benachrichtigung bei Beginn/Ende/Abbruch
  - `-M me@provider.de` – E-Mail-Adresse
- **Execution Part:** Ausführung von `./hello`.

---

## Slide 21 – Submitting Parallel Jobs (MPI)

**Ziel:**

- MPI-Job mit 2 Prozessen auf 1 Knoten einreichen.

**Beispielskript (MPI):**

```bash
#!/bin/bash
#MSUB -l nodes=1:ppn=2
#MSUB -l walltime=00:03:00
#MSUB -l pmem=1000mb
#MSUB -l advres=workshop.8
#MSUB -N hello_mpi

module load mpi/impi
mpirun ./hello_mpi
#sleep 60
```

**Hinweise:**

- Für Rechnungen auf **mehr als einem Knoten**:
  - Queue `multinode` verwenden.
- Das entsprechende MPI-Modul muss auf den Compute-Nodes geladen sein.
- Ausführung erfolgt mit `mpirun`.

**Kompilierung des MPI-Programms:**

```bash
module load mpi/impi
mpicc -o hello_mpi hello_mpi.c
```

---

## Slide 22 – Submitting Parallel Jobs (OpenMP)

**Ziel:**

- OpenMP-Job auf einem Knoten mit mehreren Threads einreichen.

**Beispielskript (OpenMP):**

```bash
#!/bin/bash
#MSUB -l nodes=1:ppn=8
#MSUB -l walltime=00:05:00
#MSUB -l pmem=1000mb
#MSUB -q singlenode
#MSUB -N hello_omp

EXECUTABLE=./hello_omp
export OMP_NUM_THREADS=${MOAB_PROCCOUNT}

echo "Executable ${EXECUTABLE} running with ${OMP_NUM_THREADS} threads"
${EXECUTABLE}
```

**Besonderheiten:**

- **Shared memory**:
  - Job ist auf einen Knoten (shared memory) beschränkt (`q=singlenode`).
- Anzahl der Threads **nicht explizit** fest im Skript setzen:
  - Stattdessen `OMP_NUM_THREADS` aus der MOAB-Variablen `MOAB_PROCCOUNT` ableiten.
- Typische Kompilierung (Intel-Compiler mit OpenMP):

  ```bash
  icc -qopenmp -o hello_omp hello_omp.c
  ```

---

## Slide 23 – Hybrid Parallel Jobs (OpenMP + MPI)

**Ziel:**

- Hybrid-Job: MPI + OpenMP (Tasks × Threads) auf mehreren Knoten.

**Beispielskript (MPI + OpenMP):**

```bash
#!/bin/bash
#MSUB -l nodes=2:ppn=16
#MSUB -l walltime=0:05:00
#MSUB -l pmem=1000mb
#MSUB -q multinode
#MSUB -v EXE=./hello_mpi_omp
#MSUB -v OMP_NUM_THREADS=2
#MSUB -N hello_mpi_omp
#MSUB -o $(JOBNAME).o$(JOBID)

module load mpi/openmpi

export NTASKS=$((${MOAB_PROCCOUNT}/${OMP_NUM_THREADS}))

echo "Executable ${EXE} running on ${MOAB_PROCCOUNT} cores with \
${NTASKS} tasks and ${OMP_NUM_THREADS} threads"

mpirun -n ${NTASKS} --bind-to core \
                   --map-by node:PE=${OMP_NUM_THREADS} ${EXE}
```

**Hinweis:**

- Explizite Deklaration von:
  - Anzahl der MPI-Tasks (`NTASKS`)
  - Anzahl der Threads (`OMP_NUM_THREADS`)
- `MOAB_PROCCOUNT` wird verwendet, um Tasks und Threads auf die angeforderten Kerne zu verteilen.

---

## Slide 24 – A Very Brief Overview on OpenMPI / OpenMP

**Kernaussagen der Folie:**

- OpenMP ist eine:
  - **einfache**
  - **portable**
  - **inkrementelle**

  Spezifikation für **Node-Level-Parallelisierung**.

- Charakteristika:
  - Thread-basiert
  - Shared-Memory, Single-Node (im Gegensatz zu MPI, das auf mehrere Knoten skalieren kann).

**Funktionsweise:**

- C/C++/Fortran-Quellcode wird mit **Pragmas** annotiert.
- Der Compiler generiert den benötigten Parallelisierungscode.
- Nicht-parallele Codeblöcke:
  - werden nur vom **Hauptthread** (Master) ausgeführt.
- Parallele Blöcke:
  - werden an ein **Team von Threads** übergeben und parallel ausgeführt.

**Wichtig:**

- Wenn der Compiler **kein OpenMP** unterstützt oder OpenMP **nicht aktiviert** wird:
  - werden die Pragmas ignoriert.
  - der Code läuft auf **einem einzelnen Kern**,
  - das Ergebnis bleibt dennoch korrekt (nur ohne Beschleunigung durch Parallelität).

---

## Slide 25 – OpenMP Core Syntax (Structured Blocks / Parallel Regions)

**Begriffe:**

- Viele OpenMP-Pragmas beziehen sich auf einen **„structured block“** bzw. eine **„parallel region“**.
- Ein „structured block“ ist:
  - eine einzelne Anweisung **oder**
  - ein Block aus mehreren Anweisungen mit:
    - genau einem Eintrittspunkt (am Blockanfang) und
    - genau einem Austrittspunkt (am Blockende).

**Eigenschaften:**

- Nur Anweisungen **innerhalb** eines Blocks, der mit der `parallel`-Klausel markiert ist, werden parallel ausgeführt.
- Es ist erlaubt, innerhalb eines solchen Blocks die gesamte Applikation abzubrechen (z. B. via `exit`).

**Beispiel-Syntax (C/C++):**

```c
#pragma omp parallel
{
    // statements
}
```

**Beispiel-Syntax (Fortran):**

```fortran
!$omp parallel
    ! statements
!$omp end parallel
```

- Diese Beispiele illustrieren, wie ein paralleler Block in OpenMP markiert wird.
- Ohne aktiviertes OpenMP werden diese Pragmas vom Compiler ignoriert.

---

_Ende der vollständigen inhaltlichen Zusammenfassung der 25 Folien der Präsentation._