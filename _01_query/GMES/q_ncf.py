"""
GMES 부적합(NCF) 쿼리 관리 모듈

- GMES 부적합 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 월별 부적합 현황을 조회하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.MES.MAS_D_LMASTR101, HKT_DW.MES.QLT_F_LQLTTR107

작성자: [Your Name]
"""

import sys
from typing import Optional, List, Union

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

# --- SQL 쿼리 템플릿 정의 ---
CTE_MES_MASTER = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD,
        STXC
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND SPEC_FG = 'KT'
    """

CTE_MES_NONCOFOMITY_MONTHLY = """--sql
    SELECT 
        PLT_CD PLANT,                                 -- 공장
        SPEC_CD,                                      -- 규격 코드
        DFT_CD,                                      -- 부적합 코드
        SUBSTRING(INS_DATE, 1, 4) YYYY,               -- 연도
        SUBSTRING(INS_DATE, 5, 2) MM,                 -- 월
        SUM(DFT_QTY) NCF_QTY                          -- 부적합 수량
    FROM 
        HKT_DW.MES.QLT_F_LQLTTR107                    -- 부적합 테이블
    WHERE 
        1=1
        AND DFT_QTY <> 0                              -- 부적합 수량이 0이 아님
        AND STXC IN ('S', 'M', 'T')                   -- 상태 코드 필터링
        AND INS_TP_CD IN ('1', '2', '3')              -- 검사 유형 필터링(SCRAB)
    GROUP BY
        PLT_CD,
        SPEC_CD,
        DFT_CD,
        SUBSTRING(INS_DATE, 1, 4),
        SUBSTRING(INS_DATE, 5, 2)
    HAVING
        SUM(DFT_QTY) IS NOT NULL
    """

CTE_MES_NONCOFOMITY_DAILY = """--sql
    SELECT
        PLT_CD PLANT,
        SPEC_CD,
        DFT_CD,
        INS_DATE,
        SUM(DFT_QTY) as DFT_QTY
    FROM HKT_DW.MES.QLT_F_LQLTTR107
    WHERE 1=1
        AND DFT_QTY <> 0
        AND STXC IN ('S', 'M', 'T')
        AND INS_TP_CD IN ('1', '2', '3')
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
    """
    # WHERE 절 조건을 동적으로 생성
    where_conditions = []

    if mcode_list:
        mcode_str = ", ".join(f"'{m}'" for m in mcode_list)
        where_conditions.append(f"MAS.M_CODE IN ({mcode_str})")

    if yyyy:
        where_conditions.append(f"NCF.YYYY = {yyyy}")

    if mm:
        where_conditions.append(f"NCF.MM = {mm}")

    if ncf_list:
        ncf_str = ", ".join(f"'{n}'" for n in ncf_list)
        where_conditions.append(f"NCF.DFT_CD IN ({ncf_str})")

    if start_date:
        where_conditions.append(f"NCF.INS_DATE >= '{start_date}'")

    if end_date:
        where_conditions.append(f"NCF.INS_DATE <= '{end_date}'")

    # WHERE 절 문자열 생성
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER}),
            NCF AS ({CTE_MES_NONCOFOMITY_MONTHLY})
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD,
            MAS.STXC,
            NCF.YYYY,
            NCF.MM,
            NCF.DFT_CD,
            NCF.NCF_QTY
        FROM MAS
        LEFT JOIN NCF
            ON MAS.SPEC_CD = NCF.SPEC_CD 
                AND MAS.PLANT = NCF.PLANT
        WHERE {where_clause}
    """
    return query


def ncf_daily(
    mcode_list: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ncf_list: Optional[List[str]] = None,
) -> str:
    """
    일별 부적합 현황을 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    mcode_list : Optional[List[str]], optional
        조회할 제품 코드 리스트. 기본값은 None
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
    where_conditions = []

    if mcode_list:
        mcode_str = ", ".join(f"'{m}'" for m in mcode_list)
        where_conditions.append(f"MAS.M_CODE IN ({mcode_str})")

    if ncf_list:
        ncf_str = ", ".join(f"'{n}'" for n in ncf_list)
        where_conditions.append(f"NCF.DFT_CD IN ({ncf_str})")

    if start_date:
        where_conditions.append(f"NCF.INS_DATE >= '{start_date}'")

    if end_date:
        where_conditions.append(f"NCF.INS_DATE <= '{end_date}'")

    # WHERE 절 문자열 생성
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER}),
            NCF AS ({CTE_MES_NONCOFOMITY_DAILY})
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
        WHERE {where_clause}
    """
    return query


def main() -> None:
    """
    test_query_by_itself 유틸리티를 사용하여 부적합 쿼리를 단독 실행합니다.
    """
    test_query_by_itself(ncf_monthly, yyyy=2024)


if __name__ == "__main__":
    main()
