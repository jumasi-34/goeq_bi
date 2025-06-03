"""
인사정보 기본 데이터를 조회하는 CTE 쿼리

- 사원번호와 사원명을 조회하는 기본 인사정보 쿼리입니다.
- 데이터 소스: HKT_DW.BI_GERPUSER.ZHRT90041 (인사정보 테이블)

Returns
-------
str
    사원번호(PNL_NO)와 사원명(PNL_NM)을 조회하는 SQL 쿼리 문자열
"""

CTE_HR_PERSONAL = """--sql
    SELECT
        PERNR AS PNL_NO,  -- 사원번호
        NACHN AS PNL_NM   -- 사원명
    FROM HKT_DW.BI_GERPUSER.ZHRT90041  -- 인사정보 테이블
"""
