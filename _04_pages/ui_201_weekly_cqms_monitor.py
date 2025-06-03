"""
품질 이슈, 4M 변경, 감사 현황을 추적하는 작업장 모니터링 대시보드입니다.
각 공장별 주간 상태 업데이트와 지표를 제공합니다.
"""

import sys
import datetime as dt
import streamlit as st

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _05_commons import config
from _02_preprocessing.CQMS import df_quality_issue, df_4m_change, df_customer_audit
from _03_visualization import bi_201_weekly_cqms_monitor

if config.DEV_MODE:
    import importlib

    importlib.reload(df_quality_issue)
    importlib.reload(df_4m_change)
    importlib.reload(df_customer_audit)
    importlib.reload(bi_201_weekly_cqms_monitor)

# Initialize page layout and tabs
tabs = st.tabs(["Weekly Work Place"])

# Define status options
all_status = ["Open", "Open & Close", "Close", "On-going"]
all_status_for_Audit = ["NEW", "Upcoming", "CLOSE", "Need Update"]


with tabs[0]:
    # 메트릭 컬럼 생성
    metric = st.columns(4)

    # 날짜 선택 섹션
    with metric[0]:
        with st.container(border=False):
            # 날짜 선택 위젯
            selected_date = st.date_input(
                "Select a date:",
                config.today,
                min_value=dt.date(2022, 1, 1),
                max_value=config.today.date(),
                format="YYYY-MM-DD",
            )
            selected_date = dt.datetime.strptime(
                selected_date.strftime("%Y-%m-%d"), "%Y-%m-%d"
            )

            # 주간 범위 계산
            start_of_week = selected_date - dt.timedelta(days=selected_date.weekday())
            end_of_week = start_of_week + dt.timedelta(days=6)

            # 검색 기간 표시
            st.markdown(
                f"**Search Period** :  {start_of_week.strftime('%Y-%m-%d')} ~ {end_of_week.strftime('%Y-%m-%d')}"
            )
            st.info(
                "Shows the progress of each menu in the CQMS for the week based on the selected date."
            )

    # 품질 이슈 메트릭
    with metric[1]:
        with st.container(border=True):
            # 현재 주와 이전 주 데이터 조회
            df_pivot_qi = df_quality_issue.pivot_quality_by_week_and_status(
                start_date=start_of_week, end_date=end_of_week
            )
            before_df_pivot_qi = df_quality_issue.pivot_quality_by_week_and_status(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # Global 데이터 필터링
            df_current = df_pivot_qi[df_pivot_qi["PLANT"] == "Global"].iloc[0]
            df_before = before_df_pivot_qi[
                before_df_pivot_qi["PLANT"] == "Global"
            ].iloc[0]

            st.subheader("Quality Issue")
            cols = st.columns(2)

            # 메트릭 표시
            for i, key in enumerate(all_status):
                value = df_current[key]
                DELTA = int(value - df_before[key]) if key == "On-going" else None
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )

    # 4M 변경 메트릭
    with metric[2]:
        with st.container(border=True):
            # 현재 주와 이전 주 데이터 조회
            df_pivot_4m = df_4m_change.df_pivot_4m(
                start_date=start_of_week, end_date=end_of_week
            )
            before_df_pivot_4m = df_4m_change.df_pivot_4m(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # Global 데이터 필터링
            df_current = df_pivot_4m[df_pivot_4m["PLANT"] == "Global"].iloc[0]
            df_before = before_df_pivot_4m[
                before_df_pivot_4m["PLANT"] == "Global"
            ].iloc[0]

            st.subheader("4M Change")
            cols = st.columns(2)

            # 메트릭 표시
            for i, key in enumerate(all_status):
                value = df_current[key]
                DELTA = int(value - df_before[key]) if key == "On-going" else None
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )

    # 감사 메트릭
    with metric[3]:
        with st.container(border=True):
            # 현재 주와 이전 주 데이터 조회
            df_pivot_audit = df_customer_audit.df_pivot_audit(
                start_date=start_of_week, end_date=end_of_week
            )
            before_df_pivot_audit = df_customer_audit.df_pivot_audit(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # Global 데이터 필터링
            df_current = df_pivot_audit[df_pivot_audit["PLANT"] == "Global"].iloc[0]
            df_before = before_df_pivot_audit[
                before_df_pivot_audit["PLANT"] == "Global"
            ].iloc[0]

            st.subheader("Audit")
            cols = st.columns(2)

            # 메트릭 표시
            for i, key in enumerate(all_status_for_Audit):
                value = df_current[key]
                DELTA = int(value - df_before[key]) if key == "Need Update" else None
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )
    # Quality Issue 섹션
    st.header("Quality Issue")

    # 레이아웃 설정 (히트맵:데이터프레임 = 3:5)
    cols = st.columns([3, 5])

    # 히트맵 표시
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_qi_weekly(start_of_week, end_of_week)
        st.plotly_chart(fig, use_container_width=True)

    # 데이터프레임 표시
    with cols[1]:
        # 데이터 로드
        df = df_quality_issue.load_quality_issues_by_week(start_of_week, end_of_week)

        # 상태 필터
        selected_status = st.radio(
            "Selection",
            all_status,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="qi",
        )
        filtered_df = df[df["Status"] == selected_status]

        # 표시할 컬럼 정의
        display_columns = [
            "OEQ GROUP",
            "PLANT",
            "M_CODE",
            "OEM",
            "VEH",
            "PJT",
            "REG_DATE",
            "MTTC",
            "PNL_NM",
            "URL",
            "TYPE",
            "CAT",
            "SUB_CAT",
            "LOCATION",
            "MARKET",
            "Status",
        ]

        # 컬럼 설정 정의
        column_config = {
            "DOC_NO": st.column_config.TextColumn("Doc. No"),
            "M_CODE": st.column_config.TextColumn("M-Code"),
            "REG_DATE": st.column_config.DateColumn(
                "Registration", format="YYYY-MM-DD"
            ),
            "PNL_NM": st.column_config.TextColumn("Owner"),
            "CATEGORY": st.column_config.TextColumn("Category"),
            "SUB_CATEGORY": st.column_config.TextColumn("Sub Category"),
            "ISSUE_REGIST_DATE": st.column_config.DateColumn(
                "Countermeasure", format="YYYY-MM-DD"
            ),
            "COMP_DATE": st.column_config.DateColumn("Complete", format="YYYY-MM-DD"),
            "HK_FAULT_YN": st.column_config.TextColumn("HK fault"),
            "URL": st.column_config.LinkColumn("Link", display_text="Link"),
        }

        # 데이터프레임 표시
        st.dataframe(
            filtered_df[display_columns],
            column_config=column_config,
            use_container_width=True,
        )

    # 4M Change 섹션
    st.header("4M Change")

    # 레이아웃 설정: 히트맵(3) + 데이터프레임(5) 비율로 분할
    cols = st.columns([3, 5])

    # 히트맵 표시
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_4m_weekly(start_of_week, end_of_week)
        st.plotly_chart(fig, use_container_width=True)

    # 데이터프레임 표시
    with cols[1]:
        # 데이터 필터링
        df = df_4m_change.filtered_4m_by_weekly(start_of_week, end_of_week)

        # 상태 필터 라디오 버튼
        selected_status = st.radio(
            "Selection",
            all_status,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="4M",
        )
        filtered_4m_weekly = df[df["STATUS"] == selected_status]

        # 표시할 컬럼 정의
        display_columns = [
            "DOC_NO",
            "PLANT",
            "M_CODE",
            "PURPOSE",
            "SUBJECT",
            "STATUS",
            "REQUESTER",
            "REG_DATE",
            "COMP_DATE",
            "URL",
            "Status",
        ]

        # 컬럼 설정 정의
        column_config = {
            "DOC_NO": st.column_config.TextColumn("Doc. No"),
            "URL": st.column_config.LinkColumn(
                "Link", display_text="Link", width="small"
            ),
            "REG_DATE": st.column_config.DateColumn(
                "Registration", format="YYYY-MM-DD"
            ),
            "COMP_DATE": st.column_config.DateColumn("Complete", format="YYYY-MM-DD"),
        }

        # 데이터프레임 표시
        st.dataframe(
            filtered_4m_weekly,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

    # OE Audit 섹션 헤더
    st.header("OE Audit")

    # 3:5 비율로 컬럼 분할
    cols = st.columns([3, 5])

    # 왼쪽 컬럼: 히트맵 시각화
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_audit_weekly(
            start_of_week, end_of_week
        )
        st.plotly_chart(fig, use_container_width=True)

    # 오른쪽 컬럼: 데이터 필터링 및 테이블 표시
    with cols[1]:
        # 상태 필터 라디오 버튼
        selected_status = st.radio(
            "Selection",
            all_status_for_Audit,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="audit",
        )

        # 데이터 필터링
        df = df_customer_audit.df_audit_weekly(start_of_week, end_of_week)
        filtered_customer_audit = df[df["STATUS"] == selected_status]

        # 컬럼 설정 정의
        audit_column_config = {
            "CAR_MAKER": st.column_config.TextColumn("OEM"),
            "AUDIT_SUBJECT": st.column_config.TextColumn("Subject"),
            "START_DT": st.column_config.DateColumn("Audit Start", format="YYYY-MM-DD"),
            "END_DT": st.column_config.DateColumn("Audit End", format="YYYY-MM-DD"),
            "OWNER_ACC_NO": st.column_config.TextColumn("Owner"),
            "REG_DT": st.column_config.DateColumn("Registration", format="YYYY-MM-DD"),
            "COMP_DT": st.column_config.DateColumn("Update", format="YYYY-MM-DD"),
            "URL": st.column_config.LinkColumn("Link", display_text="Link"),
        }
        # 데이터프레임 표시 (인덱스 숨김)
        st.dataframe(
            filtered_customer_audit,
            column_config=audit_column_config,
            use_container_width=True,
            hide_index=True,
        )
