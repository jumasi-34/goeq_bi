import sys
from datetime import datetime as dt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import config_plotly, helper_plotly


def create_pie_chart(df, value_col, title):
    """파이 차트를 생성하는 함수

    Args:
        df (pd.DataFrame): 차트를 그릴 데이터프레임
        value_col (str): 차트에 사용할 값이 있는 컬럼명
        title (str): 차트 제목

    Returns:
        plotly.graph_objects.Figure: 생성된 파이 차트

    Raises:
        ValueError: 필수 컬럼이 없거나 데이터프레임이 비어있는 경우
    """
    # 데이터 유효성 검사
    if df.empty:
        raise ValueError("데이터프레임이 비어있습니다.")
    if value_col not in df.columns:
        raise ValueError(f"'{value_col}' 컬럼이 데이터프레임에 존재하지 않습니다.")

    # 색상 설정
    colors = helper_plotly.get_transparent_colors(config_plotly.ORANGE_CLR, len(df))

    # 파이 차트 생성
    fig = go.Figure(
        go.Pie(
            labels=df.index,
            values=df[value_col],
            textinfo=config_plotly.CHART_STYLES["pie"]["textinfo"],
            direction=config_plotly.CHART_STYLES["pie"]["direction"],
            marker=dict(
                colors=colors,
                line=dict(
                    color=config_plotly.GRAY_CLR,
                    width=config_plotly.CHART_STYLES["pie"]["line_width"],
                ),
            ),
            hovertemplate=config_plotly.CHART_STYLES["pie"]["hover_template"],
        )
    )

    # 레이아웃 설정
    fig.update_layout(title_text=title, **config_plotly.LAYOUT_STYLES["pie"])
    return fig


def create_bar_chart(df, value_col, title):
    """바 차트를 생성하는 함수

    Args:
        df (pd.DataFrame): 차트를 그릴 데이터프레임
        value_col (str): 차트에 사용할 값이 있는 컬럼명
        title (str): 차트 제목

    Returns:
        plotly.graph_objects.Figure: 생성된 바 차트

    Raises:
        ValueError: 필수 컬럼이 없거나 데이터프레임이 비어있는 경우
    """
    # 데이터 유효성 검사
    if df.empty:
        raise ValueError("데이터프레임이 비어있습니다.")
    if value_col not in df.columns:
        raise ValueError(f"'{value_col}' 컬럼이 데이터프레임에 존재하지 않습니다.")

    # Y축 범위 설정 (최대값의 1.3배)
    range_max = df[value_col].max() * 1.3

    # 바 차트 생성
    fig = go.Figure(
        go.Bar(
            x=df.index,
            y=df[value_col],
            text=df[value_col],
            marker=dict(color=config_plotly.ORANGE_CLR),
            textposition=config_plotly.CHART_STYLES["bar"]["text_position"],
            texttemplate=["%{text:.0f}" if val != 0 else "" for val in df[value_col]],
            hovertemplate=config_plotly.CHART_STYLES["bar"]["hover_template"],
        )
    )

    # 레이아웃 설정
    layout = config_plotly.LAYOUT_STYLES["bar"].copy()
    layout["title_text"] = title
    layout["yaxis"]["range"] = [0, range_max]
    layout["xaxis"].update(
        {
            "tickvals": df.index,
            "ticktext": [dt.strftime("%Y-%m") for dt in df.index],
        }
    )
    fig.update_layout(**layout)
    return fig


# 품질 이슈 관련 차트 생성 함수들
def ongoing_qi_pie_by_plant(plants=None):
    """공장별 품질 이슈 현황을 파이 차트로 표시"""
    df = df_quality_issue.summarize_ongoing_quality_by_plant(plants=plants)
    return create_pie_chart(
        df, "count", config_plotly.CHART_TITLES["ongoing_qi"]["pie"]
    )


def ongoing_qi_bar_by_month(plants=None):
    """월별 품질 이슈 현황을 바 차트로 표시"""
    df = df_quality_issue.summarize_ongoing_quality_by_month(plants=plants)
    return create_bar_chart(
        df, "count", config_plotly.CHART_TITLES["ongoing_qi"]["bar"]
    )


# 4M 변경 관련 차트 생성 함수들
def ongoing_4m_pie_by_plant(plants=None):
    """공장별 4M 변경 현황을 파이 차트로 표시"""
    _, _, df_by_plant, _ = df_4m_change.filtered_4m_ongoing_by_yearly(plants=plants)
    return create_pie_chart(
        df_by_plant, "COUNT", config_plotly.CHART_TITLES["ongoing_4m"]["pie"]
    )


def ongoing_4m_bar_by_month(plants=None):
    """월별 4M 변경 현황을 바 차트로 표시"""
    _, _, _, df_by_month = df_4m_change.filtered_4m_ongoing_by_yearly(plants=plants)
    return create_bar_chart(
        df_by_month, "COUNT", config_plotly.CHART_TITLES["ongoing_4m"]["bar"]
    )


# 고객 감사 관련 차트 생성 함수들
def ongoing_audit_pie_by_plant(plants=None):
    """공장별 고객 감사 현황을 파이 차트로 표시"""
    _, df_by_plant, _ = df_customer_audit.get_audit_ongoing_df(plants=plants)
    return create_pie_chart(
        df_by_plant, "COUNT", config_plotly.CHART_TITLES["ongoing_audit"]["pie"]
    )


def ongoing_audit_bar_by_month(plants=None):
    """월별 고객 감사 현황을 바 차트로 표시"""
    _, _, df_by_month = df_customer_audit.get_audit_ongoing_df(plants=plants)
    return create_bar_chart(
        df_by_month, "COUNT", config_plotly.CHART_TITLES["ongoing_audit"]["bar"]
    )


def main():
    """모든 차트를 생성하고 표시"""
    ongoing_qi_pie_by_plant().show()
    ongoing_qi_bar_by_month().show()
    ongoing_4m_pie_by_plant().show()
    ongoing_4m_bar_by_month().show()
    ongoing_audit_pie_by_plant().show()
    ongoing_audit_bar_by_month().show()


if __name__ == "__main__":
    main()
