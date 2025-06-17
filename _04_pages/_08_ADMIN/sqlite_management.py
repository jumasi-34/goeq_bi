import streamlit as st
import pandas as pd
from _05_commons.helper import SQLiteDML, SQLiteDDL


st.title("SQLite 테이블 관리")

# 데이터베이스 연결 객체 생성
dml = SQLiteDML()
ddl = SQLiteDDL()

# 테이블 목록 조회
tables = dml.list_tables()

# 사이드바에 테이블 선택
selected_table = st.selectbox("테이블 선택", tables)

if selected_table:
    # 테이블 데이터 표시
    st.subheader("테이블 데이터")
    data = dml.fetch_query(f"SELECT * FROM {selected_table}")
    st.dataframe(data)

    # 테이블 스키마 표시
    st.subheader("테이블 스키마")
    schema = ddl.get_table_schema(selected_table)
    st.dataframe(schema)

    # 테이블 관리 기능
    st.subheader("테이블 관리")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["컬럼 추가", "컬럼 이름 변경", "SQL 실행", "테이블 삭제"]
    )

    with tab1:
        st.write("새 컬럼 추가")
        new_column = st.text_input("컬럼 이름")
        data_type = st.selectbox("데이터 타입", ["TEXT", "INTEGER", "REAL", "BLOB"])
        if st.button("컬럼 추가"):
            ddl.alter_table_add_column(selected_table, new_column, data_type)
            st.success("컬럼이 추가되었습니다.")
            st.rerun()

    with tab2:
        st.write("컬럼 이름 변경")
        old_name = st.selectbox("변경할 컬럼", schema["name"].tolist())
        new_name = st.text_input("새 컬럼 이름")
        if st.button("이름 변경"):
            ddl.alter_table_rename_column(selected_table, old_name, new_name)
            st.success("컬럼 이름이 변경되었습니다.")
            st.rerun()

    with tab3:
        st.write("SQL 쿼리 실행")
        query = st.text_area("SQL 쿼리 입력")
        if st.button("실행"):
            try:
                result = ddl.execute_custom_sql(query)
                st.dataframe(result)
            except Exception as e:
                st.error(f"쿼리 실행 중 오류 발생: {str(e)}")

    with tab4:
        st.write("테이블 삭제")
        st.warning(f"⚠️ '{selected_table}' 테이블을 삭제하시겠습니까?")
        st.write("이 작업은 되돌릴 수 없습니다.")

        # 확인 체크박스
        confirm_delete = st.checkbox("테이블 삭제를 확인합니다")

        if confirm_delete:
            if st.button("테이블 삭제", type="primary"):
                try:
                    dml.drop_table(selected_table)
                    st.success(f"'{selected_table}' 테이블이 삭제되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"테이블 삭제 중 오류 발생: {str(e)}")
