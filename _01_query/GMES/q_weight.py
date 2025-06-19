"""
GMES 중량 테스트 쿼리 관리 모듈

- GMES 중량 테스트 데이터 조회를 위한 SQL 쿼리 템플릿과 유틸리티를 제공합니다.
- 중량 테스트 데이터의 합격률을 계산하는 메인 쿼리를 생성합니다.
- 데이터 소스: HKT_DW.MES.MAS_D_LMASTR101, HKT_DW.MES.QLT_F_LQLTTR127

작성자: [Your Name]
"""

import sys
import os
import logging
from typing import Optional, List, Union
from pathlib import Path
import pandas as pd

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from _00_database.db_client import get_client

# --- SQL 쿼리 템플릿 정의 ---
CTE_MES_MASTER_HX = """--sql
    SELECT DISTINCT
        PLT_CD PLANT,
        PRD_CD M_CODE,
        SPEC_CD SPEC_CD_HX,
        STXC
    FROM HKT_DW.MES.MAS_D_LMASTR101
    WHERE 1=1
        AND STXC IN ('S', 'M', 'T')
        AND SPEC_FG = 'HX'
"""

CTE_MES_GT_WT = """--sql
    SELECT
        PLT_CD PLANT,
        SPEC_CD,
        INS_DATE,
        STD_WGT,
        MRM_WGT,
        CASE
            WHEN MRM_WGT <= UPM_STD_WGT AND MRM_WGT >= LWM_STD_WGT THEN 1 -- 판정
            ELSE 0 
        END AS JDG
    FROM 
        HKT_DW.MES.QLT_F_LQLTTR127
    WHERE
        1=1
        AND MRM_WGT <> 0
"""


def gt_wt_assess(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mcode_list: Optional[Union[str, List[str]]] = None,
) -> str:
    """
    중량 테스트 데이터의 합격률을 계산하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    start_date : Optional[str], optional
        조회 시작일 (YYYY-MM-DD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일 (YYYY-MM-DD 형식). 기본값은 None
    mcode_list : Optional[Union[str, List[str]]], optional
        조회할 제품 코드 목록. 기본값은 None

    Returns
    -------
    str
        CTE를 포함한 SQL 쿼리 문자열을 반환합니다.
    """
    try:
        query = f"""--sql
        WITH
            MAS AS({CTE_MES_MASTER_HX}),
            WT AS ({CTE_MES_GT_WT})
        SELECT
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD_HX,
            MAS.STXC,
            COUNT(WT.JDG) WT_INS_QTY,
            SUM(WT.JDG) WT_PASS_QTY
        FROM MAS
        LEFT JOIN WT
            ON MAS.SPEC_CD_HX = WT.SPEC_CD 
                AND MAS.PLANT = WT.PLANT
        WHERE 
            1=1
            {f"AND WT.INS_DATE BETWEEN '{start_date}' AND '{end_date}'" if start_date else ""}
            {f"AND MAS.M_CODE = '{mcode_list}'" if mcode_list else ""}
        GROUP BY
            MAS.PLANT,
            MAS.M_CODE,
            MAS.SPEC_CD_HX,
            MAS.STXC
        """
        return query

    except Exception as e:
        logger.error(f"쿼리 생성 중 오류 발생: {str(e)}")
        raise


def gt_wt_gruopby_ym(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    중량 테스트 개별 데이터를 조회하는 SQL 쿼리를 생성합니다.

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
        MAS AS ({CTE_MES_MASTER_HX}),
        WT AS ({CTE_MES_GT_WT})
    SELECT
        MAS.PLANT,
        MAS.M_CODE,
        MAS.SPEC_CD_HX,
        TO_CHAR(TO_DATE(SUBSTRING(WT.INS_DATE, 0, 8), 'YYYYMMDD'), 'YYYYMM') AS INS_DATE_YM,
        COUNT(WT.JDG) AS WT_INS_QTY,
        SUM(WT.JDG) AS WT_PASS_QTY
    FROM MAS
    LEFT JOIN WT
        ON MAS.SPEC_CD_HX = WT.SPEC_CD 
            AND MAS.PLANT = WT.PLANT
    WHERE 
        1=1
        {f"AND WT.INS_DATE >= '{start_date}'" if start_date else ""}
        {f"AND WT.INS_DATE <= '{end_date}'" if end_date else ""}
        {f"AND MAS.M_CODE = '{mcode}'" if mcode else ""}
    GROUP BY
        MAS.PLANT,
        MAS.M_CODE,
        MAS.SPEC_CD_HX,
        TO_CHAR(TO_DATE(SUBSTRING(WT.INS_DATE, 0, 8), 'YYYYMMDD'), 'YYYYMM')
    ORDER BY
        INS_DATE_YM
    """
    return query


def gt_wt_individual(
    mcode: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    중량 테스트 개별 데이터를 조회하는 SQL 쿼리를 생성합니다.

    Parameters
    ----------
    mcode : Optional[str], optional
        조회할 제품 코드. 기본값은 None
    start_date : Optional[str], optional
        조회 시작일자 (YYYYMMDD 형식). 기본값은 None
    end_date : Optional[str], optional
        조회 종료일자 (YYYYMMDD 형식). 기본값은 None
    """
    query = f"""--sql
    WITH 
        MAS AS ({CTE_MES_MASTER_HX}),
        WT AS ({CTE_MES_GT_WT})
    SELECT
        MAS.PLANT,
        MAS.M_CODE,
        MAS.SPEC_CD_HX,
        WT.INS_DATE,
        WT.STD_WGT,
        WT.MRM_WGT,
        WT.JDG
    FROM MAS
    LEFT JOIN WT
        ON MAS.SPEC_CD_HX = WT.SPEC_CD 
            AND MAS.PLANT = WT.PLANT
    WHERE 
        1=1
        {f"AND WT.INS_DATE >= '{start_date}'" if start_date else ""}
        {f"AND WT.INS_DATE <= '{end_date}'" if end_date else ""}
        {f"AND MAS.M_CODE = '{mcode}'" if mcode else ""}
    """
    return query


def main() -> pd.DataFrame:
    """
    중량 테스트 데이터의 합격률을 계산하는 메인 함수입니다.

    Returns
    -------
    pd.DataFrame
        중량 테스트 데이터와 합격률이 포함된 데이터프레임을 반환합니다.
    """
    try:
        df = get_client("snowflake").execute(gt_wt_assess())
        df["WT_PASS"] = df["WT_PASS_QTY"] / df["WT_INS_QTY"]
        return df

    except Exception as e:
        logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    main()
