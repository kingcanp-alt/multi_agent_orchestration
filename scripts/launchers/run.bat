@echo off
setlocal enabledelayedexpansion
title Multi-Agent Orchestration - Workshop App
REM Wechsel ins Projekt-Root (Startskripte liegen nun in launchers\)
cd /d "%~dp0.."

echo ========================================
echo Multi-Agent Orchestration Workshop
echo ========================================
echo.

REM Pruefe Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo FEHLER: Python nicht gefunden!
        echo Bitte Python 3.9+ installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PYTHON_CMD=py -3
) else (
    set PYTHON_CMD=python
)

REM Pruefe Python-Version (>=3.9)
%PYTHON_CMD% -c "import sys; import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo FEHLER: Python 3.9+ benötigt. Gefunden:
    %PYTHON_CMD% --version
    pause
    exit /b 1
)

REM Venv anlegen, falls nicht vorhanden
if not exist "venv\Scripts\activate.bat" (
    echo [1/4] Erstelle virtuelles Environment...
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo FEHLER: Virtual Environment konnte nicht erstellt werden!
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual Environment gefunden
)

call "venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo FEHLER: Virtual Environment konnte nicht aktiviert werden!
    pause
    exit /b 1
)

REM .env Datei erstellen, falls nicht vorhanden
if not exist ".env" (
    echo [2/4] Erstelle .env Datei...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo WICHTIG: Bitte .env Datei oeffnen und OPENAI_API_KEY eintragen!
        echo.
    ) else (
        echo OPENAI_API_KEY= > .env
        echo WICHTIG: Bitte .env Datei oeffnen und API-Key eintragen!
        echo.
    )
) else (
    echo [2/4] .env Datei vorhanden
)

REM Dependencies installieren
echo [3/4] Installiere Abhaengigkeiten (dauert 1-2 Minuten)...
REM pip kann nach abgebrochenen Installs eine defekte "~penai*" Distribution warnen; cleanen wir vorab.
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import site; print(site.getsitepackages()[0])"') do set "SITE_PACKAGES=%%i"
for /d %%d in ("%SITE_PACKAGES%\~penai*") do (
    rmdir /s /q "%%d" >nul 2>&1
)
%PYTHON_CMD% -m pip install --upgrade pip --quiet >nul 2>&1
%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo FEHLER: Installation fehlgeschlagen!
    pause
    exit /b 1
)

REM App starten
echo [4/4] Starte App...
echo.
echo ========================================
echo App startet jetzt im Browser!
echo Zum Beenden: Strg+C im Fenster
echo ========================================
echo.

%PYTHON_CMD% -m streamlit run app/app.py

endlocal
