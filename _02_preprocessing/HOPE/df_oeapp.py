"""
df_402_fm_monitoring.py
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _05_commons import config

from _00_database.db_client import get_client
from _01_query.GMES import q_production
from _01_query.HOPE import q_hope
from _02_preprocessing import helper_pandas


def load_oeapp_df():
    df = get_client("snowflake").execute(q_hope.CTE_HOPE_OE_APP_ALL)
    return df


def load_oeapp_df_by_mcode(m_code):
    df = get_client("snowflake").execute(q_hope.CTE_HOPE_OE_APP_ALL)
    df.columns = df.columns.str.upper()
    df = df[df["M_CODE"] == m_code]
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
