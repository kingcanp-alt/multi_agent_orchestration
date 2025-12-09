# Workshop Checkliste
## Vorbereitung für den Multi-Agent Orchestration Workshop

---

## Code-Bereitstellung

**WICHTIG:** Siehe `WORKSHOP_CODE_BEREITSTELLUNG.md` (im selben Ordner) für detaillierte Anleitung!

**Empfohlene Option:** GitHub-Repo + Online-App als Fallback

---

## 1 Woche vorher

- [ ] **Code-Bereitstellung** (SIEHE `WORKSHOP_CODE_BEREITSTELLUNG.md` im selben Ordner)
  - [ ] GitHub-Repo erstellt und Code hochgeladen
  - [ ] Backup-Branch erstellt (`workshop-backup`)
  - [ ] README.md mit Setup-Anleitung aktualisiert
  - [ ] ZIP-Datei vorbereitet (als Alternative)
  - [ ] Online-App deployt (optional, aber empfohlen als Fallback)
  - [ ] Links bereit (Repo, ZIP, App)

- [ ] **Technische Vorbereitung**
  - [ ] Streamlit App testen (`streamlit run app.py`)
  - [ ] Alle drei Pipelines erfolgreich ausführen
  - [ ] Test-Installation durchgeführt (wie Teilnehmer es machen würden)
  - [ ] OpenAI API Key prüfen (oder lokales Modell konfigurieren)
  - [ ] DSPy Installation prüfen (falls Teleprompting-Demo geplant)
  - [ ] Test-PDFs vorbereiten (2-3 kurze Research Papers)
  - [ ] Dev-Set prüfen (`eval/dev.jsonl` existiert und ist valide)

- [ ] **Materialien**
  - [ ] Präsentationsfolien erstellen (optional)
  - [ ] Code-Snippets für Walkthrough vorbereiten
  - [ ] Vergleichstabelle mit Metriken vorbereiten (optional: vorgefertigte Ergebnisse)

- [ ] **Kommunikation**
  - [ ] Teilnehmer informieren über technische Voraussetzungen (falls nötig)
  - [ ] Raum/Setup prüfen (Beamer, Internet, ggf. Laptops für Teilnehmer)

---

## 1 Tag vorher

- [ ] **Finale Tests**
  - [ ] Live-Demo komplett durchspielen
  - [ ] Alle Buttons in Streamlit App testen
  - [ ] Backup-Plan vorbereiten (falls API-Limits oder Internetprobleme)
  - [ ] Screenshots von Ergebnissen machen (als Backup)

- [ ] **Code-Review**
  - [ ] Code-Kommentare aktualisieren (für Walkthrough)
  - [ ] Fehlerbehandlung testen (was passiert bei fehlerhaften Inputs?)
  - [ ] Timing-Logs prüfen (Telemetry funktioniert)

- [ ] **Präsentation**
  - [ ] Folien finalisieren
  - [ ] Timing der Präsentation durchgehen
  - [ ] Q&A-Antworten vorbereiten

---

## Am Workshoptag

### Vor dem Workshop (30 Min vorher)

- [ ] **Code-Zugriff bereitstellen**
  - [ ] GitHub-Repo-Link bereit (Chat, Slide, Email)
  - [ ] ZIP-Download-Link bereit (falls Alternative)
  - [ ] Online-App-Link bereit (falls Fallback)
  - [ ] Setup-Anleitung erklärt (5 Minuten einplanen)

- [ ] **Setup prüfen**
  - [ ] Laptop an Beamer anschließen
  - [ ] Streamlit App starten (im Browser öffnen)
  - [ ] Internet-Verbindung testen
  - [ ] API-Keys funktionieren (kurzer Test-Call)
  - [ ] Beispiel-PDFs hochladen und testen

- [ ] **Backup vorbereiten**
  - [ ] Screenshots/Video der Demo (falls Live-Demo scheitert)
  - [ ] Vorgefertigte Ergebnisse als JSON (für Vergleichstabelle)
  - [ ] Offline-Modus vorbereiten (falls Internet ausfällt)

### Während des Workshops

- [ ] **Teil 1: Motivation & Konzept** (10 Min)
  - [ ] Problemstellung erklären
  - [ ] Framework-Vergleich zeigen
  - [ ] Kurze Architektur-Demo

- [ ] **Teil 2: LangChain** (15 Min)
  - [ ] Code-Walkthrough
  - [ ] Live-Demo
  - [ ] Hands-on Aufgabe (Teilnehmer experimentieren)

- [ ] **Teil 3: LangGraph** (15 Min)
  - [ ] StateGraph-Konzept erklären
  - [ ] Graph-Visualisierung zeigen
  - [ ] Vergleich mit LangChain
  - [ ] Hands-on Aufgabe

- [ ] **Teil 4: DSPy** (15 Min)
  - [ ] Deklaratives Paradigma erklären
  - [ ] Teleprompting-Demo
  - [ ] Trade-offs diskutieren

- [ ] **Teil 5: Fazit** (5 Min)
  - [ ] Quantitative Vergleich
  - [ ] Entscheidungsmatrix
  - [ ] Q&A

### Nach dem Workshop

- [ ] **Feedback sammeln**
  - [ ] Fragen der Teilnehmer notieren
  - [ ] Verbesserungsvorschläge dokumentieren
  - [ ] Technische Probleme notieren (für zukünftige Workshops)

---

## Troubleshooting Guide

### Problem: API-Limits erreicht
**Lösung**: 
- Vorgefertigte Ergebnisse zeigen
- Lokales Modell nutzen (falls konfiguriert)
- API-Keys rotieren (falls mehrere vorhanden)

### Problem: Internet-Verbindung ausgefallen
**Lösung**:
- Offline-Modus mit lokalem Modell
- Screenshots/Videos der Demo zeigen
- Code-Walkthrough fokussieren (keine Live-Execution)

### Problem: Streamlit App crasht
**Lösung**:
- Logs prüfen (`streamlit run app.py --logger.level=debug`)
- Backup: Code direkt im Terminal ausführen
- Minimal-Beispiel zeigen (ohne Streamlit)

### Problem: DSPy nicht installiert
**Lösung**:
- Stub-Modus erklären (wird bereits im Code gehandhabt)
- Konzept erklären, ohne Live-Demo
- Screenshots von Teleprompting-Ergebnissen zeigen

### Problem: Teilnehmer kommen nicht mit
**Lösung**:
- Tempo reduzieren
- Mehr Zeit für Hands-on Aufgaben
- Code-Snippets ausdrucken/teilen

---

## Erfolgs-Kriterien

Der Workshop war erfolgreich, wenn:
- Teilnehmer können Unterschiede zwischen Frameworks erklären
- Alle drei Pipelines wurden live demonstriert
- Teilnehmer haben mindestens eine Pipeline selbst getestet
- Vergleichs-Metriken wurden diskutiert
- Q&A-Runde hatte relevante Fragen

---

## Post-Workshop

- [ ] **Dokumentation aktualisieren**
  - [ ] README aktualisieren (falls nötig)
  - [ ] Code-Kommentare verbessern (basierend auf Fragen)
  - [ ] Known Issues dokumentieren

- [ ] **Materialien teilen**
  - [ ] Präsentationsfolien auf GitHub/Teams hochladen
  - [ ] Code-Repository verlinken
  - [ ] Workshop-Feedback sammeln

---

Viel Erfolg!
