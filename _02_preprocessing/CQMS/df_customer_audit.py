import sys
import pandas as pd
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database.db_client import get_client
from _01_query.CQMS import q_customer_audit
from _02_preprocessing import config_pandas
from _02_preprocessing.helper_pandas import test_dataframe_by_itself
from _05_commons import config

all_status_for_Audit = ["NEW", "Upcoming", "CLOSE", "Need Update"]


@st.cache_data(ttl=600)
def df_audit_weekly(start_date, end_date):

    df = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
    df.columns = df.columns.str.upper()
    df = df.assign(REG_DT=pd.to_datetime(df["REG_DT"], errors="coerce"))
    df = df.assign(START_DT=pd.to_datetime(df["START_DT"], errors="coerce"))
    df = df.assign(COMP_DT=pd.to_datetime(df["COMP_DT"], errors="coerce"))
    df["URL"] = config_pandas.URL_AUDIT + df["URL"]

    bool_audit_new = (df["REG_DT"] >= start_date) & (df["REG_DT"] <= end_date)
    bool_audit_upcoming = (df["START_DT"] > end_date) & ~bool_audit_new
    bool_audit_close = (
        (df["STATUS"] == "COMPLETE")
        & (df["COMP_DT"] >= start_date)
        & (df["COMP_DT"] <= end_date)
    ) & ~bool_audit_upcoming

    bool_audit_needupdate = (df["START_DT"] < start_date) & (
        (df["COMP_DT"] > end_date) | (df["STATUS"] == "OPEN")
    )

    df.loc[bool_audit_close, "STATUS"] = "CLOSE"
    df.loc[bool_audit_needupdate, "STATUS"] = "Need Update"
    df.loc[bool_audit_upcoming, "STATUS"] = "Upcoming"
    df.loc[bool_audit_new, "STATUS"] = "NEW"

    df["STATUS"] = pd.Categorical(
        df["STATUS"], categories=all_status_for_Audit, ordered=True
    )
    df["PLANT"] = pd.Categorical(
        df["PLANT"], categories=config.plant_codes[:-1], ordered=True
    )
    return df


def df_pivot_audit(start_date, end_date):
    df = df_audit_weekly(start_date, end_date)
    df = (
        df.pivot_table(
            index="PLANT",
            columns="STATUS",
            values="URL",
            margins=True,
            margins_name="Global",
            aggfunc="count",
            fill_value=0,
            observed=False,
        )
        .reset_index()
        .drop(columns="Global")
    )

    return df


@st.cache_data(ttl=600)
def get_audit_ongoing_df(plants=None):
    # 1. 감사 데이터 조회 및 컬럼 대문자화
    df = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
    df.columns = df.columns.str.upper()
    df["URL"] = config_pandas.URL_AUDIT + df["URL"]

    # 2. 조건 정의
    valid_types = ["System", "Project"]
    today = config.today

    # 3. 필터링
    df = df[df["TYPE"].isin(valid_types)]
    df = df[df["STATUS"] == "OPEN"]
    df = df[pd.to_datetime(df["END_DT"]) <= today]

    # 4. 파생 컬럼 생성
    df["END_DT"] = pd.to_datetime(df["END_DT"])
    df["ELAPSED_PERIOD"] = (today - df["END_DT"]).dt.days

    filtered_df = df[df["PLANT"].isin(plants)] if plants else df

    groupby_filtered_df_by_plant = (
        filtered_df.groupby("PLANT")
        .agg(COUNT=("SUBJECT", "count"))
        .sort_values(by="COUNT", ascending=False)
    )

    groupby_filtered_df_by_month = filtered_df.groupby(
        pd.Grouper(key="END_DT", freq="ME")
    ).agg(COUNT=("SUBJECT", "count"))

    return (
        filtered_df,
        groupby_filtered_df_by_plant,
        groupby_filtered_df_by_month,
    )


def main():

    today = config.today
    one_week_ago = config.a_week_ago
    test_dataframe_by_itself(df_audit_weekly, today, one_week_ago)
    test_dataframe_by_itself(df_pivot_audit, today, one_week_ago)
    test_dataframe_by_itself(get_audit_ongoing_df)


if __name__ == "__main__":
    main()
