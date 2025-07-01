"""
Test page for debugging and validating data processing functions.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Optional, Dict, Any

from _00_database.db_client import get_client
from _01_query.GMES import q_production, q_ncf
from _02_preprocessing.GMES import df_uf

db_client = get_client("sqlite")


# 테스트용 데이터프레임 생성
insight_df = pd.DataFrame(
    {
        "M_CODE": [
            "1234567890",
            "1234567890",
            "1234567890",
            "1234567890",
            "1234567890",
        ],
        "Status": ["Need Update", "Reviewed", "Completed", "Completed", "Completed"],
        "Update": [
            "2024-01-15",
            "2024-01-14",
            "2024-01-13",
            "2024-01-12",
            "2024-01-11",
        ],
        "Insight": [
            "System performance is optimal",
            "Maintenance required",
            "Waiting for approval",
            "Task completed successfully",
            "Error occurred during processing",
        ],
    }
)
insight_df["Update"] = pd.to_datetime(insight_df["Update"])

db_client.insert_dataframe(insight_df, "mass_assess_insight")

insight_df = db_client.execute("SELECT * FROM mass_assess_insight")
st.dataframe(insight_df)
