"""
GMES 생산 데이터 쿼리 관리 모듈

- GMES 생산 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 월별 생산 현황을 조회하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.MES.MAS_D_LMASTR101, HKT_DW.MES.WRK_F_LWRKTS118

작성자: [Your Name]
"""

import sys
from typing import Optional, List

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

# --- SQL 쿼리 템플릿 정의 ---
CTE_MES_MASTER_ALL = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD,
        STXC
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND SPEC_FG = 'KT'
    """

CTE_MES_PRODUCTION_MONTHLY = """--sql
    SELECT
        PLT_CD PLANT,                      -- 공장지 코드
        SPEC_CD,                           -- SPEC 코드
        SUBSTRING(WRK_DATE, 1, 4) YYYY,    -- 연도
        SUBSTRING(WRK_DATE, 5, 2) MM,      -- 월
        SUM(PRDT_QTY) PRDT_QTY             -- 생산량
    FROM HKT_DW.MES.WRK_F_LWRKTS118
    WHERE 1=1
        AND SPEC_CD LIKE 'KT%'
    GROUP BY 
        PLT_CD, 
        SPEC_CD, 
        SUBSTRING(WRK_DATE, 1, 4),
        SUBSTRING(WRK_DATE, 5, 2)
    """


def curing_prdt_monthly(
    mcode_list: Optional[List[str]] = None,
    yyyy: Optional[int] = None,
    mm: Optional[int] = None,
) -> str:
    """
    월별 생산 현황을 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    mcode_list : Optional[List[str]], optional
        조회할 제품 코드 리스트. 기본값은 None
    yyyy : Optional[int], optional
        조회할 연도. 기본값은 None
    mm : Optional[int], optional
        조회할 월. 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
    WITH 
        MAS AS ({CTE_MES_MASTER_ALL}),
        PRDT AS ({CTE_MES_PRODUCTION_MONTHLY})
    SELECT
        MAS.PLANT,
        MAS.M_CODE,
        MAS.SPEC_CD,
        MAS.STXC,
        PRDT.YYYY,
        PRDT.MM,
        PRDT.PRDT_QTY     
    FROM MAS
    LEFT JOIN PRDT
        ON MAS.SPEC_CD = PRDT.SPEC_CD 
        AND MAS.PLANT = PRDT.PLANT
    WHERE 1=1
        {f'AND MAS.M_CODE IN ({",".join(f"\'{m}\'" for m in mcode_list)})' if mcode_list else ""}
        {f'AND PRDT.YYYY = {yyyy}' if yyyy else ""}
        {f'AND PRDT.MM = {mm}' if mm else ""}
    """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 생산 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(curing_prdt_monthly, yyyy=2024)


if __name__ == "__main__":
    main()
