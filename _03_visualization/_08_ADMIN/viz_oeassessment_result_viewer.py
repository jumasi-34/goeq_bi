"""
OE Assessment 결과 시각화 모듈

이 모듈은 OE Assessment 결과를 다양한 차트와 그래프로 시각화하는 함수들을 제공합니다.
Plotly Graph Objects를 사용하여 인터랙티브한 차트를 생성합니다.

주요 기능:
- 생산량 바 차트
- NCF (부적합) 분석 차트
- UF (Uniformity) 분석 차트
- 중량 분포 분석 차트
- RR (Reliability) 분석 차트
- CTL (Control) 분석 차트

작성자: [작성자명]
최종 수정일: [날짜]
"""

import plotly.graph_objects as go
from _03_visualization import config_plotly
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd


# 생산량
def draw_barplot_production(df):
    """
    생산량 월별 바 차트를 생성합니다.

    Args:
        df (pd.DataFrame): 생산량 데이터프레임
            - YYYYMM: 년월 (str)
            - PRDT_QTY: 생산량 (int/float)

    Returns:
        go.Figure: 생산량 바 차트

    시각화 특징:
        - 오렌지색 바 차트
        - Y축 범위는 최대값의 1.2배로 설정
        - X축은 카테고리 순서로 정렬
    """
    trace = go.Bar(
        x=df["YYYYMM"],
        y=df["PRDT_QTY"],
        text=df["PRDT_QTY"],
        texttemplate="%{text:,.0f}",
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        title_text="Production",
        xaxis_title="Month",
        yaxis_title="Production Qty",
        yaxis=dict(range=[0, df["PRDT_QTY"].max() * 1.2]),
        xaxis=dict(
            type="category",
            categoryorder="category ascending",
        ),
    )
    fig = go.Figure(trace, layout)
    return fig


# 부적합
def draw_barplot_ncf(df):
    """
    NCF (부적합) 월별 바 차트를 생성합니다.

    Args:
        df (pd.DataFrame): NCF 데이터프레임
            - YYYYMM: 년월 (str)
            - DFT_QTY: 부적합 수량 (int/float)

    Returns:
        go.Figure: NCF 바 차트

    시각화 특징:
        - 오렌지색 바 차트
        - Y축 범위는 최대값의 1.2배로 설정
    """
    trace = go.Bar(
        x=df["YYYYMM"],
        y=df["DFT_QTY"],
        text=df["DFT_QTY"],
        texttemplate="%{text:,.0f}",
        marker=dict(color=config_plotly.ORANGE_CLR),
    )
    layout = go.Layout(
        title_text="NCF",
        xaxis_title="Month",
        yaxis_title="DFT Qty",
        yaxis=dict(range=[0, df["DFT_QTY"].max() * 1.2]),
    )
    fig = go.Figure(trace, layout)
    return fig


def draw_barplot_ncf_pareto(df):
    """
    NCF 부적합코드별 파레토 차트를 생성합니다.

    Args:
        df (pd.DataFrame): NCF 파레토 데이터프레임
            - DFT_CD: 부적합 코드 (str)
            - DFT_QTY: 부적합 수량 (int/float)
            - CUM_PCT: 누적 백분율 (float)

    Returns:
        go.Figure: NCF 파레토 차트

    시각화 특징:
        - 회색 바 차트 (부적합 수량)
        - 빨간색 선 그래프 (누적 백분율)
        - 이중 Y축 사용
    """
    trace1 = go.Scatter(
        x=df["DFT_CD"],
        y=df["CUM_PCT"],
        text=df["CUM_PCT"],
        name="Cumulative %",
        marker=dict(color=config_plotly.NEGATIVE_CLR),
        yaxis="y2",
    )
    trace2 = go.Bar(
        x=df["DFT_CD"],
        y=df["DFT_QTY"],
        text=df["DFT_QTY"],
        texttemplate="%{text:.0f}",
        marker=dict(color=config_plotly.GRAY_CLR),
        yaxis="y",
    )
    layout = go.Layout(
        title_text="NCF : Pareto Chart",
        yaxis=dict(
            title="value_col",
            showgrid=False,
        ),
        yaxis2=dict(
            title="Cumulative Percentage",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        showlegend=False,
        hovermode="x",
    )
    fig = go.Figure([trace1, trace2], layout)
    return fig


# UF
def draw_barplot_uf(df):
    """
    UF (Uniformity) 월별 합격률 차트를 생성합니다.

    Args:
        df (pd.DataFrame): UF 데이터프레임
            - YYYYMM: 년월 (str)
            - UF_INS_QTY: 검사 수량 (int/float)
            - UF_PASS_QTY: 합격 수량 (int/float)
            - PASS_RATE: 합격률 (float)

    Returns:
        go.Figure: UF 합격률 차트

    시각화 특징:
        - 그룹 바 차트 (검사 수량, 합격 수량)
        - 선 그래프 (합격률)
        - 이중 Y축 사용
        - 가로 범례 배치
    """
    trace1 = go.Bar(
        x=df["YYYYMM"],
        y=df["UF_INS_QTY"],
        text=df["UF_INS_QTY"],
        texttemplate="%{text:,.0f}",
        marker=dict(color=config_plotly.GRAY_CLR),
        name="UF INS QTY",
    )
    trace2 = go.Bar(
        x=df["YYYYMM"],
        y=df["UF_PASS_QTY"],
        text=df["UF_PASS_QTY"],
        texttemplate="%{text:,.0f}",
        marker=dict(color=config_plotly.ORANGE_CLR),
        name="UF PASS QTY",
    )
    trace3 = go.Scatter(
        x=df["YYYYMM"],
        y=df["PASS_RATE"],
        text=df["PASS_RATE"],
        marker=dict(color=config_plotly.NEGATIVE_CLR),
        mode="lines+markers+text",
        name="Uniformity Pass %",
        texttemplate="%{text:,.1%}",
        textposition="top center",
        yaxis="y2",
    )
    layout = go.Layout(
        height=500,
        title="Uniformity Pass Rate",
        barmode="group",
        yaxis=dict(
            title="Production Quantity",
            showgrid=False,
            domain=[0, 0.9],
            range=[0, max(df["UF_INS_QTY"]) * 2],
        ),
        yaxis2=dict(
            title="UF PASS RATE",
            overlaying="y",
            side="right",
            range=[
                df["PASS_RATE"].min() * 0.9,
                df["PASS_RATE"].max() * 1.1,
            ],
            tickformat=".1%",
        ),
        xaxis=dict(
            type="date",
            tickformat="%b %y",
            dtick="M1",
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            x=1,
            xanchor="right",
            y=1,
            yanchor="top",
        ),
    )

    fig = go.Figure([trace1, trace2, trace3], layout)
    return fig


def draw_barplot_uf_individual(df_raw, df_standard):
    """
    UF 개별 항목별 히스토그램을 생성합니다.

    Args:
        df_raw (pd.DataFrame): UF 원시 데이터프레임
            - RFV: RFV 측정값 (float)
            - LFV: LFV 측정값 (float)
            - CON: CON 측정값 (float)
            - HAR: HAR 측정값 (float)
        df_standard (pd.DataFrame): UF 표준값 데이터프레임
            - RFV_STD: RFV 표준값 (float)
            - LFV_STD: LFV 표준값 (float)
            - CON_STD: CON 표준값 (float)
            - HAR_STD: HAR 표준값 (float)

    Returns:
        go.Figure: UF 개별 항목 히스토그램 (2x2 서브플롯)

    시각화 특징:
        - 2x2 서브플롯 구성
        - RFV, LFV: 오렌지색 히스토그램
        - CON: 음수값을 양수로 변환하여 빨간색 히스토그램
        - HAR: 오렌지색 히스토그램
    """
    rfv_std = df_standard["RFV_STD"].values[0]
    lfv_std = df_standard["LFV_STD"].values[0]
    con_std = df_standard["CON_STD"].values[0]
    har_std = df_standard["HAR_STD"].values[0]

    positive_con = df_raw[df_raw["CON"] > 0].copy()
    negative_con = df_raw[df_raw["CON"] < 0].copy()
    negative_con["CON"] = negative_con["CON"] * -1

    # 2x2 서브플롯 생성
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("RFV", "LFV", "CON", "HAR"),
        vertical_spacing=0.3,
        horizontal_spacing=0.1,
    )

    # RFV 히스토그램 추가
    fig.add_trace(
        go.Histogram(
            x=df_raw["RFV"],
            marker=dict(color=config_plotly.ORANGE_CLR),
            name="RFV",
        ),
        row=1,
        col=1,
    )

    # LFV 히스토그램 추가
    fig.add_trace(
        go.Histogram(
            x=df_raw["LFV"],
            marker=dict(color=config_plotly.ORANGE_CLR),
            name="LFV",
        ),
        row=1,
        col=2,
    )

    # CON 히스토그램 추가
    fig.add_trace(
        go.Histogram(
            x=negative_con["CON"],
            marker=dict(color=config_plotly.NEGATIVE_CLR, opacity=0.5),
            name="CON",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Histogram(
            x=positive_con["CON"],
            marker=dict(color=config_plotly.POSITIVE_CLR, opacity=0.5),
            name="CON",
        ),
        row=2,
        col=1,
    )

    # HAR 히스토그램 추가
    fig.add_trace(
        go.Histogram(
            x=df_raw["HAR"],
            marker=dict(color=config_plotly.ORANGE_CLR),
            name="HAR",
        ),
        row=2,
        col=2,
    )

    # 레이아웃 업데이트
    fig.update_layout(
        height=500, showlegend=False, title_text="Uniformity Test Results", title_x=0.5
    )

    # x축 레이블 업데이트
    fig.update_xaxes(title_text="Value", row=1, col=1)
    fig.update_xaxes(title_text="Value", row=1, col=2)
    fig.update_xaxes(title_text="Value", row=2, col=1)
    fig.update_xaxes(title_text="Value", row=2, col=2)

    # y축 레이블 업데이트
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=2)

    fig.add_vline(
        line=dict(width=1, color="red", dash="dash"),
        annotation=dict(
            text=f"RFV : {rfv_std}",
            showarrow=True,
            ax=30,
            ay=20,
            arrowcolor=config_plotly.GRAY_CLR,
            arrowhead=2,
            arrowwidth=1.5,
            arrowside="end",
            standoff=3,
        ),
        x=rfv_std,
        row=1,
        col=1,
    )
    fig.add_vline(
        line=dict(width=1, color="red", dash="dash"),
        annotation=dict(
            text=f"LFV : {lfv_std}",
            showarrow=True,
            ax=lfv_std,
            ay=20,
            arrowcolor=config_plotly.GRAY_CLR,
            arrowhead=2,
            arrowwidth=1.5,
            arrowside="end",
            standoff=3,
        ),
        x=lfv_std,
        row=1,
        col=2,
    )
    fig.add_vline(
        line=dict(width=1, color="red", dash="dash"),
        annotation=dict(
            text=f"CON : {con_std}",
            showarrow=True,
            ax=con_std,
            ay=20,
            arrowcolor=config_plotly.GRAY_CLR,
            arrowhead=2,
            arrowwidth=1.5,
            arrowside="end",
            standoff=3,
        ),
        x=con_std,
        row=2,
        col=1,
    )
    fig.add_vline(
        line=dict(width=1, color="red", dash="dash"),
        annotation=dict(
            text=f"HAR : {har_std}",
            showarrow=True,
            ax=har_std,
            ay=20,
            arrowcolor=config_plotly.GRAY_CLR,
            arrowhead=2,
            arrowwidth=1.5,
            arrowside="end",
            standoff=3,
        ),
        x=har_std,
        row=2,
        col=2,
    )
    return fig


# weight
def draw_weight_distribution(df):
    """
    중량 합격률 월별 차트를 생성합니다.

    Args:
        df (pd.DataFrame): 중량 데이터프레임
            - INS_DATE_YM: 검사 년월 (str)
            - WT_INS_QTY: 검사 수량 (int/float)
            - WT_PASS_QTY: 합격 수량 (int/float)
            - PASS_PCT: 합격률 (float)

    Returns:
        go.Figure: 중량 합격률 차트

    시각화 특징:
        - 그룹 바 차트 (검사 수량, 합격 수량)
        - 선 그래프 (합격률)
        - 이중 Y축 사용
        - 가로 범례 배치
    """
    # 검사 수량 바 차트
    trace1 = go.Bar(
        x=df["INS_DATE_YM"],
        y=df["WT_INS_QTY"],
        text=df["WT_INS_QTY"],
        name="Inspection Quantity",
        marker=dict(color=config_plotly.GRAY_CLR),
        texttemplate="%{text:,.0f}",
        textposition=None,
        yaxis="y",
    )
    # 합격 수량 바 차트
    trace2 = go.Bar(
        x=df["INS_DATE_YM"],
        y=df["WT_PASS_QTY"],
        text=df["WT_PASS_QTY"],
        name="PASS Quantity",
        marker=dict(color=config_plotly.ORANGE_CLR),
        texttemplate="%{text:,.0f}",
        textposition=None,
        yaxis="y",
    )
    # 합격률 선 그래프 (우측 Y축)
    trace3 = go.Scatter(
        x=df["INS_DATE_YM"],
        y=df["PASS_PCT"],
        text=df["PASS_PCT"],
        textposition="top center",
        marker=dict(color=config_plotly.NEGATIVE_CLR),
        mode="lines+markers+text",
        texttemplate="%{text:,.1%}",
        yaxis="y2",
        name="GT Weight Pass %",
    )
    layout = go.Layout(
        title="GT Weight Pass Rate",
        barmode="group",  # bar 차트를 그룹 형태로 표시
        yaxis=dict(
            title="Production Quantity",
            showgrid=False,
            domain=[0, 0.85],
            range=[0, max(df["WT_INS_QTY"]) * 1.2],
        ),
        yaxis2=dict(
            title="GT Weight Pass %",
            overlaying="y",
            side="right",
            range=[0.7, 1.05],
        ),
        xaxis=dict(
            type="date",
            tickformat="%b %y",
            dtick="M1",
            rangemode="tozero",
        ),
        legend=dict(orientation="h", y=1, yanchor="top"),
    )
    fig = go.Figure([trace1, trace2, trace3], layout)
    return fig


def draw_weight_distribution_individual(df, wt_spec):
    """
    개별 중량 분포 박스플롯을 생성합니다.

    Args:
        df (pd.DataFrame): 중량 개별 데이터프레임
            - INS_DATE_YM: 검사 년월 (str)
            - MRM_WGT: 측정 중량 (float)
        wt_spec (float): 표준 중량값

    Returns:
        go.Figure: 중량 분포 박스플롯

    시각화 특징:
        - 월별 박스플롯
        - 평균값 표시
        - 아웃라이어 제거된 데이터 사용
        - 표준 중량값 수평선 표시
    """
    fig = go.Figure()

    # 박스플롯 생성
    trace = go.Box(
        x=df["INS_DATE_YM"],
        y=df["MRM_WGT"],
        name="Weight Distribution",
        marker=dict(color=config_plotly.ORANGE_CLR, opacity=0.5),
        boxmean=True,  # 평균값 표시
        notched=False,
        boxpoints=False,  # 개별 데이터 포인트 표시하지 않음
    )

    # 레이아웃 설정
    layout = go.Layout(
        title="Monthly Weight Distribution (Outliers Removed)",
        xaxis_title="Month",
        yaxis_title="Weight",
        showlegend=False,
    )

    # x축 날짜 정렬

    fig = go.Figure([trace], layout)
    fig.update_xaxes(type="category", categoryorder="category ascending")
    fig.add_hline(
        y=wt_spec, line=dict(color=config_plotly.GRAY_CLR, width=1, dash="dash")
    )
    return fig


def draw_rr_trend(rr_raw_df, rr_standard_df):
    """
    RR (Reliability) 트렌드 차트를 생성합니다.

    Args:
        rr_raw_df (pd.DataFrame): RR 원시 데이터프레임
            - SMPL_DATE: 샘플링 날짜 (datetime)
            - Result_new: RR 측정값 (float)
        rr_standard_df (pd.DataFrame): RR 표준값 데이터프레임
            - SPEC_MAX: 최대 허용값 (float)
            - SPEC_MIN: 최소 허용값 (float)

    Returns:
        go.Figure: RR 트렌드 차트

    시각화 특징:
        - 산점도 형태의 트렌드 차트
        - 최대/최소 허용값 수평선 표시
        - Y축 범위는 표준값 기준으로 설정
    """
    # 표준값 추출
    spec_max = rr_standard_df["SPEC_MAX"].values[0]
    spec_min = rr_standard_df["SPEC_MIN"].values[0]

    # RR 트렌드 산점도
    trace = go.Scatter(
        x=rr_raw_df["SMPL_DATE"],
        y=rr_raw_df["Result_new"],
        text=rr_raw_df["Result_new"],
        marker=dict(color=config_plotly.ORANGE_CLR, size=10),
        texttemplate="%{text:.2f}",
        mode="markers",
    )

    layout = go.Layout(
        title_text="RR Trend",
        xaxis_title="DATE",
        yaxis_title="RRc",
        yaxis=dict(
            range=[
                spec_max - 0.7 if spec_min == 0 else spec_min * 0.95,
                spec_max + 0.1,
            ],
        ),
    )

    fig = go.Figure([trace], layout)

    # 최대 허용값 수평선 추가
    fig.add_hline(
        y=spec_max,
        line_width=1,
        line_dash="dot",
        line_color=config_plotly.NEGATIVE_CLR,
    )
    # 최소 허용값이 0이 아닌 경우에만 수평선 추가
    if spec_min != 0:
        fig.add_hline(
            y=spec_min,
            line_width=1,
            line_dash="dot",
            line_color=config_plotly.NEGATIVE_CLR,
        )
    return fig


def draw_rr_distribution(rr_df, rr_standard_df):
    """
    RR (Reliability) 정규분포 차트를 생성합니다.

    Args:
        rr_df (pd.DataFrame): RR 데이터프레임
            - Result_new: RR 측정값 (float)
        rr_standard_df (pd.DataFrame): RR 표준값 데이터프레임
            - SPEC_MAX: 최대 허용값 (float)
            - SPEC_MIN: 최소 허용값 (float)

    Returns:
        go.Figure: RR 정규분포 차트

    시각화 특징:
        - 정규분포 곡선
        - 평균값 수직선
        - 최대/최소 허용값 수직선
        - 확률밀도 함수 사용
    """
    # 표준값 추출
    spec_max = rr_standard_df["SPEC_MAX"].values[0]
    spec_min = rr_standard_df["SPEC_MIN"].values[0]

    # RR 분포 통계 계산
    mean, std = np.mean(rr_df["Result_new"]), np.std(rr_df["Result_new"])
    range_max = max(spec_max + 0.1, rr_df["Result_new"].max())
    range_min = min(
        spec_min - 0.7 if spec_min == 0 else spec_min - 0.1,
        rr_df["Result_new"].min(),
    )

    # 정규분포 곡선 생성
    x = np.linspace(range_min, spec_max, 100)
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-((x - mean) ** 2) / (2 * std**2))

    # 정규분포 곡선 트레이스
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name="Normal Distribution",
        line=dict(color=config_plotly.ORANGE_CLR),
    )

    layout = go.Layout(
        title="Normal Distribution",
        xaxis=dict(title="Value", showgrid=False),
        yaxis=dict(
            title=dict(text="Probability Density"),
            showticklabels=False,
            showgrid=False,
        ),
    )

    fig = go.Figure([trace], layout)

    # 평균값 수직선 추가
    fig.add_vline(x=mean, line=dict(color="red", dash="dash"), annotation_text="Mean")
    # 최대 허용값 수직선 추가
    fig.add_vline(
        x=spec_max,
        line=dict(color="green", dash="dot"),
        annotation_text="Max",
    )
    # 최소 허용값이 0이 아닌 경우에만 수직선 추가
    if spec_min != 0:
        fig.add_vline(
            x=spec_min,
            line=dict(color="green", dash="dot"),
            annotation_text="Min",
        )
    return fig


# CTL
def draw_ctl_trend(df):
    """
    CTL (Control) 합격률 트렌드 차트를 생성합니다.

    Args:
        df (pd.DataFrame): CTL 트렌드 데이터프레임
            - MRM_DATE: 측정 날짜 (str)
            - ctl_pass_rate: CTL 합격률 (float)

    Returns:
        go.Figure: CTL 합격률 트렌드 차트

    시각화 특징:
        - 바 차트 형태의 트렌드
        - Y축 범위는 0~110% (1.1)
        - 퍼센트 형식으로 표시
    """
    trace = go.Bar(
        x=df["MRM_DATE"],
        y=df["ctl_pass_rate"],
        text=df["ctl_pass_rate"],
        texttemplate="%{text:.1%}",
    )

    layout = go.Layout(
        title=dict(text="CTL Pass Rate"),
        xaxis=dict(type="category"),
        yaxis=dict(range=[0, 1.1], tickformat=".0%", showgrid=False),
    )

    fig = go.Figure([trace], layout)
    return fig


def draw_ctl_detail(df):
    """
    CTL (Control) 상세 분석 차트를 생성합니다.

    Args:
        df (pd.DataFrame): CTL 상세 데이터프레임
            - MRM_ITEM: 측정 항목 (str)
            - 기타 측정값 컬럼들

    Returns:
        go.Figure: CTL 상세 분석 차트 (4x4 서브플롯)

    시각화 특징:
        - 4x4 서브플롯 구성
        - 16개 측정 항목별 개별 차트
        - 각 항목별 상세 분석 결과 표시
    """
    rows, cols = 4, 4
    # CTL 측정 항목 리스트
    CTMS_MRM_ITEM = (
        "BS.12",
        "ILG",
        "NBD",
        "FCD",
        "RCG",
        "CRCC",
        "CRCB",
        "UTG.G0",
        "UTG.G1",
        "UTG.Sho",
        "1BHAW",
        "2BHAW",
        "1TUAH",
        "BFH",
        "I/P",
        "TShG.C+y",
    )

    # 4x4 서브플롯 생성
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=CTMS_MRM_ITEM[: rows * cols],
        shared_xaxes=True,
    )

    # 각 측정 항목별로 서브플롯에 차트 추가
    for idx, item in enumerate(CTMS_MRM_ITEM[: rows * cols]):
        row = (idx // cols) + 1
        col = (idx % cols) + 1

        # 해당 항목의 데이터 필터링
        subset = df[df["MRM_ITEM"] == item]

        # UPPER와 LOWER 데이터 분리
        UPPER = subset[subset["SIDE"] == "UPPER"]
        LOWER = subset[subset["SIDE"] == "LOWER"]

        # UPPER 측정값 산점도 추가
        fig.add_trace(
            go.Scatter(
                x=UPPER["MRM_DATE"],
                y=UPPER["ACTUAL"],
                text=UPPER["ACTUAL"],
                mode="markers",
                marker=dict(color=config_plotly.multi_color_lst[0]),
                name="UPPER",
                showlegend=(idx == 0),  # 첫 번째 서브플롯에서만 범례 표시
                legendgroup="UPPER",
            ),
            row=row,
            col=col,
        )

        # LOWER 측정값 산점도 추가
        fig.add_trace(
            go.Scatter(
                x=LOWER["MRM_DATE"],
                y=LOWER["ACTUAL"],
                text=LOWER["ACTUAL"],
                mode="markers",
                marker=dict(color=config_plotly.multi_color_lst[1]),
                showlegend=(idx == 0),  # 첫 번째 서브플롯에서만 범례 표시
                name="LOWER",
                legendgroup="LOWER",
            ),
            row=row,
            col=col,
        )

        # UPPER 허용 한계선 추가 (존재하는 경우)
        if "UL" in UPPER.columns and not pd.isna(UPPER["UL"].values[0]):
            fig.add_hline(
                y=UPPER["UL"].values[0],
                line=dict(color=config_plotly.NEGATIVE_CLR, dash="dot", width=1),
                row=row,
                col=col,
            )
        # LOWER 허용 한계선 추가 (존재하는 경우)
        if "LL" in UPPER.columns and not pd.isna(UPPER["LL"].values[0]):
            fig.add_hline(
                y=UPPER["LL"].values[0],
                line=dict(color=config_plotly.NEGATIVE_CLR, dash="dot", width=1),
                row=row,
                col=col,
            )

    # 전체 레이아웃 설정
    fig.update_layout(
        title="CTL Trend",
        height=500,
        legend=dict(orientation="h", y=1.1, yanchor="bottom", x=1, xanchor="right"),
    )
    # X축을 카테고리 타입으로 설정
    fig.update_xaxes(type="category")
    # Y축 그리드 제거
    fig.update_yaxes(showgrid=False)
    return fig
