"""
Workplace monitoring dashboard for tracking Quality Issues, 4M Changes, and Audits.
Provides weekly status updates and metrics for each plant.
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


# st.set_page_config(layout="wide")
tabs = st.tabs(["Weekly Work Place"])

all_status = ["Open", "Open & Close", "Close", "On-going"]
all_status_for_Audit = ["NEW", "Upcoming", "CLOSE", "Need Update"]


with tabs[0]:
    metric = st.columns(4)

    with metric[0]:
        # 날짜 선택 섹션
        with st.container(border=False):
            selected_date = st.date_input(
                "Select a date:",
                config.today,
                min_value=dt.date(2022, 1, 1),
                max_value=config.today.date(),
                format="YYYY-MM-DD",
            )  # 날짜 선택
            selected_date = dt.datetime.strptime(
                selected_date.strftime("%Y-%m-%d"), "%Y-%m-%d"
            )

            start_of_week = selected_date - dt.timedelta(
                days=selected_date.weekday()
            )  # 선택일 기준 시작점
            end_of_week = start_of_week + dt.timedelta(days=6)  # 선택일 기준 끝점

            st.markdown(
                f"**Search Period** :  {start_of_week.strftime('%Y-%m-%d')} ~ {end_of_week.strftime('%Y-%m-%d')}"
            )  # 검색 기간 디스플레이
            st.info(
                "Shows the progress of each menu in the CQMS for the week based on the selected date."
            )

    with metric[1]:
        with st.container(border=True):
            df_pivot_qi = df_quality_issue.pivot_quality_by_week_and_status(
                start_date=start_of_week, end_date=end_of_week
            )
            before_df_pivot_qi = df_quality_issue.pivot_quality_by_week_and_status(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # "Global" 필터 한 번만 수행
            df_current = df_pivot_qi[df_pivot_qi["PLANT"] == "Global"].iloc[0]
            df_before = before_df_pivot_qi[
                before_df_pivot_qi["PLANT"] == "Global"
            ].iloc[0]

            # 보여줄 항목
            metric_keys = ["Open", "Open & Close", "Close", "On-going"]

            st.subheader("Quality Issue")
            cols = st.columns(2)

            for i, key in enumerate(metric_keys):
                value = df_current[key]
                DELTA = None
                if key == "On-going":
                    DELTA = int(value - df_before[key])
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )

    with metric[2]:
        with st.container(border=True):

            df_pivot_4m = df_4m_change.df_pivot_4m(
                start_date=start_of_week, end_date=end_of_week
            )

            before_df_pivot_4m = df_4m_change.df_pivot_4m(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # "Global" 필터 한 번만 수행
            df_current = df_pivot_4m[df_pivot_4m["PLANT"] == "Global"].iloc[0]
            df_before = before_df_pivot_4m[
                before_df_pivot_4m["PLANT"] == "Global"
            ].iloc[0]

            # 보여줄 항목
            metric_keys = ["Open", "Open & Close", "Close", "On-going"]

            st.subheader("4M Change")
            cols = st.columns(2)

            for i, key in enumerate(metric_keys):
                value = df_current[key]
                DELTA = None
                if key == "On-going":
                    DELTA = int(value - df_before[key])
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )
    with metric[3]:
        with st.container(border=True):

            df_pivot_audit = df_customer_audit.df_pivot_audit(
                start_date=start_of_week, end_date=end_of_week
            )

            before_df_pivot_audit = df_customer_audit.df_pivot_audit(
                start_date=start_of_week - dt.timedelta(weeks=1),
                end_date=end_of_week - dt.timedelta(weeks=1),
            )

            # "Global" 필터 한 번만 수행
            df_current = df_pivot_audit[df_pivot_audit["PLANT"] == "Global"].iloc[0]

            df_before = before_df_pivot_audit[
                before_df_pivot_audit["PLANT"] == "Global"
            ].iloc[0]

            # 보여줄 항목
            metric_keys = ["NEW", "Upcoming", "CLOSE", "Need Update"]

            st.subheader("Audit")
            cols = st.columns(2)

            for i, key in enumerate(metric_keys):
                value = df_current[key]
                DELTA = None
                if key == "Need Update":
                    DELTA = int(value - df_before[key])
                with cols[i // 2]:
                    st.metric(
                        label=key,
                        value=value,
                        delta=DELTA,
                        delta_color="inverse" if DELTA is not None else "normal",
                    )

    st.header("Quality Issue")
    cols = st.columns([3, 5])
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_qi_weekly(start_of_week, end_of_week)
        st.plotly_chart(fig, use_container_width=True)
    with cols[1]:
        df = df_quality_issue.load_quality_issues_by_week(start_of_week, end_of_week)

        # data filter selection
        selected_status = st.radio(
            "Selection",
            all_status,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="qi",
        )
        filtered_df = df[df["Status"] == selected_status]

        # dataframe visualization
        remain_col = [
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
        qi_column_config_dic = dict(
            DOC_NO=st.column_config.TextColumn("Doc. No"),
            M_CODE=st.column_config.TextColumn("M-Code"),
            REG_DATE=st.column_config.DateColumn("Registration", format="YYYY-MM-DD"),
            PNL_NM=st.column_config.TextColumn("Owner"),
            CATEGORY=st.column_config.TextColumn("Category"),
            SUB_CATEGORY=st.column_config.TextColumn("Sub Cateogory"),
            ISSUE_REGIST_DATE=st.column_config.DateColumn(
                "Coutermeasure", format="YYYY-MM-DD"
            ),
            COMP_DATE=st.column_config.DateColumn("Complete", format="YYYY-MM-DD"),
            HK_FAULT_YN=st.column_config.TextColumn("HK fault"),
            URL=st.column_config.LinkColumn("Link", display_text="Link"),
        )
        st.dataframe(
            filtered_df[remain_col],
            column_config=qi_column_config_dic,
            use_container_width=True,
        )

    st.header("4M Change")
    cols = st.columns([3, 5])
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_4m_weekly(start_of_week, end_of_week)
        st.plotly_chart(fig, use_container_width=True)
    with cols[1]:
        df = df_4m_change.filtered_4m_by_weekly(start_of_week, end_of_week)

        # data filter selection
        selected_status = st.radio(
            "Selection",
            all_status,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="4M",
        )
        filtered_4m_weekly = df[df["STATUS"] == selected_status]

        # dataframe visualization
        remain_col = [
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
        _4m_column_config_dic = dict(
            DOC_NO=st.column_config.TextColumn("Doc. No"),
            URL=st.column_config.LinkColumn("Link", display_text="Link", width="small"),
            REG_DATE=st.column_config.DateColumn("Registration", format="YYYY-MM-DD"),
            COMP_DATE=st.column_config.DateColumn("Complete", format="YYYY-MM-DD"),
        )
        st.dataframe(
            filtered_4m_weekly,
            column_config=_4m_column_config_dic,
            use_container_width=True,
        )

    st.header("OE Audit")
    cols = st.columns([3, 5])
    with cols[0]:
        fig = bi_201_weekly_cqms_monitor.heatmap_audit_weekly(
            start_of_week, end_of_week
        )
        st.plotly_chart(fig, use_container_width=True)
    with cols[1]:

        # data filter selection
        selected_status = st.radio(
            "Selection",
            all_status_for_Audit,
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="audit",
        )
        df = df_customer_audit.df_audit_weekly(start_of_week, end_of_week)
        filtered_customer_audit = df[df["STATUS"] == selected_status]

        # dataframe visualization
        audit_column_config_dic = dict(
            CAR_MAKER=st.column_config.TextColumn("OEM"),
            AUDIT_SUBJECT=st.column_config.TextColumn("Subject"),
            START_DT=st.column_config.DateColumn("Audit Start", format="YYYY-MM-DD"),
            END_DT=st.column_config.DateColumn("Audit End", format="YYYY-MM-DD"),
            OWNER_ACC_NO=st.column_config.TextColumn("Owner"),
            REG_DT=st.column_config.DateColumn("Registration", format="YYYY-MM-DD"),
            COMP_DT=st.column_config.DateColumn("Update", format="YYYY-MM-DD"),
            URL=st.column_config.LinkColumn("Link", display_text="Link"),
        )

        st.dataframe(
            filtered_customer_audit,
            column_config=audit_column_config_dic,
            use_container_width=True,
        )
