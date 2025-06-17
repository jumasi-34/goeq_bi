from _00_database.db_client import get_client
import sys
import os
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _05_commons import config
from _05_commons import helper
from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_weight import gt_wt_assess
from _01_query.GMES.q_ctl import get_ctl_raw_query
from _01_query.helper_sql import format_date_to_yyyymmdd
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate

# 테이블 스키마 정의
MASS_ASSESS_RESULT_SCHEMA = [
    ("m_code", "TEXT"),
    ("min_date", "TEXT"),
    ("max_date", "TEXT"),
    ("total_qty", "INTEGER"),
    ("ncf_qty", "INTEGER"),
    ("uf_pass_rate", "REAL"),
    ("gt_wt_pass_rate", "REAL"),
    ("rr_pass_rate_pdf", "REAL"),
    ("ctl_pass_rate", "REAL"),
    ("created_at", "TEXT"),
]


@dataclass
class DateRange:
    start_date: str
    end_date: str
    formatted_start: str
    formatted_end: str


def calculate_pass_rate_with_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """확률밀도함수를 사용하여 합격률을 계산합니다."""

    def get_pass_rate(row: pd.Series) -> float:
        if pd.isna(row["spec_max"]) or pd.isna(row["spec_min"]):
            return np.nan

        mean, std = row["avg"], row["std"]
        if std == 0 or pd.isna(std):
            return np.nan

        upper_prob = norm.cdf(row["spec_max"], loc=mean, scale=std)
        lower_prob = norm.cdf(row["spec_min"], loc=mean, scale=std)
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
    # 컬럼명을 소문자로 변환
    prdt_df.columns = prdt_df.columns.str.lower()
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
    # 컬럼명을 소문자로 변환
    ncf_df.columns = ncf_df.columns.str.lower()
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
    try:
        # 데이터 병합
        result_df = prdt_df.copy()

        # NCF 데이터 병합
        if not ncf_df.empty:
            result_df = result_df.merge(ncf_df, on=["m_code"], how="left")

        # UF 데이터 병합
        if not uf_df.empty:
            result_df = result_df.merge(uf_df, on=["m_code"], how="left")

        # GT weight 데이터 병합
        if not gt_wt_df.empty:
            result_df = result_df.merge(gt_wt_df, on=["m_code"], how="left")

        # RR 데이터 병합
        if not rr_df.empty:
            rr_cols = ["m_code", "count", "rr_pass_rate_pdf"]
            available_cols = [col for col in rr_cols if col in rr_df.columns]
            if available_cols:
                result_df = result_df.merge(
                    rr_df[available_cols], on=["m_code"], how="left"
                )

        # CTL 데이터 병합
        if not ctl_df.empty:
            result_df = result_df.merge(
                ctl_df[["m_code", "ctl_pass_rate"]], on=["m_code"], how="left"
            )

        # 결측값 처리
        result_df = result_df.fillna(0)

        return result_df

    except Exception as e:
        st.error(f"Error in merge_all_data: {str(e)}")
        return pd.DataFrame()


def process_single_mcode(row: pd.Series) -> pd.DataFrame:
    """단일 M-code에 대한 데이터를 처리합니다."""
    mcode = row["M_CODE"]
    mcode_rr = row["M_CODE_RR"]
    date_range = get_date_range(pd.to_datetime(row["START_MASS_PRODUCTION"]))

    try:
        # 데이터 수집
        prdt_df = collect_production_data(mcode, date_range)
        if prdt_df.empty:
            st.warning(f"No production data found for M-code: {mcode}")
            return pd.DataFrame()

        ncf_df = collect_ncf_data(mcode, date_range)
        uf_df = calculate_uf_pass_rate(
            mcode, date_range.formatted_start, date_range.formatted_end
        )
        # UF 데이터 컬럼명 소문자로 변환
        uf_df.columns = uf_df.columns.str.lower()

        gt_wt_df = get_client("snowflake").execute(
            gt_wt_assess(
                mcode_list=mcode,
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
            )
        )
        # GT weight 데이터 컬럼명 소문자로 변환
        gt_wt_df.columns = gt_wt_df.columns.str.lower()

        # RR 데이터 처리
        _, rr_df, _ = get_rr_df(
            mcode_list=mcode_rr,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
        )
        # RR 데이터 컬럼명 소문자로 변환
        rr_df.columns = rr_df.columns.str.lower()

        rr_list = get_rr_oe_list_df()
        # RR 리스트 데이터 컬럼명 소문자로 변환
        rr_list.columns = rr_list.columns.str.lower()

        rr_list = rr_list[rr_list["m_code"] == mcode_rr][
            ["m_code", "plant", "spec_max", "spec_min"]
        ]

        # RR 데이터와 spec 정보 병합
        rr_df = pd.merge(rr_df, rr_list, on=["m_code", "plant"], how="left")

        # 합격률 계산
        rr_df = calculate_pass_rate_with_pdf(rr_df)

        # CTL 데이터 처리
        ctl_df = get_client("snowflake").execute(
            get_ctl_raw_query(
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
                mcode=mcode,
            )
        )
        # CTL 데이터 컬럼명 소문자로 변환
        ctl_df.columns = ctl_df.columns.str.lower()
        ctl_df = process_ctl_data(ctl_df)

        # 데이터 병합
        result_df = merge_all_data(prdt_df, ncf_df, uf_df, gt_wt_df, rr_df, ctl_df)

        if result_df.empty:
            st.warning(f"No data after merging for M-code: {mcode}")
            return pd.DataFrame()

        return result_df

    except Exception as e:
        st.error(f"Error processing M-code {mcode}: {str(e)}")
        return pd.DataFrame()


def main():
    # SQLite 클라이언트 초기화
    sqlite_manager = get_client("sqlite")

    # 타겟 데이터 로드
    target_df = sqlite_manager.execute("SELECT * FROM mass_assess_target")

    # 테스트를 위해 첫 3개 행만 선택
    target_df = target_df.head(3)

    # 각 M-code 처리
    all_results = []
    for idx, row in target_df.iterrows():
        result_df = process_single_mcode(row)
        if not result_df.empty:
            # 생성 시간 추가
            result_df["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_results.append(result_df)

    if all_results:
        # 결과 저장
        final_df = pd.concat(all_results, ignore_index=True)

        # 결과 저장
        try:
            # 기존 데이터 삭제
            sqlite_manager.execute("DELETE FROM mass_assess_result")
        except Exception as e:
            # 새로운 데이터 저장
            sqlite_manager.insert_dataframe(final_df, "mass_assess_result")


main()
