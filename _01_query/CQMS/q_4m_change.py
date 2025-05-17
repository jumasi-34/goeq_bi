"""
CQMS 4m change 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import convert_dict_to_decode, test_query_by_itself

purpose_4M_dict = {
    "000": "Nonconformity Improvement",
    "001": "Performance Improvement",
    "002": "Cost reduction",
    "003": "Facility movement",
}
DECODE_PURPOSE_4M = convert_dict_to_decode(purpose_4M_dict)
status_4M_dict = {
    "000": "Saved",
    "001": "Awaiting approval(Request)",
    "002": "Waiting for Reception",
    "003": "Under Verification",
    "004": "Waiting for Final Approval",
    "005": "Complete",
    "006": "Reject(Request)",
    "007": "Reject(Final Approval)",
}
DECODE_STATUS_4M = convert_dict_to_decode(status_4M_dict)

CTE_CQMS_4M_MAIN = f"""--sql
    SELECT
        DOCUMENT_NO DOC_NO,
        DECODE(DOC_CATEGORY, {DECODE_PURPOSE_4M}) PURPOSE,
        DOC_SUBJECT SUBJECT,
        DECODE(DOC_STATUS , {DECODE_STATUS_4M}) STATUS,
        CREATE_USER_ID REQUESTER,
        TO_DATE(CREATE_DT, 'YYYYMMDD') REG_DATE,
        TO_DATE(DOC_END_ARENA_UPDATE_DT, 'YYYYMMDD') COMP_DATE,
        ID URL,
        DEL_YN
    FROM
        HKT_DW.EQMSUSER.CQMS_CHANGE_M
"""
CTE_CQMS_4M_MATERIAL = """--sql
    SELECT DISTINCT
        DOCUMENT_NO DOC_NO,
        M_CODE
    FROM HKT_DW.EQMSUSER.CQMS_SUB_MCODE_D
"""
CTE_HOPE_OE_APP_UNIQUE = """--sql
    SELECT DISTINCT
        LBTXT PLANT,  -- 공장지 코드
        MATNR M_CODE, -- 제품 코드
        ZCARMAKER1,
        LISTAGG(ZCARMAKER1 || '(' || ZPROJECT || ')', ', ' ) WITHIN GROUP(ORDER BY LBTXT) AS PROJECT -- PROJECT 정보
    FROM (SELECT DISTINCT LBTXT, MATNR, ZCARMAKER1, ZPROJECT 
            FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041)
    GROUP BY LBTXT, MATNR, ZCARMAKER1
    """


def query_4m_change():
    query = f"""--sql
        WITH 
            MAIN AS ({CTE_CQMS_4M_MAIN}),
            MTL AS ({CTE_CQMS_4M_MATERIAL}),
            APP AS ({CTE_HOPE_OE_APP_UNIQUE})
        SELECT
            MAIN.DOC_NO,
            SUB.PLANT,
            MAIN.PURPOSE,
            MAIN.SUBJECT,
            MAIN.STATUS,
            MAIN.REQUESTER,
            MAIN.REG_DATE,
            MAIN.COMP_DATE,
            MAIN.URL,
            SUB.M_CODE
        FROM MAIN
        LEFT JOIN (SELECT DISTINCT
                        MTL.DOC_NO,
                        APP.PLANT,
                        MTL.M_CODE
                    FROM MTL 
                    LEFT JOIN APP 
                    ON MTL.M_CODE = APP.M_CODE) SUB
            ON MAIN.DOC_NO = SUB.DOC_NO
        WHERE 1=1
            AND MAIN.DEL_YN != 'Y'
            AND MAIN.STATUS != 'Reject(Request)'
        """
    return query


def main():
    test_query_by_itself(query_4m_change)


if __name__ == "__main__":
    main()
