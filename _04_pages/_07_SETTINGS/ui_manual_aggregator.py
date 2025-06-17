"""
수동 데이터 집계를 위한 Streamlit UI 페이지

이 모듈은 HOPE 셀인 데이터와 제품 평가 데이터의 수동 집계를 위한 사용자 인터페이스를 제공합니다.
각 탭에서 해당하는 집계 작업을 실행할 수 있으며, 실행 결과는 UI에 표시됩니다.
"""

import sys
from pathlib import Path
import streamlit as st
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from _08_automation.oracle_to_sqlite import main as generate_sellin_monthly_agg
from _08_automation.product_assessment import main as run_product_assessment

# 세션 상태 초기화
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Sell-in Data"
if "last_run_time" not in st.session_state:
    st.session_state.last_run_time = None


@st.cache_data(ttl=3600)  # 1시간 동안 캐시 유지
def run_manual_aggregation():
    """
    HOPE 셀인 데이터의 수동 집계를 실행하는 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Oracle DB에서 데이터를 조회하는 중...")
        progress_bar.progress(20)

        generate_sellin_monthly_agg()

        progress_bar.progress(100)
        status_text.text("완료!")
        st.success("집계가 완료되었습니다!")

        # 마지막 실행 시간 업데이트
        st.session_state.last_run_time = datetime.now()

    except Exception as e:
        st.error(f"집계 중 오류가 발생했습니다: {str(e)}")


@st.cache_data(ttl=3600)  # 1시간 동안 캐시 유지
def run_product_assessment_aggregation():
    """
    제품 평가 데이터의 수동 집계를 실행하는 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("제품 평가 데이터를 수집하는 중...")
        progress_bar.progress(20)

        run_product_assessment()

        progress_bar.progress(100)
        status_text.text("완료!")
        st.success("제품 평가 집계가 완료되었습니다!")

        # 마지막 실행 시간 업데이트
        st.session_state.last_run_time = datetime.now()

    except Exception as e:
        st.error(f"제품 평가 집계 중 오류가 발생했습니다: {str(e)}")


# Streamlit UI 구성
st.title("Manual Data Aggregation")

# 마지막 실행 시간 표시
if st.session_state.last_run_time:
    st.info(
        f"마지막 실행 시간: {st.session_state.last_run_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

# 데이터 집계 유형별 탭 생성
tab1, tab2 = st.tabs(["Sell-in Data", "Product Assessment"])


# HOPE 셀인 데이터 집계 탭
with tab1:
    st.markdown(
        """
    이 탭에서는 HOPE 셀인 데이터를 월별로 집계하여 SQLite 데이터베이스에 저장합니다.
    """
    )
    if st.button("Run Sell-in Aggregation", type="primary"):
        st.session_state.active_tab = "Sell-in Data"
        run_manual_aggregation()

# 제품 평가 데이터 집계 탭
with tab2:
    st.markdown(
        """
    이 탭에서는 제품 평가 데이터를 집계하여 SQLite 데이터베이스에 저장합니다.
    """
    )
    if st.button("Run Product Assessment Aggregation", type="primary"):
        st.session_state.active_tab = "Product Assessment"
        run_product_assessment_aggregation()

    # 이미지 로딩을 지연시키기 위해 expander 사용
    with st.expander("제품 평가 프로세스 다이어그램 보기"):
        st.image("_06_assets/Diagram/product_assessment.png")
