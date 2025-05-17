import sys
import numpy as np
import plotly.graph_objects as go

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import config_plotly, helper_plotly


def create_pie_chart(df, value_col, title):
    colors = helper_plotly.get_transparent_colors(config_plotly.ORANGE_CLR, len(df))
    fig = go.Figure(
        go.Pie(
            labels=df.index,
            values=df[value_col],
            textinfo="label+value",
            direction="clockwise",
            marker=dict(
                colors=colors,
                line=dict(color=config_plotly.GRAY_CLR, width=0.5),
            ),
            hovertemplate=(
                """<b>Plant</b>: %{label}<br><b>Count</b>: %{value}<br><b>Possession</b>: %{percent:.1%}<extra></extra>"""
            ),
        )
    )
    fig.update_layout(title_text=title, showlegend=False)
    return fig


def create_bar_chart(df, value_col, title):
    range_max = df[value_col].max() * 1.3
    fig = go.Figure(
        go.Bar(
            x=df.index,
            y=df[value_col],
            text=df[value_col],
            marker=dict(color=config_plotly.ORANGE_CLR),
            textposition="outside",
            texttemplate=["%{text:.0f}" if val != 0 else "" for val in df[value_col]],
            hovertemplate=(
                """<b>Month</b>: %{x|%b. %Y}<br><b>Count</b>: %{y:.0f}EA<extra></extra>"""
            ),
        )
    )
    fig.update_layout(
        title_text=title,
        yaxis=dict(showgrid=False, showticklabels=False, range=[0, range_max]),
        xaxis=dict(
            tickmode="array",
            tickvals=df.index,
            ticktext=[dt.strftime("%Y-%m") for dt in df.index],
        ),
        showlegend=False,
    )
    return fig


def ongoing_qi_pie_by_plant(plants=None):
    df = df_quality_issue.summarize_ongoing_quality_by_plant(plants=plants)
    return create_pie_chart(df, "count", "Opening status by plant")


def ongoing_qi_bar_by_month(plants=None):
    df = df_quality_issue.summarize_ongoing_quality_by_month(plants=plants)
    return create_bar_chart(df, "count", "Monthly openings")


def ongoing_4m_pie_by_plant(plants=None):
    _, _, df_by_plant, _ = df_4m_change.filtered_4m_ongoing_by_yearly(plants=plants)
    return create_pie_chart(df_by_plant, "COUNT", "Opening status by plant")


def ongoing_4m_bar_by_month(plants=None):
    _, _, _, df_by_month = df_4m_change.filtered_4m_ongoing_by_yearly(plants=plants)
    return create_bar_chart(df_by_month, "COUNT", "Monthly openings")


def ongoing_audit_pie_by_plant(plants=None):
    _, df_by_plant, _ = df_customer_audit.get_audit_ongoing_df(plants=plants)
    return create_pie_chart(df_by_plant, "COUNT", "Opening status by plant")


def ongoing_audit_bar_by_month(plants=None):
    _, _, df_by_month = df_customer_audit.get_audit_ongoing_df(plants=plants)
    return create_bar_chart(df_by_month, "COUNT", "Monthly openings")


def main():
    ongoing_qi_pie_by_plant().show()
    ongoing_qi_bar_by_month().show()
    ongoing_4m_pie_by_plant().show()
    ongoing_4m_bar_by_month().show()
    ongoing_audit_pie_by_plant().show()
    ongoing_audit_bar_by_month().show()


if __name__ == "__main__":
    main()
