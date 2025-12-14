# Terminal-Start (ohne Doppelklick)

## macOS / Linux (Bash/Zsh)
```bash
cd /path/to/multi_agent_orchestration
python3 --version   # muss 3.9+ sein
python3 -m venv venv
source venv/bin/activate
cp .env.example .env  # falls .env fehlt; OPENAI_API_KEY eintragen
pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app/app.py
```

If you see `urllib3` / `NotOpenSSLWarning` on macOS (LibreSSL), run `pip install -U "urllib3<2"` and re-run Streamlit.
If you see `WARNING: Ignoring invalid distribution -penai`, delete leftover folders in your venv site-packages (e.g. `rm -rf venv/lib/python*/site-packages/~penai*`) and re-run `pip install -r requirements.txt`.

## Windows (PowerShell)
```powershell
cd C:\path\to\multi_agent_orchestration
python --version    # muss 3.9+ sein; alternativ: py -3 --version
python -m venv venv # oder: py -3 -m venv venv
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env -ErrorAction SilentlyContinue
# .env öffnen und OPENAI_API_KEY eintragen
python -m pip install --upgrade pip
python -m pip install -r requirements.txt   # oder: py -3 -m pip install ...
python -m streamlit run app/app.py          # oder: py -3 -m streamlit run app/app.py
```
