from typing import Optional
import pandas as pd

# SQL 쿼리 템플릿 정의
CTE_MES_MASTER = f"""--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD,
        SPEC_FG,
        STXC
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND SPEC_FG = 'KT'
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

CTE_UF_DATA_MONTHLY = """--sql
    SELECT
        UF.PLT_CD PLANT,
        UF.SPEC_CD,
        SUBSTR(UF.INS_DATE, 1, 6) AS YYYYMM,
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
        AND UF.INS_DATE >= '{start_date}'
        AND UF.INS_DATE <= '{end_date}'
    GROUP BY
        UF.PLT_CD,
        UF.SPEC_CD,
        SUBSTR(UF.INS_DATE, 1, 6)
"""

CTE_MES_UF_SPECIFICATION = """(
    SELECT
        PLT_CD PLANT,
        SPEC_CD,
        CASE 
            WHEN PLT_CD IN ('JP', 'HP', 'CP') THEN RFV_3GR 
            ELSE RFV_4GR 
        END AS RFV_STD,
        CASE 
            WHEN PLT_CD IN ('JP', 'HP', 'CP') THEN LFV_3GR 
            ELSE LFV_4GR 
        END AS LFV_STD,
        CASE 
            WHEN PLT_CD IN ('JP', 'HP', 'CP') THEN CON_3GR-CON_N3GR
            ELSE CON_4GR - CON_N4GR
        END AS CON_STD,
        CASE 
            WHEN PLT_CD IN ('JP', 'HP', 'CP') THEN RFV_1TH_HRM_3GR 
            ELSE RFV_1TH_HRM_4GR 
        END AS HAR_STD
    FROM HKT_DW.MES.QLT_D_LCOMTR201
)"""

CTE_MES_UF_INDIVIDUAL = """--sql
    SELECT
        PLT_CD PLANT,                          -- '사업장_코드'
        SPEC_CD,                               -- '규격_코드'
        TO_DATE(INS_DATE, 'YYYYMMDD') INS_DATE,  -- 날짜 형식 변환
        RFV,
        LFV,
        CON,
        RFV_1TH_HRM HAR,
        JDG_GR
    FROM
        HKT_DW.MES.QLT_F_LQLTTR105
    WHERE
        1=1
        AND STXC IN ('S', 'M', 'T')    -- 'KT_스펙_번호'
        AND INS_FG = '1' -- 초검만 | '검사_구분'(0:선행, 1:초검) - HKT_DW.MES.MST_D_LCOMTR107(Q380참조)
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


def uf_product_assess_monthly(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mcode: Optional[str] = None,
) -> pd.DataFrame:
    """제품별 균일성(UF) 평가 데이터를 조회합니다."""
    query = f"""--sql
        WITH 
            MAS AS ({CTE_MES_MASTER.format(mcode=mcode)}),
            UF AS ({CTE_UF_DATA_MONTHLY.format(start_date=start_date, end_date=end_date)})
        SELECT
            MAS.M_CODE,
            UF.YYYYMM,
            UF.PLANT,
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


def uf_standard(mcode: Optional[str] = None):
    query = f"""--sql
        WITH  
            MAS AS ({CTE_MES_MASTER}),
            UF_STD AS ({CTE_MES_UF_SPECIFICATION})
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD,
            UF_STD.RFV_STD,
            UF_STD.LFV_STD,
            UF_STD.CON_STD,
            UF_STD.HAR_STD
        FROM MAS
        LEFT JOIN UF_STD
            ON MAS.SPEC_CD = UF_STD.SPEC_CD 
                AND MAS.PLANT = UF_STD.PLANT
        WHERE 1=1
            {f"AND MAS.M_CODE = '{mcode}'" if mcode else ""}
        AND MAS.SPEC_FG = 'KT'
    """
    return query


def uf_individual(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    개별 UF 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    mcode : Optional[str], optional
        조회할 제품 코드. 기본값은 None
    start_date : Optional[str], optional
        조회 시작일자 (YYYYMMDD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일자 (YYYYMMDD 형식). 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    query = f"""--sql
    WITH 
        MAS AS ({CTE_MES_MASTER.format(mcode=mcode)}),
        UF AS ({CTE_MES_UF_INDIVIDUAL})
    SELECT
        MAS.PLANT,
        MAS.M_CODE,
        MAS.SPEC_CD,
        MAS.STXC,
        UF.INS_DATE,
        UF.RFV, 
        UF.LFV,
        UF.CON,
        UF.HAR,
        UF.JDG_GR
    FROM MAS
    LEFT JOIN UF
        ON MAS.SPEC_CD = UF.SPEC_CD 
            AND MAS.PLANT = UF.PLANT
    WHERE 1=1
        {f"AND MAS.M_CODE = '{mcode}'" if mcode else ""}
        {f"AND UF.INS_DATE BETWEEN TO_DATE('{start_date}', 'YYYYMMDD') AND TO_DATE('{end_date}', 'YYYYMMDD')" if start_date and end_date else ""}
    """
    return query
