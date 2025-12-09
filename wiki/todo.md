🟧 TICKET 1 — Müll-Chunks vor LLM filtern
Titel

Filter meaningless Chunks before semantic annotation

Beschreibung

Die Statistik zeigt, dass ~20–30 % aller Chunks keinen fachlichen Inhalt enthalten (z. B. ".", Kapitelnummern, Seitenfragmente, Tabellenfragmente).
Diese Chunks führen regelmäßig zu leeren Feldern in domain, content_type, artifact_role und sinnlosen summary_short-Werten.

Diese Chunks dürfen nicht ans LLM geschickt werden.

Akzeptanzkriterien

Chunks mit weniger als 5 Zeichen werden ohne LLM annotiert.

Chunks, die nur aus Ziffern, Punkt, Komma, Leerzeichen oder Bindestrichen bestehen, werden ohne LLM annotiert.

Annotation für diese Chunks enthält:

artifact_role=["structural"]

trust_level="low"

leere Listen für alle anderen Felder

Technische Aufgaben

Datei öffnen:
scripts/annotate_semantics.py

In process_file(), vor classify_chunk(), Filterregeln einbauen.

Implementation exakt wie im Analysevorschlag.

🟧 TICKET 2 — Heading-Chunks mit erweitertem Kontext annotieren
Titel

Improve semantic annotation of heading-only chunks using neighbor context

Beschreibung

Heading-Chunks (z. B. "12.4.2 Hierarchical Clustering") enthalten nicht genug Text, um Domain, Content-Type oder artifact_role korrekt zu bestimmen.
Ohne Kontext bleiben Domain & artifact_role häufig leer.

Diese Chunks sollen automatisch mit erweitertem Kontext (nächster und ggf. übernächster Chunk) an das LLM übergeben werden.

Akzeptanzkriterien

Wenn meta.has_heading == True und content < 40 Zeichen:
→ mindestens der nächste Chunk wird als Kontext übergeben.

Optional: zusätzlich der zweite Folgechunk, falls vorhanden.

Domain- und artifact_role-Quote verbessert sich messbar.

Technische Aufgaben

Datei öffnen:
scripts/annotate_semantics.py

In process_file() Heading-Erkennung implementieren:
is_heading = rec["meta"].get("has_heading", False)

Kontextvariablen next_text und next2_text erweitern.

Kontext an die Funktion classify_chunk() übergeben.

🟧 TICKET 3 — artifact_role Defaults für strukturelle Chunks
Titel

Assign default artifact_role for structural chunks (heading/table/figure)

Beschreibung

artifact_role ist in 65 % der Chunks leer.
Viele dieser Chunks sind aber klar strukturelle Elemente wie:

Überschriften

Tabellenanfänge

Abbildungsbeschriftungen

Diese sollen standardmäßig Rollen erhalten, ohne dass das LLM bemüht wird.

Akzeptanzkriterien

Chunk mit meta.has_heading == true erhält artifact_role=["heading"]

Chunk mit meta.has_table == true erhält artifact_role=["table"]

Das passiert zusätzlich zur normalen LLM-Annotation.

artifact_role-Füllquote steigt auf >50 %

Technische Aufgaben

Datei öffnen: scripts/annotate_semantics.py

In normalize_semantic_result() Default-Append implementieren.

Keine bestehenden Rollen überschreiben.

🟧 TICKET 4 — summary_short für strukturelle Chunks unterdrücken
Titel

Suppress summary_short generation for non-informative structural chunks

Beschreibung

23 % der summary_short Werte sind <10 Zeichen.
Ursache: Überschriften, Tabellenfragmente, oder so kurze Chunks, dass keine echte Zusammenfassung existiert.

Diese Summaries sollen nicht erzeugt werden.

Akzeptanzkriterien

Bei Headings, Tabellen, extrem kurzen Texten (<40 Zeichen):
→ summary_short wird auf "" gesetzt.

Keine Mini-Summaries wie ".", "–", "Table", "Heading", etc.

Technische Aufgaben

Datei öffnen: scripts/annotate_semantics.py

In normalize_semantic_result() entsprechende Abfrage implementieren.

LLM-Antworten ggf. überschreiben, wenn strukturelle Chunks.

🟧 TICKET 5 — Prompt härten für nicht annotierbare Chunks
Titel

Extend system prompt to force empty JSON for meaningless chunks

Beschreibung

Das LLM versucht manchmal, auch bei inhaltslosen Chunks sinnlose Klassifikationen zu erzeugen.
Der Prompt muss klar definieren, wie bei „non-meaningful content“ zu antworten ist.

Akzeptanzkriterien

system_prompt enthält eine Regel wie:

If theft (less than 5 characters,
only punctuation, or only numbers), return empty lists and an empty summary.


LLM soll zuverlässig „leere“ JSON-Objekte erzeugen.

Technische Aufgaben

Datei öffnen: scripts/annotate_semantics.py

system_prompt erweitern (in LLMSemanticClassifier.classify_chunk()).

Keine Logik im Prompt ändern, nur Ergänzung.

🟧 TICKET 6 — Hook für zukünftigen FAISS-Kontext einbauen
Titel

Add placeholder hook for FAISS similarity context inside LLM prompt builder

Beschreibung

Später soll das LLM ähnliche Chunks per FAISS finden und als Kontext nutzen können.
Dafür ist ein klarer Einbaupunkt nötig.

Akzeptanzkriterien

Im Prompt-Aufbau existiert ein kommentierter Codeblock:

# TODO: Insert FAISS neighbor retrieval here


Dieser Block steht VOR dem finalen prompt assembly.

Kein funktionaler Code nötig – nur Platzhalter.

Technische Aufgaben

Datei öffnen: scripts/annotate_semantics.py

Suche den Bereich, wo user_prompt gebaut wird.

TODO-Kommentar einfügen.

🟧 TICKET 7 — Verbesserung der Sprache (Language fallback)
Titel

Improve language assignment for low-information chunks

Beschreibung

Chunks ohne alphabetische Zeichen (nur Zahlen/Punkt/Tabellen) werden fälschlich als „en“ erkannt.
Diese Chunks sollen language="unknown" erhalten.

Akzeptanzkriterien

Bei allen nicht annotierbaren Chunks → Sprache = "unknown"

Sprache nicht vom LLM korrigieren lassen.

Technische Aufgaben

In process_file() direkt vor dem Output:
Wenn Müll-Chunk → Sprache überschreiben mit "unknown".