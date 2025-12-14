#!/bin/bash
# Multi-Agent Orchestration - Runner (macOS/Linux)

# Wechsle ins Projekt-Root (Startskripte liegen nun in launchers/)
cd "$(dirname "$0")/.."

echo "========================================"
echo "Multi-Agent Orchestration Workshop"
echo "========================================"
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
