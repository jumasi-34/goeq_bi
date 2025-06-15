import sys
import pandas as pd
import streamlit as st

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)
from _00_database.db_client import get_client
from _01_query.GMES import q_production
from _05_commons import config


@st.cache_data(ttl=600)
def get_yearly_production_df(yyyy: int) -> pd.DataFrame:
    query = q_production.curing_prdt_monthly_by_ym(yyyy=yyyy)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    df = df.groupby("PLANT", as_index=False)["PRDT_QTY"].sum()
    df = df.sort_values(by="PRDT_QTY", ascending=False)
    df = df.assign(
        PLANT=pd.Categorical(df["PLANT"], categories=config.plant_codes, ordered=True)
    ).sort_values(by="PLANT")
    return df
