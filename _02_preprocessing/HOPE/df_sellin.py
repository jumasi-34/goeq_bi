import os
import sys
import pandas as pd
from _00_database.db_client import get_client

project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


def get_sellin_df(m_code, start_date, end_date):
    "sqlite에 정제된 쿼리"
    query = f"""
    SELECT * FROM sellin_monthly_agg
    WHERE m_code = '{m_code}'
    """
    df = get_client("sqlite").execute(query)
    df = df.sort_values(by=["YYYY", "MM"]).reset_index(drop=True)
    df["YYYY_MM"] = df["YYYY"].astype(str) + "-" + df["MM"].astype(str).str.zfill(2)
    df = df[df["YYYY_MM"] >= start_date]
    df = df[df["YYYY_MM"] <= end_date]
    return df
