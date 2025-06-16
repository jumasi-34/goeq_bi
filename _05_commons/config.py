"""
전역 설정 파일

이 모듈은 앱 전반에 걸쳐 공통으로 사용되는 전역 상수들을 정의합니다.

주요 기능:
- 시스템 설정 (DB 경로, 개발 모드)
- 날짜 관련 상수 정의
- 공장 및 OEQ 그룹 관련 상수 정의

상세 설명:
1. 시스템 설정
   - SQLITE_DB_PATH: SQLite 데이터베이스 파일 경로
   - DEV_MODE: 개발 모드 활성화 여부
   - PROJECT_ROOT: 프로젝트 루트 디렉토리 경로

2. 날짜 관련 상수
   - today: 현재 날짜/시간
   - today_str: YYYY-MM-DD 형식의 현재 날짜 문자열
   - this_year: 현재 연도
   - one_year_ago: 1년 전 날짜
   - a_week_ago: 1주일 전 날짜

3. 공장 및 OEQ 그룹 관련 상수
   - plant_codes: 공장 코드 목록
   - plant_oeqg_dict: 공장별 OEQ 그룹 매핑
   - oeqg_codes: OEQ 그룹 코드 목록

사용 예시:
    from _05_commons import config

    # DB 접근
    db_path = config.SQLITE_DB_PATH

    # MTTC 계산
    mttc = calculate_mttc(config.today, config.a_week_ago)

    # 공장 필터링
    filtered_plants = [p for p in config.plant_codes if p in config.plant_oeqg_dict]
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import os
import sys

# 시스템 설정
SQLITE_DB_PATH: str = "../database/goeq_database.db"
DEV_MODE: bool = True

# 날짜 관련 상수
today: datetime = datetime.now()
today_str: str = today.strftime("%Y-%m-%d")
this_year: int = today.year
one_year_ago: datetime = today - timedelta(days=365)
a_week_ago: datetime = today - timedelta(days=7)

# 공장 관련 상수
plant_codes: List[str] = ["DP", "KP", "JP", "HP", "CP", "MP", "IP", "TP", "OT"]

# OEQ 그룹 관련 상수
plant_oeqg_dict: Dict[str, str] = {
    "KP": "G.OE Quality",
    "DP": "G.OE Quality",
    "IP": "G.OE Quality",
    "JP": "China OE Quality",
    "HP": "China OE Quality",
    "CP": "China OE Quality",
    "MP": "Europe OE Quality",
    "TP": "NA OE Quality",
}

oeqg_codes: List[str] = [
    "G.OE Quality",
    "China OE Quality",
    "Europe OE Quality",
    "NA OE Quality",
]
