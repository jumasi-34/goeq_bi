"""
CTMS 측정 데이터 쿼리 관리 모듈

- CTMS 측정 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 측정 데이터의 원본 쿼리를 생성하고, 측정 목적과 항목을 필터링합니다.
- 데이터 소스: HKT_DW.BI_DWUSER.CTMS_RESULT_DATA

작성자: [Your Name]
"""

from _00_database.db_client import get_client
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 측정 목적 상수 정의
CTMS_PURPOSE = (
    "P_Lot",
    "P_Initial Sample",
    "P_OE Special Control",
    "P_Special Control",
)

# 측정 항목 상수 정의
CTMS_MRM_ITEM = (
    "BS.12",
    "ILG",
    "NBD",
    "FCD",
    "RCG",
    "CRCC",
    "CRCB",
    "UTG.G0",
    "UTG.G1",
    "UTG.Sho",
    "1BHAW",
    "2BHAW",
    "1TUAH",
    "BFH",
    "I/P",
    "TShG.C+y",
)


def get_ctl_raw_query(
    start_date: str = "20240101", end_date: str = "20241231", mcode: str = None
) -> str:
    """CTMS 측정 데이터의 기본 쿼리를 생성합니다.

    Args:
        start_date (str, optional): 시작일자. Defaults to '20240101'.
        end_date (str, optional): 종료일자. Defaults to '20241231'.
        mcode (str, optional): 제품코드. Defaults to None.

    Returns:
        str: CTMS 측정 데이터 조회를 위한 기본 SQL 쿼리
    """
    mcode_filter = f"AND SUBSTR(MFG_CD, 5, 7) = '{mcode}'" if mcode else ""

    return f"""--sql
    SELECT
        MRM_RPT_NO DOC_NO,                                -- 레포트넘버
        PLT_CD PLANT,                                     -- 공장
        TO_DATE(MRM_DATE, 'YYYYMMDD') MRM_DATE,           -- 생산일
        MRM_OBJ_FG MRM_PURPOSE,                           -- 측정 목적
        CTL_ITEM_NM MRM_ITEM,                             -- 측정 항목
        STXC,                                             -- 시방 구분
        SUBSTR(MFG_CD, 5, 7) M_CODE,                      -- 제품 코드
        SPEC_SIZE,                                        -- SIZE
        SPEC_PTRN,                                        -- 패턴
        'UPPER' SIDE,                                     -- 상한
        U_SPEC_VAL SPEC,                                  -- 스펙
        TOL_VAL TOL,                                      -- 허용치
        CASE                                              -- 하한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
            ELSE REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') - REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
        END AS LL,
        CASE                                              -- 상한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN NULL
            ELSE REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') + REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
        END AS UL,
        U_MRM_AVG ACTUAL,                                 -- 측정값
        U_MRM_RST JDG,                                    -- 판정결과
        TO_DATE(PRDT_DATE, 'YYYYMMDD') PRDT_DATE          -- 생산일
    FROM
        HKT_DW.BI_DWUSER.CTMS_RESULT_DATA CTL
    WHERE
        1=1
        AND MRM_DATE BETWEEN '{start_date}' AND '{end_date}' -- 원하는 연월 범위 지정
        AND STXC IN ('S', 'M', 'V')
        AND MRM_PURPOSE IN {CTMS_PURPOSE}
        AND MRM_ITEM IN {CTMS_MRM_ITEM}
        {mcode_filter}
    UNION ALL            
    SELECT
        MRM_RPT_NO DOC_NO,                                -- 레포트넘버
        PLT_CD PLANT,                                     -- 공장
        TO_DATE(MRM_DATE, 'YYYYMMDD') MRM_DATE,           -- 생산일
        MRM_OBJ_FG MRM_PURPOSE,                           -- 측정 목적
        CTL_ITEM_NM MRM_ITEM,                             -- 측정 항목
        STXC,                                             -- 시방 구분
        SUBSTR(MFG_CD, 5, 7) M_CODE,                      -- 제품 코드
        SPEC_SIZE,                                        -- SIZE
        SPEC_PTRN,                                        -- 패턴
        'LOWER' SIDE,                                     -- 하한
        L_SPEC_VAL SPEC,                                  -- 스펙
        TOL_VAL TOL,                                      -- 허용치
        CASE                                              -- 하한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
            ELSE REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') - REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
        END AS LL, 
        CASE                                              -- 상한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN NULL
            ELSE REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') + REGEXP_SUBSTR(TOL_VAL, '[0-9.]+')
        END AS UL,
        L_MRM_AVG ACTUAL,                                 -- 측정값
        L_MRM_RST JDG,                                    -- 판정결과
        TO_DATE(PRDT_DATE, 'YYYYMMDD') PRDT_DATE          -- 생산일
    FROM
        HKT_DW.BI_DWUSER.CTMS_RESULT_DATA
    WHERE
        1=1
        AND MRM_DATE BETWEEN '{start_date}' AND '{end_date}' -- 원하는 연월 범위 지정
        AND STXC IN ('S', 'M')
        AND MRM_PURPOSE IN {CTMS_PURPOSE}
        AND MRM_ITEM IN {CTMS_MRM_ITEM}
        {mcode_filter}
    """


def get_ctl_raw_individual_query(
    start_date: str | None = None,
    end_date: str | None = None,
    mcode: str | None = None,
) -> str:
    """CTMS 측정 데이터의 기본 쿼리를 생성합니다.

    Args:
        start_date (str | None, optional): 시작일자. Defaults to None.
        end_date (str | None, optional): 종료일자. Defaults to None.
        mcode (str | None, optional): 제품코드. Defaults to None.

    Returns:
        str: CTMS 측정 데이터 조회를 위한 기본 SQL 쿼리
    """
    # 날짜 필터 조건 생성
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND MRM_DATE BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        date_filter = f"AND MRM_DATE >= '{start_date}'"
    elif end_date:
        date_filter = f"AND MRM_DATE <= '{end_date}'"

    # 제품코드 필터 조건 생성
    mcode_filter = f"AND SUBSTR(MFG_CD, 5, 7) = '{mcode}'" if mcode else ""

    return f"""--sql
    SELECT
        MRM_RPT_NO DOC_NO,                                -- 레포트넘버
        PLT_CD PLANT,                                     -- 공장
        TO_DATE(MRM_DATE, 'YYYYMMDD') MRM_DATE,           -- 생산일
        MRM_OBJ_FG MRM_PURPOSE,                           -- 측정 목적
        CTL_ITEM_NM MRM_ITEM,                             -- 측정 항목
        STXC,                                             -- 시방 구분
        SUBSTR(MFG_CD, 5, 7) M_CODE,                      -- 제품 코드
        SPEC_SIZE,                                        -- SIZE
        SPEC_PTRN,                                        -- 패턴
        'UPPER' SIDE,                                     -- 상한
        U_SPEC_VAL SPEC,                                  -- 스펙
        TOL_VAL TOL,                                      -- 허용치
        CASE                                              -- 하한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN 
                CASE 
                    WHEN REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL 
                    THEN TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
            ELSE 
                CASE 
                    WHEN REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') IS NOT NULL 
                         AND REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL
                    THEN TRY_CAST(REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') AS FLOAT) - 
                         TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
        END AS LL,
        CASE                                              -- 상한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN NULL
            ELSE 
                CASE 
                    WHEN REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') IS NOT NULL 
                         AND REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL
                    THEN TRY_CAST(REGEXP_SUBSTR(U_SPEC_VAL, '[0-9.]+') AS FLOAT) + 
                         TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
        END AS UL,
        U_MRM_AVG ACTUAL,                                 -- 측정값
        U_MRM_RST JDG,                                    -- 판정결과
        TO_DATE(PRDT_DATE, 'YYYYMMDD') PRDT_DATE          -- 생산일
    FROM
        HKT_DW.BI_DWUSER.CTMS_RESULT_DATA CTL
    WHERE
        1=1
        {date_filter}                                     -- 날짜 범위 조건
        AND STXC IN ('S', 'M', 'V')
        AND MRM_PURPOSE IN {CTMS_PURPOSE}
        AND MRM_ITEM IN {CTMS_MRM_ITEM}
        {mcode_filter}
    UNION ALL            
    SELECT
        MRM_RPT_NO DOC_NO,                                -- 레포트넘버
        PLT_CD PLANT,                                     -- 공장
        TO_DATE(MRM_DATE, 'YYYYMMDD') MRM_DATE,           -- 생산일
        MRM_OBJ_FG MRM_PURPOSE,                           -- 측정 목적
        CTL_ITEM_NM MRM_ITEM,                             -- 측정 항목
        STXC,                                             -- 시방 구분
        SUBSTR(MFG_CD, 5, 7) M_CODE,                      -- 제품 코드
        SPEC_SIZE,                                        -- SIZE
        SPEC_PTRN,                                        -- 패턴
        'LOWER' SIDE,                                     -- 하한
        L_SPEC_VAL SPEC,                                  -- 스펙
        TOL_VAL TOL,                                      -- 허용치
        CASE                                              -- 하한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN 
                CASE 
                    WHEN REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL 
                    THEN TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
            ELSE 
                CASE 
                    WHEN REGEXP_SUBSTR(L_SPEC_VAL, '[0-9.]+') IS NOT NULL 
                         AND REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL
                    THEN TRY_CAST(REGEXP_SUBSTR(L_SPEC_VAL, '[0-9.]+') AS FLOAT) - 
                         TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
        END AS LL, 
        CASE                                              -- 상한          
            WHEN LOWER(TOL_VAL) LIKE '%min%' THEN NULL
            ELSE 
                CASE 
                    WHEN REGEXP_SUBSTR(L_SPEC_VAL, '[0-9.]+') IS NOT NULL 
                         AND REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') IS NOT NULL
                    THEN TRY_CAST(REGEXP_SUBSTR(L_SPEC_VAL, '[0-9.]+') AS FLOAT) + 
                         TRY_CAST(REGEXP_SUBSTR(TOL_VAL, '[0-9.]+') AS FLOAT)
                    ELSE NULL 
                END
        END AS UL,
        L_MRM_AVG ACTUAL,                                 -- 측정값
        L_MRM_RST JDG,                                    -- 판정결과
        TO_DATE(PRDT_DATE, 'YYYYMMDD') PRDT_DATE          -- 생산일
    FROM
        HKT_DW.BI_DWUSER.CTMS_RESULT_DATA CTL2
    WHERE
        1=1
        {date_filter}                                     -- 날짜 범위 조건
        AND STXC IN ('S', 'M')
        AND MRM_PURPOSE IN {CTMS_PURPOSE}
        AND MRM_ITEM IN {CTMS_MRM_ITEM}
        {mcode_filter}
    """


def main():
    """CTMS 측정 데이터를 조회하고 처리합니다.

    Returns:
        pandas.DataFrame: 처리된 CTMS 측정 데이터
    """
    try:
        df = get_client("snowflake").execute(get_ctl_raw_query(mcode="1024247"))

        if df.empty:
            logger.warning("조회된 데이터가 없습니다.")
            return df

        # LSL 판정 로직
        bool_LSL = (df["TOL"].str.upper().str.contains("MIN")) & (df["TOL"].notna())
        df.loc[bool_LSL, "LIMIT"] = "LSL"
        df.loc[~bool_LSL, "LIMIT"] = "NS"

        return df

    except Exception as e:
        logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
        raise
