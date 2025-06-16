"""
Pandas 기반 전처리 및 MTTC 계산 유틸

이 모듈은 품질 이슈 데이터를 처리하는 데 필요한 다양한 전처리 함수와
근무일 기반 MTTC 계산 클래스를 제공합니다.

포함된 항목:
- CountWorkingDays 클래스: MTTC 및 각종 경과일 계산
- 전처리 함수들: 컬럼명 표준화, 날짜/카테고리 변환
- 테스트 도우미 함수: DataFrame 반환 결과 미리보기
- Streamlit 안전 캐시 데코레이터

사용처 예시:
- Streamlit 대시보드에서 품질 이슈 테이블 처리
- 날짜 필터링 및 카테고리화
- 캐시 불가능한 환경 대응용 캐시 함수
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

from datetime import datetime
from functools import wraps
import numpy as np
import pandas as pd
import streamlit as st
from IPython.display import display


# MTTC 계산 class
class CountWorkingDays:
    """
    MTTC 계산을 위한 Class
    """

    today = datetime.now()
    today_formatted_date = today.strftime("%Y-%m-%d")

    def __init__(
        self,
        df,
        occ_date,
        reg_date,
        return_date,
        countermeasure_date,
        comp_date,
        return_yn,
    ):
        self.df = df
        self.occ_date = occ_date
        self.reg_date = reg_date
        self.return_date = return_date
        self.countermeasure_date = countermeasure_date
        self.comp_date = comp_date
        self.return_yn = return_yn

    def get_days(self, start_col, end_col):
        """
        주어진 시작일과 종료일을 기반으로 근무일 수를 계산하여 반환
        """
        num_working_days = []

        for start_date, end_date in zip(self.df[start_col], self.df[end_col]):
            if pd.isnull(start_date):
                num_working_days.append(np.nan)
                continue
            elif pd.isnull(end_date):
                working_days = pd.bdate_range(
                    start=start_date, end=self.today_formatted_date
                ).shape[0]
            else:
                working_days = pd.bdate_range(start=start_date, end=end_date).shape[0]
            num_working_days.append(working_days)

        return pd.Series(num_working_days, index=self.df.index)

    def get_reg_days(self):
        return self.get_days(self.occ_date, self.reg_date).astype("Int64")

    def get_return_days(self):
        num_working_days = []

        for return_yn, start_date, end_date in zip(
            self.df[self.return_yn], self.df[self.reg_date], self.df[self.return_date]
        ):
            if return_yn == "N":
                num_working_days.append(np.nan)
                continue
            elif return_yn == "Y" and pd.isnull(end_date):
                working_days = pd.bdate_range(
                    start=start_date, end=self.today_formatted_date
                ).shape[0]
            else:
                working_days = pd.bdate_range(start=start_date, end=end_date).shape[0]
            num_working_days.append(working_days)
        return pd.Series(num_working_days, index=self.df.index).astype("Int64")

    def get_countermeasure_days(self):
        num_working_days = []

        for return_yn, start_date, mid_date, end_date in zip(
            self.df[self.return_yn],
            self.df[self.reg_date],
            self.df[self.return_date],
            self.df[self.countermeasure_date],
        ):
            # 기본값 설정
            start = end = None

            # 조건에 따라 시작일/종료일 결정
            if return_yn == "Y":
                if pd.isnull(mid_date):
                    num_working_days.append(np.nan)
                    continue
                start = mid_date
            else:  # return_yn == "N"
                if pd.isnull(start_date):
                    num_working_days.append(np.nan)
                    continue
                start = start_date

            if pd.isnull(end_date):
                end = self.today_formatted_date
            else:
                end = end_date

            # 영업일 계산
            working_days = pd.bdate_range(start=start, end=end).shape[0]
            num_working_days.append(working_days)

        return pd.Series(num_working_days, index=self.df.index).astype("Int64")

    # def get_8d_report_days(self):
    #     return self.get_days(self.countermeasure_date, self.comp_date).astype("Int64")

    def get_8d_report_days(self):
        num_working_days = []

        for start_date, end_date in zip(
            self.df[self.countermeasure_date], self.df[self.comp_date]
        ):
            if pd.isnull(start_date):
                # countermeasure_date가 없으면 0 반환
                num_working_days.append(0)
            else:
                # comp_date가 없으면 오늘 날짜로 계산
                end = end_date if not pd.isnull(end_date) else self.today_formatted_date
                working_days = pd.bdate_range(start=start_date, end=end).shape[0]
                num_working_days.append(working_days)

        return pd.Series(num_working_days, index=self.df.index).astype("Int64")


def test_dataframe_by_itself(func, *args, **kwargs):
    result = func(*args, **kwargs)

    # 튜플인 경우 → 모든 항목을 순회하면서 DataFrame 출력
    if isinstance(result, tuple):
        for idx, df in enumerate(result):
            if isinstance(df, pd.DataFrame):
                print(
                    f"[{func.__name__} - Result {idx}] rows : {df.shape[0]} columns : {df.shape[1]}"
                )
                print(df.head())
                print("-" * 40)
            else:
                print(
                    f"[{func.__name__} - Result {idx}] is not a DataFrame: {type(df)}"
                )
                print("-" * 40)

    # 단일 반환인 경우 → 그대로 출력
    elif isinstance(result, pd.DataFrame):
        print(f"[{func.__name__}] rows : {result.shape[0]} columns : {result.shape[1]}")
        print(result.head())
        print("-" * 40)

    else:
        raise TypeError(
            f"[{func.__name__}] did not return a DataFrame or tuple of DataFrames. Got {type(result)}."
        )


# TEST 함수
def test_dataframe_by_ipynb(func, *args, **kwargs):
    df = func(*args, **kwargs)
    print(f"Testing [{func.__name__}] rows : {df.shape[0]} columns : {df.shape[1]}")
    display(df.head())


# Status return 함수
def get_weekly_conditions(df, local_start_of_week, local_end_of_week):
    bool_open = (df["REG_DATE"] >= local_start_of_week) & (
        df["REG_DATE"] <= local_end_of_week
    )
    bool_close = (df["COMP_DATE"] >= local_start_of_week) & (
        df["COMP_DATE"] <= local_end_of_week
    )
    bool_ongoing1 = (df["REG_DATE"] < local_start_of_week) & (
        df["COMP_DATE"] > local_end_of_week
    )
    bool_ongoing2 = (df["REG_DATE"] < local_start_of_week) & (df["COMP_DATE"].isnull())

    return bool_open, bool_close, bool_ongoing1, bool_ongoing2


# * region 공통 전처리 함수
def standardize_columns_uppercase(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame 컬럼명을 모두 대문자로 변환합니다."""
    df.columns = df.columns.str.upper()
    return df


def convert_date_columns(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """지정한 컬럼들을 datetime 형식으로 변환합니다."""
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def convert_category_columns(df: pd.DataFrame, cat_cols: list) -> pd.DataFrame:
    """지정한 컬럼들을 category 타입으로 변환합니다."""
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


def convert_plant_category(
    df: pd.DataFrame, plant_codes: list, exclude_ot: bool = False
) -> pd.DataFrame:
    """PLANT 컬럼을 주어진 plant_codes를 기준으로 카테고리화합니다."""
    if "PLANT" in df.columns:
        categories = plant_codes[:-1] if exclude_ot else plant_codes
        df["PLANT"] = pd.Categorical(df["PLANT"], ordered=True, categories=categories)
    return df


def add_url_column(df: pd.DataFrame, seq_col: str, base_url: str) -> pd.DataFrame:
    """지정 컬럼을 이용해 URL 컬럼을 추가합니다."""
    if seq_col in df.columns:
        df["URL"] = base_url + df[seq_col].astype(str)
    return df


# 조건부 캐시 데코레이터 정의
try:

    _is_streamlit = st.runtime.exists()
except:
    _is_streamlit = False


# * Sremlit 실행 중일 때만 st.cache_data가 적용되도록 하는 데코레이션 보완 함수
def cache_data_safe(ttl=600):
    """Streamlit이 실행 중일 때만 cache_data를 적용"""

    def decorator(func):
        if _is_streamlit:
            return st.cache_data(ttl=ttl)(func)
        else:
            return func  # 캐시 없이 원본 함수 반환

    return decorator
