"""
CQMS 고객사 감사 쿼리 관리 모듈

- CQMS 고객사 감사 관리용 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 감사 유형과 상태 코드를 매핑하고, 대시보드/리포트용 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.EQMSUSER.CQMS_CUSTOMER_AUDIT, CQMS_CUSTOMER_AUDIT_MATERIAL

작성자: [Your Name]
"""

import sys

from _05_commons import config
sys.path.append(config.PROJECT_ROOT)
from _01_query.helper_sql import test_query_by_itself

# --- 감사 유형/상태 코드 매핑 상수 정의 ---
AUDIT_TYPE_DICT = {"S": "System", "P": "Project"}  # 시스템 감사  # 프로젝트 감사

AUDIT_STATUS_DICT = {
    "CUSTOMER_AUDIT_ARENA_REPORT_C": "COMPLETE",  # 완료
    "CUSTOMER_AUDIT_REG_START": "OPEN",  # 진행중
    "CUSTOMER_AUDIT_DELETED": "DELETED",  # 삭제됨
}

# --- SQL 쿼리 템플릿 정의 ---
CTE_CQMS_AUDIT_MAIN = f"""--sql
    SELECT
        DECODE(AUDIT_TYPE, 
            'S', 'System', 
            'P', 'Project'
        ) TYPE,
        AUDIT_SUBJECT SUBJECT, 
        TO_CHAR(AUDIT_START_DATE, 'YYYY-MM-DD') START_DT, 
        TO_CHAR(AUDIT_END_DATE, 'YYYY-MM-DD') END_DT, 
        OWNER_ACC_NO OWNER_ID, 
        TO_CHAR(CREATE_DATE, 'YYYY-MM-DD') REG_DT, 
        TO_CHAR(UPDATE_DATE, 'YYYY-MM-DD') COMP_DT, 
        DECODE(AUDIT_STATUS, 
            'CUSTOMER_AUDIT_ARENA_REPORT_C', 'COMPLETE', 
            'CUSTOMER_AUDIT_REG_START', 'OPEN',
            'CUSTOMER_AUDIT_DELETED', 'DELETED'
        ) STATUS,
        CQMS_CUSTOMER_AUDIT_SEQ URL
    FROM 
        HKT_DW.EQMSUSER.CQMS_CUSTOMER_AUDIT 
"""

CTE_CQMS_AUDIT_MATERIAL = """--sql
    SELECT
        PLANT,
        CAR_MAKER,
        PROJECT,
        MATERIAL M_CODE,
        CQMS_CUSTOMER_AUDIT_SEQ URL
    FROM HKT_DW.EQMSUSER.CQMS_CUSTOMER_AUDIT_MATERIAL
"""


def query_customer_audit() -> str:
    """
    CQMS 고객사 감사 현황 대시보드/리포트용 메인 SQL 쿼리를 생성합니다.

    반환값
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
        WITH
            MAIN AS ({CTE_CQMS_AUDIT_MAIN}),
            SUB AS ({CTE_CQMS_AUDIT_MATERIAL})
        SELECT
            MAIN.TYPE,
            MAIN.SUBJECT,
            MAIN.START_DT,
            MAIN.END_DT,
            MAIN.OWNER_ID,
            MAIN.REG_DT,
            MAIN.COMP_DT,
            MAIN.STATUS,
            MAIN.URL,
            SUB.PLANT,
            SUB.CAR_MAKER,
            SUB.PROJECT,
            SUB.M_CODE
        FROM MAIN
        LEFT JOIN SUB ON MAIN.URL = SUB.URL
        WHERE 1=1
            AND TYPE IN ('System', 'Project')
            AND STATUS != 'DELETED'
    """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 고객사 감사 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(query_customer_audit)


if __name__ == "__main__":
    main()
