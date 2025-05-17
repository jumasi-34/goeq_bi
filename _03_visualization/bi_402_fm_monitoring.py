"""
bi_402_fm_monitoring
"""

import sys
import plotly.graph_objects as go

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _02_preprocessing.GMES import df_ncf
from _03_visualization import config_plotly
from _05_commons import config

if config.DEV_MODE:
    import importlib

    importlib.reload(df_ncf)

selected_year = "2024"


def plot_fm_ncf_qty_by_plant(yyyy):

    df = df_ncf.get_yearly_ppm_df(yyyy)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["PLANT"],
            y=df["NCF_QTY"],
            text=df["NCF_QTY"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.ORANGE_CLR),
        )
    )

    fig.update_layout(
        title=dict(
            text="공장별 FM 부적합 연간 발생 수량",
            font=dict(color=config_plotly.GRAY_CLR),
        ),
    )
    fig.update_yaxes(showgrid=False, showticklabels=False).update_xaxes(
        domain=[0.1, 0.9]
    )
    return fig


def plot_fm_ppm_by_plant(yyyy):
    df = df_ncf.get_yearly_ppm_df(yyyy)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["PLANT"],
            y=df["PPM"],
            text=df["PPM"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.ORANGE_CLR),
        )
    )
    fig.update_layout(
        title=dict(
            text="공장별 FM 부적합 발생율 (PPM)",
            font=dict(color=config_plotly.GRAY_CLR),
        ),
    )
    fig.update_yaxes(showgrid=False, showticklabels=False)
    fig.update_xaxes(domain=[0.1, 0.9])
    return fig


def plot_monthly_fm_ppm_for_plant(year, plant):
    df = df_ncf.get_monthly_ppm_by_plant_df(year, plant)

    month_mean = df["NCF_QTY"].sum() / df["PRDT_QTY"].sum() * 1000000
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["MM"],
            y=df["PPM"],
            text=df["PPM"],
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.ORANGE_CLR),
            mode="markers+lines+text",
            textposition="top center",
        )
    )
    fig.update_xaxes(
        dtick=1,
        range=[0, 13],
        tickmode="array",
        tickvals=list(range(1, 13)),  # monthly_merge_ncf_ppm["MM"],
        ticktext=config_plotly.months_abbreviation,
        domain=[0, 0.9],
    )
    fig.update_yaxes(showgrid=False)
    fig.add_hline(
        y=month_mean,
        line=dict(width=1, color=config_plotly.NEGATIVE_CLR),
        annotation=dict(
            text=f"Monthly Avg : <br>{month_mean:,.0f} ppm", x=1.05, xanchor="right"
        ),
    )
    fig.update_layout(
        height=400,
        margin=dict(t=60, b=40, l=40, r=20),
        title=dict(
            text=f"{selected_plant} 월별 FM 부적합 발생 현황",
            font=dict(color=config_plotly.GRAY_CLR),
        ),
    )
    return fig


def plot_fm_ncf_by_defect_type_for_plant(yyyy, plant):
    df = df_ncf.get_ncf_detail_by_plant_df(yyyy, selected_plant=plant)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["DFT_CD"],
            y=df["NCF_QTY"],
            text=df["NCF_QTY"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.ORANGE_CLR),
        )
    ).update_xaxes(dtick=1).update_yaxes(showgrid=False).update_layout(
        title=dict(
            text=f"{selected_plant} 유형별 FM 부적합 발생 현황",
            font=dict(color=config_plotly.GRAY_CLR),
        )
    )
    return fig


selected_year = "2024"
selected_plant = "DP"


def main():
    plot_fm_ncf_qty_by_plant(selected_year).show()
    plot_fm_ppm_by_plant(selected_year).show()

    plot_monthly_fm_ppm_for_plant(selected_year, selected_plant).show()

    plot_fm_ncf_by_defect_type_for_plant(selected_year, selected_plant).show()


if __name__ == "__main__":
    main()
