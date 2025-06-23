"""
Product History Dashboard

이 모듈은 특정 M-Code에 대한 제품 이력을 종합적으로 조회하고 시각화하는 Streamlit 페이지입니다.
CQMS 이벤트, OE 애플리케이션, HGWS, 생산 데이터, 품질 지표 등을 통합하여 제품의 전체적인 이력을 제공합니다.

주요 기능:
- CQMS 이벤트 조회 (Quality Issue, 4M Change, Audit)
- OE 애플리케이션 정보 표시
- HGWS 반품 데이터 분석
- 생산, NCF, RR, Weight, CTL, Uniformity 데이터 시각화

작성자: [작성자명]
작성일: [작성일]
수정일: [수정일]
"""

import streamlit as st
from datetime import datetime, timedelta
import importlib

from _02_preprocessing.CQMS import df_cqms_unified
from _02_preprocessing.HOPE import df_sellin, df_oeapp
from _02_preprocessing.HGWS import df_hgws
from _02_preprocessing.GMES import (
    df_production,
    df_ncf,
    df_rr,
    df_weight,
    df_ctl,
    df_uf,
)
from _03_visualization._08_ADMIN import (
    viz_oeassessment_result_viewer,
    viz_product_history,
)
from _05_commons import config


def load_search_interface():
    """
    사용자 검색 인터페이스를 로드합니다.

    Returns:
        tuple: (selected_mcode, start_date, end_date) 또는 None
    """
    # 개발 모드에서 모듈 리로드
    if config.DEV_MODE:
        importlib.reload(df_sellin)
        importlib.reload(df_hgws)

    # 기본 날짜 범위 설정 (1년 전 ~ 오늘)
    lastyear_first_day = datetime.now() - timedelta(days=365)
    today = datetime.now()

    st.subheader("Search")
    with st.container():
        with st.form("Individual Search"):
            mcode_col, start_col, end_col = st.columns(3)

            # M-Code 입력 필드
            selected_mcode = mcode_col.text_input(
                "Input M - Code",
                placeholder="7 - digits",
                help="Enter a valid 7-digit M-Code supplied by the OE",
            )

            # 날짜 범위 선택
            start_date = start_col.date_input("Start Date", value=lastyear_first_day)
            end_date = end_col.date_input("End Date", value=today)
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())
            start_date_YYYYMMDD = start_date.strftime("%Y%m%d")
            end_date_YYYYMMDD = end_date.strftime("%Y%m%d")

            btn_individual = st.form_submit_button("Run")
            if btn_individual:
                if selected_mcode and start_date and end_date:
                    return (
                        selected_mcode,
                        start_date,
                        end_date,
                        start_date_YYYYMMDD,
                        end_date_YYYYMMDD,
                    )
                else:
                    st.warning("Please enter valid information in all fields.")
                    return None
    return None


def display_cqms_metrics(cqms_data):
    """
    CQMS 이벤트 통계 메트릭을 표시합니다.

    Args:
        cqms_data (pd.DataFrame): CQMS 데이터
    """
    metric_col = st.columns(5, vertical_alignment="center")
    metric_col[0].title("CQMS Events")
    stats_data = (
        cqms_data if "cqms_data" in locals() and len(cqms_data) > 0 else cqms_data
    )

    # 총 이벤트 수
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

    # Quality Issue 수
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

    # 4M Change 수
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

    # Audit 수
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


def display_cqms_charts(cqms_data):
    """
    CQMS 이벤트 차트를 표시합니다.

    Args:
        cqms_data (pd.DataFrame): CQMS 데이터
    """
    if len(cqms_data) > 0:
        event_counts = cqms_data["CATEGORY"].value_counts()

        cqms_event_col = st.columns([1, 3.5], vertical_alignment="center")

        # 파이 차트 (이벤트 분포)
        with cqms_event_col[0]:
            st.plotly_chart(
                viz_product_history.draw_pie_cqms_event(event_counts),
                use_container_width=True,
                key="event_distribution",
            )

        # 간트 차트 (타임라인)
        with cqms_event_col[1]:
            st.plotly_chart(
                viz_product_history.draw_gantt_timeline(cqms_data),
                use_container_width=True,
                key="gantt_timeline",
            )
    else:
        st.warning(
            "No events found for the selected filters. Please adjust your filter criteria."
        )


def display_oe_application(m_code):
    """
    OE 애플리케이션 정보를 표시합니다.

    Args:
        m_code (str): 조회할 M-Code
    """
    # OE 애플리케이션 데이터 로드
    oe_app = df_oeapp.load_oeapp_df_by_mcode(m_code)

    st.subheader("OE Application")
    column_config = {
        "M_CODE": st.column_config.TextColumn(label="M-CODE"),
        "VEHICLE MODEL(GLOBAL)": st.column_config.TextColumn(
            label="Veh. Model (Global)"
        ),
        "VEHICLE MODEL(LOCAL)": st.column_config.TextColumn(label="Veh. Model (Local)"),
    }
    st.dataframe(
        oe_app,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


def display_sellin_data(m_code, start_date, end_date):
    """
    Sellin 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
    """
    # Sellin 데이터 쿼리 및 전처리
    df_sellin_by_mcode = df_sellin.get_sellin_df(m_code, start_date, end_date)

    st.plotly_chart(
        viz_product_history.draw_area_chart_sellin_by_mcode(df_sellin_by_mcode)
    )


def display_hgws_data(m_code, start_date, end_date):
    """
    HGWS 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # HGWS 데이터 로드 및 전처리
    hgws = df_hgws.get_hgws_df(m_code, start_date, end_date)

    st.subheader("HGWS")
    st.plotly_chart(viz_product_history.draw_barplot_hgws_by_mcode(hgws))


def display_production_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD):
    """
    생산 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # 생산 데이터 로드
    df_production_data = df_production.get_daily_production_df(
        mcode=m_code,
        start_date=start_date_YYYYMMDD,
        end_date=end_date_YYYYMMDD,
    )

    st.subheader("Production")
    st.plotly_chart(
        viz_oeassessment_result_viewer.draw_barplot_production(df_production_data)
    )


def display_ncf_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD):
    """
    NCF 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # NCF 월별 데이터
    groupby_ncf_monthly = df_ncf.get_ncf_monthly_df(
        start_date=start_date_YYYYMMDD, end_date=end_date_YYYYMMDD, mcode=m_code
    )

    # NCF DFT 코드별 데이터
    groupby_dft_cd = df_ncf.get_ncf_by_dft_cd(
        start_date=start_date_YYYYMMDD, end_date=end_date_YYYYMMDD, mcode=m_code
    )

    st.subheader("NCF")
    ncf_col = st.columns(2)

    # 월별 NCF 차트
    ncf_col[0].plotly_chart(
        viz_oeassessment_result_viewer.draw_barplot_ncf(groupby_ncf_monthly)
    )

    # Pareto 차트
    ncf_col[1].plotly_chart(
        viz_oeassessment_result_viewer.draw_barplot_ncf_pareto(groupby_dft_cd)
    )


def display_rr_data(m_code, start_date, end_date):
    """
    RR 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # RR 원시 데이터 로드 및 전처리
    rr_raw_df = df_rr.get_processed_raw_rr_data(
        start_date=start_date, end_date=end_date, mcode=m_code
    )
    rr_raw_df = rr_raw_df.sort_values(by="SMPL_DATE")
    rr_raw_df = rr_raw_df.reset_index(drop=True)

    # RR 표준 데이터 로드
    rr_standard_df = df_rr.get_rr_oe_list_df()
    rr_standard_df = rr_standard_df[rr_standard_df["M_CODE"] == m_code]

    rr_col = st.columns(2)

    # RR 트렌드 차트
    rr_col[0].plotly_chart(
        viz_oeassessment_result_viewer.draw_rr_trend(rr_raw_df, rr_standard_df)
    )

    # RR 분포 차트
    rr_col[1].plotly_chart(
        viz_oeassessment_result_viewer.draw_rr_distribution(rr_raw_df, rr_standard_df)
    )


def display_weight_data(m_code, start_date, end_date):
    """
    Weight 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # Weight 데이터 로드
    wt_individual_df = df_weight.get_groupby_weight_ym_df(
        start_date=start_date, end_date=end_date, mcode=m_code
    )

    st.subheader("Weight")
    st.plotly_chart(
        viz_oeassessment_result_viewer.draw_weight_distribution(wt_individual_df)
    )


def display_ctl_data(m_code, start_date, end_date):
    """
    CTL 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # CTL 데이터 로드
    ctl_df = df_ctl.get_groupby_doc_ctl_df(
        start_date=start_date, end_date=end_date, mcode=m_code
    )

    st.subheader("CTL")
    st.plotly_chart(viz_oeassessment_result_viewer.draw_ctl_trend(ctl_df))


def display_uniformity_data(m_code, start_date, end_date):
    """
    Uniformity 데이터를 로드하고 시각화합니다.

    Args:
        m_code (str): 조회할 M-Code
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
    """
    # Uniformity 데이터 로드
    uf_df = df_uf.calculate_uf_pass_rate_monthly(
        start_date=start_date, end_date=end_date, mcode=m_code
    )

    st.subheader("Uniformity")
    st.plotly_chart(viz_oeassessment_result_viewer.draw_barplot_uf(uf_df))


st.markdown(
    """
    - CQMS 세부 데이터에 대해 Link 추가 필요
    - 조회 기간 연동 필요
    - 레이아웃 수정 필요
    - Run 수행시 작동하도록 수정 필요
    """,
    unsafe_allow_html=True,
)

# 검색 인터페이스 로드
search_result = load_search_interface()

# 검색 결과가 있을 때만 분석 수행
if search_result:
    m_code, start_date, end_date, start_date_YYYYMMDD, end_date_YYYYMMDD = search_result
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    # CQMS 데이터 로드 및 표시
    cqms_data = df_cqms_unified.get_cqms_unified_df(m_code)

    # CQMS 메트릭 표시
    display_cqms_metrics(cqms_data)

    # CQMS 차트 표시
    display_cqms_charts(cqms_data)

    # CQMS 데이터 테이블 표시
    with st.expander("CQMS Events Data(Table)"):
        st.dataframe(cqms_data, use_container_width=True, hide_index=True)

    # OE 애플리케이션 정보 표시
    display_oe_application(m_code)

    # Sellin 데이터 표시
    display_sellin_data(m_code, start_date, end_date)

    # HGWS 데이터 표시
    display_hgws_data(m_code, start_date, end_date)

    # 생산 데이터 표시
    display_production_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD)

    # NCF 데이터 표시
    display_ncf_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD)

    # RR 데이터 표시
    display_rr_data(m_code, start_date, end_date)

    # Weight 데이터 표시
    display_weight_data(m_code, start_date, end_date)

    # CTL 데이터 표시
    display_ctl_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD)

    # Uniformity 데이터 표시
    display_uniformity_data(m_code, start_date_YYYYMMDD, end_date_YYYYMMDD)

else:
    # 검색 결과가 없을 때 안내 메시지 표시
    st.info(
        "Please enter search criteria and click 'Run' to view product history analysis."
    )
