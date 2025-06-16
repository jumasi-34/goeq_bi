"""
4M 변경 관리 데이터 전처리 모듈

이 모듈은 4M 변경 관리 데이터를 로드하고 전처리하는 함수들을 제공합니다.
주요 기능:
- 4M 변경 데이터 로드 및 기본 전처리
- 주간/연간 기준 데이터 필터링
- 피벗 테이블 생성
- 진행중인 변경사항 분석
"""

import sys
import numpy as np
import pandas as pd
import streamlit as st
from typing import Tuple
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database.db_client import get_client
from _01_query.CQMS import q_4m_change
from _02_preprocessing import config_pandas
from _02_preprocessing import helper_pandas
from _05_commons import config

# 공통 상수 정의
ALL_STATUS = ["Open", "Open & Close", "Close", "On-going"]
EXCLUDED_STATUS = ["Reject(Request)", "Reject(Final Approval)", "Complete", "Saved"]


@helper_pandas.cache_data_safe(ttl=600)
def load_4m() -> pd.DataFrame:
    """4M 변경 데이터를 로드하고 기본 전처리를 수행합니다.

    Returns:
        pd.DataFrame: 전처리된 4M 변경 데이터프레임
    """
    try:
        df = get_client("snowflake").execute(q_4m_change.query_4m_change())
        df = helper_pandas.standardize_columns_uppercase(df).pipe(
            helper_pandas.convert_date_columns, ["REG_DATE", "COMP_DATE"]
        )
        df["URL"] = config_pandas.URL_CHANGE_4M + df["DOC_NO"]
        df["DOC_NO"] = df["DOC_NO"].str.replace("MANA-DOC-", "4M-", regex=False)
        return df
    except Exception as e:
        st.error(f"4M 데이터 로드 중 오류 발생: {str(e)}")
        return pd.DataFrame()


@helper_pandas.cache_data_safe(ttl=600)
def filtered_4m_by_weekly(
    start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """주간 기준으로 4M 변경 데이터를 필터링하고 DOC_NO, PLANT, SUBJECT 기준으로 그룹화합니다.

    Args:
        start_date: 시작일
        end_date: 종료일

    Returns:
        pd.DataFrame: DOC_NO, PLANT, SUBJECT 기준으로 그룹화된 4M 변경 데이터프레임
    """
    df = load_4m()

    # 주간 조건 계산
    bool_open, bool_close, bool_ongoing1, bool_ongoing2 = (
        helper_pandas.get_weekly_conditions(df, start_date, end_date)
    )

    # 상태 분류 조건 설정
    conditions = [
        bool_open & ~bool_close,
        bool_open & bool_close,
        ~bool_open & bool_close,
        bool_ongoing1 | bool_ongoing2,
    ]

    # 상태 카테고리 설정
    df["STATUS"] = np.select(conditions, ALL_STATUS, default=None)
    df["STATUS"] = pd.Categorical(df["STATUS"], categories=ALL_STATUS, ordered=True)
    df["PLANT"] = pd.Categorical(
        df["PLANT"], categories=config.plant_codes[:-1], ordered=True
    )

    # DOC_NO, PLANT, SUBJECT 기준으로 그룹화
    df_grouped = (
        df.groupby(["DOC_NO", "PLANT", "SUBJECT"])
        .agg(
            {
                "STATUS": "first",
                "REG_DATE": "first",
                "COMP_DATE": "first",
                "URL": "first",
            }
        )
        .reset_index()
    )

    return df_grouped


@helper_pandas.cache_data_safe(ttl=600)
def df_pivot_4m(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """4M 변경 데이터의 피벗 테이블을 생성합니다.

    Args:
        start_date: 시작일
        end_date: 종료일

    Returns:
        pd.DataFrame: 공장별, 상태별 집계된 피벗 테이블
    """
    df = filtered_4m_by_weekly(start_date, end_date)
    return (
        df.pivot_table(
            index="PLANT",
            columns="STATUS",
            values="DOC_NO",
            aggfunc="count",
            fill_value=0,
            margins=True,
            margins_name="Global",
            observed=False,
        )
        .reset_index()
        .drop(columns="Global")
    )


@helper_pandas.cache_data_safe(ttl=600)
def filtered_4m_ongoing_by_yearly(
    plants: list = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """연간 기준으로 진행중인 4M 변경 데이터를 분석합니다.

    Args:
        plants: 분석할 공장 리스트 (선택사항)

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - NA 데이터프레임
            - 그룹화된 상세 데이터프레임
            - 공장별 집계 데이터프레임
            - 월별 집계 데이터프레임
    """
    df = load_4m()
    df = df[~df["STATUS"].isin(EXCLUDED_STATUS)].sort_values(by="REG_DATE")
    df["Elapsed_period"] = config.today - df["REG_DATE"]

    # NA 데이터와 유효 데이터 분리
    df_na = df[df["PLANT"].isna()]
    df_valid = df.dropna(subset=["PLANT"])
    if plants:
        df_valid = df_valid[df_valid["PLANT"].isin(plants)]

    # 상세 데이터 그룹화
    grouped = (
        df_valid.groupby(
            [
                "DOC_NO",
                "PLANT",
                "PURPOSE",
                "SUBJECT",
                "STATUS",
                "REQUESTER",
                "REG_DATE",
                "URL",
                "Elapsed_period",
            ]
        )["M_CODE"]
        .agg(list)
        .reset_index()
    )

    # 공장별 집계
    grouped_by_plant = (
        grouped.groupby("PLANT")
        .agg(COUNT=("DOC_NO", "count"))
        .sort_values("COUNT", ascending=False)
    )

    # 월별 집계
    grouped_by_month = grouped.groupby(pd.Grouper(key="REG_DATE", freq="ME")).agg(
        COUNT=("DOC_NO", "count")
    )

    return df_na, grouped, grouped_by_plant, grouped_by_month


def main():
    """모듈 테스트 실행"""
    today = config.today
    one_week_ago = config.a_week_ago

    # 각 함수별 테스트 실행
    helper_pandas.test_dataframe_by_itself(filtered_4m_by_weekly, today, one_week_ago)
    helper_pandas.test_dataframe_by_itself(df_pivot_4m, today, one_week_ago)
    helper_pandas.test_dataframe_by_itself(filtered_4m_ongoing_by_yearly)


if __name__ == "__main__":
    main()
