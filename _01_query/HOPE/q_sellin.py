"""
CQMS customer audit 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself
from _01_query.HOPE.q_hope import CTE_HOPE_OE_APP_UNIQUE, CTE_HOPE_OE_APP_ALL

CTE_HOPE_SELL_IN = """
    SELECT
        MATERIAL M_CODE,
        SUBSTRING(BILMON, 1, 4) AS "YYYY",
        SUBSTRING(BILMON, 5, 2) AS "MM",
        SUM(quantity) SUPP_QTY,
        ZOERESEG "OERE",
    FROM HKT_DW.BI_DWUSER.SAP_ZSDT02068
    GROUP BY 
        M_CODE,
        ZOERESEG,
        SUBSTRING(BILMON, 1, 4),
        SUBSTRING(BILMON, 5, 2)
"""

# ! 사용후 삭제
CTE_HOPE_SELL_All = """
    SELECT *
    FROM HKT_DW.BI_DWUSER.SAP_ZSDT02068
    WHERE SUBSTRING(BILMON, 1, 4) = 2024
"""


def sellin_3_years(year):
    query = f"""--sql
    WITH
        SELLIN AS({CTE_HOPE_SELL_IN}),
        OEAPP AS({CTE_HOPE_OE_APP_UNIQUE})
    SELECT 
        OEAPP.PLANT,
        SELLIN.YYYY,
        SELLIN.MM,
        SUM(SELLIN.SUPP_QTY) SUPP_QTY,
    FROM SELLIN
    LEFT JOIN OEAPP ON SELLIN.M_CODE = OEAPP.M_CODE
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


def ev_sellin(year):
    query = f"""--sql
        WITH
            SELLIN AS ({CTE_HOPE_SELL_IN}),
            OEAPP AS({CTE_HOPE_OE_APP_ALL})
        SELECT
            M_CODE,
            CASE
                WHEN M_CODE IN (SELECT DISTINCT M_CODE FROM OEAPP WHERE EV IN ('EV', 'FCEV')) THEN 'Y'
                ELSE 'N'
            END EV,
            SUPP_QTY
        FROM SELLIN
        WHERE 1=1
            AND YYYY = {year}
            AND OERE = 'OE'
        """
    return query
