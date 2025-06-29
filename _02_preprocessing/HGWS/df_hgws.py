from _00_database.db_client import get_client
from _01_query.HGWS import q_hgws


def get_hgws_df(m_code, start_date=None, end_date=None):
    query = q_hgws.query_return_individual(
        mcode=m_code, start_date=start_date, end_date=end_date
    )
    df = get_client("snowflake").execute(query)
    df.columns = df.columns.str.upper()
    df = df.sort_values(by="RETURN CNT", ascending=False)
    return df
