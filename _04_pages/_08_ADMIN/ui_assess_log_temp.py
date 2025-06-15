"""
Docstring
"""
import sys
import pandas as pd
import streamlit as st

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)

from _00_database import db_client
from _01_query.SAP.q_hk_personnel  import CTE_HR_PERSONAL
from _05_commons import config, helper


if config.DEV_MODE:
    import importlib

    importlib.reload(db_client)
    importlib.reload(config)


DB_PATH = "../database/goeq_database.db"
df = db_client.get_client('sqlite')


sqlite = helper.SQLiteDML()

df_login = sqlite.fetch_query("SELECT * FROM logins")
df_employee_info = db_client.get_client('snowflake').execute(CTE_HR_PERSONAL)

merge_login = pd.merge(
    df_login,df_employee_info, "left", left_on="employee_id", right_on="pnl_no"
)

merge_login = merge_login.assign(
    login_time=pd.to_datetime(merge_login["login_time"], "coerce")
)

merge_login["login_time"] = merge_login["login_time"].dt.tz_localize("UTC")
merge_login["login_time"] = merge_login["login_time"].dt.tz_convert("Asia/Seoul")

st.dataframe(merge_login, use_container_width=True)
print(merge_login.dtypes)