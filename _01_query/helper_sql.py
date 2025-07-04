"""
DB 클라이언트를 사용하여 다양한 데이터베이스에서 쿼리를 실행하고 결과를 반환하는 모듈입니다.

이 모듈은 Snowflake, Oracle (BI, MES), SQLite와의 연결을 관리하고, 지정된 데이터베이스에서 SQL 쿼리를 실행한 후
결과를 pandas DataFrame 형식으로 반환합니다. 또한, SQL DECODE 구문을 생성할 수 있는 함수도 제공합니다.

주요 기능:
- 데이터베이스 연결을 위한 다양한 클라이언트 클래스 제공 (Snowflake, Oracle_BI, Oracle_MES, SQLite)
- 쿼리 실행 및 DataFrame으로 결과 반환
- 딕셔너리를 SQL DECODE 구문으로 변환하는 기능 제공

사용법:
1. `convert_dict_to_decode` 함수로 딕셔너리를 SQL DECODE 구문으로 변환
2. `test_query` 함수로 다양한 데이터베이스에서 쿼리 실행
3. 각 DB에 맞는 클라이언트를 생성하여 SQL 쿼리 실행 및 결과 반환

클라이언트 클래스:
- `SnowflakeClient`: Snowflake 데이터베이스와 연결하여 쿼리 실행
- `OracleClientBI`: Oracle BI 데이터베이스와 연결하여 쿼리 실행
- `OracleClientMES`: Oracle MES 데이터베이스와 연결하여 쿼리 실행
- `SQLiteClient`: SQLite 데이터베이스와 연결하여 쿼리 실행

참고:
- 각 DB 클라이언트 클래스는 `get_client` 함수로 동적으로 생성할 수 있습니다.
- `test_query` 함수는 실행할 쿼리와 사용할 데이터베이스 종류를 인자로 받아 결과를 출력합니다.
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

from IPython.display import display
import pandas as pd
import _00_database.db_client as db_client


# decode
def convert_dict_to_decode(dict_set):
    """
    DECODE 활용을 위해 딕셔너리 > DECODE 변환 함수
    """
    decode = ", ".join([f"'{key}', '{value}'" for key, value in dict_set.items()])
    return decode


# 주피터 노트북 전용 함수 : 쿼리를 받아서 작동여부와 대략 정보를 확인하는 함수
def test_query_from_ipynb(
    query_func, db_type: str = "snowflake", max_rows: int = 5
) -> pd.DataFrame:
    """
    지정한 DB에서 쿼리를 실행하고 결과를 DataFrame 형태로 출력 및 반환합니다.

    Parameters:
        query (str): 실행할 SQL 쿼리 문자열
        db_type (str): 사용할 DB 종류 ("snowflake", "oracle_bi", "oracle_mes", "sqlite") (기본값: "snowflake")
        max_rows (Optional[int]): 출력할 최대 행 수 (기본값: 5)

    Returns:
        pd.DataFrame: 쿼리 실행 결과
    """
    try:
        query = query_func()
        client = db_client.get_client(db_type=db_type)
        df = client.execute(query=query)

        print(f"[INFO] Query executed successfully on '{db_type}' database.")
        print(
            f"Testing [{query_func.__name__}] rows : {df.shape[0]} columns : {df.shape[1]}"
        )
        display(df.head(max_rows))
        print("-" * 40)

    except Exception as e:
        print(f"[ERROR] Failed to execute query: {e}")
        raise


# 파일 자체 test 공용 함수
def test_query_by_itself(
    query_func, db_type: str = "snowflake", max_rows: int = 5, *args, **kwargs
) -> pd.DataFrame:
    """
    지정한 DB에서 쿼리를 실행하고 결과를 DataFrame 형태로 출력 및 반환합니다.

    Parameters:
        query (str): 실행할 SQL 쿼리 문자열
        db_type (str): 사용할 DB 종류 ("snowflake", "oracle_bi", "oracle_mes", "sqlite") (기본값: "snowflake")
        max_rows (Optional[int]): 출력할 최대 행 수 (기본값: 5)

    Returns:
        pd.DataFrame: 쿼리 실행 결과
    """
    try:
        query = query_func(*args, **kwargs)
        client = db_client.get_client(db_type=db_type)
        df = client.execute(query=query)

        print(f"[INFO] Query executed successfully on '{db_type}' database.")
        print(
            f"Testing [{query_func.__name__}] rows : {df.shape[0]} columns : {df.shape[1]}"
        )
        print(df.head(max_rows))
        print("-" * 40)

    except Exception as e:
        print(f"[ERROR] Failed to execute query: {e}")
        raise


# 날짜 형식 변환 함수
def format_date_to_yyyymmdd(date_str: str) -> str:
    """
    YYYY-MM-DD 형식의 날짜 문자열을 YYYYMMDD 형식으로 변환합니다.

    Parameters
    ----------
    date_str : str
        YYYY-MM-DD 형식의 날짜 문자열

    Returns
    -------
    str
        YYYYMMDD 형식의 날짜 문자열

    Examples
    --------
    >>> format_date_to_yyyymmdd("2025-01-01")
    '20250101'
    """
    try:
        return date_str.replace("-", "")
    except AttributeError:
        print(f"[ERROR] Failed to format date: {date_str}")
        return None
