# CQMS 모니터링 대시보드 API 문서

## 개요
CQMS 모니터링 대시보드는 품질 이슈, 4M 변경사항, 고객 감사 데이터를 시각화하고 모니터링하는 웹 애플리케이션입니다.

## 주요 기능

### 1. 데이터 로딩 및 처리
- `load_metric_data(start_of_week: datetime, end_of_week: datetime, metric_type: str) -> Tuple[pd.Series, pd.Series, str, List[str]]`
  - 주간 지표 데이터를 로드하고 반환
  - 매개변수:
    - `start_of_week`: 주의 시작일
    - `end_of_week`: 주의 종료일
    - `metric_type`: 지표 유형 ("quality", "4m", "audit")
  - 반환값:
    - 현재 주 데이터
    - 이전 주 데이터
    - 지표 제목
    - 지표 키 목록

### 2. 데이터 표시
- `display_metric_section(df_current: pd.Series, df_before: pd.Series, metric_keys: List[str], title: str) -> None`
  - 지표 섹션을 표시
  - 매개변수:
    - `df_current`: 현재 데이터
    - `df_before`: 이전 데이터
    - `metric_keys`: 표시할 지표 키
    - `title`: 섹션 제목

### 3. 데이터 필터링
- `display_data_section(df: pd.DataFrame, status_options: List[str], key: str, column_config: Dict) -> None`
  - 필터링된 데이터를 표시
  - 매개변수:
    - `df`: 원본 데이터프레임
    - `status_options`: 상태 옵션 목록
    - `key`: 섹션 식별자
    - `column_config`: 컬럼 설정

## 설정

### 환경 변수
- `CQMS_ENV`: 환경 설정 (development/production)
- `SNOWFLAKE_*`: Snowflake 데이터베이스 연결 정보
- `SQLITE_DB_PATH`: SQLite 데이터베이스 경로

### 로깅
- 로그 파일: `logs/cqms_monitor.log`
- 로그 레벨: INFO
- 로그 포맷: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## 성능 모니터링

### 메트릭
- 함수 실행 시간
- 데이터 로딩 시간
- 캐시 히트율

### 임계값
- 로그 임계값: 1.0초
- 캐시 TTL: 3600초 (1시간)
- 최대 캐시 크기: 1000

## 에러 처리

### 주요 예외 상황
1. 데이터베이스 연결 실패
2. 데이터 로딩 실패
3. 잘못된 날짜 범위
4. 잘못된 지표 타입

### 에러 메시지
- 사용자 친화적인 에러 메시지 표시
- 상세한 로그 기록
- 관리자 알림

## 보안

### 인증
- 역할 기반 접근 제어
- 비밀번호 해싱
- 세션 관리

### 데이터 보호
- 민감 정보 암호화
- 접근 로그 기록
- 정기적인 감사 