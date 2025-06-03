"""
SQLite 데이터베이스 유틸리티 모듈

이 모듈은 SQLite 데이터베이스 작업을 위한 유틸리티 클래스와 함수들을 제공합니다.
주요 기능:
1. 데이터베이스 스키마 관리 (DDL)
   - 테이블 생성/삭제
   - 스키마 변경
2. 데이터 조작 (DML)
   - CRUD 작업
   - 쿼리 실행
3. 개발 지원
   - 동적 모듈 로딩
   - 숫자 포맷팅

사용 예시:
>>> dml = SQLiteDML()
>>> dml.select_data("users", ["id", "name"], "WHERE id = ?", (1,))
>>> ddl = SQLiteDDL("path/to/db.db")
>>> ddl.create_table("users", [("id", "INTEGER"), ("name", "TEXT")])
"""

import sqlite3
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from _05_commons import config


def dynamic_import_modules(
    module_paths: List[str], 
    dev_mode: bool = config.DEV_MODE
) -> Dict[str, Any]:
    """
    여러 모듈을 동적으로 불러오거나 재로딩합니다.
    
    Args:
        module_paths: 불러올 모듈 경로 리스트
        dev_mode: 개발 모드 여부 (True일 경우 모듈 재로딩)
        
    Returns:
        Dict[str, Any]: {모듈 경로: 모듈 객체} 딕셔너리
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


def format_number(num: Union[int, float]) -> str:
    """
    숫자를 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        num: 변환할 숫자
        
    Returns:
        str: 포맷팅된 문자열
        - 1,000,000 이상: '1.0M'
        - 1,000 이상: '1.0K'
        - 그 외: '123'
    """
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{num:.0f}"


class SQLiteDML:
    """SQLite 데이터 조작(DML) 작업을 위한 클래스"""
    
    DB_PATH = Path("../database/goeq_database.db")

    def __init__(self) -> None:
        self.db_path = self.DB_PATH

    def execute_query(self, query: str, params: Tuple = ()) -> None:
        """
        INSERT, UPDATE, DELETE 쿼리를 실행합니다.
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리 파라미터
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_query(self, query: str, params: Tuple = ()) -> pd.DataFrame:
        """
        SELECT 쿼리를 실행하고 결과를 DataFrame으로 반환합니다.
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            pd.DataFrame: 쿼리 결과
        """
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def insert_data(self, table: str, columns: List[str], values: Tuple) -> None:
        """
        단일 행 데이터를 삽입합니다.
        
        Args:
            table: 대상 테이블
            columns: 컬럼명 리스트
            values: 삽입할 값 튜플
        """
        placeholders = ", ".join(["?"] * len(values))
        column_names = ", ".join(columns)
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        self.execute_query(query, values)

    def select_data(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        condition: str = "",
        params: Tuple = (),
    ) -> pd.DataFrame:
        """
        조건부 SELECT 쿼리를 실행합니다.
        
        Args:
            table: 대상 테이블
            columns: 선택할 컬럼 리스트 (None일 경우 모든 컬럼)
            condition: WHERE 절 조건
            params: 쿼리 파라미터
            
        Returns:
            pd.DataFrame: 쿼리 결과
        """
        column_names = ", ".join(columns) if columns else "*"
        query = f"SELECT {column_names} FROM {table} {condition}"
        return self.fetch_query(query, params)

    def delete_data(self, table: str, condition: str, params: Tuple) -> None:
        """
        조건부 DELETE 쿼리를 실행합니다.
        
        Args:
            table: 대상 테이블
            condition: WHERE 절 조건
            params: 쿼리 파라미터
        """
        query = f"DELETE FROM {table} {condition}"
        self.execute_query(query, params)

    def list_tables(self) -> List[str]:
        """
        데이터베이스의 모든 테이블 이름을 반환합니다.
        
        Returns:
            List[str]: 테이블 이름 리스트
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        tables = self.fetch_query(query)
        return tables["name"].tolist()


class SQLiteDDL:
    """SQLite 스키마 정의(DDL) 작업을 위한 클래스"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def execute_query(self, query: str) -> None:
        """
        DDL 쿼리를 실행합니다.
        
        Args:
            query: 실행할 SQL 쿼리
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query)
            conn.commit()

    def create_table(self, table: str, columns: List[Tuple[str, str]]) -> None:
        """
        테이블을 생성합니다.
        
        Args:
            table: 생성할 테이블 이름
            columns: (컬럼명, 데이터타입) 튜플 리스트
        """
        column_defs = ", ".join(f"{name} {dtype}" for name, dtype in columns)
        query = f"CREATE TABLE IF NOT EXISTS {table} ({column_defs})"
        self.execute_query(query)

    def drop_table(self, table: str) -> None:
        """
        테이블을 삭제합니다.
        
        Args:
            table: 삭제할 테이블 이름
        """
        query = f"DROP TABLE IF EXISTS {table}"
        self.execute_query(query)
