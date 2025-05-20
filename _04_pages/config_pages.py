"""
Streamlit 페이지 구성 설정

Streamlit 앱의 라우팅, 페이지 정보, 권한 등을 정의하는 설정 파일입니다.

각 페이지는 다음 항목으로 구성됩니다:
- filename: 페이지의 경로
- title: 앱에서 보여질 제목
- icon: Streamlit에서 사용할 아이콘 (emoji or material)
- category: 페이지 분류 (탭 또는 섹션 기준)
- roles: 접근 가능한 사용자 권한 수준

사용처 예시:
- 페이지 탐색 메뉴 구성
- 접근 제어를 위한 권한 필터링
"""

PAGE_CONFIGS = {
    "Navigation": {
        "filename": "_04_pages/ui_000_navigation.py",
        "icon": ":material/autorenew:",
        "category": "OE Quality BI",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "Weekly CQMS Monitor": {
        "filename": "_04_pages/ui_201_weekly_cqms_monitor.py",
        "icon": ":material/autorenew:",
        "category": "Workplace",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "Ongoing Status Tracker": {
        "filename": "_04_pages/ui_202_ongoing_status_tracker.py",
        "icon": ":material/autorenew:",
        "category": "Workplace",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "OE Quality Issue Dashboard": {
        "filename": "_04_pages/ui_301_oe_quality_issue_dashboard.py",
        "icon": ":material/dashboard:",
        "category": "Detail",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "RR Analysis": {
        "filename": "_04_pages/ui_401_rr_analysis.py",
        "icon": ":material/query_stats:",
        "category": "Support",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "FM Monitoring": {
        "filename": "_04_pages/ui_402_fm_monitoring.py",
        "icon": ":material/query_stats:",
        "category": "Support",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "Manual Aggregator": {
        "filename": "_04_pages/ui_901_manual_aggregator.py",
        "icon": ":material/query_stats:",
        "category": "Setting",
        "roles": ["Admin"],
    },
        "Login History Access": {
        "filename": "_04_pages/ui_902_assess_log_temp.py",
        "icon": ":material/query_stats:",
        "category": "Setting",
        "roles": ["Admin"],
    },
}
