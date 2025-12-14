# Workshop: Code-Bereitstellung für Teilnehmer
## Wie bekommen die Teilnehmer den Code?

---

## Option 1: GitHub-Repo (Empfohlen)

### Vorbereitung (vor dem Workshop)

1. **GitHub-Repo erstellen** (falls noch nicht vorhanden):
   - Erstellt ein neues Repository auf GitHub
   - Pusht den Code hoch
   - Prüft, dass alle notwendigen Dateien drin sind

2. **Backup-Branch erstellen**:
   ```bash
   git checkout -b workshop-backup
   git push origin workshop-backup
   ```
   Falls Teilnehmer etwas kaputt machen, könnt ihr schnell wiederherstellen.

3. **README anpassen**:
   - Klare Setup-Anweisungen
   - Link zu `WORKSHOP_QUICK_START.md`
   - API-Key-Anleitung

### Teilnehmer-Setup (während Workshop)

**Am Workshop-Tag - SUPER EINFACH:**

1. **Teilnehmer klonen das Repo:**
   ```bash
   git clone https://github.com/euer-username/multi_agent_orchestration.git
   cd multi_agent_orchestration
   ```

2. **Doppelklick-Start:**
   - **Windows:** Doppelklick auf `run.bat`
   - **Mac/Linux:** Doppelklick auf `run.sh` (oder: `chmod +x run.sh && ./run.sh`)

**Das war's!** Die App startet automatisch. Beim ersten Mal dauert es 1-2 Minuten (Installation), dann öffnet sich der Browser automatisch.

**Falls `.env` noch nicht vorhanden:** Das Skript erstellt sie automatisch. Teilnehmer müssen nur den API-Key eintragen.

**Vorteile:**
- Teilnehmer haben vollständigen Code-Zugriff
- Git erleichtert das Wiederherstellen nach Änderungen (`git checkout -- .`)
- Einfach zu aktualisieren (Pull)

**Nachteile:**
- Teilnehmer brauchen Git
- Setup dauert länger

---

## Option 2: ZIP-Datei

### Vorbereitung (vor dem Workshop)

1. **ZIP erstellen**:
   ```bash
   # Wichtig: venv NICHT inkludieren!
   zip -r workshop-code.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".env" "telemetry.csv"
   ```

2. **README.md in ZIP prüfen**: Klare Setup-Anleitung enthalten

3. **Bereitstellen**: 
   - Upload auf Cloud-Speicher (Dropbox, Google Drive, etc.)
   - Oder per Email/Dateifreigabe

### Teilnehmer-Setup (während Workshop)

1. ZIP herunterladen und entpacken
2. Terminal öffnen, in Ordner wechseln
3. Virtual Environment erstellen:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. API-Key setzen
5. `streamlit run app.py`

**Vorteile:**
- Einfach zu teilen
- Keine Git-Kenntnisse nötig
- Schnell verteilt

**Nachteile:**
- Keine einfache Wiederherstellung nach Änderungen
- Müssen manuell Backup machen

---

## Option 3: Nur App online (ohne Code-Zugriff)

### Vorbereitung (vor dem Workshop)

1. **App auf Server deployen**:
   - Streamlit Cloud
   - Heroku
   - Oder eigener Server

2. **Link bereitstellen**: Teilnehmer bekommen Link zur App

### Teilnehmer-Setup

1. Link öffnen
2. Fertig - keine Installation nötig

**Vorteile:**
- Keine Setup-Zeit
- Funktioniert sofort
- Keine lokalen Abhängigkeiten

**Nachteile:**
- **Keine Code-Experimente möglich!**
- Workshop wird weniger praktisch
- Teilnehmer können keine Prompts/Code ändern

**Wann sinnvoll:** Nur wenn Code-Experimente nicht möglich sind (Zeitmangel, technische Probleme)

---

## Option 4: Hybrid (Empfohlen für größere Gruppen)

### Setup

1. **App online deployen** (für alle)
2. **GitHub-Repo bereitstellen** (für die, die Code-Experimente machen wollen)

### Teilnehmer wählen

- **Nur App nutzen:** Teilnehmer ohne Code-Interesse oder Zeitmangel
- **Code-Experimente:** Teilnehmer mit Code-Zugriff und mehr Zeit

**Vorteile:**
- Flexibel
- Jeder kann nach seinem Tempo arbeiten
- Code-Experimente optional

---

## Was brauchen Teilnehmer wirklich?

### Minimum für Code-Experimente:
- Code-Dateien (`agents/*.py`, `workflows/*.py`)
- `app.py`
- `requirements.txt`
- `docs/participants/TEILNEHMER_SKRIPT.md`
- `docs/participants/CODE_EXPERIMENTE.md`

### Nicht nötig:
- `venv/` (wird lokal erstellt)
- `telemetry.csv` (wird automatisch erstellt)
- `.env` (Teilnehmer erstellen selbst)

---

## Empfohlener Ablauf (Workshop-Tag)

### Vor dem Workshop (30 Min vorher)

1. **GitHub-Repo prüfen**: Funktioniert das Klonen?
2. **Backup erstellen**: Sicherheitskopie des Codes
3. **Test-Installation**: Einmal komplett durchführen (wie Teilnehmer es machen würden)
4. **Link bereitstellen**: 
   - GitHub-Repo Link
   - Oder ZIP-Download-Link
   - Oder Online-App Link

### Am Workshop-Tag (5 Min Setup)

**Option A: GitHub-Repo**
```
"Bitte klont das Repo von GitHub. Link ist in der Chat/Slide."
- Repo klonen
- venv erstellen und aktivieren
- pip install -r requirements.txt
- API-Key setzen (falls lokal)
- streamlit run app.py
```

**Option B: ZIP-Datei**
```
"Bitte ladet die ZIP-Datei herunter. Link ist in der Chat/Slide."
- ZIP entpacken
- venv erstellen und aktivieren
- pip install -r requirements.txt
- API-Key setzen (falls lokal)
- streamlit run app.py
```

**Option C: Nur App**
```
"Bitte öffnet diesen Link: [URL]"
- Link öffnen
- Fertig!
```

### Während des Workshops

- **Code-Experimente sind optional**: Teilnehmer ohne Code können trotzdem mitmachen (nur App nutzen)
- **Hilfe anbieten**: Bei Setup-Problemen sofort helfen
- **Backup bereit halten**: Falls jemand Code kaputt macht, schnell wiederherstellen

---

## Checkliste für Moderatoren

### Vor dem Workshop:
- [ ] GitHub-Repo erstellt und getestet (oder ZIP vorbereitet)
- [ ] Backup-Branch/Backup-Ordner erstellt
- [ ] README.md mit Setup-Anleitung aktualisiert
- [ ] Link zum Repo/ZIP bereitgestellt
- [ ] Test-Installation durchgeführt (auf Windows und Mac)
- [ ] API-Key-Anleitung bereit (falls lokal nötig)

### Am Workshop-Tag:
- [ ] Link zum Repo/ZIP/App bereitgestellt (Chat, Slide, Email)
- [ ] Setup-Anleitung erklärt (5 Minuten)
- [ ] Hilfe bei Setup-Problemen angeboten
- [ ] Backup bereit (falls Code kaputt geht)

### Während Code-Experimenten:
- [ ] Teilnehmer erinnern: Git checkout für Wiederherstellung
- [ ] Code-Snippets aus `docs/participants/CODE_EXPERIMENTE.md` bereit
- [ ] Schnelle Hilfe bei Syntax-Fehlern

---

## Troubleshooting für Teilnehmer

### "Ich kann das Repo nicht klonen"
- **Prüfen**: Git installiert? (`git --version`)
- **Alternative**: ZIP-Datei nutzen

### "pip install schlägt fehl"
- **Prüfen**: Python Version? (3.9+)
- **Prüfen**: Virtual Environment aktiviert?
- **Lösung**: `pip install --upgrade pip` dann nochmal versuchen

### "API-Key nicht gefunden"
- **Lokal**: `.env` Datei erstellen oder Umgebungsvariable setzen
- **Online-App**: Kein API-Key nötig (wird serverseitig genutzt)

### "Code-Änderungen werden nicht übernommen"
- **Warten**: 10 Sekunden nach Speichern
- **Neu starten**: `streamlit run app.py` neu starten
- **Prüfen**: Editor hat wirklich gespeichert?

### "Ich habe Code kaputt gemacht"
- **Git**: `git checkout -- .` (setzt alle Änderungen zurück)
- **ZIP**: Dateien aus ZIP neu entpacken
- **Backup**: Moderatoren helfen

---

## Empfehlung

**Für den Workshop empfehle ich: Option 1 (GitHub-Repo) + Option 3 (Online-App) als Fallback**

**Warum?**
- GitHub-Repo ermöglicht Code-Experimente
- Git macht Wiederherstellung einfach (`git checkout -- .`)
- Online-App als Fallback für Teilnehmer mit Setup-Problemen
- Flexibel - jeder kann wählen

**Vorbereitung:**
1. GitHub-Repo erstellen
2. Backup-Branch erstellen
3. Online-App deployen (optional, aber empfohlen)
4. Beide Links bereitstellen

**Am Tag:**
- GitHub-Repo als Hauptoption
- Online-App als Alternative für schnelle Teilnehmer oder bei Problemen
