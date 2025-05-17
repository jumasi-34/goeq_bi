"""
Global OE Quality KPI 대시보드
"""

import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _05_commons import config, helper
from _02_preprocessing.CQMS import df_quality_issue as pd_df
from _02_preprocessing.HOPE import df_oeapp
from _03_visualization import bi_301_OE_Quality_Issue_Dashboard as viz
from _03_visualization import config_plotly

# 개발 모드 시 리로드
if config.DEV_MODE:
    import importlib

    importlib.reload(config)
    importlib.reload(pd_df)
    importlib.reload(viz)

# st.set_page_config(layout="wide")

this_year = config.this_year
year_selection_option = range(2023, this_year + 1)

selected_year = st.radio(
    label="Choose year?",
    key=max(year_selection_option),
    options=year_selection_option,
    horizontal=True,
    index=len(year_selection_option) - 1,
    label_visibility="collapsed",
)

three_years = range(selected_year - 2, selected_year + 1)

df_raw_3_years = pd_df.load_quality_issues_for_3_years(selected_year)
df_plant_monthly = pd_df.aggregate_oeqi_by_plant_monthly(selected_year)
df_plant_yearly = pd_df.aggregate_oeqi_by_plant_yearly(selected_year)
df_global_monthly = pd_df.aggregate_oeqi_by_global_monthly(selected_year)
df_global_yearly = pd_df.aggregate_oeqi_by_global_yearly(selected_year)
df_goeq_monthly = pd_df.aggregate_oeqi_by_goeq_monthly(selected_year)
df_goeq_yearly = pd_df.aggregate_oeqi_by_goeq_yearly(selected_year)
df_oeapp = df_oeapp.load_oeapp_df()


tabs = st.tabs(["GLOBAL", "PLANT", "OEQG", "RAWDATA"])

with tabs[0]:  # GLOBAL
    st.subheader(
        "Global OE Quality Index",
        help=(
            "**Note:** \\\nOEQI and OE supply quantity data are available\\\n"
            "**starting from the year 2023**.\\\n"
            "Please keep this in mind when analyzing historical trends."
        ),
    )
    cols = st.columns([25, 45, 30])

    cols[0].plotly_chart(
        viz.draw_three_years_oeqi(df_global_yearly), use_container_width=True
    )
    # cols[1].dataframe(df_global_monthly)
    cols[1].plotly_chart(
        viz.draw_monthly_oeqi_trend(df_global_monthly, selected_year),
        use_container_width=True,
    )
    cols[2].plotly_chart(viz.draw_pie_issue_count_by_oem(df_raw_3_years, selected_year))

    cols = st.columns([25, 45, 30])
    cols[0].plotly_chart(
        viz.draw_three_years_issue_count(df_global_yearly), use_container_width=True
    )
    cols[1].plotly_chart(
        viz.draw_monthly_issue_count_trend(df_global_monthly, selected_year),
        use_container_width=True,
    )
    cols[2].plotly_chart(
        viz.draw_pie_issue_count_by_market(df_raw_3_years, selected_year)
    )

    st.subheader("Quality metrics by Plant")
    cols = st.columns(3)
    cols[0].plotly_chart(viz.draw_supply_quantity_by_plant(df_plant_yearly))
    cols[1].plotly_chart(viz.draw_issue_count_by_plant(df_plant_yearly))
    cols[2].plotly_chart(viz.draw_oeqi_by_plant(df_plant_yearly))

    cols = st.columns(3)
    st.subheader("Categorize quality issues by type")
    cols = st.columns([5, 2, 2])
    cols[0].plotly_chart(
        viz.draw_issue_type_distribution(df_raw_3_years, selected_year)
    )
    pies = viz.draw_pie_for_top_issue_types(df_raw_3_years, selected_year)
    cols[1].plotly_chart(pies[0], use_container_width=True)
    cols[1].plotly_chart(pies[2], use_container_width=True)
    cols[2].plotly_chart(pies[1], use_container_width=True)
    cols[2].plotly_chart(pies[3], use_container_width=True)

    # st.subheader("EV vs. ICE Quality Index Comparison")
    help = """
**MTTC (Mean Time To Closure)** represents the average number of business days it takes to close a quality issue.

This metric is calculated by summing up several work phases, including:
- **Occurrence to Registration**
- **Registration to Return** (only if the issue is returned)
- **Return or Registration to Countermeasure**
- **Countermeasure to 8D Completion**

The system uses **business days** (excluding weekends) based on actual dates provided in the report.

If certain dates (e.g., completion) are missing, the calculation assumes **today's date** as the endpoint.  
This ensures ongoing issues are also reflected in the MTTC calculation.

> A lower MTTC indicates faster resolution and better responsiveness to quality issues.
        """
    st.subheader("MTTC Index", help=help)
    cols = st.columns([1, 1.5, 1.2])
    df_mttc = df_global_yearly[df_global_yearly["YYYY"] == selected_year]
    df_mttc = (
        df_mttc.groupby("YYYY")[["REG_PRD", "RTN_PRD", "CTM_PRD", "COMP_PRD", "MTTC"]]
        .mean()
        .reset_index()
    )
    cols[0].plotly_chart(
        viz.draw_three_years_mttc(df_global_yearly), use_container_width=True
    )
    cols[1].plotly_chart(
        viz.draw_mttc_global_indicator(df_mttc), use_container_width=True
    )
    cols[2].plotly_chart(
        viz.draw_mttc_by_plant(df_plant_yearly), use_container_width=True
    )
    cols = st.columns(4)
    cols[0].plotly_chart(
        viz.draw_mttc_reg_global_indicator(df_mttc), use_container_width=True
    )
    cols[1].plotly_chart(
        viz.draw_mttc_rtn_global_indicator(df_mttc), use_container_width=True
    )
    cols[2].plotly_chart(
        viz.draw_mttc_countermeasure_global_indicator(df_mttc), use_container_width=True
    )
    cols[3].plotly_chart(
        viz.draw_mttc_8d_global_indicator(df_mttc), use_container_width=True
    )

with tabs[1]:  # PLANT
    selected_plt = st.selectbox("Plant Select", config.plant_codes[:-1], index=0)
    st.markdown("---")
    cols = st.columns(4, gap="medium")
    with cols[0]:  # col_project
        st.subheader("Projects")
        sub_cols = st.columns(2)
        sub_cols[0].metric(
            "Mass Production",
            value=df_oeapp[
                (df_oeapp["plant"] == selected_plt)
                & (df_oeapp["Status"] == "Supplying")
            ].shape[0],
        )
        sub_cols[1].metric(
            "Development",
            value=df_oeapp[
                (df_oeapp["plant"] == selected_plt)
                & (df_oeapp["Status"] == "Developing")
            ].shape[0],
        )
    with cols[1]:  # col_supplies
        st.subheader("Supplies")
        val = df_plant_yearly.loc[
            df_plant_yearly["PLANT"] == selected_plt, "SUPP_QTY"
        ].values[0]
        val = helper.format_number(num=val)
        st.metric(label="OE Supplies", value=f"{val}")
    with cols[2]:  # col_quality_issue
        st.subheader("Quality Issue")
        sub_cols = st.columns(2)

        bool_on_going = df_raw_3_years["STATUS"] == "On-going"
        bool_on_complete = df_raw_3_years["STATUS"] == "Complete"
        bool_on_selected_plt = df_raw_3_years["PLANT"] == selected_plt
        bool_on_selected_year = df_raw_3_years["YYYY"] == selected_year

        comp_cnt = df_raw_3_years[
            bool_on_complete & bool_on_selected_plt & bool_on_selected_year
        ].shape[0]
        on_going_cnt = df_raw_3_years[
            bool_on_complete & bool_on_selected_plt & bool_on_selected_year
        ].shape[0]
        sub_cols[0].metric(label="Complete", value=comp_cnt)
        sub_cols[1].metric(label="On-going", value=on_going_cnt)
    with cols[3]:  # col_index
        st.subheader("Index")
        sub_cols = st.columns(2)
        val = df_plant_yearly.loc[
            df_plant_yearly["PLANT"] == selected_plt, "OEQI"
        ].values[0]
        sub_cols[0].metric(label="OEQI", value=f"{val:.2f}")
        val = df_plant_yearly.loc[
            df_plant_yearly["PLANT"] == selected_plt, "MTTC"
        ].values[0]
        val = 0 if pd.isna(val) else val
        sub_cols[1].metric(label="MTTC", value=f"{val:.1f} days")
    st.markdown("---")
    cols = st.columns(2)
    with cols[0]:  # comparision
        st.plotly_chart(
            viz.draw_plant_view_oeqi_highlight(df_plant_yearly, selected_plt),
            use_container_width=True,
        )
        st.plotly_chart(
            viz.draw_plant_view_issue_count_highlight(df_plant_yearly, selected_plt),
            use_container_width=True,
        )
    with cols[1]:  # trend
        st.plotly_chart(
            viz.draw_plant_view_oeqi_index_trend(
                df_plant_monthly, selected_year, selected_plt
            )
        )
        st.plotly_chart(
            viz.draw_plant_view_issue_count_index_trend(
                df_plant_monthly, selected_year, selected_plt
            )
        )

    st.subheader("Quality Issue List")
    bool_yyyy = df_raw_3_years["YYYY"] == int(selected_year)
    bool_plant = df_raw_3_years["PLANT"] == selected_plt
    df_raw_3_years = df_raw_3_years[bool_yyyy & bool_plant]
    st.dataframe(df_raw_3_years, use_container_width=True)

with tabs[2]:  # OEQG
    cols = st.columns(2)
    cols[0].plotly_chart(viz.draw_goeq_view_issue_count_monthly_trend(df_goeq_monthly))
    cols[1].plotly_chart(viz.draw_goeq_view_oeqi_monthly_trend(df_goeq_monthly))

    def get_mttc_bar_trace(y_col):
        trace_local = go.Bar(
            x=df_goeq_yearly["OEQ GROUP"],
            y=df_goeq_yearly[y_col],
            text=df_goeq_yearly[y_col],
            texttemplate="%{text:.1f}",
            marker=dict(color=config_plotly.multi_color_lst[:4]),
        )
        return trace_local

    def get_mttc_layout(height):
        layout_local = go.Layout(
            height=height, yaxis=dict(range=[0, None], showticklabels=False)
        )
        return layout_local

    def draw_target_line(fig_local, target):
        fig_local.add_hline(
            y=target, line=dict(color=config_plotly.NEGATIVE_CLR, dash="dash")
        )

    cols = st.columns([4, 2, 2], gap="large", vertical_alignment="center")

    cols[0].subheader("MTTC")
    trace = get_mttc_bar_trace("MTTC")
    layout = get_mttc_layout(height=500)
    fig = go.Figure(data=trace, layout=layout)
    draw_target_line(fig, target=10)
    cols[0].plotly_chart(fig)

    cols[1].subheader("REG_PRD")
    trace = get_mttc_bar_trace("REG_PRD")
    layout = get_mttc_layout(height=300)
    fig = go.Figure(data=trace, layout=layout)
    draw_target_line(fig, target=2)
    cols[1].plotly_chart(fig)

    cols[1].subheader("CTM_PRD")
    trace = get_mttc_bar_trace("CTM_PRD")
    layout = get_mttc_layout(height=300)
    fig = go.Figure(data=trace, layout=layout)
    draw_target_line(fig, target=5)
    cols[1].plotly_chart(fig)

    cols[2].subheader("RTN_PRD")
    trace = get_mttc_bar_trace("RTN_PRD")
    layout = get_mttc_layout(height=300)
    fig = go.Figure(data=trace, layout=layout)
    draw_target_line(fig, target=7)
    cols[2].plotly_chart(fig)

    cols[2].subheader("COMP_PRD")
    trace = get_mttc_bar_trace("COMP_PRD")
    layout = get_mttc_layout(height=300)
    fig = go.Figure(data=trace, layout=layout)
    draw_target_line(fig, target=2)
    cols[2].plotly_chart(fig)

with tabs[3]:  # RAWDATA
    st.subheader("Raw Data[Qaulity Issue]")
    st.write("If a column doesn't make sense, hover over it to see the details.")
