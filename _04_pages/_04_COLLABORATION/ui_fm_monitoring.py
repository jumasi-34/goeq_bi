"""
Global FM 현황 모니터링 대시보드

이 모듈은 전 세계 공장의 FM(Factory Management) 부적합 현황을 모니터링하는 Streamlit 대시보드를 구현합니다.
주요 기능:
- 연도별/공장별 FM 부적합 수량 및 PPM 현황 조회
- 공장별 월간 FM 부적합 추이 분석
- 불량 유형별 부적합 현황 분석

데이터 소스:
- GMES 시스템의 부적합 데이터
- 공장별 생산량 데이터

작성자: [Your Name]
"""

import sys
import streamlit as st
import pandas as pd
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


from _02_preprocessing.GMES import df_ncf
from _03_visualization._04_COLLABORATION import viz_fm_monitoring
from _05_commons import config
from _03_visualization import config_plotly

# 개발 모드에서 모듈 리로드
if config.DEV_MODE:
    import importlib
    from _02_preprocessing.GMES import df_ncf

    importlib.reload(config)
    importlib.reload(df_ncf)
    importlib.reload(viz_fm_monitoring)

# 선택 가능한 연도 범위 설정 (2025년부터 2021년까지)
available_years = list(range(2025, 2020, -1))

# 사용자 입력 컬럼 생성
input_columns = st.columns(2)

# 연도 선택 위젯
selected_year = input_columns[0].selectbox(
    "Select year :", available_years, key="year_select"
)

# 공장 선택 위젯 (마지막 공장 코드 제외)
selected_plant = input_columns[1].selectbox("Select plant :", config.plant_codes[:-1])

# 데이터 로드
global_ncf_monthly = df_ncf.get_global_ncf_monthly_df(selected_year)
global_ncf_monthly_prev = df_ncf.get_global_ncf_monthly_df(selected_year - 1)
yearly_ncf_summary = df_ncf.get_yearly_ncf_ppm_by_plant_df(selected_year)
yearly_ncf_summary_prev = df_ncf.get_yearly_ncf_ppm_by_plant_df(selected_year - 1)
monthly_ppm_data = df_ncf.get_monthly_ncf_ppm_by_plant_df(selected_year, selected_plant)
monthly_ppm_data_prev = df_ncf.get_monthly_ncf_ppm_by_plant_df(
    selected_year - 1, selected_plant
)
defect_type_data = df_ncf.get_ncf_detail_by_plant(selected_year, selected_plant)

# 전역 FM 부적합 현황 섹션
st.markdown(
    f"<h2>Global FM Non-conformance Status : <span style='color: blue;'>{selected_year}</span></h2>",
    unsafe_allow_html=True,
)

# 메트릭 컬럼 생성
st.divider()
metric_columns = st.columns(4, vertical_alignment="center")

# 현재 월 계산 (전월 기준)
current_month = pd.Timestamp.now().month - 1

# 현재 연도와 이전 연도의 데이터 필터링
if selected_year == pd.Timestamp.now().year:
    # 올해인 경우 현재 월까지만 비교
    current_year_data = (
        global_ncf_monthly[global_ncf_monthly["MM"].astype(int) <= current_month]
        .copy()
        .assign(
            total_prdt_qty=lambda x: x["PRDT_QTY"].sum(),
            total_ncf_qty=lambda x: x["NCF_QTY"].sum(),
            avg_ppm=lambda x: x["PPM"].mean(),
        )
    )

    prev_year_data = (
        global_ncf_monthly_prev[
            global_ncf_monthly_prev["MM"].astype(int) <= current_month
        ]
        .copy()
        .assign(
            total_prdt_qty=lambda x: x["PRDT_QTY"].sum(),
            total_ncf_qty=lambda x: x["NCF_QTY"].sum(),
            avg_ppm=lambda x: x["PPM"].mean(),
        )
    )
else:
    # 과거 연도인 경우 12월까지 전체 데이터 비교
    current_year_data = global_ncf_monthly.copy().assign(
        total_prdt_qty=lambda x: x["PRDT_QTY"].sum(),
        total_ncf_qty=lambda x: x["NCF_QTY"].sum(),
        avg_ppm=lambda x: x["PPM"].mean(),
    )

    prev_year_data = global_ncf_monthly_prev.copy().assign(
        total_prdt_qty=lambda x: x["PRDT_QTY"].sum(),
        total_ncf_qty=lambda x: x["NCF_QTY"].sum(),
        avg_ppm=lambda x: x["PPM"].mean(),
    )

# 메트릭 데이터 설명
help = """
Global FM Metrics Overview:

• Production Quantity: Total number of products manufactured  
• Non-conformance Quantity: Total number of defective products  
• Non-conformance Rate: Defect rate in PPM (Parts Per Million)  

Metrics Guide:

• Production Qty: ↑ (Higher) / ↓ (Lower) vs PY (Previous Year)  
• NCF Metrics: Lower (Better) / Higher (Worse) vs Previous Year
"""
metric_columns[0].subheader(
    "Global FM Metrics",
    help=help,
)
metric_columns[0].markdown(
    f"""
    <div style='text-align: left; color: #666666; font-size: 0.9em;'>
        • <b>Period:</b> {selected_year}<br>
        • <b>Comparison Period:</b> {selected_year-1} (Previous Year)<br>
        • <b>Comparison Range:</b> {f'Jan ~ {pd.Timestamp(2024, current_month, 1).strftime("%b")}' if selected_year == pd.Timestamp.now().year else 'Jan ~ Dec'}<br>
        • <b>Metrics:</b> Production Qty, NCF Qty, NCF Rate
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# 생산량 메트릭
metric_columns[1].metric(
    label="Global Production Quantity",
    value=f"{current_year_data['total_prdt_qty'].iloc[0]:,.0f} EA",
    delta=f"{current_year_data['total_prdt_qty'].iloc[0] - prev_year_data['total_prdt_qty'].iloc[0]:,.0f}",
)

# 부적합 수량 메트릭
metric_columns[2].metric(
    label="Global FM Non-conformance Quantity",
    value=f"{current_year_data['total_ncf_qty'].iloc[0]:,.0f} EA",
    delta=f"{current_year_data['total_ncf_qty'].iloc[0] - prev_year_data['total_ncf_qty'].iloc[0]:,.0f}",
    delta_color=(
        "normal"
        if current_year_data["total_ncf_qty"].iloc[0]
        - prev_year_data["total_ncf_qty"].iloc[0]
        >= 0
        else "inverse"
    ),
)

# 부적합률 메트릭
metric_columns[3].metric(
    label="Global FM Non-conformance Rate",
    value=f"{current_year_data['avg_ppm'].iloc[0]:,.0f} PPM",
    delta=f"{current_year_data['avg_ppm'].iloc[0] - prev_year_data['avg_ppm'].iloc[0]:,.0f}",
    delta_color=(
        "normal"
        if current_year_data["avg_ppm"].iloc[0] - prev_year_data["avg_ppm"].iloc[0] >= 0
        else "inverse"
    ),
)

chart_columns = st.columns(2)

chart_columns[0].plotly_chart(
    viz_fm_monitoring.plot_global_ncf_monthly(
        df=global_ncf_monthly,
        prev_df=global_ncf_monthly_prev,
        current_year=selected_year,
        prev_year=selected_year - 1,
    )
)
chart_columns[1].plotly_chart(
    viz_fm_monitoring.plot_global_ncf_ppm_monthly(
        df=global_ncf_monthly,
        prev_df=global_ncf_monthly_prev,
        current_year=selected_year,
        prev_year=selected_year - 1,
    )
)
# 차트 컬럼 생성
chart_columns = st.columns(2)

# 부적합 수량 차트
ncf_qty_chart = viz_fm_monitoring.plot_fm_ncf_qty_by_plant(yearly_ncf_summary)
chart_columns[0].plotly_chart(ncf_qty_chart, use_container_width=True)

# PPM 차트
ppm_chart = viz_fm_monitoring.plot_fm_ppm_by_plant(
    df=yearly_ncf_summary, prev_df=yearly_ncf_summary_prev
)
chart_columns[1].plotly_chart(ppm_chart, use_container_width=True)

st.divider()
# 공장별 상세 현황 섹션
st.markdown(
    f"<h2>Plant-specific FM Non-conformance Status and Issues : <span style='color: blue;'>{selected_plant}</span></h2>",
    unsafe_allow_html=True,
)

# 컨트롤 및 차트 컬럼 생성
control_columns = st.columns(2)
chart_columns = st.columns(2)

# 월별 PPM 추이 차트
monthly_ppm_chart = viz_fm_monitoring.plot_monthly_fm_ppm_for_plant(
    df=monthly_ppm_data, plant=selected_plant, prev_df=monthly_ppm_data_prev
)
chart_columns[0].plotly_chart(monthly_ppm_chart, use_container_width=True)

# Toggle for defect type display options
show_all_defect_types = control_columns[1].toggle(
    "Show All Defect Types",
    value=False,
    help="Toggle ON to display all defect types, OFF to show top 10 and others.",
)

# 불량 유형별 부적합 현황 차트
defect_type_chart = viz_fm_monitoring.plot_fm_ncf_by_defect_type_for_plant(
    df=defect_type_data, plant=selected_plant, show_all_defects=show_all_defect_types
)
chart_columns[1].plotly_chart(defect_type_chart, use_container_width=True)
