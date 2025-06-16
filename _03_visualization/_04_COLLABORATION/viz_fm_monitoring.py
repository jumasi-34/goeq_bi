"""
FM 모니터링 시각화 모듈

이 모듈은 FM(Final Manufacturing) 관련 데이터를 시각화하는 함수들을 제공합니다.
주요 기능:
- 공장별 FM 부적합 수량 시각화
- 공장별 FM 부적합 PPM 시각화
- 공장별 월간 FM 부적합 PPM 추이 시각화
- 공장별 불량 유형별 FM 부적합 현황 시각화

작성자: [Your Name]
"""

import sys
from datetime import datetime as dt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _03_visualization import config_plotly

if config.DEV_MODE:
    import importlib


def plot_global_ncf_monthly(df, prev_df, current_year, prev_year):
    """전체 공장의 월별 FM 부적합 수량을 선 그래프로 시각화합니다.

    Args:
        df (pd.DataFrame): 전체 공장의 월별 FM 부적합 수량 데이터
            - MM: 월
            - NCF_QTY: 부적합 수량

    Returns:
        go.Figure: 전체 공장의 월별 FM 부적합 수량 선 그래프
    """
    # Define hover template
    hovertemplate = (
        "<b>Month:</b> %{x}<br><b>Non-conformance:</b> %{y:,.0f}EA<br>"
        + "<extra></extra>"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=prev_df["MM"],
            y=prev_df["NCF_QTY"],
            name=f"{prev_year}",
            text=prev_df["NCF_QTY"],
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.GRAY_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["MM"],
            y=df["NCF_QTY"],
            name=f"{current_year}",
            text=df["NCF_QTY"],
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.ORANGE_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.update_layout(
        title=dict(
            text="Global FM Non-conformance Quantity by Month",
            font=dict(color=config_plotly.GRAY_CLR),
            x=0.05,
            xanchor="left",
            y=0.95,
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        range=[0, max(df["NCF_QTY"].max(), prev_df["NCF_QTY"].max()) * 1.2],
        title="Non-conformance Quantity[EA]",
    )
    fig.update_xaxes(
        domain=[0.1, 0.9],
        tickangle=0,
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=config_plotly.months_abbreviation,
    )

    return fig


def plot_global_ncf_ppm_monthly(df, prev_df, current_year, prev_year):
    """전체 공장의 월별 FM 부적합 PPM을 선 그래프로 시각화합니다.

    Args:
        df (pd.DataFrame): 전체 공장의 월별 FM 부적합 PPM 데이터
            - MM: 월
            - PPM: 부적합 PPM

    Returns:
        go.Figure: 전체 공장의 월별 FM 부적합 PPM 선 그래프
    """
    # Define hover template
    hovertemplate = (
        "<b>Month:</b> %{x}<br><b>Non-conformance:</b> %{y:,.0f} ppm<br>"
        + "<extra></extra>"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=prev_df["MM"],
            y=prev_df["PPM"],
            mode="markers+lines+text",
            name=f"{prev_year}",
            text=prev_df["PPM"],
            textposition="top center",
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.GRAY_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["MM"],
            y=df["PPM"],
            mode="markers+lines+text",
            name=f"{current_year}",
            text=df["PPM"],
            textposition="top center",
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.ORANGE_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.update_layout(
        title=dict(
            text="Global FM Non-conformance PPM by Month",
            font=dict(color=config_plotly.GRAY_CLR),
            x=0.05,
            xanchor="left",
            y=0.95,
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        range=[0, max(df["PPM"].max(), prev_df["PPM"].max()) * 1.2],
        title="Non-conformance Rate[PPM]",
    )
    fig.update_xaxes(
        domain=[0.1, 0.9],
        tickangle=0,
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=config_plotly.months_abbreviation,
    )
    return fig


def plot_fm_ncf_qty_by_plant(df):
    """공장별 FM 부적합 수량을 막대 그래프로 시각화합니다.

    Args:
        df (pd.DataFrame): 공장별 FM 부적합 수량 데이터
            - PLANT: 공장 코드
            - NCF_QTY: 부적합 수량

    Returns:
        go.Figure: 공장별 FM 부적합 수량 막대 그래프
    """
    # Define hover template
    hovertemplate = (
        "<b>Plant:</b> %{x}<br><b>NCF Quantity:</b> %{y:,.0f}<br>" + "<extra></extra>"
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["PLANT"],
            y=df["NCF_QTY"],
            text=df["NCF_QTY"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.ORANGE_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.update_layout(
        title=dict(
            text="Annual FM Non-conformance Quantity by Plant",
            font=dict(color=config_plotly.GRAY_CLR),
            x=0.05,
            xanchor="left",
            y=0.95,
        ),
    )

    fig.update_yaxes(
        showgrid=False,
        showticklabels=False,
        zeroline=False,
        range=[0, df["NCF_QTY"].max() * 1.2],
    )
    fig.update_xaxes(domain=[0.1, 0.9], tickangle=0)

    return fig


def plot_fm_ppm_by_plant(df, prev_df=None):
    """공장별 FM 부적합 PPM(Parts Per Million)을 막대 그래프로 시각화합니다.

    Args:
        df (pd.DataFrame): 공장별 FM 부적합 PPM 데이터
            - PLANT: 공장 코드
            - PPM: 부적합 PPM
        prev_df (pd.DataFrame, optional): 전년도 공장별 FM 부적합 PPM 데이터
            - PLANT: 공장 코드
            - PPM: 부적합 PPM

    Returns:
        go.Figure: 공장별 FM 부적합 PPM 막대 그래프
    """
    # Define hover template
    hovertemplate = (
        "<b>Plant:</b> %{x}<br><b>PPM:</b> %{y:,.0f}<br>" + "<extra></extra>"
    )

    fig = go.Figure()

    # 전년도 데이터가 있는 경우 추가
    if prev_df is not None:
        fig.add_trace(
            go.Bar(
                x=prev_df["PLANT"],
                y=prev_df["PPM"],
                name="Previous Year",
                text=prev_df["PPM"],
                texttemplate="%{y:,.0f}",
                textposition="outside",
                marker=dict(color=config_plotly.GRAY_CLR),
                hovertemplate=hovertemplate,
            )
        )

    # 현재 연도 데이터 추가
    fig.add_trace(
        go.Bar(
            x=df["PLANT"],
            y=df["PPM"],
            name="Current Year",
            text=df["PPM"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            marker=dict(color=config_plotly.ORANGE_CLR),
            hovertemplate=hovertemplate,
        )
    )

    fig.update_layout(
        title=dict(
            text="Annual FM Non-conformance PPM by Plant",
            font=dict(color=config_plotly.GRAY_CLR),
            x=0.05,
            xanchor="left",
            y=0.95,
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(
        showgrid=False,
        showticklabels=False,
        zeroline=False,
        range=[
            0,
            max(df["PPM"].max(), prev_df["PPM"].max() if prev_df is not None else 0)
            * 1.2,
        ],
    )
    fig.update_xaxes(domain=[0.1, 0.9], tickangle=0)

    return fig


def plot_monthly_fm_ppm_for_plant(df, plant, prev_df=None):
    """특정 공장의 월별 FM 부적합 PPM 추이를 선 그래프로 시각화합니다.

    Args:
        df (pd.DataFrame): 월별 FM 부적합 PPM 데이터
            - MM: 월
            - PPM: 부적합 PPM
            - NCF_QTY: 부적합 수량
            - PRDT_QTY: 생산 수량
        plant (str): 공장 코드
        prev_df (pd.DataFrame, optional): 전년도 월별 FM 부적합 PPM 데이터

    Returns:
        go.Figure: 월별 FM 부적합 PPM 추이 선 그래프
    """
    month_mean = df["NCF_QTY"].sum() / df["PRDT_QTY"].sum() * 1000000

    # Define hover template
    hovertemplate = (
        "<b>Month:</b> %{x}<br>"
        "<b>Non-conformance:</b> %{customdata[0]:,.0f}EA ( <span style='color: #FF4B4B'>%{y:,.0f} ppm</span> )<br>"
        "<b>Production:</b> %{customdata[1]:,.0f}EA<br>" + "<extra></extra>"
    )

    fig = go.Figure()

    # 전년도 데이터가 있는 경우 추가
    if prev_df is not None:
        fig.add_trace(
            go.Scatter(
                x=prev_df["MM"],
                y=prev_df["PPM"],
                name="Previous Year",
                marker=dict(color=config_plotly.GRAY_CLR),
                mode="lines",
                line=dict(dash="dot"),
                customdata=prev_df[["NCF_QTY", "PRDT_QTY"]],
                hovertemplate=hovertemplate,
            )
        )

    # 현재 연도 데이터 추가
    fig.add_trace(
        go.Scatter(
            x=df["MM"],
            y=df["PPM"],
            name="Current Year",
            text=df["PPM"],
            texttemplate="%{y:,.0f}",
            marker=dict(color=config_plotly.ORANGE_CLR),
            mode="markers+lines+text",
            textposition="top center",
            customdata=df[["NCF_QTY", "PRDT_QTY"]],
            hovertemplate=hovertemplate,
        )
    )

    fig.update_xaxes(
        dtick=1,
        range=[0, 13],
        tickmode="array",
        tickvals=list(range(1, 13)),
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
            text=f"Monthly FM Non-conformance PPM Trend - {plant}",
            font=dict(color=config_plotly.GRAY_CLR),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_fm_ncf_by_defect_type_for_plant(df, plant, show_all_defects=False):
    """특정 공장의 불량 유형별 FM 부적합 현황을 파레토 차트로 시각화합니다.

    Args:
        df (pd.DataFrame): 불량 유형별 FM 부적합 데이터
            - DFT_CD: 불량 코드
            - NCF_QTY: 부적합 수량
        plant (str): 공장 코드
        show_all_defects (bool): 모든 불량 유형을 표시할지 여부 (기본값: False)

    Returns:
        go.Figure: 불량 유형별 FM 부적합 현황 파레토 차트
    """
    if not show_all_defects:
        # 상위 10개 부적합만 선택하고 나머지는 '기타'로 합치기
        df_sorted = df.sort_values("NCF_QTY", ascending=False)
        top_10 = df_sorted.head(10)
        others = df_sorted.iloc[10:]

        if not others.empty:
            others_sum = pd.DataFrame(
                {"DFT_CD": ["Others"], "NCF_QTY": [others["NCF_QTY"].sum()]}
            )
            df_plot = pd.concat([top_10, others_sum])
        else:
            df_plot = top_10
    else:
        df_plot = df.sort_values("NCF_QTY", ascending=False)

    # 누적 백분율 계산
    total_ncf = df_plot["NCF_QTY"].sum()
    df_plot["CUM_PCT"] = df_plot["NCF_QTY"].cumsum() / total_ncf * 100

    # 호버 템플릿 정의
    hovertemplate_bar = (
        "<b>Defect Type:</b> %{x}<br>"
        "<b>Non-conformance:</b> %{y:,.0f}EA<br>"
        "<extra></extra>"
    )

    hovertemplate_line = (
        "<b>Defect Type:</b> %{x}<br>"
        "<b>Cumulative %:</b> %{y:.1f}%<br>"
        "<extra></extra>"
    )

    fig = go.Figure()

    if not show_all_defects and not others.empty:
        # 상위 10개 항목과 기타 항목을 다른 색상으로 표시
        fig.add_trace(
            go.Bar(
                x=top_10["DFT_CD"],
                y=top_10["NCF_QTY"],
                text=top_10["NCF_QTY"],
                texttemplate="%{y:,.0f}",
                textposition="outside",
                marker=dict(color=config_plotly.ORANGE_CLR),
                hovertemplate=hovertemplate_bar,
                name="Non-conformance",
                yaxis="y1",
            )
        )
        fig.add_trace(
            go.Bar(
                x=others_sum["DFT_CD"],
                y=others_sum["NCF_QTY"],
                text=others_sum["NCF_QTY"],
                texttemplate="%{y:,.0f}",
                textposition="outside",
                marker=dict(color=config_plotly.GRAY_CLR),
                hovertemplate=hovertemplate_bar,
                name="Others",
                yaxis="y1",
            )
        )
    else:
        # 모든 항목을 동일한 색상으로 표시
        fig.add_trace(
            go.Bar(
                x=df_plot["DFT_CD"],
                y=df_plot["NCF_QTY"],
                text=df_plot["NCF_QTY"],
                texttemplate="%{y:,.0f}",
                textposition="outside",
                marker=dict(color=config_plotly.ORANGE_CLR),
                hovertemplate=hovertemplate_bar,
                name="Non-conformance",
                yaxis="y1",
            )
        )

    # 누적 백분율 라인 추가
    fig.add_trace(
        go.Scatter(
            x=df_plot["DFT_CD"],
            y=df_plot["CUM_PCT"],
            mode="lines+markers",
            name="Cumulative %",
            line=dict(color=config_plotly.NEGATIVE_CLR, width=2),
            marker=dict(color=config_plotly.NEGATIVE_CLR, size=8),
            hovertemplate=hovertemplate_line,
            yaxis="y2",
        )
    )

    # Y축 설정
    fig.update_layout(
        yaxis=dict(
            title="Non-conformance Quantity",
            showgrid=False,
            side="left",
            # y축 상단 여백을 위해 range 설정
            range=[0, df_plot["NCF_QTY"].max() * 1.2],
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 110],
            showgrid=False,
        ),
    )

    fig.update_xaxes(dtick=1)
    fig.update_layout(
        height=400,
        margin=dict(t=60, b=40, l=40, r=40),
        title=dict(
            text=f"FM Non-conformance Pareto Chart by Defect Type - {plant}",
            font=dict(color=config_plotly.GRAY_CLR),
        ),
        showlegend=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


selected_year = "2024"
selected_plant = "DP"


def main():
    """메인 실행 함수"""
    plot_fm_ncf_qty_by_plant(selected_year).show()
    plot_fm_ppm_by_plant(selected_year).show()
    plot_monthly_fm_ppm_for_plant(selected_year, selected_plant).show()
    plot_fm_ncf_by_defect_type_for_plant(selected_year, selected_plant).show()


if __name__ == "__main__":
    main()
