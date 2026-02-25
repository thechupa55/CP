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
    dt1 = pd.to_datetime(s_string, errors="coerce", dayfirst=False)

    mask8 = s_string.str.fullmatch(r"\d{8}", na=False)
    dt2 = pd.to_datetime(s_string.where(mask8), format="%m%d%Y", errors="coerce")

    numeric = pd.to_numeric(s_string, errors="coerce")
    excel_mask = numeric.between(1, 60000, inclusive="both")
    dt3 = pd.to_datetime(numeric.where(excel_mask), unit="D", origin="1899-12-30", errors="coerce")

    return dt1.fillna(dt2).fillna(dt3)


def build_report_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, frame in sheets.items():
            if frame is None:
                continue
            frame.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()
