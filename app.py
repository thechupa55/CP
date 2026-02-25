# app.py
import io
import re
import pandas as pd
import streamlit as st

from config import (
    CP_SERVICE_DEFAULT_LETTERS,
    CP_SERVICE_DEFAULT_NAMES,
    SAFE_FAMILIES_DEFAULT_LETTERS,
    SAFE_FAMILIES_DEFAULT_NAMES,
    STRUCTURED_DEFAULTS,
)
from core import (
    cp_services_indicator_core,
    disability_gender_core,
    geography_analysis_core,
    safe_families_monthly_gender_core,
    structured_core,
    structured_monthly_first_time_core,
)
from utils import build_report_excel, make_unique_columns

SAVE_THE_CHILDREN_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/5/5c/Save_the_Children_Logo.svg"
SAVE_THE_CHILDREN_RED = "#DA291C"
SAVE_THE_CHILDREN_BLACK = "#111111"


def _normalize_col(name: str) -> str:
    return str(name).strip().casefold()


def _find_default_index(options: list[str], default_name: str) -> int:
    if not options:
        return 0
    target = _normalize_col(default_name)
    normalized = [_normalize_col(o) for o in options]
    if target in normalized:
        return normalized.index(target)
    for i, n in enumerate(normalized):
        if n.startswith(target + "__"):
            return i
    for i, n in enumerate(normalized):
        if target in n:
            return i
    return 0


def pick_col_with_default(df: pd.DataFrame, label: str, default_name: str, key: str | None = None):
    opts = df.columns.tolist()
    idx = _find_default_index(opts, default_name)
    return st.selectbox(label, opts, index=idx, key=key)


def _canon_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).strip().casefold())


def _resolve_col_name(options: list[str], target_name: str) -> str | None:
    target_norm = _normalize_col(target_name)
    for col in options:
        n = _normalize_col(col)
        if n == target_norm or n.startswith(target_norm + "__"):
            return col

    target_canon = _canon_col(target_name)
    for col in options:
        if _canon_col(col) == target_canon:
            return col
    for col in options:
        if target_canon and target_canon in _canon_col(col):
            return col
    return None


@st.cache_data(show_spinner=False)
def get_sheet_names(file_bytes: bytes) -> list[str]:
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


@st.cache_data(show_spinner=False)
def read_excel_sheet(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)


def apply_theme(theme_mode: str):
    if theme_mode != "Save the Children corporate":
        return

    st.markdown(
        f"""
        <style>
            [data-testid="stAppViewContainer"] {{
                background:
                    radial-gradient(circle at 15% 15%, rgba(218, 41, 28, 0.10), transparent 40%),
                    radial-gradient(circle at 85% 5%, rgba(218, 41, 28, 0.08), transparent 35%),
                    linear-gradient(180deg, #ffffff 0%, #fff8f7 100%);
            }}
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #ffffff 0%, #fff3f1 100%);
                border-right: 1px solid rgba(218, 41, 28, 0.20);
            }}
            .stMetric {{
                border: 1px solid rgba(218, 41, 28, 0.28);
                border-radius: 12px;
                padding: 0.5rem 0.8rem;
                background: #ffffff;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.3rem;
            }}
            .stTabs [data-baseweb="tab"] {{
                background: #fff5f4;
                border: 1px solid rgba(218, 41, 28, 0.25);
                border-radius: 10px 10px 0 0;
            }}
            .stTabs [aria-selected="true"] {{
                background: {SAVE_THE_CHILDREN_RED};
                color: #ffffff;
                border-color: {SAVE_THE_CHILDREN_RED};
            }}
            .stButton > button, .stDownloadButton > button {{
                background: {SAVE_THE_CHILDREN_RED};
                color: #ffffff;
                border: 1px solid {SAVE_THE_CHILDREN_RED};
                border-radius: 10px;
                font-weight: 600;
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{
                background: #b52319;
                border-color: #b52319;
                color: #ffffff;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(theme_mode: str):
    if theme_mode == "Save the Children corporate":
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
              <img src="{SAVE_THE_CHILDREN_LOGO_URL}" alt="Save the Children logo" style="height:48px;max-width:260px;object-fit:contain;">
              <div>
                <div style="font-size:1.6rem;font-weight:800;color:{SAVE_THE_CHILDREN_BLACK};line-height:1.1;">
                  MEAL Counter Tool
                </div>
                <div style="font-size:0.95rem;color:#5a5a5a;">Corporate Theme - Save the Children</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title("MEAL Counter Tool v1")


def main():
    # =============================
    # Page
    # =============================
    st.set_page_config(page_title="MEAL Counter Tool v1", layout="wide")
    
    # =============================
    # Sidebar: load file / sheet / id
    # =============================
    with st.sidebar:
        st.header("Settings")
        theme_mode = st.selectbox(
            "Design",
            ["default", "Save the Children corporate"],
            index=0,
            key="ui_theme_mode",
        )
        uploaded = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        preview_rows = st.number_input("Preview rows", min_value=5, max_value=200, value=20, step=5)
        st.divider()

    apply_theme(theme_mode)
    render_header(theme_mode)
    
    if not uploaded:
        st.info("Upload an Excel file to start.")
        st.stop()
    
    try:
        file_bytes = uploaded.getvalue()
        sheet_names = get_sheet_names(file_bytes)
    except Exception as e:
        st.error(f"Cannot read Excel file: {e}")
        st.stop()
    
    with st.sidebar:
        sheet = st.selectbox("Select sheet", sheet_names, key="sidebar_sheet")
    
    try:
        df = read_excel_sheet(file_bytes, sheet)
    except Exception as e:
        st.error(f"Cannot read selected sheet: {e}")
        st.stop()
    
    df.columns = df.columns.astype(str).str.strip()
    df.columns = make_unique_columns(df.columns)
    
    with st.sidebar:
        st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns):,}")
        id_col = st.selectbox("Optional: Unique Child ID column", ["(none)"] + df.columns.tolist(), key="sidebar_id")
        use_id = id_col != "(none)"
        if use_id and df[id_col].isna().any():
            st.warning("Some rows have missing Child ID. Those rows are excluded from ID-based groupings.")
    
    # =============================
    # Tabs
    # =============================
    tab_preview, tab_struct, tab_struct_month, tab_cp, tab_sf_month, tab_geo, tab_disability, tab_downloads = st.tabs(
        [
            "Preview",
            "Structured",
            "Structured Monthly",
            "CP Services Indicator",
            "Safe Families Monthly",
            "Geography",
            "Disability",
            "Downloads",
        ]
    )
    
    # -----------------------------
    # Preview
    # -----------------------------
    with tab_preview:
        st.subheader("Data preview")
        st.dataframe(df.head(int(preview_rows)), use_container_width=True)
    
    # -----------------------------
    # Structured
    # -----------------------------
    with tab_struct:
        st.subheader("Structured programs (TEAM_UP / HEART / CYR / ISMF)")
    
        col_left, col_right = st.columns(2)
        with col_left:
            p1_name = st.text_input(
                "Program 1 name",
                value=STRUCTURED_DEFAULTS["programs"][0][0],
                key=f"p1_name_ui__{sheet}",
            )
            p1_col = pick_col_with_default(
                df,
                "Program 1 column",
                STRUCTURED_DEFAULTS["programs"][0][1],
                key=f"p1_col_ui__{sheet}",
            )
    
            p2_name = st.text_input(
                "Program 2 name",
                value=STRUCTURED_DEFAULTS["programs"][1][0],
                key=f"p2_name_ui__{sheet}",
            )
            p2_col = pick_col_with_default(
                df,
                "Program 2 column",
                STRUCTURED_DEFAULTS["programs"][1][1],
                key=f"p2_col_ui__{sheet}",
            )
    
        with col_right:
            p3_name = st.text_input(
                "Program 3 name",
                value=STRUCTURED_DEFAULTS["programs"][2][0],
                key=f"p3_name_ui__{sheet}",
            )
            p3_col = pick_col_with_default(
                df,
                "Program 3 column",
                STRUCTURED_DEFAULTS["programs"][2][1],
                key=f"p3_col_ui__{sheet}",
            )
    
            p4_name = st.text_input(
                "Program 4 name",
                value=STRUCTURED_DEFAULTS["programs"][3][0],
                key=f"p4_name_ui__{sheet}",
            )
            p4_col = pick_col_with_default(
                df,
                "Program 4 column",
                STRUCTURED_DEFAULTS["programs"][3][1],
                key=f"p4_col_ui__{sheet}",
            )
    
        programs = [
            (p1_name.strip() or "PROGRAM_1", p1_col),
            (p2_name.strip() or "PROGRAM_2", p2_col),
            (p3_name.strip() or "PROGRAM_3", p3_col),
            (p4_name.strip() or "PROGRAM_4", p4_col),
        ]
    
        chosen_cols = [c for _, c in programs]
        if len(set(chosen_cols)) < len(chosen_cols):
            st.warning("You selected the same column for multiple programs. Results will be distorted.")
    
        export_filter = st.selectbox(
            "Export rows (structured filter)",
            [
                "All rows",
                "Only children with at least 1 structured program",
                "Only children with 0 structured programs",
                "Only children with 2+ structured programs",
                "Only children with exactly 1 structured program",
            ],
            key="structured_export_mode_ui",
        )
    
        structured = structured_core(df, use_id, id_col, programs, export_filter)
        st.session_state["structured_cached"] = structured
    
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total children", f"{structured['n_total']:,}")
        c2.metric("At least 1 structured program", f"{structured['n_any']:,}")
        c3.metric("0 structured programs", f"{int(structured['dist'][0]):,}")
        c4.metric("2+ structured programs", f"{int(structured['dist'][2] + structured['dist'][3] + structured['dist'][4]):,}")
    
        st.divider()
        subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs(
            ["Summary", "Per program", "Only one", "Combinations", "Export preview"]
        )
        with subtab1:
            st.dataframe(structured["structured_summary_df"], use_container_width=True)
        with subtab2:
            st.dataframe(structured["structured_per_program_df"], use_container_width=True)
        with subtab3:
            st.dataframe(structured["structured_only_one_df"], use_container_width=True)
        with subtab4:
            st.dataframe(structured["structured_combo_df"], use_container_width=True)
        with subtab5:
            st.caption(f"Export rows: {len(structured['export_rows']):,}")
            st.dataframe(structured["export_rows"].head(50), use_container_width=True)
    
            # unique key
            st.download_button(
                "Download export rows (CSV)",
                data=structured["export_rows"].to_csv(index=False).encode("utf-8"),
                file_name="MEAL_Counter_ExportRows.csv",
                mime="text/csv",
                key="dl_export_rows_structured_tab",
            )
    
    # -----------------------------
    # Structured Monthly
    # -----------------------------
    with tab_struct_month:
        st.subheader("Monthly achievements: Structured MHPSS (first-time completion)")
        st.caption("Counts child in the month of their FIRST completed structured program.")
    
        team_completed_col = pick_col_with_default(
            df,
            "TEAM_UP Completed column",
            STRUCTURED_DEFAULTS["programs"][0][1],
            key=f"m_team_comp__{sheet}",
        )
        team_date_col = pick_col_with_default(
            df,
            "TEAM_UP completion date column",
            STRUCTURED_DEFAULTS["dates"]["TEAM_UP"],
            key=f"m_team_date__{sheet}",
        )
    
        heart_completed_col = pick_col_with_default(
            df,
            "HEART Completed column",
            STRUCTURED_DEFAULTS["programs"][1][1],
            key=f"m_heart_comp__{sheet}",
        )
        heart_date_col = pick_col_with_default(
            df,
            "HEART completion date column",
            STRUCTURED_DEFAULTS["dates"]["HEART"],
            key=f"m_heart_date__{sheet}",
        )
    
        cyr_completed_col = pick_col_with_default(
            df,
            "CYR Completed column",
            STRUCTURED_DEFAULTS["programs"][2][1],
            key=f"m_cyr_comp__{sheet}",
        )
        cyr_date_col = pick_col_with_default(
            df,
            "CYR completion date column",
            STRUCTURED_DEFAULTS["dates"]["CYR"],
            key=f"m_cyr_date__{sheet}",
        )
    
        ismf_completed_col = pick_col_with_default(
            df,
            "ISMF Completed column",
            STRUCTURED_DEFAULTS["programs"][3][1],
            key=f"m_ismf_comp__{sheet}",
        )
        ismf_date_col = pick_col_with_default(
            df,
            "ISMF completion date column",
            STRUCTURED_DEFAULTS["dates"]["ISMF"],
            key=f"m_ismf_date__{sheet}",
        )
    
        gender_col = pick_col_with_default(
            df,
            "Gender column",
            STRUCTURED_DEFAULTS["gender"],
            key=f"m_gender__{sheet}",
        )
    
        monthly_struct = structured_monthly_first_time_core(
            df, use_id, id_col,
            team_completed_col, team_date_col,
            heart_completed_col, heart_date_col,
            cyr_completed_col, cyr_date_col,
            ismf_completed_col, ismf_date_col,
            gender_col
        )
    
        available_months = (
            monthly_struct["first_dt"]
            .dropna()
            .dt.to_period("M")
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )
        month_options = ["All months"] + available_months
        selected_month = st.selectbox(
            "Select month for detailed information",
            month_options,
            key=f"struct_month_filter__{sheet}",
        )
        month_suffix = "all_months" if selected_month == "All months" else selected_month.replace("-", "_")
    
        def _filter_by_month(monthly_df: pd.DataFrame) -> pd.DataFrame:
            if selected_month == "All months":
                return monthly_df
            filtered = monthly_df.copy()
            return filtered[filtered["Month"].astype("string") == selected_month].reset_index(drop=True)
    
        qa1, qa2, qa3 = st.columns(3)
        qa1.metric("Total first-time structured (all time)", f"{int(monthly_struct['first_dt'].dropna().shape[0]):,}")
        qa2.metric("Completed=yes but date missing (any program)", f"{int(monthly_struct['missing_date_count']):,}")
        qa3.metric("Children with no structured completion", f"{int(monthly_struct['first_dt'].isna().sum()):,}")
        selected_month_count = int(
            monthly_struct["first_dt"].dropna().dt.to_period("M").astype(str).eq(selected_month).sum()
        ) if selected_month != "All months" else int(monthly_struct["first_dt"].dropna().shape[0])
        st.caption(f"Selected month: {selected_month} | First-time structured in selection: {selected_month_count:,}")
    
        st.divider()
        mt1, mt2, mt3, mt4, mt5 = st.tabs(
            ["Monthly total", "Monthly by first program", "Monthly by gender", "Children list", "Monthly by first program + gender"]
        )
        with mt1:
            monthly_total_view = _filter_by_month(monthly_struct["monthly_total"])
            st.dataframe(monthly_total_view, use_container_width=True)
            st.download_button(
                "Download monthly totals (CSV)",
                data=monthly_total_view.to_csv(index=False).encode("utf-8"),
                file_name=f"structured_mhpss_first_time_monthly_{month_suffix}.csv",
                mime="text/csv",
                key="dl_struct_monthly_total",
            )
        with mt2:
            monthly_by_program_view = _filter_by_month(monthly_struct["monthly_by_program"])
            st.dataframe(monthly_by_program_view, use_container_width=True)
            st.download_button(
                "Download monthly by first program (CSV)",
                data=monthly_by_program_view.to_csv(index=False).encode("utf-8"),
                file_name=f"structured_mhpss_first_time_monthly_by_program_{month_suffix}.csv",
                mime="text/csv",
                key="dl_struct_monthly_by_program",
            )
        with mt3:
            monthly_by_gender_view = _filter_by_month(monthly_struct["monthly_by_gender_pivot"])
            st.dataframe(monthly_by_gender_view, use_container_width=True)
            st.download_button(
                "Download monthly by gender (CSV)",
                data=monthly_by_gender_view.to_csv(index=False).encode("utf-8"),
                file_name=f"structured_mhpss_first_time_monthly_by_gender_{month_suffix}.csv",
                mime="text/csv",
                key="dl_struct_monthly_by_gender",
            )
        with mt4:
            required_cols = ["Child Full Name", "Full Parent Name", "Parents phone"]
            resolved_cols = {c: _resolve_col_name(df.columns.tolist(), c) for c in required_cols}
            missing_cols = [c for c, real_col in resolved_cols.items() if real_col is None]

            if missing_cols:
                st.warning(
                    f"Could not auto-detect columns: {', '.join(missing_cols)}. "
                    "Please map them manually below."
                )
                resolved_cols["Child Full Name"] = st.selectbox(
                    "Child Full Name column",
                    df.columns.tolist(),
                    index=_find_default_index(df.columns.tolist(), "Child Full Name"),
                    key=f"m_child_full_name__{sheet}",
                )
                resolved_cols["Full Parent Name"] = st.selectbox(
                    "Full Parent Name column",
                    df.columns.tolist(),
                    index=_find_default_index(df.columns.tolist(), "Full Parent Name"),
                    key=f"m_full_parent_name__{sheet}",
                )
                resolved_cols["Parents phone"] = st.selectbox(
                    "Parents phone column",
                    df.columns.tolist(),
                    index=_find_default_index(df.columns.tolist(), "Parents phone"),
                    key=f"m_parents_phone__{sheet}",
                )

            first_meta = pd.DataFrame(
                {
                    "_row_index": monthly_struct["first_row_index"],
                    "First structured date": monthly_struct["first_dt"],
                    "First structured program": monthly_struct["first_program"],
                }
            ).dropna(subset=["_row_index"])
            if selected_month != "All months":
                first_meta = first_meta[
                    first_meta["First structured date"].dt.to_period("M").astype(str) == selected_month
                ]

            if first_meta.empty:
                st.info(f"No first-time structured completions found for {selected_month}.")
            else:
                first_meta["_row_index"] = first_meta["_row_index"].astype(int)
                selected_cols = [resolved_cols[c] for c in required_cols]
                child_list_df = df.loc[first_meta["_row_index"], selected_cols].reset_index(drop=True)
                child_list_df.columns = required_cols
                child_list_df = pd.concat(
                    [
                        child_list_df,
                        first_meta[["First structured date", "First structured program"]].reset_index(drop=True),
                    ],
                    axis=1,
                )
                child_list_df["First structured date"] = pd.to_datetime(
                    child_list_df["First structured date"], errors="coerce"
                ).dt.date

                st.caption(f"Children in first-time structured list: {len(child_list_df):,}")
                st.dataframe(child_list_df, use_container_width=True)
                st.download_button(
                    "Download children list (CSV)",
                    data=child_list_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"structured_mhpss_children_list_{month_suffix}.csv",
                    mime="text/csv",
                    key="dl_struct_monthly_children_list",
                )
        with mt5:
            monthly_by_program_gender_view = _filter_by_month(monthly_struct["monthly_by_program_gender_pivot"])
            st.dataframe(monthly_by_program_gender_view, use_container_width=True)
            st.download_button(
                "Download monthly by first program + gender (CSV)",
                data=monthly_by_program_gender_view.to_csv(index=False).encode("utf-8"),
                file_name=f"structured_mhpss_first_time_monthly_by_program_gender_{month_suffix}.csv",
                mime="text/csv",
                key="dl_struct_monthly_by_program_gender",
            )
    
    # -----------------------------
    # CP Services Indicator
    # -----------------------------
    with tab_cp:
        st.subheader("Indicator: # of individuals participating in child protection services (>=2 total sessions)")
        st.caption("Logic: total sessions across ALL activities >= 2. Columns by Excel letters: AL, AO, AR, AU, AZ, BC, BD, BG")
    
        team_s_col = st.selectbox(
            f"TEAM_UP sessions ({CP_SERVICE_DEFAULT_LETTERS['TEAM_UP']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["TEAM_UP"]),
            key=f"cp_team__{sheet}",
        )
        heart_s_col = st.selectbox(
            f"HEART sessions ({CP_SERVICE_DEFAULT_LETTERS['HEART']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["HEART"]),
            key=f"cp_heart__{sheet}",
        )
        cyr_s_col = st.selectbox(
            f"CYR sessions ({CP_SERVICE_DEFAULT_LETTERS['CYR']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["CYR"]),
            key=f"cp_cyr__{sheet}",
        )
        ismf_s_col = st.selectbox(
            f"ISMF sessions ({CP_SERVICE_DEFAULT_LETTERS['ISMF']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["ISMF"]),
            key=f"cp_ismf__{sheet}",
        )
        sf_s_col = st.selectbox(
            f"Safe Families sessions ({CP_SERVICE_DEFAULT_LETTERS['SAFE_FAMILIES']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["SAFE_FAMILIES"]),
            key=f"cp_sf__{sheet}",
        )
        rec_s_col = st.selectbox(
            f"Recreational sessions ({CP_SERVICE_DEFAULT_LETTERS['RECREATIONAL']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["RECREATIONAL"]),
            key=f"cp_rec__{sheet}",
        )
        infedu_s_col = st.selectbox(
            f"Informal Education sessions ({CP_SERVICE_DEFAULT_LETTERS['INFORMAL_EDU']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["INFORMAL_EDU"]),
            key=f"cp_infedu__{sheet}",
        )
        eore_s_col = st.selectbox(
            f"EORE sessions ({CP_SERVICE_DEFAULT_LETTERS['EORE']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), CP_SERVICE_DEFAULT_NAMES["EORE"]),
            key=f"cp_eore__{sheet}",
        )
    
        total_sessions, indicator_mask = cp_services_indicator_core(
            df, use_id, id_col,
            team_s_col, heart_s_col, cyr_s_col, ismf_s_col,
            sf_s_col, rec_s_col, infedu_s_col, eore_s_col
        )
    
        indicator_total = int(indicator_mask.sum())
        indicator_total_children = int(len(total_sessions))
        indicator_rate = (indicator_total / indicator_total_children * 100) if indicator_total_children > 0 else 0.0
    
        i1, i2, i3 = st.columns(3)
        i1.metric("Children meeting indicator", f"{indicator_total:,}")
        i2.metric("Total children considered", f"{indicator_total_children:,}")
        i3.metric("Rate (%)", f"{indicator_rate:.2f}%")
    
        with st.expander("Indicator validation (breakdown)", expanded=False):
            st.write({
                "Children with 0 sessions": int((total_sessions == 0).sum()),
                "Children with exactly 1 session": int((total_sessions == 1).sum()),
                "Children with >=2 sessions": int((total_sessions >= 2).sum()),
                "Average sessions per child": round(float(total_sessions.mean()), 2),
                "Max sessions per child": float(total_sessions.max()),
            })
    
        if st.checkbox("Enable export list: children meeting indicator (>=2 sessions)", key="cp_export_chk"):
            if use_id:
                ids = total_sessions[indicator_mask].index
                export_indicator_df = df[df[id_col].isin(ids)].copy()
            else:
                export_indicator_df = df.loc[indicator_mask].copy()
    
            export_indicator_df.columns = make_unique_columns(export_indicator_df.columns)
    
            st.download_button(
                "Download indicator children (CSV)",
                data=export_indicator_df.to_csv(index=False).encode("utf-8"),
                file_name="indicator_CP_services_children.csv",
                mime="text/csv",
                key="dl_cp_indicator_children",
            )
    
    # -----------------------------
    # Safe Families Monthly by Gender
    # -----------------------------
    with tab_sf_month:
        st.subheader("Safe Families: monthly achievements by gender")
        st.caption("BA = Completed (Yes/No), BB = Completion Date (MMDDYYYY), U = gender (boy/girl)")
    
        sf_completed_col = st.selectbox(
            f"Safe Families Completed ({SAFE_FAMILIES_DEFAULT_LETTERS['completed']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), SAFE_FAMILIES_DEFAULT_NAMES["completed"]),
            key=f"sf_comp__{sheet}",
        )
        sf_date_col = st.selectbox(
            f"Safe Families completion date ({SAFE_FAMILIES_DEFAULT_LETTERS['date']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), SAFE_FAMILIES_DEFAULT_NAMES["date"]),
            key=f"sf_date__{sheet}",
        )
        gender_col = st.selectbox(
            f"Gender column ({SAFE_FAMILIES_DEFAULT_LETTERS['gender']})",
            df.columns.tolist(),
            index=_find_default_index(df.columns.tolist(), SAFE_FAMILIES_DEFAULT_NAMES["gender"]),
            key=f"sf_gender__{sheet}",
        )
    
        sf_monthly_pivot, sf_summary_df, sf_completed_total, sf_missing_dates = safe_families_monthly_gender_core(
            df, use_id, id_col, sf_completed_col, sf_date_col, gender_col
        )
    
        c1, c2 = st.columns(2)
        c1.metric("Safe Families completed (total)", f"{sf_completed_total:,}")
        c2.metric("Completed=yes but date missing", f"{sf_missing_dates:,}")
    
        st.dataframe(sf_monthly_pivot, use_container_width=True)
    
        st.download_button(
            "Download Safe Families monthly by gender (CSV)",
            data=sf_monthly_pivot.to_csv(index=False).encode("utf-8"),
            file_name="safe_families_monthly_by_gender.csv",
            mime="text/csv",
            key="dl_sf_monthly_by_gender",
        )
    
        st.session_state["safe_families_cached"] = {
            "monthly": sf_monthly_pivot,
            "summary": sf_summary_df,
        }

    # -----------------------------
    # Geography
    # -----------------------------
    with tab_geo:
        st.subheader("Geography analysis")
        st.caption("Default mapping from source file: D = Oblast, E = Raion, F = Hromada, G = Settlement")

        geo_col1, geo_col2 = st.columns(2)
        with geo_col1:
            oblast_col = pick_col_with_default(
                df,
                "Oblast column",
                "Oblast",
                key=f"geo_oblast__{sheet}",
            )
            hromada_col = pick_col_with_default(
                df,
                "Hromada column",
                "Hromada",
                key=f"geo_hromada__{sheet}",
            )
        with geo_col2:
            raion_col = pick_col_with_default(
                df,
                "Raion column",
                "Raion",
                key=f"geo_raion__{sheet}",
            )
            settlement_col = pick_col_with_default(
                df,
                "Settlement column",
                "Settlement",
                key=f"geo_settlement__{sheet}",
            )

        st.divider()
        st.caption("Filter rule: only children meeting CP indicator (>=2 total sessions).")

        cp_col_left, cp_col_right = st.columns(2)
        cp_opts = df.columns.tolist()

        def _geo_cp_default_index(state_key: str, default_name: str) -> int:
            selected = st.session_state.get(state_key)
            if isinstance(selected, str) and selected in cp_opts:
                return cp_opts.index(selected)
            return _find_default_index(cp_opts, default_name)

        with cp_col_left:
            geo_team_s_col = st.selectbox(
                "TEAM_UP sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_team__{sheet}", CP_SERVICE_DEFAULT_NAMES["TEAM_UP"]),
                key=f"geo_cp_team__{sheet}",
            )
            geo_cyr_s_col = st.selectbox(
                "CYR sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_cyr__{sheet}", CP_SERVICE_DEFAULT_NAMES["CYR"]),
                key=f"geo_cp_cyr__{sheet}",
            )
            geo_sf_s_col = st.selectbox(
                "Safe Families sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_sf__{sheet}", CP_SERVICE_DEFAULT_NAMES["SAFE_FAMILIES"]),
                key=f"geo_cp_sf__{sheet}",
            )
            geo_infedu_s_col = st.selectbox(
                "Informal Education sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_infedu__{sheet}", CP_SERVICE_DEFAULT_NAMES["INFORMAL_EDU"]),
                key=f"geo_cp_infedu__{sheet}",
            )
        with cp_col_right:
            geo_heart_s_col = st.selectbox(
                "HEART sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_heart__{sheet}", CP_SERVICE_DEFAULT_NAMES["HEART"]),
                key=f"geo_cp_heart__{sheet}",
            )
            geo_ismf_s_col = st.selectbox(
                "ISMF sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_ismf__{sheet}", CP_SERVICE_DEFAULT_NAMES["ISMF"]),
                key=f"geo_cp_ismf__{sheet}",
            )
            geo_rec_s_col = st.selectbox(
                "Recreational sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_rec__{sheet}", CP_SERVICE_DEFAULT_NAMES["RECREATIONAL"]),
                key=f"geo_cp_rec__{sheet}",
            )
            geo_eore_s_col = st.selectbox(
                "EORE sessions column",
                cp_opts,
                index=_geo_cp_default_index(f"cp_eore__{sheet}", CP_SERVICE_DEFAULT_NAMES["EORE"]),
                key=f"geo_cp_eore__{sheet}",
            )

        geo_total_sessions, geo_indicator_mask = cp_services_indicator_core(
            df,
            use_id,
            id_col,
            geo_team_s_col,
            geo_heart_s_col,
            geo_cyr_s_col,
            geo_ismf_s_col,
            geo_sf_s_col,
            geo_rec_s_col,
            geo_infedu_s_col,
            geo_eore_s_col,
        )

        geo_indicator_total = int(geo_indicator_mask.sum())
        geo_considered_total = int(len(geo_total_sessions))
        geo_indicator_rate = (geo_indicator_total / geo_considered_total * 100) if geo_considered_total > 0 else 0.0

        if use_id:
            indicator_ids = geo_total_sessions[geo_indicator_mask].index
            geo_source_df = df[df[id_col].isin(indicator_ids)].copy()
        else:
            geo_source_df = df.loc[geo_indicator_mask].copy()

        geo = geography_analysis_core(
            geo_source_df,
            use_id,
            id_col,
            oblast_col,
            raion_col,
            hromada_col,
            settlement_col,
        )

        gm1, gm2, gm3, gm4, gm5 = st.columns(5)
        gm1.metric("Children in indicator", f"{geo['n_total']:,}")
        gm2.metric("Unique oblast", f"{geo['n_oblast']:,}")
        gm3.metric("Unique raion", f"{geo['n_raion']:,}")
        gm4.metric("Unique hromada", f"{geo['n_hromada']:,}")
        gm5.metric("Unique settlement", f"{geo['n_settlement']:,}")
        st.caption(
            f"Indicator filter result: {geo_indicator_total:,} of {geo_considered_total:,} children ({geo_indicator_rate:.2f}%)."
        )

        gt1, gt2, gt3, gt4, gt5 = st.tabs(
            ["By Oblast", "By Raion", "By Hromada", "By Settlement", "Hierarchy"]
        )

        with gt1:
            st.dataframe(geo["by_oblast"], use_container_width=True)
            st.download_button(
                "Download by oblast (CSV)",
                data=geo["by_oblast"].to_csv(index=False).encode("utf-8"),
                file_name="geography_by_oblast.csv",
                mime="text/csv",
                key="dl_geo_oblast",
            )
        with gt2:
            st.dataframe(geo["by_raion"], use_container_width=True)
            st.download_button(
                "Download by raion (CSV)",
                data=geo["by_raion"].to_csv(index=False).encode("utf-8"),
                file_name="geography_by_raion.csv",
                mime="text/csv",
                key="dl_geo_raion",
            )
        with gt3:
            st.dataframe(geo["by_hromada"], use_container_width=True)
            st.download_button(
                "Download by hromada (CSV)",
                data=geo["by_hromada"].to_csv(index=False).encode("utf-8"),
                file_name="geography_by_hromada.csv",
                mime="text/csv",
                key="dl_geo_hromada",
            )
        with gt4:
            st.dataframe(geo["by_settlement"], use_container_width=True)
            st.download_button(
                "Download by settlement (CSV)",
                data=geo["by_settlement"].to_csv(index=False).encode("utf-8"),
                file_name="geography_by_settlement.csv",
                mime="text/csv",
                key="dl_geo_settlement",
            )
        with gt5:
            oblast_filter_options = ["All oblasts"] + geo["by_oblast"]["Oblast"].tolist()
            selected_oblast = st.selectbox(
                "Filter hierarchy by oblast",
                oblast_filter_options,
                key=f"geo_oblast_filter__{sheet}",
            )

            by_oblast_raion_view = geo["by_oblast_raion"]
            by_full_path_view = geo["by_full_path"]
            if selected_oblast != "All oblasts":
                by_oblast_raion_view = by_oblast_raion_view[by_oblast_raion_view["Oblast"] == selected_oblast].reset_index(drop=True)
                by_full_path_view = by_full_path_view[by_full_path_view["Oblast"] == selected_oblast].reset_index(drop=True)

            st.caption("Oblast -> Raion")
            st.dataframe(by_oblast_raion_view, use_container_width=True)
            st.caption("Oblast -> Raion -> Hromada -> Settlement")
            st.dataframe(by_full_path_view, use_container_width=True)

            st.download_button(
                "Download hierarchy (CSV)",
                data=by_full_path_view.to_csv(index=False).encode("utf-8"),
                file_name="geography_hierarchy_full.csv",
                mime="text/csv",
                key="dl_geo_hierarchy_full",
            )

        st.session_state["geography_cached"] = {
            "by_oblast": geo["by_oblast"],
            "by_raion": geo["by_raion"],
            "by_hromada": geo["by_hromada"],
            "by_settlement": geo["by_settlement"],
            "by_oblast_raion": geo["by_oblast_raion"],
            "by_full_path": geo["by_full_path"],
        }

    # -----------------------------
    # Disability
    # -----------------------------
    with tab_disability:
        st.subheader("Disability status analysis")
        st.caption("Default mapping from source file: X = Disability status, U = Gender")

        dis_col_left, dis_col_right = st.columns(2)
        with dis_col_left:
            disability_col = pick_col_with_default(
                df,
                "Disability status column",
                "Disability status",
                key=f"dis_status__{sheet}",
            )
        with dis_col_right:
            disability_gender_col = pick_col_with_default(
                df,
                "Gender column",
                "Gender",
                key=f"dis_gender__{sheet}",
            )

        dis = disability_gender_core(
            df,
            use_id,
            id_col,
            disability_col,
            disability_gender_col,
        )

        d1, d2 = st.columns(2)
        d1.metric("Children considered", f"{dis['n_total']:,}")
        d2.metric("Unique disability statuses", f"{len(dis['total_by_disability']):,}")

        dt1, dt2 = st.tabs(["Total by disability status", "Disability by gender"])
        with dt1:
            st.dataframe(dis["total_by_disability"], use_container_width=True)
            st.download_button(
                "Download disability totals (CSV)",
                data=dis["total_by_disability"].to_csv(index=False).encode("utf-8"),
                file_name="disability_total_by_status.csv",
                mime="text/csv",
                key="dl_disability_total",
            )
        with dt2:
            st.dataframe(dis["by_disability_gender"], use_container_width=True)
            st.download_button(
                "Download disability by gender (CSV)",
                data=dis["by_disability_gender"].to_csv(index=False).encode("utf-8"),
                file_name="disability_by_gender.csv",
                mime="text/csv",
                key="dl_disability_gender",
            )

        st.session_state["disability_cached"] = {
            "total": dis["total_by_disability"],
            "by_gender": dis["by_disability_gender"],
        }
    
    # -----------------------------
    # Downloads
    # -----------------------------
    with tab_downloads:
        st.subheader("Downloads")
    
        structured_cached = st.session_state.get("structured_cached")
        sf_cached = st.session_state.get("safe_families_cached")
        geo_cached = st.session_state.get("geography_cached")
        disability_cached = st.session_state.get("disability_cached")
    
        if not structured_cached:
            st.warning("Open the 'Structured' tab once to generate structured tables for the Excel report.")
        if not sf_cached:
            st.info("If you want Safe Families tables included in the Excel report, open 'Safe Families Monthly' tab once.")
        if not geo_cached:
            st.info("If you want Geography tables included in the Excel report, open 'Geography' tab once.")
        if not disability_cached:
            st.info("If you want Disability tables included in the Excel report, open 'Disability' tab once.")
    
        sheets = {}
    
        if structured_cached:
            sheets["Structured_Summary"] = structured_cached["structured_summary_df"]
            sheets["Structured_Per_Program"] = structured_cached["structured_per_program_df"]
            sheets["Structured_Only_One"] = structured_cached["structured_only_one_df"]
            sheets["Structured_Combinations"] = structured_cached["structured_combo_df"]
            sheets["Export_Rows"] = structured_cached["export_rows"].head(5000)
    
            # unique key (different from structured tab)
            st.download_button(
                "Download export rows (CSV)",
                data=structured_cached["export_rows"].to_csv(index=False).encode("utf-8"),
                file_name="MEAL_Counter_ExportRows.csv",
                mime="text/csv",
                key="dl_export_rows_downloads_tab",
            )
    
        if sf_cached:
            sheets["Safe_Families_Monthly_Gender"] = sf_cached["monthly"]
            sheets["Safe_Families_Summary"] = sf_cached["summary"]

        if geo_cached:
            sheets["Geo_By_Oblast"] = geo_cached["by_oblast"]
            sheets["Geo_By_Raion"] = geo_cached["by_raion"]
            sheets["Geo_By_Hromada"] = geo_cached["by_hromada"]
            sheets["Geo_By_Settlement"] = geo_cached["by_settlement"]
            sheets["Geo_Oblast_Raion"] = geo_cached["by_oblast_raion"]
            sheets["Geo_Hierarchy_Full"] = geo_cached["by_full_path"]

        if disability_cached:
            sheets["Disability_Total"] = disability_cached["total"]
            sheets["Disability_By_Gender"] = disability_cached["by_gender"]
    
        if sheets:
            report_bytes = build_report_excel(sheets)
            st.download_button(
                "Download report (Excel)",
                data=report_bytes,
                file_name="MEAL_Counter_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_excel_report",
            )
        else:
            st.info("Nothing to export yet. Open at least one analysis tab first.")


if __name__ == "__main__":
    main()
