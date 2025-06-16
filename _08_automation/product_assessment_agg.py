"""
OE Assessment 결과 집계 스크립트

이 스크립트는 OE Assessment 결과를 집계하고 SQLite 데이터베이스에 저장합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 결과는 mass_assess_result 테이블에 저장됩니다.
"""

# 표준 라이브러리
import os
import sys
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple

# 데이터 처리 및 분석 라이브러리
import numpy as np
import pandas as pd
from scipy.stats import norm

# 프로젝트 루트 경로 설정
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 데이터베이스 및 쿼리 관련 모듈
from _00_database.db_client import get_client
from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_uf import uf_product_assess
from _01_query.GMES.q_weight import gt_wt_assess
from _01_query.GMES.q_ctl import get_ctl_raw_query
from _01_query.helper_sql import format_date_to_yyyymmdd

# 전처리 모듈
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("product_assessment.log"), logging.StreamHandler()],
)


@dataclass
class DateRange:
    start_date: str
    end_date: str
    formatted_start: str
    formatted_end: str


def calculate_pass_rate_with_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """확률밀도함수를 사용하여 합격률을 계산합니다.

    Args:
        df: RR 데이터프레임

    Returns:
        pd.DataFrame: 합격률이 추가된 데이터프레임
    """

    def get_pass_rate(row: pd.Series) -> float:
        if pd.isna(row["SPEC_MAX"]) or pd.isna(row["SPEC_MIN"]):
            return np.nan

        mean, std = row["avg"], row["std"]
        if std == 0 or pd.isna(std):
            return np.nan

        upper_prob = norm.cdf(row["SPEC_MAX"], loc=mean, scale=std)
        lower_prob = norm.cdf(row["SPEC_MIN"], loc=mean, scale=std)
        return upper_prob - lower_prob

    return df.assign(rr_pass_rate_pdf=df.apply(get_pass_rate, axis=1))


def get_date_range(start_date: datetime) -> DateRange:
    """날짜 범위를 계산합니다."""
    end_date = start_date + timedelta(days=180)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    return DateRange(
        start_date=start_date_str,
        end_date=end_date_str,
        formatted_start=format_date_to_yyyymmdd(start_date_str),
        formatted_end=format_date_to_yyyymmdd(end_date_str),
    )


def collect_production_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """생산 데이터를 수집하고 집계합니다."""
    prdt_df = get_client("snowflake").execute(
        curing_prdt_daily(
            mcode_list=[mcode],
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    return (
        prdt_df.groupby(["m_code"])
        .agg(
            min_date=("wrk_date", "min"),
            max_date=("wrk_date", "max"),
            total_qty=("prdt_qty", "sum"),
        )
        .reset_index()
    )


def collect_ncf_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """NCF 데이터를 수집하고 집계합니다."""
    ncf_df = get_client("snowflake").execute(
        ncf_daily(
            mcode_list=[mcode],
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    return ncf_df.groupby(["m_code"]).agg(ncf_qty=("dft_qty", "sum")).reset_index()


def process_ctl_data(ctl_df: pd.DataFrame) -> pd.DataFrame:
    """CTL 데이터를 처리합니다."""
    ctl_df = ctl_df.groupby(["m_code", "jdg"]).size().reset_index(name="count")
    ctl_pivot = ctl_df.pivot(index="m_code", columns="jdg", values="count").fillna(0)

    if "OK" in ctl_pivot.columns and "NI" in ctl_pivot.columns:
        ctl_pivot["ctl_pass_rate"] = ctl_pivot["OK"] / (
            ctl_pivot["NI"] + ctl_pivot["OK"]
        )
    else:
        ctl_pivot["ctl_pass_rate"] = 0

    return ctl_pivot.reset_index()


def merge_all_data(
    prdt_df: pd.DataFrame,
    ncf_df: pd.DataFrame,
    uf_df: pd.DataFrame,
    gt_wt_df: pd.DataFrame,
    rr_df: pd.DataFrame,
    ctl_df: pd.DataFrame,
) -> pd.DataFrame:
    """모든 데이터를 병합합니다."""
    # 컬럼명 통일 (소문자로)
    rr_df = rr_df.rename(columns={"M_CODE": "m_code"})

    return (
        prdt_df.merge(ncf_df, on=["m_code"], how="left")
        .merge(ncf_df, on=["m_code"], how="left")
        .merge(uf_df, on=["m_code"], how="left")
        .merge(gt_wt_df, on=["m_code"], how="left")
        .merge(
            rr_df[["m_code", "count", "rr_pass_rate_pdf"]],
            on=["m_code"],
            how="left",
        )
        .merge(ctl_df[["m_code", "ctl_pass_rate"]], on=["m_code"], how="left")
        .fillna(0)
    )


def process_single_mcode(row: pd.Series) -> pd.DataFrame:
    """단일 M-code에 대한 데이터를 처리합니다."""
    mcode = row["M_CODE"]
    mcode_rr = row["M_CODE_RR"]
    date_range = get_date_range(pd.to_datetime(row["START_MASS_PRODUCTION"]))

    try:
        # 데이터 수집
        prdt_df = collect_production_data(mcode, date_range)
        ncf_df = collect_ncf_data(mcode, date_range)
        uf_df = calculate_uf_pass_rate(
            mcode, date_range.formatted_start, date_range.formatted_end
        )

        gt_wt_df = get_client("snowflake").execute(
            gt_wt_assess(
                mcode_list=mcode,
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
            )
        )

        # RR 데이터 처리
        _, rr_df, _ = get_rr_df(
            mcode_list=mcode_rr,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
        )
        rr_list = get_rr_oe_list_df()
        rr_list = rr_list[rr_list["M_CODE"] == mcode_rr][
            ["M_CODE", "PLANT", "SPEC_MAX", "SPEC_MIN"]
        ]
        # 컬럼명 통일 (소문자로)
        rr_list = rr_list.rename(columns={"M_CODE": "m_code"})
        rr_df = pd.merge(rr_df, rr_list, on=["m_code", "PLANT"], how="left")
        rr_df = calculate_pass_rate_with_pdf(rr_df)

        # CTL 데이터 처리
        ctl_df = get_client("snowflake").execute(
            get_ctl_raw_query(
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
                mcode=mcode,
            )
        )
        ctl_df = process_ctl_data(ctl_df)

        # 데이터 병합
        return merge_all_data(prdt_df, ncf_df, uf_df, gt_wt_df, rr_df, ctl_df)

    except Exception as e:
        logging.error(f"Error processing M-code {mcode}: {str(e)}")
        return pd.DataFrame()


def main():
    try:
        # 타겟 데이터 로드
        target_df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")
        logging.info(f"Loaded {len(target_df)} target records")

        # 각 M-code 처리
        all_results = []
        for _, row in target_df.iterrows():
            result_df = process_single_mcode(row)
            if not result_df.empty:
                all_results.append(result_df)
                logging.info(f"Successfully processed M-code: {row['M_CODE']}")

        if all_results:
            # 결과 저장
            final_df = pd.concat(all_results, ignore_index=True)
            sqlite_client = get_client("sqlite")

            try:
                sqlite_client.execute("DROP TABLE IF EXISTS mass_assess_result")
                logging.info("Existing mass_assess_result table dropped")
            except Exception as e:
                logging.warning(f"Error dropping table: {str(e)}")

            sqlite_client.insert_dataframe(final_df, "mass_assess_result")
            logging.info("Results saved to mass_assess_result table")
        else:
            logging.warning("No data was processed")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
