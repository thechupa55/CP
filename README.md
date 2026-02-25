# MEAL Counter Tool

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run App

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Notes

- If your default `python` points to another version, use full path to Python 3.12.
- The app opens in browser at `http://localhost:8501`.
