"""
bi_201_weekly_cqms_monitor
"""

import sys
from datetime import timedelta, datetime
import numpy as np
import plotly.graph_objects as go


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import config_plotly, helper_plotly
from _05_commons import config


def create_heatmap(df, title):
    """
    Weekly 모니터링 Heatmap 생성 공통함수
    """
    df = df.set_index("PLANT").drop("Global", errors="ignore")
    tickvalas_max = df.values.max()
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
                tickvals=np.arange(0, tickvalas_max + 1, 1),
            ),
            hovertemplate="""<b>Status</b>: %{x}<br><b>PLANT</b>: %{y}<br><b>Count</b>: %{z}<extra></extra>""",
        )
    )
    fig.update_layout(
        margin=dict(t=80, b=50, l=25, r=25),
        title_text=title,
        yaxis=dict(autorange="reversed"),
    )

    return fig


def heatmap_qi_weekly(start_date, end_date):
    """
    Weekly Quality Issue Heat Map
    """

    df = df_quality_issue.pivot_quality_by_week_and_status(start_date, end_date)
    title = "Weekly quality issue progress"
    fig = create_heatmap(df, title)
    return fig


def heatmap_4m_weekly(start_date, end_date):
    """
    Weekly 4M Change Heat Map
    """
    df = df_4m_change.df_pivot_4m(start_date, end_date)
    title = "Weekly 4M Change progress by plant"
    fig = create_heatmap(df, title)
    return fig


def heatmap_audit_weekly(start_date, end_date):
    """
    Weekly Customer Audit Heat Map
    """
    df = df_customer_audit.df_pivot_audit(start_date, end_date)
    title = "Weekly Audit progress by plant"
    fig = create_heatmap(df, title)
    return fig


def main():
    today = config.today
    aweekago = config.today - timedelta(days=7)
    heatmap_4m_weekly(today, aweekago).show()
    heatmap_4m_weekly(today, aweekago).show()
    heatmap_audit_weekly(today, aweekago).show()


if __name__ == "__main__":
    main()
