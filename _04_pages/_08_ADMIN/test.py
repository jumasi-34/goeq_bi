import streamlit as st
from _00_database.db_client import get_client
from _01_query.SAP import q_hk_personnel
import pandas as pd

db = get_client("snowflake")

df = db.execute(q_hk_personnel.CTE_HR_PERSONAL)
st.write("Original data from Snowflake:")
st.dataframe(df)
st.write("Data types:", df.dtypes)

# 컬럼명을 대문자로 변환
df.columns = df.columns.str.upper()

# 수동 데이터 추가
df_new = pd.DataFrame(
    [
        {"PNL_NO": "21300315", "PNL_NM": "KIM JEE WOONG"},
        {"PNL_NO": "21000075", "PNL_NM": "SOUNG HYUN JUN"},
        {"PNL_NO": "21100293", "PNL_NM": "KIM SEUNG JAE"},
        {"PNL_NO": "21200424", "PNL_NM": "OH JIN TAEK"},
        {"PNL_NO": "21604756", "PNL_NM": "RYU JE WOOK"},
    ]
)

st.write("Manual data:")
st.dataframe(df_new)

# 데이터프레임 결합 후 인덱스 재설정
df_concat = pd.concat([df, df_new], ignore_index=True)

st.write("Combined data:")
st.dataframe(df_concat)
st.write("Combined data types:", df_concat.dtypes)

# 중복 확인
duplicates = df_concat[df_concat.duplicated(subset=["PNL_NO"], keep=False)]
if not duplicates.empty:
    st.warning(f"Found duplicate PNL_NO entries: {duplicates['PNL_NO'].tolist()}")
else:
    st.success("No duplicate PNL_NO entries found")
