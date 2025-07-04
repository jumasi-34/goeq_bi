"""
데이터베이스 클라이언트 모듈

이 모듈은 다양한 데이터베이스 시스템과의 연결 및 쿼리 실행을 위한 클라이언트 클래스들을 제공합니다.
주요 기능:
- Snowflake, Oracle(BI/MES), SQLite 등 다양한 DB 시스템 지원
- 데이터베이스 연결 및 쿼리 실행
- 쿼리 결과를 pandas DataFrame으로 변환
- Streamlit 환경에서의 캐싱 지원

사용 예시:
    from db_client import get_client

    # Snowflake 클라이언트 생성
    sf_client = get_client('snowflake')
    df = sf_client.execute_query("SELECT * FROM table")

    # Oracle BI 클라이언트 생성
    oracle_client = get_client('oracle_bi')
    df = oracle_client.execute_query("SELECT * FROM table")

클라이언트 클래스들:
    - SnowflakeClient: Snowflake 데이터베이스와 연결하여 쿼리 실행
    - OracleClientBI: Oracle BI 데이터베이스와 연결하여 쿼리 실행
    - OracleClientMES: Oracle MES 데이터베이스와 연결하여 쿼리 실행
    - SQLiteClient: SQLite 데이터베이스와 연결하여 쿼리 실행

함수:
    - get_client: 주어진 DB 종류에 맞는 클라이언트 객체를 반환합니다.
"""

import sys
import os
from dotenv import load_dotenv
from functools import wraps
import pandas as pd
import streamlit as st
import sqlite3
from sqlalchemy import create_engine, Engine
from pathlib import Path
import logging

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from _05_commons import config


def cache_resource_safe(*args, **kwargs):
    """
    Streamlit이 실행 중일 때만 @st.cache_resource를 적용합니다.
    그렇지 않으면 원본 함수를 그대로 반환합니다.
    """

    def decorator(func):
        if st.runtime.exists():
            return st.cache_resource(*args, **kwargs)(func)
        else:

            @wraps(func)
            def wrapper(*f_args, **f_kwargs):
                return func(*f_args, **f_kwargs)

            return wrapper

    return decorator


class SnowflakeClient:
    """
    Snowflake DB와 연결하여 쿼리를 실행하는 클라이언트 클래스입니다.
    """

    def __init__(self):
        self.config = {
            "user": "21300584",
            "password": "Jumasi21300584",
            "account": "ls58031.ap-northeast-2.privatelink",
            "warehouse": "SMALL_WH",
            "database": "HKT_DW",
            "schema": "KPPMES",
        }

    def _create_engine(self) -> Engine:
        """
        SQLAlchemy 엔진을 생성합니다. PrivateLink 환경에서 SSL 인증서 오류 방지를 위해
        ocsp_fail_open 옵션을 False로 설정합니다.
        """
        return create_engine(
            "snowflake://",
            connect_args={
                "user": self.config["user"],
                "password": self.config["password"],
                "account": self.config["account"],
                "warehouse": self.config["warehouse"],
                "database": self.config["database"],
                "schema": self.config["schema"],
                "ocsp_fail_open": False,
            },
        )

    def execute(self, query: str) -> pd.DataFrame:
        """
        Snowflake에 연결하여 주어진 쿼리를 실행한 결과를 DataFrame으로 반환합니다.

        Args:
            query (str): 실행할 SQL 쿼리

        Returns:
            pd.DataFrame: 쿼리 결과
        """
        engine = self._create_engine()
        try:
            return pd.read_sql(query, engine)
        finally:
            engine.dispose()


class OracleClientBI:
    """
    Oracle DB와 연결하여 쿼리를 실행하는 클라이언트 클래스입니다.(BI)
    """

    def __init__(self):
        self.user = "BI_DWUSER"
        self.password = "bidw123"
        self.host = "202.31.33.111"
        self.port = "1521"
        self.service_name = "DHKDSFT.hankooktech.com"

    def execute(self, query: str):
        oracle_uri = f"oracle+cx_oracle://{self.user}:{self.password}@{self.host}:{self.port}/?service_name={self.service_name}"
        engine = create_engine(oracle_uri)
        try:
            return pd.read_sql(query, con=engine)
        finally:
            engine.dispose()


class OracleClientMES:
    """
    Oracle DB와 연결하여 쿼리를 실행하는 클라이언트 클래스입니다.(MES)
    """

    def __init__(self):
        self.user = "HQGMES"
        self.password = "HQGMES"
        self.host = "202.31.25.83"
        self.port = "1521"
        self.service_name = "DKPPODA.kppodad"

    def execute(self, query: str):
        oracle_uri = f"oracle+cx_oracle://{self.user}:{self.password}@{self.host}:{self.port}/?service_name={self.service_name}"
        engine = create_engine(oracle_uri)
        try:
            return pd.read_sql(query, con=engine)
        finally:
            engine.dispose()


class SQLiteClient:
    """
    SQLite DB와 연결하여 쿼리를 실행하는 클라이언트 클래스입니다.
    """

    _DB_PATH = config.SQLITE_DB_PATH

    def __init__(self):
        """
        Parameters:
            db_path (str): SQLite DB 파일 경로 (기본값: goeq_database.db)
        """
        self.db_path = self._DB_PATH

    def execute(self, query: str):
        """
        SQLite에 연결하여 쿼리를 실행한 후 DataFrame으로 반환합니다.
        연결은 내부적으로 자동 열고 닫습니다.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            return pd.read_sql(query, conn)
        finally:
            conn.close()

    def insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """
        DataFrame을 SQLite 테이블에 삽입합니다.

        Args:
            df: 삽입할 DataFrame
            table_name: 대상 테이블 이름
        """
        if df is None or df.empty:
            raise ValueError("삽입할 데이터가 없습니다.")

        conn = sqlite3.connect(self.db_path)
        try:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"데이터 저장 중 오류 발생: {str(e)}")
        finally:
            conn.close()


# @cache_resource_safe(ttl=3600)
def get_client(db_type: str = "snowflake"):
    """
    주어진 DB 종류에 맞는 클라이언트 객체를 반환합니다.

    Parameters:
        db_type (str): 사용할 DB 종류 ("snowflake", "oracle_bi", "oracle_mes", "sqlite")

    Returns:
        BaseClient: 해당 DB에 연결 가능한 클라이언트 객체

    Raises:
        ValueError: 지원하지 않는 DB 타입일 경우 발생
    """
    db_type = db_type.lower()

    if db_type == "snowflake":
        return SnowflakeClient()
    elif db_type == "oracle_bi":
        return OracleClientBI()
    elif db_type == "oracle_mes":
        return OracleClientMES()
    elif db_type == "sqlite":
        return SQLiteClient()
    else:
        raise ValueError(f"지원하지 않는 DB 타입입니다: {db_type}")


def main():
    logging.warning("==== main() 함수 진입 ====")
    print("==== main() 함수 진입 ====")

    # Snowflake 테스트
    print("Testing Snowflake Client...")
    snowflake_query = """--sql
    SELECT
        PERNR PNL_NO,
        NACHN PNL_NM
    FROM HKT_DW.BI_GERPUSER.ZHRT90041
    """
    snowflake_client = get_client("snowflake")
    snowflake_df = snowflake_client.execute(snowflake_query)
    print("Snowflake query result:")
    print(snowflake_df.head())

    # Oracle_bi 테스트
    print("\nTesting Oracle(BI) Client...")
    oracle_query = """--sql
    SELECT table_name FROM user_tables
    """
    oracle_client = get_client("oracle_bi")
    oracle_df = oracle_client.execute(oracle_query)
    print("Oracle query result:")
    print(oracle_df.head())

    # Oracle_mes 테스트
    print("\nTesting Oracle(MES) Client...")
    oracle_query = """--sql
    SELECT table_name FROM user_tables
    """
    oracle_client = get_client("oracle_mes")
    oracle_df = oracle_client.execute(oracle_query)
    print("Oracle query result:")
    print(oracle_df.head())

    # SQLite 테스트
    print("\nTesting SQLite Client...")
    sqlite_query = """--sql
    SELECT * 
    FROM logins
    """
    sqlite_client = get_client("sqlite")
    sqlite_df = sqlite_client.execute(sqlite_query)
    print("SQLite query result:")
    print(sqlite_df.head())


if __name__ == "__main__":
    main()
