import pandas as pd
from _00_database.db_client import get_client
from _01_query.GMES.q_weight import gt_wt_gruopby_ym, gt_wt_individual


def get_groupby_weight_ym_df(
    mcode: str, start_date: str, end_date: str
) -> pd.DataFrame:
    query = gt_wt_gruopby_ym(mcode=mcode, start_date=start_date, end_date=end_date)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    df["PASS_PCT"] = df["WT_PASS_QTY"] / df["WT_INS_QTY"]
    df["INS_DATE_YM"] = df["INS_DATE_YM"].str[:4] + "-" + df["INS_DATE_YM"].str[4:6]
    return df


def get_weight_individual_df(
    mcode: str, start_date: str, end_date: str
) -> pd.DataFrame:
    query = gt_wt_individual(mcode=mcode, start_date=start_date, end_date=end_date)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    df["INS_DATE"] = pd.to_datetime(df["INS_DATE"])
    df["INS_DATE_YM"] = df["INS_DATE"].dt.strftime("%Y-%m")
    return df
