"""
SQLite 조작 및 동적 모듈 로딩 유틸

이 모듈은 SQLite 기반의 DML/DDL 조작을 위한 클래스를 제공하며,
개발 모드에서 유용한 동적 모듈 임포트 함수도 포함합니다.

포함된 클래스/함수:
- SQLiteDML: SELECT, INSERT, DELETE 등 데이터 조작 기능
- SQLiteDDL: 테이블 생성 및 삭제 등 스키마 정의 기능
- dynamic_import_modules: 모듈을 런타임 중 재로딩/불러오기

사용처 예시:
- 로그인 DB 관리
- 자동화된 테이블 생성
- 개발 중 모듈 실시간 반영
"""

import sqlite3
import importlib
import sys
from pathlib import Path
import pandas as pd

from _05_commons import config


def dynamic_import_modules(
    module_paths: list[str], dev_mode: bool = config.DEV_MODE
) -> dict[str, object]:
    """
    여러 모듈을 한 번에 동적으로 불러옵니다.
    :param module_paths: 불러올 모듈 경로 리스트
    :param dev_mode: 개발 모드일 경우 reload 적용 여부
    :return: {모듈 경로: 모듈 객체} 딕셔너리
    """
    modules = {}
    for path in module_paths:
        if path in sys.modules:
            mod = sys.modules[path]
            if dev_mode:
                mod = importlib.reload(mod)
        else:
            mod = importlib.import_module(path)
        modules[path] = mod
    return modules


def format_number(num):
    """
    숫자를 입력받아, 백만 단위는 'M', 천 단위는 'K'로 포맷팅하여 반환
    """
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return f"{num:.0f}"


class SQLiteDML:
    """
    SQLite 데이터 조작용 클래스 (INSERT, SELECT, DELETE 등)
    """

    DB_PATH = Path("../database/goeq_database.db")

    def __init__(self):
        self.db_path = self.DB_PATH

    def execute_query(self, query: str, params: tuple = ()) -> None:
        """INSERT, UPDATE, DELETE용 쿼리 실행"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_query(self, query: str, params: tuple = ()) -> list[tuple]:
        """SELECT 쿼리 실행 및 결과 반환"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def insert_data(self, table: str, columns: list[str], values: tuple) -> None:
        """단일 행 데이터 삽입"""
        placeholders = ", ".join(["?"] * len(values))
        column_names = ", ".join(columns)
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        self.execute_query(query, values)

    def select_data(
        self,
        table: str,
        columns: list[str] = None,
        condition: str = "",
        params: tuple = (),
    ) -> list[tuple]:
        """조건부 SELECT 쿼리 실행"""
        column_names = ", ".join(columns) if columns else "*"
        query = f"SELECT {column_names} FROM {table} {condition}"
        return self.fetch_query(query, params)

    def delete_data(self, table: str, condition: str, params: tuple) -> None:
        """조건부 DELETE 쿼리 실행"""
        query = f"DELETE FROM {table} {condition}"
        self.execute_query(query, params)

    def list_tables(self) -> list[str]:
        """데이터베이스 내 모든 테이블 이름 반환"""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        tables = self.fetch_query(query)
        return [table[0] for table in tables]


class SQLiteDDL:
    """
    SQLite DDL 작업 클래스 (CREATE, DROP 등)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_query(self, query: str) -> None:
        """DDL 쿼리 실행"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query)
            conn.commit()

    def create_table(self, table: str, columns: list[tuple[str, str]]) -> None:
        """
        CREATE TABLE 구문 실행
        :param table: 테이블 이름
        :param columns: (컬럼명, 데이터타입) 튜플 리스트
        """
        column_defs = ", ".join(f"{name} {dtype}" for name, dtype in columns)
        query = f"CREATE TABLE IF NOT EXISTS {table} ({column_defs})"
        self.execute_query(query)

    def drop_table(self, table: str) -> None:
        """
        테이블 삭제
        :param table: 삭제할 테이블 이름
        """
        query = f"DROP TABLE IF EXISTS {table}"
        self.execute_query(query)
