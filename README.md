# MEAL Counter Tool

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Reproducible Setup (Lockfile)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
```

Update lockfile after dependency changes:

```powershell
.\.venv\Scripts\python.exe -m pip freeze > requirements.lock
```

## Run App

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Lint / Typecheck

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app.py core.py utils.py config.py
```

## Notes

- If your default `python` points to another version, use full path to Python 3.12.
- The app opens in browser at `http://localhost:8501`.

## Versioning

- This project uses `Semantic Versioning` (`MAJOR.MINOR.PATCH`).
- All user-visible changes should be recorded in [CHANGELOG.md](./CHANGELOG.md).
- Add new work to `Unreleased` first, then move it to a version section on release day.
