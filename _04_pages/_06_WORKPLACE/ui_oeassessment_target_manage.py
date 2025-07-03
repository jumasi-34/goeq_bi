"""
OE 평가 대상 관리 페이지

이 페이지는 OE 평가 대상 데이터와 평가 결과 데이터를 관리하고 편집할 수 있는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에 저장되며, 사용자는 데이터를 직접 편집하고 변경사항을 저장할 수 있습니다.
"""

import pandas as pd
import streamlit as st
from _00_database.db_client import get_client
import uuid

st.title("OE Assessment Target Management")

# 탭 생성
tab1, tab2 = st.tabs(["Assessment Target", "Assessment Insight"])

# =============================================================================
# Assessment Target 탭
# =============================================================================
with tab1:
    st.header("Assessment Target Management")

    # 데이터 로드 (항상 원본)
    if "original_target_df" not in st.session_state:
        target_df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")
        for col in ["M_CODE", "M_CODE_RR", "M_CODE_PAIR"]:
            if col in target_df.columns:
                target_df[col] = target_df[col].astype(str).replace("nan", "")
        st.session_state.original_target_df = target_df.copy()

    df_for_edit = st.session_state.original_target_df.copy()

    # data_editor의 key를 세션 상태에서 관리
    if "target_editor_key" not in st.session_state:
        st.session_state.target_editor_key = str(uuid.uuid4())

    # 데이터프레임 편집기 표시
    target_col_config = {
        "No": st.column_config.NumberColumn(
            "No",
            help="No",
            required=True,
        ),
        "Year": st.column_config.NumberColumn(
            "Year",
            help="Year",
            required=True,
        ),
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

    edited_target_df = st.data_editor(
        df_for_edit,
        num_rows="dynamic",
        use_container_width=True,
        key=st.session_state.target_editor_key,
        column_config=target_col_config,
        hide_index=False,
    )

    # 저장 버튼에서만 세션 상태와 DB 갱신
    if st.button("Save Target Changes", key="save_target"):
        try:
            sqlite_client = get_client("sqlite")
            sqlite_client.insert_dataframe(edited_target_df, "mass_assess_target")
            st.session_state.original_target_df = edited_target_df.copy()
            st.success("Target changes have been saved successfully!")
        except Exception as e:
            st.error(f"Error occurred while saving target data: {str(e)}")

    # 리셋 버튼에서만 세션 상태 갱신 및 key 변경
    if st.button(
        "Reset Target Data",
        key="reset_target",
        help="Cancel all current changes and revert to original data from DB",
    ):
        try:
            target_df = get_client("sqlite").execute("SELECT * FROM mass_assess_target")
            for col in ["M_CODE", "M_CODE_RR", "M_CODE_PAIR"]:
                if col in target_df.columns:
                    target_df[col] = target_df[col].astype(str).replace("nan", "")
            st.session_state.original_target_df = target_df.copy()
            # data_editor의 key를 새로 생성
            st.session_state.target_editor_key = str(uuid.uuid4())
            st.success("Target data has been reset successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error occurred while resetting target data: {str(e)}")

# =============================================================================
# Assessment Result 탭
# =============================================================================
with tab2:
    st.header("Assessment Insight Management")

    # 데이터 로드 (항상 원본)
    if "original_insight_df" not in st.session_state:
        insight_df = get_client("sqlite").execute("SELECT * FROM mass_assess_insight")
        st.session_state.original_insight_df = insight_df.copy()

    # 편집용 데이터프레임 (항상 원본에서 복사)
    insight_df_for_edit = st.session_state.original_insight_df.copy()

    # data_editor의 key를 세션 상태에서 관리
    if "insight_editor_key" not in st.session_state:
        st.session_state.insight_editor_key = str(uuid.uuid4())

    col_config = {
        "M_CODE": st.column_config.TextColumn(
            "Material Code",
            help="자재 코드",
            required=True,
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Status",
            required=True,
            options=["Need Update", "Reviewed", "Completed"],
        ),
        "Insight": st.column_config.TextColumn(
            "Insight",
            help="Insight",
            required=True,
        ),
    }

    edited_insight_df = st.data_editor(
        insight_df_for_edit,
        num_rows="dynamic",
        use_container_width=True,
        key=st.session_state.insight_editor_key,
        hide_index=False,
        column_config=col_config,
    )

    # 저장 버튼에서만 세션 상태와 DB 갱신
    if st.button("Save Result Changes", key="save_result"):
        try:
            sqlite_client = get_client("sqlite")
            sqlite_client.insert_dataframe(edited_insight_df, "mass_assess_insight")
            st.session_state.original_insight_df = edited_insight_df.copy()
            st.success("Result changes have been saved successfully!")
        except Exception as e:
            st.error(f"Error occurred while saving result data: {str(e)}")

    # 리셋 버튼에서만 세션 상태 갱신 및 key 변경
    if st.button(
        "Reset Result Data",
        key="reset_result",
        help="Cancel all current changes and revert to original data from DB",
    ):
        try:
            target_df = get_client("sqlite").execute(
                "SELECT * FROM mass_assess_insight"
            )
            st.session_state.original_insight_df = target_df.copy()
            # data_editor의 key를 새로 생성
            st.session_state.insight_editor_key = str(uuid.uuid4())
            st.success("Result data has been reset successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error occurred while resetting result data: {str(e)}")
    # st.dataframe(st.session_state.original_target_df)
    # st.dataframe(st.session_state.original_insight_df)
    updated_mcode_list = st.session_state.original_insight_df["M_CODE"].tolist()
    need_update_target_df = st.session_state.original_target_df[
        ~st.session_state.original_target_df["M_CODE"].isin(updated_mcode_list)
    ]

    st.subheader(f"Update 필요한 대상 규격 : {len(need_update_target_df)} 규격")
    st.dataframe(need_update_target_df)

    st.markdown(
        """
| 문법 및 숏코드                           | 설명 |
|----------------------------------------|------|
| `#, ##, ###, ####`                       | 헤더 (H1, H2, H3) – GitHub Flavored Markdown 기반 |
| `**굵게**, *기울임*, ***굵게+기울기***` | 굵기/이탤릭 강조 – 일반 Markdown 지원 |
| `- 목록, 1. 순서 목록`               | 비순서/순서 목록 – 일반 Markdown 지원 |
| `> 인용문`                             | 인용 – 일반 Markdown 지원 |
| `---`                                  | 수평선 – 일반 Markdown 지원 |
| `:material/icon_name:`                 | 구글 머티리얼 심볼 아이콘 삽입 |
| `:color[text]`                         | 컬러 텍스트 (blue, green, orange, red, violet, gray/grey, rainbow, primary) |
| `:color-background[text]`              | 배경 컬러 적용 텍스트 |
| `:color-badge[text]`                   | 컬러 배지 – 배경과 테두리 포함 |
| `:small[text]`                         | 작은 글씨 표시 |
    """,
        unsafe_allow_html=True,
    )
