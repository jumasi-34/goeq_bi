"""
CQMS Quality Issue 쿼리 관리 모듈

- CQMS 품질 이슈 관리용 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 공장/이슈 영역/시장 코드를 매핑하고, 대시보드/리포트용 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.EQMSUSER.CQMS_QUALITY_ISSUE, CQMS_ISSUE_CATEGORY_DATA, CQMS_QUALITY_ISSUE_MATERIAL, ZHRT90041

작성자: [Your Name]
"""

import sys
from typing import Optional

# 절대 경로로 임포트 수정
from _01_query.helper_sql import convert_dict_to_decode, test_query_by_itself

# --- 코드 매핑 상수 정의 ---
PLANT_TO_OEQG_DICT = {  # PLANT <> OEQG
    "KP": "G.OE Quality",
    "DP": "G.OE Quality",
    "IP": "G.OE Quality",
    "JP": "China OE Quality",
    "HP": "China OE Quality",
    "CP": "China OE Quality",
    "MP": "Europe OE Quality",
    "TP": "NA OE Quality",
}
DECODE_PLANT_TO_OEQG = convert_dict_to_decode(PLANT_TO_OEQG_DICT)

ISSUE_AREA_DICT = {
    "01": "In-Line(OE)",
    "02": "Field",
    "03": "Warehouse",
    "04": "Test",
    "05": "Internal",
    "06": "Non-official(In-line)",
}
DECODE_ISSUE_AREA = convert_dict_to_decode(ISSUE_AREA_DICT)

KPI_INCLUSION_DICT = {  # ISSUE_AREA CODE <> KPI
    "01": "Include",
    "02": "Include",
    "03": "Include",
    "04": "Include",
    "05": "Exclude",
    "06": "Exclude",
}
DECODE_KPI_INCLUSION = convert_dict_to_decode(KPI_INCLUSION_DICT)

MARKET_DICT = {
    "01": "Europe",
    "02": "Africa",
    "03": "ASIA(China)",
    "04": "ASIA(Japan)",
    "05": "ASIA(Korea)",
    "06": "ASIA(South East)",
    "07": "Australia",
    "08": "North America",
    "09": "South America",
    "10": "ETC",
}
DECODE_MARKET = convert_dict_to_decode(MARKET_DICT)

# --- SQL 쿼리 템플릿 정의 ---
CTE_CQMS_QI_MAIN = f"""--sql
    SELECT
        CQMS_ISSUE_DOCUMENT_NO "DOC_NO",
        DECODE(PLANT, {DECODE_PLANT_TO_OEQG},'G.OE Quality') AS "OEQ Group",
        PLANT,
        STAGE AS "STAGE",
        OEM,
        VEH_MODEL "VEH",
        PROJECT "PJT",
        ISSUE_ETC,
        DESCRIPTION,
        CAUSE_OF_DEFECT,
        ISSUE_CATEGORY_SEQ_1 TYPE_CD,
        ISSUE_CATEGORY_SEQ_2 CAT_CD,
        ISSUE_CATEGORY_SEQ_3 SUB_CAT_CD,
        OWNER_NO "OWNER_ID",
        RESPONSIBLE_PERSON_NO "RESP_ID",
        OCCURRENCE_DATE OCC_DATE,
        TO_DATE(CREATE_DATE) AS REG_DATE,
        RETURN_TIRE_YN RETURN_YN,
        RETURN_TIRE_RECEIVED_DATE RTN_DATE,
        TO_CHAR(CQMS_ISSUE_ISSUE_ARENA_APPROVAL_DATE, 'YYYY-MM-DD') CTM_DATE,
        IS_HK_FAULT "HK_FAULT_YN",
        TO_CHAR(ISSUE_COMPLETE_DATE, 'YYYY-MM-DD') COMP_DATE,
        DECODE(OE_QUALITY_ISSUE_STATUS,
            'ISSUE_PROCESS_COMPLETE',
            'Complete',
            'On-going') STATUS,
        DECODE(ISSUE_AREA, {DECODE_ISSUE_AREA}) LOCATION,
        DECODE(ISSUE_AREA, {DECODE_KPI_INCLUSION}) KPI,
        DECODE(ISSUE_REGION, {DECODE_MARKET}) MARKET,
        CQMS_QUALITY_ISSUE_SEQ SEQ
    FROM HKT_DW.EQMSUSER.CQMS_QUALITY_ISSUE
    WHERE 1=1
    ORDER BY START_DATE DESC
    """

CTE_CQMS_QI_CAT = """--sql
    SELECT
        SEQ CD,
        DATA_NM CD_NM
    FROM 
        HKT_DW.EQMSUSER.CQMS_ISSUE_CATEGORY_DATA
"""

CTE_CQMS_QI_MATERIAL = """--sql
    SELECT
        CQMS_QUALITY_ISSUE_SEQ SEQ,
        MATERIAL_NO M_CODE
    FROM 
        HKT_DW.EQMSUSER.CQMS_QUALITY_ISSUE_MATERIAL
"""

CTE_HR_PERSONAL = """--sql
    SELECT
        PERNR PNL_NO,
        NACHN PNL_NM
    FROM HKT_DW.BI_GERPUSER.ZHRT90041
"""


def query_quality_issue(year: Optional[int] = None) -> str:
    """
    품질 이슈 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    year : Optional[int], optional
        조회할 연도. 기본값은 None이며, 지정 시 해당 연도와 그 전 2년간의 데이터를 조회합니다.

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
    WITH 
        QI AS ({CTE_CQMS_QI_MAIN}),
        CAT AS ({CTE_CQMS_QI_CAT}),
        M AS ({CTE_CQMS_QI_MATERIAL}),
        PNL AS ({CTE_HR_PERSONAL})
    SELECT 
        QI.*,
        M.M_CODE,
        PNL.PNL_NM,
        A.CD_NM TYPE,
        B.CD_NM CAT,
        C.CD_NM SUB_CAT
    FROM QI
    LEFT JOIN M ON QI.SEQ = M.SEQ
    LEFT JOIN CAT A ON QI.TYPE_CD = A.CD
    LEFT JOIN CAT B ON QI.CAT_CD = B.CD
    LEFT JOIN CAT C ON QI.SUB_CAT_CD = C.CD
    LEFT JOIN PNL ON QI.OWNER_ID = PNL.PNL_NO
    WHERE 1=1
        {f"AND EXTRACT(YEAR FROM QI.REG_DATE) BETWEEN {year}-2 AND {year}" if year else ""}
        AND (HK_FAULT_YN = 'Y' OR HK_FAULT_YN IS NULL)
        AND QI.STAGE = '02'
    """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 품질 이슈 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(query_quality_issue)


if __name__ == "__main__":
    main()
