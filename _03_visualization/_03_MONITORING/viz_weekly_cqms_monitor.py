"""
주간 CQMS 모니터링 대시보드의 히트맵 시각화 모듈

이 모듈은 품질 이슈, 4M 변경, 고객사 감사의 주간 진행상황을 히트맵으로 시각화합니다.
"""

import sys
from datetime import timedelta
import numpy as np
import plotly.graph_objects as go
from typing import Tuple, Union
import pandas as pd
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import config_plotly
from _05_commons import config


def create_heatmap(df: pd.DataFrame, title: str) -> go.Figure:
    """
    주간 모니터링 히트맵을 생성하는 공통 함수입니다.

    Args:
        df (pd.DataFrame): 피벗된 데이터프레임
        title (str): 히트맵 제목

    Returns:
        go.Figure: 생성된 히트맵 figure 객체
    """
    try:
        # Global 행 제거 및 인덱스 설정
        df = df.set_index("PLANT").drop("Global", errors="ignore")
        tickvals_max = df.values.max()

        # 히트맵 생성
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df.columns,
                y=df.index,
                z=df.values,
                texttemplate="%{z}",
                colorscale=[[0, config_plotly.GRAY_CLR], [1, config_plotly.ORANGE_CLR]],
                colorbar=dict(
                    title="Count",
                    tickvals=np.arange(0, tickvals_max + 1, 1),
                ),
                hovertemplate="""<b>Status</b>: %{x}<br><b>PLANT</b>: %{y}<br><b>Count</b>: %{z}<extra></extra>""",
            )
        )

        # 레이아웃 설정
        fig.update_layout(
            margin=dict(t=80, b=50, l=25, r=25),
            title_text=title,
            yaxis=dict(autorange="reversed"),
        )

        return fig

    except Exception as e:
        print(f"히트맵 생성 중 오류 발생: {str(e)}")
        return go.Figure()


def heatmap_qi_weekly(start_date: pd.Timestamp, end_date: pd.Timestamp) -> go.Figure:
    """
    품질 이슈의 주간 진행상황 히트맵을 생성합니다.

    Args:
        start_date (pd.Timestamp): 시작일
        end_date (pd.Timestamp): 종료일

    Returns:
        go.Figure: 품질 이슈 히트맵 figure 객체
    """
    try:
        df = df_quality_issue.pivot_quality_by_week_and_status(start_date, end_date)
        title = "Weekly Quality Issue Progress"
        return create_heatmap(df, title)
    except Exception as e:
        print(f"품질 이슈 히트맵 생성 중 오류 발생: {str(e)}")
        return go.Figure()


def heatmap_4m_weekly(start_date: pd.Timestamp, end_date: pd.Timestamp) -> go.Figure:
    """
    4M 변경의 주간 진행상황 히트맵을 생성합니다.

    Args:
        start_date (pd.Timestamp): 시작일
        end_date (pd.Timestamp): 종료일

    Returns:
        go.Figure: 4M 변경 히트맵 figure 객체
    """
    try:
        df = df_4m_change.df_pivot_4m(start_date, end_date)
        title = "Weekly 4M Change Progress by Plant"
        return create_heatmap(df, title)
    except Exception as e:
        print(f"4M 변경 히트맵 생성 중 오류 발생: {str(e)}")
        return go.Figure()


def heatmap_audit_weekly(start_date: pd.Timestamp, end_date: pd.Timestamp) -> go.Figure:
    """
    고객사 감사의 주간 진행상황 히트맵을 생성합니다.

    Args:
        start_date (pd.Timestamp): 시작일
        end_date (pd.Timestamp): 종료일

    Returns:
        go.Figure: 고객사 감사 히트맵 figure 객체
    """
    try:
        df = df_customer_audit.df_pivot_audit(start_date, end_date)
        title = "Weekly Audit Progress by Plant"
        return create_heatmap(df, title)
    except Exception as e:
        print(f"고객사 감사 히트맵 생성 중 오류 발생: {str(e)}")
        return go.Figure()


def main():
    """테스트 실행 함수"""
    today = config.today
    aweekago = config.today - timedelta(days=7)

    # 테스트용 히트맵 생성
    heatmap_4m_weekly(today, aweekago).show()
    heatmap_qi_weekly(today, aweekago).show()
    heatmap_audit_weekly(today, aweekago).show()


if __name__ == "__main__":
    main()
