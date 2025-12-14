# Workshop-Leitfaden für Moderatoren
## Multi-Agent Workflow Orchestration - Zeitplan für 60 Minuten

Ziel: Workshop in exakt 60 Minuten durchführen. Teilnehmer arbeiten direkt mit der App und folgen dem Teilnehmer-Skript.

Für eine „Folien + Sprechtext“-Variante (zum Durchklicken im Workshop) siehe: `docs/moderators/FOLIENSKRIPT_WORKSHOP.md`.

---

## Vorbereitung (10 Minuten vor Start)

### Technische Prüfung

Stelle sicher, dass die Streamlit-App läuft. Starte bei Bedarf `streamlit run app.py`. Öffne den Browser unter http://localhost:8501. Führe einen kurzen Test mit dem "Starten"-Button aus, um die API-Key-Funktionalität zu prüfen.

### Materialien bereitstellen

Bereite ein Test-PDF vor (2-3 Seiten). Stelle das Teilnehmer-Skript bereit (ausgedruckt oder als Link zu `docs/participants/TEILNEHMER_SKRIPT.md`). Prüfe Beamer/Laptop-Verbindung für eventuelle Präsentationen.

### App-Funktionalität prüfen

Verifiziere: Sidebar ist funktionsfähig, alle drei Pipeline-Optionen (LangChain, LangGraph, DSPy) sind verfügbar, Upload-Funktion funktioniert, Button "Alle Pipelines vergleichen" funktioniert.

---

## Workshop-Ablauf (60 Minuten)

### Minute 0-2: Begrüßung & Setup

Begrüße die Teilnehmer und stelle das Ziel vor: Kennenlernen von LangChain, LangGraph und DSPy. Die Teilnehmer arbeiten direkt mit der Streamlit-App und folgen dem Teilnehmer-Skript.

Teilnehmer öffnen die App (Link oder lokal), lesen die Hilfe-Sektion und erkunden die Sidebar. Überwache, dass alle Teilnehmer die App erfolgreich geöffnet haben. Biete bei Problemen sofortige Unterstützung.

---

### Minute 2-12: Einführung

#### Konzept vorstellen

Erkläre Multi-Agent Orchestration: Die Koordination mehrerer LLM-Agenten in einer strukturierten Pipeline. Präsentiere das Beispiel: Research Paper Analyzer mit vier Agenten (Reader, Summarizer, Critic, Integrator).

Demonstriere die Pipeline live in der App. Lade ein kurzes PDF hoch und erkläre die Struktur: Reader extrahiert Notizen, Summarizer erstellt Zusammenfassung, Critic bewertet Qualität, Integrator erstellt finale Summary.

Stelle eine Einstiegsfrage: Wer hat bereits mehrere LLM-Calls nacheinander verwendet? Welche Probleme traten dabei auf? Dies aktiviert Vorwissen und schafft einen Diskussionseinstieg.

#### Framework-Überblick

Präsentiere eine Übersichtstabelle mit den drei Frameworks:

- LangChain: Prozedural mit Chains, einfach und linear
- LangGraph: Graph-based, robust und nachvollziehbar
- DSPy: Deklarativ, automatisches Optimieren

Erkläre die Paradigmen-Unterschiede kurz: Prozedural bedeutet explizite Kontrollfluss-Definition. Graph-based bedeutet Struktur als Graph mit hoher Transparenz. Deklarativ bedeutet Zielbeschreibung statt Prozessbeschreibung.

Formuliere das Workshop-Ziel: Den gleichen Workflow mit allen drei Frameworks implementieren und vergleichen.

#### App-Struktur demonstrieren

Zeige die wichtigsten Elemente der App: Sidebar mit Settings, Presets und Model-Auswahl, Pipeline-Auswahl (LangChain, LangGraph, DSPy), Buttons ("Starten", "Alle Pipelines vergleichen", "DSPy Teleprompt Gain").

Weise die Teilnehmer an, dem Teilnehmer-Skript zu folgen (`docs/participants/TEILNEHMER_SKRIPT.md`), beginnend mit Teil 2.

---

### Minute 12-24: Teil 2 - LangChain

Die Teilnehmer arbeiten selbstständig an den Aufgaben 2.1 bis 2.3. Gehe durch den Raum und unterstütze bei Problemen. Beantworte Fragen und stelle sicher, dass alle mitkommen.

#### Aufgabe 2.1: Pipeline ausführen und Code verstehen (4 Minuten)

Teilnehmer laden ein Dokument hoch, führen die LangChain-Pipeline aus und analysieren die Ergebnisse. 

Dann öffnen sie `workflows/langchain_pipeline.py` und schauen sich die Funktion `run_pipeline` an (Zeilen 17-81). Zeige ihnen, wie der Code die Agenten sequenziell aufruft.

Nach 4 Minuten: Kurze Zwischenfrage: "Welcher Schritt benötigt die längste Laufzeit?" Typischerweise sind dies Reader oder Summarizer aufgrund des höheren Textverarbeitungsaufwands.

Unterstütze Teilnehmer, die Probleme haben: Prüfe, ob Dokument hochgeladen wurde. Bei Fehlern: Erneuter Versuch oder kleineres Dokument verwenden.

#### Aufgabe 2.2: Agenten-Prompts anpassen (5 Minuten)

Teilnehmer öffnen `agents/summarizer.py` und ändern den Prompt. Zum Beispiel: Ändern "200-300 words" zu "50-100 words". Speichern und Pipeline erneut ausführen.

Wichtig: Die Teilnehmer sehen direkt, wie Code-Änderungen das Verhalten beeinflussen. Das ist der Kernpunkt - sie experimentieren mit dem Code.

Schnellere Teilnehmer können auch den Critic-Prompt ändern (neue Kategorie hinzufügen im Rubric).

Hinweis: Falls die Änderung nicht übernommen wird, warte ein paar Sekunden oder starte die App neu.

#### Aufgabe 2.3: Reihenfolge ändern (3 Minuten)

Teilnehmer ändern die Reihenfolge in `workflows/langchain_pipeline.py`. Versuchen Critic vor Summarizer auszuführen. 

Beobachtung: Es funktioniert nicht richtig, weil der Critic die Summary braucht. Das zeigt die impliziten Abhängigkeiten in LangChain - man sieht sie nicht explizit im Code.

#### Aufgabe 2.4: Limitationen diskutieren (optional, falls Zeit)

Falls noch Zeit ist, diskutieren Teilnehmer in Zweiergruppen Probleme sequenzieller Ausführung: Fehlerbehandlung, Debugging-Fähigkeiten. Sammle Ergebnisse: "Was habt ihr durch die Code-Experimente gelernt?" Höre dir einige Antworten an.

---

### Minute 24-39: Teil 3 - LangGraph

Kündige den Wechsel zu LangGraph an: Graph-basierte Orchestrierung als nächster Schritt.

#### Aufgabe 3.1: Graph-Pipeline ausführen und Code verstehen (4 Minuten)

Teilnehmer führen die LangGraph-Pipeline aus und analysieren die aktuelle Graph-Visualisierung.

Dann öffnen sie `workflows/langgraph_pipeline.py` und schauen sich `_build_langgraph_workflow` an (Zeilen 186-210). Zeige ihnen, wie der Graph nun Translator-, Keyword- und Judge-Aggregator-Nodes enthält und wie Conditional Edges mit `_critic_post_path` die Reihenfolge dynamisch steuern.

Demonstriere die Graph-Struktur live: "Input - Retriever - Reader - Summarizer - Translator - Keyword - Critic → Quality/Judge (kurze Summary) bzw. zurück zum Summarizer bei schlechtem Critic Score - Judge Aggregator - Integrator - Output." Die Visualisierung macht die Zweige direkt sichtbar.

Hinweis: Falls Teilnehmer die Graph-Visualisierung nicht sehen, weise darauf hin, dass sie nach unten scrollen müssen.

#### Aufgabe 3.2: Translator & Keyword Nodes erkunden (6 Minuten)

Diese Nodes existieren bereits und liefern zusätzliche Outputs (`summary_translated`, `keywords`). Zeige, wie `_execute_translator_node` gezielt eine deutsch-englische Kurzfassung mit Kürzungsstufen erzeugt und wie `_execute_keyword_node` häufige Begriffe extrahiert.

Die Teilnehmer dürfen:
1. Die Sprache bzw. den Stil im Translator ändern (z.B. `translator_language`, `translator_style` im Config-Dict).
2. Die Keyword-Logik erweitern (z.B. Stopwords, mehr Keywords).
3. Die zusätzlichen State-Felder auslesen (z.B. `summary_translated`, `keywords`) und in der App vergleichen.

#### Aufgabe 3.3: Conditional Flow und Judge-Aggregator (5 Minuten)

Zeige die neue Funktion `_critic_post_path`, die:
- bei kurzen Summaries (`len(summary)<100`) direkt zu `judge` springt,
- bei schlechtem Critic-Score (`<0.5`) den Summarizer noch einmal ausführt (Loop-Limit beachten),
- ansonsten zu `quality`.

Betone, dass Judge und Aggregator jetzt explizit Nodes sind: `judge` liefert einen Wert 0-5, `aggregator` verrechnet Judge, Quality und Critic zu einem Gesamtwert. Teilnehmer können z.B. die Schwellenwerte verändern oder weitere Metriken ergänzen.

#### Aufgabe 3.4: Unterschiede zwischen LangChain und LangGraph sehen (5 Minuten)

Teilnehmer vergleichen die Code-Dateien direkt. Öffnen beide Pipeline-Dateien nebeneinander.

**LangChain** (`workflows/langchain_pipeline.py`, Zeilen 33-52): Einfache Funktionsaufrufe nacheinander, keine explizite Struktur, keine Fehlerbehandlung zwischen Schritten.

**LangGraph** (`workflows/langgraph_pipeline.py`, Zeilen 186-210): Expliziter Graph, der Code verwaltet State explizit, zusätzliche Nodes (Translator, Keyword, Aggregator) und Conditional Edges steuern den Flow.

Erkläre: "Der Hauptunterschied ist, dass LangGraph die Struktur explizit macht. Ihr könnt diese sehen, modifizieren, erweitern."

Teilnehmer vergleichen auch: Quality- und Judge-Nodes gibt es nur in LangGraph. Warum? In LangChain müsste man sie manuell einfügen. In LangGraph sind sie einfach Nodes im Graph.

Optional: Teilnehmer nutzen "Alle Pipelines vergleichen" für Metriken-Vergleich. Dabei geht es nicht nur um Unigram-F1, sondern um das neue ROUGE-1/ROUGE-2/ROUGE-L-Reporting plus Coverage- und Coherence-Werte – das macht Unterschiede zwischen Prompt-Varianten und Conditional Flows nachvollziehbar.

---

### Minute 39-54: Teil 4 - DSPy

Kündige DSPy an: Deklarative und selbstoptimierende Pipeline.

#### Aufgabe 5.1: DSPy Base und Code verstehen (5 Minuten)

Teilnehmer führen DSPy ohne Teleprompting aus. Öffnen `workflows/dspy_pipeline.py` und schauen sich die Signatures an (Zeilen 80-104).

Erkläre den Unterschied: In LangChain/LangGraph definiert der Code Prompts explizit (z.B. in `agents/reader.py`). In DSPy definiert der Code nur Signatures - der Code beschreibt Input und Output, nicht den exakten Prompt.

Die Teilnehmer vergleichen `agents/reader.py` (expliziter Prompt) mit `workflows/dspy_pipeline.py` (Signature). Das zeigt das deklarative Paradigma.

#### Aufgabe 5.2: Signature anpassen (5 Minuten)

Teilnehmer ändern eine Signature, z.B. die `Summarize` Signature. Ändern die Beschreibung von "200-300 word" zu "100-150 word". Führen DSPy erneut aus und beobachten die Änderung.

Wichtig: Die Teilnehmer sehen, dass sich die Outputs ändern, auch wenn kein expliziter Prompt angepasst wurde. Das Framework generiert den Prompt automatisch basierend auf der Signature.

Schnellere Teilnehmer können versuchen, ein neues Feld zur Signature hinzuzufügen (z.B. TARGET_LENGTH).

Hinweis: Falls eine Warnung erscheint, dass DSPy nicht installiert ist, erkläre, dass das ok ist. Die App nutzt einen Stub-Modus mit Dummy-Output und einer klaren `meta`-Nachricht, damit die Demo nicht abstürzt und die Teilnehmer trotzdem sehen, wie der Mechanismus funktioniert.

#### Aufgabe 5.3: Teleprompting (5 Minuten)

Warnung vorab: "Achtung: Ausführung dauert 1-2 Minuten. Teleprompting optimiert Prompts basierend auf Trainingsdaten."

Teilnehmer aktivieren "DSPy optimieren", prüfen den Dev-Set Pfad (`dev-set/dev.jsonl`) und klicken auf "DSPy Teleprompt Gain". 

Ergänzend erwähnen: Das Dev-Set wurde auf 15 Beispiele erweitert, die verschiedene `target_length`-Tags (short/medium/long) und `prompt_focus`-Tags (Results/Method/Conclusion) enthalten. Dadurch sehen die Teilnehmer live, wie DSPy die Prompt-Strategie anpasst, welche Beispieltypen schneller trainieren und wo der Latenz-gegen-Qualität-Trade-off entsteht. Die Teleprompt-Metriken (`teleprompt_target_lengths`, `teleprompt_prompt_focus`, `teleprompt_gain`, `teleprompt_choice`) erscheinen im Ergebnis und in der erweiterten `meta`-Zusammenfassung.

Während der Wartezeit (2 Minuten) erkläre den Prozess: "DSPy testet verschiedene Prompts. Es nutzt das Dev-Set (Trainingsdaten mit Beispielen). Es evaluiert jeden Prompt gegen die Beispiele und wählt die optimale Variante. Dies ist Few-Shot-Bootstrapping - das System lernt aus Beispielen und optimiert sich selbst."

Falls Code-Zugriff vorhanden: Zeige, wo Teleprompting konfiguriert ist. Suche nach "teleprompt" in `workflows/dspy_pipeline.py`. Erkläre, wie das Dev-Set verwendet wird.

Wichtig: Nutze die Wartezeit produktiv. Erkläre, was passiert. Frage, ob Teilnehmer Fragen haben.

Nach Teleprompting: "Analysiert die Vergleichstabelle. Wie viel besser ist Teleprompt?" Typischerweise: positiver F1 Gain, erhöhte Latenz (klassischer Trade-off). Die 15 Dev-Beispiele spiegeln unterschiedliche Ziel-Längen (`target_length`) und Fokus-Schwerpunkte (`prompt_focus`), sodass sichtbar wird, wie Teleprompting seine Prompts je nach Beispielart optimiert; `meta` enthält zusätzlich `teleprompt_gain`, `teleprompt_choice`, `teleprompt_target_lengths` und `teleprompt_prompt_focus`.

Teilnehmer vergleichen Base vs. Teleprompt Outputs in den Tab-Reitern. Was ist besser? Meist: bessere Coverage, bessere Kohärenz.

---

### Minute 54-60: Teil 6 - Experimentieren und Vergleich

#### Aufgabe 6.1: Unterschiede durch Code-Änderungen sehen (4 Minuten)

Teilnehmer machen ein Experiment: Ändern den Summarizer-Prompt in `agents/summarizer.py`. Führen dann alle drei Pipelines aus.

Beobachtung: Sehen LangChain und LangGraph die Änderung? Ja. Sieht DSPy die Änderung? Nein, weil DSPy seinen eigenen Prompt generiert.

Das zeigt den fundamentalen Unterschied: In LangChain/LangGraph kontrolliert ihr Prompts direkt. In DSPy beschreibt ihr nur das Ziel.

Erkläre: "Das ist das deklarative Paradigma. Ihr beschreibt, was erreicht werden soll, nicht wie."

#### Aufgabe 6.2: Vergleich dokumentieren (2 Minuten)

Teilnehmer füllen die Entscheidungsmatrix aus basierend auf ihren Code-Experimenten. Fokus auf das, was sie durch Code-Änderungen gelernt haben.

#### Abschluss (1 Minute)

Abschlussformulierung: "Danke für eure Teilnahme. Ihr habt heute nicht nur die Frameworks kennengelernt, sondern auch praktisch mit dem Code experimentiert. Das zeigt euch die Unterschiede viel besser als nur Theorie. Experimentiert weiter, ändert Code, seht, was passiert."

Frage: "Gibt es noch Fragen?" Beantworte diese kurz, bleibe bei der Zeitvorgabe.

---

## Timing-Strategien

### Zu schnell (3 Minuten Puffer)

Nutze zusätzliche Zeit für: Vertiefte Diskussionen in Teil 5, Bonus-Aufgaben aus dem Teilnehmer-Skript (Teilnehmer können schwierigere Varianten bearbeiten), Code-Struktur-Demonstration (falls verfügbar), konkrete Use Cases diskutieren.

### Zu langsam (3 Minuten sparen)

Kürze: Aufgabe 2.2 auf 2 Presets statt 3, Aufgabe 3.2 auf Graph-Visualisierung ohne Diskussion, Aufgabe 4.3 auf kurze Diskussion ohne Dokumentation, Reflexion (Aufgabe 5.3) kann entfallen.

### Technische Probleme

Alternativen: Vorgefertigte Screenshots zeigen, Code-Walkthrough ohne Live-Execution, Diskussion vertiefen während der Problemlösung.

---

## Wichtige Hinweise

### Schwierigkeitsgrade

Die Aufgaben im Teilnehmer-Skript haben unterschiedliche Schwierigkeitsgrade (Einfach, Mittel, Schwer). Stelle sicher, dass alle Teilnehmer die einfachen Varianten schaffen. Schnellere Teilnehmer können die schwierigeren Varianten bearbeiten. Biete zusätzliche Herausforderungen an, falls nötig.

### Kommunikation

Sprich klar und in angemessenem Tempo, verwende kurze Sätze. Wiederhole wichtige Punkte mehrmals. Stelle regelmäßig Fragen: "Hat jemand Fragen?" nach jedem größeren Abschnitt. Gehe durch den Raum und unterstütze Teilnehmer aktiv.

Besonders wichtig: Wenn Teilnehmer Code ändern, gehe rum und schaue, ob sie Hilfe brauchen. Code-Syntax-Fehler sind häufig - helfe schnell, damit sie weitermachen können.

### App-Probleme

Bei Timeout: "Das kann vorkommen. Einfach nochmal versuchen." Bei fehlendem DSPy: "Das ist ok, ihr seht eine Warnung. Das Konzept ist wichtig." Bei langsamer Ausführung: "Das ist normal, besonders bei 'Detail'-Preset."

Bei Code-Problemen: "Prüft die Syntax. Falls die Änderung nicht übernommen wird, wartet ein paar Sekunden oder startet die App neu."

Erkläre, wo Teilnehmer Hilfe finden: Hilfe-Sektion der App, Workshop-Team fragen, Teilnehmer-Skript mit Tipps, Code-Kommentare in den Dateien.

### Gruppenarbeit

Bilde Zweiergruppen nach Minute 2 oder 3. Sammle Zwischenergebnisse nach jedem größeren Abschnitt. Beziehe alle Teilnehmer ein, nicht nur die Schnellen. Biete unterschiedliche Herausforderungen an, damit alle auf ihrem Niveau arbeiten können.

---

## Checkliste während des Workshops

- Minute 2: Alle Teilnehmer haben App geöffnet
- Minute 12: Teilnehmer starten mit LangChain
- Minute 24: Teilnehmer starten mit LangGraph
- Minute 39: Teilnehmer starten mit DSPy
- Minute 43: Teleprompting läuft (1-2 Minuten Wartezeit)
- Minute 54: Vergleich wird diskutiert
- Minute 60: Workshop beendet

---

## Nach dem Workshop

Optional: Feedback sammeln, Fragen beantworten, Code-Repository verlinken, Materialien (Folien, Skripte) teilen.

Viel Erfolg beim Workshop!
