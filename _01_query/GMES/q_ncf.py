"""
GMES 부적합(NCF) 쿼리 관리 모듈

이 모듈은 GMES(Global Manufacturing Execution System)의 부적합(Non-Conformity) 데이터를
조회하기 위한 SQL 쿼리 템플릿과 유틸리티 함수를 제공합니다.

주요 기능:
- 월별/일별 부적합 현황 조회 쿼리 생성
- 제품 코드, 기간, 부적합 코드 등 다양한 조건으로 데이터 필터링
- 부적합 수량 집계 및 분석

데이터 소스:
- HKT_DW.MES.MAS_D_LMASTR101: 제품 마스터 테이블
- HKT_DW.MES.QLT_F_LQLTTR107: 부적합 이력 테이블

작성자: [Your Name]
최종수정: 2024-03-21
"""

import sys
from typing import Optional, List, Union
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _01_query.helper_sql import test_query_by_itself

# --- SQL 쿼리 템플릿 정의 ---
# 제품 마스터 정보를 조회하는 CTE
CTE_MES_MASTER = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,     -- 공장 코드
        PRD_CD M_CODE,    -- 제품 코드
        SPEC_CD,          -- 규격 코드
        STXC              -- 상태 코드
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND SPEC_FG = 'KT'  -- KT 규격 제품만 조회
    """

# 월별 부적합 현황을 집계하는 CTE
CTE_MES_NONCOFOMITY_MONTHLY = """--sql
    SELECT 
        PLT_CD PLANT,                                 -- 공장 코드
        SPEC_CD,                                      -- 규격 코드
        DFT_CD,                                       -- 부적합 코드
        SUBSTRING(INS_DATE, 1, 4) YYYY,              -- 연도
        SUBSTRING(INS_DATE, 5, 2) MM,                -- 월
        SUM(DFT_QTY) NCF_QTY                         -- 부적합 수량 합계
    FROM 
        HKT_DW.MES.QLT_F_LQLTTR107                   -- 부적합 이력 테이블
    WHERE 
        1=1
        AND DFT_QTY <> 0                             -- 부적합 수량이 0이 아닌 경우만
        AND STXC IN ('S', 'M', 'T')                  
        AND INS_TP_CD IN ('1', '2', '3', '5', '6', '7', '9')        
    GROUP BY
        PLT_CD,
        SPEC_CD,
        DFT_CD,
        SUBSTRING(INS_DATE, 1, 4),
        SUBSTRING(INS_DATE, 5, 2)
    HAVING
        SUM(DFT_QTY) IS NOT NULL                     -- 부적합 수량이 있는 경우만
    """

# 일별 부적합 현황을 집계하는 CTE
CTE_MES_NONCOFOMITY_DAILY = """--sql
    SELECT
        PLT_CD PLANT,                                -- 공장 코드
        SPEC_CD,                                     -- 규격 코드
        DFT_CD,                                      -- 부적합 코드
        INS_DATE,                                    -- 검사 일자
        SUM(DFT_QTY) as DFT_QTY                      -- 부적합 수량 합계
    FROM HKT_DW.MES.QLT_F_LQLTTR107
    WHERE 1=1
        AND DFT_QTY <> 0                            -- 부적합 수량이 0이 아닌 경우만
        AND STXC IN ('S', 'M', 'T')                 -- 상태 코드: S(Scrap), M(Modify), T(Transfer)
        AND INS_TP_CD IN ('1', '2', '3', '5', '6', '7', '9')           
    GROUP BY
        PLT_CD,
        SPEC_CD,
        DFT_CD,
        INS_DATE
"""
CTE_MES_SHIPPING_NCF_MONTHLY = """--sql
    SELECT
        PLT_CD PLANT,
        SPEC_CD,
        DFT_CD,
        SUBSTRING(INS_DATE, 1, 4) YYYY,
        SUBSTRING(INS_DATE, 5, 2) MM,
        SUM(DFT_QTY) as DFT_QTY
    FROM HKT_DW.MES.QLT_F_LQLTTR120
    WHERE 1=1
        AND DFT_QTY <> 0
        AND DFT_OCCR_FG = 1
    GROUP BY
        PLT_CD, 
        SPEC_CD,
        DFT_CD,
        SUBSTRING(INS_DATE, 1, 4),
        SUBSTRING(INS_DATE, 5, 2)
    HAVING
        SUM(DFT_QTY) IS NOT NULL    
"""


CTE_MES_SHIPPING_NCF_DAILY = """--sql
    SELECT
        PLT_CD PLANT,
        SPEC_CD,
        DFT_CD,
        INS_DATE,
        SUM(DFT_QTY) as DFT_QTY
    FROM HKT_DW.MES.QLT_F_LQLTTR120
    WHERE 1=1
        AND DFT_QTY <> 0
        AND DFT_OCCR_FG = 1
    GROUP BY
        PLT_CD, 
        SPEC_CD,
        DFT_CD,
        INS_DATE
"""


def ncf_monthly(
    mcode_list: Optional[List[str]] = None,
    yyyy: Optional[int] = None,
    mm: Optional[int] = None,
    ncf_list: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    월별 부적합 현황을 조회하는 SQL 쿼리를 생성합니다.

    이 함수는 제품 마스터와 부적합 이력을 조인하여 월별 부적합 현황을 조회합니다.
    다양한 필터링 조건을 적용할 수 있으며, 조건이 지정되지 않은 경우 모든 데이터를 조회합니다.

    Parameters
    ----------
    mcode_list : Optional[List[str]], optional
        조회할 제품 코드 리스트. 기본값은 None
    yyyy : Optional[int], optional
        조회할 연도. 기본값은 None
    mm : Optional[int], optional
        조회할 월. 기본값은 None
    ncf_list : Optional[List[str]], optional
        조회할 부적합 코드 리스트. 기본값은 None
    start_date : Optional[str], optional
        조회 시작일 (YYYY-MM-DD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일 (YYYY-MM-DD 형식). 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.

    Examples
    --------
    >>> query = ncf_monthly(mcode_list=['ABC123'], yyyy=2024, mm=3)
    >>> print(query)
    """
    # WHERE 절 조건을 동적으로 생성
    where_conditions_ncf = []
    where_conditions_shp = []

    if mcode_list:
        mcode_str = ", ".join(f"'{m}'" for m in mcode_list)
        where_conditions_ncf.append(f"MAS.M_CODE IN ({mcode_str})")
        where_conditions_shp.append(f"MAS.M_CODE IN ({mcode_str})")

    if yyyy:
        where_conditions_ncf.append(f"NCF.YYYY = {yyyy}")
        where_conditions_shp.append(f"SHP.YYYY = {yyyy}")

    if mm:
        where_conditions_ncf.append(f"NCF.MM = {mm}")
        where_conditions_shp.append(f"SHP.MM = {mm}")

    if ncf_list:
        ncf_str = ", ".join(f"'{n}'" for n in ncf_list)
        where_conditions_ncf.append(f"NCF.DFT_CD IN ({ncf_str})")
        where_conditions_shp.append(f"SHP.DFT_CD IN ({ncf_str})")

    if start_date and end_date:
        # 월별 데이터는 YYYYMM 형식으로 변환하여 비교
        start_yyyy = start_date[:4]
        start_mm = start_date[4:6]
        end_yyyy = end_date[:4]
        end_mm = end_date[4:6]

        # 기간 범위 조회 (해당 기간 내의 모든 월 데이터)
        where_conditions_ncf.append(
            f"(NCF.YYYY > {start_yyyy} OR (NCF.YYYY = {start_yyyy} AND NCF.MM >= {start_mm}))"
        )
        where_conditions_shp.append(
            f"(SHP.YYYY > {start_yyyy} OR (SHP.YYYY = {start_yyyy} AND SHP.MM >= {start_mm}))"
        )
        where_conditions_ncf.append(
            f"(NCF.YYYY < {end_yyyy} OR (NCF.YYYY = {end_yyyy} AND NCF.MM <= {end_mm}))"
        )
        where_conditions_shp.append(
            f"(SHP.YYYY < {end_yyyy} OR (SHP.YYYY = {end_yyyy} AND SHP.MM <= {end_mm}))"
        )

    # WHERE 절 문자열 생성
    where_clause_ncf = (
        " AND ".join(where_conditions_ncf) if where_conditions_ncf else "1=1"
    )
    where_clause_shp = (
        " AND ".join(where_conditions_shp) if where_conditions_shp else "1=1"
    )

    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER}),
            NCF AS ({CTE_MES_NONCOFOMITY_MONTHLY}),
            SHP AS ({CTE_MES_SHIPPING_NCF_MONTHLY})
        SELECT
            MAS.PLANT,                               -- 공장 코드
            MAS.M_CODE,                              -- 제품 코드
            MAS.SPEC_CD,                             -- 규격 코드
            MAS.STXC,                                -- 상태 코드
            NCF.YYYY,                                -- 연도
            NCF.MM,                                  -- 월
            NCF.DFT_CD,                              -- 부적합 코드
            NCF.NCF_QTY                              -- 부적합 수량
        FROM MAS
        LEFT JOIN NCF
            ON MAS.SPEC_CD = NCF.SPEC_CD 
                AND MAS.PLANT = NCF.PLANT
        WHERE {where_clause_ncf}
        UNION ALL
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD,
            MAS.STXC,
            SHP.YYYY,
            SHP.MM,
            SHP.DFT_CD,
            SHP.DFT_QTY
        FROM MAS
        LEFT JOIN SHP
            ON MAS.SPEC_CD = SHP.SPEC_CD 
                AND MAS.PLANT = SHP.PLANT
        WHERE {where_clause_shp}
    """
    return query


def ncf_daily(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ncf_list: Optional[List[str]] = None,
) -> str:
    """
    일별 부적합 현황을 조회하는 SQL 쿼리를 생성합니다.

    이 함수는 제품 마스터와 부적합 이력을 조인하여 일별 부적합 현황을 조회합니다.
    다양한 필터링 조건을 적용할 수 있으며, 조건이 지정되지 않은 경우 모든 데이터를 조회합니다.

    Parameters
    ----------
    mcode : Optional[str], optional
        조회할 제품 코드. 기본값은 None
    start_date : Optional[str], optional
        조회 시작일자 (YYYYMMDD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일자 (YYYYMMDD 형식). 기본값은 None
    ncf_list : Optional[List[str]], optional
        조회할 부적합 코드 리스트. 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    # WHERE 절 조건을 동적으로 생성
    where_conditions_ncf = []

    if mcode:
        where_conditions_ncf.append(f"MAS.M_CODE = '{mcode}'")

    if ncf_list:
        ncf_str = ", ".join(f"'{n}'" for n in ncf_list)
        where_conditions_ncf.append(f"NCF.DFT_CD IN ({ncf_str})")

    if start_date:
        where_conditions_ncf.append(f"NCF.INS_DATE >= '{start_date}'")

    if end_date:
        where_conditions_ncf.append(f"NCF.INS_DATE <= '{end_date}'")

    where_conditions_shp = []

    if mcode:
        where_conditions_shp.append(f"MAS.M_CODE = '{mcode}'")

    if start_date:
        where_conditions_shp.append(f"SHP.INS_DATE >= '{start_date}'")

    if end_date:
        where_conditions_shp.append(f"SHP.INS_DATE <= '{end_date}'")

    # WHERE 절 문자열 생성
    where_clause_ncf = (
        " AND ".join(where_conditions_ncf) if where_conditions_ncf else "1=1"
    )
    where_clause_shp = (
        " AND ".join(where_conditions_shp) if where_conditions_shp else "1=1"
    )

    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER}),
            NCF AS ({CTE_MES_NONCOFOMITY_DAILY}),
            SHP AS ({CTE_MES_SHIPPING_NCF_DAILY})
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD,
            MAS.STXC,
            NCF.DFT_CD,
            NCF.DFT_QTY,
            NCF.INS_DATE
        FROM MAS
        LEFT JOIN NCF
            ON MAS.SPEC_CD = NCF.SPEC_CD 
                AND MAS.PLANT = NCF.PLANT
        WHERE {where_clause_ncf}
        UNION
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD,
            MAS.STXC,
            SHP.DFT_CD,
            SHP.DFT_QTY,
            SHP.INS_DATE
        FROM MAS
        LEFT JOIN SHP
            ON MAS.SPEC_CD = SHP.SPEC_CD 
                AND MAS.PLANT = SHP.PLANT
        WHERE {where_clause_shp}
    """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 부적합 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(ncf_monthly, yyyy=2024)


if __name__ == "__main__":
    main()
