"""
수동 데이터 집계를 위한 Streamlit UI 페이지

이 모듈은 HOPE 셀인 데이터와 제품 평가 데이터의 수동 집계를 위한 사용자 인터페이스를 제공합니다.
각 탭에서 해당하는 집계 작업을 실행할 수 있으며, 실행 결과는 로그 파일과 UI에 표시됩니다.
"""

import sys
from pathlib import Path
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
import streamlit as st
from _08_automation.oracle_to_sqlite import main as generate_sellin_monthly_agg
from _08_automation.product_assessment import main as run_product_assessment
import logging
from datetime import datetime

# 로깅 설정
log_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "_08_automation"
)
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "ui_manual_aggregator.log")),
        logging.StreamHandler(),
    ],
)


def run_manual_aggregation():
    """
    HOPE 셀인 데이터의 수동 집계를 실행하는 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
        오류 발생 시 로그 파일에 기록됩니다.
    """
    try:
        st.info("집계를 시작합니다...")
        generate_sellin_monthly_agg()
        st.success("집계가 완료되었습니다!")

    except Exception as e:
        error_msg = f"집계 중 오류가 발생했습니다: {str(e)}"
        st.error(error_msg)
        logging.error(error_msg, exc_info=True)


def run_product_assessment_aggregation():
    """
    제품 평가 데이터의 수동 집계를 실행하는 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
        오류 발생 시 로그 파일에 기록됩니다.
    """
    try:
        st.info("제품 평가 집계를 시작합니다...")
        logging.info("제품 평가 집계 시작")
        run_product_assessment()
        st.success("제품 평가 집계가 완료되었습니다!")
        logging.info("제품 평가 집계 완료")

    except Exception as e:
        error_msg = f"제품 평가 집계 중 오류가 발생했습니다: {str(e)}"
        st.error(error_msg)
        logging.error(error_msg, exc_info=True)


# Streamlit UI 구성
st.title("Manual Data Aggregation")

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
        run_manual_aggregation()

# 제품 평가 데이터 집계 탭
with tab2:
    st.markdown(
        """
    이 탭에서는 제품 평가 데이터를 집계하여 SQLite 데이터베이스에 저장합니다.
    """
    )
    if st.button("Run Product Assessment Aggregation", type="primary"):
        run_product_assessment_aggregation()
    st.image("_06_assets/Diagram/product_assessment.png")
