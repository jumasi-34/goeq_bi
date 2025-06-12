"""
OE 평가 대상 관리 페이지

이 페이지는 OE 평가 대상 데이터를 관리하고 편집할 수 있는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에 저장되며, 사용자는 데이터를 직접 편집하고 변경사항을 저장할 수 있습니다.
"""

import pandas as pd
import streamlit as st
from _00_database.db_client import get_client
import uuid

st.title("OE Assessment Target Management")

# 데이터 로드 (항상 원본)
if "original_df" not in st.session_state:
    df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")
    for col in ["M_CODE", "M_CODE_RR", "M_CODE_PAIR"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "")
    st.session_state.original_df = df.copy()

# 편집용 데이터프레임 (항상 원본에서 복사)
df_for_edit = st.session_state.original_df.copy()

# data_editor의 key를 세션 상태에서 관리
if "editor_key" not in st.session_state:
    st.session_state.editor_key = str(uuid.uuid4())

# 데이터프레임 편집기 표시
col_config = {
    "PLANT": st.column_config.TextColumn(
        "Plant",
        help="공장 코드",
        required=True,
    ),
    "M_CODE": st.column_config.TextColumn(
        "Material Code",
        help="자재 코드",
        required=True,
    ),
    "M_CODE_RR": st.column_config.TextColumn(
        "Material Code RR",
        help="자재 코드 RR",
        required=True,
    ),
    "R-Level ": st.column_config.NumberColumn(
        "R-Level",
        step=0.01,
        format="%.2f",
        help="R-Level",
        min_value=0,
        max_value=100,
    ),
}
edited_df = st.data_editor(
    df_for_edit,
    num_rows="dynamic",
    use_container_width=True,
    key=st.session_state.editor_key,  # 매번 새로운 key 사용
    column_config=col_config,
)

# 저장 버튼에서만 세션 상태와 DB 갱신
if st.button("Save Changes"):
    try:
        sqlite_client = get_client("sqlite")
        sqlite_client.insert_dataframe(edited_df, "mass_assess_target")
        st.session_state.original_df = edited_df.copy()
        st.success("Changes have been saved successfully!")
    except Exception as e:
        st.error(f"Error occurred while saving data: {str(e)}")

# 리셋 버튼에서만 세션 상태 갱신 및 key 변경
if st.button(
    "Reset Data", help="Cancel all current changes and revert to original data from DB"
):
    try:
        df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")
        for col in ["M_CODE", "M_CODE_RR", "M_CODE_PAIR"]:
            if col in df.columns:
                df[col] = df[col].astype(str).replace("nan", "")
        st.session_state.original_df = df.copy()
        # data_editor의 key를 새로 생성
        st.session_state.editor_key = str(uuid.uuid4())
        st.success("Data has been reset successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error occurred while resetting data: {str(e)}")
