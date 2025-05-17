"""
RR 분석 대시보드
"""

import sys
import streamlit as st
from datetime import datetime as dt

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _03_visualization import bi_401_rr_analysis
from _02_preprocessing.GMES.df_rr import (
    get_processed_agg_rr_data,
    get_processed_raw_rr_data,
)
from _05_commons import config

# 개발 모드 시 리로드
if config.DEV_MODE:
    import importlib

    importlib.reload(config)
    importlib.reload(bi_401_rr_analysis)

# st.set_page_config(layout="wide")


# 📌 상단 고정값
start_date = dt.strptime(f"{config.this_year}-01-01", "%Y-%m-%d")
end_date = config.today


# ✅ 세션 스테이트 초기화
# 선택된 탭이나 UI 상태를 다른 탭에서도 유지하기 위해 사용
# 즉, form 제출 후에도 현재 탭이나 이전 값들이 유지되도록 함

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Tab 1"


if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Plant-level Overview"

# ✅ 날짜 입력
with st.form("Select Date"):
    input_col = st.columns([3, 3, 1, 2], vertical_alignment="bottom")

    start_date = input_col[0].date_input(label="Start Date", value=start_date.date())
    end_date = input_col[1].date_input(label="End Date", value=end_date)
    input_col[3].form_submit_button("Submit", use_container_width=True)

# ✅ 탭 구성
tabs = st.tabs(["Plant-level Overview", "Specification-Specific Details"])

# ─────────────────────────────
# 🔹 Tab 1: 공장별 집계
# ─────────────────────────────

with tabs[0]:
    overview_col = st.columns([1.5, 5], gap="large")

    agg_rr_df = get_processed_agg_rr_data(start_date=start_date, end_date=end_date)

    with overview_col[0]:
        fig = bi_401_rr_analysis.hbar_expected_pass_rate_by_plant(agg_rr_df)
        st.plotly_chart(fig, use_container_width=True)

    with overview_col[1]:
        fig = bi_401_rr_analysis.histogram_expected_pass_rate_by_plant(agg_rr_df)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Specification-Level Aggregation")
    user_col = st.columns([5, 4, 2], vertical_alignment="bottom", gap="large")
    selected_plant = user_col[0].multiselect(
        "Select Plants", config.plant_codes[:-1], config.plant_codes[:-1]
    )
    minimum_cnt = user_col[1].slider("Minimum measurement count", 3, 20, 5)
    max_spec_check_box = user_col[2].checkbox("Include Max Spec limit", value=True)

    filtered_agg_rr_df = agg_rr_df.loc[  # User Search Option 적용
        agg_rr_df["PLANT"].isin(selected_plant)
    ].loc[agg_rr_df["count"] >= minimum_cnt]
    if not max_spec_check_box:
        filtered_agg_rr_df = filtered_agg_rr_df[
            filtered_agg_rr_df["limit"] == "Nominal"
        ]
    filtered_agg_rr_df = filtered_agg_rr_df.sort_values(by="EPass")

    agg_col = st.columns(2)

    with agg_col[0]:
        fig = bi_401_rr_analysis.scatter_expected_pass_rate_by_project(
            filtered_agg_rr_df
        )
        st.plotly_chart(fig, use_container_width=True)

    with agg_col[1]:
        st.subheader("Specification List")
        display_cols = [
            "PLANT",
            "M_CODE",
            "OEM",
            "VEH",
            "SPEC_MAX",
            "SPEC_MIN",
            "count",
            "avg",
            "std",
            "EPass",
            "Offset",
            "CP",
            "limit",
            "RR_INDEX",
            "MASS",
        ]
        column_config = {
            "M_CODE": st.column_config.TextColumn("M-Code"),
            "VEH": st.column_config.TextColumn("Vehicle"),
            "SPEC_MAX": st.column_config.NumberColumn("MAX", format="%.2f"),
            "SPEC_MIN": st.column_config.NumberColumn("MIN", format="%.2f"),
            "count": st.column_config.NumberColumn("Count"),
            "avg": st.column_config.NumberColumn("Avg.", format="%.2f"),
            "std": st.column_config.NumberColumn("STD", format="%.2f"),
            "EPass": st.column_config.NumberColumn("Expected %", format="%.1f%%"),
            "Offset": st.column_config.NumberColumn("Offset", format="%.1f%%"),
            "CP": st.column_config.NumberColumn("CP", format="%.2f"),
        }
        st.dataframe(
            filtered_agg_rr_df[display_cols],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

# ─────────────────────────────
# 🔹 Tab 2: M-Code 기준 세부 분석
# ─────────────────────────────
with tabs[1]:
    with st.form("Select M_code"):
        mcode_input_col = st.columns([6, 2], vertical_alignment="bottom")
        input_mcode = mcode_input_col[0].number_input(
            "Insert M-Code", value=None, placeholder="Input a number", step=1
        )
        input_mcode = str(input_mcode)

        submitted = mcode_input_col[1].form_submit_button(
            "Submit", use_container_width=True
        )
        if submitted and input_mcode is not None:
            df_raw_rr = get_processed_raw_rr_data(
                start_date=start_date, end_date=end_date, mcode=input_mcode
            )
            fig = bi_401_rr_analysis.scatter_rr_trend_individual(df_raw_rr)
            st.plotly_chart(fig)

            additional_plot_col = st.columns(2, gap="large")
            with additional_plot_col[0]:
                fig = bi_401_rr_analysis.box_rr_individual(df_raw_rr)
                st.plotly_chart(fig)
            with additional_plot_col[1]:
                fig = bi_401_rr_analysis.pdf_rr_individual(df_raw_rr)
                st.plotly_chart(fig)

            st.subheader("Raw Data")

            # 전체 컬럼 LIST = [
            #     "PLANT_x",
            #     "SMPL_DATE",
            #     "M_CODE",
            #     "POSITION",
            #     "JDG",
            #     "TEST_RESULT_OLD",
            #     "OE_TEST_METHOD",
            #     "MASS_YN_x",
            #     "START_DT",
            #     "END_DT",
            #     "Result_new",
            #     "PLANT_y",
            #     "OEM",
            #     "VEH",
            #     "MASS",
            #     "SPEC_MIN",
            #     "SPEC_MAX",
            #     "TEST_FG",
            #     "MASS_YN_y",
            #     "START_DATE",
            #     "END_DATE",
            #     "SPEC_CHANGE",
            #     "CHG_APP_DATE",
            #     "RR_INDEX",
            #     "SELANT_FLG",
            #     "CD_ITEM",
            #     "limit",
            #     "e_max",
            #     "e_min",
            #     "CL",
            # ]
            display_cols = [
                "SMPL_DATE",
                "POSITION",
                "JDG",
                "TEST_RESULT_OLD",
                "Result_new",
            ]
            column_config = {
                "SMPL_DATE": st.column_config.DateColumn("Sample Date"),
                "POSITION": st.column_config.TextColumn("RR Machine Position"),
                "JDG": st.column_config.TextColumn("Judgement"),
                "TEST_RESULT_OLD": st.column_config.NumberColumn(
                    "Result Old", format="%.2f"
                ),
                "Result_new": st.column_config.NumberColumn(
                    "Result New", format="%.2f"
                ),
            }
            st.dataframe(
                df_raw_rr[display_cols],
                column_config=column_config,
                use_container_width=True,
            )
        else:
            st.subheader("Enter the M-Code and press the Submit button.")
