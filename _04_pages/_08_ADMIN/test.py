import pandas as pd
from _02_preprocessing.GMES.df_ctl import get_groupby_mcode_ctl_df
import streamlit as st

df = get_groupby_mcode_ctl_df(
    mcode="1031953", start_date="20240415", end_date="20241012"
)

st.dataframe(df)
