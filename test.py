import streamlit as st

st.set_page_config(layout="wide")

# 상단 소개
st.title("📘 글로벌 품질 분석 시스템 가이드")
st.caption("품질 데이터 입력부터 분석, 리포트 출력까지 단계별 사용법 안내")
# st.video("videos/intro.mp4")

# 1차 탭: 메뉴 구분
main_tabs = st.tabs(["Quality Issue", "4M Change", "OE Document", "보고서 출력"])

# 예시: 입력 탭
with main_tabs[0]:
    sub_tabs = st.tabs(
        ["Define The Problem", "Root cause & Countermeasure", "Conclusion"]
    )

    with sub_tabs[0]:
        st.subheader("기능 A: 날짜 입력")
        # st.video("videos/input_date.mp4")

        # st.image("images/date_picker.png", caption="날짜 선택 화면 예시")
        st.markdown(
            """
        - 날짜 입력창에서 원하는 조회 기간을 설정합니다  
        - 기본값은 오늘 날짜 기준 최근 1개월입니다
        """
        )

        with st.expander("❓ 팁 / 유의사항"):
            st.info(
                "날짜는 최소 1일 이상 선택해야 하며, 미래 날짜는 선택할 수 없습니다."
            )

    with sub_tabs[1]:
        st.subheader("기능 B: 공장 선택")
        # st.video("videos/input_plant.mp4")

        # st.image("images/plant_select.png", caption="공장 선택 예시")
        st.markdown(
            """
        - 드롭다운에서 공장을 선택하세요  
        - 다중 선택이 가능합니다
        """
        )

        with st.expander("❗ 주의"):
            st.warning("공장을 선택하지 않으면 전체 공장 기준으로 집계됩니다.")

    with sub_tabs[2]:
        st.subheader("❓ FAQ - 입력 관련")
        with st.expander("Q. 날짜를 선택했는데 데이터가 보이지 않아요."):
            st.markdown(
                "→ 선택한 기간에 데이터가 없을 수 있습니다. 날짜를 다시 지정해 보세요."
            )
        with st.expander("Q. 공장 목록이 안 나와요."):
            st.markdown("→ 네트워크 오류이거나 공장 정보가 등록되지 않은 경우입니다.")

# 다른 메뉴 탭도 동일 구조 반복 가능
# main_tabs[1], main_tabs[2] ... 각 하위 탭 구성 동일
