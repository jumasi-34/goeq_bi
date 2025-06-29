"""
로그인 기록 분석 및 관리 페이지

이 모듈은 사용자 로그인 기록을 분석하고 관리하는 관리자 전용 페이지입니다.
SQLite 데이터베이스의 로그인 기록과 Snowflake의 인사 정보를 결합하여
통합된 로그인 분석 데이터를 제공합니다.

주요 기능:
- 로그인 기록 조회 및 분석
- 인사 정보와 로그인 데이터 결합
- 시간대 변환 (UTC → Asia/Seoul)
- 관리자용 데이터 테이블 표시
"""

import sys
import pandas as pd
import streamlit as st
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database import db_client
from _01_query.SAP.q_hk_personnel import CTE_HR_PERSONAL
from _05_commons import config, helper

# 개발 모드에서 모듈 재로드 (핫 리로드 지원)
if config.DEV_MODE:
    import importlib

    importlib.reload(db_client)
    importlib.reload(config)

# 데이터베이스 경로 설정
DB_PATH = "../database/goeq_database.db"
df = db_client.get_client("sqlite")

# SQLite 데이터베이스 연결 객체 생성
sqlite = helper.SQLiteDML()

# 로그인 기록 데이터 로드
df_login = sqlite.fetch_query("SELECT * FROM logins")

# Snowflake에서 인사 정보 데이터 로드
df_employee_info = db_client.get_client("snowflake").execute(CTE_HR_PERSONAL)
manual_df = pd.DataFrame(
    [
        {"pnl_no": 21300315, "pnl_nm": "KIM JEE WOONG"},
        {"pnl_no": 21000075, "pnl_nm": "SOUNG HYUN JUN"},
        {"pnl_no": 21100293, "pnl_nm": "KIM SEUNG JAE"},
        {"pnl_no": 21200424, "pnl_nm": "OH JIN TAEK"},
        {"pnl_no": 21604756, "pnl_nm": "RYU JE WOOK"},
    ]
)
df_employee_info["pnl_no"] = df_employee_info["pnl_no"].astype("int64")
manual_df["pnl_no"] = manual_df["pnl_no"].astype("int64")
df_employee_info = pd.concat([df_employee_info, manual_df], ignore_index=True)
df_login["employee_id"] = df_login["employee_id"].astype("int64")

# 로그인 기록과 인사 정보를 결합 (left join)
merge_login = pd.merge(
    df_login, df_employee_info, "left", left_on="employee_id", right_on="pnl_no"
)

# 로그인 시간을 datetime 타입으로 변환
merge_login = merge_login.assign(
    login_time=pd.to_datetime(merge_login["login_time"], "coerce")
)

# 시간대 변환: UTC → Asia/Seoul
merge_login["login_time"] = merge_login["login_time"].dt.tz_localize("UTC")
merge_login["login_time"] = merge_login["login_time"].dt.tz_convert("Asia/Seoul")

# 결합된 데이터를 Streamlit 데이터프레임으로 표시
st.dataframe(merge_login, use_container_width=True, height=700)

# 디버깅: 데이터프레임 컬럼 타입 출력
print(merge_login.dtypes)
