"""
Docstring
"""

import sys
import streamlit as st
import os


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database import db_client
from _01_query.HOPE.q_hope import oe_app
from _05_commons import config
from _08_automation.oracle_to_sqlite import generate_sellin_monthly_agg

if config.DEV_MODE:
    import importlib

    importlib.reload(db_client)
    importlib.reload(config)


st.divider()
cols = st.columns([4, 1], vertical_alignment="bottom")
cols[0].title("HOPE Sell-in 수동 집계 도구")  # 더 명확한 제목으로
cols[0].write("Oracle 데이터를 집계하여 SQLite에 저장합니다.")

# 버튼 생성
if cols[1].button("HOPE Sellin 집계 실행", use_container_width=True):
    with st.spinner("집계 중입니다. 잠시만 기다려 주세요..."):
        try:
            generate_sellin_monthly_agg()
            st.success("✅ 집계가 완료되었습니다!")
        except Exception as e:
            st.error(f"❌ 집계 중 오류가 발생했습니다: {e}")

        sqlite_query = """--sql
        SELECT * 
        FROM sellin_monthly_agg
        """

        sqlite_db = db_client.get_client("sqlite")
        df = sqlite_db.execute(sqlite_query)

        st.dataframe(df)


oe_app = db_client.get_client("snowflake").execute(oe_app())
oe_app = oe_app[["m_code", "plant"]].drop_duplicates()

df = df.merge(oe_app, on=["m_code"], how="left")
# 중복된 인덱스 문제를 해결하기 위해 pivot_table 사용
df = df.pivot_table(
    index="plant",
    columns=["yyyy", "mm"],
    values="supp_qty",
    aggfunc="sum",  # 중복된 값이 있을 경우 합계로 처리
)
st.dataframe(df)
