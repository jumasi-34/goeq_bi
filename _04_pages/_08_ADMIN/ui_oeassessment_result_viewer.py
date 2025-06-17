"""
OE Assessment 결과 조회 페이지

이 페이지는 OE Assessment 결과를 조회하고 표시하는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 사용자는 결과를 확인할 수 있습니다.
"""

import numpy as np
from scipy.stats import norm
import pandas as pd
import streamlit as st
from _00_database.db_client import get_client
from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_uf import uf_product_assess
from _01_query.GMES.q_weight import gt_wt_assess
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate
from _01_query.helper_sql import format_date_to_yyyymmdd
from _01_query.GMES.q_ctl import get_ctl_raw_query

# 메인 페이지 코드
st.title("OE Assessment Result Viewer")

result_df = get_client("sqlite").execute("SELECT * FROM mass_assess_result")

st.subheader("Assessment Result")
st.dataframe(result_df)
