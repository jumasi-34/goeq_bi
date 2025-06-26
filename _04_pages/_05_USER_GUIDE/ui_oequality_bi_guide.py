import streamlit as st
import base64

# --- Page Title ---
st.title("OE Quality BI User Guide")

# --- Tabs ---

style = """
    border-radius: 20px;
    box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.3);
"""


def get_gif_html(gif_path: str, width=800, style=style):
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


# --- 1. 전체 화면 구조 안내 ---
layout_title = """Layout
This document explains the common layout components used across all pages of the OE Quality BI dashboard. Each page follows the same structural format, allowing users to efficiently navigate and interact with quality-related data.
"""
layout_description = """
##### Top Navigation Bar
Provides dropdown access to key system menus at the top of the screen.

##### Filter Area
Allows users to filter data from the left sidebar, with results reflected in the main content.

##### Tabs
Enables switching between data views or categories within the same page.

##### Main Contents
Displays core visualizations and supports interactive features like zoom and filtering.

##### Navigation Button
Redirects users to the Navigation page showing the full system menu for quick access.
"""
display_gif_step(
    layout_title,
    "_06_assets/bi_guide/ug_bi_layout_icon.png",
    layout_description,
)

# --- 2. Plotly 그래프 사용법 및 버튼 설명 ---
plotly_control_title = """Basic Interactions in Plotly Charts
Plotly charts offer various interactive features that allow users to intuitively explore
"""
plotly_control_description = """
##### Legend Control (Show / Hide)
Click a legend item → Show or hide the corresponding data series  
Double-click → Highlight only the selected series

##### Hover Information
Hover over a data point to view its value and additional details

##### Axis Control
Mouse drag left/right → Pan along the X-axis  
Double-click → Reset axis to default view  
Shift + drag → Pan (when in Zoom mode)
"""
display_gif_step(
    plotly_control_title,
    "_06_assets/bi_guide/ug_bi_plotly_control.gif",
    plotly_control_description,
)

plotly_toolbar_title = """Toolbar Functions in Plotly Charts
Plotly charts include a set of toolbar icons that enhance interactivity and usability. These tools allow users to zoom, reset, save, and expand the chart for better analysis and presentation.
"""
plotly_toolbar_description = """
##### ① Download plot as a png
Save the chart as a PNG image for use in reports or presentations.  

##### ② Zoom & Pan
Zoom in to examine specific areas or move across the chart. These functions must be activated by clicking the corresponding icons in the toolbar. Once active, you can interact with the chart using your mouse.

##### ③ Zoom in / Zoom out
Adjust the zoom level to focus in or out on the chart.  

##### ④ Autoscale / Reset axes
Restore the chart view to its original or best-fit layout.  

##### ⑤ Fullscreen / Close fullscreen
View the chart in full screen for better visibility during presentations.  
"""
display_gif_step(
    plotly_toolbar_title,
    "_06_assets/bi_guide/ug_bi_plotly_icon.png",
    plotly_toolbar_description,
)

dataframe_title = """Basic Table Manipulation
Streamlit tables offer a variety of user-friendly interactive features that enable efficient and intuitive data exploration. These built-in capabilities help users quickly analyze, organize, and extract information from tabular data with ease — all within a clean and responsive interface.
"""
dataframe_description = """
##### Column Sorting
Click on any column header to sort the data in ascending or descending order.

##### Scrolling with Fixed Headers
For large datasets, tables support vertical and horizontal scrolling with fixed headers.

##### Copy and Paste
Select and copy cells to paste into other applications like Excel or text editors.

##### CSV Download
Download the table data as a CSV file for external use.

##### Column Reordering
Columns can be rearranged by dragging their headers, allowing users to customize the layout by placing important information upfront and grouping related columns for easier comparison.
"""
display_gif_step(
    dataframe_title,
    "_06_assets/bi_guide/ug_bi_df.gif",
    dataframe_description,
)
