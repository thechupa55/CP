import pandas as pd

from utils import (
    make_unique_columns,
    parse_mixed_date,
    to_bool_series,
    to_num,
)


def structured_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    programs: list[tuple[str, str]],
    export_filter: str,
):
    prog = pd.DataFrame({name: to_bool_series(df[col]) for name, col in programs})

    if use_id:
        prog_by = prog.groupby(df[id_col]).max()
        base_df = df.drop_duplicates(subset=[id_col]).set_index(id_col)
        n_total = len(prog_by)
    else:
        prog_by = prog
        base_df = df
        n_total = len(df)

    n_any = int(prog_by.any(axis=1).sum())
    n_each = prog_by.sum().astype(int)
    n_programs = prog_by.sum(axis=1)
    dist = n_programs.value_counts().reindex([0, 1, 2, 3, 4], fill_value=0).astype(int)

    only_one_mask = n_programs == 1
    only_one_by_program = prog_by[only_one_mask].sum().astype(int)

    def combo_label(row: pd.Series) -> str:
        picked = [k for k, v in row.items() if bool(v)]
        return "NONE" if not picked else "+".join(picked)

    combo_series = prog_by.apply(combo_label, axis=1)
    structured_combo_df = combo_series.value_counts().reset_index()
    structured_combo_df.columns = ["Combination", "Count"]

    if export_filter == "All rows":
        export_mask = pd.Series([True] * len(prog_by), index=prog_by.index)
    elif export_filter == "Only children with at least 1 structured program":
        export_mask = n_programs >= 1
    elif export_filter == "Only children with 0 structured programs":
        export_mask = n_programs == 0
    elif export_filter == "Only children with 2+ structured programs":
        export_mask = n_programs >= 2
    else:
        export_mask = n_programs == 1

    export_prog = prog_by.copy()
    export_prog["__Structured_Programs_Count"] = n_programs
    export_prog["__Structured_Combination"] = combo_series

    if use_id:
        export_rows = base_df.join(export_prog, how="left").loc[export_mask].reset_index()
    else:
        export_rows = pd.concat([base_df.reset_index(drop=True), export_prog.reset_index(drop=True)], axis=1)
        export_rows = export_rows.loc[export_mask.reset_index(drop=True)].copy()

    export_rows.columns = make_unique_columns(export_rows.columns)

    structured_summary_df = pd.DataFrame(
        [
            ["Total children", n_total],
            ["At least 1 structured program", n_any],
            ["0 structured programs", int(dist[0])],
            ["1 structured program", int(dist[1])],
            ["2 structured programs", int(dist[2])],
            ["3 structured programs", int(dist[3])],
            ["4 structured programs", int(dist[4])],
        ],
        columns=["Metric", "Value"],
    )

    structured_per_program_df = n_each.reset_index()
    structured_per_program_df.columns = ["Program", "Children"]

    structured_only_one_df = only_one_by_program.reset_index()
    structured_only_one_df.columns = ["Only this program", "Children"]

    return {
        "prog_by": prog_by,
        "n_total": n_total,
        "n_any": n_any,
        "n_each": n_each,
        "n_programs": n_programs,
        "dist": dist,
        "combo_series": combo_series,
        "structured_combo_df": structured_combo_df,
        "structured_summary_df": structured_summary_df,
        "structured_per_program_df": structured_per_program_df,
        "structured_only_one_df": structured_only_one_df,
        "export_rows": export_rows,
    }


def structured_monthly_first_time_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    team_completed_col: str,
    team_date_col: str,
    heart_completed_col: str,
    heart_date_col: str,
    cyr_completed_col: str,
    cyr_date_col: str,
    ismf_completed_col: str,
    ismf_date_col: str,
    gender_col: str,
):
    team_done = to_bool_series(df[team_completed_col])
    heart_done = to_bool_series(df[heart_completed_col])
    cyr_done = to_bool_series(df[cyr_completed_col])
    ismf_done = to_bool_series(df[ismf_completed_col])

    team_dt = parse_mixed_date(df[team_date_col]).where(team_done)
    heart_dt = parse_mixed_date(df[heart_date_col]).where(heart_done)
    cyr_dt = parse_mixed_date(df[cyr_date_col]).where(cyr_done)
    ismf_dt = parse_mixed_date(df[ismf_date_col]).where(ismf_done)

    dates_df = pd.DataFrame({"TEAM_UP": team_dt, "HEART": heart_dt, "CYR": cyr_dt, "ISMF": ismf_dt})
    first_dt_row = dates_df.min(axis=1)

    first_program_row = dates_df.eq(first_dt_row, axis=0).idxmax(axis=1)
    first_program_row = first_program_row.where(first_dt_row.notna())

    gender_clean = df[gender_col].astype("string").str.strip().str.lower()
    gender_clean = gender_clean.where(gender_clean.isin(["boy", "girl"]), "unknown")

    if use_id:
        tmp = pd.DataFrame(
            {
                "_id": df[id_col],
                "first_dt": first_dt_row,
                "first_program": first_program_row,
                "gender": gender_clean,
                "_row_index": df.index,
            }
        )
        tmp = tmp.dropna(subset=["first_dt"]).sort_values(["_id", "first_dt", "_row_index"])
        tmp_first = tmp.groupby("_id").first()
        first_dt = tmp_first["first_dt"]
        first_program = tmp_first["first_program"]
        gender_for_first = tmp_first["gender"]
        first_row_index = tmp_first["_row_index"].astype("Int64")
    else:
        first_dt = first_dt_row
        first_program = first_program_row
        gender_for_first = gender_clean
        first_row_index = first_dt_row[first_dt_row.notna()].index.to_series().astype("Int64")

    monthly_total = (
        first_dt.dropna().dt.to_period("M").value_counts().sort_index()
        .rename_axis("Month").reset_index(name="First-time structured completions")
    )

    monthly_by_program = (
        pd.DataFrame(
            {
                "Month": first_dt.dropna().dt.to_period("M").astype(str),
                "Program": first_program.loc[first_dt.dropna().index].astype("string"),
            }
        )
        .value_counts().reset_index(name="Count").sort_values(["Month", "Program"])
    )

    mpg = pd.DataFrame(
        {
            "Month": first_dt.dropna().dt.to_period("M").astype(str),
            "Program": first_program.loc[first_dt.dropna().index].astype("string"),
            "Gender": gender_for_first.loc[first_dt.dropna().index].astype("string"),
        }
    )
    monthly_by_program_gender_long = (
        mpg.value_counts().reset_index(name="Count").sort_values(["Month", "Program", "Gender"])
    )
    monthly_by_program_gender_pivot = (
        monthly_by_program_gender_long.pivot(
            index=["Month", "Program"], columns="Gender", values="Count"
        )
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    if "boy" not in monthly_by_program_gender_pivot.columns:
        monthly_by_program_gender_pivot["boy"] = 0
    if "girl" not in monthly_by_program_gender_pivot.columns:
        monthly_by_program_gender_pivot["girl"] = 0
    if "unknown" not in monthly_by_program_gender_pivot.columns:
        monthly_by_program_gender_pivot["unknown"] = 0
    monthly_by_program_gender_pivot["Total"] = (
        monthly_by_program_gender_pivot["boy"]
        + monthly_by_program_gender_pivot["girl"]
        + monthly_by_program_gender_pivot["unknown"]
    )
    monthly_by_program_gender_pivot = monthly_by_program_gender_pivot[
        ["Month", "Program", "boy", "girl", "Total", "unknown"]
    ]

    mg = pd.DataFrame(
        {
            "Month": first_dt.dropna().dt.to_period("M").astype(str),
            "Gender": gender_for_first.loc[first_dt.dropna().index].astype("string"),
        }
    )
    monthly_by_gender_long = mg.value_counts().reset_index(name="Count").sort_values(["Month", "Gender"])
    monthly_by_gender_pivot = (
        monthly_by_gender_long.pivot(index="Month", columns="Gender", values="Count")
        .fillna(0).astype(int).reset_index()
    )
    if "boy" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["boy"] = 0
    if "girl" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["girl"] = 0
    if "unknown" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["unknown"] = 0
    monthly_by_gender_pivot["Total"] = (
        monthly_by_gender_pivot["boy"]
        + monthly_by_gender_pivot["girl"]
        + monthly_by_gender_pivot["unknown"]
    )
    monthly_by_gender_pivot = monthly_by_gender_pivot[
        ["Month", "boy", "girl", "Total", "unknown"]
    ]

    missing_date_count = int(
        ((team_done & team_dt.isna()) |
         (heart_done & heart_dt.isna()) |
         (cyr_done & cyr_dt.isna()) |
         (ismf_done & ismf_dt.isna()))
        .sum()
    )

    return {
        "first_dt": first_dt,
        "first_program": first_program,
        "gender_for_first": gender_for_first,
        "first_row_index": first_row_index,
        "monthly_total": monthly_total,
        "monthly_by_program": monthly_by_program,
        "monthly_by_program_gender_pivot": monthly_by_program_gender_pivot,
        "monthly_by_gender_pivot": monthly_by_gender_pivot,
        "missing_date_count": missing_date_count,
    }


def cp_services_indicator_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    team_s_col: str,
    heart_s_col: str,
    cyr_s_col: str,
    ismf_s_col: str,
    sf_s_col: str,
    rec_s_col: str,
    infedu_s_col: str,
    eore_s_col: str,
):
    team_n = to_num(df[team_s_col])
    heart_n = to_num(df[heart_s_col])
    cyr_n = to_num(df[cyr_s_col])
    ismf_n = to_num(df[ismf_s_col])
    sf_n = to_num(df[sf_s_col])
    rec_n = to_num(df[rec_s_col])
    infedu_n = to_num(df[infedu_s_col])
    eore_n = to_num(df[eore_s_col])

    if use_id:
        team_n = team_n.groupby(df[id_col]).sum()
        heart_n = heart_n.groupby(df[id_col]).sum()
        cyr_n = cyr_n.groupby(df[id_col]).sum()
        ismf_n = ismf_n.groupby(df[id_col]).sum()
        sf_n = sf_n.groupby(df[id_col]).sum()
        rec_n = rec_n.groupby(df[id_col]).sum()
        infedu_n = infedu_n.groupby(df[id_col]).sum()
        eore_n = eore_n.groupby(df[id_col]).sum()

    total_sessions = team_n + heart_n + cyr_n + ismf_n + sf_n + rec_n + infedu_n + eore_n
    indicator_mask = total_sessions >= 2
    return total_sessions, indicator_mask


def cp_services_indicator_monthly_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    team_s_col: str,
    heart_s_col: str,
    cyr_s_col: str,
    ismf_s_col: str,
    sf_s_col: str,
    rec_s_col: str,
    infedu_s_col: str,
    eore_s_col: str,
    date_col: str,
    gender_col: str,
):
    row_total = (
        to_num(df[team_s_col]) + to_num(df[heart_s_col]) + to_num(df[cyr_s_col]) + to_num(df[ismf_s_col]) +
        to_num(df[sf_s_col]) + to_num(df[rec_s_col]) + to_num(df[infedu_s_col]) + to_num(df[eore_s_col])
    )
    row_dt = parse_mixed_date(df[date_col])
    row_gender = df[gender_col].astype("string").str.strip().str.lower()
    row_gender = row_gender.where(row_gender.isin(["boy", "girl"]), "unknown")

    if use_id:
        total_sessions, indicator_mask = cp_services_indicator_core(
            df,
            use_id,
            id_col,
            team_s_col,
            heart_s_col,
            cyr_s_col,
            ismf_s_col,
            sf_s_col,
            rec_s_col,
            infedu_s_col,
            eore_s_col,
        )
        indicator_ids = total_sessions[indicator_mask].index

        tmp = pd.DataFrame(
            {
                "_id": df[id_col],
                "_row_index": df.index,
                "_row_total": row_total,
                "_dt": row_dt,
                "_gender": row_gender,
            }
        )
        tmp = tmp[tmp["_id"].isin(indicator_ids)].copy()
        tmp = tmp.sort_values(["_id", "_dt", "_row_index"], na_position="last")
        tmp["_cum_total"] = tmp.groupby("_id")["_row_total"].cumsum()

        reached = tmp[tmp["_cum_total"] >= 2].copy()
        first_reached = reached.groupby("_id", as_index=True).first()

        first_dt = first_reached["_dt"]
        first_gender = first_reached["_gender"]
        first_row_index = first_reached["_row_index"].astype("Int64")
        first_total_sessions = total_sessions.loc[first_reached.index]
    else:
        total_sessions = row_total
        indicator_mask = total_sessions >= 2

        first_dt = row_dt.where(indicator_mask)
        first_gender = row_gender.where(indicator_mask)
        first_row_index = first_dt[first_dt.notna()].index.to_series().astype("Int64")
        first_total_sessions = total_sessions.loc[first_dt.dropna().index]

    monthly_total = (
        first_dt.dropna().dt.to_period("M").value_counts().sort_index()
        .rename_axis("Month").reset_index(name="CP indicator achievements")
    )

    mg = pd.DataFrame(
        {
            "Month": first_dt.dropna().dt.to_period("M").astype(str),
            "Gender": first_gender.loc[first_dt.dropna().index].astype("string"),
        }
    )
    monthly_by_gender_long = mg.value_counts().reset_index(name="Count").sort_values(["Month", "Gender"])
    monthly_by_gender_pivot = (
        monthly_by_gender_long.pivot(index="Month", columns="Gender", values="Count")
        .fillna(0).astype(int).reset_index()
    )
    if "boy" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["boy"] = 0
    if "girl" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["girl"] = 0
    if "unknown" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["unknown"] = 0
    monthly_by_gender_pivot["Total"] = (
        monthly_by_gender_pivot["boy"]
        + monthly_by_gender_pivot["girl"]
        + monthly_by_gender_pivot["unknown"]
    )
    monthly_by_gender_pivot = monthly_by_gender_pivot[
        ["Month", "boy", "girl", "Total", "unknown"]
    ]

    first_meta = pd.DataFrame(
        {
            "_row_index": first_row_index,
            "First indicator date": first_dt.loc[first_row_index.index if use_id else first_row_index.index],
            "Gender": first_gender.loc[first_row_index.index if use_id else first_row_index.index],
            "Total sessions": first_total_sessions,
        }
    ).dropna(subset=["_row_index"])

    missing_date_count = int(indicator_mask.sum() - first_dt.dropna().shape[0])

    return {
        "first_dt": first_dt,
        "first_gender": first_gender,
        "first_row_index": first_row_index,
        "first_meta": first_meta,
        "monthly_total": monthly_total,
        "monthly_by_gender_pivot": monthly_by_gender_pivot,
        "missing_date_count": missing_date_count,
        "indicator_total": int(indicator_mask.sum()),
    }


def cp_services_indicator_adult_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    sf_s_col: str,
    unstructured_s_col: str,
):
    sf_n = to_num(df[sf_s_col])
    unstructured_n = to_num(df[unstructured_s_col])

    if use_id:
        sf_n = sf_n.groupby(df[id_col]).sum()
        unstructured_n = unstructured_n.groupby(df[id_col]).sum()

    total_sessions = sf_n + unstructured_n
    indicator_mask = total_sessions >= 2
    return total_sessions, indicator_mask


def cp_services_indicator_adult_monthly_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    sf_s_col: str,
    unstructured_s_col: str,
    date_col: str,
    gender_col: str,
):
    row_total = to_num(df[sf_s_col]) + to_num(df[unstructured_s_col])
    row_dt = parse_mixed_date(df[date_col])
    row_gender = df[gender_col].astype("string").str.strip().str.lower()
    row_gender = row_gender.where(row_gender.isin(["male", "female"]), "unknown")

    if use_id:
        total_sessions, indicator_mask = cp_services_indicator_adult_core(
            df, use_id, id_col, sf_s_col, unstructured_s_col
        )
        indicator_ids = total_sessions[indicator_mask].index

        tmp = pd.DataFrame(
            {
                "_id": df[id_col],
                "_row_index": df.index,
                "_row_total": row_total,
                "_dt": row_dt,
                "_gender": row_gender,
            }
        )
        tmp = tmp[tmp["_id"].isin(indicator_ids)].copy()
        tmp = tmp.sort_values(["_id", "_dt", "_row_index"], na_position="last")
        tmp["_cum_total"] = tmp.groupby("_id")["_row_total"].cumsum()

        reached = tmp[tmp["_cum_total"] >= 2].copy()
        first_reached = reached.groupby("_id", as_index=True).first()

        first_dt = first_reached["_dt"]
        first_gender = first_reached["_gender"]
        first_row_index = first_reached["_row_index"].astype("Int64")
        first_total_sessions = total_sessions.loc[first_reached.index]
    else:
        total_sessions = row_total
        indicator_mask = total_sessions >= 2

        first_dt = row_dt.where(indicator_mask)
        first_gender = row_gender.where(indicator_mask)
        first_row_index = first_dt[first_dt.notna()].index.to_series().astype("Int64")
        first_total_sessions = total_sessions.loc[first_dt.dropna().index]

    monthly_total = (
        first_dt.dropna().dt.to_period("M").value_counts().sort_index()
        .rename_axis("Month").reset_index(name="Adult CP indicator achievements")
    )

    mg = pd.DataFrame(
        {
            "Month": first_dt.dropna().dt.to_period("M").astype(str),
            "Gender": first_gender.loc[first_dt.dropna().index].astype("string"),
        }
    )
    monthly_by_gender_long = mg.value_counts().reset_index(name="Count").sort_values(["Month", "Gender"])
    monthly_by_gender_pivot = (
        monthly_by_gender_long.pivot(index="Month", columns="Gender", values="Count")
        .fillna(0).astype(int).reset_index()
    )
    if "female" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["female"] = 0
    if "male" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["male"] = 0
    if "unknown" not in monthly_by_gender_pivot.columns:
        monthly_by_gender_pivot["unknown"] = 0
    monthly_by_gender_pivot["Total"] = (
        monthly_by_gender_pivot["female"]
        + monthly_by_gender_pivot["male"]
        + monthly_by_gender_pivot["unknown"]
    )
    monthly_by_gender_pivot = monthly_by_gender_pivot[
        ["Month", "female", "male", "Total", "unknown"]
    ]

    first_meta = pd.DataFrame(
        {
            "_row_index": first_row_index,
            "First indicator date": first_dt.loc[first_row_index.index if use_id else first_row_index.index],
            "Gender": first_gender.loc[first_row_index.index if use_id else first_row_index.index],
            "Total sessions": first_total_sessions,
        }
    ).dropna(subset=["_row_index"])

    missing_date_count = int(indicator_mask.sum() - first_dt.dropna().shape[0])

    return {
        "first_dt": first_dt,
        "first_meta": first_meta,
        "monthly_total": monthly_total,
        "monthly_by_gender_pivot": monthly_by_gender_pivot,
        "missing_date_count": missing_date_count,
        "indicator_total": int(indicator_mask.sum()),
        "indicator_total_people": int(len(total_sessions)),
    }


def _normalize_geo_series(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    return s.where(s.notna() & s.ne(""), "Unknown")


def geography_analysis_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    oblast_col: str,
    raion_col: str,
    hromada_col: str,
    settlement_col: str,
):
    def pick_best(values: pd.Series) -> str:
        cleaned = values.astype("string").str.strip()
        cleaned = cleaned.where(cleaned.notna() & cleaned.ne(""), "Unknown")
        non_unknown = cleaned[cleaned.str.casefold() != "unknown"]
        if not non_unknown.empty:
            return str(non_unknown.iloc[0])
        return "Unknown"

    geo_df = pd.DataFrame(
        {
            "Oblast": _normalize_geo_series(df[oblast_col]),
            "Raion": _normalize_geo_series(df[raion_col]),
            "Hromada": _normalize_geo_series(df[hromada_col]),
            "Settlement": _normalize_geo_series(df[settlement_col]),
        }
    )

    if use_id:
        geo_with_id = geo_df.copy()
        geo_with_id["_id"] = df[id_col]
        geo_with_id = geo_with_id[geo_with_id["_id"].notna()].copy()
        geo_base = (
            geo_with_id
            .groupby("_id")
            .agg(
                {
                    "Oblast": pick_best,
                    "Raion": pick_best,
                    "Hromada": pick_best,
                    "Settlement": pick_best,
                }
            )
            .reset_index(drop=True)
        )
    else:
        geo_base = geo_df.reset_index(drop=True)

    def count_by(col: str) -> pd.DataFrame:
        out = geo_base[col].value_counts(dropna=False).rename_axis(col).reset_index(name="Children")
        return out.sort_values(["Children", col], ascending=[False, True]).reset_index(drop=True)

    by_oblast = count_by("Oblast")
    by_raion = count_by("Raion")
    by_hromada = count_by("Hromada")
    by_settlement = count_by("Settlement")

    by_oblast_raion = (
        geo_base.groupby(["Oblast", "Raion"]).size().reset_index(name="Children")
        .sort_values(["Children", "Oblast", "Raion"], ascending=[False, True, True])
        .reset_index(drop=True)
    )
    by_full_path = (
        geo_base.groupby(["Oblast", "Raion", "Hromada", "Settlement"]).size().reset_index(name="Children")
        .sort_values(["Children", "Oblast", "Raion", "Hromada", "Settlement"], ascending=[False, True, True, True, True])
        .reset_index(drop=True)
    )

    return {
        "n_total": int(len(geo_base)),
        "n_oblast": int(geo_base["Oblast"].nunique(dropna=False)),
        "n_raion": int(geo_base["Raion"].nunique(dropna=False)),
        "n_hromada": int(geo_base["Hromada"].nunique(dropna=False)),
        "n_settlement": int(geo_base["Settlement"].nunique(dropna=False)),
        "by_oblast": by_oblast,
        "by_raion": by_raion,
        "by_hromada": by_hromada,
        "by_settlement": by_settlement,
        "by_oblast_raion": by_oblast_raion,
        "by_full_path": by_full_path,
    }


def disability_gender_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    disability_col: str,
    gender_col: str,
):
    def normalize_text(series: pd.Series) -> pd.Series:
        s = series.astype("string").str.strip()
        return s.where(s.notna() & s.ne(""), "Unknown")

    disability = normalize_text(df[disability_col])
    gender = normalize_text(df[gender_col]).str.lower()
    gender = gender.where(gender.isin(["boy", "girl"]), "unknown")

    base = pd.DataFrame(
        {
            "Disability status": disability,
            "Gender": gender,
        }
    )

    if use_id:
        tmp = base.copy()
        tmp["_id"] = df[id_col]
        tmp = tmp[tmp["_id"].notna()].copy()
        base = (
            tmp.groupby("_id")
            .agg(
                {
                    "Disability status": lambda s: normalize_text(s).iloc[0],
                    "Gender": lambda s: normalize_text(s).str.lower().iloc[0],
                }
            )
            .reset_index(drop=True)
        )
        base["Gender"] = base["Gender"].where(base["Gender"].isin(["boy", "girl"]), "unknown")

    total_by_disability = (
        base["Disability status"]
        .value_counts()
        .rename_axis("Disability status")
        .reset_index(name="Children")
        .sort_values(["Children", "Disability status"], ascending=[False, True])
        .reset_index(drop=True)
    )

    by_disability_gender = (
        base.groupby(["Disability status", "Gender"]).size().reset_index(name="Children")
        .pivot(index="Disability status", columns="Gender", values="Children")
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    if "boy" not in by_disability_gender.columns:
        by_disability_gender["boy"] = 0
    if "girl" not in by_disability_gender.columns:
        by_disability_gender["girl"] = 0
    if "unknown" not in by_disability_gender.columns:
        by_disability_gender["unknown"] = 0

    by_disability_gender = by_disability_gender[["Disability status", "boy", "girl", "unknown"]]
    by_disability_gender["Total"] = (
        by_disability_gender["boy"] + by_disability_gender["girl"] + by_disability_gender["unknown"]
    )
    by_disability_gender = by_disability_gender.sort_values(
        ["Total", "Disability status"], ascending=[False, True]
    ).reset_index(drop=True)

    return {
        "n_total": int(len(base)),
        "total_by_disability": total_by_disability,
        "by_disability_gender": by_disability_gender,
    }


def safe_families_monthly_gender_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    sf_completed_col: str,
    sf_date_col: str,
    gender_col: str,
):
    sf_done = to_bool_series(df[sf_completed_col])
    sf_dt = parse_mixed_date(df[sf_date_col]).where(sf_done)

    g = df[gender_col].astype("string").str.strip().str.lower()
    g = g.where(g.isin(["boy", "girl"]), "unknown")

    if use_id:
        tmp = pd.DataFrame({"_id": df[id_col], "_sf_dt": sf_dt, "_gender": g}).dropna(subset=["_sf_dt"])
        tmp = tmp.sort_values(["_id", "_sf_dt"])
        first = tmp.groupby("_id").first()
        sf_dt_in = first["_sf_dt"]
        g_in = first["_gender"].astype("string").where(first["_gender"].isin(["boy", "girl"]), "unknown")
        completed_total = int(len(sf_dt_in))
    else:
        sf_dt_in = sf_dt.dropna()
        g_in = g.loc[sf_dt_in.index].astype("string").where(g.loc[sf_dt_in.index].isin(["boy", "girl"]), "unknown")
        completed_total = int(sf_done.sum())

    monthly_gender = (
        pd.DataFrame({"Month": sf_dt_in.dt.to_period("M").astype(str), "Gender": g_in})
        .value_counts().reset_index(name="Count").sort_values(["Month", "Gender"])
    )
    monthly_gender_pivot = (
        monthly_gender.pivot(index="Month", columns="Gender", values="Count")
        .fillna(0).astype(int).reset_index()
    )
    if "boy" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["boy"] = 0
    if "girl" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["girl"] = 0
    if "unknown" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["unknown"] = 0
    monthly_gender_pivot["Total"] = (
        monthly_gender_pivot["boy"]
        + monthly_gender_pivot["girl"]
        + monthly_gender_pivot["unknown"]
    )
    monthly_gender_pivot = monthly_gender_pivot[
        ["Month", "boy", "girl", "Total", "unknown"]
    ]
    missing_dates = int((sf_done & sf_dt.isna()).sum())

    safe_families_df = pd.DataFrame(
        [
            ["Completed column used", sf_completed_col],
            ["Date column used", sf_date_col],
            ["Gender column used", gender_col],
            ["Completed total", completed_total],
            ["Completed=yes but date missing", missing_dates],
        ],
        columns=["Metric", "Value"],
    )

    return monthly_gender_pivot, safe_families_df, completed_total, missing_dates


def safe_families_monthly_gender_adult_core(
    df: pd.DataFrame,
    use_id: bool,
    id_col: str,
    sf_completed_col: str,
    sf_date_col: str,
    gender_col: str,
):
    sf_done = to_bool_series(df[sf_completed_col])
    sf_dt = parse_mixed_date(df[sf_date_col]).where(sf_done)

    g = df[gender_col].astype("string").str.strip().str.lower()
    g = g.where(g.isin(["male", "female"]), "unknown")

    if use_id:
        tmp = pd.DataFrame({"_id": df[id_col], "_sf_dt": sf_dt, "_gender": g}).dropna(subset=["_sf_dt"])
        tmp = tmp.sort_values(["_id", "_sf_dt"])
        first = tmp.groupby("_id").first()
        sf_dt_in = first["_sf_dt"]
        g_in = first["_gender"].astype("string").where(first["_gender"].isin(["male", "female"]), "unknown")
        completed_total = int(len(sf_dt_in))
    else:
        sf_dt_in = sf_dt.dropna()
        g_in = g.loc[sf_dt_in.index].astype("string").where(g.loc[sf_dt_in.index].isin(["male", "female"]), "unknown")
        completed_total = int(sf_done.sum())

    monthly_gender = (
        pd.DataFrame({"Month": sf_dt_in.dt.to_period("M").astype(str), "Gender": g_in})
        .value_counts().reset_index(name="Count").sort_values(["Month", "Gender"])
    )
    monthly_gender_pivot = (
        monthly_gender.pivot(index="Month", columns="Gender", values="Count")
        .fillna(0).astype(int).reset_index()
    )
    if "female" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["female"] = 0
    if "male" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["male"] = 0
    if "unknown" not in monthly_gender_pivot.columns:
        monthly_gender_pivot["unknown"] = 0
    monthly_gender_pivot["Total"] = (
        monthly_gender_pivot["female"]
        + monthly_gender_pivot["male"]
        + monthly_gender_pivot["unknown"]
    )
    monthly_gender_pivot = monthly_gender_pivot[
        ["Month", "female", "male", "Total", "unknown"]
    ]
    missing_dates = int((sf_done & sf_dt.isna()).sum())

    safe_families_df = pd.DataFrame(
        [
            ["Completed column used", sf_completed_col],
            ["Date column used", sf_date_col],
            ["Gender column used", gender_col],
            ["Completed total", completed_total],
            ["Completed=yes but date missing", missing_dates],
        ],
        columns=["Metric", "Value"],
    )

    return monthly_gender_pivot, safe_families_df, completed_total, missing_dates
