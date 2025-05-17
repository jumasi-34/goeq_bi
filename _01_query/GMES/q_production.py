"""
CQMS customer audit 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

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
(
    SELECT
        PLT_CD PLANT,                      -- 공장지 코드
        SPEC_CD,                           -- SPEC 코드
        SUBSTRING(WRK_DATE, 1, 4) YYYY,    -- YYYY
        SUBSTRING(WRK_DATE, 5, 2) MM,      -- MM
        SUM(PRDT_QTY) PRDT_QTY             -- 생산량
    FROM HKT_DW.MES.WRK_F_LWRKTS118
    WHERE 1=1
        -- AND WRK_DATE LIKE '2024%'
        AND SPEC_CD LIKE 'KT%'
    GROUP BY 
        PLT_CD, 
        SPEC_CD, 
        SUBSTRING(WRK_DATE, 1, 4),
        SUBSTRING(WRK_DATE, 5, 2)
    )"""


def curing_prdt_monthly(mcode_list=None, yyyy=None, mm=None):
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
                    ON MAS.SPEC_CD = PRDT.SPEC_CD AND MAS.PLANT = PRDT.PLANT
                WHERE 1=1
                {f"AND MAS.M_CODE IN ({mcode_list})" if mcode_list else ""}
                {f"AND PRDT.YYYY = {yyyy}" if yyyy else ""}
                {f"AND PRDT.MM = {mm}" if mm else ""}
            """
    return query


def main():
    test_query_by_itself(curing_prdt_monthly, yyyy="2024")


if __name__ == "__main__":
    main()
