"""
docstring
"""

import matplotlib.colors as mcolors


def get_transparent_colors(base_color, num_colors):
    """
    주어진 기본 색상을 기준으로 투명도가 점점 증가하는 색상 목록을 생성하여 반환
    base_color는 기본 색상이고, num_colors는 생성할 색상의 개수
    색상은 RGBA 형식으로 반환
    """
    base_rgb = mcolors.hex2color(base_color)
    if num_colors != 1:
        colors = []
        for i in range(num_colors):
            alpha = 1.0 - (i / (num_colors - 1) * 0.8)  # 투명도 조정 (0.2 to 1.0)
            color_with_alpha = "rgba({},{},{},{})".format(
                int(base_rgb[0] * 255),
                int(base_rgb[1] * 255),
                int(base_rgb[2] * 255),
                alpha,
            )
            colors.append(color_with_alpha)
    else:
        colors = [base_color]
    return colors
