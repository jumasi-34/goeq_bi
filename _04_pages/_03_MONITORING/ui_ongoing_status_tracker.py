"""
진행 중인 상태 추적기 UI 페이지

이 페이지는 다음 세 가지 주요 항목의 진행 상태를 추적하고 시각화합니다:
1. 품질 이슈 (Quality Issues)
2. 4M 변경 사항 (4M Changes)
3. 고객 감사 (Customer Audits)

각 섹션은 다음 정보를 포함합니다:
- 공장별 진행 중인 항목 수
- 월별 진행 상황 차트
- 상세 데이터 테이블

사용자는 상단의 멀티셀렉트를 통해 특정 공장을 선택하여 필터링할 수 있습니다.
"""

import sys
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _05_commons import config
from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization._03_MONITORING import viz_ongoing_status_tracker


def reload_modules():
    """
    개발 모드에서 필요한 모듈들을 리로드합니다.

    개발 모드(config.DEV_MODE가 True)일 때만 실행되며,
    다음 모듈들을 리로드합니다:
    - df_quality_issue
    - df_4m_change
    - df_customer_audit
    - bi_202_ongoing_status_tracker
    """
    if config.DEV_MODE:
        import importlib

        importlib.reload(df_quality_issue)
        importlib.reload(df_4m_change)
        importlib.reload(df_customer_audit)
        importlib.reload(viz_ongoing_status_tracker)


def setup_common_ui():
    """
    공통 UI 컴포넌트를 설정하고 초기화합니다.

    Returns:
        list: 선택된 공장 코드 리스트
    """
    plant_codes = config.plant_codes[:-1]
    return st.multiselect("Select Plant", options=plant_codes, default=plant_codes)


def display_dataframe(df, columns, column_config, container):
    """
    데이터프레임을 Streamlit 컨테이너에 표시합니다.

    Args:
        df (pandas.DataFrame): 표시할 데이터프레임
        columns (list): 표시할 컬럼 리스트
        column_config (dict): 컬럼 설정 딕셔너리
        container (streamlit.container): 데이터프레임을 표시할 컨테이너
    """
    container.dataframe(
        df[columns],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )


def display_section(
    title, count, pie_chart_func, bar_chart_func, df, columns, column_config
):
    """
    각 섹션(품질 이슈, 4M 변경, 감사)을 표시합니다.

    Args:
        title (str): 섹션 제목
        count (int): 진행 중인 항목 수
        pie_chart_func (function): 파이 차트 생성 함수
        bar_chart_func (function): 바 차트 생성 함수
        df (pandas.DataFrame): 표시할 데이터프레임
        columns (list): 표시할 컬럼 리스트
        column_config (dict): 컬럼 설정 딕셔너리
    """
    st.subheader(f"{title} (On-going : {count})")
    cols = st.columns([1, 2, 4])

    fig = pie_chart_func(selected_plant)
    cols[0].plotly_chart(fig, use_container_width=True)

    fig = bar_chart_func(selected_plant)
    cols[1].plotly_chart(fig, use_container_width=True)

    display_dataframe(df, columns, column_config, cols[2])


reload_modules()
selected_plant = setup_common_ui()

# 품질 이슈 섹션
qi_df = df_quality_issue.load_ongoing_quality_issues(selected_plant)
qi_columns = [
    "PLANT",
    "OEM",
    "VEH",
    "PJT",
    "REG_DATE",
    "STATUS",
    "LOCATION",
    "MARKET",
    "M_CODE",
    "PNL_NM",
    "TYPE",
    "CAT",
    "SUB_CAT",
    "URL",
]
qi_column_config = {
    "DOC_NO": st.column_config.TextColumn("Document No."),
    "REG_DATE": st.column_config.DateColumn("Reg. Date", format="YYYY-MM-DD"),
    "URL": st.column_config.LinkColumn("LINK", display_text="Click"),
}
display_section(
    "Quality Issue",
    len(qi_df),
    viz_ongoing_status_tracker.ongoing_qi_pie_by_plant,
    viz_ongoing_status_tracker.ongoing_qi_bar_by_month,
    qi_df,
    qi_columns,
    qi_column_config,
)

st.divider()

# 4M 변경 섹션
(filtered_df_plant_na, filtered_df, _, _) = df_4m_change.filtered_4m_ongoing_by_yearly(
    selected_plant
)
m4_columns = [
    "DOC_NO",
    "PLANT",
    "SUBJECT",
    "STATUS",
    "REG_DATE",
    "URL",
    "Elapsed_period",
    "M_CODE",
]
m4_column_config = {
    "DOC_NO": st.column_config.TextColumn("Document No."),
    "REG_DATE": st.column_config.DateColumn("Reg. Date", format="YYYY-MM-DD"),
    "URL": st.column_config.LinkColumn("LINK", display_text="Click"),
    "M_CODE_LIST": st.column_config.ListColumn("M Code List"),
}
display_section(
    "4M Change",
    len(filtered_df),
    viz_ongoing_status_tracker.ongoing_4m_pie_by_plant,
    viz_ongoing_status_tracker.ongoing_4m_bar_by_month,
    filtered_df,
    m4_columns,
    m4_column_config,
)

# 미등록 4M 정보 표시
n_of_non_registration = len(filtered_df_plant_na)
non_reg_columns = [
    "DOC_NO",
    "PURPOSE",
    "SUBJECT",
    "STATUS",
    "REQUESTER",
    "REG_DATE",
    "URL",
    "M_CODE",
    "Elapsed_period",
]
non_reg_column_config = {
    "URL": st.column_config.LinkColumn("Link", display_text="Click"),
    "REG_DATE": st.column_config.DateColumn("Registration Date", format="YYYY-MM-DD"),
}

with st.expander(
    label=f"※ 4M information for M-Code not registered in OE Application( On-going : {n_of_non_registration})"
):
    display_dataframe(filtered_df_plant_na, non_reg_columns, non_reg_column_config, st)

st.divider()

# 감사 섹션
(audit_df, _, _) = df_customer_audit.get_audit_ongoing_df(selected_plant)
audit_columns = [
    "TYPE",
    "START_DT",
    "END_DT",
    "SUBJECT",
    "M_CODE",
    "PLANT",
    "CAR_MAKER",
    "URL",
    "ELAPSED_PERIOD",
]
audit_column_config = {
    "START_DT": st.column_config.DateColumn("Start", format="YYYY-MM-DD"),
    "END_DT": st.column_config.DateColumn("End", format="YYYY-MM-DD"),
    "URL": st.column_config.LinkColumn("LINK", display_text="Click"),
}
display_section(
    "OE Audit",
    len(audit_df),
    viz_ongoing_status_tracker.ongoing_audit_pie_by_plant,
    viz_ongoing_status_tracker.ongoing_audit_bar_by_month,
    audit_df,
    audit_columns,
    audit_column_config,
)
