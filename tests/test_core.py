import pandas as pd

from core import disability_gender_core, geography_analysis_core, structured_core
from utils import parse_mixed_date


def test_parse_mixed_date_handles_excel_serial():
    s = pd.Series([45234, "45235", "09042025", "9/5/2025", None])
    dt = parse_mixed_date(s)
    assert pd.notna(dt.iloc[0])
    assert pd.notna(dt.iloc[1])
    assert str(dt.iloc[2].date()) == "2025-09-04"
    assert str(dt.iloc[3].date()) == "2025-09-05"


def test_structured_core_counts():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "TEAM_UP Completed": ["yes", "no", "yes"],
            "HEART Completed": ["no", "no", "yes"],
        }
    )
    programs = [("TEAM_UP", "TEAM_UP Completed"), ("HEART", "HEART Completed")]
    result = structured_core(df, use_id=True, id_col="id", programs=programs, export_filter="All rows")
    assert result["n_total"] == 3
    assert result["n_any"] == 2
    assert int(result["dist"][0]) == 1


def test_geography_analysis_core_use_id_deduplicates_and_normalizes():
    df = pd.DataFrame(
        {
            "id": [1, 1, 2, 3],
            "Oblast_col": ["Kyiv", "", "Lviv", None],
            "Raion_col": ["Shevchenkivskyi", None, "Stryiskyi", ""],
            "Hromada_col": ["A", "A", "B", ""],
            "Settlement_col": ["X", "", "Y", None],
        }
    )

    result = geography_analysis_core(
        df,
        use_id=True,
        id_col="id",
        oblast_col="Oblast_col",
        raion_col="Raion_col",
        hromada_col="Hromada_col",
        settlement_col="Settlement_col",
    )

    assert result["n_total"] == 3
    assert int(result["by_oblast"].set_index("Oblast").loc["Kyiv", "Children"]) == 1
    assert int(result["by_oblast"].set_index("Oblast").loc["Lviv", "Children"]) == 1
    assert int(result["by_oblast"].set_index("Oblast").loc["Unknown", "Children"]) == 1


def test_disability_gender_core_totals_and_gender_split():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "disability": ["yes", "no", "", None],
            "gender": ["boy", "girl", "boy", ""],
        }
    )

    result = disability_gender_core(
        df,
        use_id=True,
        id_col="id",
        disability_col="disability",
        gender_col="gender",
    )

    totals = result["total_by_disability"].set_index("Disability status")["Children"]
    assert int(totals["Unknown"]) == 2
    assert int(totals["yes"]) == 1
    assert int(totals["no"]) == 1

    split = result["by_disability_gender"].set_index("Disability status")
    assert int(split.loc["yes", "boy"]) == 1
    assert int(split.loc["no", "girl"]) == 1
    assert int(split.loc["Unknown", "unknown"]) == 1
