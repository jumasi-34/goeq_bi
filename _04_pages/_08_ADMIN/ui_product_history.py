import streamlit as st
from datetime import datetime, timedelta
import importlib
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from _00_database.db_client import get_client
from _01_query.HOPE import q_hope
from _01_query.CQMS import q_quality_issue, q_4m_change, q_customer_audit
from _01_query.HGWS import q_hgws
from _03_visualization import config_plotly
from _05_commons import config

if config.DEV_MODE:
    importlib.reload(q_hope)
    importlib.reload(q_hgws)


def create_gantt_timeline_chart(cqms_data):
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
        if category in cqms_data["CATEGORY"].unique():
            category_data = cqms_data[cqms_data["CATEGORY"] == category].copy()
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


lastyear_first_day = datetime.now() - timedelta(days=365)
today = datetime.now()

st.subheader("Search")
with st.container():
    with st.form("Individual Search"):
        mcode_col, start_col, end_col = st.columns(3)
        selected_mcode = mcode_col.text_input(
            "Input M - Code",
            placeholder="7 - digits",
            help="Enter a valid 7-digit M-Code supplied by the OE",
        )
        start_date = start_col.date_input("Start Date", value=lastyear_first_day)
        end_date = end_col.date_input("End Date", value=today)
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.min.time())

        btn_individual = st.form_submit_button("Run")
        if btn_individual:
            if selected_mcode and start_date and end_date:
                selected_mcode = selected_mcode
                start_date = start_date
                end_date = end_date
            else:
                # 입력 정보가 부족할 경우 사용자에게 알림
                st.warning("Please enter valid information in all fields.")

# m_code = '1024247'
m_code = "1024247"
start_date = "2022-01-01"
end_date = "2025-05-19"

# 데이터 로드
oe_app = get_client("snowflake").execute(q_hope.oe_app(m_code))
oe_app.columns = oe_app.columns.str.upper()

q_issue = get_client("snowflake").execute(q_quality_issue.query_quality_issue())
q_issue.columns = q_issue.columns.str.upper()
q_issue = q_issue[q_issue["M_CODE"] == m_code]
q_issue["SUBJECT"] = (
    q_issue["TYPE"] + " - " + q_issue["CAT"] + " - " + q_issue["SUB_CAT"]
)
q_issue["CATEGORY"] = "Quality Issue"
q_issue = q_issue[["CATEGORY", "SUBJECT", "REG_DATE", "SEQ"]]
q_issue = q_issue.rename(columns={"SEQ": "URL"})


chg_4m = get_client("snowflake").execute(q_4m_change.query_4m_change())
chg_4m.columns = chg_4m.columns.str.upper()
chg_4m = chg_4m[chg_4m["M_CODE"] == m_code]
chg_4m["CATEGORY"] = "4M Change"
chg_4m = chg_4m[["CATEGORY", "SUBJECT", "REG_DATE", "URL"]]

audit = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
audit.columns = audit.columns.str.upper()
audit = audit[audit["M_CODE"] == m_code]
audit["CATEGORY"] = "Audit"
audit = audit[["CATEGORY", "SUBJECT", "START_DT", "URL"]]
audit = audit.rename(columns={"START_DT": "REG_DATE"})

cqms_data = pd.concat([q_issue, chg_4m, audit])

# REG_DATE 컬럼이 datetime 타입인지 확인하고 변환
if not pd.api.types.is_datetime64_any_dtype(cqms_data["REG_DATE"]):
    cqms_data["REG_DATE"] = pd.to_datetime(cqms_data["REG_DATE"], errors="coerce")

# 날짜 형식 변환
cqms_data["REG_DATE"] = cqms_data["REG_DATE"].dt.strftime("%Y-%m-%d")
cqms_data = cqms_data.sort_values(by="REG_DATE", ascending=False)
cqms_data["CATEGORY"] = pd.Categorical(
    cqms_data["CATEGORY"],
    categories=["Quality Issue", "4M Change", "Audit"],
    ordered=True,
)

st.empty()
metric_col = st.columns(5, vertical_alignment="center")
metric_col[0].title("CQMS Events")
stats_data = cqms_data if "cqms_data" in locals() and len(cqms_data) > 0 else cqms_data

with metric_col[1]:
    total_events = len(stats_data)
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="font-size: 1rem; color: #666666; margin-bottom: 0.2rem;">Total Events</div>
            <div style="font-size: 3rem; font-weight: bold; color: #666666;">{total_events}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric_col[2]:
    quality_issues = len(stats_data[stats_data["CATEGORY"] == "Quality Issue"])
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="font-size: 1rem; color: #666666; margin-bottom: 0.2rem;">Quality Issues</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: #000000;">{quality_issues}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric_col[3]:
    m_changes = len(stats_data[stats_data["CATEGORY"] == "4M Change"])
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="font-size: 1rem; color: #666666; margin-bottom: 0.2rem;">4M Changes</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: #000000;">{m_changes}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric_col[4]:
    audits = len(stats_data[stats_data["CATEGORY"] == "Audit"])
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="font-size: 1rem; color: #666666; margin-bottom: 0.2rem;">Audits</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: #000000;">{audits}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if len(cqms_data) > 0:
    event_counts = stats_data["CATEGORY"].value_counts()

    cqms_event_col = st.columns([1, 3.5], vertical_alignment="center")
    with cqms_event_col[0]:
        # 파이 차트 생성
        trace = go.Pie(
            labels=event_counts.index,
            values=event_counts.values,
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
        st.plotly_chart(fig, use_container_width=True, key="event_distribution")

    with cqms_event_col[1]:
        # Gantt 차트 생성
        gantt_fig = create_gantt_timeline_chart(cqms_data)
        st.plotly_chart(gantt_fig, use_container_width=True, key="gantt_timeline")

else:
    st.warning(
        "No events found for the selected filters. Please adjust your filter criteria."
    )

with st.expander("CQMS Events Data(Table)"):
    st.dataframe(cqms_data, use_container_width=True, hide_index=True)

st.subheader("OE Application")
column_config = {
    "M_CODE": st.column_config.TextColumn(label="M-CODE"),
    "VEHICLE MODEL(GLOBAL)": st.column_config.TextColumn(label="Veh. Model (Global)"),
    "VEHICLE MODEL(LOCAL)": st.column_config.TextColumn(label="Veh. Model (Local)"),
}
st.dataframe(
    oe_app,
    use_container_width=True,
    hide_index=True,
    column_config=column_config,
)


query = """
SELECT * FROM sellin_monthly_agg WHERE M_CODE = '1024247'
"""
test = get_client("sqlite").execute(query)
test = test.sort_values(by=["YYYY", "MM"]).reset_index(drop=True)
test["YYYY_MM"] = test["YYYY"].astype(str) + "-" + test["MM"].astype(str).str.zfill(2)

trace = go.Scatter(
    x=test["YYYY_MM"],
    y=test["SUPP_QTY"],
    name="Supply",
    fill="tonexty",  # 영역 채우기 추가
    marker=dict(color=config_plotly.ORANGE_CLR),
)
layout = go.Layout(
    title="Supply Trend",
    xaxis_title="Month",
    yaxis_title="Quantity",
    yaxis=dict(range=[0, test["SUPP_QTY"].max() * 1.1]),
    xaxis=dict(
        type="category",
        categoryorder="category ascending",
        tickmode="array",
        tickvals=test["YYYY_MM"].tolist(),
        ticktext=test["YYYY_MM"].tolist(),
        tickangle=45,  # 틱 라벨 회전
        rangeslider=dict(visible=False),
    ),
)
fig = go.Figure(data=[trace], layout=layout)
st.plotly_chart(fig)

hgws = get_client("snowflake").execute(
    q_hgws.query_return_individual(
        mcode=m_code, start_date=start_date, end_date=end_date
    )
)
hgws.columns = hgws.columns.str.upper()
hgws = hgws.sort_values(by="RETURN CNT", ascending=False)


st.subheader("HGWS")

trace = go.Bar(
    x=hgws["RETURN CNT"],
    y=hgws["REASON DESCRIPTION"],
    text=hgws["RETURN CNT"],
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
        range=[0, hgws["RETURN CNT"].max() * 1.1],
    ),
    yaxis=dict(
        autorange="reversed",
        categoryorder="array",
    ),
)
fig = go.Figure(data=[trace], layout=layout)
st.plotly_chart(fig)


from _02_preprocessing.GMES import df_production, df_ncf

from _03_visualization._08_ADMIN import viz_oeassessment_result_viewer

df_production = df_production.get_daily_production_df(
    start_date=start_date, end_date=end_date, mcode=m_code
)

df_ncf = df_ncf.get_ncf_by_dft_cd(
    start_date=start_date, end_date=end_date, mcode=m_code
)
df_ncf = df_ncf.sort_values(by="NCF", ascending=False)
df_ncf = df_ncf.reset_index(drop=True)


st.subheader("Production")
st.plotly_chart(viz_oeassessment_result_viewer.draw_barplot_production(df_production))


st.subheader("NCF by DFT Code")
st.dataframe(df_ncf, use_container_width=True, hide_index=True)

st.subheader("NCF")
st.plotly_chart(viz_oeassessment_result_viewer.draw_barplot_ncf(df_ncf))
