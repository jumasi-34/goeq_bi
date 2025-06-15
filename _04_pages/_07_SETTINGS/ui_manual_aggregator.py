"""
HOPE Sell-in 데이터 수동 집계 도구
- Oracle DB에서 데이터를 가져와 SQLite DB에 저장
- 저장된 데이터를 피벗 테이블 형태로 표시
"""

import sys
import streamlit as st
import os
import pandas as pd

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
cols[0].title("HOPE Sell-in 수동 집계 도구")
cols[0].write("Oracle 데이터를 집계하여 SQLite에 저장합니다.")

# 버튼 생성
if cols[1].button("HOPE Sellin 집계 실행", use_container_width=True):
    with st.spinner("집계 중입니다. 잠시만 기다려 주세요..."):
        try:
            success, message = generate_sellin_monthly_agg()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
                st.stop()  # 에러 발생 시 이후 코드 실행 중단

            # SQLite에서 데이터 조회
            sqlite_query = """--sql
            SELECT * 
            FROM sellin_monthly_agg
            """
            sqlite_db = db_client.get_client("sqlite")
            df = sqlite_db.execute(sqlite_query)

            if df is None or df.empty:
                st.warning("저장된 데이터가 없습니다.")
                st.stop()

            # OE 데이터 조회 및 병합
            try:
                oe_app_df = db_client.get_client("snowflake").execute(oe_app())
                oe_app_df.columns = oe_app_df.columns.str.upper()
                oe_app_df = oe_app_df[["M_CODE", "PLANT"]].drop_duplicates()

                df = df.merge(oe_app_df, on=["M_CODE"], how="left")
                df["M_CODE"] = df["M_CODE"].str.upper()

                # 피벗 테이블 생성
                pivot_df = df.pivot_table(
                    index="PLANT",
                    columns=["YYYY", "MM"],
                    values="SUPP_QTY",
                    aggfunc="sum",
                )

                # 데이터 표시
                st.subheader("월별 집계 데이터")
                st.dataframe(pivot_df, use_container_width=True)

                # 통계 정보 표시
                st.subheader("기본 통계")
                stats_df = (
                    df.groupby("PLANT")["SUPP_QTY"]
                    .agg(["sum", "mean", "count"])
                    .round(2)
                )
                stats_df.columns = ["총계", "평균", "건수"]
                st.dataframe(stats_df, use_container_width=True)

            except Exception as e:
                st.error(f"데이터 처리 중 오류 발생: {str(e)}")

        except Exception as e:
            st.error(f"처리 중 예기치 않은 오류 발생: {str(e)}")
