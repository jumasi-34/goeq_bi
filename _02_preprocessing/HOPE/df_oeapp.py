"""
df_402_fm_monitoring.py
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _00_database.db_client import get_client
from _01_query.GMES import q_production
from _01_query.HOPE import q_hope
from _02_preprocessing.helper_pandas import CountWorkingDays, test_dataframe_by_itself


def load_oeapp_df():
    df = get_client("snowflake").execute(q_hope.CTE_HOPE_OE_APP_ALL)
    return df


def oe_sku():
    df = load_oeapp_df()
    df = df[df["Status"] == "Supplying"][["plant", "m_code"]]
    df = (
        df.groupby("plant")
        .count()
        .sort_values(by="m_code", ascending=False)
        .reset_index()
    )
    return df
