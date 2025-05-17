"""
Streamlit 네비게이션 페이지
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

import streamlit as st

from _04_pages.config_pages import PAGE_CONFIGS
from _00_database.db_client import get_client
from _05_commons.helper import SQLiteDDL, SQLiteDML

sqlite_db = SQLiteDML()

# ------------------------
# 🔸 페이지 분류별 구성 정의
# ------------------------

# ?페이지를 추가할 경우 'PAGE_CONFIGS'에 등록된 Page의 key값을 추가하면됨!

NAVIGATION_SECTIONS = {
    "Summary": [],
    "Workplace": ["Weekly CQMS Monitor", "Ongoing Status Tracker"],
    "Detail Page": ["OE Quality Issue Dashboard"],
    "Support": ["RR Analysis", "FM Monitoring"],
}

# ------------------------
# 🔸 첫 번째 컨테이너 (Navigation)
# ------------------------
with st.container(border=True):
    cols = st.columns(len(NAVIGATION_SECTIONS))

    for i, (section, page_titles) in enumerate(NAVIGATION_SECTIONS.items()):
        with cols[i]:
            st.subheader(section)
            st.write("")
            for title in page_titles:
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
