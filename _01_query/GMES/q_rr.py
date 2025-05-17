"""
docstring
"""

import pandas as pd

CTE_MES_RR_SAMPLE = """--sql
(
    SELECT
        PLT_CD PLANT,
        SMPL_ID,
        MTL_CD M_CODE,
        TEST_FG, -- OE ( 2: OE 데이터만)
        -- , SPEC_CD
        -- , SPEC_GRP
        -- , TEST_CD
        PGS_STS
    FROM
        HKT_DW.MES.QLT_D_LQLTTR309
    WHERE
        1=1
        AND PGS_STS = 80 -- SAMPLE STATUS(80:승인 데이터만)
    )
    """
CTE_MES_RR_TEST_LIST = """--sql
(
    SELECT
        PLT_CD PLANT,
        SMPL_ID,
        ATCH_SEQ,
        WARM_LOAD,
        RSLT_RRC_CORR,
        RSLT_RRC,
        RSLT_RR,
        STD_TEST_POS,
        JDG,
        TEST_VAL,
        TEST_SEQ,
        ROW_NUMBER() OVER (PARTITION BY PLT_CD, SMPL_ID, TEST_SEQ ORDER BY ATCH_SEQ DESC) AS rn -- 마지막 첨부만 사용
    FROM
        HKT_DW.MES.QLT_F_LQLTTR316
    WHERE
        1=1
)"""
CTE_MES_RR_OE_SPEC = """--sql
(
    SELECT DISTINCT
        PLT_CD PLANT, 
        MTL_CD M_CODE, 
        CAR_MAKER_2 OEM,
        V_MODEL Veh,
        USE_TROT MASS,
        APV_RRC_MIN SPEC_MIN,
        APV_RRC_MAX SPEC_MAX,
        TEST_FG, 
        USE_TROT MASS_YN, 
        START_DATE START_DATE,
        END_DATE END_DATE,
        SPEC_CHANGE,
        APP_DATE CHG_APP_DATE,
        RR_INDEX,
        SELANT_FLG
    FROM 
        HKT_DW.MES.QLT_D_LQLTTR510    
)"""
CTE_MES_CODE_RR_TEST_METHOD = """--sql
(   -- OE RR RR CODE 변환
    SELECT CD_ITEM, CD_ITEM_NM
    FROM HKT_DW.MES.MST_D_LCOMTR107
    WHERE CD_ID = 'F570'
    )"""


def rr(
    start_date=None,
    end_date=None,
    test_fg="OE",
):

    # 1. 테스트 구분 코드 설정
    test_fg_code = 2 if test_fg == "OE" else 1

    # 2. 날짜 조건 분리
    date_filter = ""
    if start_date and end_date:
        date_filter = f"""
            AND TRY_TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') 
                BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD')
                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
        """
    # 3. 전체 코드
    query = f"""--sql
            WITH
                SPL AS {CTE_MES_RR_SAMPLE},
                LST AS {CTE_MES_RR_TEST_LIST},
                SPEC AS {CTE_MES_RR_OE_SPEC},
                CD AS {CTE_MES_CODE_RR_TEST_METHOD}
            SELECT
                SPL.PLANT,
                TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') SMPL_DATE,
                SPL.M_CODE,
                LST.WARM_LOAD,
                LST.RSLT_RRC AS RRC,
                LST.RSLT_RRC_CORR AS HK_GLOBAL,
                LST.STD_TEST_POS AS POSITION,
                DECODE(LST.JDG, 10, 'OK', 20, '재시험', 30, 'NG', 40, 'N/A') AS JDG,
                LST.TEST_VAL AS TEST_RESULT_OLD,
                CD.CD_ITEM_NM AS OE_TEST_METHOD,
                SPEC.MASS_YN,
                TRY_TO_DATE(SPEC.START_DATE, 'YYYYMMDD') START_DT,
                TRY_TO_DATE(SPEC.END_DATE, 'YYYYMMDD') END_DT
            FROM SPL
            LEFT JOIN LST ON SPL.PLANT = LST.PLANT AND SPL.SMPL_ID = LST.SMPL_ID
            LEFT JOIN SPEC ON SPL.PLANT = SPEC.PLANT AND SPL.M_CODE = SPEC.M_CODE
            LEFT JOIN CD ON SPEC.TEST_FG = CD.CD_ITEM
            WHERE
                1=1
                {date_filter}
                AND LST.rn = 1
                AND SUBSTR(SPL.SMPL_ID, 1, 2) > 20 -- 20년 이후 데이터만
                AND SPEC.TEST_FG IS NOT NULL
                AND TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD') 
                    BETWEEN TRY_TO_DATE(SPEC.START_DATE, 'YYYYMMDD') 
                    AND IFNULL(
                        TRY_TO_DATE(SPEC.END_DATE, 'YYYYMMDD'), 
                        TO_DATE(SUBSTRING(SPL.SMPL_ID, 1, 6), 'YYMMDD')
                        )
                AND SPL.TEST_FG = {test_fg_code}
            """
    return query


def rr_oe_list():
    query = f"""--sql
    WITH
    RR_OE_LIST AS ({CTE_MES_RR_OE_SPEC}),
    CD AS ({CTE_MES_CODE_RR_TEST_METHOD})
    SELECT
        RR_OE_LIST.*,
        CD.CD_ITEM
    FROM RR_OE_LIST
    LEFT JOIN CD ON RR_OE_LIST.TEST_FG = CD.CD_ITEM
    """
    return query


# corr csv
PATH = "_01_query/CSV/iso_local_to_hkGlobal.csv"
rr_corr_csv = pd.read_csv(PATH)
