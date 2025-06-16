"""
GMES 롤링 저항(RR) 쿼리 관리 모듈

- GMES 롤링 저항 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- OE 테스트 데이터와 일반 테스트 데이터를 조회하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.MES.QLT_D_LQLTTR309, HKT_DW.MES.QLT_F_LQLTTR316, HKT_DW.MES.QLT_D_LQLTTR510

작성자: [Your Name]
"""

import pandas as pd
from typing import Optional, Union
import logging
import os
import sys

project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SQL 쿼리 템플릿 정의 ---
CTE_MES_RR_SAMPLE = """--sql
    SELECT
        PLT_CD PLANT,
        SMPL_ID,
        MTL_CD M_CODE,
        TEST_FG,  -- OE (2: OE 데이터만)
        PGS_STS
    FROM
        HKT_DW.MES.QLT_D_LQLTTR309
    WHERE
        1=1
        AND PGS_STS = 80  -- SAMPLE STATUS(80:승인 데이터만)
"""

CTE_MES_RR_TEST_LIST = """--sql
    SELECT
        PLT_CD PLANT,
        SMPL_ID,
        ATCH_SEQ,
        WARM_LOAD,
        RSLT_RRC_CORR,
        RSLT_RRC,
        RSLT_RR,
        STD_TEST_POS,
        JDG,
        TEST_VAL,
        TEST_SEQ,
        ROW_NUMBER() OVER (
            PARTITION BY PLT_CD, SMPL_ID, TEST_SEQ 
            ORDER BY ATCH_SEQ DESC
        ) AS rn  -- 마지막 첨부만 사용
    FROM
        HKT_DW.MES.QLT_F_LQLTTR316
    WHERE
        1=1
"""

CTE_MES_RR_OE_SPEC = """--sql
    SELECT DISTINCT
        PLT_CD PLANT, 
        MTL_CD M_CODE, 
        CAR_MAKER_2 OEM,
        V_MODEL Veh,
        USE_TROT MASS,
        APV_RRC_MIN SPEC_MIN,
        APV_RRC_MAX SPEC_MAX,
        TEST_FG, 
        USE_TROT MASS_YN, 
        START_DATE START_DATE,
        END_DATE END_DATE,
        SPEC_CHANGE,
        APP_DATE CHG_APP_DATE,
        RR_INDEX,
        SELANT_FLG
    FROM 
        HKT_DW.MES.QLT_D_LQLTTR510    
"""

CTE_MES_CODE_RR_TEST_METHOD = """--sql
    SELECT 
        CD_ITEM, 
        CD_ITEM_NM
    FROM 
        HKT_DW.MES.MST_D_LCOMTR107
    WHERE 
        CD_ID = 'F570'  -- OE RR RR CODE 변환
"""


def rr(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    test_fg: str = "OE",
) -> str:
    """
    롤링 저항 테스트 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    start_date : Optional[str], optional
        조회 시작일 (YYYY-MM-DD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일 (YYYY-MM-DD 형식). 기본값은 None
    test_fg : str, optional
        테스트 구분 ("OE" 또는 "일반"). 기본값은 "OE"

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    # 1. 테스트 구분 코드 설정
    test_fg_code = 2 if test_fg == "OE" else 1

    # 2. 날짜 조건 분리
    date_filter = ""
    if start_date and end_date:
        date_filter = f"""
            AND TRY_TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') 
                BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        """

    # 3. 전체 쿼리 생성
    query = f"""--sql
        WITH
            SPL AS ({CTE_MES_RR_SAMPLE}),
            LST AS ({CTE_MES_RR_TEST_LIST}),
            SPEC AS ({CTE_MES_RR_OE_SPEC}),
            CD AS ({CTE_MES_CODE_RR_TEST_METHOD})
        SELECT
            SPL.PLANT,
            TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') SMPL_DATE,
            SPL.M_CODE,
            LST.WARM_LOAD,
            LST.RSLT_RRC AS RRC,
            LST.RSLT_RRC_CORR AS HK_GLOBAL,
            LST.STD_TEST_POS AS POSITION,
            DECODE(LST.JDG, 10, 'OK', 20, '재시험', 30, 'NG', 40, 'N/A') AS JDG,
            LST.TEST_VAL AS TEST_RESULT_OLD,
            CD.CD_ITEM_NM AS OE_TEST_METHOD,
            SPEC.MASS_YN,
            TRY_TO_DATE(SPEC.START_DATE, 'YYYYMMDD') START_DT,
            TRY_TO_DATE(SPEC.END_DATE, 'YYYYMMDD') END_DT
        FROM SPL
        LEFT JOIN LST 
            ON SPL.PLANT = LST.PLANT 
            AND SPL.SMPL_ID = LST.SMPL_ID
        LEFT JOIN SPEC 
            ON SPL.PLANT = SPEC.PLANT 
            AND SPL.M_CODE = SPEC.M_CODE
        LEFT JOIN CD 
            ON SPEC.TEST_FG = CD.CD_ITEM
        WHERE
            1=1
            {date_filter}
            AND LST.rn = 1
            AND SUBSTR(SPL.SMPL_ID, 1, 2) > 20  -- 20년 이후 데이터만
            AND SPEC.TEST_FG IS NOT NULL
            AND TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') 
                BETWEEN TRY_TO_DATE(SPEC.START_DATE, 'YYYYMMDD') 
                AND IFNULL(
                    TRY_TO_DATE(SPEC.END_DATE, 'YYYYMMDD'), 
                    TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD')
                )
            AND SPL.TEST_FG = {test_fg_code}
    """
    return query


def rr_oe_list() -> str:
    """
    OE 롤링 저항 테스트 목록을 조회하는 SQL 쿼리를 생성합니다.

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
        WITH
            RR_OE_LIST AS ({CTE_MES_RR_OE_SPEC}),
            CD AS ({CTE_MES_CODE_RR_TEST_METHOD})
        SELECT
            RR_OE_LIST.*,
            CD.CD_ITEM
        FROM RR_OE_LIST
        LEFT JOIN CD 
            ON RR_OE_LIST.TEST_FG = CD.CD_ITEM
    """
    return query


# ISO Local to HK Global 보정 계수 데이터 로드
PATH = "_01_query/CSV/iso_local_to_hkGlobal.csv"
rr_corr_csv = pd.read_csv(PATH)


def main():
    """
    모듈의 주요 기능을 테스트하는 메인 함수입니다.
    """
    try:
        # 1. 기본 OE 테스트 쿼리 생성 테스트
        logger.info("1. 기본 OE 테스트 쿼리 생성 테스트")
        oe_query = rr(test_fg="OE")
        logger.info(f"생성된 OE 쿼리:\n{oe_query[:200]}...")

        # 2. 날짜 조건이 포함된 쿼리 생성 테스트
        logger.info("\n2. 날짜 조건이 포함된 쿼리 생성 테스트")
        date_query = rr(start_date="2023-01-01", end_date="2023-12-31", test_fg="OE")
        logger.info(f"생성된 날짜 조건 쿼리:\n{date_query[:200]}...")

        # 3. OE 리스트 쿼리 생성 테스트
        logger.info("\n3. OE 리스트 쿼리 생성 테스트")
        oe_list_query = rr_oe_list()
        logger.info(f"생성된 OE 리스트 쿼리:\n{oe_list_query[:200]}...")

        # 4. 보정 계수 데이터 로드 테스트
        logger.info("\n4. 보정 계수 데이터 로드 테스트")
        logger.info(f"로드된 보정 계수 데이터:\n{rr_corr_csv.head()}")

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    main()
