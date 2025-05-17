# _00_database
## db_client.py
### get_client() 함수 사용법
> 프로젝트에서 사용하는 데이터베이스 종류에 따라 적절한 클라이언트 객체를 반환하는 팩토리 함수

#### 1.함수 정의
```python
@st.cache_resource
def get_client(db_type: str = "snowflake") -> BaseClient:
```

#### 2. 파라미터 및 반환값
- 파라미터  
    - db_type (str, 기본값: "snowflake"): 사용할 DB 종류. 아래 값 중 하나를 선택
        - "**snowflake**": Snowflake 데이터베이스  
        - "**oracle_bi**": Oracle BI 시스템  
        - "**oracle_mes**": Oracle MES 시스템  
        - "**sqlite**": 로컬 SQLite DB  

- 반환값
  - 선택한 DB에 연결 가능한 클라이언트 객체  
    (SnowflakeClient, OracleClientBI, OracleClientMES, SQLiteClient)

#### 3. USECASE

```python
# Snowflake 클라이언트 가져오기
client = get_client("snowflake")
df = client.execute("SELECT * FROM my_table")
```

#### 4. 팁 및 주의사항
- 이 함수는 @st.cache_resource로 캐싱되어 있으므로 Streamlit 앱의 성능 최적화에 도움됩니다.
- 내부적으로 create_engine()을 사용해 SQLAlchemy 기반 연결을 생성하며, 연결 종료 시 engine.dispose()로 자원을 해제합니다.
- SQLite 클라이언트는 config.SQLITE_DB_PATH를 참조하므로, 해당 경로가 정확히 설정되어야 합니다.
- SQLite 외 다른 DB의 접속 정보는 코드에 하드코딩되어 있으므로 보안에 유의해야 합니다.



# _01_query_package
## q_query_module.py 작성요령
    1. 공통 import 및 경로 설정
    2. DECODE용 딕셔너리 정의 및 변환
    3. CTE 정의
    4. 최종 SQL 생성 함수(query_*)
    5. main() 테스트 함수
   
### 전체 작성 시 고려할 수 있는 보일러플레이트 템플릿
```python
"""
[모듈 설명]
"""

import sys
sys.path.append(...)
from _01_query.helper_sql import convert_dict_to_decode, test_query_by_itself

# DECODE 딕셔너리
...

# CTE 정의
...

# 최종 Query 함수
def query_something(param=None):
    ...
    return query

# 단독 실행용
def main():
    test_query_by_itself(query_something)

if __name__ == "__main__":
    main()
```

### 1. Import 및 공통 설정
- 모든 모듈에서 경로 설정은 동일하게 sys.path.append()로 시작
- 반복되는 유틸 함수는 helper_sql.py에 정의하고 import

### 2. DECODE 변환 딕셔너리 관리
- 딕셔너리 형태로 비즈니스 룰을 명확히 정의
- convert_dict_to_decode()를 사용해 Snowflake/Oracle SQL의 DECODE() 문으로 자동 변환
- 파라미터화된 DECODE를 사용하면 가독성 향상과 하드코딩 방지 가능
- ✅ 팁: DECODE 변환 값은 모두 상수처럼 대문자 네이밍 사용 → DECODE_...

### 3. CTE 분리 작성
- 하나의 쿼리라도 논리적 구성 단위로 나누어 CTE로 관리
- 각 CTE 이름은 CTE_ 접두어 + 의미 있는 이름 구성
- CTE 정의 시 반드시 SQL 주석 --sql 추가 (IDE 또는 Obsidian 구문 하이라이팅 대응)
- 권장 순서: 
  1. 메인 테이블 
  2. 코드성 테이블 [ 01:Performance, 02:Visual ]
  3. 외부 참조 인사 테이블 (ex. 인사정보, 마스터코드 등)

### 4. SQL 함수 구성 규칙
- 함수명은 query_데이터명() 형태로 작성
- 내부에서는 WITH ...로 CTE를 연결하고, 연도 필터(year) 등은 Python에서 처리
- 파라미터는 모두 선택형으로 작성하여 유연성 확보
- SQL 주석은 항상 --sql을 포함해 가독성과 구문 강조 유도

### 5. main() 함수 구성
- 모든 쿼리 모듈은 main()을 포함하여 독립 실행 가능하도록 설계
- test_query_by_itself()는 개발 시 개별 쿼리 검증을 위한 공통 헬퍼 함수



