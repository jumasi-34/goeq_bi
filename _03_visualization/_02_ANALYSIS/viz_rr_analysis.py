"""
RR Analysis Visualization
"""

import sys
from datetime import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
import numpy as np


from _05_commons import config
sys.path.append(config.PROJECT_ROOT)

from _02_preprocessing.GMES.df_rr import (
    get_processed_agg_rr_data,
    get_processed_raw_rr_data,
)
from _03_visualization import config_plotly
from _05_commons import config

# 범주-색상 매핑
cat_color_map = {
    "<50%": "red",
    "<70%": "orange",
    "<80%": "yellow",
    "<90%": "green",
    "<95%": "blue",
    "Above 95%": "purple",
}


def get_spec_limits(df):
    # if df.empty:
    # raise ValueError("Empty DataFrame passed to get_spec_limits")

    first_row = df.iloc[0]  # 위치 기반 접근으로 안전
    usl = float(first_row["SPEC_MAX"])
    lsl = float(first_row["SPEC_MIN"])
    ucl = lcl = None

    if lsl == 0.0:
        rr_index = float(first_row["RR_INDEX"])
        ucl = min(usl, rr_index + 0.3)
        lcl = rr_index - 0.3

    return usl, lsl, ucl, lcl


def hbar_expected_pass_rate_by_plant(df):

    df = (
        df.pivot_table(index="PLANT", values="EPass", aggfunc="mean")
        .reset_index()
        .sort_values(by="EPass")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["EPass"],
            y=df["PLANT"],
            orientation="h",
            text=df["EPass"].apply(lambda x: f"{x:.1%}"),
            textposition="auto",
            marker=dict(color=config_plotly.ORANGE_CLR),
        )
    )

    fig.update_layout(
        title_text="Expected Pass Rate Status by Plant",
        xaxis=dict(showticklabels=True, title="EPass Rate"),
        yaxis=dict(title="Plant"),
        margin=dict(t=60, l=80, r=30, b=40),
    )

    return fig


def histogram_expected_pass_rate_by_plant(df):
    df = df.dropna(subset=["EPass"])
    categories = (
        df.pivot_table(index="PLANT", values="EPass", aggfunc="mean")
        .reset_index()
        .sort_values(by="EPass")
    )
    categories = list(reversed(categories["PLANT"].unique()))

    fig = make_subplots(
        rows=2,
        cols=4,
        subplot_titles=categories,
        shared_xaxes=True,
    )
    for idx, cat in enumerate(categories):
        row = (idx // 4) + 1  # 2행 4열이므로 행 계산
        col = (idx % 4) + 1  # 열 계산
        filtered_df = df[df["PLANT"] == cat]
        fig.add_trace(
            go.Histogram(
                x=filtered_df["EPass"],
                name=f"PLANT : {cat}",
                texttemplate="%{y}",
                textangle=0,
                xbins=dict(start=0, end=1, size=0.1),
                marker=dict(color=config_plotly.GRAY_CLR),
            ),
            row=row,
            col=col,
        )
    fig.update_layout(
        title_text="Histogram of Expected Pass Rate Levels by Specification Across Plants",
        showlegend=False,
        margin=dict(t=60, l=80, r=30, b=40),
    )
    fig.update_xaxes(range=[0, 1], dtick=0.2)

    return fig


def scatter_expected_pass_rate_by_project(df):
    fig = go.Figure()
    for category, color in cat_color_map.items():
        subset = df[df["EPass_cat"] == category]
        customdata = list(
            zip(
                subset["PLANT"],
                subset["M_CODE"],
                subset["OEM"],
                subset["VEH"],
                subset["limit"],
                subset["SPEC_MIN"],
                subset["SPEC_MAX"],
                subset["e_min"],
                subset["e_max"],
                subset["count"],
                subset["avg"],
                subset["std"],
                subset["CP"],
                subset["Offset"],
                subset["EPass"],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=subset["Offset"],
                y=subset["CP"],
                mode="markers",
                name=category,
                marker=dict(color=color, size=10, opacity=0.7),
                customdata=customdata,
                hovertemplate=(
                    "<b>Plant</b> : %{customdata[0]}<br>"
                    "<b>M_CODE</b> : %{customdata[1]}<br>"
                    "OEM : %{customdata[2]} | "
                    "Vehicle : %{customdata[3]}<br><br>"
                    "<b>Spec Information</b><br>"
                    "LIMIT : %{customdata[4]}<br>"
                    "MIN / MAX : %{customdata[5]} / %{customdata[6]}<br>"
                    "LCL / UCL : %{customdata[7]} / %{customdata[8]}<br><br>"
                    "<b>Measurement Result</b><br>"
                    "Count : %{customdata[9]}<br>"
                    "Avg. : %{customdata[10]:.2f}<br>"
                    "STD : %{customdata[11]:.2f}<br>"
                    "CP : %{customdata[12]:.2f}<br>"
                    "Offset : %{customdata[13]:.1%}<br>"
                    "<b>Expected Pass Ratio(%)</b> : %{customdata[14]:.1%}<br>"
                ),
            )
        )
    range_max = max(abs(df["Offset"])) * 1.1 if len(df["Offset"]) > 1 else 0.1

    fig.update_layout(
        height=500,
        title_text="RR Level by Specification",
        title_subtitle_text="Scatter Plot of OFFSET vs. CP for Expected Pass Rate",
        xaxis=dict(
            title_text="OFFSET",
            tickformat=".1%",
            zeroline=True,
            range=[-range_max, range_max],
        ),
        yaxis=dict(title_text="CP", zeroline=True),
    )
    return fig


def scatter_rr_trend_individual(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["SMPL_DATE"],
            y=df["Result_new"],
            mode="markers",
            name="Corrected",
            marker=dict(color=config_plotly.ORANGE_CLR),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["SMPL_DATE"],
            y=df["TEST_RESULT_OLD"],
            mode="markers",
            name="Original",
            marker=dict(color=config_plotly.GRAY_CLR),
            visible="legendonly",
        )
    )

    usl, lsl, ucl, lcl = get_spec_limits(df)
    fig.add_hline(y=usl, line_dash="dot", line_color=config_plotly.NEGATIVE_CLR)
    if lsl == 0.0:
        fig.add_hline(y=ucl, line_dash="dot", line_color=config_plotly.POSITIVE_CLR)
        fig.add_hline(y=lcl, line_dash="dot", line_color=config_plotly.POSITIVE_CLR)
    else:
        fig.add_hline(y=lsl, line_dash="dot", line_color=config_plotly.NEGATIVE_CLR)

    fig.update_layout(
        title="Control Chart", xaxis_title="Sample Date", yaxis_title="Result"
    )
    return fig


def box_rr_individual(df):
    usl, lsl, _, _ = get_spec_limits(df)
    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=df["Result_new"],
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.8,
            boxmean=True,
            marker=dict(color=config_plotly.ORANGE_CLR),
            fillcolor=config_plotly.GRAY_CLR,
        )
    )
    fig.add_hline(
        y=usl,
        line_width=1,
        line_dash="dot",
        line_color=config_plotly.NEGATIVE_CLR,
    )
    if lsl != 0.0:
        fig.add_hline(
            y=lsl,
            line_width=1,
            line_dash="dot",
            line_color="red",
        )
    return fig


def pdf_rr_individual(df):
    usl, lsl, ucl, lcl = get_spec_limits(df)
    mu, sigma = np.mean(df["Result_new"]), np.std(df["Result_new"])
    x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 100)
    y = norm.pdf(x, mu, sigma)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=df["Result_new"],
            histnorm="probability density",
            opacity=0.6,
            marker=dict(color=config_plotly.LIGHT_GRAY_CLR),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color=config_plotly.ORANGE_CLR, width=2),
        )
    )
    fig.add_vline(x=mu, line_dash="dash", line_color="black")

    for i, color in zip(range(1, 4), ["green", "orange", "red"]):
        fig.add_shape(
            type="rect",
            x0=mu - i * sigma,
            x1=mu + i * sigma,
            y0=0,
            y1=max(y),
            fillcolor=color,
            opacity=0.1,
            line=dict(width=0),
        )

    fig.add_vline(x=usl, line_dash="dot", line_color="red")
    if lsl == 0.0:
        if usl != ucl:
            fig.add_vline(x=ucl, line_dash="dot", line_color="green")
        fig.add_vline(x=lcl, line_dash="dot", line_color="green")
    else:
        fig.add_vline(x=lsl, line_dash="dot", line_color="red")

    return fig


def main():
    # ? TEST 기간동안 M-Code 이력이 없을 수 있음을 감안해야함
    today = config.today_str
    one_year_ago = config.one_year_ago
    selected_mcode = "1032181"

    rr_agg = get_processed_agg_rr_data()
    rr_raw = get_processed_raw_rr_data(
        start_date=one_year_ago, end_date=today, mcode=selected_mcode
    )
    hbar_expected_pass_rate_by_plant(rr_agg).show()
    histogram_expected_pass_rate_by_plant(rr_agg).show()
    scatter_expected_pass_rate_by_project(rr_agg).show()
    scatter_rr_trend_individual(rr_raw).show()
    box_rr_individual(rr_raw).show()
    pdf_rr_individual(rr_raw).show()


if __name__ == "__main__":
    main()
