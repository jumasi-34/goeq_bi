"""
df_402_fm_monitoring.py
"""

import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


sys.path.append(r"D:\OneDrive - HKNC\@ Project_CQMS\# Workstation_2")
from _00_database.db_client import get_client
from _01_query.GMES import q_production, q_ncf
from _02_preprocessing import config_pandas
from _05_commons import config
from _02_preprocessing.helper_pandas import CountWorkingDays, test_dataframe_by_itself


fm_ncf_list = [
    "FBC",
    "FCB",
    "FGB",
    "FHV",
    "FIR",
    "FLA",
    "FM",
    "FM1",
    "FM2",
    "FM3",
    "FM4",
    "FMA",
    "FMB",
    "FMC",
    "FME",
    "FMF",
    "FMG",
    "FMH",
    "FMI",
    "FML",
    "FMM",
    "FMN",
    "FMO",
    "FMP",
    "FMR",
    "FMS",
    "FMT",
    "FMV",
    "FMW",
    "FMX",
    "FPA",
    "FPL",
    "FMA",
    "FMD",
    "FSP",
]


def get_yearly_production_df(yyyy):
    """연도별 생산 데이터를 조회합니다.

    Args:
        yyyy (int): 조회할 연도

    Returns:
        pd.DataFrame: 생산 데이터프레임
    """
    query = f"""--sql
    SELECT 
        PLT_CD AS PLANT,
        SUM(PRDT_QTY) AS PRDT_QTY
    FROM HKT_DW.MES.WRK_F_LWRKTS118
    WHERE 1=1
        AND SUBSTRING(WRK_DATE, 1, 4) = '{yyyy}'
    GROUP BY PLT_CD
    """
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    return df


def get_monthly_fm_ncf_df(yyyy, ncf_list=fm_ncf_list):
    query = q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=ncf_list)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    return df


def get_yearly_ncf_df(yyyy, ncf_list=fm_ncf_list):
    """
    연도별 부적합 데이터를 조회합니다.

    Parameters
    ----------
    yyyy : int
        조회할 연도
    ncf_list : list, optional
        조회할 부적합 코드 리스트. 기본값은 fm_ncf_list

    Returns
    -------
    pandas.DataFrame
        부적합 데이터프레임

    Raises
    ------
    ValueError
        ncf_list가 비어있거나 None인 경우
    """

    # 부적합 코드 리스트를 SQL IN 절에 사용할 수 있는 문자열로 변환
    query = q_ncf.ncf_monthly(yyyy=yyyy, ncf_list=fm_ncf_list)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    return df


def get_yearly_ppm_df(yyyy, ncf_list=fm_ncf_list):
    df = pd.merge(
        get_yearly_production_df(yyyy=yyyy)
        .groupby("PLANT", as_index=False)["PRDT_QTY"]
        .sum(),
        get_yearly_ncf_df(yyyy=yyyy, ncf_list=ncf_list)
        .groupby("PLANT", as_index=False)["NCF_QTY"]
        .sum(),
        on="PLANT",
        how="left",
    )
    df["PPM"] = df["NCF_QTY"] / df["PRDT_QTY"] * 1_000_000
    df = df.assign(
        PLANT=pd.Categorical(df["PLANT"], categories=config.plant_codes, ordered=True)
    ).sort_values(by="PLANT")

    return df


def get_monthly_ppm_by_plant_df(yyyy, selected_plant, ncf_list=fm_ncf_list):
    df_prdt = q_production.get_yearly_production_df(yyyy=yyyy)
    df_prdt = (
        df_prdt[df_prdt["PLANT"] == selected_plant]
        .groupby("MM", as_index=False)["PRDT_QTY"]
        .sum()
    )
    df_ncf = get_yearly_ncf_df(yyyy=yyyy, ncf_list=ncf_list)
    df_ncf = (
        df_ncf[df_ncf["PLANT"] == selected_plant]
        .groupby("MM", as_index=False)["NCF_QTY"]
        .sum()
    )
    df_plant_ncf_ppm_by_monthly = pd.merge(df_prdt, df_ncf, on="MM", how="left")
    df_plant_ncf_ppm_by_monthly["PPM"] = (
        df_plant_ncf_ppm_by_monthly["NCF_QTY"]
        / df_plant_ncf_ppm_by_monthly["PRDT_QTY"]
        * 1_000_000
    )

    return df_plant_ncf_ppm_by_monthly


def get_ncf_detail_by_plant_df(yyyy, selected_plant, ncf_list=fm_ncf_list):
    yyyy = yyyy or str(datetime.today().year)
    selected_plant = selected_plant or "KP"
    df = get_yearly_ncf_df(yyyy, ncf_list)
    df = df[df["PLANT"] == selected_plant]
    df = (
        df.groupby("DFT_CD")["NCF_QTY"]
        .sum()
        .reset_index()
        .sort_values(by="NCF_QTY", ascending=False)
    )
    return df


def main():
    test_dataframe_by_itself(get_yearly_production_df, yyyy="2024")
    test_dataframe_by_itself(get_yearly_ncf_df, yyyy="2024")
    test_dataframe_by_itself(get_yearly_ppm_df, yyyy="2024")
    test_dataframe_by_itself(
        get_monthly_ppm_by_plant_df, yyyy="2024", selected_plant="KP"
    )
    test_dataframe_by_itself(
        get_ncf_detail_by_plant_df,
        yyyy="2024",
        selected_plant="KP",
    )


if __name__ == "__main__":
    main()
