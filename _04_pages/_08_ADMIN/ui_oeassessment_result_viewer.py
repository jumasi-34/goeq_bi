"""
OE Assessment 결과 조회 페이지

이 페이지는 OE Assessment 결과를 조회하고 표시하는 인터페이스를 제공합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 사용자는 결과를 확인할 수 있습니다.

주요 기능:
- Assessment 결과 테이블 표시
- 생산량, NCF, UF, 중량, RR, CTL 데이터 시각화
- 선택된 모델 코드와 기간에 대한 종합적인 품질 분석

작성자: [작성자명]
최종 수정일: [날짜]
"""

import streamlit as st
from _00_database.db_client import get_client
from _02_preprocessing.GMES.df_ctl import (
    get_ctl_raw_individual_df,
    get_groupby_doc_ctl_df,
)
from _02_preprocessing.GMES.df_production import get_daily_production_df
from _02_preprocessing.GMES.df_ncf import get_ncf_monthly_df, get_ncf_by_dft_cd
from _02_preprocessing.GMES.df_uf import (
    calculate_uf_pass_rate_monthly,
    uf_standard,
    uf_individual,
)
from _02_preprocessing.GMES.df_rr import get_processed_raw_rr_data, get_rr_oe_list_df
from _02_preprocessing.GMES.df_weight import (
    get_groupby_weight_ym_df,
    get_weight_individual_df,
)
from _03_visualization._08_ADMIN import viz_oeassessment_result_viewer as viz


def remove_outliers(group):
    """
    IQR 방법을 사용하여 그룹별 아웃라이어를 제거하는 함수

    Args:
        group (pd.DataFrame): 중량 데이터 그룹

    Returns:
        pd.DataFrame: 아웃라이어가 제거된 데이터프레임

    계산 방법:
        - Q1 (25% 분위수)와 Q3 (75% 분위수) 계산
        - IQR = Q3 - Q1
        - 하한 = Q1 - 1.5 * IQR
        - 상한 = Q3 + 1.5 * IQR
    """
    Q1 = group["MRM_WGT"].quantile(0.25)
    Q3 = group["MRM_WGT"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return group[(group["MRM_WGT"] >= lower_bound) & (group["MRM_WGT"] <= upper_bound)]


# =============================================================================
# 메인 페이지 UI 구성
# =============================================================================

main_tab = st.tabs(["Overview", "Detail", "Description"])

# SQLite 데이터베이스에서 Assessment 결과 데이터 로드
result_df = get_client("sqlite").execute("SELECT * FROM mass_assess_result")
with main_tab[0]:
    st.dataframe(result_df, use_container_width=True, hide_index=True)
    st.subheader("대상 규격 수")
    st.write(f"대상 규격 수: {len(result_df)}")

with main_tab[1]:
    # 페이지 제목 설정
    st.title("OE Assessment Result Viewer")

    # Assessment 결과 섹션 제목
    st.subheader("Assessment Result")

    # 세션 상태에 결과 데이터프레임 저장 (성능 최적화)
    if "result_df" not in st.session_state:
        st.session_state["result_df"] = result_df

    # Assessment 결과를 표 형태로 표시
    # - use_container_width: 컨테이너 전체 너비 사용
    # - hide_index: 인덱스 숨김
    # - selection_mode: 단일 행 선택 모드
    event_df = st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
        key="event_df",
        on_select="rerun",
        selection_mode="single-row",
    )

    # =============================================================================
    # 분석 대상 데이터 설정
    # =============================================================================
    # 선택된 행이 있는지 확인
    if event_df.selection.rows:
        selected_mcode = result_df.iloc[event_df.selection.rows[0]]["m_code"]
        selected_start_date = result_df.iloc[event_df.selection.rows[0]]["min_date"]
        selected_end_date = result_df.iloc[event_df.selection.rows[0]]["max_date"]

        st.subheader("Selected Data")
        st.subheader(f"M - CODE : {selected_mcode}")

        # 날짜 형식을 YYYY-MM-DD로 변환 (일부 함수에서 사용)
        formatted_start_date = f"{selected_start_date[:4]}-{selected_start_date[4:6]}-{selected_start_date[6:]}"
        formatted_end_date = (
            f"{selected_end_date[:4]}-{selected_end_date[4:6]}-{selected_end_date[6:]}"
        )

        # =============================================================================
        # 생산량 분석 섹션
        # =============================================================================

        # 일별 생산량 데이터 조회 및 시각화
        prdt_df = get_daily_production_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        st.plotly_chart(viz.draw_barplot_production(prdt_df), use_container_width=True)

        # =============================================================================
        # NCF (부적합) 분석 섹션
        # =============================================================================

        # 2열 레이아웃으로 NCF 분석 결과 표시
        ncf_cols = st.columns(2)

        # NCF 월별 수량 분석
        ncf_df = get_ncf_monthly_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        ncf_cols[0].plotly_chart(viz.draw_barplot_ncf(ncf_df), use_container_width=True)

        # NCF 부적합코드별 수량 분석 (파레토 차트)
        ncf_by_dft_cd_df = get_ncf_by_dft_cd(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        ncf_cols[1].plotly_chart(
            viz.draw_barplot_ncf_pareto(ncf_by_dft_cd_df), use_container_width=True
        )

        # =============================================================================
        # UF (Uniformity) 분석 섹션
        # =============================================================================

        # 2열 레이아웃으로 UF 분석 결과 표시
        uf_cols = st.columns(2)

        # UF 월별 합격률 분석
        uf_pass_rate_df = calculate_uf_pass_rate_monthly(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        uf_cols[0].plotly_chart(
            viz.draw_barplot_uf(uf_pass_rate_df), use_container_width=True
        )

        # UF 항목별 합격률 분석
        # 표준값 조회
        uf_standard_df = uf_standard(mcode=selected_mcode)
        # 개별 측정값 조회
        uf_individual_df = uf_individual(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        uf_cols[1].plotly_chart(
            viz.draw_barplot_uf_individual(uf_individual_df, uf_standard_df),
            use_container_width=True,
        )

        # =============================================================================
        # 중량 분석 섹션
        # =============================================================================

        # 2열 레이아웃으로 중량 분석 결과 표시
        wt_col = st.columns(2)

        # 중량 부적합 월별 분석
        groupby_weight_ym_df = get_groupby_weight_ym_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        wt_col[0].plotly_chart(
            viz.draw_weight_distribution(groupby_weight_ym_df), use_container_width=True
        )

        # 개별 중량 데이터 조회
        wt_individual_df = get_weight_individual_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        # 월별로 아웃라이어 제거하여 정확한 분포 분석
        wt_individual_df_no_outliers = (
            wt_individual_df.groupby("INS_DATE_YM")
            .apply(remove_outliers)
            .reset_index(drop=True)
        )

        # 표준 중량값 추출 (마지막 행의 표준값 사용)
        wt_spec = wt_individual_df["STD_WGT"].iloc[-1]

        # 아웃라이어가 제거된 중량 분포 시각화
        wt_col[1].plotly_chart(
            viz.draw_weight_distribution_individual(
                wt_individual_df_no_outliers, wt_spec
            ),
            use_container_width=True,
        )

        # =============================================================================
        # RR (Reliability) 분석 섹션
        # =============================================================================

        # 2열 레이아웃으로 RR 분석 결과 표시
        rr_col = st.columns(2)

        # RR 원시 데이터 조회 (날짜 형식: YYYY-MM-DD)
        rr_df = get_processed_raw_rr_data(
            mcode=selected_mcode,
            start_date=formatted_start_date,
            end_date=formatted_end_date,
        )
        # 날짜순으로 정렬
        rr_df = rr_df.sort_values(by="SMPL_DATE").reset_index(drop=True)

        # RR 표준값 조회 및 필터링
        rr_standard_df = get_rr_oe_list_df()
        rr_standard_df = rr_standard_df[rr_standard_df["M_CODE"] == selected_mcode]

        # RR 데이터가 존재하는 경우에만 시각화
        if len(rr_df) > 0:
            # RR 트렌드 분석
            rr_col[0].plotly_chart(
                viz.draw_rr_trend(rr_df, rr_standard_df), use_container_width=True
            )
            # RR 분포 분석
            rr_col[1].plotly_chart(
                viz.draw_rr_distribution(rr_df, rr_standard_df),
                use_container_width=True,
            )
        else:
            # RR 데이터가 없는 경우 경고 메시지 표시
            st.warning("No RR data found")

        # =============================================================================
        # CTL (Control) 분석 섹션
        # =============================================================================

        # 1:3 비율로 CTL 분석 결과 표시 (트렌드:상세 = 1:3)
        ctl_col = st.columns([1, 3])

        # CTL 원시 데이터 조회
        ctl_raw_data = get_ctl_raw_individual_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        # CTL 데이터가 존재하는 경우에만 시각화
        if len(ctl_raw_data) > 0:
            # CTL 그룹별 집계 데이터 조회
            gruopby_ctl_df = get_groupby_doc_ctl_df(
                mcode=selected_mcode,
                start_date=selected_start_date,
                end_date=selected_end_date,
            )

            # CTL 트렌드 분석 (좌측 1/4 영역)
            ctl_col[0].plotly_chart(
                viz.draw_ctl_trend(gruopby_ctl_df), use_container_width=True
            )

            # CTL 상세 분석 (우측 3/4 영역)
            ctl_col[1].plotly_chart(
                viz.draw_ctl_detail(ctl_raw_data), use_container_width=True
            )
        else:
            # CTL 데이터가 없는 경우 경고 메시지 표시
            st.warning("No CTL data found")

    else:
        # 선택된 행이 없는 경우 기본값 설정
        st.warning(
            "Please select a row from the assessment result table to view detailed analysis."
        )


with main_tab[2]:
    st.title("Detail")

    # product_assessment.md 파일을 직접 읽어서 마크다운으로 표시
    try:
        with open("_07_docs/product_assessment.md", "r", encoding="utf-8") as file:
            markdown_content = file.read()
        st.markdown(markdown_content)
    except FileNotFoundError:
        st.error("product_assessment.md 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {str(e)}")
