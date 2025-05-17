"""
CQMS customer audit 쿼리 관리
"""

import sys

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

CTE_HOPE_OE_APP_ALL = """(
    SELECT 
        MATNR M_CODE,
        ZGUBUN "Status",
        ZCARMAKER1 "Car Maker",
        ZCARMAKER2 "Sales Brand",
        ZVEHICLE1 "Vehicle Model(Global)",
        ZVEHICLE2 "Vehicle Model(Local)",
        ZPROJECT "Project",
        NVL(NULLIF(ZELECTRIC,' '),'ICE') AS "EV",
        ZSIZE "Size",
        ZLOAD_INDEX "LI/SS", 
        ZPLY "PR", 
        ZTYPE "Pattern", 
        ZL "Load",
        ZW "B", 
        ZUSE "USE", 
        ZBR "Brand",
        ZPRODUCT "Prod Name", 
        LBTXT "PLANT", 
        ZOEPLANT "OE PLANT", 
        ZSOP "SOP", 
        ZEOP "EOP"
    FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041
)
"""
CTE_HOPE_OE_APP_UNIQUE = """
    SELECT DISTINCT
        LBTXT PLANT,  -- 공장지 코드
        MATNR M_CODE, -- 제품 코드
        ZCARMAKER1,
        LISTAGG(ZCARMAKER1 || '(' || ZPROJECT || ')', ', ' ) WITHIN GROUP(ORDER BY LBTXT) AS PROJECT -- PROJECT 정보
    FROM (SELECT DISTINCT LBTXT, MATNR, ZCARMAKER1, ZPROJECT 
            FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041)
    GROUP BY LBTXT, MATNR, ZCARMAKER1
    """


def oe_app(m_code=None):
    query = f"""--sql
        SELECT * FROM {CTE_HOPE_OE_APP_ALL}
    """
    return query


def ev_mcode_lst():
    query = f"""--sql
    WITH
        OEAPP AS({CTE_HOPE_OE_APP_ALL})
    SELECT DISTINCT 
        M_CODE 
    FROM OEAPP 
    WHERE EV IN ('EV', 'FCEV')
    """
    return query
