import pandas as pd
from _00_database.db_client import get_client
from _01_query.GMES.q_ctl import get_ctl_raw_query


def get_ctl_raw_individual_df(
    mcode: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """CTMS 측정 데이터를 조회하여 DataFrame으로 반환합니다.

    Args:
        mcode (str): 제품코드
        start_date (str): 시작일자
        end_date (str): 종료일자

    Returns:
        pd.DataFrame: CTMS 측정 데이터
    """
    query = get_ctl_raw_query(mcode=mcode, start_date=start_date, end_date=end_date)
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    return df


def get_groupby_doc_ctl_df(mcode: str, start_date: str, end_date: str) -> pd.DataFrame:
    """CTMS 측정 데이터를 그룹화하여 통계를 계산합니다.

    Args:
        mcode (str): 제품코드
        start_date (str): 시작일자
        end_date (str): 종료일자

    Returns:
        pd.DataFrame: 그룹화된 CTMS 측정 데이터 통계
    """
    raw_df = get_ctl_raw_individual_df(
        mcode=mcode, start_date=start_date, end_date=end_date
    )
    groupby_df = (
        raw_df.groupby(["DOC_NO", "MRM_DATE"])
        .agg(
            COUNT=("JDG", "count"),
            OK=("JDG", lambda x: (x == "OK").sum()),
            NO=("JDG", lambda x: (x == "NO").sum()),
            NI=("JDG", lambda x: (x == "NI").sum()),
        )
        .reset_index()
    )

    groupby_df["ctl_pass_rate"] = groupby_df["OK"] / (
        groupby_df["OK"] + groupby_df["NI"]
    )
    return groupby_df


def get_groupby_mcode_ctl_df(
    mcode: str, start_date: str, end_date: str
) -> pd.DataFrame:
    raw_df = get_ctl_raw_individual_df(
        mcode=mcode, start_date=start_date, end_date=end_date
    )
    groupby_df = raw_df.groupby(["M_CODE"]).agg(
        COUNT=("JDG", "count"),
        OK=("JDG", lambda x: (x == "OK").sum()),
        NO=("JDG", lambda x: (x == "NO").sum()),
        NI=("JDG", lambda x: (x == "NI").sum()),
    )
    groupby_df["CTL_PASS_RATE"] = groupby_df["OK"] / (
        groupby_df["OK"] + groupby_df["NI"]
    )
    groupby_df = groupby_df.reset_index()
    groupby_df.columns = groupby_df.columns.str.lower()
    return groupby_df
