import sys
import pandas as pd
import streamlit as st
import os
from typing import Optional

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database.db_client import get_client
from _01_query.GMES import q_production
from _05_commons import config


@st.cache_data(ttl=600)
def get_yearly_production_df(yyyy: int) -> pd.DataFrame:
    query = q_production.curing_prdt_monthly_by_ym(yyyy=yyyy)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    df = df.groupby("PLANT", as_index=False)["PRDT_QTY"].sum()
    df = df.sort_values(by="PRDT_QTY", ascending=False)
    df = df.assign(
        PLANT=pd.Categorical(df["PLANT"], categories=config.plant_codes, ordered=True)
    ).sort_values(by="PLANT")
    return df


def get_daily_production_df(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    일별 생산 데이터를 조회하여 DataFrame으로 반환합니다.

    Parameters
    ----------
    mcode : Optional[str], optional
        조회할 제품 코드. 기본값은 None
    start_date : Optional[str], optional
        조회 시작일자 (YYYYMMDD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일자 (YYYYMMDD 형식). 기본값은 None

    Returns
    -------
    pd.DataFrame
        공장별 일별 생산량 데이터
    """
    query = q_production.curing_prdt_daily(
        mcode_list=[mcode] if mcode else None, start_date=start_date, end_date=end_date
    )
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()

    if not df.empty:
        df["WRK_DATE"] = pd.to_datetime(df["WRK_DATE"], format="%Y%m%d").dt.strftime(
            "%Y-%m-%d"
        )
        # 월별 그룹핑을 위한 연월 컬럼 추가
        df["YYYYMM"] = pd.to_datetime(df["WRK_DATE"]).dt.strftime("%Y-%m")

        # 월별 생산량 집계
        df = df.groupby(
            ["PLANT", "M_CODE", "SPEC_CD", "STXC", "YYYYMM"], as_index=False
        )["PRDT_QTY"].sum()

        # 날짜 기준 정렬
        df = df.sort_values(by=["YYYYMM", "PLANT"])

        # PLANT 컬럼을 카테고리 타입으로 변환하여 정렬
        df = df.assign(
            PLANT=pd.Categorical(
                df["PLANT"], categories=config.plant_codes, ordered=True
            )
        ).sort_values(by=["YYYYMM", "PLANT"])

    return df
