# 2nd bwUniCluster & DACHS User Workshop – HPC @ HAW (29.07.2025)

Zusammenfassung der Präsentation **„2nd bwUniCluster & DACHS User Workshop – HPC @ HAW, 29.07.2025“**.  
Die Inhalte sind nach Folien gegliedert und fassen die wesentlichen Texte, Beispiele und Abbildungen zusammen, ohne zusätzliche Informationen hinzuzufügen.

---

## Folie 1 – Titel

- **Titel:** 2nd bwUniCluster & DACHS User Workshop – HPC @ HAW – 29.07.2025  
- **Logos / Grafik:**
  - Links oben: bwHPC-Logo.  
  - Rechts oben: Dachs-Maskottchen (Badger-Kopf).  
  - Im unteren Bereich: Logos der beteiligten Hochschulen/Universitäten (u. a. Universität Heidelberg, Hochschule Esslingen, Universität Stuttgart, Universität Tübingen, KIT, Universität Ulm, weitere).

---

## Folie 2 – Overview

- Die **Folien** werden als PDF zur Verfügung gestellt.
- Eine **Aufzeichnung (Recording)** steht zum Download bereit unter:  
  <https://www.hs-esslingen.de/informatik-und-informationstechnik/forschunglabore/forschung/laufende-projekte/dachs>  
  (inkl. Informationen zu Registrierung, Login etc.).

### Themen des Workshops

- Wiederholung des **Project Overview**.
- Nutzung von **Software Modules**.
- **Best Practices** für **Microsoft Visual Studio Code (VS Code)**.
- **Forschungsdatenmanagement (FDM)** mit DACHS.
- **Security-Info:** Firewall auf den DACHS-Login-Knoten.
- **Parallele Dateisysteme** Lustre/BeeGFS & `localscratch`.
- Wie man **bwUniCluster / DACHS in Publikationen** erwähnt.
- Weitere Dokumentation.

---

## Folie 3 – HPC Overview (Kapiteltrenner)

- Kapitel-Titel: **HPC Overview**.
- Reine Übergangsfolie ohne zusätzlichen Textinhalt.

---

## Folie 4 – BaWü Data Federation / HPC-Landschaft

- Überschrift: **BaWü Data Federation – Strategy for implementing High Performance Computing (HPC), Data intensive Computing (DIC)**.
- **Diagramm (Pyramide)** mit HPC-Ebenen („Tiers“):

  - **0: European HPC Center**
    - Hinweis: Top-500-Systeme.
    - **Top 4:** JUPITER Booster, JSC.

  - **Tier 1: National HPC Centers, GCS**
    - Zentren: HLRS, JSC, LRZ.

  - **Tier 2: National HPC Centers**
    - KIT „Horeka“.

  - **Tier 3: Regional HPC Centers**  
    - Beispiele: Justus3, NEMO2, BinAC, bwUniCluster3.0, MLS&WISO, Hunter & Herder.  
    - Beschriftung: „HPC enabler“.

- Rechts im Diagramm: **BaWü Data Federation** mit Bausteinen:
  - **LSDF2**
  - **bwSFS**
  - **Data Analysis**
  - **Data Repositories**
  - **bwCloud**
  - **Data Archive**

- **HAW Participation (Teilnahme der Hochschulen für Angewandte Wissenschaften):**
  1. **Partnering HPC@HAW:** Anteil am bwUniCluster (HAW als Gesamtheit).
  2. **Partnering Datenanalyse Cluster der HS (DACHS).**

---

## Folie 5 – Project HAW Datenanalyse Cluster BaWü

- **Partnering as an Association with a cross-site installation:**

  Liste der beteiligten Hochschulen:

  1. HS Aalen  
  2. HS Albstadt-Sigmaringen  
  3. HS Esslingen  
  4. HS Heilbronn  
  5. HS Karlsruhe  
  6. HTWG Konstanz  
  7. HS Mannheim  
  8. HS Offenburg  
  9. HS Reutlingen  
  10. HfT Stuttgart  
  11. THU Ulm  

- Rechts: Karte von Baden-Württemberg mit markierten Standorten und Foto eines Racks mit DACHS-Hardware.
- **Förderhinweis:** Antrag als „Großgeräte der Länder“, positiv durch DFG begutachtet, zu 50 % kofinanziert durch MWK und alle Partner.

---

## Folie 6 – Setup Datenanalyse Cluster BaWü (Hardware)

### Hardware-Überblick

- **GPU-Knoten:**
  - 45 × Single-GPU-Nodes (**NVIDIA L40S**, jeweils 48 GB).
- **APU-Knoten:**
  - 1 × Quad-Socket-APU-Node:
    - 4 × **AMD MI300A**, insgesamt **512 GB HBM3 RAM**.
- **High-End-GPU-Knoten:**
  - 1 × Octo-GPU-Node:
    - 8 × **NVIDIA H100** mit je 80 GB (SXM5),
    - Dual-AMD EPYC 9454 (48 Cores, 128 MB L3),
    - insgesamt **1,5 TB ECC-RAM**.
- **Login- und Management-Server:**
  - 2 × Login-Node.
  - 1 × Management-Node.
- **Speicher:**
  - Paralleles **BeeGFS**-Dateisystem mit **700 TB netto**.
- **Netzwerk:**
  - NVIDIA/Mellanox **InfiniBand HDR 200 Gbit**-Switch.

### Gemeinsame Eigenschaften aller Knoten

- **CPUs:**
  - Dual-AMD EPYC 9254 CPU (24 Cores, 2,9 GHz, 128 MB L3).
- **RAM:**
  - 384 GB ECC-RAM.
- **Lokaler Speicher:**
  - 1,92 TB lokale SSD (für **local scratch**).
- Nutzung vorhandener Kühlinfrastruktur und Racks.
- Gesamt: **75 kW Peak-Kühlbedarf**.

### Diagramm (Cluster-Layout)

- Darstellung der Knoten `gpu101`–`gpu145` in mehreren Chassis (`C0`, `C1`, `C2`).
- Markierung der:
  - 1×-L40S-Knoten (gpu101–gpu145).
  - MI300A-Node (`gpu401`).
  - H100-Node (`gpu801`).
- Zusätzlich: Storage-Nodes & JBODs, 10kVA-USV, HDR-IB-Switch, Management- und Login-Knoten.

---

## Folie 7 – Usage of Software Modules (Kapiteltrenner)

- Titel-Folie: **Usage of Software Modules**.
- Übergang zum Abschnitt über Software-Modulverwaltung mittels Lmod.

---

## Folie 8 – Software Modules 1/3

- Auf HPC-Systemen wird häufig benötigte Software zentral bereitgestellt (auf Anfrage).
- Auf **bwUniCluster & DACHS** wird **Lmod** zur Bereitstellung von Software-Modulen verwendet.

### Wichtige Befehle

- Alle verfügbaren Module anzeigen:

  ```bash
  module avail
  ```

  - Beispiel: `module avail compiler` zeigt nur Compiler-Module.

- Spezifische Compiler-Version laden:

  ```bash
  module load compiler/gnu/15.1
  ```

- Neueste verfügbare Version laden:

  ```bash
  module load compiler/gnu
  ```

- Modulinformation anzeigen:

  ```bash
  module help mpi/openmpi
  module whatis module_name
  ```

- Module-Umgebung zurücksetzen:

  ```bash
  module purge
  ```

### Wirkung der Software-Module

- Software-Umgebungen passen u. a. an:
  - `PATH`
  - `LD_LIBRARY_PATH`
  - `MANPATH`
  - und setzen weitere Umgebungsvariablen.
- Beispiel: Der GNU-Compiler setzt `GNU_VERSION` und `GNU_HOME`.
- Hinweis: Vor und nach dem Laden eines Moduls können die Umgebungsvariablen geprüft werden, z. B.:

  ```bash
  env | sort | less
  ```

---

## Folie 9 – Software Modules 2/3

- Zur Kontrolle, ob die **richtige Software-Version** verwendet wird:

  ```bash
  echo $PATH
  which gcc
  ```

  - So lässt sich z. B. prüfen, dass `gcc` von `compiler/gnu/15.1` stammt.

- **Versteckte („hidden“) Module:**
  - Einige Module werden in `module avail` nicht angezeigt.
  - Ihr Modulname beginnt mit einem Punkt `.`.
  - Sie können dennoch geladen werden:

    ```bash
    module load devel/pocl/.6.0
    ```

    - (Hinweis in Klammern: Portable OpenCL v7 ist verfügbar.)

- Wenn die exakte Software-Version **nicht wichtig** ist und die **neueste** genügt:

  ```bash
  module load compiler/gnu
  ```

- Software hat Abhängigkeiten von Systembibliotheken und anderen Modulen, die beim Laden automatisch berücksichtigt werden, z. B.:

  ```bash
  module load devel/python/3.13.3-llvm-18.1
  ```

  - Solche Modulnamen können dadurch sehr lang werden.

---

## Folie 10 – Software Modules 3/3

- **Betriebssystemstand:**
  - bwUniCluster und DACHS laufen auf aktueller **Rocky Linux**-Version.
- Die gängige Software für den täglichen Gebrauch ist verfügbar und relativ aktuell, z. B. **cmake**, **git**.
- Wenn zusätzliche Standardsoftware benötigt wird, sollen sich Nutzer melden.

### Standort-spezifische Software

- Jede Hochschule kann Software im organisations-spezifischen Verzeichnis installieren:

  ```text
  /opt/bwhpc/es/…
  ```

- Dieses Verzeichnis enthält dieselben SW-Kategorien wie `common/`:

  - `admin`, `mpi`, `cae`, `numlib`, `compiler`, `system`, `cs`, `vis`, `devel`
  - plus dazu passende **modulefiles**.

- Auf **bwUniCluster3.0** steht zusätzlich **EasyBuild** zur Bereitstellung von Software zur Verfügung.

---

## Folie 11 – Build Software?

- Thema: Software-Build-Prozess auf HPC-Systemen.

### Konfiguration

- Mögliche Werkzeuge zum Konfigurieren:

  - **cmake**
  - **AutoConf**
  - **Scons**
  - **Bazel**

### Build-Systeme

- Mögliche Werkzeuge zum Bauen:

  - **Make**
  - **Ninja**

- Hinweis: Die Details sind stark Software-abhängig.
- Bei Interesse: **bwHPC TigerTeam** ansprechen – „Please talk to us.“

---

## Folie 12 – Visual Studio Code (Kapiteltrenner)

- Titel-Folie: **Visual Studio Code**.
- Übergang zum Abschnitt über VS Code und Remote-Entwicklung.

---

## Folie 13 – Visual Studio Code 1/3

- **Microsoft Visual Studio Code (VS Code)** wird als **Open-Source-Tool** präsentiert.
- Erweiterungen (Extensions) machen VS Code sehr leistungsfähig.

### Hervorgehobene Funktionen

- **Integrated Development Environment (IDE):**
  - Projektverwaltung, Explorer, integrierte Terminals.
- **Code Completion** für viele Sprachen (z. B. C, C++).
- **GitHub Copilot**:
  - KI-gestütztes Pair Programming, generiert Code-Vorschläge.

- Screenshot: Startseite von VS Code mit „Get started with VS Code“ und Auswahl von Themen/Workspaces.

---

## Folie 14 – Visual Studio Code 2/3 (Remote Development)

- Empfohlene Erweiterungen:

  - **„C/C++“** (mit IntelliSense).
  - **„Remote Development“**.

### Remote Development per SSH

- **Remote Explorer**-Tab in VS Code:
  - Erscheint nach Installation der Remote-Extensions.
- Zugriff auf Remote-Server via SSH:
  - Auswahl von „Connect to Host“.
  - Konfiguration einer der eigenen SSH-Verbindungen.
- Screenshot zeigt:
  - Extensions-Ansicht mit „Remote Development“.
  - Hervorgehobenen Tab „remote explorer“.

---

## Folie 15 – Visual Studio Code – SSH-Konfiguration

### SSH-Host-Konfiguration

- Beim Hinzufügen eines SSH-Hosts wird die Datei `~/.ssh/config` angepasst, z. B.:

  ```text
  Host dachs
      HostName dachs-login.hs-esslingen.de
      User es_rakeller
  ```

- Nach Eingabe von OTP (One-Time Password) und Passwort ist man eingeloggt.
  - Auf dem Remote-System werden unter `~/.vscode-server/` ca. 450 MB installiert.

### Arbeiten auf dem Remote-Server

- In VS Code stehen zur Verfügung:

  - Terminal auf dem entfernten System.
  - Editieren von Dateien.
  - Öffnen von Verzeichnissen (Folders).

- Hinweis: **SSH kann noch deutlich mehr**, z. B. Tunneling, Agent-Forwarding etc.

---

## Folie 16 – ssh Jump Host

- Statt direkt auf einen Server zuzugreifen, kann bei fehlendem VPN bzw. bei Firewall-Beschränkungen ein **Jump Host** notwendig sein.

### Beispielkonfiguration in `~/.ssh/config`

```text
Host bwJUMP
    User ORG_USERNAME
    HostName bwunicluster.scc.kit.edu
    ProxyCommand /usr/bin/ssh -i ~/.ssh/id_rsa_bwcloud_proxyjump -l ubuntu -v -W '[%h]:%p' YOUR.bw-cloud-instance.org
    IdentityFile ~/.ssh/id_rsa_bwcloud_proxyjump
    ForwardAgent yes
    PubkeyAuthentication yes

Host bwcloud
    User ubuntu_username_on_bwcloud
    HostName YOUR.bw-cloud-instance.org
    IdentityFile ~/.ssh/id_rsa_bwcloud_proxyjump
    ProxyJump bwJUMP
```

- Kursiv hervorgehobene Platzhalter (z. B. `YOUR.bw-cloud-instance.org`) müssen durch system-spezifische Werte ersetzt werden.
- So kann man über eine bwCloud-Instanz auf bwUniCluster zugreifen.

---

## Folie 17 – ssh Public Key Access

- Ziel: Statt jedes Mal OTP & Passwort einzugeben, soll der Zugriff per **SSH-Key mit Passwort** erfolgen.

### Schlüsselpaar erzeugen

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_dachs_USER
```

- Danach Verweis in `~/.ssh/config` für den Dienst eintragen:

```text
IdentityFile ~/.ssh/id_ed25519_dachs_USER
```

### Registrierung des Public Keys

1. **Öffentlichen Schlüssel registrieren** unter:  
   <https://login.bwidm.de>  
   - Tab **Index → My SSH PubKeys → Add Key**.
   - Danach erscheint der Key in der Liste.

2. Unter **Registered Service**:
   - „Add Key“ zum gewünschten Service.
   - Anschließend wird der Key für diesen Dienst freigeschaltet.

### Hinweise

- Der Key ist jeweils **für 1 Stunde freigeschaltet**; danach muss erneut OTP/Passwort eingegeben werden.
- Verwendung von:

  ```bash
  ssh-agent    # Dienst zum Verwalten von Schlüsseln
  ssh-add      # Key im Agent zwischenspeichern
  ```

- Somit muss das Passwort zum Schlüssel nicht bei jeder Verbindung erneut eingegeben werden.

---

## Folie 18 – VS Code remote in Kombination mit git

- Empfohlene Arbeitsweise mit **Dual-Screen-Setup**:

  - **Bildschirm 1:**  
    - Lokaler VS Code → Änderungen entwickeln, testen und in **git einchecken**.
  - **Bildschirm 2:**  
    - Remote VS Code (via SSH) → Änderungen aus **git auschecken und auf DACHS kompilieren**.
  - (Optional) **Bildschirm 3:**  
    - Für Dokumentation, Browser etc.

- Vorteil: Guter **Turnaround** beim Ausprobieren neuer Features durch direkten Wechsel zwischen lokalem und remote Build.

- Hinweis: Es existiert auch **VScodium** (VS-Code-Fork ohne Microsoft-Branding), angemerkt von R. Breuer.

---

## Folie 19 – Forschungsdatenmanagement (FDM) with DACHS (Kapiteltrenner)

- Titel-Folie: **Forschungsdatenmanagement (FDM) with DACHS**.
- Übergang zum Abschnitt über Publikation und Verwaltung von Forschungsdaten.

---

## Folie 20 – Publication of Your research data

### Dienste für Forschungsdaten

- Es gibt verschiedene Services:

  - **SDS@HD** – Temporäre Speicherung von großskaligen Daten (kostenpflichtig).
  - **bwDataArchive** – Backup von „kalten“ Daten auf Langzeitspeicher.
  - Community-spezifische Repositorien, die **bwSFS** bzw. **bwSFS2** (bald) nutzen.

### FDM mit DACHS – `fdm-publish`

- Wenn man die Daten zu einer **Fachpublikation** veröffentlichen möchte, kann DACHS’ FDM eingesetzt werden:

  ```bash
  fdm-publish [-h] -b BIBTEX -a ARCHIVES1 [ARCHIVES2 …]
  ```

  - `[-h]` – Optionale Hilfe.
  - `-b BIBTEX` – **Pflichtargument:** Pfad zu einer `.bib`-Datei.
  - `-a ARCHIVES…` – **Pflichtargument:** Ein oder mehrere zu veröffentlichende Archive (z. B. `.tar.gz`, `.zip`).

- Der Befehl:

  - erzeugt eine **HTML-Seite**,
  - stellt die Archive unter einer öffentlich zugänglichen URL bereit.

- Beispiel: Datensatz **ROVER** von Fabian Schmidt et al.:

  - <https://fdm.hs-esslingen.de/schmidt2025rover/>

---

## Folie 21 – FDM Publication Internals

### Vereinbarung / Rahmenbedingungen

- **Speicherbudget:** ca. **1 TB pro Professor**.
- Daten sind über die URL etwa **5 Jahre lang** erreichbar.
- **Kein QoS:** kein Backup, „best-effort“-Bereitstellung.

### Technische Details

- Der Name der URL wird aus dem **Key** der `.bib`-Datei generiert.
- Die bereitgestellten Archive können unterschiedliche Formate kombinieren:
  - `.tar`, `.tar.gz`, `.gz`, `.zip` etc.
- Die generierte HTML-Datei und die Archive werden unter folgendem Pfad abgelegt:

  ```text
  /beegfs/fdm/YOUR_KEY
  ```

- Dieses Verzeichnis ist für den Nutzer **beschreibbar**:
  - Archive und HTML können nachträglich live erweitert oder angepasst werden.

---

## Folie 22 – Security-Info: Firewall on DACHS Login (Kapiteltrenner)

- Titel-Folie: **Security-Info: Firewall on DACHS Login**.
- Übergang zu den neuen Firewall-Regeln auf den DACHS-Login-Knoten.

---

## Folie 23 – Firewall Rules – Overview

- Änderung der **Default Policy** für eingehenden Traffic von `ACCEPT` auf **`DROP`**, mit Ausnahmen.

### Erlaubte Verbindungen (Ausnahmen)

- **SSH** (extern und intern) zu den Login-Knoten `134.108.188.4` und `.5`:
  - Externer Zugriff wird durch die Firewall auf **BelWue-IP-Bereiche** und interne Domains `hs-esslingen.de` begrenzt.
- **HTTPS**:
  - Weltweiter Zugriff für FDM (statisches HTML-Serving).
- **UCARP**:
  - Common Address Redundancy Protocol zwischen den Login-Nodes:
  - `dachs-login.hs-esslingen.de` stellt zwei IPv4-Adressen bereit.
- **SLURM-Kommunikation:**
  - `slurmctld`, `slurmd`, Kommunikation zwischen Compute- und Login-Nodes.
- **BeeGFS-Kommunikation:**
  - Metadaten-Server dürfen von Cluster-internen IPs erreichen werden.
- **ICMP**-Pakete (z. B. Ping).
- **Forwarding**:
  - Traffic zwischen Compute-Nodes und Internet.
- **NAT (Network Address Translation)**:
  - Für das Subnetz der Compute-Nodes.

---

## Folie 24 – Firewall Rules – Cluster Overview

- Übersichtsgrafik der Firewall-Architektur:

  - Zeigt die Login-Nodes, Compute-Nodes, das interne Cluster-Netz, die Verbindung zum Internet sowie die Rolle der Firewall dazwischen.
  - Markiert eingehenden/ausgehenden Traffic, NAT-Bereich und erlaubte Protokolle (SSH, HTTPS, SLURM, BeeGFS).

- Dient als visuelles Gesamtbild der in Folie 23 beschriebenen Regeln.

---

## Folie 25 – Firewall Rules – Log dropped traffic

### Logging von verworfenem Traffic

- Um verworfene Pakete zu protokollieren, kann eine Regel am Ende der `INPUT`-Chain ergänzt werden:

  ```bash
  -A INPUT -j LOG --log-prefix "iptables:policy drop: " --log-level 6
  ```

- Nach dem Laden des neuen Regelwerks können die geloggten Pakete mit `grep` gefiltert werden:

  ```bash
  grep 'iptables:policy drop' /var/log/messages
  ```

### Beispiel einer Logzeile

- Beispielhafter Eintrag:

  ```text
  Jul 26 09:49:30 login1 kernel: iptables:policy drop: IN=bond-ext OUT=
  MAC=44:49:88:02:f3:98:e4:1f:7b:eb:7b:9f:08:00
  SRC=45.227.254.156 DST=134.108.188.2 LEN=52 TOS=0x00 PREC=0x00 TTL=117
  ID=3751 DF PROTO=TCP SPT=65179 DPT=443 WINDOW=200 RES=0x00 CWR ECE SYN
  URGP=0
  ```

- Die Zeile zeigt:

  - Eingangsinterface, Quell- und Ziel-IP, Port (hier `443`), Flags etc.
  - So können verdächtige Verbindungsversuche identifiziert werden.

---

## Folie 26 – Parallel Filesystem & local scratch (Kapiteltrenner)

- Titel-Folie: **Parallel Filesystem & local scratch**.
- Übergang zum Abschnitt über Workspaces und lokalen Scratch-Speicher.

---

## Folie 27 – Workspace Tools Repetition

- **Home-Verzeichnisse** und **Workspaces** liegen:
  - auf **Lustre** (bwUniCluster) bzw.
  - auf **BeeGFS** (DACHS).

- Workspaces bieten **großen, schnellen, aber temporären Speicher**.

### Standard-Laufzeit

- **Default:** 30 Tage.
- Verlängerbar bis zu **3×**, jeweils bis zu **90 Tage**.

### Basis-Kommandos

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

- Speicherpfad eines Workspaces finden:

  ```bash
  ws_find <name>
  # Beispiel:
  # /beegfs/scratch/workspace/xx_use-test_workspace
  ```

- Eigene Workspaces auflisten:

  ```bash
  ws_list
  ```

---

## Folie 28 – Workspace Tools (Erweiterte Nutzung)

### Ablauf & Ablaufbenachrichtigung

- **E-Mail-Erinnerung**:

  - Wird **eine Woche vor Ablauf** eines Workspaces verschickt.

- Nach Ablauf bleibt der Workspace weitere **14 Tage** erhalten, bevor er gelöscht wird.

### Wiederherstellung abgelaufener Workspaces

- Mit `ws_restore`:

  ```bash
  ws_restore -l             # Liste der wiederherstellbaren Workspaces
  ws_allocate <new-ws>      # neuen Workspace anlegen
  ws_restore <old> <new-ws> # abgelaufenen Workspace unter neuem Namen wiederherstellen
  ```

- Weitere Beispiele im User Guide:  
  <https://github.com/holgerBerger/hpc-workspace/blob/master/user-guide.md>

### Workspaces teilen

- Um einen Workspace für andere Nutzer freizugeben (ACL-basiert):

  ```bash
  ws_share <ws> <user>
  ```

---

## Folie 29 – Local Scratch

- Jeder **Compute-Node** verfügt über ca. **1 TB** NVMe-SSD als lokalen Scratch-Speicher.
- Dateisystem: **XFS**.
- Mountpoint für Nutzerjobs:

  ```text
  $TMPDIR  →  /localscratch/tmpdir.${SLURM_JOB_ID}
  ```

### Empfohlene Nutzung

- Besonders geeignet, wenn Programme:

  - sehr häufig lesen/schreiben,
  - viele kleine Dateien erzeugen.

- Typischer Ablauf:

  1. Daten von `$HOME` oder Workspace nach `${TMPDIR}` kopieren.
  2. Job dort arbeiten lassen.
  3. Ergebnisse zurück in `$HOME` oder Workspace kopieren.

### Beispiele

- Verzeichnis aus `$HOME` rekursiv nach `${TMPDIR}` kopieren:

  ```bash
  cp -r $HOME/dir ${TMPDIR}
  ```

- Datei aus Workspace im Local Scratch entpacken:

  ```bash
  unzip `ws_find my_workspace`/file.zip -d ${TMPDIR}
  ```

- Hinweis: Dateien in `${TMPDIR}` werden **nach Jobende gelöscht**.  
  → Ergebnisse müssen im Batch-Skript explizit zurückkopiert werden.

---

## Folie 30 – Acknowledgements & further Documentation (Kapiteltrenner)

- Titel-Folie: **Acknowledgements & further Documentation**.
- Übergang zu Zitierempfehlungen und Dokumentationsquellen.

---

## Folie 31 – Acknowledgements of Usage of HPC Systems

### Motivation

- Zukünftige Finanzierung hängt davon ab, dass die Systeme **sichtbar genutzt** werden.
- Betreiber sind gegenüber Förderern rechenschaftspflichtig.

- Nutzer werden daher gebeten:

  - die Cluster in **Projektanträgen** zu erwähnen,
  - und die Nutzung in Publikationen zu **danken/acknowledgen**.

### Empfohlene Formulierungen

- Für **bwUniCluster**:

  > “The authors acknowledge support by the state of Baden-Württemberg through bwHPC.”

- Für **DACHS**:

  > “We thank the DACHS data analysis cluster, hosted at Hochschule Esslingen and co-funded by the MWK within the DFG's "Großgeräte der Länder" program, for providing the computational resources necessary for this research.”

---

## Folie 32 – Further Documentation

### bwHPC-Wiki

- Allgemeine Startseite:  
  <https://wiki.bwhpc.de>
- Spezifische Seiten:
  - bwUniCluster3.0: <https://wiki.bwhpc.de/e/bwUniCluster3.0>
  - DACHS: <https://wiki.bwhpc.de/e/DACHS>

### Weitere Dokumentation

- **BeeGFS Documentation**
- **Lustre Documentation**

### Trainingsplattform

- Online-Trainings, u. a. zu Linux, SLURM, HPC:  
  <https://training.bwhpc.de>

### Support

- Bei Problemen: Ticket erstellen unter:  
  <https://www.bwhpc.de/supportportal/>
- Oder E-Mail an:
  - `dachs-support@hs-esslingen.de`
  - `dachs-admin@hs-esslingen.de`

- Hinweis: Nächster Workshop am **7. November 2025 um 14 Uhr**.

---

## Folie 33 – Fragen? / Kontakt

- Abschlussfolie mit Kontaktmöglichkeiten:

  - Bei weiteren Fragen:  
    **E-Mail:** `dachs-admin@hs-esslingen.de`
  - Für Support-Tickets:  
    **Supportportal:** <https://www.bwhpc.de/supportportal/>

- Förderhinweis: **Förderträger: <http://www.bwhpc.de>** (Logo-Einblendung).

---

_Ende der vollständigen Zusammenfassung aller 33 Folien der „2nd bwUniCluster & DACHS User Workshop – HPC @ HAW“-Präsentation vom 29.07.2025._
