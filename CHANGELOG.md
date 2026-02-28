# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Added `Indicator Monthly` tab (right after `Indicators`) with monthly breakdown tables for all 3 headline indicators.
- Added transposed monthly layout in `Indicator Monthly`:
  - rows: `# of girls`, `# of boys`, `# of women`, `# of men`, `total`
  - month columns + `Overall` summary column.
- Extended child CP services programs in CP indicator logic and UI:
  - added `SEL`, `SOCR`, `GBV`, `LA`
  - kept `EORE` and updated expected column order.
- Added adult CP third program mapping:
  - `Adult Youth Resilience sessions column`.
- Added robust file-switch state reset for mapping keys to avoid stale mappings after switching between different Excel files.
- Added deterministic date parsing order in `parse_mixed_date` (`utils.py`) before generic fallback.
- Added reproducible dependency lockfile:
  - `requirements.lock`
  - README section for lockfile setup.
- Added lint/typecheck commands to README and added tools to dependencies:
  - `ruff`
  - `mypy`.

### Changed
- Updated app title from `MEAL Counter Tool v1` to `MEAL Counter Tool v2`.
- Standardized many column selectors to `pick_col_with_default(...)` and unified empty-selection policy.
- Improved fallback behavior: if default column is not found, selectors now use explicit empty option instead of silently picking first column.
- Changed adult Youth Resilience default mapping target to `Unstructured MHPSS Activities Youth Resilience` (with fallback compatibility).
- Reworded structured indicator labels to reflect current implemented scope (children).

### Fixed
- Fixed Streamlit session-state warning in structured tab caused by selectbox `index` + explicit state assignment conflict.
- Fixed adults not appearing in CP monthly totals in `Indicator Monthly` by including unknown-gender counts in `total`.
- Fixed repeated heavy calculations across tabs by introducing per-rerun memoization wrappers in `app.py`.
- Fixed potential crashes when mapped columns are empty/unavailable by adding safe column accessors in `core.py`.
- Removed pollution of source dataframes by no longer adding `EMPTY_COL_OPTION` as a physical column.

### Quality
- Added dependency upper bounds in `requirements.txt`.
- Improved local quality workflow with `pytest`, `ruff`, and `mypy` execution paths documented in README.

## [1.3.0] - 2026-02-25

### Added
- Added `Data Quality` tab with targeted checks:
  - Parent name with multiple phones (`Full Parent Name -> many Parents phone`)
  - Child name duplicates (`Child Full Name`) with details:
    - `Settlement`
    - `Full Parent Name`
    - `Parents phone`
    - `Date of birth`
  - Phone used by multiple parent names (`Parents phone -> many Full Parent Name`)
  - CSV exports for all data-quality checks.
- Added `Status IDP` tab:
  - Based on `Status IDP` values (`local`, `idp`, `returnee`)
  - Gender split with `girl`, `boy`, `unknown`, `Total`
  - Uses CP-indicator filter (`>=2 sessions`) for child records.

### Changed
- Reordered main tabs to:
  - `Preview`, `Data Quality`, `Indicators`, `CP Services Indicator`, `Structured`, `Structured Monthly`, `Safe Families Monthly`, `Geography`, `Disability`, `Status IDP`, `Downloads`.
- Updated column ordering in multiple tables:
  - Child CP monthly gender: `Month, girl, boy, Total, unknown`
  - Structured monthly by first program + gender: `Month, Program, girl, boy, Total, unknown`
  - Safe Families child monthly gender: `Month, girl, boy, Total, unknown`
  - Disability / Status IDP gender tables: `girl` before `boy`
  - Adult CP monthly gender: `Month, female, male, Total, unknown`
  - Adult Safe Families monthly gender: includes `Total`.
- Added `Total` columns where needed across monthly gender tables (child and adult).

### Fixed
- Restored correct child gender logic (`boy/girl`) in structured monthly tables after intermediate regressions.
- Fixed adult monthly CP gender table to reliably include `Total`.
- Improved column resolution and fallback handling for key list/report outputs.

## [1.2.0] - 2026-02-25

### Added
- Added new `Indicators` tab (after `Preview`) with 3 headline indicators:
  - `# of individuals participating in child protection services`
  - `# of children and adults who received mental health and/or psycosocial support (structured MHPSS programs)`
  - `# of individuals who attended Safe Families positive parenting group or childrens sessions`
- Added highlighted KPI banner component for key indicators (`render_indicator_banner`).

### Changed
- Updated `Structured Monthly` tabs order so `Monthly by first program + gender` is directly after `Monthly by first program`.
- Added robust child name auto-detection with alias support (`Child Full Name` and alternative label variant) and column-letter fallback.
- Updated labels/metrics:
  - `Total child indicator achievements (all time)`
  - `Child Safe Families completed (total)`.

## [1.1.0] - 2026-02-25

### Added
- Added dual-sheet workflow: `Child Info` and `Adult Info` can be loaded simultaneously from one Excel file.
- Added support for optional `Adult ID` in sidebar settings.
- Added adult logic to `CP Services Indicator`:
  - Adult indicator based on `Safe Families + Unstructured MHPSS Activities >= 2 sessions`
  - Adult monthly achievements block with tabs:
    - `Monthly total (Adults)`
    - `Monthly by gender (Adults)`
    - `Adults list`
  - Adult CSV exports for indicator and monthly views.
- Added adult logic to `Safe Families Monthly`:
  - Separate metrics/table/export for adults (`male/female`).

## [1.0.0] - 2026-02-24

### Added
- Core Streamlit app for Child Info with tabs:
  - `Preview`
  - `Structured`
  - `Structured Monthly`
  - `CP Services Indicator`
  - `Safe Families Monthly`
  - `Geography`
  - `Disability`
  - `Downloads`
- Structured first-time monthly reporting with:
  - monthly total
  - by first program
  - by gender
  - child list export
- CP Services indicator core logic (`>=2 total sessions`) and child export list.
- Safe Families monthly by gender (child).
- Geography analysis and Disability analysis tables/exports.

### Fixed
- Refactored app entrypoint so `app.py` is import-safe (`main()` + `if __name__ == "__main__":`).
