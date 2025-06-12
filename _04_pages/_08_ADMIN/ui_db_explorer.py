"""
SQLite 데이터베이스 탐색 페이지

이 모듈은 SQLite 데이터베이스를 탐색하고 시각화할 수 있는 Streamlit 페이지를 제공합니다.
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import io
from _05_commons import config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 고정된 데이터베이스 경로
DB_PATH = config.SQLITE_DB_PATH


def get_tables(conn: sqlite3.Connection) -> List[str]:
    """데이터베이스의 모든 테이블 목록을 반환"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [table[0] for table in cursor.fetchall()]


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """테이블의 스키마 정보를 반환"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    schema = cursor.fetchall()
    return pd.DataFrame(
        schema, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]
    )


def load_data(
    conn: sqlite3.Connection, table_name: str, limit: Optional[int] = None
) -> pd.DataFrame:
    """테이블의 데이터를 DataFrame으로 로드"""
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    return pd.read_sql_query(query, conn)


def create_visualization(
    df: pd.DataFrame, viz_type: str, x_col: str, y_col: Optional[str] = None
) -> go.Figure:
    """데이터 시각화 생성"""
    if viz_type == "scatter" and y_col:
        fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
    elif viz_type == "histogram":
        fig = px.histogram(df, x=x_col, title=f"{x_col} 분포")
    elif viz_type == "box":
        fig = px.box(df, y=x_col, title=f"{x_col} 박스플롯")
    elif viz_type == "bar":
        fig = px.bar(df, x=x_col, title=f"{x_col} 막대 그래프")
    else:
        raise ValueError(f"지원하지 않는 시각화 유형: {viz_type}")
    return fig


def render():
    """데이터베이스 탐색 페이지를 렌더링"""
    st.title("🔍 SQLite 데이터베이스 탐색기")

    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(DB_PATH)

        # 테이블 목록 가져오기
        tables = get_tables(conn)

        if tables:
            # 테이블 선택 및 기본 설정
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_table = st.selectbox(
                    "테이블 선택", tables, help="분석할 테이블을 선택하세요."
                )
            with col2:
                row_limit = st.number_input(
                    "행 제한",
                    min_value=100,
                    max_value=10000,
                    value=1000,
                    step=100,
                    help="로드할 최대 행 수를 설정하세요.",
                )

            # 테이블 스키마 표시
            st.subheader("테이블 스키마")
            schema_df = get_table_schema(conn, selected_table)
            st.dataframe(schema_df, use_container_width=True)

            # 데이터 로드
            df = load_data(conn, selected_table, limit=row_limit)

            # 탭 생성
            tab1, tab2, tab3, tab4 = st.tabs(
                ["데이터 미리보기", "통계 분석", "시각화", "SQL 쿼리"]
            )

            with tab1:
                st.subheader("데이터 미리보기")
                st.dataframe(df.head(), use_container_width=True)

                # 데이터 정보
                st.subheader("데이터 정보")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())

            with tab2:
                st.subheader("기본 통계")
                st.dataframe(df.describe(), use_container_width=True)

                # 결측치 분석
                st.subheader("결측치 분석")
                missing_data = pd.DataFrame(
                    {
                        "결측치 수": df.isnull().sum(),
                        "결측치 비율": (df.isnull().sum() / len(df) * 100).round(2),
                    }
                )
                st.dataframe(missing_data, use_container_width=True)

            with tab3:
                st.subheader("데이터 시각화")

                # 시각화 유형 선택
                viz_type = st.selectbox(
                    "시각화 유형",
                    ["scatter", "histogram", "box", "bar"],
                    help="원하는 시각화 유형을 선택하세요.",
                )

                # 컬럼 선택
                numeric_columns = df.select_dtypes(include=["int64", "float64"]).columns
                categorical_columns = df.select_dtypes(
                    include=["object", "category"]
                ).columns

                if viz_type == "scatter":
                    col1, col2 = st.columns(2)
                    with col1:
                        x_axis = st.selectbox("X축 선택", numeric_columns)
                    with col2:
                        y_axis = st.selectbox("Y축 선택", numeric_columns)
                    if x_axis and y_axis:
                        fig = create_visualization(df, viz_type, x_axis, y_axis)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    if viz_type in ["histogram", "box"]:
                        columns = numeric_columns
                    else:
                        columns = categorical_columns

                    selected_column = st.selectbox("컬럼 선택", columns)
                    if selected_column:
                        fig = create_visualization(df, viz_type, selected_column)
                        st.plotly_chart(fig, use_container_width=True)

            with tab4:
                st.subheader("SQL 쿼리 실행")
                default_query = f"SELECT * FROM {selected_table} LIMIT 100"
                query = st.text_area(
                    "SQL 쿼리를 입력하세요",
                    default_query,
                    help="실행할 SQL 쿼리를 입력하세요.",
                )

                if st.button("쿼리 실행"):
                    try:
                        query_df = pd.read_sql_query(query, conn)
                        st.dataframe(query_df, use_container_width=True)

                        # 쿼리 결과 다운로드
                        csv = query_df.to_csv(index=False)
                        st.download_button(
                            "결과 다운로드 (CSV)",
                            csv,
                            "query_results.csv",
                            "text/csv",
                            key="download-csv",
                        )
                    except Exception as e:
                        st.error(f"쿼리 실행 중 오류 발생: {str(e)}")

            # 연결 종료
            conn.close()
        else:
            st.warning("데이터베이스에 테이블이 없습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 처리 중 오류 발생: {str(e)}")
        st.error("데이터베이스 처리 중 오류가 발생했습니다.")


render()
