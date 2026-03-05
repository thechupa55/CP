import pandas as pd

from core import (
    activities_participation_core,
    activities_participation_monthly_core,
    disability_gender_core,
    geography_analysis_core,
    p01_cp_services_from_attendance_core,
    structured_core,
)
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


def test_activities_participation_core_counts_by_unique_child_id():
    df = pd.DataFrame(
        {
            "child_id": ["1", "1", "2", "3", "4", "5", "", None],
            "site_type": ["CFS", "Mobile", "CFS", "Mobile", "CFS", "CFS", "CFS", "CFS"],
            "program": [
                "recreational_activity",
                "recreational_activity",
                "recreational_activity",
                "EORE",
                "EORE",
                "recreational_activity",
                "recreational_activity",
                "recreational_activity",
            ],
            "gender": ["girl", "girl", "boy", "girl", "male", "female", "girl", "boy"],
        }
    )

    result = activities_participation_core(
        df,
        id_col="child_id",
        site_type_col="site_type",
        program_col="program",
        gender_col="gender",
    ).set_index("Activity")

    assert int(result.loc["Recreational activities (static)", "girl"]) == 1
    assert int(result.loc["Recreational activities (static)", "boy"]) == 1
    assert int(result.loc["Recreational activities (static)", "female"]) == 1
    assert int(result.loc["Recreational activities (static)", "Total"]) == 3

    assert int(result.loc["Recreational activities (mobile)", "girl"]) == 1
    assert int(result.loc["Recreational activities (mobile)", "Total"]) == 1

    assert int(result.loc["Provision of Explosive Ordnance Risk Education (EORE)", "girl"]) == 1
    assert int(result.loc["Provision of Explosive Ordnance Risk Education (EORE)", "male"]) == 1
    assert int(result.loc["Provision of Explosive Ordnance Risk Education (EORE)", "Total"]) == 2


def test_activities_participation_monthly_core_counts_by_child_id_and_month():
    df = pd.DataFrame(
        {
            "child_id": ["1", "1", "2", "3", "3", "4"],
            "site_type": ["CFS", "CFS", "Mobile", "CFS", "CFS", "CFS"],
            "program": [
                "recreational_activity",
                "recreational_activity",
                "recreational_activity",
                "EORE",
                "EORE",
                "EORE",
            ],
            "gender": ["girl", "girl", "boy", "male", "male", "female"],
            "date_att": ["2025-01-10", "2025-01-20", "2025-01-11", "2025-02-01", "2025-02-15", "2025-02-18"],
        }
    )

    out = activities_participation_monthly_core(
        df,
        id_col="child_id",
        site_type_col="site_type",
        program_col="program",
        gender_col="gender",
        date_col="date_att",
    )

    static_girl = out[
        (out["Activity"] == "Recreational activities (static)")
        & (out["Gender"] == "girl")
    ].iloc[0]
    assert int(static_girl["2025-01"]) == 1
    assert int(static_girl["Total"]) == 1

    mobile_boy = out[
        (out["Activity"] == "Recreational activities (mobile)")
        & (out["Gender"] == "boy")
    ].iloc[0]
    assert int(mobile_boy["2025-01"]) == 1
    assert int(mobile_boy["Total"]) == 1

    eore_male = out[
        (out["Activity"] == "Provision of Explosive Ordnance Risk Education (EORE)")
        & (out["Gender"] == "male")
    ].iloc[0]
    eore_female = out[
        (out["Activity"] == "Provision of Explosive Ordnance Risk Education (EORE)")
        & (out["Gender"] == "female")
    ].iloc[0]
    assert int(eore_male["2025-02"]) == 1
    assert int(eore_female["2025-02"]) == 1
    assert int(eore_male["Total"]) == 1
    assert int(eore_female["Total"]) == 1

    eore_total = out[
        (out["Activity"] == "Provision of Explosive Ordnance Risk Education (EORE)")
        & (out["Gender"] == "Total")
    ].iloc[0]
    assert int(eore_total["2025-02"]) == 2
    assert int(eore_total["Total"]) == 2


def test_p01_cp_services_from_attendance_core_conditions_and_totals():
    df = pd.DataFrame(
        {
            "child_id": ["1", "2", "2", "3", "4", "4", "5"],
            "program": ["EORE", "TEAM_UP", "HEART", "TEAM_UP", "JSWP", "safe families", "EORE"],
            "date_att": [
                "2025-01-05",
                "2025-01-03",
                "2025-02-10",
                "2025-03-01",
                "2025-01-10",
                "2025-01-20",
                "2025-02-15",
            ],
            "gender": ["girl", "boy", "boy", "male", "female", "female", "female"],
            "age_group": ["10-14 years", "15-17 years", "15-17 years", "30-59 years", "18-29 years", "18-29 years", "60 years and older"],
        }
    )

    result = p01_cp_services_from_attendance_core(
        df,
        id_col="child_id",
        program_col="program",
        date_col="date_att",
        gender_col="gender",
        age_group_col="age_group",
    )
    table = result["table"]
    assert int(result["indicator_total"]) == 4  # ids: 1(A),2(B),4(B),5(A)

    female_10_14 = table[(table["Sex"] == "Female") & (table["Age Group"] == "10-14 years")].iloc[0]
    assert int(female_10_14["2025-01"]) == 1
    assert int(female_10_14["Total"]) == 1

    male_15_17 = table[(table["Sex"] == "Male") & (table["Age Group"] == "15-17 years")].iloc[0]
    assert int(male_15_17["2025-02"]) == 1
    assert int(male_15_17["Total"]) == 1

    total_row = table[table["Sex"] == "Total"].iloc[0]
    assert int(total_row["2025-01"]) == 2
    assert int(total_row["2025-02"]) == 2
    assert int(total_row["Total"]) == 4


def test_p01_prefers_earliest_qualifying_date_between_b_and_eore():
    df = pd.DataFrame(
        {
            "child_id": ["10", "10", "10"],
            "program": ["TEAM_UP", "HEART", "EORE"],
            "date_att": ["2025-01-01", "2025-01-05", "2025-02-10"],
            "gender": ["boy", "boy", "boy"],
            "age_group": ["15-17 years", "15-17 years", "15-17 years"],
        }
    )

    result = p01_cp_services_from_attendance_core(
        df,
        id_col="child_id",
        program_col="program",
        date_col="date_att",
        gender_col="gender",
        age_group_col="age_group",
    )
    table = result["table"]

    assert int(result["indicator_total"]) == 1
    # This ID qualifies by B on 2025-01-05 and by A on 2025-02-10.
    # Entry month must be the earliest qualifying month (2025-01).
    male_15_17 = table[(table["Sex"] == "Male") & (table["Age Group"] == "15-17 years")].iloc[0]
    assert int(male_15_17.get("2025-01", 0)) == 1
    assert int(male_15_17.get("2025-02", 0)) == 0
