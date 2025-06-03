"""
RR Analysis Visualization
"""

import sys
from datetime import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")


from _02_preprocessing.CQMS.df_quality_issue import (
    aggregate_oeqi_by_plant_yearly,
    aggregate_oeqi_by_plant_monthly,
    aggregate_oeqi_by_global_monthly,
    load_quality_issues_for_3_years,
    aggregate_oeqi_by_global_yearly,
    aggregate_oeqi_by_goeq_yearly,
)
from _03_visualization import config_plotly, helper_plotly
from _05_commons import config

# 변수
three_color_lst = [
    config_plotly.LIGHT_GRAY_CLR,
    config_plotly.GRAY_CLR,
    config_plotly.ORANGE_CLR,
]

# 데이터 로드
selected_year = config.this_year
selected_plant = "mp"

plant_yearly_oeqi = aggregate_oeqi_by_plant_yearly(selected_year)
plant_monthly_oeqi = aggregate_oeqi_by_plant_monthly(selected_year)
global_monthly_oeqi = aggregate_oeqi_by_global_monthly(selected_year)
global_yearly_oeqi = aggregate_oeqi_by_global_yearly(selected_year)
oeqi_3years = load_quality_issues_for_3_years(selected_year)
df_mttc = oeqi_3years.copy()
df_goeq_yearly = aggregate_oeqi_by_goeq_yearly(selected_year)
df_goeq_yearly_pre = aggregate_oeqi_by_goeq_yearly(selected_year - 1)
df_mttc = df_mttc[df_mttc["YYYY"] == selected_year]
df_mttc = (
    df_mttc.groupby("YYYY")[["REG_PRD", "RTN_PRD", "CTM_PRD", "COMP_PRD", "MTTC"]]
    .mean()
    .reset_index()
)


# ================================
# 🎨 1. 공통 Chart 생성 함수
# ================================
def draw_three_years_bar(
    df,
    y_col,
    title="3-years Chart",
    yaxis_title=None,
    text_format="%{text}",
    color_list=None,
):
    if y_col == "OEQI":
        hovertemplate = """<b>Year</b>: %{x}<br><b>OEQI</b>: %{y:.2f}<extra></extra>"""
    else:
        hovertemplate = """<b>Year</b>: %{x}<br><b>Count</b>: %{y:.0f}<extra></extra>"""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["YYYY"],
            y=df[y_col],
            text=df[y_col],
            marker=dict(color=color_list if color_list else config_plotly.GRAY_CLR),
            texttemplate=text_format,
            hovertemplate=hovertemplate,
        )
    )
    fig.update_layout(
        height=300,
        title_text=title,
        yaxis_title=yaxis_title if yaxis_title else y_col,
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[0, df[y_col].max() * 1.3],
        ),
    )
    return fig


def draw_monthly_trend(df, selected_year, y_col, title, chart_type="bar"):
    years = [selected_year, selected_year - 1]
    colors = [config_plotly.ORANGE_CLR, config_plotly.GRAY_CLR]
    traces = []
    if y_col == "OEQI":
        hovertemplate = """<b>Month</b>: %{x}<br><b>OEQI</b>: %{y:.2f}<extra></extra>"""
    else:
        hovertemplate = (
            """<b>Month</b>: %{x}<br><b>Count</b>: %{y:.0f}<extra></extra>"""
        )
    for i in reversed(range(2)):
        subset = df[df["YYYY"] == years[i]]
        if chart_type == "line":
            trace = go.Scatter(
                x=subset["MM"],
                y=subset[y_col],
                text=subset[y_col] if i == 0 else None,
                texttemplate="%{text:.1f}" if i == 0 else None,
                mode="markers+lines+text" if i == 0 else "markers+lines",
                textposition="top center",
                marker=dict(color=colors[i]),
                hovertemplate=hovertemplate,
            )
        elif chart_type == "bar":
            trace = go.Bar(
                x=subset["MM"],
                y=subset[y_col],
                text=subset[y_col] if i == 0 else None,
                texttemplate="%{text:.0f}" if i == 0 else None,
                marker=dict(color=colors[i]),
                textposition="outside",
                hovertemplate=hovertemplate,
            )
        traces.append(trace)

        layout = go.Layout(
            height=300,
            title_text=title,
            yaxis=dict(showticklabels=False, showgrid=False),
            xaxis=dict(
                tickvals=list(range(1, 13)), ticktext=config_plotly.months_abbreviation
            ),
            showlegend=False,
        )
        fig = go.Figure(traces, layout)
    return fig


# ================================
# 📊 2. KPI 메인 시각화 함수 (draw_)
# ================================
def draw_three_years_oeqi(df):
    return draw_three_years_bar(
        df,
        y_col="OEQI",
        title="3-years OEQI",
        yaxis_title="OEQI",
        text_format="%{text:.1f}",
        color_list=three_color_lst,
    )


def draw_three_years_issue_count(df):
    return draw_three_years_bar(
        df,
        y_col="count",
        title="3-years Number of Quality Issue",
        yaxis_title="Issue count",
        text_format="%{text:.0f}",
        color_list=three_color_lst,
    )


def draw_monthly_oeqi_trend(df, selected_year):
    return draw_monthly_trend(
        df,
        selected_year,
        y_col="OEQI",
        title="Monthly OE Quality Index Trend",
        chart_type="line",
    )


def draw_monthly_issue_count_trend(df, selected_year):
    return draw_monthly_trend(
        df,
        selected_year,
        y_col="count",
        title="Monthly Quality issue Trend",
        chart_type="bar",
    )


def draw_pie_issue_count_by_oem(df, selected_year):
    df = df[df["YYYY"] == selected_year]
    df = (
        df.groupby("OEM", observed=False)["M_CODE"]
        .agg([("count", "count")])
        .sort_values(by="count", ascending=False)
        .reset_index()
    )
    top5 = df.nlargest(5, "count")
    etc = pd.DataFrame([["etc", df.iloc[5:]["count"].sum()]], columns=["OEM", "count"])
    df = pd.concat([top5, etc])
    color_ls = helper_plotly.get_transparent_colors(config_plotly.ORANGE_CLR, len(df))

    trace = go.Pie(
        labels=df["OEM"],
        values=df["count"],
        textinfo="label + percent",
        marker=dict(colors=color_ls),
        textfont_size=10,
        hole=0.3,
        sort=False,
        direction="clockwise",
        hovertemplate="""<b>OEM</b>: %{label}<br><b>Count</b>: %{value}<br><b>Possesion</b>: %{percent:.1%}<extra></extra>""",
    )
    layout = go.Layout(
        height=300, title_text="Quality Issue rate by OEM", showlegend=False
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_pie_issue_count_by_market(df, selected_year):
    df = df[df["YYYY"] == selected_year]
    df = (
        df.groupby("MARKET", observed=False)["M_CODE"]
        .agg([("count", "count")])
        .sort_values(by="count", ascending=False)
        .reset_index()
    )
    top5 = df.nlargest(5, "count")
    etc = pd.DataFrame(
        [["etc", df.iloc[5:]["count"].sum()]], columns=["MARKET", "count"]
    )
    df = pd.concat([top5, etc])
    color_ls = helper_plotly.get_transparent_colors(config_plotly.ORANGE_CLR, len(df))

    trace = go.Pie(
        labels=df["MARKET"],
        values=df["count"],
        textinfo="label + percent",
        marker=dict(colors=color_ls),
        textfont_size=10,
        hole=0.3,
        sort=False,
        direction="clockwise",
        hovertemplate="""<b>Market</b>: %{label}<br><b>Count</b>: %{value}<br><b>Possesion</b>: %{percent:.1%}<extra></extra>""",
    )
    layout = go.Layout(
        height=300, title_text="Quality Issue rate by Region", showlegend=False
    )
    fig = go.Figure(trace, layout)
    return fig


# ================================
# 🏭 3. Plant 단위 시각화 함수 (draw_)
# ================================
def draw_supply_quantity_by_plant(df):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["SUPP_QTY"],
            y=df["PLANT"],
            text=df["SUPP_QTY"],
            marker=dict(color=config_plotly.GRAY_CLR),
            texttemplate="%{text:.2s}",
            orientation="h",
            hovertemplate="<b>Plant:</b> %{y}<br><b>Supply:</b> %{x:,} EA<extra></extra>",
        )
    )
    fig.update_layout(
        height=350,
        title_text="OE Supplies",
        xaxis_title="Quantity of supply [ EA ]",
        xaxis=dict(showticklabels=False, showgrid=True),
        yaxis=dict(categoryorder="total ascending"),
    )
    return fig


def draw_issue_count_by_plant(df):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["count"],
            y=df["PLANT"],
            text=df["count"],
            marker=dict(color=config_plotly.GRAY_CLR),
            texttemplate="%{text:.0f}",
            orientation="h",
            hovertemplate="<b>Plant:</b> %{y}<br><b>Issue Count:</b> %{x:,} <extra></extra>",
        )
    )
    fig.update_layout(
        height=350,
        title_text="Quality Issue",
        xaxis_title="Quality Issues [ number of cases ]",
        xaxis=dict(showticklabels=False, showgrid=True),
        yaxis=dict(categoryorder="total ascending"),
    )
    return fig


def draw_oeqi_by_plant(df):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["OEQI"],
            y=df["PLANT"],
            text=df["OEQI"],
            marker=dict(color=config_plotly.GRAY_CLR),
            texttemplate="%{text:.2f}",
            orientation="h",
            hovertemplate="<b>Plant:</b> %{y}<br><b>OEQI INDEX:</b> %{x:.2f} <extra></extra>",
        )
    )
    fig.update_layout(
        height=350,
        title_text="OE Quality Index",
        xaxis_title="Quality Issues per million deliveries",
        xaxis=dict(showticklabels=False, showgrid=True),
        yaxis=dict(categoryorder="total ascending"),
    )
    return fig


# ================================
# 🧩 4. Issue 유형별 시각화 함수 (draw_)
# ================================
def draw_issue_type_distribution(df, selected_year):
    filtered_df = df[df["YYYY"] == selected_year]
    CAT_list = (
        filtered_df.groupby("CAT")
        .size()
        .rename("total")
        .sort_values(ascending=False)
        .index
    )
    # group_qi_issueCAT
    filtered_df = (
        filtered_df.groupby(["CAT", "SUB_CAT"]).size().rename("count").reset_index()
    )
    # ETC항목에 CAT 표시
    filtered_df.loc[filtered_df["SUB_CAT"] == "Etc", "SUB_CAT"] = (
        filtered_df["SUB_CAT"] + "( " + filtered_df["CAT"] + " )"
    )
    # CAT 컬럼 카테고리화
    filtered_df["CAT"] = pd.Categorical(
        filtered_df["CAT"], categories=CAT_list, ordered=True
    )
    # 차트정렬을 위한 전처리
    filtered_df = filtered_df.sort_values(["CAT", "count"], ascending=[False, False])

    color_list = dict(zip(CAT_list, config_plotly.multi_color_lst))

    fig = go.Figure()
    for cat, subset in filtered_df.groupby("CAT", observed=False):
        fig.add_trace(
            go.Bar(
                x=subset["count"],
                y=subset["SUB_CAT"],
                text=subset["count"],
                textposition="outside",
                texttemplate="%{text:.0f}",
                name=cat,
                orientation="h",
                marker=dict(color=color_list[cat]),
                hovertemplate="<b>Issue Type:</b> %{y}<br><b>Issue Count:</b> %{x:,} EA<extra></extra>",
            )
        )
    fig.update_layout(
        height=600,
        margin=dict(pad=0, b=80, l=80, r=80, t=70),
        title_text="Top Global Quality Issue Types",
        xaxis_title="Quality issues[number of cases]",
        yaxis_title="Quality issue types",
        xaxis=dict(showgrid=True, domain=[0.2, 1]),
        yaxis=dict(autorange="reversed"),
        legend=dict(x=0.95, y=0, xanchor="right", yanchor="bottom"),
    )
    return fig


def draw_pie_for_top_issue_types(df, selected_year):
    filtered_df = df[df["YYYY"] == selected_year]
    if filtered_df.empty:
        return go.Figure(), go.Figure(), go.Figure(), go.Figure()

    filtered_df["PLANT"] = filtered_df["PLANT"].astype("str")

    # CAT 순서 생성
    CAT_list = (
        filtered_df.groupby("CAT")
        .size()
        .rename("total")
        .sort_values(ascending=False)
        .index.tolist()
    )

    # 그룹화 후 count 집계
    filtered_df = (
        filtered_df.groupby(["CAT", "SUB_CAT", "PLANT"])
        .size()
        .rename("count")
        .reset_index()
    )

    # Etc 처리
    mask = filtered_df["SUB_CAT"] == "Etc"
    filtered_df.loc[mask, "SUB_CAT"] = (
        filtered_df.loc[mask, "SUB_CAT"] + "( " + filtered_df.loc[mask, "CAT"] + " )"
    )

    # 카테고리 순서 적용
    filtered_df["CAT"] = filtered_df["CAT"].astype(str)

    # 정렬
    grouped = (
        filtered_df.groupby(["CAT", "SUB_CAT"])["count"]
        .sum()
        .reset_index()
        .sort_values("count", ascending=False)
    )

    # 상위 4개 추출
    worst_issue_sub_cat = (
        grouped[~grouped["SUB_CAT"].str.contains("Etc")]["SUB_CAT"]
        .drop_duplicates()
        .head(4)
        .tolist()
    )

    # 피그 생성
    fig_lst = [go.Figure() for _ in range(4)]

    for i, fig in enumerate(fig_lst):
        if i < len(worst_issue_sub_cat):
            worst = worst_issue_sub_cat[i]
            condition = filtered_df["SUB_CAT"] == worst
            group_worst_issue = (
                filtered_df[condition]
                .groupby("PLANT")["count"]
                .sum()
                .reset_index()
                .sort_values(by="count", ascending=False)
            )
            group_worst_issue = group_worst_issue.dropna(subset="count")
            if not group_worst_issue.empty:
                color_lst = helper_plotly.get_transparent_colors(
                    base_color=config_plotly.ORANGE_CLR,
                    num_colors=len(group_worst_issue),
                )
                fig.add_trace(
                    go.Pie(
                        labels=group_worst_issue["PLANT"],
                        values=group_worst_issue["count"],
                        marker=dict(colors=color_lst),
                        textinfo="label+percent",
                        hovertemplate="<b>Plant:</b> %{label}<br><b>Possesion:</b> %{percent:.1%}<br><b>Issue Count:</b> %{value:,} EA<extra></extra>",
                    )
                )
                fig.update_layout(
                    height=300, margin=dict(t=70), title_text=worst, showlegend=False
                )
        else:
            fig.update_layout(title_text="No Data", height=300)

    return tuple(fig_lst)


# ================================
# 🧩 6. Global MTTC (draw_)
# ================================
def draw_three_years_mttc(df):
    df = df.groupby("YYYY")["MTTC"].mean().reset_index()
    trace = go.Bar(
        x=df["YYYY"],
        y=df["MTTC"],
        text=df["MTTC"],
        texttemplate="%{text:.1f}",
        marker=dict(color=three_color_lst),
        hovertemplate="""<b>Year</b>: %{x}<br><b>MTTC</b>: %{y:.2f} Days<extra></extra>""",
    )
    layout = go.Layout(
        height=350,
        title_text="3-years MTTC",
        yaxis_title="MTTC",
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[0, max(df["MTTC"]) * 1.3],
        ),
    )
    fig = go.Figure(trace, layout)
    return fig


def generate_indicator(target, reference, range_max):
    trace = go.Indicator(
        mode="number+gauge+delta",
        value=target,
        number=dict(valueformat=".1f"),
        domain={"x": [0.1, 1], "y": [0.2, 0.8]},
        delta=dict(
            reference=reference,
            increasing=dict(symbol="▲", color=config_plotly.NEGATIVE_CLR),
            decreasing=dict(symbol="▼", color=config_plotly.POSITIVE_CLR),
            valueformat=".1f",
        ),
        gauge=dict(
            shape="bullet",
            axis=dict(range=[None, max([target, reference, range_max]) * 1.2]),
            bar=dict(color=config_plotly.ORANGE_CLR, thickness=0.5),
            threshold=dict(
                line=dict(color="red", width=2), thickness=1, value=reference
            ),
            steps=[dict(range=[0, reference], color=config_plotly.GRAY_CLR)],
        ),
    )
    return trace


def draw_mttc_global_indicator(df):
    trace = generate_indicator(target=df["MTTC"].max(), reference=10, range_max=10)
    layout = go.Layout(height=350, margin=dict(t=130, b=130), title_text="MTTC")
    fig = go.Figure(trace, layout)

    return fig


def draw_mttc_by_plant(df):
    fig = go.Figure()
    gruopby_df = (
        df.groupby("PLANT", observed=False)["MTTC"]
        .mean()
        .reset_index()
        .sort_values(by="MTTC", ascending=False)
    )
    gruopby_df = gruopby_df[gruopby_df["MTTC"] > 0]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=gruopby_df["MTTC"],
            y=gruopby_df["PLANT"],
            text=gruopby_df["MTTC"],
            texttemplate="%{text:.1f}",
            orientation="h",
            marker=dict(color=config_plotly.GRAY_CLR),
            hovertemplate="""<b>PLANT</b>: %{y}<br><b>MTTC</b>: %{x:.2f} Days<extra></extra>""",
        )
    )
    fig.update_layout(
        height=350,
        title_text="by PLANT",
        xaxis_title="MTTC(days)",
        xaxis=dict(showticklabels=False),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def draw_mttc_reg_global_indicator(df):
    trace = generate_indicator(target=df["REG_PRD"].max(), reference=2, range_max=2)
    layout = go.Layout(
        height=120, margin=dict(t=30, b=30, l=10, r=10), title_text="Registration"
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_mttc_rtn_global_indicator(df):
    trace = generate_indicator(target=df["RTN_PRD"].max(), reference=7, range_max=7)
    layout = go.Layout(
        height=120, margin=dict(t=30, b=30, l=10, r=10), title_text="Return"
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_mttc_countermeasure_global_indicator(df):
    trace = generate_indicator(target=df["CTM_PRD"].max(), reference=5, range_max=5)
    layout = go.Layout(
        height=120, margin=dict(t=30, b=30, l=10, r=10), title_text="Countermeasure"
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_mttc_8d_global_indicator(df):
    trace = generate_indicator(target=df["COMP_PRD"].max(), reference=2, range_max=2)
    layout = go.Layout(
        height=120, margin=dict(t=30, b=30, l=10, r=10), title_text="8D Report"
    )
    fig = go.Figure(trace, layout)
    return fig


# ================================
# 🧩 7. Plant View (draw_)
# ================================


def draw_plant_view_oeqi_highlight(df, selected_plant):
    df = df[df["PLANT"] != "OT"]
    df = df.sort_values(by="OEQI", ascending=False)

    color_list = [
        config_plotly.ORANGE_CLR if plant == selected_plant else config_plotly.GRAY_CLR
        for plant in df["PLANT"]
    ]
    trace = go.Bar(
        x=df["PLANT"],
        y=df["OEQI"],
        text=df["OEQI"],
        texttemplate="%{text:.1f}",
        marker=dict(color=color_list),
    )
    layout = go.Layout(
        height=300,
        title_text="OE Quality Index",
        xaxis_title="PLANT",
        yaxis_title="OEQI",
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[0, max(df["OEQI"]) * 1.2],
        ),
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_plant_view_issue_count_highlight(df, selected_plant):
    df = df[df["PLANT"] != "OT"]
    df = df.sort_values(by="count", ascending=False)
    color_list = [
        config_plotly.ORANGE_CLR if plant == selected_plant else config_plotly.GRAY_CLR
        for plant in df["PLANT"]
    ]
    trace = go.Bar(
        x=df["PLANT"],
        y=df["count"],
        text=df["count"],
        marker=dict(color=color_list),
        texttemplate="%{text:.0f}",
    )
    layout = go.Layout(
        height=300,
        title_text="OE Quality Index",
        xaxis_title="PLANT",
        yaxis_title="Issue Count",
        xaxis=dict(categoryorder="total descending"),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[0, max(df["count"]) * 1.2],
        ),
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_plant_view_oeqi_index_trend(df, selected_year, selected_plant):
    bool_yyyy = df["YYYY"] == int(selected_year)
    bool_plant = df["PLANT"] == selected_plant
    df = df[bool_yyyy & bool_plant]
    trace = go.Scatter(
        x=df["MM"],
        y=df["OEQI"],
        text=df["OEQI"],
        texttemplate="%{text:.1f}",
        textposition="top center",
        mode="lines + markers + text",
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        height=300,
        title_text="OEQI Monthly Trend",
        xaxis=dict(
            ticktext=config_plotly.months_abbreviation, tickvals=list(range(1, 13))
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=True,
            range=[0, max(df["OEQI"]) * 1.2],
        ),
    )

    fig = go.Figure(trace, layout)
    return fig


def draw_plant_view_issue_count_index_trend(df, selected_year, selected_plant):
    bool_yyyy = df["YYYY"] == int(selected_year)
    bool_plant = df["PLANT"] == selected_plant
    df = df[bool_yyyy & bool_plant]
    trace = go.Bar(
        x=df["MM"],
        y=df["count"],
        text=df["count"],
        texttemplate="%{text:.0f}",
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        height=300,
        title_text="OEQI Monthly Trend",
        xaxis=dict(
            ticktext=config_plotly.months_abbreviation, tickvals=list(range(1, 13))
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=True,
            range=[0, max(df["count"] * 1.2)],
        ),
    )

    fig = go.Figure(trace, layout)
    return fig


# ================================
# 🧩 8. GOEQ View (draw_)
# ================================


def draw_goeq_view_issue_count_monthly_trend(df):
    traces = []
    for i, group in enumerate(config.oeqg_codes):
        subset = df[df["OEQ GROUP"] == group]

        trace = go.Bar(
            x=subset["MM"],
            y=subset["count"],
            text=subset["count"],
            name=group,
            texttemplate="%{text:.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.multi_color_lst[i]),
        )
        traces.append(trace)

    layout = go.Layout(
        title_text="Monthly Quality Issues by Local OE Quality Team",
        xaxis_title="Month",
        yaxis_title="Number of Quality Issue",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=config_plotly.months_abbreviation,
            range=[0.5, 12.5],
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            domain=[0, 0.8],
            range=[0, max(df["count"]) * 1.2],
        ),
        legend=dict(orientation="h", yanchor="top", y=1.0, xanchor="right", x=1.0),
    )
    fig = go.Figure(traces, layout)
    return fig


def draw_goeq_view_oeqi_monthly_trend(df):
    traces = []
    for i, group in enumerate(config.oeqg_codes):
        subset = df[df["OEQ GROUP"] == group]

        trace = go.Scatter(
            x=subset["MM"],
            y=subset["OEQI"],
            text=subset["OEQI"],
            textposition="top center",
            texttemplate="%{text:.1f}",
            mode="markers + lines + text",
            name=group,
            marker=dict(color=config_plotly.multi_color_lst[i]),
        )
        traces.append(trace)

    layout = go.Layout(
        title_text="Monthly OEQI by Local OE Quality Team",
        xaxis_title="Month",
        yaxis_title="Number of Quality Issue",
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            domain=[0, 0.8],
            range=[0, max(df["OEQI"]) * 1.2],
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=config_plotly.months_abbreviation,
            range=[0.5, 12.5],
        ),
        legend=dict(orientation="h", yanchor="top", y=1.0, xanchor="right", x=1.0),
    )
    fig = go.Figure(traces, layout)
    return fig


def draw_goeq_view_mttc_summary(df):
    mttc_cols = ["MTTC", "REG_PRD", "RTN_PRD", "CTM_PRD", "COMP_PRD"]
    titles = ["a", "b", "c", "d", "e"]
    df["OEQ GROUP"] = pd.Categorical(
        values=df["OEQ GROUP"], ordered=True, categories=config.oeqg_codes
    )
    df = df.sort_values(by="OEQ GROUP")
    figs = []
    for group in config.oeqg_codes:
        for item, ref, title in zip(mttc_cols, [10, 2, 7, 5, 2], titles):
            trace = generate_indicator(
                target=df.loc[df["OEQ GROUP"] == group, item],
                reference=ref,
                range_max=ref,
            )
            layout = go.Layout(height=350, margin=dict(t=130, b=130), title_text=group)
            fig = go.Figure(trace, layout)
            figs.append(fig)
    return figs


def draw_goeq_view_mttc_compare(df_1, df_2):
    trace_1 = go.Bar(
        y=df_1["MTTC"],
        x=df_1["OEQ GROUP"],
        text=df_1["MTTC"],
        texttemplate="%{text:.1f}",
        name=selected_year - 1,
        marker=dict(color=config_plotly.GRAY_CLR),
        width=0.35,  # 바 폭 조정
    )
    trace_2 = go.Bar(
        y=df_2["MTTC"],
        x=df_2["OEQ GROUP"],
        text=df_2["MTTC"],
        texttemplate="%{text:.1f}",
        name=selected_year,
        marker=dict(color=config_plotly.ORANGE_CLR),
        width=0.35,  # 바 폭 조정
    )
    layout = go.Layout(
        height=300,
        title=dict(text="MTTC"),
        yaxis=dict(
            range=[0, None],
            showgrid=False,
            showticklabels=False,
            zerolinewidth=2,
            zerolinecolor=config_plotly.GRAY_CLR,
        ),
        xaxis=dict(showgrid=False),
        margin=dict(l=70, r=70, t=70, b=70),
        bargap=0.2,  # 바 사이 간격 조정
        bargroupgap=0.1,  # 그룹 간 간격 조정
    )
    fig = go.Figure(data=[trace_1, trace_2], layout=layout)
    fig = fig.add_hline(y=10, line=dict(color=config_plotly.NEGATIVE_CLR, dash="dash"))
    return fig


# ================================
# 🧪 테스트용 함수 (test_)
# ================================


def main():

    figs = [
        # Global page
        draw_three_years_oeqi(plant_yearly_oeqi),
        draw_three_years_issue_count(plant_yearly_oeqi),
        draw_monthly_oeqi_trend(global_monthly_oeqi, selected_year),
        draw_monthly_issue_count_trend(global_monthly_oeqi, selected_year),
        draw_pie_issue_count_by_oem(oeqi_3years, selected_year),
        draw_pie_issue_count_by_market(oeqi_3years, selected_year),
        draw_issue_type_distribution(oeqi_3years, selected_year),
        draw_pie_for_top_issue_types(oeqi_3years, selected_year),
        draw_three_years_mttc(oeqi_3years),
        draw_mttc_global_indicator(df_mttc),
        draw_mttc_by_plant(oeqi_3years),
        draw_mttc_reg_global_indicator(df_mttc),
        draw_mttc_rtn_global_indicator(df_mttc),
        draw_mttc_countermeasure_global_indicator(df_mttc),
        draw_mttc_8d_global_indicator(df_mttc),
        # Plant Page
        draw_plant_view_oeqi_highlight(plant_yearly_oeqi, selected_plant),
        draw_plant_view_issue_count_highlight(plant_yearly_oeqi, selected_plant),
        draw_plant_view_oeqi_index_trend(
            plant_monthly_oeqi, selected_year, selected_plant
        ),
        draw_plant_view_issue_count_index_trend(
            plant_monthly_oeqi, selected_year, selected_plant
        ),
    ]
    return figs


if __name__ == "__main__":
    figs = main()
    for fig in figs:
        fig.show()
