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
import pandas as pd

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(project_root, "logs", "app.log"),
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
# env_path = Path(project_root) / ".env"
# load_dotenv(dotenv_path=env_path)

# 상수 정의
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
ROLES = ["Viewer", "Contributor", "Admin"]

# 고정 비밀번호 설정
FIXED_PASSWORDS = {"Contributor": "December", "Admin": "131209"}

from _00_database.db_client import get_client
from _01_query.SAP.q_hk_personnel import CTE_HR_PERSONAL
from _04_pages.config_pages import PAGE_CONFIGS
from _05_commons.helper import SQLiteDML
from _05_commons import config, helper

# 기본 설정
st.set_page_config(layout="wide")
DB_PATH = config.SQLITE_DB_PATH
db_dml = SQLiteDML()

# pg 변수 초기화
pg = None


def verify_password(role: str, provided_password: str) -> bool:
    """비밀번호를 검증합니다.

    Args:
        role (str): 사용자 역할
        provided_password (str): 검증할 비밀번호

    Returns:
        bool: 비밀번호 일치 여부
    """
    return FIXED_PASSWORDS.get(role) == provided_password


def load_personnel_df():
    """인사 데이터를 로드하고 전처리합니다.

    Returns:
        DataFrame: 전처리된 인사 데이터프레임
    """
    client = get_client("snowflake")
    if client is None:
        logger.error("Failed to get Snowflake client")
        return None

    df = client.execute(CTE_HR_PERSONAL)
    if df is None or df.empty:
        logger.error("No data returned from Snowflake query")
        return None

    # 컬럼명을 대문자로 변환
    df.columns = df.columns.str.upper()

    # 수동 데이터 추가
    manual_df = pd.DataFrame(
        [
            {"PNL_NO": 21300315, "PNL_NM": "KIM JEE WOONG"},
            {"PNL_NO": 21000075, "PNL_NM": "SOUNG HYUN JUN"},
            {"PNL_NO": 21100293, "PNL_NM": "KIM SEUNG JAE"},
            {"PNL_NO": 21200424, "PNL_NM": "OH JIN TAEK"},
            {"PNL_NO": 21604756, "PNL_NM": "RYU JE WOOK"},
        ]
    )

    # 데이터프레임 결합 후 인덱스 재설정
    df = pd.concat([df, manual_df], ignore_index=True)

    # PNL_NO를 object 타입으로 변환 (문자열과 숫자 혼재 가능)
    df["PNL_NO"] = pd.to_numeric(df["PNL_NO"], errors="coerce").fillna(0).astype(int)

    return df


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

    footer = """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #f9f9f9;
        text-align: center;
        padding: 8px 0;
        font-size: 13px;
        color: #6c757d;
        border-top: 1px solid #dee2e6;
    }
    </style>

    <div class="footer">
        For inquiries or improvement requests, please contact: 
        <br>
        Jungman Sim (Global OE Quality Team) 📞 +82-42-724-2957 | ✉️ Jungman.Sim@hankookn.com <br>
        Eunyoung Woo (Global OE Quality Team) 📞 +82-42-724-2942 | ✉️ Eunyoung.Woo@hankookn.com
    </div>
    """

    st.markdown(footer, unsafe_allow_html=True)

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

    # 애플리케이션 요약 정보 추가
    st.markdown("---")

    # 애플리케이션 개요 섹션
    st.markdown("**Global OE Quality Integrated Data and Analytics Platform**")
    desc_col = st.columns([3, 2, 2])
    desc_col[0].markdown(
        """
    ### :material/monitoring: **Core Features**
    - **CQMS Integration**: Quality Issue Management, 4M Change Management, and Customer Audit Monitoring
    - **Production Quality Analysis**: GMES-based production, NCF, RR, Weight, CTL, Uniformity data analysis
    - **OE Application Management**: HOPE system-based OE product information management
    - **Return Data Analysis**: HGWS system-based return status analysis
    """
    )
    desc_col[1].markdown(
        """
    ### :material/admin_panel_settings: **Role-Based Access Control**
    - **Viewer**: Read-only access to dashboards and reports
    - **Contributor**: Data entry and modification capabilities
    - **Admin**: Full system administration and configuration rights
    """
    )

    desc_col[2].markdown(
        """
    ### :material/settings: **Current Status**
    - Real-time data integration with enterprise systems
    - Integrated dashboard and analysis tools
    - Automated data processing and report generation
    - Secure session management with timeout protection
    """
    )

    st.markdown("---")


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
        # 디버깅을 위한 데이터 정보 출력 (개발 환경에서만)
        logger.info(f"Personnel data shape: {df_personnel.shape}")
        logger.info(f"Personnel data columns: {df_personnel.columns.tolist()}")
        logger.info(f"Personnel data types: {df_personnel.dtypes.to_dict()}")

        # 중복된 PNL_NO 확인
        duplicates = df_personnel[
            df_personnel.duplicated(subset=["PNL_NO"], keep=False)
        ]
        if not duplicates.empty:
            logger.warning(
                f"Found duplicate PNL_NO entries: {duplicates['PNL_NO'].tolist()}"
            )

        # 사용자 ID 매칭 (더 안전한 방식)
        try:
            user_id = int(st.session_state.personel_id)
            df_matched = df_personnel[df_personnel["PNL_NO"] == user_id]

            if df_matched.empty:
                st.warning("No matching personnel ID record found.")
                st.stop()

            # 중복된 사용자 ID가 있는 경우 첫 번째 결과만 사용
            if len(df_matched) > 1:
                logger.warning(
                    f"Multiple records found for user ID {user_id}, using first match"
                )
                df_matched = df_matched.iloc[:1]

            personel_nm = df_matched["PNL_NM"].values[0]

        except (ValueError, TypeError) as e:
            logger.error(
                f"Error processing user ID {st.session_state.personel_id}: {str(e)}"
            )
            st.error("Invalid user ID format. Please contact administrator.")
            st.stop()

        menu_col = st.columns([9, 1, 1], vertical_alignment="center")

        # Navigation과 Logout을 동일한 디자인으로 통일
        if menu_col[1].button(
            label="Navigation",
            icon=":material/home:",
            type="tertiary",
            use_container_width=True,
        ):
            st.switch_page("_04_pages/_09_SYSTEM/ui_navigation.py")
        menu_col[2].button(
            label="Log out",
            icon=":material/logout:",
            on_click=logout,
            type="tertiary",
            use_container_width=True,
        )

        menu_col[0].caption(
            f":grey[Welcome,] **{personel_nm}**:grey[! You have access with] **{st.session_state.role}** :grey[privileges.]"
        )

        page_groups = {}
        for title, page in PAGE_CONFIGS.items():
            if st.session_state.role in page["roles"]:
                CATEGORY = page["category"]
                page = st.Page(page["filename"], title=title, icon=page["icon"])
                page_groups.setdefault(CATEGORY, []).append(page)

        # # User Guide와 Workplace 사이에 구분선 추가
        # if "User Guide" in page_groups and "Workplace" in page_groups:
        #     page_groups["User Guide"].append(
        #         st.Page(
        #             lambda: st.divider(),
        #             title="------------------------------------------------",
        #             icon="",
        #         )
        #     )

        page_groups["System"] = page_groups.get("System", []) + [
            st.Page(logout, title="Log out", icon=":material/logout:")
        ]
        pg = st.navigation(page_groups, position="top")
    else:
        st.error("Failed to load user data. Please try again later.")
        pg = st.navigation([st.Page(login)])
else:
    pg = st.navigation([st.Page(login)])

if pg is not None:
    pg.run()
else:
    st.error("Navigation initialization failed. Please refresh the page.")
