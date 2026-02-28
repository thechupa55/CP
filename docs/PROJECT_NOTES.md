# PROJECT NOTES

## Purpose
- Streamlit MEAL analytics tool for Child/Adult Excel data.
- Main goal: stable indicator calculations across varying file schemas via explicit column mapping.

## Core Rules (Mapping)
- Column selectors must use `pick_col_with_default(...)` for mapping fields.
- If default column is not found, selector must use `"(empty - choose column)"` (never silently pick first column).
- Empty mapping must show a clear warning and block only the affected sub-block (not the whole app).
- Do not add service options as physical dataframe columns (no data pollution).

## File-Switch Behavior
- Mapping state is cleared on file change using explicit mapping-key registry.
- Re-initialize critical defaults after file switch:
  - Child CP monthly date: `Attendance 2nd Date`
  - Child CP monthly gender: `Gender`
  - Adult CP: `Safe Families`, `Unstructured MHPSS Activities`, `Unstructured MHPSS Activities Youth Resilience` (fallback to `Youth Resilience`).

## Indicator Decisions
- Child CP indicator includes: `TEAM_UP`, `HEART`, `CYR`, `ISMF`, `SF + JSWP`, `Recreational Activity`, `Informal Education Activity`, `SEL`, `SOCR`, `EORE`, `GBV`, `LA`.
- Adult CP indicator uses 3 programs:
  - `Safe Families`
  - `Unstructured MHPSS Activities`
  - `Unstructured MHPSS Activities Youth Resilience` (or `Youth Resilience` fallback).

## Indicator Monthly Decisions
- Added separate `Indicator Monthly` tab.
- Table layout is transposed:
  - rows: `# of girls`, `# of boys`, `# of women`, `# of men`, `total`
  - columns: months + `Overall`.
- `total` includes unknown-gender counts from child and adult data, but unknown is not shown as a separate row.

## Date Parsing
- `parse_mixed_date` uses deterministic parsing order:
  1. `YYYY-MM-DD`
  2. `YYYY/MM/DD`
  3. `MM/DD/YYYY`
  4. `MMDDYYYY`
  5. Excel serial numbers
  6. fallback parser for unresolved values only

## Performance
- Heavy repeated aggregations are memoized per rerun in `app.py`.
- Reuse cached wrappers for CP/Structured/Safe Families monthly computations across tabs.

## Quality Workflow
- Tests: `pytest`
- Lint: `ruff`
- Typecheck: `mypy`
- Dependency policy:
  - `requirements.txt` has upper bounds.
  - `requirements.lock` stores pinned environment snapshot.

## Naming / Version Notes
- App title: `MEAL Counter Tool v2`.
- Keep `CHANGELOG.md` updated under `Unreleased` for all user-visible changes.
