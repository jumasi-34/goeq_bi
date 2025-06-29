from datetime import datetime
from typing import Union


def query_return_individual(
    start_date: Union[str, datetime, None] = None,
    end_date: Union[str, datetime, None] = None,
    mcode: Union[str, list[str], None] = None,
) -> str:
    """HGWS 반품 개별 조회 쿼리를 생성합니다.

    Args:
        start_date (str | datetime | None, optional): 시작일자 (YYYY-MM-DD 형식 또는 datetime 객체). Defaults to None.
        end_date (str | datetime | None, optional): 종료일자 (YYYY-MM-DD 형식 또는 datetime 객체). Defaults to None.
        mcode (str | list[str] | None, optional): 제품코드 또는 제품코드 리스트. Defaults to None.

    Returns:
        str: HGWS 반품 데이터 조회를 위한 SQL 쿼리
    """
    # 기본값 설정
    if start_date is None:
        start_date = "2024-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 날짜 형식을 YYYYMM으로 변환
    def convert_to_yyyymm(date):
        if isinstance(date, datetime):
            return date.strftime("%Y%m")
        elif isinstance(date, str):
            return date.replace("-", "")[:6]
        return date

    start_date = convert_to_yyyymm(start_date)
    end_date = convert_to_yyyymm(end_date)

    # mcode 조건 처리
    mcode_condition = ""
    if mcode:
        if isinstance(mcode, str):
            mcode_condition = f"AND ZMATNR = '{mcode}'"
        elif isinstance(mcode, list):
            if all(isinstance(code, str) for code in mcode):
                formatted_list = ", ".join(f"'{code}'" for code in mcode)
            else:
                formatted_list = ", ".join(f"'{str(code)}'" for code in mcode)
            mcode_condition = f"AND ZMATNR IN ({formatted_list})"

    query = f"""--sql
        SELECT
            CASE 
                WHEN WERKS = '6220' THEN 'HP'
                WHEN WERKS = '1120' THEN 'DP'
                WHEN WERKS = '6510' THEN 'CP'
                WHEN WERKS = '4310' THEN 'IP'
                WHEN WERKS = '1130' THEN 'KP'
                WHEN WERKS = '6110' THEN 'JP'
                WHEN WERKS = '3A10' THEN 'MP'
                WHEN WERKS = '2910' THEN 'TP'
                ELSE 'NI' 
            END AS "PLANT",
            ZMATNR "MCODE",
            ZCLS3T "Sort 3", 
            ZCLS4T "Sort 4", 
            ZNAME "Reason Description", 
            COUNT(*) "Return cnt"
        FROM HKT_DW.BI_DWUSER.SAP_ZSRT10000
        WHERE ZREASON NOT IN ('W1SA', 'W1SB', 'W2SB', 'W5SA', 'W5SB', 'W5SC', 'W5SD', 'W5SF', 'W5SG')
        AND ZRULT NOT IN ('R')
        AND SPMON >= '{start_date}'
        AND SPMON <= '{end_date}'
        {mcode_condition}
        GROUP BY WERKS, ZMATNR, ZCLS3T, ZCLS4T, ZNAME
        ORDER BY "Return cnt" DESC;
    """
    return query
