# CQMS Query Management Package

CQMS(CQMS Quality Issue) 쿼리 관리 패키지입니다.

## 기능

- CQMS 품질 이슈 관리용 SQL 쿼리 템플릿 제공
- 공장/이슈 영역/시장 코드 매핑
- 대시보드/리포트용 메인 쿼리 생성

## 데이터 소스

- HKT_DW.EQMSUSER.CQMS_QUALITY_ISSUE
- CQMS_ISSUE_CATEGORY_DATA
- CQMS_QUALITY_ISSUE_MATERIAL
- ZHRT90041

## 설치 방법

```bash
pip install -e .
```

## 사용 방법

```python
from _01_query.CQMS.q_quality_issue import query_quality_issue

# 특정 연도의 데이터 조회
query = query_quality_issue(year=2024)
```

## 요구사항

- Python 3.8 이상
- pandas
- numpy
- sqlalchemy 