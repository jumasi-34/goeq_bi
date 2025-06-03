"""
HOPE OE 애플리케이션 쿼리 관리 모듈

- HOPE OE 애플리케이션 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- OE 애플리케이션 정보와 전기차 제품 코드 목록을 조회하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.BI_DWUSER.SAP_ZSTT70041

작성자: [Your Name]
"""

import sys
from typing import Optional

sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _01_query.helper_sql import test_query_by_itself

# --- SQL 쿼리 템플릿 정의 ---
CTE_HOPE_OE_APP_ALL = """--sql
    SELECT 
        MATNR AS M_CODE,
        ZGUBUN AS "Status",
        ZCARMAKER1 AS "Car Maker",
        ZCARMAKER2 AS "Sales Brand",
        ZVEHICLE1 AS "Vehicle Model(Global)",
        ZVEHICLE2 AS "Vehicle Model(Local)",
        ZPROJECT AS "Project",
        NVL(NULLIF(ZELECTRIC,' '),'ICE') AS "EV",
        ZSIZE AS "Size",
        ZLOAD_INDEX AS "LI/SS", 
        ZPLY AS "PR", 
        ZTYPE AS "Pattern", 
        ZL AS "Load",
        ZW AS "B", 
        ZUSE AS "USE", 
        ZBR AS "Brand",
        ZPRODUCT AS "Prod Name", 
        LBTXT AS "PLANT", 
        ZOEPLANT AS "OE PLANT", 
        ZSOP AS "SOP", 
        ZEOP AS "EOP"
    FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041
"""

CTE_HOPE_OE_APP_UNIQUE = """--sql
    SELECT DISTINCT
        LBTXT AS PLANT,  -- 공장지 코드
        MATNR AS M_CODE, -- 제품 코드
        ZCARMAKER1,
        LISTAGG(ZCARMAKER1 || '(' || ZPROJECT || ')', ', ' ) 
            WITHIN GROUP(ORDER BY LBTXT) AS PROJECT -- PROJECT 정보
    FROM (
        SELECT DISTINCT 
            LBTXT, 
            MATNR, 
            ZCARMAKER1, 
            ZPROJECT 
        FROM HKT_DW.BI_DWUSER.SAP_ZSTT70041
    )
    GROUP BY 
        LBTXT, 
        MATNR, 
        ZCARMAKER1
"""


def oe_app(m_code: Optional[str] = None) -> str:
    """
    OE 애플리케이션 정보를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    m_code : Optional[str], optional
        조회할 제품 코드. 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
        WITH OEAPP AS ({CTE_HOPE_OE_APP_ALL})
        SELECT * 
        FROM OEAPP
        {f"WHERE M_CODE = '{m_code}'" if m_code else ""}
    """
    return query


def ev_mcode_lst() -> str:
    """
    전기차 제품 코드 목록을 조회하는 SQL 쿼리를 생성합니다.

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
        WITH OEAPP AS ({CTE_HOPE_OE_APP_ALL})
        SELECT DISTINCT 
            M_CODE 
        FROM OEAPP 
        WHERE EV IN ('EV', 'FCEV')
    """
    return query


def main() -> None:
    """
    모듈의 주요 기능을 테스트하는 메인 함수입니다.
    """
    try:
        # 1. 기본 OE 애플리케이션 쿼리 생성 테스트
        print("1. 기본 OE 애플리케이션 쿼리 생성 테스트")
        oe_query = oe_app()
        print(f"생성된 OE 쿼리:\n{oe_query[:200]}...")

        # 2. 특정 제품 코드에 대한 쿼리 생성 테스트
        print("\n2. 특정 제품 코드에 대한 쿼리 생성 테스트")
        mcode_query = oe_app(m_code="TEST001")
        print(f"생성된 제품 코드 쿼리:\n{mcode_query[:200]}...")

        # 3. 전기차 제품 코드 목록 쿼리 생성 테스트
        print("\n3. 전기차 제품 코드 목록 쿼리 생성 테스트")
        ev_query = ev_mcode_lst()
        print(f"생성된 전기차 쿼리:\n{ev_query[:200]}...")

    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    main()
