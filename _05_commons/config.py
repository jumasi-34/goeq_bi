"""
전역 설정 파일

이 모듈은 앱 전반에 걸쳐 공통으로 사용되는 전역 상수들을 정의합니다.

포함된 항목:
- SQLite DB 경로 및 개발 모드 여부
- 날짜 기준값 (오늘, 일주일 전, 1년 전)
- 공장 코드 목록 및 OEQ 그룹 분류

사용처 예시:
- DB 접근 (`SQLITE_DB_PATH`)
- MTTC 계산 기준일 (`today`, `a_week_ago`)
- 시각화 또는 필터 기준 (`plant_codes`, `oeqg_codes`)
"""

from datetime import datetime, timedelta
from pathlib import Path

# 시스템 설정
SQLITE_DB_PATH = "../database/goeq_database.db"
DEV_MODE = True


# 날짜 관련 함수
today = datetime.now()
today_str = datetime.today().strftime("%Y-%m-%d")

this_year = today.year
one_year_ago = today - timedelta(days=365)
a_week_ago = today - timedelta(days=7)

# List & Dictionary 모음
plant_codes = ["DP", "KP", "JP", "HP", "CP", "MP", "IP", "TP", "OT"]
plant_oeqg_dict = {
    "KP": "G.OE Quality",
    "DP": "G.OE Quality",
    "IP": "G.OE Quality",
    "JP": "China OE Quality",
    "HP": "China OE Quality",
    "CP": "China OE Quality",
    "MP": "Europe OE Quality",
    "TP": "NA OE Quality",
}
oeqg_codes = ["G.OE Quality", "China OE Quality", "Europe OE Quality", "NA OE Quality"]
