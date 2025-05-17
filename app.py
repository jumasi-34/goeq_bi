"""
Docstring
"""

import sys
import streamlit as st
import re
from datetime import datetime
from pathlib import Path
import os

os.environ["LD_LIBRARY_PATH"] = "/opt/oracle/instantclient_23_8"
# 프로젝트 루트 추가
sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database.db_client import get_client
from _01_query.SAP.q_hk_personnel import CTE_HR_PERSONAL
from _04_pages.config_pages import PAGE_CONFIGS
from _05_commons.helper import SQLiteDML
from _05_commons import config


# 기본 설정
st.set_page_config(layout="wide")
ROLES = ["Viewer", "Contributor", "Admin"]
PASSWORDS = {"Contributor": "1", "Admin": "2"}
DB_PATH = config.SQLITE_DB_PATH
db_dml = SQLiteDML()


# 캐시된 DB 호출 함수 정의
@st.cache_data(ttl=600)
def load_personnel_df():
    df = get_client("snowflake").execute(CTE_HR_PERSONAL)
    df.columns = df.columns.str.upper()
    df["PNL_NO"] = df["PNL_NO"].astype(int)
    return df


# session_state 초기화
def init_session_state():
    defaults = {
        "role": None,
        "personel_id": None,
        "password_verified": False,
        "login_recorded": False,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)


# 호출 위치
init_session_state()


# 로그인 함수
def login():
    st.header("Log in")
    selected_role = st.selectbox("Choose your role", ROLES)
    personel_id_local = st.text_input("Personnel ID (8-digit number)", max_chars=8)

    # 사번 존재 유무 확인
    if personel_id_local and not re.match(r"^\d{8}$", personel_id_local):
        st.warning("Please enter a valid 8-digit number.")
        return

    password = None
    is_pw_valid = True

    if selected_role in PASSWORDS:
        password = st.text_input("Enter your password", type="password")
        is_pw_valid = password == PASSWORDS[selected_role]

    if st.button("Log in"):
        if not personel_id_local or not is_pw_valid:
            st.warning("Invalid login credentials.")
            return

        st.session_state.role = selected_role
        st.session_state.personel_id = int(personel_id_local)
        st.session_state.password_verified = is_pw_valid

        if not st.session_state.login_recorded:
            db_dml.execute_query(
                "INSERT INTO logins (employee_id, login_time) VALUES (?, ?)",
                (int(personel_id_local), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            st.session_state.login_recorded = True
        st.rerun()


# 로그아웃 함수
def logout():
    for key in ["role", "personel_id", "password_verified", "login_recorded"]:
        st.session_state[key] = None
    st.rerun()


# 본문 실행 로직
st.logo(image="_06_assets/logo.png", icon_image="_06_assets/logo_only.png")
role = st.session_state.role
personel_id = st.session_state.personel_id

# 로그인 성공 이후에만 실행
if st.session_state.password_verified:
    df_personnel = load_personnel_df()
    df_matched = df_personnel[df_personnel["PNL_NO"] == st.session_state.personel_id]

    if df_matched.empty:
        st.warning("No matching personnel ID record found.")
        st.stop()

    personel_nm = df_matched["PNL_NM"].values[0]
    st.caption(
        f":grey[Welcome,] **{personel_nm}**:grey[! You have access with] **{st.session_state.role}** :grey[privileges.]"
    )

    page_groups = {}

    for title, page in PAGE_CONFIGS.items():
        if role in page["roles"]:
            CATEGORY = page["category"]
            page = st.Page(page["filename"], title=title, icon=page["icon"])
            page_groups.setdefault(CATEGORY, []).append(page)

    page_groups["Account"] = [
        st.Page(logout, title="Log out", icon=":material/logout:")
    ]
    pg = st.navigation(page_groups)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
