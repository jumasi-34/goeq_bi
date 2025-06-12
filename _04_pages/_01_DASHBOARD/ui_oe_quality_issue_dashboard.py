"""
Global OE Quality KPI 대시보드

이 대시보드는 전 세계 OE 품질 이슈를 모니터링하고 분석하기 위한 KPI 대시보드입니다.
주요 기능:
- 연도별 품질 이슈 추이 분석
- 공장별 월간/연간 품질 이슈 현황
- 글로벌 수준의 월간/연간 품질 이슈 통계
- GOEQ(Global OE Quality) 지표 분석
- OE 애플리케이션 데이터 연동

사용된 데이터:
- 품질 이슈 데이터 (df_quality_issue)
- OE 애플리케이션 데이터 (df_oeapp)
"""

# 표준 라이브러리
import sys
import importlib

# 서드파티 라이브러리
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 프로젝트 경로 설정
sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

# 프로젝트 모듈
from _05_commons import config, helper
from _02_preprocessing.CQMS import df_quality_issue as pd_df
from _02_preprocessing.HOPE import df_oeapp
from _03_visualization._01_DASHBOARD import viz_oe_quality_issue_dashboard as viz
from _03_visualization import config_plotly

# 개발 모드 시 모듈 리로드
if config.DEV_MODE:
    importlib.reload(config)
    importlib.reload(pd_df)


# 데이터 로드 함수
def load_data(selected_year):
    """선택된 연도에 대한 모든 데이터를 로드합니다."""
    return {
        "raw_3_years": pd_df.load_quality_issues_for_3_years(selected_year),
        "plant_monthly": pd_df.aggregate_oeqi_by_plant_monthly(selected_year),
        "plant_yearly": pd_df.aggregate_oeqi_by_plant_yearly(selected_year),
        "global_monthly": pd_df.aggregate_oeqi_by_global_monthly(selected_year),
        "global_yearly": pd_df.aggregate_oeqi_by_global_yearly(selected_year),
        "goeq_monthly": pd_df.aggregate_oeqi_by_goeq_monthly(selected_year),
        "goeq_yearly": pd_df.aggregate_oeqi_by_goeq_yearly(selected_year),
        "goeq_yearly_pre": pd_df.aggregate_oeqi_by_goeq_yearly(selected_year - 1),
        "oeapp": df_oeapp.load_oeapp_df(),
        "oe_sku": df_oeapp.oe_sku(),
    }


def render_global_tab(data, selected_year):
    """GLOBAL 탭 렌더링"""
    # 1. Global OE Quality Index 섹션
    st.subheader(
        "Global OE Quality Index",
        help=(
            "**Note:** \\\nOEQI and OE supply quantity data are available\\\n"
            "**starting from the year 2023**.\\\n"
            "Please keep this in mind when analyzing historical trends."
        ),
    )

    # 1.1 OEQI 트렌드 차트
    cols = st.columns([25, 45, 30])
    cols[0].plotly_chart(
        viz.draw_three_years_oeqi(data["global_yearly"]), use_container_width=True
    )
    cols[1].plotly_chart(
        viz.draw_monthly_oeqi_trend(data["global_monthly"], selected_year),
        use_container_width=True,
    )
    cols[2].plotly_chart(
        viz.draw_pie_issue_count_by_oem(data["raw_3_years"], selected_year)
    )

    # 1.2 이슈 카운트 트렌드 차트
    cols = st.columns([25, 45, 30])
    cols[0].plotly_chart(
        viz.draw_three_years_issue_count(data["global_yearly"]),
        use_container_width=True,
    )
    cols[1].plotly_chart(
        viz.draw_monthly_issue_count_trend(data["global_monthly"], selected_year),
        use_container_width=True,
    )
    cols[2].plotly_chart(
        viz.draw_pie_issue_count_by_market(data["raw_3_years"], selected_year)
    )

    # 2. Plant별 품질 지표 섹션
    st.subheader("Quality metrics by Plant")

    cols = st.columns(4)
    cols[0].plotly_chart(viz.draw_sku_by_plant(data["oe_sku"]))
    cols[1].plotly_chart(viz.draw_supply_quantity_by_plant(data["plant_yearly"]))
    cols[2].plotly_chart(viz.draw_issue_count_by_plant(data["plant_yearly"]))
    cols[3].plotly_chart(viz.draw_oeqi_by_plant(data["plant_yearly"]))

    # 3. 이슈 타입 분류 섹션
    st.subheader("Categorize quality issues by type")
    cols = st.columns([5, 2, 2])
    cols[0].plotly_chart(
        viz.draw_issue_type_distribution(data["raw_3_years"], selected_year)
    )
    pies = viz.draw_pie_for_top_issue_types(data["raw_3_years"], selected_year)
    cols[1].plotly_chart(pies[0], use_container_width=True)
    cols[1].plotly_chart(pies[2], use_container_width=True)
    cols[2].plotly_chart(pies[1], use_container_width=True)
    cols[2].plotly_chart(pies[3], use_container_width=True)

    # 4. MTTC Index 섹션
    mttc_help = """
MTTC (Mean Time To Closure) represents the average number of business days it takes to close a quality issue.

This metric is calculated by summing up several work phases, including:
- Occurrence to Registration
- Registration to Return (only if the issue is returned)
- Return or Registration to Countermeasure
- Countermeasure to 8D Completion

The system uses business days (excluding weekends) based on actual dates provided in the report.

If certain dates (e.g., completion) are missing, the calculation assumes today's date as the endpoint.
This ensures ongoing issues are also reflected in the MTTC calculation.

A lower MTTC indicates faster resolution and better responsiveness to quality issues.
"""
    st.subheader("MTTC Index", help=mttc_help)

    # 4.1 MTTC 데이터 준비
    df_mttc = data["global_yearly"][data["global_yearly"]["YYYY"] == selected_year]
    df_mttc = (
        df_mttc.groupby("YYYY")[["REG_PRD", "RTN_PRD", "CTM_PRD", "COMP_PRD", "MTTC"]]
        .mean()
        .reset_index()
    )
    cols = st.columns(3)
    cols[0].plotly_chart(
        viz.draw_three_years_mttc(data["global_yearly"]),
        use_container_width=True,
        key="MTTC_BAR",
    )
    cols[1].plotly_chart(
        viz.draw_mttc_global_indicator(df_mttc), use_container_width=True
    )
    cols[2].plotly_chart(
        viz.draw_mttc_by_plant(data["plant_yearly"]), use_container_width=True
    )

    # 4.3 MTTC 상세 지표
    cols = st.columns(4)
    cols[0].plotly_chart(
        viz.draw_mttc_reg_global_indicator(df_mttc), use_container_width=True
    )
    cols[1].plotly_chart(
        viz.draw_mttc_rtn_global_indicator(df_mttc), use_container_width=True
    )
    cols[2].plotly_chart(
        viz.draw_mttc_countermeasure_global_indicator(df_mttc), use_container_width=True
    )
    cols[3].plotly_chart(
        viz.draw_mttc_8d_global_indicator(df_mttc), use_container_width=True
    )


# 공통 컬럼 설정 정의
COMMON_COLUMN_CONFIG = {
    # Basic Information
    "OEQ GROUP": st.column_config.TextColumn("OEQ GROUP", help="OEQ GROUP"),
    "PLANT": st.column_config.TextColumn("Plant", help="Plant code"),
    "OEM": st.column_config.TextColumn("OEM", help="OEM"),
    "VEH": st.column_config.TextColumn("Vehicle", help="Vehicle model"),
    "PJT": st.column_config.TextColumn("Project", help="Project code"),
    # Date Information
    "OCC_DATE": st.column_config.DateColumn(
        "Occurrence Date", format="YYYY-MM-DD", help="Quality issue occurrence date"
    ),
    "REG_DATE": st.column_config.DateColumn(
        "Registration Date", format="YYYY-MM-DD", help="Quality issue registration date"
    ),
    "RTN_DATE": st.column_config.DateColumn(
        "Return Date", format="YYYY-MM-DD", help="Quality issue return date"
    ),
    "CTM_DATE": st.column_config.DateColumn(
        "Countermeasure Date",
        format="YYYY-MM-DD",
        help="Countermeasure implementation date",
    ),
    "COMP_DATE": st.column_config.DateColumn(
        "Completion Date", format="YYYY-MM-DD", help="8D report completion date"
    ),
    # Status Information
    "STATUS": st.column_config.TextColumn(
        "Status", help="Current quality issue status"
    ),
    # Classification Information
    "LOCATION": st.column_config.TextColumn("Location", help="Location"),
    "MARKET": st.column_config.TextColumn("Market", help="Market"),
    "M_CODE": st.column_config.TextColumn("M Code", help="M Code"),
    "PNL_NM": st.column_config.TextColumn("Personnel Name", help="Panel Name"),
    "TYPE": st.column_config.TextColumn("Type", help="Type"),
    "CAT": st.column_config.TextColumn("Category", help="Category"),
    "SUB_CAT": st.column_config.TextColumn("Sub Category", help="Sub Category"),
    # Period Information
    "REG_PRD": st.column_config.NumberColumn(
        "Registration Period", help="Registration period in days", format="%.0f"
    ),
    "RTN_PRD": st.column_config.NumberColumn(
        "Return Period", help="Return period in days", format="%.0f"
    ),
    "CTM_PRD": st.column_config.NumberColumn(
        "Countermeasure Period", help="Countermeasure period in days", format="%.0f"
    ),
    "COMP_PRD": st.column_config.NumberColumn(
        "Completion Period", help="8D report completion period in days", format="%.0f"
    ),
    "MTTC": st.column_config.NumberColumn(
        "MTTC", help="Total period in days", format="%.0f"
    ),
    # Other Information
    "URL": st.column_config.LinkColumn(
        "Link", help="Link to quality issue detail page", display_text="Link"
    ),
}

# 공통 컬럼 그룹 정의
COMMON_COLUMNS = {
    "Basic Info": ["OEQ GROUP", "PLANT", "OEM", "VEH", "PJT"],
    "Dates": ["OCC_DATE", "REG_DATE", "RTN_DATE", "CTM_DATE", "COMP_DATE"],
    "Status": ["STATUS"],
    "Classification": [
        "LOCATION",
        "MARKET",
        "M_CODE",
        "PNL_NM",
        "TYPE",
        "CAT",
        "SUB_CAT",
    ],
    "Periods": ["REG_PRD", "RTN_PRD", "CTM_PRD", "COMP_PRD", "MTTC"],
    "Others": ["URL"],
}


def render_plant_tab(data, selected_year):
    """PLANT 탭 렌더링"""
    # 1. 공장 선택
    selected_plt = st.selectbox("Plant Select", config.plant_codes[:-1], index=0)
    st.markdown("---")

    # 2. 주요 지표 표시
    cols = st.columns(4, gap="medium")

    # 2.1 프로젝트 현황
    with cols[0]:
        st.subheader("Projects")
        sub_cols = st.columns(2)

        df_plt_projects = data["oeapp"][data["oeapp"]["plant"] == selected_plt]

        # 데이터가 없는 경우 0으로 처리
        mass_prod_count = (
            df_plt_projects[df_plt_projects["Status"] == "Supplying"].shape[0]
            if not df_plt_projects.empty
            else 0
        )
        dev_count = (
            df_plt_projects[df_plt_projects["Status"] == "Developing"].shape[0]
            if not df_plt_projects.empty
            else 0
        )

        sub_cols[0].metric(
            "Mass Production",
            value=mass_prod_count,
        )
        sub_cols[1].metric(
            "Development",
            value=dev_count,
        )

    # 2.2 공급 현황
    with cols[1]:
        st.subheader("Supplies")
        supp_qty = (
            data["plant_yearly"]
            .loc[data["plant_yearly"]["PLANT"] == selected_plt, "SUPP_QTY"]
            .values[0]
        )
        st.metric(label="OE Supplies", value=helper.format_number(num=supp_qty))

    # 2.3 품질 이슈 현황
    with cols[2]:
        st.subheader("Quality Issue")
        sub_cols = st.columns(2)

        df_plt_issues = data["raw_3_years"][
            (data["raw_3_years"]["PLANT"] == selected_plt)
            & (data["raw_3_years"]["YYYY"] == selected_year)
        ]

        comp_cnt = df_plt_issues[df_plt_issues["STATUS"] == "Complete"].shape[0]
        on_going_cnt = df_plt_issues[df_plt_issues["STATUS"] == "On-going"].shape[0]

        sub_cols[0].metric(label="Complete", value=comp_cnt)
        sub_cols[1].metric(label="On-going", value=on_going_cnt)

    # 2.4 지표 현황
    with cols[3]:
        st.subheader("Index")
        sub_cols = st.columns(2)

        oeqi_val = (
            data["plant_yearly"]
            .loc[data["plant_yearly"]["PLANT"] == selected_plt, "OEQI"]
            .values[0]
        )
        mttc_val = (
            data["plant_yearly"]
            .loc[data["plant_yearly"]["PLANT"] == selected_plt, "MTTC"]
            .values[0]
        )
        mttc_val = 0 if pd.isna(mttc_val) else mttc_val

        sub_cols[0].metric(label="OEQI", value=f"{oeqi_val:.2f}")
        sub_cols[1].metric(label="MTTC", value=f"{mttc_val:.1f} days")

    st.markdown("---")

    # 3. 차트 표시
    cols = st.columns(2)

    # 3.1 비교 차트
    with cols[0]:
        st.plotly_chart(
            viz.draw_plant_view_oeqi_highlight(data["plant_yearly"], selected_plt),
            use_container_width=True,
        )
        st.plotly_chart(
            viz.draw_plant_view_issue_count_highlight(
                data["plant_yearly"], selected_plt
            ),
            use_container_width=True,
        )

    # 3.2 트렌드 차트
    with cols[1]:
        st.plotly_chart(
            viz.draw_plant_view_oeqi_index_trend(
                data["plant_monthly"], selected_year, selected_plt
            )
        )
        st.plotly_chart(
            viz.draw_plant_view_issue_count_index_trend(
                data["plant_monthly"], selected_year, selected_plt
            )
        )

    # 4. 품질 이슈 리스트
    st.subheader("Quality Issue List")
    df_plt_issues = data["raw_3_years"][
        (data["raw_3_years"]["YYYY"] == int(selected_year))
        & (data["raw_3_years"]["PLANT"] == selected_plt)
    ]

    # 컬럼 정의
    columns = COMMON_COLUMNS.copy()

    # 모든 컬럼을 하나의 리스트로 병합
    remain_col = [col for cols in columns.values() for col in cols]
    df_plt_issues = df_plt_issues[remain_col]
    df_plt_issues = df_plt_issues.sort_values(by="REG_DATE", ascending=False)

    st.dataframe(
        df_plt_issues,
        use_container_width=True,
        column_config=COMMON_COLUMN_CONFIG,
    )


def render_oeqg_tab(data, selected_year):
    """OEQG 탭 렌더링"""
    # 1. 월간 트렌드 차트
    cols = st.columns(2, gap="large")
    cols[0].plotly_chart(
        viz.draw_goeq_view_issue_count_monthly_trend(data["goeq_monthly"])
    )
    cols[1].plotly_chart(viz.draw_goeq_view_oeqi_monthly_trend(data["goeq_monthly"]))

    # 2. MTTC 관련 유틸리티 함수들
    def get_mttc_bar_trace(y_col):
        return go.Bar(
            x=data["goeq_yearly"]["OEQ GROUP"],
            y=data["goeq_yearly"][y_col],
            text=data["goeq_yearly"][y_col],
            texttemplate="%{text:.1f}",
            marker=dict(color=config_plotly.multi_color_lst[:4]),
        )

    def get_mttc_layout(height, title):
        return go.Layout(
            height=height,
            title=dict(text=title),
            yaxis=dict(
                range=[0, None],
                showgrid=False,
                showticklabels=False,
                zerolinewidth=2,
                zerolinecolor=config_plotly.GRAY_CLR,
            ),
            xaxis=dict(showgrid=False),
            margin=dict(l=70, r=70, t=70, b=70),
        )

    def draw_target_line(fig_local, target):
        fig_local.add_hline(
            y=target, line=dict(color=config_plotly.NEGATIVE_CLR, dash="dash")
        )

    # 3. MTTC 비교 차트
    cols = st.columns([2, 7], gap="large", vertical_alignment="center")
    cols[0].plotly_chart(
        viz.draw_three_years_mttc(data["global_yearly"]),
        use_container_width=True,
        key="MTTC_BAR_2",
    )
    cols[1].plotly_chart(
        viz.draw_goeq_view_mttc_compare(
            data["goeq_yearly_pre"],
            data["goeq_yearly"],
        )
    )

    # 4. MTTC 상세 지표 차트
    cols = st.columns(4, gap="large")

    # MTTC 지표별 설정
    mttc_metrics = {
        "REG_PRD": {"title": "Registration", "target": 2, "col_idx": 0},
        "RTN_PRD": {"title": "Return", "target": 7, "col_idx": 1},
        "CTM_PRD": {"title": "Countermeasure", "target": 5, "col_idx": 2},
        "COMP_PRD": {"title": "8D Report", "target": 2, "col_idx": 3},
    }

    # 각 지표별 차트 생성
    for metric, config in mttc_metrics.items():
        trace = get_mttc_bar_trace(metric)
        layout = get_mttc_layout(height=300, title=config["title"])
        fig = go.Figure(data=trace, layout=layout)
        draw_target_line(fig, target=config["target"])
        cols[config["col_idx"]].plotly_chart(fig, use_container_width=True)


def render_rawdata_tab(data, selected_year):
    """RAWDATA 탭 렌더링"""
    # 헤더 섹션
    st.subheader("Raw Data[Quality Issue]")
    st.write("Hover over columns to see detailed descriptions.")

    # 컬럼 정의
    columns = COMMON_COLUMNS.copy()

    # 모든 컬럼을 하나의 리스트로 병합
    remain_col = [col for cols in columns.values() for col in cols]

    # 데이터프레임 표시
    filtered_data = data["raw_3_years"][data["raw_3_years"]["YYYY"] == selected_year][
        remain_col
    ]
    st.dataframe(
        filtered_data,
        use_container_width=True,
        column_config=COMMON_COLUMN_CONFIG,
    )


# 연도 선택 라디오 버튼
this_year = config.this_year
year_selection_option = range(2023, this_year + 1)

selected_year = st.radio(
    label="Choose year?",
    key=max(year_selection_option),
    options=year_selection_option,
    horizontal=True,
    index=len(year_selection_option) - 1,
    label_visibility="collapsed",
)

# 데이터 로드
data = load_data(selected_year)

# 탭 생성
tabs = st.tabs(["GLOBAL", "PLANT", "OEQG", "RAWDATA"])

with tabs[0]:  # GLOBAL
    render_global_tab(data, selected_year)
with tabs[1]:  # PLANT
    render_plant_tab(data, selected_year)
with tabs[2]:  # OEQG
    render_oeqg_tab(data, selected_year)
with tabs[3]:  # RAWDATA
    render_rawdata_tab(data, selected_year)
