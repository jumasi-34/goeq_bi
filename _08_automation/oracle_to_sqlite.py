"""
Docstring
"""

import sys
import sqlite3
import pandas as pd

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database.db_client import get_client
from _05_commons import config

if config.DEV_MODE:
    import importlib

    importlib.reload(config)


DB_PATH = config.SQLITE_DB_PATH


query_hope_sellin = """--sql
    SELECT
        "RE/OE",
        "Prod." AS M_CODE,
        SUBSTR("Billing YYYYMM",1,4) AS YYYY,
        SUBSTR("Billing YYYYMM",5,6) AS MM,
        SUM("Qty.") AS SUPP_QTY
    FROM VW_SF_HOPE_SELLIN_SUMMARY
    WHERE SUBSTR("Billing YYYYMM",1,4) >= '2020'
        AND "Data Category" = 'SELLIN'
    GROUP BY
        "RE/OE",
        "Prod.",
        SUBSTR("Billing YYYYMM",1,4),
        SUBSTR("Billing YYYYMM",5,6)
"""


def save_df_to_sqlite(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "replace",
    index: bool = False,
):
    """
    DataFrame을 SQLite DB로 저장합니다.

    Parameters:
        df (pd.DataFrame): 저장할 데이터프레임
        db_path (str): SQLite DB 파일 경로
        table_name (str): 저장할 테이블명
        if_exists (str): 'replace', 'append', 'fail' 중 선택
        index (bool): 인덱스를 DB에 저장할지 여부
    """
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=index)


def generate_sellin_monthly_agg():
    df = get_client("oracle_bi").execute(query_hope_sellin)
    save_df_to_sqlite(df, "sellin_monthly_agg")


def main():
    generate_sellin_monthly_agg()


if __name__ == "__main__":
    main()
