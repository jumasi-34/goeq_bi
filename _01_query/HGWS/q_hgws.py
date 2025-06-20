from datetime import datetime


def query_return_individual(
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    mcode: str | None = None,
):
    """HGWS 반품 개별 조회 쿼리를 생성합니다.

    Args:
        start_date (str | datetime | None, optional): 시작일자 (YYYY-MM-DD 형식 또는 datetime 객체). Defaults to None.
        end_date (str | datetime | None, optional): 종료일자 (YYYY-MM-DD 형식 또는 datetime 객체). Defaults to None.
        mcode (str | None, optional): 제품코드. Defaults to None.

    Returns:
        str: HGWS 반품 데이터 조회를 위한 SQL 쿼리
    """
    # 기본값 설정
    if start_date is None:
        start_date = "2024-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if mcode is None:
        mcode = "*"

    # 날짜 형식을 YYYYMM으로 변환
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y%m")
    elif isinstance(start_date, str):
        # YYYY-MM-DD 형식을 YYYYMM으로 변환
        start_date = start_date.replace("-", "")[:6]

    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y%m")
    elif isinstance(end_date, str):
        # YYYY-MM-DD 형식을 YYYYMM으로 변환
        end_date = end_date.replace("-", "")[:6]

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
        {f"AND ZMATNR = '{mcode}'" if mcode != "*" else ""}
        GROUP BY WERKS, ZMATNR, ZCLS3T, ZCLS4T, ZNAME
        ORDER BY "Return cnt" DESC;
    """
    return query
