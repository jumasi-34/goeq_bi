"""
생산혁신팀과 협업 : Global FM 현황 화면
"""

import sys
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _02_preprocessing.GMES import df_ncf
from _03_visualization import bi_402_fm_monitoring
from _05_commons import config

if config.DEV_MODE:
    import importlib

    importlib.reload(config)
    importlib.reload(df_ncf)
    importlib.reload(bi_402_fm_monitoring)

# st.set_page_config(layout="wide")


selectable_year = list(range(2025, 2020, -1))

user_input_col = st.columns(2)
selected_year = user_input_col[0].selectbox(
    "Select year :", selectable_year, key="year_select"
)
selected_plant = user_input_col[1].selectbox("Select plant :", config.plant_codes[:-1])


st.subheader(f"Global 공장 FM 부적합 현황 : {selected_year} year")

figure_col = st.columns(2)
fig = bi_402_fm_monitoring.plot_fm_ncf_qty_by_plant(selected_year)
figure_col[0].plotly_chart(fig, use_container_width=True)
fig = bi_402_fm_monitoring.plot_fm_ppm_by_plant(yyyy=selected_year)
figure_col[1].plotly_chart(fig, use_container_width=True)

st.subheader("공장별 FM 부적합 현황 및 이슈")
figure_col = st.columns(2)
fig = bi_402_fm_monitoring.plot_monthly_fm_ppm_for_plant(
    year=selected_year, plant=selected_plant
)
figure_col[0].plotly_chart(fig, use_container_width=True)
fig = bi_402_fm_monitoring.plot_fm_ncf_by_defect_type_for_plant(
    selected_year, selected_plant
)
figure_col[1].plotly_chart(fig, use_container_width=True)
