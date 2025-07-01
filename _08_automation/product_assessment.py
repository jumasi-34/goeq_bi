"""
대량 생산 제품의 품질 평가를 위한 모듈입니다.
생산 데이터, NCF, UF, GT weight, RR, CTL 등의 데이터를 수집하고 분석하여
제품의 품질 지표를 계산합니다.
"""

from _00_database.db_client import get_client
import sys
import os
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_weight import gt_wt_assess
from _01_query.GMES.q_ctl import get_ctl_raw_query
from _01_query.helper_sql import format_date_to_yyyymmdd
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate
from _02_preprocessing.GMES.df_ctl import get_groupby_mcode_ctl_df

# 양산 평가 결과 테이블의 스키마 정의
MASS_ASSESS_RESULT_SCHEMA = [
    ("m_code", "TEXT"),  # 제품 코드
    ("min_date", "TEXT"),  # 최소 날짜
    ("max_date", "TEXT"),  # 최대 날짜
    ("total_qty", "INTEGER"),  # 총 생산량
    ("ncf_qty", "INTEGER"),  # NCF 수량
    ("uf_pass_rate", "REAL"),  # UF 합격률
    ("gt_wt_pass_rate", "REAL"),  # GT weight 합격률
    ("rr_pass_rate_pdf", "REAL"),  # RR 합격률 (PDF 기반)
    ("ctl_pass_rate", "REAL"),  # CTL 합격률
    ("created_at", "TEXT"),  # 생성 시간
]


@dataclass
class DateRange:
    """날짜 범위를 저장하는 데이터 클래스"""

    start_date: str  # 시작 날짜 (YYYY-MM-DD)
    end_date: str  # 종료 날짜 (YYYY-MM-DD)
    formatted_start: str  # 시작 날짜 (YYYYMMDD)
    formatted_end: str  # 종료 날짜 (YYYYMMDD)


def calculate_pass_rate_with_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """
    확률밀도함수를 사용하여 합격률을 계산합니다.

    Args:
        df (pd.DataFrame): 평균과 표준편차가 포함된 데이터프레임

    Returns:
        pd.DataFrame: 합격률이 추가된 데이터프레임
    """

    def get_pass_rate(row: pd.Series) -> float:
        """개별 행에 대한 합격률을 계산합니다."""
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
    """
    주어진 시작 날짜로부터 180일 범위의 날짜를 계산합니다.

    Args:
        start_date (datetime): 시작 날짜

    Returns:
        DateRange: 계산된 날짜 범위
    """
    # None, NaT, 또는 유효하지 않은 날짜 처리
    if start_date is None or pd.isna(start_date):
        raise ValueError("시작 날짜가 None이거나 유효하지 않습니다.")

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
    """
    생산 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        date_range (DateRange): 날짜 범위

    Returns:
        pd.DataFrame: 집계된 생산 데이터
    """
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
    """
    NCF 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        date_range (DateRange): 날짜 범위

    Returns
    -------
    pd.DataFrame: 집계된 NCF 데이터
    """
    ncf_df = get_client("snowflake").execute(
        ncf_daily(
            mcode=mcode,
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    # 컬럼명을 소문자로 변환
    ncf_df.columns = ncf_df.columns.str.lower()
    return ncf_df.groupby(["m_code"]).agg(ncf_qty=("dft_qty", "sum")).reset_index()


def collect_uf_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """
    UF 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        date_range (DateRange): 날짜 범위

    Returns:
        pd.DataFrame: 집계된 UF 데이터
    """
    uf_df = calculate_uf_pass_rate(
        mcode, date_range.formatted_start, date_range.formatted_end
    )
    # UF 데이터 컬럼명 소문자로 변환
    uf_df.columns = uf_df.columns.str.lower()

    # m_code 기준으로 집계 (여러 공장/규격의 평균 계산)
    if not uf_df.empty:
        return (
            uf_df.groupby(["m_code"])
            .agg(
                uf_pass_rate=("uf_pass_rate", "mean"),  # 평균 합격률
                uf_ins_qty=("uf_ins_qty", "sum"),  # 총 검사 수량
                uf_pass_qty=("uf_pass_qty", "sum"),  # 총 합격 수량
            )
            .reset_index()
        )
    return pd.DataFrame()


def collect_gt_weight_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """
    GT weight 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        date_range (DateRange): 날짜 범위

    Returns:
        pd.DataFrame: 집계된 GT weight 데이터
    """
    gt_wt_df = get_client("snowflake").execute(
        gt_wt_assess(
            mcode_list=mcode,
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    # GT weight 데이터 컬럼명 소문자로 변환
    gt_wt_df.columns = gt_wt_df.columns.str.lower()

    # m_code 기준으로 집계
    if not gt_wt_df.empty:
        aggregated_df = (
            gt_wt_df.groupby(["m_code"])
            .agg(
                gt_wt_ins_qty=("wt_ins_qty", "sum"),  # 총 검사 수량
                gt_wt_pass_qty=("wt_pass_qty", "sum"),  # 총 합격 수량
            )
            .reset_index()
        )

        # 합격률 계산
        aggregated_df["gt_wt_pass_rate"] = aggregated_df.apply(
            lambda row: (
                row["gt_wt_pass_qty"] / row["gt_wt_ins_qty"]
                if row["gt_wt_ins_qty"] > 0
                else 0
            ),
            axis=1,
        )

        return aggregated_df
    return pd.DataFrame()


def collect_rr_data(mcode: str, mcode_rr: str, date_range: DateRange) -> pd.DataFrame:
    """
    RR 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        mcode_rr (str): RR 제품 코드
        date_range (DateRange): 날짜 범위

    Returns:
        pd.DataFrame: 집계된 RR 데이터
    """
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

    # m_code 기준으로 집계 (여러 공장의 평균 계산)
    if not rr_df.empty:
        return (
            rr_df.groupby(["m_code"])
            .agg(
                rr_pass_rate_pdf=("rr_pass_rate_pdf", "mean"),  # 평균 합격률
                count=("count", "sum"),  # 총 측정 수량
            )
            .reset_index()
        )
    return pd.DataFrame()


def collect_ctl_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """
    CTL 데이터를 수집하고 집계합니다.

    Args:
        mcode (str): 제품 코드
        date_range (DateRange): 날짜 범위

    Returns:
        pd.DataFrame: 집계된 CTL 데이터
    """
    ctl_df = get_groupby_mcode_ctl_df(
        mcode=mcode,
        start_date=date_range.formatted_start,
        end_date=date_range.formatted_end,
    )
    # CTL 데이터 컬럼명 소문자로 변환
    ctl_df.columns = ctl_df.columns.str.lower()

    # 이미 m_code 기준으로 집계되어 있으므로 그대로 반환
    return ctl_df


def merge_all_data(
    target_df: pd.DataFrame,
    prdt_df: pd.DataFrame,
    ncf_df: pd.DataFrame,
    uf_df: pd.DataFrame,
    gt_wt_df: pd.DataFrame,
    rr_df: pd.DataFrame,
    ctl_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    모든 데이터를 병합하여 최종 결과를 생성합니다.
    각 데이터프레임은 이미 m_code 기준으로 집계되어 있습니다.

    Args:
        target_df (pd.DataFrame): 타겟 데이터프레임
        prdt_df (pd.DataFrame): 생산 데이터 (m_code 기준 집계)
        ncf_df (pd.DataFrame): NCF 데이터 (m_code 기준 집계)
        uf_df (pd.DataFrame): UF 데이터 (m_code 기준 집계)
        gt_wt_df (pd.DataFrame): GT weight 데이터 (m_code 기준 집계)
        rr_df (pd.DataFrame): RR 데이터 (m_code 기준 집계)
        ctl_df (pd.DataFrame): CTL 데이터 (m_code 기준 집계)

    Returns:
        pd.DataFrame: 병합된 최종 결과
    """
    try:
        # 타겟 데이터프레임 복사 및 컬럼명 소문자로 변환
        result_df = target_df.copy()
        result_df.columns = result_df.columns.str.lower()

        # 각 데이터프레임을 순차적으로 병합 (모두 m_code 기준으로 집계되어 있음)
        dataframes = [
            ("prdt", prdt_df),
            ("ncf", ncf_df),
            ("uf", uf_df),
            ("gt_wt", gt_wt_df),
            ("rr", rr_df),
            ("ctl", ctl_df),
        ]

        for name, df in dataframes:
            if not df.empty:
                # 필요한 컬럼만 선택하여 병합
                if name == "prdt":
                    merge_cols = ["m_code", "min_date", "max_date", "total_qty"]
                elif name == "ncf":
                    merge_cols = ["m_code", "ncf_qty"]
                elif name == "uf":
                    merge_cols = ["m_code", "uf_pass_rate"]
                elif name == "gt_wt":
                    merge_cols = ["m_code", "gt_wt_pass_rate"]
                elif name == "rr":
                    merge_cols = ["m_code", "rr_pass_rate_pdf"]
                elif name == "ctl":
                    merge_cols = ["m_code", "ctl_pass_rate"]

                # 존재하는 컬럼만 선택
                available_cols = [col for col in merge_cols if col in df.columns]
                if available_cols:
                    result_df = result_df.merge(
                        df[available_cols], on="m_code", how="left"
                    )

        # 결측값 처리
        result_df = result_df.fillna(0)

        return result_df

    except Exception as e:
        st.error(f"Error in merge_all_data: {str(e)}")
        return pd.DataFrame()


def process_single_mcode(target_df: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    """단일 M-code에 대한 데이터를 처리합니다."""
    mcode = row["M_CODE"]
    mcode_rr = row["M_CODE_RR"]

    # START_MASS_PRODUCTION 값 검증
    start_mass_production = row["START_MASS_PRODUCTION"]
    if pd.isna(start_mass_production) or start_mass_production is None:
        st.warning(f"START_MASS_PRODUCTION 값이 없습니다. M-code: {mcode}")
        return pd.DataFrame()

    try:
        start_date = pd.to_datetime(start_mass_production)
        if pd.isna(start_date):
            st.warning(
                f"START_MASS_PRODUCTION 날짜 변환 실패. M-code: {mcode}, 값: {start_mass_production}"
            )
            return pd.DataFrame()

        date_range = get_date_range(start_date)
    except Exception as e:
        st.error(f"날짜 범위 계산 중 오류 발생. M-code: {mcode}, 오류: {str(e)}")
        return pd.DataFrame()

    try:
        # 현재 처리 중인 m_code의 행만 선택
        current_target_df = pd.DataFrame([row])

        # 데이터 수집
        prdt_df = collect_production_data(mcode, date_range)
        if prdt_df.empty:
            st.warning(f"No production data found for M-code: {mcode}")
            return pd.DataFrame()

        ncf_df = collect_ncf_data(mcode, date_range)
        uf_df = collect_uf_data(mcode, date_range)
        gt_wt_df = collect_gt_weight_data(mcode, date_range)
        rr_df = collect_rr_data(mcode, mcode_rr, date_range)
        ctl_df = collect_ctl_data(mcode, date_range)

        # 데이터 병합 (현재 m_code의 행만 사용)
        result_df = merge_all_data(
            current_target_df, prdt_df, ncf_df, uf_df, gt_wt_df, rr_df, ctl_df
        )

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
    # target_df = target_df.head(3)

    # 각 M-code 처리
    all_results = []
    for idx, row in target_df.iterrows():
        result_df = process_single_mcode(target_df, row)
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
