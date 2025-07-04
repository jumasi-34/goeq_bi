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

# =============================================================================
# Import Libraries
# =============================================================================
import importlib
import logging
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Database
from _00_database.db_client import get_client

# GMES Data Processing
from _02_preprocessing.GMES import df_ctl
from _02_preprocessing.GMES.df_production import get_daily_production_df
from _02_preprocessing.GMES.df_ncf import (
    get_ncf_monthly_df,
    get_ncf_by_dft_cd,
    get_ncf_detail,
)
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

# Other System Data Processing
from _02_preprocessing.HGWS.df_hgws import get_hgws_df
from _02_preprocessing.CQMS.df_quality_issue import get_quality_issue_df_detail
from _02_preprocessing.CQMS.df_4m_change import get_4m_change_detail_df
from _02_preprocessing.CQMS.df_cqms_unified import get_cqms_unified_df
from _02_preprocessing.HOPE.df_oeapp import load_oeapp_df_by_mcode

# Visualization
from _03_visualization._08_ADMIN import viz_oeassessment_result_viewer as viz
from _03_visualization import config_plotly
from _05_commons.css_style_config import load_custom_css
from _05_commons import config

if config.DEV_MODE:
    importlib.reload(df_ctl)

# =============================================================================
# 로깅 설정
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'logs/oeassessment_{datetime.now().strftime("%Y%m%d")}.log'
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# =============================================================================
# 에러 처리 데코레이터
# =============================================================================
def handle_data_loading_errors(
    func: Callable[..., pd.DataFrame],
) -> Callable[..., pd.DataFrame]:
    """
    데이터 로딩 함수 에러 처리 데코레이터

    Args:
        func: 실행할 데이터 로딩 함수

    Returns:
        에러 처리가 적용된 함수
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
        try:
            logger.info(f"데이터 로딩 시작: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"데이터 로딩 완료: {func.__name__} - {len(result)} 행")
            return result
        except Exception as e:
            logger.error(f"데이터 로딩 중 오류 발생: {func.__name__} - {str(e)}")
            st.error(f"데이터 로딩 중 오류 발생: {str(e)}")
            return pd.DataFrame()

    return wrapper


def handle_section_rendering_errors(func: Callable[..., None]) -> Callable[..., None]:
    """
    섹션 렌더링 함수 에러 처리 데코레이터

    Args:
        func: 실행할 섹션 함수

    Returns:
        에러 처리가 적용된 함수
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            logger.info(f"섹션 렌더링 시작: {func.__name__}")
            func(*args, **kwargs)
            logger.info(f"섹션 렌더링 완료: {func.__name__}")
        except Exception as e:
            logger.error(f"섹션 렌더링 중 오류 발생: {func.__name__} - {str(e)}")
            st.error(f"섹션 렌더링 중 오류 발생: {str(e)}")

    return wrapper


def handle_data_processing_errors(
    func: Callable[..., pd.DataFrame],
) -> Callable[..., pd.DataFrame]:
    """
    데이터 처리 함수 에러 처리 데코레이터

    Args:
        func: 실행할 데이터 처리 함수

    Returns:
        에러 처리가 적용된 함수
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
        try:
            logger.info(f"데이터 처리 시작: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"데이터 처리 완료: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"데이터 처리 중 오류 발생: {func.__name__} - {str(e)}")
            st.error(f"데이터 처리 중 오류 발생: {str(e)}")
            return pd.DataFrame()

    return wrapper


def handle_ui_rendering_errors(func: Callable[..., None]) -> Callable[..., None]:
    """
    UI 렌더링 함수 에러 처리 데코레이터

    Args:
        func: 실행할 UI 렌더링 함수

    Returns:
        에러 처리가 적용된 함수
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            logger.info(f"UI 렌더링 시작: {func.__name__}")
            func(*args, **kwargs)
            logger.info(f"UI 렌더링 완료: {func.__name__}")
        except Exception as e:
            logger.error(f"UI 렌더링 중 오류 발생: {func.__name__} - {str(e)}")
            st.error(f"UI 렌더링 중 오류 발생: {str(e)}")

    return wrapper


# =============================================================================
# 상수 정의
# =============================================================================
# 품질 지수 계산을 위한 상수들
QUALITY_INDICES_CONFIG: Dict[str, Dict[str, Union[int, float]]] = {
    "ncf": {"max_rate": 20909, "min_rate": 1165, "multiplier": 1000000},
    "uf": {"max_rate": 0.9948, "min_rate": 0.599},
    "gt_weight": {"max_rate": 1.0, "min_rate": 0.9719},
    "rr": {"max_rate": 0.999, "min_rate": 0.593},
    "ctl": {"max_rate": 1.0, "min_rate": 0.857},
}

# UI 레이아웃 상수
UI_CONFIG: Dict[str, Any] = {
    "column_ratios": {
        "ctl": [1, 3],
        "metric": [0.5, 6, 4],
        "project_info": [0.5, 10],
        "oem_event_detail": [0.5, 10],
        "production_analysis": [0.5, 10],
    },
    "status_thresholds": {
        "excellent": 80,
        "warning": 50,
    },
    "table_columns": {
        "full": [
            "m_code",
            "plant",
            "min_date",
            "max_date",
            "total_qty",
            "ncf_qty",
            "ncf_rate",
            "ncf_idx",
            "uf_pass_rate",
            "uf_idx",
            "gt_wt_pass_rate",
            "gt_idx",
            "rr_pass_rate_pdf",
            "rr_idx",
            "ctl_pass_rate",
            "ctl_idx",
            "Quality Issue",
            "4M Change",
            "Audit",
            "Field Return",
        ],
        "summary": [
            "m_code",
            "plant",
            "min_date",
            "max_date",
            "total_qty",
            "ncf_idx",
            "uf_idx",
            "gt_idx",
            "rr_idx",
            "ctl_idx",
            "Quality Issue",
            "4M Change",
            "Audit",
            "Field Return",
        ],
    },
}

# =============================================================================
# CSS Styles
# =============================================================================
load_custom_css()


# =============================================================================
# 연도 선택
# =============================================================================
with st.sidebar:
    year_select = st.pills(
        "Select Year",
        options=["2024", "2025"],
        default="2025",
    )

    year_select = int(year_select)


# =============================================================================
# Utility Functions
# =============================================================================
def remove_outliers(group: pd.DataFrame) -> pd.DataFrame:
    """
    IQR 방법을 사용하여 그룹별 아웃라이어를 제거하는 함수

    Args:
        group: 중량 데이터 그룹

    Returns:
        아웃라이어가 제거된 데이터프레임

    계산 방법:
        - Q1 (25% 분위수)와 Q3 (75% 분위수) 계산
        - IQR = Q3 - Q1
        - 하한 = Q1 - 1.5 * IQR
        - 상한 = Q3 + 1.5 * IQR

    Raises:
        KeyError: 'MRM_WGT' 컬럼이 없는 경우
        ValueError: 데이터가 비어있는 경우
    """
    if group.empty:
        raise ValueError("입력 데이터가 비어있습니다.")

    if "MRM_WGT" not in group.columns:
        raise KeyError("'MRM_WGT' 컬럼이 데이터프레임에 없습니다.")

    Q1 = group["MRM_WGT"].quantile(0.25)
    Q3 = group["MRM_WGT"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return group[(group["MRM_WGT"] >= lower_bound) & (group["MRM_WGT"] <= upper_bound)]


def multi_condition_style(val: Union[float, int]) -> str:
    """
    품질 지수 값에 따른 조건부 스타일링을 적용하는 함수

    Args:
        val: 스타일링할 값

    Returns:
        CSS 스타일 문자열

    스타일 규칙:
        - NaN 또는 0: 검은색
        - > 80: 긍정적 색상 (파란색)
        - > 50: 경고 색상 (주황색)
        - > 0: 부정적 색상 (빨간색)
    """
    if pd.isna(val) or val == 0:
        return "color: black"
    elif val > 80:
        return f"color: {config_plotly.POSITIVE_CLR}"
    elif val > 50:
        return f"color: {config_plotly.ORANGE_CLR}"
    elif val > 0:
        return f"color: {config_plotly.NEGATIVE_CLR}"
    else:
        return ""  # 기본 스타일


def get_insight_status_style(status: str) -> Tuple[str, str, str]:
    """
    Assessment Insight 상태에 따른 스타일 정보를 반환하는 함수

    Args:
        status: 상태 값 ("Need Update", "Reviewed", "Completed")

    Returns:
        (배경색, 테두리색, 텍스트색) 튜플

    상태별 색상:
        - "Need Update": 주황색 (경고)
        - "Reviewed": 파란색 (검토 중)
        - "Completed": 초록색 (완료)
    """
    status_colors = {
        "Need Update": {
            "bg_color": "#fef3c7",  # 연한 주황색 배경
            "border_color": "#f59e0b",  # 주황색 테두리
            "text_color": "#92400e",  # 진한 주황색 텍스트
        },
        "Reviewed": {
            "bg_color": "#dbeafe",  # 연한 파란색 배경
            "border_color": "#3b82f6",  # 파란색 테두리
            "text_color": "#1e40af",  # 진한 파란색 텍스트
        },
        "Completed": {
            "bg_color": "#dcfce7",  # 연한 초록색 배경
            "border_color": "#22c55e",  # 초록색 테두리
            "text_color": "#166534",  # 진한 초록색 텍스트
        },
    }

    # 기본값 (알 수 없는 상태)
    default_style = {
        "bg_color": "#f3f4f6",  # 회색 배경
        "border_color": "#9ca3af",  # 회색 테두리
        "text_color": "#6b7280",  # 회색 텍스트
    }

    style = status_colors.get(status, default_style)
    return style["bg_color"], style["border_color"], style["text_color"]


@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")


# =============================================================================
# Data Loading
# =============================================================================
@handle_data_loading_errors
def load_assessment_result() -> pd.DataFrame:
    """
    Assessment 결과 데이터를 SQLite 데이터베이스에서 로드

    Returns:
        Assessment 결과 데이터프레임

    Raises:
        Exception: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
    """
    result_df = get_client("sqlite").execute("SELECT * FROM mass_assess_result")
    result_df = result_df[result_df["year"] == year_select]

    return result_df


# =============================================================================
# 데이터 처리 함수들
# =============================================================================
@handle_data_processing_errors
def calculate_quality_indices(result_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assessment 결과에 품질 지수들을 계산하여 추가합니다.

    계산되는 지수들:
    - NCF Index: 부적합률 기반 지수 (0-100)
    - UF Index: Uniformity 합격률 기반 지수 (0-100)
    - GT Weight Index: 중량 합격률 기반 지수 (0-100)
    - RR Index: Reliability 합격률 기반 지수 (0-100)
    - CTL Index: Control 합격률 기반 지수 (0-100)

    Args:
        result_df: 원본 Assessment 결과 데이터프레임
            - ncf_qty: 부적합 수량
            - total_qty: 총 수량
            - uf_pass_rate: UF 합격률
            - gt_wt_pass_rate: GT weight 합격률
            - rr_pass_rate_pdf: RR 합격률
            - ctl_pass_rate: CTL 합격률

    Returns:
        품질 지수가 추가된 데이터프레임
            - ncf_rate: NCF 비율 (ppm)
            - ncf_idx: NCF 지수 (0-100)
            - uf_idx: UF 지수 (0-100)
            - gt_rate: GT Weight 비율
            - gt_idx: GT Weight 지수 (0-100)
            - rr_idx: RR 지수 (0-100)
            - ctl_idx: CTL 지수 (0-100)

    Raises:
        ValueError: 필수 컬럼이 없는 경우
        ZeroDivisionError: total_qty가 0인 경우
    """

    # 데이터 정렬
    result_df["start_mass_production"] = result_df["start_mass_production"].astype(
        "datetime64[ns]"
    )
    result_df["end_mass_production"] = result_df[
        "start_mass_production"
    ] + pd.Timedelta(days=179)
    result_df["status"] = result_df["end_mass_production"].apply(
        lambda x: "Completed" if x < datetime.now() else "In Progress"
    )
    result_df["YYYYMM"] = result_df["start_mass_production"].dt.strftime("%Y-%m")

    # 필수 컬럼 검증
    required_columns = [
        "ncf_qty",
        "total_qty",
        "uf_pass_rate",
        "gt_wt_pass_rate",
        "rr_pass_rate_pdf",
        "ctl_pass_rate",
    ]
    missing_columns = [col for col in required_columns if col not in result_df.columns]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")

    # 0으로 나누기 방지
    if (result_df["total_qty"] == 0).any():
        raise ZeroDivisionError("total_qty가 0인 행이 있습니다.")

    def calculate_index(
        rate: pd.Series, config: Dict[str, Union[int, float]], reverse: bool = False
    ) -> pd.Series:
        """
        품질 지수를 계산하는 헬퍼 함수

        Args:
            rate: 계산할 비율 데이터
            config: 지수 계산 설정 (max_rate, min_rate)
            reverse: 역방향 계산 여부 (높은 값이 좋은 경우 False, 낮은 값이 좋은 경우 True)

        Returns:
            계산된 지수 (0-100)
        """
        max_rate = config["max_rate"]
        min_rate = config["min_rate"]

        if reverse:
            # 낮은 값이 좋은 경우 (NCF)
            index = ((max_rate - rate) / (max_rate - min_rate) * 100).clip(0, 100)
        else:
            # 높은 값이 좋은 경우 (UF, GT Weight, RR, CTL)
            index = ((rate - min_rate) / (max_rate - min_rate) * 100).clip(0, 100)

        return index.round(1)

    # NCF 지수 계산
    result_df["ncf_rate"] = (
        result_df["ncf_qty"]
        / result_df["total_qty"]
        * QUALITY_INDICES_CONFIG["ncf"]["multiplier"]
    )
    result_df["ncf_idx"] = calculate_index(
        result_df["ncf_rate"], QUALITY_INDICES_CONFIG["ncf"], reverse=True
    )

    # UF 지수 계산
    result_df["uf_idx"] = calculate_index(
        result_df["uf_pass_rate"], QUALITY_INDICES_CONFIG["uf"]
    )

    # GT Weight 지수 계산
    result_df["gt_rate"] = result_df["gt_wt_pass_rate"]
    result_df["gt_idx"] = calculate_index(
        result_df["gt_rate"], QUALITY_INDICES_CONFIG["gt_weight"]
    )

    # RR 지수 계산
    result_df["rr_idx"] = calculate_index(
        result_df["rr_pass_rate_pdf"], QUALITY_INDICES_CONFIG["rr"]
    )

    # CTL 지수 계산
    result_df["ctl_idx"] = calculate_index(
        result_df["ctl_pass_rate"], QUALITY_INDICES_CONFIG["ctl"]
    )

    # 지수 평균
    # None 값이 아닌 지수들만 평균 계산
    valid_indices = result_df[
        ["ncf_idx", "uf_idx", "gt_idx", "rr_idx", "ctl_idx"]
    ].notna()
    result_df["total_idx"] = (
        result_df["ncf_idx"].where(valid_indices["ncf_idx"], 0)
        + result_df["uf_idx"].where(valid_indices["uf_idx"], 0)
        + result_df["gt_idx"].where(valid_indices["gt_idx"], 0)
        + result_df["rr_idx"].where(valid_indices["rr_idx"], 0)
        + result_df["ctl_idx"].where(valid_indices["ctl_idx"], 0)
    ) / valid_indices.sum(axis=1)

    result_df["uf_pass_rate"] = result_df["uf_pass_rate"] * 100
    result_df["gt_wt_pass_rate"] = result_df["gt_wt_pass_rate"] * 100
    result_df["rr_pass_rate_pdf"] = result_df["rr_pass_rate_pdf"] * 100
    result_df["ctl_pass_rate"] = result_df["ctl_pass_rate"] * 100

    return result_df


def calculate_cqms_n_filed_return(result_df: pd.DataFrame):
    mcode_list = result_df["m_code"].tolist()

    unified_cqms_df = get_cqms_unified_df(mcode_list)
    unified_cqms_df = unified_cqms_df.pivot_table(
        index="M_CODE",
        columns="CATEGORY",
        aggfunc="size",
    )
    unified_cqms_df = unified_cqms_df.reset_index()
    unified_cqms_df = unified_cqms_df.rename(columns={"M_CODE": "m_code"})
    result_df = pd.merge(
        result_df,
        unified_cqms_df,
        on="m_code",
        how="left",
    )
    result_df["Quality Issue"] = result_df["Quality Issue"].fillna(value=0)
    result_df["4M Change"] = result_df["4M Change"].fillna(value=0)
    result_df["Audit"] = result_df["Audit"].fillna(value=0)

    hgws_df = get_hgws_df(mcode_list)
    hgws_df = hgws_df.groupby("MCODE").agg({"RETURN CNT": "sum"}).reset_index()
    hgws_df = hgws_df.rename(columns={"MCODE": "m_code", "RETURN CNT": "Field Return"})
    result_df = pd.merge(
        result_df,
        hgws_df,
        on="m_code",
        how="left",
    )
    result_df["Field Return"] = result_df["Field Return"].fillna(value=0)
    return result_df


def format_date_string(date_str: str) -> str:
    """
    날짜 문자열을 YYYY-MM-DD 형식으로 변환

    Args:
        date_str: YYYYMMDD 형식의 날짜 문자열

    Returns:
        YYYY-MM-DD 형식의 날짜 문자열

    Raises:
        ValueError: 날짜 문자열 형식이 올바르지 않은 경우
        IndexError: 날짜 문자열 길이가 8자리가 아닌 경우
    """
    if not date_str or len(date_str) != 8:
        raise ValueError("날짜 문자열은 8자리여야 합니다 (YYYYMMDD)")

    try:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    except IndexError:
        raise ValueError("날짜 문자열 형식이 올바르지 않습니다")


# session state에 기록된 data
def get_selected_data_info(
    result_df: pd.DataFrame, selected_row_index: int
) -> Dict[str, str]:
    """
    선택된 행의 데이터 정보를 추출

    Args:
        result_df: Assessment 결과 데이터프레임
        selected_row_index: 선택된 행 인덱스

    Returns:
        선택된 데이터 정보 딕셔너리
            - mcode: 모델 코드
            - start_date: 시작 날짜 (YYYYMMDD)
            - end_date: 종료 날짜 (YYYYMMDD)
            - formatted_start_date: 포맷된 시작 날짜 (YYYY-MM-DD)
            - formatted_end_date: 포맷된 종료 날짜 (YYYY-MM-DD)

    Raises:
        IndexError: 선택된 행 인덱스가 범위를 벗어난 경우
        KeyError: 필수 컬럼이 없는 경우
    """
    if selected_row_index >= len(result_df):
        raise IndexError("선택된 행 인덱스가 데이터프레임 범위를 벗어났습니다")

    selected_row = result_df.iloc[selected_row_index]

    # 필수 컬럼 검증
    required_columns = ["m_code", "min_date", "max_date"]
    missing_columns = [col for col in required_columns if col not in selected_row.index]
    if missing_columns:
        raise KeyError(f"필수 컬럼이 없습니다: {missing_columns}")

    return {
        "mcode": selected_row["m_code"],
        "start_date": selected_row["min_date"],
        "end_date": selected_row["max_date"],
        "formatted_start_date": format_date_string(selected_row["min_date"]),
        "formatted_end_date": format_date_string(selected_row["max_date"]),
    }


# Expender 상태 평가 정의 함수
def get_quality_status_indicator(idx_value: float) -> Tuple[str, str]:
    """
    품질 지표의 상태를 3단계로 시각적으로 표시하는 함수

    Args:
        idx_value: 품질 지수 값

    Returns:
        (상태 텍스트, 상태 레벨) 튜플
            - 상태 텍스트: "Excellent", "Warning", "Critical"
            - 상태 레벨: "blue", "orange", "red"

    상태 기준:
        - >= 80: Excellent (blue)
        - >= 50: Warning (orange)
        - < 50: Critical (red)
    """
    if idx_value >= UI_CONFIG["status_thresholds"]["excellent"]:
        status_text = "Excellent"
        status_level = "blue"
    elif idx_value >= UI_CONFIG["status_thresholds"]["warning"]:
        status_text = "Warning"
        status_level = "orange"
    else:
        status_text = "Critical"
        status_level = "red"

    return status_text, status_level


# =============================================================================
# Streamlit Tab 호출 함수
# =============================================================================
def render_overview_tab(result_df: pd.DataFrame) -> None:
    """
    Overview 탭 렌더링

    Args:
        result_df: Assessment 결과 데이터프레임
    """

    render_matric_info(result_df)
    render_status_indicator(result_df)


def render_detail_tab(result_df: pd.DataFrame) -> None:
    """
    Detail 탭 렌더링

    Args:
        result_df: Assessment 결과 데이터프레임
    """
    if "result_df" not in st.session_state:
        st.session_state["result_df"] = result_df

    with st.expander(
        "Assessment Detail Table", expanded=True, icon=":material/table_chart:"
    ):
        assessment_result_df = render_main_table_for_detail_tab(result_df)

    # assessment_result_df가 None인 경우 처리
    if assessment_result_df is None:
        st.error("테이블을 불러올 수 없습니다. 데이터를 확인해주세요.")
        return

    # 선택된 행 처리
    if (
        hasattr(assessment_result_df, "selection")
        and assessment_result_df.selection.rows
    ):
        selected_data = get_selected_data_info(
            result_df, assessment_result_df.selection.rows[0]
        )

        render_search_criteria_section(selected_data)
        render_project_info_section(selected_data)
        render_assessment_insight(selected_data)

        # 각 분석 섹션 렌더링
        st.markdown(
            f"#### :material/analytics: **:grey[Production Analysis]**",
        )
        production_col = st.columns([0.5, 10], vertical_alignment="center")
        with production_col[1]:
            render_production_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )
            render_ncf_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )
            render_uf_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )
            render_weight_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )
            render_rr_section(
                selected_data["mcode"],
                selected_data["formatted_start_date"],
                selected_data["formatted_end_date"],
                result_df,
            )
            render_ctl_section(
                selected_data["mcode"],
                selected_data["start_date"],
                selected_data["end_date"],
                result_df,
            )

    else:
        st.warning(
            "Please select a row from the assessment result table to view detailed analysis."
        )


@handle_ui_rendering_errors
def render_description_tab() -> None:
    """
    Description 탭 렌더링
    """
    st.title("Detail")

    try:
        with open("_07_docs/product_assessment.md", "r", encoding="utf-8") as file:
            markdown_content = file.read()
        st.markdown(markdown_content)
    except FileNotFoundError:
        st.error("product_assessment.md 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {str(e)}")


# =============================================================================
# UI 섹션 함수들 - Overview Tab
# =============================================================================


def render_matric_info(result_df: pd.DataFrame) -> None:
    n_target = len(result_df)
    st.subheader(f"대상 규격 수 : :grey[{n_target}개]")
    total_idx_avg = result_df["total_idx"].mean()
    st.subheader(f"Total Index 평균 : :grey[{total_idx_avg:.2f}]")

    mcode_list = result_df["m_code"].tolist()

    # 4M 변경
    df_4m_change = get_4m_change_detail_df(mcode_list)

    merge_4m_change = pd.merge(
        left=result_df[["m_code", "start_mass_production"]],
        right=df_4m_change,
        left_on="m_code",
        right_on="M_CODE",
        how="left",
    )
    merge_4m_change["end_mass_production"] = merge_4m_change[
        "start_mass_production"
    ] + pd.Timedelta(days=365)
    merge_4m_change = merge_4m_change.dropna(subset=["DOC_NO"])
    merge_4m_change["Include"] = merge_4m_change.apply(
        lambda row: (
            "Include"
            if pd.notna(row["COMP_DATE"])
            and pd.notna(row["end_mass_production"])
            and row["COMP_DATE"] < row["end_mass_production"]
            else "Exclude"
        ),
        axis=1,
    )
    merge_4m_change = merge_4m_change[merge_4m_change["Include"] == "Include"]
    merge_4m_change = merge_4m_change[
        ~(merge_4m_change["STATUS"] == "Reject(Final Approval)")
    ]
    count_4m_change = len(merge_4m_change)
    st.subheader(f"4M 변경건수 : :grey[{count_4m_change}]")

    st.dataframe(merge_4m_change)

    # 품질이슈
    df_quality_issue = get_quality_issue_df_detail(mcode_list)
    merge_quality_issue = pd.merge(
        left=result_df[["m_code", "start_mass_production"]],
        right=df_quality_issue,
        left_on="m_code",
        right_on="M_CODE",
        how="left",
    )
    merge_quality_issue["end_mass_production"] = merge_quality_issue[
        "start_mass_production"
    ] + pd.Timedelta(days=365)
    merge_quality_issue["Include"] = merge_quality_issue.apply(
        lambda row: (
            "Include"
            if pd.notna(row["COMP_DATE"])
            and pd.notna(row["end_mass_production"])
            and row["COMP_DATE"] < row["end_mass_production"]
            else "Exclude"
        ),
        axis=1,
    )
    merge_quality_issue = merge_quality_issue[
        merge_quality_issue["Include"] == "Include"
    ]
    merge_quality_issue = merge_quality_issue[
        ~(merge_quality_issue["STATUS"] == "Reject(Final Approval)")
    ]
    count_quality_issue = len(merge_quality_issue)
    st.subheader(f"품질이슈건수 : :grey[{count_quality_issue}]")

    st.dataframe(merge_quality_issue)


def render_status_indicator(result_df: pd.DataFrame) -> None:
    col = st.columns(4, vertical_alignment="center")

    groupby_yyyymm = result_df.groupby("YYYYMM").agg({"m_code": "count"}).reset_index()
    trace = go.Bar(
        x=groupby_yyyymm["YYYYMM"],
        y=groupby_yyyymm["m_code"],
        text=groupby_yyyymm["m_code"],
        textposition="outside",
    )
    layout = go.Layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=20),
    )
    fig = go.Figure(data=[trace], layout=layout)
    col[0].plotly_chart(fig, use_container_width=True)

    groupby_status = result_df.groupby("status").agg({"m_code": "count"}).reset_index()
    trace = go.Pie(
        labels=groupby_status["status"],
        values=groupby_status["m_code"],
        direction="clockwise",
        textinfo="label+value",
        textposition="inside",
    )
    layout = go.Layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=20),
    )
    fig = go.Figure(data=[trace], layout=layout)
    col[1].plotly_chart(fig, use_container_width=True)

    groupby_plant = result_df.groupby("plant").agg({"m_code": "count"}).reset_index()
    trace = go.Pie(
        labels=groupby_plant["plant"],
        values=groupby_plant["m_code"],
        direction="clockwise",
        textinfo="label+value",
        textposition="inside",
    )
    layout = go.Layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=20),
    )
    fig = go.Figure(data=[trace], layout=layout)
    col[2].plotly_chart(fig, use_container_width=True)

    groupby_oem = result_df.groupby("oem").agg({"m_code": "count"}).reset_index()
    trace = go.Pie(
        labels=groupby_oem["oem"],
        values=groupby_oem["m_code"],
        direction="clockwise",
        textinfo="label+value",
        textposition="inside",
    )
    layout = go.Layout()
    fig = go.Figure(data=[trace], layout=layout)
    col[3].plotly_chart(fig, use_container_width=True)


# =============================================================================
# UI 섹션 함수들 - Detail Tab
# =============================================================================


def render_main_table_for_detail_tab(result_df: pd.DataFrame):
    """
    Detail 탭의 메인 테이블을 렌더링하는 함수

    Args:
        result_df: Assessment 결과 데이터프레임

    Returns:
        Streamlit dataframe 객체 또는 None (오류 발생 시)
    """
    try:
        show_full_table = st.toggle("Show Full Table", value=False)
        if show_full_table:
            remain_columns = [
                "year",
                "m_code",
                "plant",
                "oem",
                "vehicle",
                "min_date",
                "max_date",
                "total_qty",
                "ncf_qty",
                "ncf_rate",
                "ncf_idx",
                "uf_pass_rate",
                "uf_idx",
                "gt_wt_pass_rate",
                "gt_idx",
                "rr_pass_rate_pdf",
                "rr_idx",
                "ctl_pass_rate",
                "ctl_idx",
                "total_idx",
                "Quality Issue",
                "4M Change",
                "Audit",
                "Field Return",
            ]
        else:
            remain_columns = [
                "year",
                "m_code",
                "plant",
                "oem",
                "vehicle",
                "min_date",
                "max_date",
                "total_qty",
                "ncf_idx",
                "uf_idx",
                "gt_idx",
                "rr_idx",
                "ctl_idx",
                "total_idx",
                "Quality Issue",
                "4M Change",
                "Audit",
                "Field Return",
            ]

        # 존재하는 컬럼만 필터링
        remain_columns = [col for col in remain_columns if col in result_df.columns]

        # pandas 스타일링 적용
        styled_df = (
            result_df[remain_columns]
            .style.set_properties(
                subset=[
                    "ncf_idx",
                    "uf_idx",
                    "gt_idx",
                    "rr_idx",
                    "ctl_idx",
                    "total_idx",
                ],
                **{
                    "background-color": f"{config_plotly.LIGHT_GRAY_CLR}",
                    "text-align": "center",
                    "font-size": "12px",
                    "border": "1px solid #ddd",
                },
            )
            .applymap(
                multi_condition_style,
                subset=[
                    "ncf_idx",
                    "uf_idx",
                    "gt_idx",
                    "rr_idx",
                    "ctl_idx",
                    "total_idx",
                ],
            )
        )

        column_config = {
            "year": st.column_config.TextColumn("Year", width="small"),
            "m_code": st.column_config.TextColumn("M-Code", width="small"),
            "plant": st.column_config.TextColumn("Plant", width="small"),
            "oem": st.column_config.TextColumn("OEM", width="small"),
            "vehicle": st.column_config.TextColumn("Vehicle", width="small"),
            "min_date": st.column_config.TextColumn(
                "Start",
                help="Mass Production Start Date",
                width="small",
            ),
            "max_date": st.column_config.TextColumn(
                "End",
                help="Mass Production End Date",
                width="small",
            ),
            "total_qty": st.column_config.NumberColumn(
                "Total Qty", width="small", format="%.0f"
            ),
            "ncf_qty": st.column_config.NumberColumn(
                "NCF Qty", width="small", format="%.0f"
            ),
            "ncf_rate": st.column_config.NumberColumn("NCF(ppm)", format="%.0f ppm"),
            "ncf_idx": st.column_config.NumberColumn(
                "NCF Index", width="small", format="%.0f"
            ),
            "uf_pass_rate": st.column_config.NumberColumn("UF(%)", format="%.1f%%"),
            "uf_idx": st.column_config.NumberColumn(
                "UF Index", width="small", format="%.0f"
            ),
            "gt_wt_pass_rate": st.column_config.NumberColumn(
                "GT(%)", width="small", format="%.1f%%"
            ),
            "gt_idx": st.column_config.NumberColumn(
                "GT Index", width="small", format="%.0f"
            ),
            "rr_pass_rate_pdf": st.column_config.NumberColumn(
                "RR(%)", width="small", format="%.1f%%"
            ),
            "rr_idx": st.column_config.NumberColumn(
                "RR Index", width="small", format="%.0f"
            ),
            "ctl_pass_rate": st.column_config.NumberColumn(
                "CTL(%)", width="small", format="%.1f%%"
            ),
            "ctl_idx": st.column_config.NumberColumn(
                "CTL Index", width="small", format="%.0f"
            ),
            "total_idx": st.column_config.NumberColumn(
                "Total Index", width="small", format="%.0f"
            ),
            "Quality Issue": st.column_config.NumberColumn(
                "Quality Issue", width="small", format="%.0f"
            ),
            "4M Change": st.column_config.NumberColumn(
                "4M Change", width="small", format="%.0f"
            ),
            "Audit": st.column_config.NumberColumn(
                "Audit", width="small", format="%.0f"
            ),
            "Field Return": st.column_config.NumberColumn(
                "Field Return", width="small", format="%.0f"
            ),
        }

        # 데이터프레임 표시
        assessment_result_df = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            key="event_df",
            on_select="rerun",
            selection_mode="single-row",
        )
        return assessment_result_df

    except Exception as e:
        logger.error(f"메인 테이블 렌더링 중 오류 발생: {str(e)}")
        st.error(f"테이블 렌더링 중 오류가 발생했습니다: {str(e)}")
        return None


@handle_section_rendering_errors
def render_search_criteria_section(selected_data):
    markdown = f"""
            <div class="card-container">
                <h3><span class="material-symbols-rounded">feature_search</span> Search Criteria Information</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>M-Code:</strong><br>
                        <span style="font-size: 1.2rem; font-weight: bold;">{selected_data['mcode']}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>Start Date:</strong><br>
                        <span style="font-size: 1.2rem;">{selected_data['formatted_start_date']}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                        <strong>End Date:</strong><br>
                        <span style="font-size: 1.2rem;">{selected_data['formatted_end_date']}</span>
                    </div>
                </div>
            </div>
            """
    st.markdown(
        markdown,
        unsafe_allow_html=True,
    )


@handle_section_rendering_errors
def render_project_info_section(selected_data):
    oeapp_df = load_oeapp_df_by_mcode(m_code=selected_data["mcode"])

    # SOP, EOP 날짜 형식 변환 (YYYYMM -> YYYY-MM 형태의 문자열로 변환)
    if not oeapp_df.empty:
        for date_col in ["SOP", "EOP"]:
            if date_col in oeapp_df.columns:
                oeapp_df[date_col] = oeapp_df[date_col].apply(
                    lambda x: (
                        f"{str(x)[:4]}-{str(x)[4:6]}"
                        if pd.notna(x) and str(x) != "nan" and len(str(x)) == 6
                        else x
                    )
                )

    st.markdown(f"#### :material/info: **:grey[Project Information]**")
    if not oeapp_df.empty:
        project_info_col = st.columns([0.5, 10], vertical_alignment="center")
        # 규격 정보
        project_info_col[1].markdown(
            f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>Plant:</strong><br>
                <span style="font-size: 1.2rem;">{oeapp_df.iloc[0]['PLANT']}</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>Size:</strong><br>
                <span style="font-size: 1.2rem;">{oeapp_df.iloc[0]['SIZE']}</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>Pattern:</strong><br>
                <span style="font-size: 1.2rem;">{oeapp_df.iloc[0]['PATTERN']}</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>Product Name:</strong><br>
                <span style="font-size: 1.2rem;">{oeapp_df.iloc[0]['PROD NAME']}</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>EV / ICE :</strong><br>
                <span style="font-size: 1.2rem;">{oeapp_df.iloc[0]['EV']}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 프로젝트 정보
        oe_app_info_col = st.columns([0.5, 1, 9], vertical_alignment="center")
        oe_app_info_col[1].markdown(f"###### **:grey[OE App]**")

        remain_col = [
            "STATUS",
            "CAR MAKER",
            "SALES BRAND",
            "VEHICLE MODEL(GLOBAL)",
            # "VEHICLE MODEL(LOCAL)",
            "PROJECT",
            "SOP",
            "EOP",
        ]
        column_config = {
            "STATUS": st.column_config.TextColumn("Status", width="small"),
            "CAR MAKER": st.column_config.TextColumn("Car Maker", width="small"),
            "SALES BRAND": st.column_config.TextColumn("Sales Brand", width="small"),
            "VEHICLE MODEL(GLOBAL)": st.column_config.TextColumn(
                "Vehicle Model", width="medium"
            ),
            "PROJECT": st.column_config.TextColumn("Project", width="small"),
            "SOP": st.column_config.TextColumn("SOP", width="small"),
            "EOP": st.column_config.TextColumn("EOP", width="small"),
        }
        oe_app_info_col[2].dataframe(
            oeapp_df[remain_col],
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )
    else:
        st.info("No OE Application data available for the selected model code.")

    metric_title_col = st.columns([0.5, 6, 4], vertical_alignment="center")
    metric_title_col[1].markdown(f"###### **:grey[OEM Event]**")
    metric_title_col[2].markdown(f"###### **:grey[Field Return]**")

    metric_col = st.columns([0.5, 6, 4], vertical_alignment="center")
    cqms_unified_df = get_cqms_unified_df(m_code=selected_data["mcode"])
    groupby_cqms_unified_df = (
        cqms_unified_df.groupby("CATEGORY")
        .agg(Count=("CATEGORY", "count"))
        .reset_index()
    )

    with metric_col[1]:
        cqms_col = st.columns(3)

        cqms_col[0].metric(
            label="Quality Issue",
            value=(
                groupby_cqms_unified_df[
                    groupby_cqms_unified_df["CATEGORY"] == "Quality Issue"
                ]["Count"].values[0]
            ),
            delta=None,
        )
        cqms_col[1].metric(
            label="4M Change",
            value=(
                groupby_cqms_unified_df[
                    groupby_cqms_unified_df["CATEGORY"] == "4M Change"
                ]["Count"].values[0]
            ),
            delta=None,
        )
        cqms_col[2].metric(
            label="Audit",
            value=(
                groupby_cqms_unified_df[groupby_cqms_unified_df["CATEGORY"] == "Audit"][
                    "Count"
                ].values[0]
            ),
            delta=None,
        )
    with metric_col[2]:
        hgws_df = get_hgws_df(m_code=selected_data["mcode"])
        hgws_df = hgws_df.sort_values(by="RETURN CNT", ascending=False)
        if not hgws_df.empty:
            trace = go.Bar(
                x=hgws_df["RETURN CNT"],
                y=hgws_df["REASON DESCRIPTION"],
                text=hgws_df["RETURN CNT"],
                textposition="outside",
                marker=dict(color=config_plotly.ORANGE_CLR),
                orientation="h",
            )
            layout = go.Layout(
                xaxis=dict(
                    title="Field Return Count",
                    range=[0, max(hgws_df["RETURN CNT"]) + 1],
                    visible=False,
                ),
                yaxis=dict(title="Reason Description", autorange="reversed"),
                height=150,
                margin=dict(l=0, r=0, t=20, b=20),
            )
            fig = go.Figure(data=[trace], layout=layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("### :grey[No Field Return]")
    oem_event_col_detail = st.columns([0.5, 10], vertical_alignment="center")
    with oem_event_col_detail[1].expander("Detail", expanded=False):
        if len(cqms_unified_df) > 0:
            st.dataframe(cqms_unified_df, use_container_width=True, hide_index=True)
        else:
            st.info("### :grey[No OEM Event]")
        if len(hgws_df) > 0:
            st.dataframe(hgws_df, use_container_width=True, hide_index=True)
        else:
            st.info("### :grey[No Field Return]")


@handle_section_rendering_errors
def render_assessment_insight(selected_data: Dict[str, Any]) -> None:
    """
    Assessment Insight 섹션 렌더링

    Args:
        selected_data: 선택된 데이터 정보를 담은 딕셔너리
    """
    insight_df = get_client("sqlite").execute(
        f"SELECT * FROM mass_assess_insight WHERE M_CODE = '{selected_data['mcode']}'"
    )

    # Insight 섹션 헤더
    st.markdown(f"#### :material/lightbulb: **:grey[Assessment Insights]**")

    # 상태에 따른 색상 스타일 가져오기

    if not insight_df.empty:
        # Status와 Insight 데이터 추출
        status = str(insight_df.iloc[0]["Status"])
        insight = str(insight_df.iloc[0]["Insight"])
        bg_color, border_color, text_color = get_insight_status_style(status)

        # Insight 섹션 레이아웃
        insight_col = st.columns([0.5, 2, 0.5, 7.5], vertical_alignment="center")

        # Status 표시 (왼쪽 컬럼)
        with insight_col[1]:
            st.markdown(
                f"""
                <div style="
                    background: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 12px;
                    padding: 1.5rem;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                ">
                    <div style="
                        font-size: 1.2rem;
                        font-weight: 600;
                        color: {text_color};
                        margin: 0;
                    ">{status}</div>
                """,
                unsafe_allow_html=True,
            )

        # Insight 표시 (오른쪽 컬럼)
        with insight_col[3]:
            st.markdown(
                insight,
                unsafe_allow_html=True,
            )
    else:
        # 데이터가 없는 경우
        insight_col = st.columns([0.5, 10], vertical_alignment="center")
        insight_col[1].markdown(
            f"""
            <div class="section-card">
                <div style="text-align: center; padding: 1rem;">
                    <p style="color: #9ca3af; margin: 0;">No Assessment Insights Available</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


@handle_section_rendering_errors
def render_production_section(
    selected_mcode: str,
    selected_start_date: str,
    selected_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    생산량 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        selected_start_date: 선택된 시작 날짜
        selected_end_date: 선택된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    production_df = get_daily_production_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
    total_production = result_df[result_df["m_code"] == selected_mcode][
        "total_qty"
    ].values[0]

    with st.expander(
        f"Total Production : {total_production:,.0f} ea",
        icon=":material/factory:",
        expanded=False,
    ):
        st.plotly_chart(
            viz.draw_barplot_production(production_df), use_container_width=True
        )


@handle_section_rendering_errors
def render_ncf_section(
    selected_mcode: str,
    selected_start_date: str,
    selected_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    NCF 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        selected_start_date: 선택된 시작 날짜
        selected_end_date: 선택된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    ncf_df = get_ncf_monthly_df(
        mcode=selected_mcode,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
    ncf_ppm = result_df[result_df["m_code"] == selected_mcode]["ncf_rate"].values[0]
    ncf_idx = result_df[result_df["m_code"] == selected_mcode]["ncf_idx"].values[0]

    # 3단계 상태 평가 (NCF는 높을수록 나쁨 - reverse=True)
    status_text, status_level = get_quality_status_indicator(ncf_idx)

    # 상태 표시 텍스트 생성 (색상 적용)
    status_text_display = f"**:{status_level}[{status_text} - {ncf_idx:,.0f}p]**"

    with st.expander(
        f"Non-Conformance Finding : {ncf_ppm:,.0f} ppm | {status_text_display}",
        icon=":material/problem:",
        expanded=False,
    ):
        # Download Button
        ncf_download_col = st.columns([8, 1])
        ncf_detail_df = get_ncf_detail(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        converted_ncf_detail_df = convert_for_download(ncf_detail_df)
        ncf_download_col[1].download_button(
            label="Download CSV",
            data=converted_ncf_detail_df,
            file_name=f"{selected_mcode}_ncf_detail.csv",
            type="tertiary",
            mime="text/csv",
            icon=":material/download:",
            use_container_width=True,
        )

        # 상태에 따른 배경색 변경을 위한 컨테이너
        ncf_cols = st.columns(2)

        ncf_cols[0].plotly_chart(viz.draw_barplot_ncf(ncf_df), use_container_width=True)

        ncf_by_dft_cd_df = get_ncf_by_dft_cd(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        ncf_cols[1].plotly_chart(
            viz.draw_barplot_ncf_pareto(ncf_by_dft_cd_df), use_container_width=True
        )


@handle_section_rendering_errors
def render_uf_section(
    selected_mcode: str,
    selected_start_date: str,
    selected_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    UF 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        selected_start_date: 선택된 시작 날짜
        selected_end_date: 선택된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    uf_pass_rate = result_df[result_df["m_code"] == selected_mcode][
        "uf_pass_rate"
    ].values[0]
    uf_idx = result_df[result_df["m_code"] == selected_mcode]["uf_idx"].values[0]

    # 3단계 상태 평가 (UF Pass Rate는 높을수록 좋음 - reverse=False)
    status_text, status_level = get_quality_status_indicator(uf_idx)

    # 상태 표시 텍스트 생성 (색상 적용)
    status_text_display = f"**:{status_level}[{status_text} - {uf_idx:,.0f}p]**"

    with st.expander(
        f"Uniformity Pass Rate : {uf_pass_rate:,.1f} % | {status_text_display}",
        icon=":material/adjust:",
        expanded=False,
    ):
        uf_individual_df = uf_individual(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        # Download Button
        uf_download_col = st.columns([8, 1])

        converted_uf_detail_df = convert_for_download(uf_individual_df)
        uf_download_col[1].download_button(
            label="Download CSV",
            data=converted_uf_detail_df,
            file_name=f"{selected_mcode}_uf_detail.csv",
            type="tertiary",
            mime="text/csv",
            icon=":material/download:",
            use_container_width=True,
        )

        # 상태에 따른 배경색 변경을 위한 컨테이너
        uf_cols = st.columns(2)

        uf_pass_rate_df = calculate_uf_pass_rate_monthly(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        uf_cols[0].plotly_chart(
            viz.draw_barplot_uf(uf_pass_rate_df), use_container_width=True
        )

        uf_standard_df = uf_standard(mcode=selected_mcode)

        uf_cols[1].plotly_chart(
            viz.draw_barplot_uf_individual(uf_individual_df, uf_standard_df),
            use_container_width=True,
        )


@handle_section_rendering_errors
def render_weight_section(
    selected_mcode: str,
    selected_start_date: str,
    selected_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    중량 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        selected_start_date: 선택된 시작 날짜
        selected_end_date: 선택된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    wt_pass_rate = result_df[result_df["m_code"] == selected_mcode][
        "gt_wt_pass_rate"
    ].values[0]
    wt_idx = result_df[result_df["m_code"] == selected_mcode]["gt_idx"].values[0]

    # 3단계 상태 평가 (Weight Pass Rate는 높을수록 좋음 - reverse=False)
    status_text, status_level = get_quality_status_indicator(wt_idx)

    # 상태 표시 텍스트 생성 (색상 적용)
    status_text_display = f"**:{status_level}[{status_text} - {wt_idx:,.0f}p]**"

    with st.expander(
        f"GT Weight Pass Rate : {wt_pass_rate:,.1f} % | {status_text_display}",
        expanded=False,
        icon=":material/weight:",
    ):
        wt_individual_df = get_weight_individual_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        # Download Button
        wt_download_col = st.columns([8, 1])
        converted_wt_detail_df = convert_for_download(wt_individual_df)
        wt_download_col[1].download_button(
            label="Download CSV",
            data=converted_wt_detail_df,
            file_name=f"{selected_mcode}_wt_detail.csv",
            type="tertiary",
            mime="text/csv",
            icon=":material/download:",
            use_container_width=True,
        )

        wt_col = st.columns(2)

        groupby_weight_ym_df = get_groupby_weight_ym_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )
        wt_col[0].plotly_chart(
            viz.draw_weight_distribution(groupby_weight_ym_df), use_container_width=True
        )

        wt_individual_df_no_outliers = (
            wt_individual_df.groupby("INS_DATE_YM")
            .apply(remove_outliers)
            .reset_index(drop=True)
        )

        wt_spec = wt_individual_df["STD_WGT"].iloc[-1]

        wt_col[1].plotly_chart(
            viz.draw_weight_distribution_individual(
                wt_individual_df_no_outliers, wt_spec
            ),
            use_container_width=True,
        )


@handle_section_rendering_errors
def render_rr_section(
    selected_mcode: str,
    formatted_start_date: str,
    formatted_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    RR 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        formatted_start_date: 포맷된 시작 날짜
        formatted_end_date: 포맷된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    rr_pass_rate = result_df[result_df["m_code"] == selected_mcode][
        "rr_pass_rate_pdf"
    ].values[0]
    rr_idx = result_df[result_df["m_code"] == selected_mcode]["rr_idx"].values[0]

    # 3단계 상태 평가 (RR Pass Rate는 높을수록 좋음 - reverse=False)
    status_text, status_level = get_quality_status_indicator(rr_idx)

    # 상태 표시 텍스트 생성 (색상 적용)
    status_text_display = f"**:{status_level}[{status_text} - {rr_idx:,.0f}p]**"

    with st.expander(
        f"RR Pass Rate : {rr_pass_rate:,.1f} % | {status_text_display}",
        expanded=False,
        icon=":material/tire_repair:",
    ):
        # 상태에 따른 배경색 변경을 위한 컨테이너

        rr_df = get_processed_raw_rr_data(
            mcode=selected_mcode,
            start_date=formatted_start_date,
            end_date=formatted_end_date,
        )
        rr_df = rr_df.sort_values(by="SMPL_DATE").reset_index(drop=True)

        rr_standard_df = get_rr_oe_list_df()
        rr_standard_df = rr_standard_df[rr_standard_df["M_CODE"] == selected_mcode]

        # Download Button
        rr_download_col = st.columns([8, 1])
        converted_rr_detail_df = convert_for_download(rr_df)
        rr_download_col[1].download_button(
            label="Download CSV",
            data=converted_rr_detail_df,
            file_name=f"{selected_mcode}_rr_detail.csv",
            type="tertiary",
            mime="text/csv",
            icon=":material/download:",
            use_container_width=True,
        )

        rr_col = st.columns(2)

        if len(rr_df) > 0:
            rr_col[0].plotly_chart(
                viz.draw_rr_trend(rr_df, rr_standard_df), use_container_width=True
            )
            rr_col[1].plotly_chart(
                viz.draw_rr_distribution(rr_df, rr_standard_df),
                use_container_width=True,
            )
        else:
            st.warning("No RR data found")


@handle_section_rendering_errors
def render_ctl_section(
    selected_mcode: str,
    selected_start_date: str,
    selected_end_date: str,
    result_df: pd.DataFrame,
) -> None:
    """
    CTL 분석 섹션 렌더링

    Args:
        selected_mcode: 선택된 모델 코드
        selected_start_date: 선택된 시작 날짜
        selected_end_date: 선택된 종료 날짜
        result_df: Assessment 결과 데이터프레임
    """
    ctl_pass_rate = result_df[result_df["m_code"] == selected_mcode][
        "ctl_pass_rate"
    ].values[0]
    ctl_idx = result_df[result_df["m_code"] == selected_mcode]["ctl_idx"].values[0]

    status_text, status_level = get_quality_status_indicator(ctl_idx)

    with st.expander(
        f"CTL Pass Rate : {ctl_pass_rate:,.1f} % | **:{status_level}[{status_text} - {ctl_idx:,.0f}p]**",
        expanded=False,
        icon=":material/straighten:",
    ):

        ctl_raw_data = df_ctl.get_ctl_raw_individual_df(
            mcode=selected_mcode,
            start_date=selected_start_date,
            end_date=selected_end_date,
        )

        # Download Button
        ctl_download_col = st.columns([8, 1])
        converted_ctl_detail_df = convert_for_download(ctl_raw_data)
        ctl_download_col[1].download_button(
            label="Download CSV",
            data=converted_ctl_detail_df,
            file_name=f"{selected_mcode}_ctl_detail.csv",
            type="tertiary",
            mime="text/csv",
            icon=":material/download:",
            use_container_width=True,
        )

        ctl_raw_data["JDG"] = pd.Categorical(
            ctl_raw_data["JDG"], categories=["OK", "NI", "NO"]
        )
        ctl_col = st.columns(3, vertical_alignment="center", gap="large")
        if len(ctl_raw_data) > 0:
            grouped_ctl_df = df_ctl.get_groupby_doc_ctl_df(
                mcode=selected_mcode,
                start_date=selected_start_date,
                end_date=selected_end_date,
            )
            ctl_col[0].plotly_chart(
                viz.draw_ctl_trend(grouped_ctl_df), use_container_width=True
            )
            MRM_PASS_RATE = (
                ctl_raw_data.pivot_table(
                    index="MRM_ITEM",
                    columns="JDG",
                    values="DOC_NO",
                    aggfunc="count",
                )
                .reset_index()
                .fillna(0)
            )
            MRM_PASS_RATE["PASS_RATE"] = MRM_PASS_RATE["OK"] / (
                MRM_PASS_RATE["NI"] + MRM_PASS_RATE["OK"]
            )
            NO_MRM_ITEMS = MRM_PASS_RATE[MRM_PASS_RATE["PASS_RATE"].isna()][
                "MRM_ITEM"
            ].tolist()
            MRM_ITEMS = MRM_PASS_RATE[~MRM_PASS_RATE["PASS_RATE"].isna()][
                "MRM_ITEM"
            ].tolist()

            MRM_PASS_RATE = MRM_PASS_RATE[~MRM_PASS_RATE["MRM_ITEM"].isin(NO_MRM_ITEMS)]

            # Pass Rate가 0-1 범위이므로 가독성을 위해 퍼센트로 변환
            pass_rate_pct = MRM_PASS_RATE["PASS_RATE"] * 100

            # N/A 값 처리 (0으로 나누기 등으로 인한 NaN)
            pass_rate_pct = pass_rate_pct.fillna(0)

            # 가로 막대 차트로 변경 (항목명이 길 수 있으므로)
            trace = go.Bar(
                x=MRM_PASS_RATE["MRM_ITEM"],  # y축에 항목명
                y=pass_rate_pct,  # x축에 합격률
                marker=dict(
                    color=config_plotly.GRAY_CLR,
                ),
                text=[f"{rate:.0f}%" for rate in pass_rate_pct],  # 값 표시
                textposition="auto",
            )

            layout = go.Layout(
                title="Pass Rate by Measurement Items",
                xaxis=dict(
                    title="Pass Rate (%)",
                ),  # 0-100% 범위 고정
                yaxis=dict(title="Measurement Items", range=[0, 100]),
                height=400,  # 가로 막대는 높이를 늘려서 가독성 향상
            )

            fig = go.Figure(data=trace, layout=layout)
            ctl_col[1].plotly_chart(fig)
            ctl_col[1].markdown(f"**No Measurement Items** : {', '.join(NO_MRM_ITEMS)}")

            selected_mrm_item = ctl_col[2].selectbox(
                "Select Measurement Item",
                options=MRM_ITEMS,
                index=0,
            )
            if selected_mrm_item:
                ctl_raw_data = ctl_raw_data[
                    ctl_raw_data["MRM_ITEM"] == selected_mrm_item
                ]
                UPPER = ctl_raw_data[ctl_raw_data["SIDE"] == "UPPER"]
                LOWER = ctl_raw_data[ctl_raw_data["SIDE"] == "LOWER"]

                trace1 = go.Scatter(
                    x=UPPER["MRM_DATE"],
                    y=UPPER["ACTUAL"],
                    text=UPPER["ACTUAL"],
                    mode="markers",
                    marker=dict(color=config_plotly.multi_color_lst[0]),
                    name="UPPER",
                    legendgroup="UPPER",
                )

                trace2 = go.Scatter(
                    x=LOWER["MRM_DATE"],
                    y=LOWER["ACTUAL"],
                    text=LOWER["ACTUAL"],
                    mode="markers",
                    marker=dict(color=config_plotly.multi_color_lst[1]),
                    name="LOWER",
                    legendgroup="LOWER",
                )
                # 전체 레이아웃 설정
                layout = go.Layout(
                    title="CTL Trend",
                    height=300,
                    legend=dict(
                        orientation="h", y=1.1, yanchor="bottom", x=1, xanchor="right"
                    ),
                )
                fig = go.Figure(data=[trace1, trace2], layout=layout)
                if "UL" in UPPER.columns and not pd.isna(UPPER["UL"].values[0]):
                    fig.add_hline(
                        y=UPPER["UL"].values[0],
                        line=dict(
                            color=config_plotly.NEGATIVE_CLR, dash="dot", width=1
                        ),
                    )
                if "LL" in UPPER.columns and not pd.isna(UPPER["LL"].values[0]):
                    fig.add_hline(
                        y=UPPER["LL"].values[0],
                        line=dict(
                            color=config_plotly.NEGATIVE_CLR, dash="dot", width=1
                        ),
                    )
                # X축을 카테고리 타입으로 설정
                fig.update_xaxes(type="category")
                # Y축 그리드 제거
                fig.update_yaxes(showgrid=False)
                ctl_col[2].plotly_chart(fig)
        else:
            st.warning("No CTL data found")


# =============================================================================
# 메인 페이지 UI 구성
# =============================================================================

st.title("OE Mass Production Assessment")
main_tab = st.tabs(["Overview", "Detail", "Description"])

# Assessment 결과 데이터 로드
result_df = load_assessment_result()

# 품질 지수 계산
result_df = calculate_quality_indices(result_df)

# CQMS, Field Return 추가
result_df = calculate_cqms_n_filed_return(result_df)


with main_tab[0]:
    render_overview_tab(result_df)

with main_tab[1]:
    render_detail_tab(result_df)

with main_tab[2]:
    render_description_tab()
