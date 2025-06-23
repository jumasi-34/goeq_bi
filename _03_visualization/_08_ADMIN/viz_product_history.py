import plotly.graph_objects as go
from _03_visualization import config_plotly


def draw_pie_cqms_event(df):
    trace = go.Pie(
        labels=df.index,
        values=df.values,
        hole=0.4,
        marker=dict(
            colors=[
                config_plotly.RED_CLR,
                config_plotly.BLUE_CLR,
                config_plotly.GREEN_CLR,
            ]
        ),
        textinfo="label+percent+value",
        texttemplate="%{label}<br><b>%{value}</b> [%{percent:.1%}]",
        textfont=dict(size=12),
        direction="clockwise",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
    )

    layout = go.Layout(
        title="Event Distribution by Category",
        height=300,
        margin=dict(l=30, r=30, t=50, b=30),
        showlegend=False,
    )

    fig = go.Figure(data=[trace], layout=layout)
    return fig


def draw_gantt_timeline(df):
    """
    CQMS 데이터를 Gantt 차트 스타일의 타임라인으로 시각화

    Args:
        cqms_data (pd.DataFrame): CQMS 이벤트 데이터

    Returns:
        go.Figure: Gantt 스타일 타임라인 차트
    """
    # 카테고리별 색상 매핑
    color_map = {
        "Quality Issue": config_plotly.RED_CLR,
        "4M Change": config_plotly.BLUE_CLR,
        "Audit": config_plotly.GREEN_CLR,
    }

    # 각 카테고리별로 trace 생성
    traces = []

    # 카테고리 순서 고정
    category_order = ["Quality Issue", "4M Change", "Audit"]

    for category in category_order[::-1]:
        if category in df["CATEGORY"].unique():
            category_data = df[df["CATEGORY"] == category].copy()
            category_data = category_data.sort_values("REG_DATE")

            # 마커 trace
            marker_trace = go.Scatter(
                x=category_data["REG_DATE"],
                y=category_data["SUBJECT"],
                mode="markers+text",
                name=category,
                text=(
                    category_data["SUBJECT"].str[:30] + "..."
                    if category_data["SUBJECT"].str.len().max() > 30
                    else category_data["SUBJECT"]
                ),
                textposition="top center",
                textfont=dict(size=9, color="white"),
                marker=dict(
                    color=color_map.get(category, config_plotly.ORANGE_CLR),
                    size=16,
                    symbol="diamond",
                    line=dict(color="white", width=2),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    + "Category: "
                    + category
                    + "<br>"
                    + "Date: %{x}<br>"
                    + "<extra></extra>"
                ),
                showlegend=True,
            )
            traces.append(marker_trace)

            # 연결선 trace (같은 카테고리 내에서)
            if len(category_data) > 1:
                line_trace = go.Scatter(
                    x=category_data["REG_DATE"],
                    y=category_data["SUBJECT"],
                    mode="lines",
                    name=f"{category} Timeline",
                    line=dict(
                        color=color_map.get(category, config_plotly.ORANGE_CLR),
                        width=2,
                        dash="dot",
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
                traces.append(line_trace)

    # 레이아웃 설정
    layout = go.Layout(
        title=dict(
            text="CQMS Events Timeline",
            x=0.5,
            font=dict(size=16, color="black"),
        ),
        xaxis=dict(
            title="Date",
            type="date",
            tickangle=45,
            tickformat="%Y-%m-%d",
            gridcolor="lightgray",
            showgrid=True,
        ),
        yaxis=dict(
            title="Event",
            showgrid=False,
            zeroline=False,
            categoryorder="array",
            categoryarray=category_order,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return go.Figure(data=traces, layout=layout)


def draw_area_chart_sellin_by_mcode(df):
    trace = go.Scatter(
        x=df["YYYY_MM"],
        y=df["SUPP_QTY"],
        name="Supply",
        fill="tonexty",  # 영역 채우기 추가
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        title="Supply Trend",
        xaxis_title="Month",
        yaxis_title="Quantity",
        yaxis=dict(range=[0, df["SUPP_QTY"].max() * 1.1]),
        xaxis=dict(
            type="category",
            categoryorder="category ascending",
            tickmode="array",
            tickvals=df["YYYY_MM"].tolist(),
            ticktext=df["YYYY_MM"].tolist(),
            tickangle=45,  # 틱 라벨 회전
            rangeslider=dict(visible=False),
        ),
    )
    fig = go.Figure(data=[trace], layout=layout)
    return fig


def draw_barplot_hgws_by_mcode(df):
    trace = go.Bar(
        x=df["RETURN CNT"],
        y=df["REASON DESCRIPTION"],
        text=df["RETURN CNT"],
        textposition="outside",
        textfont=dict(size=12),
        orientation="h",
        name="Return",
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        height=500,
        title="Return Trend",
        xaxis_title="Return Count",
        yaxis_title="Reason Description",
        xaxis=dict(
            range=[0, df["RETURN CNT"].max() * 1.1],
        ),
        yaxis=dict(
            autorange="reversed",
            categoryorder="array",
        ),
    )
    fig = go.Figure(data=[trace], layout=layout)
    return fig
