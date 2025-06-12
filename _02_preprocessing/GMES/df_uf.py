"""
df_uf.py
"""

import sys
import pandas as pd
import logging

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _00_database.db_client import get_client
from _01_query.GMES.q_uf import uf_product_assess


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


if __name__ == "__main__":
    df = df_uf(mcode="1024247", start_date="2025-01-01", end_date="2025-06-30")
    print(df)
