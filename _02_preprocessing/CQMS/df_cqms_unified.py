import os
import sys
import pandas as pd

from _00_database.db_client import get_client
from _01_query.CQMS import q_4m_change, q_quality_issue, q_customer_audit

project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


def get_cqms_unified_df(m_code):
    """
    CQMS 데이터를 로드하고 전처리합니다.

    Args:
        m_code (str): 조회할 M-Code

    Returns:
        pd.DataFrame: 전처리된 CQMS 데이터
    """
    # Quality Issue 데이터 로드 및 전처리
    q_issue = get_client("snowflake").execute(q_quality_issue.query_quality_issue())
    q_issue.columns = q_issue.columns.str.upper()
    q_issue = q_issue[q_issue["M_CODE"] == m_code]
    q_issue["SUBJECT"] = (
        q_issue["TYPE"] + " - " + q_issue["CAT"] + " - " + q_issue["SUB_CAT"]
    )
    q_issue["CATEGORY"] = "Quality Issue"
    q_issue = q_issue[["CATEGORY", "SUBJECT", "REG_DATE", "SEQ"]]
    q_issue = q_issue.rename(columns={"SEQ": "URL"})

    # 4M Change 데이터 로드 및 전처리
    chg_4m = get_client("snowflake").execute(q_4m_change.query_4m_change())
    chg_4m.columns = chg_4m.columns.str.upper()
    chg_4m = chg_4m[chg_4m["M_CODE"] == m_code]
    chg_4m["CATEGORY"] = "4M Change"
    chg_4m = chg_4m[["CATEGORY", "SUBJECT", "REG_DATE", "URL"]]

    # Customer Audit 데이터 로드 및 전처리
    audit = get_client("snowflake").execute(q_customer_audit.query_customer_audit())
    audit.columns = audit.columns.str.upper()
    audit = audit[audit["M_CODE"] == m_code]
    audit["CATEGORY"] = "Audit"
    audit = audit[["CATEGORY", "SUBJECT", "START_DT", "URL"]]
    audit = audit.rename(columns={"START_DT": "REG_DATE"})

    # 데이터 통합 및 전처리
    cqms_data = pd.concat([q_issue, chg_4m, audit])

    # REG_DATE 컬럼이 datetime 타입인지 확인하고 변환
    if not pd.api.types.is_datetime64_any_dtype(cqms_data["REG_DATE"]):
        cqms_data["REG_DATE"] = pd.to_datetime(cqms_data["REG_DATE"], errors="coerce")

    # 날짜 형식 변환 및 정렬
    cqms_data["REG_DATE"] = cqms_data["REG_DATE"].dt.strftime("%Y-%m-%d")
    cqms_data = cqms_data.sort_values(by="REG_DATE", ascending=False)
    cqms_data["CATEGORY"] = pd.Categorical(
        cqms_data["CATEGORY"],
        categories=["Quality Issue", "4M Change", "Audit"],
        ordered=True,
    )

    return cqms_data
