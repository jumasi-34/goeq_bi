"""
Oracle DB에서 데이터를 가져와 SQLite DB로 변환하는 자동화 스크립트
- HOPE SELLIN 데이터를 월별로 집계하여 SQLite DB에 저장
"""

import sys
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")

from _00_database.db_client import get_client
from _05_commons import config

# 개발 모드일 경우 config 모듈 리로드
if config.DEV_MODE:
    import importlib

    importlib.reload(config)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'logs/oracle_to_sqlite_{datetime.now().strftime("%Y%m%d")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# SQLite DB 파일 경로 설정
DB_PATH = config.SQLITE_DB_PATH

# HOPE SELLIN 데이터를 월별로 집계하는 쿼리
# - RE/OE 구분
# - 제품 코드
# - 연도/월별 수량 집계
query_hope_sellin = """--sql
    SELECT
        "RE/OE",
        "Prod." AS M_CODE,
        SUBSTR("Billing YYYYMM",1,4) AS YYYY,
        SUBSTR("Billing YYYYMM",5,6) AS MM,
        SUM("Qty.") AS SUPP_QTY
    FROM VW_SF_HOPE_SELLIN_SUMMARY
    WHERE SUBSTR("Billing YYYYMM",1,4) >= '2020'
        AND "Data Category" = 'SELLIN'
    GROUP BY
        "RE/OE",
        "Prod.",
        SUBSTR("Billing YYYYMM",1,4),
        SUBSTR("Billing YYYYMM",5,6)
"""


def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    DataFrame의 데이터 유효성을 검증합니다.

    Parameters:
        df (pd.DataFrame): 검증할 데이터프레임

    Returns:
        bool: 검증 결과
    """
    try:
        # 필수 컬럼 존재 여부 확인
        required_columns = ["RE/OE", "M_CODE", "YYYY", "MM", "SUPP_QTY"]
        if not all(col in df.columns for col in required_columns):
            logger.error(
                f"필수 컬럼 누락: {[col for col in required_columns if col not in df.columns]}"
            )
            return False

        # 데이터 타입 검증
        if not pd.api.types.is_numeric_dtype(df["SUPP_QTY"]):
            logger.error("SUPP_QTY 컬럼이 숫자형이 아닙니다.")
            return False

        # NULL 값 검증
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.warning(f"NULL 값이 존재합니다:\n{null_counts[null_counts > 0]}")

        # 음수 수량 검증
        negative_qty = df[df["SUPP_QTY"] < 0]
        if not negative_qty.empty:
            logger.warning(f"음수 수량이 {len(negative_qty)}건 존재합니다.")

        return True

    except Exception as e:
        logger.error(f"데이터 검증 중 오류 발생: {str(e)}")
        return False


def save_df_to_sqlite(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "replace",
    index: bool = False,
) -> bool:
    """
    DataFrame을 SQLite DB로 저장합니다.

    Parameters:
        df (pd.DataFrame): 저장할 데이터프레임
        table_name (str): 저장할 테이블명
        if_exists (str): 'replace', 'append', 'fail' 중 선택
        index (bool): 인덱스를 DB에 저장할지 여부

    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 데이터 검증
        if not validate_dataframe(df):
            return False

        # DB 파일 존재 여부 확인
        db_path = Path(DB_PATH)
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True)
            logger.info(f"DB 디렉토리 생성: {db_path.parent}")

        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=index)
            logger.info(f"테이블 '{table_name}' 저장 완료 (레코드 수: {len(df)})")
        return True

    except Exception as e:
        logger.error(f"SQLite 저장 중 오류 발생: {str(e)}")
        return False


def generate_sellin_monthly_agg() -> bool:
    """
    Oracle DB에서 HOPE SELLIN 데이터를 가져와 월별 집계 후 SQLite DB에 저장

    Returns:
        bool: 처리 성공 여부
    """
    try:
        logger.info("HOPE SELLIN 데이터 집계 시작")

        # Oracle DB에서 데이터 조회
        df = get_client("oracle_bi").execute(query_hope_sellin)
        logger.info(f"Oracle DB에서 {len(df)}건의 데이터 조회 완료")

        # SQLite DB에 저장
        if save_df_to_sqlite(df, "sellin_monthly_agg"):
            logger.info("HOPE SELLIN 데이터 집계 완료")
            return True
        return False

    except Exception as e:
        logger.error(f"HOPE SELLIN 데이터 집계 중 오류 발생: {str(e)}")
        return False


def main():
    try:
        if generate_sellin_monthly_agg():
            logger.info("프로그램 정상 종료")
        else:
            logger.error("프로그램 비정상 종료")
    except Exception as e:
        logger.error(f"프로그램 실행 중 예기치 않은 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
