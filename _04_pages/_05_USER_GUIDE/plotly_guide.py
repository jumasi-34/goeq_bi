import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def render():
    """Plotly 차트 인터페이스 가이드 페이지를 렌더링합니다."""
    st.title("Plotly Chart Guide")

    # Plotly의 주요 특징
    st.header("1. Key Features")
    st.markdown(
        """
    - **Interactive Visualization**: Zoom, pan, hover over data points
    - **Multiple Chart Types**: Over 40 different chart types available
    - **Responsive Design**: Works on mobile, tablet, and desktop
    - **Real-time Updates**: Optimized for dynamic data visualization
    - **Advanced Customization**: Fine control over layout, colors, and animations
    """
    )

    # 기본 사용법
    st.header("2. Basic Usage")
    st.markdown(
        """
    ### Chart Controls
    - **Zoom**: Click and drag to zoom in/out
    - **Pan**: Click and drag to move around
    - **Reset**: Double click to reset the view
    - **Hover**: Move mouse over data points to see details
    - **Download**: Click the camera icon to save as PNG
    """
    )

    # 차트 타입 설명
    st.header("3. Common Chart Types")
    st.markdown(
        """
    - **Line Chart**: Show trends over time
    - **Bar Chart**: Compare values across categories
    - **Scatter Plot**: Show relationship between two variables
    - **Pie Chart**: Show proportions of a whole
    - **Box Plot**: Show distribution of data
    """
    )

    # 인터랙션 가이드
    st.header("4. Interaction Guide")
    st.markdown(
        """
    ### Mouse Controls
    - **Left Click + Drag**: Pan the chart
    - **Scroll**: Zoom in/out
    - **Double Click**: Reset view
    - **Right Click**: Show context menu
    
    ### Touch Controls
    - **Pinch**: Zoom in/out
    - **Tap + Drag**: Pan the chart
    - **Double Tap**: Reset view
    """
    )


render()
