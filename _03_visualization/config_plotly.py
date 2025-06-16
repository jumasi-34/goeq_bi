import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.getenv(
    "PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

"""
Plotly 시각화 설정

이 모듈은 Plotly 차트를 구성할 때 사용할 색상 코드, 날짜 범위, 월 이름 등의
시각적 스타일 설정값을 정의합니다.

포함된 항목:
- 월 이름 약어 리스트
- 색상 상수 및 RGBA 값 (긍정/부정/회색 계열 등)
- 차트 스타일 및 레이아웃 설정

사용처 예시:
- Plotly 그래프의 색상 통일
- 시계열 차트 범위 지정
- 월별 축 라벨링
- 차트 스타일 및 레이아웃 통일
"""

from datetime import datetime, timedelta

months_abbreviation = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

## Color Setting
BLACK_CLR = "#000000"
WHITE_CLR = "#FFFFFF"
NEGATIVE_CLR = "#E31C12"
POSITIVE_CLR = "#0078FF"
GRAY_CLR, color_Gray_RGBA = "#9a9b9c", "rgba(154, 155, 156, 0.6)"
LIGHT_GRAY_CLR, color_LightGray_RGBA = "#ededed", "rgba(237, 237, 237, 0.6)"
DARK_GRAY_CLR, color_DarkGray_RGBA = "#575756", "rgba(87, 87, 86, 0.6)"
ORANGE_CLR, color_Orange_RGBA = "#ec6608", "rgba(236, 102, 8, 0.6)"
multi_color_lst = [
    "#EC6608",
    "#F5BF1E",
    "#A1D127",
    "#348C57",
    "#6BBFED",
    "#315A74",
    "#5F4327",
    "#575756",
    "#909090",
    "#AAAAAA",
    "#AAAAAA",
]

## Chart Style Settings
CHART_STYLES = {
    "pie": {
        "textinfo": "label+value",
        "direction": "clockwise",
        "line_width": 0.5,
        "hover_template": """<b>Plant</b>: %{label}<br><b>Count</b>: %{value}<br><b>Possession</b>: %{percent:.1%}<extra></extra>""",
    },
    "bar": {
        "text_position": "outside",
        "hover_template": """<b>Month</b>: %{x|%b. %Y}<br><b>Count</b>: %{y:.0f}EA<extra></extra>""",
    },
}

## Layout Settings
LAYOUT_STYLES = {
    "pie": {"showlegend": False},
    "bar": {
        "yaxis": {"showgrid": False, "showticklabels": False},
        "xaxis": {"tickmode": "array"},
        "showlegend": False,
    },
}

## Chart Titles
CHART_TITLES = {
    "ongoing_qi": {"pie": "Opening status by plant", "bar": "Monthly openings"},
    "ongoing_4m": {"pie": "Opening status by plant", "bar": "Monthly openings"},
    "ongoing_audit": {"pie": "Opening status by plant", "bar": "Monthly openings"},
}
