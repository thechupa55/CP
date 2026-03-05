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

## P01 Logic (Attendance List)

- P01 counts each `Child ID` only once.
- A child is qualified by either:
  - first `EORE` visit, or
  - second visit in CP programs:
    `team_up`, `heart`, `cyr`, `ismf`, `safe families`, `jswp`,
    `recreational_activity`, `informal_education_activity`, `sel`,
    `socr`, `gbv`, `la`.
- If both conditions are met for the same child, the earliest qualifying date is used.
- Rows without `Child ID` or valid attendance date are excluded.

## Versioning

- This project uses `Semantic Versioning` (`MAJOR.MINOR.PATCH`).
- All user-visible changes should be recorded in [CHANGELOG.md](./CHANGELOG.md).
- Add new work to `Unreleased` first, then move it to a version section on release day.
