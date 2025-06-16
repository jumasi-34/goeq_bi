"""
CQMS 시스템 URL 설정

이 모듈은 품질 이슈, 감사 리포트, 4M 변경 등의 CQMS 시스템 상세 페이지에
접속할 수 있는 URL prefix를 정의합니다.

포함된 항목:
- URL_QUALITY_ISSUE: 품질 이슈 상세
- URL_AUDIT: 감사 리포트 상세
- URL_CHANGE_4M: 4M 변경 보고서

사용처 예시:
- Pandas DataFrame에 URL 컬럼을 추가할 때
- Streamlit에서 외부 링크 생성 시 활용
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

from datetime import datetime
import pandas as pd

# CQMS URL PREFIX
URL_QUALITY_ISSUE = "http://egqms.hankooktech.com/OE_Quality_Issue/OE_QualityIssue_Popup.html?callid=filter&cqmsQualityIssueSeq="
URL_AUDIT = (
    "http://egqms.hankooktech.com/CUSTOMER_AUDIT_LIST/"
    "customerAuditReportPopup.html?callid=filter&cqmsCustomerAuditSeq="
)
URL_CHANGE_4M = "http://egqms.hankooktech.com/CHANGE_MANAGE_FOUR_M/Cqms4mChangeReportArenaPopup.html?callid=filter&PART=3&DOCUMENT_NO="
