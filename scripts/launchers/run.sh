#!/bin/bash
# Multi-Agent Orchestration - Runner (macOS/Linux)

# Wechsle ins Projekt-Root (Startskripte liegen nun in scripts/launchers/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Wechsle ins Projekt-Root
cd "$PROJECT_ROOT" || {
    echo "FEHLER: Konnte nicht ins Projekt-Root wechseln!"
    exit 1
}

# Prüfe, ob wir im richtigen Verzeichnis sind
if [ ! -f "requirements.txt" ]; then
    echo "FEHLER: requirements.txt nicht gefunden!"
    echo "Aktuelles Verzeichnis: $(pwd)"
    echo "Erwartetes Verzeichnis sollte requirements.txt enthalten."
    exit 1
fi

echo "========================================"
echo "Multi-Agent Orchestration Workshop"
echo "========================================"
echo "Projekt-Verzeichnis: $PROJECT_ROOT"
echo ""

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "FEHLER: Python nicht gefunden!"
        echo "Bitte Python 3.9+ installieren"
        exit 1
    fi
    PYTHON_CMD=python
else
    PYTHON_CMD=python3
fi

# Stelle sicher, dass Python 3.9+ ist
if ! $PYTHON_CMD - <<'PY'
import sys
sys.exit(0 if (sys.version_info >= (3, 9)) else 1)
PY
then
    echo "FEHLER: Python 3.9+ benötigt (gefunden: $($PYTHON_CMD --version 2>&1))"
    exit 1
fi

# Aktiviere das virtuelle Environment
if [ -d "venv" ]; then
    echo "[1/4] Virtual Environment gefunden"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "[1/4] Virtual Environment gefunden (.venv)"
    source .venv/bin/activate
else
    echo "[1/4] Erstelle virtuelles Environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "FEHLER: Virtual Environment konnte nicht erstellt werden!"
        exit 1
    fi
    source venv/bin/activate
fi

# .env Datei erstellen, falls nicht vorhanden
if [ ! -f ".env" ]; then
    echo "[2/4] Erstelle .env Datei..."
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "WICHTIG: Bitte .env Datei öffnen und OPENAI_API_KEY eintragen!"
        echo ""
    else
        echo "OPENAI_API_KEY=" > .env
        echo "WICHTIG: Bitte .env Datei öffnen und API-Key eintragen!"
        echo ""
    fi
else
    echo "[2/4] .env Datei vorhanden"
fi

# Upgrade pip und installiere Dependencies
echo "[3/4] Installiere Abhängigkeiten (dauert 1-2 Minuten)..."
SITE_PACKAGES="$($PYTHON_CMD -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || true)"
if [ -n "$SITE_PACKAGES" ]; then
    # pip kann nach abgebrochenen Installs eine defekte "~penai*" Distribution warnen; cleanen wir vorab.
    rm -rf "$SITE_PACKAGES"/~penai* 2>/dev/null || true
fi
$PYTHON_CMD -m pip install --upgrade pip --quiet > /dev/null 2>&1
$PYTHON_CMD -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "FEHLER: Installation fehlgeschlagen!"
    exit 1
fi

# Starte Streamlit
echo "[4/4] Starte App..."
echo ""
echo "========================================"
echo "App startet jetzt im Browser!"
echo "Zum Beenden: Strg+C"
echo "========================================"
echo ""

$PYTHON_CMD -m streamlit run app/app.py
