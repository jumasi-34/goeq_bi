"""
df_uf.py
"""

import sys
import numpy as np
import pandas as pd
import logging
import os
from typing import Optional

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database.db_client import get_client
from _01_query.GMES.q_uf import uf_product_assess
from _01_query.GMES.q_uf import uf_product_assess_monthly
from _01_query.GMES.q_uf import uf_standard as uf_standard_query
from _01_query.GMES.q_uf import uf_individual as uf_individual_query


def calculate_uf_pass_rate(mcode: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    균일성(UF) 평가 데이터를 전처리하여 검사수량, 합격수량, 합격률을 산출합니다.

    Args:
        mcode (str): 제품 코드
        start_date (str): 시작일자 (YYYYMMDD)
        end_date (str): 종료일자 (YYYYMMDD)

    Returns:
        pd.DataFrame: 전처리된 균일성 평가 데이터
            - m_code: 제품 코드
            - plant: 공장 코드
            - spec_cd: 규격 코드
            - uf_ins_qty: 검사 수량
            - uf_pass_qty: 합격 수량
            - pass_rate: 합격률
    """
    try:
        # 데이터 조회
        df = get_client("snowflake").execute(
            uf_product_assess(mcode=mcode, start_date=start_date, end_date=end_date)
        )

        # 컬럼명을 모두 소문자로 통일
        df.columns = [col.lower() for col in df.columns]

        # JDG 컬럼 리스트 (소문자)
        jdg_cols = [col for col in df.columns if col.startswith("jdg_")]
        # 검사수량 계산
        df["uf_ins_qty"] = df[jdg_cols].sum(axis=1)

        # 공장별 합격 기준 정의 (소문자)
        pass_criteria = {
            "KP|IP|MP|TP|DP": ["jdg_1", "jdg_2", "jdg_3", "jdg_4"],
            "HP|JP|CP": ["jdg_1", "jdg_2", "jdg_3"],
        }

        # 합격수량 계산
        df["uf_pass_qty"] = 0
        for plant_pattern, cols in pass_criteria.items():
            mask = df["plant"].str.contains(plant_pattern, regex=True)
            df.loc[mask, "uf_pass_qty"] = df.loc[mask, cols].sum(axis=1)

        # 합격률 계산 (0으로 나누기 방지)
        df["pass_rate"] = df.apply(
            lambda x: x["uf_pass_qty"] / x["uf_ins_qty"] if x["uf_ins_qty"] > 0 else 0,
            axis=1,
        )

        # 결과 컬럼만 반환
        return (
            df[["m_code", "plant", "spec_cd", "uf_ins_qty", "uf_pass_qty", "pass_rate"]]
            .dropna()
            .reset_index(drop=True)
        )

    except Exception as e:
        logging.error(f"데이터 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame()


def calculate_uf_pass_rate_monthly(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    균일성(UF) 평가 데이터를 전처리하여 검사수량, 합격수량, 합격률을 산출합니다.

    Args:
        mcode (str): 제품 코드
        start_date (str): 시작일자 (YYYYMMDD)
        end_date (str): 종료일자 (YYYYMMDD)

    Returns:
        pd.DataFrame: 전처리된 균일성 평가 데이터
            - m_code: 제품 코드
            - plant: 공장 코드
            - spec_cd: 규격 코드
            - uf_ins_qty: 검사 수량
            - uf_pass_qty: 합격 수량
            - pass_rate: 합격률
    """
    try:
        # 데이터 조회
        df = get_client("snowflake").execute(
            uf_product_assess_monthly(
                mcode=mcode, start_date=start_date, end_date=end_date
            )
        )
        # 컬럼명을 모두 소문자로 통일
        df.columns = [col.upper() for col in df.columns]
        df["YYYYMM"] = pd.to_datetime(df["YYYYMM"], format="%Y%m").dt.strftime("%Y-%m")

        # JDG 컬럼 리스트 (소문자)
        jdg_cols = [col for col in df.columns if col.startswith("JDG_")]
        # # 검사수량 계산
        df["UF_INS_QTY"] = df[jdg_cols].sum(axis=1)

        # 공장별 합격 기준 정의 (소문자)
        pass_criteria = {
            "KP|IP|MP|TP|DP": ["JDG_1", "JDG_2", "JDG_3", "JDG_4"],
            "HP|JP|CP": ["JDG_1", "JDG_2", "JDG_3"],
        }

        # 합격수량 계산
        df["UF_PASS_QTY"] = 0
        for plant_pattern, cols in pass_criteria.items():
            mask = df["PLANT"].str.contains(plant_pattern, regex=True)
            df.loc[mask, "UF_PASS_QTY"] = df.loc[mask, cols].sum(axis=1)

        # 합격률 계산 (0으로 나누기 방지)
        df["PASS_RATE"] = df.apply(
            lambda x: (
                x["UF_PASS_QTY"] / x["UF_INS_QTY"] if x["UF_INS_QTY"] > 0 else 0
            ),
            axis=1,
        )
        df = df.sort_values(by="YYYYMM", ascending=True)
        # 결과 컬럼만 반환
        return df
    except Exception as e:
        logging.error(f"데이터 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame()


def uf_standard(mcode):
    uf_standard_df = get_client("snowflake").execute(uf_standard_query(mcode=mcode))
    uf_standard_df.columns = [col.upper() for col in uf_standard_df.columns]
    uf_standard_df = uf_standard_df.dropna()
    uf_standard_df = uf_standard_df.sort_values(by="SPEC_CD", ascending=False)
    uf_standard_df = uf_standard_df.head(1).reset_index(drop=True)

    return uf_standard_df


def uf_individual(mcode, start_date, end_date):
    df = get_client("snowflake").execute(
        uf_individual_query(mcode=mcode, start_date=start_date, end_date=end_date)
    )
    df.columns = [col.upper() for col in df.columns]
    # plant_groups = {
    #     "group1": ["KP", "IP", "MP", "TP", "DP"],
    #     "group2": ["HP", "JP", "CP"],
    # }
    # pass_jdg_group = {
    #     "group1": ["1", "2", "3", "4"],
    #     "group2": ["1", "2", "3"],
    # }
    # conditions = [
    #     (df["PLANT"].isin(plant_groups["group1"]))
    #     & (df["JDG_GR"].isin(pass_jdg_group["group1"])),
    #     (df["PLANT"].isin(plant_groups["group2"]))
    #     & (df["JDG_GR"].isin(pass_jdg_group["group2"])),
    # ]
    # choices = ["OK", "OK"]

    # df["JDG"] = np.select(conditions, choices, default="NG")
    # df["INS_DATE"] = pd.to_datetime(df["INS_DATE"], errors="coerce")
    return df
