"""
HOPE 셀인 데이터 쿼리 관리 모듈

- HOPE 셀인 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 공장별 월간 셀인 데이터와 전기차 셀인 데이터를 조회하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.BI_DWUSER.SAP_ZSDT02068

작성자: [Your Name]
"""

import sys
import logging
from typing import Optional
import os

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _01_query.HOPE.q_hope import CTE_HOPE_OE_APP_UNIQUE, CTE_HOPE_OE_APP_ALL
from _01_query.helper_sql import test_query_by_itself

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SQL 쿼리 템플릿 정의 ---
CTE_HOPE_SELL_IN = """--sql
    SELECT
        MATERIAL AS M_CODE,
        SUBSTRING(BILMON, 1, 4) AS "YYYY",
        SUBSTRING(BILMON, 5, 2) AS "MM",
        SUM(quantity) AS SUPP_QTY,
        ZOERESEG AS "OERE"
    FROM HKT_DW.BI_DWUSER.SAP_ZSDT02068
    GROUP BY 
        M_CODE,
        ZOERESEG,
        SUBSTRING(BILMON, 1, 4),
        SUBSTRING(BILMON, 5, 2)
"""


def sellin_3_years(year: int) -> str:
    """
    공장별 3년간의 월간 셀인 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    year : int
        조회 종료 연도

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
    WITH
        SELLIN AS ({CTE_HOPE_SELL_IN}),
        OEAPP AS ({CTE_HOPE_OE_APP_UNIQUE})
    SELECT 
        OEAPP.PLANT,
        SELLIN.YYYY,
        SELLIN.MM,
        SUM(SELLIN.SUPP_QTY) AS SUPP_QTY
    FROM SELLIN
    LEFT JOIN OEAPP 
        ON SELLIN.M_CODE = OEAPP.M_CODE
    WHERE 
        1=1
        AND SELLIN.YYYY BETWEEN {year-2} AND {year}
        AND OEAPP.PLANT IS NOT NULL
        AND SELLIN.OERE = 'OE'
    GROUP BY 
        OEAPP.PLANT, 
        SELLIN.YYYY,
        SELLIN.MM
    """
    return query


def ev_sellin(year: int) -> str:
    """
    전기차 셀인 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    year : int
        조회 연도

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
    WITH
        SELLIN AS ({CTE_HOPE_SELL_IN}),
        OEAPP AS ({CTE_HOPE_OE_APP_ALL})
    SELECT
        M_CODE,
        CASE
            WHEN M_CODE IN (
                SELECT DISTINCT M_CODE 
                FROM OEAPP 
                WHERE EV IN ('EV', 'FCEV')
            ) THEN 'Y'
            ELSE 'N'
        END AS EV,
        SUPP_QTY
    FROM SELLIN
    WHERE 1=1
        AND YYYY = {year}
        AND OERE = 'OE'
    """
    return query


def main():
    """
    모듈의 주요 기능을 테스트하는 메인 함수입니다.
    """
    try:
        # 1. 3년간 셀인 데이터 쿼리 생성 테스트
        logger.info("1. 3년간 셀인 데이터 쿼리 생성 테스트")
        sellin_query = sellin_3_years(2024)
        logger.info(f"생성된 셀인 쿼리:\n{sellin_query[:200]}...")

        # 2. 전기차 셀인 데이터 쿼리 생성 테스트
        logger.info("\n2. 전기차 셀인 데이터 쿼리 생성 테스트")
        ev_query = ev_sellin(2024)
        logger.info(f"생성된 전기차 셀인 쿼리:\n{ev_query[:200]}...")

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    main()
