"""
CQMS 4M 변경 쿼리 관리 모듈

- CQMS 4M 변경 관리용 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 목적/상태 코드를 한글로 매핑하고, 대시보드/리포트용 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.EQMSUSER.CQMS_CHANGE_M, CQMS_SUB_MCODE_D, SAP_ZSTT70041

작성자: [Your Name]
"""

import sys
from datetime import datetime as dt
import pandas as pd
import numpy as np
from typing import List, Optional

from _05_commons import config

sys.path.append(config.PROJECT_ROOT)
from _01_query.helper_sql import convert_dict_to_decode, test_query_by_itself

# --- 목적/상태 코드 매핑 상수 정의 ---
PURPOSE_4M_DICT = {
    "000": "Nonconformity Improvement",  # 부적합 개선
    "001": "Performance Improvement",  # 성능 개선
    "002": "Cost reduction",  # 원가 절감
    "003": "Facility movement",  # 설비 이동
}
DECODE_PURPOSE_4M = convert_dict_to_decode(PURPOSE_4M_DICT)

STATUS_4M_DICT = {
    "000": "Saved",  # 저장됨
    "001": "Awaiting approval(Request)",  # 결재 대기(신청)
    "002": "Waiting for Reception",  # 접수 대기
    "003": "Under Verification",  # 검증 중
    "004": "Waiting for Final Approval",  # 최종 결재 대기
    "005": "Complete",  # 완료
    "006": "Reject(Request)",  # 반려(신청)
    "007": "Reject(Final Approval)",  # 반려(최종결재)
}
DECODE_STATUS_4M = convert_dict_to_decode(STATUS_4M_DICT)

# --- SQL 쿼리 템플릿 정의 ---
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
        ID,
        M_SIZE,
        M_PATTERN,
        DOCUMENT_NO DOC_NO,
        M_CODE
    FROM HKT_DW.EQMSUSER.CQMS_SUB_MCODE_D
"""

CTE_HOPE_OE_APP_UNIQUE = """--sql
    SELECT DISTINCT
        LBTXT PLANT,         -- 공장 코드
        MATNR M_CODE,        -- 자재 코드
        ZCARMAKER1,          -- 자동차 메이커
        LISTAGG(ZCARMAKER1 || '(' || ZPROJECT || ')', ', ' ) WITHIN GROUP(ORDER BY LBTXT) AS PROJECT -- 프로젝트 정보
    FROM (SELECT DISTINCT LBTXT, MATNR, ZCARMAKER1, ZPROJECT 
            FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041)
    GROUP BY LBTXT, MATNR, ZCARMAKER1
"""


def query_4m_change() -> str:
    """
    CQMS 4M 변경 현황 대시보드/리포트용 메인 SQL 쿼리를 생성합니다.

    반환값
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
        WITH 
            MAIN AS ({CTE_CQMS_4M_MAIN}),      -- 메인 변경문서
            MTL AS ({CTE_CQMS_4M_MATERIAL}),   -- 자재 정보
            APP AS ({CTE_HOPE_OE_APP_UNIQUE})  -- 프로젝트/공장 정보
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
        LEFT JOIN (
            SELECT DISTINCT
                MTL.DOC_NO,
                APP.PLANT,
                MTL.M_CODE
            FROM MTL 
            LEFT JOIN APP 
                ON MTL.M_CODE = APP.M_CODE
        ) SUB
            ON MAIN.DOC_NO = SUB.DOC_NO
        WHERE 1=1
            AND MAIN.DEL_YN != 'Y'           -- 삭제되지 않은 문서만 조회
            AND MAIN.STATUS != 'Reject(Request)' -- 반려(신청) 상태 제외
        """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 4M 변경 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(query_4m_change)


if __name__ == "__main__":
    main()
