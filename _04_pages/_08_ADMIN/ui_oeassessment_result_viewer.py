"""
OE Assessment 결과 조회 페이지

이 페이지는 OE Assessment 결과를 조회하고 표시하는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 사용자는 결과를 확인할 수 있습니다.
"""

import numpy as np
from scipy.stats import norm
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from _00_database.db_client import get_client
from _02_preprocessing.GMES.df_production import get_daily_production_df
from _02_preprocessing.GMES.df_ncf import get_ncf_monthly_df, get_ncf_by_dft_cd
from _02_preprocessing.GMES.df_uf import (
    calculate_uf_pass_rate_monthly,
    uf_standard,
    uf_individual,
)
from _01_query.GMES.q_weight import gt_wt_gruopby_ym, gt_wt_individual
from _01_query.GMES.q_ctl import get_ctl_raw_individual_query
from _02_preprocessing.GMES.df_rr import get_processed_raw_rr_data, get_rr_oe_list_df
from _03_visualization._08_ADMIN import viz_oeassessment_result_viewer as viz
from _03_visualization import config_plotly
from _05_commons import config

# 메인 페이지 코드
st.title("OE Assessment Result Viewer")

result_df = get_client("sqlite").execute("SELECT * FROM mass_assess_result")

st.subheader("Assessment Result")

if "result_df" not in st.session_state:
    st.session_state["result_df"] = result_df

event_df = st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True,
    key="event_df",
    on_select="rerun",
    selection_mode="single-row",
)


# example m_code : 1031953
# 2024-04-15 ~ 2024-10-12
selected_mcode = "1031953"
selected_start_date = "20240415"
selected_end_date = "20241012"

formatted_start_date = (
    f"{selected_start_date[:4]}-{selected_start_date[4:6]}-{selected_start_date[6:]}"
)
formatted_end_date = (
    f"{selected_end_date[:4]}-{selected_end_date[4:6]}-{selected_end_date[6:]}"
)

# region 생산량
prdt_df = get_daily_production_df(
    mcode=selected_mcode, start_date=selected_start_date, end_date=selected_end_date
)
st.plotly_chart(viz.draw_barplot_production(prdt_df), use_container_width=True)
# endregion

ncf_cols = st.columns(2)
# region ncf 월별 수량
ncf_df = get_ncf_monthly_df(
    mcode=selected_mcode, start_date=selected_start_date, end_date=selected_end_date
)
ncf_cols[0].plotly_chart(viz.draw_barplot_ncf(ncf_df), use_container_width=True)
# endregion

# region ncf 부적합코드별 수량 조회
ncf_by_dft_cd_df = get_ncf_by_dft_cd(
    mcode=selected_mcode, start_date=selected_start_date, end_date=selected_end_date
)
ncf_cols[1].plotly_chart(
    viz.draw_barplot_ncf_pareto(ncf_by_dft_cd_df), use_container_width=True
)
# endregion

uf_cols = st.columns(2)
# region  uf 월별 합격률

uf_pass_rate_df = calculate_uf_pass_rate_monthly(
    mcode=selected_mcode, start_date=selected_start_date, end_date=selected_end_date
)

uf_cols[0].plotly_chart(viz.draw_barplot_uf(uf_pass_rate_df), use_container_width=True)

# endregion
# region uf 항목별 합격률

uf_standard_df = uf_standard(mcode=selected_mcode)

uf_individual_df = uf_individual(
    mcode=selected_mcode, start_date=selected_start_date, end_date=selected_end_date
)

uf_cols[1].plotly_chart(
    viz.draw_barplot_uf_individual(uf_individual_df, uf_standard_df),
    use_container_width=True,
)
# endregion

wt_col = st.columns(2)
# region 중량 부적합
wt_df = get_client("snowflake").execute(
    gt_wt_gruopby_ym(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
)
wt_df.columns = wt_df.columns.str.upper()
wt_df["PASS_PCT"] = wt_df["WT_PASS_QTY"] / wt_df["WT_INS_QTY"]

wt_col[0].plotly_chart(viz.draw_weight_distribution(wt_df), use_container_width=True)

# 중량 분포
wt_individual_df = get_client("snowflake").execute(
    gt_wt_individual(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
)
wt_individual_df.columns = wt_individual_df.columns.str.upper()
wt_individual_df["INS_DATE"] = pd.to_datetime(wt_individual_df["INS_DATE"])
wt_individual_df["INS_DATE_YM"] = wt_individual_df["INS_DATE"].dt.strftime("%Y-%m")


# 아웃라이어 제거를 위한 IQR 계산
def remove_outliers(group):
    Q1 = group["MRM_WGT"].quantile(0.25)
    Q3 = group["MRM_WGT"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return group[(group["MRM_WGT"] >= lower_bound) & (group["MRM_WGT"] <= upper_bound)]


# 월별로 아웃라이어 제거
wt_individual_df_no_outliers = (
    wt_individual_df.groupby("INS_DATE_YM")
    .apply(remove_outliers)
    .reset_index(drop=True)
)

wt_spec = wt_individual_df["STD_WGT"].iloc[-1]

wt_col[1].plotly_chart(
    viz.draw_weight_distribution_individual(wt_individual_df_no_outliers, wt_spec),
    use_container_width=True,
)
# endregion

rr_col = st.columns(2)
# region RR
# 날짜 형식을 yyyy-mm-dd로 변환

rr_df = get_processed_raw_rr_data(
    mcode=selected_mcode,
    start_date=formatted_start_date,
    end_date=formatted_end_date,
)
rr_df = rr_df.sort_values(by="SMPL_DATE").reset_index(drop=True)
rr_standard_df = get_rr_oe_list_df()
rr_standard_df = rr_standard_df[rr_standard_df["M_CODE"] == selected_mcode]

if len(rr_df) > 0:

    rr_col[0].plotly_chart(
        viz.draw_rr_trend(rr_df, rr_standard_df), use_container_width=True
    )

    rr_col[1].plotly_chart(
        viz.draw_rr_distribution(rr_df, rr_standard_df), use_container_width=True
    )
else:
    st.warning("No RR data found")

# endregion

ctl_col = st.columns([1, 3])
# region CTL
# CTL
ctl_df = get_client("snowflake").execute(
    get_ctl_raw_individual_query(
        mcode=selected_mcode,
        start_date=selected_start_date,  # YYYYMMDD 형식 사용
        end_date=selected_end_date,  # YYYYMMDD 형식 사용
    )
)
ctl_df.columns = ctl_df.columns.str.upper()
if len(ctl_df) > 0:
    gruopby_ctl_df = (
        ctl_df.groupby(["DOC_NO", "MRM_DATE"])
        .agg(
            COUNT=("JDG", "count"),
            OK=("JDG", lambda x: (x == "OK").sum()),
            NO=("JDG", lambda x: (x == "NO").sum()),
            NI=("JDG", lambda x: (x == "NI").sum()),
        )
        .reset_index()
    )
    gruopby_ctl_df["ctl_pass_rate"] = gruopby_ctl_df["OK"] / (
        gruopby_ctl_df["COUNT"] - gruopby_ctl_df["NO"]
    )

    ctl_col[0].plotly_chart(
        viz.draw_ctl_trend(gruopby_ctl_df), use_container_width=True
    )

    ctl_col[1].plotly_chart(viz.draw_ctl_detail(ctl_df), use_container_width=True)


else:
    st.warning("No CTL data found")


# endregion
