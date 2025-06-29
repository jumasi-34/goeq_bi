"""
OE Assessment 결과 조회 페이지

이 페이지는 OE Assessment 결과를 조회하고 표시하는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 사용자는 결과를 확인할 수 있습니다.

주요 기능:
- Assessment 결과 테이블 표시
- 생산량, NCF, UF, 중량, RR, CTL 데이터 시각화
- 선택된 모델 코드와 기간에 대한 종합적인 품질 분석

작성자: [작성자명]
최종 수정일: [날짜]
"""

# =============================================================================
# Import Libraries
# =============================================================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Database
from _00_database.db_client import get_client

# GMES Data Processing
from _02_preprocessing.GMES.df_ctl import (
    get_ctl_raw_individual_df,
    get_groupby_doc_ctl_df,
)
from _02_preprocessing.GMES.df_production import get_daily_production_df
from _02_preprocessing.GMES.df_ncf import get_ncf_monthly_df, get_ncf_by_dft_cd
from _02_preprocessing.GMES.df_uf import (
    calculate_uf_pass_rate_monthly,
    uf_standard,
    uf_individual,
)
from _02_preprocessing.GMES.df_rr import get_processed_raw_rr_data, get_rr_oe_list_df
from _02_preprocessing.GMES.df_weight import (
    get_groupby_weight_ym_df,
    get_weight_individual_df,
)

# Other System Data Processing
from _02_preprocessing.HGWS.df_hgws import get_hgws_df
from _02_preprocessing.CQMS.df_cqms_unified import get_cqms_unified_df
from _02_preprocessing.HOPE.df_oeapp import load_oeapp_df_by_mcode

# Visualization
from _03_visualization._08_ADMIN import viz_oeassessment_result_viewer as viz


# =============================================================================
# CSS Styles
# =============================================================================
def load_custom_css():
    """커스텀 CSS 스타일을 로드하여 UI 일관성을 향상시킵니다."""
    st.markdown(
        """
    <style>
    /* 전체 페이지 여백 조정 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 섹션 간격 조정 */
    .stMarkdown {
        margin-bottom: 1rem;
    }
    
    /* 데이터프레임 스타일링 */
    .stDataFrame {
        margin: 1rem 0;
    }
    
    /* 메트릭 카드 스타일링 */
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    
    /* 탭 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #1f77b4;
    }
    
    /* 차트 컨테이너 스타일링 */
    .stPlotlyChart {
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #ffffff;
    }
    
    /* 구분선 스타일링 */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e0e0e0;
    }
    
    /* 경고 메시지 스타일링 */
    .stAlert {
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    
    /* 정보 메시지 스타일링 */
    .stInfo {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 제목 스타일링 */
    h1, h2, h3, h4 {
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #1f2937;
    }
    
    /* 컬럼 간격 조정 */
    .row-widget.stHorizontal {
        gap: 1rem;
    }
    
    /* 컨테이너 패딩 */
    .stContainer {
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 카드 스타일링 */
    .card-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        border-left: 4px solid #1f77b4;
    }
    
    .card-container h3 {
        color: #1f2937;
        margin-bottom: 1rem;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .metric-card h4 {
        color: #1f2937;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 0.5rem 0;
    }
    
    .metric-value.quality-excellent {
        color: #059669;
    }
    
    .metric-value.quality-good {
        color: #2563eb;
    }
    
    .metric-value.quality-warning {
        color: #d97706;
    }
    
    .metric-value.quality-poor {
        color: #dc2626;
    }
    
    .metric-description {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f3f4f6;
    }
    
    .section-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: #1f77b4;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
    }
    
    .insight-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .insight-title {
        font-weight: 600;
        color: #92400e;
        margin-bottom: 0.5rem;
    }
    
    .insight-text {
        color: #78350f;
        font-size: 0.95rem;
    }
    
    .quality-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .quality-excellent {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .quality-good {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    
    .quality-warning {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    .quality-poor {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    .toggle-section {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 1rem 0;
        overflow: hidden;
    }
    
    .toggle-header {
        background: #f1f5f9;
        padding: 1rem;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .toggle-content {
        padding: 1rem;
        background: white;
    }
    
    .highlight-box {
        background: #e0e7ff;
        border: 1px solid #6366f1;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .highlight-title {
        font-weight: 600;
        color: #3730a3;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .highlight-text {
        color: #4338ca;
        font-size: 1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Utility Functions
# =============================================================================
def remove_outliers(group):
    """
    IQR 방법을 사용하여 그룹별 아웃라이어를 제거하는 함수

    Args:
        group (pd.DataFrame): 중량 데이터 그룹

    Returns:
        pd.DataFrame: 아웃라이어가 제거된 데이터프레임

    계산 방법:
        - Q1 (25% 분위수)와 Q3 (75% 분위수) 계산
        - IQR = Q3 - Q1
        - 하한 = Q1 - 1.5 * IQR
        - 상한 = Q3 + 1.5 * IQR
    """
    Q1 = group["MRM_WGT"].quantile(0.25)
    Q3 = group["MRM_WGT"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return group[(group["MRM_WGT"] >= lower_bound) & (group["MRM_WGT"] <= upper_bound)]


# =============================================================================
# Data Loading
# =============================================================================
def load_assessment_result():
    """Assessment 결과 데이터를 SQLite 데이터베이스에서 로드"""
    return get_client("sqlite").execute("SELECT * FROM mass_assess_result")


def load_sellin_data(mcode):
    """판매 데이터를 SQLite 데이터베이스에서 로드"""
    return get_client("sqlite").execute(
        f"SELECT * FROM sellin_monthly_agg WHERE M_CODE = '{mcode}'"
    )


# =============================================================================
# 데이터 처리 함수들
# =============================================================================
def calculate_quality_indices(result_df):
    """
    Assessment 결과에 품질 지수들을 계산하여 추가합니다.

    계산되는 지수들:
    - NCF Index: 부적합률 기반 지수 (0-100)
    - UF Index: Uniformity 합격률 기반 지수 (0-100)
    - GT Weight Index: 중량 합격률 기반 지수 (0-100)
    - RR Index: Reliability 합격률 기반 지수 (0-100)
    - CTL Index: Control 합격률 기반 지수 (0-100)

    Args:
        result_df (pd.DataFrame): 원본 Assessment 결과 데이터프레임
            - ncf_qty: 부적합 수량
            - total_qty: 총 수량
            - pass_rate: UF 합격률
            - wt_pass_qty: 중량 합격 수량
            - wt_ins_qty: 중량 검사 수량
            - rr_pass_rate_pdf: RR 합격률
            - ctl_pass_rate: CTL 합격률

    Returns:
        pd.DataFrame: 품질 지수가 추가된 데이터프레임
            - ncf_rate: NCF 비율 (ppm)
            - ncf_idx: NCF 지수 (0-100)
            - uf_idx: UF 지수 (0-100)
            - gt_rate: GT Weight 비율
            - gt_idx: GT Weight 지수 (0-100)
            - rr_idx: RR 지수 (0-100)
            - ctl_idx: CTL 지수 (0-100)
    """

    def calculate_index(rate, config, reverse=False):
        """
        품질 지수를 계산하는 헬퍼 함수

        Args:
            rate (pd.Series): 계산할 비율 데이터
            config (dict): 지수 계산 설정 (max_rate, min_rate)
            reverse (bool): 역방향 계산 여부 (높은 값이 좋은 경우 False, 낮은 값이 좋은 경우 True)

        Returns:
            pd.Series: 계산된 지수 (0-100)
        """
        max_rate = config["max_rate"]
        min_rate = config["min_rate"]

        if reverse:
            # 낮은 값이 좋은 경우 (NCF)
            index = ((max_rate - rate) / (max_rate - min_rate) * 100).clip(0, 100)
        else:
            # 높은 값이 좋은 경우 (UF, GT Weight, RR, CTL)
            index = ((rate - min_rate) / (max_rate - min_rate) * 100).clip(0, 100)

        return index.round(1)

    # NCF 지수 계산
    result_df["ncf_rate"] = (
        result_df["ncf_qty"]
        / result_df["total_qty"]
        * QUALITY_INDICES_CONFIG["ncf"]["multiplier"]
    )
    result_df["ncf_idx"] = calculate_index(
        result_df["ncf_rate"], QUALITY_INDICES_CONFIG["ncf"], reverse=True
    )

    # UF 지수 계산
    result_df["uf_idx"] = calculate_index(
        result_df["pass_rate"], QUALITY_INDICES_CONFIG["uf"]
    )

    # GT Weight 지수 계산
    result_df["gt_rate"] = result_df["wt_pass_qty"] / result_df["wt_ins_qty"]
    result_df["gt_idx"] = calculate_index(
        result_df["gt_rate"], QUALITY_INDICES_CONFIG["gt_weight"]
    )

    # RR 지수 계산
    result_df["rr_idx"] = calculate_index(
        result_df["rr_pass_rate_pdf"], QUALITY_INDICES_CONFIG["rr"]
    )

    # CTL 지수 계산
    result_df["ctl_idx"] = calculate_index(
        result_df["ctl_pass_rate"], QUALITY_INDICES_CONFIG["ctl"]
    )

    return result_df


def format_date_string(date_str):
    """
    날짜 문자열을 YYYY-MM-DD 형식으로 변환

    Args:
        date_str (str): YYYYMMDD 형식의 날짜 문자열

    Returns:
        str: YYYY-MM-DD 형식의 날짜 문자열
    """
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"


def get_selected_data_info(result_df, selected_row_index):
    """
    선택된 행의 데이터 정보를 추출

    Args:
        result_df (pd.DataFrame): Assessment 결과 데이터프레임
        selected_row_index (int): 선택된 행 인덱스

    Returns:
        dict: 선택된 데이터 정보
    """
    selected_row = result_df.iloc[selected_row_index]
    return {
        "mcode": selected_row["m_code"],
        "start_date": selected_row["min_date"],
        "end_date": selected_row["max_date"],
        "formatted_start_date": format_date_string(selected_row["min_date"]),
        "formatted_end_date": format_date_string(selected_row["max_date"]),
    }


# =============================================================================
# UI 섹션 함수들
# =============================================================================
def render_overview_tab(result_df):
    """Overview 탭 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    # 요약 정보 섹션
    st.markdown("### 📊 Assessment Results Overview")

    # 전체 통계 카드
    stats_cols = st.columns(4)
    with stats_cols[0]:
        st.metric(
            label="Total Models",
            value=len(result_df),
            help="Total number of models in assessment",
        )

    with stats_cols[1]:
        avg_ncf = result_df["ncf_qty"].sum() / result_df["total_qty"].sum() * 1000000
        st.metric(
            label="Average NCF Rate",
            value=f"{avg_ncf:,.0f} ppm",
            help="Average NCF rate across all models",
        )

    with stats_cols[2]:
        avg_uf = result_df["pass_rate"].mean() * 100
        st.metric(
            label="Average UF Pass Rate",
            value=f"{avg_uf:.1f}%",
            help="Average Uniformity pass rate across all models",
        )

    with stats_cols[3]:
        avg_weight = (
            result_df["wt_pass_qty"].sum() / result_df["wt_ins_qty"].sum()
        ) * 100
        st.metric(
            label="Average Weight Pass Rate",
            value=f"{avg_weight:.1f}%",
            help="Average Weight pass rate across all models",
        )

    # 구분선
    st.markdown("---")

    # 데이터프레임 섹션
    st.markdown("### 📋 Detailed Results Table")
    st.markdown(
        "Select a row from the table below to view detailed analysis in the Detail tab."
    )

    # 데이터프레임을 컨테이너로 감싸서 스타일링
    with st.container():
        st.dataframe(result_df, use_container_width=True, hide_index=True, height=400)

    # 구분선
    st.markdown("---")

    # 추가 정보
    st.markdown("### ℹ️ How to Use")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **📋 Overview Tab:**
        - View summary statistics
        - Browse all assessment results
        - Get quick insights into overall performance
        """
        )

    with col2:
        st.markdown(
            """
        **🔍 Detail Tab:**
        - Select a specific model row
        - View detailed quality analysis
        - Explore charts and trends
        """
        )


def render_production_section(
    selected_mcode, selected_start_date, selected_end_date, result_df
):
    """생산량 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    production_df = get_daily_production_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
    total_production = result_df[result_df["m_code"] == selected_mcode][
        "total_qty"
    ].values[0]

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">Production Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total Production</h4>
                <div class="metric-value">{total_production:,.0f}</div>
                <div class="metric-description">Total production quantity during the assessment period</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        avg_daily = (
            total_production / len(production_df) if len(production_df) > 0 else 0
        )
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Average Daily Production</h4>
                <div class="metric-value">{avg_daily:,.0f}</div>
                <div class="metric-description">Average daily production quantity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        # max_daily = production_df["PROD_QTY"].max() if len(production_df) > 0 else 0
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Peak Daily Production</h4>
                <div class="metric-value"></div>
                <div class="metric-description">Highest daily production quantity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📈</div>
                <div class="section-title">Daily Production Trend</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        viz.draw_barplot_production(production_df), use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_ncf_section(
    selected_mcode, selected_start_date, selected_end_date, result_df
):
    """NCF 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    ncf_df = get_ncf_monthly_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
    ncf_ppm = result_df[result_df["m_code"] == selected_mcode]["ncf_rate"].values[0]

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">🔴</div>
                <div class="section-title">NCF Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        ncf_class = get_quality_indicator_class(ncf_ppm, "ncf")
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>NCF Rate</h4>
                <div class="metric-value {ncf_class}">{ncf_ppm:,.0f} ppm</div>
                <div class="metric-description">Non-Conformity Factor rate in parts per million</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        ncf_qty = result_df[result_df["m_code"] == selected_mcode]["ncf_qty"].values[0]
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total NCF Quantity</h4>
                <div class="metric-value">{ncf_qty:,.0f}</div>
                <div class="metric-description">Total non-conforming units</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        total_qty = result_df[result_df["m_code"] == selected_mcode][
            "total_qty"
        ].values[0]
        ncf_percentage = (ncf_qty / total_qty) * 100
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>NCF Percentage</h4>
                <div class="metric-value">{ncf_percentage:.3f}%</div>
                <div class="metric-description">NCF as percentage of total production</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">NCF Analysis Charts</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    ncf_cols = st.columns(2)

    with ncf_cols[0]:
        st.markdown("**Monthly NCF Trend**")
        st.plotly_chart(viz.draw_barplot_ncf(ncf_df), use_container_width=True)

    ncf_by_dft_cd_df = get_ncf_by_dft_cd(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    with ncf_cols[1]:
        st.markdown("**NCF by Defect Code (Pareto)**")
        st.plotly_chart(
            viz.draw_barplot_ncf_pareto(ncf_by_dft_cd_df), use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_uf_section(
    selected_mcode, selected_start_date, selected_end_date, result_df
):
    """UF 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    uf_pass_rate = (
        result_df[result_df["m_code"] == selected_mcode]["pass_rate"].values[0] * 100
    )

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📏</div>
                <div class="section-title">Uniformity Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        uf_class = get_quality_indicator_class(uf_pass_rate, "rate")
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Uniformity Pass Rate</h4>
                <div class="metric-value {uf_class}">{uf_pass_rate:.1f}%</div>
                <div class="metric-description">Uniformity test pass rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        fail_rate = 100 - uf_pass_rate
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Uniformity Fail Rate</h4>
                <div class="metric-value">{fail_rate:.1f}%</div>
                <div class="metric-description">Uniformity test fail rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        total_tests = result_df[result_df["m_code"] == selected_mcode][
            "total_qty"
        ].values[0]
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total Tests</h4>
                <div class="metric-value">{total_tests:,.0f}</div>
                <div class="metric-description">Total uniformity tests conducted</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">Uniformity Analysis Charts</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    uf_cols = st.columns(2)

    uf_pass_rate_df = calculate_uf_pass_rate_monthly(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    with uf_cols[0]:
        st.markdown("**Monthly Uniformity Pass Rate**")
        st.plotly_chart(viz.draw_barplot_uf(uf_pass_rate_df), use_container_width=True)

    uf_standard_df = uf_standard(mcode=selected_mcode)
    uf_individual_df = uf_individual(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    with uf_cols[1]:
        st.markdown("**Individual Uniformity vs Standard**")
        st.plotly_chart(
            viz.draw_barplot_uf_individual(uf_individual_df, uf_standard_df),
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_weight_section(
    selected_mcode, selected_start_date, selected_end_date, result_df
):
    """중량 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    wt_pass_rate = (
        result_df[result_df["m_code"] == selected_mcode]["gt_rate"].values[0] * 100
    )

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">⚖️</div>
                <div class="section-title">Weight Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        weight_class = get_quality_indicator_class(wt_pass_rate, "rate")
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Weight Pass Rate</h4>
                <div class="metric-value {weight_class}">{wt_pass_rate:.1f}%</div>
                <div class="metric-description">GT Weight test pass rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        wt_pass_qty = result_df[result_df["m_code"] == selected_mcode][
            "wt_pass_qty"
        ].values[0]
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Weight Pass Quantity</h4>
                <div class="metric-value">{wt_pass_qty:,.0f}</div>
                <div class="metric-description">Number of units passing weight test</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        wt_ins_qty = result_df[result_df["m_code"] == selected_mcode][
            "wt_ins_qty"
        ].values[0]
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Weight Inspection Quantity</h4>
                <div class="metric-value">{wt_ins_qty:,.0f}</div>
                <div class="metric-description">Total units inspected for weight</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">Weight Analysis Charts</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    wt_col = st.columns(2)

    groupby_weight_ym_df = get_groupby_weight_ym_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    with wt_col[0]:
        st.markdown("**Monthly Weight Distribution**")
        st.plotly_chart(
            viz.draw_weight_distribution(groupby_weight_ym_df), use_container_width=True
        )

    wt_individual_df = get_weight_individual_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    wt_individual_df_no_outliers = (
        wt_individual_df.groupby("INS_DATE_YM")
        .apply(remove_outliers)
        .reset_index(drop=True)
    )

    wt_spec = wt_individual_df["STD_WGT"].iloc[-1]

    with wt_col[1]:
        st.markdown("**Individual Weight Distribution (Outliers Removed)**")
        st.plotly_chart(
            viz.draw_weight_distribution_individual(
                wt_individual_df_no_outliers, wt_spec
            ),
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_rr_section(
    selected_mcode, formatted_start_date, formatted_end_date, result_df
):
    """RR 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    rr_pass_rate = (
        result_df[result_df["m_code"] == selected_mcode]["rr_pass_rate_pdf"].values[0]
        * 100
    )

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">🔄</div>
                <div class="section-title">Reliability Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        rr_class = get_quality_indicator_class(rr_pass_rate, "rate")
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>RR Pass Rate</h4>
                <div class="metric-value {rr_class}">{rr_pass_rate:.1f}%</div>
                <div class="metric-description">Reliability test pass rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        rr_fail_rate = 100 - rr_pass_rate
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>RR Fail Rate</h4>
                <div class="metric-value">{rr_fail_rate:.1f}%</div>
                <div class="metric-description">Reliability test fail rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Reliability Status</h4>
                <div class="metric-value {rr_class}">{'Pass' if rr_pass_rate >= 95 else 'Warning' if rr_pass_rate >= 80 else 'Fail'}</div>
                <div class="metric-description">Overall reliability assessment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">Reliability Analysis Charts</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    rr_col = st.columns(2)

    rr_df = get_processed_raw_rr_data(
        mcode=selected_mcode,
        start_date=formatted_start_date,
        end_date=formatted_end_date,
    )
    rr_df = rr_df.sort_values(by="SMPL_DATE").reset_index(drop=True)

    rr_standard_df = get_rr_oe_list_df()
    rr_standard_df = rr_standard_df[rr_standard_df["M_CODE"] == selected_mcode]

    if len(rr_df) > 0:
        with rr_col[0]:
            st.markdown("**RR Trend Over Time**")
            st.plotly_chart(
                viz.draw_rr_trend(rr_df, rr_standard_df), use_container_width=True
            )

        with rr_col[1]:
            st.markdown("**RR Distribution**")
            st.plotly_chart(
                viz.draw_rr_distribution(rr_df, rr_standard_df),
                use_container_width=True,
            )
    else:
        st.warning("No RR data found for the selected period")

    st.markdown("</div>", unsafe_allow_html=True)


def render_ctl_section(
    selected_mcode, selected_start_date, selected_end_date, result_df
):
    """CTL 분석 섹션 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    ctl_pass_rate = (
        result_df[result_df["m_code"] == selected_mcode]["ctl_pass_rate"].values[0]
        * 100
    )

    # KPI 카드 형태로 표시
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">🎯</div>
                <div class="section-title">Control Summary</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_col = st.columns(3)
    with kpi_col[0]:
        ctl_class = get_quality_indicator_class(ctl_pass_rate, "rate")
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>CTL Pass Rate</h4>
                <div class="metric-value {ctl_class}">{ctl_pass_rate:.1f}%</div>
                <div class="metric-description">Control test pass rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[1]:
        ctl_fail_rate = 100 - ctl_pass_rate
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>CTL Fail Rate</h4>
                <div class="metric-value">{ctl_fail_rate:.1f}%</div>
                <div class="metric-description">Control test fail rate percentage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col[2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Control Status</h4>
                <div class="metric-value {ctl_class}">{'Pass' if ctl_pass_rate >= 95 else 'Warning' if ctl_pass_rate >= 85 else 'Fail'}</div>
                <div class="metric-description">Overall control assessment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 차트 섹션
    st.markdown(
        """
        <div class="section-card">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div class="section-title">Control Analysis Charts</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    ctl_col = st.columns([1, 3])

    ctl_raw_data = get_ctl_raw_individual_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    if len(ctl_raw_data) > 0:
        grouped_ctl_df = get_groupby_doc_ctl_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        with ctl_col[0]:
            st.markdown("**CTL Trend**")
            st.plotly_chart(
                viz.draw_ctl_trend(grouped_ctl_df), use_container_width=True
            )

        with ctl_col[1]:
            st.markdown("**CTL Detailed Analysis**")
            st.plotly_chart(viz.draw_ctl_detail(ctl_raw_data), use_container_width=True)
    else:
        st.warning("No CTL data found for the selected period")

    st.markdown("</div>", unsafe_allow_html=True)


def get_quality_indicator_class(value, metric_type):
    """
    품질 지표에 따른 CSS 클래스를 반환합니다.

    Args:
        value (float): 품질 지표 값
        metric_type (str): 지표 타입 ('rate', 'ncf', 'index')

    Returns:
        str: CSS 클래스명
    """
    if metric_type == "rate":
        if value >= 95:
            return "quality-excellent"
        elif value >= 85:
            return "quality-good"
        elif value >= 70:
            return "quality-warning"
        else:
            return "quality-poor"
    elif metric_type == "ncf":
        if value <= 2000:
            return "quality-excellent"
        elif value <= 5000:
            return "quality-good"
        elif value <= 10000:
            return "quality-warning"
        else:
            return "quality-poor"
    elif metric_type == "index":
        if value >= 80:
            return "quality-excellent"
        elif value >= 60:
            return "quality-good"
        elif value >= 40:
            return "quality-warning"
        else:
            return "quality-poor"
    return "quality-good"


def render_quality_insights(result_df, selected_mcode):
    """
    선택된 모델의 품질 인사이트를 렌더링합니다.

    Args:
        result_df (pd.DataFrame): Assessment 결과 데이터프레임
        selected_mcode (str): 선택된 모델 코드
    """
    selected_data = result_df[result_df["m_code"] == selected_mcode].iloc[0]

    # 품질 지수 계산
    ncf_rate = selected_data["ncf_rate"]
    uf_pass_rate = selected_data["pass_rate"] * 100
    weight_pass_rate = selected_data["gt_rate"] * 100
    rr_pass_rate = selected_data["rr_pass_rate_pdf"] * 100
    ctl_pass_rate = selected_data["ctl_pass_rate"] * 100

    insights = []

    # NCF 인사이트
    if ncf_rate > 10000:
        insights.append(
            {
                "type": "warning",
                "title": "🔴 High NCF Rate Detected",
                "message": f"NCF rate of {ncf_rate:,.0f} ppm is significantly above target. Root cause analysis recommended.",
            }
        )
    elif ncf_rate > 5000:
        insights.append(
            {
                "type": "info",
                "title": "⚠️ Moderate NCF Rate",
                "message": f"NCF rate of {ncf_rate:,.0f} ppm requires attention and monitoring.",
            }
        )
    else:
        insights.append(
            {
                "type": "success",
                "title": "✅ Excellent NCF Performance",
                "message": f"NCF rate of {ncf_rate:,.0f} ppm is within acceptable range.",
            }
        )

    # UF 인사이트
    if uf_pass_rate < 80:
        insights.append(
            {
                "type": "warning",
                "title": "📏 Uniformity Issues",
                "message": f"Uniformity pass rate of {uf_pass_rate:.1f}% indicates potential process variation.",
            }
        )
    elif uf_pass_rate < 90:
        insights.append(
            {
                "type": "info",
                "title": "📏 Uniformity Monitoring",
                "message": f"Uniformity pass rate of {uf_pass_rate:.1f}% should be monitored closely.",
            }
        )
    else:
        insights.append(
            {
                "type": "success",
                "title": "📏 Good Uniformity",
                "message": f"Uniformity pass rate of {uf_pass_rate:.1f}% shows stable process control.",
            }
        )

    # Weight 인사이트
    if weight_pass_rate < 95:
        insights.append(
            {
                "type": "warning",
                "title": "⚖️ Weight Control Issues",
                "message": f"Weight pass rate of {weight_pass_rate:.1f}% suggests weight control problems.",
            }
        )
    else:
        insights.append(
            {
                "type": "success",
                "title": "⚖️ Excellent Weight Control",
                "message": f"Weight pass rate of {weight_pass_rate:.1f}% indicates good weight management.",
            }
        )

    # 종합 인사이트
    overall_score = (uf_pass_rate + weight_pass_rate + rr_pass_rate + ctl_pass_rate) / 4
    if overall_score >= 95:
        overall_message = "Overall quality performance is excellent across all metrics."
        overall_type = "success"
    elif overall_score >= 85:
        overall_message = (
            "Overall quality performance is good with some areas for improvement."
        )
        overall_type = "info"
    else:
        overall_message = "Overall quality performance requires immediate attention and improvement actions."
        overall_type = "warning"

    insights.append(
        {
            "type": overall_type,
            "title": "🎯 Overall Quality Assessment",
            "message": f"{overall_message} Average score: {overall_score:.1f}%",
        }
    )

    # 인사이트 렌더링
    st.markdown("### 💡 Quality Insights & Recommendations")

    for insight in insights:
        if insight["type"] == "success":
            bg_color = "#dcfce7"
            border_color = "#bbf7d0"
            text_color = "#166534"
        elif insight["type"] == "warning":
            bg_color = "#fee2e2"
            border_color = "#fecaca"
            text_color = "#991b1b"
        else:
            bg_color = "#dbeafe"
            border_color = "#bfdbfe"
            text_color = "#1e40af"

        st.markdown(
            f"""
            <div style="
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <div style="font-weight: 600; color: {text_color}; margin-bottom: 0.5rem;">
                    {insight['title']}
                </div>
                <div style="color: {text_color}; font-size: 0.95rem;">
                    {insight['message']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_card(title, value, unit="", description="", quality_class=""):
    """
    메트릭 카드를 렌더링합니다.

    Args:
        title (str): 메트릭 제목
        value (float): 메트릭 값
        unit (str): 단위
        description (str): 설명
        quality_class (str): 품질 클래스
    """
    st.markdown(
        f"""
        <div class="metric-card">
            <h4>{title}</h4>
            <div class="metric-value {quality_class}">{value:,.1f}{unit}</div>
            <div class="metric-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_detail_tab(result_df):
    """Detail 탭 렌더링"""
    st.title("OE Assessment Result Viewer")

    # 상단 여백 추가
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("Assessment Result")

    if "result_df" not in st.session_state:
        st.session_state["result_df"] = result_df

    # 품질 지수 계산
    result_df = calculate_quality_indices(result_df)

    # 데이터프레임 표시 - 컨테이너로 감싸서 패딩 추가
    with st.container():
        st.markdown("#### 📊 Assessment Results Table")
        assessment_result_df = st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True,
            key="event_df",
            on_select="rerun",
            selection_mode="single-row",
        )

    # 선택된 행 처리
    if assessment_result_df.selection.rows:
        selected_data = get_selected_data_info(
            result_df, assessment_result_df.selection.rows[0]
        )

        # 구분선 추가
        st.markdown("---")

        # 선택된 모델 정보를 카드 형태로 표시
        st.markdown(
            f"""
            <div class="card-container">
                <h3>📋 Model Information</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>Model Code:</strong><br>
                        <span style="font-size: 1.2rem; font-weight: bold;">{selected_data['mcode']}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>Start Date:</strong><br>
                        <span style="font-size: 1.2rem;">{selected_data['formatted_start_date']}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>End Date:</strong><br>
                        <span style="font-size: 1.2rem;">{selected_data['formatted_end_date']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 공급량 정보
        sell_in = load_sellin_data(selected_data["mcode"])
        total_supply = sell_in["SUPP_QTY"].sum()

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-title">📦 Supply Information</div>
                <div class="highlight-text">Total Supply: {total_supply:,.0f} units</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 품질 인사이트 섹션
        render_quality_insights(result_df, selected_data["mcode"])

        # 구분선 추가
        st.markdown("---")

        # 품질 지표 요약 카드
        selected_row = result_df[result_df["m_code"] == selected_data["mcode"]].iloc[0]

        st.markdown("### 📊 Quality Metrics Summary")

        metric_cols = st.columns(4)

        with metric_cols[0]:
            ncf_rate = selected_row["ncf_rate"]
            ncf_class = get_quality_indicator_class(ncf_rate, "ncf")
            render_metric_card(
                "NCF Rate", ncf_rate, " ppm", "Non-Conformity Factor rate", ncf_class
            )

        with metric_cols[1]:
            uf_rate = selected_row["pass_rate"] * 100
            uf_class = get_quality_indicator_class(uf_rate, "rate")
            render_metric_card(
                "UF Pass Rate", uf_rate, "%", "Uniformity test pass rate", uf_class
            )

        with metric_cols[2]:
            weight_rate = selected_row["gt_rate"] * 100
            weight_class = get_quality_indicator_class(weight_rate, "rate")
            render_metric_card(
                "Weight Pass Rate",
                weight_rate,
                "%",
                "GT Weight test pass rate",
                weight_class,
            )

        with metric_cols[3]:
            rr_rate = selected_row["rr_pass_rate_pdf"] * 100
            rr_class = get_quality_indicator_class(rr_rate, "rate")
            render_metric_card(
                "RR Pass Rate", rr_rate, "%", "Reliability test pass rate", rr_class
            )

        # 구분선 추가
        st.markdown("---")

        # 상세 분석 섹션을 아코디언 형태로 구성
        st.markdown("### 🔍 Detailed Analysis")

        # Production Analysis
        with st.expander("📊 Production Analysis", expanded=True):
            render_production_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

        # NCF Analysis
        with st.expander("🔴 NCF (Non-Conformity Factor) Analysis", expanded=False):
            render_ncf_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

        # Uniformity Analysis
        with st.expander("📏 Uniformity Analysis", expanded=False):
            render_uf_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

        # Weight Analysis
        with st.expander("⚖️ Weight Analysis", expanded=False):
            render_weight_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

        # Reliability Analysis
        with st.expander("🔄 Reliability (RR) Analysis", expanded=False):
            render_rr_section(
                selected_data["mcode"],
                selected_data["formatted_start_date"],
                selected_data["formatted_end_date"],
                result_df,
            )

        # Control Analysis
        with st.expander("🎯 Control (CTL) Analysis", expanded=False):
            render_ctl_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

        # 구분선 추가
        st.markdown("---")

        # 추가 정보 섹션
        st.markdown("### 📋 Additional Information")

        # OE Application 정보
        with st.expander("🔧 OE Application Data", expanded=False):
            oeapp_df = load_oeapp_df_by_mcode(m_code=selected_data["mcode"])

            if not oeapp_df.empty:
                st.dataframe(
                    oeapp_df, use_container_width=True, hide_index=True, height=200
                )
            else:
                st.info("No OE Application data available")

        # CQMS Event 정보
        with st.expander("⚠️ CQMS Events", expanded=False):
            cqms_unified_df = get_cqms_unified_df(m_code=selected_data["mcode"])

            if not cqms_unified_df.empty:
                st.dataframe(
                    cqms_unified_df,
                    use_container_width=True,
                    hide_index=True,
                    height=200,
                )
            else:
                st.info("No CQMS events found")

        # HGWS Event 정보
        with st.expander("🔍 HGWS Events", expanded=False):
            hgws_df = get_hgws_df(m_code=selected_data["mcode"])

            if not hgws_df.empty:
                st.dataframe(
                    hgws_df, use_container_width=True, hide_index=True, height=200
                )
            else:
                st.info("No HGWS events found")

    else:
        # 선택 안내 메시지를 더 눈에 띄게 표시
        st.markdown("---")
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
                border: 2px solid #6366f1;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                margin: 2rem 0;
            ">
                <h3 style="color: #3730a3; margin-bottom: 1rem;">🔍 Selection Required</h3>
                <p style="color: #4338ca; font-size: 1.1rem;">
                    Please select a row from the assessment result table above to view detailed analysis.
                </p>
                <p style="color: #6366f1; font-size: 0.9rem; margin-top: 1rem;">
                    Click on any row in the table to explore comprehensive quality metrics and insights.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_description_tab():
    """Description 탭 렌더링"""
    # 상단 여백
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📖 Assessment Methodology & Documentation")

    # 구분선
    st.markdown("---")

    try:
        with open("_07_docs/product_assessment.md", "r", encoding="utf-8") as file:
            markdown_content = file.read()

        # 마크다운 내용을 컨테이너로 감싸서 스타일링
        with st.container():
            st.markdown(markdown_content)

    except FileNotFoundError:
        st.error(
            "❌ **File Not Found:** `product_assessment.md` 파일을 찾을 수 없습니다."
        )
        st.markdown(
            """
        ### 📝 Expected Documentation Structure
        
        The documentation should include:
        - **Assessment Methodology**: How the OE assessment is conducted
        - **Quality Metrics**: Explanation of NCF, UF, Weight, RR, and CTL metrics
        - **Data Sources**: Information about data collection and processing
        - **Interpretation Guidelines**: How to interpret the results
        
        Please ensure the `_07_docs/product_assessment.md` file exists and contains the required documentation.
        """
        )

    except Exception as e:
        st.error(
            f"❌ **Error Reading File:** 파일을 읽는 중 오류가 발생했습니다: {str(e)}"
        )

    # 구분선
    st.markdown("---")

    # 추가 정보 섹션
    st.markdown("### 🔧 Technical Information")

    info_cols = st.columns(2)

    with info_cols[0]:
        st.markdown(
            """
        **📊 Data Sources:**
        - GMES (Production, NCF, UF, Weight, RR, CTL)
        - HGWS (Event data)
        - CQMS (Quality events)
        - HOPE (OE Application data)
        """
        )

    with info_cols[1]:
        st.markdown(
            """
        **🎯 Quality Metrics:**
        - **NCF**: Non-Conformity Factor (ppm)
        - **UF**: Uniformity test pass rate
        - **Weight**: GT Weight test pass rate
        - **RR**: Reliability test pass rate
        - **CTL**: Control test pass rate
        """
        )


# =============================================================================
# 상수 정의
# =============================================================================
# 품질 지수 계산을 위한 상수들
QUALITY_INDICES_CONFIG = {
    "ncf": {"max_rate": 20909, "min_rate": 1165, "multiplier": 1000000},
    "uf": {"max_rate": 0.9948, "min_rate": 0.599},
    "gt_weight": {"max_rate": 1.0, "min_rate": 0.9719},
    "rr": {"max_rate": 0.999, "min_rate": 0.593},
    "ctl": {"max_rate": 1.0, "min_rate": 0.857},
}

# UI 레이아웃 상수
CTL_COLUMN_RATIO = [1, 3]  # CTL 섹션의 컬럼 비율


# =============================================================================
# 메인 페이지 UI 구성
# =============================================================================
# 페이지 설정
st.set_page_config(
    page_title="OE Assessment Result Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 로드
load_custom_css()

# 페이지 헤더
st.markdown(
    """
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #1f2937; margin-bottom: 0.5rem;">📊 OE Assessment Result Viewer</h1>
    <p style="color: #6b7280; font-size: 1.1rem;">Comprehensive quality analysis dashboard for OE assessment results</p>
</div>
""",
    unsafe_allow_html=True,
)

main_tab = st.tabs(["📋 Overview", "🔍 Detail", "📖 Description"])

# Assessment 결과 데이터 로드
result_df = load_assessment_result()

with main_tab[0]:
    render_overview_tab(result_df)

with main_tab[1]:
    render_detail_tab(result_df)

with main_tab[2]:
    render_description_tab()


def safe_data_loading(func, *args, **kwargs):
    """
    데이터 로딩 함수를 안전하게 실행하는 래퍼 함수

    Args:
        func: 실행할 데이터 로딩 함수
        *args, **kwargs: 함수 인자들

    Returns:
        pd.DataFrame: 로딩된 데이터프레임 또는 빈 데이터프레임
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {str(e)}")
        return pd.DataFrame()


def render_section_with_error_handling(section_func, *args, **kwargs):
    """
    섹션 렌더링 함수를 에러 처리와 함께 실행

    Args:
        section_func: 실행할 섹션 함수
        *args, **kwargs: 함수 인자들
    """
    try:
        section_func(*args, **kwargs)
    except Exception as e:
        st.error(f"섹션 렌더링 중 오류 발생: {str(e)}")
