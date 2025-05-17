"""
docstring
"""

import sys
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _05_commons import config
from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import bi_202_ongoing_status_tracker

if config.DEV_MODE:
    import importlib

    importlib.reload(df_quality_issue)
    importlib.reload(df_4m_change)
    importlib.reload(df_customer_audit)
    importlib.reload(bi_202_ongoing_status_tracker)

# st.set_page_config(layout="wide")

plant_codes = config.plant_codes[:-1]
selected_plant = st.multiselect(
    "Select Plant", options=plant_codes, default=plant_codes
)

# QI
filtered_df = df_quality_issue.load_ongoing_quality_issues(selected_plant)

cnt = len(filtered_df)

st.subheader(f"Quality Issue (On-going : {cnt})")
cols = st.columns([1, 2, 4])

fig = bi_202_ongoing_status_tracker.ongoing_qi_pie_by_plant(selected_plant)
cols[0].plotly_chart(fig, use_container_width=True)
fig = bi_202_ongoing_status_tracker.ongoing_qi_bar_by_month(selected_plant)
cols[1].plotly_chart(fig, use_container_width=True)

remain_col = [
    "PLANT",
    "OEM",
    "VEH",
    "PJT",
    "REG_DATE",
    "STATUS",
    "LOCATION",
    "MARKET",
    "M_CODE",
    "PNL_NM",
    "TYPE",
    "CAT",
    "SUB_CAT",
    "URL",
]

column_config = dict(
    DOC_NO=st.column_config.TextColumn("Document No."),
    REG_DATE=st.column_config.DateColumn("Reg. Date", format="YYYY-MM-DD"),
    URL=st.column_config.LinkColumn("LINK", display_text="Click"),
)


cols[2].dataframe(
    filtered_df[remain_col],
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
)

st.divider()

# 4M
(
    filtered_df_plant_na,
    filtered_df,
    groupby_filtered_df_by_plant,
    groupby_filtered_df_by_month,
) = df_4m_change.filtered_4m_ongoing_by_yearly(selected_plant)

cnt = len(filtered_df)
st.subheader(f"4M Change (On-going : {cnt})")
cols = st.columns([1, 2, 4])

fig = bi_202_ongoing_status_tracker.ongoing_4m_pie_by_plant(selected_plant)
cols[0].plotly_chart(fig, use_container_width=True)
fig = bi_202_ongoing_status_tracker.ongoing_4m_bar_by_month(selected_plant)
cols[1].plotly_chart(fig, use_container_width=True)

remain_col = [
    "DOC_NO",
    "PLANT",
    "SUBJECT",
    "STATUS",
    "REG_DATE",
    "URL",
    "Elapsed_period",
    "M_CODE",
]

column_config = dict(
    DOC_NO=st.column_config.TextColumn("Doucment No."),
    REG_DATE=st.column_config.DateColumn("Reg. Date", format="YYYY-MM-DD"),
    URL=st.column_config.LinkColumn("LINK", display_text="Click"),
    M_CODE_LIST=st.column_config.ListColumn("M Code List"),
)

cols[2].dataframe(
    filtered_df[remain_col],
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
)

n_of_non_registration = len(filtered_df_plant_na)

remain_col = [
    "DOC_NO",
    "PURPOSE",
    "SUBJECT",
    "STATUS",
    "REQUESTER",
    "REG_DATE",
    "URL",
    "M_CODE",
    "Elapsed_period",
]
column_config = dict(
    URL=st.column_config.LinkColumn("Link", display_text="Click"),
    REG_DATE=st.column_config.DateColumn("Registration Date", format="YYYY-MM-DD"),
)
with st.expander(
    label=f"※ 4M information for M-Code not registered in OE Application( On-going : {n_of_non_registration})",
):
    st.dataframe(
        filtered_df_plant_na[remain_col],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# AUDIT

(
    filtered_df,
    groupby_filtered_df_by_plant,
    groupby_filtered_df_by_month,
) = df_customer_audit.get_audit_ongoing_df(selected_plant)

cnt = len(filtered_df)
st.subheader(f"OE Audit (On-going : {cnt})")
cols = st.columns([1, 2, 4])

fig = bi_202_ongoing_status_tracker.ongoing_audit_pie_by_plant(selected_plant)
cols[0].plotly_chart(fig, use_container_width=True)
fig = bi_202_ongoing_status_tracker.ongoing_audit_bar_by_month(selected_plant)
cols[1].plotly_chart(fig, use_container_width=True)

remain_col = [
    "TYPE",
    "START_DT",
    "END_DT",
    "SUBJECT",
    "M_CODE",
    "PLANT",
    "CAR_MAKER",
    "URL",
    "ELAPSED_PERIOD",
]


filtered_df = filtered_df[remain_col]
column_config = {
    "START_DT": st.column_config.DateColumn("Strat", format="YYYY-MM-DD"),
    "END_DT": st.column_config.DateColumn("End", format="YYYY-MM-DD"),
    "URL": st.column_config.LinkColumn("LINK", display_text="Click"),
}

cols[2].dataframe(
    filtered_df, use_container_width=True, column_config=column_config, hide_index=True
)
