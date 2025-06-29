import streamlit as st


def load_custom_css():
    """커스텀 CSS 스타일을 로드하여 UI 일관성을 향상시킵니다."""
    st.markdown(
        """
    <style>
    /* Material Icons 스타일링 */
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }
    
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }
    
    .material-symbols-sharp {
        font-family: 'Material Symbols Sharp';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }
    
    /* 아이콘 크기 변형 */
    .icon-small { font-size: 16px; }
    .icon-medium { font-size: 24px; }
    .icon-large { font-size: 32px; }
    .icon-xlarge { font-size: 48px; }
    
    /* 아이콘 색상 변형 */
    .icon-primary { color: #1f77b4; }
    .icon-success { color: #059669; }
    .icon-warning { color: #d97706; }
    .icon-danger { color: #dc2626; }
    .icon-info { color: #2563eb; }
    .icon-secondary { color: #6b7280; }
    
    /* 전체 페이지 여백 조정 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 섹션 간격 조정 */
    .stMarkdown {
        margin-bottom: 1rem;
    }
    
    /* 데이터프레임 스타일링 */
    .stDataFrame {
        margin: 1rem 0;
    }
    
    /* 메트릭 카드 스타일링 */
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    
    
    
    /* 구분선 스타일링 */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e0e0e0;
    }
    
    /* 경고 메시지 스타일링 */
    .stAlert {
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    
    /* 정보 메시지 스타일링 */
    .stInfo {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 제목 스타일링 */
    h1, h2, h3, h4 {
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #1f2937;
    }
    
    /* 컬럼 간격 조정 */
    .row-widget.stHorizontal {
        gap: 1rem;
    }
    
    /* 컨테이너 패딩 */
    .stContainer {
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 카드 스타일링 */
    .card-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        border-left: 4px solid #ec6608;
    }
    
    .card-container h3 {
        color: #1f2937;
        margin-bottom: 1rem;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .metric-card h4 {
        color: #1f2937;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 0.5rem 0;
    }
    
    .metric-value.quality-excellent {
        color: #059669;
    }
    
    .metric-value.quality-good {
        color: #2563eb;
    }
    
    .metric-value.quality-warning {
        color: #d97706;
    }
    
    .metric-value.quality-poor {
        color: #dc2626;
    }
    
    .metric-description {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f3f4f6;
    }
    
    .section-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: #1f77b4;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
    }
    
    .insight-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .insight-title {
        font-weight: 600;
        color: #92400e;
        margin-bottom: 0.5rem;
    }
    
    .insight-text {
        color: #78350f;
        font-size: 0.95rem;
    }
    
    .quality-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .quality-excellent {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .quality-good {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    
    .quality-warning {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    .quality-poor {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    .toggle-section {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 1rem 0;
        overflow: hidden;
    }
    
    .toggle-header {
        background: #f1f5f9;
        padding: 1rem;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .toggle-content {
        padding: 1rem;
        background: white;
    }
    
    .highlight-box {
        background: #e0e7ff;
        border: 1px solid #6366f1;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .highlight-title {
        font-weight: 600;
        color: #3730a3;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .highlight-text {
        color: #4338ca;
        font-size: 1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
