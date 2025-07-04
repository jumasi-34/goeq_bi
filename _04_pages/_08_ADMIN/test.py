"""
Test page for debugging and validating data processing functions.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Optional, Dict, Any
import os
import sys
import importlib
import time

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


from _05_commons import config
from _00_database.db_client import get_client
from _01_query.GMES import q_rr
from _01_query.GMES import q_uf

# 개발 모드 시 모듈 리로드 (코드 변경사항 반영을 위해)
if config.DEV_MODE:
    importlib.reload(config)
    importlib.reload(q_rr)
    importlib.reload(q_uf)


db_client = get_client("snowflake")
df = db_client.execute(q_uf.uf_standard())

st.download_button(
    label="Download Data",
    data=df.to_csv(index=False),
    file_name="uf_standard.csv",
    mime="text/csv",
)

st.dataframe(df)

st.dataframe(df)
