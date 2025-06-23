import streamlit as st
from pathlib import Path
from _02_preprocessing.GMES.df_ctl import get_groupby_mcode_ctl_df
import sys
import base64

sys.path.append(
    str(Path(__file__).parent.parent.parent)
)  # 현재 파일의 상위 디렉토리 추가


# 전역 변수로 스타일 정의
style = """
    border-radius: 20px;
    box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.3);
"""


def get_gif_html(gif_path: str, width=600, style=style):
    with open(gif_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        return (
            f'<img src="data:image/gif;base64,{b64}" width="{width}" style="{style}">'
        )


def display_gif_step(title: str, gif_path: str, description: str = ""):
    """
    GIF와 설명을 포함한 단계별 표시 함수

    Args:
        title (str): 단계 제목 (예: "01 Registration")
        gif_path (str): GIF 파일 경로
        description (str): 오른쪽 컬럼에 표시할 설명 텍스트
    """
    st.markdown(f"### {title}")
    cols = st.columns([5, 5], gap="large")
    cols[0].markdown(
        get_gif_html(gif_path),
        unsafe_allow_html=True,
    )
    if description:
        cols[1].markdown(description)
    st.markdown("<br>", unsafe_allow_html=True)


def material_icon_text(
    icon_name: str,
    text: str,
    size: int = 24,
    weight: int = 400,
    fill: int = 0,
    grad: int = 0,
) -> str:
    """
    Material Symbols Outlined 아이콘과 텍스트를 함께 반환하는 함수

    Args:
        icon_name (str): 아이콘 이름 (예: 'left_click')
        text (str): 표시할 텍스트
        size (int): 아이콘 크기 (20~48 추천)
        weight (int): 두께 (100~700)
        fill (int): 채우기 (0 or 1)
        grad (int): 그라디언트 (-50~200)

    Returns:
        str: HTML 문자열 (마크다운용)
    """
    style = f"--material-symbols-outlined-font-variation-settings: 'opsz' {size}, 'wght' {weight}, 'FILL' {fill}, 'GRAD' {grad}; font-variation-settings: 'opsz' {size}, 'wght' {weight}, 'FILL' {fill}, 'GRAD' {grad}; vertical-align: middle;"
    return f'<span class="material-symbols-outlined" style="{style}">{icon_name}</span> {text}'


# 탭 생성
menu_tab = st.tabs(
    [
        "📊 Overview",
        "🔧 Quality Improvement",
        "🔍 OE Audit",
        "🔄 Horizontal Deployment",
        "⚙️ 4M Change",
        "🎯 Initial Quality Management",
        "✅ OE Approval Record",
        "📋 Reliability Test Report",
        "📁 OE Document Old",
        "📄 OE Document New",
    ]
)

# Overview 탭
with menu_tab[0]:

    overview_cols = st.columns([2, 3, 3], vertical_alignment="center")
    # overview_cols[0].markdown("# Quality Improvement")
    overview_cols[1].markdown("### Purpose")
    overview_cols[2].markdown("### Expected Benefits")

    quality_issue_cols = st.columns([2, 3, 3], vertical_alignment="center")
    quality_issue_cols[0].markdown("# Quality Improvement")
    quality_issue_cols[1].markdown(
        """
- 품질이슈를 체계적으로 등록하고 관리하여 문제 발생 시 신속하게 대응할 수 있도록 지원
- 개선대책을 효과적으로 기록하고 추적하여 품질 문제의 재발을 방지
- 품질 관련 업무의 전체 이력과 진행 상황을 한눈에 파악할 수 있도록 지원
"""
    )
    quality_issue_cols[2].markdown(
        """
- 품질 이슈의 신속하고 효과적인 해결
- 체계적인 추적 및 분석을 통한 재발 방지
- 체계적인 문서 관리로 내부 업무 효율성 증대
"""
    )


## 1. Overview
### Purpose

### Expected Benefits


# Quality Improvement 탭
with menu_tab[1]:
    st.markdown("# Quality Improvement")

    st.markdown(
        """
    ## Process Flow & User Roles
    """
    )
    st.image(
        "_06_assets/cqms/PF_quality_issue.png",
        caption="Quality Improvement Process",
    )
    st.markdown(
        """
    📋 **역할 및 권한 정리**
    | No. | Stage | 작성자 | 승인자 | 비고 |
    |------|-----------|--------|--------|------|
    | 1 | 품질 이슈 등록 | 누구나 | - | 시스템 내 등록 |
    | 2 | 저장 및 기본 정보 입력 | 최초 등록자 | - | 초안 저장 |
    | 3 | 원인 및 대책 작성 | 지정된 인원 (품질팀 등) | - | 일반 사용자는 작성 불가 |
    """,
        unsafe_allow_html=True,
    )
    # 각 단계별 GIF 표시
    st.markdown("## How to Use")
    tab_guide_detail = st.tabs(
        [
            "Key Features",
            "User Guide 01: Define The Problem",
            "User Guide 02: Root Cause & Countermeasure",
            "User Guide 03: Conclusion",
        ]
    )
    with tab_guide_detail[0]:
        cols = st.columns(3)
        with cols[0].container(border=True):
            st.markdown(
                """
                ### 1. Quality Issue Registration
                - 품질 이슈 등록
                - 품질 이슈 등록
                """
            )
        with cols[1].container(border=True):
            st.markdown(
                """
                ### 2. Quality Issue Registration
                - 품질 이슈 등록
                - 품질 이슈 등록
                """
            )
        with cols[2].container(border=True):
            st.markdown(
                """
                ### 3. Quality Issue Registration
                - 품질 이슈 등록
                - 품질 이슈 등록"""
            )

    with tab_guide_detail[1]:
        cols = st.columns([1, 9], gap="large")
        cols[0].markdown("## User Guide")
        with cols[1].container(border=True):
            contents = """
    - Registration Tab Click 🖱️
    """
            display_gif_step(
                "01 Registration", "_06_assets/cqms/qi_01_registration.gif", contents
            )

            display_gif_step("02 M-Code", "_06_assets/cqms/qi_02_mcode.gif")

            display_gif_step("03 Return", "_06_assets/cqms/qi_03_return.gif")

        st.divider()
        st.markdown("## FAQ")


# 나머지 탭들도 필요에 따라 추가
with menu_tab[2]:
    st.markdown("# OE Audit")
    st.write("OE Audit content here...")

# ... 기타 탭들
