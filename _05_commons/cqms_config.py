"""
CQMS 모니터링 대시보드 설정 파일
"""

import os
import sys
from typing import Dict, List

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

# 환경 설정
ENV = os.getenv("CQMS_ENV", "development")
DEV_MODE = ENV == "development"

# 로깅 설정
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_dir": "logs",
    "log_file": "cqms_monitor.log",
}

# 상태 옵션
STATUS_OPTIONS = {
    "quality_4m": ["Open", "Open & Close", "Close", "On-going"],
    "audit": ["NEW", "Upcoming", "CLOSE", "Need Update"],
}

# 컬럼 설정
COLUMN_CONFIGS = {
    "quality_issue": {
        "DOC_NO": "문서 번호",
        "M_CODE": "M-코드",
        "REG_DATE": "등록일",
        "PNL_NM": "담당자",
        "CATEGORY": "카테고리",
        "SUB_CATEGORY": "하위 카테고리",
        "ISSUE_REGIST_DATE": "대책",
        "COMP_DATE": "완료일",
        "HK_FAULT_YN": "HK 결함",
        "URL": "링크",
    },
    "4m_change": {
        "DOC_NO": "문서 번호",
        "URL": "링크",
        "REG_DATE": "등록일",
        "COMP_DATE": "완료일",
    },
    "audit": {
        "CAR_MAKER": "OEM",
        "AUDIT_SUBJECT": "주제",
        "START_DT": "감사 시작",
        "END_DT": "감사 종료",
        "OWNER_ACC_NO": "담당자",
        "REG_DT": "등록일",
        "COMP_DT": "업데이트",
        "URL": "링크",
    },
}

# 성능 모니터링 설정
PERFORMANCE_CONFIG = {
    "log_threshold": 1.0,  # 1초 이상 걸리는 작업 로깅
    "metrics_enabled": True,
}

# 데이터베이스 설정
DB_CONFIG = {
    "snowflake": {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    },
    "sqlite": {"path": os.getenv("SQLITE_DB_PATH", "data/cqms.db")},
}

# 캐시 설정
CACHE_CONFIG = {"ttl": 3600, "max_size": 1000}  # 1시간

# UI 설정
UI_CONFIG = {
    "date_format": "YYYY-MM-DD",
    "min_date": "2022-01-01",
    "max_date": None,  # 현재 날짜로 설정
    "page_title": "CQMS 모니터링 대시보드",
    "page_icon": "📊",
}
