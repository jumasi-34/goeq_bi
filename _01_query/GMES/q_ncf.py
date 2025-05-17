"""
CQMS customer audit 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

CTE_MES_MASTER = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD,
        STXC
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        -- AND STXC IN ('S', 'M', 'T')
        AND SPEC_FG = 'KT'
    """
CTE_MES_NONCOFOMITY_MONTHLY = """(
    SELECT 
        PLT_CD PLANT,                                 -- 공장
        SPEC_CD,                                      -- 규격 코드
        DFT_CD,                                      -- 규격 코드
        SUBSTRING(INS_DATE, 1, 4) YYYY,               -- YYYYY
        SUBSTRING(INS_DATE, 5, 2) MM,                 -- MM
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
    )"""


def ncf_monthly(mcode_list=None, yyyy=None, mm=None, ncf_list=None):
    query = f"""
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
        WHERE 1=1
        {f'AND MAS.M_CODE IN ({mcode_list})' if mcode_list else ""}
        {f'AND NCF.YYYY = {yyyy}' if yyyy else ""}
        {f'AND NCF.MM = {mm}' if mm else ""}
        {f'AND NCF.DFT_CD IN ({ncf_list})' if ncf_list else ""}
    """
    return query


def main():
    test_query_by_itself(ncf_monthly, yyyy=2024)


if __name__ == "__main__":
    main()
