"""
대상규격기준으로 집계 및 DB에 저장하는 모듈입니다.

이 모듈은 다음과 같은 기능을 수행합니다:
1. 대상 규격 데이터를 DB에서 로드
2. 각 규격별로 180일간의 품질 데이터 수집
3. 수집된 데이터를 항목별로 집계
4. 집계 결과를 DB에 저장

Returns:
    None
"""

import sys

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)

import pandas as pd
import numpy as np
import streamlit as st
from typing import List, Dict, Any

from _00_database.db_client import get_client, SQLiteClient
from _01_query.GMES.q_production import curing_prdt_monthly
from _01_query.GMES.q_ncf import ncf_monthly
from _01_query.GMES.q_rr import rr, rr_oe_list
from _01_query.GMES.q_weight import gt_wt_assess
from _01_query.GMES.q_ctl import ctl_raw
from _02_preprocessing import config_pandas
from _02_preprocessing import helper_pandas
from _02_preprocessing import data

# 상수 정의
DB_PATH = "D:/OneDrive - HKNC/@ Project_CQMS/database/goeq_database.db"
ASSESSMENT_PERIOD_DAYS = 180


# 데이터 로드 함수
def load_target_specifications(db_client: SQLiteClient) -> pd.DataFrame:
    """대상 규격 데이터를 DB에서 로드합니다.

    Args:
        db_client: SQLiteClient 인스턴스

    Returns:
        pd.DataFrame: 대상 규격 데이터프레임
    """
    query = """--sql
        SELECT * FROM OE_Assess_Target_Specifications
    """
    df_target = db_client.execute(query)
    return df_target.assign(
        START_MASS_PRODUCTION=pd.to_datetime(
            df_target["START_MASS_PRODUCTION"], errors="coerce"
        ),
    )


# 데이터 수집 함수
def collect_quality_data(
    m_code: str,
    m_code_rr: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> Dict[str, pd.DataFrame]:
    """특정 규격에 대한 품질 데이터를 수집합니다.

    Args:
        m_code: 규격 코드
        m_code_rr: RR 규격 코드
        start_date: 시작일
        end_date: 종료일

    Returns:
        Dict[str, pd.DataFrame]: 수집된 품질 데이터 딕셔너리
    """
    return {
        "prdt": get_client("snowflake").execute(
            curing_prdt_monthly(
                mcode_list=[m_code], yyyy=start_date.year, mm=start_date.month
            )
        ),
        "ncf": get_client("snowflake").execute(
            ncf_monthly(
                mcode_list=[m_code],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
        ),
        "uf": get_client("snowflake").execute(
            rr(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                test_fg="OE",
            )
        ),
        "gt_wt": get_client("snowflake").execute(
            rr(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                test_fg="OE",
            )
        ),
        "rr": get_client("snowflake").execute(
            rr(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                test_fg="OE",
            )
        ),
        "ctl": get_client("snowflake").execute(
            ctl_raw(mcode=m_code, start_date=start_date, end_date=end_date)
        ),
    }


# 데이터 집계 함수
def aggregate_quality_data(
    df_list: Dict[str, List[pd.DataFrame]], criteria_tbl: pd.DataFrame
) -> pd.DataFrame:
    """수집된 품질 데이터를 집계합니다.

    Args:
        df_list: 수집된 데이터 리스트 딕셔너리
        criteria_tbl: 기준 정보 테이블

    Returns:
        pd.DataFrame: 집계된 품질 데이터
    """
    # 데이터프레임 연결
    dfs = {k: pd.concat(v, ignore_index=True) for k, v in df_list.items()}

    # 생산량 집계
    groupby_agg_prdt = (
        dfs["prdt"]
        .groupby("M_CODE")
        .agg(
            MASS_START=("DATE", "min"),
            MASS_END=("DATE", "max"),
            PRDT_QTY=("PRDT_QTY", "sum"),
        )
    )

    # 부적합 집계
    groupby_agg_ncf = (
        dfs["ncf"]
        .groupby("M_CODE")
        .agg(
            DFT_QTY=("DFT_QTY", "sum"),
        )
        .sort_values("DFT_QTY")
    )

    # Uniformity 집계
    df_agg_uf = dfs["uf"].set_index("M_CODE")[
        ["UF_INS_QTY", "UF_PASS_QTY", "PASS_RATE"]
    ]

    # GT Weight 집계
    df_agg_gt_wt = dfs["gt_wt"].set_index("M_CODE")[
        ["WT_INS_QTY", "WT_PASS_QTY", "WT_PASS"]
    ]

    # RR 집계
    rr_criteria = criteria_tbl[["M_CODE", "SPEC_MIN", "SPEC_MAX"]]
    df_agg_rr = pd.merge(dfs["rr"], rr_criteria, how="left", on="M_CODE")

    groupby_agg_rr = df_agg_rr.groupby("M_CODE").agg(
        SPEC_MIN=("SPEC_MIN", "min"),
        SPEC_MAX=("SPEC_MAX", "min"),
        mean=("Result_new", "mean"),
        std=("Result_new", "std"),
        count=("Result_new", "count"),
    )

    groupby_agg_rr = (
        groupby_agg_rr.assign(
            margin=np.minimum(
                (groupby_agg_rr["SPEC_MAX"] - groupby_agg_rr["mean"])
                / (groupby_agg_rr["std"] * 3),
                (groupby_agg_rr["mean"] - groupby_agg_rr["SPEC_MIN"])
                / (groupby_agg_rr["std"] * 3),
            )
        )
        .reset_index(drop=False)
        .merge(
            criteria_tbl[["M_CODE", "M_CODE_RR"]],
            how="left",
            left_on="M_CODE",
            right_on="M_CODE_RR",
        )
        .drop(labels="M_CODE_x", axis=1)
        .rename(columns={"M_CODE_y": "M_CODE"})
        .set_index("M_CODE")
    )

    # CTL 집계
    groupby_agg_ctl = (
        dfs["ctl"]
        .groupby("M_CODE")
        .agg(
            OK=("JDG", lambda x: (x == "OK").sum()),
            NI=("JDG", lambda x: (x == "NI").sum()),
            NO=("JDG", lambda x: (x == "NO").sum()),
        )
    )
    groupby_agg_ctl = groupby_agg_ctl.assign(
        ctl_pass_rate=groupby_agg_ctl["OK"]
        / (groupby_agg_ctl["OK"] + groupby_agg_ctl["NI"])
    )

    # 전체 데이터 병합
    return pd.concat(
        [
            groupby_agg_prdt,
            groupby_agg_ncf,
            df_agg_uf,
            df_agg_gt_wt,
            groupby_agg_rr,
            groupby_agg_ctl,
        ],
        axis=1,
        join="outer",
        ignore_index=False,
    ).reset_index()


# 메인 실행 코드
def main():
    """메인 실행 함수"""
    try:
        # 데이터 로더 초기화
        db_client = SQLiteClient()
        criteria_tbl = db_client.execute("SELECT * FROM OE_Assess_Criteria")

        # 대상 규격 데이터 로드
        df_target = load_target_specifications(db_client)

        # 데이터 수집
        df_list = {"prdt": [], "ncf": [], "uf": [], "gt_wt": [], "rr": [], "ctl": []}

        for _, row in df_target.iterrows():
            if pd.notna(row["START_MASS_PRODUCTION"]):
                start_date = row["START_MASS_PRODUCTION"].date()
                end_date = (
                    row["START_MASS_PRODUCTION"]
                    + pd.Timedelta(days=ASSESSMENT_PERIOD_DAYS)
                ).date()

                quality_data = collect_quality_data(
                    row["M_CODE"], row["M_CODE_RR"], start_date, end_date
                )

                for k, v in quality_data.items():
                    df_list[k].append(v)

        # 데이터 집계
        concat_agg = aggregate_quality_data(df_list, criteria_tbl)

        # DB 저장
        db_client.insert_dataframe(concat_agg, "agg_oe_assess_quality_data")

        st.success("품질 데이터 집계 및 저장이 완료되었습니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        raise


if __name__ == "__main__":
    main()
