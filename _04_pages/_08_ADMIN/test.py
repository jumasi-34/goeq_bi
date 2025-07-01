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

path = "temp_df.csv"
df = pd.read_csv(path)

db_client.insert_dataframe(df, "mass_assess_target")

target_df = db_client.execute("SELECT * FROM mass_assess_target")
st.dataframe(target_df)
