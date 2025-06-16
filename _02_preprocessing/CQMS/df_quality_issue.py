"""
df_201_weekly_cqms_monitor.py
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import os

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _05_commons import config

from _00_database.db_client import get_client
from _01_query.CQMS import q_quality_issue
from _01_query.HOPE import q_sellin, q_hope
from _02_preprocessing import config_pandas, helper_pandas
from _02_preprocessing.HOPE import df_oeapp
from _02_preprocessing.helper_pandas import (
    CountWorkingDays,
    test_dataframe_by_itself,
    get_weekly_conditions,
)
from _05_commons import config

all_status = ["Open", "Open & Close", "Close", "On-going"]


# func
def calculate_mttc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """MTTC 계산에 필요한 기간 컬럼들을 추가합니다."""
    mttc = CountWorkingDays(
        df,
        "OCC_DATE",
        "REG_DATE",
        "RTN_DATE",
        "CTM_DATE",
        "COMP_DATE",
        "RETURN_YN",
    )
    df["REG_PRD"] = mttc.get_reg_days() - 1
    df["RTN_PRD"] = mttc.get_return_days() - 1
    df["CTM_PRD"] = mttc.get_countermeasure_days() - 1
    df["COMP_PRD"] = mttc.get_8d_report_days() - 1
    df["MTTC"] = df[["REG_PRD", "CTM_PRD", "COMP_PRD"]].sum(axis=1)
    return df


def prepare_qi_base(df: pd.DataFrame, exclude_ot=False) -> pd.DataFrame:
    return (
        helper_pandas.standardize_columns_uppercase(df)
        .pipe(lambda df: df.set_index("DOC_NO"))
        .pipe(
            helper_pandas.convert_date_columns,
            ["OCC_DATE", "REG_DATE", "RTN_DATE", "CTM_DATE", "COMP_DATE"],
        )
        .pipe(
            helper_pandas.convert_category_columns,
            ["PLANT", "OEQ GROUP", "OEM", "TYPE", "STATUS", "LOCATION", "MARKET"],
        )
        .pipe(
            helper_pandas.convert_plant_category,
            config.plant_codes,
            exclude_ot=exclude_ot,
        )
        .pipe(helper_pandas.add_url_column, "SEQ", config_pandas.URL_QUALITY_ISSUE)
    )


# #############################################


@helper_pandas.cache_data_safe(ttl=600)
def load_quality_issues_for_3_years(year) -> pd.DataFrame:
    df = get_client("snowflake").execute(q_quality_issue.query_quality_issue(year))
    df = prepare_qi_base(df)
    df = calculate_mttc_columns(df)

    df = df[~df["LOCATION"].isin(["Internal", "Non-official(In-line)"])]
    df = df.drop(columns=["TYPE_CD", "CAT_CD", "SUB_CAT_CD"], errors="ignore")

    df["YYYY"] = df["REG_DATE"].dt.year
    df["MM"] = df["REG_DATE"].dt.month

    return df


@helper_pandas.cache_data_safe(ttl=600)
def load_sellin_data_for_3_years(year) -> pd.DataFrame:
    sqlite_query = """--sql
    SELECT * 
    FROM sellin_monthly_agg
    """
    df_sellin = get_client("sqlite").execute(sqlite_query)
    df_sellin = helper_pandas.standardize_columns_uppercase(df_sellin)
    df_sellin = df_sellin[df_sellin["RE/OE"] == "OE"]
    df_sellin = df_sellin[
        (df_sellin["YYYY"] >= (str(year - 2))) & (df_sellin["YYYY"] <= (str(year)))
    ]
    df_sellin[["YYYY", "MM"]] = df_sellin[["YYYY", "MM"]].astype("int")

    df_app = df_oeapp.load_oeapp_df()
    df_app = helper_pandas.standardize_columns_uppercase(df_app)
    df_app = df_app[["PLANT", "M_CODE"]].drop_duplicates()

    merge_df = pd.merge(df_sellin, df_app[["PLANT", "M_CODE"]], how="left", on="M_CODE")
    merge_df = (
        merge_df.groupby(["PLANT", "YYYY", "MM"], observed=False)["SUPP_QTY"]
        .sum()
        .reset_index()
    )

    return merge_df


@helper_pandas.cache_data_safe(ttl=600)
def load_sellin_by_ev(year) -> pd.DataFrame:
    df = get_client("snowflake").execute(q_sellin.ev_sellin(year))
    df = (
        helper_pandas.standardize_columns_uppercase(df)
        .groupby("EV", dropna=False)
        .agg(SUPP_QTY=("SUPP_QTY", "sum"))
        .reset_index()
    )
    return df


@helper_pandas.cache_data_safe(ttl=600)
def load_quality_issues_by_week(start_date, end_date) -> pd.DataFrame:
    df = get_client("snowflake").execute(q_quality_issue.query_quality_issue())
    df = prepare_qi_base(df, exclude_ot=True)
    df = calculate_mttc_columns(df)

    df["YYYY"] = df["REG_DATE"].dt.year
    df["MM"] = df["REG_DATE"].dt.month

    df = df.drop(columns=["TYPE_CD", "CAT_CD", "SUB_CAT_CD"], errors="ignore")

    bool_open, bool_close, bool_ongoing1, bool_ongoing2 = get_weekly_conditions(
        df, start_date, end_date
    )
    conditions = [
        bool_open & ~bool_close,
        bool_open & bool_close,
        ~bool_open & bool_close,
        bool_ongoing1 | bool_ongoing2,
    ]
    choices = ["Open", "Open & Close", "Close", "On-going"]

    df["Status"] = np.select(conditions, choices, default=None)
    df["Status"] = pd.Categorical(df["Status"], categories=all_status, ordered=True)
    return df


@helper_pandas.cache_data_safe(ttl=600)
def load_ongoing_quality_issues(plants=None) -> pd.DataFrame:
    df = get_client("snowflake").execute(q_quality_issue.query_quality_issue())

    df = (
        helper_pandas.standardize_columns_uppercase(df)
        .pipe(helper_pandas.convert_date_columns, ["REG_DATE"])
        .pipe(helper_pandas.add_url_column, "SEQ", config_pandas.URL_QUALITY_ISSUE)
    )

    df = df[df["STATUS"] == "On-going"].sort_values(by="REG_DATE")

    if plants:
        df = df[df["PLANT"].isin(plants)]

    return df


@helper_pandas.cache_data_safe(ttl=600)
def summarize_ongoing_quality_by_plant(plants=None) -> pd.DataFrame:
    df = load_ongoing_quality_issues(plants)
    return (
        df.groupby("PLANT")
        .agg(count=("DOC_NO", "count"))
        .sort_values("count", ascending=False)
    )


@helper_pandas.cache_data_safe(ttl=600)
def summarize_ongoing_quality_by_month(plants=None) -> pd.DataFrame:
    df = load_ongoing_quality_issues(plants)
    return df.groupby(pd.Grouper(key="REG_DATE", freq="ME")).agg(
        count=("DOC_NO", "count")
    )


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_plant_monthly(year: int) -> pd.DataFrame:
    df_oeqi = load_quality_issues_for_3_years(year)
    df_sellin = load_sellin_data_for_3_years(year)

    # OEQI 건수 집계
    df_oeqi_grouped = (
        df_oeqi.groupby(["YYYY", "MM", "PLANT"], dropna=False, observed=False)
        .agg(count=("M_CODE", "count"))
        .reset_index()
    )

    merged_df = pd.merge(
        df_oeqi_grouped, df_sellin, on=["YYYY", "MM", "PLANT"], how="outer"
    )
    merged_df["count_cumsum"] = merged_df.groupby(["PLANT", "YYYY"])["count"].transform(
        "cumsum"
    )
    merged_df["SUPP_QTY_cumsum"] = merged_df.groupby(["PLANT", "YYYY"])[
        "SUPP_QTY"
    ].transform("cumsum")
    merged_df["OEQI"] = (
        merged_df["count_cumsum"] / merged_df["SUPP_QTY_cumsum"] * 1_000_000
    )

    return merged_df


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_plant_yearly(year: int) -> pd.DataFrame:
    """연간 OEQI 집계"""

    df_oeqi = load_quality_issues_for_3_years(year)
    df_oeqi = df_oeqi[df_oeqi["YYYY"] == year]
    df_sellin = load_sellin_data_for_3_years(year)
    df_sellin = df_sellin[df_sellin["YYYY"] == year]

    # OEQI 건수 집계
    df_oeqi_grouped = (
        df_oeqi.groupby(["PLANT", "YYYY"], dropna=False, observed=False)
        .agg(
            count=("M_CODE", "count"),
            MTTC=("MTTC", "mean"),
            REG_PRD=("REG_PRD", "mean"),
            RTN_PRD=("RTN_PRD", "mean"),
            CTM_PRD=("CTM_PRD", "mean"),
            COMP_PRD=("COMP_PRD", "mean"),
        )
        .reset_index()
    )

    df_sellin_gruopped = (
        df_sellin.groupby(["PLANT", "YYYY"], dropna=False, observed=False)
        .agg(SUPP_QTY=("SUPP_QTY", "sum"))
        .reset_index()
    )

    # 병합 및 누적 합산
    merged_df = pd.merge(
        df_oeqi_grouped, df_sellin_gruopped, on=["PLANT", "YYYY"], how="outer"
    )
    merged_df["OEQI"] = merged_df["count"] / merged_df["SUPP_QTY"] * 1_000_000
    return merged_df


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_global_monthly(year: int) -> pd.DataFrame:
    """글로벌 전체 기준 월별 OEQI"""
    df_oeqi = load_quality_issues_for_3_years(year)
    df_sellin = load_sellin_data_for_3_years(year)

    groupby_oeqi = (
        df_oeqi.groupby(["YYYY", "MM"], observed=False)
        .agg(count=("PLANT", "count"))
        .reset_index()
    )
    groupby_sellin = (
        df_sellin.groupby(["YYYY", "MM"], observed=False)["SUPP_QTY"]
        .sum()
        .reset_index()
    )

    global_monthly = pd.merge(
        groupby_oeqi, groupby_sellin, "outer", on=["YYYY", "MM"]
    ).fillna(0)

    global_monthly["count_cumsum"] = global_monthly.groupby(["YYYY"])[
        "count"
    ].transform("cumsum")
    global_monthly["SUPP_QTY_cumsum"] = global_monthly.groupby(["YYYY"])[
        "SUPP_QTY"
    ].transform("cumsum")
    global_monthly["OEQI"] = (
        global_monthly["count_cumsum"] / global_monthly["SUPP_QTY_cumsum"] * 1_000_000
    )
    return global_monthly


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_global_yearly(year: int) -> pd.DataFrame:
    df_oeqi = load_quality_issues_for_3_years(year)
    df_sellin = load_sellin_data_for_3_years(year)
    # OEQI 건수 집계
    df_oeqi_grouped = (
        df_oeqi.groupby(["YYYY"], dropna=False, observed=False)
        .agg(
            count=("M_CODE", "count"),
            MTTC=("MTTC", "mean"),
            REG_PRD=("REG_PRD", "mean"),
            RTN_PRD=("RTN_PRD", "mean"),
            CTM_PRD=("CTM_PRD", "mean"),
            COMP_PRD=("COMP_PRD", "mean"),
        )
        .reset_index()
    )
    df_sellin_gruopped = (
        df_sellin.groupby("YYYY", dropna=False, observed=False)
        .agg(SUPP_QTY=("SUPP_QTY", "sum"))
        .reset_index()
    )

    # 병합 및 누적 합산
    merged_df = pd.merge(df_oeqi_grouped, df_sellin_gruopped, on="YYYY", how="outer")
    merged_df["OEQI"] = merged_df["count"] / merged_df["SUPP_QTY"] * 1_000_000

    return merged_df


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_goeq_monthly(year: int) -> pd.DataFrame:
    df_oeqi = load_quality_issues_for_3_years(year)
    df_oeqi = df_oeqi[df_oeqi["YYYY"] == year].copy()

    groupby_oeqi = (
        df_oeqi.groupby(["OEQ GROUP", "MM"], observed=False)
        .agg(count=("PLANT", "count"))
        .reset_index()
    )
    groupby_oeqi.loc[:, "cum_count"] = groupby_oeqi.groupby(
        ["OEQ GROUP"], observed=False
    )["count"].transform("cumsum")

    df_sellin = load_sellin_data_for_3_years(year)
    df_sellin = df_sellin[df_sellin["YYYY"] == year].copy()
    df_sellin["OEQ GROUP"] = df_sellin["PLANT"].map(config.plant_oeqg_dict)

    groupby_sellin = (
        df_sellin.groupby(["OEQ GROUP", "MM"])
        .agg(SUPP_QTY=("SUPP_QTY", "sum"))
        .reset_index()
    )
    groupby_sellin["CUM_SUPP_QTY"] = groupby_sellin.groupby(
        "OEQ GROUP", observed=False
    )["SUPP_QTY"].transform("cumsum")

    merge_df = pd.merge(groupby_oeqi, groupby_sellin, "outer", on=["OEQ GROUP", "MM"])
    merge_df["OEQI"] = merge_df["cum_count"] / merge_df["CUM_SUPP_QTY"] * 1_000_000

    merge_df["OEQ GROUP"] = pd.Categorical(
        merge_df["OEQ GROUP"], categories=config.oeqg_codes
    )
    merge_df = merge_df.sort_values(by=["OEQ GROUP", "MM"])

    return merge_df


@helper_pandas.cache_data_safe(ttl=600)
def aggregate_oeqi_by_goeq_yearly(year: int) -> pd.DataFrame:
    df_oeqi = load_quality_issues_for_3_years(year)
    df_oeqi = df_oeqi[df_oeqi["YYYY"] == year]

    df_oeqi_grouped = (
        df_oeqi.groupby("OEQ GROUP", dropna=False, observed=False)
        .agg(
            count=("M_CODE", "count"),
            MTTC=("MTTC", "mean"),
            REG_PRD=("REG_PRD", "mean"),
            RTN_PRD=("RTN_PRD", "mean"),
            CTM_PRD=("CTM_PRD", "mean"),
            COMP_PRD=("COMP_PRD", "mean"),
        )
        .reset_index()
    )
    df_oeqi_grouped["OEQ GROUP"] = pd.Categorical(
        df_oeqi_grouped["OEQ GROUP"], categories=config.oeqg_codes
    )
    df_oeqi_grouped = df_oeqi_grouped.sort_values(by="OEQ GROUP").reset_index(drop=True)
    return df_oeqi_grouped


@helper_pandas.cache_data_safe(ttl=600)
def compare_quality_by_ev_group(year: int):
    """EV vs 비EV 품질이슈 비교 및 KPI 계산"""

    # EV M_CODE 리스트 조회
    ev_mcode_list = (
        get_client("snowflake").execute(q_hope.ev_mcode_lst())["m_code"].tolist()
    )

    # 해당 연도 OEQI 데이터 조회
    df = load_quality_issues_for_3_years(year).query("YYYY == @year")

    # EV 여부 라벨링
    df["EV"] = df["M_CODE"].apply(lambda x: "Y" if x in ev_mcode_list else "N")

    # EV/비EV 그룹별 건수 집계
    ev_summary = df.groupby("EV", dropna=False).size().reset_index(name="cnt")

    # EV KPI 계산
    ev_sellin_df = load_sellin_by_ev(year)
    ev_kpi = (
        pd.merge(ev_summary, ev_sellin_df, how="inner", on="EV")
        .assign(OEQI=lambda x: x["cnt"] / x["SUPP_QTY"] * 1_000_000)
        .set_index("EV")
    )

    # EV/비EV 주요 SUB_CAT 집계
    def top_subcategories(df_filtered, top_n=7):
        return (
            df_filtered.groupby("SUB_CAT", dropna=False)
            .size()
            .reset_index(name="cnt")
            .sort_values(by="cnt", ascending=False)
            .query("SUB_CAT != 'Etc'")
            .head(top_n)
        )

    ev_top_subcat = top_subcategories(df.query("EV == 'Y'"))
    non_ev_top_subcat = top_subcategories(df.query("EV == 'N'"))

    return df, ev_summary, ev_kpi, ev_top_subcat, non_ev_top_subcat


@helper_pandas.cache_data_safe(ttl=600)
def pivot_quality_by_week_and_status(
    start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """주간 품질이슈를 PLANT별 상태별로 피벗하여 집계합니다."""

    # 주간 데이터 로드 및 초기 정리
    df = load_quality_issues_by_week(start_date, end_date).reset_index()

    # 피벗 테이블 생성
    pivot_df = df.pivot_table(
        index="PLANT",
        columns="Status",
        values="DOC_NO",
        aggfunc="count",
        fill_value=0,
        observed=False,  # category 타입이면 True로 바꿔도 됨
        margins=True,
        margins_name="Global",
    ).reset_index()

    # 컬럼 정렬 (Status 순서 맞추기)
    if "PLANT" in pivot_df.columns:
        ordered_cols = ["PLANT"] + [
            status for status in all_status if status in pivot_df.columns
        ]
        pivot_df = pivot_df.reindex(columns=ordered_cols)

    return pivot_df


def main():
    year = 2024
    start_date = config.a_week_ago
    end_date = config.today

    print(load_quality_issues_for_3_years(year).head())
    print(load_sellin_data_for_3_years(year).head())
    print(load_sellin_by_ev(year).head())
    print(load_quality_issues_by_week(start_date, end_date).head())
    print(load_ongoing_quality_issues().head())
    print(summarize_ongoing_quality_by_plant().head())
    print(summarize_ongoing_quality_by_month().head())

    print(aggregate_oeqi_by_plant_monthly(year).head())
    print(aggregate_oeqi_by_plant_yearly(year).head())
    print(aggregate_oeqi_by_global_monthly(year).head())
    print(aggregate_oeqi_by_global_yearly(year).head())
    print(aggregate_oeqi_by_goeq_monthly(year).head())
    print(aggregate_oeqi_by_goeq_yearly(year).head())

    print(compare_quality_by_ev_group(year)[0].head())
    print(compare_quality_by_ev_group(year)[1].head())
    print(compare_quality_by_ev_group(year)[2].head())
    print(compare_quality_by_ev_group(year)[3].head())
    print(compare_quality_by_ev_group(year)[4].head())
    print(
        pivot_quality_by_week_and_status(
            start_date=start_date, end_date=end_date
        ).head()
    )


if __name__ == "__main__":
    main()
