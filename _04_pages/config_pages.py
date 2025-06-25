import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

"""
Streamlit 페이지 구성 설정

Streamlit 앱의 라우팅, 페이지 정보, 권한 등을 정의하는 설정 파일입니다.

각 페이지는 다음 항목으로 구성됩니다:
- filename: 페이지의 경로
- title: 앱에서 보여질 제목
- icon: Streamlit에서 사용할 아이콘 (material)
- category: 페이지 분류 (탭 또는 섹션 기준)
- roles: 접근 가능한 사용자 권한 수준

사용처 예시:
- 페이지 탐색 메뉴 구성
- 접근 제어를 위한 권한 필터링
"""

"""
- Dashboard
- Analysis
- Monitoring
- Collaboration
- User Guide
- Workplace
- Settings
- Admin
- System
"""

PAGE_CONFIGS = {
    # Dashboard
    "OE Quality Issue Dashboard": {
        "filename": "_04_pages/_01_DASHBOARD/ui_oe_quality_issue_dashboard.py",
        "icon": ":material/dashboard:",
        "category": "Dashboard",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "Product Assessment Result(OE)": {
        "filename": "_04_pages/_08_ADMIN/ui_oeassessment_result_viewer.py",
        "icon": ":material/assessment:",
        "category": "Dashboard",
        "roles": ["Contributor", "Admin"],
    },
    # Analysis
    "Product History": {
        "filename": "_04_pages/_08_ADMIN/ui_product_history.py",
        "icon": ":material/query_stats:",
        "category": "Analysis",
        "roles": ["Contributor", "Admin"],
    },
    "RR Analysis": {
        "filename": "_04_pages/_02_ANALYSIS/ui_rr_analysis.py",
        "icon": ":material/query_stats:",
        "category": "Analysis",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    # Monitoring
    "Weekly CQMS Monitor": {
        "filename": "_04_pages/_03_MONITORING/ui_weekly_cqms_monitor.py",
        "icon": ":material/autorenew:",
        "category": "Monitoring",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    "Ongoing Status Tracker": {
        "filename": "_04_pages/_03_MONITORING/ui_ongoing_status_tracker.py",
        "icon": ":material/autorenew:",
        "category": "Monitoring",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    # Collaboration
    "FM Monitoring": {
        "filename": "_04_pages/_04_COLLABORATION/ui_fm_monitoring.py",
        "icon": ":material/query_stats:",
        "category": "Collaboration",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
    # User Guide
    "CQMS User Guide": {
        "filename": "_04_pages/_05_USER_GUIDE/ui_cqms_userguide.py",
        "icon": ":material/bar_chart:",
        "category": "User Guide",
        "roles": ["Admin"],
    },
    "Plotly Guide": {
        "filename": "_04_pages/_05_USER_GUIDE/plotly_guide.py",
        "icon": ":material/bar_chart:",
        "category": "User Guide",
        "roles": ["Admin"],
    },
    # Workplace
    "OE Assessment Target": {
        "filename": "_04_pages/_06_WORKPLACE/ui_oeassessment_target_manage.py",
        "icon": ":material/settings:",
        "category": "Workplace",
        "roles": ["Contributor", "Admin"],
    },
    # Settings
    "Manual Aggregator": {
        "filename": "_04_pages/_07_SETTINGS/ui_manual_aggregator.py",
        "icon": ":material/query_stats:",
        "category": "Settings",
        "roles": ["Contributor", "Admin"],
    },
    # Admin
    "Database Explorer": {
        "filename": "_04_pages/_08_ADMIN/ui_db_explorer.py",
        "icon": ":material/database:",
        "category": "Admin",
        "roles": ["Admin"],
    },
    "SQLite Management": {
        "filename": "_04_pages/_08_ADMIN/sqlite_management.py",
        "icon": ":material/query_stats:",
        "category": "Admin",
        "roles": ["Admin"],
    },
    "test": {
        "filename": "_04_pages/_08_ADMIN/test.py",
        "icon": ":material/query_stats:",
        "category": "Admin",
        "roles": ["Admin"],
    },
    "Login History Access": {
        "filename": "_04_pages/_08_ADMIN/ui_assess_log_temp.py",
        "icon": ":material/query_stats:",
        "category": "Admin",
        "roles": ["Admin"],
    },
    # System
    "Navigation": {
        "filename": "_04_pages/_09_SYSTEM/ui_navigation.py",
        "icon": ":material/autorenew:",
        "category": "System",
        "roles": ["Viewer", "Contributor", "Admin"],
    },
}
