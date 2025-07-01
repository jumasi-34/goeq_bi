"""
Test page for debugging and validating data processing functions.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Optional, Dict, Any

from _00_database.db_client import get_client
from _01_query.GMES import q_production, q_ncf
from _02_preprocessing.GMES import df_uf

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sqlite_data(table_name: str) -> Optional[pd.DataFrame]:
    """
    SQLite 테이블에서 데이터를 로드합니다.

    Args:
        table_name (str): 테이블명

    Returns:
        Optional[pd.DataFrame]: 로드된 데이터프레임 또는 None
    """
    try:
        sqlite_db_manager = get_client("sqlite")
        query = f"SELECT * FROM {table_name}"
        df = sqlite_db_manager.execute(query)

        if df.empty:
            st.warning(f"No data found in {table_name} table")
            return None

        return df

    except Exception as e:
        st.error(f"Error loading data from {table_name}: {str(e)}")
        logger.error(f"Database error for {table_name}: {str(e)}")
        return None


def load_production_data(
    mcode_list: list, start_date: str, end_date: str
) -> Optional[pd.DataFrame]:
    """
    생산 데이터를 로드하고 집계합니다.

    Args:
        mcode_list (list): 제품 코드 리스트
        start_date (str): 시작일자 (YYYYMMDD)
        end_date (str): 종료일자 (YYYYMMDD)

    Returns:
        Optional[pd.DataFrame]: 집계된 생산 데이터
    """
    try:
        prdt_df = get_client("snowflake").execute(
            q_production.curing_prdt_daily(
                mcode_list=mcode_list,
                start_date=start_date,
                end_date=end_date,
            )
        )

        if prdt_df.empty:
            st.warning("No production data found for the specified criteria")
            return None

        # 데이터 집계
        aggregated_df = (
            prdt_df.groupby("m_code")
            .agg(
                min_date=("wrk_date", "min"),
                max_date=("wrk_date", "max"),
                total_qty=("prdt_qty", "sum"),
            )
            .reset_index()
        )

        return aggregated_df

    except Exception as e:
        st.error(f"Error loading production data: {str(e)}")
        logger.error(f"Production data error: {str(e)}")
        return None


def load_ncf_data(mcode: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    NCF 데이터를 로드하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        start_date (str): 시작일자 (YYYYMMDD)
        end_date (str): 종료일자 (YYYYMMDD)

    Returns:
        Optional[pd.DataFrame]: 집계된 NCF 데이터
    """
    try:
        ncf_df = get_client("snowflake").execute(
            q_ncf.ncf_daily(
                mcode=mcode,
                start_date=start_date,
                end_date=end_date,
            )
        )

        if ncf_df.empty:
            st.warning("No NCF data found for the specified criteria")
            return None

        # 컬럼명을 소문자로 변환
        ncf_df.columns = ncf_df.columns.str.lower()

        # 데이터 집계
        aggregated_df = (
            ncf_df.groupby(["m_code"]).agg(ncf_qty=("dft_qty", "sum")).reset_index()
        )

        return aggregated_df

    except Exception as e:
        st.error(f"Error loading NCF data: {str(e)}")
        logger.error(f"NCF data error: {str(e)}")
        return None


def load_uf_data(mcode: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    UF 데이터를 로드합니다.

    Args:
        mcode (str): 제품 코드
        start_date (str): 시작일자 (YYYYMMDD)
        end_date (str): 종료일자 (YYYYMMDD)

    Returns:
        Optional[pd.DataFrame]: UF 데이터
    """
    try:
        uf_df = get_client("snowflake").execute(
            df_uf.calculate_uf_pass_rate(
                mcode=mcode,
                start_date=start_date,
                end_date=end_date,
            )
        )

        if uf_df.empty:
            st.warning("No UF data found for the specified criteria")
            return None

        return uf_df

    except Exception as e:
        st.error(f"Error loading UF data: {str(e)}")
        logger.error(f"UF data error: {str(e)}")
        return None


def display_dataframe_with_info(df: pd.DataFrame, title: str, show_info: bool = True):
    """
    데이터프레임을 표시하고 기본 정보를 제공합니다.

    Args:
        df (pd.DataFrame): 표시할 데이터프레임
        title (str): 섹션 제목
        show_info (bool): 기본 정보 표시 여부
    """
    st.subheader(title)

    if show_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric(
                "Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB"
            )

    st.dataframe(df)


def main():
    """메인 실행 함수"""
    st.title("Data Validation Test Page")

    # 설정값 (나중에 Streamlit 입력으로 변경 가능)
    TEST_CONFIG = {
        "mcode": "1031954",
        "mcode_list": ["1031954"],
        "start_date": "20240419",
        "end_date": "20241011",
    }

    # 1. SQLite 데이터 로드
    st.header("📊 SQLite Data")

    target_df = load_sqlite_data("mass_assess_target")
    if target_df is not None:
        display_dataframe_with_info(target_df, "Target Data")

    result_df = load_sqlite_data("mass_assess_result")
    if result_df is not None:
        display_dataframe_with_info(result_df, "Result Data")

    # 2. Snowflake 데이터 로드
    st.header("❄️ Snowflake Data")

    # 생산 데이터
    prdt_df = load_production_data(
        TEST_CONFIG["mcode_list"], TEST_CONFIG["start_date"], TEST_CONFIG["end_date"]
    )
    if prdt_df is not None:
        display_dataframe_with_info(prdt_df, "Production Data")

    # NCF 데이터
    ncf_df = load_ncf_data(
        TEST_CONFIG["mcode"], TEST_CONFIG["start_date"], TEST_CONFIG["end_date"]
    )
    if ncf_df is not None:
        display_dataframe_with_info(ncf_df, "NCF Data")

    # UF 데이터
    uf_df = load_uf_data(
        TEST_CONFIG["mcode"], TEST_CONFIG["start_date"], TEST_CONFIG["end_date"]
    )
    if uf_df is not None:
        display_dataframe_with_info(uf_df, "UF Data")

    # 3. 데이터 통합 요약
    st.header("📈 Data Summary")

    summary_data = []
    for name, df in [
        ("Target", target_df),
        ("Result", result_df),
        ("Production", prdt_df),
        ("NCF", ncf_df),
        ("UF", uf_df),
    ]:
        if df is not None:
            summary_data.append(
                {
                    "Dataset": name,
                    "Rows": len(df),
                    "Columns": len(df.columns),
                    "Memory (KB)": round(df.memory_usage(deep=True).sum() / 1024, 1),
                }
            )

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)


if __name__ == "__main__":
    main()
