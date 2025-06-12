from typing import Optional
import pandas as pd

# SQL 쿼리 템플릿 정의
CTE_MES_MASTER = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND PRD_CD = '{mcode}'
"""

CTE_UF_DATA = """--sql
    SELECT
        UF.PLT_CD PLANT,
        UF.SPEC_CD,
        SUM(CASE WHEN UF.JDG_GR = 1 THEN 1 ELSE 0 END) AS JDG_1,
        SUM(CASE WHEN UF.JDG_GR = 2 THEN 1 ELSE 0 END) AS JDG_2,
        SUM(CASE WHEN UF.JDG_GR = 3 THEN 1 ELSE 0 END) AS JDG_3,
        SUM(CASE WHEN UF.JDG_GR = 4 THEN 1 ELSE 0 END) AS JDG_4,
        SUM(CASE WHEN UF.JDG_GR = 5 THEN 1 ELSE 0 END) AS JDG_5,
        SUM(CASE WHEN UF.JDG_GR = 6 THEN 1 ELSE 0 END) AS JDG_6,
        SUM(CASE WHEN UF.JDG_GR = 7 THEN 1 ELSE 0 END) AS JDG_7,
        SUM(CASE WHEN UF.JDG_GR = 8 THEN 1 ELSE 0 END) AS JDG_8
    FROM HKT_DW.MES.QLT_F_LQLTTR105 AS UF
    WHERE 1=1
        AND UF.STXC IN ('S', 'M', 'T')
        AND UF.INS_FG = '1'
        AND UF.INS_DATE BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        UF.PLT_CD,
        UF.SPEC_CD
"""


def uf_product_assess(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mcode: Optional[str] = None,
) -> pd.DataFrame:
    """제품별 균일성(UF) 평가 데이터를 조회합니다.

    Args:
        start_date (Optional[str]): 시작일자 (YYYYMMDD)
        end_date (Optional[str]): 종료일자 (YYYYMMDD)
        mcode (Optional[str]): 제품 코드

    Returns:
        pd.DataFrame: 균일성 평가 데이터
            - M_CODE: 제품 코드
            - PLANT: 공장 코드
            - SPEC_CD: 규격 코드
            - UF_INS_QTY: 검사 수량
            - UF_PASS_QTY: 합격 수량
            - PASS_RATE: 합격률
    """
    # CTE 조합하여 최종 쿼리 생성
    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER.format(mcode=mcode)}),
            UF AS ({CTE_UF_DATA.format(start_date=start_date, end_date=end_date)})
        SELECT
            MAS.M_CODE,
            UF.PLANT,
            UF.SPEC_CD,
            UF.JDG_1,
            UF.JDG_2,
            UF.JDG_3,
            UF.JDG_4,
            UF.JDG_5,
            UF.JDG_6,
            UF.JDG_7,
            UF.JDG_8
        FROM MAS
        INNER JOIN UF
            ON MAS.SPEC_CD = UF.SPEC_CD 
            AND MAS.PLANT = UF.PLANT
    """
    return query
