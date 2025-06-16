import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
import streamlit as st
from _08_automation.oracle_to_sqlite import generate_sellin_monthly_agg
from _08_automation.product_assessment_agg import main as run_product_assessment
import logging
from datetime import datetime
import os


def run_manual_aggregation():
    """
    수동 집계 실행 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
    """
    try:
        st.info("집계를 시작합니다...")
        generate_sellin_monthly_agg()
        st.success("집계가 완료되었습니다!")

    except Exception as e:
        st.error(f"집계 중 오류가 발생했습니다: {str(e)}")
        logging.error(f"집계 오류: {str(e)}")


def run_product_assessment_aggregation():
    """
    제품 평가 집계 실행 함수

    Returns
    -------
    None
        집계 실행 결과를 Streamlit UI에 표시합니다.
    """
    try:
        st.info("제품 평가 집계를 시작합니다...")
        run_product_assessment()
        st.success("제품 평가 집계가 완료되었습니다!")

    except Exception as e:
        st.error(f"제품 평가 집계 중 오류가 발생했습니다: {str(e)}")
        logging.error(f"제품 평가 집계 오류: {str(e)}")


# 페이지 제목
st.title("Manual Data Aggregation")

# 탭 생성
tab1, tab2 = st.tabs(["Sell-in Data", "Product Assessment"])

# Sell-in Data 탭
with tab1:
    st.markdown(
        """
    이 탭에서는 HOPE 셀인 데이터를 월별로 집계하여 SQLite 데이터베이스에 저장합니다.
    """
    )
    if st.button("Run Sell-in Aggregation", type="primary"):
        run_manual_aggregation()

# Product Assessment 탭
with tab2:
    st.markdown(
        """
    이 탭에서는 제품 평가 데이터를 집계하여 SQLite 데이터베이스에 저장합니다.
    """
    )
    st.image("_06_assets/Diagram/product_assessment.png")
    if st.button("Run Product Assessment Aggregation", type="primary"):
        run_product_assessment_aggregation()
