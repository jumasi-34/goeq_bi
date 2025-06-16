"""
엑셀 파일의 데이터를 DB에 저장하는 모듈입니다.

이 모듈은 다음과 같은 기능을 수행합니다:
1. 엑셀 파일에서 데이터를 로드
2. 데이터 전처리
3. DB에 저장

Returns:
    None
"""

import sys
import os
import pandas as pd
import streamlit as st

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from _00_database.db_client import SQLiteClient


def load_excel_data(file_path: str) -> pd.DataFrame:
    """엑셀 파일에서 데이터를 로드합니다.

    Args:
        file_path: 엑셀 파일 경로

    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"엑셀 파일 로드 중 오류 발생: {str(e)}")
        raise


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """데이터를 전처리합니다.

    Args:
        df: 원본 데이터프레임

    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    # 날짜 컬럼이 있다면 datetime 형식으로 변환
    date_columns = df.select_dtypes(include=["object"]).columns
    for col in date_columns:
        try:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        except:
            continue

    return df


def save_to_db(df: pd.DataFrame, table_name: str, db_client: SQLiteClient):
    """데이터를 DB에 저장합니다.

    Args:
        df: 저장할 데이터프레임
        table_name: 저장할 테이블 이름
        db_client: DB 클라이언트 인스턴스
    """
    try:
        db_client.insert_dataframe(df, table_name)
        st.success(f"데이터가 {table_name} 테이블에 성공적으로 저장되었습니다.")
    except Exception as e:
        st.error(f"DB 저장 중 오류 발생: {str(e)}")
        raise


def main():
    """메인 실행 함수"""
    try:
        # 파일 경로 설정
        file_path = "mass_assess.xlsx"
        table_name = "mass_assess_target"

        # DB 클라이언트 초기화
        db_client = SQLiteClient()

        # 엑셀 파일 로드
        df = load_excel_data(file_path)

        # 데이터 전처리
        df_processed = preprocess_data(df)

        # DB에 저장
        save_to_db(df_processed, table_name, db_client)

    except Exception as e:
        st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
        raise


if __name__ == "__main__":
    main()
