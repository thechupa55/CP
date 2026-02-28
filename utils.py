import io
import pandas as pd

TRUE_SET = {"yes", "y", "true", "1", "completed", "done"}


def to_bool_series(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.lower()
    return s.isin(TRUE_SET)


def to_num(series: pd.Series) -> pd.Series:
    n = pd.to_numeric(series, errors="coerce")
    return n.fillna(0)


def make_unique_columns(cols) -> list[str]:
    seen = {}
    out = []
    for c in cols:
        c = str(c).strip()
        if c in seen:
            seen[c] += 1
            out.append(f"{c}__{seen[c]}")
        else:
            seen[c] = 0
            out.append(c)
    return out


def parse_mixed_date(series: pd.Series) -> pd.Series:
    """
    Handles:
      - Excel datetime values
      - strings like 9/4/2025
      - strings like 09042025 (MMDDYYYY)
      - Excel serial numbers (e.g., 45234)
    """
    s = series.copy()
    if pd.api.types.is_datetime64_any_dtype(s):
        return s

    s_string = s.astype("string").str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    # 1) ISO-like explicit forms first (stable and unambiguous)
    iso_dash = s_string.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    out = out.where(~iso_dash, pd.to_datetime(s_string.where(iso_dash), format="%Y-%m-%d", errors="coerce"))

    iso_slash = s_string.str.fullmatch(r"\d{4}/\d{2}/\d{2}", na=False)
    out = out.where(~iso_slash, pd.to_datetime(s_string.where(iso_slash), format="%Y/%m/%d", errors="coerce"))

    # 2) Common US forms
    mmddyyyy_slash = s_string.str.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", na=False)
    out = out.where(
        ~(out.isna() & mmddyyyy_slash),
        pd.to_datetime(s_string.where(mmddyyyy_slash), format="%m/%d/%Y", errors="coerce"),
    )

    # 3) Compact MMDDYYYY
    compact8 = s_string.str.fullmatch(r"\d{8}", na=False)
    out = out.where(
        ~(out.isna() & compact8),
        pd.to_datetime(s_string.where(compact8), format="%m%d%Y", errors="coerce"),
    )

    # 4) Excel serial numbers
    numeric = pd.to_numeric(s_string, errors="coerce")
    excel_mask = out.isna() & numeric.between(1, 60000, inclusive="both")
    out = out.where(
        ~excel_mask,
        pd.to_datetime(numeric.where(excel_mask), unit="D", origin="1899-12-30", errors="coerce"),
    )

    # 5) Controlled fallback only for unresolved values
    unresolved = out.isna() & s_string.notna() & s_string.ne("")
    if unresolved.any():
        out = out.where(
            ~unresolved,
            pd.to_datetime(s_string.where(unresolved), errors="coerce", dayfirst=False),
        )

    return out


def build_report_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, frame in sheets.items():
            if frame is None:
                continue
            frame.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()
