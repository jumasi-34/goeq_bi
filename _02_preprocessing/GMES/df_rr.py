"""
df_402_fm_monitoring.py
"""

import sys

# from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.GMES import q_rr
from _00_database.db_client import get_client

# from _02_preprocessing import config
from _02_preprocessing.helper_pandas import test_dataframe_by_itself
from _05_commons import config

## MES RR
ISO_LST = [
    "ISO 28580 (AUDI)",
    "ISO 28580 (EU)",
    "ISO 28580 (HKMC)",
    "ISO 28580 (R&D#2)",
    "ISO 28580 (R&D#3)",
    "ISO 28580 (TOYOTA_2013)",
    "ISTO 28580 (TOYOTA_2018)",
]
SVP_LST = ["SVP (HKMC)", "SVP (HONDA)", "SVP (NISSAN)"]
SAE_LST = [
    "SAE-J2452",
    "SAE-J2452(Ford_2016)",
    "SAE-J2452(Ford_2020)",
    "SAE-J2452(GM_1.7)",
    "SAE-J2452(GM_2.0)",
    "SAE-J2452(Tesla)",
]


# 범주-색상 매핑
cat_color_map = {
    "<50%": "red",
    "<70%": "orange",
    "<80%": "yellow",
    "<90%": "lightgreen",
    "<95%": "green",
    "Above 95%": "darkgreen",
}

# 전처리


@st.cache_data(ttl=600)
def preprocess_iso_data(df, corr_df):

    iso_df = df[df["OE_TEST_METHOD"].isin(ISO_LST)]
    remain_cols = ["PLANT", "POSITION", "Slope", "Intercept"]
    corr_local = corr_df[
        (corr_df["OE_RR_TEST_METHOD"] == "-") & (corr_df["METHOD"] == "ISO")
    ][remain_cols]
    iso_df = iso_df.merge(
        corr_local.rename(columns={"Slope": "A", "Intercept": "B"}),
        on=["PLANT", "POSITION"],
        how="left",
    )

    corr_rnd = corr_df[(corr_df["POSITION"] == "-") & (corr_df["METHOD"] == "ISO")][
        ["OE_RR_TEST_METHOD", "Slope", "Intercept"]
    ]
    corr_rnd = corr_rnd.rename(columns={"Slope": "C", "Intercept": "D"})
    iso_df = iso_df.merge(
        corr_rnd, how="left", left_on="OE_TEST_METHOD", right_on="OE_RR_TEST_METHOD"
    ).drop(columns="OE_RR_TEST_METHOD")
    return iso_df


@st.cache_data(ttl=600)
def preprocess_svp_data(df, corr_df):
    svp_df = df[df["OE_TEST_METHOD"].isin(SVP_LST)].copy()
    svp_df["POSITION"] = svp_df["POSITION"].str.upper()

    remain_cols = ["PLANT", "POSITION", "OE_RR_TEST_METHOD", "Slope", "Intercept"]

    corr_svp = corr_df[corr_df["METHOD"] == "SVP"][remain_cols].copy()
    corr_svp["POSITION"] = corr_svp["POSITION"].str.upper()
    corr_svp = corr_svp.rename(
        columns={"Slope": "A", "Intercept": "B", "OE_RR_TEST_METHOD": "OE_TEST_METHOD"}
    )

    svp_df = svp_df.merge(
        corr_svp, on=["PLANT", "POSITION", "OE_TEST_METHOD"], how="left"
    )

    svp_df[["C", "D"]] = [1, 0]  # 임의 값
    return svp_df


@st.cache_data(ttl=600)
def preprocess_sae_data(df):
    sae_df = df[df["OE_TEST_METHOD"].isin(SAE_LST)].copy()
    sae_df["Result_new"] = sae_df["TEST_RESULT_OLD"]
    return sae_df


@st.cache_data(ttl=600)
def apply_product_specific_factors(df):
    factors = {
        "1020898": 0.9055,
        "1017808": 0.9400,
        "1021593": 0.9732,
        "1018940": 0.9055,
    }
    for mcode, factor in factors.items():
        df.loc[df["M_CODE"] == mcode, "Result_new"] *= factor
    return df


@st.cache_data(ttl=600)
def apply_hkmc_formula(df):
    slope = 0.9035
    intercept = -3.4652
    kgf_to_n = 9.80665

    mask = df["OE_TEST_METHOD"] == "SVP (HKMC)"
    result = df.loc[mask, "Result_new"]
    load = df.loc[mask, "WARM_LOAD"]

    df.loc[mask, "Result_new"] = (
        ((result * load * kgf_to_n / 1000) * slope + intercept) * 1000
    ) / (load * kgf_to_n)
    return df


# 집계
@st.cache_data(ttl=600)
def calc_epass(df: pd.DataFrame, merge_source: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(merge_source, how="left", on=["PLANT", "M_CODE"])

    # std가 0 또는 NaN인 경우 계산 제외
    valid = df["std"].notna() & (df["std"] != 0)

    df = df.assign(
        Offset=(df["avg"] - df["CL"]) / df["CL"],
        CP=(df["e_max"] - df["e_min"]) / (df["std"] * 6),
        EPass=np.nan,  # 초기화
    )

    df.loc[valid, "EPass"] = norm.cdf(
        df.loc[valid, "e_max"], loc=df.loc[valid, "avg"], scale=df.loc[valid, "std"]
    ) - norm.cdf(
        df.loc[valid, "e_min"], loc=df.loc[valid, "avg"], scale=df.loc[valid, "std"]
    )

    # 범주 및 색상 매핑
    bins = [0, 0.5, 0.7, 0.8, 0.9, 0.95, 1]
    labels = ["<50%", "<70%", "<80%", "<90%", "<95%", "Above 95%"]
    df["EPass_cat"] = pd.cut(df["EPass"], bins=bins, labels=labels)
    df["color"] = df["EPass_cat"].map(cat_color_map)

    # 불필요 컬럼 제거
    del_cols = ["START_DATE", "END_DATE", "CHG_APP_DATE", "SPEC_CHANGE", "SELANT_FLG"]
    df = df.drop(columns=[col for col in del_cols if col in df.columns])

    return df


# main 함수
@st.cache_data(ttl=600)
def get_rr_df(
    start_date: str | None = None,
    end_date: str | None = None,
    test_fg: str = "OE",
    break_date: str | None = None,
    mcode_list: list[str] | str | int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    df = get_client("snowflake").execute(q_rr.rr(start_date, end_date, test_fg))
    df.columns = df.columns.str.upper()

    iso = preprocess_iso_data(df, q_rr.rr_corr_csv)
    svp = preprocess_svp_data(df, q_rr.rr_corr_csv)
    sae = preprocess_sae_data(df)

    # 결과 병합 및 계산
    rr_concat = pd.concat([iso, svp])
    # 보정식: Result_new = ((RRC × A + B) × C + D)
    rr_concat["Result_new"] = (
        rr_concat["RRC"] * rr_concat["A"] + rr_concat["B"]
    ) * rr_concat["C"] + rr_concat["D"]
    rr_concat = rr_concat.drop(columns=["A", "B", "C", "D"])
    rr_concat = pd.concat([rr_concat, sae])

    rr_concat = apply_product_specific_factors(rr_concat)
    rr_concat = apply_hkmc_formula(rr_concat)

    rr_raw = rr_concat.drop(columns=["RRC", "HK_GLOBAL", "WARM_LOAD"])
    rr_raw[["SMPL_DATE", "START_DT", "END_DT"]] = rr_raw[
        ["SMPL_DATE", "START_DT", "END_DT"]
    ].apply(pd.to_datetime)
    rr_raw = rr_raw.reset_index(drop=True)

    # 비교 집계
    rr_raw_compare = None
    if break_date:
        rr_raw_compare = rr_raw.copy()
        rr_raw_compare["PRE_POST"] = np.where(
            rr_raw_compare["SMPL_DATE"] < break_date, "PRE", "POST"
        )
        rr_raw_compare = rr_raw_compare.groupby(
            ["PRE_POST", "PLANT", "M_CODE"], as_index=False
        ).agg(
            avg=("Result_new", "mean"),
            std=("Result_new", "std"),
            count=("Result_new", "count"),
        )

    rr_raw_agg = rr_raw.groupby(["PLANT", "M_CODE"], as_index=False).agg(
        avg=("Result_new", "mean"),
        std=("Result_new", "std"),
        count=("Result_new", "count"),
    )

    if mcode_list:
        if isinstance(mcode_list, (int, str)):
            mcode_list = [mcode_list]
        rr_raw = rr_raw[rr_raw["M_CODE"].isin(mcode_list)]
        rr_raw_agg = rr_raw_agg[rr_raw_agg["M_CODE"].isin(mcode_list)]

    return (
        rr_raw,
        rr_raw_agg,
        rr_raw_compare,
    )  # raw sample, aggregated, pre/post comparison


@st.cache_data(ttl=600)
def get_rr_oe_list_df():
    df = get_client("snowflake").execute(q_rr.rr_oe_list())
    df.columns = df.columns.str.upper()

    # 날짜 필터 범위 상수
    valid_date_range = ("1900-01-01", "2100-12-31")

    # 날짜 유효성 필터링 함수
    def filter_valid_date_range(df, column):
        return df[column].isnull() | (
            (df[column] >= valid_date_range[0]) & (df[column] <= valid_date_range[1])
        )

    # 날짜 유효성 필터 적용
    for col in ["START_DATE", "END_DATE", "CHG_APP_DATE"]:
        df = df[filter_valid_date_range(df, col)]

    # assign으로 숫자 변환과 날짜 변환 한 번에 처리
    df = df.assign(
        **{
            "RR_INDEX": pd.to_numeric(df["RR_INDEX"], errors="coerce"),
            "SPEC_MAX": pd.to_numeric(df["SPEC_MAX"], errors="coerce"),
            "SPEC_MIN": pd.to_numeric(df["SPEC_MIN"], errors="coerce"),
            "START_DATE": pd.to_datetime(
                df["START_DATE"], format="%Y%m%d", errors="coerce"
            ),
            "END_DATE": pd.to_datetime(
                df["END_DATE"], format="%Y%m%d", errors="coerce"
            ),
            "CHG_APP_DATE": pd.to_datetime(
                df["CHG_APP_DATE"], format="%Y%m%d", errors="coerce"
            ),
        }
    )

    # LIMIT 구분 및 계산
    usl_only = df["SPEC_MIN"] == 0
    df = df.assign(
        limit=np.where(usl_only, "USL only", "Nominal"),
        e_max=np.where(
            usl_only, np.minimum(df["SPEC_MAX"], df["RR_INDEX"] + 0.3), df["SPEC_MAX"]
        ),
        e_min=np.where(usl_only, df["RR_INDEX"] - 0.3, df["SPEC_MIN"]),
    )
    df = df.assign(CL=(df["e_max"] + df["e_min"]) / 2)
    # endregion

    # Spec_Max 정보가 없는 규격은 삭제
    df = df.dropna(subset=["SPEC_MAX"])

    return df.reset_index(drop=True)


# @st.cache_data(show_spinner=True, ttl=600)  # 10분마다 캐시 갱신
@st.cache_data(ttl=600)
def get_processed_agg_rr_data(start_date=None, end_date=None):
    _, rr_raw_agg, _ = get_rr_df(start_date, end_date)
    rr_oe_list = get_rr_oe_list_df()
    df = calc_epass(rr_raw_agg, rr_oe_list).reset_index(drop=True)
    return df


# @st.cache_data(show_spinner=True)
@st.cache_data(ttl=600)
def get_processed_raw_rr_data(start_date, end_date, mcode):
    rr_raw, _, _ = get_rr_df(start_date=start_date, end_date=end_date)
    rr_oe_list = get_rr_oe_list_df()
    rr_individual = rr_raw[rr_raw["M_CODE"] == mcode]
    rr_individual = rr_individual.merge(rr_oe_list, how="left", on="M_CODE")

    rr_individual["SPEC_MIN"] = rr_individual["SPEC_MIN"].fillna(0)

    rr_individual = rr_individual.reset_index(drop=True)

    return rr_individual


def main():
    # ? TEST 기간동안 M-Code 이력이 없을 수 있음을 감안해야함
    today = config.today
    one_year_ago = config.one_year_ago
    selected_mcode = "1032181"

    test_dataframe_by_itself(get_rr_df, mcode_list=selected_mcode)
    test_dataframe_by_itself(get_rr_oe_list_df)
    test_dataframe_by_itself(
        get_processed_raw_rr_data,
        start_date=one_year_ago,
        end_date=today,
        mcode=selected_mcode,
    )


if __name__ == "__main__":
    main()
