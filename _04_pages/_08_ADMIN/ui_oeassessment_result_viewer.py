"""
OE Assessment 결과 조회 페이지

이 페이지는 OE Assessment 결과를 조회하고 표시하는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 사용자는 결과를 확인할 수 있습니다.
"""

import numpy as np
from scipy.stats import norm
import pandas as pd
import streamlit as st
from _00_database.db_client import get_client
from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_uf import uf_product_assess
from _01_query.GMES.q_weight import gt_wt_assess
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate
from _01_query.helper_sql import format_date_to_yyyymmdd
from _01_query.GMES.q_ctl import get_ctl_raw_query

# 메인 페이지 코드
st.title("OE Assessment Result Viewer")

target_df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")

# 데이터 표시
st.subheader("Assessment Target")
st.dataframe(target_df)

# 결과를 저장할 리스트
all_results = []


# RR 데이터에 대한 확률밀도함수 기반 합격률 계산
def calculate_pass_rate_with_pdf(df):
    """확률밀도함수를 사용하여 합격률을 계산합니다.

    Args:
        df: RR 데이터프레임

    Returns:
        pd.DataFrame: 합격률이 추가된 데이터프레임
    """

    # 정규분포 기반 확률밀도함수 계산
    def get_pass_rate(row):
        if pd.isna(row["SPEC_MAX"]) or pd.isna(row["SPEC_MIN"]):
            return np.nan

        mean = row["avg"]
        std = row["std"]

        if std == 0 or pd.isna(std):
            return np.nan

        # 상한/하한 기준으로 정규분포 누적확률 계산
        upper_prob = norm.cdf(row["SPEC_MAX"], loc=mean, scale=std)
        lower_prob = norm.cdf(row["SPEC_MIN"], loc=mean, scale=std)

        # 합격률 = 상한 누적확률 - 하한 누적확률
        pass_rate = upper_prob - lower_prob

        return pass_rate

    # 합격률 계산 적용
    df = df.assign(rr_pass_rate_pdf=df.apply(get_pass_rate, axis=1))

    return df


# target_df의 각 M-code에 대해 반복
for _, row in target_df.iterrows():
    mcode = row["M_CODE"]
    mcode_rr = row["M_CODE_RR"]

    # 날짜 형식 변환 및 검증
    try:
        start_date = pd.to_datetime(row["START_MASS_PRODUCTION"])
        end_date = start_date + pd.DateOffset(days=180)

        # datetime 객체를 문자열로 변환 (YYYY-MM-DD 형식)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        formatted_start_date = format_date_to_yyyymmdd(start_date_str)
        formatted_end_date = format_date_to_yyyymmdd(end_date_str)

    except Exception as e:
        st.error(f"날짜 변환 중 오류 발생 (M-code: {mcode}): {str(e)}")
        continue

    # prdt
    prdt_df = get_client("snowflake").execute(
        curing_prdt_daily(
            mcode_list=[mcode],
            start_date=formatted_start_date,
            end_date=formatted_end_date,
        )
    )
    prdt_df = (
        prdt_df.groupby(["m_code"])
        .agg(
            min_date=("wrk_date", "min"),
            max_date=("wrk_date", "max"),
            total_qty=("prdt_qty", "sum"),
        )
        .reset_index()
    )
    # ncf
    ncf_df = get_client("snowflake").execute(
        ncf_daily(
            mcode_list=[mcode],
            start_date=formatted_start_date,
            end_date=formatted_end_date,
        )
    )
    ncf_df = ncf_df.groupby(["m_code"]).agg(ncf_qty=("dft_qty", "sum")).reset_index()

    # uf
    uf_df = calculate_uf_pass_rate(
        mcode=mcode, start_date=formatted_start_date, end_date=formatted_end_date
    )
    uf_df = uf_df.assign(
        uf_ins_qty=lambda x: x["uf_ins_qty"].astype(int),
        uf_pass_qty=lambda x: x["uf_pass_qty"].astype(int),
        pass_rate=lambda x: x["pass_rate"].astype(float),
    )

    # weight
    gt_wt_df = get_client("snowflake").execute(
        gt_wt_assess(
            mcode_list=mcode,
            start_date=formatted_start_date,
            end_date=formatted_end_date,
        )
    )

    gt_wt_df = gt_wt_df.assign(
        wt_ins_qty=lambda x: x["wt_ins_qty"].astype(int),
        wt_pass_qty=lambda x: x["wt_pass_qty"].astype(int),
        wt_pass_rate=lambda x: x["wt_pass_qty"] / x["wt_ins_qty"],
    )

    # rr
    try:
        _, rr_df, _ = get_rr_df(
            mcode_list=mcode_rr,
            start_date=start_date_str,
            end_date=end_date_str,
        )
        rr_list = get_rr_oe_list_df()
        rr_list = rr_list[rr_list["M_CODE"] == mcode_rr][
            ["M_CODE", "PLANT", "SPEC_MAX", "SPEC_MIN"]
        ]
        rr_df = pd.merge(rr_df, rr_list, on=["M_CODE", "PLANT"], how="left")
        rr_df = calculate_pass_rate_with_pdf(rr_df)
    except Exception as e:
        st.error(f"RR 데이터 처리 중 오류 발생 (M-code: {mcode_rr}): {str(e)}")
        continue

    # ctl
    ctl_df = get_client("snowflake").execute(
        get_ctl_raw_query(
            start_date=formatted_start_date,
            end_date=formatted_end_date,
            mcode=mcode,
        )
    )

    # JDG 컬럼의 항목별 개수를 계산하고 합격률을 계산
    ctl_df = (
        ctl_df.groupby(["m_code", "jdg"])
        .size()
        .reset_index(name="count")
        .pivot(index="m_code", columns="jdg", values="count")
        .fillna(0)
    )

    # 합격률 계산: OK / (NI + OK)
    # OK와 NI 컬럼이 모두 있는 경우에만 계산
    if "OK" in ctl_df.columns and "NI" in ctl_df.columns:
        ctl_df["ctl_pass_rate"] = ctl_df["OK"] / (ctl_df["NI"] + ctl_df["OK"])
    else:
        # OK나 NI 컬럼이 없는 경우 0으로 설정
        ctl_df["ctl_pass_rate"] = 0

    ctl_df = ctl_df.reset_index()

    # 데이터 병합
    merged_df = (
        pd.merge(prdt_df, ncf_df, on=["m_code"], how="left")
        .merge(ncf_df, on=["m_code"], how="left")
        .merge(uf_df, on=["m_code"], how="left")
        .merge(gt_wt_df, on=["m_code"], how="left")
        .merge(
            rr_df[["M_CODE", "count", "rr_pass_rate_pdf"]],
            left_on=["m_code"],
            right_on=["M_CODE"],
            how="left",
        )
        .merge(ctl_df[["m_code", "ctl_pass_rate"]], on=["m_code"], how="left")
        .fillna(0)
    )

    # 결과를 리스트에 추가
    all_results.append(merged_df)


# 모든 결과를 하나의 데이터프레임으로 결합
if all_results:
    final_df = pd.concat(all_results, ignore_index=True)
    st.subheader("모든 M-code의 집계 결과")
    st.dataframe(final_df)
else:
    st.warning("처리된 데이터가 없습니다.")
