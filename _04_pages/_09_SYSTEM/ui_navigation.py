"""
Streamlit 네비게이션 페이지
"""

import sys

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)

import streamlit as st

from _04_pages.config_pages import PAGE_CONFIGS
from _00_database.db_client import get_client
from _05_commons.helper import SQLiteDDL, SQLiteDML

sqlite_db = SQLiteDML()

# ------------------------
# 🔸 페이지 분류별 구성 정의
# ------------------------

# 카테고리 그룹 정의
CATEGORY_GROUPS = {
    "Main": ["Dashboard", "Analysis", "Monitoring", "Collaboration", "User Guide"],
    "Management": ["Workplace", "Settings", "Admin", "System"],
}


# 사용자 권한에 따라 페이지 필터링
def get_authorized_pages():
    user_role = st.session_state.get("role")
    if not user_role:
        return {}

    authorized_pages = {}
    for page_title, page_config in PAGE_CONFIGS.items():
        if user_role in page_config["roles"]:
            category = page_config["category"]
            if category not in authorized_pages:
                authorized_pages[category] = []
            authorized_pages[category].append(page_title)

    return authorized_pages


# ------------------------
# 🔸 첫 번째 컨테이너 (Navigation)
# ------------------------
with st.container(border=True):
    authorized_pages = get_authorized_pages()

    if not authorized_pages:
        st.warning("로그인이 필요합니다.")
    else:
        # Main 섹션
        st.subheader("Main")
        main_cols = st.columns(len(CATEGORY_GROUPS["Main"]))

        for i, category in enumerate(CATEGORY_GROUPS["Main"]):
            if category in authorized_pages:
                with main_cols[i]:
                    st.write(f"**{category}**")
                    for title in authorized_pages[category]:
                        cfg = PAGE_CONFIGS[title]
                        st.page_link(cfg["filename"], label=title, icon=cfg["icon"])

        st.divider()

        # Management 섹션
        st.subheader("Management")
        mgmt_cols = st.columns(len(CATEGORY_GROUPS["Management"]))

        for i, category in enumerate(CATEGORY_GROUPS["Management"]):
            if category in authorized_pages:
                with mgmt_cols[i]:
                    st.write(f"**{category}**")
                    for title in authorized_pages[category]:
                        cfg = PAGE_CONFIGS[title]
                        st.page_link(cfg["filename"], label=title, icon=cfg["icon"])

# ------------------------
# 🔸 두 번째 컨테이너 (문서)
# ------------------------
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    col1.subheader("Document")
    col2.write("")

# ------------------------
# 🔸 세 번째 컨테이너 (외부 링크)
# ------------------------
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    col1.subheader("Link")
    col2.write("")
    col2.page_link(
        "http://egqms.hankooktech.com/login.html",
        label="CQMS",
        icon=":material/select_window:",
    )
