"""
CQMS 웹 애플리케이션 메인 모듈

이 모듈은 CQMS(Customer Quality Management System)의 메인 애플리케이션을 구현합니다.
사용자 인증, 세션 관리, 페이지 라우팅 등의 핵심 기능을 제공합니다.
"""

import sys
import streamlit as st
import re
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Dict, Optional
from dotenv import load_dotenv
import logging
import cx_Oracle

# 프로젝트 루트 디렉토리를 Python 경로에 추가
from _05_commons import config

sys.path.append(config.PROJECT_ROOT)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 상수 정의
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
ROLES = ["Viewer", "Contributor", "Admin"]

# 고정 비밀번호 설정
FIXED_PASSWORDS = {"Contributor": "January", "Admin": "December"}

from _00_database.db_client import get_client
from _01_query.SAP.q_hk_personnel import CTE_HR_PERSONAL
from _04_pages.config_pages import PAGE_CONFIGS
from _05_commons.helper import SQLiteDML

# 기본 설정
st.set_page_config(layout="wide")
DB_PATH = config.SQLITE_DB_PATH
db_dml = SQLiteDML()


def verify_password(role: str, provided_password: str) -> bool:
    """비밀번호를 검증합니다.

    Args:
        role (str): 사용자 역할
        provided_password (str): 검증할 비밀번호

    Returns:
        bool: 비밀번호 일치 여부
    """
    return FIXED_PASSWORDS.get(role) == provided_password


@st.cache_data(ttl=3600)
def load_personnel_df():
    """인사 데이터를 로드하고 전처리합니다.

    Returns:
        DataFrame: 전처리된 인사 데이터프레임
    """
    try:
        df = get_client("snowflake").execute(CTE_HR_PERSONAL)
        df.columns = df.columns.str.upper()
        df["PNL_NO"] = df["PNL_NO"].astype(int)
        return df
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        st.error("Failed to load personnel data. Please try again later.")
        return None


def init_session_state():
    """세션 상태를 초기화합니다."""
    defaults = {
        "role": None,
        "personel_id": None,
        "password_verified": False,
        "login_recorded": False,
        "login_attempts": 0,
        "last_activity": datetime.now(),
        "is_locked": False,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)


def check_session_timeout() -> bool:
    """세션 타임아웃을 확인합니다.

    Returns:
        bool: 세션 만료 여부
    """
    if st.session_state.last_activity:
        time_diff = datetime.now() - st.session_state.last_activity
        if time_diff > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            logout()
            st.warning("Session expired. Please log in again.")
            return True
    return False


def login():
    """사용자 로그인을 처리합니다.

    Returns:
        None: 로그인 성공 시 세션 상태를 업데이트하고 페이지를 새로고침합니다.

    Raises:
        Exception: 로그인 처리 중 오류 발생 시 예외를 발생시킵니다.
    """
    st.header("Log in")

    # 계정 잠금 상태 확인
    if st.session_state.is_locked:
        st.error("Account is locked. Please contact administrator.")
        return

    # 역할 선택 및 인사번호 입력
    selected_role = st.selectbox("Choose your role", ROLES)
    personel_id_local = st.text_input("Personnel ID (8-digit number)", max_chars=8)

    # 인사번호 유효성 검사
    if personel_id_local and not re.match(r"^\d{8}$", personel_id_local):
        st.warning("Please enter a valid 8-digit number.")
        return

    # 비밀번호 입력 및 검증
    password = None
    is_pw_valid = True

    if selected_role in ["Contributor", "Admin"]:
        password = st.text_input("Enter your password", type="password")
        if password:
            is_pw_valid = verify_password(selected_role, password)

    # 로그인 버튼 클릭 시 처리
    if st.button("Log in"):
        # 입력값 검증
        if not personel_id_local or not is_pw_valid:
            st.session_state.login_attempts += 1
            if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                st.session_state.is_locked = True
                st.error("Account locked due to too many failed login attempts.")
                return
            st.warning("Invalid login credentials.")
            return

        try:
            # 세션 상태 업데이트
            st.session_state.update(
                {
                    "role": selected_role,
                    "personel_id": int(personel_id_local),
                    "password_verified": is_pw_valid,
                    "last_activity": datetime.now(),
                    "login_attempts": 0,
                }
            )

            # 로그인 기록 저장
            if not st.session_state.login_recorded:
                db_dml.execute_query(
                    "INSERT INTO logins (employee_id, login_time) VALUES (?, ?)",
                    (
                        int(personel_id_local),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                st.session_state.login_recorded = True
                logger.info(f"User {personel_id_local} logged in successfully")

            st.rerun()

        except Exception as e:
            logger.error(f"Login process error: {str(e)}")
            st.error("An error occurred during login. Please try again.")


def logout():
    """사용자 로그아웃을 처리합니다."""
    try:
        for key in ["role", "personel_id", "password_verified", "login_recorded"]:
            st.session_state[key] = None
        logger.info("User logged out successfully")
        st.rerun()
    except Exception as e:
        logger.error(f"Logout process error: {str(e)}")
        st.error("An error occurred during logout. Please try again.")


# 메인 실행 로직
init_session_state()
st.logo(image="_06_assets/logo.png", icon_image="_06_assets/logo_only.png")

if st.session_state.password_verified:
    df_personnel = load_personnel_df()
    if df_personnel is not None:
        df_matched = df_personnel[
            df_personnel["PNL_NO"] == st.session_state.personel_id
        ]

        if df_matched.empty:
            st.warning("No matching personnel ID record found.")
            st.stop()

        personel_nm = df_matched["PNL_NM"].values[0]
        st.caption(
            f":grey[Welcome,] **{personel_nm}**:grey[! You have access with] **{st.session_state.role}** :grey[privileges.]"
        )

        page_groups = {}
        for title, page in PAGE_CONFIGS.items():
            if st.session_state.role in page["roles"]:
                CATEGORY = page["category"]
                page = st.Page(page["filename"], title=title, icon=page["icon"])
                page_groups.setdefault(CATEGORY, []).append(page)

        # User Guide와 Workplace 사이에 구분선 추가
        if "User Guide" in page_groups and "Workplace" in page_groups:
            page_groups["User Guide"].append(
                st.Page(
                    lambda: st.divider(),
                    title="------------------------------------------------",
                    icon="",
                )
            )

        page_groups["System"] = page_groups.get("System", []) + [
            st.Page(logout, title="Log out", icon=":material/logout:")
        ]
        pg = st.navigation(page_groups)
    else:
        st.error("Failed to load user data. Please try again later.")
else:
    pg = st.navigation([st.Page(login)])

pg.run()
