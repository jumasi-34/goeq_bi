"""
FM(Final Manufacturing) 부적합 데이터 전처리 모듈

이 모듈은 FM 관련 부적합 데이터를 처리하고 분석하기 위한 함수들을 제공합니다.
주요 기능:
- 공장별 연간 FM 부적합 수량 집계
- 공장별 FM 부적합 PPM 계산
- 공장별 월간 FM 부적합 PPM 추이 분석
- 공장별 불량 유형별 FM 부적합 현황 분석

작성자: [Your Name]
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import time

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)
from _00_database.db_client import get_client
from _01_query.GMES import q_production, q_ncf
from _02_preprocessing.GMES import df_production
from _02_preprocessing import config_pandas
from _05_commons import config
from _02_preprocessing.helper_pandas import CountWorkingDays, test_dataframe_by_itself

# FM 부적합 코드 리스트
fm_ncf_list = [
    "FBC",
    "FCB",
    "FGB",
    "FHV",
    "FIR",
    "FLA",
    "FM",
    "FM1",
    "FM2",
    "FM3",
    "FM4",
    "FMA",
    "FMB",
    "FMC",
    "FME",
    "FMF",
    "FMG",
    "FMH",
    "FMI",
    "FML",
    "FMM",
    "FMN",
    "FMO",
    "FMP",
    "FMR",
    "FMS",
    "FMT",
    "FMV",
    "FMW",
    "FMX",
    "FPA",
    "FPL",
    "FMA",
    "FMD",
    "FSP",
]


@st.cache_data(ttl=600)
def get_global_ncf_monthly_df(yyyy: int) -> pd.DataFrame:
    """전체 공장의 연간 FM 부적합 수량을 집계합니다.

    Args:
        yyyy (int): 분석 대상 연도

    Returns:
        pd.DataFrame: 전체 공장의 부적합 수량 데이터
            - NCF_QTY: 부적합 수량
    """
    df_ncf = get_client("snowflake").execute(
        q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=fm_ncf_list)
    )
    df_ncf.columns = df_ncf.columns.str.upper()
    df_prdt = get_client("snowflake").execute(
        q_production.curing_prdt_monthly_by_ym(yyyy=yyyy)
    )
    df_prdt.columns = df_prdt.columns.str.upper()

    df_ncf = df_ncf.groupby("MM", as_index=False)["NCF_QTY"].sum()
    df_ncf = df_ncf.sort_values(by="MM")
    df_prdt = df_prdt.groupby("MM", as_index=False)["PRDT_QTY"].sum()
    df_prdt = df_prdt.sort_values(by="MM")
    df_ncf = pd.merge(df_ncf, df_prdt, on="MM", how="left")
    df_ncf["PPM"] = df_ncf["NCF_QTY"] / df_ncf["PRDT_QTY"] * 1_000_000
    return df_ncf


@st.cache_data(ttl=600)
def get_yearly_ncf_by_plant_df(yyyy: int, ncf_list: list = fm_ncf_list) -> pd.DataFrame:
    """공장별 연간 FM 부적합 수량을 집계합니다.

    Args:
        yyyy (int): 분석 대상 연도
        ncf_list (list, optional): 부적합 코드 리스트. 기본값은 fm_ncf_list

    Returns:
        pd.DataFrame: 공장별 부적합 수량 데이터
            - PLANT: 공장 코드
            - NCF_QTY: 부적합 수량
    """
    df = get_client("snowflake").execute(
        q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=ncf_list)
    )
    df.columns = df.columns.str.upper()
    df = df.groupby("PLANT", as_index=False)["NCF_QTY"].sum()
    df = df.sort_values(by="NCF_QTY", ascending=False)
    df = df.assign(
        PLANT=pd.Categorical(df["PLANT"], categories=config.plant_codes, ordered=True)
    ).sort_values(by="PLANT")
    return df


@st.cache_data(ttl=600)
def get_yearly_ncf_ppm_by_plant_df(yyyy: int) -> pd.DataFrame:
    """공장별 연간 FM 부적합 PPM을 계산합니다.

    Args:
        yyyy (int): 분석 대상 연도

    Returns:
        pd.DataFrame: 공장별 부적합 PPM 데이터
            - PLANT: 공장 코드
            - NCF_QTY: 부적합 수량
            - PRDT_QTY: 생산 수량
            - PPM: 부적합 PPM
    """
    df_ncf = get_yearly_ncf_by_plant_df(yyyy)
    df_prdt = df_production.get_yearly_production_df(yyyy)
    df_ncf_ppm = pd.merge(df_ncf, df_prdt, on="PLANT", how="left")
    df_ncf_ppm["PPM"] = df_ncf_ppm["NCF_QTY"] / df_ncf_ppm["PRDT_QTY"] * 1_000_000
    return df_ncf_ppm


@st.cache_data(ttl=600)
def get_monthly_ncf_ppm_by_plant_df(yyyy: int, plant: str) -> pd.DataFrame:
    """특정 공장의 월별 FM 부적합 PPM 추이를 분석합니다.

    Args:
        yyyy (int): 분석 대상 연도
        plant (str): 공장 코드

    Returns:
        pd.DataFrame: 월별 부적합 PPM 데이터
            - MM: 월
            - NCF_QTY: 부적합 수량
            - PRDT_QTY: 생산 수량
            - PPM: 부적합 PPM
    """
    # 부적합 데이터 조회 및 전처리
    df_ncf = get_client("snowflake").execute(
        q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=fm_ncf_list)
    )
    df_ncf.columns = df_ncf.columns.str.upper()

    # 생산 데이터 조회 및 전처리
    df_prdt = get_client("snowflake").execute(
        q_production.curing_prdt_monthly_by_ym(yyyy=yyyy)
    )
    df_prdt.columns = df_prdt.columns.str.upper()

    # 특정 공장 데이터 필터링 및 집계
    df_ncf = df_ncf[df_ncf["PLANT"] == plant]
    df_ncf = df_ncf.groupby("MM", as_index=False)["NCF_QTY"].sum()
    df_ncf = df_ncf.sort_values(by="MM")

    df_prdt = df_prdt[df_prdt["PLANT"] == plant]
    df_prdt = df_prdt.groupby("MM", as_index=False)["PRDT_QTY"].sum()
    df_prdt = df_prdt.sort_values(by="MM")

    # PPM 계산
    groupby_df = pd.merge(df_ncf, df_prdt, on="MM", how="left")
    groupby_df["PPM"] = groupby_df["NCF_QTY"] / groupby_df["PRDT_QTY"] * 1_000_000
    return groupby_df


@st.cache_data(ttl=600)
def get_ncf_detail_by_plant(yyyy: int, plant: str) -> pd.DataFrame:
    """특정 공장의 불량 유형별 FM 부적합 현황을 분석합니다.

    Args:
        yyyy (int): 분석 대상 연도
        plant (str): 공장 코드

    Returns:
        pd.DataFrame: 불량 유형별 부적합 수량 데이터
            - DFT_CD: 불량 코드
            - NCF_QTY: 부적합 수량
    """
    df = get_client("snowflake").execute(
        q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=fm_ncf_list)
    )
    df.columns = df.columns.str.upper()
    df = df[df["PLANT"] == plant]
    df = df.groupby("DFT_CD", as_index=False)["NCF_QTY"].sum()
    df = df.sort_values(by="NCF_QTY", ascending=False)
    return df
