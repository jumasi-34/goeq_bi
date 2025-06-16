"""
고객사 감사 데이터 전처리 모듈

이 모듈은 고객사 감사 데이터를 처리하고 분석하기 위한 함수들을 제공합니다.
주요 기능:
- 주간 감사 현황 데이터 생성
- 감사 현황 피벗 테이블 생성
- 진행중인 감사 데이터 조회
"""

import sys
import pandas as pd
import streamlit as st
from typing import Optional, Tuple, List
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database.db_client import get_client
from _01_query.CQMS import q_customer_audit
from _02_preprocessing import config_pandas
from _02_preprocessing.helper_pandas import test_dataframe_by_itself
from _05_commons import config

# 감사 상태 정의
AUDIT_STATUS = ["NEW", "Upcoming", "CLOSE", "Need Update"]


@st.cache_data(ttl=600)
def df_audit_weekly(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    주간 감사 현황 데이터를 생성합니다.

    Args:
        start_date (pd.Timestamp): 시작일
        end_date (pd.Timestamp): 종료일

    Returns:
        pd.DataFrame: 처리된 감사 데이터프레임
    """
    try:
        # 데이터 로드 및 기본 전처리
        df = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
        df.columns = df.columns.str.upper()

        # 날짜 컬럼 변환
        date_columns = ["REG_DT", "START_DT", "COMP_DT"]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        df["URL"] = config_pandas.URL_AUDIT + df["URL"]

        # 상태별 조건 정의
        conditions = {
            "NEW": (df["REG_DT"] >= start_date) & (df["REG_DT"] <= end_date),
            "Upcoming": (df["START_DT"] > end_date)
            & ~((df["REG_DT"] >= start_date) & (df["REG_DT"] <= end_date)),
            "CLOSE": (
                (df["STATUS"] == "COMPLETE")
                & (df["COMP_DT"] >= start_date)
                & (df["COMP_DT"] <= end_date)
            )
            & ~(
                (df["START_DT"] > end_date)
                & ~((df["REG_DT"] >= start_date) & (df["REG_DT"] <= end_date))
            ),
            "Need Update": (df["START_DT"] < start_date)
            & ((df["COMP_DT"] > end_date) | (df["STATUS"] == "OPEN")),
        }

        # 상태 업데이트
        for status, condition in conditions.items():
            df.loc[condition, "STATUS"] = status

        # 카테고리 타입 변환
        df["STATUS"] = pd.Categorical(
            df["STATUS"], categories=AUDIT_STATUS, ordered=True
        )
        df["PLANT"] = pd.Categorical(
            df["PLANT"], categories=config.plant_codes[:-1], ordered=True
        )

        return df

    except Exception as e:
        st.error(f"감사 데이터 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame()


def df_pivot_audit(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    감사 현황 피벗 테이블을 생성합니다.

    Args:
        start_date (pd.Timestamp): 시작일
        end_date (pd.Timestamp): 종료일

    Returns:
        pd.DataFrame: 피벗된 감사 데이터프레임
    """
    df = df_audit_weekly(start_date, end_date)
    return (
        df.pivot_table(
            index="PLANT",
            columns="STATUS",
            values="URL",
            margins=True,
            margins_name="Global",
            aggfunc="count",
            fill_value=0,
            observed=False,
        )
        .reset_index()
        .drop(columns="Global")
    )


@st.cache_data(ttl=600)
def get_audit_ongoing_df(
    plants: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    진행중인 감사 데이터를 조회합니다.

    Args:
        plants (Optional[List[str]]): 공장 코드 리스트

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - 필터링된 감사 데이터
            - 공장별 집계 데이터
            - 월별 집계 데이터
    """
    try:
        # 데이터 로드 및 기본 전처리
        df = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
        df.columns = df.columns.str.upper()
        df["URL"] = config_pandas.URL_AUDIT + df["URL"]

        # 필터링 조건
        valid_types = ["System", "Project"]
        today = config.today

        # 데이터 필터링
        df = (
            df[df["TYPE"].isin(valid_types)]
            .query("STATUS == 'OPEN'")
            .assign(END_DT=lambda x: pd.to_datetime(x["END_DT"]))
            .query("END_DT <= @today")
            .assign(ELAPSED_PERIOD=lambda x: (today - x["END_DT"]).dt.days)
        )

        # 공장별 필터링
        filtered_df = df[df["PLANT"].isin(plants)] if plants else df

        # 집계 데이터 생성
        groupby_filtered_df_by_plant = (
            filtered_df.groupby("PLANT")
            .agg(COUNT=("SUBJECT", "count"))
            .sort_values(by="COUNT", ascending=False)
        )

        groupby_filtered_df_by_month = filtered_df.groupby(
            pd.Grouper(key="END_DT", freq="ME")
        ).agg(COUNT=("SUBJECT", "count"))

        return filtered_df, groupby_filtered_df_by_plant, groupby_filtered_df_by_month

    except Exception as e:
        st.error(f"진행중인 감사 데이터 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def main():
    """테스트 실행 함수"""
    today = config.today
    one_week_ago = config.a_week_ago

    test_dataframe_by_itself(df_audit_weekly, today, one_week_ago)
    test_dataframe_by_itself(df_pivot_audit, today, one_week_ago)
    test_dataframe_by_itself(get_audit_ongoing_df)


if __name__ == "__main__":
    main()
