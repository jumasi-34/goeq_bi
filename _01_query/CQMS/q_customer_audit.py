"""
CQMS customer audit 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself


CTE_CQMS_AUDIT_MAIN = """--sql
    SELECT
        DECODE(AUDIT_TYPE, 'S', 'System', 'P', 'Project') TYPE,
        AUDIT_SUBJECT SUBJECT, 
        TO_CHAR(AUDIT_START_DATE, 'YYYY-MM-DD') START_DT, 
        TO_CHAR(AUDIT_END_DATE, 'YYYY-MM-DD') END_DT, 
        OWNER_ACC_NO OWNER_ID, 
        TO_CHAR(CREATE_DATE, 'YYYY-MM-DD') REG_DT, 
        TO_CHAR(UPDATE_DATE, 'YYYY-MM-DD') COMP_DT, 
        DECODE(AUDIT_STATUS, 
            'CUSTOMER_AUDIT_ARENA_REPORT_C', 
            'COMPLETE', 
            'CUSTOMER_AUDIT_REG_START', 
            'OPEN',
            'CUSTOMER_AUDIT_DELETED',
            'DELETED'
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
        CQMS_CUSTOMER_AUDIT_SEQ URL,
    FROM HKT_DW.EQMSUSER.CQMS_CUSTOMER_AUDIT_MATERIAL
"""


def query_customer_audit():
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


def main():
    test_query_by_itself(query_customer_audit)


if __name__ == "__main__":
    main()
