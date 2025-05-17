"""
doc_string
"""

import sys
import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database.db_client import get_client
from _01_query.CQMS import q_4m_change
from _02_preprocessing import config_pandas
from _02_preprocessing import helper_pandas
from _05_commons import config

# 공통 상수
ALL_STATUS = ["Open", "Open & Close", "Close", "On-going"]
EXCLUDED_STATUS = ["Reject(Request)", "Reject(Final Approval)", "Complete", "Saved"]


# ✅ 공통 전처리 유틸
@helper_pandas.cache_data_safe(ttl=600)
def load_4m() -> pd.DataFrame:
    df = get_client("snowflake").execute(q_4m_change.query_4m_change())
    df = helper_pandas.standardize_columns_uppercase(df).pipe(
        helper_pandas.convert_date_columns, ["REG_DATE", "COMP_DATE"]
    )
    df["DOC_NO"] = df["DOC_NO"].str.replace("MANA-DOC-", "4M-", regex=False)
    df["URL"] = config_pandas.URL_CHANGE_4M + df["DOC_NO"]
    return df


@helper_pandas.cache_data_safe(ttl=600)
def filtered_4m_by_weekly(start_date, end_date) -> pd.DataFrame:
    df = load_4m()

    bool_open, bool_close, bool_ongoing1, bool_ongoing2 = (
        helper_pandas.get_weekly_conditions(df, start_date, end_date)
    )

    conditions = [
        bool_open & ~bool_close,
        bool_open & bool_close,
        ~bool_open & bool_close,
        bool_ongoing1 | bool_ongoing2,
    ]
    choices = ALL_STATUS

    df["STATUS"] = np.select(conditions, choices, default=None)
    df["STATUS"] = pd.Categorical(df["STATUS"], categories=ALL_STATUS, ordered=True)

    df["PLANT"] = pd.Categorical(
        df["PLANT"], categories=config.plant_codes[:-1], ordered=True
    )
    return df


@helper_pandas.cache_data_safe(ttl=600)
def df_pivot_4m(start_date, end_date) -> pd.DataFrame:
    df = filtered_4m_by_weekly(start_date, end_date)
    return (
        df.pivot_table(
            index="PLANT",
            columns="STATUS",
            values="DOC_NO",
            aggfunc="count",
            fill_value=0,
            margins=True,
            margins_name="Global",
            observed=False,
        )
        .reset_index()
        .drop(columns="Global")
    )


@helper_pandas.cache_data_safe(ttl=600)
def filtered_4m_ongoing_by_yearly(
    plants=None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = load_4m()
    df = df[~df["STATUS"].isin(EXCLUDED_STATUS)].sort_values(by="REG_DATE")

    df["Elapsed_period"] = config.today - df["REG_DATE"]

    df_na = df[df["PLANT"].isna()]
    df_valid = df.dropna(subset=["PLANT"])
    if plants:
        df_valid = df_valid[df_valid["PLANT"].isin(plants)]

    grouped = (
        df_valid.groupby(
            [
                "DOC_NO",
                "PLANT",
                "PURPOSE",
                "SUBJECT",
                "STATUS",
                "REQUESTER",
                "REG_DATE",
                "URL",
                "Elapsed_period",
            ]
        )["M_CODE"]
        .agg(list)
        .reset_index()
    )

    grouped_by_plant = (
        grouped.groupby("PLANT")
        .agg(COUNT=("DOC_NO", "count"))
        .sort_values("COUNT", ascending=False)
    )

    grouped_by_month = grouped.groupby(pd.Grouper(key="REG_DATE", freq="ME")).agg(
        COUNT=("DOC_NO", "count")
    )

    return df_na, grouped, grouped_by_plant, grouped_by_month


def main():

    today = config.today
    one_week_ago = config.a_week_ago
    helper_pandas.test_dataframe_by_itself(filtered_4m_by_weekly, today, one_week_ago)
    helper_pandas.test_dataframe_by_itself(df_pivot_4m, today, one_week_ago)
    helper_pandas.test_dataframe_by_itself(filtered_4m_ongoing_by_yearly)


if __name__ == "__main__":
    main()
